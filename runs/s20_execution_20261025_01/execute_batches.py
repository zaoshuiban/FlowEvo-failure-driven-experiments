"""Authorized fixed-order launcher; uses frozen entry, never retries failed processes."""
import pathlib,sys,subprocess,time,traceback
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1];B=R/'runs/s20_preparation_20261025_01';sys.path.insert(0,str(R/'scripts'));import run_workflow_v2 as e
assert e.read(P/'preflight.json')['passed'] and e.read(P/'worker_probes.json')['status']=='PASS'
assert not (P/'execution_status.json').exists(),'No automatic restart of experiment launcher'
rows=[];e.write(P/'execution_status.json',dict(status='RUNNING',batches=rows,started_at=time.time()))
try:
 for batch in range(1,9):
  for arm in 'GMF':
   for f,h in e.read(B/'source_dependencies.json').items():assert e.sha(R/f)==h,f
   plan=e.read(B/f'plan_{arm}.json');folder=R/'runs'/plan['run_id'];started=time.time()
   print('START',batch,arm,flush=True)
   cmd=[sys.executable,str(R/'scripts/run_learning_stream.py'),'--plan',str(B/f'plan_{arm}.json'),'--authorization',str(P/f'authorization_{arm}.json'),'--tasks',str(B/'stream_tasks.json'),'--stop-after-batch',str(batch)]
   if batch>1:cmd+=['--resume']
   with (P/f'batch_{batch}_{arm}.log').open('w') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
   if code:raise RuntimeError(f'batch {batch} arm {arm} exited {code}; no automatic retry')
   state=e.read(folder/'state.json');assert all(not x['unknown_or_pending_requests'] for x in state['budgets'].values())
   requests=[x for ch in ('solve','learning','validation') for x in e.read(folder/f'{ch}_requests.json')]
   assert all(x['status']=='COMPLETED' for x in requests),'unknown request stop'
   row=dict(batch=batch,arm=arm,started_at=started,finished_at=time.time(),budgets=state['budgets'],requests=len(requests))
   rows.append(row);e.write(P/'execution_status.json',dict(status='RUNNING',batches=rows));print('FINISHED',batch,arm,len(requests),flush=True)
   if batch<8 and any(v['max_cost_microusd']>0 and state['budgets'][k]['remaining_cost_microusd']<=0 for k,v in plan['budgets'].items()):raise RuntimeError('frozen monetary hard cap exhausted')
 e.write(P/'execution_status.json',dict(status='ONLINE_COMPLETE',batches=rows,finished_at=time.time()))
 print('ALL_ONLINE_COMPLETE',flush=True)
except Exception as exc:
 e.write(P/'execution_status.json',dict(status='STOPPED',reason=str(exc),batches=rows,at=time.time()));traceback.print_exc();sys.exit(1)
