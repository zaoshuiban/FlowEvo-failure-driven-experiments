"""Stream boundary regression under explicit S19 v2; old v1 rule tests remain separate."""
import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
import run_workflow_v2 as e
from run_learning_stream import LearningStream
from test_s19_v2 import Provider,FakeJudge,tasks,plan

class Tests(unittest.TestCase):
 def test_arms_isolated_and_success_memory_restored(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   runners=[]
   for arm in ['G','M','F']:
    provider=Provider();p=plan(arm);r=e.ExperimentRunner(Path(tmp)/arm,p,provider.factory)
    s=LearningStream(r,tasks(1),arm=arm);runners.append((r,s))
   r,s=runners[0];s.run()
   self.assertTrue(r.libraries);self.assertFalse(runners[1][0].libraries);self.assertFalse(runners[2][0].libraries)
   self.assertEqual(runners[1][1].index.states(),{});self.assertEqual(runners[2][1].packets,{})
   recovered=e.ExperimentRunner(Path(tmp)/'G',r.plan,Provider().factory,resume=True)
   self.assertEqual({k:v.to_dict() for k,v in r.libraries.items()},{k:v.to_dict() for k,v in recovered.libraries.items()})
   with self.assertRaises(ValueError):LearningStream(recovered,tasks(1),arm='F')
 def test_no_replay_interrupted_task(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   r=e.ExperimentRunner(Path(tmp)/'F',plan(),Provider().factory);s=LearningStream(r,tasks(1));s.event('TASK_STARTED',task_id='fixture-0')
   with self.assertRaisesRegex(ValueError,'interrupted task'):s.run()
 def test_m_settled_response_recovery_without_resend(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   provider=Provider()
   def factory(ch):
    base=provider.factory(ch)
    def send(wire):
     r=base(wire)
     if ch=='learning':r['choices'][0]['message']['content']=json.dumps({'memory':'Public feedback is limited; retain uncertainty and original budget.'})
     return r
    return send
   p=plan('M-recovery');r=e.ExperimentRunner(Path(tmp)/'M',p,factory)
   def fault(stage):
    if stage=='MEMORY_RESPONSE_PERSISTED':raise RuntimeError('crash before memory snapshot')
   with self.assertRaises(RuntimeError):LearningStream(r,tasks(1),arm='M',batch_size=1,fault=fault).run()
   r.save();calls=dict(provider.calls);r=e.ExperimentRunner(Path(tmp)/'M',p,factory,resume=True)
   LearningStream(r,tasks(1),arm='M',batch_size=1).run()
   self.assertEqual(provider.calls,calls);self.assertIn('retain uncertainty',r.memory)
if __name__=='__main__':unittest.main()
