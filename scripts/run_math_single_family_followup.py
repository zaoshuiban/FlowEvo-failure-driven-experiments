"""One disclosed development follow-up; first-failure family, no outcome switching."""
import json,random,time,sys
from pathlib import Path
import run_math_auto100 as b
import run_math_synthetic100 as data
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.contracts import fingerprint,canonical
from failure_evo.math_learning import MathLearningPipeline
from failure_evo.math_operators import MathOperatorRegistry,MathOperatorRunner,FrozenMathLibrary
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.math_transport import NoGoldSolverChannel
from code_math.no_gold import PublicMathTask,NoGoldPolicy,NoGoldMathController
from code_math.discovery_continuation import grade_continuation
from code_math.private_math_scoring import normalized
OUT=ROOT/'runs/math_synthetic_single_family_20261031_01';PARENT=data.OUT;VERSION='synthetic-single-family-followup-v1'
class Adapter(b.Adapter):
 protocol=VERSION
 def preflight(self,r):
  wire=super().preflight(r);payload=json.loads(wire['messages'][1]['content'])
  payload['evidence']['selection']='Frozen chronological source questions, at most six; identical questions in both conditions.'
  wire['messages'][1]['content']=canonical(payload)
  if len(canonical(wire).encode())+256>self.max_wire_input_upper:raise ValueError('wire bound')
  return wire

def load(name):return json.loads((OUT/name).read_text())
def freeze():
 if OUT.exists():raise RuntimeError('new run required')
 failures=b.read(PARENT/'failures.json');labels={x['task_id']:x for x in b.read(PARENT/'private.json')};family=labels[failures[0]['task']['task_id']]['family']
 selected=[e for e in failures if labels[e['task']['task_id']]['family']==family][:6];roles=b.read(PARENT/'roles.json');private=b.read(PARENT/'private.json');seen={fingerprint([x['family'],x['parameters']]) for x in private};rng=random.Random(93120261031);future=[];checks=[]
 others=[f for f in ['expression','digits','walk'] if f!=family]
 for i in range(30):
  f=family if i%5!=4 else others[(i//5)%2]
  while True:
   if f=='expression':
    n=rng.choice([7,8,9]);p=dict(numbers=[rng.randint(2,19) for _ in range(n)],operations=[rng.choice(['+','-','*']) for _ in range(n-1)])
   elif f=='digits':p=dict(digits=sorted(rng.sample(range(10),rng.choice([5,6,7]))),length=rng.choice([3,4]),repetition_allowed=bool(rng.randrange(2)))
   else:p=dict(steps=rng.choice([[-1,1],[-2,1],[-2,-1,1,2],[-1,1,2]]),target=rng.choice([-3,-2,-1,1,2,3]),time=rng.randint(12,20))
   key=fingerprint([f,p])
   if key not in seen:seen.add(key);break
  answer,review={'expression':data.expression,'digits':data.digits,'walk':data.walk}[f](p)
  t=dict(task_id='single-family-future-'+str(i),problem=data.statement(f,p));future.append(t);private.append(dict(task_id=t['task_id'],gold_answer=answer,problem_sha256=fingerprint(t['problem']),family=f,parameters=p));checks.append(dict(task_id=t['task_id'],**review))
 roles=dict(Source=[e['task'] for e in selected],Design=roles['Design'],Gate=roles['Gate'],Test=future)
 files=[Path(__file__).resolve(),ROOT/'scripts/run_math_auto100.py',ROOT/'scripts/run_math_synthetic100.py',ROOT/'scripts/run_math_v3_development.py']+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+list((ROOT/'FlowEvo/src/code_math').glob('*.py'))
 plan=dict(version=VERSION,model='deepseek-flash',reason='Disclosed follow-up after both mixed-family hypotheses declined compilation. No change to parent run.',selection='family of earliest confirmed terminal failure; all eligible same-family failures chronological max6; not by Test success',selected_family=family,source_count=len(selected),future=dict(count=30,primary_family=24,other_family_controls=6,seed=93120261031),roles_hash=fingerprint(roles),private_hash=fingerprint(private),bundle_hash=fingerprint({'events':selected,'cutoff_sequence':20}),parent_hashes={name:sha(PARENT/name) for name in ['protocol.json','roles.json','private.json','failures.json','learning_results.json']},source_hashes={str(p.relative_to(ROOT)):sha(p) for p in files},worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),generation=dict(calls_per_arm=2,candidates_per_arm=1,revisions=0,neutral_selection_metadata=True),solver=dict(calls=2,output=4096,input_upper=32768,temperature=0),max_calls=184,max_usd=11,budget='two generation arms x$1 +90solver episodes x$0.09 =10.10, under11USD',scope='manual family partition plus model-generated code; synthetic parameter generalization; one bounded post-development follow-up; no independent original-task claim',authorization='User requested hand-designed exploratory automatic learning experiments; bounded new follow-up, no parent quota transfer')
 save(OUT/'protocol.json',plan);save(OUT/'freeze.json',{'sha256':fingerprint(plan)});save(OUT/'roles.json',roles);save(OUT/'private.json',private);save(OUT/'selected_bundle.json',{'events':selected,'cutoff_sequence':20});save(OUT/'oracle_acceptance.json',checks)
 for f in files:
  q=OUT/'frozen_source'/f.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(f.read_bytes())
 print('FROZEN',family,len(selected),fingerprint(plan),flush=True)
def run():
 p=load('protocol.json');ph=fingerprint(p);assert ph==load('freeze.json')['sha256'];assert all(sha(ROOT/f)==h for f,h in p['source_hashes'].items());assert all(sha(PARENT/f)==h for f,h in p['parent_hashes'].items())
 if not (PARENT/'COMPLETE.json').exists():raise RuntimeError('wait for parent to complete, no interleaved paid experiments')
 if (OUT/'STARTED.json').exists():raise RuntimeError('consumed run')
 roles=load('roles.json');private=load('private.json');bundle=load('selected_bundle.json');assert fingerprint(roles)==p['roles_hash'] and fingerprint(private)==p['private_hash'] and fingerprint(bundle)==p['bundle_hash'];answers={x['task_id']:x for x in private};save(OUT/'STARTED.json',{'at':time.time()})
 backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER);registries={a:MathOperatorRegistry(OUT/a/'registry.jsonl') for a in ['T','F']};learning=[];results=[]
 def health():
  old=b.OUT
  try:b.OUT=OUT;b.health()
  finally:b.OUT=old
 try:
  for arm in ['T','F']:
   path=OUT/arm;budget=b.makebudget(path/'budget.jsonl',OUT.name+':'+arm,ph,2,1000000,tools=120);auth=dict(run_id=budget.config['run_id'],protocol_hash=ph,model=p['model'],protocol=VERSION,max_cost_microusd=1000000,paid_api_authorized=True);save(path/'authorization.json',auth)
   provider=Adapter(path/'provider.jsonl',budget,model=p['model'],authorization=auth,max_wire_input_upper=65536);compiler=BoundedCompiler(provider,budget,path/'compiler.jsonl',p['model'],max_input_upper=65536,max_output_upper=8192)
   pipe=MathLearningPipeline(path/'pipeline',compiler,registries[arm],MathOperatorRunner(backend,budget),arm=arm,source_tasks=[PublicMathTask.parse(t) for t in roles['Source']],design_tasks=[PublicMathTask.parse(t) for t in roles['Design']],gate_tasks=[PublicMathTask.parse(t) for t in roles['Gate']],private_rows=private)
   try:
    job=pipe.induce(bundle)
    if job is None:record=dict(arm=arm,status='NO_EXECUTABLE_PROPOSAL')
    else:
     review=pipe.candidate(job,0);record=dict(arm=arm,status='SHADOW_DEVELOPMENT_FAILED',artifact=review['artifact'],development_passed=review['development_passed'])
     if review['development_passed']:
      gate=pipe.gate(review,after_sequence=39);record.update(status='EXPERIMENTAL' if gate['gate_passed'] else 'SHADOW_GATE_FAILED',gate=gate)
   except ValueError as e:
    health();record=dict(arm=arm,status='SETTLED_DELIVERY_REJECTED',reason=str(e))
   learning.append(record);save(OUT/'learning_results.json',learning);health();print('LEARNING',arm,record['status'],flush=True)
  save(OUT/'PRE_TEST_LOCK.json',dict(learning_sha256=sha(OUT/'learning_results.json'),registries={a:sha(OUT/a/'registry.jsonl') if (OUT/a/'registry.jsonl').exists() else None for a in registries}))
  # Pre-registered futility condition: no qualified code means no new effect comparison.
  if not any(x['status']=='EXPERIMENTAL' for x in learning):
   save(OUT/'COMPLETE.json',dict(status='NO_ADMITTED_OPERATOR',future_evaluated=0));return
  def episode(t,arm,seq):
   path=OUT/'episodes'/t['task_id']/arm;budget=b.makebudget(path/'budget.jsonl',OUT.name+':'+t['task_id']+':'+arm,ph,2,90000,tools=2);auth=dict(run_id=budget.config['run_id'],protocol_hash=ph,model=p['model'],max_cost_microusd=90000,paid_api_authorized=True,channel='math-solver-no-gold-v1');save(path/'authorization.json',auth)
   client=NoGoldSolverChannel(budget,path/'requests.jsonl',authorization=auth);lib=FrozenMathLibrary(registries[arm],MathOperatorRunner(backend,budget)) if arm in registries else None
   ctl=NoGoldMathController(client,path/'controller.jsonl',policy=NoGoldPolicy(delivery_profile='concise-v1',operators_enabled=lib is not None),library=lib);locked=ctl.solve(PublicMathTask.parse(t),episode_id=budget.config['run_id'],sequence=seq);answer=answers[t['task_id']];assert answer['problem_sha256']==fingerprint(t['problem'])
   grade=grade_continuation(locked['final_output'],answer['gold_answer'],locked['responses'][-1]['finish_reason']) if locked['responses'] else dict(status='CONFIRMED_CORRECT' if normalized(locked['final_output'])==normalized(answer['gold_answer']) else 'CONFIRMED_WRONG',correct=normalized(locked['final_output'])==normalized(answer['gold_answer']))
   row=dict(task_id=t['task_id'],arm=arm,locked=locked,grade=grade);save(path/'result.json',row);return row
  import concurrent.futures
  for i,t in enumerate(roles['Test']):
   order=['G','T','F'];order=order[i%3:]+order[:i%3]
   with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    fs=[pool.submit(episode,t,a,40+i) for a in order];got=[];errors=[]
    for f in fs:
     try:got.append(f.result())
     except BaseException as e:errors.append(e)
   results+=got;save(OUT/'results.json',results)
   if errors:raise errors[0]
   health();print('TEST',i+1,[(r['arm'],r['grade']['status'],len(r['locked']['operator_events'])) for r in got],flush=True)
  save(OUT/'COMPLETE.json',dict(status='COMPLETE',future_evaluated=30))
 except BaseException as e:
  save(OUT/'STOP.json',dict(reason=str(e),type=type(e).__name__,no_resend=True));raise
if __name__=='__main__':(freeze if sys.argv[1]=='freeze' else run)()
