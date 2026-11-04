import hashlib,tempfile,unittest
from pathlib import Path
from failure_evo.operator_contract import receive_contract,binding,record_stage,require_release,STAGES
from failure_evo.math_operators import MathOperatorRegistry

class ContractTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.registry=MathOperatorRegistry(Path(self.tmp.name)/'registry')
  code='def solve(parameters):\n return 1\n'
  self.a=dict(source_original_ids=["source-original"],code=code,code_sha256=hashlib.sha256(code.encode()).hexdigest(),operator_contract=dict(
   artifact_kind='REUSABLE_CANDIDATE',input_schema={'type':'object'},output_schema={'type':'integer'},
   preconditions=['finite input'],algorithm='model proposed computation',complexity_bound={'max_items':10},
   failure_modes=['unsupported input'],source_evidence=['event1']))
 def approve(self):
  for stage in STAGES:record_stage(self.registry,self.a,stage=stage,passed=True,data_hash='data',worker_hash='worker',source_original_ids=['independent-original'],independent=True)
 def test_permissions_rejected(self):
  self.a['operator_contract']['validation_status']='verified'
  with self.assertRaises(ValueError):receive_contract(self.a['operator_contract'])
 def test_missing_stage_blocks(self):
  with self.assertRaises(PermissionError):require_release(self.registry,self.a)
 def test_reviews_bind_both_components(self):
  self.approve();require_release(self.registry,self.a)
  self.a['operator_contract']['algorithm']='changed'
  with self.assertRaises(PermissionError):require_release(self.registry,self.a)
 def test_source_change_invalidates(self):
  self.approve();self.a['code']+='\n'
  with self.assertRaises(ValueError):binding(self.a)
 def test_instance_never_reusable(self):
  self.a['operator_contract']['artifact_kind']='INSTANCE_SOLVER';self.approve()
  with self.assertRaises(PermissionError):require_release(self.registry,self.a)
 def test_unknown_gate_provenance_rejected(self):
  with self.assertRaises(PermissionError):record_stage(self.registry,self.a,stage='INDEPENDENT_GATE',passed=True,data_hash='d',worker_hash='w',source_original_ids=['UNKNOWN'],independent=True)
 def test_contract_cannot_bypass_existing_gate(self):
  self.registry.shadow(self.a);self.approve()
  with self.assertRaises(PermissionError):self.registry.admit(self.a,{},after_sequence=1)
if __name__=='__main__':unittest.main()
