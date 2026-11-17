import unittest,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import run_alfworld_a4_exploratory as E
class Tests(unittest.TestCase):
 def test_52_exact_projections(self):
  samples=E.B.read(E.DATA/'review.private.json')['samples'];self.assertEqual(len(samples),52)
  for s in samples:
   origin,ids=E.origin_for(s);self.assertEqual(origin['steps'][origin['projected']['anchor']-1]['observation'],'Nothing happens.')
 def test_gating(self):
  for arm in E.ARMS:
   for status in ['MATCH','DECLINE','UNKNOWN','ERROR']:
    self.assertEqual(E.allows_recovery(arm,{'status':status}),arm=='S0' or status=='MATCH')
  with self.assertRaises(ValueError):E.allows_recovery('OTHER',{'status':'MATCH'})
 def test_veto_no_test_execution(self):
  class Card:
   version='frozen'
   def to_dict(self):return {}
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);p={'wall_seconds':100};budget=SimpleNamespace(snapshot=lambda:{})
   with patch.object(E,'verify',return_value=(p,None)),patch.object(E,'setup',return_value=(budget,None,None,None,None,None,{'A3b_candidate_0':Card()})),patch.object(E.B,'exposed_regression',return_value={'retention_passed':False}),patch.object(E,'origin_for',side_effect=AssertionError('must not read A4')):
    result=E.run(out);self.assertEqual(result['status'],'RETENTION_VETO_A4_NOT_RUN')
 def test_hashes_unchanged(self):
  f=E.B.read(E.PREP/'Candidate_Freeze.json')
  for x in f['arms'].values():self.assertEqual(E.B.sha(x['original_path']),x['sha256'])
if __name__=='__main__':unittest.main()
