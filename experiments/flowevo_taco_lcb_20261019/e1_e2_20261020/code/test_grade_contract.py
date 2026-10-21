import unittest
from grade_e2 import compare,extract
class GradeContract(unittest.TestCase):
 def test_fixed_precision_and_finite(self):
  c={'expected':['3'],'comparison':'rounded_four_decimals'}
  self.assertTrue(compare('3.0000\n',c));self.assertFalse(compare('3.0001',c));self.assertFalse(compare('3',c));self.assertFalse(compare('NaN',c));self.assertFalse(compare('3.0000 3.0000',c))
 def test_order_multiplicity_preserved(self):
  c={'expected':['1','2','2'],'comparison':'integer_tokens'}
  self.assertTrue(compare('1\n2\n2',c));self.assertFalse(compare('2 1 2',c));self.assertFalse(compare('1 2',c))
 def test_code_completeness(self):
  self.assertEqual(extract(''),'');self.assertEqual(extract('```python\nprint(1)\n```'),'print(1)\n');self.assertTrue(extract('```python\nprint(').startswith('```'))
if __name__=='__main__':unittest.main()
