import unittest
import run_hard_math_property_probe as r
class T(unittest.TestCase):
 def test_scores_exact_discrete(self):
  p=dict(total_problems=2,base_score=0,correct_coefficient=4,wrong_coefficient=3,threshold=-1,max_score=10,require_unique_correct_count=False)
  self.assertEqual(r.oracle('score',p),dict(status='VALUE',value='0'))
  self.assertIsNone(r.oracle('score',dict(p,total_problems=True)))
 def test_no_score(self):
  p=dict(total_problems=0,base_score=0,correct_coefficient=4,wrong_coefficient=1,threshold=0,max_score=10,require_unique_correct_count=True)
  self.assertEqual(r.oracle('score',p)['status'],'NO_SOLUTION')
 def test_digits(self):self.assertEqual(r.oracle('digits',dict(upper_bound=3)),dict(status='VALUE',value='1'))
 def test_radical_exact_match(self):
  p=dict(p=8,q=1,multiplier=1,bound=1,tolerance=1e-30)
  self.assertEqual(r.oracle('radical',p),dict(status='VALUE',value='3'))
 def test_radical_no_solution(self):
  self.assertEqual(r.oracle('radical',dict(p=27,q=1,multiplier=1,bound=1,tolerance=1e-30)),dict(status='NO_SOLUTION'))
 def test_safe_reject(self):
  ref=dict(status='NO_SOLUTION');self.assertEqual(r.classify(ref,dict(status='RUNTIME_ERROR',raw={'error':'ValueError: none'})),'CORRECT_REJECTION')
  self.assertEqual(r.classify(ref,dict(status='EXECUTED_UNSCORED',raw={'value':'3'})),'WRONG_ACCEPT')
 def test_gold_guard(self):
  with self.assertRaises(AssertionError):r.core.assert_no_gold({'analysis':{'reference_answer':'2'}})
if __name__=='__main__':unittest.main()
