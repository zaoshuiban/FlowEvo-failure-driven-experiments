import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import run_v42_delivery_repair as r
from failure_evo.delivery_reception import receive
from failure_evo.property_validation import check_binding
class Flow(unittest.TestCase):
 def test_historical_audit(self):
  rows=r.load(r.OUT/'historical_reception_replay.json');by={x['job']:x for x in rows}
  self.assertEqual(by['poly-B-code']['receipt']['status'],'ACCEPTED')
  self.assertEqual(by['walk-B-R-review']['receipt']['status'],'ACCEPTED')
  p=by['walk-C-properties']['receipt'];self.assertEqual(p['status'],'ACCEPTED_WITH_UNEVALUABLE_TESTS');self.assertTrue(all(x['status']=='SEMANTICALLY_INCOMPLETE' for x in p['test_audit']))
 def test_real_parent_and_binding(self):
  manifest=r.load(r.OUT/'parent_manifest.json');a=dict(status='STATIC_VALID',sha256=manifest['sha256'],path=str(r.OUT/'parent.py'))
  proposal=dict(diagnosis='MOCK engineering only',replacement_hypothesis='MOCK',properties=[dict(id='mock',claim='MOCK reference comparison',preconditions='MOCK',tests=[dict(relation='oracle_correct',left=dict(target_x=0,target_y=0,max_steps=0,step_set=[[1,0]]),right=None)])])
  with tempfile.TemporaryDirectory(dir=r.OUT) as d:
   d=Path(d);r.save(d/'public_source.json',r.load(r.OUT/'public_source.json'))
   with patch.object(r,'OUT',d):receipt=r.assess(a,proposal)
  self.assertEqual(receipt['records'][0]['verdict']['status'],'ALGORITHM_COUNTEREXAMPLE')
  self.assertTrue(check_binding(receipt,a['sha256']))
  with self.assertRaises(ValueError):check_binding(receipt,'changed')
  self.assertNotIn('expected',r.canonical(receipt))
 def test_no_overlap(self):
  prior={r.fingerprint(x['parameters']) for x in r.load(r.V4/'private/tests.json') if x['family']=='walk'}
  prior|={r.fingerprint(x['parameters']) for x in r.load(r.OLD/'private/confirmation.json') if x['family']=='walk'}
  fresh=r.load(r.OUT/'private/new_confirmation.json');self.assertEqual(len(fresh),30);self.assertFalse(prior&{r.fingerprint(x['parameters']) for x in fresh})
 def test_no_model_answer_authority(self):
  result=receive('properties',dict(diagnosis='a',replacement_hypothesis='b',properties=[],tests=[dict(expected=999)]))
  self.assertFalse(result['model_tests_are_oracle']);self.assertEqual(result['normalized']['properties'],[])
if __name__=='__main__':unittest.main()
