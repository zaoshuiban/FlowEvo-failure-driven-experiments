import unittest,json,tempfile,sys,copy,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.corrective_mechanism import parse,difference_check,algorithm_spec,FIELDS
from failure_evo.semantic_contract import artifact,SplitRunner,parse_contract,component_check,FIELDS as CF
from failure_evo.operator_test_generation import IndependentOracle
from failure_evo.operator_dual_validation import evaluate,development_passed
from failure_evo.operator_version_gate import VersionGate
from failure_evo.math_operator_v3_pipeline import CorrectiveAdapter
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.math_operators import FrozenMathLibrary
from code_math.no_gold import PublicMathTask,NoGoldMathController,NoGoldPolicy
IMAGE='sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8'
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
SOLVE="def solve(parameters):\n    return str(parameters['x']+1)\n"
MATCH="""def match(problem):
    if problem == 'Add one to 2':
        return {'status':'MATCH','parameters':{'x':2},'reason':'exact fixture','assumption_quotes':['Add one'],'requested_quantity':'successor'}
    return {'status':'UNKNOWN','parameters':{},'reason':'uncertain','assumption_quotes':[],'requested_quantity':''}
"""
class Tests(unittest.TestCase):
 def setUp(self):
  if os.environ.get('V3_TEST_ARTIFACT_DIR'):
   self.temp=None;self.p=Path(os.environ['V3_TEST_ARTIFACT_DIR'])/self._testMethodName;self.p.mkdir(parents=True)
  else:self.temp=tempfile.TemporaryDirectory(dir=ROOT,prefix='.v3-test-');self.p=Path(self.temp.name)
  self.contract={k:'engineering fixture' for k in CF};self.contract.update(parameter_schema=json.dumps(dict(type='object',properties={'x':{'type':'integer'}},required=['x'],additionalProperties=False)),requested_quantity='successor')
  self.a=artifact(self.p,SOLVE,MATCH,self.contract,provenance={'origin':'MOCK'})
  self.runner=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),self.p/'worker.jsonl')
 def tearDown(self):
  if self.temp:self.temp.cleanup()
 def test_correction_not_text_certification(self):
  m={k:'same' for k in FIELDS};m.update(source_evidence_ids=['e'],generation_decision='PROPOSE_CORRECTION')
  self.assertEqual(difference_check(m)['status'],'ERROR_REPRODUCTION_RISK');m['proposed_corrective_operation']='different'
  self.assertFalse(difference_check(m)['verified']);self.assertNotIn('suspected_invalid_operation',algorithm_spec(m))
  for d in ('NO_MECHANISM','HYPOTHESIS_ONLY'):
   m['generation_decision']=d;parse(m)
   with self.assertRaises(PermissionError):algorithm_spec(m)
 def test_components_real_worker(self):
  m=self.runner.match(self.a,'Add one to 2');self.assertEqual(m['parameters'],{'x':2})
  self.assertEqual(self.runner.solve(self.a,{'x':2})['answer'],'3')
  self.assertEqual(self.runner.run(self.a,PublicMathTask('t','other'))['status'],'DECLINED')
  self.assertEqual(self.runner.solve(self.a,{'x':'bad'})['status'],'ERROR')
 def test_version_and_permissions(self):
  b=artifact(self.p,SOLVE.replace('+1','+2'),MATCH,self.contract,provenance={'origin':'MOCK'})
  c=artifact(self.p,SOLVE,MATCH+'\n',self.contract,provenance={'origin':'MOCK'})
  self.assertNotEqual(b['code_sha256'],self.a['code_sha256']);self.assertNotEqual(c['code_sha256'],self.a['code_sha256'])
  self.assertFalse(component_check('import os\n'+SOLVE,'solve')['passed'])
 def test_oracle_rejects_self_and_unverified(self):
  proposal=dict(kind='POSITIVE',problem='new',base_problem='',changed_dimension='x',claimed_behavior='MATCH',invariant='')
  self.assertEqual(IndependentOracle([],candidate_hashes=[]).audit_all([proposal])[0]['review']['status'],'UNVERIFIED')
  with self.assertRaises(PermissionError):IndependentOracle([dict(authority='MODEL',reference_sha256='x')],candidate_hashes=[])
  with self.assertRaises(PermissionError):IndependentOracle([dict(authority='HOST_INDEPENDENT_REVIEW',reference_sha256=self.a['solver_sha256'],derived_from_candidate=False)],candidate_hashes=[self.a['solver_sha256']])
 def test_gold_stays_in_oracle_and_all_metrics(self):
  cases=[dict(proposal=dict(problem='Add one to 2'),review=dict(status='VERIFIED',record=dict(supported=True,parameters={'x':2},answer='3'))),dict(proposal=dict(problem='other'),review=dict(status='VERIFIED',record=dict(supported=False)))]
  rows=evaluate(self.runner,self.a,cases);self.assertEqual(rows[0]['computation'],'CORRECT');self.assertEqual(rows[1]['applicability'],'UNKNOWN');self.assertFalse(development_passed(rows))
  self.assertNotIn('gold_answer',(self.p/'worker.jsonl').read_text())
 def test_registry_shadow_no_admission_and_gate_consume(self):
  reg=VersionGate(self.p/'registry');reg.shadow(self.a);self.assertEqual(reg.eligible(PublicMathTask('later','x'),99),[])
  with self.assertRaises(PermissionError):reg.admit(self.a,dict(passed=True),after_sequence=1)
  with self.assertRaises(PermissionError):reg.freeze_gate([self.a],data_hash='d',development_ids=['x'],gate_ids=['x'])
  reg.freeze_gate([self.a],data_hash='d',development_ids=['x'],gate_ids=['y'])
  verdict=reg.record_review(self.a,[],role='Gate',data_hash='d',exposed=False)
  with self.assertRaises(PermissionError):reg.admit(self.a,verdict,after_sequence=1)
  with self.assertRaises(PermissionError):reg.record_review(self.a,[],role='Gate',data_hash='d',exposed=False)
 def test_disabled_and_fallback_controller(self):
  class Client:
   def generate_no_gold(self,**kw):return dict(text='The answer is 3',usage=dict(prompt_tokens=1,completion_tokens=1),reasoning_tokens=0)
  class Library:
   def run(self,*a,**k):raise AssertionError('disabled feature called')
  c=NoGoldMathController(Client(),self.p/'controller',policy=NoGoldPolicy(),library=Library());self.assertEqual(c.solve(PublicMathTask('t','x'),episode_id='e',sequence=1)['model_calls'],2)
  reg=VersionGate(self.p/'reg');reg.shadow(self.a);lib=FrozenMathLibrary(reg,self.runner,engineering=True)
  c=NoGoldMathController(Client(),self.p/'c2',policy=NoGoldPolicy(operators_enabled=True),library=lib);self.assertEqual(c.solve(PublicMathTask('t2','x'),episode_id='e2',sequence=2)['model_calls'],2)
 def test_schema_ref_and_unbound_quote_rejected(self):
  c=dict(self.contract,parameter_schema=json.dumps({'type':'object','additionalProperties':False,'$ref':'https://invalid.example/schema'}))
  with self.assertRaises(ValueError):parse_contract(c)
  bad=MATCH.replace("['Add one']","['not in statement']")
  a=artifact(self.p,SOLVE,bad,self.contract,provenance={'origin':'MOCK'})
  self.assertEqual(self.runner.match(a,'Add one to 2')['status'],'UNKNOWN')
 def test_only_refusal_cannot_pass(self):
  self.assertFalse(development_passed([dict(applicability='CORRECT_REFUSAL',combined='CORRECT_REFUSAL',computation='UNVERIFIED')]))
 def test_new_version_not_in_gate_set(self):
  reg=VersionGate(self.p/'gate');reg.freeze_gate([self.a],data_hash='g',development_ids=['d'],gate_ids=['g'])
  b=artifact(self.p,SOLVE.replace('+1','+2'),MATCH,self.contract,provenance={'origin':'MOCK'})
  with self.assertRaises(PermissionError):reg.record_review(b,[],role='Gate',data_hash='g',exposed=False)
 def test_parameter_mismatch_not_combined_success(self):
  cases=[dict(proposal=dict(problem='Add one to 2'),review=dict(status='VERIFIED',record=dict(supported=True,parameters={'x':1},answer='2')))]
  r=evaluate(self.runner,self.a,cases)[0]
  self.assertEqual(r['computation'],'CORRECT');self.assertEqual(r['combined'],'PARAMETER_MISMATCH')
 def test_finite_trial_and_actual_decline_fallback(self):
  from failure_evo.operator_version_gate import V3FrozenLibrary
  reg=VersionGate(self.p/'trial')
  # Mock host-qualified receipt only, never a real admission claim.
  reg.events.append('MATH_EXPERIMENTAL',dict(artifact=self.a,validation={'origin':'MOCK'},effective_after=1),0)
  self.assertEqual(reg.eligible(PublicMathTask('future','other'),2),[])
  reg.authorize_trial(self.a,future_task_ids=['future'],max_uses=1,after_sequence=1)
  lib=V3FrozenLibrary(reg,self.runner,engineering=True)
  class Client:
   def generate_no_gold(self,**kw):return dict(text='The answer is 3',usage=dict(prompt_tokens=1,completion_tokens=1),reasoning_tokens=0)
  c=NoGoldMathController(Client(),self.p/'trial_controller',policy=NoGoldPolicy(operators_enabled=True),library=lib)
  row=c.solve(PublicMathTask('future','other'),episode_id='trial',sequence=2)
  self.assertTrue(row['fallback']);self.assertEqual(row['model_calls'],2)
  self.assertEqual(reg.eligible(PublicMathTask('future','other'),3),[])
 def test_applied_is_not_gold_rescued(self):
  class Client:
   def generate_no_gold(self,**kw):raise AssertionError('hidden rescue invoked')
  class Library:
   def run(self,*a,**k):return [dict(status='APPLIED',answer='wrong but unscored',seconds=0)]
  c=NoGoldMathController(Client(),self.p/'no_rescue',policy=NoGoldPolicy(operators_enabled=True),library=Library())
  row=c.solve(PublicMathTask('q','question'),episode_id='locked',sequence=2)
  self.assertEqual(row['final_output'],'wrong but unscored');self.assertEqual(row['model_calls'],0)
 def test_host_schema_regex_is_not_executed(self):
  c=dict(self.contract,parameter_schema=json.dumps({'type':'object','additionalProperties':False,'properties':{'x':{'type':'string','pattern':'(a+)+$'}}}))
  with self.assertRaises(ValueError):parse_contract(c)
 def test_mock_gpt_to_split_worker_complete(self):
  from failure_evo.compile_queue import BoundedCompiler
  from failure_evo.persistent_budget import PersistentBudget
  from failure_evo.contracts import canonical
  rows=json.loads((ROOT/'runs/math_p2_all12_20261027_01/source_failures.json').read_text())
  h={k:'Mock fixture only' for k in FIELDS};h.update(source_evidence_ids=[rows[0]['evidence_id']],generation_decision='PROPOSE_CORRECTION')
  values=iter([h,dict(code=SOLVE,description=json.dumps(dict(contract=self.contract,tests=[])),applicability=MATCH)])
  wires=[]
  def send(w):
   wires.append(w)
   return dict(model='openai/gpt-5.4',id='mock-v3',choices=[dict(message=dict(content=json.dumps(next(values))),finish_reason='stop')],usage=dict(prompt_tokens=10,completion_tokens=10,total_tokens=20))
  b=PersistentBudget(self.p/'compile_budget',run_id='engineering:v3mock',protocol_hash='mock',max_calls=3,max_tokens=233472,max_tools=0,max_cost_microusd=4000000,token_rate_microusd_per_million=15000000,tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=20000,wall_seconds=300)
  a=CorrectiveAdapter(self.p/'provider',b,model='gpt-5.4',mock=True,sender=send,max_wire_input_upper=65536)
  c=BoundedCompiler(a,b,self.p/'compiler','gpt-5.4',max_input_upper=65536,max_output_upper=8192)
  job=dict(stream_id=b.config['run_id'],family_id='v3',arm='F',source_ids=h['source_evidence_ids'],discovery={'events':rows})
  import time
  found=c.request(job,'induction',0,time.time(),output_upper=8192);job['specification']=found['specification']
  result=c.request(job,'candidate',0,time.time(),output_upper=8192)
  made=artifact(self.p/'generated',result['code'],result['applicability'],json.loads(result['description'])['contract'],provenance={'origin':result['origin']})
  self.assertEqual(self.runner.run(made,PublicMathTask('mock','Add one to 2'))['answer'],'3')
  payload=json.loads(wires[-1]['messages'][1]['content']);self.assertNotIn('failure_diagnosis',payload['corrective_algorithm_specification'])
  self.assertNotIn('gold_answer',canonical(wires));self.assertEqual(result['origin'],'MOCK')
 def test_deepseek_component_explicit_provider_and_public_wire(self):
  from failure_evo.math_v3_component_generation import DeepSeekComponentAdapter
  from failure_evo.persistent_budget import PersistentBudget
  rows=json.loads((ROOT/'runs/math_p2_all12_20261027_01/source_failures.json').read_text())
  b=PersistentBudget(self.p/'dsbudget',run_id='engineering:ds',protocol_hash='p',max_calls=1,max_tokens=100000,max_tools=0,max_cost_microusd=4000000,token_rate_microusd_per_million=15000000,tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=20000,wall_seconds=60)
  a=DeepSeekComponentAdapter(self.p/'dsprovider',b,model='deepseek-flash',sender=lambda x:None,mock=True,max_wire_input_upper=65536)
  h={k:'Mock-only hypothesis, no mathematical hint' for k in FIELDS};h.update(source_evidence_ids=[rows[0]['evidence_id']],generation_decision='PROPOSE_CORRECTION')
  req=dict(phase='candidate',slot=0,max_tokens=8192,arm='F',source_ids=h['source_evidence_ids'],discovery={'events':rows},specification=json.dumps(h))
  wire=a.preflight(req)
  self.assertEqual(wire['model'],'deepseek-flash');self.assertEqual(wire['thinking'],{'type':'disabled'});self.assertNotIn('provider',wire);self.assertNotIn('reasoning',wire)
  self.assertEqual(wire['response_format'],{'type':'json_object'})
  payload=json.loads(wire['messages'][1]['content']);self.assertNotIn('gold_answer',json.dumps(payload));self.assertNotIn('solution',payload)
  self.assertEqual(a.provider_origin,'DEEPSEEK')
  a.mock=False;a.authorization=None
  with self.assertRaises(PermissionError):a._authorize()
if __name__=='__main__':unittest.main(verbosity=2)
