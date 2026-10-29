"""Paired source-disjoint semantic-contract experiment; existing compiler and Worker.
No mathematics regenerated, no outcome-adaptive prompts or revisions.
"""
import json,sys,time,urllib.request,random
from pathlib import Path
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.math_v31_semantic import SYSTEM
from failure_evo.autonomous_generation import DeepSeekCompilerAdapter
from failure_evo.contracts import canonical,fingerprint
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.semantic_contract import artifact
from failure_evo.model_api import configured_api_key
VERSION='math-v32-source-disjoint-semantic-v1'
class Adapter(DeepSeekCompilerAdapter):
 protocol=VERSION
 def preflight(self,r):
  self._authorize()
  if not self.mock and not configured_api_key():raise PermissionError('DeepSeek credential')
  if r['phase']!='candidate' or r['slot']!=0:raise PermissionError('one candidate only')
  v=r['semantic_input'];required={'solver_code','solver_sha256','parameter_schema','source_problems'}
  if set(v) not in (required,required|{'historical_observations'}):raise ValueError('exact input keys')
  import hashlib
  if hashlib.sha256(v['solver_code'].encode()).hexdigest()!=v['solver_sha256']:raise ValueError('algorithm changed')
  for t in v['source_problems']:
   if set(t)!={'task_id','problem'}:raise ValueError('public source')
  for e in v.get('historical_observations',[]):
   if set(e)!={'task','supported_by_prior_review','observed_match','observed_status','reason','source_record_sha256','source_run','source_lock'}:raise ValueError('evidence projection')
   if set(e['task'])!={'task_id','problem'}:raise ValueError('public evidence task')
   if set(e['observed_match'])-{'status','parameters','reason','assumption_quotes','requested_quantity'}:raise ValueError('match-only feedback')
  body=dict(model=self.model,messages=[dict(role='system',content=SYSTEM),dict(role='user',content=canonical(v))],max_tokens=r['max_tokens'],thinking={'type':'disabled'},reasoning_effort='none',temperature=.2,stream=False,response_format={'type':'json_object'})
  if len(canonical(body).encode())+256>self.max_wire_input_upper:raise ValueError('wire bound')
  return body

def load(p):return json.loads(p.read_text())
def freeze(out):
 if (out/'protocol.json').exists():raise RuntimeError('already frozen')
 data=out/'data_v2';manifest=load(data/'manifest.json');base=load(data/'shared_generation_input.json');evidence=load(data/'historical_evidence.json')
 order=['T1','F1','F2','T2','T3','F3'];inputs={k:dict(base,**({'historical_observations':evidence} if k.startswith('F') else {})) for k in order}
 files=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/prepare_math_v32.py',ROOT/'scripts/evaluate_math_v32.py']
 plan=dict(version=VERSION,created_at=time.time(),data_manifest_sha256=sha(data/'manifest.json'),data='data_v2',discarded_preflight_data='data: never sent/evaluated; corrected negative-case lineage hash to derive from actual problem, not unused numeric scaffold; no model outcomes used',model='deepseek-flash',temperature=.2,output_tokens=12288,input_upper=65536,order=order,max_requests=6,replicates_per_arm=3,revisions=0,algorithm_sha256=base['solver_sha256'],inputs_sha256=fingerprint(inputs),source_hashes={str(p.relative_to(ROOT)):sha(p) for p in files},no_p_control='Offline compatible tokenizer unavailable locally. No claim of knowledge-specific effect independent of length; matched model/output ceilings, actual input costs reported.',gate_policy=manifest['gate_policy'],selection='All static-valid F/T replicas frozen before any Development or Gate output; no best-of selection; exactly one Gate evaluation per frozen code, no revision/admission',history_files={str(p):sha(p) for name in ['math_v31_semantic_20261027_01','math_v3_components_deepseek_repair_20261027_01'] for p in (ROOT/'runs'/name).rglob('*') if p.is_file()})
 save(out/'protocol.json',plan);save(out/'inputs.json',inputs);save(out/'freeze.json',dict(sha256=fingerprint(plan)))
 (out/'pricing.html').write_bytes(urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing',timeout=30).read())
 for rel in plan['source_hashes']:
  dest=out/'frozen_source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/rel).read_bytes())
 # zero API projection checks. Neither new Development nor Gate text may occur in any generation wire.
 checks=[]
 adapter=Adapter(out/'preflight.jsonl',None,model='deepseek-flash',mock=True,sender=lambda x:None,max_wire_input_upper=65536)
 public=[*load(data/'public/development.json'),*load(data/'public/gate.json')]
 for k,v in inputs.items():
  w=adapter.preflight(dict(phase='candidate',slot=0,semantic_input=v,max_tokens=12288));text=canonical(w)
  assert not any(t['problem'] in text for t in public)
  assert 'gold_answer' not in text and 'reference_answer' not in text
  checks.append(dict(key=k,bytes=len(text.encode()),new_evaluation_text_absent=True,solver_sha256=v['solver_sha256']))
 save(out/'zero_api_preflight.json',checks)
 print('FROZEN',fingerprint(plan),flush=True)
def generate(out):
 p=load(out/'protocol.json');assert fingerprint(p)==load(out/'freeze.json')['sha256'];assert all(sha(ROOT/k)==h for k,h in p['source_hashes'].items());inputs=load(out/'inputs.json');assert fingerprint(inputs)==p['inputs_sha256'];results=[]
 try:
  for key in p['order']:
   d=out/key
   if d.exists():raise RuntimeError('consumed; no retry')
   d.mkdir();v=inputs[key];(d/'solver.py').write_text(v['solver_code'])
   b=PersistentBudget(d/'budget.jsonl',run_id=out.name+':'+key,protocol_hash=fingerprint(p),max_calls=1,max_tokens=77824,max_tools=0,max_cost_microusd=1000000,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=20000,wall_seconds=900)
   grant=dict(run_id=b.config['run_id'],protocol_hash=b.config['protocol_hash'],model='deepseek-flash',protocol=VERSION,max_cost_microusd=1000000,paid_api_authorized=True);save(d/'authorization.json',grant)
   a=Adapter(d/'provider.jsonl',b,model='deepseek-flash',authorization=grant,max_wire_input_upper=65536);c=BoundedCompiler(a,b,d/'compiler.jsonl','deepseek-flash',max_input_upper=65536,max_output_upper=12288)
   job=dict(stream_id=b.config['run_id'],family_id='semantic-only',semantic_input=v);save(d/'specification.json',dict(solver_sha256=v['solver_sha256'],only_match=True));job['specification']=c.import_specification(job,d/'specification.json',time.time())
   try:
    r=c.request(job,'candidate',0,time.time(),output_upper=12288);save(d/'response.json',r);(d/'matcher.py').write_text(r['code']);contract=json.loads(r['description'])
    if json.loads(contract['parameter_schema'])!=v['parameter_schema']:raise ValueError('PARAMETER_SCHEMA_CHANGED')
    art=artifact(d/'artifacts',v['solver_code'],r['code'],contract,provenance=dict(origin=r['origin'],model=r['model'],response_sha256=r['response_sha256'],request_sha256=r['wire_sha256'],solver_sha256=v['solver_sha256'],condition=key[0]))
    save(d/'artifact.json',art);result=dict(key=key,status='STATIC_VALID_SHADOW',joint_sha256=art['code_sha256'])
   except (ValueError,TypeError,KeyError) as e:result=dict(key=key,status='REJECTED',reason=str(e))
   save(d/'result.json',result);results.append(result);print(json.dumps(result),flush=True)
  save(out/'GENERATION_COMPLETE.json',results)
 except BaseException as e:save(out/'STOP.json',dict(type=type(e).__name__,message=str(e),results=results,no_resend=True));raise
 finally:save(out/'history_integrity.json',{k:sha(k)==h for k,h in p['history_files'].items()})
if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]).resolve())
