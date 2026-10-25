import sys,json,hashlib,datetime,collections
from pathlib import Path
sys.path.insert(0,'scripts');import run_workflow_v2 as e
r=e.ROOT/'runs/s19f_stream17_20261024_01';out=e.ROOT/'reports/s19f_stream17_20261024_01'
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(l) for l in p.read_text().splitlines() if l] if p.exists() else []
p=read(r/'plan.json');tasks=read(e.ROOT/'reports/s19f_preparation_20261024_01/tasks.json');stream=rows(r/'stream.jsonl');locked=any(x['kind']=='ONLINE_LOCKED' for x in stream)
if not locked:raise SystemExit('Not locked; reporting final results is prohibited')
out.mkdir(exist_ok=True)
assert all(e.sha(e.ROOT/f)==h for f,h in p['frozen_files'].items())
facts=[x['payload'] for x in rows(r/'evidence_F.jsonl') if x['kind']=='FAILURE_FACT'];hr=rows(r/'hypotheses.jsonl');registry=rows(r/'rule_registry.jsonl')
channels={};requests=[]
for ch in ('solve','learning','validation'):
 ledger=rows(r/f'{ch}_budget.jsonl');res={x['payload']['request_id']:x for x in ledger if x['kind']=='RESERVED'}
 reqs=read(r/f'{ch}_requests.json')
 for x in reqs:
  u=x.get('usage',{});stamp=res[x['request_id']]['at'];dt=datetime.datetime.fromtimestamp(stamp,datetime.timezone.utc)
  if dt.weekday()<5:raise ValueError('holiday/peak determination must be explicitly reviewed')
  hit=u.get('prompt_cache_hit_tokens',u.get('prompt_tokens_details',{}).get('cached_tokens'))
  miss=u.get('prompt_cache_miss_tokens',u.get('prompt_tokens',0)-hit if hit is not None else None)
  if x['status']=='COMPLETED' and (hit is None or miss is None):raise ValueError('do not fabricate cache split')
  fee=(hit*.003+miss*.15+u['completion_tokens']*.6)/1e6 if x['status']=='COMPLETED' else None
  requests.append(dict(channel=ch,request_id=x['request_id'],status=x['status'],at_utc=dt.isoformat(),model=x.get('model'),usage=u,estimated_usd=fee,invoice_known=False,request_sha256=x['request_sha256'],input_upper=x['conservative_input_token_upper']))
 relevant=[x for x in requests if x['channel']==ch]
 channels[ch]=dict(requests=len(relevant),completed=sum(x['status']=='COMPLETED' for x in relevant),tokens=sum(x['usage'].get('total_tokens',0) for x in relevant),estimated_usd=sum(x['estimated_usd'] or 0 for x in relevant),unknown=[x['request_id'] for x in relevant if x['status']=='UNKNOWN'],worker_milliseconds=sum(x['payload'].get('tool_milliseconds',0) for x in ledger if x['kind']=='SETTLED'))
results=[]
for i,t in enumerate(tasks):
 v=read(r/'branches'/t['task_id']/'F'/'workflow.json');reqs=[x for x in requests if x['channel']=='solve' and x['request_id'].startswith('F/'+t['task_id']+'/')]
 results.append(dict(order=i+1,task_id=t['task_id'],batch=i//5+1,status=v['status'],public_pass=bool(v.get('selected')),stages=[dict(stage=x['stage'],status=x.get('public_feedback',{}).get('status'),blocked=x.get('blocked')) for x in v['events']],requests=len(reqs),tokens=sum(x['usage'].get('total_tokens',0) for x in reqs),estimated_usd=sum(x['estimated_usd'] or 0 for x in reqs),budget=v['budget'],hook_events=v.get('hook_events',[]),routing=v.get('routing_events',[])))
batches=[]
for i in range(4):
 rr=results[i*5:i*5+5];ids={x['task_id'] for x in rr}
 batches.append(dict(batch=i+1,task_ids=[x['task_id'] for x in rr],public_pass=sum(x['public_pass'] for x in rr),new_failure_events=sum(x['task_id'] in ids for x in facts),new_failure_tasks=len({x['task_id'] for x in facts if x['task_id'] in ids}),solve_requests=sum(x['requests'] for x in rr),tokens=sum(x['tokens'] for x in rr),estimated_usd=sum(x['estimated_usd'] for x in rr)))
hypotheses={x['payload']['hypothesis_id']:x['payload'] for x in hr if x['kind']=='HYPOTHESIS_VERSION'}
state=read(r/'state.json');summary=dict(run_id=p['run_id'],protocol_hash=p['protocol_hash'],start_utc=datetime.datetime.fromtimestamp(stream[0]['at'],datetime.timezone.utc).isoformat(),end_utc=datetime.datetime.fromtimestamp(stream[-1]['at'],datetime.timezone.utc).isoformat(),wall_seconds=stream[-1]['at']-stream[0]['at'],locked=locked,tasks=len(results),public_pass=sum(x['public_pass'] for x in results),failure_events=len(facts),failure_tasks=len({x['task_id'] for x in facts}),symptom_groups=len(hypotheses),learning_jobs=sum(x['kind']=='JOB_STARTED' for x in hr),operator_events=len(registry),actual_operator_uses=sum(len(x['hook_events']) for x in results),channels=channels,requests=sum(x['requests'] for x in channels.values()),tokens=sum(x['tokens'] for x in channels.values()),estimated_usd=sum(x['estimated_usd'] for x in channels.values()),persistent_budgets=state['budgets'],source_dependencies_unchanged=True,private_final_tests_read=False)
for name,value in [('summary',summary),('tasks',results),('batches',batches),('requests',requests),('failure_facts',facts),('hypothesis_history',hr),('operator_history',registry)]:e.write(out/(name+'.json'),value)
e.write(out/'raw_manifest.json',{str(f.relative_to(r)):e.sha(f) for f in sorted(r.rglob('*')) if f.is_file()})
print(json.dumps(summary,ensure_ascii=False,indent=2))
