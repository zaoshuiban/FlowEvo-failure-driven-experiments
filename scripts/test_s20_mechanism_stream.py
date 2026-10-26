import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
import run_workflow_v2 as e
from s20_mechanism_stream import MechanismStream
from s20_repair_stream import VERSION
from test_s19_v2 import plan,tasks,FakeJudge,Provider
from failure_evo.contracts import fingerprint
class Tests(unittest.TestCase):
 def test_both_crash_windows_do_not_resend(self):
  for point in ['MEMORY_RESPONSE_PERSISTED','MEMORY_STATE_SAVED']:
   with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
    p=plan(point);p['repair_protocol']=VERSION;p['protocol_hash']=fingerprint({k:v for k,v in p.items() if k!='protocol_hash'});provider=Provider()
    def factory(ch):
     base=provider.factory(ch)
     def send(wire):
      r=base(wire)
      if ch=='learning':r['choices'][0]['message']['content']=json.dumps({'memory':'Retain public failure uncertainty.'})
      return r
     return send
    def fault(stage):
     if stage==point:raise RuntimeError('crash')
    r=e.ExperimentRunner(Path(tmp)/'r',p,factory)
    with self.assertRaisesRegex(RuntimeError,'crash'):MechanismStream(r,tasks(1),arm='M',batch_size=1,fault=fault).run()
    calls=dict(provider.calls);r=e.ExperimentRunner(r.folder,p,factory,resume=True);MechanismStream(r,tasks(1),arm='M',batch_size=1).run();self.assertEqual(calls,provider.calls);self.assertTrue(r.memory)
if __name__=='__main__':unittest.main()
