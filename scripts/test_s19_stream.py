"""Engineering-only mock responses; never experimental model evidence."""
import unittest,tempfile,json,os
from pathlib import Path
from unittest.mock import patch
import run_workflow_v2 as e
from run_learning_stream import LearningStream
from failure_evo.contracts import fingerprint

RULE={'when':{'candidate_state':'STRUCTURAL_PASS','public_result':'WRONG_ANSWER','remaining_calls_min':1},'action':'REGENERATE_FRESH','fallback':'NATIVE'}
def result(code):
 good=code.strip()=='print(2)';harm=code.strip()=='print(3)'
 flags=[good or harm,not harm]
 cases=[dict(input=str(i),expected='1',actual='1' if v else '0',correct=v,visibility='public',legal_verified=True,exception_class=None) for i,v in enumerate(flags)]
 return dict(visibility='public',status='PUBLIC_PASS' if all(flags) else 'WRONG_ANSWER',passed=all(flags),tests_run=2,tests_passed=sum(flags),cases=cases)
class Judge:
 def __init__(self,*a):pass
 def run(self,tid,code,cases):return result(code)
 def decision(self,*a):raise AssertionError('no Python policy')
class Tests(unittest.TestCase):
 def test_four_tasks_actual_controller_and_lifecycle(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',Judge):
   root=Path(tmp);calls={'learning':0,'solve':0,'validation':0};host=0
   def factory(channel):
    def sender(wire):
     nonlocal host
     calls[channel]+=1;body=json.loads(wire)
     if channel=='learning':text=json.dumps(RULE)
     elif channel=='validation':text='```python\nprint(%d)\n```'%(0 if calls[channel]==1 else 2)
     else:
      requested='Develop a fresh solution' in body['messages'][-1]['content']
      if requested:host+=1
      text='```python\nprint(%d)\n```'%((2 if host==1 else 3) if requested else 0)
     return dict(model='deepseek-flash',usage=dict(prompt_tokens=2,completion_tokens=2,total_tokens=4),choices=[dict(message=dict(content=text),finish_reason='stop')])
    return sender
   plan=dict(run_id='mock-s19',shared_protocol=e.VERSION,model='deepseek-flash',evidence_kind='engineering_fixture',operator_representation='repair-choice-json-v1',frozen_files={},budgets={k:e.prior.config(n,100,1000000) for k,n in [('solve',30),('learning',4),('validation',4)]},per_task=dict(max_calls=3,max_tokens=150000,max_tools=20,wall_seconds=600),allow_bounded_trials=True,trial_opportunities=2,validated_action_safety=dict.fromkeys(['contract','boundary','negative_cases','fallback','no_known_harm'],True))
   plan['protocol_hash']=fingerprint(plan)
   tasks=[dict(task_id=f't{i}',dataset='taco',difficulty='easy',task_public=dict(problem_id=f't{i}',prompt='Print correct answer',public_examples=[]),public_cases=[dict(input='0',expected='1')]) for i in range(4)]
   runner=e.ExperimentRunner(root/'F',plan,factory);stream=LearningStream(runner,tasks,batch_size=1);stream.run()
   with stream.memory._transaction() as (rows,_):
    self.assertTrue(any(r['event']=='CANDIDATE_SAVED' for r in rows));self.assertTrue(any(r['event']=='TRIAL_RESULT' for r in rows));self.assertTrue(any(r.get('decision')=='SUSPEND' for r in rows))
   self.assertTrue(runner.libraries);self.assertTrue(any(s['independent_task_count']>=2 for s in stream.index.states().values()))
   before=dict(calls);resumed=e.ExperimentRunner(root/'F',plan,factory,resume=True);LearningStream(resumed,tasks,batch_size=1).run();self.assertEqual(calls,before)
   if os.environ.get('S19_ACCEPTANCE_TRACE'):
    Path(os.environ['S19_ACCEPTANCE_TRACE']).write_text(json.dumps(dict(evidence_kind='engineering_fixture',paid_api_calls=0,mock_calls=calls,stream=stream.log.records(),hypotheses=stream.index.events.records(),lifecycle=[{k:v for k,v in row.items() if k!='state'} for row in rows],budgets={k:v.snapshot() for k,v in runner.budgets.items()},resume_calls_unchanged=calls==before),ensure_ascii=False,indent=2))
   self.assertEqual({k:v.to_dict() for k,v in runner.libraries.items()},{k:v.to_dict() for k,v in resumed.libraries.items()})
   changed=dict(plan,run_id='other')
   with self.assertRaises(ValueError):e.ExperimentRunner(root/'F',changed,factory,resume=True)
 def test_no_replay_interrupted_task(self):
  # Persistence barrier itself is tested without any generated code execution.
  from failure_evo.evidence import EvidenceStore
  from types import SimpleNamespace
  from failure_evo.failure_events import FailureEvidenceStore
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);r=SimpleNamespace(folder=p,stores={'F':FailureEvidenceStore(p/'facts')},plan={'run_id':'x'})
   tasks=[{'task_id':'t'}];s=LearningStream(r,tasks);s.log.append('TASK_STARTED',{'task_id':'t'},1e12)
   with self.assertRaisesRegex(ValueError,'interrupted task'):s.run()
if __name__=='__main__':unittest.main()
