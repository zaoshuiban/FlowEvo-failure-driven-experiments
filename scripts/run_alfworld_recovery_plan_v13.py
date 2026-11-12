"""Source-only B v13 Pilot on the frozen B v12 mechanisms and checkpoints."""

import argparse
from collections import Counter
import fcntl
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from alfworld_.failure_learning import EnvironmentPolicyRunner, context_view, register_environment_candidate
from alfworld_.generic_recovery_skill import parse_command, receipt_truth, worker_source
from alfworld_.recovery_acquisition import RecoveryAdapter, stage_request
from alfworld_.recovery_plan import MAX_REPEAT_ACTIONS, PROMPT, REPAIR_PROMPT, VERSION, compile_plan, inspect_phase
from alfworld_.skill_acquisition import INPUT_LIMIT, StrictTrainEnv, _replay, _reset, _step, import_source_events, verify_source_game
from failure_evo.contracts import canonical, fingerprint
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.math_stream import read, save, sha
from failure_evo.run_health import trusted_usage
import run_alfworld_recovery_v12 as parent


PREVIOUS = parent.previous
OUTPUT_LIMIT = PREVIOUS.OUTPUT_UPPER
REVISION_LIMIT = 1
MAX_ORIGINAL_BYTES = 16_384


def configuration(base, output, mock):
    roots = list(base.glob('alfworld_recovery_v12_*'))
    if any(output.resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(output.resolve())
           for root in roots):
        raise PermissionError('v13 must use a separate directory')
    previous, source, events, host, schedule, boundaries, backend = parent.configuration(base, output, False)
    parent_root = base/parent.PILOT
    frozen, finished = read(parent_root/'protocol.json'), read(parent_root/'result.json')
    if ({**previous, 'run_id':'real:'+parent.PILOT} != {key: value for key, value in frozen.items()
                                                      if key != 'mock_acceptance'}
            or finished['protocol_sha256'] != fingerprint(frozen) or finished['paid_requests'] != len(schedule)):
        raise PermissionError('v12 provenance mismatch')
    files = {Path(__file__).resolve(), PREVIOUS.ROOT/'FlowEvo/src/alfworld_/recovery_plan.py',
             *(PREVIOUS.ROOT/name for name in previous['code_sha256'])}
    history = {**previous['historical_sha256'], **{str(path): sha(path) for root in roots
               for path in root.rglob('*') if path.is_file()}}
    if any(sha(path) != digest for path, digest in history.items()):
        raise PermissionError('historical evidence changed')
    entries = []
    with TemporaryDirectory() as temp:
        for group, selected, payload, _ in schedule:
            adapter = RecoveryAdapter(Path(temp)/'provider.jsonl', None, model=PREVIOUS.MODEL, mock=True,
                sender=lambda _: None, stage='analyze', payload=payload, parser=None, protocol=VERSION,
                analysis_prompt=PROMPT, max_wire_input_upper=INPUT_LIMIT)
            wire = adapter.preflight(dict(phase='induction', max_tokens=OUTPUT_LIMIT,
                discovery=dict(stage='analyze', payload_sha256=fingerprint(payload))))
            entries.append(dict(group=group, sequences=[row['sequence'] for row in selected],
                                wire_sha256=fingerprint(wire), input_upper=len(canonical(wire).encode())+256))
    bounds = [row['input_upper'] for row in entries] + [INPUT_LIMIT] * (len(entries) * REVISION_LIMIT)
    calls = len(bounds)
    plan = dict(version=VERSION, scope='MOCK_PLAN_SOURCE_ONLY' if mock else 'REAL_PLAN_SOURCE_ONLY',
        disposition='SHADOW_SOURCE_ONLY', run_id=('mock:' if mock else 'real:')+output.name,
        model=PREVIOUS.MODEL, parent_protocol_sha256=fingerprint(frozen),
        schedule=entries, network_policy=previous['network_policy'], worker=backend.manifest(),
        worker_calls=previous['worker_calls'], source_window=previous['source_window'],
        max_repeat_actions=MAX_REPEAT_ACTIONS,
        checkpoints_sha256=previous['checkpoints_sha256'], boundaries_sha256=previous['boundaries_sha256'],
        historical_sha256=history, code_sha256={str(path.relative_to(PREVIOUS.ROOT)): sha(path) for path in sorted(files)},
        prompt_sha256=fingerprint(PROMPT), revision_prompt_sha256=fingerprint(REPAIR_PROMPT),
        revision_limit=REVISION_LIMIT, output_upper=OUTPUT_LIMIT, max_calls=calls,
        max_tokens=sum(bounds)+calls*OUTPUT_LIMIT,
        max_cost_microusd=sum((120*(size+OUTPUT_LIMIT)+99)//100 for size in bounds),
        quote_upper_usd=(30*sum(bounds)+120*calls*OUTPUT_LIMIT)/100_000_000)
    return plan, source, events, host, schedule, boundaries, backend


def authorization_for(plan):
    return dict(run_id=plan['run_id'], protocol_hash=fingerprint(plan), model=plan['model'], protocol=VERSION,
                max_cost_microusd=plan['max_cost_microusd'], paid_api_authorized=True)


def prepare(base, output):
    plan, *_ = configuration(base, output, False)
    output.mkdir(mode=0o700, exist_ok=False, parents=True)
    save(output/'protocol.json', plan)
    save(output/'authorization.template.json', {**authorization_for(plan), 'paid_api_authorized':False})
    return plan


def result_of(response):
    if not response.get('parse_status'):
        return json.loads(response['specification'])
    if response.get('finish_reason') == 'stop':
        return dict(status='STATIC_REJECTED', candidate=None, diagnostics=[dict(field='$',
                    code='STRUCTURED_OUTPUT_REQUIRED', detail='Return one complete JSON object.')])
    return dict(status='PROVIDER_DELIVERY_REJECTED', candidate=None, diagnostics=[])


def revision_packet(response, result, public_steps):
    if result['status'] != 'STATIC_REJECTED' or response.get('finish_reason') != 'stop':
        return None
    original = response['raw_response']['choices'][0]['message'].get('content')
    if not isinstance(original, str) or len(original.encode()) > MAX_ORIGINAL_BYTES:
        return None
    return dict(previous_plan=original, diagnostics=result['diagnostics'], allowed_step_ids=sorted(public_steps))


def revision_changes(original, result):
    if result['candidate'] is None:
        return dict(status='NOT_COMPILED')
    try:
        before = json.loads(original)
    except (ValueError, RecursionError):
        before = None
    if not isinstance(before, dict):
        return dict(status='NOT_COMPARABLE')
    after = result['candidate']['plan']
    fields = sorted(key for key in before.keys() | after.keys()
                    if key not in before or key not in after or before[key] != after[key])
    return dict(status='STRUCTURAL_COMPARISON_ONLY', changed_fields=fields)


def decide(skill, public, phase, card, runner, until=None, repeat_limit=False, *, starting=None):
    checks = inspect_phase(skill, public, phase, until, starting=starting)
    selection = checks['selection']
    if selection is None:
        return checks, dict(status='declined', reason=checks['block'])
    if repeat_limit:
        return checks, dict(status='declined', reason='PHASE_REPEAT_LIMIT')
    context = context_view(public['goal'], public['observation'], public['admissible_commands'],
                           public['history'], selection)
    return checks, runner.run(card, context)


def validate_source(data, origin, compiled, card, runner, registry, path, limit):
    anchor = origin['projected']['anchor']
    identity = fingerprint([VERSION, card.version, origin['receipt_sha256'], anchor, limit, runner.backend.manifest()])
    if registry.state(card)['permission'] != 'shadow' or not card.intact():
        raise PermissionError('intact Shadow candidate required')
    if path.exists():
        saved = read(path)
        if saved['validation_sha256'] != identity:
            raise PermissionError('source receipt identity changed')
        return saved
    prefix = origin['steps'][:anchor]
    current = prefix[-1]
    skill, steps = compiled['skill'], compiled['plan']['steps']
    decisive = PREVIOUS._decisive(origin)['action']
    already_ready = decisive in current['commands']
    branch, decisions, phase, repeats = [], [], 0, 0
    witness, stop = None, 'STEP_BUDGET'
    env = StrictTrainEnv(data, max_steps=50)
    try:
        env.initialize(frozen_game_files=[str(verify_source_game(data, origin))])
        _reset(env, origin)
        _replay(env, prefix)
        while phase < len(steps) and len(branch) < min(limit, 50-anchor):
            public = PREVIOUS.public_state('source', origin['projected']['goal'], current, prefix+branch, anchor-1)
            until = steps[phase].get('repeat_until')
            checks, action = decide(skill, public, phase, card, runner, until,
                                    repeats >= MAX_REPEAT_ACTIONS, starting=not branch and phase==0)
            decisions.append(dict(phase=phase, checks=checks, operator=action))
            if checks.get('phase_satisfied'):
                phase, repeats = phase+1, 0
                continue
            if action['status'] != 'applied':
                stop = action['reason'] if action['status'] == 'declined' else 'POLICY_ERROR'
                break
            command = action['action']
            parsed = parse_command(command)
            if (not parsed or command not in current['commands']
                    or (parsed[0], [entity.name for entity in parsed[1]]) !=
                       (skill['rules'][phase]['action']['verb'], checks['selection']['values'])):
                raise PermissionError('Worker did not return the selected live action')
            after = _step(env, command)
            branch.append(after)
            effect = receipt_truth(parsed, after['observation'])
            decisions[-1]['effect'] = effect
            if effect == 'TRUE':
                if until:
                    repeats += 1
                else:
                    phase, repeats = phase+1, 0
            if witness is None and (after['won'] or after['score'] > current['score']):
                witness = dict(kind='ENVIRONMENT_SCORE_OR_WIN', phase=decisions[-1]['phase'], action=command)
            if witness is None and effect == 'TRUE' and not already_ready and decisive in after['commands']:
                witness = dict(kind='DECISIVE_ACTION_NEWLY_ADMISSIBLE', phase=decisions[-1]['phase'], action=decisive)
            if after['done'] or after['won']:
                stop = 'ENVIRONMENT_TERMINAL'
                break
            if effect != 'TRUE':
                stop = 'NO_EFFECT' if effect == 'FALSE' else 'EFFECT_UNKNOWN'
                break
            current = after
        if phase == len(steps) and stop == 'STEP_BUDGET':
            stop = 'PLAN_COMPLETED'
    finally:
        env.close()
    first_effect = next((row['effect'] for row in decisions if 'effect' in row), None)
    result = dict(validation_sha256=identity, sequence=origin['sequence'], stop=stop, actions=branch, decisions=decisions,
        first_action_executed=bool(branch), first_action_verified=first_effect=='TRUE',
        confirmed_phases=phase, plan_completed=phase==len(steps),
        local_repair_verified=witness is not None, local_witness=witness, won=bool(branch and branch[-1]['won']))
    save(path, result)
    return result


def acquire(plan, source, events, host, schedule, boundaries, backend, output, sender, authorization):
    budget = PREVIOUS.create_accounts(output, plan)
    registry = FailureOperatorRegistry(output/'registry.jsonl', FailureEvidenceStore(output/'failures.jsonl'))
    runner = EnvironmentPolicyRunner(backend, output/'worker.jsonl', budget)
    imported = import_source_events('B', events, host, output, registry.evidence, plan['run_id'])
    known = {row['event_id']: row for row in registry.evidence.visible(time(), plan['run_id'])}
    usage, candidates = Counter(), []
    for index, (group, selected, payload, _) in enumerate(schedule):
        name = f'candidate_{index}'
        directory = output/name
        anchors = {row['evidence_id']: row['failure_step_id'] for row in payload['source_receipts']}
        steps = {row[0] for receipt in payload['source_receipts'] for row in receipt['steps']}

        def request(stage, packet, prompt):
            response = stage_request(output, f'{name}/{stage}', 'analyze', packet,
                lambda value: compile_plan(value, anchors, steps), budget, sender=sender,
                authorization=authorization, network_policy=plan['network_policy'] if sender is None else None,
                protocol=VERSION, analysis_prompt=prompt)
            usage.update(trusted_usage(response['raw_response']))
            return response, result_of(response)

        response, first = request('initial', payload, PROMPT)
        if response['wire_sha256'] != plan['schedule'][index]['wire_sha256']:
            raise PermissionError('initial request differs from freeze')
        attempts = [dict(response_sha256=response['response_sha256'], result=first)]
        final = first
        if (packet := revision_packet(response, first, steps)) is not None:
            response, final = request('revision', packet, REPAIR_PROMPT)
            attempts.append(dict(response_sha256=response['response_sha256'], result=final,
                                 revision_changes=revision_changes(packet['previous_plan'], final)))
        record = dict(group=group, status=final['status'], attempts=attempts)
        candidates.append(record)
        save(directory/'compile_receipt.json', record)
        if final['candidate'] is None:
            continue
        skill = final['candidate']['skill']
        generated = dict(code=worker_source(skill), description='Compiled public recovery plan',
            applicability=skill['scope'], model=response['model'], id=response['id'],
            response_sha256=response['response_sha256'])
        registration = register_environment_candidate(directory, generated,
            dict(mechanism=payload['mechanism'], plan=final['candidate']['plan'], skill=skill),
            [imported[key] for key in anchors], known, backend.manifest(), registry,
            engineering=sender is not None, protocol=VERSION, baseline='alfworld-v13-plan-shadow')
        record.update(registration)
        if record['status'] != 'SHADOW':
            continue
        card = FailureOperator.from_dict(registration['card'])
        sources = [validate_source(source['data_root'], host[row['evidence_id']], final['candidate'], card, runner, registry,
            directory/f"source_{row['sequence']}.json", plan['source_window']) for row in selected]
        controls = []
        for case in boundaries:
            phase = 0
            steps = final['candidate']['plan']['steps']
            while phase < len(steps):
                checks, action = decide(skill, case['public'], phase, card, runner, steps[phase].get('repeat_until'))
                if not checks.get('phase_satisfied'):
                    break
                phase += 1
            controls.append(dict(category=case['category'], expected=case['expected'], checks=checks, operator=action))
        metrics = dict(source_checks=len(sources), boundaries=len(controls),
            false_triggers=sum(row['expected']=='NO' and row['operator']['status']=='applied' for row in controls),
            uncertain_triggers=sum(row['expected']=='UNKNOWN' and row['operator']['status']=='applied' for row in controls),
            boundary_errors=sum(row['operator']['status']=='error' for row in controls))
        for key in ('first_action_executed', 'first_action_verified', 'plan_completed', 'local_repair_verified', 'won'):
            metrics[key] = sum(row[key] for row in sources)
        record.update(metrics=metrics, sources=sources, boundaries=controls)
        if registry.state(card)['permission'] != 'shadow':
            raise PermissionError('unexpected candidate permission')
        save(directory/'validation.json', record)
    if any(sha(path) != digest for path, digest in plan['historical_sha256'].items()):
        raise PermissionError('historical evidence changed during v13')
    result = dict(scope=plan['scope'], protocol_sha256=fingerprint(plan), candidates=candidates, usage=dict(usage),
        paid_requests=0 if sender is not None else sum(len(row['attempts']) for row in candidates),
        quote_estimated_usd=(30*usage['input_tokens']+120*usage['output_tokens'])/100_000_000,
        budget=budget.snapshot(), independent_gate_games=0, disposition=plan['disposition'])
    save(output/'result.json', result)
    return result


def run(base, output, *, sender=None, authorization=None):
    plan, *inputs = configuration(base, output, sender is not None)
    frozen = output/'protocol.json'
    if sender is None and (not frozen.is_file() or authorization != authorization_for(plan)):
        raise PermissionError('frozen v13 protocol and separate authorization required')
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if frozen.exists() and read(frozen) != plan:
            raise PermissionError('v13 protocol drift')
        if not frozen.exists():
            if sender is None:
                raise PermissionError('v13 protocol disappeared')
            save(frozen, plan)
        try:
            return acquire(plan, *inputs, output, sender, authorization)
        except (Exception, KeyboardInterrupt) as error:
            save(output/'interruption.json', dict(protocol_sha256=fingerprint(plan), type=type(error).__name__,
                                                  reason=str(error)))
            raise


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('action', choices=('prepare', 'run'))
    cli.add_argument('--base', type=Path, default=Path.home()/'.local/share/flowevo')
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--authorization', type=Path)
    args = cli.parse_args()
    if args.action == 'prepare':
        plan = prepare(args.base, args.output)
        print(canonical({key: plan[key] for key in ('run_id', 'max_calls', 'max_cost_microusd', 'quote_upper_usd')} |
                        dict(status='PREPARED_NOT_AUTHORIZED', protocol_sha256=fingerprint(plan))))
    elif args.authorization is None:
        cli.error('run requires --authorization')
    else:
        result = run(args.base, args.output, authorization=read(args.authorization))
        print(canonical(dict(paid_requests=result['paid_requests'], candidates=[
            dict(group=row['group'], status=row['status'], metrics=row.get('metrics')) for row in result['candidates']])))


if __name__ == '__main__':
    main()
