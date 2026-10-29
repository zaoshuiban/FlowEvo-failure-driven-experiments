import importlib.util,json,unittest,time,sys
from pathlib import Path
p=Path(__file__).with_name('test_math_no_gold.py');spec=importlib.util.spec_from_file_location('oldtest',p);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
from failure_evo.math_discovery_p1p2 import *
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.math_operators import MathOperatorRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from code_math.no_gold import NoGoldMathController,PublicMathTask

def mock_gpt(v):return dict(model='openai/gpt-5.4',id='mock',choices=[dict(message=dict(content=json.dumps(v)),finish_reason='stop')],usage=dict(prompt_tokens=20,completion_tokens=20,total_tokens=40))
class P1P2Tests(old.MathTests):
 def make_bundle(self):
  tasks=[PublicMathTask('s1','Sum integers: 2,3'),PublicMathTask('s2','Sum integers: 4,5')]
  c=NoGoldMathController(self.channel(),self.p/'controller')
  record=DiscoveryRecorder(self.p/'record',self.p/'controller',[old.private(tasks[0],'5'),old.private(tasks[1],'9')])
  for i,t in enumerate(tasks):record.record(t,c.solve(t,episode_id=t.task_id,sequence=i))
  return record.bundle()
 def test_binary_feedback_projection(self):
  b=self.make_bundle();f=learning_view(b,'F');t=learning_view(b,'T')
  self.assertEqual(f['questions'],t['questions']);self.assertTrue(all(r['correct'] is False for r in f['observed_attempts']))
  self.assertNotIn('observed_attempts',t);self.assertNotIn('gold_answer',canonical(f))
  self.assertNotIn('scorer',canonical(f));self.assertNotIn('solution',canonical(f))
  b['events'][0]['scorer_version']='obsolete'
  with self.assertRaises(PermissionError):learning_view(b,'F')
  b['events'][0]['scorer_version']='math-explicit-terminal-answer-v2'
  b['events'][0]['final']['correct']=True
  with self.assertRaises(PermissionError):learning_view(b,'F')
 def test_three_score_classes(self):
  self.assertEqual(grade_output('The answer is 2','3')['status'],'CONFIRMED_WRONG')
  self.assertEqual(grade_output('The answer is 2','2')['status'],'CONFIRMED_CORRECT')
  self.assertEqual(grade_output('The answer is x+x','2x')['status'],'UNVERIFIED')
  self.assertEqual(grade_output('','2')['status'],'EXECUTION_ERROR')
 def test_truncated_numeric_tail_not_wrong(self):
  self.assertEqual(grade_output('Negatives:\n1. -84\n2. -203\n25','99','length')['status'],'EXECUTION_ERROR')
  self.assertIsNone(grade_output('25','99','length')['correct'])
  self.assertEqual(grade_output(r'The answer is \(\frac{1}{2}\).','1/2','stop')['status'],'CONFIRMED_CORRECT')
  self.assertEqual(grade_output('uncompleted list\n25','99','stop')['status'],'EXECUTION_ERROR')
 def test_real_worker_p2_only(self):
  bundle=self.make_bundle();b=old.budget(self.p/'compilebudget',3)
  out=iter([mock_gpt(old.H),mock_gpt(dict(code=old.CODE,description='mock calculation',applicability='mock'))]);wires=[]
  def sender(w):wires.append(w);return next(out)
  provider=BinaryMathGPTAdapter(self.p/'provider',b,model='gpt-5.4',mock=True,sender=sender,max_wire_input_upper=65536)
  compiler=BoundedCompiler(provider,b,self.p/'compile','gpt-5.4',max_input_upper=65536,max_output_upper=8192)
  runner=MathOperatorRunner(FrozenLinuxBackend(image=old.IMAGE,worker_script=old.WORKER),budget=b)
  job=EngineeringDiscovery(self.p/'eng',compiler,runner,'F');r=job.run(bundle)
  self.assertTrue(r['engineering_passed']);self.assertEqual(r['applied_source_count'],2)
  self.assertIn('"correct":false',wires[0]['messages'][1]['content']);self.assertNotIn('gold_answer',canonical(wires))
  for term in ('parenthesization','restricted_prime','bracket','prime'):
   self.assertNotIn(term,wires[0]['messages'][0]['content'])
  self.assertFalse((self.p/'registry').exists())
 def test_p2_no_mechanism(self):
  bundle=self.make_bundle();b=old.budget(self.p/'compilebudget',3)
  provider=BinaryMathGPTAdapter(self.p/'provider',b,model='gpt-5.4',mock=True,sender=lambda w:mock_gpt(dict(old.H,decision='NO_MECHANISM')),max_wire_input_upper=65536)
  compiler=BoundedCompiler(provider,b,self.p/'compile','gpt-5.4',max_input_upper=65536,max_output_upper=8192)
  r=EngineeringDiscovery(self.p/'eng',compiler,None,'F').run(bundle)
  self.assertEqual(r['candidate_count'],0)

if __name__=='__main__':unittest.main(verbosity=2)
