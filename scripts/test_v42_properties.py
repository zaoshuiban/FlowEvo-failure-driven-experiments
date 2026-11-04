import unittest,tempfile,json
from pathlib import Path
from run_v42_properties import *
from failure_evo.property_validation import *
from v42_oracles import reference,confirmation
class Tests(unittest.TestCase):
 def test_proposal_no_self_verified(self):
  p=dict(diagnosis='hypothesis',replacement_hypothesis='unverified',properties=[])
  self.assertEqual(parse_property_proposal(p),p)
  with self.assertRaises(ValueError):parse_property_proposal(dict(p,verified=True))
 def test_model_gold_rejected(self):
  p=dict(diagnosis='h',replacement_hypothesis='h',properties=[dict(id='x',claim='h',preconditions='h',tests=[dict(relation='oracle_correct',left={},right=None,expected='42')])])
  with self.assertRaises(ValueError):parse_property_proposal(p)
 def test_relation_not_sufficient(self):
  ex=[dict(status='EXECUTED_UNSCORED',raw={'value':'0'})]*2
  self.assertEqual(adjudicate('equal',['1','1'],ex)['status'],'ALGORITHM_COUNTEREXAMPLE')
 def test_false_property(self):
  self.assertEqual(adjudicate('equal',['1','2'],[])['status'],'PROPERTY_COUNTEREXAMPLE')
 def test_unverified(self):self.assertEqual(adjudicate('oracle_correct',[None],[])['status'],'UNVERIFIED')
 def test_no_universal_pass(self):self.assertEqual(adjudicate('oracle_correct',['1'],[dict(status='EXECUTED_UNSCORED',raw={'value':'1'})])['status'],'FINITE_SAMPLE_SUPPORTED')
 def test_binding(self):
  r=bind_validation('first',{},[],'development');self.assertTrue(check_binding(r,'first'))
  with self.assertRaises(ValueError):check_binding(r,'second')
 def test_oracles(self):
  self.assertEqual(reference('expression',dict(expression='2+3*4',base=10,allow_implicit_multiplication=False)),'14')
  self.assertEqual(reference('walk',dict(target_x=0,target_y=0,max_steps=0,step_set=[[1,0]])),'2')
  self.assertEqual(reference('poly',dict(plus_inputs=[1,3,5,7],minus_inputs=[2,4,6,8],external_point=0)),'315')
 def test_confirmation(self):self.assertTrue(all(t['expected'] is not None for t in confirmation()))
 def test_A_isolation(self):
  with tempfile.TemporaryDirectory(dir=OUT) as d:
   a=Adapter(Path(d)/'p',None,model='deepseek-flash',mock=True,sender=lambda _:None)
   with self.assertRaises(ValueError):a.preflight(dict(stage='code',arm='A',public_input={'problem':'p','schema':{},'failure_evidence':{}},max_tokens=100))
 def test_real_mock_worker(self):
  with tempfile.TemporaryDirectory(dir=OUT) as d:
   p=Path(d)/'solve.py';p.write_text('def solve(parameters):\n return str(parameters["x"]+1)\n')
   r=execute_frozen(p,sha(p),{'x':2},FrozenLinuxBackend(image=IMAGE,worker_script=WORKER))
   self.assertEqual(r['raw']['value'],'3')
if __name__=='__main__':unittest.main()
