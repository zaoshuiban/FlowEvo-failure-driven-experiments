"""Preregistered synthetic capability test. No online promotion, no hand operator.
A disclosed protocol change separates uncertain root cause from testable proposals.
"""
import json,random,time,sys,urllib.request,concurrent.futures
from pathlib import Path
import run_math_auto100 as base
import run_math_synthetic100 as data
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.contracts import fingerprint,canonical
from failure_evo.math_learning import MathLearningPipeline
from failure_evo.math_operators import MathOperatorRegistry,MathOperatorRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.math_transport import NoGoldSolverChannel
from code_math.no_gold import PublicMathTask,NoGoldPolicy,NoGoldMathController
from code_math.discovery_continuation import grade_continuation
from code_math.private_math_scoring import normalized
OUT=ROOT/'runs/math_synthetic_candidate_probe_20261031_01'
PARENT=ROOT/'runs/math_synthetic_single_family_20261031_01'
VERSION='testable-unverified-proposal-v1'
CLARIFICATION='''A cause may remain uncertain while a computational candidate is testable.
PROPOSE means only that you can describe a concrete deterministic computation worth independent testing, NOT that a root cause or transfer has been proved.
HYPOTHESIS_ONLY means that no sufficiently concrete executable candidate can yet be specified.
NO_MECHANISM is also valid. Do not force a proposal. No candidate is verified by its author.
These decision meanings apply equally with or without observed failures. Do not ask for gold answers.'''
class Adapter(base.Adapter):
 protocol=VERSION
 def preflight(self,r):
  w=super().preflight(r);p=json.loads(w['messages'][1]['content'])
  p['evidence']['selection']='Frozen source questions in chronological order; identical questions in both conditions.'
  if r['phase']=='induction':w['messages'][0]['content']+='\n'+CLARIFICATION
  w['messages'][1]['content']=canonical(p)
  if len(canonical(w).encode())+256>self.max_wire_input_upper:raise ValueError('wire bound')
  return w

def load(n):return json.loads((OUT/n).read_text())
def freeze():
 if OUT.exists():raise RuntimeError('new run required')
 bundle=base.read(PARENT/'selected_bundle.json');assert len(bundle['events'])==5
 # Source selection is inherited from the earlier frozen first-failure-family rule.
 old=base.read(PARENT/'private.json');seen={fingerprint(x['parameters']) for x in old if x['family']=='digits'}
 rng=random.Random(43120261031);tasks=[];private=[];oracles=[]
 for i in range(100):
  while True:
   p=dict(digits=sorted(rng.sample(range(10),rng.choice([5,6,7]))),length=3+i%2,repetition_allowed=bool((i//2)%2))
   if fingerprint(p) not in seen:seen.add(fingerprint(p));break
  answer,review=data.digits(p);t=dict(task_id=f'candidate-probe-{i:03d}',problem=data.statement('digits',p))
  tasks.append(t);private.append(dict(task_id=t['task_id'],problem_sha256=fingerprint(t['problem']),gold_answer=answer,parameters=p));oracles.append(dict(task_id=t['task_id'],**review))
 roles=dict(Source=[e['task'] for e in bundle['events']],Design=tasks[:20],Gate=tasks[20:40],Test=tasks[40:])
 private += [x for x in old if x['task_id'] in {e['task']['task_id'] for e in bundle['events']}]
 order=[dict(pair=i,arm=a) for i in range(3) for a in (['T','F'] if i%2==0 else ['F','T'])]
 files=[Path(__file__).resolve(),ROOT/'scripts/run_math_auto100.py',ROOT/'scripts/run_math_synthetic100.py',ROOT/'scripts/run_math_v3_development.py']+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+list((ROOT/'FlowEvo/src/code_math').glob('*.py'))
 p=dict(version=VERSION,model='deepseek-flash',model_version='DeepSeek-V4.1-Flash-1017',seed=43120261031,roles={k:len(v) for k,v in roles.items()},roles_hash=fingerprint(roles),private_hash=fingerprint(private),bundle_hash=fingerprint(bundle),parent_bundle_hash=sha(PARENT/'selected_bundle.json'),order=order,max_requests=132,max_usd=12,allocations='six learning jobs x1USD +60native episodes x0.09USD =11.40USD; no budget transfer',generation='one hypothesis then at most one source per paired arm; no revision, no resampling; same decision semantics',clarification=CLARIFICATION,qualification='all source APPLIED correct; Design and Gate >=80% APPLIED correct, no wrong/ERROR, refusal controls pass; no online registry admission',solver=dict(calls=2,output_tokens=4096,profile='concise-v1',temperature=0),evaluation='60 held-out parameter instances; all frozen candidates inspected, only qualified arms enter primary capability-plus-shared-fallback comparison; same cached Generic fallback, never gold-triggered rescue',primary='F versus T within each of3 independent generation pairs; G is reference. A tie does not show incremental failure value.',futility='no qualified T or F after all6 jobs => no new Generic Test requests; normal result',scope='human-designed single-family synthetic parameter distribution, not different original problems; sources already exposed development evidence;3generation pairs not180independent test questions',price=dict(input_cache_miss_per_million=.3,input_cache_hit_per_million=.006,output_per_million=1.2,offpeak_multiplier=.5),worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),source_hashes={str(f.relative_to(ROOT)):sha(f) for f in files},authorization='User requested another hand-designed real learning experiment; bounded12USD newRun, no historical budget transfer')
 save(OUT/'protocol.json',p);save(OUT/'freeze.json',{'sha256':fingerprint(p)});save(OUT/'roles.json',roles);save(OUT/'private.json',private);save(OUT/'bundle.json',bundle);save(OUT/'oracle_acceptance.json',oracles)
 (OUT/'pricing.html').write_bytes(urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing',timeout=30).read())
 for f in files:
  dest=OUT/'frozen_source'/f.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes())
 print('FROZEN',fingerprint(p),flush=True)

def run():
 p=load('protocol.json');ph=fingerprint(p);assert ph==load('freeze.json')['sha256']
 assert all(sha(ROOT/k)==v for k,v in p['source_hashes'].items())
 assert sha(PARENT/'selected_bundle.json')==p['parent_bundle_hash']
 roles=load('roles.json');private=load('private.json');bundle=load('bundle.json')
 assert fingerprint(roles)==p['roles_hash'] and fingerprint(private)==p['private_hash'] and fingerprint(bundle)==p['bundle_hash']
 if (OUT/'STARTED.json').exists():raise RuntimeError('consumed run; do not resend')
 save(OUT/'STARTED.json',dict(at=time.time()));answers={x['task_id']:x for x in private};backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
 learning=[];pipes={};reviews={};budgets={}
 def health():
  prev=base.OUT
  try:base.OUT=OUT;base.health()
  finally:base.OUT=prev
 def qualifies(rows,source=False):
  return bool(rows) and sum(r['correct'] for r in rows)>=(len(rows) if source else .8*len(rows)) and not any(r['status']=='ERROR' or r['status']=='APPLIED' and not r['correct'] for r in rows)
 try:
  for spec in p['order']:
   arm=spec['arm'];name=f"{spec['pair']}-{arm}";path=OUT/name
   budget=base.makebudget(path/'budget.jsonl',OUT.name+':'+name,ph,2,1000000,tools=150);budgets[name]=budget
   auth=dict(run_id=budget.config['run_id'],protocol_hash=ph,model=p['model'],protocol=VERSION,max_cost_microusd=1000000,paid_api_authorized=True);save(path/'authorization.json',auth)
   adapter=Adapter(path/'provider.jsonl',budget,model=p['model'],authorization=auth,max_wire_input_upper=65536)
   compiler=BoundedCompiler(adapter,budget,path/'compiler.jsonl',p['model'],max_input_upper=65536,max_output_upper=8192)
   registry=MathOperatorRegistry(path/'registry.jsonl');runner=MathOperatorRunner(backend,budget)
   pipe=MathLearningPipeline(path/'pipeline',compiler,registry,runner,arm=arm,source_tasks=[PublicMathTask.parse(t) for t in roles['Source']],design_tasks=[PublicMathTask.parse(t) for t in roles['Design']],gate_tasks=[PublicMathTask.parse(t) for t in roles['Gate']],private_rows=private);pipes[name]=pipe
   record=dict(name=name,**spec,status='NO_PROPOSAL',qualified=False)
   try:
    job=pipe.induce(bundle)
    if job is not None:
     rv=pipe.candidate(job,0);reviews[name]=rv;source=[x for x in rv['diagnostics'] if x['role']=='Source'];design=[x for x in rv['diagnostics'] if x['role']=='Design' and x.get('reason')!='ENGINEERING_REFUSAL_CONTROL']
     good=rv['development_passed'] and qualifies(source,True) and qualifies(design)
     record.update(status='DEVELOPMENT_PASSED' if good else 'SHADOW_DEVELOPMENT_FAILED',artifact=rv['artifact'],source_correct=sum(x['correct'] for x in source),design_correct=sum(x['correct'] for x in design),development_passed=good)
   except ValueError as e:
    health();record.update(status='SETTLED_DELIVERY_REJECTED',reason=str(e))
   learning.append(record);save(OUT/'learning.json',learning);health();print('LEARNING',name,record['status'],flush=True)
  save(OUT/'CODE_LOCK.json',dict(learning_sha256=sha(OUT/'learning.json'),artifacts={x['name']:x['artifact']['code_sha256'] for x in learning if 'artifact' in x}))
  for r in learning:
   if r.get('development_passed'):
    rows=pipes[r['name']].evaluate(r['artifact'],'Gate');save(OUT/r['name']/'gate.json',rows);r['qualified']=qualifies(rows);r['status']='OFFLINE_GATE_PASSED' if r['qualified'] else 'SHADOW_GATE_FAILED'
   print('GATE',r['name'],r['status'],flush=True)
  save(OUT/'qualification.json',learning);save(OUT/'PRE_TEST_LOCK.json',dict(qualification_sha256=sha(OUT/'qualification.json')))
  if not any(r['qualified'] for r in learning):
   save(OUT/'COMPLETE.json',dict(status='NO_QUALIFIED_CANDIDATE',test_tasks_evaluated=0));return
  # No reuse permissions are granted. This is offline capability and paired replay.
  def native(t,i):
   path=OUT/'G'/t['task_id'];budget=base.makebudget(path/'budget.jsonl',OUT.name+':G:'+t['task_id'],ph,2,90000)
   auth=dict(run_id=budget.config['run_id'],protocol_hash=ph,model=p['model'],max_cost_microusd=90000,paid_api_authorized=True,channel='math-solver-no-gold-v1');save(path/'authorization.json',auth)
   client=NoGoldSolverChannel(budget,path/'requests.jsonl',authorization=auth)
   lock=NoGoldMathController(client,path/'controller.jsonl',policy=NoGoldPolicy(delivery_profile='concise-v1')).solve(PublicMathTask.parse(t),episode_id=budget.config['run_id'],sequence=40+i)
   grade=grade_continuation(lock['final_output'],answers[t['task_id']]['gold_answer'],lock['responses'][-1]['finish_reason']);row=dict(task_id=t['task_id'],locked=lock,grade=grade);save(path/'result.json',row);return row
  results=[]
  for start in range(0,60,3):
   batch=roles['Test'][start:start+3]
   with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    fs=[pool.submit(native,t,start+j) for j,t in enumerate(batch)];gs=[];errors=[]
    for f in fs:
     try:gs.append(f.result())
     except BaseException as e:errors.append(e)
   if errors:raise errors[0]
   for t,g in zip(batch,gs):
    outputs=[]
    for r in learning:
     op=None
     if 'artifact' in r and reviews[r['name']]['static']['passed']:
      op=pipes[r['name']].runner.run(r['artifact'],PublicMathTask.parse(t))
     used=bool(r['qualified'] and op and op['status']=='APPLIED')
     good=normalized(op['answer'])==normalized(answers[t['task_id']]['gold_answer']) if used else g['grade']['status']=='CONFIRMED_CORRECT'
     outputs.append(dict(name=r['name'],qualified=r['qualified'],raw_operator=op,used=used,primary_correct=good,fallback=not used))
    results.append(dict(task_id=t['task_id'],generic=g,candidates=outputs))
   save(OUT/'results.json',results);health();print('TEST',len(results),'G_correct',sum(x['generic']['grade']['status']=='CONFIRMED_CORRECT' for x in results),flush=True)
  save(OUT/'COMPLETE.json',dict(status='COMPLETE_OFFLINE_CAPABILITY',test_tasks_evaluated=60,online_operator_uses=0))
 except BaseException as e:
  save(OUT/'STOP.json',dict(type=type(e).__name__,reason=str(e),no_resend=True));raise
if __name__=='__main__':(freeze if sys.argv[1]=='freeze' else run)()
