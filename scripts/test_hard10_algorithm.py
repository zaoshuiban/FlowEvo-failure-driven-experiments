import unittest,tempfile,json
from pathlib import Path
from run_hard10_algorithm import *
class TestHard10(unittest.TestCase):
 def test_freeze(self):
  p=verify();self.assertEqual(len(load(OUT/'tasks.json')),10);self.assertEqual(p['max_calls'],80)
 def test_private_not_public(self):
  with self.assertRaises(ValueError):public_guard(dict(source_tasks=[dict(task_id='x',problem='q',gold_answer='1')]),'T','analysis')
 def test_true_not_failure(self):
  e=dict(task_id='x',correct=True,attempt_index=0,wrong_answer='0',output='x',finish_reason='stop',locked_sha256='a',evidence_id='b')
  with self.assertRaises(ValueError):public_guard(dict(source_tasks=[],failure_evidence=e),'F','analysis')
 def test_t_no_evidence(self):
  with self.assertRaises(ValueError):public_guard(dict(source_tasks=[],failure_evidence={}), 'T','analysis')
 def test_score(self):
  self.assertEqual(grade_continuation('The answer is 2','3','stop')['status'],'CONFIRMED_WRONG')
  self.assertEqual(grade_continuation('The answer is x','3','stop')['status'],'UNVERIFIED')
  self.assertEqual(grade_continuation('The answer is 2','3','length')['status'],'TRUNCATED')
 def test_auth(self):
  with tempfile.TemporaryDirectory() as d:
   a=Adapter(Path(d)/'events',None,model='deepseek-flash')
   with self.assertRaises(PermissionError):a.preflight(dict())
 def test_mock_wire(self):
  with tempfile.TemporaryDirectory() as d:
   a=Adapter(Path(d)/'events',None,model='deepseek-flash',mock=True,sender=lambda b:None)
   for arm in ['T','F','FC']:
    inp=dict(source_tasks=[load(OUT/'tasks.json')[0]])
    if arm!='T':inp['failure_evidence']=dict(task_id='x',correct=False,attempt_index=0,wrong_answer='0',output='wrong output',finish_reason='stop',locked_sha256='a',evidence_id='b')
    wire=a.preflight(dict(arm=arm,stage='analysis',public_input=inp));self.assertLess(len(canonical(wire).encode()),65536);self.assertNotIn('gold_answer',canonical(wire))
 def test_actual_worker_mock_source(self):
  with tempfile.TemporaryDirectory(dir=OUT) as d:
   p=Path(d)/'mock.py';p.write_text('def solve(parameters):\n return str(parameters["x"] + 1)\n');self.assertTrue(component_check(p.read_text(),'solve')['passed'])
   with FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)(p) as w:self.assertEqual(w.call(dict(mode='function',function='solve',args=[{'x':3}],timeout=2))['value'],'4')
if __name__=='__main__':unittest.main()
