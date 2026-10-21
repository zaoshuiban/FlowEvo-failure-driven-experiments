import unittest
from comparison import stdio_equal
class Formats(unittest.TestCase):
 def test_fixed(self):
  p={'decimal_places':2};self.assertTrue(stdio_equal('4.00\n3.50','4.00 3.50',p));self.assertFalse(stdio_equal('4 3.5','4.00 3.50',p));self.assertFalse(stdio_equal('4.01 3.50','4.00 3.50',p));self.assertTrue(stdio_equal('47.0000','47.0000',{'decimal_places':4}))
 def test_scientific(self):
  p={'scientific_mantissa_places':3};self.assertTrue(stdio_equal('2.000 1 0.000 0','2.000 1 0.000 0',p));self.assertFalse(stdio_equal('2.000 2','2.000 1',p));self.assertFalse(stdio_equal('0.000 3','0.000 3',p));self.assertFalse(stdio_equal('10.000 1','10.000 1',p))
 def test_invalid_scientific_reference(self):
  import json
  from preflight import preflight
  task={'task_id':'taco_0536','dataset':'taco','function_name':None,'input_output':json.dumps({'inputs':['1\n1 5 2'], 'outputs':['2.000']})}
  pre,cases=preflight(task,{'protocol':'stdio','comparison':'tokens','scientific_mantissa_places':3})
  self.assertEqual(pre['status'],'NO_VALID_TESTS')
  self.assertTrue(pre['reference_issues']);self.assertFalse(cases)
if __name__=='__main__':unittest.main(verbosity=2)
