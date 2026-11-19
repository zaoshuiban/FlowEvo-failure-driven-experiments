"""Development veto followed by one independent zero-model confirmation.

No online or paid execution entry. Reuses frozen Worker/Registry/scoring and
durable checkpoint collector. Never edits the model's candidate or old records.
"""
import argparse
from pathlib import Path
from unittest.mock import patch
from collections import Counter
import prepare_alfworld_route_a_prerequisites_v2 as N

A=N.A; V=N.V; X=N.X; P=N.P; B=N.B; ROOT=N.ROOT


def candidate(root):
    p=N.verify_preparation(root);r=A.read(root/'generation/result.json');src=root/'generation/candidate.py'
    if r['origin']!='REAL_MODEL' or r['status']!='STATIC_PASSED_PENDING_DEVELOPMENT':
        raise PermissionError('no real accepted model candidate')
    if A.sha(src)!=r['code_sha256'] or A.sha(p['frozen_recovery']['path'])!=p['frozen_recovery']['sha256']:
        raise PermissionError('candidate/recovery drift')
    return p,r,src


def freeze(root,phase):
    p,r,src=candidate(root);out=root/phase
    if (out/'protocol.json').exists():return verify(out)[0]
    if phase=='confirmation':
        dev=A.read(root/'development/Readiness.json')
        if not dev['passed'] or dev['candidate_version']!=r['candidate_version']:
            raise PermissionError('development veto; no new games executed')
    old=A.read(N.OLD/'protocol.json');plan=dict(old)
    files=dict(old['files']);files.update(p['source_files'])
    files.update({str(q):A.sha(q) for q in (Path(__file__).resolve(),src,root/'generation/result.json')})
    files.update(A.read(root/'exposure.private.json')['files'])
    chosen=A.read(N.OLD/'collection/selection.private.json') if phase=='development' else A.read(root/'confirmation_selection.private.json')
    A.commit(out/'collection/selection.private.json',chosen)
    A.commit(out/'online/selection.private.json',A.read(N.OLD/'online/selection.private.json'))
    A.commit(out/'exposure.private.json',A.read(root/'exposure.private.json'))
    candidates=dict(old['candidates'],Route_A=dict(path=str(src),sha256=r['code_sha256']))
    plan.update(version=N.VERSION+'-'+phase,run_id=out.parent.name+'-'+phase,files=files,candidates=candidates,
        candidate_version=r['candidate_version'],parent_run=str(N.OLD),phase=phase,
        selection_sha256=A.sha(out/'collection/selection.private.json'),
        online_selection_sha256=A.sha(out/'online/selection.private.json'),exposure_sha256=A.sha(out/'exposure.private.json'),
        joint_sha256=A.digest([candidates,r['candidate_version'],phase]),
        worker_calls=6000,environment_steps=18000,max_calls=0,max_tokens=0,max_cost_microusd=0,
        checkpoint_rules='All reviewed full states and one equal-length READY pair per game; all unresolved controls retained separately; no candidate-dependent selection.',
        additional_coverage=dict(phase_conflict_games=3,instance_conflict_games=3),
        source_pending='Unproven phase/instance labels must remain unresolved, never inferred from no-win.',
        native_online_execution_allowed=False,permission='SHADOW')
    A.commit(out/'protocol.json',plan);A.commit(out/'collection/protocol.json',plan)
    A.commit(out/'Candidate_Freeze.json',dict(candidate_version=r['candidate_version'],
        gate_sha256=r['code_sha256'],recovery_sha256=candidates['S0']['sha256'],phase=phase,
        protocol_sha256=A.digest(plan),model_revision_finished_before_independent_collection=True))
    if phase=='development':
        data=A.read(N.OLD/'checkpoints.private.json');A.commit(out/'checkpoints.private.json',data)
        oldfreeze=A.read(N.OLD/'Checkpoint_Freeze.json')
        A.commit(out/'Checkpoint_Freeze.json',dict(oldfreeze,protocol_sha256=A.digest(plan),
            checkpoint_sha256=A.sha(out/'checkpoints.private.json'),status='EXPOSED_DEVELOPMENT_REGRESSION'))
    return plan


def verify(out):
    p=A.read(out/'protocol.json');N.verify_preparation(out.parent)
    phase=out.name
    if phase not in ('development','confirmation') or p['version']!=N.VERSION+'-'+phase:
        raise PermissionError('phase')
    if p['max_calls'] or p['max_tokens'] or p['max_cost_microusd'] or p['native_online_execution_allowed'] or p['permission']!='SHADOW':
        raise PermissionError('zero-model Shadow scope')
    P.verify_history(p['files'])
    for f,key in [('collection/selection.private.json','selection_sha256'),('online/selection.private.json','online_selection_sha256'),('exposure.private.json','exposure_sha256')]:
        if A.sha(out/f)!=p[key]:raise PermissionError('freeze drift')
    if A.sha(out/'collection/protocol.json')!=A.sha(out/'protocol.json'):raise PermissionError('collection freeze')
    if P.environment_manifest(p['data_root'])!=p['environment']:raise PermissionError('environment drift')
    for c in p['candidates'].values():
        if A.sha(c['path'])!=c['sha256']:raise PermissionError('candidate changed')
    selected=A.read(out/'collection/selection.private.json')
    if phase=='confirmation':
        protected={r['task']['group'] for r in A.read(out/'exposure.private.json')['protected_games']}
        groups={r['task']['group'] for r in selected['tasks']}
        if len(groups)!=48 or groups&protected:raise PermissionError('new task isolation')
    for r in selected['tasks']:X.C.C.verify_game(p['data_root'],dict(row=r['task']))
    return p,selected


def preflight(out):
    with patch.object(V,'verify',side_effect=lambda _:verify(out)):return V.preflight(out)


def collect(out):
    if out.name!='confirmation':raise PermissionError('no development recollection')
    verify(out)
    with patch.object(X,'verify',side_effect=lambda _:verify(out)):return X.collect(out)


def all_samples(rows):
    # Select without reading decisions. Retain distinct IDs, never inflate games.
    return list({s['sample_id']:s for s in rows}.values())


def review(out):
    if out.name!='confirmation':raise PermissionError('old labels immutable')
    with patch.object(X,'verify',side_effect=lambda _:verify(out)),patch.object(X,'choose_samples',side_effect=all_samples):
        return X.review(out)


def readiness(out):
    p,_=verify(out);rows=A.read(out/'result.json')['rows'];samples=A.read(out/'checkpoints.private.json')['samples']
    if out.name=='development':
        old=A.read(N.OLD/'result.json')['rows'];old_good={r['sample_id'] for r in old if r['score']['completed_repair']}
        now={r['sample_id']:r for r in rows}
        lost=sorted(i for i in old_good if not now[i]['score']['completed_repair'])
        unsafe=[r['sample_id'] for r in rows if r['score']['unsupported_recovery'] or r['score']['false_final_delivery_recovery'] or r['score']['safety_unresolved']]
        errors=[r['sample_id'] for r in rows if r['gate_error'] or r['score']['candidate_error']]
        result=dict(passed=bool(old_good) and not lost and not unsafe and not errors,retained=len(old_good)-len(lost),
            old_successes=len(old_good),lost=lost,unsafe=unsafe,errors=errors,scope='EXPOSED_DEVELOPMENT_NOT_INDEPENDENT')
    else:
        result=V.assess(rows,p['thresholds'])
        # Names/modes alone are not trusted labels. Current inherited reviewer
        # explicitly leaves these mechanisms unresolved: report the gap.
        negative=[s for s in samples if s['label']=='DECLINE' and s['label_status']=='EVIDENCE_REVIEWED']
        counts=dict(phase_conflict_games=len({s['game_sha256'] for s in negative if s['mode']=='UNPROCESSED'}),
                    instance_conflict_games=len({s['game_sha256'] for s in negative if s['mode']=='OTHER_INSTANCE'}))
        result['additional_coverage']=counts
        result['additional_coverage_ready']=all(counts[k]>=v for k,v in p['additional_coverage'].items())
        result['passed']=result['eligible_for_online_preparation'] and result['additional_coverage_ready']
        result['eligible_for_online_preparation']=result['passed']
    result.update(candidate_version=p['candidate_version'],labels=dict(Counter(s['label'] for s in samples)),
        published=False,online_authorized=False,paid_requests=0)
    return A.commit(out/'Readiness.json',result)


def evaluate(out):
    original=X.origin_for
    origin=lambda _,s:original(N.OLD if out.name=='development' else out,s)
    with patch.object(V,'verify',side_effect=lambda _:verify(out)),patch.object(X,'origin_for',side_effect=origin):
        V.evaluate(out)
    return readiness(out)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze','verify','preflight','collect','review','evaluate','readiness'])
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--phase',choices=['development','confirmation'],required=True)
    args=parser.parse_args();out=args.output/args.phase
    r=freeze(args.output,args.phase) if args.command=='freeze' else globals()[args.command](out)
    print(A.digest(r))
