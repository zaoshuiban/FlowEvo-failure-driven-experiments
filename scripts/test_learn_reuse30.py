import copy, json, tempfile, time, unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import learn_reuse30 as p
from failure_evo.workflow_policy import *
from failure_evo.runtime import Budget, BudgetExhausted
from failure_evo.contracts import Fingerprint, PublicTaskView, PublicFeedback
from failure_evo.failure_events import FailureEvidenceStore

class ProtocolTests(unittest.TestCase):
 def test_extraction_complete_python_survives_length_and_formula(self):
  self.assertEqual(p.extract('```\nx+y\n```\n```python\nprint(1)\n```'),'print(1)')
  self.assertEqual(p.extract('```python\nprint(1)'),'print(1)')
 def test_no_concatenation_or_syntax_repair(self):
  self.assertEqual(p.extract('```python\nprint(1)\n```\n```python\nprint(2)\n```'),'print(1)')
  self.assertEqual(p.extract('```python\ndef f(\n```'),'def f(')
 def test_static_permission_and_fallthrough(self):
  self.assertFalse(validate_source('import os\ndef repair_operator(context):\n return {}')['passed'])
  self.assertFalse(validate_source('def repair_operator(context):\n if context:\n  return {}')['passed'])
  self.assertFalse(validate_source('def repair_operator(context):\n return getattr(context,"x",None)')['passed'])
  self.assertTrue(validate_source('def repair_operator(context):\n try:\n  return {"status":"declined","reason":"no"}\n except Exception:\n  return {"status":"error","reason":"bad"}')['passed'])
 def test_action_capability_does_not_include_permissions_or_applied(self):
  for x in [dict(status='applied',candidate_code='print(1)'),dict(status='declined',reason='',instruction='do'),dict(status='request_repair',instruction='do',reason='',model='other')]:
   with self.assertRaises(ValueError):validate_decision(x)
  self.assertEqual(validate_decision(dict(status='request_repair',instruction='fix',reason='observed'))['status'],'request_repair')
 def test_old_contract_keeps_zero_model_call(self):
  with self.assertRaises(ValueError):FailureOperator('x','1','x','h',Fingerprint('a','b','c','d','e'),'s',('e',),('g',),max_model_calls=1)
 def test_new_card_roundtrip(self):
  c=WorkflowPolicy('x','v','p','h',Fingerprint('a','b','c','d','e'),'s',('e',),('g',))
  self.assertEqual(WorkflowPolicy.from_dict(json.loads(canonical(c.to_dict()))),c)
  self.assertEqual(c.max_model_calls,0);self.assertEqual(c.max_host_model_requests,1)
 def test_preflight_no_budget_no_send(self):
  with tempfile.TemporaryDirectory() as d,patch.object(p,'RUN',Path(d)),patch.object(p.DeepSeekGenerator,'_post') as post:
   ledger=NS(reserve=lambda *a,**kw:self.fail('reserve on invalid preflight'))
   tr=p.Transport(ledger,Path(d)/'x','test',100);b=Budget(max_calls=2)
   with self.assertRaises(BudgetExhausted):tr.call([dict(role='user',content='x'*1000)],task_budget=b)
   self.assertEqual(b.calls,0);post.assert_not_called()
 def test_host_call_shares_budget_and_exact_body(self):
  with tempfile.TemporaryDirectory() as d,patch.object(p,'RUN',Path(d)):
   budget=p.PersistentBudget(Path(d)/'budget.jsonl',run_id='test',protocol_hash='hash',**p.config(2,0,100000))
   tr=p.Transport(budget,Path(d)/'request','test');local=Budget(max_calls=1)
   raw={'model':'deepseek-flash','usage':{'prompt_tokens':4,'completion_tokens':3,'total_tokens':7},'choices':[{'message':{'content':'print(1)'},'finish_reason':'stop'}]}
   with patch.object(p.DeepSeekGenerator,'_post',return_value=raw) as post,patch.object(p,'configured_api_key',return_value='mock'):
    tr.call([dict(role='user',content='task')],task_budget=local)
    self.assertEqual(post.call_args.args[0],tr.rows[0]['request']);self.assertEqual(local.calls,1);self.assertEqual(budget.calls,1)
    with self.assertRaises(BudgetExhausted):tr.call([dict(role='user',content='task')],task_budget=local)
    self.assertEqual(post.call_count,1)
 def test_causal_projection_excludes_hindsight(self):
  packet=dict(task_public={},candidate_code='bad',public_feedback={},current_generation=dict(finish_reason='length',text='future hidden'),audit={'hidden_answer':'x'},selected={'future_code':'x'},later_model_cost=99)
  value=p.causal(packet);self.assertNotIn('hidden',canonical(value));self.assertNotIn('future',canonical(value));self.assertNotIn('later_model_cost',value)
 def test_plugin_failed_repair_no_false_applied(self):
  card=WorkflowPolicy('x','v','p','h',Fingerprint('a','b','c','d','e'),'s',('e',),('g',))
  registry=NS(valid=lambda *a:True,reserve_opportunity=lambda *a,**kw:'r',complete_opportunity=lambda *a,**kw:outcomes.append(kw['outcome']),suspend=lambda *a:self.fail('ordinary failed test should not suspend'))
  outcomes=[]
  def host(payload,instruction,b):
   k=b.reserve(1,1);b.settle(k,2);return dict(code='print(0)',finish_reason='stop')
  plugin=WorkflowPlugin(registry,None,card.evidence_fingerprint,stream_id='s',experiment_id='e',host_repair=host,decision_runner=lambda *a:dict(status='request_repair',reason='x',instruction='fix'))
  plugin.current=dict(task=PublicTaskView.project(dict(problem_id='t',prompt='p')),snapshot=NS(cards=(card,),snapshot_id='snap',task_index=1),ledger=[dict(generation_metadata={'finish_reason':'length'})],observations=[],hooks=[],attempted=set())
  b=Budget(max_calls=3);feedback=PublicFeedback('COMPILE_ERROR')
  actual=plugin.invoke('before_native_retry','l2a','l2a','def f(',feedback,b,lambda *a:dict(visibility='public',status='WRONG_ANSWER',tests_run=1,tests_passed=0,cases=[]),time.time())
  self.assertIsNone(actual);self.assertEqual(outcomes[0]['status'],'declined');self.assertEqual(b.calls,1)
  self.assertIsNone(plugin.invoke('before_native_retry','l2b','l2b','def f(',feedback,b,lambda *a:self.fail('same version retried'),time.time()))
  self.assertEqual(len(outcomes),1)

if __name__=='__main__':unittest.main()
