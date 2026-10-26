import copy,json,pathlib,hashlib,tempfile,unittest
from types import SimpleNamespace
import run_workflow_v2 as e
from run_learning_stream import LearningStream
from test_s19_v2 import tasks
from failure_evo import selective_experience as s
from failure_evo.contracts import fingerprint,atomic_json
from failure_evo.workflow_protocol_v2 import SharedTransport,prepare,PreflightRejected
from failure_evo.persistent_budget import PersistentBudget


def packet(tid,stage='l2b',code='print(0)',status='WRONG_ANSWER'):
 t=tasks(1)[0];t['task_public']['problem_id']=tid
 return dict(task_id=tid,task_public=t['task_public'],public_cases=t['public_cases'],code=code,feedback=dict(status=status,summary='Audited public result',visibility='public',public_cases=[dict(input='1\n',expected='1',actual='0',exception_class=None)]),stage=stage,checkpoint_budget=dict(max_calls=5,calls=2,max_tokens=100000,used_tokens=0,max_tools=10,tool_calls=0,remaining_seconds=30),event_id=tid+stage,candidate_sha256=hashlib.sha256(code.encode()).hexdigest(),artifact_state='STRUCTURAL_PASS')


def fixture():
 p=packet('source','l1');fact=dict(event_id=p['event_id'],task_id='source',stage='l1',candidate_sha256=p['candidate_sha256'],visibility='public',synthetic=False,observed_at=1,available_from=2)
 catalog={p['event_id']:dict(packet=p,fact=fact)}
 c=s.seal_card(dict(experience_id='fixture',origin='HUMAN_HYPOTHESIS',source_refs=[s.source_ref(p,fact)],observed_failure_pattern='Engineering fixture, no real benefit',applicability_conditions=dict(candidate_state='STRUCTURAL_PASS',repeat_same_program_feedback=True,remaining_calls_min=2),proposed_intervention=dict(kind='LEGAL_ACTION_SWITCH',action='REGENERATE_FRESH',guidance=''),expected_local_effect='Unverified',refusal_conditions=['unknown'],stop_conditions=['budget'],evidence_level='OBSERVED_PATTERN',uncertainty='Not verified',available_from=3))
 p=packet('target');h=dict(packet=packet('target','l2a'),observed_at=4)
 return p,h,c,catalog


def change(c,**kw):
 d={k:v for k,v in copy.deepcopy(c).items() if k not in ('card_hash','provenance_hash','version')};d.update(kw);return s.seal_card(d)


class Tests(unittest.TestCase):
 def setUp(self):self.p,self.h,self.c,self.catalog=fixture()
 def state(self):return s.snapshot(self.p,observed_at=5,history=[self.h])
 def decide(self,cards=None,**kw):return s.recommend(self.state(),cards or [self.c],enabled=True,source_catalog=self.catalog,**kw)
 def test_default_and_transparency(self):
  st=self.state();d=s.recommend(st,[self.c],source_catalog=self.catalog);self.assertIsNone(d['proposal']);_,a=s.prepare_view(st,d);self.assertFalse(a['request_changed'])
 def test_match_is_shadow_only(self):
  d=self.decide();self.assertEqual(d['proposal']['action'],'REGENERATE_FRESH');self.assertEqual(d['actual_kind'],'NO_INTERVENTION');self.assertEqual(d['permission'],'shadow')
 def test_no_repeat(self):
  self.h['packet']=packet('target','l2a','print(2)');self.assertIsNone(self.decide()['proposal'])
 def test_same_coarse_state_mismatch(self):
  self.h['packet']['feedback']['public_cases'][0]['actual']='2';self.assertFalse(self.state()['features']['repeat_same_program_feedback']);self.assertIsNone(self.decide()['proposal'])
 def test_conflict_abstains(self):
  c=change(self.c,experience_id='guidance',proposed_intervention=dict(kind='TARGETED_REPAIR_GUIDANCE',action='GENERIC',guidance='Compare unchanged public failure and source hash before reusing this implementation.'))
  self.assertEqual(self.decide([self.c,c])['reason'],'CONFLICT_ABSTAIN')
 def test_multiple_same_deterministic(self):
  c=change(self.c,experience_id='z');a=self.decide([self.c,c]);self.assertEqual(a,self.decide([c,self.c]));self.assertEqual(len(a['matched_ids']),2)
 def test_budget(self):
  for key,value in [('calls',4),('used_tokens',100000),('tool_calls',10),('remaining_seconds',0)]:
   with self.subTest(key=key):
    self.p=packet('target');self.p['checkpoint_budget'][key]=value;self.assertIsNone(self.decide()['proposal'])
 def test_pass_unknown_evaluator(self):
  for status in ('PUBLIC_PASS','UNKNOWN','EVALUATOR_ERROR','PRIVATE_RESULT_WITHHELD'):
   self.p['feedback']['status']=status;self.assertIsNone(self.decide()['proposal'])
 def test_future_history(self):
  self.h['observed_at']=6
  with self.assertRaises(ValueError):self.state()
 def test_later_stage_equal_clock_rejected(self):
  self.h['packet']['stage']='l3';self.h['observed_at']=5
  with self.assertRaises(ValueError):self.state()
 def test_future_card(self):self.assertIsNone(self.decide([change(self.c,available_from=6)])['proposal'])
 def test_task_and_lineage_isolation(self):
  self.assertIsNone(self.decide(target_lineage='source')['proposal']);self.p=packet('source');self.h=dict(packet=packet('source','l2a'),observed_at=4);self.assertIsNone(self.decide()['proposal'])
 def test_unverified_source(self):
  self.catalog['sourcel1']['packet']['code']='print(1)'
  with self.assertRaises(ValueError):self.decide()
 def test_unknown_evidence(self):self.assertIsNone(self.decide([change(self.c,evidence_level='UNKNOWN')])['proposal'])
 def test_no_verified_self_claim(self):
  with self.assertRaises(ValueError):change(self.c,evidence_level='VERIFIED')
 def test_private_input(self):
  self.p['hidden_tests']=[]
  with self.assertRaises(ValueError):self.state()
 def test_guidance_same_action_different_wire(self):
  c=change(self.c,proposed_intervention=dict(kind='TARGETED_REPAIR_GUIDANCE',action='GENERIC',guidance='The earlier retry returned identical code and public feedback; check whether the intended edit was actually applied before repeating that request.'))
  st=self.state();d=self.decide([c]);_,audit=s.prepare_view(st,d,offline_proposal=True);self.assertTrue(audit['request_changed']);self.assertFalse(audit['action_changed'])
 def test_switch_preview_no_send(self):
  st=self.state();d=self.decide();_,a=s.prepare_view(st,d,offline_proposal=True);self.assertTrue(a['action_changed']);_,b=s.prepare_view(st,d);self.assertFalse(b['request_changed'])
 def test_changed_state_rejected(self):
  st=self.state();d=self.decide();st['evidence']['packet']['code']='print(9)'
  with self.assertRaises(ValueError):s.prepare_view(st,d)
 def test_freeze_determinism(self):self.assertEqual(self.decide(),self.decide())
 def test_restart_completed_and_unknown_no_resend(self):
  for unknown in (False,True):
   with tempfile.TemporaryDirectory() as td:
    path=pathlib.Path(td);cfg=e.prior.config(3,10,150000);budget=PersistentBudget(path/'budget.jsonl',run_id='fixture',protocol_hash='s21',**cfg);calls=[]
    def sender(wire):
     calls.append(wire)
     if unknown:raise OSError('injected lost response')
     return dict(model='deepseek-flash',usage=dict(prompt_tokens=1,completion_tokens=1,total_tokens=2),choices=[dict(message=dict(content='fixture'),finish_reason='stop')])
    auth=dict(run_id='fixture',protocol_hash='s21');tr=SharedTransport(budget,sender,authorized=auth);wire,_=s.prepare_view(self.state(),self.decide(),offline_proposal=True)
    stream=SimpleNamespace(runner=SimpleNamespace(transports={'solve':tr}))
    try:LearningStream.send_prepared(stream,'solve',wire,'frozen-id')
    except OSError:pass
    atomic_json(path/'audit.json',tr.audit);restored=SharedTransport(PersistentBudget(path/'budget.jsonl',run_id='fixture',protocol_hash='s21',**cfg),sender,authorized=auth,audit=json.loads((path/'audit.json').read_text()));stream.runner.transports['solve']=restored
    if unknown:
     with self.assertRaises(ValueError):LearningStream.send_prepared(stream,'solve',wire,'frozen-id')
    else:
     result=LearningStream.send_prepared(stream,'solve',wire,'frozen-id');self.assertEqual(result['text'],'fixture')
    self.assertEqual(len(calls),1)
if __name__=='__main__':unittest.main()
