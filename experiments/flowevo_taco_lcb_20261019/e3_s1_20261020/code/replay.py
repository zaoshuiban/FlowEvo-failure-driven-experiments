"""Offline sandbox execution of every selected historical program, no model access."""
import ast,concurrent.futures,hashlib,json,pathlib,sys,time
from legal_suite import R,B,accepts
SANDBOX=B/'repair_v2d_20261020/code'
if not SANDBOX.exists():SANDBOX=B/'repair_v2/epochs/repair_v2d_20261020/code'
sys.path.insert(0,str(SANDBOX))
from sandbox import Worker
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2));tmp.replace(p)
def evaluate(tid,path,cases,fn=None):
 text=path.read_text();start=time.monotonic();base={'tests_total':len(cases),'tests_run':0,'tests_passed':0,'failures':[],'executions':0}
 if not text.strip():return {**base,'status':'NO_COMPLETE_CODE','passed':False}
 try:ast.parse(text)
 except SyntaxError as e:return {**base,'status':'COMPILE_ERROR','passed':False,'exception':str(e)}
 with Worker(path) as w:
  if not fn:
   v=w.call({'mode':'compile_stdio','timeout':6})
   if v['status']!='OK':return {**base,'status':v['status'],'passed':False,'diagnostic':v}
  for i,c in enumerate(cases):
   req={'mode':'function' if fn else 'stdio','timeout':6 if tid.startswith('lcb') else 4}
   if fn:req.update(function=fn,args=c['input'])
   else:req['input']=c['input']
   v=w.call(req);base['tests_run']+=1;base['executions']+=1
   actual=v.get('value') if fn else v.get('output','')
   okay=v['status']=='OK' and accepts(tid,c,actual)
   if okay:base['tests_passed']+=1
   elif len(base['failures'])<3:base['failures'].append({'case_index':i,'case':c,'actual':v,'status':v['status'] if v['status']!='OK' else 'WRONG_ANSWER'})
   if v['status'] in ['TIME_LIMIT','EVALUATOR_ERROR']:break
 return {**base,'status':base['failures'][0]['status'] if base['failures'] else 'PASS','passed':not base['failures'],'seconds':time.monotonic()-start}
def main():
 manifest=read(R/'review_manifest.json');suite=read(R/'public_suite.json')['cases'];audit=read(R/'input_contract_review.json');assert len(audit)==48 and sum(x['public_cases_verified'] for x in audit)==sum(map(len,suite.values()))
 hashes={str(p.relative_to(R)):sha(p) for p in [R/'review_manifest.json',R/'public_suite.json',R/'input_contract_review.json',*sorted((R/'code').glob('*.py'))]}
 frozen={'hashes':hashes,'new_model_calls':0,'comparison':'finite legal probes only; a PASS is not full-domain correctness','workers':2,'sandbox':'existing bwrap Worker, no network/credential/test mounts; host-side comparisons'}
 pin=R/'replay_frozen.json'
 if pin.exists():assert read(pin)==frozen,'Pinned replay inputs changed; use a new epoch'
 else:write(pin,frozen)
 jobs=[]
 for t in manifest['tasks']:
  task=read(R/'source/tasks'/(t['task_id']+'.json'))
  for a in t['historical_programs']:
   p=(R/a['source_path']).resolve()
   assert sha(p)==a['code_sha256']
   jobs.append((t['task_id'],a,p,task.get('function_name')))
 def run(job):
  tid,a,p,fn=job;dest=R/'verdicts'/tid/(a['stage']+'.json')
  if dest.exists():
   old=read(dest);assert old['code_sha256']==a['code_sha256'];return
  result=evaluate(tid,p,suite[tid],fn);result.update(task_id=tid,stage=a['stage'],code_sha256=a['code_sha256'],public_suite_sha256=hashes['public_suite.json']);write(dest,result);print(tid,a['stage'],result['status'],str(result['tests_passed'])+'/'+str(result['tests_total']),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,jobs))
 rows=[read(p) for p in sorted((R/'verdicts').glob('*/*.json'))];assert len(rows)==manifest['selected_programs'];write(R/'replay_summary.json',{'tasks':len(manifest['tasks']),'programs':len(rows),'sandbox_test_executions':sum(x['executions'] for x in rows),'new_model_calls':0,'new_model_tokens':0})
if __name__=='__main__':main()
