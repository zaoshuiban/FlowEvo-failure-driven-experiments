"""Freeze or run the single-proposal, Shadow-only B v10 condition experiment."""

import argparse
import fcntl
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from alfworld_.decision_diagnostic import decision_scores, project
from alfworld_.precondition_diagnostic import (
    CHECKER_VERSION, OPERATORS, PROMPT, RULES, SCHEMA_VERSION, SELECTORS, VERSION,
    evaluate_development, parse_candidate,
)
from alfworld_.recovery_acquisition import RecoveryAdapter, recovery_view, stage_request
from alfworld_.skill_acquisition import INPUT_LIMIT, MODEL
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, save, sha
from failure_evo.run_health import trusted_usage
from run_alfworld_decision_v9 import ROOT, load_v8
from run_alfworld_recovery_v5 import prepare as audit_v4_mechanism
from run_alfworld_skill_acquisition import create_accounts

SOURCE = 'alfworld_full_library_online120_20261109_01'
V4 = 'alfworld_recovery_v4_pilot_20261110_01'
V4_AUDIT = 'alfworld_recovery_v4_development_audit_20261110_01'
V8 = 'alfworld_binding_v8_pilot_20261111_01'
V9 = 'alfworld_decision_v9_pilot_20261111_01'
V9_CONTINUATION = 'alfworld_decision_v9_continuation_20261111_01'
OUTPUT_UPPER = 4096
PRICE = {'input_cents_per_million': 30, 'output_cents_per_million': 120}
SYSTEM = PROMPT + '\nFrozen interface: ' + canonical(dict(
    selectors=SELECTORS, operators=OPERATORS, limits=RULES,
    extension_policy='Unrecognized named operators are recorded as unsupported and cannot permit recovery.',
))


def source_payload(base, output):
    provenance, _, mechanism, _, _, events, host, _ = audit_v4_mechanism(
        base/SOURCE, base/V4, base/V4_AUDIT, output,
    )
    selected = [event for event in events if event['evidence_id'] in mechanism['evidence_ids']]
    if len(selected) != 11 or set(mechanism['evidence_ids']) != {event['evidence_id'] for event in selected}:
        raise PermissionError('B v4 source evidence drift')
    projected = []
    for event in selected:
        origin = host[event['evidence_id']]
        commands = origin['steps'][event['anchor']-1]['commands']
        view = recovery_view(event, commands)
        projected.append({key:view[key] for key in ('evidence_id', 'goal', 'initial_observation',
                                                     'failure_step_id', 'steps', 'anchor_admissible_commands')})
    payload = dict(mechanism=mechanism, source_receipts=projected)
    ids = {step[0] for event in projected for step in event['steps']}
    if len(ids) != sum(len(event['steps']) for event in projected):
        raise PermissionError('ambiguous learning evidence scope')
    return payload, ids, provenance


def historical_snapshot(base):
    v9, child = base/V9, base/V9_CONTINUATION
    old_plan = read(v9/'protocol.json')
    child_plan = read(child/'protocol.json')
    if (child_plan['parent_protocol_sha256'] != fingerprint(old_plan)
            or any(sha(v9/name) != digest for name, digest in child_plan['parent_artifact_sha256'].items())):
        raise PermissionError('B v9 parent provenance changed')
    events = EvidenceStore(v9/'provider.jsonl').records()
    pending = [row['payload'] for row in events if row['kind'] == 'SEND_UNKNOWN']
    expected = next(row for row in old_plan['schedule'] if row['arm']=='S' and row['batch']==3)
    if len(pending) != 1 or not any(
            row['kind'] == 'SEND_STARTED' and row['payload']['key'] == pending[0]['key']
            and row['payload']['wire_sha256'] == expected['wire_sha256'] for row in events):
        raise PermissionError('B v9 unknown request differs from the audited S_03')
    if any(row['kind'] == 'RAW_RESPONSE' and row['payload']['key'] == pending[0]['key'] for row in events):
        raise PermissionError('B v9 S_03 unexpectedly has a receipt')
    ledger = EvidenceStore(v9/'budget.jsonl').records()
    if not any(row['kind']=='UNKNOWN' and row['payload']['request_id']==pending[0]['request_id'] for row in ledger):
        raise PermissionError('B v9 unknown ledger entry missing')
    pinned = old_plan['historical_sha256']
    if any(sha(path) != digest for path, digest in pinned.items()):
        raise PermissionError('B v3–v8 history drift')
    files = [p for root in (v9, child) for p in root.rglob('*') if p.is_file()]
    return {**pinned, **{str(path.resolve()):sha(path) for path in files}}, old_plan


def protocol(base, output, mock):
    historical, v9 = historical_snapshot(base)
    roots = [base/SOURCE, *(base.glob('alfworld_recovery_v[3-7]_*')),
             *(base.glob('alfworld_binding_v8_*')), *(base.glob('alfworld_decision_v9_*'))]
    if any(output.resolve().is_relative_to(path.resolve()) or path.resolve().is_relative_to(output.resolve())
           for path in roots):
        raise PermissionError('v10 output must be separate from existing source and diagnostic runs')
    payload, evidence_ids, provenance = source_payload(base, output)
    _, cohort, _ = load_v8(base/V8)
    public = [project(row['public']) for row in cohort]
    refs = {row['public']['id']:dict(role=row['role'], recovery_needed=row['B']['recovery_needed'])
            for row in cohort}
    if fingerprint(public) != v9['public_sha256']:
        raise PermissionError('v10 validation projection differs from v9')
    with TemporaryDirectory() as temp:
        adapter = RecoveryAdapter(Path(temp)/'preflight.jsonl', None, model=MODEL,
            mock=True, sender=lambda _: None, stage='analyze', payload=payload, parser=None,
            max_wire_input_upper=INPUT_LIMIT, protocol=VERSION, analysis_prompt=SYSTEM)
        wire = adapter.preflight(dict(phase='induction', max_tokens=OUTPUT_UPPER,
            discovery=dict(stage='analyze', payload_sha256=fingerprint(payload))))
    input_upper = len(canonical(wire).encode())+256
    files = [Path(__file__).resolve(), ROOT/'scripts/run_alfworld_recovery_v5.py',
             ROOT/'scripts/evaluate_alfworld_recovery_development.py', ROOT/'scripts/run_alfworld_decision_v9.py',
             ROOT/'scripts/run_alfworld_skill_acquisition.py', ROOT/'scripts/test_alfworld_precondition_v10.py']
    for directory in ('alfworld_', 'failure_evo', 'runtime'):
        files.extend((ROOT/'FlowEvo/src'/directory).glob('*.py'))
    plan = dict(
        version=VERSION, schema_version=SCHEMA_VERSION, checker_version=CHECKER_VERSION,
        scope='MOCK_CONDITION_DIAGNOSTIC' if mock else 'REAL_CONDITION_DEVELOPMENT_SHADOW',
        run_id=('mock:' if mock else 'real:')+output.name, model=MODEL,
        model_release_reference='DeepSeek-V4.1-Flash-1017', thinking='disabled', temperature=0,
        response_format='json_object', prompt_sha256=fingerprint(SYSTEM),
        learning_sha256=fingerprint(payload), public_sha256=fingerprint(public), reference_sha256=fingerprint(refs),
        wire_sha256=fingerprint(wire), v4_mechanism_sha256=provenance['selected_mechanism_sha256'],
        v4_raw_response_sha256=provenance['v4_response_sha256'],
        v9_unknown_batch='S_03', historical_sha256=historical,
        code_sha256={str(path.relative_to(ROOT)):sha(path) for path in sorted(set(files))},
        learning_calls=1, validation_model_calls=0, max_calls=1, worker_calls=0,
        input_upper=input_upper, output_upper=OUTPUT_UPPER, max_tokens=input_upper+OUTPUT_UPPER,
        price=PRICE, price_source='https://api-docs.deepseek.com/quick_start/pricing/',
        quote_upper_usd=(PRICE['input_cents_per_million']*input_upper
                         + PRICE['output_cents_per_million']*OUTPUT_UPPER)/100_000_000,
        max_cost_microusd=(PRICE['output_cents_per_million']*(input_upper+OUTPUT_UPPER)+99)//100,
        network_policy=v9['network_policy'], disposition='SHADOW_DIAGNOSTIC_ONLY',
    )
    return plan, payload, evidence_ids, public, refs


def grant(plan):
    return dict(run_id=plan['run_id'], protocol_hash=fingerprint(plan), model=MODEL, protocol=VERSION,
                max_cost_microusd=plan['max_cost_microusd'], paid_api_authorized=True)


def shared(plan):
    return {key:value for key,value in plan.items() if key not in {'run_id', 'scope', 'mock_acceptance'}}


def prepare(base, output, mock_output):
    plan, payload, _, public, refs = protocol(base, output, False)
    mock_plan, result = read(mock_output/'protocol.json'), read(mock_output/'result.json')
    if (mock_plan['scope'] != 'MOCK_CONDITION_DIAGNOSTIC' or shared(plan) != shared(mock_plan)
            or result['protocol_sha256'] != fingerprint(mock_plan) or result['scope'] != mock_plan['scope']
            or result['paid_requests'] != 0 or result['budget']['calls'] != 1
            or result['proposal']['status'] != 'CANDIDATE_DELIVERED'
            or result['validation']['by_role']['all']['evaluable'] != len(public)):
        raise PermissionError('matching one-call end-to-end mock acceptance required')
    plan['mock_acceptance'] = dict(protocol_sha256=fingerprint(mock_plan), result_sha256=sha(mock_output/'result.json'))
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    save(output/'protocol.json', plan)
    save(output/'learning.public.json', payload)
    save(output/'validation.public.json', public)
    save(output/'references.private.json', refs)
    save(output/'authorization.template.json', {**grant(plan), 'paid_api_authorized':False})
    return plan


def run(base, output, *, sender=None, authorization=None):
    mock = sender is not None
    plan, payload, ids, public, refs = protocol(base, output, mock)
    frozen_path = output/'protocol.json'
    if not mock:
        if not frozen_path.exists():
            raise PermissionError('prepare a separate v10 protocol before sending')
        plan['mock_acceptance'] = read(frozen_path)['mock_acceptance']
        if authorization != grant(plan):
            raise PermissionError('exact independent B v10 authorization required')
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if frozen_path.exists() and read(frozen_path) != plan:
            raise PermissionError('v10 protocol drift')
        if mock:
            save(frozen_path, plan)
        elif any(read(output/name) != expected for name, expected in (
                ('learning.public.json', payload), ('validation.public.json', public), ('references.private.json', refs))):
            raise PermissionError('frozen v10 data copy changed')
        budget = create_accounts(output, plan)
        response = stage_request(output, 'P', 'analyze', payload, lambda value:parse_candidate(value, ids),
            budget, sender=sender, authorization=authorization, protocol=VERSION,
            network_policy=None if mock else plan['network_policy'], analysis_prompt=SYSTEM)
        if response['wire_sha256'] != plan['wire_sha256']:
            raise PermissionError('v10 response does not match the frozen wire')
        proposal = (dict(status='PROPOSAL_DELIVERY_REJECTED', reason=response.get('contract_diagnostic'),
                         candidate=None) if response.get('parse_status') else json.loads(response['specification']))
        candidate = proposal['candidate']
        timing_start = perf_counter_ns()
        validation = evaluate_development(candidate, public, refs) if candidate else None
        elapsed = perf_counter_ns()-timing_start
        usage = trusted_usage(response['raw_response'])
        estimated = (PRICE['input_cents_per_million']*usage['input_tokens']
                     + PRICE['output_cents_per_million']*usage['output_tokens'])/100_000_000
        historical_d = read(base/V9_CONTINUATION/'result.json')['model_predictions']['D']
        if historical_d.keys() != refs.keys():
            raise PermissionError('historical direct baseline coverage differs from validation')
        result = dict(
            historical_direct=dict(scope='B_V9_DESCRIPTIVE_ONLY', scores=decision_scores(refs,refs,historical_d)),
            scope=plan['scope'], protocol_sha256=fingerprint(plan), proposal=proposal, validation=validation,
            budget=budget.snapshot(), response=response, usage=usage, quote_estimated_usd=estimated,
            paid_requests=0 if mock else 1, disposition=plan['disposition'],
            generation=dict(proposed=int(candidate is not None or proposal['status']=='INVALID_CONDITION'
                                         and proposal.get('submitted_conditions',0)>0),
                submitted_conditions=(len(candidate['conditions']) if candidate else proposal.get('submitted_conditions',0)),
                source_bound_conditions=len(candidate['conditions']) if candidate else 0,
                supported_conditions=(len(candidate['conditions'])-len(proposal['unsupported_conditions'])
                                      if candidate else 0)),
        )
        saved = output/'result.json'
        if saved.exists():
            previous = read(saved)
            timing = previous.pop('validation_elapsed_ns')
            if previous != result:
                raise PermissionError('v10 replay differs from saved result')
            elapsed = timing
        result['validation_elapsed_ns'] = elapsed
        if any(sha(path) != digest for path,digest in plan['historical_sha256'].items()):
            raise PermissionError('historical artifact changed during v10')
        save(saved, result)
        return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('action', choices=('prepare', 'run'))
    cli.add_argument('--base', type=Path, default=Path.home()/'.local/share/flowevo')
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--mock-output', type=Path)
    cli.add_argument('--authorization', type=Path)
    args = cli.parse_args()
    if args.action == 'prepare':
        if args.mock_output is None:
            cli.error('prepare requires --mock-output')
        plan = prepare(args.base, args.output, args.mock_output)
        print(canonical(dict(status='PREPARED_NOT_AUTHORIZED', protocol_sha256=fingerprint(plan),
                             max_cost_microusd=plan['max_cost_microusd'], max_tokens=plan['max_tokens'])))
    else:
        if args.authorization is None:
            cli.error('run requires --authorization')
        result = run(args.base, args.output, authorization=read(args.authorization))
        print(canonical(dict(status=result['proposal']['status'], disposition=result['disposition'],
                             paid_requests=result['paid_requests'])))


if __name__ == '__main__':
    main()
