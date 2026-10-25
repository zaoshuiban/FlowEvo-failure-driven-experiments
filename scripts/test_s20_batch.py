"""Zero-provider-API real runner batch recovery checks."""
import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import run_workflow_v2 as e
from run_learning_stream import LearningStream
from test_s19_v2 import Provider, FakeJudge, tasks, plan

class Tests(unittest.TestCase):
 def test_pause_resume_each_arm(self):
  for arm in ('G','M','F'):
   with self.subTest(arm=arm), tempfile.TemporaryDirectory() as tmp, patch.object(e.prior,'Judge',FakeJudge):
    provider=Provider();p=plan(arm);folder=Path(tmp)/arm
    r=e.ExperimentRunner(folder,p,provider.factory)
    s=LearningStream(r,tasks(3),arm=arm,batch_size=1)
    s.run(stop_after_batch=1)
    rows=s.log.records()
    self.assertEqual(sum(x['kind']=='TASK_FINALIZED' for x in rows),1)
    self.assertEqual(sum(x['kind']=='BATCH_FINALIZED' for x in rows),1)
    self.assertFalse(any(x['kind']=='ONLINE_LOCKED' for x in rows))
    calls=dict(provider.calls)
    r=e.ExperimentRunner(folder,p,provider.factory,resume=True)
    s=LearningStream(r,tasks(3),arm=arm,batch_size=1)
    with patch.object(s,'boundary',side_effect=AssertionError('completed boundary replayed')):
     s.run(stop_after_batch=1)
    self.assertEqual(calls,provider.calls)
    with self.assertRaises(ValueError):LearningStream(r,tasks(2),arm=arm,batch_size=1)
    s.run(stop_after_batch=2)
    self.assertFalse(any(x['kind']=='ONLINE_LOCKED' for x in s.log.records()))
    s.run(stop_after_batch=3)
    self.assertEqual(sum(x['kind']=='ONLINE_LOCKED' for x in s.log.records()),1)
    calls=dict(provider.calls);s.run();self.assertEqual(calls,provider.calls)
 def test_invalid_limit(self):
  with tempfile.TemporaryDirectory() as tmp, patch.object(e.prior,'Judge',FakeJudge):
   s=LearningStream(e.ExperimentRunner(Path(tmp)/'F',plan(),Provider().factory),tasks(1))
   for value in (0,-1,True,1.5):
    with self.assertRaises(ValueError):s.run(stop_after_batch=value)
if __name__=='__main__':unittest.main()
