"""Prepare and run the frozen, public-only ALFWorld B v9 D/S diagnostic."""

import argparse
from collections import Counter
import fcntl
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from alfworld_.decision_diagnostic import (
    CONSISTENCY_VERSION, PROMPTS, SCHEMAS, SCHEMA_VERSION, VERSION, parse_rows, project,
    replay_v8, score_pairs,
)
from alfworld_.recovery_acquisition import RecoveryAdapter, stage_request
from alfworld_.skill_acquisition import INPUT_LIMIT, MODEL
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, save, sha
from failure_evo.network_transport import DEFAULT_POLICY
from failure_evo.run_health import trusted_usage
from run_alfworld_skill_acquisition import create_accounts

ROOT = Path(__file__).resolve().parents[1]
BATCH_SIZE = 6
OUTPUT_UPPER = 4096  # Existing stage_request/replay_train_generation bound, identical across arms.
PRICE = dict(input=30, output=120)  # USD cents per million tokens.
V8_HASH = '2752020e1068eddc9066df33de4b55fd084a71b3302baca988bb62db25ea7ee8'
GOALS = {
    'put some vase on safe.': ('vase', None, 'safe', None),
    'put some spraybottle on drawer.': ('spraybottle', None, 'drawer', None),
    'put a clean bowl in fridge.': ('bowl', None, 'fridge', None),
    'put a cool apple in microwave.': ('apple', None, 'microwave', None),
    'put some book on desk.': ('book', None, 'desk', None),
    'put the vase 7 in the safe 3.': ('vase', 'vase 7', 'safe', 'safe 3'),
    'put some mug in fridge.': ('mug', None, 'fridge', None),
    'heat some potato and put it in garbagecan.': ('potato', None, 'garbagecan', None),
    'put some vase in safe.': ('vase', None, 'safe', None),
    'heat some potato and put it in fridge.': ('potato', None, 'fridge', None),
    'put some apple in microwave.': ('apple', None, 'microwave', None),
    'put some cup in cabinet.': ('cup', None, 'cabinet', None),
    'put some plate in cabinet.': ('plate', None, 'cabinet', None),
    'put some mug in drawer.': ('mug', None, 'drawer', None),
    'put the plate 8 in cabinet 15.': ('plate', 'plate 8', 'cabinet', 'cabinet 15'),
    'put the mug 9 in drawer 16.': ('mug', 'mug 9', 'drawer', 'drawer 16'),
    'put some book in cabinet.': ('book', None, 'cabinet', None),
    'put some book in drawer.': ('book', None, 'drawer', None),
}


def compare_explicit(a, b):
    if a is None or b is None:
        return 'UNKNOWN'
    return 'MATCH' if a == b else 'CONFLICT'


def reference(case):
    """Development annotations from the public snapshot and existing v8 labels."""
    a, b, public = case['A'], case['B'], case['public']
    case_key = case['case_key']
    obj, obj_instance, dest, dest_instance = GOALS[public['goal']]
    # A.object_match merged goal compatibility and current possession. Reuse
    # its categories/local target, and annotate possession/stage independently.
    held_goal, held_failed, changed, completed = 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN'
    if case['role'] == 'source' or public['held_object'] is not None:
        held_goal = compare_explicit(obj_instance or obj, public['held_object'] or a['object_instance'])
        if obj_instance is None:
            held_goal = compare_explicit(obj, a['object_type'])
        held_failed, changed, completed = 'MATCH', 'NO', 'NO'
    if case_key in {'wrong_held_object', 'newly_held_object_differs'}:
        held_goal = 'CONFLICT'
    if case_key in {'already_open', 'wrong_goal_open_safe', 'needs_heating_first', 'obstacle_already_resolved'}:
        held_goal = 'MATCH'  # Public legal move or pickup receipt.
    if case_key == 'obstacle_already_resolved':
        held_failed, completed = 'MATCH', 'NO'
    if case_key in {'newly_held_object_differs', 'subgoal_already_completed'}:
        held_failed, changed = 'CONFLICT', 'YES'
    if case_key == 'subgoal_already_completed':
        completed = 'YES'
    phase = a['phase_match']
    if case_key == 'newly_held_object_differs' or case['category'] == 'object_conflict':
        phase = 'UNKNOWN'  # A possession or category conflict alone does not locate the task stage.
    obstacle = b['failure_unresolved'] if public['failure_step_id'] else 'UNKNOWN'
    resolved = {'YES': 'NO', 'NO': 'YES'}.get(obstacle, 'UNKNOWN')
    facts = dict(
        goal_object_type=obj, goal_object_instance=obj_instance, goal_container_type=dest,
        goal_container_instance=dest_instance, failed_object_type=a['object_type'],
        failed_object_instance=a['object_instance'], failed_container_type=a['target_type'],
        failed_container_instance=a['target_instance'], object_category_match=a['object_type_match'],
        container_category_match=a['target_type_match'],
        object_instance_match=compare_explicit(obj_instance, a['object_instance']),
        container_instance_match=compare_explicit(dest_instance, a['target_instance']),
        held_object_matches_goal=held_goal, held_failed_object_match=held_failed,
        local_target_binding=a['target_match'], phase_match=phase, binding_consistent=b['binding_consistent'],
        obstacle_resolved=resolved, held_object_changed=changed, subgoal_completed=completed,
        failure_step_id=public['failure_step_id'],
    )
    return dict(failure_relevant=b['failure_relevant'], obstacle_present=obstacle,
                recovery_needed=b['recovery_needed'], facts=facts)


def load_v8(v8):
    protocol, cases, result = (read(v8/name) for name in ('protocol.json', 'dataset.private.json', 'result.json'))
    if (fingerprint(protocol) != V8_HASH or result['protocol_sha256'] != V8_HASH
            or fingerprint(cases) != protocol['dataset_sha256']
            or result['scope'] != 'REAL_DIAGNOSTIC_NOT_STRATEGY'
            or Counter(case['role'] for case in cases) != {'source': 4, 'v7_regression': 20, 'fresh_synthetic': 12}
            or len({case['public']['id'] for case in cases}) != 36):
        raise PermissionError('v8 frozen diagnostic inputs mismatch')
    raw = [row['payload']['response'] for row in EvidenceStore(v8/'provider.jsonl').records()
           if row['kind'] == 'RAW_RESPONSE']
    if raw != [receipt['result']['raw_response'] for receipt in result['receipts']] or len(raw) != 12:
        raise PermissionError('v8 saved model responses do not match provider journal')
    return protocol, cases, result


def batches(public):
    for arm in SCHEMAS:
        for start in range(0, len(public), BATCH_SIZE):
            yield arm, start // BATCH_SIZE, dict(cases=public[start:start+BATCH_SIZE])


def request_bounds(public):
    schedule = []
    with TemporaryDirectory() as temporary:
        for arm, batch, payload in batches(public):
            adapter = RecoveryAdapter(Path(temporary)/'unused.jsonl', None, model=MODEL, mock=True,
                sender=lambda _: None, stage='analyze', payload=payload, parser=None, protocol=VERSION,
                analysis_prompt=PROMPTS[arm], max_wire_input_upper=INPUT_LIMIT)
            wire = adapter.preflight(dict(phase='induction', max_tokens=OUTPUT_UPPER,
                discovery=dict(stage='analyze', payload_sha256=fingerprint(payload))))
            schedule.append(dict(arm=arm, batch=batch, input_upper=len(canonical(wire).encode()) + 256,
                                 output_upper=OUTPUT_UPPER, wire_sha256=fingerprint(wire),
                                 case_ids=[case['id'] for case in payload['cases']]))
    return schedule


def history_manifest(v8, protocol):
    pinned = protocol['historical_sha256']
    if any(sha(Path(path)) != digest for path, digest in pinned.items()):
        raise PermissionError('historical v3–v7 run differs from v8 manifest')
    roots = [v8, *sorted(v8.parent.glob('alfworld_recovery_v[3-7]_*')),
             *sorted(v8.parent.glob('alfworld_binding_v8_acceptance_*'))]
    files = {str(file.resolve()): sha(file) for root in roots
             for file in root.rglob('*') if file.is_file()}
    return {**pinned, **files}


def ensure_separate_output(v8, output):
    history_roots = [v8.resolve(), *v8.parent.glob('alfworld_recovery_v[3-7]_*'),
                     *v8.parent.glob('alfworld_binding_v8_*')]
    resolved = output.resolve()
    if any(resolved == path.resolve() or resolved.is_relative_to(path.resolve())
           or path.resolve().is_relative_to(resolved) for path in history_roots):
        raise PermissionError('v9 needs its own directory outside v3–v8 runs')


def plan_for(v8, output, *, mock):
    ensure_separate_output(v8, output)
    old, cases, _ = load_v8(v8)
    public = [project(case['public']) for case in cases]
    refs = {case['public']['id']: reference(case) for case in cases}
    schedule = request_bounds(public)
    input_upper = sum(batch['input_upper'] for batch in schedule)
    output_upper = sum(batch['output_upper'] for batch in schedule)
    reservation = sum((PRICE['output'] * (batch['input_upper'] + batch['output_upper']) + 99) // 100
                      for batch in schedule)
    files = [Path(__file__).resolve(), ROOT/'scripts/test_alfworld_decision_v9.py',
             ROOT/'scripts/run_alfworld_skill_acquisition.py']
    for directory in ('alfworld_', 'failure_evo', 'runtime'):
        files.extend((ROOT/'FlowEvo/src'/directory).glob('*.py'))
    plan = dict(
        version=VERSION, schema_version=SCHEMA_VERSION, consistency_version=CONSISTENCY_VERSION,
        run_id=('mock:' if mock else 'real:') + output.name,
        scope='MOCK_DEVELOPMENT' if mock else 'REAL_PAIRED_DEVELOPMENT_DIAGNOSTIC',
        v8_protocol_sha256=V8_HASH, v8_dataset_sha256=old['dataset_sha256'],
        public_sha256=fingerprint(public), reference_sha256=fingerprint(refs),
        prompts=PROMPTS, schemas=SCHEMAS, schedule=schedule, batch_size=BATCH_SIZE,
        model=MODEL, model_release_reference='DeepSeek-V4.1-Flash-1017',
        temperature=0, thinking='disabled', response_format='json_object',
        input_upper=input_upper, output_upper=output_upper, max_tokens=input_upper+output_upper,
        price_usd_cents_per_million=PRICE,
        price_source='https://api-docs.deepseek.com/quick_start/pricing/',
        quote_upper_usd=(input_upper*PRICE['input']+output_upper*PRICE['output'])/100_000_000,
        max_cost_microusd=reservation, max_calls=len(schedule), worker_calls=0,
        network_policy=DEFAULT_POLICY,
        code_sha256={str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files))},
        historical_sha256=history_manifest(v8, old),
    )
    return plan, cases, public, refs


def grant(plan):
    return dict(paid_api_authorized=True, run_id=plan['run_id'], protocol_hash=fingerprint(plan),
                model=MODEL, protocol=VERSION, max_cost_microusd=plan['max_cost_microusd'])


def shared_protocol(plan):
    return {key: value for key, value in plan.items() if key not in ('scope', 'run_id')}


def prepare(v8, output, mock_output):
    plan, _, public, refs = plan_for(v8, output, mock=False)
    mock_plan = read(mock_output/'protocol.json')
    mock_result = read(mock_output/'result.json')
    if (mock_plan['scope'] != 'MOCK_DEVELOPMENT' or shared_protocol(mock_plan) != shared_protocol(plan)
            or mock_result['scope'] != 'MOCK_DEVELOPMENT'
            or mock_result['protocol_sha256'] != fingerprint(mock_plan)
            or mock_result['paid_requests'] != 0 or mock_result['budget']['calls'] != plan['max_calls']):
        raise PermissionError('matching complete zero-API mock acceptance required')
    # Bind the preflight evidence to authorization as well as the model/data configuration.
    plan['mock_acceptance'] = dict(protocol_sha256=fingerprint(mock_plan),
                                   result_sha256=sha(mock_output/'result.json'))
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    save(output/'protocol.json', plan)
    save(output/'public_input.json', public)
    save(output/'references.private.json', refs)
    save(output/'authorization.template.json', {**grant(plan), 'paid_api_authorized': False})
    return plan


def delivery_counts(receipts):
    issues, requests, usage = Counter(), Counter(), Counter()
    for receipt in receipts:
        raw = receipt['response']['raw_response']
        requests['provider_responses'] += 1
        usage.update(trusted_usage(raw))
        if receipt['response'].get('finish_reason') == 'stop':
            requests['normal_stop'] += 1
        try:
            json.loads(raw['choices'][0]['message']['content'])
        except (ValueError, KeyError, TypeError, IndexError):
            requests['invalid_json'] += 1
        else:
            requests['json_received'] += 1
        parsed = receipt['parsed']
        requests[parsed['envelope']] += 1
        requests['accepted_rows'] += len(parsed['rows'])
        requests['rejected_rows'] += len(parsed['rejected'])
        requests['missing_expected_rows'] += len(parsed['missing'])
        for reject in parsed['rejected']:
            issues.update({error['code'] for error in reject['errors']})
    return dict(requests=dict(requests), rejected_rows_by_error=dict(issues), usage=dict(usage),
                quote_estimated_usd=(usage['input_tokens']*PRICE['input']
                                     + usage['output_tokens']*PRICE['output'])/100_000_000)


def run(v8, output, *, sender=None, authorization=None):
    mock = sender is not None
    plan, cases, public, refs = plan_for(v8, output, mock=mock)
    frozen = read(output/'protocol.json') if (output/'protocol.json').exists() else None
    if not mock:
        if frozen is None or 'mock_acceptance' not in frozen:
            raise PermissionError('prepared v9 protocol required')
        plan['mock_acceptance'] = frozen['mock_acceptance']
        if authorization != grant(plan):
            raise PermissionError('new matching v9 authorization required')
    if frozen is not None and frozen != plan:
        raise PermissionError('frozen protocol drift')
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (output/'protocol.json').exists() and read(output/'protocol.json') != plan:
            raise PermissionError('frozen protocol drift')
        if mock:
            save(output/'protocol.json', plan)
            save(output/'public_input.json', public)
            save(output/'references.private.json', refs)
        elif (read(output/'public_input.json') != public or read(output/'references.private.json') != refs):
            raise PermissionError('frozen public input or reference copy drift')
        budget = create_accounts(output, plan)
        receipts = {arm: [] for arm in SCHEMAS}
        predictions = {arm: {} for arm in SCHEMAS}
        checks = {arm: {} for arm in SCHEMAS}
        for (arm, batch, payload), spec in zip(batches(public), plan['schedule'], strict=True):
            batch_cases = payload['cases']
            response = stage_request(output, f'{arm}_{batch:02}', 'analyze', payload,
                lambda value: parse_rows(value, arm, batch_cases), budget, sender=sender,
                authorization=authorization, network_policy=None if mock else plan['network_policy'],
                protocol=VERSION, analysis_prompt=PROMPTS[arm])
            if response['wire_sha256'] != spec['wire_sha256']:
                raise PermissionError('wire receipt differs from frozen schedule')
            if response.get('parse_status'):
                parsed = dict(envelope='PROVIDER_DELIVERY_REJECTED', rows={}, consistency={}, rejected=[],
                              missing=[case['id'] for case in batch_cases])
            else:
                parsed = json.loads(response['specification'])
            predictions[arm].update(parsed['rows'])
            checks[arm].update(parsed['consistency'])
            receipts[arm].append(dict(batch=batch, response=response, parsed=parsed))
        result = dict(
            scope=plan['scope'], protocol_sha256=fingerprint(plan), budget=budget.snapshot(),
            paid_requests=0 if mock else sum(map(len, receipts.values())),
            receipts=receipts, model_predictions=predictions, consistency_checks=checks,
            reference_evaluation=score_pairs(cases, refs, predictions, checks),
            delivery={arm: delivery_counts(rows) for arm, rows in receipts.items()},
        )
        save(output/'result.json', result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run', 'replay-v8'))
    parser.add_argument('--v8', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--mock-output', type=Path)
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        if args.mock_output is None:
            parser.error('prepare requires --mock-output')
        plan = prepare(args.v8, args.output, args.mock_output)
        print(canonical(dict(status='PREPARED_NOT_AUTHORIZED', protocol_sha256=fingerprint(plan),
                             max_calls=plan['max_calls'], max_cost_microusd=plan['max_cost_microusd'])))
    elif args.action == 'replay-v8':
        ensure_separate_output(args.v8, args.output)
        _, cases, original = load_v8(args.v8)
        args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
        save(args.output/'v8_read_only_audit.json', replay_v8(cases, original))
    else:
        if args.authorization is None:
            parser.error('run requires --authorization')
        result = run(args.v8, args.output, authorization=read(args.authorization))
        print(canonical(dict(status='COMPLETE', paid_requests=result['paid_requests'],
                             delivery=result['delivery'])))


if __name__ == '__main__':
    main()
