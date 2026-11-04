import sys,unittest,tempfile
from pathlib import Path
from run_hard10_algorithm import ROOT
from failure_evo.delivery_reception import *
class Tests(unittest.TestCase):
 def test_code_optional(self):
  r=receive('code',{'code':'def solve(p):\n return "1"\n'});self.assertEqual(r['status'],'ACCEPTED');self.assertTrue(r['protected_content_unchanged']);self.assertIsNone(r['normalized']['description'])
 def test_alias(self):self.assertEqual(receive('review',{'diagnostics':'x','revision_plan':'y'})['normalized']['diagnosis'],'x')
 def test_conflict(self):self.assertEqual(receive('review',{'diagnostics':'x','diagnosis':'z','revision_plan':'y'})['status'],'REJECTED')
 def test_permissions(self):self.assertEqual(receive('code',{'code':'x','permissions':['network']})['status'],'REJECTED')
 def test_metadata(self):self.assertEqual(receive('code',{'code':'x','type':'python'})['status'],'REJECTED')
 def test_supplement_quarantine(self):
  r=receive('code',{'code':'x','self_tests':[{'expected':42}]});self.assertFalse(r['model_tests_are_oracle']);self.assertNotIn('self_tests',r['normalized'])
 def test_missing_relation(self):
  p={'diagnosis':'a','replacement_hypothesis':'b','properties':[dict(id='a',claim='b',preconditions=['c'],tests=[dict(relation='equal',left={},right=None)])],'tests':[]}
  r=receive('properties',p);self.assertEqual(r['status'],'ACCEPTED_WITH_UNEVALUABLE_TESTS');self.assertEqual(r['normalized']['properties'],p['properties'])
 def test_missing_semantics(self):self.assertEqual(receive('properties',{'diagnosis':'a','properties':[]})['status'],'REJECTED')
 def test_new_version(self):self.assertTrue(content_change({'code':'a'},{'code':'b'},'code'))
 def test_non_object_repair_version(self):self.assertTrue(content_change([],{'code':'x'},'code'))
 def test_four_properties_retained(self):
  v=dict(diagnosis='a',replacement_hypothesis='b',properties=[dict(id=str(i),claim='c',preconditions='p',tests=[]) for i in range(4)])
  r=receive('properties',v);self.assertEqual(r['status'],'ACCEPTED');self.assertEqual(r['normalized'],v)
if __name__=='__main__':unittest.main()
