"""Stage-one real isolated execution; engineering fixtures are NOT natural gains.
No model calls, no registration/promotion, no generated source edits.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo import PersistentBudget
from failure_evo.contracts import PublicTaskView, PublicFeedback, fingerprint
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.failure_events import FailureEvidenceStore, checked_public_feedback
from failure_evo.plugin import FailureLearningPlugin
from failure_evo.runtime import Budget
from failure_evo.checkpoint_evaluator import CheckpointEvaluator, resolve_action
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
SOURCE=ROOT/'runs/s12b3_revision_20261021_01'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


class EvaluationOnlyRegistry:
    """In-memory fixture to exercise host invoke(), NOT a production authorization.

    No evidence, gate, snapshot publication or registry events are manufactured.
    Real Shadow registry exclusion is checked separately.
    """
    @staticmethod
    def valid(card, at):return sha(Path(card.artifact_path))==card.artifact_sha256


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--image',required=True);args=ap.parse_args()
    run=ROOT/args.run
    if (run/'result.json').exists() or (run/'budget.jsonl').exists():raise FileExistsError('fresh acceptance run required')
    registered=json.loads((SOURCE/'shadow_registry.jsonl').read_text().splitlines()[0])['payload']['card']
    card=FailureOperator.from_dict(registered)
    assert sha(Path(card.artifact_path))==card.artifact_sha256
    protocol=dict(run_id=run.name,image=args.image,artifact_sha256=card.artifact_sha256,
        evidence_scope='engineering-functional-acceptance-only',new_model_calls=0,
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),WORKER]+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))},
        acceptance_sha256=sha(run/'worker_acceptance.json'),card=registered)
    protocol['protocol_hash']=fingerprint(protocol);write(run/'protocol.json',protocol)
    budget=PersistentBudget(run/'budget.jsonl',run_id=run.name,protocol_hash=protocol['protocol_hash'],
        max_calls=0,max_tokens=0,max_tools=180,max_cost_microusd=0,token_rate_microusd_per_million=1200000,
        tool_cost_upper_microusd=0,max_tool_milliseconds=1800000,tool_milliseconds_upper=10000,wall_seconds=1800)
    evaluator=CheckpointEvaluator(ROOT,budget,image=args.image,worker_script=WORKER,acceptance_path=run/'worker_acceptance.json')
    result=dict(status='RUNNING',direct=[],host=[],historical={},new_model_calls=0,
        experimental_authorizations=0,scope='engineering fixtures, not independent gate or online gain')
    def save():
        result['budget']=budget.snapshot();write(run/'result.json',result)
    save()
    # Genuine public executions on deliberately simple engineering programs.
    cases=[dict(case_id='engineering-echo-'+str(i),input=x+'\n',expected=x+'\n',comparison='whitespace_token_exact') for i,x in enumerate(['7','19'])]
    good='print(input())\n';bad='print(0)\n'
    verdict_good=evaluator.judge(good,cases,3);verdict_bad=evaluator.judge(bad,cases,3)
    assert verdict_good['outcome']=='passed' and verdict_bad['outcome']=='failed'
    result['engineering_program_checks']=dict(good=verdict_good,bad=verdict_bad)
    def feedback(v):
        return checked_public_feedback(dict(visibility='public',status='PUBLIC_PASS' if v['outcome']=='passed' else 'WRONG_ANSWER',tests_run=v['tests_run'],tests_passed=v['tests_passed']))
    passed=feedback(verdict_good);failed=feedback(verdict_bad);unknown=PublicFeedback('UNKNOWN');empty=PublicFeedback('NO_COMPLETE_CODE')
    task=PublicTaskView.project(dict(problem_id='engineering-echo',prompt='Echo the input integer.'))
    def state(rows,current='',current_fb=empty):
        plugin=FailureLearningPlugin(EvaluationOnlyRegistry(),None,card.evidence_fingerprint,stream_id=run.name,synthetic=True)
        plugin.current=dict(task=task,snapshot=SimpleNamespace(cards=(card,),snapshot_id='ENGINEERING_ONLY_NOT_AUTHORIZATION'),ledger=[],observations=[],hooks=[],attempted=set())
        for code,stage,fb in rows:plugin.observe(code,stage,fb,{'finish_reason':'stop'},time.time())
        plugin.observe(current,'l2b',current_fb,{'finish_reason':'length'},time.time())
        return plugin
    def payload(plugin,current='',current_fb=empty):
        # Same fields as production invoke; later host tests capture actual invoke payloads.
        return dict(task_public=plugin.current['task'].to_dict(),candidate_code=current,public_feedback=current_fb.to_dict(),
            generation_metadata=plugin.current['ledger'][-1]['generation_metadata'],candidate_ledger=copy.deepcopy(plugin.current['ledger']),
            remaining_budget=Budget(max_calls=0).snapshot(),hook='before_native_retry',checkpoint_id='engineering',registry_snapshot_id='ENGINEERING_ONLY_NOT_AUTHORIZATION')
    base=payload(state([(good,'l2a',passed)]))
    direct=[('verified_previous',base,'applied','c1'),
        ('structure_only',payload(state([(good,'l2a',unknown)])),'declined',None),
        ('failed_public',payload(state([(bad,'l2a',failed)])),'declined',None),
        ('no_history',dict(base,candidate_ledger=[]),'declined',None),
        ('current_complete',payload(state([(good,'l2a',passed)],good,passed),good,passed),'declined',None),
        ('missing_ledger',{k:v for k,v in base.items() if k!='candidate_ledger'},'declined',None),
        ('invalid_ledger_type',dict(base,candidate_ledger={ }),'declined',None),
        ('invalid_rows',dict(base,candidate_ledger=[None,{},dict(code=good)]),'declined',None),
        ('missing_public_feedback',dict(base,public_feedback=None),'declined',None),
        ('later_stage_only',payload(state([(good,'l4',passed)])),'applied','c1'),
        ('mixed_stage_order',payload(state([(good,'l2b',passed),(good,'l4',passed)])),'applied','c1'),
        ('same_stage_latest',payload(state([(good,'l2a',passed),(good,'l2a',passed)])),'applied','c2')]
    for name,context,expected,selected in direct:
        raw=evaluator._charged('operator-direct',lambda:evaluator.runner.run(card,context,1))
        proposed=resolve_action(raw,context.get('candidate_ledger',[]) if isinstance(context.get('candidate_ledger',[]),list) else [])
        ok=raw.get('status')==expected and (selected is None or raw.get('selected_candidate_id')==selected)
        public=evaluator.judge(proposed,cases,3) if proposed is not None else None
        if public is not None:ok=ok and public['outcome']=='passed'
        result['direct'].append(dict(name=name,passed=ok,payload=context,operator_result=raw,public_revalidation=public,expected=expected))
        save();print(name,raw.get('status'),ok,flush=True)
    # Production host invoke, using an explicitly synthetic in-memory admission fixture.
    for name,mode in [('host_applied','pass'),('host_public_failure','fail'),('host_public_unavailable','unavailable'),('host_evaluator_exception','exception'),('host_budget_insufficient','budget'),('host_worker_exception','worker_exception'),('host_wrong_id','wrong_id')]:
        plugin=state([(good,'l2a',passed)]);captured=[];host_budget=Budget(max_calls=0,max_tools=2 if mode=='budget' else 10,wall_seconds=30)
        class TracedRunner:
            def run(self,c,p,t):
                captured.append(copy.deepcopy(p))
                if mode=='worker_exception':raise RuntimeError('engineering injected worker outage')
                if mode=='wrong_id':return {'status':'applied','selected_candidate_id':'not-in-ledger'}
                return evaluator._charged('operator-host',lambda:evaluator.runner.run(c,p,t))
        plugin.runner=TracedRunner();public_calls=[]
        def judge(t,code):
            if mode=='exception':raise RuntimeError('engineering injected host checker outage')
            if mode=='unavailable':return dict(visibility='public',status='UNKNOWN',tests_run=0,tests_passed=0)
            selected_cases=cases if mode=='pass' else [dict(c,expected='0\n') for c in cases]
            v=evaluator.judge(code,selected_cases,3);public_calls.append(v)
            return dict(visibility='public',status='PUBLIC_PASS' if v['outcome']=='passed' else 'WRONG_ANSWER',tests_run=v['tests_run'],tests_passed=v['tests_passed'])
        applied=plugin.invoke('before_native_retry',name,'l2b','',empty,host_budget,judge,time.time())
        final_code=applied['code'] if applied else ''
        ok=(applied is not None and final_code==good) if mode=='pass' else applied is None and final_code==''
        result['host'].append(dict(name=name,passed=ok,host_applied=applied is not None,native_fallback=applied is None,original_preserved=final_code=='',audit=plugin.current['hooks'],payloads=captured,public_checks=public_calls,
            injected_fault=mode if mode in ('worker_exception','wrong_id','exception','budget','unavailable') else None,
            admission='in-memory engineering fixture; no Experimental authorization'))
        save();print(name,ok,flush=True)
    # Real saved witness, re-evaluated solely against frozen public samples.
    checkpoint=json.loads((ROOT/'runs/s12a2_20261021_01/data/lcb_atcoder_abc371_f.checkpoint.json').read_text())
    rows=[];checks=[]
    for row in checkpoint['candidate_ledger']:
        path=ROOT/row['source_path'];assert sha(path)==row['sha256'];code=path.read_text()
        v=evaluator.judge(code,checkpoint['public_cases'],3)
        checks.append(dict(event_id=row['event_id'],code_sha256=row['sha256'],public=v))
        rows.append((code,row['stage'],feedback(v) if v['outcome'] in ('passed','failed') else unknown))
    historical=state(rows[:-1]);historical.current['task']=PublicTaskView.project(checkpoint['task_public'])
    context=payload(historical)
    raw=evaluator._charged('operator-historical',lambda:evaluator.runner.run(card,context,1))
    proposed=resolve_action(raw,context['candidate_ledger'])
    recheck=evaluator.judge(proposed,checkpoint['public_cases'],3) if proposed is not None else None
    result['historical']=dict(public_checks=checks,operator_result=raw,public_revalidation=recheck,
        payload=context,scope='new public-test reconstruction of historical checkpoint, not observed online continuation',natural_online_gain=False)
    registry=FailureOperatorRegistry(SOURCE/'shadow_registry.jsonl',FailureEvidenceStore(ROOT/'runs/s12a2_20261021_01/data/discovery_facts.jsonl'))
    snapshot=registry.snapshot(stream_id=run.name,task_index=1,experiment_id='',at=time.time())
    result['production_registry_shadow_excluded']=not any(c.operator_id==card.operator_id for c in snapshot.cards)
    result['engineering_acceptance']=all(r['passed'] for r in result['direct']+result['host'])
    result['status']='PASS_ENGINEERING_ONLY' if result['engineering_acceptance'] else 'FAIL_ENGINEERING'
    result['artifact_unchanged']=sha(Path(card.artifact_path))==card.artifact_sha256
    save();print(result['status'],flush=True)

if __name__=='__main__':main()
