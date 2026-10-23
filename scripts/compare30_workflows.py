"""Frozen 30-task developmental comparison; generated programs execute only in Docker."""
import argparse, asyncio, hashlib, importlib.util, json, math, os, re, shutil, sys, tempfile, time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[1]
AFLOW=Path('/Users/majiatong/lab/AFlow')
BASE=ROOT/'experiments/flowevo_taco_lcb_20261019'
RUN=ROOT/'runs/s13_compare30_20261022_01'
WORKER=BASE/'repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
ACCEPTANCE=ROOT/'runs/s12c_functional_20261021_01/worker_acceptance.json'
IMAGE='sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8'
sys.path[:0]=[str(ROOT/'FlowEvo/src'),str(AFLOW)]
from failure_evo.contracts import Fingerprint, fingerprint, canonical, PublicTaskView
from failure_evo.runtime import Budget, BudgetExhausted
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.checkpoint_evaluator import CheckpointEvaluator
from failure_evo.native_adapter import NativeBenchmarkSession, prompt_for
from failure_evo.failure_events import FailureEvidenceStore, structural_status
from failure_evo.failure_registry import FailureOperatorRegistry, FailureOperator, OperatorSnapshot
from failure_evo.plugin import FailureLearningPlugin
from failure_evo.model_api import configured_api_key, DeepSeekGenerator
from code_math.runner import CodeSkillLibrary, extract_code
from core.schemas import CodeTaskInstance
import scripts.d0_aflow_b_adapter as af

def read(p):return json.loads(Path(p).read_text())
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rank(x):return hashlib.sha256(('compare30-20261022|'+x).encode()).hexdigest()
def loadmod(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
LEGAL=loadmod('compare30_legal',BASE/'e3_s1_20261020/code/legal_suite.py')
OLD=loadmod('compare30_old',BASE/'trusted_rgf_20261020/code/suite.py')
def accepts(tid,c,out):
 if c.get('comparison')=='prior':return OLD.accepts(tid,c['prior_case'],out)
 return (LEGAL if c['scorer']=='s1' else OLD).accepts(tid,c,out)
def budget_config(calls=540,tools=12000):
 return dict(max_calls=calls,max_tokens=calls*36864,max_tools=tools,max_cost_microusd=24000000 if calls else 0,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=tools*20000,tool_milliseconds_upper=20000,wall_seconds=14400)
def setup():
 (RUN/'tmp').mkdir(exist_ok=True,parents=True)
 os.environ.update(DOCKER_CONFIG=str(ROOT/'runs/s12c_functional_20261021_01/docker_public'),DOCKER_HOST='unix:///Users/majiatong/.colima/default/docker.sock',TMPDIR=str(RUN/'tmp'))
 tempfile.tempdir=str(RUN/'tmp')
 af.P=AFLOW/'results/experiment_d0_aflow_b_stage0_20261019_v1';af.F=af.P/'frozen_official/results'

def prepare():
 if (RUN/'protocol.json').exists():raise FileExistsError('already frozen')
 pool={}
 for label,path in [('trusted',BASE/'trusted_rgf_20261020/suite_frozen.json'),('s1',BASE/'e3_s1_20261020/public_suite.json')]:
  for tid,cases in read(path)['cases'].items():pool[tid]=[dict(c,scorer=label) for c in cases]
 tasks={t:read(ROOT/'datasets/extracted/data/tasks'/(t+'.json')) for t in pool}
 allowed=[t for t,d in tasks.items() if not d['function_name'] and t not in ('taco_0445','lcb_atcoder_abc301_f')]
 chosen=[t for t in allowed if t.startswith('lcb_')]
 for diff,n in [('EASY',5),('MEDIUM',5),('MEDIUM_HARD',5),('HARD',5),('VERY_HARD',4)]:
  chosen+=sorted([t for t in allowed if t.startswith('taco_') and tasks[t]['difficulty']==diff],key=rank)[:n]
 assert len(chosen)==30
 chosen.sort(key=rank)
 s1={r['task_id']:r for r in read(BASE/'e3_s1_20261020/scoring_validation.json')['rows']}
 trusted={r['task_id']:r for r in read(BASE/'trusted_rgf_20261020/trusted_tasks.json')}
 rows=[]
 for tid in chosen:
  task=tasks[tid];unique={c['input']:c for c in pool[tid]};cases=sorted(unique.values(),key=lambda c:rank(tid+'|'+c['input']))
  assert len(cases)>=6
  if tid in s1:
   src=s1[tid]['positive_consistency_witness']['source_path'];ref=(BASE/'e3_s1_20261020'/src).resolve()
   if src.startswith('/opt/'):ref=BASE/src.split('/flowevo-benchmark-20261019/')[1]
  else:
   r=trusted[tid];ref=BASE/f"e3_s0_20261020/raw/runs/{task['dataset']}_{task['difficulty']}/{tid}/{r['positive_historical_stage']}.py"
   assert sha(ref)==r['positive_program_sha256']
  assert ref.is_file(),str(ref)
  public=PublicTaskView.project(task).to_dict()
  # Additional legal public checks are equal across arms; no final-audit input enters this view.
  shown=[]
  for c in cases[:3]:
   kind=c.get('prior_case',c)['comparison']
   shown.append(dict(input=c['input'],expected=c['expected'],comparison=kind))
  public['prompt']+='\n\nAdditional public checks (statement-derived; nonunique outputs use the statement validity rule):\n'+json.dumps(shown,ensure_ascii=False)
  rows.append(dict(task_id=tid,dataset=task['dataset'],difficulty=task['difficulty'],task_sha256=sha(ROOT/'datasets/extracted/data/tasks'/(tid+'.json')),task_public=public,public_cases=cases[:3],audit_cases=cases[3:27],reference_path=str(ref),reference_sha256=sha(ref),prior_development_exposure=True))
 write(RUN/'tasks.json',rows)
 registry_paths=[ROOT/'runs'/r/f for r,f in [('s12i_capacity_safe_ast_20261022_01','registry.jsonl'),('s12j_capacity_scope_v2_20261022_01','registry.jsonl'),('s12j_capacity_scope_v2_revision_20261022_01','registry.jsonl'),('s12b3_revision_20261021_01','shadow_registry.jsonl')]]
 inventory=[]
 for i,p in enumerate(registry_paths):
  if not p.exists():continue
  dest=RUN/'registries'/f'{i}.jsonl';dest.parent.mkdir(exist_ok=True);shutil.copyfile(p,dest)
  reg=FailureOperatorRegistry(dest,FailureEvidenceStore(RUN/'inventory_evidence.jsonl'))
  for r in reg.events.records():
   if r['kind']=='SHADOW_REGISTERED':
    card=FailureOperator.from_dict(r['payload']['card']);state=reg.state(card)
    inventory.append(dict(registry=str(dest),source_registry=str(p),operator_id=card.operator_id,version=card.version,artifact_sha256=card.artifact_sha256,permission=state['permission'],generation=state['generation']))
 assert inventory and all(x['permission'] in ('shadow','suspended') for x in inventory)
 write(RUN/'operator_inventory.json',inventory)
 files=[Path(__file__),WORKER,ACCEPTANCE,RUN/'tasks.json',RUN/'operator_inventory.json',BASE/'e3_s1_20261020/code/legal_suite.py',BASE/'trusted_rgf_20261020/code/suite.py',AFLOW/'scripts/d0_aflow_b_adapter.py']
 files+=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[ROOT/'FlowEvo/src/code_math/runner.py']+list(af.F.rglob('*.py'))+list((RUN/'registries').glob('*.jsonl'))
 p=dict(run_id=RUN.name,arms=['FlowEvo','AFlow','FailureLearning'],selection='audited developmental pool, deterministic SHA256 order; 24 TACO stratified 5/5/5/5/4 and 6 LCB; exclude capacity discovery abc301_f and ambiguous taco_0445; no sampling by new outcomes',repeats=1,model='deepseek-flash',provider_version_quote='DeepSeek-V4.1-Flash-1017',quote=read(ROOT/'runs/s12j_capacity_scope_v2_20261022_01/protocol.json')['quote'],max_input_token_upper=32768,max_output_tokens=4096,thinking='disabled',api_budget=budget_config(),acceptance_budget=budget_config(0,2000),per_branch=dict(max_calls=8,max_tokens=294912,wall_seconds=600,public_seconds=120),flow_native_stages=5,aflow_max_calls=8,authorization_basis='User requested 30-task experiment and explicitly selected three arms; new bounded run, no prior balance',generation_calls=0,permission_changes=0,score='all frozen offline audit cases pass; not official hidden-test accuracy; formerly exposed development tasks',aflow='official MBPP round14 graph adapted to stdin/stdout TACO/LCB, frozen operator control flow and new shared sandbox/transport',failure_learning='current registry and evidence hooks enabled; no eligible operators, compile budget zero; not a cold-start learning efficacy experiment',native='public-feedback-adapted FlowEvo; success libraries separate per arm and dataset/difficulty',final_selection='FlowEvo selected public-pass else last candidate; AFlow only official final returned source; no audit-based selection',pricing_local_tools='monetary cost unknown; tool counts and time recorded separately',frozen_files={str(f):sha(f) for f in sorted(set(files))})
 p['protocol_hash']=fingerprint(p);write(RUN/'protocol.json',p)
 print('FROZEN',len(rows),Counter((r['dataset'],r['difficulty']) for r in rows),len(inventory),flush=True)

def verify():
 p=read(RUN/'protocol.json');assert p['protocol_hash']==fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})
 for f,h in p['frozen_files'].items():assert sha(f)==h,f
 return p

class Judge:
 def __init__(self,budget):self.ev=CheckpointEvaluator(ROOT,budget,image=IMAGE,worker_script=WORKER,acceptance_path=ACCEPTANCE)
 def run(self,tid,code,cases):
  start=time.monotonic();obs=[]
  if structural_status(code)!='STRUCTURAL_PASS':return dict(passed=False,status='COMPILE_ERROR' if code.strip() else 'NO_COMPLETE_CODE',tests_run=0,tests_passed=0,cases=[],seconds=0)
  with tempfile.TemporaryDirectory(prefix='compare30-') as tmp:
   src=Path(tmp)/'candidate.py';src.write_text(code)
   with self.ev.factory(src) as worker:
    raw=self.ev._charged('compile',lambda:worker.call(dict(mode='compile_stdio',timeout=5)))
    if raw.get('status')=='OK':
     for c in cases:
      raw=self.ev._charged('program-test',lambda:worker.call(dict(mode='stdio',input=c['input'],timeout=5)))
      if raw.get('status') in ('EVALUATOR_ERROR','WORKER_ERROR'):raise RuntimeError('isolated worker failure: '+str(raw))
      good=raw.get('status')=='OK' and accepts(tid,c,raw.get('output',''))
      obs.append(dict(input=c['input'],expected=c['expected'],actual=raw.get('output',''),exception_class=raw.get('exception_class',raw.get('error')),worker_status=raw.get('status'),correct=bool(good),visibility='public',legal_verified=True))
      if raw.get('origin')=='host_deadline':break
  good=len(obs)==len(cases) and all(c['correct'] for c in obs)
  status='PUBLIC_PASS' if good else ('WRONG_ANSWER' if obs and all(c['worker_status']=='OK' for c in obs) else 'RUNTIME_ERROR')
  return dict(passed=good,status=status,tests_run=len(obs),tests_passed=sum(c['correct'] for c in obs),cases=obs,seconds=time.monotonic()-start,visibility='public')

def acceptance():
 p=verify();budget=PersistentBudget(RUN/'acceptance_budget.jsonl',run_id=RUN.name+'-acceptance',protocol_hash=p['protocol_hash'],**p['acceptance_budget']);judge=Judge(budget);rows=[]
 for t in read(RUN/'tasks.json'):
  assert sha(t['reference_path'])==t['reference_sha256']
  good=judge.run(t['task_id'],Path(t['reference_path']).read_text(),t['public_cases']+t['audit_cases'])
  bad=judge.run(t['task_id'],"print('INVALID_COMPARISON_FIXTURE')",t['public_cases'])
  rows.append(dict(task_id=t['task_id'],positive=good,negative=bad,passed=good['passed'] and not bad['passed']))
  write(RUN/'scoring_acceptance.json',dict(passed=all(x['passed'] for x in rows) and len(rows)==30,rows=rows,budget=budget.snapshot()))
  print('CHECK',len(rows),t['task_id'],rows[-1]['passed'],flush=True)
  if not rows[-1]['passed']:raise RuntimeError('scorer consistency failed; no API')

class Transport:
 def __init__(self,budget,path):self.budget=budget;self.path=path;self.requests=[];self.cost_manager=NS(total_cost=0.0)
 def call(self,messages,temperature=0):
  if len(self.requests)>=8:raise BudgetExhausted('branch request ceiling')
  body=dict(model='deepseek-flash',messages=messages,temperature=temperature,max_tokens=4096,thinking={'type':'disabled'},reasoning_effort='none',stream=False)
  bound=len(canonical(body).encode())+2048
  if bound>32768:raise BudgetExhausted('final serialized input upper exceeds 32768')
  i=len(self.requests)+1;rid=str(self.path.relative_to(RUN))+f'/request_{i}'
  key=self.budget.reserve(bound,4096,job_id=str(self.path.relative_to(RUN)),capability='solve',request_id=rid,request_hash=fingerprint(body))
  row=dict(request=body,status='RESERVED',input_token_upper=bound,physical_model_request=True);self.requests.append(row);write(self.path/'requests.json',self.requests);start=time.monotonic()
  try:
   raw=DeepSeekGenerator._post(body,configured_api_key(),min(90,600))
   write(self.path/f'response_{i}.json',raw)
   if 'usage' not in raw or not raw.get('choices'):raise RuntimeError('provider response contract: '+str(raw.get('http_status','missing_usage')))
   u=raw['usage'];self.budget.settle(key,u['total_tokens'])
   if u['prompt_tokens']>bound or u['completion_tokens']>4096:raise BudgetExhausted('provider exceeded frozen token bound')
   row.update(status='COMPLETED',usage=u,model=raw['model'],seconds=time.monotonic()-start,estimated_usd=(u['prompt_tokens']*.3+u['completion_tokens']*1.2)/1000000)
   self.cost_manager.total_cost+=row['estimated_usd'];write(self.path/'requests.json',self.requests)
   choice=raw['choices'][0]
   if raw['model']!='deepseek-flash':raise RuntimeError('model alias differs from frozen model')
   return dict(text=choice['message'].get('content') or '',usage=u,model=raw['model'],finish_reason=choice.get('finish_reason'))
  except BaseException as e:
   self.budget.settle(key);row.update(error_type=type(e).__name__,seconds=time.monotonic()-start);write(self.path/'requests.json',self.requests);raise
 def native(self,r):return self.call([dict(role='system',content=r['system_prompt']),dict(role='user',content=r['prompt'])],r['temperature'])
 async def request(self,model,context,mode,function_name=None):
  key='reflection_and_solution' if model.__name__=='ReflectionTestOp' else 'response'
  if mode=='context_fill':context+='\nReturn strictly XML fields: '+''.join('<'+k+'>'+str(f.description or '')+'</'+k+'>' for k,f in model.model_fields.items())
  elif mode=='code_fill':context+='\nReturn complete runnable Python source, optionally in one python code fence, with no explanation. Preserve the public task interface.'
  r=self.call([dict(role='user',content=context)])
  text=r['text']
  if mode=='context_fill':
   found=dict(re.findall(r'<(\w+)>(.*?)</\1>',text,re.S))
   if not found.get('solution_letter','').strip():raise af.FormatFault('missing ensemble selection')
   return {k:v.strip() for k,v in found.items()}
  return {key:af.code_extract(text)} if mode=='code_fill' else {'response':text}

class RegistryUnion:
 """Read-only union of actual frozen registries; never changes old permissions."""
 def __init__(self,evidence):
  self.regs=[FailureOperatorRegistry(p,evidence) for p in sorted((RUN/'registries').glob('*.jsonl'))];self.queries=[]
 def snapshot(self,**kw):
  snaps=[r.snapshot(**kw) for r in self.regs];cards=tuple(c for s in snaps for c in s.cards)
  assert not cards,'new authorization requires a new frozen experiment'
  self.queries.append(dict(**kw,eligible_operator_count=len(cards),source_snapshot_ids=[s.snapshot_id for s in snaps]))
  write(RUN/'registry_queries.json',self.queries)
  return OperatorSnapshot(fingerprint([s.snapshot_id for s in snaps]),kw['stream_id'],kw['task_index'],cards,kw['experiment_id'],kw['at'])

def execute():
 p=verify();assert read(RUN/'scoring_acceptance.json')['passed'];assert configured_api_key(),'configured API key missing'
 if (RUN/'budget.jsonl').exists():raise FileExistsError('no automatic retry or reuse')
 budget=PersistentBudget(RUN/'budget.jsonl',run_id=RUN.name,protocol_hash=p['protocol_hash'],**p['api_budget']);judge=Judge(budget)
 context=Fingerprint('FlowEvo-native-public-v2','compare30-frozen-legal','deepseek-flash',sha(WORKER),p['protocol_hash'])
 evidence=FailureEvidenceStore(RUN/'failure_evidence.jsonl');registry=RegistryUnion(evidence);libraries={};rows=[]
 for index,t in enumerate(read(RUN/'tasks.json')):
  arms=p['arms'][index%3:]+p['arms'][:index%3]
  for arm in arms:
   path=RUN/'branches'/t['task_id']/arm;transport=Transport(budget,path);start=time.monotonic();checks=[];before=budget.snapshot()
   def public_eval(_task,code):
    if sum(c['seconds'] for c in checks)>=120:raise BudgetExhausted('public wall time')
    r=judge.run(t['task_id'],code,t['public_cases']);checks.append(r);return r
   if arm=='AFlow':
    class SharedAdaptation(af.Adaptation):
     async def check_public(self,code):
      r=public_eval(None,code);self.test_seconds+=r['seconds'];self.events.append(dict(kind='public_test',result=r))
      if r['passed']:return 'no error'
      if r['status']!='WRONG_ANSWER':return {'exec_fail_case':r['status']}
      return [dict(test_fail_case=dict(test_case=c,error_type='AssertionError',error_message='public output differs',traceback='isolated execution; host comparison')) for c in r['cases'] if not c['correct']]
    adapter=SharedAdaptation(dict(cases=t['public_cases']),transport,path)
    result=asyncio.run(adapter.run(prompt_for(t['task_public']),''));code=result.get('source','')
   else:
    bucket=(arm,t['dataset'],t['difficulty']);library=libraries.setdefault(bucket,CodeSkillLibrary())
    plugin=FailureLearningPlugin(registry,evidence,context,stream_id=RUN.name+'-'+t['dataset']+'-'+t['difficulty'],experiment_id=RUN.name,runner=judge.ev.runner) if arm=='FailureLearning' else None
    session=NativeBenchmarkSession(transport.native,public_eval,context,library=library,instance_factory=lambda d:CodeTaskInstance(task_id=d['problem_id'],benchmark=t['dataset'],prompt=d['prompt'],text=d['prompt']),extract_code=extract_code,plugin=plugin,max_output=4096)
    result=session.solve(t['task_public'],Budget(max_calls=8,max_tokens=294912,max_tools=30,wall_seconds=600));code=result['selected']['code'] if result.get('selected') else result['last_candidate']
   online_seconds=time.monotonic()-start;online_tools=budget.snapshot()['tool_calls']-before['tool_calls']
   write(path/'workflow.json',result);write(path/'public_checks.json',checks);(path/'final.py').write_text(code)
   # Final source is locked before separate audit; no audit is returned to any workflow/library.
   write(path/'final_lock.json',dict(sha256=sha(path/'final.py'),at=time.time(),status=result['status']))
   audit=judge.run(t['task_id'],code,t['audit_cases']);write(path/'audit.json',audit)
   row=dict(task_id=t['task_id'],dataset=t['dataset'],difficulty=t['difficulty'],arm=arm,status=result['status'],audit_pass=audit['passed'],audit_tests=audit['tests_run'],audit_passed=audit['tests_passed'],model_calls=len(transport.requests),input_tokens=sum(r.get('usage',{}).get('prompt_tokens',0) for r in transport.requests),output_tokens=sum(r.get('usage',{}).get('completion_tokens',0) for r in transport.requests),estimated_usd=sum(r.get('estimated_usd',0) for r in transport.requests),online_seconds=online_seconds,online_tool_calls=online_tools,audit_seconds=audit['seconds'],operator_calls=len(result.get('hook_events',[])),final_sha256=sha(path/'final.py'))
   rows.append(row);write(RUN/'results.json',dict(status='COMPLETE' if len(rows)==90 else 'RUNNING',rows=rows,budget=budget.snapshot()))
   print('RESULT',len(rows),t['task_id'],arm,'PASS' if audit['passed'] else 'FAIL','calls',len(transport.requests),'usd',round(row['estimated_usd'],5),flush=True)
 print('COMPLETE',flush=True)

if __name__=='__main__':
 setup();a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','acceptance','execute']);args=a.parse_args();globals()[args.phase]()
