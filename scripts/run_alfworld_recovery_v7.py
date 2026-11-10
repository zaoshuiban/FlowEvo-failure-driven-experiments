"""Zero-API preparation and explicitly authorized B v7 fixed-mechanism runner."""
import argparse
from pathlib import Path

from alfworld_.recovery_acquisition import RECOVERY_SOURCE_CONTRACT
from failure_evo.contracts import fingerprint
from failure_evo.math_stream import read, sha
from run_alfworld_recovery_v6 import ROOT, freeze as freeze_v6, prepare as prepare_pilot, run as run_pilot

VERSION = 'alfworld-recovery-acquisition-v7'
MOCK_SCOPE = 'MOCK_B_V7'
REQUIREMENTS = """
Fixed-mechanism study: design a new post-failure policy from the supplied public
evidence. Separate Failure Validity, Target Binding and Recovery Decision.
History position alone does not determine validity. Consider all intervening
public state changes, including changes in goal, possession, destination identity
or subgoal completion. A later observation need not invalidate relevant evidence.
Require coherent evidence that a failure still blocks the current goal. Confirm
the task object, held instance, intended destination instance, failed action and
final delivery phase are consistent. Decline when evidence conflicts or is
insufficient. If the obstacle has already been removed outside your current
recovery, leave the next normal step to the native agent. Any continuation
requires evidence of your own ongoing recovery and the same unresolved objective.
Do not pick a command just because it is legal. Use reason to identify the first
unsupported decision if possible, with no new output fields.

Static source delivery: exactly one JSON object with three nonempty strings
code, description, applicability. code is plain Python, no Markdown, at most
65536 UTF-8 bytes. At module scope use only allowed imports, literal data
assignments and plain function definitions. No import-time calls, including
re.compile, and no computed constants, self-tests, decorators, annotations or
default argument values. For regular expressions use literal pattern strings
at module scope, and perform matching or compilation only inside functions.
"""


def freeze(*paths, mock):
    plan, payload, protocol, events, host, checkpoints, negatives = freeze_v6(*paths,mock=mock)
    base=paths[0].parent
    old=base/'alfworld_recovery_v6_pilot_20261110_01'
    revision=base/'alfworld_recovery_v6_engineering_revision_20261110_01'
    old_plan=read(old/'protocol.json')
    old_result=read(old/'result.json')
    revision_plan=read(revision/'protocol.json')
    revision_result=read(revision/'result.json')
    if (fingerprint(old_plan)!=old_result['protocol_sha256']
            or old_result['candidate']['status']!='STATIC_REJECTED'
            or fingerprint(revision_plan)!=revision_result['protocol_sha256']
            or revision_plan['parent_protocol_sha256']!=old_result['protocol_sha256']
            or revision_plan['validation_sha256']!=plan['validation_sha256']
            or read(old/'validation.private.json')!=dict(checkpoints=checkpoints,negatives=negatives)
            or read(revision/'validation.private.json')!=dict(checkpoints=checkpoints,negatives=negatives)
            or sha(revision/'original_model_policy.py')!=old_result['candidate']['check']['source_sha256']
            or sha(revision/'revised_policy.py')!=revision_plan['revision_sha256']
            or len(negatives)!=20):
        raise PermissionError('v6 comparator or validation identity changed')
    history={}
    for version in (3,4,5,6):
        run=base/f'alfworld_recovery_v{version}_pilot_20261110_01'
        for name in ('protocol.json','result.json','provider.jsonl','budget.jsonl'):
            path=run/name
            history[str(path.relative_to(base))]=sha(path)
    for name in ('protocol.json','result.json','original_model_policy.py','revised_policy.py','source.diff'):
        path=revision/name
        history[str(path.relative_to(base))]=sha(path)
    for path in (Path(__file__).resolve(),ROOT/'scripts/test_alfworld_recovery_v7.py'):
        plan['code_sha256'][str(path.relative_to(ROOT))]=sha(path)
    plan.update(version=VERSION,scope=MOCK_SCOPE if mock else 'REAL_B_V7_SOURCE_ONLY',
        generation_requirements_sha256=fingerprint(REQUIREMENTS),
        generation_system_sha256=fingerprint(RECOVERY_SOURCE_CONTRACT+REQUIREMENTS),
        historical_sha256=history,model_release='DeepSeek-V4.1-Flash-1017',
        thinking='disabled',temperature=0,response_format='json_object',max_output_tokens=4096,
        price_per_million_usd=dict(peak_uncached_input=.30,peak_output=1.20),
        request_estimate_usd=.024576,reservation_upper_usd=.083559)
    return plan,payload,protocol,events,host,checkpoints,negatives


def run(paths, **kwargs):
    return run_pilot(paths,freeze_fn=freeze,requirements=REQUIREMENTS,**kwargs)


def prepare(args):
    return prepare_pilot(args,freeze_fn=freeze,mock_scope=MOCK_SCOPE)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','run'))
    for key in ('source','v4','audit-v4','v5','diagnostic','output'):
        parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--mock-run',type=Path)
    parser.add_argument('--authorization',type=Path)
    args=parser.parse_args()
    args.paths=(args.source,args.v4,args.audit_v4,args.v5,args.diagnostic,args.output)
    if args.action=='prepare':
        if args.mock_run is None:
            parser.error('prepare requires --mock-run')
        prepare(args)
    else:
        if args.authorization is None:
            parser.error('run requires --authorization')
        result=run(args.paths,authorization=read(args.authorization))
        print(result['candidate']['status'])
