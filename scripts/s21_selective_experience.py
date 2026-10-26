"""Zero-API replay of one manually formulated, public-evidence-backed hypothesis."""
import pathlib,json,time,hashlib,sys
from s21_audit import collect,ORDER,ROOT,OUT
from failure_evo import selective_experience as s
from failure_evo.contracts import atomic_json,fingerprint


def load_source(row):
 p=json.loads((ROOT/row['packet_ref']).read_text());root=ROOT/'runs'/f"s20_taco80_{row['arm'].lower()}_20261025_01"
 fact=next(json.loads(l)['payload'] for l in (root/f"evidence_{row['arm']}.jsonl").read_text().splitlines() if json.loads(l)['payload'].get('event_id')==row['event_id'])
 return dict(packet=p,fact=fact)


def main():
 audit=json.loads((OUT/'audit.json').read_text());rows=audit['events'];byid={x['event_id']:x for x in rows}
 source=next(x for x in rows if x['arm']=='M' and x['task_id']=='s19g_taco-train-s00-r0236' and x['repeat_opportunity'])
 refs=[source['event_id'],*source['prior_same_signature']];catalog={i:load_source(byid[i]) for i in refs}
 stamp=OUT/'replay_clock.json'
 if not stamp.exists():atomic_json(stamp,dict(card_authored_at=time.time(),meaning='actual S21 authorship; not backdated to source observations'))
 now=json.loads(stamp.read_text())['card_authored_at']
 card=s.seal_card(dict(experience_id='unchanged-public-retry-v1',origin='HUMAN_HYPOTHESIS',source_refs=[s.source_ref(**catalog[i]) for i in sorted(catalog)],observed_failure_pattern='Earlier repair-stage checkpoints expose identical code and identical public feedback; root cause and unseen raw response remain UNKNOWN.',applicability_conditions=dict(candidate_state='STRUCTURAL_PASS',repeat_same_program_feedback=True,remaining_calls_min=2),proposed_intervention=dict(kind='LEGAL_ACTION_SWITCH',action='REGENERATE_FRESH',guidance=''),expected_local_effect='Test whether omitting the unchanged failed implementation avoids another identical retry; no observed benefit asserted.',refusal_conditions=['no earlier identical public checkpoint','same source task/lineage','unknown evaluator','illegal or exhausted action','insufficient/contradictory evidence'],stop_conditions=['public pass','unknown request','budget limit','source provenance invalid'],evidence_level='OBSERVED_PATTERN',uncertainty='Manually proposed from two same-task public observations, not automatically learned. Fresh generation can lose useful partial work. No conditional paired benefit is known.',available_from=now))
 atomic_json(OUT/'experience_card.json',card);replay=[]
 for row in rows:
  p=load_source(row)['packet'];history=[dict(packet=load_source(z)['packet'],observed_at=z['observed_at']) for z in rows if z['arm']==row['arm'] and z['task_id']==row['task_id'] and ORDER[z['stage']]<ORDER[row['stage']] and z['observed_at']<=row['observed_at']]
  # Replay is evaluated now. Original-cutoff eligibility is a separate audit,
  # since this manually authored card did not exist during S20.
  state=s.snapshot(p,observed_at=now,history=history)
  old=s.snapshot(p,observed_at=row['observed_at'],history=history)
  historical=s.recommend(old,[card],enabled=True,source_catalog=catalog)
  decision=s.recommend(state,[card],enabled=True,source_catalog=catalog)
  conservative=s.recommend(state,[card],enabled=False,source_catalog=catalog)
  assert conservative['proposal'] is None
  wire=None;error=None
  try:
   normal,transparent=s.prepare_view(state,decision);preview,wire=s.prepare_view(state,decision,offline_proposal=True)
   assert not transparent['request_changed']
  except Exception as exc:error=type(exc).__name__+':'+str(exc)
  replay.append(dict(event_id=row['event_id'],task_id=row['task_id'],arm=row['arm'],historical_cutoff=row['observed_at'],historical_recommendation=historical,s21_replay_cutoff=now,decision=decision,wire_audit=wire,preflight_error=error))
 atomic_json(OUT/'replay.json',replay)
 summary=dict(new_api_calls=0,rows=len(replay),shadow_proposals=sum(bool(x['decision']['proposal']) for x in replay),distinct_action_previews=sum(bool(x['wire_audit'] and x['wire_audit']['action_changed']) for x in replay),distinct_request_previews=sum(bool(x['wire_audit'] and x['wire_audit']['request_changed']) for x in replay),preflight_rejections=sum(bool(x['preflight_error']) for x in replay),actual_interventions=0,historical_card_available_matches=sum(bool(x['historical_recommendation']['proposal']) for x in replay),interpretation='retrospective development preview; card authored now; no historical online reuse')
 atomic_json(OUT/'replay_summary.json',summary);print(summary)
if __name__=='__main__':main()
