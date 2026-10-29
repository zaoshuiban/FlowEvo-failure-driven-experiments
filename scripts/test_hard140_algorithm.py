import unittest,tempfile
from pathlib import Path
from run_hard140_algorithm import *
from run_hard10_algorithm import public_guard
class Test140(unittest.TestCase):
 def test_frozen(self):
  p=verify();self.assertEqual(len(load(OUT/'tasks.json')),140);self.assertEqual(p['max_calls'],364)
 def test_strata(self):
  labels=load(OUT/'private/labels.json');self.assertEqual(collections.Counter(x['subject'] for x in labels),{s:20 for s in SUBJECTS});self.assertTrue(all(x['level']=='Level 5' for x in labels))
 def test_no_old10(self):
  old={fingerprint(x['problem']) for x in load(ROOT/'runs/hard10_algorithm_20261028_01/tasks.json')};self.assertFalse(old&{fingerprint(x['problem']) for x in load(OUT/'tasks.json')})
 def test_all_inputs(self):
  for t in load(OUT/'tasks.json'):
   task=PublicMathTask.parse(t);w=prepare(solver_messages(task,profile='concise-v1'),limits=Limits(output_tokens=8192),temperature=0);self.assertLessEqual(w.input_upper,32768)
 def test_wrong_admission(self):
  self.assertEqual(grade_continuation('The answer is 2','3','length')['status'],'TRUNCATED');self.assertEqual(grade_continuation('The answer is x','3','stop')['status'],'UNVERIFIED')
  with self.assertRaises(ValueError):public_guard(dict(source_tasks=[dict(task_id='x',problem='p',gold_answer='z')]),'T','analysis')
 def test_review_without_scores(self):
  task=PublicMathTask('x','Compute a number.');m=solver_messages(task,'The answer is 2',profile='concise-v1');self.assertNotIn('correct=false',canonical(m));self.assertNotIn('gold_answer',canonical(m));self.assertIn('unverified',canonical(m))
 def test_authorization_denied(self):
  with tempfile.TemporaryDirectory(dir=OUT) as d:
   a=Adapter(Path(d)/'requests',None,model='deepseek-flash')
   with self.assertRaises(PermissionError):a.preflight({})
 def test_actual_worker(self):
  with tempfile.TemporaryDirectory(dir=OUT) as d:
   path=Path(d)/'mock.py';path.write_text('def solve(parameters):\n return str(parameters["x"] + 1)\n')
   with FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)(path) as w:self.assertEqual(w.call(dict(mode='function',function='solve',args=[{'x':3}],timeout=2))['value'],'4')
if __name__=='__main__':unittest.main()
