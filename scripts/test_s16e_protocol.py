import unittest
from unittest.mock import patch
import experiment_s16e_workflow as x
class ProtocolTests(unittest.TestCase):
 def test_all_solver_routes_share_instruction(self):
  calls=[]
  def fake(self,messages,budget,temperature,capability):calls.append(messages);return {}
  with patch.object(x.WorkflowClient,'_call',fake):
   for marker in ('G','M','F'):
    c=x.StrongClient(None,marker);c._call([dict(role='user',content=marker)],None,0,marker)
  self.assertEqual([m[-1]['content'] for m in calls],[x.COMMON]*3)
 def test_projection_excludes_external_channel(self):
  task=dict(task_public=dict(problem_id='x',prompt='public'),audit_cases='SECRET',reference_path='SECRET')
  f=dict(status='WRONG_ANSWER',visibility='public',public_cases=[])
  packet=x.public_packet(task,'print(1)',f,'stop')
  self.assertNotIn('SECRET',x.canonical(packet));self.assertEqual(set(packet),{'task_public','candidate_code','public_feedback','generation_metadata','hook','stage'})
 def test_real_prefixes_have_sufficient_calls_and_code(self):
  for v in x.base_inputs().values():self.assertEqual(v['lineage']['remaining_calls'],4);self.assertTrue(v['code']);self.assertTrue(v['task']['public_cases'])
 def test_learning_messages_have_no_external_field(self):
  packet=dict(candidate_code='print(1)',public_feedback={'status':'WRONG_ANSWER'})
  m=x.learn_messages(dict(mechanism='public'),packet);self.assertNotIn('external_cases',x.canonical(m));self.assertIn(x.COMMON,x.canonical(m))
 def test_normalizer_keeps_strict_unknown_rejection(self):
  import json
  s={k:'public' for k in ('mechanism','conditions','repair_strategy','refusal_conditions','stop_rule','limitations')}
  self.assertEqual(x.normalize(dict(text=json.dumps(dict(s,type='json_object')),finish_reason='stop'))['specification'],s)
  with self.assertRaises(ValueError):x.normalize(dict(text=json.dumps(dict(s,external_score='SECRET')),finish_reason='stop'))
if __name__=='__main__':unittest.main()
