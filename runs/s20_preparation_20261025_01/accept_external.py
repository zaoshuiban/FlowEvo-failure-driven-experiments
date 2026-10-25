"""Frozen external order; actual isolated references and negative scoring, zero model API."""
import pathlib,sys,tempfile,time,hashlib,ast,concurrent.futures
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1];sys.path.insert(0,str(R/'scripts'));import run_workflow_v2 as e
from run_learning_stream import configure_worker
from failure_evo.persistent_budget import PersistentBudget
configure_worker(e.read(R/'reports/s19_v2_acceptance/worker_environment.json'));(P/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(P/'tmp')
allow={r['id'] for r in e.read(P/'external_output_review.json') if r['accepted']};cs=[c for c in e.read(P/'external_candidates.json') if c['id'] in allow]
protocol=dict(candidate_sha256=e.sha(P/'external_candidates.json'),review_sha256=e.sha(P/'external_output_review.json'),order_sha256=e.sha(P/'external_candidate_order.json'),targets={'apps':40,'contests':20},max_reference_versions=4,worker_config=e.read(R/'reports/s19_v2_acceptance/worker_environment.json'),model_api_calls=0,max_tools_per_candidate=180,selection='first qualifying in source order; batches of4, excess pass reserve')
if (P/'external_worker_protocol.json').exists():assert e.read(P/'external_worker_protocol.json')==protocol
else:e.write(P/'external_worker_protocol.json',protocol)
results=e.read(P/'external_worker_results.json') if (P/'external_worker_results.json').exists() else [];done={r['id'] for r in results};start=time.monotonic()
def check(c):
 b=PersistentBudget(P/'external_ledgers'/(c['id']+'.jsonl'),run_id='s20-'+c['id'],protocol_hash=e.sha(P/'external_worker_protocol.json'),**e.prior.config(0,180,0));j=e.prior.Judge(b);rows=[];good=[]
 for code in c['solutions']:
  v=j.run(c['id'],code,c['public']+c['review']);rows.append(dict(sha256=hashlib.sha256(code.encode()).hexdigest(),ast_sha256=hashlib.sha256(ast.dump(ast.parse(code),include_attributes=False).encode()).hexdigest(),result=v))
  if v['passed']:good.append(code)
  if len(good)==2:break
 neg=j.run(c['id'],"print('S20_INVALID_OUTPUT_SENTINEL')",c['public']+c['review']) if len(good)==2 else None
 passed=len(good)==2 and neg['tests_passed']==0
 if passed:
  folder=P/'external_tasks'/c['id'];folder.mkdir(parents=True,exist_ok=True)
  for i,code in enumerate(good):(folder/f'reference_{i}.py').write_text(code)
 return dict(id=c['id'],dataset=c['dataset'],passed=passed,references=rows,negative=neg,budget=b.snapshot())
with concurrent.futures.ThreadPoolExecutor(4) as ex:
 for ds,target in protocol['targets'].items():
  subset=[c for c in cs if c['dataset']==ds]
  for off in range(0,len(subset),4):
   if sum(r['passed'] and r['dataset']==ds for r in results)>=target:break
   batch=[c for c in subset[off:off+4] if c['id'] not in done]
   for c,r in zip(batch,ex.map(check,batch)):
    results.append(r);done.add(c['id']);e.write(P/'external_worker_results.json',results);print(c['id'],r['passed'],'passed',sum(x['passed'] and x['dataset']==ds for x in results),flush=True)
selected={ds:[r['id'] for r in results if r['dataset']==ds and r['passed']][:n] for ds,n in protocol['targets'].items()}
e.write(P/'external_acceptance.json',dict(selected=selected,model_requests=0,elapsed_seconds=time.monotonic()-start,examined=len(results),all_passed=sum(r['passed'] for r in results)))
print('DONE', {k:len(v) for k,v in selected.items()},flush=True)
