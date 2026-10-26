"""Sealed evaluation only after all three online states are locked. No model sender."""
import pathlib,sys,tempfile,time,hashlib
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1];B=R/'runs/s20_preparation_20261025_01';sys.path.insert(0,str(R/'scripts'));import run_workflow_v2 as e
from run_learning_stream import configure_worker
from failure_evo.evidence import EvidenceStore
from failure_evo.contracts import fingerprint
assert e.read(P/'execution_status.json')['status']=='ONLINE_COMPLETE'
for arm in 'GMF':
 folder=R/'runs'/e.read(B/f'plan_{arm}.json')['run_id'];rows=EvidenceStore(folder/'stream.jsonl').records()
 assert any(x['kind']=='ONLINE_LOCKED' for x in rows) and sum(x['kind']=='TASK_FINALIZED' for x in rows)==80
sealed={x['task_id']:x['cases'] for x in e.read(B/'sealed_final_tasks.json')};tasks=e.read(B/'stream_tasks.json')
configure_worker(e.read(B/'plan_G.json')['worker_environment']);tempfile.tempdir=str(P/'tmp')
protocol=dict(tasks_sha256=e.sha(B/'stream_tasks.json'),sealed_sha256=e.sha(B/'sealed_final_tasks.json'),source_commit='7229373535abc42794c9dd993d7f9f98308f8eda',max_tools=4368,wall_seconds=21600,model_requests=0,selection='selected code else unchanged last_candidate; source and trial outputs separately; no feedback to online state')
e.write(P/'final_evaluation_protocol.json',protocol)
budget=e.PersistentBudget(P/'final_evaluation_budget.jsonl',run_id=P.name+'-sealed',protocol_hash=fingerprint(protocol),**e.prior.config(0,4368,0));judge=e.prior.Judge(budget)
rows=[];started=time.time()
for arm in 'GMF':
 folder=R/'runs'/e.read(B/f'plan_{arm}.json')['run_id']
 for task in tasks:
  tid=task['task_id'];f=folder/'branches'/tid/arm/'workflow.json';w=e.read(f);code=w['selected']['code'] if w.get('selected') else w.get('last_candidate','')
  result=judge.run(tid,code,sealed[tid]);rows.append(dict(arm=arm,task_id=tid,kind='TASK_FINAL',code_sha256=hashlib.sha256(code.encode()).hexdigest(),public_pass=w['status']=='PUBLIC_ACCEPTED',selected=bool(w.get('selected')),result=result))
  e.write(P/'sealed_results.json',rows);print(arm,tid,result['tests_passed'],result['tests_run'],flush=True)
folder=R/'runs'/e.read(B/'plan_F.json')['run_id']
for f in sorted((folder/'assessments').glob('*.json')):
 a=e.read(f)
 if not a.get('proposed_code'):continue
 packet=e.read(folder/'public_packets'/(a['source_event_id']+'.json'));tid=packet['task_id'];result=judge.run(tid,a['proposed_code'],sealed[tid]);rows.append(dict(arm='F',task_id=tid,kind='SOURCE_OPERATOR',assessment=str(f.relative_to(R)),public_pass=bool(a.get('source_success')),result=result));e.write(P/'sealed_results.json',rows)
for f in sorted((folder/'branches').glob('*/F/workflow.json')):
 w=e.read(f);tid=w['problem_id']
 for h in w.get('hook_events',[]):
  if not h.get('proposed_code'):continue
  result=judge.run(tid,h['proposed_code'],sealed[tid]);rows.append(dict(arm='F',task_id=tid,kind='FUTURE_OPERATOR',candidate_id=h['candidate_id'],public_pass=h['status']=='applied',result=result));e.write(P/'sealed_results.json',rows)
e.write(P/'sealed_summary.json',dict(completed=True,seconds=time.time()-started,budget=budget.snapshot(),model_calls=0,results=len(rows)))
