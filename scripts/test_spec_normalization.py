import json,unittest
import run_workflow_v2
from failure_evo.spec_normalization import *
class Tests(unittest.TestCase):
 def value(self):return {k:'  valid semantic value  ' for k in FIELDS}
 def n(self,v,finish='stop'):return normalize(dict(text=json.dumps(v),finish_reason=finish))
 def test_exact_values_preserved(self):self.assertEqual(self.n(self.value())['specification'],self.value())
 def test_allowlisted_metadata(self):
  v=self.value();v['type']='json_object';n=self.n(v);self.assertEqual(n['specification'],self.value());self.assertEqual(n['normalization']['removed_fields'],{'type':'json_object'})
 def test_unknown_semantic_field_not_removed(self):
  with self.assertRaises(SpecificationError):self.n(dict(self.value(),permissions='network'))
 def test_wrong_metadata_value(self):
  for x in ['object',None,{},False]:
   with self.assertRaises(SpecificationError):self.n(dict(self.value(),type=x))
 def test_missing_or_invalid_fields(self):
  for x in [None,[],False,' ']:
   v=self.value();v['mechanism']=x
   with self.assertRaises(SpecificationError):self.n(v)
  v=self.value();del v['conditions']
  with self.assertRaises(SpecificationError):self.n(v)
 def test_truncated_rejected(self):
  with self.assertRaises(SpecificationError):self.n(self.value(),'length')
 def test_duplicate_rejected(self):
  text=json.dumps(self.value())[:-1]+',"mechanism":"replacement"}'
  with self.assertRaises(SpecificationError):normalize(dict(text=text,finish_reason='stop'))
 def test_real_historical_spec(self):
  raw=run_workflow_v2.read(run_workflow_v2.ROOT/'runs/s16b_source_20261022_01/wire/learning/1/response.json');c=raw['choices'][0]
  n=normalize(dict(text=c['message']['content'],finish_reason=c['finish_reason']))
  self.assertEqual(n['normalization']['removed_fields'],{'type':'json_object'})
  self.assertEqual(set(n['specification']),set(FIELDS))
if __name__=='__main__':unittest.main()
