import unittest,tempfile,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.symptom_learning import SymptomLearning
from failure_evo.contracts import PublicFeedback

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=pathlib.Path(self.tmp.name)
  self.store=FailureEvidenceStore(self.p/'facts');self.index=SymptomLearning(self.p/'index',self.store,'F');self.now=0
 def record(self,task,code='print(0)',status='WRONG_ANSWER',legal=True,exception=None):
  self.now+=1
  f=PublicFeedback.project(dict(visibility='public',status=status,cases=[dict(visibility='public',legal_verified=legal,input='1',expected='1',actual='0',exception_class=exception)]))
  fact=self.store.record(stream_id='F',task_id=task,family_id='unknown',stage='l1',code=code,feedback=f,observed_at=self.now,available_from=self.now)
  if fact:return fact,self.index.ingest(fact,f,code,remaining_calls=2,at=self.now)
  return None,None
 def test_task_dedup_and_related_group(self):
  a,s=self.record('a');b,t=self.record('a');c,u=self.record('b')
  self.assertEqual(t['independent_task_count'],1);self.assertEqual(u['independent_task_count'],2);self.assertEqual(s['group_id'],u['group_id']);self.assertEqual(u['status'],'UNTESTED')
 def test_different_observation_not_same_cause(self):
  _,a=self.record('a');_,b=self.record('b','def solve():\n pass')
  self.assertNotEqual(a['group_id'],b['group_id']);self.assertFalse(b['applicable_actions'])
 def test_invalid_and_unknown_are_not_certified(self):
  self.assertIsNone(self.record('a',legal=False)[0]);self.assertIsNone(self.record('b',status='RUNTIME_ERROR',exception='UnknownException')[0])
 def test_counterevidence_append_and_revoke(self):
  a,s=self.record('a');b,_=self.record('b');self.index.feedback(s['hypothesis_id'],b['event_id'],supports=False,claim='selection may be wrong',at=3)
  self.assertEqual(self.index.states()[s['hypothesis_id']]['contradicting_evidence_ids'],[b['event_id']]);self.store.revoke(b['event_id'],'invalid source',4)
  job=self.index.schedule(at=4,budget_available=True)[0];self.assertNotIn(b['event_id'],job['evidence_ids'])
 def test_one_witness_no_repeat_and_revision(self):
  self.record('a');j=self.index.schedule(at=1,budget_available=True)[0];self.assertEqual(j['decision'],'GENERATE');self.index.start(j,1);self.index.finish(j,None,1)
  self.assertEqual(self.index.schedule(at=1,budget_available=True),[])
  self.record('b');j=self.index.schedule(at=2,budget_available=True)[0];self.assertEqual(j['decision'],'REVISE')
 def test_budget_and_recovery(self):
  self.record('a');self.assertEqual(self.index.schedule(at=1,budget_available=False),[])
  j=self.index.schedule(at=1,budget_available=True)[0];self.index.start(j,1)
  recovered=SymptomLearning(self.p/'index',self.store,'F');self.assertEqual(recovered.schedule(at=1,budget_available=True),[])
  with self.assertRaises(ValueError):recovered.start(j,1)
if __name__=='__main__':unittest.main()
