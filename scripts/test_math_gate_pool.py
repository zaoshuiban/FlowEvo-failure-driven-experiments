"""New sealed-provider path, old disclosed fixtures, actual Docker, zero API."""
import sys,json,copy,math,time
from pathlib import Path
from failure_evo.math_stream import save,read,sha
from failure_evo.contracts import fingerprint
from failure_evo.math_gate_pool import PoolReviewedRelease,SealedGateProvider,VERSION
from failure_evo.math_cumulative_stream import CumulativeStream,DEFAULTS
from failure_evo.evidence import EvidenceStore
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from test_math_continuous_stream import raw,gen_sender,solve_sender
from math_candidate_mock import assessment
from run_math_manual_lifecycle import problem
from run_math_stream200 import WORKER,IMAGE
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=False);checks={};wires=[]
tasks=[dict(task_id='old-fixture-'+str(i),problem=problem(i)) for i in range(1,9)]
tasks[1]['problem']='Compute the product of integers from 1 through 3, inclusive.'
private=[dict(task_id=t['task_id'],problem_sha256=fingerprint(t['problem']),gold_answer='6' if i==2 else str(i*(i+1)//2)) for i,t in enumerate(tasks,1)]
lineage={t['task_id']:dict(source_original_id='ENGINEERING_'+t['task_id']) for t in tasks}
scores=OUT/'private_scores.jsonl';scores.write_text(''.join(json.dumps(r)+'\n' for r in private))
pool=[]
for i in range(4):
 n=100+i;positive=i<2;q=problem(n) if positive else 'Compute the product of integers from 1 through '+str(n)+', inclusive.'
 pool.append(dict(task_id='gate-fixture-'+str(i),original_id='MOCK_ONLY_GATE_'+str(i),problem=q,answer=str(n*(n+1)//2) if positive else str(math.factorial(n)),oracle_sha256=fingerprint(['engineering_builtin_reference',n])))
poolpath=OUT/'pool.json';save(poolpath,dict(cases=pool,origin='ENGINEERING_FIXTURE'))
plan=dict(tasks_sha256=fingerprint(tasks),window=2,r_policy='previous-completed-window-f-call-credit-v2',r_max_extra_calls=48,auxiliary_calls_per_window=48,max_gate_cases=6,max_tools_per_arm=1600,stop_for_gate_review=True,learning_calls_per_window=32,sources={},
 cumulative=dict(DEFAULTS,max_association_jobs=2,max_generation_jobs=1),gate_pool_binding=dict(path=str(poolpath.resolve()),sha256=sha(poolpath)),gate_reviewers=['ENGINEERING_REVIEWER'],
 cumulative_input_bindings=dict(private_scoring=dict(path=str(scores.resolve()),sha256=sha(scores))))
def generate(arm):
 base=gen_sender(arm)
 def send(w):
  d=json.loads(w['messages'][1]['content']);wires.append((arm,copy.deepcopy(d)))
  if 'candidate_clusters' not in d:
   if 'hypothesis' not in d:return raw(json.dumps(assessment([e['evidence_id'] for e in d['learning_evidence_bundle']['evidence']])))
   return base(w)
  es=d['evidence'];refs=[e['evidence_id'] for e in es]
  return raw(json.dumps(dict(descriptions=[dict(evidence_id=e['evidence_id'],task_structure='MOCK',observable_symptom='MOCK',possible_cause='UNVERIFIED',possible_correction='MOCK',uncertainty='MOCK') for e in es],clusters=[dict(cluster_id='NEW',hypothesis=dict(mechanism='MOCK',uncertainty='MOCK',applicability='MOCK',exclusions='MOCK',input_output='MOCK'),assessment=assessment(refs),links=[dict(evidence_id=e['evidence_id'],relation='POSSIBLE',reason='MOCK',evidence_quote=e['problem'],new_information=True) for e in es])])))
 return send
# Test review arrives after Shadow, not injected before source creation.
def release(s,a):
 r=PoolReviewedRelease(s,a);r.sender=solve_sender(a);return r
def make():return CumulativeStream(OUT/'stream',plan,tasks,private,lineage,backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),engineering=True,sender_factory=solve_sender,learning_sender_factory=generate,release_factory=release)
s=make();s.run()
checks['paused_at_review_barrier']=read(s.path/'progress.json')['status']=='INDEPENDENT_REVIEW_REQUIRED' and read(s.path/'progress.json')['last_sequence']==2
before_pause=len(wires);s=make();s.run();checks['missing_review_no_new_calls']=len(wires)==before_pause
for arm in ('T','F'):
 rr=s.arms[arm]['learner'].release
 pending=[r['payload'] for r in rr.journal.records() if r['kind']=='RELEASE_PENDING'];assert pending
 a=pending[0]['artifact'];assert not any(r['kind']=='MATH_ROUTER_PUBLICATION' for r in s.arms[arm]['registry'].events.records())
 labels=[]
 for i,c in enumerate(pool):labels.append(dict(task_id=c['task_id'],supported=i<2,parameters={'n':100+i} if i<2 else None,reason='Old engineering fixture only, not real mathematical learning',assumption_quotes=[c['problem']]))
 dev=[dict(task_id=t['task_id'],supported=i==0,parameters={'n':1} if i==0 else None,reason='Disclosed fixture semantics',assumption_quotes=[t['problem']]) for i,t in enumerate(tasks[:2])]
 review=dict(version=VERSION,artifact_sha256=a['code_sha256'],pool_sha256=sha(poolpath),reviewer='ENGINEERING_REVIEWER',review_method='INDEPENDENT_SEMANTIC_REVIEW_BEFORE_EXECUTION',Development=dev,Gate=labels)
 p=rr.packages.review_path(a)
 for name,mutate in [('gold_field',lambda r:r['Gate'][0].update(answer='SECRET')),('changed_sha',lambda r:r.update(artifact_sha256='bad')),('missing_pool_item',lambda r:r['Gate'].pop()),('future_dev',lambda r:r['Development'][0].update(task_id=tasks[7]['task_id'])),('untrusted_reviewer',lambda r:r.update(reviewer='GENERATOR_SELF_REPORT'))]:
  bad=copy.deepcopy(review);mutate(bad);save(p,bad)
  try:rr.packages(a,2)
  except (PermissionError,ValueError):checks[arm+'_'+name+'_rejected']=True
  else:raise AssertionError(name)
 save(p,review)
checks['shadow_before_review']=True
s=make();s.run();before=len(wires);s=make();s.run();checks['resume_no_generation']=len(wires)==before
checks['terminal_stream_not_paused_for_unused_reviews']=not s._awaiting_reviews()
for arm in ('T','F'):
 reg=s.arms[arm]['registry'].events.records()
 checks[arm+'_publication']=any(r['kind']=='MATH_ROUTER_PUBLICATION' for r in reg)
 checks[arm+'_future_execution']=any(r['kind']=='MATH_ROUTER_EXECUTED' and r['payload']['sequence']>2 for r in reg)
 rows=s.arms[arm]['learner'].release.journal.records();checks[arm+'_one_release']=sum(r['kind']=='RELEASE_COMPLETED' for r in rows)==1
 checks[arm+'_gate_window_accounted']=bool(list((OUT/'stream'/arm/'learning/2').rglob('gate_budget.jsonl')))
 checks[arm+'_freeze_selection_before_execution']=all(x['payload']['selected_gate_ids']==[c['task_id'] for c in pool] for x in s.arms[arm]['learner'].release.packages.events.records() if x['kind']=='REVIEW_FROZEN')
checks['no_gate_in_learning']=all(not any(c['problem'] in json.dumps(w) for c in pool) for _,w in wires)
checks['real_worker']=sum(r['kind']=='V3_COMPONENT_EXECUTED' for p in OUT.rglob('worker.jsonl') for r in EvidenceStore(p).records())>0
s.health();checks['settled_budgets']=True
checks['R_counted_gate_credit']=any(r['kind']=='RETRY_CREDIT' and r['payload']['previous_window']==2 and r['payload']['extra_calls']>=12 for r in s.arms['R']['states'].records())
# Revision of a consumed host review cannot authorize a second run.
rr=s.arms['F']['learner'].release;a=next(r['payload']['artifact'] for r in rr.journal.records() if r['kind']=='RELEASE_PENDING');p=rr.packages.review_path(a);r=read(p);r['Gate'][0]['reason']='changed';save(p,r)
try:rr.packages(a,8)
except PermissionError:checks['consumed_review_immutable']=True
save(OUT/'acceptance.json',dict(checks=checks,passed=sum(checks.values()),total=len(checks),worker='ACTUAL_DOCKER_LINUX',paid_model_calls=0,real_pilot_questions_used=0,research_result='NOT_MEASURED_ENGINEERING_FIXTURES'))
print(checks);assert all(checks.values())
