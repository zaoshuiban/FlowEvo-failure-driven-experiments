"""Read-only A3 source replay and diagnostic copies; no model or environment calls."""
import argparse
from pathlib import Path
from dataclasses import replace
from time import time
import json
import shutil
from alfworld_.applicability_semantic_feedback import instrument,decode_trace,category
from failure_evo.contracts import canonical,fingerprint
from failure_evo.math_stream import read,sha
import run_alfworld_applicability_multicandidate as B

OLD=B.ROOT/'runs/alfworld_route_a_a3_preparation_20261113_01'


def archived_hashes():return {str(p):sha(p) for p in OLD.rglob('*') if p.is_file()}


def card_for(root,source,template,registry,tag):
    adapted=B.worker_artifact(source);check=B.static_check_detailed(adapted)
    if not check['passed']:raise ValueError(check)
    path=root/(tag+'.py');B.pilot.save_exact_source(path,adapted)
    version=fingerprint([sha(path),tag,'DIAGNOSTIC_ONLY'])
    c=replace(template,version=version,operator_id=version[:16],artifact_path=str(path),artifact_sha256=sha(path))
    if not registry._rows(c):registry.register(c,time())
    return c


def setup(root,tools):
    root.mkdir(parents=True,exist_ok=True)
    evidence=root/'failures.jsonl'
    if not evidence.exists() or evidence.stat().st_size==0:shutil.copyfile(OLD/'failures.jsonl',evidence)
    if sha(evidence)!=sha(OLD/'failures.jsonl'):raise PermissionError('diagnostic evidence import differs')
    for original in (OLD/'failure_artifacts').glob('*.py'):
        target=root/'failure_artifacts'/original.name;target.parent.mkdir(exist_ok=True)
        if not target.exists():shutil.copyfile(original,target)
        if sha(target)!=sha(original):raise PermissionError('evidence artifact import differs')
    plan=dict(run_id='diagnostic:'+root.name,max_calls=0,max_tokens=0,max_cost_microusd=0,worker_calls=tools)
    B.pilot.commit(root/'protocol.json',plan)
    budget=B.create_accounts(root,plan);backend=B.FrozenLinuxBackend(image=B.IMAGE,worker_script=B.WORKER)
    runner=B.EnvironmentPolicyRunner(backend,root/'worker.jsonl',budget)
    registry=B.FailureOperatorRegistry(root/'registry.jsonl',B.FailureEvidenceStore(root/'failures.jsonl'))
    return plan,runner,registry


def replay(root):
    before=archived_hashes();B.pilot.commit(root/'historical_sha256.json',before)
    roles=read(OLD/'roles.private.json');old=read(OLD/'result.json')
    byid={fingerprint(r['sample_id']):r for rs in roles.values() for r in rs}
    plan,runner,registry=setup(root,2000)
    backend=runner.backend.manifest()
    if backend!=read(OLD/'protocol.json')['worker']:raise PermissionError('Worker drift')
    traces=[]
    for a in old['attempts']:
        template=B.FailureOperator.from_dict(a['registration']['card'])
        original=card_for(root,a['code'],template,registry,a['candidate_id']+'_v'+str(a['revision'])+'_original')
        instrumented,branches=instrument(a['code'])
        diagnostic=card_for(root,instrumented,template,registry,a['candidate_id']+'_v'+str(a['revision'])+'_trace')
        for saved in a['train']+a['validation']:
            row=byid[saved['sample_id']];ctx=dict(row['candidate_context'],state={})
            decision=B.learned_decision(runner,original,ctx)
            if decision['status']!=saved['actual'] or decision['reason']!=saved['reason']:raise PermissionError('original replay differs')
            located=B.learned_decision(runner,diagnostic,ctx);trace=decode_trace(located,branches,saved)
            if not trace['decision_preserved']:raise PermissionError('instrumentation changed decision')
            traces.append(dict(candidate=a['candidate_id'],version='v'+str(a['revision']),candidate_version=a['version'],
                sample_id=saved['sample_id'],split=saved['role'],expected_label=saved['expected'],predicted_label=decision['status'],
                reason=decision['reason'],first_rejecting_branch=trace.get('reached_return'),trace=trace,exception=None,
                category=category(saved,trace),game_sha256=row['game_sha256'],original_execution_id=decision['execution_id'],
                diagnostic_execution_id=located['execution_id']))
        B.pilot.commit(root/(a['candidate_id']+'_v'+str(a['revision'])+'_traces.json'),[r for r in traces if r['candidate_version']==a['version']])
        print(a['candidate_id'],a['revision'],'replayed',flush=True)
    path=root/'A3b_Decision_Trace.jsonl'
    text=''.join(canonical(r)+'\n' for r in traces)
    if path.exists() and path.read_text()!=text:raise PermissionError('trace drift')
    path.write_text(text)
    assert archived_hashes()==before
    return B.pilot.commit(root/'replay_summary.json',dict(status='REPLAY_MATCHED',decisions=len(traces),worker_calls=runner.budget.tool_calls,
        history_unchanged=True,paid_requests=0,environment_steps=0,scope='DIAGNOSTIC_ONLY',trace_sha256=sha(path)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();replay(a.output.resolve())
