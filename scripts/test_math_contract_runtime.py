"""Host boundary and recovery tests; real Worker acceptance is a separate script."""
import unittest,tempfile,copy
from pathlib import Path
from types import SimpleNamespace
from failure_evo.evidence import EvidenceStore
from failure_evo.math_contract_runtime import ContractShadow
from failure_evo.operator_contract import receive_contract,attach_contract,binding
from test_operator_contract import ContractTests

class RuntimeTests(ContractTests):
 def test_partial_journal_never_grants_permission(self):
  from failure_evo.operator_contract import require_release
  self.approve()
  with self.registry.events.path.open('ab') as f:f.write(b'{')
  with self.assertRaises(ValueError):require_release(self.registry,self.a)
 def test_pending_validator_cannot_reuse_older_pass(self):
  from failure_evo.operator_contract import require_release
  self.approve()
  self.registry.events.append('OPERATOR_VALIDATOR_STARTED',dict(binding=binding(self.a),stage='SOURCE',execution_id='unresolved'),__import__('time').time())
  with self.assertRaises(PermissionError):require_release(self.registry,self.a)
 def test_unresolved_execution_blocks_global_health(self):
  from failure_evo.math_stream import StreamRuntime
  from failure_evo.contracts import fingerprint
  from failure_evo.run_health import RunUnhealthy
  stream=StreamRuntime.__new__(StreamRuntime);stream.plan={};stream.ph=fingerprint({});stream.path=Path(self.tmp.name);stream.arms={'F':{'registry':self.registry}}
  self.registry.events.append('OPERATOR_VALIDATOR_STARTED',dict(binding=binding(self.a),stage='SOURCE',execution_id='unknown'),__import__('time').time())
  with self.assertRaises(RunUnhealthy):stream.health()
 def test_unresolved_publication_blocks_before_next_solver(self):
  from failure_evo.math_stream import StreamRuntime
  from failure_evo.contracts import fingerprint
  from failure_evo.run_health import RunUnhealthy
  stream=StreamRuntime.__new__(StreamRuntime);stream.plan={};stream.ph=fingerprint({});stream.path=Path(self.tmp.name);stream.arms={'F':{'registry':self.registry}}
  self.registry.events.append('CONTRACT_RELEASE_RESUME_STARTED',dict(version='unknown-version'),0)
  with self.assertRaises(RunUnhealthy):stream.health()
 def test_interrupted_publication_is_not_replayed(self):
  from failure_evo.math_stream_learning import ReviewedRelease
  from failure_evo.run_health import RunUnhealthy
  self.a['candidate_version']=binding(self.a)
  self.registry.events.append('CONTRACT_RELEASE_PENDING',dict(artifact=self.a,path=self.tmp.name),0)
  self.registry.events.append('CONTRACT_RELEASE_RESUME_STARTED',dict(version=self.a['candidate_version']),1)
  release=ReviewedRelease(SimpleNamespace(arms={'F':{'registry':self.registry}}),'F')
  with self.assertRaises(RunUnhealthy):release.poll_contract(3)
 def test_shadow_started_without_response_blocks(self):
  from code_math.no_gold import PublicMathTask
  from failure_evo.contracts import fingerprint
  from failure_evo.run_health import RunUnhealthy
  self.a.update(candidate_created_after=0,excluded_task_ids=[])
  self.registry.shadow(self.a);self.approve()
  task=PublicMathTask('future','public')
  state=dict(path=Path(self.tmp.name),registry=self.registry,states=EvidenceStore(Path(self.tmp.name)/'states'))
  s=SimpleNamespace(arms={'F':state},engineering=True,lineage={'future':{'source_original_id':'future-original'}})
  eid=fingerprint([binding(self.a),'future',1,'shadow-v1'])
  self.registry.events.append('CONTRACT_SHADOW_STARTED',dict(execution_id=eid),__import__('time').time())
  shadow=ContractShadow(s,'F',[dict(task_id='future',problem_sha256=fingerprint('public'),gold_answer='1')])
  with self.assertRaises(RunUnhealthy):shadow.observe(task,1)
 def test_static_permission_examples(self):
  from failure_evo.semantic_contract import component_check
  for code in ('import subprocess\ndef solve(p):return subprocess.run(p)', 'import socket\ndef solve(p):return socket.socket()', 'def solve(p):return open(p)', 'def solve(p):return eval(p)'):
   self.assertFalse(component_check(code,'solve')['passed'])
 def test_single_source_not_reusable(self):
  self.a['source_original_ids']=['only-one']
  self.approve()
  from failure_evo.operator_contract import require_release
  with self.assertRaises(PermissionError):require_release(self.registry,self.a)
 def test_source_identity_changes_version(self):
  old=binding(self.a);self.a['source_original_ids'].append('new')
  self.assertNotEqual(old,binding(self.a))
 def test_external_schema_not_accepted(self):
  for schema in ({'$ref':'https://example.invalid/private'},{'type':'impossible'},{'type':'string','pattern':'(a+)+$'},{'type':'object','properties':[]}):
   c=copy.deepcopy(self.a['operator_contract']);c['input_schema']=schema
   with self.assertRaises(ValueError):receive_contract(c)
 def test_no_score_without_baseline_lock(self):
  from code_math.no_gold import PublicMathTask
  state=dict(path=Path(self.tmp.name),registry=self.registry,states=EvidenceStore(Path(self.tmp.name)/'states'))
  s=SimpleNamespace(arms={'F':state},engineering=True)
  shadow=ContractShadow(s,'F',[dict(task_id='t',problem_sha256='unused',gold_answer='1')])
  with self.assertRaises(PermissionError):shadow.finalize(PublicMathTask('t','public'),{'locked_sha256':'fake'})
 def test_mock_cannot_authorize_real_candidate(self):
  self.approve();self.a['origin']='DEEPSEEK'
  from failure_evo.operator_contract import require_release
  with self.assertRaises(PermissionError):require_release(self.registry,self.a)
if __name__=='__main__':unittest.main()
