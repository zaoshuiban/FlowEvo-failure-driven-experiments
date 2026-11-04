import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
import run_v42_discovery_repair as r
class Test(unittest.TestCase):
 def test_no_gold(self):
  with self.assertRaises(AssertionError):r.assert_no_gold({'diagnostics':[{'expected':'5'}]})
  r.assert_no_gold({'diagnostics':[{'actual':'5','status':'CONFIRMED_WRONG'}]})
 def test_same_problem_mapping(self):
  p=dict(plus_inputs=[-1,3],minus_inputs=[0,2],external_point=4)
  self.assertEqual(r.casekey(p),r.casekey(r.canonical_case(r.params(p,'Z'),'Z')))
  self.assertEqual(r.cross_reference(p),r.reference('poly',p))
 def test_unsupported_not_wrong(self):
  self.assertIsNone(r.canonical_case(dict(nodes=[0,1],signs=[1,0]),'Z'))
  self.assertIsNone(r.canonical_case(dict(plus_inputs=[0],minus_inputs=[0]),'Q'))
 def test_zero_properties(self):
  p={'diagnosis':'No defect','replacement_hypothesis':'None','properties':[]}
  receipt=r.receive('properties',p);self.assertEqual(receipt['status'],'ACCEPTED')
  self.assertEqual(r.assay('Q',{'sha256':'mock'},p)['records'],[])
 def test_invalid_property_is_not_algorithm_error(self):
  p={'diagnosis':'mock','replacement_hypothesis':'mock','properties':[{'id':'a','claim':'mock','preconditions':'mock','tests':[{'relation':'equal','left':{'plus_inputs':[0],'minus_inputs':[1],'external_point':2},'right':{'plus_inputs':[0],'minus_inputs':[3],'external_point':2}}]}]}
  def fake(a,p):return dict(status='EXECUTED_UNSCORED',raw=dict(value=r.cross_reference(p)))
  with patch.object(r,'execute',fake):out=r.assay('Q',{'sha256':'mock'},p)
  self.assertEqual(out['records'][0]['status'],'PROPERTY_COUNTEREXAMPLE')
  self.assertTrue(all(o['status']=='CONFIRMED_CORRECT' for o in out['records'][0]['observations']))
 def test_mock_wire_same_shared_information(self):
  a=r.Adapter.__new__(r.Adapter);a.mock=True;a.model='deepseek-flash'
  inp=dict(problem='task',schema={},scope='domain',previous_code='def solve(parameters):\n return "1"')
  x=a.preflight(dict(arm='D',study_phase='discover',stage='properties',public_input=inp));y=a.preflight(dict(arm='C',study_phase='discover',stage='properties',public_input=inp))
  self.assertEqual(x['messages'][1],y['messages'][1]);self.assertEqual(x['max_tokens'],y['max_tokens']);self.assertNotEqual(x['messages'][0],y['messages'][0])
if __name__=='__main__':unittest.main()
