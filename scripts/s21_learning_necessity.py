"""Bounded read-only R/S ablation. No sender, learning, Worker, or sealed inputs."""
import copy,hashlib,json,pathlib
from s21_audit import ROOT,ORDER,OUT as OLD
from s21_selective_experience import load_source
from failure_evo import selective_experience as s
from failure_evo.contracts import atomic_json,fingerprint,strict_feedback,PublicTaskView
from failure_evo.learning_evidence_bundle import check_packet,checkpoint_budget
from failure_evo.repair_choice_v2 import observation,eligible_actions,generic_choice
from failure_evo.repair_choice import action_messages
from failure_evo.workflow_protocol_v2 import prepare
OUT=ROOT/'reports/s21_learning_necessity_v1'


def local_rule(packet,history,cutoff,adjacent=False):
    """R has no card/catalog parameter. Only same-task observed public prefix."""
    check_packet(packet);s.finite(cutoff);prior=[]
    for h in history:
        p=check_packet(h['packet']);s.finite(h['observed_at'])
        if p['task_id']!=packet['task_id'] or h['observed_at']>cutoff or ORDER[p['stage']]>=ORDER[packet['stage']]:raise ValueError('invalid local prefix')
        prior.append(p)
    if adjacent and prior:prior=[max(prior,key=lambda p:ORDER[p['stage']])]
    signature=lambda p:fingerprint([p['candidate_sha256'],p['feedback']])
    same=[p['event_id'] for p in prior if signature(p)==signature(packet)]
    b=checkpoint_budget(packet);fb=strict_feedback(packet['feedback']);g=generic_choice(packet['code'],fb,b)
    o=observation(packet['code'],fb,b);legal=eligible_actions(packet['code'],fb,b)
    trigger=bool(same and o['candidate_state']=='STRUCTURAL_PASS' and g!='REGENERATE_FRESH' and 'REGENERATE_FRESH' in legal)
    return dict(action='REGENERATE_FRESH' if trigger else g,trigger=trigger,generic=g,matching_local_events=sorted(same),uses_cross_task_history=False)


def main():
    files={}
    def read(p):
        p=ROOT/p if not pathlib.Path(p).is_absolute() else pathlib.Path(p)
        files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
        return json.loads(p.read_text())
    audit=read(OLD/'audit.json');rows=audit['events'];byid={x['event_id']:x for x in rows}
    oldhash=read(OLD/'input_hashes.json')
    for p,h in oldhash.items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
        files[p]=h
    card=read(OLD/'experience_card.json');catalog={r['event_id']:load_source(byid[r['event_id']]) for r in card['source_refs']}
    # Validly resealed non-executable prose change; no fake facts or permissions.
    text_card={k:v for k,v in copy.deepcopy(card).items() if k not in ('version','card_hash','provenance_hash')}
    text_card['observed_failure_pattern']='Text ablation: no historical explanation is supplied.'
    text_card['expected_local_effect']='Unknown; no effect claimed.'
    text_card['uncertainty']='Ablation only, not a new experience.'
    text_card=s.seal_card(text_card)
    replay=[]
    for row in rows:
        p=load_source(row)['packet']
        history=[dict(packet=load_source(x)['packet'],observed_at=x['observed_at']) for x in rows if x['arm']==row['arm'] and x['task_id']==row['task_id'] and ORDER[x['stage']]<ORDER[row['stage']] and x['observed_at']<=row['observed_at']]
        state=s.snapshot(p,observed_at=card['available_from'],history=history)
        d=s.recommend(state,[card],enabled=True,source_catalog=catalog)
        empty=s.recommend(state,[],enabled=True,source_catalog={})
        prose=s.recommend(state,[text_card],enabled=True,source_catalog=catalog)
        r=local_rule(p,history,row['observed_at']);adj=local_rule(p,history,row['observed_at'],True)
        sa=d['proposal']['action'] if d['proposal'] else d['generic_action']
        assert d['proposal']==prose['proposal']
        wire={}
        try:
            g,_=s.prepare_view(state,d);sp,_=s.prepare_view(state,d,offline_proposal=True)
            rp=prepare(action_messages(r['action'],PublicTaskView.project(p['task_public']),p['code'],strict_feedback(p['feedback']))) if r['trigger'] else g
            wire=dict(G=g.sha256,R=rp.sha256,S=sp.sha256,R_S_equal=rp.wire==sp.wire)
        except Exception as exc:wire=dict(preflight_error=type(exc).__name__+':'+str(exc))
        replay.append(dict(event_id=row['event_id'],task_id=row['task_id'],arm=row['arm'],stage=row['stage'],R=r,R_adjacent=adj,S_action=sa,S_proposal=d['proposal'],S_rejections=d['conditions'],S_empty_action=empty['generic_action'],S_prose_ablation_action=sa,R_S_different=r['action']!=sa,wire=wire,actual_interventions=0))
    differences=[x for x in replay if x['R_S_different']]
    plan=read(OLD/'experiment_draft.json');draft_ids={x['event_id'] for x in plan['samples']}
    summary=dict(events=len(rows),original_tasks=len({x['task_id'] for x in rows}),R_triggers=sum(x['R']['trigger'] for x in replay),S_shadow_triggers=sum(bool(x['S_proposal']) for x in replay),R_S_same=sum(not x['R_S_different'] for x in replay),R_S_different=len(differences),S_only_triggers=sum(bool(x['S_proposal']) and not x['R']['trigger'] for x in replay),R_only_triggers=sum(x['R']['trigger'] and not x['S_proposal'] for x in replay),R_adjacent_differences=sum(x['R']['action']!=x['R_adjacent']['action'] for x in replay),empty_card_changes_vs_S=sum(x['S_empty_action']!=x['S_action'] for x in replay),prose_ablation_changes=0,wire_comparable=sum('R_S_equal' in x['wire'] for x in replay),wire_equal=sum(x['wire'].get('R_S_equal',False) for x in replay),preflight_blocked=sum('preflight_error' in x['wire'] for x in replay),draft_three_R_S_differences=sum(x['R_S_different'] for x in replay if x['event_id'] in draft_ids),benefit_supported_differences=0,actual_interventions=0,new_api_calls=0)
    # Later public observations are audit outcomes only, never selector inputs.
    followups=[]
    for row in rows:
        if not row['repeat_opportunity']:continue
        path=ROOT/'runs'/f"s20_taco80_{row['arm'].lower()}_20261025_01"/'branches'/row['task_id']/row['arm']/'workflow.json'
        data=read(path)
        later=[dict(stage=e['stage'],status=e['public_feedback']['status'],code_sha256=e.get('code_sha256'),blocked=e.get('blocked')) for e in data['events'] if e.get('stage') in ORDER and ORDER[e['stage']]>ORDER[row['stage']] and 'public_feedback' in e]
        followups.append(dict(event_id=row['event_id'],task_id=row['task_id'],arm=row['arm'],later_public_only=later,paired_alternative_exists=False,interpretation='Later observational native path, not an input to R/S and not a causal counterfactual.'))
    pairs=[]
    for run in ['s17b_pairs_20261023_01','s18p2_pairs_20261023_01']:
        data=read(ROOT/'runs'/run/'summary.json')
        # Only public results/costs are projected; review/gold outcomes excluded.
        for task in sorted({k.split('/')[0] for k in data['arms']}):
            arms={a:{k:data['arms'][task+'/'+a][k] for k in ('public_pass','calls','tokens','estimated_usd')} for a in ['A','B']}
            pairs.append(dict(run=run,task=task,public_outcomes=arms,repeat_condition_at_checkpoint='NOT_ESTABLISHED_IN_SUMMARY',opposite_preference_supported=bool(arms['A']['public_pass'] and not arms['B']['public_pass']),request_confound='Existing B omits source and actual/exception feedback',eligible_for_learning_boundary=False))
    result=dict(summary=summary,events=replay,differences=differences)
    atomic_json(OUT/'rs_replay.json',result)
    atomic_json(OUT/'public_opportunity_search.json',dict(scope='same 175 events; 3 repeated episodes later public path; 5 previously completed A/B task pairs',followups=followups,existing_pairs=pairs,new_supported_history_dependent_boundaries=0,selection_uses_future_outcomes=False))
    atomic_json(OUT/'input_hashes.json',files)
    for p,h in files.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    print(json.dumps(summary,indent=2));print('difference',[(x['task_id'],x['arm'],x['S_rejections'][0]['rejections']) for x in differences]);print('followups',followups)
if __name__=='__main__':main()
