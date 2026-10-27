import copy,json,pathlib,tempfile,unittest
import s22_executor as e
from s22_action_audit import compare
class ExecutorTests(unittest.TestCase):
 def test_twenty_and_restart(self):
  with tempfile.TemporaryDirectory() as d:
   sent=[]
   def sender(w,t):sent.append(w);return e.mock_sender(w,t)
   state=e.run(d,sender=sender)
   self.assertEqual(state['status'],'ONLINE_LOCKED');self.assertEqual(len(sent),20)
   e.run(d,sender=sender);self.assertEqual(len(sent),20)
   for i,w in enumerate(sent):
    n=i//2+1;p=e.read(e.BASE/f'frozen/{n:02}.json');arm=('A','B') if n%2 else ('B','A')
    self.assertEqual(json.loads(w),p['request_freeze']['arms'][arm[i%2]]['wire'])
 def test_unknown_no_resend(self):
  with tempfile.TemporaryDirectory() as d:
   sent=[]
   def fail(w,t):sent.append(w);raise EOFError('mock')
   with self.assertRaises(EOFError):e.run(d,sender=fail)
   with self.assertRaises(RuntimeError):e.run(d,sender=fail)
   self.assertEqual(len(sent),1)
   self.assertEqual(e.read(pathlib.Path(d)/'state.json')['budget']['unknown_or_pending_requests'],['01-A'])
 def test_auth_before_sender(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(PermissionError):e.run(d,mode='real',sender=lambda *a:self.fail('sent'))
 def test_worker_failure_stops(self):
  with tempfile.TemporaryDirectory() as d:
   def fail(*a):raise RuntimeError('worker')
   with self.assertRaises(RuntimeError):e.run(d,judge=fail)
   with self.assertRaises(RuntimeError):e.run(d)
   self.assertEqual(e.read(pathlib.Path(d)/'state.json')['budget']['calls'],1)
 def test_bad_provider(self):
  with tempfile.TemporaryDirectory() as d:
   def bad(w,t):r=e.mock_sender(w,t);r['model']='wrong';return r
   with self.assertRaises(ValueError):e.run(d,sender=bad)
 def test_no_algorithm_claim(self):
  v=compare('x=1\nprint(x)','y=1\nprint(y)','length')
  self.assertEqual(v['ast_node_type_similarity'],1);self.assertTrue(v['truncated'])
  self.assertEqual(v['algorithm_changed'],'REQUIRES_MANUAL_REVIEW')
 def test_sealed_gate_and_twenty_mock(self):
  from s22_final_review import review
  with tempfile.TemporaryDirectory() as d:
   e.save(pathlib.Path(d)/'state.json',dict(status='READY',branches={}))
   e.save(pathlib.Path(d)/'identity.json',{})
   with self.assertRaises(RuntimeError):review(d)
  with tempfile.TemporaryDirectory() as d:
   e.run(d);r=review(d)
   self.assertEqual(len(r['pairs']),10)
   self.assertTrue(all(x['strict']=='Both-fail' for x in r['pairs']))
   self.assertEqual(review(d),r)
 def test_manifest_and_sources(self):e.verify()
 def test_scope_budget(self):
  with tempfile.TemporaryDirectory() as d:
   b=e.ledger(pathlib.Path(d)/'b','x','y');b.task_scope=e.Budget(max_tools=0)
   with self.assertRaises(RuntimeError):b.tool()
   self.assertEqual(b.tool_calls,0)
if __name__=='__main__':unittest.main()
