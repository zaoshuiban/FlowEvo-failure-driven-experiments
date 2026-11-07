"""Zero-API acceptance on the actual frozen ten-failure TRAIN input."""
import argparse
import json
from pathlib import Path

from accept_post_pilot50_validator import fixture
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_skill_transfer import SkillLifecycle
from failure_evo.math_stream import save
from failure_evo.math_transfer_launch import TransferBudget
from failure_evo.operator_version_gate import VersionGate
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from launch_math_skill_transfer import execute_train, preflight
from math_candidate_mock import assessment
from run_math_skill_transfer import raw


def acceptance(config, output):
    cfg, schedule, backend, _ = preflight(config)
    output.mkdir(mode=0o700)
    schedule.root = output/'run'
    artifact,_,_,_ = fixture(output/'fixture')
    contract = artifact['contract']
    sources = Path(artifact['solver_path']).read_text()+'\n'+Path(artifact['matcher_path']).read_text()
    operator = dict(artifact['operator_contract'],input_schema=json.loads(contract['parameter_schema']))
    frozen_train = {f['id']:f['task']['problem'] for f in schedule.facts}
    calls = []

    def mock(arm, wire):
        data = json.loads(wire['messages'][-1]['content'])
        assert wire['model']==cfg['model']
        calls.append(arm)
        if arm=='A':
            assert all(frozen_train[e['evidence_id']]==e['problem'] for e in data['evidence'])
            return raw(json.dumps(dict(clusters=[],descriptions=[
                dict(evidence_id=e['evidence_id'],task_structure='fixture',observable_symptom='wrong',
                     possible_cause='unknown',possible_correction='fixture',uncertainty='unverified')
                for e in data['evidence']])))
        if 'hypothesis' in data:
            assert arm in 'BD'
            assert all(x['problem'] in frozen_train.values() for x in data['evidence']['questions'])
            fid = data['learning_evidence_bundle']['evidence'][0]['evidence_id']
            return raw(json.dumps(dict(code=sources,description=json.dumps(contract),
                                      applicability=json.dumps(dict(operator,source_evidence=[fid])))))
        fid=data['failure_id']
        assert frozen_train[fid]==data['problem'] and data['correct'] is False
        return raw(json.dumps(dict(kind='NON_EXECUTABLE_EXPERIENCE' if arm=='C' else 'VERIFIER_CANDIDATE',
                                  subtask='fixture sum',error_location='fixture',error_type='fixture',
                                  observable_evidence='fixture',correction='fixture',unknown_conditions='fixture',
                                  verification_scope='NONE' if arm=='C' else 'OBJECTIVE_VALUE',
                                  assessment=assessment([fid],role='DIAGNOSTIC',
                                      decision='NEEDS_SPECIFICATION' if arm=='C' else 'GENERATE'))))

    # Simulate a host interruption after an already settled prefix, before a new arm starts.
    from unittest.mock import patch
    from failure_evo.math_skill_transfer import SingleFailureTrainHandler
    original = SingleFailureTrainHandler.__call__
    def interrupt(self,job,fact,resuming):
        if job['sequence']==2 and job['arm']=='B':
            raise InterruptedError('host checkpoint interruption')
        return original(self,job,fact,resuming)

    with patch.object(SingleFailureTrainHandler,'__call__',interrupt):
        try:
            execute_train(cfg,schedule,backend,mock_sender=mock)
        except InterruptedError:
            pass
        else:
            raise AssertionError('interruption was not exercised')
    results = execute_train(cfg,schedule,backend,mock_sender=mock)
    before = len(calls)
    assert len(results)==40 and execute_train(cfg,schedule,backend,mock_sender=mock)==results
    assert len(calls)==before
    for arm in 'BCD':
        entries=[x['result'] for x in results if x['job']['arm']==arm]
        if arm=='C':
            assert all(x['status']=='TEXT_ONLY' and 'artifact' not in x for x in entries)
        else:
            assert all(x['status']=='UNVERIFIED' and x['source_diagnostic']['status']=='EXECUTED_UNVERIFIED'
                       for x in entries),[x['status'] for x in entries]
            if arm=='D':
                assert all(x['dev_comparison_status']=='PENDING_INDEPENDENT_DEV_REVIEW' for x in entries)
            registry=VersionGate(schedule.root/arm/'registry.jsonl')
            try:
                SkillLifecycle(arm,schedule.root/arm).freeze([entries[0]['artifact']],registry,'test-fixture')
            except PermissionError:
                pass
            else:
                raise AssertionError('unverified artifact was publishable')
            assert not any(r['kind'] in ('MATH_EXPERIMENTAL','V3_TRIAL_AUTHORIZATION') for r in registry.events.records())
    limits=TransferBudget(schedule.root,'engineering:'+cfg['run_id'],fingerprint(cfg))
    try:
        limits.allocate(schedule.root/'overflow.jsonl','TRAIN','C',1)
    except BudgetExhausted:
        pass
    else:
        raise AssertionError('arm cap was bypassed')
    pending=limits.allocate(schedule.root/'unknown.jsonl','TRAIN','D',1)
    key=pending.reserve(100,20)
    pending.settle(key)
    try:
        execute_train(cfg,schedule,backend,mock_sender=mock)
    except RunUnhealthy:
        assert len(calls)==before
    else:
        raise AssertionError('unknown did not block')
    journal=EvidenceStore(schedule.root/'train.jsonl').records()
    save(output/'receipt.json',dict(config_sha256=fingerprint(cfg),passed=True,paid_requests=0,
                                    mock_calls=before,settled_jobs=len(results),
                                    journal_tail_sha256=journal[-1]['record_hash']))
    print(json.dumps(dict(settled_jobs=len(results),mock_calls=before,paid_requests=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    acceptance(args.config,args.output)
