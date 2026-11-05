"""Real existing SplitRunner -> independent fixture oracle -> registry receipt."""
import json,tempfile
from pathlib import Path
from run_math_v3_development import ROOT,IMAGE,WORKER
from run_math_manual_lifecycle import SOLVE,MATCH,problem
from failure_evo.semantic_contract import artifact,SplitRunner,FIELDS
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.operator_version_gate import VersionGate
from failure_evo.operator_contract import attach_contract,validate_computation_stage,record_stage

def fixture(directory):
 p=Path(directory);contract={k:'ENGINEERING_ONLY' for k in FIELDS}
 contract.update(requested_quantity='integer sum',parameter_schema=json.dumps(dict(type='object',properties=dict(n=dict(type='integer',minimum=0,maximum=10000)),required=['n'],additionalProperties=False)))
 a=artifact(p/'artifact',SOLVE,MATCH,contract,provenance=dict(origin='MOCK',excluded_task_ids=['source']))
 proposal=dict(artifact_kind='REUSABLE_CANDIDATE',input_schema={'type':'object'},output_schema={'type':'string'},preconditions=['fixture'],algorithm='fixture only',complexity_bound={'n':10000},failure_modes=['other targets'],source_evidence=['e1','e2'])
 a=attach_contract(a,proposal,evidence_ids=['e1','e2'],protocol='engineering',original_ids=['source1','source2'])
 reg=VersionGate(p/'registry.jsonl');reg.shadow(a)
 runner=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),p/'worker.jsonl')
 cases=[dict(proposal=dict(problem=problem(7)),review=dict(status='VERIFIED',record=dict(supported=True,parameters={'n':7},answer='28'))),dict(proposal=dict(problem='Compute the product of integers from 1 through 4, inclusive.'),review=dict(status='VERIFIED',record=dict(supported=False,parameters=None,answer='24')))]
 return a,reg,runner,cases

def main():
 out=ROOT/'reports/post_pilot50_end_to_end'
 with tempfile.TemporaryDirectory(dir=out) as tmp:
  p=Path(tmp)
  a,reg,runner,cases=fixture(p)
  from failure_evo.math_contract_runtime import validate_safety
  safety=validate_safety(reg,a,runner,engineering=True)
  assert safety['passed']
  first=validate_computation_stage(reg,a,runner,cases,stage='SOURCE',source_original_ids=['source1'],engineering=True)
  count=len(runner.events.records())
  second=validate_computation_stage(reg,a,runner,cases,stage='SOURCE',source_original_ids=['source1'],engineering=True)
  assert len(runner.events.records())==count
  gate=validate_computation_stage(reg,a,runner,cases,stage='INDEPENDENT_GATE',source_original_ids=['gate1'],independent=True,engineering=True)
  assert first['passed'] and gate['passed']
  from types import SimpleNamespace
  from failure_evo.math_contract_runtime import ContractShadow
  from failure_evo.evidence import EvidenceStore
  from code_math.no_gold import PublicMathTask
  a['candidate_created_after']=0
  reg.shadow(a)
  state=dict(path=p,registry=reg,split=runner,states=EvidenceStore(p/'states'))
  stream=SimpleNamespace(arms={'F':state},engineering=True,lineage={'future':{'source_original_id':'future-original'}})
  task=PublicMathTask('future',problem(9))
  shadow=ContractShadow(stream,'F',[dict(task_id='future',problem_sha256=__import__('failure_evo.contracts',fromlist=['fingerprint']).fingerprint(task.problem),gold_answer='45')])
  shadow.observe(task,1)
  baseline={'locked_sha256':'independent-baseline-lock'}
  state['states'].append('ANSWER_LOCKED',dict(task_id='future',lock=baseline),__import__('time').time())
  shadow.finalize(task,baseline)
  shadow.finalize(task,baseline)
  from failure_evo.operator_contract import require_release
  require_release(reg,a)
  assert len([r for r in reg.events.records() if r['kind']=='OPERATOR_CONTRACT_REVIEW' and r['payload']['stage']=='SHADOW_OBSERVATION'])==1
  rejected=False
  try:record_stage(reg,a,stage='STATIC_SAFETY',passed=True,data_hash='fake',worker_hash='fake',source_original_ids=['x'])
  except PermissionError:rejected=True
  assert rejected
  result=dict(engineering_fixture=True,real_linux_worker=True,source=first,gate=gate,safety=safety,shadow_scored=True,baseline_unchanged=baseline=={'locked_sha256':'independent-baseline-lock'},resume_reexecutes_worker=False,forged_boolean_rejected=rejected,api_calls=0,not_real_generalization=True,registry_events=reg.events.records(),component_events=runner.events.records(),solver_source=SOLVE,matcher_source=MATCH)
  (out/'validator_acceptance.json').write_text(json.dumps(result,indent=2)+'\n')
  print('SOURCE/Gate executed; cached resume; forged boolean rejected; engineering only')
if __name__=='__main__':main()
