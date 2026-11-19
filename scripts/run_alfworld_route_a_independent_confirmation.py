"""New-game confirmation of the frozen repaired gate. Zero model requests.

Reuse existing collection, label review, Worker, Registry and gate scoring.
No sampling replacements, candidate revisions, or online solver entry.
"""
import argparse
from datetime import datetime,timezone
from pathlib import Path
import run_alfworld_route_a_targeted_revision as V

A=V.A; ROOT=V.ROOT


def require_development(root):
    p=V.verify(root)
    g=A.read(root/'generation/result.json');accept=A.read(root/'Semantic_Acceptance.json')
    manifest=A.read(root/'frozen_candidate/manifest.json')
    if not accept['passed'] or not accept['development_passed'] or not accept['engineering_passed']:
        raise PermissionError('development and engineering required')
    if accept['candidate_version']!=g['candidate_version'] or manifest['candidate_version']!=g['candidate_version']:
        raise PermissionError('mixed candidate version')
    V.P.verify_history(accept['receipts'])
    if A.sha(root/'frozen_candidate/gate.py')!=g['code_sha256'] or A.sha(root/'generation/candidate.py')!=g['code_sha256']:
        raise PermissionError('frozen gate changed')
    if A.sha(V.B.CODE)!=g['recovery_sha256'] or manifest['permission']!='SHADOW':
        raise PermissionError('recovery/permission drift')
    if A.sha(V.N.OLD/'online/selection.private.json')!=p['online_selection_sha256']:
        raise PermissionError('online roster changed')
    return p,g


def check_isolation(selected,audit,online):
    if audit['malformed']:raise PermissionError('incomplete fresh exposure audit')
    group={r['task']['group'] for r in selected}
    hashes={r['task']['game_sha256'] for r in selected}
    trajectories={r['task']['trajectory_sha256'] for r in selected}
    if len(group)!=48 or len(selected)!=48:raise PermissionError('48 independent task groups required')
    conflicts=[r for r in audit['protected_games'] if r['task']['group'] in group or r['task']['game_sha256'] in hashes or r['task']['trajectory_sha256'] in trajectories]
    if conflicts:raise PermissionError('new-game exposure/reservation overlap')
    if group & {r['task']['group'] for r in online}:raise PermissionError('online task overlap')
    return True


def freeze(root):
    p,g=require_development(root);out=root/'confirmation'
    if (out/'Stage_Freeze.json').exists():return verify(root)
    if (out/'collection/collection.jsonl').exists():raise PermissionError('cannot freeze after interaction')
    V.P.verify_history(A.read(root/'Closeout_Integrity.json')['files'])
    data=Path(A.read(root/'development/protocol.json')['data_root'])
    audit_path=out/'Fresh_Exposure.private.json'
    if audit_path.exists():audit=A.read(audit_path)
    else:
        audit=V.N.X.A.protection(V.N.X.A.dataset_rows(data),[ROOT/'runs',Path.home()/'.local/share/flowevo'],out)
        A.commit(audit_path,audit)
    selected=A.read(root/'confirmation_selection.private.json')['tasks']
    online=A.read(V.N.OLD/'online/selection.private.json')['tasks']
    check_isolation(selected,audit,online)
    with V.adapter():plan=V.R.freeze(root,'confirmation')
    bindings={str(f):A.sha(f) for f in (Path(__file__).resolve(),ROOT/'scripts/test_alfworld_route_a_independent_confirmation.py',
        root/'Semantic_Acceptance.json',root/'frozen_candidate/gate.py',root/'frozen_candidate/manifest.json',audit_path,
        ROOT/'scripts/analyze_alfworld_route_a_independent_confirmation.py')}
    bindings.update(audit['files'])
    return A.commit(out/'Stage_Freeze.json',dict(status='FROZEN_BEFORE_NEW_GAME_EXECUTION',
        authorized_by='User: 继续下一步 (independent zero-API confirmation; online remains separately authorized)',
        at=datetime.now(timezone.utc).isoformat(),files=bindings,protocol_sha256=A.digest(plan),candidate_version=g['candidate_version'],
        max_model_calls=0,max_api_usd=0,online_authorized=False,permission='SHADOW',
        selected_games=48,selection_sha256=A.sha(root/'confirmation_selection.private.json'),
        rule='Original frozen 48 game order, original labels/scorer and thresholds; unresolved stage/instance labels stay unresolved; no replacements or feedback revisions'))


def verify(root):
    p,g=require_development(root);out=root/'confirmation';s=A.read(out/'Stage_Freeze.json')
    V.P.verify_history(s['files'])
    with V.adapter():plan,selection=V.R.verify(out)
    if s['protocol_sha256']!=A.digest(plan) or s['candidate_version']!=g['candidate_version'] or s['max_model_calls'] or s['max_api_usd'] or s['online_authorized']:
        raise PermissionError('stage freeze mismatch')
    check_isolation(selection['tasks'],A.read(out/'Fresh_Exposure.private.json'),A.read(V.N.OLD/'online/selection.private.json')['tasks'])
    return s


def execute(root,stage):
    verify(root)
    with V.adapter():
        if stage=='preflight' and (root/'confirmation/Preflight.json').exists():
            value=A.read(root/'confirmation/Preflight.json')
            if value['protocol_sha256']!=A.digest(A.read(root/'confirmation/protocol.json')):raise PermissionError('preflight mismatch')
            return value
        return getattr(V.R,stage)(root/'confirmation')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','verify','preflight','collect','review','evaluate']);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.output.resolve()
    result=freeze(root) if a.command=='freeze' else verify(root) if a.command=='verify' else execute(root,a.command)
    print(A.digest(result))
