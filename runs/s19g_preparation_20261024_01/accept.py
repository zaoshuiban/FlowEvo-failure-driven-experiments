import sys,json,pathlib,os,tempfile,ast,time,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=pathlib.Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts'));import run_workflow_v2 as e
from failure_evo.persistent_budget import PersistentBudget
os.environ.update(DOCKER_CONFIG=str(ROOT/'runs/s12c_functional_20261021_01/docker_public'),DOCKER_HOST='unix:///Users/majiatong/.colima/default/docker.sock')
(OUT/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(OUT/'tmp')
plan=e.read(OUT/'selection_protocol.json');budget=PersistentBudget(OUT/'acceptance_budget.jsonl',run_id=OUT.name,protocol_hash=e.sha(OUT/'selection_protocol.json'),**e.prior.config(0,30000,0))
judge=e.prior.Judge(budget);admitted=e.read(OUT/'tasks.json') if (OUT/'tasks.json').exists() else [];reviews=e.read(OUT/'scoring_acceptance.json') if (OUT/'scoring_acceptance.json').exists() else [];urls={t['original_url'] for t in admitted};done={r['id'] for r in reviews}
for c in e.read(OUT/'admission_inputs.json'):
 if len(admitted)>=80:break
 if c['id'] in done:continue
 if c['url'] in urls:continue
 report={'id':c['id'],'references':[],'passed':False};refs=[];structures=set()
 for src in c['solutions']:
  if len(refs)>=4:break
  if not isinstance(src,str):continue
  try:ast.parse(src);compile(src,'reference','exec')
  except (SyntaxError,ValueError):continue
  h=hashlib.sha256(src.encode()).hexdigest()
  structure=ast.dump(ast.parse(src),include_attributes=False)
  if structure in structures:continue
  structures.add(structure)
  if h not in [x[0] for x in refs]:refs.append((h,src))
 good=[]
 for h,src in refs:
  result=judge.run(c['id'],src,c['public']+c['review'])
  report['references'].append({'sha256':h,'result':result})
  if result['passed']:good.append((h,src))
  if len(good)>=2:break
 if len(good)>=2:
  negative=judge.run(c['id'],"print('S19G_INVALID_OUTPUT')",c['public']+c['review']);report['negative']=negative
  if negative['tests_passed']==0:
   report['passed']=True;urls.add(c['url']);role='long_stream_development_distribution'
   p=OUT/'tasks'/c['id'];p.mkdir(parents=True,exist_ok=True)
   for i,(h,src) in enumerate(good):(p/f'reference_{i}.py').write_text(src)
   task={'task_id':'s19g_'+c['id'],'original_id':c['id'],'dataset':'taco','difficulty':c['difficulty'],'original_url':c['url'],'role':role,'task_public':{'problem_id':'s19g_'+c['id'],'prompt':c['prompt'],'starter_code':'','function_name':'','public_examples':[{'input':x['input'],'expected':x['expected'],'visibility':'public','legal_verified':True} for x in c['statement_samples']]},'public_cases':c['public'],'audit_cases':c['review'],'reference_hashes':[h for h,s in good],'prior_metadata_only':True,'prior_project_execution_found':False,'limits':'cross-project exposure audit limited to available saved records; no claim model-training cleanliness; two distinct references may share algorithm lineage'}
   e.write(p/'task.json',task);admitted.append(task)
 reviews.append(report);e.write(OUT/'scoring_acceptance.json',reviews);e.write(OUT/'tasks.json',admitted)
 print(c['id'],report['passed'],'admitted',len(admitted),flush=True)
e.write(OUT/'acceptance_summary.json',{'examined':len(reviews),'qualified':len(admitted),'api_calls':0,'budget':budget.snapshot()})
