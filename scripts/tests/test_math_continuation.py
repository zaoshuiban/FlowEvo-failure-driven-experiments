import sys,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
p=Path(__file__).with_name('test_math_no_gold.py');spec=importlib.util.spec_from_file_location('old',p);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
from code_math.discovery_continuation import *
from code_math.no_gold import *
class ContinuationTests(old.MathTests):
 def test_separate_truncation(self):
  r=grade_continuation('25','99','length');self.assertEqual(r['status'],'TRUNCATED');self.assertIsNone(r['correct'])
  self.assertEqual(grade_continuation('The answer is 25','99','stop')['status'],'CONFIRMED_WRONG')
  self.assertEqual(grade_continuation('The answer is x+x','2x','stop')['status'],'UNVERIFIED')
 def test_concise_fixed_no_feedback(self):
  c=NoGoldMathController(self.channel(),self.p/'c',policy=NoGoldPolicy(delivery_profile='concise-v1'))
  r=c.solve(PublicMathTask('t','Compute a value.'),episode_id='t',sequence=0)
  self.assertEqual(r['model_calls'],2)
  self.assertEqual(self.wires[0]['messages'][0]['content'],CONCISE_SOLVER_SYSTEM)
  self.assertEqual(self.wires[1]['messages'][0]['content'],CONCISE_REVIEW_SYSTEM)
  self.assertNotIn('correct=false',str(self.wires))
 def test_recorder_keeps_truncation_out_of_pool(self):
  from failure_evo.math_discovery_p1p2 import DiscoveryRecorder
  def truncated(w):
   v=old.ds('25');v['choices'][0]['finish_reason']='length';return v
  task=PublicMathTask('x','Compute an integer.')
  c=NoGoldMathController(self.channel(sender=truncated),self.p/'c',policy=NoGoldPolicy(delivery_profile='concise-v1'))
  locked=c.solve(task,episode_id='x',sequence=14)
  r=DiscoveryRecorder(self.p/'scores',self.p/'c',[old.private(task,'99')],grade_function=grade_continuation,scorer_version=VERSION)
  self.assertEqual(r.record(task,locked)['final']['status'],'TRUNCATED');self.assertEqual(r.failures(),[])
 def test_real_plan_keeps_unknown_excluded(self):
  import json
  rows=[json.loads(x) for x in (ROOT/'reports/math_no_gold_p0_20261027/data/public/discovery.jsonl').read_text().splitlines()]
  run=ROOT/'runs/math_p1p2_20261027_01';p=plan_tasks(rows,run/'controller.jsonl',run/'solver_budget.jsonl')
  self.assertEqual(len(p['new_tasks']),82);self.assertEqual(len(p['exposed_locked']),13);self.assertEqual(len(p['quarantined_started_unlocked']),1)
  self.assertEqual(p['new_tasks'],rows[14:]);self.assertEqual(len(p['unknown_requests']),1)
if __name__=='__main__':unittest.main(verbosity=2)
