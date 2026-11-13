"""One revision from archived ALFWorld source feedback, with no initial generation."""

import argparse
import fcntl
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time
from types import SimpleNamespace

from alfworld_.failure_learning import EnvironmentPolicyRunner, static_check_detailed
from alfworld_.python_recovery_feedback import delivery
from alfworld_.recovery_execution_feedback import DECLINE_REVISION_PROMPT, with_decline_context
from alfworld_.skill_acquisition import StrictTrainEnv, import_source_events
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.math_stream import read, sha
from failure_evo.network_transport import DefinitelyNotSent, SendUnknown
from failure_evo.run_health import RunUnhealthy, trusted_usage
import run_alfworld_python_recovery_feedback as pilot


VERSION = 'alfworld-python-recovery-decline-revision-v1'
PARENT = pilot.ROOT/'runs'/'python_recovery_container_pilot_20261112_01'
PARENT_PROTOCOL_SHA = '2be1114573c96f296cf46776c4c658c4cc9ef69aab3b13290abfc113921d314e'
PARENT_RESULT_SHA = '674a9f63f9008ce69f35fca6094410f185cc72cb965d4815f711d6b31a4d40cc'
STAGE = 'revision_02'
JOB = 'candidate_0/'+STAGE
PACKET_FILE = 'revision_input.private.json'


def archived_baseline(parent, origins, protocol):
    """Bind the decoded source and refusal receipts to the concluded real run."""
    if fingerprint(protocol)!=PARENT_PROTOCOL_SHA or sha(parent/'result.json')!=PARENT_RESULT_SHA:
        raise PermissionError('archived container run identity differs')
    group, = read(parent/'result.json')['candidates']
    baseline, = [a for a in group['attempts'] if a['stage']=='revision_01']
    directory = parent/'candidate_0'/'revision_01'
    raw, = [row['payload']['response'] for row in EvidenceStore(parent/'provider.jsonl').records()
            if row['kind']=='RAW_RESPONSE' and row['payload']['sha256']==baseline['response_sha256']]
    choice, = raw['choices']
    if (raw['model']!=protocol['model'] or choice['finish_reason']!='stop'
            or fingerprint(raw)!=baseline['response_sha256']
            or pilot.parse_delivery(json.loads(choice['message']['content']))!=baseline['delivery']
            or sha(directory/'decoded.py')!=baseline['code_sha256']
            or (directory/'decoded.py').read_bytes()!=baseline['delivery']['proposal']['code'].encode()
            or not baseline['static']['passed'] or baseline['registration']['status']!='SHADOW'):
        raise PermissionError('archived baseline source binding differs')
    card = baseline['registration']['card']
    workers = {row['payload']['execution_id']:row['payload'] for row in EvidenceStore(parent/'worker.jsonl').records()
               if row['kind']=='ENVIRONMENT_POLICY_EXECUTED'}
    starts = {}
    for (ref, origin), source in zip(origins.items(), baseline['sources'], strict=True):
        decision, = source['decisions']
        worker = workers[decision['execution_id']]
        if (source['source_ref']!=ref or source['sequence']!=origin['sequence']
                or source!=read(directory/(ref+'.json')) or source['outcome']!='DECLINED'
                or source['actions'] or decision['receipt'] is not None or decision['selected_action'] is not None
                or worker['candidate_version']!=card['version']
                or {worker['artifact_sha256'],decision['artifact_sha256'],card['artifact_sha256']}
                    !={baseline['code_sha256']}
                or worker['context_sha256']!=decision['context_sha256']
                or worker['raw']['status']!='OK' or worker['result']!=decision['operator']
                or worker['raw']['value']!=decision['operator'] or decision['operator']['status']!='declined'):
            raise PermissionError('archived refusal is not a confirmed source Worker result')
        starts[ref] = pilot.start_state(origin, protocol)
    return baseline, starts


def configuration(base, parent, output):
    if (output.name==parent.name or output.is_relative_to(parent) or parent.is_relative_to(output)):
        raise PermissionError('one-revision run must be separate from the archived run')
    old, source, events, host, schedule, boundaries, backend = pilot.frozen_real_inputs(
        base, parent, container_only=True)
    (group, selected, original), = schedule
    origins = {f'source_{i}':host[row['evidence_id']] for i,row in enumerate(selected,1)}
    baseline, starts = archived_baseline(parent, origins, old)
    packet = with_decline_context(original, baseline, starts, stage=STAGE)
    with TemporaryDirectory() as temp:
        body = pilot.wire(Path(temp)/'provider.jsonl', packet, DECLINE_REVISION_PROMPT)
    input_upper = len(canonical(body).encode())+256
    reserved = pilot.ceiling_microusd(input_upper+pilot.OUTPUT_UPPER, pilot.RESERVATION_RATE)
    increment = pilot.HARD_CAP_INCREMENT
    slots = sum(min(old['source_window'],old['episode_limit']-row['anchor']) for row in selected)
    plan = {key:old[key] for key in ('model','scope','environment','environment_type','worker','source_window',
        'episode_limit','max_stagnant_repeats','network_policy','source_protocol_sha256','historical_sha256',
        'boundaries_sha256','pricing','run_wall_seconds')}
    code = [Path(__file__).resolve(), pilot.ROOT/'FlowEvo/src/alfworld_/recovery_execution_feedback.py']
    plan.update(
        version=VERSION, run_id='real:'+output.name, stage=STAGE, paid_api_authorized=False,
        disposition='SHADOW_SOURCE_ONLY', group=group, sources=selected, revision_limit=0, max_calls=1,
        baseline=dict(run_id=old['run_id'], stage=baseline['stage'], version=baseline['version'],
                      code_sha256=baseline['code_sha256'], response_sha256=baseline['response_sha256'],
                      protocol_sha256=PARENT_PROTOCOL_SHA, result_sha256=PARENT_RESULT_SHA),
        archive_sha256={str(path):sha(path) for path in sorted(parent.rglob('*')) if path.is_file()},
        code_sha256={**old['code_sha256'], **{str(p.relative_to(pilot.ROOT)):sha(p) for p in code}},
        packet_sha256=fingerprint(packet), wire_sha256=fingerprint(body),
        revision_prompt_sha256=fingerprint(DECLINE_REVISION_PROMPT),
        input_upper=input_upper, output_upper=pilot.OUTPUT_UPPER, max_tokens=input_upper+pilot.OUTPUT_UPPER,
        conservative_cost_upper_microusd=reserved, max_cost_microusd=((reserved+increment-1)//increment)*increment,
        peak_no_cache_quote_upper_usd=pilot.estimate_peak(input_upper,pilot.OUTPUT_UPPER),
        source_action_slots=slots, environment_steps=len(selected)*old['episode_limit'],
        worker_calls=slots+len(boundaries), worker_milliseconds_total=(slots+len(boundaries))*15_000,
    )
    return plan, packet, source, events, host, origins, boundaries, backend, baseline


def prepare(base, parent, output):
    plan, packet, *_ = configuration(base, parent, output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    pilot.commit(output/'protocol.json', plan)
    pilot.commit(output/PACKET_FILE, packet)
    pilot.commit(output/'authorization.template.json', pilot.authorization_template(plan))
    return plan


def verify_frozen(output, plan, packet):
    if (output.stat().st_mode & 0o077
            or read(output/'protocol.json')!=plan or read(output/PACKET_FILE)!=packet
            or read(output/'authorization.template.json')!=pilot.authorization_template(plan)
            or any(sha(pilot.ROOT/name)!=digest for name,digest in plan['code_sha256'].items())):
        raise PermissionError('frozen revision run or request differs')
    pilot.verify_history(plan['archive_sha256'])


def preflight(base, parent, output):
    plan, packet, *_ = configuration(base, parent, output)
    verify_frozen(output, plan, packet)
    pilot.check_local_runtime(plan)
    return dict(status='READY' if pilot.configured_api_key() else 'CREDENTIAL_REQUIRED',
                run_id=plan['run_id'], protocol_sha256=fingerprint(plan), max_calls=1,
                max_tokens=plan['max_tokens'], max_cost_microusd=plan['max_cost_microusd'],
                peak_no_cache_quote_upper_usd=plan['peak_no_cache_quote_upper_usd'],
                feedback_sources=len(packet['source_feedback']))


def submit(output, plan, packet, budget, provider, authorization):
    directory = output/JOB
    pilot.commit(directory/'request_binding.json', dict(
        stage=STAGE, wire_sha256=plan['wire_sha256'], parent_version=plan['baseline']['version']))
    try:
        response = pilot.stage_request(output, JOB, 'analyze', packet, pilot.parse_delivery, budget,
            authorization=authorization, network_policy=plan['network_policy'], protocol=VERSION,
            analysis_prompt=DECLINE_REVISION_PROMPT)
    except (DefinitelyNotSent, SendUnknown):
        raise
    except Exception:
        pilot.check_response_commit(budget, provider)
        raise
    raw = response['raw_response']
    usage = trusted_usage(raw)
    if (response['wire_sha256']!=plan['wire_sha256'] or fingerprint(raw)!=response['response_sha256']
            or not usage or usage['input_tokens']>plan['input_upper'] or usage['output_tokens']>plan['output_upper']):
        raise RunUnhealthy('revision receipt or usage does not match the frozen request')
    parsed = delivery(response)
    attempt = dict(stage=STAGE, parent_version=plan['baseline']['version'], delivery=parsed,
        static=dict(status='NOT_CHECKED'), registration=dict(status='NOT_RUN'), sources=[],
        version=fingerprint([fingerprint(plan),response['response_sha256']]),
        response_sha256=response['response_sha256'], wire_sha256=response['wire_sha256'], usage=usage,
        provider_finish_reason=response['finish_reason'], provider_model=raw.get('model'),
        provider_response_id=raw.get('id'), provider_system_fingerprint=raw.get('system_fingerprint'),
        disposition=parsed['status'])
    if 'submitted_code' in parsed:
        attempt['code_sha256'] = pilot.save_exact_source(directory/'decoded.py', parsed['submitted_code'])
    if parsed['status']=='PROPOSE':
        code = parsed['proposal']['code']
        attempt['code_sha256'] = pilot.save_exact_source(directory/'decoded.py', code)
        check = static_check_detailed(code)
        attempt['static'] = dict(check, status='PASSED' if check['passed'] else 'REJECTED')
        attempt['disposition'] = 'STATIC_PASSED' if check['passed'] else 'STATIC_REJECTED'
    return response, attempt


def run(base, parent, output, *, authorization, resume=False):
    if not isinstance(authorization,dict) or authorization.get('paid_api_authorized') is not True:
        raise PermissionError('explicit authorization for one revision required')
    plan, packet, source, events, host, origins, boundaries, backend, baseline = configuration(base,parent,output)
    verify_frozen(output, plan, packet)
    if canonical(authorization)!=canonical(pilot.authorization_for(plan)) or not pilot.configured_api_key():
        raise PermissionError('matching revision authorization and configured credential required')
    pilot.check_local_runtime(plan)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        started = (output/'budget.jsonl').exists()
        if started!=resume:
            raise PermissionError('use resume only with an existing revision ledger')
        if not started and any(p.name not in ('protocol.json',PACKET_FILE,'authorization.template.json',
                'authorization.json','preflight.json','run.lock','console.log') for p in output.iterdir()):
            raise PermissionError('unrecognized file in new revision run')
        budget = pilot.PREVIOUS.create_accounts(output, plan)
        provider = SimpleNamespace(events=EvidenceStore(output/'provider.jsonl'))
        registry = FailureOperatorRegistry(output/'registry.jsonl', FailureEvidenceStore(output/'failures.jsonl'))
        runner = EnvironmentPolicyRunner(backend, output/'worker.jsonl', budget)
        receipts = pilot.EnvironmentReceipts(output/'environment.jsonl', plan['environment_steps'])
        pilot.check_run(budget, provider, runner, plan['network_policy'])
        imported = import_source_events('B', events, host, output, registry.evidence, plan['run_id'])
        verify_frozen(output, plan, packet)
        response, attempt = submit(output, plan, packet, budget, provider, authorization)
        verify_frozen(output, plan, packet)
        directory = output/JOB
        if attempt['static']['status']=='PASSED':
            known = {row['event_id']:row for row in registry.evidence.visible(time(), plan['run_id'])}
            attempt['registration'] = pilot.register(directory, attempt['delivery']['proposal'], response,
                packet['original_learning_input']['hypothesis'],
                [imported[row['evidence_id']] for row in plan['sources']], known, runner, registry,
                engineering=False, protocol=VERSION)
            if attempt['registration']['status']!='SHADOW':
                raise RunUnhealthy('revised candidate lacks exact Shadow registration')
            card = FailureOperator.from_dict(attempt['registration']['card'])
            if card.artifact_sha256!=attempt['code_sha256'] or not card.intact():
                raise PermissionError('revision source differs from registered artifact')
            attempt['sources'] = [pilot.validate_source(plan, source['data_root'], origin, ref, card, runner,
                registry, receipts, directory, StrictTrainEnv, None) for ref,origin in origins.items()]
            attempt['disposition'] = 'SOURCE_EVALUATED'
        pilot.commit(directory/'attempt.json', attempt)
        group = dict(group=plan['group'], attempts=[attempt], scheduled_source_count=len(origins))
        pilot.check_run(budget, provider, runner, plan['network_policy'])
        pilot.evaluate_boundaries(output, [group], boundaries, runner, registry)
        pilot.check_run(budget, provider, runner, plan['network_policy'])
        verify_frozen(output, plan, packet)
        attempt['metrics'] = pilot.version_metrics(attempt, group, boundaries)
        worker_rows = [row['payload'] for row in runner.events.records() if row['kind']=='ENVIRONMENT_POLICY_EXECUTED']
        comparison, = pilot.container_milestones([baseline, attempt])['feedback_revision_comparisons']
        actual = attempt['usage']
        result = dict(run_id=plan['run_id'], protocol_sha256=fingerprint(plan), baseline=plan['baseline'],
            code_changed=attempt.get('code_sha256')!=baseline['code_sha256'] if 'code_sha256' in attempt else None,
            attempt=attempt, baseline_metrics=baseline['metrics'], paired_source_comparison=comparison,
            baseline_boundary_evaluation=baseline['boundary_evaluation'],
            resources=pilot.count_version_resources(attempt,worker_rows,receipts),
            paid_requests=1, usage=actual, budget=budget.snapshot(), independent_gate_games=0,
            peak_no_cache_estimate_usd=pilot.estimate_peak(actual['input_tokens'],actual['output_tokens']),
            actual_billed_usd=None, disposition=plan['disposition'])
        return pilot.commit(output/'result.json', result)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('command', choices=('prepare','preflight','run','resume'))
    cli.add_argument('--base', type=Path, default=Path.home()/'.local/share/flowevo')
    cli.add_argument('--parent', type=Path, default=PARENT)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--authorization', type=Path)
    args = cli.parse_args()
    paths = (args.base.resolve(), args.parent.resolve(), args.output.resolve())
    if args.command=='prepare':
        plan = prepare(*paths)
        summary = dict(status='PREPARED', run_id=plan['run_id'], protocol_sha256=fingerprint(plan),
                       max_calls=1,max_cost_microusd=plan['max_cost_microusd'])
    elif args.command=='preflight':
        summary = preflight(*paths)
    else:
        if not args.authorization:
            cli.error('run and resume require --authorization')
        result = run(*paths, authorization=read(args.authorization), resume=args.command=='resume')
        summary = {k:result[k] for k in ('run_id','paid_requests','code_changed','usage',
                                        'peak_no_cache_estimate_usd','paired_source_comparison')}
        summary.update(status=result['attempt']['disposition'], metrics=result['attempt']['metrics'])
    print(canonical(summary))


if __name__=='__main__':
    main()
