"""Offline receipt verification; no model or Worker execution."""
import json
from collections import Counter
from pathlib import Path
import run_alfworld_route_d5 as X
from analyze_alfworld_route_d2 import journal


def main():
    run=X.OUT;selection=X.A.read(run/'selection.private.json');protocol=X.A.read(run/'protocol.json')
    checks={};details=[];windows=[]
    checks['source_and_components_unchanged']=all(X.A.sha(Path(p))==h for p,h in protocol['files'].items())
    checks['s1_exact']=X.A.sha(run/'frozen/code.py')==X.SHA
    checks['24_distinct_groups']=len(selection['tasks'])==len({t['group'] for t in selection['tasks']})==24
    checks['12_plus_12']=Counter(x['stratum'] for x in selection['rows'])=={'put_two':12,'other':12}
    checks['six_orders_four_each']=len(Counter(tuple(x) for x in selection['orders']))==6 and set(Counter(tuple(x) for x in selection['orders']).values())=={4}
    checks['old_fixture_continuity']=X.A.read(run/'Fixture_Continuity_Audit.json')['passed']
    protected=[x['task'] for x in X.A.read(run/'exposure.private.json')['protected_games']]
    d4=X.A.read(X.OLD/'selection.private.json')['tasks']
    sealed=[x['task'] for x in X.A.read(X.ROOT/'runs/alfworld_route_a_online_value_20261117_01/online/selection.private.json')['tasks']]
    for name,other in [('historical',protected),('D4',d4),('sealed60',sealed)]:
        for key in ['task_id','group','game_sha256','trajectory_sha256']:
            checks[name+'_disjoint_'+key]=not ({t[key] for t in selection['tasks']}&{t[key] for t in other})
    events=journal(run/'environment_actions.jsonl');returns=[e['payload'] for e in events if e['kind']=='RETURNED']
    checks['fixtures_within100']=sum('/fixtures/' in e['branch'] for e in returns)<=100
    blocks=sorted((run/'pairs/formal').glob('*/*/comparison.json'))
    for bp in blocks:
        b=X.A.read(bp);i=b['game_index'];stem=bp.parent;case=X.A.read(run/f'native/{i:02d}/case.private.json')
        assert case['goal']==selection['rows'][i]['goal']
        prefix=X.A.read(run/b['prefix']/'result.json')
        if not b['entry']:
            assert all(a['reference']==b['prefix'] and a['won']==prefix['won'] for a in b['arms'].values())
            details.append(dict(game_index=i,shared_terminal=True,passed=True));continue
        cp=X.A.read(stem/'checkpoint.private.json');assert cp['steps']==prefix['steps']
        starts=[];arm_results={}
        for arm in ['H','F_full','F8']:
            folder=stem/arm;ident=str(folder.relative_to(run));r=X.A.read(folder/'result.json');arm_results[arm]=r
            assert r['anchor']==len(cp['steps']) and len(r['steps'])<=50
            sig=X.signature(cp,cp['steps'][-1]['observation'],cp['steps'][-1]['commands'],cp['steps'])
            assert X.A.read(folder/'start.private.json')==sig and r['start_sha256']==X.A.digest(sig)
            starts.append(r['start_sha256'])
            replay=[e['feedback'] for e in returns if e['branch']==ident and e['phase']=='prefix']
            assert replay==cp['steps']
            steps=list(cp['steps']);state={};obs=steps[-1]['observation'];cmds=steps[-1]['commands'];worker_count=0
            for rec in r['records']:
                n=len(steps)+1;assert rec['step']==n and rec['before_observation']==obs and rec['legal_before']==cmds
                wp=folder/f'workers/{n:02d}.json'
                if wp.exists():
                    w=X.A.read(wp);ctx=X.C.context_view(cp['goal'],obs,cmds,X.D.public_history(cp['initial'],steps),state)
                    assert w['context_sha256']==X.A.digest(ctx) and w['code_sha256']==X.SHA and w['result']==rec['decision']
                    state=w['result'].get('state',{});worker_count+=1
                if rec['actor']=='MODEL':
                    guidance,directives=X.C.guidance(cp['skills'])
                    req=X.A.read(run/'requests'/ident/f'action_{n:02d}/request.private.json')
                    expected=dict(model='deepseek-flash',messages=[dict(role='system',content=X.C._build_system(directives)),dict(role='user',content=X.D.full_user(cp['goal'],obs,cmds,cp['initial'],steps,guidance))],max_tokens=1024,temperature=0,thinking={'type':'disabled'},reasoning_effort='none',stream=False)
                    assert req==expected
                fb=rec['feedback'];assert fb['action'] in cmds;steps.append(fb);obs=fb['observation'];cmds=fb['commands']
            assert steps==r['steps']
            if r['shared_h']:
                assert r['policy_actions']==0 and r['handback']['kind']=='CANDIDATE_DECLINED'
                w=X.A.read(next((folder/'workers').glob('*.json')))
                ctx=X.C.context_view(cp['goal'],obs,cmds,X.D.public_history(cp['initial'],steps),state)
                assert w['context_sha256']==X.A.digest(ctx) and w['code_sha256']==X.SHA
                assert r['shared_h']['start_sha256']==r['start_sha256'];worker_count+=1
            assert worker_count==r['worker_calls']
            if arm=='F8':
                assert r['policy_actions']<=8
                h=r['handback']
                if h and h['kind']=='HOST_WINDOW_EXHAUSTED':
                    assert r['policy_actions']==8 and r['worker_calls']==8 and not r['shared_h']
                    assert h['at_action']==r['anchor']+8 and h['remaining']==50-h['at_action']>0
                    eighth=r['records'][7];assert eighth['actor']=='SKILL' and not eighth['feedback']['done'] and not eighth['feedback']['won']
                    at=cp['steps']+[x['feedback'] for x in r['records'][:8]]
                    assert h['controller_signature_sha256']==X.A.digest(X.signature(cp,at[-1]['observation'],at[-1]['commands'],at))
                    assert not (len(at)>=12 and [s['action'] for s in at[-9:-6]]==[s['action'] for s in at[-6:-3]]==[s['action'] for s in at[-3:]])
                    assert not (len(at)>=3 and all('nothing happens' in s['observation'].lower() for s in at[-3:]))
                    assert len(r['records'])>8 and all(x['actor']=='MODEL' for x in r['records'][8:])
                    assert r['records'][8]['step']==r['anchor']+9
        assert len(set(starts))==1
        full,limited=arm_results['F_full'],arm_results['F8']
        skill=[x for x in limited['records'] if x['actor']=='SKILL']
        for a,c in zip(full['records'],skill):
            assert a['actor']=='SKILL' and a['decision']==c['decision'] and a['feedback']==c['feedback']
            wa=X.A.read(stem/f'F_full/workers/{a["step"]:02d}.json');wc=X.A.read(stem/f'F8/workers/{c["step"]:02d}.json')
            assert wa['context_sha256']==wc['context_sha256']
        if limited['handback'] and limited['handback']['kind']=='HOST_WINDOW_EXHAUSTED':
            windows.append(dict(game_index=i,group=selection['tasks'][i]['group'],goal=case['goal'],anchor=limited['anchor'],remaining_at_handback=limited['handback']['remaining'],
                F_full_won=full['won'],F_full_skill_actions=full['policy_actions'],F_full_status=full['stop_reason'],F8_won=limited['won'],F8_H_actions=len(limited['records'])-8,F8_status=limited['stop_reason'],
                H_won=arm_results['H']['won'],F_full_actual_tail=full['records'][8:],F8_actual_H_tail=limited['records'][8:]))
        details.append(dict(game_index=i,shared_terminal=False,matched_worker_prefix=len(skill),passed=True))
    checks['all_complete_block_continuity']=all(x['passed'] for x in details)
    exact_eight=[X.A.read(p) for p in (run/'pairs/formal').glob('*/0/F8/result.json') if X.A.read(p)['won'] and X.A.read(p)['environment_actions']==8 and X.A.read(p)['policy_actions']==8]
    checks['observed_win_on_eighth_precedes_handback']=bool(exact_eight) and all(r['handback'] is None and r['worker_calls']==8 for r in exact_eight)
    coverage=dict(planned_blocks=24,complete_blocks=len(blocks),full_planned_coverage=len(blocks)==24)
    partial=[]
    for i,t in enumerate(selection['tasks']):
        pref=run/f'pairs/formal/{i:02d}/0/prefix';ps=sorted((pref/'steps').glob('*.json'))
        if not ps:continue
        case=X.A.read(run/f'native/{i:02d}/case.private.json');steps=[];obs=case['initial']['observation'];cmds=case['initial']['commands'];ident=str(pref.relative_to(run))
        for path in ps:
            rec=X.A.read(path);n=len(steps)+1;assert rec['step']==n and rec['actor']=='MODEL' and rec['before_observation']==obs and rec['legal_before']==cmds
            g,d=X.C.guidance(case['skills']);wire=X.A.read(run/'requests'/ident/f'action_{n:02d}/request.private.json')
            assert wire['messages']==[dict(role='system',content=X.C._build_system(d)),dict(role='user',content=X.D.full_user(case['goal'],obs,cmds,case['initial'],steps,g))]
            fb=rec['feedback'];steps.append(fb);obs=fb['observation'];cmds=fb['commands']
        assert [e['feedback'] for e in returns if e['branch']==ident]==steps
        if not (pref/'result.json').exists():partial.append(dict(game_index=i,public_actions=len(steps),paired_scoring=False))
    checks['all_executed_prefix_actions_accounted']=True
    budget=journal(run/'budget.jsonl');ns=[e['payload'] for e in budget if e['kind']=='NOT_SENT'];sends={e['payload']['request_id'] for e in budget if e['kind']=='NETWORK_SEND_STARTED'}
    checks['not_sent_proof']=all(x['request_id'] not in sends and not x['model_http_started'] for x in ns)
    checks['frozen_connection_stop_honored']=len(blocks)==24 or (bool(list(run.glob('Stopped*'))) and all(x['connection_attempts']==protocol['network_policy']['max_connect_attempts'] for x in ns))
    coverage.update(partial_blocks=partial,not_started=24-len(blocks)-len(partial),stopped_without_reissue=bool(ns))
    checks['no_pro_no_learning']=not (run/'generation_budget.jsonl').exists() and all(X.A.read(p)['model']=='deepseek-flash' for p in (run/'requests').rglob('request.private.json'))
    checks['frozen_protocol_documents']=X.A.sha(X.REPORT/'Protocol.md')==X.A.read(run/'Preflight.json')['protocol_md_sha256'] and X.A.sha(run/'protocol.json')==X.A.read(run/'Preflight.json')['protocol_json_sha256']
    output=dict(checks=checks,coverage=coverage,blocks=details,window_cases=windows,read_only=True)
    (X.REPORT/'Continuity_Audit.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(checks=checks,completed_blocks=len(blocks),window_games=[x['game_index'] for x in windows]),ensure_ascii=False,indent=2))
    assert all(checks.values())


if __name__=='__main__':main()
