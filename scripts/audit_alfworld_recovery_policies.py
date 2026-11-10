"""Read-only v3 candidate audit and independent-game metadata freeze, zero API."""
import argparse
from collections import Counter
from pathlib import Path

from alfworld_.failure_learning import EnvironmentPolicyRunner, context_view
from alfworld_.skill_acquisition import load_source, verify_source_game
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_registry import FailureOperator
from failure_evo.math_stream import read, save, sha
from run_alfworld_skill_acquisition import create_accounts
from run_alfworld_success_baseline import exposure
from run_math_v3_development import IMAGE, WORKER

# Exposed provenance identifies the two previously successful v3 candidates.
HISTORIC_PROTOCOL = 'b36b6f5662ec5e1ac4ea2e3db319a33d5f6fa21f32d6bc0ca89a97ab7bfd57ea'
SOURCE_CHECKS = {'safe': {33,54}, 'microwave': {72,86}}
EXPOSURE_KEYS = ('game_sha256','trajectory_sha256','group','scene')


def fixtures(loaded):
    def case(label, goal, obs, commands, expected=None, history=()):
        return dict(id=label, source='SYNTHETIC_PUBLIC_CONTEXT', expected=expected,
                    context=context_view(goal,obs,commands,history,{}))
    cases = [
        case('irrelevant_closed_safe','put some book on desk.','The safe 2 is closed.',
             ['look','open safe 2','go to desk 1']),
        case('irrelevant_open_safe','put some book on desk.','The safe 2 is open.',
             ['look','move book 1 to safe 2']),
        case('no_target_container','put some book on desk.','You arrive at desk 1.',
             ['look','inventory','examine desk 1']),
        case('microwave_is_tool_not_destination','heat some potato and put it in garbagecan.',
             'The microwave 2 is open.', ['heat potato 1 with microwave 2','move potato 1 to microwave 2']),
        case('wrong_safe_target','put the vase 7 in the safe 3.','The safe 2 is closed. The safe 3 is closed.',
             ['look','open safe 2']),
        case('ambiguous_microwave_target','put some apple in microwave.',
             'The microwave 2 is closed. The microwave 3 is closed.',
             ['look','open microwave 2','open microwave 3']),
        case('unseen_container_repair','put some cup in cabinet.','The cabinet 7 is closed.',
             ['look','open cabinet 7'], expected='open cabinet 7'),
    ]
    # Actual source prefixes only, from locked exposed episodes; no held-out game is started.
    for label, number in [('safe',33),('microwave',72),('drawer',40)]:
        origin = next(o for o in loaded.values() if o['sequence']==number)
        event = origin['projected']
        i = event['anchor']-1
        before = origin['steps'][i-1] if i else origin['initial']
        expected = origin['steps'][i+1]['action']
        cases.append(dict(id=f'exposed_{label}_{number}',source='EXPOSED_SOURCE_PREFIX',
            expected=expected,context=context_view(event['goal'],before['observation'],
                                                before['commands'],origin['steps'][:i],{})))
    return cases


def run(source, previous, pool_path, output):
    protocol,_,host = load_source(source)
    baseline = read(previous/'result.json')
    if (baseline['protocol_sha256']!=HISTORIC_PROTOCOL
            or fingerprint(read(previous/'protocol.json'))!=HISTORIC_PROTOCOL):
        raise PermissionError('expected frozen v3 run')
    registered = {r['payload']['card']['version']:r['payload']['card']
                  for r in EvidenceStore(previous/'registry.jsonl').records()
                  if r['kind']=='SHADOW_REGISTERED'}
    cards = {}
    for candidate in baseline['result']['candidates']:
        ids = {host[e['checkpoint']['evidence_id']]['sequence'] for e in candidate.get('checks',[])
               if e['episode_won']}
        for label,numbers in SOURCE_CHECKS.items():
            if ids==numbers:
                card = FailureOperator.from_dict(candidate['card'])
                if canonical(registered[card.version])!=canonical(card.to_dict()) or not card.intact():
                    raise PermissionError('frozen v3 artifact changed')
                cards[label]=card
    if set(cards)!=set(SOURCE_CHECKS):
        raise PermissionError('successful candidate set changed')
    pool = read(pool_path)
    rows = pool['candidate_pool']
    data = Path(protocol['data_root'])
    exposed, manifests = exposure(source.parent,data)
    if (pool['source_protocol_sha256']!=fingerprint(protocol)
            or pool['candidate_pool_sha256']!=fingerprint(rows)
            or len({r['game_sha256'] for r in rows})!=len(rows)
            or any({r[k] for r in rows}&{r[k] for r in exposed} for k in EXPOSURE_KEYS)):
        raise PermissionError('independent pool provenance changed or overlaps')
    for row in rows:
        game=(data/row['game']).resolve()
        if not game.is_relative_to(data.resolve()) or sha(game)!=row['game_sha256'] or sha(game.parent/'traj_data.json')!=row['trajectory_sha256']:
            raise PermissionError('independent pool artifacts changed')
    for origin in host.values():
        if origin['sequence'] in (33,72,40):
            verify_source_game(data,origin)
    backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
    cases=fixtures(host)
    output.mkdir(mode=0o700,parents=True)
    config=dict(run_id=output.name, scope='ZERO_API_NO_GATE_EXECUTION', max_calls=0, max_tokens=0,
        max_cost_microusd=0, worker_calls=len(cases)*len(cards), worker=backend.manifest(),
        candidates={k:c.to_dict() for k,c in cards.items()}, previous_result_sha256=sha(previous/'result.json'),
        audit_cases_sha256=fingerprint(cases), independent_pool_sha256=pool['candidate_pool_sha256'])
    save(output/'audit_freeze.private.json',config)
    runner=EnvironmentPolicyRunner(backend,output/'worker.jsonl',create_accounts(output,config))
    results=[]
    for label,card in cards.items():
        for case in cases:
            result=runner.run(card,case['context'])
            results.append(dict(candidate=label,case=case['id'],source=case['source'],
                expected=case['expected'],actual=result,correct=(
                    result.get('action')==case['expected'] and result['status']=='applied'
                    if case['expected'] else result['status']=='declined')))
    families=Counter(row['group'].rsplit('-',2)[-2] for row in rows)
    reasons=['ZERO_SAME_FAMILY_GOAL_DESTINATIONS','NEW_CONTAINER_POSITIVE_COVERAGE_INSUFFICIENT',
             'DEVELOPMENT_NEGATIVE_CHECKS_FAILED','NO_FROZEN_INDEPENDENT_CHECKPOINT_LABELS']
    # This freezes an independent-game protocol proposal, not a publication receipt.
    save(output/'independent_validation.private.json',dict(status='BLOCKED',reasons=reasons,
         source_protocol_sha256=fingerprint(protocol),candidate_versions={k:c.version for k,c in cards.items()},
         pool_sha256=pool['candidate_pool_sha256'],exposure_manifests=manifests,candidate_pool=rows,
         proposed_design=dict(min_positive_games=4,min_negative_games=4,min_scenes_per_role=2,
             require_distinct_task_groups=True,max_policy_actions=4,
             checkpoint_selection='freeze from public native prefix without seeing candidate output',
             same_checkpoint_arms=['native','frozen_candidate'],include_native_success_cases=True,
             roles=['same_family_unseen_scene','new_container_family','near_negative_wrong_target_or_phase'],
             fail_closed_on_unlabelled=True,
             score=['local_repair','won','decline','false_trigger','regression','steps','model_calls'])))
    summary=dict(results=results,paid_calls=0,independent_games_executed=0,gate_status='BLOCKED',
                 scenes=sorted({row['scene'] for row in rows}),goal_destination_counts=dict(families),
                 worker_calls=runner.budget.tool_calls,configuration_sha256=fingerprint(config))
    save(output/'summary.json',summary)
    print(canonical(summary))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','previous','pool','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    run(args.source,args.previous,args.pool,args.output)
