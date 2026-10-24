"""Zero-API v2 integration; fake providers, explicit engineering task provenance."""
import json,os,tempfile,unittest,copy
from pathlib import Path
from unittest.mock import patch
import run_workflow_v2 as e
from run_learning_stream import LearningStream,restore_budget,packet_check,configure_worker
from failure_evo.contracts import fingerprint,strict_stream_task,PublicFeedback
from failure_evo.repair_choice_v2 import *
from failure_evo.runtime import Budget

H=dict(conditions='A delivered program has audited public mismatch',action='Test a bounded recovery action',expected_improvement='Recover public behavior; benefit unverified',refusal_conditions='Public pass, unknown evidence or insufficient budget',stop_conditions='No more than original call budget',unknowns='No causal or cross-task advantage established')
def rule(action='REPAIR_EXISTING',state='STRUCTURAL_PASS',result='WRONG_ANSWER',minimum=1):
 return dict(when=dict(candidate_state=state,public_result=result,remaining_calls_min=minimum),action=action,fallback='NATIVE')
def tasks(n=4):
 cases=[dict(input=str(i)+'\n',expected=str(i),visibility='public',legal_verified=True,comparison='tokens',scorer='s1',source=dict(kind='engineering_fixture',id=f'identity-{i}',case_sha256=fingerprint([str(i)+'\n',str(i)]))) for i in range(2)]
 return [dict(task_id=f'fixture-{i}',dataset='taco',difficulty='easy',task_public=dict(problem_id=f'fixture-{i}',prompt='Read one integer and print it unchanged.',public_examples=copy.deepcopy(cases)),public_cases=copy.deepcopy(cases)) for i in range(n)]
def plan(name='mock',learning=4):
 p=dict(run_id=name,shared_protocol=e.VERSION,model='deepseek-flash',evidence_kind='engineering_fixture',operator_representation=VERSION,frozen_files={},budgets={k:e.prior.config(n,2000,2000000) for k,n in [('solve',30),('learning',learning),('validation',10)]},per_task=dict(max_calls=3,max_tokens=150000,max_tools=20,wall_seconds=600),allow_bounded_trials=True,trial_opportunities=2)
 p['protocol_hash']=fingerprint(p);return p
class Provider:
 def __init__(self):self.calls=dict(solve=0,learning=0,validation=0);self.host=0
 def factory(self,ch):
  def send(wire):
   self.calls[ch]+=1;body=json.loads(wire)
   if ch=='learning':
    n=self.calls[ch];text=json.dumps(dict(hypothesis=dict(H,action='Repair existing' if n<3 else 'Generate fresh'),rule=rule('REPAIR_EXISTING' if n<3 else 'REGENERATE_FRESH')))
   else:
    code='print(0)'
    if ch=='validation' and self.calls[ch]>=3:code='print(int(input()))'
    if ch=='solve' and 'Develop a fresh solution' in body['messages'][-1]['content']:
     self.host+=1;code='print(int(input()))' if self.host==1 else 'print(1)'
    text='```python\n'+code+'\n```'
   return dict(model='deepseek-flash',usage=dict(prompt_tokens=2,completion_tokens=2,total_tokens=4),choices=[dict(message=dict(content=text),finish_reason='stop')])
  return send
class FakeJudge:
 def __init__(self,*args):pass
 def decision(self,*args):raise AssertionError('not Python policies')
 def run(self,tid,code,cases):
  actual=lambda c: c['input'].strip() if code=='print(int(input()))' else '1' if code=='print(1)' else '0'
  rows=[dict(input=c['input'],expected=c['expected'],actual=actual(c),correct=actual(c)==c['expected'],exception_class=None,visibility='public',legal_verified=True) for c in cases]
  return dict(passed=all(c['correct'] for c in rows),status='PUBLIC_PASS' if all(c['correct'] for c in rows) else 'WRONG_ANSWER',tests_run=len(rows),tests_passed=sum(c['correct'] for c in rows),cases=rows,visibility='public')
class Tests(unittest.TestCase):
 def test_deep_private_rejected(self):
  for where in ('task_public','public_cases','example','source'):
   t=tasks(1)[0]
   target=t['task_public'] if where=='task_public' else t['public_cases'][0] if where=='public_cases' else t['task_public']['public_examples'][0] if where=='example' else t['public_cases'][0]['source']
   target['hidden_tests']={'input':'PRIVATE_SENTINEL'}
   with self.assertRaises(ValueError):strict_stream_task(t)
  t=tasks(1)[0];del t['public_cases'][0]['source']
  with self.assertRaises(ValueError):strict_stream_task(t)
 def test_action_and_budget_consistency(self):
  b=Budget(max_calls=3)
  self.assertEqual(eligible_actions('',PublicFeedback('NO_COMPLETE_CODE'),b),('REGENERATE_FRESH',))
  f=PublicFeedback.project(dict(visibility='public',status='WRONG_ANSWER',cases=[dict(visibility='public',legal_verified=True,input='0',expected='0',actual='1')]))
  self.assertEqual(observation('def f(): pass',f,b)['candidate_state'],'NO_ENTRY')
  self.assertEqual(eligible_actions('def f(): pass',f,b),('REGENERATE_FRESH',))
  self.assertEqual(eligible_actions('print(',PublicFeedback('COMPILE_ERROR'),b),ACTIONS)
  self.assertEqual(eligible_actions('print(0)',f,Budget(max_calls=1)),())
  cp=dict(max_calls=5,calls=2,max_tokens=100000,used_tokens=4000,max_tools=20,tool_calls=2,remaining_seconds=90.)
  restored=restore_budget(cp);self.assertEqual(restored.max_calls-restored.calls,3)
  self.assertEqual(choose(rule(minimum=3),'print(0)',f,restored),'REPAIR_EXISTING')
 def test_loop_revision_feedback_and_recovery(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   provider=Provider();p=plan();runner=e.ExperimentRunner(Path(tmp)/'F',p,provider.factory)
   stream=LearningStream(runner,tasks(),batch_size=1);stream.run()
   self.assertEqual(provider.calls['learning'],3)
   with stream.memory._transaction() as (rows,_):
    self.assertEqual(sum(x['event']=='CANDIDATE_SAVED' for x in rows),2)
    self.assertTrue(any(x.get('decision')=='SUSPEND' for x in rows))
   h=[x for x in stream.index.states().values() if x['applicable_actions']][0]
   self.assertEqual(h['content_version'],2);self.assertTrue(h['contradicting_evidence_ids']);self.assertGreaterEqual(h['independent_task_count'],2)
   calls=dict(provider.calls);runner2=e.ExperimentRunner(Path(tmp)/'F',p,provider.factory,resume=True);LearningStream(runner2,tasks(),batch_size=1).run();self.assertEqual(provider.calls,calls)
 def test_response_registration_recovery_no_resend(self):
  for point in ('RESPONSE_PERSISTED','CANDIDATE_REGISTERED','SOURCE_ASSESSED'):
   with self.subTest(point=point),tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
    provider=Provider();p=plan();runner=e.ExperimentRunner(Path(tmp)/'F',p,provider.factory)
    fired=[]
    def fault(stage):
     if stage==point and not fired:fired.append(stage);raise RuntimeError('injected crash')
    stream=LearningStream(runner,tasks(1),batch_size=1,fault=fault)
    with self.assertRaises(RuntimeError):stream.run()
    runner.save();runner=e.ExperimentRunner(Path(tmp)/'F',p,provider.factory,resume=True)
    LearningStream(runner,tasks(1),batch_size=1).run()
    self.assertEqual(provider.calls['learning'],2);self.assertEqual(provider.calls['validation'],2)
 def test_source_budget_and_private_stream_never_send(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   provider=Provider();p=plan();r=e.ExperimentRunner(Path(tmp)/'F',p,provider.factory)
   bad=tasks(1);bad[0]['public_cases'][0]['hidden_score']='PRIVATE_SENTINEL'
   with self.assertRaises(ValueError):LearningStream(r,bad)
   self.assertEqual(sum(provider.calls.values()),0)
   stream=LearningStream(r,tasks(1),arm='G');result=r.solve('G',tasks(1)[0]);stream.finalize(tasks(1)[0],result)
   source=next(k for k,v in stream.packets.items() if v['checkpoint_budget']['calls']==1)
   key=stream.memory.add(rule(minimum=3),[source]);job=dict(job_id='budget-probe',evidence_ids=[source])
   before=provider.calls['validation'];report=stream.assess(key,job,0)
   self.assertEqual(provider.calls['validation'],before);self.assertEqual(report['diagnosis'],'source applicability declined')
 def test_nested_effect_rejection_and_unchanged_rule(self):
  from failure_evo.repair_choice_memory import RuleMemory
  with tempfile.TemporaryDirectory() as tmp:
   m=RuleMemory(Path(tmp)/'rules',VERSION);one=m.add(rule(),['a']);two=m.add(rule(),['a','b'],parent_operator_id=one)
   self.assertEqual(one,two);self.assertEqual(m.state(one)['operator_version'],1)
   self.assertEqual(m.state(one)['permission'],'shadow')
 def test_unknown_stop(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   provider=Provider();p=plan();runner=e.ExperimentRunner(Path(tmp)/'F',p,provider.factory)
   runner.transports['learning'].sender=lambda wire:(_ for _ in ()).throw(TimeoutError('unknown'))
   with self.assertRaises(TimeoutError):LearningStream(runner,tasks(1),batch_size=1).run()
   runner.save();self.assertTrue(runner.budgets['learning'].snapshot()['unknown_or_pending_requests'])
   with self.assertRaises(ValueError):e.ExperimentRunner(Path(tmp)/'F',p,provider.factory,resume=True)
 def test_no_learning_budget_and_no_duplicate_compile(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   provider=Provider();r=e.ExperimentRunner(Path(tmp)/'F',plan(learning=0),provider.factory)
   stream=LearningStream(r,tasks(2),batch_size=1);stream.run()
   self.assertEqual(provider.calls['learning'],0)
   self.assertTrue(any(x['kind']=='SCHEDULE_DECISION' and x['payload']['reason']=='NO_BUDGET' for x in stream.index.events.records()))
 def test_private_input_same_boundary_g_m_f(self):
  for arm in ('G','M','F'):
   with tempfile.TemporaryDirectory() as tmp:
    provider=Provider();r=e.ExperimentRunner(Path(tmp)/arm,plan(),provider.factory)
    bad=tasks(1);bad[0]['task_public']['public_examples'][0]['source']['private_score']='PRIVATE_SENTINEL'
    with self.assertRaises(ValueError):LearningStream(r,bad,arm=arm)
    self.assertEqual(sum(provider.calls.values()),0)
    self.assertFalse(list((r.folder/'wire').glob('**/request.json')))
 def test_comparison_flag_and_counterexample_identity(self):
  t=tasks(1)[0];t['public_cases'][0]['case_insensitive']=True
  self.assertTrue(strict_stream_task(t)['public_cases'][0]['case_insensitive'])
  t['public_cases'][0]['case_insensitive']={'hidden':'sentinel'}
  with self.assertRaises(ValueError):strict_stream_task(t)
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   provider=Provider();r=e.ExperimentRunner(Path(tmp)/'F',plan(),provider.factory);stream=LearningStream(r,tasks(1),batch_size=1);stream.run()
   h=next(x for x in stream.index.states().values() if x['effects']);effect=h['effects'][0]
   with self.assertRaises(ValueError):stream.index.effect(h['hypothesis_id'],candidate_id=effect['candidate_id'],source_event_id=effect['source_event_id'],task_id='wrong-task',checkpoint_hash=effect['checkpoint_hash'],report=effect['report'],at=9999999999)
   with self.assertRaises(ValueError):stream.index.effect(h['hypothesis_id'],candidate_id=effect['candidate_id'],source_event_id=effect['source_event_id'],task_id=effect['task_id'],checkpoint_hash=effect['checkpoint_hash'],report=dict(effect['report'],hidden_score=1),at=9999999999)
 def test_tampered_saved_response_cannot_resume(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(e.prior,'Judge',FakeJudge):
   provider=Provider();p=plan();r=e.ExperimentRunner(Path(tmp)/'F',p,provider.factory)
   def fault(stage):
    if stage=='RESPONSE_PERSISTED':raise RuntimeError('crash')
   with self.assertRaises(RuntimeError):LearningStream(r,tasks(1),batch_size=1,fault=fault).run()
   r.save();rp=next((r.folder/'jobs').glob('*/*-response.json'));value=e.read(rp);value['text']='{}';e.write(rp,value)
   calls=dict(provider.calls);r=e.ExperimentRunner(Path(tmp)/'F',p,provider.factory,resume=True)
   with self.assertRaises(ValueError):LearningStream(r,tasks(1),batch_size=1).run()
   self.assertEqual(provider.calls,calls)
 def test_pilot_projection_preserves_scorer(self):
  import prepare_s19_pilot as prep
  if not all((e.ROOT/x).exists() for x in prep.SOURCES):self.skipTest('local historical development data unavailable')
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp)/'pilot';manifest=prep.freeze(folder);prepared=e.read(folder/'development_tasks.json')
   self.assertEqual(len(prepared),40)
   for task,origin in zip(prepared,manifest['rows']):
    strict_stream_task(task);old=e.read(e.ROOT/origin['source'])[origin['source_index']]
    for before,after in zip(old['public_cases'],task['public_cases']):
     for output in (before['expected'],before['expected']+'\n','INVALID','0','0.00000000001'):
      self.assertEqual(e.prior.old.accepts(task['task_id'],before,output),e.prior.old.accepts(task['task_id'],after,output))
   self.assertFalse(manifest['reserves_read'])
if __name__=='__main__':unittest.main()
