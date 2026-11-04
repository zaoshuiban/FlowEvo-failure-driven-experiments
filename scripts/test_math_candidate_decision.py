"""Two-axis readiness matrix, fail-closed interface and old-protocol isolation."""
import unittest,copy,json,tempfile
from pathlib import Path
from math_candidate_mock import assessment
from failure_evo.math_candidate_decision import *
from failure_evo.math_cumulative_stream import validate_config,DEFAULTS
from failure_evo.math_cumulative_learning import BundleCompilerAdapter
from failure_evo.math_stream import budget

class Decisions(unittest.TestCase):
 def test_all_nine_combinations(self):
  for cause in ['SUPPORTED','SUSPECTED','UNSUPPORTED']:
   for decision in ['GENERATE','NEEDS_SPECIFICATION','NOT_GENERATABLE']:
    a=assessment(['visible'],cause,decision);bind_evidence(validate_decision(a),['visible'])
    self.assertEqual(generatable(a),decision=='GENERATE')
 def test_generic_advice_cannot_generate_without_contract(self):
  a=assessment();a['algorithm_candidate']['details']=None;a['algorithm_candidate']['reason']='Check carefully'
  with self.assertRaises(ValueError):validate_decision(a)
 def test_missing_steps(self):
  a=assessment();a['algorithm_candidate']['details']['computation_steps']=[]
  with self.assertRaises(ValueError):validate_decision(a)
 def test_no_independent_plan(self):
  a=assessment();a['algorithm_candidate']['details']['independent_validation']['independence_basis']=''
  with self.assertRaises(ValueError):validate_decision(a)
 def test_open_parameter_schema(self):
  a=assessment();a['algorithm_candidate']['details']['parameters']['json_schema']='{"type":"object"}'
  with self.assertRaises(ValueError):validate_decision(a)
 def test_old_hypothesis_only_not_promoted(self):
  with self.assertRaises(ValueError):validate_decision(dict(decision='HYPOTHESIS_ONLY',executable_suggestion='Try an enumeration'))
 def test_model_cannot_grant_verified(self):
  a=assessment();a['verified']=True
  with self.assertRaises(ValueError):validate_decision(a)
 def test_unavailable_evidence_rejected(self):
  with self.assertRaises(ValueError):bind_evidence(assessment(['future']),['past'])
 def test_supported_needs_citations(self):
  with self.assertRaises(ValueError):bind_evidence(assessment(status='SUPPORTED'),[])
 def test_old_run_config_rejected(self):
  with self.assertRaises(ValueError):validate_config(dict(DEFAULTS,version='math-cumulative-v1'),[])
 def test_diagnostic_preserved(self):
  self.assertEqual(validate_decision(assessment(role='DIAGNOSTIC'))['algorithm_candidate']['details']['output']['role'],'DIAGNOSTIC')
 def test_both_arms_share_wire_and_block_unready_candidate(self):
  with tempfile.TemporaryDirectory() as d:
   b=budget(Path(d)/'budget.jsonl','engineering:decision','fixture',calls=3)
   adapter=BundleCompilerAdapter(Path(d)/'provider.jsonl',b,model='deepseek-flash',mock=True,sender=lambda w:None,max_wire_input_upper=65536)
   for arm in ['T','F']:
    r=dict(phase='candidate',arm=arm,public_evidence=dict(questions=[dict(problem='Public problem')]),learning_evidence_bundle=dict(evidence=[dict(evidence_id='e')]),specification=canonical(assessment(['e'],decision='NEEDS_SPECIFICATION')),max_tokens=1024)
    if arm=='F':r['public_evidence']['observations']=[]
    with self.assertRaises(PermissionError):adapter.preflight(r)
    r['specification']=canonical(assessment(['e'],status='UNSUPPORTED'));wire=adapter.preflight(r)
    self.assertEqual(json.loads(wire['messages'][1]['content'])['hypothesis']['mechanism_assessment']['status'],'UNSUPPORTED')
    self.assertNotIn('PROPOSE',wire['messages'][0]['content'])
if __name__=='__main__':unittest.main()
