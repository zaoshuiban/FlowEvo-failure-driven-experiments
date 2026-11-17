"""B3 prospective metadata only. Never opens an environment or model channel."""
import argparse
from pathlib import Path
import run_alfworld_container_information as E
import run_alfworld_a4_confirmatory as A
from alfworld_.route_b_runtime import RecoveryBridge
from types import SimpleNamespace
P=E.P

def paired_bridge(native,policy,checkpoint,library_snapshot,expected_library_sha):
    """Thin shared-budget adapter; native construction and calls stay upstream.

    This is offline checkpoint evaluation, not Registry publication. Caller must
    supply the already-bound native generator and an approved evaluation policy.
    """
    if P.fingerprint(library_snapshot)!=expected_library_sha:raise PermissionError('native library snapshot mismatch')
    length=len(checkpoint['history'])
    if length>=50:raise ValueError('no remaining environment steps')
    if policy is None:
        policy=SimpleNamespace(native=native,states={},used=[],errors=set(),finalize=lambda trace:None)
        opportunities=0
    else:
        if policy.native is not native:raise PermissionError('different native fallback')
        opportunities=1
    return RecoveryBridge(policy,episode_limit=min(50,length+18),window=min(18,50-length),max_opportunities=opportunities)

def prepare(preparation,out):
    if out.exists():raise FileExistsError('do not replace a prospective pool')
    p=P.read(preparation/'protocol.json');out.mkdir(mode=0o700,parents=True)
    rows=A.dataset_rows(Path(p['data_root']))
    audit=A.protection(rows,[E.ROOT/'runs',Path.home()/'.local/share/flowevo'],out)
    # Existing frozen allocations remain protected; never resample the current
    # experiment by rerunning preparation after observing candidate performance.
    types=('pick_and_place_simple','pick_clean_then_place_in_recep','pick_heat_then_place_in_recep','pick_cool_then_place_in_recep')
    # Reuse A4's metadata-only collection scope; never pass these names or
    # collection policies to a learner as a recovery strategy.
    targets=('Cabinet','Drawer','Fridge','Microwave','Safe')
    eligible=[r for r in audit['eligible'] if r['task']['split']=='train' and r['task']['task_type'] in types
        and r['task']['group'].rsplit('-',2)[-2] in targets]
    ordered=sorted(eligible,key=lambda r:P.fingerprint(['B3_PROSPECTIVE_V1',r['task']['game_sha256']]))
    P.commit(out/'exposure.private.json',audit)
    P.commit(out/'selection.private.json',dict(tasks=[dict(r,role='PROSPECTIVE_EVAL_ONLY_NOT_LEARNING') for r in ordered[:12]],
        rule='A4 container metadata scope; fixed SHA order; prior game/trajectory/group excluded; scene stratification only',seed='B3_PROSPECTIVE_V1',replacement_allowed=False))
    result=dict(status='METADATA_ONLY_PENDING_COLLECTION' if len(ordered)>=12 and not audit['malformed'] else 'BLOCKED',
        eligible=len(eligible),selected=min(12,len(ordered)),scenes=len({r['task']['scene'] for r in ordered[:12]}),
        strict_scene=sum(r['stratum']=='strict_scene' for r in ordered[:12]),malformed=audit['malformed'],
        environment_resets=0,candidate_executions=0,model_requests=0)
    P.commit(out/'readiness.json',result);return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preparation',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();print(P.canonical(prepare(a.preparation.resolve(),a.output.resolve())))
