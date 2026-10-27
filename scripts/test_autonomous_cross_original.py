"""Read-only audit of the real bounded run. No API / no candidate fabrication."""
import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import canonical,fingerprint
RUN=ROOT/'runs/autonomous_cross_original_20261027_01'
def read(name):return json.loads((RUN/name).read_text())
def rows(name):return [json.loads(x) for x in (RUN/name).read_text().splitlines()]
class Audit(unittest.TestCase):
 def test_source_truth_and_separate_originals(self):
  j=read('public_job.json');targets=read('targets.json');e=j['discovery']['evidence']
  self.assertEqual(len({r['task']['problem_id'] for r in e}),2)
  self.assertTrue({r['task']['problem_id'] for r in e}.isdisjoint({r['task']['problem_id'] for r in targets}))
  for r in e:
   self.assertEqual(hashlib.sha256(r['code'].encode()).hexdigest(),r['code_sha256'])
   self.assertEqual(r['root_cause_status'],'UNVERIFIED')
   self.assertTrue(all(c['valid'] for c in r['legality']))
 def test_target_material_not_in_sent_wire(self):
  raw=next(r['payload'] for r in rows('provider.jsonl') if r['kind']=='SEND_STARTED')
  wire=raw['wire'];wire=wire if isinstance(wire,str) else canonical(wire)
  for c in read('targets.json')+read('negative_controls.json'):
   self.assertNotIn(c['task']['problem_id'],wire)
   self.assertNotIn(c['task']['prompt'],wire)
   self.assertNotIn(c['code'],wire)
 def test_preflight_sent_identical(self):
  sent=next(r['payload'] for r in rows('provider.jsonl') if r['kind']=='SEND_STARTED')
  w=sent['wire'];w=json.loads(w) if isinstance(w,str) else w
  self.assertEqual(w,read('frozen_induction_wire.json'))
  self.assertLessEqual(len(canonical(w).encode())+256,65536)
 def test_hypothesis_only_did_not_generate(self):
  self.assertEqual(read('result.json')['status'],'HYPOTHESIS_ONLY')
  actual=[r for r in rows('provider.jsonl') if r['kind']=='SEND_STARTED']
  self.assertEqual(len(actual),1)
  self.assertEqual(read('result.json')['versions'],0)
  self.assertEqual(read('result.json')['cross_original_pairs'],0)
  self.assertEqual(read('pipeline/hypothesis.json')['status'],'UNVERIFIED')
  self.assertFalse((RUN/'winner_locked.json').exists())
 def test_no_unknown_or_historical_rewrite(self):
  self.assertEqual(read('result.json')['budget']['unknown_or_pending_requests'],[])
  for name,h in read('protocol.json')['historical_inputs'].items():
   self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),h)
  self.assertTrue(all(read('historical_integrity_after.json').values()))
 def test_usage_equals_provider_and_compiler(self):
  raw=next(r['payload']['response'] for r in rows('provider.jsonl') if r['kind']=='RAW_RESPONSE')
  result=next(r['payload']['response'] for r in rows('compiler.jsonl') if r['kind']=='GENERATION_RESPONSE')
  self.assertEqual(raw['usage']['total_tokens'],result['usage']['total_tokens'])
  self.assertEqual(raw['usage']['prompt_tokens']+raw['usage']['completion_tokens'],raw['usage']['total_tokens'])
  self.assertEqual(read('result.json')['budget']['calls'],1)
if __name__=='__main__':unittest.main(verbosity=2)
