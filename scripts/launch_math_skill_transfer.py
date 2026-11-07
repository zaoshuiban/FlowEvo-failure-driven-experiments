"""Unified transfer preflight and separately authorized TRAIN entry."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from code_math.no_gold import PublicMathTask
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.contracts import fingerprint
from failure_evo.math_cumulative_learning import CumulativeLearner
from failure_evo.math_skill_transfer import (
    CumulativeTrainHandler, SingleFailureAdapter, SingleFailureTrainHandler, TransferShadowRelease, TransferTrain,
)
from failure_evo.math_stream import StreamRuntime, read
from failure_evo.math_transfer_launch import COST_UPPER, TOKEN_UPPER, TransferBudget, build_dev_cases, load_launch
from failure_evo.model_api import configured_api_key
from failure_evo.operator_version_gate import VersionGate
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.run_health import assert_run_healthy
from failure_evo.semantic_contract import SplitRunner

ROOT = Path(__file__).resolve().parents[1]


def authorization_fields(cfg):
    return dict(run_id=cfg['run_id'],phase='TRAIN',config_sha256=fingerprint(cfg),model=cfg['model'],
                max_cost_microusd=cfg['phase_call_caps']['TRAIN']*COST_UPPER,paid_api_authorized=True)


def preflight(config_path, phase='TRAIN'):
    cfg = load_launch(config_path,ROOT,phase)
    private = config_path.parent
    split = private/'frozen_splits'
    manifest = read(split/'data_split_manifest.json')
    if phase!='TRAIN':
        if phase=='DEV':
            dev = read(private/'dev_review/references.private.json')
            if dev['manifest_sha256']!=cfg['manifest_sha256']:
                raise PermissionError('DEV manifest differs')
            conflicts = [r['task_id'] for r in dev['rows'] if r['status']!='REFERENCE_VERIFIED']
            return cfg, manifest, None, dict(status='DEV_BLOCKED',reference_conflicts=conflicts,
                                           blockers=['CANDIDATE_SCOPED_REVIEWS_REQUIRED'])
        return cfg, manifest, None, dict(status='TEST_BLOCKED',blockers=[
            'SKILL_AND_TEXT_LIBRARY_FREEZE_REQUIRED','PAID_TEST_ROUTING_NOT_ENABLED',
            'SEPARATE_TEST_AUTHORIZATION_REQUIRED'])
    failures = read(split/'train_public_failures.json')
    schedule = TransferTrain(private/'run',manifest,failures,manifest_sha=cfg['manifest_sha256'],
                             failures_sha=cfg['train_failure_content_sha256'])
    if len(schedule.facts)!=10:
        raise PermissionError('exactly ten frozen TRAIN failures required')
    backend = FrozenLinuxBackend(image=cfg['worker']['image'],worker_script=ROOT/cfg['worker']['script'])
    if backend.manifest()!=cfg['worker']['manifest']:
        raise PermissionError('Worker differs from freeze')
    credential = bool(configured_api_key())
    receipt = private/'TRAIN_ACCEPTANCE.json'
    accepted = receipt.is_file() and read(receipt).get('config_sha256')==fingerprint(cfg) and read(receipt).get('passed') is True
    blockers = ([] if credential else ['DEEPSEEK_CREDENTIAL_MISSING']) + ([] if accepted else ['FROZEN_TRAIN_ACCEPTANCE_REQUIRED'])
    calls = cfg['phase_call_caps']['TRAIN']
    summary = dict(status='TRAIN_BLOCKED' if blockers else 'TRAIN_READY_PENDING_AUTHORIZATION',
                   blockers=blockers,train=len(schedule.facts),credential_configured=credential,
                   request_cap=calls,token_cap=calls*TOKEN_UPPER,cost_cap_microusd=calls*COST_UPPER,
                   authorization_fields=authorization_fields(cfg),paid_requests=0)
    return cfg, schedule, backend, summary


def train(config_path, authorization):
    cfg, schedule, backend, summary = preflight(config_path)
    if summary['status']!='TRAIN_READY_PENDING_AUTHORIZATION':
        raise PermissionError('TRAIN preflight blocked')
    if read(authorization)!=authorization_fields(cfg):
        raise PermissionError('matching separate TRAIN authorization required')
    return execute_train(cfg,schedule,backend)


def execute_train(cfg,schedule,backend,*,mock_sender=None):
    engineering = mock_sender is not None
    ph = fingerprint(cfg)
    run_id = ('engineering:' if engineering else '')+cfg['run_id']
    limits = TransferBudget(schedule.root,run_id,ph)
    tools = PersistentBudget(schedule.root/'worker_budget.jsonl',run_id=run_id+':worker',protocol_hash=ph,
                             max_calls=0,max_tokens=0,max_tools=cfg['worker']['max_calls'],max_cost_microusd=0,
                             token_rate_microusd_per_million=0,tool_cost_upper_microusd=0,
                             max_tool_milliseconds=cfg['worker']['max_milliseconds'],
                             tool_milliseconds_upper=15000,wall_seconds=7*86400)

    def health():
        limits.health()
        assert_run_healthy(budgets=[tools])

    arms = {}
    runners = {}
    for arm in 'ABCD':
        path = schedule.root/arm
        runners[arm] = SplitRunner(backend,path/'worker.jsonl',budget=tools)
        arms[arm] = dict(path=path,registry=VersionGate(path/'registry.jsonl'),split=runners[arm])
    stream = SimpleNamespace(plan=cfg['cumulative_plan'],arms={'F':arms['A']},engineering=engineering,
                             path=schedule.root,ph=ph,health=health,
                             tasks=[PublicMathTask.parse(f['task']) for f in schedule.facts],
                             emit_once=lambda *args: StreamRuntime.emit_once(None,*args),
                             source_review=lambda *_:dict(status='UNVERIFIED',correct=None))
    cumulative = CumulativeLearner(stream,'F',sender=(lambda wire:mock_sender('A',wire)) if engineering else None,release=TransferShadowRelease(),
                                    budget_factory=lambda p,n:limits.allocate(p,'TRAIN','A',n))
    cumulative.paid_authorization=dict(run_id=stream.path.name,protocol_sha256=ph,paid_api_authorized=True)

    def compiler_for(path, arm):
        account = limits.allocate(path/'budget.jsonl','TRAIN',arm,1 if arm=='C' else 2)
        auth = dict(run_id=account.config['run_id'],protocol_hash=ph,model=cfg['model'],
                    protocol=SingleFailureAdapter.protocol,max_cost_microusd=account.config['max_cost_microusd'],
                    paid_api_authorized=True)
        adapter = SingleFailureAdapter(path/'provider.jsonl',account,model=cfg['model'],authorization=auth,
                                       max_wire_input_upper=32768,mock=engineering,
                                       sender=(lambda wire:mock_sender(arm,wire)) if engineering else None)
        return BoundedCompiler(adapter,account,path/'compiler.jsonl',cfg['model'],max_input_upper=32768)

    handlers = {'A':CumulativeTrainHandler(cumulative)}
    for arm in 'BCD':
        handlers[arm] = SingleFailureTrainHandler(arm,schedule.manifest,compiler_for,arms[arm]['registry'],
                                                  runners[arm],arms[arm]['path'],engineering=engineering)
    return schedule.run(handlers,health)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['preflight','train','review-dev'])
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--authorization',type=Path)
    parser.add_argument('--phase',choices=['TRAIN','DEV','TEST'],default='TRAIN')
    parser.add_argument('--review',type=Path)
    parser.add_argument('--review-sha')
    parser.add_argument('--parent',type=Path)
    parser.add_argument('--candidate',type=Path)
    args = parser.parse_args()
    if args.action=='preflight':
        print(json.dumps(preflight(args.config,args.phase)[-1],indent=2))
    elif args.action=='review-dev':
        if not all((args.review,args.review_sha,args.parent,args.candidate)):
            parser.error('review-dev requires review, trusted review SHA, parent and candidate')
        cfg, manifest, _, _ = preflight(args.config,'DEV')
        private = args.config.parent
        references = read(private/'dev_review/references.private.json')
        cases = build_dev_cases(manifest,read(private/'frozen_splits/dev/tasks.json'),
                                references,read(args.review),read(args.parent),read(args.candidate),
                                review_sha=args.review_sha,references_sha=cfg['dev_reference_content_sha256'])
        print(json.dumps(dict(cases=len(cases),cases_sha256=fingerprint(cases),paid_requests=0)))
    elif not args.authorization:
        parser.error('train requires a separate authorization file')
    else:
        print(json.dumps(dict(settled_jobs=len(train(args.config,args.authorization))),indent=2))
