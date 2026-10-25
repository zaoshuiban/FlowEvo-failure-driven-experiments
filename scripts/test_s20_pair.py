import unittest,hashlib,copy
from s20_action_pair_preflight import reconstruct
from test_s19_v2 import tasks
from failure_evo.contracts import PublicTaskView
class Tests(unittest.TestCase):
 def test_public_prefix_only(self):
  h=dict(checkpoint_task=PublicTaskView.project(tasks(1)[0]['task_public']).to_dict(),before_code='print(0)',before_sha256=hashlib.sha256(b'print(0)').hexdigest(),before_feedback=dict(status='WRONG_ANSWER',summary='',public_cases=[dict(input='1',expected='1',actual='0',exception_class=None)],visibility='public'),checkpoint_budget=dict(max_calls=5,max_tokens=204800,max_tools=128,calls=1,used_tokens=30,tool_calls=3,remaining_seconds=300.),generic_action='REPAIR_EXISTING',action='REGENERATE_FRESH',proposed_code='FUTURE_SECRET',public_feedback={'hidden':'SEALED_SECRET'})
  x=reconstruct(h);self.assertFalse(x['same_wire']);self.assertNotIn('FUTURE_SECRET',str(x));self.assertNotIn('SEALED_SECRET',str(x))
  h['action']='REPAIR_EXISTING';self.assertTrue(reconstruct(h)['same_wire'])
  h['before_code']='print(1)'
  with self.assertRaises(ValueError):reconstruct(h)
if __name__=='__main__':unittest.main()
