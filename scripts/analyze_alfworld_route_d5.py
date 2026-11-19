"""Read-only D5 accounting: physical unique spend versus logical strategy costs."""
import csv,json
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
from analyze_alfworld_route_d2 import read,sha,digest,journal
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/alfworld_route_d5_takeover_scope_20261119_01'
OUT=ROOT/'reports'/RUN.name
METRICS=['model_calls','input_tokens','output_tokens','reference_usd','environment_actions','worker_calls','worker_ms','logical_seconds']


def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def main():
    protocol=read(RUN/'protocol.json');selection=read(RUN/'selection.private.json')
    budget=[]
    for f in ['budget.jsonl']:
        if (RUN/f).exists():budget.extend(journal(RUN/f))
    env=journal(RUN/'environment_actions.jsonl') if (RUN/'environment_actions.jsonl').exists() else []
    reqs={r['payload']['request_id']:r['payload'] for r in budget if r['kind']=='RESERVED'}
    settled={r['payload']['request_id']:r['payload'] for r in budget if r['kind']=='SETTLED'}
    not_sent={r['payload']['request_id']:r['payload'] for r in budget if r['kind']=='NOT_SENT'}
    requests=[];costs=defaultdict(Counter);activity=defaultdict(list)
    for rid,res in reqs.items():
        if res['kind']=='tool':
            job=res['job_id'];branch=job.split('/workers/')[0]
            activity[branch].extend(r['at'] for r in budget if r['kind']=='RESERVED' and r['payload']['request_id']==rid)
            continue
        folder=RUN/'requests'/rid;raw=read(folder/'response.json') if (folder/'response.json').exists() else None
        key=rid.rsplit('/action_',1)[0] if '/action_' in rid else rid
        row=dict(request_id=rid,branch=key,model_calls=0 if rid in not_sent else 1,reserved_usd=0 if rid in not_sent else res['cost_upper_microusd']/1e6,actual_bill_usd=0 if rid in not_sent else None)
        if rid in not_sent:row.update(proven_not_sent=True,released_reservation_usd=res['cost_upper_microusd']/1e6,input_tokens=0,output_tokens=0,reference_usd=0)
        if raw:
            u=raw['usage'];pro='pro' in raw['model'];inp,out=(1.32,3.96) if pro else (.3,1.2)
            row.update(model=raw['model'],input_tokens=u['prompt_tokens'],output_tokens=u['completion_tokens'],total_tokens=u['total_tokens'],reference_usd=(inp*u['prompt_tokens']+out*u['completion_tokens'])/1e6,finish_reason=raw['choices'][0]['finish_reason'])
            assert settled[rid]['tokens']==u['total_tokens']
        elif rid not in not_sent:row['usage_unknown']=True
        if (folder/'Timing.json').exists():activity[key].append(read(folder/'Timing.json')['started'])
        costs[key].update({k:v for k,v in row.items() if isinstance(v,(int,float)) and k!='actual_bill_usd'})
        requests.append(row)
    def branch_cost(ident,prefix=False):
        r=read(RUN/ident/'result.json');c=Counter(costs[ident]);workers=[read(p) for p in (RUN/ident/'workers').glob('*.json')]
        c.update(environment_actions=len(r['records']),worker_calls=len(workers),worker_ms=sum(w['milliseconds'] for w in workers))
        c['logical_seconds']=r['wall_seconds'] if prefix else max(0,r['ended']-min(activity.get(ident,[r['ended']])))
        return c
    rows=[];block_details=[]
    for path in sorted((RUN/'pairs/formal').glob('*/*/comparison.json')):
        b=read(path);i=b['game_index'];rep=b['repetition'];pref=read(RUN/b['prefix']/'result.json');pc=branch_cost(b['prefix'],True)
        for arm in ['H','F_full','F8']:
            c=pc.copy();own=None;resolved=None;mode='NO_ENTRY_TERMINAL';won=pref['won'];status=pref['status'];handback=None;reference=None;policy_actions=0
            if b['entry']:
                ident=b['arms'][arm]['path'];own=read(RUN/ident/'result.json');c.update(branch_cost(ident));won=own['won'];status=own['status'];policy_actions=own['policy_actions'];handback=own['handback']
                if own['shared_h']:
                    reference=own['shared_h']['trajectory'];resolved=read(RUN/reference/'result.json');c.update(branch_cost(reference));won=resolved['won'];status=resolved['status'];mode='ZERO_ACTION_DECLINE_SHARED_H'
                    ref=read(RUN/ident/'Resolved_Reference.json');assert ref['sha256']==sha(RUN/reference/'result.json')
                    assert own['start_sha256']==resolved['start_sha256']
                elif arm=='H':mode='NATIVE_H'
                elif handback and handback['kind']=='HOST_WINDOW_EXHAUSTED':mode='HOST_WINDOW_H_SUCCESS' if won else 'HOST_WINDOW_H_FAILURE'
                elif handback and policy_actions:mode='CANDIDATE_H_SUCCESS' if won else 'CANDIDATE_H_FAILURE'
                elif won:mode='SKILL_DIRECT_COMPLETION'
                elif policy_actions:mode='SKILL_NOT_COMPLETED'
                else:mode='ZERO_ACTION_ERROR_OR_FAILURE'
            row=dict(game_index=i,task_id=selection['tasks'][i]['task_id'],group=selection['tasks'][i]['group'],stratum=b['stratum'],repetition=rep,arm=arm,entry=b['entry'],won=won,status=status,completion_mode=mode,
                policy_actions=policy_actions,handback_after_actions=bool(handback and policy_actions),voluntary_handback_after_actions=bool(handback and policy_actions and handback['status']=='declined'),
                handback_kind=handback['kind'] if handback else None,handback_status=handback['status'] if handback else None,stop_reason=own['stop_reason'] if own and not reference else ('ENVIRONMENT_WON' if won else ('TASK_BUDGET_EXHAUSTED' if len((resolved or pref)['steps'])>=50 else status)),policy_errors=own['policy_errors'] if own else 0,
                handback_remaining=handback['remaining'] if handback else None,handback_reason=handback['reason'] if handback else None,
                shared_prefix=b['prefix'],shared_suffix=reference,**{k:c[k] for k in METRICS})
            rows.append(row)
        block_details.append(b)
    summary={};comparisons={};by={(r['game_index'],r['repetition'],r['arm']):r for r in rows}
    for layer in ['all','put_two','other']:
        sub=[r for r in rows if layer=='all' or r['stratum']==layer]
        summary[layer]={}
        for arm in ['H','F_full','F8']:
            ar=[r for r in sub if r['arm']==arm]
            summary[layer][arm]=dict(logical_results=len(ar),independent_games=len({r['game_index'] for r in ar}),won=sum(r['won'] for r in ar),entry=sum(r['entry'] for r in ar),
                skill_acted=sum(r['policy_actions']>0 for r in ar),completion_modes=dict(Counter(r['completion_mode'] for r in ar)),
                active_handbacks=sum(r['voluntary_handback_after_actions'] for r in ar),candidate_declined=sum(r['handback_kind']=='CANDIDATE_DECLINED' for r in ar),host_window_handbacks=sum(r['handback_kind']=='HOST_WINDOW_EXHAUSTED' for r in ar),host_window_h_success=sum(r['handback_kind']=='HOST_WINDOW_EXHAUSTED' and r['won'] for r in ar),error_handbacks=sum(r['handback_status']=='error' for r in ar),**{k:sum(r[k] for r in ar) for k in METRICS})
        comparisons[layer]={}
        for comparator in ['F_full','H']:
            keys=[(r['game_index'],r['repetition']) for r in sub if r['arm']=='F8' and (r['game_index'],r['repetition'],comparator) in by]
            cells=defaultdict(list)
            for key in keys:
                f,c=by[key+('F8',)],by[key+(comparator,)]
                label='both_success' if f['won'] and c['won'] else 'F8_only' if f['won'] else 'comparator_only' if c['won'] else 'both_failure'
                cells[label].append(key)
            joint=cells['both_success']
            comparisons[layer]['F8_vs_'+comparator]=dict(cells={k:cells[k] for k in ['both_success','F8_only','comparator_only','both_failure']},joint_success_n=len(joint),
                all_delta={m:sum(by[k+('F8',)][m]-by[k+(comparator,)][m] for k in keys) for m in METRICS},
                joint_success_totals={a:{m:sum(by[k+(a,)][m] for k in joint) for m in METRICS} for a in ['F8',comparator]},
                joint_success_delta={m:sum(by[k+('F8',)][m]-by[k+(comparator,)][m] for k in joint) for m in METRICS})
    game_summary=[]
    for i,t in enumerate(selection['tasks']):
        per={}
        for arm in ['H','F_full','F8']:
            ar=[r for r in rows if r['game_index']==i and r['arm']==arm]
            per[arm]=dict(observations=len(ar),wins=sum(r['won'] for r in ar),
                completion_modes=[r['completion_mode'] for r in ar],means={m:sum(r[m] for r in ar)/len(ar) if ar else None for m in METRICS})
        game_summary.append(dict(game_index=i,task_id=t['task_id'],stratum=selection['rows'][i]['stratum'],arms=per))
    totals=Counter()
    for c in costs.values():totals.update(c)
    workers=[read(p) for p in RUN.rglob('*.json') if (('/workers/' in str(p) or '/output_only/' in str(p)) and p.name!='submission.json')]
    workers=[w for w in workers if 'milliseconds' in w and 'raw' in w]
    starts=[r for r in env if r['kind']=='STARTED'];returns=[r for r in env if r['kind']=='RETURNED']
    totals.update(environment_actions=len(starts),worker_calls=len(workers),worker_ms=sum(w['milliseconds'] for w in workers))
    phase_totals=defaultdict(Counter)
    def phase(ident):
        return 'generation' if ident.startswith('generation/') else 'formal' if ident.startswith('pairs/formal/') else 'development' if ident.startswith(('pairs/development/','evaluations/')) else 'contract_fixture'
    for row in requests:
        phase_totals[phase(row['request_id'])].update({k:row.get(k,0) for k in ['model_calls','input_tokens','output_tokens','reference_usd','reserved_usd']})
    for e in starts:
        phase_totals[phase(e['payload']['branch'])]['environment_actions']+=1
        phase_totals[phase(e['payload']['branch'])]['replay_actions']+=e['payload']['phase']=='prefix'
    for path in RUN.rglob('*.json'):
        if '/workers/' not in str(path) and '/output_only/' not in str(path):continue
        receipt=read(path)
        if 'milliseconds' in receipt and 'raw' in receipt:
            ph=phase(str(path.relative_to(RUN)));phase_totals[ph]['worker_calls']+=1;phase_totals[ph]['worker_ms']+=receipt['milliseconds']
    elapsed=None
    if (RUN/'Completed.json').exists():
        elapsed=datetime.fromisoformat(read(RUN/'Completed.json')['completed_at']).timestamp()-min(e['at'] for e in budget if e['kind']=='RUN_OPENED')
    if elapsed is None and list(RUN.glob('Stopped*')):
        elapsed=max(datetime.fromisoformat(read(p)['at']).timestamp() for p in RUN.glob('Stopped*'))-min(e['at'] for e in budget if e['kind']=='RUN_OPENED')
    validations=dict(frozen_components=all(sha(Path(p))==h for p,h in protocol['files'].items()),all_requests_accounted=set(reqs)==set(settled)|set(not_sent),no_unknown=not any(r['kind']=='UNKNOWN' for r in budget),
        environment_complete=len(starts)==len(returns) and {x['payload']['number'] for x in starts}=={x['payload']['number'] for x in returns},
        protocol_document=sha(OUT/'Protocol.md')==read(RUN/'Preflight.json')['protocol_md_sha256'],protocol_json=sha(RUN/'protocol.json')==read(RUN/'Preflight.json')['protocol_json_sha256'],
        budget_bounds=totals['model_calls']<=4000 and totals['reserved_usd']<=17 and len(starts)<=5000 and len(workers)<=1600 and (elapsed is None or elapsed<=10800),
        no_illegal_actual_actions=all(rec['feedback']['action'] in rec['legal_before'] for p in (RUN/'pairs').rglob('result.json') for rec in read(p).get('records',[])))
    exposure=read(RUN/'exposure.private.json');protected=[x['task'] for x in exposure['protected_games']]
    for k in ['task_id','group','game_sha256','trajectory_sha256']:validations['excluded_'+k]=not ({t[k] for t in selection['tasks']}&{t[k] for t in protected})
    validations['selected_candidate_unchanged']=sha(RUN/'frozen/code.py')==protocol['candidate_sha256']
    validations['zero_learning']=all(r['request_id'].startswith('pairs/') and (r.get('proven_not_sent') or r.get('model')=='deepseek-flash') for r in requests)
    validations['candidate_window_prefixes']=all(read(p)['passed'] for p in (RUN/'pairs/formal').glob('*/*/Window_Prefix_Validation.json'))
    for b in block_details:
        if b['entry']:
            hashes={read(RUN/b['arms'][a]['path']/'result.json')['start_sha256'] for a in ['H','F_full','F8']}
            assert len(hashes)==1
    validations['paired_prefix_signatures']=True
    development=[read(RUN/'Fixture_Acceptance.json')] if (RUN/'Fixture_Acceptance.json').exists() else []
    incomplete=[]
    for i,t in enumerate(selection['tasks']):
        stem=RUN/f'pairs/formal/{i:02d}/0'
        if (stem/'comparison.json').exists():continue
        steps=[read(p) for p in sorted((stem/'prefix/steps').glob('*.json'))]
        incomplete.append(dict(game_index=i,task_id=t['task_id'],group=t['group'],stratum=selection['rows'][i]['stratum'],status='INCOMPLETE_PREFIX' if steps else 'NOT_STARTED',public_actions=len(steps),last_record=steps[-1] if steps else None,paired_scoring=False))
    save('Incomplete_Blocks.json',incomplete)
    result=dict(run_id=RUN.name,execution_status='COMPLETED' if (RUN/'Completed.json').exists() else 'STOPPED',planned_blocks=len(selection['tasks']),incomplete_and_not_started=incomplete,development=development,selected=read(RUN/'Candidate_Identity.json'),
        formal_blocks=len(block_details),logical_results=len(rows),summary=summary,comparisons=comparisons,game_summary=game_summary,rows=rows,actual_experiment_totals=dict(totals),
        actual_environment_phase_counts=dict(Counter(r['payload']['phase'] for r in starts)),actual_costs_by_phase=dict(phase_totals),actual_run_wall_seconds=elapsed,requests=requests,actual_provider_bill_usd=None,
        logical_seconds_method='shared initial-prefix wall time once per strategy + suffix active interval from first request/tool reservation to branch end; replay/reset excluded from suffix, initial reset retained; reference adds actual refusal interval plus H suffix',
        stopped=[read(p) for p in RUN.glob('Stopped*')])
    save('Results.json',result);save('Validation.json',validations)
    if rows:
        with (OUT/'Results.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        game_rows=[]
        for g in game_summary:
            flat={k:g[k] for k in ['game_index','task_id','stratum']}
            for arm,v in g['arms'].items():
                flat[arm+'_wins_of_one']=v['wins']
                for m,value in v['means'].items():flat[arm+'_mean_'+m]=value
            game_rows.append(flat)
        with (OUT/'Game_Results.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(game_rows[0]));w.writeheader();w.writerows(game_rows)
    save('Sample_Manifest.json',dict(selection,actual_blocks=block_details,formal_started=bool(block_details),execution_status=result['execution_status'],incomplete_and_not_started=incomplete,selected_candidate=result['selected']))
    print(json.dumps(dict(formal_blocks=len(block_details),summary=summary['all'],comparisons=comparisons['all'],actual_totals=dict(totals),validations=validations),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
