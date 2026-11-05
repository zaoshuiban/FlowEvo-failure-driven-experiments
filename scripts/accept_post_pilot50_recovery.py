"""Real Worker fault injection. No model calls or real research permissions."""
import json,tempfile,time,copy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from accept_post_pilot50_validator import fixture,ROOT,problem
from failure_evo.operator_contract import validate_computation_stage,require_release
from failure_evo.math_contract_runtime import validate_safety,ContractShadow
from failure_evo.evidence import EvidenceStore
from failure_evo.contracts import fingerprint
from failure_evo.run_health import RunUnhealthy
from code_math.no_gold import PublicMathTask

class Crash(RuntimeError):pass

def main():
 out=ROOT/'reports/post_pilot50_end_to_end';checks={};trace=[]
 with tempfile.TemporaryDirectory(dir=out) as temp:
  a,reg,runner,cases=fixture(Path(temp))
  # Lost stage write after execution receipt: reconstruct the stage without running again.
  append=reg.events.append;armed=[True]
  def fail_stage(kind,payload,at):
   if kind=='OPERATOR_CONTRACT_REVIEW' and armed[0]:armed[0]=False;raise Crash('after source receipt before stage')
   return append(kind,payload,at)
  with patch.object(reg.events,'append',fail_stage):
   try:validate_computation_stage(reg,a,runner,cases,stage='SOURCE',source_original_ids=['source1'],engineering=True)
   except Crash:checks['source_receipt_before_stage_crashed']=True
  count=len(runner.events.records())
  validate_computation_stage(reg,a,runner,cases,stage='SOURCE',source_original_ids=['source1'],engineering=True)
  checks['source_stage_rebuild_no_worker_replay']=len(runner.events.records())==count
  try:require_release(reg,a)
  except PermissionError:checks['source_only_no_authorization']=True
  # Execute, then lose completion receipt: explicit audit barrier prevents implicit replay.
  a2,reg2,runner2,cases2=fixture(Path(temp)/'uncertain')
  append2=reg2.events.append
  changed=copy.deepcopy(cases);changed[0]['review']['record'].update(parameters={'n':8},answer='36');changed[0]['proposal']['problem']=problem(8)
  armed[0]=True
  def fail_receipt(kind,payload,at):
   if kind=='OPERATOR_VALIDATOR_EXECUTED' and armed[0]:armed[0]=False;raise Crash('executed but receipt not persisted')
   return append2(kind,payload,at)
  with patch.object(reg2.events,'append',fail_receipt):
   try:validate_computation_stage(reg2,a2,runner2,changed,stage='SOURCE',source_original_ids=['source1'],engineering=True)
   except Crash:checks['source_lost_receipt_crashed']=True
  count=len(runner2.events.records())
  try:validate_computation_stage(reg2,a2,runner2,changed,stage='SOURCE',source_original_ids=['source1'],engineering=True)
  except PermissionError:checks['source_lost_receipt_blocks_no_replay']=len(runner2.events.records())==count
  validate_safety(reg,a,runner,engineering=True)
  validate_computation_stage(reg,a,runner,cases,stage='INDEPENDENT_GATE',source_original_ids=['gate1'],independent=True,engineering=True)
  try:require_release(reg,a)
  except PermissionError:checks['gate_without_shadow_no_authorization']=True
  count=len(runner.events.records())
  try:validate_computation_stage(reg,a,runner,changed,stage='INDEPENDENT_GATE',source_original_ids=['gate2'],independent=True,engineering=True)
  except PermissionError:checks['gate_pool_replacement_rejected_before_worker']=len(runner.events.records())==count
  a['candidate_created_after']=0;reg.shadow(a)
  state=dict(path=Path(temp),registry=reg,split=runner,states=EvidenceStore(Path(temp)/'states'))
  task=PublicMathTask('future',problem(9));stream=SimpleNamespace(arms={'F':state},engineering=True,lineage={'future':{'source_original_id':'future-original'}})
  shadow=ContractShadow(stream,'F',[dict(task_id='future',problem_sha256=fingerprint(task.problem),gold_answer='45')])
  shadow.observe(task,1);count=len(runner.events.records())
  # Reconstruct controller after Shadow execution, before baseline lock.
  shadow=ContractShadow(stream,'F',[dict(task_id='future',problem_sha256=fingerprint(task.problem),gold_answer='45')])
  shadow.observe(task,1)
  checks['shadow_executed_resume_no_worker_replay']=len(runner.events.records())==count
  try:shadow.finalize(task,{'locked_sha256':'fake'})
  except PermissionError:checks['shadow_no_baseline_score_rejected']=True
  baseline=dict(task_id='future',final_output='The answer is 0');baseline['locked_sha256']=fingerprint(baseline)
  state['states'].append('ANSWER_LOCKED',dict(task_id='future',lock=baseline),time.time())
  before=copy.deepcopy(baseline);armed[0]=True
  with patch.object(reg.events,'append',fail_stage):
   try:shadow.finalize(task,baseline)
   except Crash:checks['shadow_score_receipt_before_stage_crashed']=True
  nscore=len(shadow.scorer.events.records());shadow.finalize(task,baseline)
  checks['shadow_score_receipt_resume_no_score_replay']=len(shadow.scorer.events.records())==nscore
  checks['baseline_answer_unchanged']=baseline==before
  require_release(reg,a)
  checks['completed_shadow_stages_qualified_not_automatically_authorized']=not any(r['kind']=='MATH_EXPERIMENTAL' for r in reg.events.records())
  trace=reg.events.records()+reg2.events.records()
 result=dict(checks=checks,passed=sum(checks.values()),total=len(checks),registry_events=trace,paid_model_calls=0,engineering_only=True)
 (out/'recovery_acceptance.json').write_text(json.dumps(result,indent=2)+'\n')
 print(checks);assert all(checks.values())
if __name__=='__main__':main()
