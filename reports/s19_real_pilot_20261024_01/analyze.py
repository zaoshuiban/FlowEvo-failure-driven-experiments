"""Post-run read-only analysis; never invokes providers, judges or hidden tests."""
import json,sys,collections,datetime,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import run_workflow_v2 as e
PRE=Path(__file__).parent;RUN=ROOT/'runs/s19_real_pilot_20261024_01'
def rows(path):return [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
plan=e.read(PRE/'plan.json');tasks=e.read(PRE/'tasks.json');log=rows(RUN/'stream.jsonl');hrows=rows(RUN/'hypotheses.jsonl');registry=rows(RUN/'rule_registry.jsonl')
channels={};request_records=[]
for ch in ('solve','learning','validation'):
 budget=e.PersistentBudget(RUN/(ch+'_budget.jsonl'),run_id=plan['run_id']+'-'+ch,protocol_hash=plan['protocol_hash'],**plan['budgets'][ch]);snapshot=budget.snapshot()
 journal=rows(RUN/(ch+'_budget.jsonl'));reserved={r['payload']['request_id']:r for r in journal if r['kind']=='RESERVED'}
 audit=e.read(RUN/(ch+'_requests.json')) if (RUN/(ch+'_requests.json')).exists() else []
 stats=dict(completed=0,input_tokens=0,output_tokens=0,total_tokens=0,reasoning_tokens=0,reasoning_tokens_reported_requests=0,cache_hit_tokens=0,cache_miss_tokens=0,offpeak_estimate_usd=0.,peak_upper_estimate_usd=0.,unknown_or_not_sent=[])
 for r in audit:
  if r['status']!='COMPLETED':stats['unknown_or_not_sent'].append(dict(request_id=r['request_id'],status=r['status'],reason=r.get('reason')));continue
  raw=r['raw_response'];u=raw['usage'];hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit)
  if hit+miss!=u['prompt_tokens']:raise ValueError('cache count mismatch')
  off=(hit*.003+miss*.15+u['completion_tokens']*.6)/1e6;peak=(hit*.006+miss*.3+u['completion_tokens']*1.2)/1e6
  stamp=reserved[r['request_id']]['at'];when=datetime.datetime.fromtimestamp(stamp,datetime.timezone.utc)
  # This run is on a UTC Saturday. No holiday inference needed.
  if when.weekday()<5:raise ValueError('review pricing window before using weekend estimate')
  reason=u.get('completion_tokens_details',{}).get('reasoning_tokens')
  stats['reasoning_tokens_reported_requests']+=reason is not None
  rec=dict(channel=ch,request_id=r['request_id'],capability=reserved[r['request_id']]['payload']['capability'],request_sha256=r['request_sha256'],actual_model=raw['model'],response_id=raw.get('id'),request_at_utc=when.isoformat(),finish_reason=raw['choices'][0].get('finish_reason'),input_tokens=u['prompt_tokens'],output_tokens=u['completion_tokens'],total_tokens=u['total_tokens'],reasoning_tokens=reason,cache_hit_tokens=hit,cache_miss_tokens=miss,cache_split_reported='prompt_cache_hit_tokens' in u,offpeak_estimate_usd=off,peak_upper_estimate_usd=peak)
  request_records.append(rec);stats['completed']+=1
  for key in ('input_tokens','output_tokens','total_tokens','reasoning_tokens','cache_hit_tokens','cache_miss_tokens','offpeak_estimate_usd','peak_upper_estimate_usd'):stats[key]+=rec[key] if rec[key] is not None else 0
 stats['persistent_budget']=snapshot;channels[ch]=stats
facts=[r['payload'] for r in rows(RUN/'evidence_F.jsonl') if r['kind']=='FAILURE_FACT']
hypotheses={r['payload']['hypothesis_id']:r['payload'] for r in hrows if r['kind']=='HYPOTHESIS_VERSION'}
operators={r['candidate_id']:r['state'] for r in registry}
per_task=[]
for n,t in enumerate(tasks,1):
 path=RUN/'branches'/t['task_id']/'F/workflow.json'
 wf=e.read(path) if path.exists() else None
 req=[r for r in request_records if r['request_id'].startswith('F/'+t['task_id']+'/')]
 trajectory=[]
 if wf:
  for event in wf['events']:
   if 'code' not in event:trajectory.append({k:event.get(k) for k in ('stage','error','request_state','diagnosis')});continue
   ledger=next((x for x in wf.get('candidate_ledger',[]) if x['stage']==event['stage'] and x['code_sha256']==event['code_sha256']),{})
   checks=ledger.get('audited_case_outcomes',{})
   trajectory.append(dict(stage=event['stage'],candidate_sha256=event['code_sha256'],code_bytes=len(event['code'].encode()),public_result=event['public_feedback']['status'],public_passed=sum(checks.values()) if checks else None,public_evaluated=len(checks),checkpoint_budget=event['checkpoint_budget']))
 per_task.append(dict(index=n,task_id=t['task_id'],batch=1+(n-1)//5,completed=any(r['kind']=='TASK_FINALIZED' and r['payload']['task_id']==t['task_id'] for r in log),status=wf['status'] if wf else 'NOT_COMPLETED',selected=wf['selected'] if wf else None,trajectory=trajectory,model_calls=len(req),tokens=sum(r['total_tokens'] for r in req),estimated_usd=sum(r['offpeak_estimate_usd'] for r in req),peak_estimated_usd=sum(r['peak_upper_estimate_usd'] for r in req),tool_budget=wf['budget'] if wf else None,hooks=wf.get('hook_events',[]) if wf else [],routing=wf.get('routing_events',[]) if wf else []))
assessments=[dict(file=str(p.relative_to(ROOT)),report=e.read(p)) for p in sorted((RUN/'assessments').glob('*.json'))]
eligible_ids={i for h in hypotheses.values() if h['applicable_actions'] for i in h['source_evidence_ids']}
by_event={f['event_id']:f for f in facts}
funnel=dict(tasks_planned=10,tasks_completed=sum(t['completed'] for t in per_task),public_accepted=sum(t['status']=='PUBLIC_ACCEPTED' for t in per_task),failure_events=len(facts),failure_tasks=len({f['task_id'] for f in facts}),symptom_groups=len(hypotheses),groups_with_legal_actions=sum(bool(h['applicable_actions']) for h in hypotheses.values()),eligible_events=len(eligible_ids),eligible_tasks=len({by_event[i]['task_id'] for i in eligible_ids}),groups_with_multiple_tasks=sum(h['independent_task_count']>1 for h in hypotheses.values()),hypotheses_with_model_content=sum(bool(h['content']) for h in hypotheses.values()),distinct_rules=len(operators),source_effective_assessments=sum(x['report'].get('source_success',False) for x in assessments),authorized_versions=sum(any(r.get('event')=='BOUNDED_TRIAL_AUTHORIZED' and r['candidate_id']==k for r in registry) for k in operators),actual_trials=sum(r.get('event')=='TRIAL_RESULT' for r in registry),changed_native_actions=sum(bool(r.get('result',{}).get('changed_generic_action')) for r in registry if r.get('event')=='TRIAL_RESULT'),suspended_versions=sum(v['permission']=='suspended' for v in operators.values()))
summary=dict(run_id=plan['run_id'],protocol_hash=plan['protocol_hash'],git_commit=plan['git_commit'],online_locked=any(r['kind']=='ONLINE_LOCKED' for r in log),funnel=funnel,per_task=per_task,channels=channels,total=dict(model_calls=sum(x['completed'] for x in channels.values()),tokens=sum(x['total_tokens'] for x in channels.values()),estimated_usd=sum(x['offpeak_estimate_usd'] for x in channels.values()),peak_estimated_usd=sum(x['peak_upper_estimate_usd'] for x in channels.values()),persistent_reserved_usd=sum(x['persistent_budget']['charged_or_reserved_cost_microusd'] for x in channels.values())/1e6,worker_tools=sum(x['persistent_budget']['tool_calls'] for x in channels.values()),worker_charged_seconds=sum(x['persistent_budget']['charged_or_reserved_tool_milliseconds'] for x in channels.values())/1000,unknown_requests=[k for x in channels.values() for k in x['persistent_budget']['unknown_or_pending_requests']],actual_invoice_usd=None),hypotheses=hypotheses,operators=operators,assessments=assessments,schedule=[r['payload'] for r in hrows if r['kind']=='SCHEDULE_DECISION'],jobs=[r for r in hrows if r['kind'].startswith('JOB_')],request_records=request_records,interpretation='Previously exposed development tasks; public checks only; no G/M causal comparison; no independent generalization claim')
e.write(RUN/'pilot_analysis.json',summary)
print(json.dumps(dict(online_locked=summary['online_locked'],funnel=funnel,total=summary['total'],channel_counts={k:v['completed'] for k,v in channels.items()}),ensure_ascii=False,indent=2))
