"""Fixed-mechanism, post-failure B v6 Pilot. No dispatch without an exact grant."""
import argparse
import fcntl
import json
from pathlib import Path
import time

from alfworld_.failure_learning import EnvironmentPolicyRunner, context_view, register_environment_candidate, static_check
from alfworld_.recovery_acquisition import recovery_metrics, stage_request
from alfworld_.skill_acquisition import (
    INPUT_LIMIT, MODEL, StrictTrainEnv, _has_instance_literals, _replay, _reset, _step,
    import_source_events, verify_source_game,
)
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.math_stream import read, save, sha
from run_alfworld_recovery_v5 import prepare as import_v4
from run_alfworld_skill_acquisition import create_accounts

VERSION = 'alfworld-recovery-acquisition-v6'
WINDOW = 12
ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = """
This is post-feedback recovery under the supplied fixed mechanism. Implement three
auditable decisions: Trigger (a currently unresolved relevant failure), Binding
(the intended object, specific destination and correct task phase), and Recovery
(a legal, relevant next action supported by those checks). The first call receives
empty policy state and public history through the actual failure feedback. Later
calls receive actual new observations and your own bounded state. Do not assume
the latest history entry, or an older failed command, is still relevant. Check
goal consistency, object and instance identity, current preconditions, intervening
actions, changed task stage and whether the subgoal is already resolved. Before
any follow-up, recheck that it still serves the same unresolved objective. Decline
when evidence is missing or ambiguous, or when the mechanism no longer applies.
Never pick a legal action merely because it is listed. Keep the existing return
schema. Use reason to identify the earliest unsupported stage when possible.
"""


def added_negatives():
    def case(name,goal,obs,commands,history):
        return dict(id=name,category='resolved_or_changed_context',expected='declined',
                    context=context_view(goal,obs,commands,history,{}))
    failed=dict(action='move cup 2 to cabinet 4',observation='Nothing happens.')
    opened=dict(action='open cabinet 4',observation='The cabinet 4 is open.')
    placed=dict(action='move cup 2 to cabinet 4',observation='You move the cup 2 to the cabinet 4.')
    return [
        case('obstacle_already_resolved','put some cup in cabinet.','The cabinet 4 is open.',
             ['look','move cup 2 to cabinet 4'],[failed,opened]),
        case('subgoal_already_completed','put some cup in cabinet.','The cabinet 4 is open.',
             ['look','close cabinet 4'],[failed,opened,placed]),
        case('newly_held_object_differs','put some cup in cabinet.','The cabinet 4 is closed.',
             ['look','open cabinet 4'],[failed,dict(action='take book 2 from desk 1',
             observation='You pick up the book 2 from the desk 1.')]),
    ]


def freeze(source, v4, audit_v4, v5, diagnostic, output, *, mock):
    previous, _, selected, analyses, protocol, events, host, dev = import_v4(source,v4,audit_v4,output)
    old = read(v5/'result.json')
    diag = read(diagnostic/'plan.private.json')
    receipt = read(diagnostic/'summary.json')
    if (fingerprint(read(v5/'protocol.json')) != old['protocol_sha256']
            or old['result']['candidates'][0]['mechanism_id'] != fingerprint(selected)
            or fingerprint(diag) != receipt['plan_sha256']
            or dev['exposed_checkpoints'] != diag['sources']
            or [c['sequence'] for c in diag['sources']] != [33,40,88,72]):
        raise PermissionError('v5 evidence or diagnostic freeze changed')
    if any(sha(v5/name)!=digest for name,digest in diag['before'].items()):
        raise PermissionError('historical v5 result changed')
    negatives = [dict(c,group='original_11') for c in dev['negative_cases']]
    for pair in diag['negative_pairs']:
        context=pair['context']
        variants=dict(without_stale=dict(context,history=[]), with_stale=context,
                      later_look=dict(context,history=[*context['history'],
                           dict(action='look',observation=context['observation'])]))
        negatives.extend(dict(id=pair['name']+'_'+label,group='stale_pairs',expected='declined',context=ctx)
                         for label,ctx in variants.items())
    negatives.extend(dict(c,group='new_state_change') for c in added_negatives())
    payload=dict(mechanism=selected,analyses=[a for a in analyses if a['evidence_id'] in selected['evidence_ids']])
    # Record exact source inputs and code. Validation labels and diagnostic outputs
    # stay on the host and are absent from the provider payload.
    code=[Path(__file__).resolve(), ROOT/'scripts/run_alfworld_recovery_v5.py',
          ROOT/'scripts/run_alfworld_skill_acquisition.py', ROOT/'scripts/evaluate_alfworld_recovery_development.py',
          ROOT/'scripts/test_alfworld_recovery_v6.py',
          *[p for name in ('alfworld_','failure_evo','runtime') for p in (ROOT/'FlowEvo/src'/name).glob('*.py')]]
    plan=dict(scope='MOCK_B_V6' if mock else 'REAL_B_V6_SOURCE_ONLY',run_id=('mock:B:' if mock else 'real:B:')+output.name,
        version=VERSION,model=MODEL,max_calls=1,max_tokens=INPUT_LIMIT+4096,max_cost_microusd=90000,
        worker_calls=4*WINDOW+len(negatives),worker=previous['worker'],network_policy=previous['network_policy'],
        mechanism_sha256=fingerprint(selected),payload_sha256=fingerprint(payload),
        generation_requirements_sha256=fingerprint(REQUIREMENTS),source_protocol_sha256=fingerprint(protocol),
        source_evidence_sha256=fingerprint(events),v4_response_sha256=previous['v4_response_sha256'],
        v5_protocol_sha256=old['protocol_sha256'],diagnostic_sha256=fingerprint(diag),
        validation_sha256=fingerprint([dev['exposed_checkpoints'],negatives]),window=WINDOW,
        acceptance_threshold=dict(local_repairs=4, false_triggers=0, policy_errors=0),
        code_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(code))})
    return plan,payload,protocol,events,host,dev['exposed_checkpoints'],negatives


def review_post_failure(data, origin, checkpoint, card, runner):
    n = checkpoint['step']
    steps = origin['steps']
    if (origin['sequence']!=checkpoint['sequence'] or origin['receipt_sha256']!=checkpoint['source_receipt']
            or n!=origin['projected']['anchor'] or not 0<n<50):
        raise PermissionError('post-failure checkpoint drift')
    prefix=steps[:n]
    failed=prefix[-1]
    if failed['observation']!='Nothing happens.' or failed['won'] or failed['done']:
        raise PermissionError('no verified nonterminal failure at checkpoint')
    goal=origin['projected']['goal']
    actions=[]
    decisions=[]
    current=failed
    state={}
    env=StrictTrainEnv(data,max_steps=50)
    try:
        env.initialize(frozen_game_files=[str(verify_source_game(data,origin))])
        _reset(env,origin)
        _replay(env,prefix)
        for _ in range(min(WINDOW,50-n)):
            ctx=context_view(goal,current['observation'],current['commands'],prefix+actions,state)
            result=runner.run(card,ctx)
            decisions.append(result)
            if result['status']!='applied':
                break
            if result['action'] not in current['commands']:
                raise PermissionError('worker action is inadmissible')
            current=_step(env,result['action'])
            actions.append(current)
            state=result['state']
            if current['done'] or current['won']:
                break
    finally:
        env.close()
    # These expectations are derived after execution, solely for scoring.
    expected_open='open '+failed['action'].rsplit(' to ',1)[1]
    target_open=bool(actions and actions[0]['action']==expected_open)
    restore=bool(target_open and failed['action'] not in failed['commands']
                 and failed['action'] in actions[0]['commands'])
    placement=any(a['action']==failed['action'] and a['observation']!='Nothing happens.' for a in actions)
    return dict(sequence=checkpoint['sequence'],family=checkpoint['family'],failed_step=n,
        failure=failed,first_context_sha256=fingerprint(context_view(goal,failed['observation'],failed['commands'],prefix,{})),
        first_action=actions[0]['action'] if actions else None,trigger_observed=decisions[0]['status']=='applied',
        correct_target_open=target_open,local_repair=restore,original_placement_completed=placement,
        won=bool(actions and actions[-1]['won']),repeated_actions=len(actions)-len({a['action'] for a in actions}),
        policy_errors=sum(r['status']=='error' for r in decisions),decisions=decisions,alternative=actions,
        original_same_horizon=steps[n:n+len(actions)], original_outcome=steps[-1]['won'])


def matching_configuration(plan):
    return fingerprint({k:v for k,v in plan.items() if k not in ('scope','run_id')})


def expected_grant(plan):
    return dict(run_id=plan['run_id'],protocol_hash=fingerprint(plan),model=MODEL,protocol=plan['version'],
                max_cost_microusd=plan['max_cost_microusd'],paid_api_authorized=True)


def prepare(args, *, freeze_fn=freeze, mock_scope='MOCK_B_V6'):
    plan,*_=freeze_fn(*args.paths,mock=False)
    mock_plan=read(args.mock_run/'protocol.json')
    result=read(args.mock_run/'result.json')
    if (mock_plan['scope']!=mock_scope or matching_configuration(plan)!=matching_configuration(mock_plan)
            or result['protocol_sha256']!=fingerprint(mock_plan) or result['paid_requests']!=0
            or result['local_repairs']!=4 or not result['false_triggers']):
        raise PermissionError('current Mock regression evidence required')
    args.output.mkdir(mode=0o700,parents=True)
    save(args.output/'protocol.json',plan)
    save(args.output/'mock_acceptance.json',dict(configuration=matching_configuration(plan),
                                                 result_sha256=sha(args.mock_run/'result.json')))
    save(args.output/'authorization.template.json',dict(expected_grant(plan),paid_api_authorized=False))
    print(canonical(dict(status='READY_PENDING_EXPLICIT_AUTHORIZATION',protocol_sha256=fingerprint(plan),
                         max_model_calls=1,max_cost_usd=.09)))


def run(paths, *, authorization=None, sender=None, freeze_fn=freeze, requirements=REQUIREMENTS):
    plan,payload,protocol,events,host,checkpoints,negatives=freeze_fn(*paths,mock=sender is not None)
    if fingerprint(requirements)!=plan['generation_requirements_sha256']:
        raise PermissionError('frozen generation prompt changed')
    output=paths[-1]
    if sender is None and (authorization!=expected_grant(plan) or read(output/'protocol.json')!=plan
                           or read(output/'mock_acceptance.json')['configuration']!=matching_configuration(plan)):
        raise PermissionError('matching explicit recovery Pilot authorization required')
    output.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=output/'protocol.json'
        if path.exists() and read(path)!=plan:
            raise PermissionError('frozen recovery plan changed')
        save(path,plan)
        save(output/'validation.private.json',dict(checkpoints=checkpoints,negatives=negatives))
        backend=FrozenLinuxBackend(image=plan['worker']['image'],worker_script=plan['worker']['worker_script'])
        if backend.manifest()!=plan['worker']:
            raise PermissionError('worker changed')
        budget=create_accounts(output,plan)
        store=FailureEvidenceStore(output/'failures.jsonl')
        registry=FailureOperatorRegistry(output/'registry.jsonl',store)
        ids=import_source_events('B',events,host,output,store,plan['run_id'])
        generated=stage_request(output,'candidate_v6','generate',payload,None,budget,sender=sender,
            authorization=authorization,network_policy=None if sender is not None else plan['network_policy'],
            protocol=plan['version'],generation_requirements=requirements)
        if generated.get('parse_status'):
            candidate=dict(status='SOURCE_DELIVERY_REJECTED',reason=generated.get('contract_diagnostic'))
        elif static_check(generated['code'])['passed'] and _has_instance_literals(generated['code'],[host[e] for e in ids]):
            candidate=dict(status='INSTANCE_LITERAL_REJECTED')
        else:
            known={e['event_id']:e for e in store.visible(time.time(),plan['run_id'])}
            candidate=register_environment_candidate(output/'candidate_v6',generated,payload['mechanism'],
                list(ids.values()),known,plan['worker'],registry,engineering=sender is not None,
                protocol=plan['version'],baseline='alfworld-full-library-online')
        positives=[]
        negative=[]
        if candidate['status']=='SHADOW':
            card=FailureOperator.from_dict(candidate['card'])
            if not card.intact() or registry.state(card)['permission']!='shadow':
                raise PermissionError('invalid shadow candidate')
            runner=EnvironmentPolicyRunner(backend,output/'worker.jsonl',budget)
            for checkpoint in checkpoints:
                receipt=output/f"source_{checkpoint['sequence']}.json"
                if receipt.exists():
                    row=read(receipt)
                    if row['candidate_version']!=card.version:
                        raise PermissionError('source review version changed')
                else:
                    row=review_post_failure(protocol['data_root'],host[checkpoint['evidence_id']],checkpoint,card,runner)
                    row['candidate_version']=card.version
                    save(receipt,row)
                positives.append(row)
            for case in negatives:
                result=runner.run(card,case['context'])
                negative.append(dict(id=case['id'],group=case['group'],category=case.get('category'),
                                     actual=result))
        result=dict(generated_complete=int(not generated.get('parse_status')),
            static_rejected=int(candidate['status']=='STATIC_REJECTED'),
            shadow_registered=int(candidate['status']=='SHADOW'),
            worker_calls=budget.tool_calls,protocol_sha256=fingerprint(plan),candidate=candidate,positives=positives,negatives=negative,
            local_repairs=sum(x['local_repair'] for x in positives),wins=sum(x['won'] for x in positives),
            false_triggers=sum(x['actual']['status']=='applied' for x in negative),
            policy_errors=sum(x['policy_errors'] for x in positives)+sum(x['actual']['status']=='error' for x in negative),
            metrics=recovery_metrics(output,dict(candidates=[candidate]),mock=sender is not None),
            budget=budget.snapshot(),paid_requests=budget.calls if sender is None else 0,independent_games=0)
        result['development_pass']=(len(positives)==4 and len(negative)==len(negatives) and result['local_repairs']==4
                                    and result['false_triggers']==0 and result['policy_errors']==0)
        save(output/'result.json',result)
        return result


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
        run(args.paths,authorization=read(args.authorization))
