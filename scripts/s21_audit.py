"""One bounded read-only S20 public-prefix audit. No provider, evaluator or sealed data."""
import json,pathlib,sys,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import fingerprint,strict_feedback,atomic_json
from failure_evo.learning_evidence_bundle import check_packet,checkpoint_budget
from failure_evo.repair_choice_v2 import observation,eligible_actions,generic_choice
ORDER={s:i for i,s in enumerate(('l1','l2a','l2b','l3','l4'))}
OUT=ROOT/'reports/s21_selective_experience_v1'

def collect():
 rows=[];files={}
 for arm in 'GMF':
  root=ROOT/'runs'/f's20_taco80_{arm.lower()}_20261025_01'
  path=root/f'evidence_{arm}.jsonl';files[str(path.relative_to(ROOT))]=__import__('hashlib').sha256(path.read_bytes()).hexdigest()
  facts={r['payload']['event_id']:r['payload'] for l in path.read_text().splitlines() if (r:=json.loads(l))['kind']=='FAILURE_FACT'}
  packets=[(p,check_packet(json.loads(p.read_text()))) for p in sorted((root/'public_packets').glob('*.json'))]
  prior=collections.defaultdict(list)
  for path,p in sorted(packets,key=lambda z:(facts[z[1]['event_id']]['observed_at'],z[1]['task_id'],ORDER[z[1]['stage']],z[1]['event_id'])):
   f=facts[p['event_id']];assert f['visibility']=='public' and not f['synthetic'];assert f['candidate_sha256']==p['candidate_sha256'];assert f['task_id']==p['task_id']
   files[str(path.relative_to(ROOT))]=__import__('hashlib').sha256(path.read_bytes()).hexdigest()
   b=checkpoint_budget(p);fb=strict_feedback(p['feedback']);o=observation(p['code'],fb,b);legal=list(eligible_actions(p['code'],fb,b));g=generic_choice(p['code'],fb,b)
   sig=fingerprint([p['candidate_sha256'],p['feedback']]);previous=[x for x in prior[p['task_id']] if ORDER[x['stage']]<ORDER[p['stage']] and x['observed_at']<=f['observed_at'] and x['public_signature']==sig]
   row=dict(event_id=p['event_id'],arm=arm,task_id=p['task_id'],stage=p['stage'],packet_ref=str(path.relative_to(ROOT)),packet_hash=fingerprint(p),candidate_sha256=p['candidate_sha256'],observed_at=f['observed_at'],available_from=f['available_from'],finish_reason=f['finish_reason'],observation=o,legal_actions=legal,generic_action=g,alternatives=[x for x in legal if x!=g],exception_classes=sorted({x['exception_class'] for x in p['feedback']['public_cases'] if x.get('exception_class')}),public_signature=sig,prior_same_signature=[x['event_id'] for x in previous],root_cause='UNKNOWN',chronology='stage order plus recorded time; task-finalized timestamps may be coalesced')
   row['repeat_opportunity']=bool(previous and o['candidate_state']=='STRUCTURAL_PASS' and g=='REPAIR_EXISTING' and 'REGENERATE_FRESH' in legal)
   prior[p['task_id']].append(row);rows.append(row)
 return rows,files

def main():
 rows,files=collect();episodes=[x for x in rows if x['repeat_opportunity']]
 for x in rows:
  sources=[s for s in episodes if s['task_id']!=x['task_id'] and s['available_from']<x['observed_at']]
  x['source_episode_ids']=[s['event_id'] for s in sources] if x['repeat_opportunity'] else []
  x['tags']=['INSUFFICIENT_EVIDENCE']
  if x['alternatives']:x['tags']+=['LEGAL_ALTERNATIVE_ONLY']
  if x['repeat_opportunity']:x['tags']+=['ACTIONABLE_CONDITION_IDENTIFIED','POTENTIAL_HARM']
  if x['source_episode_ids']:x['tags']+=['DISTINCT_INTERVENTION_POSSIBLE']
  else:x['tags']+=['NO_APPLICABLE_EXPERIENCE']
  x['paired_benefit_supported']=False
 summary=dict(events=len(rows),original_tasks=len({x['task_id'] for x in rows}),by_arm={a:dict(events=sum(x['arm']==a for x in rows),legal_alternative=sum(x['arm']==a and bool(x['alternatives']) for x in rows)) for a in 'GMF'},legal_alternative_events=sum(bool(x['alternatives']) for x in rows),observable_repeat_events=sum(x['repeat_opportunity'] for x in rows),cross_task_distinct_proposals=sum(bool(x['source_episode_ids']) for x in rows),paired_benefit_supported=0,potential_harm_candidates=sum(x['repeat_opportunity'] for x in rows),known_causal_regression_events=0,no_applicable_experience=sum(not x['source_episode_ids'] for x in rows),actual_interventions=0,new_api_calls=0,scope='exhaustive S20-A G/M/F saved public packets; same original across arms not independent; S17-S19 reviewed separately; not all historical events')
 collisions=[]
 for x in rows:
  if not x['source_episode_ids']:continue
  same=[z for z in rows if z['task_id']!=x['task_id'] and z['observation']==x['observation'] and not z['prior_same_signature']]
  collisions.append(dict(target=x['event_id'],coarse_state=x['observation'],counterexample_event_ids=[z['event_id'] for z in same],interpretation='same coarse state but no repeated identical program/feedback; not evidence of opposite optimal actions'))
 atomic_json(OUT/'audit.json',dict(summary=summary,events=rows,coarse_collisions=collisions));atomic_json(OUT/'input_hashes.json',files)
 print(json.dumps(summary,ensure_ascii=False));print('episodes',[(x['arm'],x['task_id'],x['stage'],x['source_episode_ids']) for x in rows if x['repeat_opportunity']])
if __name__=='__main__':main()
