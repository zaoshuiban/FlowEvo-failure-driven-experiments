"""V3.1 finite development experiment. Frozen algorithms; paired conditions; no Gate."""
import json,sys,time,subprocess,urllib.request
from pathlib import Path
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.math_v31_semantic import SemanticAdapter,VERSION
from failure_evo.contracts import fingerprint
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.semantic_contract import artifact,SplitRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.operator_version_gate import VersionGate
from code_math.no_gold import PublicMathTask
OLD=ROOT/'runs/math_v3_components_deepseek_repair_20261027_01'
AUDIT=ROOT/'runs/math_v3_components_audit_deepseek_20261027_01'
TESTS=ROOT/'runs/math_v3_generated_tests_review_20261027_01'
def load(p):return json.loads(p.read_text())
def freeze(out):
 if out.exists():raise RuntimeError('new run required')
 jobs=load(AUDIT/'freeze.json')['jobs'];oldscore=load(AUDIT/'scores.json');tests=load(TESTS/'scores.json');source=load(OLD/'evidence.json')
 cases=[];inputs={}
 for index,name in enumerate(['F1','F2','T2','F3','T3']):
  d=OLD/name;s=load(d/'solver_response.json');algorithm=(d/'solver.py').read_text();assert algorithm==s['code']
  group=[j for j in jobs if j['name']==name];diagnostics=[]
  for j,r in zip([j for j in jobs if j['name']==name],[r for r in oldscore if r['name']==name]):
   assert j['task']['task_id']==r['task_id']
   case=dict(algorithm=name,role=j['role'],task=j['task'],supported=j['supported'],parameters=j['parameters'],old_observed=r['observed'])
   cases.append(case)
   if r['applicability'] not in ('CORRECT_MATCH','CORRECT_REFUSAL','PARAMETER_MISMATCH'):
    diagnostics.append(dict(task=j['task'],supported_by_host_review=j['supported'],observed_match=r['observed']['match'],diagnostic=r['applicability'],role=j['role']))
  # Include all previously observed ambiguous accepts first; never expose numerical outputs.
  for t in tests:
   if t['label']=='DS_'+name and t['decision']=='ambiguous':
    proposals=load(d/'test_proposals.json');q=proposals[t['index']]['proposal']
    diagnostics.insert(0,dict(task={'task_id':'development-proposal-'+str(t['index']),'problem':q['problem']},supported_by_host_review=None,observed_match=t['observation']['match'],diagnostic='SEMANTIC_UNCERTAINTY_REQUIRES_NO_COMPUTATION',role='GeneratedDevelopment'))
  # Prioritize source and supported cases; fixed deterministic order, max 12.
  diagnostics=sorted(enumerate(diagnostics),key=lambda x:(0 if x[1]['supported_by_host_review'] is None else 1 if x[1]['supported_by_host_review'] else 2,x[0]))
  selected=[x[1] for x in diagnostics[:12]]
  base=dict(solver_code=algorithm,solver_sha256=sha(d/'solver.py'),parameter_schema=json.loads(s['applicability']),source_problems=[j['task'] for j in group if j['role']=='Source'])
  for condition in (('T','F') if index%2==0 else ('F','T')):
   inp=dict(base,condition=condition)
   if condition=='F':inp['contract_evidence']=dict(previous_matcher=(d/'matcher.py').read_text() if (d/'matcher.py').exists() else None,previous_contract=load(d/'artifact.json')['contract'] if (d/'artifact.json').exists() else None,observations=selected,selection='uncertainty then supported failures then unsupported failures; stable historical order; maximum12')
   inputs[name+'_'+condition]=inp
 plan=dict(version=VERSION,order=list(inputs),model='deepseek-flash',max_requests=10,per_condition=1,revision_calls=0,output_tokens=12288,input_upper=65536,thinking='disabled',temperature=0,selection='all five previous DeepSeek algorithms, no outcome selection',comparison='paired same solver; T only code/schema/source questions; F adds previous matcher and legal evidence',admission='full supported acceptance, zero negative accept/interface errors; no MATCH on ambiguous generated controls; otherwise Shadow; no Gate this run',worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),git_sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_hashes={str(p.relative_to(ROOT)):sha(p) for p in list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__)]},history_hashes={str(p):sha(p) for folder in (OLD,AUDIT,TESTS) for p in folder.rglob('*') if p.is_file()},cases_sha256=fingerprint(cases),inputs_sha256=fingerprint(inputs))
 price=urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing',timeout=30).read();assert b'$0.3' in price and b'$1.2' in price
 save(out/'protocol.json',plan);save(out/'freeze.json',dict(sha256=fingerprint(plan)));save(out/'inputs.json',inputs);save(out/'cases.json',cases);(out/'pricing.html').write_bytes(price)
 for rel in plan['source_hashes']:
  p=out/'frozen_source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/rel).read_bytes())
 print('FROZEN',fingerprint(plan),flush=True)
def generate(out):
 p=load(out/'protocol.json');assert fingerprint(p)==load(out/'freeze.json')['sha256'];assert all(sha(ROOT/r)==h for r,h in p['source_hashes'].items());inputs=load(out/'inputs.json');assert fingerprint(inputs)==p['inputs_sha256']
 results=[]
 try:
  for key in p['order']:
   d=out/key
   if d.exists():raise RuntimeError('consumed run; no resend')
   d.mkdir();v=inputs[key];(d/'solver.py').write_text(v['solver_code'])
   b=PersistentBudget(d/'budget.jsonl',run_id=out.name+':'+key,protocol_hash=fingerprint(p),max_calls=1,max_tokens=77824,max_tools=0,max_cost_microusd=1000000,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=20000,wall_seconds=900)
   auth=dict(run_id=b.config['run_id'],protocol_hash=b.config['protocol_hash'],model='deepseek-flash',protocol=VERSION,max_cost_microusd=1000000,paid_api_authorized=True);save(d/'authorization.json',auth)
   adapter=SemanticAdapter(d/'provider.jsonl',b,model='deepseek-flash',authorization=auth,max_wire_input_upper=65536);c=BoundedCompiler(adapter,b,d/'compiler.jsonl','deepseek-flash',max_input_upper=65536,max_output_upper=12288)
   job=dict(stream_id=b.config['run_id'],family_id='frozen-semantic',semantic_input=v)
   save(d/'specification.json',dict(solver_sha256=v['solver_sha256'],condition=v['condition'],algorithm_immutable=True));job['specification']=c.import_specification(job,d/'specification.json',time.time())
   try:
    response=c.request(job,'candidate',0,time.time(),output_upper=12288);save(d/'response.json',response);(d/'matcher.py').write_text(response['code']);contract=json.loads(response['description'])
    if json.loads(contract['parameter_schema'])!=v['parameter_schema']:raise ValueError('PARAMETER_SCHEMA_CHANGED')
    a=artifact(d/'artifacts',v['solver_code'],response['code'],contract,provenance=dict(origin=response['origin'],model=response['model'],response_sha256=response['response_sha256'],solver_parent=str(OLD/key.rsplit('_',1)[0]/'solver.py'),solver_sha256=v['solver_sha256'],excluded_task_ids=[t['task_id'] for t in v['source_problems']]))
    assert a['solver_sha256']==v['solver_sha256'];save(d/'artifact.json',a);VersionGate(out/'registry.jsonl').shadow(a)
    result=dict(key=key,status='SHADOW',joint_sha256=a['code_sha256'])
   except (ValueError,TypeError,KeyError) as e:result=dict(key=key,status='REJECTED',error=str(e))
   save(d/'result.json',result);results.append(result);print(json.dumps(result),flush=True)
  save(out/'GENERATION_COMPLETE.json',results)
 except BaseException as e:save(out/'STOP.json',dict(error=type(e).__name__,message=str(e),completed=results,no_resend=True));raise
 finally:save(out/'history_integrity.json',{r:sha(r)==h for r,h in p['history_hashes'].items()})
if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]).resolve())
