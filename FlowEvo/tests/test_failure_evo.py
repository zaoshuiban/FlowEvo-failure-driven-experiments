"""Acceptance tests for real boundary, budget, version and state-machine behavior."""
import copy,hashlib,json,pathlib,sys,tempfile,unittest,difflib
from dataclasses import replace
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from failure_evo import *
from failure_evo.runtime import BudgetExhausted

class Acceptance(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.fp=Fingerprint('clean1','score1','fixture-model','deps1','protocol1');self.task={'task_id':'unit','prompt':'repair this array','input_output':{'secret':'HIDDEN_A'},'future_trace':'FUTURE_A'}
 def tearDown(self):self.tmp.cleanup()
 def path(self,name,text):p=self.root/name;p.write_text(text);return p
 def card(self,**changes):
  p=self.path('op.py','def repair_operator(payload):\n    return {"status":"declined"}\n')
  c=OperatorCard('unitop','v1','active',str(p),hashlib.sha256(p.read_bytes()).hexdigest(),self.fp,10,required_ast_names=('x',),prompt_terms=('array',),evidence_scope='unit-test-only',evidence_id='unit-test-only')
  return replace(c,**changes)
 def choose(self,cards,at=20,budget=None,context=None,validator=None):return Router(cards,evidence_validator=validator or (lambda c,fp,t:True)).choose(PublicTaskView.project(self.task),'x = 1',PublicFeedback('WRONG_ANSWER'),'l3',context or self.fp,at,budget or Budget(clock=lambda:0))
 def solve(self,task=None,status='WRONG_ANSWER',codes=None,budget=None,router=None,runner=None):
  requests=[];seq=iter(codes or ['x=1']*5)
  def gen(request):requests.append(copy.deepcopy(request));return {'code':next(seq),'model':self.fp.model,'usage':{'total_tokens':10}}
  c=Controller(gen,lambda t,code:{'status':status,'visibility':'public'},self.fp,router=router,operator_runner=runner,clock=lambda:20,max_output=1000)
  return c.solve(task or self.task,budget or Budget(clock=lambda:0)),requests
 def test_public_projection_drops_hidden(self):
  p=PublicTaskView.project(self.task).to_dict();self.assertNotIn('input_output',p);self.assertNotIn('future_trace',p)
 def test_examples_require_verified_public(self):
  t={**self.task,'public_examples':[{'input':1,'expected':2,'visibility':'private','legal_verified':True},{'input':3,'expected':4,'visibility':'public','legal_verified':True,'secret':'bad'}]}
  self.assertEqual(PublicTaskView.project(t).to_dict()['public_examples'],[{'input':3,'expected':4}])
 def test_view_is_immutable_copy(self):
  t={**self.task,'public_examples':[{'input':[1],'expected':2,'visibility':'public','legal_verified':True}]};p=PublicTaskView.project(t);t['public_examples'][0]['input'][0]=999;self.assertEqual(p.to_dict()['public_examples'][0]['input'],[1])
 def test_private_feedback_withheld(self):self.assertEqual(PublicFeedback.project({'visibility':'private','status':'PUBLIC_PASS','summary':'SECRET'}).status,'PRIVATE_RESULT_WITHHELD')
 def test_arbitrary_feedback_not_copied(self):self.assertNotIn('SECRET',str(PublicFeedback.project({'visibility':'public','status':'WRONG_ANSWER','summary':'SECRET'}).to_dict()))
 def test_hidden_mutations_leave_prompts_unchanged(self):
  _,a=self.solve();t={**self.task,'input_output':{'secret':'HIDDEN_B'},'future_trace':'FUTURE_B','final_score':True};_,b=self.solve(task=t);self.assertEqual(a,b)
 def test_disabled_router_has_exact_stage_skeleton(self):
  r,q=self.solve();self.assertEqual([x['stage'] for x in q],['l1','l2a','l2b','l3','l4']);self.assertTrue(all('feedback' not in x for x in q[:3]));self.assertEqual(q[3]['previous_candidate'],'x=1');self.assertEqual(r['budget']['calls'],5)
 def test_stop_on_public_acceptance(self):r,q=self.solve(status='PUBLIC_PASS');self.assertEqual(len(q),1);self.assertEqual(r['selected']['stage'],'l1')
 def test_private_pass_cannot_stop_workflow(self):
  calls=[]
  def gen(q):calls.append(q);return {'code':'x=1','model':self.fp.model,'usage':{'total_tokens':1}}
  r=Controller(gen,lambda t,c:{'visibility':'private','status':'PUBLIC_PASS'},self.fp,max_output=10).solve(self.task,Budget(clock=lambda:0));self.assertEqual(len(calls),5);self.assertEqual(r['status'],'UNRESOLVED')
 def test_bad_later_artifact_does_not_erase_earlier(self):
  r,_=self.solve(codes=['x=1','x=2','x=3','','bad ```']);self.assertEqual(len(r['retained_candidates']),5);self.assertEqual(r['events'][0]['code'],'x=1');self.assertIsNone(r['selected'])
 def test_empty_code_is_not_executed(self):
  def bad(*args):raise AssertionError('must not evaluate empty code')
  r=Controller(lambda q:{'code':'','model':self.fp.model,'usage':{'total_tokens':1}},bad,self.fp,max_output=10).solve(self.task,Budget(max_calls=1,clock=lambda:0));self.assertEqual(r['events'][0]['public_feedback']['status'],'NO_COMPLETE_CODE')
 def test_model_drift_stops(self):
  r=Controller(lambda q:{'code':'x=1','model':'different','usage':{'total_tokens':1}},lambda t,c:None,self.fp,max_output=10).solve(self.task,Budget(clock=lambda:0));self.assertEqual(r['budget']['calls'],1);self.assertIn('error',r['events'][0])
 def test_unknown_provider_failure_is_charged(self):
  def fail(q):raise ConnectionError()
  r=Controller(fail,lambda t,c:None,self.fp,max_output=10).solve(self.task,Budget(clock=lambda:0));self.assertEqual(r['budget']['calls'],1);self.assertGreater(r['budget']['charged_or_reserved_tokens'],4096)
 def test_call_limit(self):r,_=self.solve(budget=Budget(max_calls=2,clock=lambda:0));self.assertEqual(r['budget']['calls'],2)
 def test_token_reservation_prevents_call(self):r,q=self.solve(budget=Budget(max_tokens=1,clock=lambda:0));self.assertEqual(q,[]);self.assertEqual(r['budget']['calls'],0)
 def test_invalid_usage_consumes_reserved_budget(self):
  b=Budget(max_tokens=1000,clock=lambda:0);key=b.reserve(10,20)
  with self.assertRaises(BudgetExhausted):b.settle(key,True)
  self.assertEqual(b.used_tokens,30)
 def test_overreported_usage_cannot_refund(self):
  b=Budget(max_tokens=100,clock=lambda:0);k=b.reserve(10,20)
  with self.assertRaises(BudgetExhausted):b.settle(k,1000)
  self.assertEqual(b.used_tokens,30)
 def test_zero_tool_budget_stops_without_more_model_calls(self):r,_=self.solve(budget=Budget(max_tools=0,clock=lambda:0));self.assertEqual(r['budget']['calls'],1)
 def test_deadline_overrun_not_accepted(self):
  now=[0]
  def gen(q):now[0]=2;return {'code':'x=1','model':self.fp.model,'usage':{'total_tokens':1}}
  r=Controller(gen,lambda t,c:{'visibility':'public','status':'PUBLIC_PASS'},self.fp,max_output=10).solve(self.task,Budget(wall_seconds=1,clock=lambda:now[0]));self.assertIsNone(r['selected']);self.assertEqual(r['budget']['calls'],1)
 def test_negative_budget_rejected(self):
  with self.assertRaises(ValueError):Budget(max_calls=-1)
 def test_router_requires_formal_admission(self):
  c=self.card();selected,blocked=Router([c]).choose(PublicTaskView.project(self.task),'x=1',PublicFeedback('WRONG_ANSWER'),'l3',self.fp,20,Budget(clock=lambda:0));self.assertIsNone(selected);self.assertEqual(blocked[0]['reason'],'no_valid_admission_record')
 def test_registry_exception_falls_back(self):
  def invalid(*args):raise OSError('registry unavailable')
  selected,blocked=self.choose([self.card()],validator=invalid);self.assertIsNone(selected);self.assertEqual(blocked[0]['reason'],'evidence_lookup_failed')
 def test_router_accepts_exact_qualified_scope(self):self.assertEqual(self.choose([self.card()])[0].operator_id,'unitop')
 def test_future_card_invisible(self):self.assertIsNone(self.choose([self.card(published_at=30)])[0])
 def test_experimental_not_callable(self):self.assertIsNone(self.choose([self.card(status='experimental')])[0])
 def test_artifact_drift_blocks(self):
  c=self.card();pathlib.Path(c.artifact_path).write_text('changed');self.assertIsNone(self.choose([c])[0])
 def test_every_fingerprint_dimension_blocks(self):
  c=self.card()
  for key in ['baseline','scorer','model','dependencies','protocol']:
   with self.subTest(key=key):self.assertIsNone(self.choose([c],context=replace(self.fp,**{key:'changed'}))[0])
 def test_missing_ast_precondition_declines(self):self.assertIsNone(self.choose([self.card(required_ast_names=('missing',))])[0])
 def test_unknown_applicability_declines(self):self.assertIsNone(self.choose([self.card(required_ast_names=(),prompt_terms=())])[0])
 def test_conflict_declines(self):
  c=self.card();self.assertIsNone(self.choose([c,replace(c,operator_id='other')])[0])
 def test_fallback_budget_reserved(self):self.assertIsNone(self.choose([self.card(max_seconds=50)],budget=Budget(wall_seconds=50,clock=lambda:0))[0])
 def test_dependency_hash_drift_blocks(self):
  p=self.path('dependency','before');c=self.card(dependency_files=((str(p),hashlib.sha256(p.read_bytes()).hexdigest()),));self.assertIsNotNone(self.choose([c])[0]);p.write_text('after');self.assertIsNone(self.choose([c])[0])
 def test_operator_decline_uses_same_model_slot(self):
  class Runner:
   def run(self,*a):return {'status':'declined'}
  r,q=self.solve(router=Router([self.card()],lambda *a:True),runner=Runner());self.assertEqual(len(q),5);self.assertNotIn('operator_proposal',q[3]);self.assertEqual(r['events'][3]['operator_status'],'declined')
 def test_operator_diagnosis_replaces_no_extra_call(self):
  class Runner:
   def run(self,*a):return {'status':'proposed','diagnostic':'unit diagnostic'}
  r,q=self.solve(router=Router([self.card()],lambda *a:True),runner=Runner());self.assertEqual(len(q),5);self.assertEqual(q[3]['operator_proposal'],{'diagnostic':'unit diagnostic'});self.assertNotIn('operator_proposal',q[4])
 def test_operator_exception_has_budgeted_fallback(self):
  class Runner:
   def run(self,*a):raise RuntimeError()
  r,q=self.solve(router=Router([self.card()],lambda *a:True),runner=Runner());self.assertEqual(len(q),5);self.assertEqual(r['events'][3]['operator_status'],'error')
 def test_sandbox_output_contract_rejects_non_dict(self):
  class Worker:
   def __init__(self,*a):pass
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def call(self,q):return {'status':'OK','value':['wrong']}
  self.assertEqual(SandboxOperatorRunner(Worker).run(self.card(),{},1)['status'],'error')
 def test_sandbox_output_excludes_unrecognized_fields(self):
  class Worker:
   def __init__(self,*a):pass
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def call(self,q):return {'status':'OK','value':{'status':'declined','hidden_score':1}}
  self.assertEqual(SandboxOperatorRunner(Worker).run(self.card(),{},1),{'status':'declined'})
 def test_forbidden_operator_import_not_executed(self):
  c=self.card();p=pathlib.Path(c.artifact_path);p.write_text('import os\ndef repair_operator(p):\n return {"status":"declined"}\n');c=replace(c,artifact_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
  def bad(*args):raise AssertionError('forbidden source reached executor')
  self.assertEqual(SandboxOperatorRunner(bad).run(c,{},1)['reason'],'static_operator_policy_rejected')
 def test_operator_hash_rechecked_before_execution(self):
  c=self.card();pathlib.Path(c.artifact_path).write_text('changed')
  self.assertEqual(SandboxOperatorRunner(None).run(c,{},1)['reason'],'artifact_changed_before_execution')
 def test_event_chain_detects_tampering(self):
  s=EvidenceStore(self.root/'events');s.append('OBSERVE',{'a':1},1);s.path.write_text(s.path.read_text().replace('"a":1','"a":2'))
  with self.assertRaises(ValueError):s.records()
 def test_future_events_filtered(self):
  s=EvidenceStore(self.root/'events');s.append('OBSERVE',{},1);s.append('OBSERVE',{},3);self.assertEqual(len(s.visible(2)),1)
 def test_no_backdated_event(self):
  s=EvidenceStore(self.root/'events');s.append('OBSERVE',{},2)
  with self.assertRaises(ValueError):s.append('OBSERVE',{},1)
 def witness(self,problem='p1',group='g1'):
  data={'legal_case':{'legal_verified':True,'visibility':'public','case_id':'c'},'oracle':{'independent':True,'method':'unit-fixture','case_id':'c','expected':1},'original_run':{'status':'RUNTIME_ERROR','exception_class':'IndexError','case_id':'c','code_sha256':'abc','expected':1},'patched_run':{'status':'PASS','tests_passed':1},'review':{'mechanism_verified':True,'violated_invariant':'unit invariant','reviewer':'UNIT_TEST_ONLY'}};files={}
  original='x=[]\nprint(x[0])\n';patched='x=[1]\nprint(x[0])\n';codehash=hashlib.sha256(original.encode()).hexdigest();data['original_run']['code_sha256']=codehash;data['patched_run'].update(original_witness_passed=True,case_id='c',code_sha256=hashlib.sha256(patched.encode()).hexdigest())
  for key,value in data.items():
   p=self.path(problem+'_'+key,json.dumps(value));files[key]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  for key,value in [('original_code',original),('patched_code',patched),('minimal_patch',''.join(difflib.unified_diff(original.splitlines(True),patched.splitlines(True),fromfile='original.py',tofile='patched.py')))]:
   p=self.path(problem+'_'+key,value);files[key]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  return {'witness_id':problem,'problem_id':problem,'provenance_group_id':group,'provenance_reviewed':True,'mechanism_id':'unit-mechanism','synthetic':False,'purpose':'HISTORICAL_FUNCTIONAL_FAILURE','observed_at':1,'code_sha256':codehash,'files':files}
 def test_synthetic_fixture_cannot_certify(self):
  s=MechanismStore(self.root/'mechanisms');w=self.witness();w['synthetic']=True
  with self.assertRaises(ValueError):s.certify(w,2)
 def test_witness_file_drift_rejected(self):
  s=MechanismStore(self.root/'mechanisms');w=self.witness();pathlib.Path(w['files']['oracle']['path']).write_text('{}')
  with self.assertRaises(ValueError):s.certify(w,2)
 def test_certification_not_backdated(self):
  with self.assertRaises(ValueError):MechanismStore(self.root/'mechanisms').certify(self.witness(),0)
 def test_singleton_cannot_publish(self):
  s=MechanismStore(self.root/'mechanisms');s.certify(self.witness(),2)
  with self.assertRaises(ValueError):s.publish('unit-mechanism',3)
 def test_duplicate_problem_not_independent_support(self):
  s=MechanismStore(self.root/'mechanisms');w=self.witness();s.certify(w,2);s.certify(w,3);s.certify(w,4);self.assertEqual(s.supports('unit-mechanism',5)['distinct_problems'],1)
 def test_same_source_group_not_cross_source(self):
  s=MechanismStore(self.root/'mechanisms')
  for i in range(3):s.certify(self.witness('p'+str(i),'onegroup'),2+i)
  with self.assertRaises(ValueError):s.publish('unit-mechanism',5)
 def test_unreviewed_sources_cannot_publish(self):
  s=MechanismStore(self.root/'mechanisms')
  for i in range(3):
   w=self.witness('p'+str(i),'g'+str(i));w['provenance_reviewed']=False;s.certify(w,2+i)
  with self.assertRaises(ValueError):s.publish('unit-mechanism',5)
 def test_cross_task_gate_and_future_certification(self):
  s=MechanismStore(self.root/'mechanisms')
  for i in range(3):s.certify(self.witness('p'+str(i),'g'+str(i%2)),2+i)
  self.assertEqual(s.supports('unit-mechanism',1)['distinct_problems'],0);self.assertEqual(s.publish('unit-mechanism',5)['payload']['state'],'CROSS_TASK_SUPPORTED_NOT_HEADROOM_TESTED')
 def test_headroom_requires_cross_task_support(self):
  with self.assertRaises(ValueError):MechanismStore(self.root/'mechanisms').record_headroom('x','missing',2)
 def gate(self,c,role='FORMAL_ADMISSION'):
  policy=self.path('policy.json','{"role":"UNIT_TEST_ONLY"}')
  g={'operator_id':c.operator_id,'version':c.version,'decision':'ADMIT','evidence_role':role,'frozen_before_evaluation':True,'independent_validation':True,'contract_checks_passed':True,'scope_checks_passed':True,'generation_data_isolated':True,'independent_source_groups':2,'artifact_sha256':c.artifact_sha256,'fingerprint':c.evidence_fingerprint.to_dict(),'scope':c.evidence_scope,'evaluated_at':10,'promotion_policy_file':str(policy),'promotion_policy_sha256':hashlib.sha256(policy.read_bytes()).hexdigest()};return self.path('gate.json',json.dumps(g))
 def test_experimental_gate_cannot_admit(self):
  c=self.card();registry=AdmissionRegistry(self.root/'admission')
  with self.assertRaises(ValueError):registry.admit(c,self.gate(c,'EXPERIMENTAL'),20)
 def test_admission_is_bound_to_evidence_file(self):
  c=self.card();gate=self.gate(c);registry=AdmissionRegistry(self.root/'admission');registry.admit(c,gate,20);self.assertTrue(registry.valid(c,self.fp,21));gate.write_text('{}');self.assertFalse(registry.valid(c,self.fp,21))
 def test_suspension_invalidates_routing(self):
  c=self.card();registry=AdmissionRegistry(self.root/'admission');registry.admit(c,self.gate(c),20);registry.suspend(c,'changed scorer',21);self.assertTrue(registry.valid(c,self.fp,20));self.assertFalse(registry.valid(c,self.fp,22))
 def test_admission_future_invisible(self):
  c=self.card();registry=AdmissionRegistry(self.root/'admission');registry.admit(c,self.gate(c),20);self.assertFalse(registry.valid(c,self.fp,19))

if __name__=='__main__':unittest.main()
