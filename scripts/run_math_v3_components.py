"""Single bounded component-delivery follow-up, same historical mechanisms F/T."""
import json,sys,time,hashlib,subprocess,urllib.request,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import fingerprint,canonical
from failure_evo.math_v3_component_generation import ComponentAdapter,DeepSeekComponentAdapter,VERSION
from failure_evo.semantic_contract import artifact,SplitRunner,component_check
from failure_evo.corrective_mechanism import parse
from failure_evo.operator_test_generation import parse_proposals,IndependentOracle
from failure_evo.operator_version_gate import VersionGate
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from code_math.no_gold import PublicMathTask
from run_math_v3_development import WORKER,IMAGE,save,sha

def run(source,out,deepseek=False):
 model_name="deepseek-flash" if deepseek else "gpt-5.4"
 adapter=DeepSeekComponentAdapter if deepseek else ComponentAdapter
 version=adapter.protocol
 if out.exists():raise RuntimeError('new run only')
 # Import completed mechanisms only; never resume or replay the interrupted provider job.
 if not (source/'protocol.json').exists():raise RuntimeError('missing historical protocol')
 p=json.loads((source/'protocol.json').read_text());rows=json.loads((source/'evidence.json').read_text())
 for spec in p['order']:
  parse(json.loads((source/(spec['arm']+str(spec['group']+1))/'mechanism.json').read_text())['normalized'])
 model=next(x for x in json.load(urllib.request.urlopen('https://openrouter.ai/api/v1/models',timeout=30))['data'] if x['id']=='openai/gpt-5.4')
 if float(model['pricing']['completion'])>.000015 or float(model['pricing']['prompt'])>.0000025:raise RuntimeError('price changed')
 backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
 plan=dict(model_catalog=model,worker=backend.manifest(),git_sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),historical_files={str(x.relative_to(ROOT)):sha(x) for x in source.rglob('*') if x.is_file()},design_sha256=sha(ROOT/'reports/math_no_gold_p0_20261027/data/public/design.jsonl'),version=version,prior_run=str(source),prior_protocol_sha256=fingerprint(p),order=p['order'],generation='one solve then one match then one test request; no re-induction; no revision',max_calls_per_arm_group=3,input_upper=65536,output_upper=8192,
  model=model_name,reasoning='disabled' if deepseek else 'low',derived_reservation_per_job_usd=4,source_hashes={str(x.relative_to(ROOT)):sha(x) for x in list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__).resolve()]})
 save(out/'evidence.json',rows)
 save(out/'protocol.json',plan);ph=fingerprint(plan);save(out/'freeze.json',dict(sha256=ph));results=[]
 for rel in plan['source_hashes']:
  dst=out/'frozen_source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((ROOT/rel).read_bytes())
 try:
  for spec in plan['order']:
   arm=spec['arm'];g=spec['group'];name=arm+str(g+1);prior=source/name;d=out/name
   mechanism=json.loads((prior/'mechanism.json').read_text())['normalized'];parse(mechanism)
   if mechanism['generation_decision']!='PROPOSE_CORRECTION':results.append(dict(name=name,status=mechanism['generation_decision']));continue
   d.mkdir();save(d/'mechanism_original.json',json.loads((prior/'mechanism.json').read_text()));save(d/'mechanism_import.json',dict(mechanism=mechanism,prior_response_path=str(prior/'provider.jsonl'),prior_response_file_sha256=sha(prior/'provider.jsonl'),new_induction_calls=0))
   b=PersistentBudget(d/'budget.jsonl',run_id=out.name+':'+name,protocol_hash=ph,max_calls=3,max_tokens=221184,max_tools=0,max_cost_microusd=4000000,token_rate_microusd_per_million=15000000,tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=20000,wall_seconds=1800)
   grant=dict(run_id=b.config['run_id'],protocol_hash=ph,model=model_name,protocol=version,max_cost_microusd=4000000,paid_api_authorized=True);save(d/'authorization.json',grant)
   a=adapter(d/'provider.jsonl',b,model=model_name,authorization=grant,max_wire_input_upper=65536);c=BoundedCompiler(a,b,d/'compiler.jsonl',model_name,max_input_upper=65536,max_output_upper=8192)
   job=dict(stream_id=b.config['run_id'],family_id='components',arm=arm,source_ids=p['groups'][g],discovery={'events':rows})
   save(d/'specification.json',mechanism);job['specification']=c.import_specification(job,d/'specification.json',time.time())
   try:
    solver=c.request(job,'candidate',0,time.time(),output_upper=8192);save(d/'solver_response.json',solver)
    (d/'solver.py').write_text(solver['code'])
    save(d/'solver_static.json',component_check(solver['code'],'solve'))
    if not component_check(solver['code'],'solve')['passed']:raise ValueError('solver static rejected')
    schema=json.loads(solver['applicability']);job.update(solver_code=solver['code'],parameter_schema=schema,algorithm_assumptions=solver['description'])
    matcher=c.request(job,'candidate',1,time.time(),output_upper=8192);save(d/'matcher_response.json',matcher)
    (d/'matcher.py').write_text(matcher['code'])
    contract=json.loads(matcher['description'])
    if json.loads(contract['parameter_schema'])!=schema:raise ValueError('parameter interface changed by matcher')
    art=artifact(d/'artifacts',solver['code'],matcher['code'],contract,provenance=dict(origin=solver['origin'],solver_response_sha256=solver['response_sha256'],matcher_response_sha256=matcher['response_sha256'],source_evidence_ids=p['groups'][g],excluded_task_ids=[x['task_id'] for x in rows],model=model_name))
    runner=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),d/'worker.jsonl')
    calls=[runner.run(art,PublicMathTask(x['task_id'],x['task']['problem'])) for x in rows if x['evidence_id'] in p['groups'][g]]
    calls.append(runner.run(art,PublicMathTask('none','No mathematical question is supplied.')))
    save(d/'engineering.json',calls);save(d/'artifact.json',art);VersionGate(out/'registry.jsonl').shadow(art)
    job['contract']=contract
    tests=c.request(job,'candidate',2,time.time(),output_upper=8192);save(d/'test_response.json',tests)
    proposals=parse_proposals(json.loads(tests['code']));reviews=IndependentOracle([],candidate_hashes=[art['solver_sha256'],art['matcher_sha256']]).audit_all(proposals);save(d/'test_proposals.json',reviews)
    result=dict(name=name,status='SHADOW',joint_sha256=art['code_sha256'],engineering_statuses=[x['status'] for x in calls],proposed_tests=len(reviews),trusted_generated_tests=0)
   except (ValueError,KeyError,TypeError) as e:result=dict(name=name,status='PARTIAL_COMPONENT_OR_CONTRACT_REJECTION',error=str(e))
   save(d/'result.json',result);results.append(result);print(json.dumps(result),flush=True)
  save(out/'COMPLETE.json',results)
 except BaseException as e:save(out/'STOP.json',dict(error=type(e).__name__,message=str(e),results=results,no_resend=True));raise
 finally:save(out/'history_integrity.json',{rel:sha(ROOT/rel)==h for rel,h in plan['historical_files'].items()})
if __name__=='__main__':run(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),deepseek="--deepseek" in sys.argv)
