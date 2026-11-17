"""Real Worker/TextWorld acceptance with a labelled non-recovery fixture. Zero API."""
import argparse,time
from pathlib import Path
from copy import deepcopy
import run_alfworld_container_b4 as R
from test_alfworld_container_information import response,proposal
P=R.P;E=R.E;D=R.D
CODE="""def environment_operator(c):
 if c['state'].get('observed'):
  return {'status':'declined','state':{},'reason':'ENGINEERING_ONLY_DONE'}
 if 'look' in c['admissible_commands']:
  return {'status':'applied','action':'look','state':{'observed':True},'reason':'ENGINEERING_ONLY_OBSERVATION'}
 return {'status':'declined','state':{},'reason':'ENGINEERING_ONLY_UNAVAILABLE'}
"""

def run(preparation,out):
    p=P.read(preparation/'protocol.json');P.verify_history(p['historical_sha256']);out.mkdir(mode=0o700,parents=True,exist_ok=True)
    P.commit(out/'protocol.json',dict(parent_sha256=P.fingerprint(p),fixture_sha256=P.fingerprint(CODE),paid_requests=0,learned_candidates=0))
    row=E.assessment(out,'fixture',dict(raw_response=response(proposal(CODE))));row.update(cell='S11',index=0)
    if row['status']!='STATIC_PASS':raise RuntimeError('fixture static')
    budget=R.account(out,p);ev=R.real_evaluate(row,p,p['train']['S11'],'TRAIN',budget,out)
    before={str(f):P.sha(f) for f in out.glob('*.jsonl')}
    assert R.real_evaluate(row,p,p['train']['S11'],'TRAIN',budget,out)==ev
    assert before=={str(f):P.sha(f) for f in out.glob('*.jsonl')}
    backend=E.B.B.FrozenLinuxBackend(image=E.B.IMAGE,worker_script=E.B.WORKER)
    runner=P.EnvironmentPolicyRunner(backend,out/'worker.jsonl',budget)
    registry=P.FailureOperatorRegistry(out/'registry.jsonl',P.FailureEvidenceStore(out/'evidence.jsonl'))
    card=R.register(row,p,out,registry)
    context=P.start_state(p['train']['S11'][0]['origin'],p)[1]
    first=runner.run(card,context);used=budget.tool_calls;assert runner.run(card,context)==first and budget.tool_calls==used
    altered=deepcopy(context);altered['state']={'observed':True};second=runner.run(card,altered)
    assert second['status']=='declined' and first['status']=='applied'
    assert budget.tool_calls==used+1
    nolegal=deepcopy(context);nolegal['admissible_commands']=[];assert runner.run(card,nolegal)['status']=='declined'
    assert registry.state(card)['permission']=='shadow'
    result=dict(status='PASS_ENGINEERING_ONLY',sources=len(ev['sources']),metrics=ev['metrics'],
        settled_environment_reentry_no_repeat=True,same_context_cache_reuse=True,changed_context_cache_separated=True,
        runtime_action_and_refusal=True,permission='shadow',paid_requests=0,new_games=0,learned_candidates=0,budget=budget.snapshot())
    P.commit(out/'result.json',result);print(P.canonical(result))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--preparation',type=Path,required=True);a.add_argument('--output',type=Path,required=True);x=a.parse_args();run(x.preparation.resolve(),x.output.resolve())
