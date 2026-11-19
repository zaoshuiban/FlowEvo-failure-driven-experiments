"""Offline receipt-based D3 reporting, never invokes candidates/models/environment."""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from analyze_alfworld_route_d2 import read, sha, digest, journal

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/alfworld_route_d3_online_20261119_01'
OUT=ROOT/'reports'/RUN.name
METRICS=['model_calls','prompt_tokens','completion_tokens','total_tokens','reference_usd','reserved_usd','environment_actions','worker_calls','worker_ms','wall_seconds']


def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def historical():
    rows=[]; sources={}; workers=0; worker_ms=0
    for run_name in ['alfworld_route_d_20261118_01','alfworld_route_d1_pro_compilation_20261118_01']:
        root=ROOT/'runs'/run_name; reqs={}; settled={}
        for ledger in root.glob('budget*.jsonl'):
            sources[str(ledger)]=sha(ledger)
            for e in journal(ledger):
                p=e['payload']
                if e['kind']=='RESERVED':reqs[p['request_id']]=p
                if e['kind']=='SETTLED':settled[p['request_id']]=p
        for p in sorted((root/'requests').rglob('response.json')):
            raw=read(p); u=raw['usage']; rel=str(p.parent.relative_to(root/'requests'))
            # Request identities in D1 are its version label, in Route D full path.
            reserve=reqs[rel]
            assert settled[rel]['tokens']==u['total_tokens']
            pro='pro' in raw['model']; inp,out=(1.32,3.96) if pro else (.30,1.20)
            stage='D1_generation_revision' if 'd1_' in run_name else ('D_recovery_discovery' if rel.startswith('P1/') else 'D_compilation_including_failed_submissions')
            rows.append(dict(run=run_name,request_id=rel,stage=stage,model=raw['model'],finish_reason=raw['choices'][0]['finish_reason'],
                prompt_tokens=u['prompt_tokens'],completion_tokens=u['completion_tokens'],total_tokens=u['total_tokens'],
                reference_usd=(u['prompt_tokens']*inp+u['completion_tokens']*out)/1e6,reserved_usd=reserve['cost_upper_microusd']/1e6,response_sha256=sha(p)))
        for p in root.rglob('*.json'):
            if 'workers' in p.parts or p.name=='exclusion_worker.json':
                d=read(p)
                if 'milliseconds' in d and 'raw' in d:workers+=1;worker_ms+=d['milliseconds']
    totals={k:sum(r[k] for r in rows) for k in ['prompt_tokens','completion_tokens','total_tokens','reference_usd','reserved_usd']}
    totals.update(model_calls=len(rows),worker_calls=workers,worker_ms=worker_ms)
    result=dict(scope='Recorded Route D recovery discovery + all Route D compilation requests (including failed/truncated) + D1 v1/v2. No request rerun. Original 120-game data collection and earlier routes excluded as prior research expenditure.',
        rows=rows,totals=totals,ledger_hashes=sources,actual_provider_bill_usd=None,
        earlier_research_cost='Not included; original historical failure collection, earlier route exploration, D2 evaluation separate. Allocation to candidate not identified.',
        amortization='Only recorded incremental acquisition quote is known; provider bill and worker dollar price unknown. No total-cost payback claim.')
    save('Historical_Costs.json',result)
    return result


def main():
    selection=read(RUN/'selection.private.json'); protocol=read(RUN/'protocol.json')
    budget=journal(RUN/'budget.jsonl'); env=journal(RUN/'environment_actions.jsonl'); journal(RUN/'events.jsonl')
    reservations={r['payload']['request_id']:r['payload'] for r in budget if r['kind']=='RESERVED'}
    settled={r['payload']['request_id']:r['payload'] for r in budget if r['kind']=='SETTLED'}
    costs=defaultdict(Counter); request_rows=[]
    for rid,res in reservations.items():
        if res['kind']!='model':continue
        parts=rid.split('/');key='/'.join(parts[:3]); p=RUN/'requests'/rid/'response.json'
        row=dict(request_id=rid,branch=key,reserved_usd=res['cost_upper_microusd']/1e6,model_calls=1)
        if p.exists():
            raw=read(p); u=raw['usage']
            for k in ['prompt_tokens','completion_tokens','total_tokens']:row[k]=u[k]
            row['reference_usd']=(u['prompt_tokens']*.30+u['completion_tokens']*1.20)/1e6
            assert settled[rid]['tokens']==u['total_tokens']
        else:row['usage_unknown']=True
        costs[key].update({k:v for k,v in row.items() if isinstance(v,(int,float))})
        request_rows.append(row)
    rows=[]; details=[]; complete_indices=[]
    for i,task in enumerate(selection['tasks']):
        arms=[]
        for arm in 'GHF':
            folder=RUN/f'pairs/{i:02d}/{arm}'; p=folder/'result.json'
            if not p.exists():continue
            result=read(p); key=f'pairs/{i:02d}/{arm}'
            row=dict(game_index=i,task_id=task['task_id'],group=task['group'],scene=task['scene'],seen_scene=selection['seen_scene'][i],arm=arm,won=result['won'],status=result['status'],
                environment_actions=len(result['steps']),wall_seconds=result['wall_seconds'],triggered=result['triggered'],entry_anchor=result['entry_anchor'],entry_reason=result['entry_reason'],
                completion_mode=result['completion_mode'],policy_actions=result['policy_actions'],policy_errors=result['policy_errors'],
                model_calls=0,prompt_tokens=0,completion_tokens=0,total_tokens=0,reference_usd=0,reserved_usd=0,
                worker_calls=0,worker_ms=0,illegal_executed=0,illegal_model_intents=0,missing_act_line=0,parser_changed=0,parser_nonexact=0,parser_first_legal_fallback=0,illegal_skill_proposals=0,
                retakes_placed_target=0,public_placement_undo=0,nothing_happens=0,navigation_revisits=0,repeated_navigation_same_receipt=0)
            row.update(costs[key])
            workers=[read(w) for w in (folder/'workers').glob('*.json')]
            row['worker_calls']=len(workers);row['worker_ms']=sum(w['milliseconds'] for w in workers)
            row['illegal_skill_proposals']=sum(w['result'].get('reason')=='ACTION_NOT_ADMISSIBLE' for w in workers)
            phase=defaultdict(Counter);events=[];placed={};visited=set(); navigation_receipts=set()
            goal=read(folder/'start.private.json')['goal'];obj=re.search(r'\btwo\s+([a-z]+)',goal.lower());dest=re.search(r'\b(?:in|on)\s+(?:a |the )?([a-z]+)\s*\.?$',goal.lower())
            row['goal']=goal
            for rec in result['records']:
                ph=phase[rec['phase']];ph['environment_actions']+=1
                fb=rec['feedback'];action=fb['action'];observation=fb['observation']
                row['illegal_executed']+=action not in rec['legal_before']
                if rec['parse']:
                    row['illegal_model_intents']+=rec['parse']['stated'] is not None and rec['parse']['stated_is_legal'] is False
                    row['missing_act_line']+=rec['parse']['stated'] is None
                    row['parser_nonexact']+=rec['parse']['stage']!='ACT_EXACT'
                    row['parser_first_legal_fallback']+=rec['parse']['stage']=='FIRST_ADMISSIBLE_FALLBACK'
                    row['parser_changed']+=rec['parse']['different']
                    u=rec['request']['usage'];ph['model_calls']+=1
                    ph['prompt_tokens']+=u['input_tokens'];ph['completion_tokens']+=u['output_tokens']
                    ph['reference_usd']+=(u['input_tokens']*.30+u['output_tokens']*1.20)/1e6
                row['nothing_happens']+='nothing happens' in observation.lower()
                if action.startswith('go to '):
                    location=action[6:];row['navigation_revisits']+=location in visited;visited.add(location)
                    row['repeated_navigation_same_receipt']+=(action,observation) in navigation_receipts
                    navigation_receipts.add((action,observation))
                move=re.fullmatch(r'You move the (.+?) to the (.+?)\.',observation)
                take=re.fullmatch(r'You pick up the (.+?) from the (.+?)\.',observation)
                if move and obj and dest and obj[1] in (move[1].rsplit(' ',1)[0],move[1].rsplit(' ',1)[0]+'s') and move[2].rsplit(' ',1)[0]==dest[1]:placed[move[1]]=move[2]
                if take and placed.get(take[1])==take[2]:
                    row['retakes_placed_target']+=1;row['public_placement_undo']+=1
                    events.append(dict(step=rec['step'],actor=rec['actor'],phase=rec['phase'],action=action,observation=observation))
                    del placed[take[1]]
            for w in workers:phase['skill']['worker_calls']+=1;phase['skill']['worker_ms']+=w['milliseconds']
            rows.append(row);arms.append(arm)
            details.append(dict(game_index=i,arm=arm,phases=dict(phase),public_undo_events=events,start_sha256=result['start_sha256']))
        if len(arms)==3:complete_indices.append(i)
    summaries={}
    for arm in 'GHF':
        subset=[r for r in rows if r['arm']==arm]
        summaries[arm]=dict(completed_runs=len(subset),won=sum(r['won'] for r in subset),**{k:sum(r[k] for r in subset) for k in METRICS},
            completion_modes=dict(Counter(r['completion_mode'] for r in subset)),triggered=sum(r['triggered'] for r in subset),
            illegal_executed=sum(r['illegal_executed'] for r in subset),illegal_model_intents=sum(r['illegal_model_intents'] for r in subset),missing_act_line=sum(r['missing_act_line'] for r in subset),parser_changed=sum(r['parser_changed'] for r in subset),parser_nonexact=sum(r['parser_nonexact'] for r in subset),parser_first_legal_fallback=sum(r['parser_first_legal_fallback'] for r in subset),
            retakes_placed_target=sum(r['retakes_placed_target'] for r in subset),navigation_revisits=sum(r['navigation_revisits'] for r in subset),nothing_happens=sum(r['nothing_happens'] for r in subset))
    by={(r['game_index'],r['arm']):r for r in rows}; comparisons={}
    for treatment,control in [('F','H'),('H','G'),('F','G')]:
        ids=[i for i in range(len(selection['tasks'])) if (i,treatment) in by and (i,control) in by]
        joint=[i for i in ids if by[i,treatment]['won'] and by[i,control]['won']]
        wins=[i for i in ids if by[i,treatment]['won'] and not by[i,control]['won']]
        losses=[i for i in ids if not by[i,treatment]['won'] and by[i,control]['won']]
        comparisons[treatment+'_vs_'+control]=dict(paired_games=len(ids),treatment_only_win=wins,control_only_win=losses,
            all_games_delta={k:sum(by[i,treatment][k]-by[i,control][k] for i in ids) for k in METRICS},
            jointly_successful_games=joint,joint_success_n=len(joint),joint_success_delta={k:sum(by[i,treatment][k]-by[i,control][k] for i in joint) for k in METRICS})
    allcost=Counter()
    for c in costs.values():allcost.update(c)
    worker_receipts=list(RUN.glob('pairs/*/*/workers/*.json'))+list(RUN.glob('fixtures/*/worker.json'))
    starts=[r for r in env if r['kind']=='STARTED'];returns=[r for r in env if r['kind']=='RETURNED']
    audit=dict(frozen_files_unchanged=all(sha(Path(p))==h for p,h in protocol['files'].items()),
        protocol_document_unchanged=sha(OUT/'Protocol.md')==read(RUN/'Preflight.json')['protocol_md_sha256'],
        protocol_json_unchanged=sha(RUN/'protocol.json')==read(RUN/'Preflight.json')['protocol_json_sha256'],
        all_requests_settled=set(reservations)==set(settled),no_unknown=not any(r['kind']=='UNKNOWN' for r in budget),
        all_environment_returned=len(starts)==len(returns) and {r['payload']['number'] for r in starts}=={r['payload']['number'] for r in returns},
        all_initial_states_equal=all(len({d['start_sha256'] for d in details if d['game_index']==i})==1 for i in complete_indices),
        all_worker_code_hashes_match=all(read(p)['code_sha256']==read(RUN/'Candidate_Freeze.json')['candidate_sha256'] for p in worker_receipts),
        all_worker_infrastructure_OK=all(read(p)['raw']['status']=='OK' for p in worker_receipts),
        three_banks_unchanged=all(sha(RUN/f'bank_{a}.private.json')==sha(RUN/'bank.private.json') for a in 'GHF'),
        old_fixtures_passed=read(RUN/'Fixture_Acceptance.json')['passed'])
    exposure=read(RUN/'exposure.private.json');reserved_path=ROOT/'runs/alfworld_route_a_online_value_20261117_01/online/selection.private.json'
    reserved=[x['task'] for x in read(reserved_path)['tasks']]
    excluded=[x['task'] for x in exposure['protected_games']]+reserved
    for k in ['group','task_id','game_sha256','trajectory_sha256']:audit['excluded_'+k+'_disjoint']=not ({t[k] for t in selection['tasks']}&{t[k] for t in excluded})
    audit['reserved60_manifest_unchanged']=sha(reserved_path)==selection['reserved60_manifest_sha256']
    audit['all_inputs_within_capacity']=all(read(p)['bytes']<=65536 for p in (RUN/'requests').rglob('Input_Size.json'))
    final_time=read(RUN/'Completed.json')['completed_at'] if (RUN/'Completed.json').exists() else None
    from datetime import datetime
    elapsed=datetime.fromisoformat(final_time).timestamp()-budget[0]['at'] if final_time else None
    audit['within_limits']=len(rows)<=36 and all(r['environment_actions']<=50 for r in rows) and len(starts)<=2000 and sum(r['payload']['branch'].startswith('pairs/') for r in starts)<=1800 and len(worker_receipts)<=650 and allcost['model_calls']<=2100 and allcost['reserved_usd']<=17 and (elapsed is None or elapsed<=10800)
    total=dict(allcost,environment_calls=len(starts),formal_environment_calls=sum(r['payload']['branch'].startswith('pairs/') for r in starts),worker_calls=len(worker_receipts),worker_ms=sum(read(p)['milliseconds'] for p in worker_receipts),wall_seconds=elapsed,actual_provider_bill_usd=None)
    result=dict(run_id=RUN.name,selected_games=len(selection['tasks']),complete_game_triplets=len(complete_indices),formal_completed_trajectories=len(rows),groups=summaries,comparisons=comparisons,rows=rows,phase_details=details,experiment_total=total,requests=request_rows,stopped=[read(p) for p in RUN.glob('Stopped*')],learning_calls=0,revisions=0)
    save('Results.json',result);save('Validation.json',audit)
    with (OUT/'Results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    save('Sample_Manifest.json',dict(selection,actual_status=[dict(game_index=i,task_id=t['task_id'],arms={a:dict(status=by[i,a]['status'],won=by[i,a]['won']) if (i,a) in by else dict(status='UNFINISHED') for a in 'GHF'}) for i,t in enumerate(selection['tasks'])]))
    old=historical()
    print(json.dumps(dict(groups=summaries,comparisons=comparisons,total=total,audit=audit,historical=old['totals']),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
