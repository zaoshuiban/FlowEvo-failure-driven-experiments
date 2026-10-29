"""One engineering-only matcher redelivery per known response, then test proposals.
The algorithm bytes and all mathematical hypotheses remain immutable. No scores read.
"""
import sys,json,time
from pathlib import Path
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.math_v3_component_generation import DeepSeekComponentAdapter
from failure_evo.contracts import canonical,fingerprint
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.semantic_contract import artifact,SplitRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.operator_test_generation import parse_proposals,IndependentOracle
from failure_evo.operator_version_gate import VersionGate
from code_math.no_gold import PublicMathTask
class DeliveryRepair(DeepSeekComponentAdapter):
 protocol='math-v3-component-deepseek-engineering-repair-v1'
 def preflight(self,r):
  b=super().preflight(r)
  if r['slot']==1:
   b['messages'][0]['content']+=' ENGINEERING REDELIVERY ONLY. Previous output failed the format contract or was truncated. Preserve the algorithm and its mathematical assumptions. Keep matcher concise, at most 150 source lines. Do not emit top-level type. The description must be a JSON-encoded object whose EVERY value is a string, INCLUDING parameter_schema. Thus parameter_schema must itself be JSON-encoded, never an object. No domain-specific corrective hint or scoring result is provided.'
   p=json.loads(b['messages'][1]['content']);p['previous_raw_content']=r['previous_raw_content'];p['engineering_diagnostics']=r['engineering_diagnostics'];b['messages'][1]['content']=canonical(p)
  if len(canonical(b).encode())+256>self.max_wire_input_upper:raise ValueError('wire bound')
  return b

def run(source,out):
 if out.exists():raise RuntimeError('new run required')
 rows=json.loads((source/'evidence.json').read_text());p=json.loads((source/'protocol.json').read_text())
 plan=dict(version=DeliveryRepair.protocol,source_run=str(source),order=['F1','F2','T2','F3','T3'],model='deepseek-flash',thinking='disabled',max_calls=10,max_per_candidate=2,revision_limit=1,output_upper=12288,source_hashes={str(x.relative_to(ROOT)):sha(x) for x in list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__)]},old_files={str(x):sha(x) for x in source.rglob('*') if x.is_file()},evidence_hash=fingerprint(rows))
 save(out/'protocol.json',plan);save(out/'freeze.json',dict(sha256=fingerprint(plan)));save(out/'evidence.json',rows)
 for rel in plan['source_hashes']:
  dest=out/'frozen_source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/rel).read_bytes())
 results=[]
 try:
  for name in plan['order']:
   old=source/name;d=out/name;d.mkdir();solver=json.loads((old/'solver_response.json').read_text());imp=json.loads((old/'mechanism_import.json').read_text());m=imp['mechanism']
   save(d/'mechanism_import.json',imp);save(d/'solver_response.json',solver);(d/'solver.py').write_bytes((old/'solver.py').read_bytes())
   raw=[json.loads(l)['payload']['response'] for l in (old/'provider.jsonl').read_text().splitlines() if json.loads(l)['kind']=='RAW_RESPONSE'][-1]
   content=raw['choices'][0]['message'].get('content','');diagnostic=json.loads((old/'result.json').read_text())
   b=PersistentBudget(d/'budget.jsonl',run_id=out.name+':'+name,protocol_hash=fingerprint(plan),max_calls=2,max_tokens=155648,max_tools=0,max_cost_microusd=4000000,token_rate_microusd_per_million=15000000,tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=20000,wall_seconds=1800)
   grant=dict(run_id=b.config['run_id'],protocol_hash=b.config['protocol_hash'],model='deepseek-flash',protocol=DeliveryRepair.protocol,max_cost_microusd=4000000,paid_api_authorized=True);save(d/'authorization.json',grant)
   a=DeliveryRepair(d/'provider.jsonl',b,model='deepseek-flash',authorization=grant,max_wire_input_upper=65536);c=BoundedCompiler(a,b,d/'compiler.jsonl','deepseek-flash',max_input_upper=65536,max_output_upper=12288)
   job=dict(stream_id=b.config['run_id'],family_id='engineering-redelivery',arm=name[0],source_ids=m['source_evidence_ids'],discovery={'events':rows},solver_code=solver['code'],parameter_schema=json.loads(solver['applicability']),algorithm_assumptions=solver['description'],previous_raw_content=content,engineering_diagnostics=diagnostic)
   save(d/'specification.json',m);job['specification']=c.import_specification(job,d/'specification.json',time.time())
   try:
    matcher=c.request(job,'candidate',1,time.time(),output_upper=12288);save(d/'matcher_response.json',matcher);(d/'matcher.py').write_text(matcher['code']);contract=json.loads(matcher['description'])
    if json.loads(contract['parameter_schema'])!=job['parameter_schema']:raise ValueError('schema changed')
    art=artifact(d/'artifacts',solver['code'],matcher['code'],contract,provenance=dict(origin='DEEPSEEK',solver_response_sha256=solver['response_sha256'],matcher_response_sha256=matcher['response_sha256'],parent_solver=str(old/'solver.py'),source_evidence_ids=m['source_evidence_ids'],model='deepseek-flash',excluded_task_ids=[x['task_id'] for x in rows]))
    save(d/'artifact.json',art);VersionGate(out/'registry.jsonl').shadow(art)
    runner=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),d/'worker.jsonl');save(d/'engineering.json',[runner.run(art,PublicMathTask(x['task_id'],x['task']['problem'])) for x in rows if x['evidence_id'] in m['source_evidence_ids']])
    job['contract']=contract;tests=c.request(job,'candidate',2,time.time(),output_upper=12288);save(d/'test_response.json',tests)
    proposals=parse_proposals(json.loads(tests['code']));save(d/'test_proposals.json',IndependentOracle([],candidate_hashes=[art['solver_sha256'],art['matcher_sha256']]).audit_all(proposals))
    result=dict(name=name,status='SHADOW',proposals=len(proposals),joint_sha256=art['code_sha256'])
   except (ValueError,TypeError,KeyError) as e:result=dict(name=name,status='PARTIAL',error=str(e))
   save(d/'result.json',result);results.append(result);print(json.dumps(result),flush=True)
  save(out/'COMPLETE.json',results)
 except BaseException as e:save(out/'STOP.json',dict(error=type(e).__name__,message=str(e),results=results));raise
 finally:save(out/'history_integrity.json',{p:sha(p)==h for p,h in plan['old_files'].items()})
if __name__=='__main__':run(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
