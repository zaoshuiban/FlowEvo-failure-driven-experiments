"""P1-only entry; a new matching authorization file is mandatory, never inferred."""
import sys,json,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from code_math.no_gold import PublicMathTask,NoGoldMathController,NoGoldPolicy
from code_math.discovery_continuation import grade_continuation,VERSION
from failure_evo.math_discovery_p1p2 import DiscoveryRecorder
from failure_evo.math_transport import NoGoldSolverChannel
from failure_evo.persistent_budget import PersistentBudget

def run(root):
 protocol_path=root/'protocol.json';p=json.loads(protocol_path.read_text());digest=hashlib.sha256(protocol_path.read_bytes()).hexdigest()
 auth=json.loads((root/'authorization.json').read_text())
 if auth!={'run_id':root.name,'protocol_sha256':digest,'max_cost_usd':8,'paid_api_authorized':True}:raise PermissionError('new exact P1 authorization required')
 if (root/'STOP.json').exists() or (root/'COMPLETE.json').exists():raise RuntimeError('consumed run')
 for name,sha in p['source_hashes'].items():
  if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError('frozen source changed')
 b=PersistentBudget(root/'budget.jsonl',run_id=root.name,protocol_hash=digest,max_calls=p['max_calls'],max_tokens=p['max_calls']*36864,max_tools=0,max_cost_microusd=8000000,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=20000,wall_seconds=21600)
 grant=dict(run_id=root.name,protocol_hash=digest,model='deepseek-flash',max_cost_microusd=8000000,paid_api_authorized=True,channel='math-solver-no-gold-v1')
 client=NoGoldSolverChannel(b,root/'requests.jsonl',authorization=grant)
 controller=NoGoldMathController(client,root/'controller.jsonl',policy=NoGoldPolicy(delivery_profile='concise-v1'))
 private_path=ROOT/'reports/math_no_gold_p0_20261027/data/private/discovery.jsonl'
 if hashlib.sha256(private_path.read_bytes()).hexdigest()!=p['private_discovery_sha256']:raise ValueError('private scorer dataset changed')
 private=[json.loads(x) for x in (ROOT/'reports/math_no_gold_p0_20261027/data/private/discovery.jsonl').read_text().splitlines()]
 recorder=DiscoveryRecorder(root/'scores.jsonl',root/'controller.jsonl',private,grade_function=grade_continuation,scorer_version=VERSION)
 try:
  for i,row in enumerate(p['plan']['new_tasks']):
   if (root/'STOP_REQUESTED').exists():raise RuntimeError('host stop at task boundary')
   task=PublicMathTask.parse(row)
   known=[r['payload'] for r in controller.events.records() if r['kind']=='MATH_ANSWER_LOCKED' and r['payload']['task_id']==task.task_id]
   locked=known[0] if known else controller.solve(task,episode_id=root.name+'/'+task.task_id,sequence=i+14)
   scored=recorder.record(task,locked)
   print(json.dumps(dict(completed=i+1,task_id=task.task_id,status=scored['final']['status']),ensure_ascii=False),flush=True)
  failures=recorder.failures()
  (root/'confirmed_failures.json').write_text(json.dumps(failures,ensure_ascii=False,indent=2)+'\n')
  (root/'COMPLETE.json').write_text(json.dumps(dict(completed=len(p['plan']['new_tasks']),confirmed_failures=len(failures),p2_started=False))+'\n')
 except BaseException as e:
  (root/'STOP.json').write_text(json.dumps(dict(error=type(e).__name__,reason=str(e)[:300],at=time.time(),no_retry=True))+'\n');raise
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
