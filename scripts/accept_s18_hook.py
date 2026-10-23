"""Zero-provider-API acceptance through actual ExperimentRunner/Controller."""
import tempfile,json,os
from pathlib import Path
import run_workflow_v2 as e
from failure_evo.contracts import fingerprint
from failure_evo.repair_choice_memory import RuleMemory
R={'when':{'candidate_state':'STRUCTURAL_PASS','public_result':'WRONG_ANSWER','remaining_calls_min':1},'action':'REGENERATE_FRESH','fallback':'NATIVE'}
TASK={'task_id':'fixture','dataset':'taco','difficulty':'MEDIUM','task_public':{'problem_id':'fixture','prompt':'Print 2'},'public_cases':[]}
def run(root,mode):
 calls=[]
 def sender(_):
  def send(wire):
   n=len(calls);calls.append(json.loads(wire))
   if mode=='unknown' and n==1:raise ConnectionError('fixture unknown send')
   value=1 if n==0 or (mode=='fallback' and n==1) or (mode=='cross_task' and n==2) else 2
   return {'model':'deepseek-flash','choices':[{'message':{'content':f'```python\nprint({value})\n```'},'finish_reason':'stop'}],'usage':{'prompt_tokens':10,'completion_tokens':10,'total_tokens':20}}
  return send
 runner=None;published=False
 def evaluate(task,code):
  nonlocal published
  if mode=='cross_task' and not published:
   authorize();published=True
  if mode=='live_suspend' and code=='print(1)':memory.archive(key,'host evidence',harmful=True)
  if os.environ.get('S18_REAL_WORKER')=='1':
   return e.prior.Judge(runner.budgets['solve']).run('engineering_fixture',code,[{'input':'','expected':'2','comparison':'tokens','scorer':'s1'}])
  good=code=='print(2)'
  return {'visibility':'public','status':'PUBLIC_PASS' if good else 'WRONG_ANSWER','tests_run':1,'tests_passed':int(good),'cases':[{'visibility':'public','legal_verified':True,'input':'','expected':'2','actual':'2\n' if good else '1\n','correct':good}]}
 plan={'run_id':mode,'protocol_hash':'','shared_protocol':e.VERSION,'operator_representation':'repair-choice-json-v1','rule_hook_enabled':mode!='disabled','model':'deepseek-flash','evidence_kind':'engineering_fixture','frozen_files':{},'budgets':{'solve':e.prior.config(10,50,600000)},'per_task':{'max_calls':1 if mode=='budget' else 5,'max_tokens':204800,'max_tools':40,'wall_seconds':60}}
 plan['protocol_hash']=fingerprint({k:v for k,v in plan.items() if k!='protocol_hash'})
 runner=e.ExperimentRunner(root/mode,plan,sender,evaluator_factory=lambda task:evaluate,decision_runner=lambda *a:None)
 memory=RuleMemory(runner.folder/'rule_registry.jsonl');key=memory.add(R,['fixture-source'])
 report=runner.folder/'fixture_report.json';report.write_text('{}')
 def authorize():
  memory.record_assessment(key,{'one':False},{'one':True},report_path=report)
  memory.authorize(key,tasks=['fixture','fixture2'],opportunities=2,safety_checks=dict.fromkeys(['contract','boundary','negative_cases','fallback','no_known_harm'],True),authorization_id='engineering-only')
 if mode not in ('shadow','cross_task'):authorize()
 if mode=='suspended':memory.archive(key,'fixture harm',harmful=True)
 error=None
 try:result=runner.solve('F',TASK)
 except ConnectionError:error='UNKNOWN';result={}
 hooks=result.get('hook_events',[])
 assert (len(hooks)>0)==(mode in ('experimental','fallback')) if not error else mode=='unknown'
 if mode=='cross_task':
  task={**TASK,'task_id':'fixture2','task_public':{**TASK['task_public'],'problem_id':'fixture2'}}
  result2=runner.solve('F',task);assert len(result2['hook_events'])==1
 if mode=='fallback':assert result['budget']['calls']==3 and result['status']=='PUBLIC_ACCEPTED'
 if mode=='experimental':assert result['budget']['calls']==2 and result['status']=='PUBLIC_ACCEPTED'
 if mode not in ('budget','unknown'):assert result['status']=='PUBLIC_ACCEPTED'
 if mode=='budget':assert len(calls)==1
 if mode=='unknown':assert len(calls)==2 and runner.budgets['solve'].snapshot()['unknown_or_pending_requests']
 return {'mode':mode,'passed':True,'mock_sends':len(calls),'error':error,'hook_events':len(hooks),'state':memory.state(key)['permission']}
if __name__=='__main__':
 out=e.ROOT/('runs/s18_hook_worker_acceptance_20261023_02' if os.environ.get('S18_REAL_WORKER')=='1' else 'runs/s18_hook_acceptance_20261023_03');out.mkdir(exist_ok=False)
 (out/'tmp').mkdir();tempfile.tempdir=str(out/'tmp')
 rows=[]
 for mode in ['disabled','shadow','experimental','fallback','budget','suspended','live_suspend','cross_task','unknown']:
  rows.append(run(out,mode));print(mode,'PASS',flush=True)
 e.write(out/'acceptance.json',{'api_calls':0,'generated_code_executed':os.environ.get('S18_REAL_WORKER')=='1','evaluator':'existing Linux Worker' if os.environ.get('S18_REAL_WORKER')=='1' else 'fixture','rows':rows})
