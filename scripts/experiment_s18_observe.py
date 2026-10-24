"""Authorized observation only. No generation, pairing, or reserve execution."""
import os,json,time,tempfile,hashlib,ast
from pathlib import Path
import run_workflow_v2 as e
from experiment_s16b2_source import sender_factory
from failure_evo.contracts import fingerprint,PublicFeedback,canonical
from failure_evo.workflow_protocol_v2 import program_observation,prepare,Limits
from failure_evo.repair_choice import action_messages
from failure_evo.contracts import PublicTaskView
ROOT=e.ROOT;DATA=ROOT/'runs/s18_data_freeze_20261023_01';OUT=ROOT/'runs/s18_observe_20261023_01'

def main():
 proposal=e.read(DATA/'budget_proposal.json');manifest=e.read(DATA/'manifest.json')
 for f,h in manifest['files'].items():assert e.sha(ROOT/f)==h,f
 tasks=e.read(DATA/'observation_tasks.json');assert len(tasks)==20 and all(t['role']=='observation' and 'audit_cases' not in t for t in tasks)
 assert not {t['task_id'] for t in tasks}&{t['task_id'] for t in e.read(DATA/'reserve_tasks.json')}
 files=[Path(__file__),ROOT/'scripts/run_workflow_v2.py',ROOT/'scripts/learn_reuse30.py',ROOT/'scripts/compare30_workflows.py',ROOT/'scripts/experiment_s16b2_source.py',DATA/'observation_tasks.json',DATA/'evaluator_only.json',DATA/'budget_proposal.json',e.prior.old.WORKER,e.prior.old.ACCEPTANCE]+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
 cfg=e.prior.config(100,2400,5000000)
 plan={'run_id':OUT.name,'shared_protocol':e.VERSION,'operator_representation':'repair-choice-json-v1','model':'deepseek-flash','evidence_kind':'real_experiment','frozen_files':{str(p.relative_to(ROOT)):e.sha(p) for p in files},'budgets':{'solve':cfg},'per_task':proposal['per_task'],'proposal_hash':e.sha(DATA/'budget_proposal.json'),'authorization':'User explicitly authorized twenty frozen observation tasks, <=100 model requests and $5; no generation, no pairing, no reserve solving.','funnel_policy':'prefix only truth; task-end native costs separate; preflight both A/B for delivered candidates; savings potential is a hypothesis, not a measured saving','stop':'unknown send, infrastructure failure or frozen integrity mismatch stops; no automatic retry of run'}
 plan['protocol_hash']=fingerprint(plan)
 os.environ.update(DOCKER_CONFIG=str(ROOT/'runs/s12c_functional_20261021_01/docker_public'),DOCKER_HOST='unix:///Users/majiatong/.colima/default/docker.sock')
 timings=[]
 def factory(channel):
  actual=sender_factory(channel)
  def send(wire):
   row={'started_at':time.time(),'request_hash':hashlib.sha256(wire).hexdigest()};timings.append(row)
   try:return actual(wire)
   finally:row['finished_at']=time.time();e.write(OUT/'request_timings.json',timings)
  return send
 runner=e.ExperimentRunner(OUT,plan,factory);(OUT/'tmp').mkdir();tempfile.tempdir=str(OUT/'tmp')
 e.write(OUT/'authorization.json',{'run_id':OUT.name,'protocol_hash':plan['protocol_hash'],'max_calls':100,'max_api_usd':5,'authorized':True,'scope':plan['authorization']})
 e.write(OUT/'observation_tasks.json',tasks)
 e.write(OUT/'initial_state.json',{'failure_facts':0,'callable_rules':0,'success_library_entries':0})
 results={};facts=[];error=None;public_logs={}
 # Instrument evaluator only, not policy/controller behavior.
 def evaluator_factory(task):
  def evaluate(public,code):
   start=time.time();value=runner.judge.run(task['task_id'],code,task['public_cases'])
   public_logs.setdefault(task['task_id'],[]).append({'at':time.time(),'started_at':start,'code_sha256':hashlib.sha256(code.encode()).hexdigest(),'result':value})
   e.write(OUT/'public_checks'/f"{task['task_id']}.json",public_logs[task['task_id']]);return value
  return evaluate
 runner.evaluator_factory=evaluator_factory
 try:
  # Basic current real Worker availability; acceptance already bound by hashes.
  probe=runner.judge.run('engineering_probe','print(2)',[{'input':'','expected':'2','comparison':'tokens','scorer':'s1'}]);assert probe['passed']
  e.write(OUT/'worker_probe.json',probe)
  for index,task in enumerate(tasks,1):
   before=runner.budgets['solve'].snapshot();start=time.time()
   result=runner.solve('F',task);results[task['task_id']]=result
   rows=[r for r in runner.transports['solve'].audit if r['request_id'].startswith('F/'+task['task_id']+'/') and r.get('usage')]
   assert not result.get('hook_events'),'empty cold library must never intervene'
   if any(r['status']=='UNKNOWN' for r in runner.transports['solve'].audit):raise RuntimeError('unknown provider result stops run')
   bad=[r for r in result['events'] if r.get('error')]
   if bad and any(r.get('request_state')!='NOT_SENT' for r in bad):raise RuntimeError('controller/evaluator infrastructure failure; stop')
   e.write(OUT/'task_metrics'/f"{task['task_id']}.json",{'index':index,'started_at':start,'ended_at':time.time(),'before':before,'after':runner.budgets['solve'].snapshot(),'preflight_blocks':bad})
   # Store prefix evidence; source-time timestamps kept distinct from admission time.
   ledger=result.get('candidate_ledger',[])
   for n,event in enumerate(result['events']):
    if 'code' not in event:continue
    f=event['public_feedback'];code=event['code'];obs=program_observation(code)
    feedback=PublicFeedback(f['status'],f['summary'],tuple(canonical(c) for c in f['public_cases']))
    record=next((r for r in ledger if r['stage']==event['stage']),{})
    checks=next((r for r in public_logs.get(task['task_id'],[]) if r['code_sha256']==event['code_sha256']),None)
    at=checks['at'] if checks else record.get('at',start)
    fact=runner.stores['F'].record(stream_id=OUT.name,task_id=task['task_id'],family_id='unclassified_public_failure',stage=event['stage'],code=code,feedback=feedback,observed_at=at,available_from=time.time(),finish_reason=record.get('generation_metadata',{}).get('finish_reason','unknown'))
    dual=False;diagnosis=None
    # Conservative operational completeness: syntax plus actual executed checks,
    # with no unresolved names/entry-only fragments. Not a correctness proof.
    complete=obs['structural_status']=='STRUCTURAL_PASS' and bool(checks) and not obs.get('definitions_and_imports_only')
    if complete and checks and any(c.get('exception_class') in ('NameError','IndentationError') for c in checks['result'].get('cases',[])):complete=False
    remaining=5-event['budget']['calls']
    if fact and complete and remaining>=2:
     try:
      view=PublicTaskView(**{**task['task_public'],'public_examples':tuple(canonical(c) for c in task['task_public']['public_examples'])})
      for action in ('REPAIR_EXISTING','REGENERATE_FRESH'):prepare(action_messages(action,view,code,feedback),limits=Limits())
      dual=True
     except Exception as exc:diagnosis=type(exc).__name__
    later=rows[n+1:];subsequent_public=[z for z in result['events'][n+1:] if z.get('public_feedback',{}).get('status')=='PUBLIC_PASS']
    facts.append({'task_id':task['task_id'],'stage':event['stage'],'candidate_sha256':event['code_sha256'],'at':at,'public_feedback':f,'prefix_ledger':ledger[:n+1],'remaining_calls':remaining,'remaining_tokens':204800-event['budget']['charged_or_reserved_tokens'],'complete_operational_candidate':complete,'structural_status':obs['structural_status'],'trusted_failure':bool(fact),'fact_id':fact['event_id'] if fact else None,'dual_action_headroom':dual,'preflight_diagnosis':diagnosis,'scheduling':'DEFER_NOT_AUTHORIZED' if dual else 'STORE_NO_CURRENT_DUAL_ACTION_OPPORTUNITY','task_end_audit_NOT_PREFIX':{'native_recovered':bool(fact and subsequent_public),'native_later_calls':len(later),'native_later_tokens':sum(r['usage']['total_tokens'] for r in later),'potential_cost_headroom':bool(dual and later),'measured_savings':None}})
   e.write(OUT/'checkpoint_observations.json',facts)
   print('TASK',index,task['task_id'],result['status'],'calls',result['budget']['calls'],'tokens',result['budget']['charged_or_reserved_tokens'],flush=True)
  # No private outcomes before the entire online/success-memory state is locked.
  runner.save();e.write(OUT/'online_lock.json',{'results':{k:fingerprint(v) for k,v in results.items()},'state_sha256':e.sha(OUT/'state.json'),'at':time.time()})
  private=e.read(DATA/'evaluator_only.json')
  for tid,result in results.items():
   code=result['selected']['code'] if result['selected'] else result['last_candidate']
   review=runner.judge.run(tid,code,private[tid]['audit_cases']);e.write(OUT/'final_review'/f'{tid}.json',review)
   print('REVIEW',tid,review['tests_passed'],'/',review['tests_run'],flush=True)
 except Exception as exc:
  error={'type':type(exc).__name__,'message':str(exc)};print('STOP',error,flush=True)
 finally:
  runner.save();rr=[r for r in runner.transports['solve'].audit if r.get('usage')]
  def count(predicate):
   xs=[x for x in facts if predicate(x)];return {'events':len(xs),'independent_tasks':len({x['task_id'] for x in xs})}
  funnel={'observed_tasks':len(results),'all_checkpoints':len(facts),'public_failures':count(lambda x:x['public_feedback']['status'] in ('WRONG_ANSWER','RUNTIME_ERROR','TIME_LIMIT','COMPILE_ERROR','NO_COMPLETE_CODE')),'trusted_failures':count(lambda x:x['trusted_failure']),'complete_candidate_failures':count(lambda x:x['trusted_failure'] and x['complete_operational_candidate']),'missing_program_failures':count(lambda x:x['structural_status']=='NO_COMPLETE_CODE'),'dual_action_headroom':count(lambda x:x['dual_action_headroom']),'native_recovery':count(lambda x:x['task_end_audit_NOT_PREFIX']['native_recovered']),'potential_cost_headroom':count(lambda x:x['task_end_audit_NOT_PREFIX']['potential_cost_headroom'])}
  summary={'error':error,'funnel':funnel,'responses':len(rr),'input_tokens':sum(r['usage']['prompt_tokens'] for r in rr),'output_tokens':sum(r['usage']['completion_tokens'] for r in rr),'tokens':sum(r['usage']['total_tokens'] for r in rr),'estimated_api_usd':sum((r['usage']['prompt_tokens']*.3+r['usage']['completion_tokens']*1.2)/1e6 for r in rr),'budget':runner.budgets['solve'].snapshot(),'generated_rules':0,'operator_invocations':0,'reserve_tasks_executed':0,'scope':'observation only; no relative benefit measured; not full S18 learning experiment'}
  e.write(OUT/'summary.json',summary);print('SUMMARY',json.dumps(summary),flush=True)
 if error:raise RuntimeError('Inspect stopped run; no automatic retry')
if __name__=='__main__':main()
