#!/usr/bin/env python3
"""Post-lock, zero-model audit. Never updates the Pilot or compiles private feedback.

Prepare pins original submissions before any full scoring. Execute reuses the
existing verifier, Docker backend, native call_skill executor and budget ledger.
Only training IDs from the frozen manifest may be scored. Private outputs live
under a separate, non-retrieval run directory; reports contain binary verdicts.
"""
from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'FlowEvo/src'))
sys.dont_write_bytecode = True
from core.schemas import CodeTaskInstance, WorkflowPlan, WorkflowStep
from eval.verifier import verify_task, _parse_harness_stdout
from failure_evo.contracts import fingerprint
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.pilot_runtime import IsolatedCodeSandbox, write_json
from failure_evo.pilot_data import task_from_manifest
from failure_evo.skill_runtime import validate_bundle, sha

OLD = REPO / 'runs/failure_acquisition_pilot_20261120/real_01'
OLD_REPORTS = REPO / 'reports/failure_acquisition_pilot_20261120'
ROOT = REPO / 'runs/failure_acquisition_postlock_audit_20261120'
REPORTS = REPO / 'reports/failure_acquisition_postlock_audit_20261120'
CONFIG = OLD_REPORTS / 'Pilot_Frozen_Config.json'
MANIFEST = OLD_REPORTS / 'Pilot_Data_Manifest.json'


def read(path):
    return json.loads(Path(path).read_text())


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative(path):
    return str(Path(path).resolve().relative_to(REPO))


def immutable_snapshot(cfg):
    files = set(OLD.rglob('*')) | set(OLD_REPORTS.rglob('*'))
    files |= {REPO / p for p in cfg['source_hashes']}
    files.add(REPO / 'configs/failure_acquisition_pilot.json')
    return {relative(p): file_sha(p) for p in sorted(files) if p.is_file()}


def find_execution(task_id, feedback, bundle, image):
    """Bind parsed verifier verdict to original raw execution, not exit status alone."""
    matches = []
    folder = OLD / 'executions/collect' / task_id.replace('/', '_')
    for path in sorted(folder.glob('*/input.json')):
        inp = read(path)
        if inp['code'] != feedback['executed_code'] or inp['bundle'] != bundle:
            continue
        result_path = path.with_name('result.json')
        result = read(result_path)
        assert result['identity'] == fingerprint(dict(code=inp['code'], bundle=bundle, image=image))
        assert result['code_sha256'] == fingerprint(inp['code'])
        _, harness = _parse_harness_stdout(result['stdout'])
        assert harness and harness['total_test_count'] > 0
        parsed_pass = result['passed'] and harness['passed_test_count'] == harness['total_test_count']
        assert parsed_pass == feedback['passed']
        matches.append(dict(input=relative(path), receipt=relative(result_path),
                            receipt_sha256=file_sha(result_path), identity=result['identity']))
    assert matches, 'ORIGINAL_EXECUTION_NOT_FOUND'
    return matches


def model_projection(row, source, *, passed, public_feedback, receipt):
    """Allowlist projection. Private VerifierFeedback is deliberately NOT an input.

    This is a future training payload, never a successful compilation trace.
    Public assertions come from the frozen public manifest, not executed_code.
    """
    if type(passed) is not bool or row['data_role'] != 'train':
        raise ValueError('TRAIN_BINARY_FEEDBACK_REQUIRED')
    return dict(task_id=row['problem_id'], public_prompt=row['prompt'], actor_source=source,
                public_feedback=dict(passed=bool(public_feedback['passed']),
                                     public_assertions=[e['assertion'] for e in row['examples']]),
                independent_training_feedback='PASS' if passed else 'FAIL',
                scoring_receipt_ref=receipt)


def projection_check(row):
    canary = 'PRIVATE_CANARY_NEVER_EXPORT_4d1fa'
    contaminated = dict(passed=True, executed_code=canary, failed_tests=[canary],
                        metrics=dict(hidden_inputs=[canary], canonical_solution=canary))
    out = model_projection(row, 'PUBLIC_SOURCE', passed=False,
                           public_feedback=contaminated, receipt='opaque_receipt_ref')
    assert canary not in json.dumps(out)
    try:
        model_projection(row, '', passed=contaminated, public_feedback=contaminated, receipt='')
    except ValueError:
        pass
    else:
        raise AssertionError('Private feedback object accepted as binary')
    return dict(nested_private_canary_removed=True, private_object_as_binary_rejected=True,
                compiler_receives_private_feedback=False)


def prepare():
    os.chdir(REPO)
    cfg, manifest = read(CONFIG), read(MANIFEST)
    assert file_sha(cfg['dataset_path']) == manifest['dataset_sha256']
    assert fingerprint(manifest) == cfg['manifest_sha256']
    drift = [p for p, h in cfg['source_hashes'].items() if file_sha(REPO / p) != h]
    assert not drift, 'PILOT_SOURCE_VERSION_DRIFT: ' + repr(drift)
    if (ROOT / 'protocol.json').exists():
        assert read(ROOT / 'immutable_before.json') == immutable_snapshot(cfg)
        print('PREPARED_ALREADY; no model or execution request')
        return
    ROOT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    write_json(ROOT / 'immutable_before.json', immutable_snapshot(cfg))
    progress = read(OLD / 'collect_progress.json')
    train = [r for r in manifest['tasks'] if r['data_role'] == 'train']
    assert len(train) == len(progress) == 24
    assert [x['result']['task_id'] for x in progress] == [r['problem_id'] for r in train]
    locked = []
    for item, row in zip(progress, train):
        tid = row['problem_id']
        result = item['result']
        info = dict(task_id=tid, task_version=dict(dataset_sha256=manifest['dataset_sha256'],
                    public_sha256=row['public_sha256']), entry_point=row['entry_point'],
                    public_verdict='PUBLIC_CHECK_PASS' if result['passed'] else 'PUBLIC_CHECK_FAIL',
                    trace_ref=result['trace_file'], planning_mode=result['planning_mode'],
                    compiled_skill_ids=result['compiled_skill_ids'],
                    compiled_skill_admitted=result['compiled_skill_admitted'],
                    compiled_skill_admission_bank=result['compiled_skill_admission_bank'],
                    source_lineage_id=row['source_lineage_id'],
                    capability_family_id=row['capability_family_id'])
        try:
            assert item['row'] == row
            trace = read(REPO / result['trace_file'])
            last = trace['attempts'][-1]
            source = last['candidate_code']
            feedback = last['verifier_feedback']
            bundle = trace['executable_dependencies']
            validate_bundle(bundle)
            assert source == trace['code_history'][-1]
            assert source in feedback['executed_code']
            assert trace['query'] == row['prompt']
            assert trace['validated_entry_point'] == row['entry_point']
            assert feedback == trace['verifier_feedback'][-1]
            assert feedback['passed'] == result['passed']
            receipts = find_execution(tid, feedback, bundle, cfg['image'])
            target = ROOT / 'locked_sources' / tid.replace('/', '_')
            target.mkdir(parents=True, exist_ok=True)
            (target / 'final.py').write_text(source)
            write_json(target / 'dependencies.json', bundle)
            write_json(target / 'public_feedback.json', feedback)
            requests = []
            request_dir = OLD / 'requests/collect' / tid.replace('/', '_') / 'actor'
            for request in sorted(request_dir.glob('*/request.json')):
                wire = read(request)
                requests.append(dict(request=relative(request), response=relative(request.with_name('response.json')),
                    receipt=relative(request.with_name('receipt.json')),
                    request_sha256=file_sha(request), response_sha256=file_sha(request.with_name('response.json')),
                    role='strategy_extraction' if 'strategy analyst' in wire['messages'][0]['content'] else 'solver'))
            info.update(source_status='RESTORED', final_source_sha256=sha(source),
                        source_ref=relative(target / 'final.py'), dependencies_ref=relative(target / 'dependencies.json'),
                        dependency_bundle_sha256=fingerprint(bundle),
                        dependencies=dict(image=cfg['image'], module_versions=bundle.get('entries', {}),
                                          third_party_packages='none; original image supplies Python and stdlib'),
                        public_feedback_ref=relative(target / 'public_feedback.json'),
                        original_executions=receipts, model_request_provenance=requests,
                        intermediate_failed_attempts=[dict(attempt_index=a['attempt_index'],
                            stage=a['stage'], source_sha256=sha(a['candidate_code']))
                            for a in trace['attempts'] if not a['verifier_feedback']['passed']])
        except (OSError, KeyError, ValueError, AssertionError) as exc:
            info.update(source_status='SOURCE_OR_DEPENDENCY_UNAVAILABLE',
                        restoration_error_type=type(exc).__name__, restoration_error=str(exc))
        locked.append(info)
    protocol = dict(name='postlock-opportunity-audit-v1', created_utc=datetime.now(timezone.utc).isoformat(),
        old_pilot_protocol_sha256=cfg['protocol_sha256'], dataset_sha256=manifest['dataset_sha256'],
        locked_submissions_sha256=fingerprint(locked), script_sha256=file_sha(__file__),
        train_ids=[r['problem_id'] for r in train],
        excluded_transfer_ids=[r['problem_id'] for r in manifest['tasks'] if r['data_role']=='transfer_dev'],
        budget=dict(model_requests=0, tokens=0, paid_model_usd=0, isolated_executions=32, wall_seconds=900),
        full_scoring='exact final source and historical dependency bundle; existing full HumanEval Verifier',
        public_call_probe=dict(task_id='Audit/HumanEval59_new_parameters', entry='largest_prime_factor',
                               inputs=[81,77,121,360], expected=[3,11,11,5],
                               scope='explicit native call_skill, not autonomous routing or independent support'),
        learning_permission=dict(scope='new protocol only; 24 assigned training tasks',
            allowed=['public prompt','actual actor source','original public feedback','binary independent training verdict'],
            forbidden=['private inputs','private expected outputs','private assertions','reference implementation',
                       'scorer code','private executed_code','transfer materials'],
            old_protocol_unchanged=True),
        selection='up to 3 FULL_CHECK_FAIL, lineage dedup, capability strata round robin, original order; otherwise inspect recovered capability gap',
        classes=['FULL_CHECK_PASS','FULL_CHECK_FAIL','SCORING_ERROR','SOURCE_OR_DEPENDENCY_UNAVAILABLE'],
        future_invalid_native_artifact_rule='quarantine identical source/dependency lineage in every future base-library copy; never rewrite old admission',
        no_compile_private_feedback=True)
    write_json(ROOT / 'locked_submissions.json', locked)
    write_json(ROOT / 'protocol.json', protocol)
    write_json(ROOT / 'projection_check.json', projection_check(train[0]))
    print(json.dumps(dict(prepared=len(locked), restored=sum(r['source_status']=='RESTORED' for r in locked),
                          protocol_sha256=fingerprint(protocol), models=0, executions=0)))


class NoGenerator:
    def __getattr__(self, name):
        raise RuntimeError('ZERO_MODEL_AUDIT_FORBIDS_GENERATION:' + name)


def deny_internet():
    def denied(*args, **kwargs):
        raise RuntimeError('ZERO_MODEL_AUDIT_NETWORK_DISABLED')
    socket.create_connection = denied
    original = socket.socket.connect
    def local_only(sock, address):
        if sock.family != socket.AF_UNIX:
            return denied()
        return original(sock, address)
    socket.socket.connect = local_only


def callable_probe(sandbox, cfg):
    from agent.executor import CodeTaskExecutor
    from agent.retriever import Retriever
    from memory.skill_registry import SkillRegistry
    from memory.negative_memory_store import NegativeMemoryStore
    registry = SkillRegistry(str(OLD / 'base/skills/registry.json'))
    cards = registry.list_all()
    card = next(c for c in cards if c.skill_id == 'skill_humaneval_HumanEval_59_trace_8c0627be')
    code = (REPO / card.code_path).read_text()
    assert sha(code) == card.source_sha256
    bundle = card.executable_dependencies
    validate_bundle(bundle)
    retriever = Retriever(registry=registry, negative_memory_store=NegativeMemoryStore(str(ROOT / 'public_probe/negative_memory.json')))
    visible = retriever._visible_cards()
    row = next(r for r in read(MANIFEST)['tasks'] if r['problem_id']=='HumanEval/59')
    task = task_from_manifest(row)
    task.task_id = 'Audit/HumanEval59_new_parameters'
    task.metadata['public_training_tests'] = [f'assert largest_prime_factor({n}) == {v}'
                                            for n,v in zip([81,77,121,360],[3,11,11,5])]
    task.visible_public_tests = task.test_list = list(task.metadata['public_training_tests'])
    plan = WorkflowPlan(plan_id='postlock_explicit_native_call', task_id=task.task_id,
        planning_mode='direct_skill', selected_skill_id=card.skill_id, steps=[WorkflowStep(
            step_id='call', step_type='call_skill', payload=dict(skill_id=card.skill_id,
                        code_path=str(REPO / card.code_path), entry_point='largest_prime_factor'))])
    executor = CodeTaskExecutor(sandbox=sandbox, max_repairs=0,
                               dynamic_generator=NoGenerator(), oracle_generator=NoGenerator())
    executor.executable_skills_enabled = True
    sandbox.context('native_call_probe','HumanEval_59')
    trace = executor.run(task, plan, mode='dynamic', task_skill_bundle=bundle, task_skill_hash=card.source_sha256)
    assert trace.code_history[-1] == code
    write_json(ROOT / 'public_probe/trace.json', trace.model_dump(mode='json'))
    original = read(OLD / 'base/traces/trace_8c0627be.json')
    first = original['attempts'][0]
    fail_receipts = find_execution('HumanEval/59', first['verifier_feedback'], original['executable_dependencies'], cfg['image'])
    write_json(ROOT / 'public_probe/original_failure.json', dict(source=first['candidate_code'],
        source_sha256=sha(first['candidate_code']), public_feedback=first['verifier_feedback'], execution_receipts=fail_receipts))
    write_json(ROOT / 'public_probe/native_card.json', card.model_dump(mode='json'))
    return dict(task_id='HumanEval/59', native_artifact_exists=True, native_admitted_in_original_11=False,
        artifact_kind='full task program with parameterized top-level function; not strategy text only',
        artifact_ref=card.code_path, artifact_sha256=card.source_sha256, signature=card.signature,
        dependency_bundle_sha256=fingerprint(bundle), status=card.status, direct_eligible=card.direct_eligible,
        compile_rejection_reason=original['compile_rejection_reason'],
        ordinary_retrieval_visible=card.skill_id in {c.skill_id for c in visible},
        callable_capability_verified=trace.success, call_scope='explicit existing CodeTaskExecutor.call_skill with frozen artifact; no promotion, wrapper, or algorithm edit',
        call_probe_trace_ref=relative(ROOT / 'public_probe/trace.json'),
        call_probe_receipt_ref=relative(sandbox.root / 'executions/native_call_probe/HumanEval_59/1/result.json'),
        original_failure_ref=relative(ROOT / 'public_probe/original_failure.json'),
        existing_implementation_needs_teacher=False,
        additional_acquisition_needed=False,
        additional_admission_or_exposure_needed=card.status!='active' or not card.direct_eligible,
        coverage_uncertain=['independent-task support not tested','ordinary Actor autonomous call not demonstrated'],
        proposed_operation_difference='same algorithm/function; only explicit contract, callable binding and independent training admission evidence would be new')


def execute():
    os.chdir(REPO)
    cfg, manifest, protocol = read(CONFIG), read(MANIFEST), read(ROOT / 'protocol.json')
    assert read(ROOT / 'immutable_before.json') == immutable_snapshot(cfg), 'OLD_RUN_CHANGED'
    locked = read(ROOT / 'locked_submissions.json')
    assert fingerprint(locked) == protocol['locked_submissions_sha256']
    assert file_sha(__file__) == protocol['script_sha256'], 'AUDIT_SCRIPT_CHANGED_AFTER_LOCK'
    assert file_sha(cfg['dataset_path']) == manifest['dataset_sha256']
    deny_internet()
    private = ROOT / 'private_scoring'
    private.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(private, 0o700)
    budget = PersistentBudget(ROOT / 'budget.jsonl', run_id='postlock_audit_20261120',
        protocol_hash=fingerprint(protocol), max_calls=0, max_tokens=0, max_tools=32,
        max_cost_microusd=0, token_rate_microusd_per_million=0, tool_cost_upper_microusd=0,
        max_tool_milliseconds=640000, tool_milliseconds_upper=20000, wall_seconds=900)
    sandbox = IsolatedCodeSandbox(image=cfg['image'], budget=budget, root=private)
    wanted = set(protocol['train_ids'])
    # Stream past other dataset records; neither select nor score their test material.
    tasks = {}
    with gzip.open(cfg['dataset_path'],'rt') as src:
        for line in src:
            raw = json.loads(line)
            if raw['task_id'] in wanted:
                tasks[raw['task_id']] = CodeTaskInstance(task_id=raw['task_id'], benchmark='humaneval',
                    prompt=raw['prompt'], entry_point=raw['entry_point'], test=raw['test'], canonical_solution='')
    assert set(tasks) == wanted
    scorer_sha = file_sha(REPO / 'FlowEvo/src/eval/verifier.py')
    results = []
    old_umask = os.umask(0o077)
    try:
        for locked_row in locked:
            result = dict(locked_row)
            tid = result['task_id']
            task = tasks[tid]
            result['scorer_version'] = dict(dataset_sha256=manifest['dataset_sha256'],
                test_sha256=sha(task.test), verifier_sha256=scorer_sha, entry='verify_humaneval', image=cfg['image'])
            if result['source_status'] != 'RESTORED':
                result['full_check_verdict'] = 'SOURCE_OR_DEPENDENCY_UNAVAILABLE'
            else:
                source = (REPO / result['source_ref']).read_text()
                bundle = read(REPO / result['dependencies_ref'])
                assert sha(source) == result['final_source_sha256']
                assert fingerprint(bundle) == result['dependency_bundle_sha256']
                public_row = next(r for r in manifest['tasks'] if r['problem_id']==tid)
                assert task.prompt == public_row['prompt'] and task.entry_point == public_row['entry_point']
                try:
                    tree = ast.parse(task.test)
                    assert any(isinstance(n,ast.FunctionDef) and n.name=='check' for n in tree.body)
                    assert any(isinstance(n,ast.Assert) for n in ast.walk(tree))
                    sandbox.context('full_check',tid.replace('/','_'))
                    with sandbox.bind_dependencies(bundle):
                        feedback = verify_task(task, source, sandbox)
                    folder = private / 'executions/full_check' / tid.replace('/','_') / '1'
                    write_json(folder / 'verifier_feedback.json',feedback.model_dump(mode='json'))
                    receipt = read(folder / 'result.json')
                    verdict = 'FULL_CHECK_PASS' if feedback.passed else 'FULL_CHECK_FAIL'
                    if receipt['status'] in {'EVALUATOR_ERROR','OUTPUT_LIMIT','MEMORY_LIMIT'}:
                        verdict = 'SCORING_ERROR'
                    result.update(full_check_verdict=verdict, execution_receipt=relative(folder / 'result.json'),
                        execution_receipt_sha256=file_sha(folder / 'result.json'), seconds=receipt['seconds'],
                        execution_status=receipt['status'], returncode=receipt['returncode'], timeout=receipt['timeout'])
                    if verdict in {'FULL_CHECK_PASS','FULL_CHECK_FAIL'}:
                        projection = model_projection(public_row, source, passed=feedback.passed,
                            public_feedback=read(REPO / result['public_feedback_ref']), receipt=result['execution_receipt'])
                        write_json(ROOT / 'training_projections' / (tid.replace('/','_')+'.json'), projection)
                except (Exception, BaseException) as exc:
                    # A backend failure is never counted as an algorithm failure.
                    if isinstance(exc, (KeyboardInterrupt,SystemExit)):
                        raise
                    result.update(full_check_verdict='SCORING_ERROR', scoring_error_type=type(exc).__name__)
                    write_json(private / (tid.replace('/','_')+'_error.json'),dict(type=type(exc).__name__, detail=str(exc)))
            results.append(result)
            write_json(ROOT / 'full_check_progress.json', results)
            print(tid, result['full_check_verdict'], flush=True)
    finally:
        os.umask(old_umask)
    probe_root = ROOT / 'public_probe'
    probe_root.mkdir(parents=True, exist_ok=True)
    probe_sandbox = IsolatedCodeSandbox(image=cfg['image'], budget=budget, root=probe_root)
    coverage = callable_probe(probe_sandbox,cfg)
    coverage['full_check_verdict'] = next(r['full_check_verdict'] for r in results if r['task_id']=='HumanEval/59')
    coverage['states'] = ['NATIVE_ARTIFACT_EXISTS']
    if coverage['callable_capability_verified']:
        coverage['states'].append('CALLABLE_CAPABILITY_VERIFIED')
    coverage['states'].append('COVERAGE_UNCERTAIN')
    write_json(ROOT / 'HumanEval59_coverage.json',coverage)
    counts = {s:sum(r['full_check_verdict']==s for r in results) for s in protocol['classes']}
    after = immutable_snapshot(cfg)
    before = read(ROOT / 'immutable_before.json')
    assert before == after, 'OLD_PILOT_MUTATED'
    write_json(ROOT / 'immutable_after.json',after)
    summary = dict(protocol_sha256=fingerprint(protocol), original_run=relative(OLD),
        counts=counts, tasks=results, humaneval59=coverage, budget=budget.snapshot(),
        projection_check=read(ROOT / 'projection_check.json'),
        integrity=dict(old_files_checked=len(before), unchanged=before==after,
                       before_sha256=fingerprint(before), after_sha256=fingerprint(after)),
        transfer_executions=0, model_requests=0,
        native_admitted_full_fail_artifacts=[dict(task_id=r['task_id'], artifact_ids=r['compiled_skill_ids'])
            for r in results if r['compiled_skill_admitted'] and r['full_check_verdict']=='FULL_CHECK_FAIL'],
        limits=['Full checks are finite tests, not a proof of correctness',
                'The call probe is explicit invocation, not independent task support or autonomous Actor reuse'])
    write_json(REPORTS / 'Postlock_Opportunity_Audit.json',summary)
    print(json.dumps(dict(counts=counts, callable=coverage['callable_capability_verified'],
                         ordinary_visible=coverage['ordinary_retrieval_visible'], budget=budget.snapshot()),ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['prepare','execute'], required=True)
    args = parser.parse_args()
    {'prepare':prepare,'execute':execute}[args.phase]()
