"""Real Linux Worker, explicit human engineering fixtures, zero model API."""
import json,time,sys,tempfile,copy
from pathlib import Path
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.contracts import fingerprint
from failure_evo.semantic_contract import artifact,SplitRunner,FIELDS
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.operator_version_gate import VersionGate
from failure_evo.operator_dual_validation import evaluate
from failure_evo.math_router import StructuredCandidateProbe,UnifiedMathRouter,RoutingPolicy,MathQuality
from failure_evo.math_publication import MathPublicationGate
from failure_evo.evidence import EvidenceStore
from failure_evo.persistent_budget import PersistentBudget
from code_math.no_gold import PublicMathTask,NoGoldMathController,NoGoldPolicy
from code_math.private_math_scoring import PrivateMathScorer
from run_math_manual_lifecycle import MockClient

SEM={'schema':{'type':'object','additionalProperties':False,'required':['requested_quantity','n'],
 'properties':{'requested_quantity':{'type':['string','null']},'n':{'type':['integer','null']}}}}

def packet(task):
 facts=json.loads(task.problem)
 evidence={k:dict(kind='EXPLICIT_AFFIRMATION' if v is not None else 'NOT_STATED',quotes=[task.problem] if v is not None else [],scope='QUOTED_TEXT' if v is not None else 'FULL_PROBLEM',rule=None,from_field=None) for k,v in facts.items()}
 p=dict(task_id=task.task_id,facts=facts,evidence=evidence,review=dict(status='NO_ISSUE_OBSERVED',quotes=[],scope='FULL_PROBLEM'))
 return p,dict(origin='MODEL_PARSE',problem_sha256=fingerprint(task.problem),parsed_sha256=fingerprint(p),response_sha256=fingerprint(p),model_origin='MOCK',usage=dict(prompt_tokens=0,completion_tokens=0,reasoning_tokens=0,model_calls=0))

def problem(n,quantity='sum'):return json.dumps(dict(requested_quantity=quantity,n=n))
def case(i,n,q='sum'):
 return dict(task_id=i,original_id='engineering-original-'+i,problem=problem(n,q),supported=q=='sum',parameters={'n':n},answer=str(sum(range(1,n+1))) if q=='sum' else '0',review_status='INDEPENDENT_VERIFIED',reviewer='host engineering fixture, NOT real original tasks',oracle_sha256=fingerprint('built-in sum range'))
def old_cases(cases):
 return [dict(proposal={'problem':c['problem']},review=dict(status='VERIFIED',record=dict(supported=c['supported'],parameters=c['parameters'],answer=c['answer']))) for c in cases]

class Adapter:
 def __init__(self,p):self.p=p
 def solve(self,a,v):return self.p.split.solve(a,v)
 def run(self,a,t):
  m=self.p.match(a,self.p.prepare(t));r=self.solve(a,m['parameters']) if m['status']=='MATCH' else dict(status='DECLINED',reason=m['reason'])
  return dict(r,match=m,code_sha256=a['code_sha256'])

def main():
 out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'runs/math_unified_router_20261031_01'
 if out.exists():raise RuntimeError('new run directory required')
 out.mkdir(parents=True)
 policy=RoutingPolicy()
 files=sorted((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+sorted((ROOT/'FlowEvo/src/code_math').glob('*.py'))+[Path(__file__).resolve()]
 save(out/'freeze.json',dict(origin='HUMAN_ENGINEERING_FIXTURES',paid_api=False,policy=policy.__dict__,files={str(p):sha(p) for p in files},worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest()))
 for p in files:
  dest=out/'frozen_source'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
 budget=PersistentBudget(out/'budget.jsonl',run_id=out.name,protocol_hash=fingerprint(policy.__dict__),max_calls=0,max_tokens=0,max_tools=300,max_cost_microusd=0,token_rate_microusd_per_million=0,tool_cost_upper_microusd=0,max_tool_milliseconds=1200000,tool_milliseconds_upper=10000,wall_seconds=1800)
 split=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),out/'worker.jsonl',budget=budget)
 probe=StructuredCandidateProbe(split,SEM,packet,parser_identity=dict(origin="MOCK",source=sha(__file__)),allow_mock=True);adapter=Adapter(probe)
 reg=VersionGate(out/'registry.jsonl');client=MockClient();checks={}
 gate=MathPublicationGate(reg,probe,out/'private_gate.jsonl',engineering=True)
 def rejected(name,fn):
  try:fn()
  except (PermissionError,ValueError,RuntimeError):checks[name]=True
  else:checks[name]=False
 def build(name,count,solver_extra=''):
  solver="def solve(parameters):\n    n=parameters['n']\n    return str(n*(n+1)//2)\n"+solver_extra
  matcher="""def match(facts):
    if facts['requested_quantity'] != 'sum':
        return {'status':'DECLINE','parameters':{},'reason':'different objective','assumption_quotes':[],'requested_quantity':'sum'}
    return {'status':'MATCH','parameters':{'n':facts['n']},'reason':'fixture explicit structured premise','assumption_quotes':[],'requested_quantity':'sum'}
"""
  c={k:'engineering fixture only' for k in FIELDS};c.update(operator_id=name,requested_quantity='sum',parameter_schema=json.dumps(dict(type='object',properties={'n':dict(type='integer',minimum=0,maximum=100)},required=['n'],additionalProperties=False)))
  a=artifact(out/name,solver,matcher,c,provenance=dict(origin='MOCK',excluded_task_ids=['source'],semantics_sha256=probe.semantic_sha256,required_facts=['requested_quantity','n']))
  reg.shadow(a)
  dev=[case(name+'d1',1),case(name+'d2',2),case(name+'dn',3,'product')]
  gr=[case(name+'g'+str(i),i+4) for i in range(count)]+[case(name+'gn',4,'product')]
  dr=evaluate(adapter,a,old_cases(dev));reg.record_review(a,dr,role='Development',data_hash=fingerprint(dev),exposed=True)
  reg.freeze_gate([a],data_hash=fingerprint(gr),development_ids=[c['task_id'] for c in dev],gate_ids=[c['task_id'] for c in gr])
  rows=evaluate(adapter,a,old_cases(gr));v=reg.record_review(a,rows,role='Gate',data_hash=fingerprint(gr),exposed=False,paired_generic=True)
  reg.admit(a,v,after_sequence=1)
  rejected(name+'_old_admission_not_publication',lambda:MathQuality(reg).rank(a,probe.sha256,2))
  fg=[case(name+'p'+str(i),i+10) for i in range(count)]+[case(name+'pn',3,'product')]
  fid=gate.freeze(a,fg,development_originals=[x['original_id'] for x in dev+gr],input_rate=0.001,output_rate=0.001,tool_second_rate=0)
  summary=gate.evaluate(fid,client,out/'controller.jsonl')
  checks[name+'_three_gates']=summary['passed']
  gate.publish(summary)
  rejected(name+'_no_gate_replay',lambda:gate.evaluate(fid,client,out/'controller.jsonl'))
  future=['rank','decline','unknown','tie','sealed','harm','after-harm','wrong-objective']
  reg.authorize_trial(a,future_task_ids=future,max_uses=len(future),after_sequence=2)
  return a,summary
 a,sa=build('alpha',2);b,sb=build('beta',3,'# independent engineering variant\n')
 MathQuality(reg).freeze_feedback_roles({k:('SEALED_GOVERNANCE' if k=='sealed' else 'ONLINE_POST_TASK') for k in ['rank','decline','unknown','tie','sealed','harm','after-harm','wrong-objective']})
 router=UnifiedMathRouter(reg,probe,engineering=True)
 ctl=NoGoldMathController(client,out/'controller.jsonl',policy=NoGoldPolicy(operators_enabled=True),library=router)
 native=NoGoldMathController(client,out/'controller.jsonl')
 disabled=NoGoldMathController(client,out/'controller.jsonl',library=router).solve(PublicMathTask('off',problem(5)),episode_id='off',sequence=20)
 checks['default_off_native_two_calls']=disabled['model_calls']==2 and not disabled['operator_events']
 checks['source_blocked']=not reg.eligible(PublicMathTask('source',problem(2)),20)
 rejected('production_mock_block',lambda:UnifiedMathRouter(reg,probe).run(PublicMathTask('rank',problem(5)),sequence=20))
 t=PublicMathTask('rank',problem(5));lock=ctl.solve(t,episode_id='rank',sequence=20)
 checks['quality_not_registration_order']=lock['operator_events'][0]['code_sha256']==b['code_sha256'] and lock['model_calls']==0 and lock['final_output']=='15'
 gl=native.solve(t,episode_id='rank-G',sequence=20)
 scorer=PrivateMathScorer([dict(task_id=t.task_id,problem_sha256=fingerprint(t.problem),gold_answer='15')],out/'controller.jsonl',out/'scores.jsonl')
 grade=scorer.score(t,lock);gg=scorer.score(t,gl)
 q=MathQuality(reg);kw=dict(controller=ctl.events,scorer=scorer.events,original_id='real-fixture-rank',cost=0,generic=gl,generic_verdict=gg,generic_cost=.1)
 receipt=q.record_outcome(b,probe.sha256,lock,grade,**kw)
 checks['future_only_evidence']=q.summary(b,probe.sha256,20)['uses']==0 and q.summary(b,probe.sha256,21)['wins']==1
 checks['idempotent_feedback']=q.record_outcome(b,probe.sha256,lock,grade,**kw)==receipt and q.summary(b,probe.sha256,21)['uses']==1
 rejected('conflicting_feedback',lambda:q.record_outcome(b,probe.sha256,lock,grade,**dict(kw,cost=.2)))
 rejected('route_crash_no_duplicate',lambda:router.run(t,sequence=20))
 dl=ctl.solve(PublicMathTask('decline',problem(5,'product')),episode_id='decline',sequence=21)
 checks['negative_real_fallback']=dl['model_calls']==2 and dl['fallback']
 ul=ctl.solve(PublicMathTask('unknown',problem(5,None)),episode_id='unknown',sequence=22)
 checks['unknown_native_fallback']=ul['model_calls']==2 and ul['fallback']
 # Same ranking and no observed online evidence: tied top candidates abstain.
 c,sc=build('gamma',3,'# third variant\n')
 tl=ctl.solve(PublicMathTask('tie',problem(7)),episode_id='tie',sequence=10)
 checks['quality_tie_abstains']=tl['operator_events'][0]['reason']=='UNRESOLVED_QUALITY_TIE' and tl['model_calls']==2
 # Sealed negative cannot change online ranking; explicit governance can suspend.
 sl=ctl.solve(PublicMathTask('sealed',problem(8)),episode_id='sealed',sequence=30)
 ss=PrivateMathScorer([dict(task_id='sealed',problem_sha256=fingerprint(problem(8)),gold_answer='999')],out/'controller.jsonl',out/'sealed_scores.jsonl')
 sg=ss.score(PublicMathTask('sealed',problem(8)),sl)
 before=q.summary(b,probe.sha256,100)
 sr=q.record_outcome(b,probe.sha256,sl,sg,controller=ctl.events,scorer=ss.events,original_id='sealed-fixture',cost=0,visibility='SEALED_GOVERNANCE')
 rejected('cannot_launder_sealed_as_online',lambda:q.record_outcome(b,probe.sha256,sl,sg,controller=ctl.events,scorer=ss.events,original_id='sealed-fixture',cost=0))
 rejected('cannot_relabel_after_execution',lambda:q.freeze_feedback_roles({'sealed':'ONLINE_POST_TASK'}))
 checks['sealed_not_online_rank']=q.summary(b,probe.sha256,100)==before
 q.governance_suspend(b,sr['id'])
 checks['sealed_explicit_governance_suspends']=b not in reg.eligible(PublicMathTask('harm',problem(8)),40)
 # Negative score here is deliberate host fault injection, not mathematical evidence.
 hl=ctl.solve(PublicMathTask('harm',problem(9)),episode_id='harm',sequence=40)
 hs=PrivateMathScorer([dict(task_id='harm',problem_sha256=fingerprint(problem(9)),gold_answer='999')],out/'controller.jsonl',out/'harm_scores.jsonl')
 hg=hs.score(PublicMathTask('harm',problem(9)),hl)
 q.record_outcome(c,probe.sha256,hl,hg,controller=ctl.events,scorer=hs.events,original_id='harm-fixture',cost=0)
 checks['online_negative_suspends_with_quota']=c not in reg.eligible(PublicMathTask('after-harm',problem(10)),41)
 changed=copy.deepcopy(a);changed['code_sha256']='0'*64
 checks['changed_version_no_quality']=not q.publications(changed,probe.sha256)
 rejected('fake_gate_summary',lambda:gate.publish(dict(sa,quality=dict(sa['quality'],net_correct=999))))
 rejected('role_overlap',lambda:gate.freeze(a,[case('x',3)],development_originals=['engineering-original-x'],input_rate=0,output_rate=0,tool_second_rate=0))
 # Resource bounds are frozen policy: no accidental inheritance of publication.
 r2=UnifiedMathRouter(reg,probe,policy=RoutingPolicy(max_candidates=1),engineering=True)
 checks['changed_policy_requalification']=r2.run(PublicMathTask('after-harm',problem(10)),sequence=45)[0]['reason']=='NO_QUALIFIED_CANDIDATE'
 # An unsupported objective must not reach solve even if a matcher claims MATCH.
 bad_match=Path(a['matcher_path']).read_text().replace("if facts['requested_quantity'] != 'sum':", "if False:")
 bad=artifact(out/'bad-objective',Path(a['solver_path']).read_text(),bad_match,a['contract'],provenance=a['provenance'])
 before_calls=len(split.events.records())
 m=probe.match(bad,probe.prepare(PublicMathTask('objective-check',problem(4,'product'))))
 checks['objective_conflict_no_compute']=m['status']=='UNKNOWN' and len(split.events.records())==before_calls+1
 # Computation PASS cannot grant release when matching always abstains.
 abstain=Path(a['matcher_path']).read_text().replace("if facts['requested_quantity'] != 'sum':", "if True:")
 ab=artifact(out/'always-refuse',Path(a['solver_path']).read_text(),abstain,a['contract'],provenance=a['provenance'])
 fid=gate.freeze(ab,[case('refuse1',4),case('refuse2',5),case('refuseN',3,'product')],development_originals=['source'],input_rate=0,output_rate=0,tool_second_rate=0)
 av=gate.evaluate(fid,client,out/'controller.jsonl')
 checks['computation_not_route_gate']=av['computation_gate'] and not av['routing_gate'] and not av['passed']
 rejected('all_refusal_cannot_publish',lambda:gate.publish(av))
 # Identical correct G and F, no cost saving: no claimed end-to-end benefit.
 class OneClient(MockClient):
  def generate_no_gold(self,**kw):
   r=super().generate_no_gold(**kw);r['text']='The answer is 1';return r
 fid=gate.freeze(a,[case('equal1',1),case('equal2',1),case('equalN',3,'product')],development_originals=['source'],input_rate=0,output_rate=0,tool_second_rate=0)
 eq=gate.evaluate(fid,OneClient(),out/'controller.jsonl')
 checks['compute_and_route_not_e2e']=eq['computation_gate'] and eq['routing_gate'] and not eq['end_to_end_gate'] and not eq['passed']
 # Parser tokens/calls are part of terminal controller totals, including fallback.
 def metered(t):
  p,v=packet(t);v['usage']=dict(prompt_tokens=17,completion_tokens=5,reasoning_tokens=2,model_calls=1);return p,v
 mp=StructuredCandidateProbe(split,SEM,metered,parser_identity=dict(origin='MOCK',source=sha(__file__)),allow_mock=True)
 mr=UnifiedMathRouter(reg,mp,engineering=True)
 ml=NoGoldMathController(client,out/'controller.jsonl',policy=NoGoldPolicy(operators_enabled=True),library=mr).solve(PublicMathTask('wrong-objective',problem(3,'product')),episode_id='metered',sequence=50)
 checks['parser_cost_not_hidden']=ml['model_calls']==3 and ml['input_tokens']==17 and ml['output_tokens']==5 and ml['reasoning_tokens']==2
 
 ft=PublicMathTask('after-harm',problem(10))
 fl=ctl.solve(ft,episode_id='host-feedback',sequence=60)
 fs=PrivateMathScorer([dict(task_id=ft.task_id,problem_sha256=fingerprint(ft.problem),gold_answer='55')],out/'controller.jsonl',out/'host_feedback_scores.jsonl')
 fv=fs.score(ft,fl)
 feedback=router.record_feedback(ft,fl,fv,controller=ctl.events,scorer=fs.events,original_id='fixture-host-feedback')
 checks['post_score_hook_unpaired_not_win']=feedback['correct'] and feedback['generic_correct'] is None and not feedback['cost_verified']
 checks['no_paid_requests']=budget.snapshot()['calls']==0
 checks['worker_budget_accounted']=budget.tool_calls==len(split.events.records())
 save(out/'checks.json',checks);save(out/'budget_snapshot.json',budget.snapshot())
 save(out/'summary.json',dict(status='ENGINEERING_PASS' if all(checks.values()) else 'FAIL',checks=len(checks),passed=sum(checks.values()),worker_calls=len(split.events.records()),worker_seconds=sum(r['payload']['seconds'] for r in split.events.records()),paid_api_calls=0,claim='manual fixtures + Mock parser/solver; no real learned benefit'))
 assert all(checks.values()),checks
 print(json.dumps(json.loads((out/'summary.json').read_text()),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
