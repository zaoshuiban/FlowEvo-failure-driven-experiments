import concurrent.futures,datetime,hashlib,json,pathlib,re,sys,threading,time
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'vendor/FlowEvo/src'))
from code_math.runner import CodeSkillLibrary,CONDITIONS,extract_code
from core.schemas import CodeTaskInstance
from sandbox_runner import evaluate
import requests
LEVELS={'taco':['EASY','MEDIUM','MEDIUM_HARD','HARD','VERY_HARD'],'lcb':['easy','medium','hard']}
STOP=threading.Event();REPORT_LOCK=threading.Lock()
CONFIG={'method':'FlowEvo official code_math ours adapter','flowevo_commit':'36e81efd4d1fdbabca7366200b15808ebef157fa','taco_evaluator_commit':'245eba3beb2d23a07082307de303de2589e4321a','lcb_evaluator_commit':'28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24','requested_model':'deepseek-reasoner','thinking':'enabled','reasoning_effort':'high','max_tokens_per_call':32768,'max_attempts':5,'seed':20261019,'skill_scope':'independent online library per dataset and difficulty','verifier_feedback':'all benchmark tests; only pass/fail or error category disclosed','protocol':'adaptive success within 5 attempts; first attempt reported separately; final metric is not hidden-test-blind pass@1','python':'3.10.12','timeouts_per_case_seconds':{'taco':4,'lcb':6},'sandbox':'bubblewrap unshare-all, uid 65534, no network, no credentials, read-only mounts','adapter_changes':['TACO/LCB prompts and official evaluators','full task and code in repair prompts instead of original 500/800-character truncation','32768-token reasoning budget instead of 2048','independent online stream per difficulty','first-failure test short circuit, same all-tests-pass predicate','API usage and actual returned model logging'],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)
def status(group,**kwargs):write(ROOT/'runs'/group/'status.json',{'group':group,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**kwargs})
def report():
 with REPORT_LOCK:
  from reporting import build_report
  return build_report(ROOT,LEVELS,CONFIG,STOP.is_set())
class API:
 def __init__(self):
  self.session=requests.Session();self.session.trust_env=False;self.key=(ROOT/'.deepseek-key').read_text().strip()
 def call(self,prompt,temp):
  body={'model':'deepseek-reasoner','messages':[{'role':'system','content':'You are an expert competitive programmer. Produce a correct and efficient Python solution.'},{'role':'user','content':prompt}],'max_tokens':32768,'temperature':temp,'thinking':{'type':'enabled'},'reasoning_effort':'high'}
  start=time.monotonic()
  for retry in range(5):
   if STOP.is_set():raise RuntimeError('Experiment stopped')
   try:
    r=self.session.post('https://api.deepseek.com/chat/completions',json=body,headers={'Authorization':'Bearer '+self.key},timeout=(20,600))
    if r.status_code in [401,402,403]:raise RuntimeError('API authorization/balance error HTTP '+str(r.status_code))
    if r.status_code in [408,409,425,429] or r.status_code>=500:
     if retry<4:time.sleep(5*(retry+1));continue
    r.raise_for_status();d=r.json();ch=d['choices'][0]
    return {'model':d.get('model'),'id':d.get('id'),'created':d.get('created'),'system_fingerprint':d.get('system_fingerprint'),'usage':d.get('usage',{}),'finish_reason':ch.get('finish_reason'),'text':ch['message'].get('content') or '','latency_s':round(time.monotonic()-start,3),'request':body}
   except (requests.Timeout,requests.ConnectionError):
    if retry==4:raise RuntimeError('API transport retries exhausted')
    time.sleep(5*(retry+1))
  raise RuntimeError('API retries exhausted')
def prompt_for(t):
 parts=['Solve this competitive programming problem in Python 3.10. Return the complete solution in one ```python``` block.','Problem:\n'+t['prompt']]
 if t['starter_code']:parts+=['Starter code / required signature:\n'+t['starter_code']]
 if t['function_name']:parts+=['Use the required function/method named '+t['function_name']+'. Preserve the required class and signature; do not read stdin.']
 else:parts+=['Write a complete program that reads standard input and prints the required output.']
 parts+=['Think carefully about correctness, edge cases and time/memory complexity.']
 return '\n\n'.join(parts)
def run_group(ds,diff):
 group=f'{ds}_{diff}';mp=ROOT/'data'/f'{ds}_manifest.json';status(group,state='waiting_for_dataset')
 while not mp.exists():
  if STOP.wait(5):return
 metas=[r for r in read(mp)['tasks'] if r['difficulty']==diff];library=CodeSkillLibrary();api=API()
 for index,meta in enumerate(metas):
  if STOP.is_set():return
  folder=ROOT/'runs'/group/meta['task_id'];folder.mkdir(parents=True,exist_ok=True)
  task_path=ROOT/'data/tasks'/(meta['task_id']+'.json');task=read(task_path)
  instance=CodeTaskInstance(task_id=task['task_id'],benchmark=ds,prompt=task['prompt'],text=task['prompt']);result_path=folder/'result.json'
  if result_path.exists():
   result=read(result_path)
   if result['passed']:library.add(instance,(folder/(result['final_stage']+'.py')).read_text())
   continue
  start=time.monotonic();context=library.retrieve(instance).get('context','');base=prompt_for(task);attempts=[];previous='';feedback=''
  for stage,temp in [('l1',0.0),('l2a',0.5),('l2b',0.5),('l3',0.7),('l4',0.2)]:
   if STOP.is_set():return
   status(group,state='generating',completed=index,total=len(metas),task_id=task['task_id'],stage=stage)
   prompt=base
   if stage in ['l3','l4']:
    prompt+='\n\nPrevious candidate:\n```python\n'+previous+'\n```\n\nVerifier feedback: '+feedback+'\nFix the solution and return the corrected complete Python program/function.'
    if context:prompt+='\n\nReference from a previously solved problem:\n'+context
   response_path=folder/(stage+'.response.json')
   if response_path.exists():response=read(response_path)
   else:response=api.call(prompt,temp);write(response_path,response)
   code=extract_code(response['text'],instance);code_path=folder/(stage+'.py');code_path.write_text(code,encoding='utf-8');vp=folder/(stage+'.verdict.json')
   status(group,state='evaluating',completed=index,total=len(metas),task_id=task['task_id'],stage=stage)
   if vp.exists():verdict=read(vp)
   elif not code.strip():verdict={'passed':False,'feedback':'Generation ended without final code.','finish_reason':response['finish_reason']};write(vp,verdict)
   else:verdict=evaluate(task_path,code_path,task['num_tests']);write(vp,verdict)
   attempts.append({'stage':stage,'passed':verdict['passed'],'feedback':verdict['feedback'],'model':response['model'],'usage':response['usage'],'finish_reason':response['finish_reason'],'code_sha256':hashlib.sha256(code.encode()).hexdigest()})
   previous=code;feedback=verdict['feedback']
   if verdict['passed']:break
  result={**meta,'first_pass':attempts[0]['passed'],'passed':attempts[-1]['passed'],'attempt_count':len(attempts),'final_stage':attempts[-1]['stage'],'attempts':attempts,'library_size_before':library.size,'repair_skill_available':bool(context),'wall_seconds':round(time.monotonic()-start,2)}
  if result['passed']:library.add(instance,previous)
  result['library_size_after']=library.size;write(result_path,result);write(ROOT/'runs'/group/'library.json',library.to_dict())
  status(group,state='running',completed=index+1,total=len(metas),last_task=task['task_id'],last_passed=result['passed'])
  print(group,index+1,'/',len(metas),'PASS' if result['passed'] else 'FAIL','attempts',len(attempts),flush=True);report()
 status(group,state='complete',completed=len(metas),total=len(metas))
def guarded(ds,diff):
 try:run_group(ds,diff)
 except BaseException as e:
  STOP.set();message=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',str(e));status(f'{ds}_{diff}',state='error',error=message[:1000]);print('ERROR',ds,diff,type(e).__name__,message[:500],flush=True);report()
def main():
 if not (ROOT/'reports/selftest.json').exists():raise RuntimeError('Evaluator self-test must pass first')
 cp=ROOT/'reports/experiment_config.json'
 if cp.exists():CONFIG['started_utc']=read(cp)['started_utc']
 write(cp,CONFIG);report()
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  fs=[pool.submit(guarded,ds,d) for ds,levels in LEVELS.items() for d in levels]
  for f in fs:f.result()
 print('EXPERIMENT_STATUS',report()['status'],flush=True)
if __name__=='__main__':main()
