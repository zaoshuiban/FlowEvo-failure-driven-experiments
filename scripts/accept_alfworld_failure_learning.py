"""Engineering fixture only: Mock induction/code, actual ALFWorld and Docker execution."""
import argparse
import json
from pathlib import Path

from alfworld_.failure_learning import VERSION,static_check
from alfworld_.learning_stream import LearningStream
from alfworld_.learning_runtime import execute_episode
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_registry import FailureOperator
from failure_evo.math_stream import read,save,sha
from run_alfworld_failure_learning import load

# Fixed MOCK response. This handwritten policy is an engineering fixture only.
FIXTURE_SOURCE="""import re
def environment_operator(c):
    goal=c['goal'].lower()
    m=re.fullmatch(r'put (?:a|an|some) ([a-z]+) (?:in|on) ([a-z]+)\\.',goal)
    if not m:
        return {'status':'declined','state':{},'reason':'fixture scope'}
    obj,dest=m.groups()
    state=c['state']
    visited=state.get('visited',[])
    holding=state.get('holding',False)
    for a in c['admissible_commands']:
        if a.startswith('move '+obj+' ') and re.search(' to '+dest+r' \\d+$',a):
            return {'status':'applied','action':a,'state':{'visited':visited,'holding':False},'reason':'fixture'}
    for a in c['admissible_commands']:
        if a.startswith('take '+obj+' '):
            return {'status':'applied','action':a,'state':{'visited':visited,'holding':True},'reason':'fixture'}
    for a in c['admissible_commands']:
        if a.startswith('open '):
            return {'status':'applied','action':a,'state':state,'reason':'fixture'}
    for a in c['admissible_commands']:
        if holding and a.startswith('go to '+dest+' '):
            return {'status':'applied','action':a,'state':state,'reason':'fixture'}
    for a in c['admissible_commands']:
        if a.startswith('go to ') and a not in visited:
            return {'status':'applied','action':a,'state':{'visited':visited+[a],'holding':holding},'reason':'fixture'}
    return {'status':'declined','state':state,'reason':'fixture exhausted'}
"""


def response(text):
    return dict(model='deepseek-flash',id='MOCK',choices=[dict(message=dict(content=text),finish_reason='stop')],
                usage=dict(prompt_tokens=100,completion_tokens=100,total_tokens=200))


def accept(prepared,output,exposed_protocol=None):
    plan,backend=load(prepared)
    frozen_hash=fingerprint(plan)
    plan=json.loads(json.dumps(plan))
    if exposed_protocol is not None:
        exposed=read(exposed_protocol)
        # Explicitly supplied already-exposed engineering games only; never use
        # the new paid Run's future/Gate rows for this reduced Mock rehearsal.
        for row in exposed['future_tasks']+[r for shard in exposed['gate_shards'] for r in shard]:
            p=Path(plan['data_root'])/row['game']
            if sha(p)!=row['game_sha256'] or sha(p.parent/'traj_data.json')!=row['trajectory_sha256']:
                raise PermissionError('exposed fixture content changed')
        plan['future_tasks']=exposed['future_tasks']
        plan['gate_shards']=exposed['gate_shards']
    # Reduce only the engineering fixture, leaving the real frozen plan unchanged.
    plan['run_id']='engineering-fixture'
    plan['future_tasks']=[r for r in plan['future_tasks'] if r['task_type']=='pick_and_place_simple'][:1]
    gates=[r for shard in plan['gate_shards'] for r in shard if r['task_type']=='pick_and_place_simple']
    plan['gate_shards']=[gates,[]]
    assert len(gates)==2 and len(plan['future_tasks'])==1
    calls=[]
    def sender(channel,wire):
        calls.append(channel)
        data=json.loads(wire['messages'][-1]['content']) if channel=='learning' else None
        if channel=='action':
            return response('Think: inspect.\nAct: look')
        assert 'expert_plan' not in json.dumps(data) and 'gate_shards' not in data
        if 'hypothesis' in data:
            return response(json.dumps(dict(code=FIXTURE_SOURCE,description='MOCK fixture',
                                            applicability='MOCK fixture only')))
        return response(json.dumps(dict(decision='PROPOSE',operator_category='MOCK',
           common_failure='fixture only',root_cause_hypothesis='unverified',
           executable_suggestion='fixture response',applicability='fixture scope',
           exclusions='unsupported objectives',uncertainties='engineering only')))
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(mode=0o700)
    stream=LearningStream(output,plan,backend,engineering=True,sender=sender)
    stream.ingest_history(Path(plan['source_run']))
    assert len(stream.store.visible(__import__('time').time(),stream.run_id))==20
    public={r['payload']['event_id']:r['payload']['public'] for r in stream.views.records()}
    ids=[eid for eid,p in public.items() if p['goal']=='put some vase on safe.']
    assert len(ids)==1
    stream.select_evidence=lambda fresh:ids
    assert static_check(FIXTURE_SOURCE)['passed']
    assert not static_check('import os\n'+FIXTURE_SOURCE)['passed']
    stream.run()
    summary=stream.report()
    save(output/'fixture_summary.json',summary)
    assert summary['authorized']==1 and summary['future_operator_actions']>0,summary
    assert summary['G_success']==0 and summary['F_success']==1,summary
    count=len(calls)
    stream.run()
    assert len(calls)==count,'resume repeated model calls'
    # Same artifact is forbidden outside an explicitly engineering runtime.
    card=next(FailureOperator.from_dict(r['payload']['card']) for r in stream.registry.events.records()
              if r['kind']=='SHADOW_REGISTERED')
    from alfworld_.learning_runtime import PolicyGenerator
    from alfworld_.generator import AlfWorldGenerator
    guard=PolicyGenerator(AlfWorldGenerator(stream.client('forbidden')),stream.registry,stream.runner,
            stream_id=stream.run_id,experiment_id=plan['run_id'],task_id='future-fixture',sequence=2,
            events=stream.events,validation_card=card,engineering=False)
    try:
        guard.step('goal','observation',['look'])
    except PermissionError:
        pass
    else:
        raise AssertionError('Mock policy escaped engineering')
    save(output/'ACCEPTANCE.json',dict(scope='ENGINEERING_ONLY',passed=True,paid_requests=0,
                                      actual_environment=True,actual_docker=True,fixture_summary=summary))
    save(prepared/'ENGINEERING_ACCEPTANCE.json',dict(scope='ENGINEERING_ONLY_EXPOSED_FIXTURES',
        protocol_sha256=frozen_hash,passed=True,paid_requests=0,
        acceptance_sha256=sha(output/'ACCEPTANCE.json'),
        acceptance_script_sha256=sha(Path(__file__))))
    print(json.dumps(dict(scope='ENGINEERING_ONLY',passed=True,summary=summary),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--prepared',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--exposed-protocol',type=Path)
    args=p.parse_args()
    accept(args.prepared,args.output,args.exposed_protocol)
