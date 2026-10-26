import copy,unittest
from s21_learning_necessity import local_rule
from test_s21_selective_experience import fixture,packet,change
from failure_evo import selective_experience as s

class Tests(unittest.TestCase):
 def setUp(self):self.p,self.h,self.c,self.catalog=fixture()
 def test_local_only_switch(self):
  self.assertTrue(local_rule(self.p,[self.h],5)['trigger'])
  self.assertFalse(local_rule(self.p,[],5)['trigger'])
 def test_same_source_is_gate_not_local_information(self):
  self.p=packet('source');self.h=dict(packet=packet('source','l2a'),observed_at=4)
  r=local_rule(self.p,[self.h],5);st=s.snapshot(self.p,observed_at=5,history=[self.h]);d=s.recommend(st,[self.c],enabled=True,source_catalog=self.catalog)
  self.assertTrue(r['trigger']);self.assertIsNone(d['proposal']);self.assertIn('SAME_SOURCE_TASK_OR_LINEAGE',d['conditions'][0]['rejections'])
 def test_empty_card_disables_but_explanation_does_not_choose(self):
  st=s.snapshot(self.p,observed_at=5,history=[self.h]);d=s.recommend(st,[self.c],enabled=True,source_catalog=self.catalog)
  altered=change(self.c,observed_failure_pattern='Different explanation, still unverified.',expected_local_effect='Unknown')
  other=s.recommend(st,[altered],enabled=True,source_catalog=self.catalog)
  self.assertEqual(d['proposal'],other['proposal']);self.assertIsNone(s.recommend(st,[],enabled=True)['proposal'])
 def test_future_and_other_task_rejected(self):
  for h in [dict(packet=self.h['packet'],observed_at=6),dict(packet=packet('other','l2a'),observed_at=4),dict(packet=packet('target','l3'),observed_at=4)]:
   with self.assertRaises(ValueError):local_rule(self.p,[h],5)
 def test_public_pass_unknown_and_budget_no_switch(self):
  for status in ['PUBLIC_PASS','UNKNOWN','EVALUATOR_ERROR']:
   p=packet('target',status=status);h=dict(packet=packet('target','l2a',status=status),observed_at=4)
   self.assertFalse(local_rule(p,[h],5)['trigger'])
  self.p['checkpoint_budget']['calls']=self.p['checkpoint_budget']['max_calls'];self.assertFalse(local_rule(self.p,[self.h],5)['trigger'])
 def test_adjacent_vs_any_is_explicit(self):
  history=[dict(packet=packet('target','l1'),observed_at=3),dict(packet=packet('target','l2a','print(2)'),observed_at=4)]
  self.assertTrue(local_rule(self.p,history,5)['trigger']);self.assertFalse(local_rule(self.p,history,5,True)['trigger'])
 def test_deterministic_no_mutation(self):
  before=copy.deepcopy((self.p,self.h));self.assertEqual(local_rule(self.p,[self.h],5),local_rule(self.p,[self.h],5));self.assertEqual(before,(self.p,self.h))
if __name__=='__main__':unittest.main()
