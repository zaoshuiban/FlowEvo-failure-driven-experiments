"""Explicitly authorized P1/P2 only. Freeze first; no legacy budgets or Gate."""
import argparse,hashlib,json,os,subprocess,sys,time,collections,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import fingerprint,canonical
from failure_evo.evidence import EvidenceStore
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.math_discovery_p1p2 import *
from failure_evo.math_transport import NoGoldSolverChannel
from failure_evo.math_operators import MathOperatorRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.model_api import configured_api_key
from failure_evo.workflow_protocol_v2 import prepare,Limits
from code_math.no_gold import NoGoldMathController,NoGoldPolicy,solver_messages
DATA=ROOT/'reports/math_no_gold_p0_20261027/data'
WORKER='experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
IMAGE='sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def lines(p):return [json.loads(s) for s in p.read_text().splitlines() if s]
def make_budget(path,run,phash,channel):
 solver=channel=='solver'
 return PersistentBudget(path,run_id=run+':'+channel,protocol_hash=phash,max_calls=192 if solver else 3,max_tokens=192*36864 if solver else 3*73728,
 max_tools=0 if solver else 6,max_cost_microusd=9000000 if solver else 4000000,token_rate_microusd_per_million=1200000 if solver else 15000000,
 tool_cost_upper_microusd=0,max_tool_milliseconds=0 if solver else 120000,tool_milliseconds_upper=20000,wall_seconds=21600)
def freeze(out):
 if out.exists():raise ValueError('new Run directory required')
 if not configured_api_key() or not os.environ.get('OPENROUTER_API_KEY'):raise PermissionError('both credentials required before freeze')
 tasks=[PublicMathTask.parse(x) for x in lines(DATA/'public/discovery.jsonl')]
 assert len(tasks)==96
 observed=[]
 for task in tasks:
  for previous in (None,'x'*16384):
   observed.append(prepare(solver_messages(task,previous),limits=Limits(input_token_upper=32768,output_tokens=4096)).input_upper)
 code={str(p.relative_to(ROOT)):sha(p) for d in ('FlowEvo/src/code_math','FlowEvo/src/failure_evo','FlowEvo/src/runtime','FlowEvo/src/core','FlowEvo/src/env','FlowEvo/src/eval') for p in (ROOT/d).rglob('*.py')}
 code[WORKER]=sha(ROOT/WORKER);code['scripts/run_math_p1p2.py']=sha(Path(__file__))
 protocol=dict(version=VERSION,run_id=out.name,scope='P1/P2 only; no Design/Gate/Legacy/Fresh/operator reuse',
 base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_hashes=code,
 data_hashes={name:sha(DATA/name) for name in ('public/discovery.jsonl','private/discovery.jsonl')},task_ids=[t.task_id for t in tasks],
 solver=dict(model='deepseek-flash',documented_version='DeepSeek-V4.1-Flash-1017',calls_per_task=2,reflection='fixed unconditional, no interim score',output=4096,input_upper=32768,temperature=0,thinking=False,hard_usd=9,max_calls=192),
 compiler=dict(model='gpt-5.4',canonical_version='openai/gpt-5.4-20260305',transport='OpenRouter',provider='OpenAI only, fallback disabled',arms=['F','T'],max_calls_each=3,hard_usd_each=4,input_upper=65536,output=8192,reasoning='medium',selection='earliest two distinct final CONFIRMED_WRONG tasks',minimum_distinct_failures=2,candidates_each=1,format_revisions_each=1),
 quote=dict(checked_on='2026-10-27',deepseek_input_per_million=.3,deepseek_output_per_million=1.2,gpt_input_per_million=2.5,gpt_output_per_million=15,deepseek='https://api-docs.deepseek.com/quick_start/pricing/',gpt='https://openrouter.ai/api/v1/models',quote_upper_usd=192*(32768*.3+4096*1.2)/1e6+6*(65536*2.5+8192*15)/1e6,reservation_upper_usd=192*36864*1.2/1e6+6*73728*15/1e6,total_hard_usd=17),
 worker=dict(image=IMAGE,script=WORKER,sha256=sha(ROOT/WORKER),timeout=2,max_calls_per_arm=6),
 preliminary_input_preflight_max=max(observed),preflight_limitation='self-review uses actual previous output at runtime; placeholder is not a proof for every possible response',
 stopping=['UNKNOWN request','gold leak','data contamination','Worker fault','hard budget exhausted'],
 user_authorization='Latest explicit user request: 已授权; scope P1/P2 bounded study; old budgets not inherited',paid_api_authorized=True)
 out.mkdir(parents=True);save(out/'protocol.json',protocol);save(out/'authorization.json',dict(protocol_sha256=sha(out/'protocol.json'),scope=protocol['scope'],max_cost_usd=17,authorized=True,source=protocol['user_authorization']))
 print(json.dumps(dict(status='FROZEN',run=str(out),hash=sha(out/'protocol.json'),budget=protocol['quote']),ensure_ascii=False),flush=True)

def run(out):
 protocol=json.loads((out/'protocol.json').read_text());phash=sha(out/'protocol.json');auth=json.loads((out/'authorization.json').read_text())
 if auth['protocol_sha256']!=phash or not auth['authorized']:raise PermissionError('authorization mismatch')
 for name,digest in protocol['source_hashes'].items():
  if sha(ROOT/name)!=digest:raise ValueError('source changed: '+name)
 for name,digest in protocol['data_hashes'].items():
  if sha(DATA/name)!=digest:raise ValueError('data changed')
 if (out/'STOP.json').exists() or (out/'COMPLETE.json').exists():raise RuntimeError('run consumed')
 tasks=[PublicMathTask.parse(x) for x in lines(DATA/'public/discovery.jsonl')]
 private=lines(DATA/'private/discovery.jsonl')
 b=make_budget(out/'solver_budget.jsonl',out.name,phash,'solver')
 authorization=dict(run_id=b.config['run_id'],protocol_hash=phash,model='deepseek-flash',max_cost_microusd=9000000,paid_api_authorized=True,channel='math-solver-no-gold-v1')
 client=NoGoldSolverChannel(b,out/'solver_requests.jsonl',authorization=authorization)
 controller=NoGoldMathController(client,out/'controller.jsonl',policy=NoGoldPolicy())
 recorder=DiscoveryRecorder(out/'discovery_scores.jsonl',out/'controller.jsonl',private)
 try:
  for i,t in enumerate(tasks):
   locked=[r['payload'] for r in controller.events.records() if r['kind']=='MATH_ANSWER_LOCKED' and r['payload']['task_id']==t.task_id]
   result=locked[0] if locked else controller.solve(t,episode_id=out.name+'/'+t.task_id,sequence=i)
   row=recorder.record(t,result)
   print(json.dumps(dict(stage='P1',completed=i+1,task_id=t.task_id,initial=row['initial']['status'],final=row['final']['status'],calls=b.snapshot()['calls']),ensure_ascii=False),flush=True)
  failures=recorder.failures();save(out/'failure_list.json',failures)
  bundle=recorder.bundle()
  if bundle is None:
   save(out/'COMPLETE.json',dict(status='PARTIAL_INSUFFICIENT_FAILURES',confirmed_final_failures=len(failures),p2_started=False));return
  save(out/'frozen_learning_bundle.json',bundle)
  results={}
  for arm in ('F','T'):
   root=out/arm;root.mkdir(exist_ok=True)
   b2=make_budget(root/'budget.jsonl',out.name,phash,arm)
   grant=dict(run_id=b2.config['run_id'],protocol_hash=phash,model='gpt-5.4',protocol=VERSION,max_cost_microusd=4000000,paid_api_authorized=True)
   provider=BinaryMathGPTAdapter(root/'provider.jsonl',b2,model='gpt-5.4',authorization=grant,max_wire_input_upper=65536)
   compiler=BoundedCompiler(provider,b2,root/'compiler.jsonl','gpt-5.4',max_input_upper=65536,max_output_upper=8192)
   runner=MathOperatorRunner(FrozenLinuxBackend(image=IMAGE,worker_script=ROOT/WORKER),budget=b2)
   # All GPT wires checked before its first send, using the immutable binary-only bundle.
   job=dict(stream_id=b2.config['run_id'],family_id='math-'+arm,arm=arm,discovery=bundle,phase='induction',slot=0,max_tokens=8192)
   body=provider.preflight(job);save(root/'induction_preflight.json',dict(wire=body,sha256=fingerprint(body),gold_exposed=False))
   result=EngineeringDiscovery(root/'candidate',compiler,runner,arm).run(bundle);results[arm]=result
   save(root/'result.json',result);print(json.dumps(dict(stage='P2',arm=arm,result=result),ensure_ascii=False),flush=True)
  save(out/'COMPLETE.json',dict(status='P1P2_COMPLETE',results=results))
 except BaseException as exc:
  save(out/'STOP.json',dict(status='STOPPED',exception_type=type(exc).__name__,message=str(exc)[:500],at=time.time(),no_retry=True))
  print(json.dumps(dict(status='STOPPED',error=type(exc).__name__,message=str(exc)[:300]),ensure_ascii=False),flush=True);raise

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','run']);p.add_argument('--run',required=True);a=p.parse_args();out=Path(a.run).resolve()
 (freeze if a.mode=='freeze' else run)(out)
