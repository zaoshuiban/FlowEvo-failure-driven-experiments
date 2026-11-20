"""Read-only outcome/cost aggregation for the frozen Route C experiment."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path

import run_alfworld_route_c_bounded_learning as C


def paired_summary(rows):
    stats={a:dict(wins=sum(r['arms'][a]['won'] for r in rows),
        calls=sum(r['arms'][a]['logical_model_calls'] for r in rows),
        steps=sum(r['arms'][a]['suffix_steps'] for r in rows),
        worker_calls=sum(r['arms'][a]['worker_calls'] for r in rows),
        policy_actions=sum(r['arms'][a]['policy_actions'] for r in rows),
        policy_errors=sum(r['arms'][a]['policy_errors'] for r in rows)) for a in ('G','R','F')}
    out=dict(checkpoints=len(rows),games=len({r['game_index'] for r in rows}),arms=stats)
    for reference in ('G','R'):
        both=[r for r in rows if r['arms'][reference]['won'] and r['arms']['F']['won']]
        out['F_vs_'+reference]=dict(
            rescued=sum(not r['arms'][reference]['won'] and r['arms']['F']['won'] for r in rows),
            harmed=sum(r['arms'][reference]['won'] and not r['arms']['F']['won'] for r in rows),
            both_success=len(both),
            model_calls_saved_on_both_success=sum(r['arms'][reference]['logical_model_calls']-r['arms']['F']['logical_model_calls'] for r in both),
            environment_steps_saved_on_both_success=sum(r['arms'][reference]['suffix_steps']-r['arms']['F']['suffix_steps'] for r in both))
    return out


def analyze(root):
    p=C.verify(root); freeze=C.A.read(root/'Frozen_Candidate.json')
    versions=[]
    for f in sorted((root/'learning').glob('v*/evaluation.json')):
        v=C.A.read(f); candidate=C.A.read(f.parent/'candidate.json')
        versions.append(dict(version=v['version'],static_pass=v['static_pass'],passed=v['complete_development_pass'],
            rank=v['rank'],code_sha256=v['code_sha256'],description=candidate['description'],applicability=candidate['applicability'],
            development=[{k:r[k] for k in ('won','status','suffix_steps','policy_actions','policy_errors','declined') if k in r} for r in v['rows']]))
    done=C.A.read(root/'Independent_Result.json') if (root/'Independent_Result.json').exists() else None
    rows=done['pairs'] if done else [C.A.read(f) for f in sorted((root/'pairs').glob('*/*/paired_result.json'))]
    for r in rows:
        if len({v['start_sha256'] for v in r['arms'].values()})!=1: raise ValueError('paired state mismatch')
        if any(v['suffix_steps']>50-r['anchor'] for v in r['arms'].values()): raise ValueError('remaining action budget violation')
    totals=defaultdict(Counter); model_versions=Counter(); paid_ids=set(); usage_count=0; missing_cost=0
    for f in sorted((root/'requests').rglob('response.json')):
        directory=f.parent; raw=C.A.read(f); stage=directory.relative_to(root/'requests').parts[0]
        usage=C.trusted_usage(raw)
        if not usage: raise ValueError('missing usage')
        model_versions[raw['model']]+=1
        if (directory/'cache.json').exists():
            totals[stage]['cached_callbacks']+=1;continue
        if raw['id'] in paid_ids: raise ValueError('duplicate paid response')
        paid_ids.add(raw['id']);usage_count+=1
        totals[stage]['paid_requests']+=1
        totals[stage].update(usage)
        if not isinstance(raw.get('usage',{}).get('cost'),(int,float)): missing_cost+=1
    native=[]
    for f in sorted((root/'native').glob('*/result.json')):
        r=C.A.read(f);case=C.A.read(f.parent/'case.private.json')
        native.append(dict(game_index=int(f.parent.name),won=r['won'],steps=len(r['steps']),
            retake_anchors=C.retake_anchors(case['goal'],r['steps']),task=case['task']))
    classes=['NATURAL_RETAKE','NORMAL_PROGRESS_CONTROL','CONTROLLED_RETAKE']
    result=dict(status='COMPLETED' if done else 'PARTIAL',protocol_sha256=C.A.digest(p),frozen=freeze,
        versions=versions,native_games=native,rows=rows,
        by_group={k:paired_summary([r for r in rows if r['group']==k]) for k in classes},
        usage_by_stage=dict(totals),unique_paid_requests=usage_count,provider_models=dict(model_versions),
        actual_billed_usd=None if missing_cost else 0,missing_supplier_money_records=missing_cost,
        budget=done['budget'] if done else C.Study(root).budget.snapshot(),
        provenance='Actual model responses, isolated Worker, replayed TextWorld transitions; learned source unedited by host.',
        interpretation='Training includes true recovery suffixes. Natural opportunities, normal controls and induced retakes are separate; repeated checkpoints of one game are not independent games.')
    C.A.commit(root/'Analysis.json',result)
    report= C.ROOT/'reports/alfworld_route_c_bounded_learning_20261118'
    report.mkdir(parents=True,exist_ok=True)
    public={k:v for k,v in result.items() if k not in ('native_games',)}
    public['native_games']=[{k:v for k,v in r.items() if k!='task'} for r in native]
    C.A.commit(report/'result_summary.json',public)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=C.OUT);a=p.parse_args()
    r=analyze(a.output.resolve());print({k:r[k] for k in ('status','by_group','usage_by_stage','unique_paid_requests')})
