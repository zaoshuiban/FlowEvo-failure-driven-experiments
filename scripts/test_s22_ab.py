import copy,json,unittest,tempfile,pathlib,contextlib,io
from unittest.mock import patch
from test_s21_selective_experience import fixture,packet
from s22_ab import freeze,classify,pair_result,INSTRUCTIONS
from failure_evo.workflow_protocol_v2 import PreflightRejected
from failure_evo.contracts import fingerprint

class Tests(unittest.TestCase):
 def setUp(self):self.p,self.h,_,_=fixture()
 def frozen(self):return freeze(self.p,[self.h],5)
 def test_same_context_only_instruction_changes(self):
  f=self.frozen();a,b=(f['arms'][x]['wire'] for x in ['A','B']);self.assertEqual(a['messages'][:2],b['messages'][:2]);self.assertEqual({k:v for k,v in a.items() if k!='messages'},{k:v for k,v in b.items() if k!='messages'})
  for arm in ['A','B']:
   self.assertTrue(f['arms'][arm]['wire']['messages'][2]['content'].endswith(INSTRUCTIONS[arm]));self.assertEqual(f['arms'][arm]['wire_sha256'],fingerprint(f['arms'][arm]['wire']))
 def test_B_retains_code_actual_and_exception(self):
  self.p['feedback']['public_cases'][0]['exception_class']='IndexError';f=self.frozen()
  ctx=json.loads(f['arms']['B']['wire']['messages'][1]['content']);self.assertEqual(ctx['candidate_code'],self.p['code']);self.assertEqual(ctx['public_feedback'],self.p['feedback'])
 def test_one_call_same_limits(self):
  f=self.frozen();self.assertEqual(f['max_calls_per_branch'],1)
  self.assertEqual(f['arms']['A']['output_upper'],8192);self.assertEqual(f['arms']['B']['wire']['temperature'],0);self.assertEqual(f['status'],'DRY_RUN_NOT_AUTHORIZED')
 def test_deterministic_no_mutation(self):
  original=copy.deepcopy((self.p,self.h));self.assertEqual(self.frozen(),self.frozen());self.assertEqual(original,(self.p,self.h))
 def test_no_cross_branch_mutation(self):
  f=self.frozen();b=copy.deepcopy(f['arms']['B']);f['arms']['A']['wire']['messages'][1]['content']='A output';self.assertEqual(f['arms']['B'],b)
 def test_future_prefix_rejected(self):
  self.h['observed_at']=6
  with self.assertRaises(ValueError):self.frozen()
 def test_hidden_fields_rejected(self):
  self.p['hidden_answer']='secret'
  with self.assertRaises(ValueError):self.frozen()
 def test_public_pass_illegal(self):
  self.p['feedback']['status']='PUBLIC_PASS'
  with self.assertRaises(ValueError):self.frozen()
 def test_insufficient_calls(self):
  self.p['checkpoint_budget']['calls']=self.p['checkpoint_budget']['max_calls']
  with self.assertRaises(ValueError):self.frozen()
 def test_input_limit(self):
  self.p['task_public']['prompt']='x'*40000
  with self.assertRaises(PreflightRejected):self.frozen()
 def test_all_pair_classes(self):
  expected={(True,True):'Both-success',(True,False):'A-only',(False,True):'B-only',(False,False):'Both-fail'}
  for pair,result in expected.items():self.assertEqual(classify(*pair),result)
  for x in [True,False,None]:self.assertEqual(classify(None,x),'UNKNOWN');self.assertEqual(classify(x,None),'UNKNOWN')
 def test_invalid_boolean(self):
  with self.assertRaises(ValueError):classify(1,False)
 def test_unknown_budget_or_tls_not_failure(self):
  good=dict(request_state='COMPLETED',public_pass=True,sealed_pass=True)
  for state in ['UNKNOWN','NOT_SENT','BUDGET_BLOCKED']:
   bad=dict(request_state=state,public_pass=False,sealed_pass=False);self.assertEqual(pair_result(good,bad,online_locked=True)['strict'],'UNKNOWN')
 def test_public_strict_separate_and_lock(self):
  a=dict(request_state='COMPLETED',public_pass=True,sealed_pass=False);b=dict(request_state='COMPLETED',public_pass=True,sealed_pass=True)
  self.assertEqual(pair_result(a,b)['strict'],'NOT_EVALUATED');self.assertEqual(pair_result(a,b,online_locked=True),dict(public='Both-success',strict='B-only',new_calls=0))
 def test_missing_review_not_invented(self):
  a=dict(request_state='COMPLETED',public_pass=True);b=dict(request_state='COMPLETED',public_pass=False)
  self.assertEqual(pair_result(a,b,online_locked=True)['strict'],'UNKNOWN');self.assertEqual(pair_result(b,b,online_locked=True)['strict'],'Both-fail')
 def test_selection_independent_of_old_AB_winners(self):
  import s22_audit as audit
  expected=json.loads((audit.OUT/'selected_checkpoints.json').read_text())
  real=audit.pairs_audit()
  for row in real:
   row['initial_public_class']='A-only';row['strict_complete_branch_class']='A-only'
   for arm in ['A','B']:row['arms'][arm]['strict_pass']=arm=='A'
  with tempfile.TemporaryDirectory() as td,patch.object(audit,'OUT',pathlib.Path(td)),patch.object(audit,'pairs_audit',return_value=real),contextlib.redirect_stdout(io.StringIO()):
   audit.main();actual=json.loads((pathlib.Path(td)/'selected_checkpoints.json').read_text())
  self.assertEqual(actual,expected)
if __name__=='__main__':unittest.main()
