"""Explicit user-approved, single-request quarantine. Frozen research modules unchanged."""
import sys,pathlib,json,time,shutil,subprocess,tempfile,fcntl
P=pathlib.Path(__file__).resolve().parent;R=P.parents[1];B=R/'runs/s20_preparation_20261025_01'
sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
import run_learning_stream as stream
from failure_evo.evidence import EvidenceStore
from experiment_s16b2_source import sender_factory
RID='F/s19g_taco-train-s00-r1204/1';TID='s19g_taco-train-s00-r1204'
F=R/'runs/s20_taco80_f_20261025_01'; AUTH=P/'resume_authorization.json'
read,write=e.read,e.write
BaseBudget=e.PersistentBudget

def check():
 a=read(AUTH);assert a['request_id']==RID and a['skip_task']==TID and a['hard_cap_usd']==66
 for f,h in read(B/'source_dependencies.json').items():assert e.sha(R/f)==h,f
 for arm in 'GMF':
  p=read(B/f'plan_{arm}.json');assert read(P/f'authorization_{arm}.json')==dict(run_id=p['run_id'],protocol_hash=p['protocol_hash'],model=p['model'],budgets=p['budgets'],allow_real_api=True)
  assert e.sha(B/'stream_tasks.json')==p['tasks_sha256']
 stream.configure_worker(read(B/'plan_F.json')['worker_environment'])
 u=[x for x in read(F/'solve_requests.json') if x['status']=='UNKNOWN'];assert len(u)==1 and u[0]['request_id']==RID
 assert not (F/'wire/solve/25/response.json').exists()

class QuarantinedBudget(BaseBudget):
 def snapshot(self):
  s=super().snapshot()
  if self.path.resolve()==(F/'solve_budget.jsonl').resolve():
   s['quarantined_unknown_requests']=[x for x in s['unknown_or_pending_requests'] if x==RID]
   s['unknown_or_pending_requests']=[x for x in s['unknown_or_pending_requests'] if x!=RID]
  return s

def runtime_read(path):
 d=read(path)
 if pathlib.Path(path).resolve()==(F/'solve_requests.json').resolve():
  for row in d:
   if row['request_id']==RID:
    assert row['status']=='UNKNOWN';row['status']='QUARANTINED_UNKNOWN';row['recovery_authorization_sha256']=e.sha(AUTH)
 return d

def durable_write(path,data):
 if pathlib.Path(path).resolve()==(F/'solve_requests.json').resolve():
  data=json.loads(json.dumps(data))
  for row in data:
   if row['request_id']==RID:
    assert row['status'] in ('QUARANTINED_UNKNOWN','UNKNOWN');row['status']='UNKNOWN'
 write(path,data)

class SkippedLog:
 def __init__(self,log):self.log=log
 def records(self):
  rows=self.log.records()
  if any(x['kind']=='INFRASTRUCTURE_TASK_SKIPPED' and x['payload']['task_id']==TID for x in rows):
   # In-memory cursor only: never persist a false successful TASK_FINALIZED.
   rows=rows+[dict(kind='TASK_FINALIZED',payload=dict(task_id=TID,administrative_skip=True))]
  return rows
 def append(self,*args,**kwargs):return self.log.append(*args,**kwargs)

def runner(dry=False):
 e.PersistentBudget=QuarantinedBudget;e.read=runtime_read;e.write=durable_write
 def forbidden(channel):
  def send(wire):raise AssertionError('zero API acceptance attempted a send')
  return send
 p=read(B/'plan_F.json');r=e.ExperimentRunner(F,p,forbidden if dry else sender_factory,resume=True)
 s=stream.LearningStream(r,read(B/'stream_tasks.json'),arm='F',batch_size=10)
 s.log=SkippedLog(s.log)
 return r,s

def accept():
 check();before=e.sha(F/'solve_budget.jsonl');r,s=runner(True)
 base=BaseBudget.snapshot(r.budgets['solve']);live=r.budgets['solve'].snapshot()
 assert RID in base['unknown_or_pending_requests'] and RID not in live['unknown_or_pending_requests']
 for k in ('calls','charged_or_reserved_tokens','charged_or_reserved_cost_microusd','remaining_cost_microusd'):assert base[k]==live[k]
 assert [x for x in r.transports['solve'].audit if x['request_id']==RID][0]['status']=='QUARANTINED_UNKNOWN'
 assert before==e.sha(F/'solve_budget.jsonl')
 assert not any(x['kind']=='TASK_FINALIZED' and x['payload']['task_id']==TID for x in EvidenceStore(F/'stream.jsonl').records())
 # New unknowns remain blocking; skip affects only one task cursor.
 from unittest.mock import patch
 with patch.object(BaseBudget,'snapshot',return_value=dict(base,unknown_or_pending_requests=[RID,'NEW_UNKNOWN'])):
  assert r.budgets['solve'].snapshot()['unknown_or_pending_requests']==['NEW_UNKNOWN']
 assert all(x['payload']['task_id']!=TID for x in s.log.records() if x['kind']=='TASK_FINALIZED')
 write(P/'resume_acceptance.json',dict(passed=True,model_calls=0,full_reservation_retained=True,new_unknown_still_blocks=True,original_unknown_status_preserved=True,ledger_sha256=before,at=time.time()))
 print('ZERO_API_RECOVERY_ACCEPTANCE_PASS',flush=True)

def execute_f(batch):
 check();r,s=runner();raw=EvidenceStore(F/'stream.jsonl')
 if not any(x['kind']=='INFRASTRUCTURE_TASK_SKIPPED' for x in raw.records()):
  raw.append('INFRASTRUCTURE_TASK_SKIPPED',dict(task_id=TID,request_id=RID,reason='URLError; no response; user-authorized missing evaluation',authorization_sha256=e.sha(AUTH),not_program_failure=True,not_learning_evidence=True),time.time())
 tempfile.tempdir=str(F/'tmp')
 try:s.run(stop_after_batch=batch)
 finally:r.save()

def launch():
 lock=(P/'resume.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 check();assert read(P/'resume_acceptance.json')['passed']
 state=read(P/'execution_status.json');assert state['status']=='STOPPED'
 rows=state['batches'];done={(x['batch'],x['arm']) for x in rows}
 assert done=={(1,'G'),(1,'M'),(1,'F'),(2,'G'),(2,'M')}
 write(P/'execution_status.json',dict(status='RUNNING',batches=rows,recovery_authorization_sha256=e.sha(AUTH),skipped=dict(arm='F',task_id=TID),unresolved_reserved_requests=[RID]))
 try:
  for batch in range(1,9):
   for arm in 'GMF':
    if (batch,arm) in done:continue
    for f,h in read(B/'source_dependencies.json').items():assert e.sha(R/f)==h,f
    print('RESUME_START',batch,arm,flush=True);started=time.time()
    if arm=='F':cmd=[sys.executable,__file__,'f',str(batch)]
    else:cmd=[sys.executable,str(R/'scripts/run_learning_stream.py'),'--plan',str(B/f'plan_{arm}.json'),'--authorization',str(P/f'authorization_{arm}.json'),'--tasks',str(B/'stream_tasks.json'),'--stop-after-batch',str(batch),'--resume']
    with (P/f'resume_batch_{batch}_{arm}.log').open('x') as out:rc=subprocess.call(cmd,cwd=R,stdout=out,stderr=subprocess.STDOUT)
    if rc:raise RuntimeError(f'resumed batch {batch} arm {arm} exited {rc}; no automatic retry')
    folder=R/'runs'/read(B/f'plan_{arm}.json')['run_id'];st=read(folder/'state.json')
    assert not any(x['unknown_or_pending_requests'] for x in st['budgets'].values())
    for ch in ('solve','learning','validation'):
     for x in read(folder/f'{ch}_requests.json'):assert x['status']=='COMPLETED' or (arm=='F' and ch=='solve' and x['request_id']==RID and x['status']=='UNKNOWN')
    rows.append(dict(batch=batch,arm=arm,started_at=started,finished_at=time.time(),budgets=st['budgets'],resumed=True))
    write(P/'execution_status.json',dict(status='RUNNING',batches=rows,skipped=dict(arm='F',task_id=TID),unresolved_reserved_requests=[RID],recovery_authorization_sha256=e.sha(AUTH)))
    print('RESUME_FINISHED',batch,arm,flush=True)
  write(P/'execution_status.json',dict(status='ONLINE_COMPLETE_WITH_INFRASTRUCTURE_SKIP',batches=rows,skipped=dict(arm='F',task_id=TID),unresolved_reserved_requests=[RID],finished_at=time.time(),sealed_evaluation='pending recovery-aware offline review'))
 except Exception as exc:
  write(P/'execution_status.json',dict(status='STOPPED',reason=str(exc),batches=rows,skipped=dict(arm='F',task_id=TID),unresolved_reserved_requests=[RID],at=time.time()));raise

if __name__=='__main__':
 if sys.argv[1]=='accept':accept()
 elif sys.argv[1]=='f':execute_f(int(sys.argv[2]))
 elif sys.argv[1]=='launch':launch()
