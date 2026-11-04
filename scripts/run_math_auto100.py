"""Frozen 100-task autonomous mathematical learning test. No hand operators."""
import sys,json,re,hashlib,time,urllib.request,concurrent.futures
from pathlib import Path
import pyarrow.parquet as pq
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.contracts import fingerprint,canonical
from failure_evo.autonomous_generation import DeepSeekCompilerAdapter
from failure_evo.math_learning import MathGPTAdapter,MathLearningPipeline,HYPOTHESIS_SCHEMA,parse_hypothesis,CONTRACT
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.math_operators import MathOperatorRegistry,MathOperatorRunner,FrozenMathLibrary
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.evidence import EvidenceStore
from failure_evo.math_transport import NoGoldSolverChannel
from code_math.no_gold import PublicMathTask,NoGoldPolicy,NoGoldMathController
from code_math.private_math_scoring import extract_answer,normalized
from code_math.discovery_continuation import grade_continuation
OUT=ROOT/'runs/math_auto100_20261031_01';VERSION='math-auto100-tf-v1'
SUBJECTS=['algebra','counting_and_probability','geometry','intermediate_algebra','number_theory','prealgebra','precalculus']
class Adapter(DeepSeekCompilerAdapter):
 protocol=VERSION;hypothesis_schema=HYPOTHESIS_SCHEMA;hypothesis_parser=staticmethod(parse_hypothesis);source_contract=CONTRACT
 def preflight(self,r):
  b=MathGPTAdapter.preflight(self,r)
  messages=b['input'];messages[0]['content']+='\nRequired JSON schema: '+canonical(b['text']['format']['schema'])
  wire=dict(model=self.model,messages=messages,max_tokens=r['max_tokens'],temperature=0,thinking={'type':'disabled'},reasoning_effort='none',stream=False,response_format={'type':'json_object'})
  if len(canonical(wire).encode())+256>self.max_wire_input_upper:raise ValueError('wire bound')
  return wire

def read(p):return json.loads(p.read_text())
def norm(s):return re.sub(r'\s+',' ',s).strip().lower()
def mask(s):return re.sub(r'\d+','N',norm(s))
def collect_public(v,out):
 if isinstance(v,dict):
  for k,x in v.items():
   if k in ('problem','prompt','question') and isinstance(x,str):out.add(norm(x))
   elif isinstance(x,(dict,list)):collect_public(x,out)
 elif isinstance(v,list):
  for x in v:collect_public(x,out)
def freeze():
 if OUT.exists():raise RuntimeError('new run required')
 known=set();paths=[]
 # Public manifests/evidence only. Never inspect sealed confirmation pools.
 for base in [ROOT/'runs',ROOT/'reports']:
  for name in ['tasks.json','source_failures.json','failure_evidence.json','selected_failure_evidence.json']:
   for p in base.glob('*/'+name):
    if p.stat().st_size>10000000:continue
    try:collect_public(read(p),known);paths.append(str(p.relative_to(ROOT)))
    except (ValueError,UnicodeError):pass
 knownmask={mask(x) for x in known};selectedmask=set();chosen={};labels={};funnel=[];rawhash={}
 from difflib import SequenceMatcher
 for sub in SUBJECTS:
  path=ROOT/'runs/hard140_algorithm_20261028_01/private'/(sub+'.parquet');rawhash[sub]=sha(path);rows=pq.read_table(path).to_pylist();chosen[sub]=[]
  for i in sorted(range(len(rows)),key=lambda i:fingerprint(['math-auto100-v1',sub,i])):
   x=rows[i];reason=None;s=x['problem'];m=mask(s)
   if x['level']!='Level 5':continue
   gold=extract_answer(x['solution'])
   if '[asy]' in s or re.search(r'(?i)\b(diagram|figure shown|pictured)\b',s):reason='VISUAL'
   elif len(s.encode())>9000:reason='INPUT_LENGTH'
   elif '\\boxed' not in x['solution'] or normalized(gold)[0]!='rational':reason='NOT_EXACT_RATIONAL_REFERENCE'
   elif norm(s) in known or m in knownmask:reason='RECORDED_EXPOSURE'
   else:
    for other in knownmask|selectedmask:
     if 2*min(len(m),len(other))/(len(m)+len(other))<.90:continue
     sm=SequenceMatcher(None,m,other,autojunk=False)
     if sm.quick_ratio()>=.90 and sm.ratio()>=.90:reason='MASKED_NEAR_DUPLICATE';break
   tid=f'math-auto100-{sub}-{i}';funnel.append({'task_id':tid,'reason':reason or 'SELECTED'})
   if reason:continue
   t=dict(task_id=tid,problem=s);chosen[sub].append(t);selectedmask.add(m);labels[tid]=dict(task_id=tid,gold_answer=gold,problem_sha256=fingerprint(s),subject=sub,row=i,level=x['level'],solution_sha256=fingerprint(x['solution']))
   if len(chosen[sub])==15:break
  if len(chosen[sub])<15:raise RuntimeError('insufficient '+sub)
 tasks=[chosen[s][i] for i in range(15) for s in SUBJECTS][:100]
 roles=dict(Discovery=tasks[:20],Design=tasks[20:30],Gate=tasks[30:40],Test=tasks[40:]);private=[labels[t['task_id']] for t in tasks]
 price=urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing',timeout=30).read();assert b'$0.3' in price and b'$1.2' in price
 files=[Path(__file__).resolve(),ROOT/'scripts/run_math_v3_development.py']+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+list((ROOT/'FlowEvo/src/code_math').glob('*.py'))
 p=dict(version=VERSION,model='deepseek-flash',tasks_total=100,roles={k:len(v) for k,v in roles.items()},selection='Level5, rational reference, text-only, stable hashed subject order/interleaving, no outcomes',raw_hashes=rawhash,roles_hash=fingerprint(roles),private_hash=fingerprint(private),max_calls=404,max_usd=20,budgets='200 solve episodes x $0.09 =18; two generation arms x $1 =2',solver=dict(calls=2,output=4096,input_upper=32768,temperature=0,profile='concise-v1'),generation=dict(arms=['T','F'],one_hypothesis_each=True,max_candidates_each=1,revisions=0,calls_each=2,output=8192,input_upper=65536,source_selection='earliest six distinct final CONFIRMED_WRONG Discovery tasks; no initial-only failure; no future outputs'),admission='existing MathLearningPipeline source+Design usefulness and two refusal controls, then one Gate; useful=at least one correct APPLIED,no wrong APPLIED/noERROR; no replacement',comparison='G/T/F each executes real no-gold workflow on same60 Test records; no matching means native fallback; per-arm independent real calls; rotate arm order',stops=['UNKNOWN/pending request','infrastructure/Worker fault','hash/leakage','hard budget'],normal_outcomes=['no failures','NO_MECHANISM','delivery/static rejection with settled usage','no Design/Gate match','zero reuse'],scope='new manifest-level tasks; limited recorded exposure/near-duplicate audit, not proof of novel competition lineage or pretraining absence; 60 final paired tasks not100 efficacy observations',source_hashes={str(f.relative_to(ROOT)):sha(f) for f in files},worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),authorization='User requests100-task real automatic learning benefit test; bounded new20USD cap, no old quota inheritance')
 save(OUT/'protocol.json',p);save(OUT/'freeze.json',{'sha256':fingerprint(p)});save(OUT/'tasks.json',tasks);save(OUT/'roles.json',roles);save(OUT/'private.json',private);save(OUT/'selection_audit.json',dict(paths=paths,known_public_texts=len(known),funnel=funnel,limitations=p['scope']));(OUT/'pricing.html').write_bytes(price)
 for f in files:
  q=OUT/'frozen_source'/f.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(f.read_bytes())
 print('FROZEN',fingerprint(p),flush=True)
def makebudget(path,run,ph,calls,cost,tools=0):
 return PersistentBudget(path,run_id=run,protocol_hash=ph,max_calls=calls,max_tokens=calls*73728,max_tools=tools,max_cost_microusd=cost,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=tools*20000,tool_milliseconds_upper=20000,wall_seconds=21600)
def health():
 for f in OUT.rglob('budget.jsonl'):
  o=PersistentBudget.__new__(PersistentBudget);o.path=f
  with o._locked() as rows:
   states,_=o._state(rows)
   if any(x['status']!='settled' for x in states.values()):raise RuntimeError('UNRESOLVED '+str(f))
def run():
 p=read(OUT/'protocol.json');ph=fingerprint(p);assert ph==read(OUT/'freeze.json')['sha256'];assert all(sha(ROOT/f)==h for f,h in p['source_hashes'].items())
 roles=read(OUT/'roles.json');private=read(OUT/'private.json');assert fingerprint(roles)==p['roles_hash'] and fingerprint(private)==p['private_hash'];answers={x['task_id']:x for x in private}
 if (OUT/'STARTED.json').exists():raise RuntimeError('consumed run; no resend')
 save(OUT/'STARTED.json',{'at':time.time()});results=[];bundle_events=[];registries={a:MathOperatorRegistry(OUT/a/'registry.jsonl') for a in ['T','F']}
 backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
 def episode(task,arm,seq):
  path=OUT/'episodes'/task['task_id']/arm;b=makebudget(path/'budget.jsonl',OUT.name+':'+task['task_id']+':'+arm,ph,2,90000,tools=2)
  auth=dict(run_id=b.config['run_id'],protocol_hash=ph,model=p['model'],max_cost_microusd=90000,paid_api_authorized=True,channel='math-solver-no-gold-v1');save(path/'authorization.json',auth)
  client=NoGoldSolverChannel(b,path/'requests.jsonl',authorization=auth);lib=FrozenMathLibrary(registries[arm],MathOperatorRunner(backend,b)) if arm in registries else None
  controller=NoGoldMathController(client,path/'controller.jsonl',policy=NoGoldPolicy(delivery_profile='concise-v1',operators_enabled=lib is not None),library=lib)
  locked=controller.solve(PublicMathTask.parse(task),episode_id=b.config['run_id'],sequence=seq)
  gold=answers[task['task_id']]['gold_answer'];assert answers[task['task_id']]['problem_sha256']==fingerprint(task['problem'])
  grade=grade_continuation(locked['final_output'],gold,locked['responses'][-1]['finish_reason']) if locked['responses'] else dict(status='CONFIRMED_CORRECT' if normalized(locked['final_output'])==normalized(gold) else 'CONFIRMED_WRONG',correct=normalized(locked['final_output'])==normalized(gold))
  row=dict(task_id=task['task_id'],arm=arm,locked=locked,grade=grade);save(path/'result.json',row);return row
 try:
  for i,t in enumerate(roles['Discovery']):
   row=episode(t,'Discovery',i);results.append(row);save(OUT/'results.json',results);health();l=row['locked']
   if row['grade']['status']=='CONFIRMED_WRONG':
    e=dict(task=t,sequence=i,available_after_sequence=i,origin='DEEPSEEK',outcome='CONFIRMED_WRONG',correct=False,final_output=l['final_output'],trajectory=[dict(text=r['text'],finish_reason=r['finish_reason'],usage=r['usage']) for r in l['responses']],model_calls=l['model_calls'],tokens=dict(input=l['input_tokens'],output=l['output_tokens']),locked_sha256=l['locked_sha256']);e['event_id']=fingerprint(e);bundle_events.append(e)
   print('DISCOVERY',i+1,row['grade']['status'],flush=True)
  save(OUT/'failures.json',bundle_events);selected=bundle_events[:6];bundle=dict(events=selected,cutoff_sequence=20);save(OUT/'selected_bundle.json',bundle)
  learning=[]
  for arm in ['T','F']:
   if not selected:learning.append(dict(arm=arm,status='NO_CONFIRMED_FAILURE'));continue
   path=OUT/arm;b=makebudget(path/'budget.jsonl',OUT.name+':learn:'+arm,ph,2,1000000,tools=120)
   auth=dict(run_id=b.config['run_id'],protocol_hash=ph,model=p['model'],protocol=VERSION,max_cost_microusd=1000000,paid_api_authorized=True);save(path/'authorization.json',auth)
   ad=Adapter(path/'provider.jsonl',b,model=p['model'],authorization=auth,max_wire_input_upper=65536);compiler=BoundedCompiler(ad,b,path/'compiler.jsonl',p['model'],max_input_upper=65536,max_output_upper=8192)
   pipe=MathLearningPipeline(path/'pipeline',compiler,registries[arm],MathOperatorRunner(backend,b),arm=arm,source_tasks=[PublicMathTask.parse(e['task']) for e in selected],design_tasks=[PublicMathTask.parse(t) for t in roles['Design']],gate_tasks=[PublicMathTask.parse(t) for t in roles['Gate']],private_rows=private)
   try:
    job=pipe.induce(bundle)
    if job is None:record=dict(arm=arm,status='NO_EXECUTABLE_PROPOSAL')
    else:
     review=pipe.candidate(job,0);record=dict(arm=arm,status='SHADOW_DEVELOPMENT_FAILED',artifact=review['artifact'],development_passed=review['development_passed'])
     if review['development_passed']:
      g=pipe.gate(review,after_sequence=39);record.update(status='EXPERIMENTAL' if g['gate_passed'] else 'SHADOW_GATE_FAILED',gate=g)
   except ValueError as e:
    health();record=dict(arm=arm,status='SETTLED_DELIVERY_REJECTED',reason=str(e))
   learning.append(record);save(OUT/'learning_results.json',learning);health();print('LEARNING',arm,record['status'],flush=True)
  save(OUT/'learning_results.json',learning)
  save(OUT/'PRE_TEST_LOCK.json',dict(at=time.time(),registries={arm:sha(OUT/arm/'registry.jsonl') if (OUT/arm/'registry.jsonl').exists() else None for arm in registries},learning_sha256=sha(OUT/'learning_results.json')))
  # Freeze learning first. Three independent arms per task; no target feedback reaches learner.
  for i,t in enumerate(roles['Test']):
   order=['G','T','F'];order=order[i%3:]+order[:i%3]
   with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    futures=[pool.submit(episode,t,arm,40+i) for arm in order]
    got=[];errors=[]
    for f in futures:
     try:got.append(f.result())
     except BaseException as e:errors.append(e)
   results+=got;save(OUT/'results.json',results)
   if errors:raise errors[0]
   health();print('TEST',i+1,[(r['arm'],r['grade']['status'],len(r['locked']['operator_events'])) for r in got],flush=True)
  save(OUT/'COMPLETE.json',dict(status='COMPLETE',unique_tasks=100,final_paired_tasks=60,at=time.time()))
 except BaseException as e:
  save(OUT/'STOP.json',dict(type=type(e).__name__,reason=str(e),no_resend=True,at=time.time()));raise
if __name__=='__main__':(freeze if sys.argv[1]=='freeze' else run)()
