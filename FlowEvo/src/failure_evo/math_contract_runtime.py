"""Host validation adapters on the existing registry, runner and private scorer.
No model calls, second registry or mathematical oracle synthesis.
"""
import time
import tempfile
from pathlib import Path
from .contracts import fingerprint
from .evidence import EvidenceStore
from .operator_contract import binding, record_stage
from .run_health import RunUnhealthy

# Host-owned isolation probes. These are not candidate algorithms or math tests.
PROBES={
 'normal':("def probe(): return 3",lambda r:r.get('status')=='OK' and r.get('value')==3),
 'network':("import socket\ndef probe():\n s=socket.socket();s.settimeout(.2)\n try: s.connect(('192.0.2.1',443));return 'OPEN'\n except OSError: return 'BLOCKED'",lambda r:r.get('value')=='BLOCKED'),
 'write':("def probe():\n try: open('/outside-probe','w').write('x');return 'OPEN'\n except OSError: return 'BLOCKED'",lambda r:r.get('value')=='BLOCKED'),
 'memory_config':("def probe(): return open('/sys/fs/cgroup/memory.max').read().strip()",lambda r:r.get('value')=='268435456'),
 'memory_enforced':("def probe(): return bytearray(512*1024*1024)",lambda r:r.get('status')=='MEMORY_LIMIT'),
 'cpu_config':("def probe(): return open('/sys/fs/cgroup/cpu.max').read().strip()",lambda r:len(str(r.get('value','')).split())==2 and str(r.get('value','')).split()[0]==str(r.get('value','')).split()[1]),
 'pids_enforced':("import subprocess\ndef probe():\n ps=[]\n try:\n  for i in range(40): ps.append(subprocess.Popen(['sleep','2']))\n  return 'OPEN'\n except OSError:return 'LIMITED'\n finally:\n  for p in ps:p.terminate()\n  for p in ps:p.wait()",lambda r:r.get('value')=='LIMITED'),
 'pids_config':("def probe(): return open('/sys/fs/cgroup/pids.max').read().strip()",lambda r:r.get('value')=='32'),
 'fds':("def probe():\n fs=[]\n try:\n  for i in range(100):fs.append(open('/dev/null'))\n except OSError:return 'LIMITED'\n return 'OPEN'",lambda r:r.get('value')=='LIMITED'),
 'tmp':("def probe():\n try:\n  with open('/tmp/probe','wb') as f:\n   for i in range(40): f.write(b'x'*1048576)\n  return 'OPEN'\n except OSError:return 'LIMITED'",lambda r:r.get('value')=='LIMITED'),
 'output':("def probe():return 'x'*(2*1024*1024)",lambda r:r.get('status')=='OUTPUT_LIMIT'),
 'timeout':("def probe():\n while True:pass",lambda r:r.get('status')=='TIME_LIMIT'),
 'recursion':("def probe():return probe()",lambda r:r.get('status')=='RUNTIME_ERROR' and 'RecursionError' in r.get('error','')),
}

def validate_safety(registry,artifact,runner,*,engineering=False):
 from .semantic_contract import SplitRunner,component_check
 if type(runner) is not SplitRunner:raise PermissionError('real SplitRunner required')
 if artifact.get('origin')=='MOCK' and not engineering:raise PermissionError('engineering artifact')
 key=binding(artifact);worker=fingerprint(runner.backend.manifest())
 manifest={n:fingerprint(code) for n,(code,_) in PROBES.items()}
 manifest['host_canary']='existing-host-file-not-mounted-v1'
 data_hash=fingerprint(manifest);eid=fingerprint([key,'STATIC_SAFETY',worker,data_hash])
 events=registry.events.records()
 finished=[r['payload'] for r in events if r['kind']=='OPERATOR_VALIDATOR_EXECUTED' and r['payload'].get('execution_id')==eid]
 if finished:receipt=finished[-1]
 else:
  if any(r['kind']=='OPERATOR_VALIDATOR_STARTED' and r['payload'].get('execution_id')==eid for r in events):raise RunUnhealthy('interrupted safety validation; no replay')
  registry.events.append('OPERATOR_VALIDATOR_STARTED',dict(execution_id=eid,binding=key,stage='STATIC_SAFETY'),time.time())
  static={c:component_check(Path(artifact[p]).read_text(),c) for c,p in [('solve','solver_path'),('match','matcher_path')]}
  checks=[]
  # Candidate source is not executed until permission validation succeeded.
  if all(x['passed'] for x in static.values()):
   with tempfile.TemporaryDirectory(dir=registry.events.path.parent) as tmp:
    canary=Path(tmp)/'host-canary.txt';canary.write_text('HOST_TEST_CANARY_NO_PRIVATE_DATA')
    code='def probe():\n try: open('+repr(str(canary.resolve()))+').read();return "OPEN"\n except OSError:return "BLOCKED"'
    probes=dict(PROBES,host_canary=(code,lambda r:r.get('value')=='BLOCKED'))
    for name,(code,predicate) in probes.items():
     p=Path(tmp)/'probe.py';p.write_text(code)
     request=dict(mode='function',function='probe',args=[],timeout=1)
     token=runner.budget.tool(capability='math-safety-probe',request_hash=fingerprint([eid,name])) if runner.budget else None
     started=time.monotonic()
     try:
      with runner.backend(p) as w:raw=w.call(request)
     finally:
      if token is not None:runner.budget.settle(token,tool_milliseconds=int(1000*(time.monotonic()-started)))
     if raw.get('status') in ('EVALUATOR_ERROR','WORKER_ERROR'):raise RunUnhealthy('safety Worker infrastructure failure: '+name)
     checks.append(dict(name=name,raw=raw,passed=bool(predicate(raw)),seconds=time.monotonic()-started))
  receipt=dict(execution_id=eid,binding=key,stage='STATIC_SAFETY',data_hash=data_hash,worker_hash=worker,
   validator_identity='math_contract_runtime.validate_safety',validator_version='isolated-probes-v1',
   result_manifest_sha256=fingerprint([static,checks]),passed=all(x['passed'] for x in static.values()) and len(checks)==len(PROBES)+1 and all(x['passed'] for x in checks),
   engineering=engineering,source_original_ids=artifact['source_original_ids'],independent=False,static=static,checks=checks)
  registry.events.append('OPERATOR_VALIDATOR_EXECUTED',receipt,time.time())
 return record_stage(registry,artifact,stage='STATIC_SAFETY',passed=receipt['passed'],data_hash=data_hash,
  worker_hash=worker,source_original_ids=artifact['source_original_ids'],receipt=receipt)

class ContractShadow:
 """Pre-score execution, post-lock private evaluation; no returned solver answer."""
 def __init__(self,stream,arm,private_rows):
  from code_math.private_math_scoring import PrivateMathScorer
  self.s,self.arm=stream,arm;self.state=stream.arms[arm];root=self.state['path']/'private/contract_shadow'
  self.controller=EvidenceStore(root/'controller.jsonl')
  self.scorer=PrivateMathScorer(private_rows,self.controller.path,root/'scores.jsonl',strict_delivery=True)
 def observe(self,task,seq):
  s=self.s;reg=self.state['registry'];events=reg.events.records()
  if any(r['kind']=='PRIVATE_SCORED' and r['payload']['task_id']==task.task_id for r in self.state['states'].records()):return
  candidates={binding(r['payload']):r['payload'] for r in events if r['kind']=='MATH_SHADOW' and 'operator_contract' in r['payload']}
  admitted={binding(r['payload']['artifact']) for r in events if r['kind']=='MATH_EXPERIMENTAL' and 'operator_contract' in r['payload']['artifact']}
  for key,a in sorted(candidates.items()):
   if key in admitted:continue
   if seq<=a.get('candidate_created_after',10**12) or task.task_id in a['excluded_task_ids']:continue
   original=s.lineage[task.task_id]['source_original_id']
   if original=='UNKNOWN' or original in a['source_original_ids']:continue
   from .operator_contract import require_stages
   if a.get('origin')=='MOCK' and not s.engineering:raise PermissionError('Mock cannot execute in real Shadow')
   try:require_stages(reg,a,('STATIC_SAFETY','SOURCE','INDEPENDENT_GATE'))
   except PermissionError:continue
   eid=fingerprint([key,task.task_id,seq,'shadow-v1'])
   old=[r for r in reg.events.records() if r['payload'].get('execution_id')==eid]
   if any(r['kind']=='CONTRACT_SHADOW_EXECUTED' for r in old):continue
   if old:raise RunUnhealthy('interrupted Shadow; no implicit replay')
   reg.events.append('CONTRACT_SHADOW_STARTED',dict(execution_id=eid,binding=key,task_id=task.task_id,sequence=seq),time.time())
   result=self.state['split'].run(a,task)
   reg.events.append('CONTRACT_SHADOW_EXECUTED',dict(execution_id=eid,binding=key,artifact=a,task_id=task.task_id,sequence=seq,result=result,original_id=original),time.time())
   break # frozen maximum one candidate per task
 def finalize(self,task,baseline):
  reg=self.state['registry']
  if not any(r['kind']=='ANSWER_LOCKED' and r['payload']['task_id']==task.task_id and r['payload']['lock']==baseline for r in self.state['states'].records()):
   raise PermissionError('Shadow scoring requires actual durable baseline lock')
  rows=[r['payload'] for r in reg.events.records() if r['kind']=='CONTRACT_SHADOW_EXECUTED' and r['payload']['task_id']==task.task_id]
  for row in rows:
   a=row['artifact'];result=row['result'];eid=row['execution_id']
   prior=[r['payload'] for r in reg.events.records() if r['kind']=='OPERATOR_VALIDATOR_EXECUTED' and r['payload'].get('execution_id')==eid]
   if prior:
    receipt=prior[-1]
    record_stage(reg,a,stage='SHADOW_OBSERVATION',passed=receipt['passed'],data_hash=receipt['data_hash'],worker_hash=receipt['worker_hash'],source_original_ids=receipt['source_original_ids'],independent=True,receipt=receipt)
    continue
   locked=dict(task_id=task.task_id,episode_id=eid,final_output=result.get('answer',''),responses=[],operator_events=[result])
   locked['locked_sha256']=fingerprint(locked)
   old=[r for r in self.controller.records() if r['kind']=='MATH_ANSWER_LOCKED' and r['payload']['episode_id']==eid]
   if old and old[0]['payload']!=locked:raise PermissionError('Shadow lock drift')
   if not old:self.controller.append('MATH_ANSWER_LOCKED',locked,time.time())
   score=self.scorer.score(task,locked)
   receipt=dict(execution_id=eid,binding=binding(a),stage='SHADOW_OBSERVATION',data_hash=fingerprint(task.problem),
    worker_hash=fingerprint(self.state['split'].backend.manifest()),validator_identity='ContractShadow/PrivateMathScorer',validator_version='shadow-v1',
    passed=result['status']=='APPLIED' and score.get('status')=='CONFIRMED_CORRECT',engineering=self.s.engineering,
    source_original_ids=[row['original_id']],independent=True,result_manifest_sha256=fingerprint([result,score]),baseline_result_reference=baseline['locked_sha256'],score=score)
   reg.events.append('OPERATOR_VALIDATOR_EXECUTED',receipt,time.time())
   record_stage(reg,a,stage='SHADOW_OBSERVATION',passed=receipt['passed'],data_hash=receipt['data_hash'],worker_hash=receipt['worker_hash'],source_original_ids=receipt['source_original_ids'],independent=True,receipt=receipt)

def contract_metrics(registry, memory=None, cutoff=None):
 """Read-only funnel; missing outcome denominators never become success rates."""
 rows=registry.events.records()
 artifacts={binding(r['payload']):r['payload'] for r in rows if r['kind']=='MATH_SHADOW' and 'operator_contract' in r['payload']}
 metrics={
  'contract_accepted_candidates':len(artifacts),
  'instance_solvers':sum(a['operator_contract']['artifact_kind']=='INSTANCE_SOLVER' for a in artifacts.values()),
  'reusable_candidates':sum(a['operator_contract']['artifact_kind']=='REUSABLE_CANDIDATE' for a in artifacts.values()),
  'shadow_executed':len({r['payload']['execution_id'] for r in rows if r['kind']=='CONTRACT_SHADOW_EXECUTED'}),
  'authorized_operators':len({r['payload'].get('candidate_version',r['payload']['code_sha256']) for r in rows if r['kind']=='V3_TRIAL_AUTHORIZATION'}),
  'actual_interventions':len({(r['payload']['task_id'],r['payload']['sequence']) for r in rows if r['kind']=='MATH_ROUTER_EXECUTED' and r['payload']['result']['status']=='APPLIED'}),
  'intervention_attempts':len({(r['payload']['task_id'],r['payload']['sequence']) for r in rows if r['kind']=='MATH_ROUTER_EXECUTED'}),
  'independent_successes':'NOT_EVALUABLE_WITHOUT_PAIRED_OUTCOME_AUDIT',
 }
 for stage,label in [('STATIC_SAFETY','static_safety_passed'),('SOURCE','source_validated'),('INDEPENDENT_GATE','independent_gate_passed')]:
  latest={r['payload']['binding']:r['payload']['passed'] for r in rows if r['kind']=='OPERATOR_CONTRACT_REVIEW' and r['payload']['stage']==stage}
  metrics[label]=sum(latest.values())
 if memory is not None and cutoff is not None:
  facts=memory.facts(cutoff);attempts=[r['payload'] for r in memory.attempts.records() if r['payload']['cutoff']<=cutoff]
  metrics.update(trusted_failures=sum(f.get('correct') is False for f in facts.values()),association_attempts=len(attempts),
   multi_evidence_attempts=sum(len(set(r['evidence_ids']))>1 for r in attempts),accepted_clusters=len(memory.state(cutoff)))
 else:
  for k in ('trusted_failures','association_attempts','multi_evidence_attempts','accepted_clusters'):metrics[k]='NOT_EVALUABLE'
 root=registry.events.path.parent
 requests=[];responses=[]
 for path in (root/'learning').rglob('compiler.jsonl') if (root/'learning').exists() else []:
  events=EvidenceStore(path).records()
  requests.extend(r['payload'] for r in events if r['kind']=='GENERATION_REQUESTED')
  responses.extend(r['payload']['response'] for r in events if r['kind']=='GENERATION_RESPONSE')
 metrics['candidate_generation_attempts']=sum(r.get('phase')=='candidate' for r in requests)
 metrics['learning_and_revision_requests']=len(requests)
 metrics['learning_response_tokens']=sum(r.get('usage',{}).get('total_tokens',0) or 0 for r in responses)
 worker=EvidenceStore(root/'worker.jsonl')
 component_rows=[r['payload'] for r in worker.records() if r['kind']=='V3_COMPONENT_EXECUTED']
 safety_rows=[r['payload'] for r in rows if r['kind']=='OPERATOR_VALIDATOR_EXECUTED' and r['payload'].get('stage')=='STATIC_SAFETY']
 metrics['worker_seconds']=sum(r.get('seconds',0) for r in component_rows)+sum(c['seconds'] for r in safety_rows for c in r.get('checks',[]))
 metrics['worker_calls']=len(component_rows)+sum(len(r.get('checks',[])) for r in safety_rows)
 from .persistent_budget import PersistentBudget
 unknown=0
 for path in root.rglob('*budget.jsonl'):
  budget=PersistentBudget.__new__(PersistentBudget);budget.path=path
  with budget._locked() as ledger:states,_=budget._state(ledger)
  unknown+=sum(r.get('cost_upper_microusd',0) for r in states.values() if r.get('status') not in ('settled','not_sent'))
 metrics['unknown_or_pending_reserved_microusd']=unknown
 metrics['estimated_model_cost']='NOT_EVALUABLE_WITHOUT_FROZEN_CHANNEL_PRICES'
 metrics['actual_supplier_bill']='NOT_AVAILABLE'
 return metrics
