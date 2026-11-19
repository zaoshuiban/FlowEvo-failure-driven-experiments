"""One targeted model revision with an executable semantic acceptance barrier.

Reuse the existing one-request ledger, gate adapter, Worker and development
runner. No host-written candidate. New games and online execution have no CLI.
"""
import argparse
import ast
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import prepare_alfworld_route_a_prerequisites_v2 as N
import run_alfworld_route_a_prerequisites_v2 as R
import check_alfworld_route_a_prerequisite_forms as E

A=N.A; P=N.P; B=N.B; ROOT=N.ROOT
PARENT=ROOT/'runs/alfworld_route_a_prerequisites_v2_20261117_01'
VERSION='route-a-targeted-processing-revision-v3'
POLICY=dict(N.POLICY,max_wire_input_bytes=48000,max_input_tokens=48256)
PROMPT=N.REVISION_PROMPT+'''
This is a FUNCTIONAL REPAIR of the supplied accepted Python gate, not a cleanup.
Its previous revision claimed that adjective prerequisites were handled, but
actual Worker tests retained three unsupported MATCH decisions. The supplied
function diagnostic identifies the executing predicate, not merely a wording issue.

Inspect the goal parsing -> processing requirement -> same-instance evidence ->
MATCH path. A goal's processing modifier must survive object-name normalization.
Adjectival and verbal requirements must produce the appropriate execution
precondition; missing successful processing evidence must not mean no processing
was requested. Processing a different object, merely attempting an action, or
being allowed to open a receptacle does not satisfy that precondition. Do not
regress ordinary placement where no processing is requested. Ambiguous or
unsupported requirements must not silently collapse to unrestricted placement.

Do not just reformat the old program or repeat the claim in the description.
Deliver complete source with the functional change actually implemented. In the
existing description field identify the changed function and the behavior it
changes. Do not add JSON fields or output tests. No host implementation, hidden
state, future game, Rule code or reference recovery route is supplied. The
recovery algorithm stays frozen. You may ABSTAIN rather than assert a repair
you cannot implement. This run allows ONE request, no replacement sampling.
Keep each gate reason <=400 characters and source within 4096 output tokens.
'''


def packet():
    result=A.read(PARENT/'generation/result.json')
    source=(PARENT/'generation/candidate.py').read_text()
    if A.sha(PARENT/'generation/candidate.py')!=result['code_sha256']:raise PermissionError('parent changed')
    funcs={n.name:ast.get_source_segment(source,n) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
    samples=A.read(N.OLD/'checkpoints.private.json')['samples']
    rows={r['sample_id']:r for r in A.read(PARENT/'development/result.json')['rows']}
    chosen=[s for s in samples if rows[s['sample_id']]['score']['unsupported_recovery']]
    for task_type in N.V.TYPES:
        chosen.append(next(s for s in samples if s['label']=='MATCH' and s['task_type']==task_type))
    return dict(previous_code=source,parent_code_sha256=result['code_sha256'],
        parent_version=result['candidate_version'],recovery_sha256=N.X.EXPECTED['S0'],
        recovery_code=N.B.CODE.read_text(),
        diagnostics=dict(stage='FUNCTIONAL_BEHAVIOR_NOT_FORMAT',
            current_requirement_function=funcs['_processing_required'],
            current_object_normalization=funcs['_strip_adj'],
            observed_mismatch='Three actual hot-object incomplete public views remained MATCH. The code tests only standalone heat/cool/clean tokens while stripping processing adjectives from the object name.',
            candidate_claim='Prior response claimed adjective processing was evidenced; this was NOT verified.'),
        feedback=[N.public_feedback(s,rows[s['sample_id']]) for s in chosen],
        scope='SEVEN_EXPOSED_REAL_DEVELOPMENT_VIEWS_NO_ENGINEERING_CASES_OR_INDEPENDENT_DATA')


def prepare(root):
    if (root/'generation/protocol.json').exists():return verify(root)
    P.verify_history(A.read(PARENT/'Closeout_Integrity.json')['files'])
    parent=A.read(PARENT/'generation/protocol.json');data=packet()
    wire=B.wire(root/'generation',data,PROMPT,0,POLICY)
    files=dict(parent['source_files'])
    for f in [Path(__file__).resolve(),ROOT/'scripts/test_alfworld_route_a_targeted_revision.py',
              PARENT/'generation/candidate.py',PARENT/'generation/result.json',PARENT/'development/result.json',
              PARENT/'Morphology_Fixtures.private.json',PARENT/'Morphology_Freeze.json',Path(E.__file__).resolve()]:
        files[str(f)]=A.sha(f)
    for name in ('exposure.private.json','confirmation_selection.private.json','Morphology_Fixtures.private.json','Morphology_Freeze.json'):
        A.commit(root/name,A.read(PARENT/name))
    A.commit(root/'generation/input.private.json',data);A.commit(root/'generation/wire.private.json',wire)
    plan=dict(version=VERSION,run_id=root.name+'-generation',model='deepseek-flash',temperature=0,
        max_calls=1,max_tokens=POLICY['max_input_tokens']+4096,max_cost_microusd=1000000,worker_calls=0,
        input_policy=POLICY,input_sha256=A.sha(root/'generation/input.private.json'),wire_sha256=A.digest(wire),
        prompt_sha256=A.digest(PROMPT),source_files=files,
        parent_candidate=dict(path=str(PARENT/'generation/candidate.py'),sha256=data['parent_code_sha256']),
        frozen_recovery=parent['frozen_recovery'],
        independent_selection_sha256=parent['independent_selection_sha256'],
        exposure_sha256=parent['exposure_sha256'],online_selection_sha256=parent['online_selection_sha256'],
        engineering_fixtures_sha256=A.sha(root/'Morphology_Fixtures.private.json'),
        semantic_acceptance='All 61 exposed development records retain positives with no unsafe/error, AND all 30 engineering assertions pass; never a publication authority.',
        authorization_status='PENDING_EXPLICIT_NEW_AUTHORIZATION',online_authorized=False,
        scope='TARGETED_DEVELOPMENT_REPAIR_ONLY_NO_NEW_GAMES',
        historical_engineering_cases_remain_model_input_forbidden=True,
        cost_note='Ledger upper-bound reserve, not actual supplier charge',
        estimated_reservation_upper_usd=(POLICY['max_input_tokens']+4096)*1.2/1000000)
    A.commit(root/'generation/protocol.json',plan)
    return plan


def verify(root):
    p=A.read(root/'generation/protocol.json');P.verify_history(p['source_files'])
    if p['version']!=VERSION or p['max_calls']!=1 or p['max_cost_microusd']!=1000000 or p['online_authorized']:
        raise PermissionError('scope')
    for f,k in [('generation/input.private.json','input_sha256'),('exposure.private.json','exposure_sha256'),
                ('confirmation_selection.private.json','independent_selection_sha256'),('Morphology_Fixtures.private.json','engineering_fixtures_sha256')]:
        if A.sha(root/f)!=p[k]:raise PermissionError('frozen data drift')
    if A.sha(N.OLD/'online/selection.private.json')!=p['online_selection_sha256']:raise PermissionError('online roster drift')
    wire=B.wire(root/'generation',A.read(root/'generation/input.private.json'),PROMPT,0,POLICY)
    if A.digest(wire)!=p['wire_sha256'] or A.digest(PROMPT)!=p['prompt_sha256']:raise PermissionError('wire drift')
    return p


@contextmanager
def adapter():
    # Scope only protocol configuration/verification; the exact original durable
    # request/Worker/Registry implementations remain unchanged and hash-bound.
    with patch.object(N,'VERSION',VERSION),patch.object(N,'PROMPT',PROMPT),patch.object(N,'POLICY',POLICY),patch.object(N,'verify_preparation',side_effect=verify):
        yield


def authorization(p):
    return dict(run_id=p['run_id'],protocol_hash=A.digest(p),model=p['model'],protocol=VERSION+':'+A.digest(p),
        max_cost_microusd=p['max_cost_microusd'],paid_api_authorized=True)


def generate(root,auth=None,sender=None):
    with adapter():return N.generate(root,authorization=auth,sender=sender)


def development(root):
    with adapter():
        R.freeze(root,'development')
        if not (root/'development/Preflight.json').exists():R.preflight(root/'development')
        return R.evaluate(root/'development')


def engineering(root):
    with adapter():return E.run(root)


def semantic_acceptance(development_result, engineering_result, version):
    if development_result['candidate_version']!=version or engineering_result['candidate_version']!=version:
        raise PermissionError('mixed candidate versions')
    passed=development_result['passed'] is True and engineering_result['passed'] is True
    return dict(status='DEVELOPMENT_REPAIR_VERIFIED' if passed else 'DEVELOPMENT_NO_GO',passed=passed,
        candidate_version=version,development_passed=development_result['passed'],engineering_passed=engineering_result['passed'],
        independent_validation_passed=False,published=False,online_authorized=False,
        next_step='Independent verification must still satisfy its separately frozen coverage/safety conditions.' if passed else 'Keep artifacts; no automatic further revision or new games.')


def accept(root):
    verify(root);g=A.read(root/'generation/result.json')
    dev=A.read(root/'development/Readiness.json');forms=A.read(root/'engineering_forms/result.json')
    # Bind acceptance to complete immutable execution inputs, not a model claim.
    with adapter():R.verify(root/'development')
    manifest=A.read(root/'engineering_forms/protocol.json')
    if manifest['candidate_sha256']!=g['code_sha256'] or manifest['fixtures_sha256']!=A.sha(root/'Morphology_Fixtures.private.json'):
        raise PermissionError('engineering receipt binding')
    result=semantic_acceptance(dev,forms,g['candidate_version'])
    result['receipts']={str(f):A.sha(f) for f in (root/'development/result.json',root/'development/Readiness.json',root/'engineering_forms/result.json')}
    return A.commit(root/'Semantic_Acceptance.json',result)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','verify','generate','development','engineering','accept'])
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--authorization',type=Path)
    args=parser.parse_args();root=args.output.resolve()
    r=generate(root,A.read(args.authorization) if args.authorization else None) if args.command=='generate' else globals()[args.command](root)
    print(A.digest(r))
