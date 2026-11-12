"""Freeze or run the B v11 source-only cross-mechanism Structured pilot."""

import argparse
from collections import Counter
import fcntl
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from alfworld_.binding_diagnostic import public_case
from alfworld_.decision_diagnostic import project
from alfworld_.failure_learning import EnvironmentPolicyRunner, context_view, register_environment_candidate
from alfworld_.generic_recovery_skill import GENERATION_PROMPT, VERSION, inspect, parse_skill, worker_source
from alfworld_.recovery_acquisition import (
    ANALYSIS_PROMPT, MERGE_FORMAT, MERGE_PROMPT, RecoveryAdapter, parse_mechanisms,
    parse_step_analyses, rank_mechanisms, recovery_view, stage_request,
)
from alfworld_.skill_acquisition import (
    INPUT_LIMIT, MODEL, StrictTrainEnv, _replay, _reset, _step, import_source_events, load_source,
    verify_source_game,
)
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import canonical, fingerprint
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.math_stream import read, save, sha
from failure_evo.run_health import trusted_usage
from run_alfworld_decision_v9 import ROOT
from run_alfworld_precondition_v10 import SOURCE, V9, historical_snapshot
from run_alfworld_skill_acquisition import IMAGE, WORKER, create_accounts

V10 = 'alfworld_precondition_v10_pilot_20261111_01'
PILOT = 'alfworld_cross_mechanism_v11_pilot_20261111_01'
MAX_CANDIDATES, SOURCE_WINDOW, OUTPUT_UPPER = 2, 18, 4096
PRICE = {'input_cents_per_million': 30, 'output_cents_per_million': 120}
GROUPS = ('container_precondition', 'lamp_interaction')


def name_family(anchor_action):
    """Research-only strata, excluded from every model and Worker payload."""
    if anchor_action.startswith('move '):
        return GROUPS[0]
    if anchor_action.startswith('go to '):
        return GROUPS[1]
    raise PermissionError('unrecognized historical stratum')


def history_snapshot(base):
    historical, v9 = historical_snapshot(base)
    v10 = base/V10
    plan, result = read(v10/'protocol.json'), read(v10/'result.json')
    if (result['protocol_sha256'] != fingerprint(plan)
            or result['proposal']['status'] != 'INVALID_CONDITION'
            or result['proposal']['reason'] != 'ROLE_BINDINGS'
            or any(sha(path) != digest for path,digest in plan['historical_sha256'].items())):
        raise PermissionError('B v10 provenance drift')
    roots = (v10, *base.glob('alfworld_precondition_v10_acceptance_*'))
    return {**historical, **{str(path.resolve()):sha(path) for root in roots
                             for path in root.rglob('*') if path.is_file()}}, v9


def public_state(key, goal, current, history, anchor):
    return project(public_case(key, goal, current['observation'], current['commands'], history, anchor))


def _decisive(origin):
    anchor = origin['projected']['anchor']
    steps = origin['steps']
    return next(step for previous, step in zip(steps[anchor-1:], steps[anchor:])
                if step['won'] or step['score'] > previous['score'])


def boundary_cases(events, host):
    """Freeze two copies of each boundary category before learning."""
    by_group = {group:[] for group in GROUPS}
    for event in events:
        origin = host[event['evidence_id']]
        by_group[name_family(origin['steps'][event['anchor']-1]['action'])].append(origin)
    result = []
    for index, group in enumerate(GROUPS):
        origin = by_group[group][0]
        goal = origin['projected']['goal']
        steps = origin['steps']
        index_at_failure = origin['projected']['anchor']-1
        prefix, anchor = steps[:index_at_failure+1], steps[index_at_failure]
        first_decisive = steps.index(_decisive(origin))
        native_ready = steps[first_decisive-1]
        distractor_goal = by_group[GROUPS[1-index]][0]['projected']['goal']
        # These are private development controls, not causal labels or prompts.
        if index == 0:
            instance_conflict = 'put the vase 3 on the safe 999.'
            other_phase = 'heat some vase and put it in safe.'
        else:
            instance_conflict = 'examine the cd with the desklamp 999.'
            other_phase = 'put some cd in desklamp.'
        rows = (
            ('wrong_goal', distractor_goal, anchor, prefix, index_at_failure, 'NO'),
            ('stale_failure', goal, steps[-1], steps, index_at_failure, 'NO'),
            ('state_changed', goal, native_ready, steps[:first_decisive], index_at_failure, 'NO'),
            ('wrong_phase', other_phase, anchor, prefix, index_at_failure, 'NO'),
            ('instance_conflict', instance_conflict, anchor, prefix, index_at_failure, 'NO'),
            ('insufficient', goal, dict(observation='You are in the room.',commands=['look','inventory']),
             [anchor], 0, 'UNKNOWN'),
            ('native_ready', goal, native_ready, steps[:first_decisive], None, 'NO'),
        )
        for category, task, current, history, selected, expected in rows:
            key = f'dev_{len(result)+1:03d}'
            result.append(dict(group=group, category=category, expected=expected,
                source_sequence=origin['sequence'], public=public_state(key,task,current,history,selected)))
    return result


def cohort(base):
    source_protocol, arms, host = load_source(base/SOURCE)
    events = arms['B']
    assert len(events) == 16
    if len({event['evidence_id'][:12] for event in events}) != len(events):
        raise PermissionError('ambiguous trajectory namespace')
    views, checkpoints = [], []
    for event in events:
        origin = host[event['evidence_id']]
        verify_source_game(source_protocol['data_root'],origin)
        anchor = origin['steps'][event['anchor']-1]
        if anchor['observation'] != 'Nothing happens.' or anchor['done'] or anchor['won']:
            raise PermissionError('nonterminal failure checkpoint required')
        view = recovery_view(event, anchor['commands'])
        views.append({key:view[key] for key in ('evidence_id', 'goal', 'initial_observation', 'steps',
                                               'failure_step_id', 'anchor_admissible_commands')})
        checkpoints.append(dict(evidence_id=event['evidence_id'], sequence=origin['sequence'],
                                source_receipt=origin['receipt_sha256'], anchor=event['anchor'],
                                group=name_family(anchor['action'])))
    if Counter(row['group'] for row in checkpoints) != dict(zip(GROUPS,(11,5))):
        raise PermissionError('historical cohort strata changed')
    return source_protocol, events, host, views, checkpoints, boundary_cases(events,host)


def wire_bound(views):
    sizes, hashes = [], []
    with TemporaryDirectory() as temp:
        for i in range(0,len(views),8):
            payload = dict(events=views[i:i+8])
            adapter = RecoveryAdapter(Path(temp)/'preflight.jsonl',None,model=MODEL,mock=True,
                sender=lambda _:None,stage='analyze',payload=payload,parser=None,protocol=VERSION,
                max_wire_input_upper=INPUT_LIMIT,analysis_prompt=ANALYSIS_PROMPT)
            wire = adapter.preflight(dict(phase='induction',max_tokens=OUTPUT_UPPER,
                discovery=dict(stage='analyze',payload_sha256=fingerprint(payload))))
            sizes.append(len(canonical(wire).encode())+256)
            hashes.append(fingerprint(wire))
    return sizes, hashes


def plan_for(base, output, mock):
    protected = [base/SOURCE, *base.glob('alfworld_recovery_v[3-7]_*'),
                 *base.glob('alfworld_binding_v8_*'), *base.glob('alfworld_decision_v9_*'),
                 *base.glob('alfworld_precondition_v10_*')]
    if any(output.resolve().is_relative_to(path.resolve()) or path.resolve().is_relative_to(output.resolve())
           for path in protected):
        raise PermissionError('v11 requires a separate run directory')
    historical, v9 = history_snapshot(base)
    source, events, host, views, checkpoints, boundaries = cohort(base)
    backend = FrozenLinuxBackend(image=IMAGE, worker_script=WORKER)
    sizes, hashes = wire_bound(views)
    bounds = [*sizes, INPUT_LIMIT, *([INPUT_LIMIT]*MAX_CANDIDATES)]
    files = [Path(__file__).resolve(), ROOT/'scripts/run_alfworld_precondition_v10.py',
             ROOT/'scripts/run_alfworld_skill_acquisition.py', ROOT/'scripts/test_alfworld_cross_mechanism_v11.py']
    for folder in ('alfworld_', 'failure_evo', 'runtime'):
        files.extend((ROOT/'FlowEvo/src'/folder).glob('*.py'))
    plan = dict(
        version=VERSION, scope='MOCK_CROSS_MECHANISM' if mock else 'REAL_STRUCTURED_SOURCE_ONLY',
        run_id=('mock:' if mock else 'real:')+output.name, model=MODEL,
        model_release_reference='DeepSeek-V4.1-Flash-1017', temperature=0, thinking='disabled',
        response_format='json_object', analysis_prompt_sha256=fingerprint(ANALYSIS_PROMPT),
        merge_prompt_sha256=fingerprint(MERGE_PROMPT+MERGE_FORMAT), generation_prompt_sha256=fingerprint(GENERATION_PROMPT),
        analysis_wire_sha256=hashes, learning_sha256=fingerprint(views), source_protocol_sha256=fingerprint(source),
        checkpoints_sha256=fingerprint(checkpoints), boundaries_sha256=fingerprint(boundaries),
        historical_sha256=historical, code_sha256={str(path.relative_to(ROOT)):sha(path) for path in sorted(set(files))},
        worker=backend.manifest(), candidate_cap=MAX_CANDIDATES, source_window=SOURCE_WINDOW,
        local_metric='recorded decisive action newly enabled or actual score/win progression',
        worker_calls=len(checkpoints)*SOURCE_WINDOW + MAX_CANDIDATES*len(boundaries), worker_seconds_per_invocation=2,
        max_calls=len(bounds), request_input_upper=bounds, output_upper=OUTPUT_UPPER,
        max_tokens=sum(bounds)+len(bounds)*OUTPUT_UPPER,
        max_cost_microusd=sum((120*(size+OUTPUT_UPPER)+99)//100 for size in bounds),
        quote_upper_usd=(sum(bounds)*PRICE['input_cents_per_million']
                         +len(bounds)*OUTPUT_UPPER*PRICE['output_cents_per_million'])/100_000_000,
        price=PRICE, network_policy=v9['network_policy'], disposition='SHADOW_SOURCE_ONLY',
    )
    return plan, source, events, host, views, checkpoints, boundaries, backend


def grant(plan):
    return dict(run_id=plan['run_id'],protocol_hash=fingerprint(plan),model=MODEL,protocol=VERSION,
                max_cost_microusd=plan['max_cost_microusd'],paid_api_authorized=True)


def generation_payload(mechanism, analyses, views):
    selected = set(mechanism['evidence_ids'])
    by_id = {row['evidence_id']:row for row in analyses}
    included = []
    for view in views:
        eid = view['evidence_id']
        if eid not in selected:
            continue
        analysis = by_id[eid]
        idx = next(i for i,row in enumerate(view['steps']) if row[0]==view['failure_step_id'])
        refs = {row['step_id'] for row in analysis['recovery']}
        refs.update(row[0] for row in view['steps'][max(0,idx-2):idx+2])
        included.append(dict(evidence_id=eid,goal=view['goal'],failure_step_id=view['failure_step_id'],
            steps=[row for row in view['steps'] if row[0] in refs],
            anchor_admissible_commands=view['anchor_admissible_commands'], analysis=analysis))
    return dict(mechanism=mechanism, source_receipts=included)


def decision(skill, public, card, runner, *, starting):
    verdict = inspect(skill,public,starting=starting)
    selection = verdict['selection']
    if selection is None:
        return verdict, dict(status='declined',reason='no verified applicable action')
    context = context_view(public['goal'],public['observation'],public['admissible_commands'],
                           public['history'],selection)
    operator = runner.run(card,context)
    execution_id = fingerprint([card.version,context,runner.backend.manifest()])
    receipt = next(row['payload'] for row in reversed(runner.events.records())
                   if row['kind']=='ENVIRONMENT_POLICY_EXECUTED' and row['payload']['execution_id']==execution_id)
    verdict['worker'] = dict(execution_id=execution_id,seconds=receipt['seconds'])
    return verdict, operator


def validate_source(data, origin, skill, card, runner, registry, path):
    anchor = origin['projected']['anchor']
    key = fingerprint([VERSION,card.version,origin['receipt_sha256'],anchor,SOURCE_WINDOW,runner.backend.manifest()])
    if registry.state(card)['permission'] != 'shadow' or not card.intact():
        raise PermissionError('exact Shadow candidate required')
    if path.exists():
        result = read(path)
        if result['validation_sha256'] != key:
            raise PermissionError('source verification identity drift')
        return result
    prefix = origin['steps'][:anchor]
    current = prefix[-1]
    initial = current
    decisive = _decisive(origin)['action']
    branch, calls = [], []
    seen = set()
    stop_reason = 'ACTION_LIMIT'
    local = None
    env = StrictTrainEnv(data,max_steps=50)
    try:
        env.initialize(frozen_game_files=[str(verify_source_game(data,origin))])
        _reset(env,origin)
        _replay(env,prefix)
        for offset in range(min(SOURCE_WINDOW,50-anchor)):
            public = public_state('source',origin['projected']['goal'],current,prefix+branch,anchor-1)
            verdict, selected = decision(skill,public,card,runner,starting=offset==0)
            calls.append(dict(conditions=verdict,operator=selected))
            if selected['status']!='applied':
                stop_reason = 'POLICY_ERROR' if selected['status']=='error' else 'DECLINED'
                break
            action = selected['action']
            if action not in current['commands']:
                raise PermissionError('action absent from exact environment commands')
            public_identity = fingerprint([current['observation'],current['commands'],action])
            if public_identity in seen:
                stop_reason = 'REPEATED_PUBLIC_ACTION'
                break
            seen.add(public_identity)
            after = _step(env,action)
            branch.append(after)
            if local is None and decisive not in initial['commands'] and decisive in after['commands']:
                local = dict(kind='HISTORIC_DECISIVE_ACTION_NEWLY_ADMISSIBLE',step=len(branch),action=decisive)
            if local is None and (after['score']>current['score'] or after['won']):
                local = dict(kind='ENVIRONMENT_SCORE_OR_WIN',step=len(branch),action=action)
            if after['done'] or after['won']:
                stop_reason = 'ENVIRONMENT_TERMINAL'
                break
            if after['observation']=='Nothing happens.':
                stop_reason = 'LEGAL_NO_PROGRESS'
                break
            current = after
    finally:
        env.close()
    result = dict(validation_sha256=key,sequence=origin['sequence'],
        group=name_family(initial['action']),selected_failure=initial['action'],anchor=anchor,
        triggered=bool(branch),local_repair_verified=local is not None,local_witness=local,
        won=bool(branch and branch[-1]['won']),native_decisive_already_admissible=decisive in initial['commands'],
        stop=stop_reason,legal_no_progress=sum(row['observation']=='Nothing happens.' for row in branch),
        worker_decisions=sum(row['conditions']['selection'] is not None for row in calls),
        calls=calls,alternative=branch,native_same_horizon=origin['steps'][anchor:anchor+len(branch)])
    save(path,result)
    return result


def summarize(source_rows, boundary_rows):
    groups = {}
    for group in GROUPS:
        local = [row for row in source_rows if row['group']==group]
        boundary = [row for row in boundary_rows if row['group']==group]
        groups[group] = dict(sources=len(local),triggered=sum(row['triggered'] for row in local),
            local_repair=sum(row['local_repair_verified'] for row in local),won=sum(row['won'] for row in local),
            native_ready=sum(row['native_decisive_already_admissible'] for row in local),
            over_rejected=sum(not row['triggered'] and row['stop']=='DECLINED'
                              and not row['native_decisive_already_admissible'] for row in local),
            source_unknown=sum(row['calls'][0]['conditions']['entry']=='UNKNOWN' for row in local if row['calls']),
            legal_no_progress=sum(row['legal_no_progress'] for row in local),
            execution_errors=sum(row['stop']=='POLICY_ERROR' for row in local)+sum(row['status']=='error' for row in boundary),
            worker_decisions=sum(row['worker_decisions'] for row in local)+sum(row['worker_called'] for row in boundary),
            worker_receipt_seconds=sum({receipt['execution_id']:receipt['seconds']
                for receipt in [*(call['conditions']['worker'] for row in local for call in row['calls']
                                  if 'worker' in call['conditions']),
                                *(row['conditions']['worker'] for row in boundary if row['worker_called'])]}.values()),
            boundary_correct_decline=sum(row['expected']=='NO' and row['status']=='declined' for row in boundary),
            boundary_false_trigger=sum(row['expected']=='NO' and row['status']=='applied' for row in boundary),
            boundary_uncertain_trigger=sum(row['expected']=='UNKNOWN' and row['status']=='applied' for row in boundary),
            boundary_unknown=sum(row['expected']=='UNKNOWN' and row['status']=='declined' for row in boundary))
    return groups


def run(base, output, *, sender=None, authorization=None):
    mock = sender is not None
    plan, source, events, host, views, checkpoints, boundaries, backend = plan_for(base,output,mock)
    path = output/'protocol.json'
    if not mock:
        if not path.exists():
            raise PermissionError('prepared v11 protocol required')
        plan['mock_acceptance'] = read(path)['mock_acceptance']
        if authorization != grant(plan):
            raise PermissionError('explicit matching v11 authorization required')
    output.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if path.exists() and read(path)!=plan:
            raise PermissionError('frozen v11 plan drift')
        if mock:
            save(path,plan)
        else:
            for name,value in [('learning.public.json',views),('checkpoints.private.json',checkpoints),
                               ('boundaries.private.json',boundaries)]:
                if read(output/name)!=value:
                    raise PermissionError('frozen v11 data copy changed')
        try:
            return _run(plan,source,events,host,views,checkpoints,boundaries,backend,output,sender,authorization)
        except (Exception, KeyboardInterrupt) as exc:
            save(output/'interruption.json',dict(type=type(exc).__name__,reason=str(exc),
                protocol_sha256=fingerprint(plan)))
            raise


def _run(plan, source, events, host, views, checkpoints, boundaries, backend, output, sender, authorization):
    budget = create_accounts(output,plan)
    registry = FailureOperatorRegistry(output/'registry.jsonl',FailureEvidenceStore(output/'failures.jsonl'))
    runner = EnvironmentPolicyRunner(backend,output/'worker.jsonl',budget)
    evidence = import_source_events('B',events,host,output,registry.evidence,plan['run_id'])
    known = {row['event_id']:row for row in registry.evidence.visible(time(),plan['run_id'])}
    receipts = []

    def stage(name, kind, payload, parser, prompt=ANALYSIS_PROMPT):
        response = stage_request(output,name,kind,payload,parser,budget,sender=sender,authorization=authorization,
            network_policy=None if sender is not None else plan['network_policy'],protocol=VERSION,analysis_prompt=prompt)
        receipts.append(dict(stage=name,response_id=response['id'],response_sha256=response['response_sha256'],
                             usage=trusted_usage(response['raw_response']),parse_status=response.get('parse_status')))
        return response, json.loads(response['specification']) if not response.get('parse_status') else None

    analyses, rejected = [], []
    for start in range(0,len(views),8):
        view_batch, batch = views[start:start+8], events[start:start+8]
        response, parsed = stage(f'analysis_{start//8}','analyze',dict(events=view_batch),
                                 lambda value:parse_step_analyses(value,batch))
        if response['wire_sha256'] != plan['analysis_wire_sha256'][start//8]:
            raise PermissionError('analysis wire drift')
        if parsed:
            analyses.extend(parsed['analyses'])
            rejected.extend(parsed['rejected'])
        else:
            rejected.extend(dict(evidence_id=row['evidence_id'],reason='BATCH_DELIVERY_REJECTED') for row in batch)
    eligible = [row for row in analyses if row['decision']=='HYPOTHESIS']
    merged = None
    if eligible:
        _, merged = stage('merge','merge',dict(analyses=eligible),lambda value:parse_mechanisms(value,eligible))
    ranked = rank_mechanisms(merged,analyses) if merged else []
    candidates = []
    for index,item in enumerate(ranked):
        mechanism = item['proposal']
        ids = mechanism['evidence_ids']
        groups = sorted({row['group'] for row in checkpoints if row['evidence_id'] in ids})
        record = dict(mechanism_id=item['mechanism_id'],mechanism=mechanism,source_groups=groups,
                      support_count=len(ids),status='FROZEN_CAP_NOT_SELECTED')
        candidates.append(record)
        if index >= MAX_CANDIDATES:
            continue
        payload = generation_payload(mechanism,eligible,views)
        anchors = {row['evidence_id']:row['failure_step_id'] for row in payload['source_receipts']}
        steps = {step[0] for row in payload['source_receipts'] for step in row['steps']}
        directory = output/f'candidate_{index}'
        response, parsed = stage(directory.name,'analyze',payload,lambda value:parse_skill(value,anchors,steps),
                                 GENERATION_PROMPT)
        record.update(parsed or dict(status='PROVIDER_DELIVERY_REJECTED',candidate=None))
        if not record['candidate']:
            continue
        skill = record['candidate']
        source_code = worker_source(skill)
        generated = dict(code=source_code,description='Host-compiled adapter for declarative model proposal',
            applicability=skill['scope'],model=response['model'],id=response['id'],response_sha256=response['response_sha256'])
        registration = register_environment_candidate(directory,generated,dict(mechanism=mechanism,skill=skill),
            list(evidence.values()),known,backend.manifest(),registry,engineering=sender is not None,
            protocol=VERSION,baseline='alfworld-structured-shadow')
        record.update(registration)
        if registration['status']!='SHADOW':
            continue
        card = FailureOperator.from_dict(registration['card'])
        selected_checkpoints = [row for row in checkpoints if row['evidence_id'] in ids]
        source_rows = [validate_source(source['data_root'],host[row['evidence_id']],skill,card,runner,registry,
                                        directory/f"source_{row['sequence']}.json") for row in selected_checkpoints]
        boundary_rows = []
        for fixture in boundaries:
            verdict, operator = decision(skill,fixture['public'],card,runner,starting=True)
            boundary_rows.append(dict(id=fixture['public']['id'],group=fixture['group'],category=fixture['category'],
                expected=fixture['expected'],status=operator['status'],worker_called=verdict['selection'] is not None,
                conditions=verdict,operator=operator))
        record.update(source_validation=source_rows,boundary_validation=boundary_rows,
                      metrics=summarize(source_rows,boundary_rows))
        record['development_reviewable'] = (
            any(row['local_repair_verified'] for row in source_rows)
            and not any(row['stop']=='POLICY_ERROR' for row in source_rows)
            and not any(row['status'] in ('applied','error') for row in boundary_rows)
        )
        if registry.state(card)['permission'] != 'shadow':
            raise PermissionError('unexpected candidate permission')
        save(directory/'validation.json',record)
    usage = Counter()
    for receipt in receipts:
        usage.update(receipt['usage'])
    by_group = {}
    for group in GROUPS:
        rows = [item for item in candidates if item['source_groups']==[group]]
        by_group[group] = dict(hypotheses=len(rows),shadow_candidates=sum(row['status']=='SHADOW' for row in rows),
            source_witness_candidates=sum(any(s['local_repair_verified'] for s in row.get('source_validation',[])) for row in rows),
            reviewable_candidates=sum(row.get('development_reviewable',False) for row in rows))
    result = dict(scope=plan['scope'],protocol_sha256=fingerprint(plan),analyses=analyses,rejected_analyses=rejected,
        merge=merged,candidates=candidates,by_group=by_group,model_receipts=receipts,usage=dict(usage),
        cross_mechanism_source_witness=all(group['source_witness_candidates'] for group in by_group.values()),
        cross_mechanism_reviewable=all(group['reviewable_candidates'] for group in by_group.values()),
        paid_requests=len(receipts) if sender is None else 0,budget=budget.snapshot(),
        quote_estimated_usd=(30*usage['input_tokens']+120*usage['output_tokens'])/100_000_000,
        disposition=plan['disposition'],independent_gate_games=0)
    if any(sha(path)!=digest for path,digest in plan['historical_sha256'].items()):
        raise PermissionError('historical artifact changed during v11')
    save(output/'result.json',result)
    return result


def _same(plan):
    return {key:value for key,value in plan.items() if key not in ('run_id','scope','mock_acceptance')}


def prepare(base,output,mock_output):
    plan,_,_,_,views,checkpoints,boundaries,_ = plan_for(base,output,False)
    mock_plan,result = read(mock_output/'protocol.json'),read(mock_output/'result.json')
    if (_same(plan)!=_same(mock_plan) or mock_plan['scope']!='MOCK_CROSS_MECHANISM'
            or result['protocol_sha256']!=fingerprint(mock_plan) or result['paid_requests']!=0
            or not result['cross_mechanism_source_witness']
            or not result['budget']['tool_calls']):
        raise PermissionError('matching two-stratum zero API source/Worker acceptance required')
    plan['mock_acceptance'] = dict(protocol_sha256=fingerprint(mock_plan),result_sha256=sha(mock_output/'result.json'))
    output.mkdir(mode=0o700,exist_ok=False,parents=True)
    for name,value in [('protocol.json',plan),('learning.public.json',views),('checkpoints.private.json',checkpoints),
                       ('boundaries.private.json',boundaries),('authorization.template.json',{**grant(plan),'paid_api_authorized':False})]:
        save(output/name,value)
    return plan


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('action',choices=('prepare','run'))
    cli.add_argument('--base',type=Path,default=Path.home()/'.local/share/flowevo')
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--mock-output',type=Path)
    cli.add_argument('--authorization',type=Path)
    args = cli.parse_args()
    if args.action=='prepare':
        if not args.mock_output:
            cli.error('prepare requires --mock-output')
        plan = prepare(args.base,args.output,args.mock_output)
        print(canonical(dict(status='PREPARED_NOT_AUTHORIZED',protocol_sha256=fingerprint(plan),
                             max_calls=plan['max_calls'],max_cost_microusd=plan['max_cost_microusd'])))
    else:
        if not args.authorization:
            cli.error('run requires --authorization')
        result = run(args.base,args.output,authorization=read(args.authorization))
        print(canonical(dict(status=result['disposition'],by_group=result['by_group'],
                             paid_requests=result['paid_requests'])))


if __name__=='__main__':
    main()
