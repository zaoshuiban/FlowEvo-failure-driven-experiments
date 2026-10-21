import importlib.util,json,pathlib,tempfile,unittest
from decimal import Decimal
from e2_oracles import selftest,magazine,transform
class Checks(unittest.TestCase):
 def test_independent_oracles(self):self.assertEqual(selftest(),{'transform_exhaustive_string_pairs':819,'magazine_leaf_subset_checks':42})
 def test_magazine_contract(self):
  for x in [[1,3,0,0],[1,2,1,3,0],[1,2,0,2],[1,2,0,0,9]]:
   with self.assertRaises(ValueError):magazine(x)
 def test_mapping_constraints(self):
  self.assertEqual(transform('aa','ab'),-1);self.assertEqual(transform('ab','ba'),3);self.assertEqual(transform('abc','baa'),3)
  self.assertEqual(transform('abcdefghijklmnopqrstuvwxyz','bcdefghijklmnopqrstuvwxyza'),-1)
 def test_no_hidden_r2_generator(self):
  source=(pathlib.Path(__file__).parent/'public_generator.py').read_text()
  for forbidden in ['private_e1','data/tasks','reference_solution','input_output']:self.assertNotIn(forbidden,source)
 def test_frozen_calls(self):
  p=pathlib.Path(__file__).resolve().parents[1]/'e2_frozen/calls.json'
  if not p.exists():self.skipTest('Remote-only frozen requests')
  calls=json.loads(p.read_text());self.assertEqual(len(calls),12)
  for tid in {c['task_id'] for c in calls}:
   subset=[c for c in calls if c['task_id']==tid];self.assertEqual(len(subset),6)
   for condition in ['R0','R1','R2']:self.assertEqual(sum(c['condition']==condition for c in subset),2)
   self.assertEqual(len({c['source_sha256'] for c in subset}),1)
   self.assertEqual(len({c['request']['temperature'] for c in subset}),1)
   for c in subset:
    self.assertEqual(c['request']['max_tokens'],32768)
    self.assertEqual(c['public_witness'] is not None,c['condition']=='R2')
if __name__=='__main__':unittest.main()
