"""Zero API: copied ledgers only; no real authorization or generated code execution."""
import sys,tempfile,time,json,unittest,itertools
from pathlib import Path
import experiment_s16c2_reuse as x
from failure_evo.workflow_policy import WorkflowRegistry
from failure_evo.contracts import fingerprint
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.folder=Path(self.tmp.name)/'s16c2-fixture';self.folder.mkdir()
  (self.folder/'registry.jsonl').write_bytes((x.OLD/'registry.jsonl').read_bytes())
  self.reg=x.RenewedRegistry(self.folder/'registry.jsonl',x.e.FailureEvidenceStore(x.OLD/'evidence_F.jsonl'))
  self.card=x.WorkflowPolicy.from_dict(x.read(x.OLD/'summary.json')['cards'][0]['card'])
  self.grant=x.make_grant(self.reg,self.card,self.folder,['taco_0914','taco_0657'])
 def tearDown(self):self.tmp.cleanup()
 def reserve(self,tid):return self.reg.reserve_opportunity(self.card,stream_id=self.folder.name+'-F',experiment_id=self.folder.name,task_index=1,task_id=tid,checkpoint='l2a',hook='before_native_retry',program_sha256='a'*64,at=time.time())
 def test_bounded_extension_preserves_history(self):
  before=self.reg.state(self.card);self.reg.extend(self.card,self.grant,time.time());state=self.reg.state(self.card)
  self.assertEqual((state['opportunity_limit'],state['opportunities_used'],state['opportunities_remaining']),(3,1,2));self.assertEqual(before['completed'],state['completed'])
  for tid in ('taco_0914','taco_0657'):
   token=self.reserve(tid);self.assertTrue(token)
   self.reg.complete_opportunity(self.card,token,outcome=dict(status='declined',actual_cost=dict(tool_calls=1,model_calls=0,elapsed_seconds=.1)),at=time.time())
  self.assertFalse(self.reserve('taco_0914'));self.assertEqual(self.reg.state(self.card)['opportunities_remaining'],0)
 def test_old_entry_remains_closed(self):
  self.reg.extend(self.card,self.grant,time.time());old=WorkflowRegistry(self.folder/'registry.jsonl',self.reg.evidence)
  self.assertEqual(old.state(self.card)['opportunities_remaining'],0)
 def test_allowlist_and_duplicate_renewal(self):
  self.reg.extend(self.card,self.grant,time.time());self.assertFalse(self.reserve('unlisted'))
  with self.assertRaises(ValueError):self.reg.extend(self.card,self.grant,time.time())
 def test_suspended_cannot_extend(self):
  self.reg.suspend(self.card,'fixture',time.time())
  with self.assertRaises(ValueError):self.reg.extend(self.card,self.grant,time.time())
 def test_grant_tamper_invalidates(self):
  self.reg.extend(self.card,self.grant,time.time());self.assertTrue(self.reg.valid(self.card,None));self.grant.write_text('{}');self.assertFalse(self.reg.valid(self.card,None));self.assertFalse(self.reserve('taco_0914'))
 def test_wrong_binding_rejected(self):
  g=x.read(self.grant);g['artifact_sha256']='wrong';x.write(self.grant,g)
  with self.assertRaises(ValueError):self.reg.extend(self.card,self.grant,time.time())
 def test_oracles_and_fixed_selection(self):
  self.assertEqual(x.beauty([6,6,6]),1);self.assertEqual(x.beauty([2,5,4,5,2,4]),3);self.assertEqual(x.beauty([1,3,2,2]),2)
  self.assertEqual(x.dishes([[1,2,3],[3,2],[4,5]]),8);self.assertEqual(x.dishes([[1,2],[4,5]]),4);self.assertEqual(x.dishes([[1,2],[3,2,5],[4,5]]),10)
  items,_=x.selection();self.assertEqual([i['task']['task_id'] for i in items],['taco_0914','taco_0657']);self.assertTrue(len(x.MEMORY.encode())<=1500)
 def test_shared_preflight_accepts_saved_M_retry(self):
  wf=x.read(x.C/'M_workflow.json');raw=x.read(x.C/'wire/solve/2/response.json')['choices'][0]
  msg,_=x.repair_messages(x.read(x.C/'checkpoint.json')['public_evidence']['task_public'],raw['message']['content'],wf['events'][0]['public_feedback'],finish_reason='length',memory=x.MEMORY)
  p=x.prepare(msg,limits=x.Limits(input_token_upper=65536));self.assertLess(p.input_upper,65536)
if __name__=='__main__':unittest.main()
