"""Execute only the authorized frozen S18-P2 pairs; no learning or registry writes."""
import os,json,time,tempfile
from pathlib import Path
import run_workflow_v2 as e
from experiment_s16b2_source import sender_factory
from failure_evo.contracts import fingerprint,PublicTaskView,PublicFeedback,canonical
from failure_evo.workflow_protocol_v2 import prepare,Limits,delivery
from failure_evo.repair_choice import action_messages,generic_choice
from failure_evo.runtime import Budget
ROOT=e.ROOT;PRE=ROOT/'runs/s18p2_preparation_20261023_01';OUT=ROOT/'runs/s18p2_pairs_20261023_01'
read=e.read;write=e.write;sha=e.sha

def main():
 frozen=read(PRE/'paired_plan.json')
 for p,h in read(PRE/'integrity.json')['files'].items():assert sha(ROOT/p)==h,p
 assert frozen['selected']==['s18_taco-test-425','s18_taco-test-463']
 authorization=read(PRE/'authorization.json')
 assert authorization['allow_real_api'] is True and authorization['paired_plan_sha256']==sha(PRE/'paired_plan.json')
 assert authorization['max_calls']==12 and authorization['api_hard_cap_usd']==.60
 files=[Path(__file__),PRE/'paired_plan.json',ROOT/'scripts/run_workflow_v2.py',ROOT/'scripts/experiment_s16b2_source.py',ROOT/'scripts/learn_reuse30.py',ROOT/'scripts/compare30_workflows.py',e.prior.old.WORKER,e.prior.old.ACCEPTANCE]+list((PRE/'frozen').rglob('*.json'))+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
 plan=dict(run_id=OUT.name,shared_protocol=e.VERSION,model='deepseek-flash',evidence_kind='real_experiment',frozen_files={str(p.relative_to(ROOT)):sha(p) for p in files},budgets={'solve':e.prior.config(12,360,600000)},authorization=authorization['basis'],paired_plan_sha256=sha(PRE/'paired_plan.json'))
 plan['protocol_hash']=fingerprint(plan)
 os.environ.update(DOCKER_CONFIG=str(ROOT/'runs/s12c_functional_20261021_01/docker_public'),DOCKER_HOST='unix:///Users/majiatong/.colima/default/docker.sock')
 runner=e.ExperimentRunner(OUT,plan,sender_factory);(OUT/'tmp').mkdir();tempfile.tempdir=str(OUT/'tmp')
 write(OUT/'authorization.json',dict(run_id=OUT.name,protocol_hash=plan['protocol_hash'],allow_real_api=True,max_calls=12,api_hard_cap_usd=.60,basis=plan['authorization']))
 results={};error=None
 try:
  # Recheck source public behavior before any model request.
  for tid in frozen['selected']:
   packet=read(PRE/'frozen'/tid/'checkpoint.json');cases=read(PRE/'frozen'/tid/'public_cases.json')
   source=runner.judge.run(tid,packet['candidate_code'],cases)
   write(OUT/'acceptance'/f'{tid}.json',source)
   assert not source['passed'] and PublicFeedback.project(source).to_dict()==packet['public_feedback']
  for index,tid in enumerate(frozen['selected']):
   packet=read(PRE/'frozen'/tid/'checkpoint.json');data={'public_cases':read(PRE/'frozen'/tid/'public_cases.json')}
   task=PublicTaskView(**{**packet['task_public'],'public_examples':tuple(canonical(c) for c in packet['task_public']['public_examples'])})
   for arm in (['A','B'] if index%2==0 else ['B','A']):
    started=time.monotonic();local=Budget(max_calls=3,max_tokens=122880,max_tools=60,wall_seconds=600)
    code=packet['candidate_code'];f=packet['public_feedback'];feedback=PublicFeedback(f['status'],f['summary'],tuple(canonical(c) for c in f['public_cases']))
    key=tid+'/'+arm;result={'task':tid,'arm':arm,'steps':[]};results[key]=result
    for attempt in range(3):
     action=('REPAIR_EXISTING' if arm=='A' else 'REGENERATE_FRESH') if attempt==0 else generic_choice(code,feedback,local)
     if action=='NATIVE':break
     try:prepared=prepare(action_messages(action,task,code,feedback),limits=Limits())
     except e.PreflightRejected as exc:
      result['blocked']={'reason':str(exc),'request_state':'NOT_SENT'};break
     if attempt==0:assert prepared.wire==(PRE/'frozen'/tid/(action+'.json')).read_text(),'frozen initial request changed'
     response=runner.transports['solve'].send(prepared,task_budget=local,request_id=key+f'/{attempt}',capability='S18P2-'+action)
     code=delivery(response['text'],response['finish_reason'])['code']
     if local.remaining_seconds<=0:raise RuntimeError('branch wall budget exhausted')
     before=runner.budgets['solve'].snapshot()['tool_calls']
     public=runner.judge.run(tid,code,data['public_cases'])
     used=runner.budgets['solve'].snapshot()['tool_calls']-before;local.tool_calls+=used
     assert local.tool_calls<=60 and local.remaining_seconds>0,'branch limits'
     feedback=PublicFeedback.project(public)
     step={'attempt':attempt,'action':action,'response':response,'code':code,'code_sha256':fingerprint(code),'public':public,'request_sha256':prepared.sha256}
     result['steps'].append(step);write(OUT/'branches'/tid/arm/'result.json',result);runner.save()
     print('STEP',tid,arm,attempt,public['status'],public['tests_passed'],'/',public['tests_run'],'tokens',response['usage']['total_tokens'],flush=True)
     if public['passed']:break
    result.update(final_code=code,public_pass=bool(result['steps'] and result['steps'][-1]['public']['passed']),calls=local.calls,tokens=local.used_tokens,tool_calls=local.tool_calls,online_seconds=time.monotonic()-started)
    write(OUT/'branches'/tid/arm/'result.json',result)
  # Locked all online branches before any external development review.
  write(OUT/'online_lock.json',{k:fingerprint(v) for k,v in results.items()})
  for key,result in results.items():
   data=read(ROOT/'runs/s18_data_freeze_20261023_01/evaluator_only.json')[result['task']]
   before=runner.budgets['solve'].snapshot()['tool_calls'];start=time.monotonic()
   review=runner.judge.run(result['task'],result['final_code'],data['audit_cases'])
   result['review']=review;result['review_seconds']=time.monotonic()-start
   result['review_tools']=runner.budgets['solve'].snapshot()['tool_calls']-before
   assert result['tool_calls']+result['review_tools']<=60
   write(OUT/'branches'/result['task']/result['arm']/'review.json',review)
   print('REVIEW',key,review['tests_passed'],'/',review['tests_run'],flush=True)
 except Exception as exc:
  error={'type':type(exc).__name__,'message':str(exc)};print('STOP',error,flush=True)
 finally:
  runner.save();summary={}
  for key,r in results.items():
   usage=[s['response']['usage'] for s in r['steps']]
   summary[key]={k:r.get(k) for k in ['public_pass','calls','tokens','tool_calls','online_seconds','review_seconds','review_tools','blocked']}
   summary[key].update(input_tokens=sum(u['prompt_tokens'] for u in usage),output_tokens=sum(u['completion_tokens'] for u in usage),estimated_usd=sum((u['prompt_tokens']*.3+u['completion_tokens']*1.2)/1e6 for u in usage),initial_public=r['steps'][0]['public']['tests_passed'] if r['steps'] else None,review_passed=r.get('review',{}).get('tests_passed'),review_total=r.get('review',{}).get('tests_run'))
  write(OUT/'summary.json',{'error':error,'arms':summary,'budget':runner.budgets['solve'].snapshot(),'provider_responses':sum(bool(x.get('raw_response')) for x in runner.transports['solve'].audit),'new_operators':0,'independent_tasks':2,'scope':'P1 prospective checkpoints reused for development pairing; not independent holdout','local_currency_cost':None})
  print('FINISHED',json.dumps(summary),flush=True)
 if error:raise RuntimeError('Stopped; inspect artifacts, no automatic replay')
if __name__=='__main__':main()
