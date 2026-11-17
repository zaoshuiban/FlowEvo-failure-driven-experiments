"""Read-only A3b descriptive metrics; no eligibility or authority changes."""
from collections import Counter
from failure_evo.contracts import fingerprint


def rows_metrics(rows):
    n=len(rows);counts=Counter(r['expected'] for r in rows)
    def ratio(k,v):return dict(numerator=k,denominator=v,value=k/v if v else None,status='EVALUABLE' if v else 'NOT_EVALUABLE')
    return dict(records=n,games=len({r['game_sha256'] for r in rows}),physical_groups=len({r['physical_state_group_id'] for r in rows}),
        predictions=dict(Counter(r['actual'] for r in rows)),
        correct_match=ratio(sum(r['expected']==r['actual']=='MATCH' for r in rows),counts['MATCH']),
        false_match=ratio(sum(r['expected']=='DECLINE' and r['actual']=='MATCH' for r in rows),counts['DECLINE']),
        unsupported_match=ratio(sum(r['expected']=='UNKNOWN' and r['actual']=='MATCH' for r in rows),counts['UNKNOWN']),
        exact_classification=ratio(sum(r['actual']==r['expected'] for r in rows),n),
        runtime_errors=sum(r['actual']=='ERROR' for r in rows),worker_seconds=sum(r.get('worker_seconds',0) for r in rows),
        source_repairs_verified=sum(r.get('recovery_verified') is True for r in rows),
        by_game={g:dict(records=len(rs),correct=sum(r['actual']==r['expected'] for r in rs),
                         matches=sum(r['actual']==r['expected']=='MATCH' for r in rs),false_match=sum(r['actual']=='MATCH' and r['expected']!='MATCH' for r in rs))
            for g in sorted({r['game_sha256'] for r in rows}) for rs in [[r for r in rows if r['game_sha256']==g]]})


def comparison(parent,child,key):
    before={r['sample_id']:r for r in parent.get(key,[])};after={r['sample_id']:r for r in child.get(key,[])}
    if set(before)!=set(after) or not before:return {'status':'NOT_EVALUABLE','reason':'missing/unequal execution coverage'}
    changes=[]
    for sid,a in before.items():
        b=after[sid]
        if (a['expected'],a['game_sha256'])!=(b['expected'],b['game_sha256']):raise PermissionError('paired label/game mismatch')
        changes.append(dict(sample_id=sid,game_sha256=a['game_sha256'],before=a['actual'],after=b['actual'],expected=a['expected'],
                            corrected=a['actual']!=a['expected'] and b['actual']==b['expected'],
                            degraded=a['actual']==a['expected'] and b['actual']!=b['expected'],
                            new_false_match=a['actual']!='MATCH' and b['actual']=='MATCH' and b['expected']!='MATCH'))
    return dict(status='DESCRIPTIVE_PAIRED',changed=sum(r['before']!=r['after'] for r in changes),
        corrected=sum(r['corrected'] for r in changes),degraded=sum(r['degraded'] for r in changes),new_false_match=sum(r['new_false_match'] for r in changes),
        improved_games=len({r['game_sha256'] for r in changes if r['corrected']}),degraded_games=len({r['game_sha256'] for r in changes if r['degraded']}),rows=changes)


def analyze(result):
    attempts=result['attempts'];byversion={a['version']:a for a in attempts};versions=[];pairs=[]
    for a in attempts:
        row=dict(candidate=a['candidate_id'],version=a['version'],status=a['status'],code_sha256=a.get('code_sha256'),usage=a.get('usage'),
                 train=rows_metrics(a.get('train',[])),validation=rows_metrics(a.get('validation',[])),duplicate_of=a.get('duplicate_of'))
        if a.get('parent_version'):
            parent=byversion[a['parent_version']]
            row['vs_initial']={k:comparison(parent,a,k) for k in ('train','validation')}
        versions.append(row)
    for p in attempts[:4]:
        branches={a.get('branch'):a for a in attempts if a.get('parent_version')==p['version']}
        pairs.append(dict(candidate=p['candidate_id'],parent_version=p['version'],R1_vs_R0={k:comparison(branches['R0'],branches['R1'],k)
            for k in ('train','validation')} if set(branches)>={'R0','R1'} else {'status':'NOT_EVALUABLE'}))
    return dict(origin='MOCK_ENGINEERING' if result['paid_requests']==0 else 'REAL_MODEL_DEVELOPMENT',versions=versions,pairs=pairs,
        selection=result['selection'],ledger=result['budget'],paid_requests=result['paid_requests'],
        inference='Previously inspected development data; four paired generations are not independent games; no confirmatory significance claim.',
        generalization='NOT_EVALUATED',source_result_sha256=fingerprint(result))
