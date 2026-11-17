"""One S1 applicability submission, evaluated with a fixed recovery artifact."""

import argparse
from collections import Counter
import fcntl
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time
from types import SimpleNamespace

from alfworld_.failure_learning import EnvironmentPolicyRunner, static_check_detailed
from alfworld_.python_recovery_feedback import delivery, parse_delivery
from alfworld_.recovery_applicability import PROMPT, STATUSES, worker_artifact
from alfworld_.recovery_applicability_rule import check_rule
from alfworld_.skill_acquisition import StrictTrainEnv, import_source_events
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.math_stream import read, sha
from failure_evo.network_transport import DefinitelyNotSent, SendUnknown
from failure_evo.run_health import RunUnhealthy, trusted_usage
from prepare_alfworld_applicability_data import (
    BASE, ROOT, RULES_SHA, S0, S0_CODE_SHA, S0_RESULT_SHA, TRAIN_FILE, archived_material,
)
import run_alfworld_python_recovery_feedback as pilot


VERSION = 'alfworld-python-container-applicability-v1'
JOB = 'candidate_0/applicability'
LEARNING = 'learning_input.private.json'
ENVIRONMENT_STEPS = 550
TRAINING_SHA = 'c42a0fe65623b9a39ee724bbb7f8093a773622504ddc028532f20e6d986db067'
RULE_SOURCE = ROOT/'FlowEvo/src/alfworld_/recovery_applicability_rule.py'


def learning_packet(training, initial, recovery_source):
    keys = ('evidence_ref','kind','observation_annotation','public_context')
    return dict(
        frozen_recovery_source=recovery_source,
        original_recovery_evidence=initial,
        natural_development_prefixes=[{k:row[k] for k in keys} for row in training['rows']],
    )


def configuration(base, output):
    if output==S0 or output.is_relative_to(S0) or S0.is_relative_to(output):
        raise PermissionError('separate applicability run directory required')
    if (sha(output/'selection_rules.json')!=RULES_SHA or sha(output/TRAIN_FILE)!=TRAINING_SHA):
        raise PermissionError('historical training freeze differs')
    training = read(output/TRAIN_FILE)
    pilot.verify_history(training['historical_manifests'])
    pilot.verify_history({row['provenance']['journal']:row['provenance']['journal_sha256']
                          for row in training['rows']})
    old,source,events,host,schedule,boundaries,backend,s0 = archived_material(base)
    (group,selected,initial), = schedule
    if (training['archived_sources_sha256']!=fingerprint(selected)
            or training['exposed_boundary_cases_sha256']!=fingerprint(boundaries)):
        raise PermissionError('training roles disagree with archived source or regression split')
    s0_path = S0/'candidate_0/revision_02/decoded.py'
    packet = learning_packet(training,initial,s0_path.read_bytes().decode())
    with TemporaryDirectory() as temp:
        wire = pilot.wire(Path(temp)/'provider.jsonl',packet,PROMPT)
    input_upper = len(canonical(wire).encode())+256
    reserved = pilot.ceiling_microusd(input_upper+pilot.OUTPUT_UPPER,pilot.RESERVATION_RATE)
    inc = pilot.HARD_CAP_INCREMENT
    files = (Path(__file__).resolve(), ROOT/'scripts/prepare_alfworld_applicability_data.py',
             ROOT/'FlowEvo/src/alfworld_/recovery_applicability.py', RULE_SOURCE)
    recovery_card = FailureOperator.from_dict(s0['attempt']['registration']['card'])
    if not recovery_card.intact() or recovery_card.artifact_sha256!=S0_CODE_SHA:
        raise PermissionError('archived recovery card does not bind the frozen source')
    plan = {key:old[key] for key in ('model','scope','environment','environment_type','worker','source_window',
            'episode_limit','max_stagnant_repeats','network_policy','source_protocol_sha256','historical_sha256',
            'boundaries_sha256','pricing','run_wall_seconds')}
    plan.update(version=VERSION, run_id='real:'+output.name, paid_api_authorized=False,
        disposition='SHADOW_DEVELOPMENT_ONLY', group=group, sources=selected, training_sha256=TRAINING_SHA,
        baseline=dict(result_sha256=S0_RESULT_SHA,code_sha256=S0_CODE_SHA,run_id=s0['run_id']),
        recovery_card_sha256=fingerprint(recovery_card.to_dict()),
        rule_sha256=sha(RULE_SOURCE),
        prompt_sha256=fingerprint(PROMPT), wire_sha256=fingerprint(wire), packet_sha256=fingerprint(packet),
        code_sha256={**old['code_sha256'],**{str(p.relative_to(ROOT)):sha(p) for p in files}},
        input_upper=input_upper, output_upper=pilot.OUTPUT_UPPER, max_calls=1,
        max_tokens=input_upper+pilot.OUTPUT_UPPER, max_cost_microusd=((reserved+inc-1)//inc)*inc,
        conservative_cost_upper_microusd=reserved, environment_steps=ENVIRONMENT_STEPS,
        worker_calls=len(selected)+len(boundaries)+sum(min(old['source_window'],old['episode_limit']-r['anchor'])
            for r in selected), peak_no_cache_quote_upper_usd=pilot.estimate_peak(input_upper,pilot.OUTPUT_UPPER),
        evaluation_only_pool_read=False, boundary_training_cases=training['historical_contexts'])
    return plan,packet,source,events,host,boundaries,backend,s0


def verify_frozen(output, plan, packet):
    if (output.stat().st_mode&0o077 or read(output/'protocol.json')!=plan or read(output/LEARNING)!=packet
            or sha(output/TRAIN_FILE)!=plan['training_sha256']
            or read(output/'authorization.template.json')!=pilot.authorization_template(plan)):
        raise PermissionError('applicability freeze differs')
    pilot.verify_history({ROOT/name:digest for name,digest in plan['code_sha256'].items()})
    pilot.verify_history({S0/'result.json':S0_RESULT_SHA,S0/'candidate_0/revision_02/decoded.py':S0_CODE_SHA})


def prepare(base, output):
    plan,packet,*_ = configuration(base,output)
    pilot.commit(output/'protocol.json',plan)
    pilot.commit(output/LEARNING,packet)
    pilot.commit(output/'authorization.template.json',pilot.authorization_template(plan))
    return plan


def submit(output, plan, packet, budget, provider, authorization):
    directory = output/JOB
    pilot.commit(directory/'request_binding.json',dict(wire_sha256=plan['wire_sha256'],stage='applicability'))
    try:
        response = pilot.stage_request(output,JOB,'analyze',packet,parse_delivery,budget,
            authorization=authorization,network_policy=plan['network_policy'],protocol=VERSION,analysis_prompt=PROMPT)
    except (DefinitelyNotSent,SendUnknown):
        raise
    except Exception:
        pilot.check_response_commit(budget,provider)
        raise
    raw = response['raw_response']
    usage = trusted_usage(raw)
    if (response['wire_sha256']!=plan['wire_sha256'] or fingerprint(raw)!=response['response_sha256']
            or not usage or usage['input_tokens']>plan['input_upper'] or usage['output_tokens']>plan['output_upper']):
        raise RunUnhealthy('S1 response or usage differs from frozen request')
    parsed = delivery(response)
    attempt = dict(status=parsed['status'],delivery=parsed,usage=usage,finish_reason=response['finish_reason'],
        response_sha256=response['response_sha256'],model=raw.get('model'),
        system_fingerprint=raw.get('system_fingerprint'))
    if 'submitted_code' in parsed:
        attempt['submitted_code_sha256'] = pilot.save_exact_source(directory/'gate.py',parsed['submitted_code'])
    if parsed['status']!='PROPOSE':
        return response,attempt,None
    code = parsed['proposal']['code']
    attempt['submitted_code_sha256'] = pilot.save_exact_source(directory/'gate.py',code)
    try:
        adapted = worker_artifact(code)
    except (SyntaxError,ValueError,RecursionError) as exc:
        attempt.update(status='GATE_CONTRACT_REJECTED',diagnostic=type(exc).__name__+': '+str(exc))
        return response,attempt,None
    attempt['static'] = static_check_detailed(adapted)
    attempt['status'] = 'STATIC_PASSED' if attempt['static']['passed'] else 'STATIC_REJECTED'
    if attempt['static']['passed']:
        attempt['worker_artifact_sha256'] = pilot.save_exact_source(directory/'adapted.py',adapted)
        return response,attempt,adapted
    return response,attempt,None


def learned_decision(runner, gate, context):
    if not gate.intact():
        raise PermissionError('learned gate source changed')
    result = pilot.invoke(runner,gate,context)
    operator = result['operator']
    state = operator['state']
    if operator['status']!='declined' or set(state)!={'applicability'} or state['applicability'] not in STATUSES:
        return dict(status='ERROR',reason=operator['reason'],execution_id=result['execution_id'])
    return dict(status=state['applicability'],reason=operator['reason'],execution_id=result['execution_id'])


def checkpoint_context(case):
    p = case['public']
    return pilot.context_view(p['goal'],p['observation'],p['admissible_commands'],p['history'],{})


def evaluate(plan, output, source, host, boundaries, baseline, runner, registry, receipts, gate):
    s0 = baseline['attempt']
    archived_card = FailureOperator.from_dict(s0['registration']['card'])
    if (not archived_card.intact() or archived_card.artifact_sha256!=S0_CODE_SHA
            or fingerprint(archived_card.to_dict())!=plan['recovery_card_sha256']):
        raise PermissionError('unchanged recovery card required')
    # The historical evidence IDs belong to the parent stream. Bind the exact
    # same executable bytes to current-stream evidence for real S1 replays.
    visible = registry.evidence.visible(time(),plan['run_id'])
    card_data = dict(archived_card.to_dict(),evidence_ids=[row['event_id'] for row in visible],
                     source_group_ids=sorted({row['provenance_group_id'] for row in visible}))
    card_data['version'] = fingerprint([archived_card.version,plan['run_id'],S0_CODE_SHA])
    card_data['operator_id'] = card_data['version'][:16]
    s0_card = FailureOperator.from_dict(card_data)
    if not registry._rows(s0_card):
        registry.register(s0_card,time())
    baseline_boundary = read(S0/'candidate_0/revision_02/boundaries.private.json')
    rows = []
    for spec,archived in zip(plan['sources'],s0['sources'],strict=True):
        origin = host[spec['evidence_id']]
        ref = archived['source_ref']
        _,context,identity = pilot.start_state(origin,plan)
        if (archived['sequence']!=spec['sequence'] or archived['start_sha256']!=identity
                or not archived['local_repair_verified']):
            raise PermissionError('source comparison is not bound to verified S0')
        rule = dict(status=check_rule(context))
        learned = learned_decision(runner,gate,context) if gate else dict(status='NOT_REACHED')
        live = None
        if learned['status']=='MATCH':
            live = pilot.validate_source(plan,source['data_root'],origin,ref,s0_card,runner,registry,
                                         receipts,output/JOB,StrictTrainEnv,None)
        reached = learned['status']!='NOT_REACHED'
        replay = dict(receipt_origin='NOT_REACHED')
        if live:
            replay = dict(local_repair=live['local_repair_verified'],won=live['won'],
                          first_action_executed=live['first_action_executed'],receipt_origin='NEW_TEXTWORLD')
        elif reached:
            replay = dict(local_repair=False,won=False,first_action_executed=False,receipt_origin='NO_ACTION')
        rows.append(dict(id=ref,sequence=spec['sequence'],role='SOURCE',expected='MATCH',start_sha256=identity,
            S0=dict(status='MATCH',local_repair=archived['local_repair_verified'],won=archived['won'],
                    first_action_executed=archived['first_action_executed'],receipt_origin='ARCHIVED_TEXTWORLD'),
            S1=dict(learned,**replay),
            Rule=dict(rule,local_repair=rule['status']=='MATCH' and archived['local_repair_verified'],
                      won=rule['status']=='MATCH' and archived['won'],
                      first_action_executed=rule['status']=='MATCH' and archived['first_action_executed'],
                      receipt_origin='SAME_CONTEXT_ARCHIVED_TEXTWORLD' if rule['status']=='MATCH' else 'NO_ACTION')))
    for case,archived in zip(boundaries,baseline_boundary,strict=True):
        context = checkpoint_context(case)
        if (case['public']['id']!=archived['case'] or case['expected']!=archived['expected']
                or fingerprint(context)!=archived['decision']['context_sha256']):
            raise PermissionError('boundary comparison is not bound to S0')
        op = archived['decision']['operator']['status']
        old = dict(status={'applied':'MATCH','declined':'DECLINE','error':'ERROR'}[op])
        rule = dict(status=check_rule(context))
        learned = learned_decision(runner,gate,context) if gate else dict(status='NOT_REACHED')
        # A false gate acceptance and an actual recovery selection are different.
        for arm in (old,rule,learned):
            arm['action_selected'] = None if arm['status']=='NOT_REACHED' else arm['status']=='MATCH' and op=='applied'
        rows.append(dict(id=archived['case'],role='EXPOSED_BOUNDARY',expected=case['expected'],
                         category=case['category'],S0=old,S1=learned,Rule=rule))
    return rows


def metrics(rows, arm):
    src = [row[arm] for row in rows if row['role']=='SOURCE']
    neg = [row[arm] for row in rows if row['expected']=='NO']
    unknown = [row[arm] for row in rows if row['expected']=='UNKNOWN']
    def count(group, field):
        values = [row.get(field) for row in group]
        return sum(values) if all(value is not None for value in values) else None

    return dict(source_denominator=len(src),source_status=dict(Counter(row['status'] for row in src)),
        first_actions=count(src,'first_action_executed'),
        local_repairs=count(src,'local_repair'),wins=count(src,'won'),
        negative_denominator=len(neg),negative_status=dict(Counter(row['status'] for row in neg)),
        false_action_selections=count(neg,'action_selected'),
        unknown_denominator=len(unknown),unknown_status=dict(Counter(row['status'] for row in unknown)),
        uncertain_action_selections=count(unknown,'action_selected'))


def paired(rows, reference):
    keys = {'SOURCE':'local_repair','EXPOSED_BOUNDARY':'action_selected'}
    pairs = {'SOURCE':{},'NO':{},'UNKNOWN':{}}
    for row in rows:
        field = keys[row['role']]
        group = 'SOURCE' if row['role']=='SOURCE' else row['expected']
        relation = ('NOT_REACHED' if row['S1']['status']=='NOT_REACHED' else
                    f"{int(row[reference][field])}->{int(row['S1'][field])}")
        pairs[group].setdefault(relation,[]).append(row['id'])
    return pairs


def run(base, output, *, authorization, resume=False):
    if not isinstance(authorization,dict) or authorization.get('paid_api_authorized') is not True:
        raise PermissionError('explicit S1 authorization required')
    plan,packet,source,events,host,boundaries,backend,baseline = configuration(base,output)
    verify_frozen(output,plan,packet)
    if canonical(authorization)!=canonical(pilot.authorization_for(plan)) or not pilot.configured_api_key():
        raise PermissionError('S1 grant and credential required')
    pilot.check_local_runtime(plan)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'budget.jsonl').exists()!=resume:
            raise PermissionError('use resume only with an existing S1 ledger')
        budget = pilot.PREVIOUS.create_accounts(output,plan)
        provider = SimpleNamespace(events=EvidenceStore(output/'provider.jsonl'))
        registry = FailureOperatorRegistry(output/'registry.jsonl',FailureEvidenceStore(output/'failures.jsonl'))
        runner = EnvironmentPolicyRunner(backend,output/'worker.jsonl',budget)
        receipts = pilot.EnvironmentReceipts(output/'environment.jsonl',plan['environment_steps'])
        pilot.check_run(budget,provider,runner,plan['network_policy'])
        imported = import_source_events('B',events,host,output,registry.evidence,plan['run_id'])
        verify_frozen(output,plan,packet)
        response,attempt,code = submit(output,plan,packet,budget,provider,authorization)
        verify_frozen(output,plan,packet)
        gate = None
        if code is not None:
            proposal = dict(attempt['delivery']['proposal'],code=code)
            known = {row['event_id']:row for row in registry.evidence.visible(time(),plan['run_id'])}
            registration = pilot.register(output/JOB,proposal,response,
                packet['original_recovery_evidence']['hypothesis'],list(imported.values()),known,runner,registry,
                engineering=False,protocol=VERSION)
            if registration['status']!='SHADOW':
                raise RunUnhealthy('S1 gate requires Shadow registration')
            gate = FailureOperator.from_dict(registration['card'])
            if gate.artifact_sha256!=attempt['worker_artifact_sha256'] or not gate.intact():
                raise PermissionError('S1 gate artifact differs')
            attempt['registration'] = registration
        pilot.commit(output/JOB/'attempt.json',attempt)
        rows = evaluate(plan,output,source,host,boundaries,baseline,runner,registry,receipts,gate)
        pilot.check_run(budget,provider,runner,plan['network_policy'])
        verify_frozen(output,plan,packet)
        snap = budget.snapshot()
        actual = attempt['usage']
        worker_rows = [row['payload'] for row in runner.events.records() if row['kind']=='ENVIRONMENT_POLICY_EXECUTED']
        gate_version = gate.version if gate else None
        gate_calls = sum(row['candidate_version']==gate_version for row in worker_rows)
        result = dict(run_id=plan['run_id'],protocol_sha256=fingerprint(plan),attempt=attempt,
            baseline=plan['baseline'],scope=plan['disposition'],paid_requests=1,independent_games_executed=0,
            rows=rows,arms={arm:metrics(rows,arm) for arm in ('S0','S1','Rule')},
            paired={arm:paired(rows,arm) for arm in ('S0','Rule')},budget=snap,
            resources=dict(environment=dict(receipts.started),worker_calls=snap['tool_calls'],gate_calls=gate_calls,
                           recovery_calls=len(worker_rows)-gate_calls,worker_seconds=sum(row['seconds'] for row in worker_rows)),
            peak_no_cache_estimate_usd=pilot.estimate_peak(actual['input_tokens'],actual['output_tokens']),
            actual_billed_usd=None)
        return pilot.commit(output/'result.json',result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','preflight','run','resume'))
    parser.add_argument('--base',type=Path,default=BASE)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--authorization',type=Path)
    args = parser.parse_args()
    base,output = args.base.resolve(),args.output.resolve()
    if args.command in ('prepare','preflight'):
        if args.command=='prepare':
            plan = prepare(base,output)
        else:
            plan,packet,*_ = configuration(base,output)
            verify_frozen(output,plan,packet)
            pilot.check_local_runtime(plan)
        summary = {key:plan[key] for key in ('run_id','max_calls','max_tokens','max_cost_microusd',
                  'peak_no_cache_quote_upper_usd','boundary_training_cases')}
        summary.update(protocol_sha256=fingerprint(plan),credential_configured=bool(pilot.configured_api_key()),
                       status='PREPARED' if args.command=='prepare' else 'PREFLIGHT_OK',paid_requests=0)
    else:
        if args.authorization is None:
            parser.error('run and resume require --authorization')
        result = run(base,output,authorization=read(args.authorization),resume=args.command=='resume')
        summary = {k:result[k] for k in ('run_id','scope','paid_requests','arms','resources','peak_no_cache_estimate_usd')}
        summary['delivery'] = result['attempt']['status']
    print(canonical(summary))


if __name__=='__main__':
    main()
