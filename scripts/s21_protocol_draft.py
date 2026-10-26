"""Freeze bounded development proposal, never send or read sealed evaluation data."""
import copy,json
from s21_audit import ROOT,OUT,ORDER
from s21_selective_experience import load_source
from failure_evo import selective_experience as s
from failure_evo.contracts import atomic_json,fingerprint,PublicTaskView,strict_feedback
from failure_evo.repair_choice import action_messages
from failure_evo.workflow_protocol_v2 import prepare


def main():
 a=json.loads((OUT/'audit.json').read_text());rows=a['events']
 target=next(x for x in rows if x['arm']=='G' and x['source_episode_ids'])
 controls=sorted((x for x in rows if x['arm']=='G' and x['task_id']!=target['task_id'] and x['observation']==target['observation'] and not x['prior_same_signature']),key=lambda x:(x['observed_at'],x['task_id'],x['event_id']))
 selected=[target];seen={target['task_id']}
 for x in controls:
  if x['task_id'] not in seen:selected.append(x);seen.add(x['task_id'])
  if len(selected)==3:break
 card=json.loads((OUT/'experience_card.json').read_text());byid={x['event_id']:x for x in rows}
 catalog={r['event_id']:load_source(byid[r['event_id']]) for r in card['source_refs']}
 advice='Read the input and output specification carefully. Return a complete executable Python program in one python fence. Check indexing, state updates and boundary conditions against the stated constraints. Do not special-case examples or merely suppress exceptions.'
 (OUT/'generic_advice.txt').write_text(advice+'\n')
 samples=[]
 for row in selected:
  p=load_source(row)['packet'];history=[dict(packet=load_source(x)['packet'],observed_at=x['observed_at']) for x in rows if x['arm']==row['arm'] and x['task_id']==row['task_id'] and ORDER[x['stage']]<ORDER[row['stage']] and x['observed_at']<=row['observed_at']]
  state=s.snapshot(p,observed_at=card['available_from'],history=history);d=s.recommend(state,[card],enabled=True,source_catalog=catalog)
  records={}
  for arm in ['G','P','S','A','B']:
   try:
    generic,_=s.prepare_view(state,d)
    if arm=='G':req=generic
    elif arm=='P':
     msgs=copy.deepcopy(generic.body['messages']);msgs[1]['content']+='\nGeneral programming advice:\n'+advice;req=prepare(msgs)
    elif arm=='S':req,_=s.prepare_view(state,d,offline_proposal=True)
    else:req=prepare(action_messages('REPAIR_EXISTING' if arm=='A' else 'REGENERATE_FRESH',PublicTaskView.project(p['task_public']),p['code'],strict_feedback(p['feedback'])))
    records[arm]=dict(sha256=req.sha256,input_upper=req.input_upper,output_upper=req.output_upper,preflight='PASS',wire=req.body)
   except Exception as exc:records[arm]=dict(preflight='NOT_SENT',error=type(exc).__name__+':'+str(exc))
  if all(records[z]['preflight']=='PASS' for z in ('G','S','B')):
   assert records['S']['sha256']==records['B' if d['proposal'] else 'G']['sha256']
  samples.append(dict(event_id=row['event_id'],task_id=row['task_id'],stage=row['stage'],arm_of_historical_checkpoint=row['arm'],packet_ref=row['packet_ref'],packet_hash=row['packet_hash'],role='matched_development' if row==target else 'coarse_state_nonmatch_control',shadow_proposal=d['proposal'],requests=records))
 plan=dict(version='s21-bounded-development-draft-v1',status='DRAFT_NOT_AUTHORIZED_NOT_EXECUTABLE',selection='G first matching original; first two other G originals in observed-time/task/event order with same coarse state but no unchanged retry; no output-based selection',base_commit='86edbb90cd4e61c5a87722652bc0b453a2d3f42b',card_hash=card['card_hash'],generic_advice_hash=fingerprint(advice),samples=samples,arms=['G','P','S','A','B'],arm_order='G P S A B within each listed checkpoint',new_model_calls_this_stage=0,max_proposed_model_calls=15,max_calls_per_branch=1,input_upper_per_request=32768,output_upper_per_request=8192,max_reserved_tokens=614400,proposed_hard_usd=1.0,pricing_assumption='Scenario bound $1.20 per million for BOTH input/output, no cache discount; not a verified current quote. Refresh and bind authorized transport before any send.',scenario_upper_usd=.73728,tool_calls_upper=450,worker_wall_seconds_upper=3600,api_dollar_budget_excludes_local_compute=True,learning_calls=0,unresolved=['Development originals already exposed; only one matched original','Scorer/Worker dependency freeze and execution authorization required; sealed files not read now','Actual S execution requires separately reviewed bounded research executor; this module only previews','Fresh treatment omits code AND actual/exception feedback; tests request-package selection, not pure action','Provider tokens and lengths not matched; S switch may shorten source context; report rather than assume balance','Original success library/raw response metadata not reconstructed; common snapshot baseline is a new protocol'],stops=['unknown request','wire/hash mismatch','data contamination','Worker/evaluator fault','budget exhaustion'],no_performance_early_stop=True,no_resend=True)
 plan['protocol_hash']=fingerprint(plan);atomic_json(OUT/'experiment_draft.json',plan)
 print([(x['task_id'],{a:r['preflight'] for a,r in x['requests'].items()}) for x in samples]);print(plan['protocol_hash'])
if __name__=='__main__':main()
