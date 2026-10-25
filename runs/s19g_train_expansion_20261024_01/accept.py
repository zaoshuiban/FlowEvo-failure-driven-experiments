"""Bounded reference scoring in existing DockerWorker; no model client is constructed."""
import pathlib,sys,os,tempfile,time,hashlib,ast,concurrent.futures,json
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1];sys.path.insert(0,str(R/'scripts'));import run_workflow_v2 as e
from failure_evo.persistent_budget import PersistentBudget
os.environ.update(DOCKER_CONFIG=str(R/'runs/s12c_functional_20261021_01/docker_public'),DOCKER_HOST='unix:///Users/majiatong/.colima/default/docker.sock');(P/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(P/'tmp')
allowed={x['id'] for x in e.read(P/'output_contract_review.json')['rows'] if x['accepted']};candidates=[x for x in e.read(P/'admission_inputs.json') if x['id'] in allowed]
protocol={'selection_sha256':e.sha(P/'selection_protocol.json'),'candidate_order_sha256':e.sha(P/'candidate_order.json'),'output_review_sha256':e.sha(P/'output_contract_review.json'),'concurrency':4,'ordering':'evaluate batches of4; consume in pre-frozen order, first61 passing; excess already evaluated is reserve only','model_calls':0,'max_tools':30000,'target_train':61}
if (P/'acceptance_protocol.json').exists():assert e.read(P/'acceptance_protocol.json')==protocol
else:e.write(P/'acceptance_protocol.json',protocol)
budget=PersistentBudget(P/'acceptance_budget.jsonl',run_id=P.name,protocol_hash=e.sha(P/'acceptance_protocol.json'),**e.prior.config(0,30000,0))
start=time.monotonic();results=e.read(P/'scoring_acceptance.json') if (P/'scoring_acceptance.json').exists() else [];done={x['id'] for x in results}
def check(c):
 judge=e.prior.Judge(budget);report={'id':c['id'],'passed':False,'references':[],'online_count':len(c['public']),'sealed_count':len(c['review'])};good=[]
 for src in c['solutions']:
  r=judge.run(c['id'],src,c['public']+c['review']);h=hashlib.sha256(src.encode()).hexdigest();report['references'].append({'sha256':h,'ast_sha256':hashlib.sha256(ast.dump(ast.parse(src),include_attributes=False).encode()).hexdigest(),'result':r})
  if r['passed']:good.append((h,src))
  if len(good)==2:break
 if len(good)==2:
  neg=judge.run(c['id'],"print('S19G_TRAIN_INVALID_OUTPUT')",c['public']+c['review']);report['negative']=neg
  if neg['tests_passed']==0:
   report['passed']=True;p=P/'tasks'/c['id'];p.mkdir(parents=True,exist_ok=True)
   for j,(h,src) in enumerate(good):(p/f'reference_{j}.py').write_text(src)
   t={'task_id':'s19g_'+c['id'],'original_id':c['id'],'dataset':'taco','difficulty':c['difficulty'],'original_url':c['url'],'role':'prospective_development_distribution','task_public':{'problem_id':'s19g_'+c['id'],'prompt':c['prompt'],'starter_code':'','function_name':'','public_examples':c['statement_samples']},'public_cases':c['public'],'audit_cases':c['review'],'reference_hashes':[h for h,_ in good],'reference_ast_hashes':[x['ast_sha256'] for x in report['references'] if x['result']['passed']],'raw_source_row':c['row'],'source_sha256':e.read(P/'download_ledger.json')['sha256'],'source_split':'train','question_hash':c['question_hash']};e.write(p/'task.json',t)
 return report
try:
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for i in range(0,len(candidates),4):
   if sum(x['passed'] for x in results)>=61:break
   batch=[c for c in candidates[i:i+4] if c['id'] not in done]
   fs=[pool.submit(check,c) for c in batch]
   for c,f in zip(batch,fs):
    r=f.result();results.append(r);done.add(c['id']);e.write(P/'scoring_acceptance.json',results);print(c['id'],r['passed'],'qualified',sum(x['passed'] for x in results),'examined',len(results),flush=True)
except Exception as exc:
 e.write(P/'acceptance_error.json',{'type':type(exc).__name__,'error':str(exc),'model_calls':0,'budget':budget.snapshot()});raise
passed=[x for x in results if x['passed']];tasks=[e.read(P/'tasks'/x['id']/'task.json') for x in passed[:61]];e.write(P/'tasks.json',tasks)
e.write(P/'acceptance_summary.json',{'examined':len(results),'passed':len(passed),'selected':len(tasks),'reference_verified_reserve':[x['id'] for x in passed[61:]],'model_calls':0,'elapsed_seconds':time.monotonic()-start,'budget':budget.snapshot()});print('DONE',len(tasks),flush=True)
