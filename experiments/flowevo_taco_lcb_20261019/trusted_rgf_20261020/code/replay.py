import ast,concurrent.futures,difflib,hashlib,json,pathlib,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT.parent
sys.path.insert(0,str(BASE/'repair_v2d_20261020/code'))
from sandbox import Worker
from regrade import write
from suite import accepts

def evaluate(tid,code,cases,function=None):
 text=code.read_text()
 if not text.strip():return {'status':'NO_COMPLETE_CODE','passed':False,'tested':0}
 try:ast.parse(text)
 except SyntaxError as exc:return {'status':'COMPILE_ERROR','passed':False,'tested':0,'error':str(exc)}
 start=time.monotonic()
 with Worker(code) as worker:
  if not function:
   response=worker.call({'mode':'compile_stdio','timeout':6})
   if response['status']!='OK':return {'status':response['status'],'passed':False,'tested':0,'actual':response}
  for i,c in enumerate(cases):
   req={'mode':'function' if function else 'stdio','timeout':6 if tid.startswith('lcb') else 4}
   if function:req.update(function=function,args=c['input'])
   else:req['input']=c['input']
   res=worker.call(req);actual=res.get('value') if function else res.get('output','')
   if res['status']!='OK' or not accepts(tid,c,actual):return {'status':res['status'] if res['status']!='OK' else 'WRONG_ANSWER','passed':False,'tested':i+1,'failed_case_index':i,'case':c,'actual':res,'seconds':time.monotonic()-start}
 return {'status':'PASS','passed':True,'tested':len(cases),'seconds':time.monotonic()-start}

def main():
 suite=json.loads((ROOT/'suite_frozen.json').read_text())['cases'];catalog={x['task_id']:x for x in json.loads((BASE/'repair_v2_20261020/catalog.json').read_text())};inventory=[];jobs=[]
 for p in sorted(BASE.glob('runs/*/*/result.json')):
  old=json.loads(p.read_text());tid=old['task_id']
  for attempt in old['attempts']:
   code=p.parent/(attempt['stage']+'.py');row={'task_id':tid,'stage':attempt['stage'],'sha256':hashlib.sha256(code.read_bytes()).hexdigest(),'in_trusted_set':tid in suite};inventory.append(row)
   if tid in suite:jobs.append((row,code,catalog[tid].get('function_name')))
 assert len(inventory)==2132
 write(ROOT/'inventory_2132.json',inventory)
 def run(job):
  row,code,fn=job;dest=ROOT/'verdicts'/row['task_id']/(row['stage']+'.json')
  if dest.exists():return
  r=evaluate(row['task_id'],code,suite[row['task_id']],fn);r.update(row);write(dest,r);print(row['task_id'],row['stage'],r['status'],r['tested'],flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,jobs))
 # Counterfactual repairs are constructed without any generation model.
 for tid in ['lcb_atcoder_abc301_f','taco_0875']:
  old=next(BASE.glob('runs/*/'+tid+'/l1.py'));original=old.read_text()
  if tid=='taco_0875':patched=original.replace('import sys\n','import sys\nsys.setrecursionlimit(10000)\n',1)
  else:patched=original.replace('    fact = [1] * (n + 1)','    n = max(n, 26)  # factorial indices include the entire alphabet\n    fact = [1] * (n + 1)',1)
  assert patched!=original
  path=ROOT/'counterfactuals'/tid/'fixed.py';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(patched);(path.parent/'original.py').write_text(original);(path.parent/'minimal.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),patched.splitlines(True),fromfile='historical_l1.py',tofile='counterfactual.py')))
  result=evaluate(tid,path,suite[tid]);write(path.parent/'verification.json',result);print('COUNTERFACTUAL',tid,result['status'],flush=True)
 write(ROOT/'offline_run.json',{'historical_inventory':2132,'selected_programs':len(jobs),'tasks':len(suite),'new_generation_calls':0})
if __name__=='__main__':main()
