import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
import run_workflow_v2 as e
from s20_repair_stream import RepairedStream,VERSION,compile_messages,RULE_SCHEMA
from test_s19_v2 import plan,tasks,FakeJudge,Provider
from failure_evo.contracts import fingerprint
class Tests(unittest.TestCase):
 def test_real_boundary_mock_send_and_resume(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   p=plan('repair-memory');p['repair_protocol']=VERSION;p['protocol_hash']=fingerprint({k:v for k,v in p.items() if k!='protocol_hash'});provider=Provider();wires=[]
   def factory(ch):
    base=provider.factory(ch)
    def send(wire):
     wires.append((ch,json.loads(wire)));r=base(wire)
     if ch=='learning':r['choices'][0]['message']['content']=json.dumps({'memory':'Public failure alone does not establish a common root cause.'})
     return r
    return send
   r=e.ExperimentRunner(Path(tmp)/'new',p,factory);s=RepairedStream(r,tasks(1),arm='M',batch_size=1);s.run();self.assertTrue(r.memory);self.assertEqual(provider.calls['learning'],1)
   count=len(wires);r=e.ExperimentRunner(r.folder,p,factory,resume=True);RepairedStream(r,tasks(1),arm='M',batch_size=1).run();self.assertEqual(count,len(wires))
   body=next(w for ch,w in wires if ch=='learning');self.assertIn('packet_sha256',str(body));self.assertNotIn('sealed',str(body))
 def test_opt_in_and_scalar_schema(self):
  self.assertEqual(RULE_SCHEMA['properties']['rule']['properties']['when']['properties']['candidate_state']['type'],'string')
  self.assertEqual(RULE_SCHEMA['properties']['hypothesis']['properties']['refusal_conditions']['type'],'string')
  m=compile_messages([{'role':'system','content':'base'}],{'compile_error':'wrong type'});self.assertIn('NOT a failure',m[0]['content'])
if __name__=='__main__':unittest.main()
