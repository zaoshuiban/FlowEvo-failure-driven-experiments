"""Small frozen B v12 generation Pilot with source-only Shadow validation."""

import argparse
from collections import Counter
import fcntl
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from alfworld_.failure_learning import EnvironmentPolicyRunner, context_view, register_environment_candidate
from alfworld_.generic_recovery_skill import worker_source
from alfworld_.recovery_acquisition import RecoveryAdapter, parse_mechanisms, stage_request
from alfworld_.recovery_skill_v12 import PROMPT, VERSION, inspect, parse_skill
from alfworld_.skill_acquisition import INPUT_LIMIT, StrictTrainEnv, _replay, _reset, _step, import_source_events, verify_source_game
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.math_stream import read, save, sha
from failure_evo.run_health import trusted_usage
import run_alfworld_cross_mechanism_expanded as expanded

previous = expanded.previous
PILOT = 'alfworld_recovery_v12_pilot_20261111_01'
GROUPS = (*previous.GROUPS, expanded.NAVIGATION)


def configuration(base, output, mock):
    parent = base/expanded.EXPANDED
    protected = [base/previous.SOURCE, *base.glob('alfworld_recovery_v[3-7]_*'),
                 *base.glob('alfworld_binding_v8_*'), *base.glob('alfworld_decision_v9_*'),
                 *base.glob('alfworld_precondition_v10_*'), *base.glob('alfworld_cross_mechanism_v11_*')]
    if any(output.resolve().is_relative_to(path.resolve()) or path.resolve().is_relative_to(output.resolve())
           for path in protected):
        raise PermissionError('v12 needs a separate directory')
    old,source,events,host,views,checkpoints,boundaries,backend = expanded.configuration(base,parent,False)
    result = read(parent/'result.json')
    if (old!=read(parent/'protocol.json') or result['protocol_sha256']!=fingerprint(old)
            or result['scope']!='REAL_EXPANDED_SOURCE_ONLY' or result['paid_requests']!=8):
        raise PermissionError('expanded v11 receipt mismatch')
    provider = EvidenceStore(parent/'provider.jsonl').records()
    merge_sha = next(row['response_sha256'] for row in result['model_receipts'] if row['stage']=='merge')
    raw, = [row['payload']['response'] for row in provider
            if row['kind']=='RAW_RESPONSE' and row['payload']['sha256']==merge_sha]
    if fingerprint(raw)!=merge_sha or raw['choices'][0]['finish_reason']!='stop':
        raise PermissionError('expanded merge response integrity mismatch')
    analyses = [row for row in result['analyses'] if row['decision']=='HYPOTHESIS']
    merged = parse_mechanisms(json.loads(raw['choices'][0]['message']['content']),analyses)
    if merged!=result['merge'] or len(merged['mechanisms'])!=3:
        raise PermissionError('three frozen mechanisms required')
    by_eid = {row['evidence_id']:row for row in checkpoints}
    scheduled, budget_sizes = [], []
    with TemporaryDirectory() as temp:
        for mechanism in merged['mechanisms']:
            selected = [by_eid[key] for key in mechanism['evidence_ids']]
            groups = {row['group'] for row in selected}
            if len(groups)!=1:
                raise PermissionError('mechanism stratum ambiguous')
            group = groups.pop()
            payload = previous.generation_payload(mechanism,analyses,views)
            adapter = RecoveryAdapter(Path(temp)/'preflight.jsonl',None,model=previous.MODEL,
                mock=True,sender=lambda _:None,stage='analyze',payload=payload,parser=None,protocol=VERSION,
                analysis_prompt=PROMPT,max_wire_input_upper=INPUT_LIMIT)
            wire=adapter.preflight(dict(phase='induction',max_tokens=previous.OUTPUT_UPPER,
                discovery=dict(stage='analyze',payload_sha256=fingerprint(payload))))
            scheduled.append((group,selected,payload,fingerprint(wire)))
            budget_sizes.append(len(canonical(wire).encode())+256)
    if {item[0] for item in scheduled}!=set(GROUPS):
        raise PermissionError('one request per original mechanism required')
    historical={**old['historical_sha256'], **{str(path.resolve()):sha(path) for path in parent.rglob('*') if path.is_file()}}
    files={Path(__file__).resolve(), previous.ROOT/'FlowEvo/src/alfworld_/recovery_skill_v12.py',
           previous.ROOT/'scripts/test_alfworld_recovery_v12.py',
           *(previous.ROOT/name for name in old['code_sha256'])}
    plan=dict(
        version=VERSION,scope='MOCK_RELIABILITY' if mock else 'REAL_STRUCTURED_SOURCE_ONLY',
        run_id=('mock:' if mock else 'real:')+output.name,model=previous.MODEL,
        source_protocol_sha256=fingerprint(source),parent_protocol_sha256=fingerprint(old),
        checkpoints_sha256=fingerprint(checkpoints),boundaries_sha256=fingerprint(boundaries),
        learning_sha256=fingerprint([row[2] for row in scheduled]),generation_prompt_sha256=fingerprint(PROMPT),
        parent_merge_response_sha256=merge_sha,historical_sha256=historical,
        code_sha256={str(path.relative_to(previous.ROOT)):sha(path) for path in sorted(files)},
        schedule=[dict(group=group,source_sequences=[row['sequence'] for row in selected],wire_sha256=wire,
                       input_upper=size,output_upper=previous.OUTPUT_UPPER)
                  for (group,selected,_,wire),size in zip(scheduled,budget_sizes,strict=True)],
        max_calls=len(scheduled),max_tokens=sum(budget_sizes)+len(scheduled)*previous.OUTPUT_UPPER,
        max_cost_microusd=sum((120*(size+previous.OUTPUT_UPPER)+99)//100 for size in budget_sizes),
        quote_upper_usd=(30*sum(budget_sizes)+120*len(scheduled)*previous.OUTPUT_UPPER)/100_000_000,
        worker_calls=sum(len(row[1]) for row in scheduled)*previous.SOURCE_WINDOW+len(scheduled)*len(boundaries),
        source_window=previous.SOURCE_WINDOW,worker=backend.manifest(),network_policy=old['network_policy'],
        disposition='SHADOW_SOURCE_ONLY',
    )
    return plan,source,events,host,scheduled,boundaries,backend


def grant(plan):
    return dict(run_id=plan['run_id'],protocol_hash=fingerprint(plan),model=plan['model'],protocol=VERSION,
                max_cost_microusd=plan['max_cost_microusd'],paid_api_authorized=True)


def _same(plan):
    return {key:value for key,value in plan.items() if key not in ('run_id','scope','mock_acceptance')}


def prepare(base,output,mock_output):
    plan,*_ = configuration(base,output,False)
    mock, result=read(mock_output/'protocol.json'), read(mock_output/'result.json')
    if (_same(plan)!=_same(mock) or mock['scope']!='MOCK_RELIABILITY'
            or result['protocol_sha256']!=fingerprint(mock) or result['paid_requests']!=0
            or not all(any(row['local_repair_verified'] for row in c.get('sources',[]))
                       for c in result['candidates']) or len(result['candidates'])!=3):
        raise PermissionError('matching three-mechanism zero-API acceptance required')
    plan['mock_acceptance']=dict(protocol_sha256=fingerprint(mock),result_sha256=sha(mock_output/'result.json'))
    output.mkdir(mode=0o700,exist_ok=False,parents=True)
    save(output/'protocol.json',plan)
    save(output/'authorization.template.json',{**grant(plan),'paid_api_authorized':False})
    return plan


def decide(skill, public, card, runner, *, starting):
    checks=inspect(skill,public,starting=starting)
    if checks['selection'] is None:
        return checks,dict(status='declined',reason=checks['block'])
    context=context_view(public['goal'],public['observation'],public['admissible_commands'],
                         public['history'],checks['selection'])
    return checks,runner.run(card,context)


def validate_source(data, origin, skill, card, runner, registry, path):
    anchor=origin['projected']['anchor']
    receipt_id=fingerprint([VERSION,card.version,origin['receipt_sha256'],anchor,previous.SOURCE_WINDOW,
                            runner.backend.manifest()])
    if registry.state(card)['permission']!='shadow' or not card.intact():
        raise PermissionError('exact Shadow card required')
    if path.exists():
        result=read(path)
        if result['validation_sha256']!=receipt_id:
            raise PermissionError('source validation drift')
        return result
    prefix=origin['steps'][:anchor]
    current=prefix[-1]
    decisive=previous._decisive(origin)['action']
    ready=decisive in current['commands']
    branch,decisions,seen=[],[],set()
    witness=None
    stop='ACTION_LIMIT'
    env=StrictTrainEnv(data,max_steps=50)
    try:
        env.initialize(frozen_game_files=[str(verify_source_game(data,origin))])
        _reset(env,origin)
        _replay(env,prefix)
        for offset in range(min(previous.SOURCE_WINDOW,50-anchor)):
            public=previous.public_state('source',origin['projected']['goal'],current,prefix+branch,anchor-1)
            checks,action=decide(skill,public,card,runner,starting=offset==0)
            decisions.append(dict(checks=checks,operator=action))
            if action['status']!='applied':
                stop='POLICY_ERROR' if action['status']=='error' else action['reason']
                break
            command=action['action']
            if command not in current['commands']:
                raise PermissionError('action absent from live legal commands')
            identity=fingerprint([current['observation'],current['commands'],command])
            if identity in seen:
                stop='REPEATED_PUBLIC_ACTION'
                break
            seen.add(identity)
            after=_step(env,command)
            branch.append(after)
            if witness is None and not ready and decisive in after['commands']:
                witness=dict(kind='DECISIVE_ACTION_NEWLY_ADMISSIBLE',step=len(branch),action=decisive)
            if witness is None and (after['won'] or after['score']>current['score']):
                witness=dict(kind='ENVIRONMENT_SCORE_OR_WIN',step=len(branch),action=command)
            if after['done'] or after['won']:
                stop='ENVIRONMENT_TERMINAL'
                break
            if after['observation']=='Nothing happens.':
                stop='LEGAL_NO_PROGRESS'
                break
            current=after
    finally:
        env.close()
    result=dict(validation_sha256=receipt_id,sequence=origin['sequence'],anchor=anchor,stop=stop,
                triggered=bool(branch),local_repair_verified=witness is not None,local_witness=witness,
                native_decisive_already_admissible=ready,won=bool(branch and branch[-1]['won']),
                actions=branch,decisions=decisions)
    save(path,result)
    return result


def run(base,output,*,sender=None,authorization=None):
    mock=sender is not None
    plan,source,events,host,scheduled,boundaries,backend=configuration(base,output,mock)
    path=output/'protocol.json'
    if not mock:
        if not path.exists():
            raise PermissionError('v12 protocol must be prepared first')
        plan['mock_acceptance']=read(path)['mock_acceptance']
        if authorization!=grant(plan):
            raise PermissionError('exact separate v12 authorization required')
    output.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if path.exists() and read(path)!=plan:
            raise PermissionError('v12 frozen protocol drift')
        if mock:
            save(path,plan)
        try:
            return _run(plan,source,events,host,scheduled,boundaries,backend,output,sender,authorization)
        except (Exception,KeyboardInterrupt) as exc:
            save(output/'interruption.json',dict(protocol_sha256=fingerprint(plan),type=type(exc).__name__,reason=str(exc)))
            raise


def _run(plan,source,events,host,scheduled,boundaries,backend,output,sender,authorization):
    budget=previous.create_accounts(output,plan)
    registry=FailureOperatorRegistry(output/'registry.jsonl',FailureEvidenceStore(output/'failures.jsonl'))
    runner=EnvironmentPolicyRunner(backend,output/'worker.jsonl',budget)
    evidence=import_source_events('B',events,host,output,registry.evidence,plan['run_id'])
    known={row['event_id']:row for row in registry.evidence.visible(time(),plan['run_id'])}
    candidates,usage=[],Counter()
    for index,(group,selected,payload,wire_hash) in enumerate(scheduled):
        name=f'candidate_{index}'
        directory=output/name
        anchors={row['evidence_id']:row['failure_step_id'] for row in payload['source_receipts']}
        steps={step[0] for row in payload['source_receipts'] for step in row['steps']}
        response=stage_request(output,name,'analyze',payload,lambda value:parse_skill(value,anchors,steps),budget,
            sender=sender,authorization=authorization,network_policy=plan['network_policy'] if sender is None else None,
            protocol=VERSION,analysis_prompt=PROMPT)
        if response['wire_sha256']!=wire_hash:
            raise PermissionError('v12 wire differs from freeze')
        usage.update(trusted_usage(response['raw_response']))
        proposal=(dict(status='PROVIDER_DELIVERY_REJECTED',reason=response.get('contract_diagnostic'),candidate=None)
                  if response.get('parse_status') else json.loads(response['specification']))
        record=dict(group=group,response_sha256=response['response_sha256'],proposal=proposal,status=proposal['status'])
        candidates.append(record)
        skill=proposal['candidate']
        if skill is None:
            continue
        generated=dict(code=worker_source(skill),description='Host-compiled v12 declarative adapter',
                       applicability=skill['scope'],model=response['model'],id=response['id'],
                       response_sha256=response['response_sha256'])
        registration=register_environment_candidate(directory,generated,dict(mechanism=payload['mechanism'],skill=skill),
            list(evidence.values()),known,backend.manifest(),registry,engineering=sender is not None,
            protocol=VERSION,baseline='alfworld-v12-structured-shadow')
        record.update(registration)
        if registration['status']!='SHADOW':
            continue
        card=FailureOperator.from_dict(registration['card'])
        sources=[validate_source(source['data_root'],host[row['evidence_id']],skill,card,runner,registry,
                                 directory/f"source_{row['sequence']}.json") for row in selected]
        controls=[]
        for case in boundaries:
            checks,action=decide(skill,case['public'],card,runner,starting=True)
            controls.append(dict(group=case['group'],category=case['category'],expected=case['expected'],
                                 status=action['status'],checks=checks,operator=action))
        record.update(sources=sources,boundaries=controls,metrics=dict(
            source_checks=len(sources),source_triggers=sum(x['triggered'] for x in sources),
            local_witnesses=sum(x['local_repair_verified'] for x in sources),wins=sum(x['won'] for x in sources),
            source_stops=dict(Counter(x['stop'] for x in sources)),boundary_checks=len(controls),
            boundary_false_triggers=sum(x['expected']=='NO' and x['status']=='applied' for x in controls),
            boundary_uncertain_triggers=sum(x['expected']=='UNKNOWN' and x['status']=='applied' for x in controls),
            boundary_errors=sum(x['status']=='error' for x in controls)),
            development_reviewable=(any(x['local_repair_verified'] for x in sources)
                and all(x['stop']!='POLICY_ERROR' for x in sources)
                and all(x['status']=='declined' for x in controls)))
        if registry.state(card)['permission']!='shadow':
            raise PermissionError('unexpected candidate permission')
        save(directory/'validation.json',record)
    result=dict(scope=plan['scope'],protocol_sha256=fingerprint(plan),candidates=candidates,
        budget=budget.snapshot(),paid_requests=len(candidates) if sender is None else 0,
        usage=dict(usage),quote_estimated_usd=(30*usage['input_tokens']+120*usage['output_tokens'])/100_000_000,
        independent_gate_games=0,disposition=plan['disposition'])
    if any(sha(path)!=digest for path,digest in plan['historical_sha256'].items()):
        raise PermissionError('historical artifact changed during v12')
    save(output/'result.json',result)
    return result


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('action',choices=('prepare','run'))
    cli.add_argument('--base',type=Path,default=Path.home()/'.local/share/flowevo')
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--mock-output',type=Path)
    cli.add_argument('--authorization',type=Path)
    args=cli.parse_args()
    if args.action=='prepare':
        if not args.mock_output:
            cli.error('prepare requires --mock-output')
        plan=prepare(args.base,args.output,args.mock_output)
        print(canonical(dict(status='PREPARED_NOT_AUTHORIZED',protocol_sha256=fingerprint(plan),
                             max_calls=plan['max_calls'],max_cost_microusd=plan['max_cost_microusd'])))
    else:
        if not args.authorization:
            cli.error('run requires --authorization')
        result=run(args.base,args.output,authorization=read(args.authorization))
        print(canonical(dict(paid_requests=result['paid_requests'],
                             candidates=[dict(group=x['group'],status=x['status'],metrics=x.get('metrics'))
                                         for x in result['candidates']])))


if __name__=='__main__':
    main()
