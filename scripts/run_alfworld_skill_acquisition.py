"""Source-only ALFWorld acquisition acceptance and isolated Gate inventory, zero paid API."""
import argparse
from collections import Counter
import fcntl
import importlib.metadata
import json
from pathlib import Path
import random

from alfworld_.failure_learning import EnvironmentPolicyRunner
from alfworld_.skill_acquisition import (
    AcquisitionAdapter, EXTENDED_WINDOW, INPUT_LIMIT, LOCAL_WINDOW, MODEL, VERSION, acquire, load_source,
    replay_source, review_source,
)
from alfworld_.recovery_acquisition import (
    BATCH_SIZE, MAX_CANDIDATES, MAX_CHECKPOINTS, MIN_GROUNDED_HYPOTHESES, VERSION as RECOVERY_VERSION,
    acquire_recoveries, recovery_metrics,
)
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.contracts import canonical, fingerprint
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.math_stream import read, save, sha
from failure_evo.network_transport import DEFAULT_POLICY
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.run_health import assert_run_healthy
from run_alfworld_success_baseline import exposure, game_row
from run_math_v3_development import IMAGE, WORKER

ROOT = Path(__file__).resolve().parents[1]
MAX_CALLS = 4
WORKER_CALLS = 24
MAX_COST_MICROUSD = 350000
MAX_TOKENS = MAX_CALLS * (INPUT_LIMIT + 4096)
GATE_KEYS = ('game_sha256', 'trajectory_sha256', 'group', 'scene')


def inventory(source, history, output):
    """Separate process and output tree, metadata only. Never boot Gate games."""
    protocol = read(source/'protocol.json')
    data = Path(protocol['data_root'])
    prior, manifests = exposure(history, data)
    for row in protocol['tasks']:
        if not any(p['game_sha256'] == row['game_sha256'] for p in prior):
            raise PermissionError('source missing from exposure inventory')
    used = {key:{row[key] for row in prior} for key in GATE_KEYS}
    candidate = []
    for split in ('train','valid_seen','valid_unseen'):
        for path in sorted((data/'json_2.1.1'/split).glob('*/*/game.tw-pddl')):
            row = game_row(path, data)
            if all(row[key] not in used[key] for key in GATE_KEYS):
                candidate.append(row)
    seed = 20261109
    random.Random(seed).shuffle(candidate)
    if any(row[key] in used[key] for row in candidate for key in GATE_KEYS):
        raise PermissionError('Gate overlaps known exposure')
    output.mkdir(mode=0o700, parents=True)
    plan = dict(status='METADATA_ONLY_NOT_GATE_READY', seed=seed, source_protocol_sha256=fingerprint(protocol),
                exposure_manifests=manifests, known_exposed_games=len(prior), candidate_pool=candidate,
                support_labels='UNAVAILABLE_UNTIL_POLICY_FREEZE', candidate_pool_sha256=fingerprint(candidate))
    save(output/'candidate_pool.private.json', plan)
    summary = dict(status=plan['status'], games=len(candidate), scenes=len({r['scene'] for r in candidate}),
                   splits=dict(Counter(r['split'] for r in candidate)),
                   types=dict(Counter(r['task_type'] for r in candidate)),
                   exposure_manifests=len(manifests), known_exposed_games=len(prior),
                   candidate_pool_sha256=plan['candidate_pool_sha256'], games_executed=0)
    save(output/'inventory_summary.json', summary)
    print(canonical(summary))


RECOVERY_LIMITS = dict(max_calls=7, max_tokens=7*(INPUT_LIMIT+4096), max_cost_microusd=600000,
                       worker_calls=MAX_CANDIDATES*MAX_CHECKPOINTS*EXTENDED_WINDOW)


def create_accounts(output, plan):
    calls = plan.get('max_calls', MAX_CALLS)
    tokens = plan.get('max_tokens', MAX_TOKENS)
    cost = plan.get('max_cost_microusd', MAX_COST_MICROUSD)
    tools = plan.get('worker_calls', WORKER_CALLS)
    return PersistentBudget(output/'budget.jsonl', run_id=plan['run_id'], protocol_hash=fingerprint(plan),
        max_calls=calls, max_tokens=tokens, max_tools=tools, max_cost_microusd=cost,
        token_rate_microusd_per_million=1200000, tool_cost_upper_microusd=0,
        max_tool_milliseconds=tools*15000, tool_milliseconds_upper=15000, wall_seconds=86400)


def acceptance(source, output, sender):
    protocol, arms, host = load_source(source)
    backend = FrozenLinuxBackend(image=IMAGE, worker_script=WORKER)
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    code = [Path(__file__), ROOT/'scripts/test_alfworld_skill_acquisition.py',
            *[p for directory in ('alfworld_', 'failure_evo', 'runtime')
              for p in (ROOT/'FlowEvo/src'/directory).glob('*.py')]]
    plan = dict(scope='MOCK_ENGINEERING_SOURCE_ONLY', run_id='mock:'+output.resolve().name, version=VERSION,
                source_protocol_sha256=fingerprint(protocol), input_sha256=fingerprint(arms),
                source_commit_sha256=sha(source/'episodes.jsonl'), worker=backend.manifest(),
                code_sha256={str(p.resolve().relative_to(ROOT)):sha(p) for p in sorted(code)},
                packages={k:importlib.metadata.version(k) for k in ('alfworld','textworld','numpy','PyYAML')},
                model=MODEL, max_calls=MAX_CALLS, max_tokens=MAX_TOKENS, max_cost_microusd=MAX_COST_MICROUSD,
                worker_calls=WORKER_CALLS)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'protocol.json').exists() and read(output/'protocol.json') != plan:
            raise PermissionError('acceptance protocol drift')
        save(output/'protocol.json', plan)
        save(output/'projected.private.json', arms)
        budget = create_accounts(output, plan)
        provider = AcquisitionAdapter(output/'provider.jsonl', budget, model=MODEL,
                                      mock=True, sender=sender, max_wire_input_upper=INPUT_LIMIT,
                                      evidence_sha256={arm:fingerprint(events) for arm, events in arms.items()})
        compiler = BoundedCompiler(provider, budget, output/'compiler.jsonl', MODEL, max_input_upper=INPUT_LIMIT)
        runner = EnvironmentPolicyRunner(backend, output/'worker.jsonl', budget)
        assert_run_healthy(budgets=[budget], providers=[provider])
        if not (output/'source_replay.json').exists():
            for origin in host.values():
                replay_source(protocol['data_root'], origin)
            save(output/'source_replay.json', dict(episodes=len(host), steps=sum(len(o['steps']) for o in host.values()),
                                                  input_sha256=plan['input_sha256']))
        results = {}
        for arm, events in arms.items():
            directory = output/arm
            store = FailureEvidenceStore(directory/'failures.jsonl')
            registry = FailureOperatorRegistry(directory/'registry.jsonl', store)
            result = acquire(arm, events, host, directory, compiler, registry, backend.manifest())
            if result['status'] == 'SHADOW':
                card = FailureOperator.from_dict(result['card'])
                proposal = read(directory/'hypothesis.json')
                result['checks'] = [review_source(protocol['data_root'], host[ref['evidence_id']], ref, card,
                    runner, registry, directory/f'review_{i}.json') for i, ref in enumerate(proposal['checkpoints'])]
                assert registry.state(card)['permission'] == 'shadow'
            results[arm] = result
        save(output/'acceptance.json', dict(scope=plan['scope'], paid_requests=0,
             protocol_sha256=fingerprint(plan), source_replay=read(output/'source_replay.json'), arms=results))
        return results


def recovery_plan(source, output, *, mock):
    protocol, arms, host = load_source(source)
    events = arms['B']
    backend = FrozenLinuxBackend(image=IMAGE, worker_script=WORKER)
    code = [Path(__file__), ROOT/'scripts/test_alfworld_recovery_acquisition.py',
            *[p for directory in ('alfworld_', 'failure_evo', 'runtime')
              for p in (ROOT/'FlowEvo/src'/directory).glob('*.py')]]
    plan = dict(scope='MOCK_B_SOURCE_ONLY' if mock else 'REAL_B_SOURCE_ONLY',
                run_id=('mock:B:' if mock else 'real:B:')+output.resolve().name, version=RECOVERY_VERSION,
                source_protocol_sha256=fingerprint(protocol), input_sha256=fingerprint(events),
                source_commit_sha256=sha(source/'episodes.jsonl'), worker=backend.manifest(), model=MODEL,
                network_policy=DEFAULT_POLICY, output_tokens=4096, input_upper=INPUT_LIMIT,
                reasoning='disabled',temperature=0,batch_size=BATCH_SIZE,candidate_cap=MAX_CANDIDATES,
                reference_scheme='episode-prefix12:step_NNN',min_grounded_hypotheses=MIN_GROUNDED_HYPOTHESES,
                checkpoints_per_candidate=MAX_CHECKPOINTS,local_window=LOCAL_WINDOW,extended_window=EXTENDED_WINDOW,
                cost_estimate_per_million_usd={'input':.30,'output':1.20},
                code_sha256={str(p.resolve().relative_to(ROOT)):sha(p) for p in sorted(code)},
                packages={k:importlib.metadata.version(k) for k in ('alfworld','textworld','numpy','PyYAML')},
                **RECOVERY_LIMITS)
    return plan,events,host,backend,protocol['data_root']


def recovery_execution(source, output, *, sender=None, authorization=None):
    mock = sender is not None
    plan,events,host,backend,data = recovery_plan(source,output,mock=mock)
    if not mock:
        grant = dict(run_id=plan['run_id'], protocol_hash=fingerprint(plan), model=MODEL,
                     protocol=RECOVERY_VERSION, max_cost_microusd=plan['max_cost_microusd'],
                     paid_api_authorized=True)
        if authorization != grant or read(output/'protocol.json') != plan:
            raise PermissionError('new explicit authorization and unchanged frozen protocol required')
        proof = read(output/'mock_acceptance.json')
        if proof['configuration_sha256'] != recovery_configuration(plan):
            raise PermissionError('zero-API acceptance does not cover this configuration')
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'protocol.json').exists() and read(output/'protocol.json') != plan:
            raise PermissionError('recovery protocol drift')
        if mock:
            save(output/'protocol.json', plan)
        budget = create_accounts(output, plan)
        store = FailureEvidenceStore(output/'failures.jsonl')
        registry = FailureOperatorRegistry(output/'registry.jsonl',store)
        runner = EnvironmentPolicyRunner(backend,output/'worker.jsonl',budget)
        result = {}
        try:
            result = acquire_recoveries(events,host,output,budget,registry,runner,data,sender=sender,
                       authorization=authorization,network_policy=None if mock else plan['network_policy'])
        except Exception as exc:
            save(output/'interrupted.json',dict(error=type(exc).__name__,budget=budget.snapshot(),
                 metrics=recovery_metrics(output,result,mock=mock)))
            raise
        save(output/'acceptance.json' if mock else output/'result.json',dict(scope=plan['scope'],
             protocol_sha256=fingerprint(plan),result=result,budget=budget.snapshot(),
             metrics=recovery_metrics(output,result,mock=mock),paid_requests=0 if mock else budget.calls))
        return result


def recovery_acceptance(source, output, sender):
    if sender is None:
        raise ValueError('zero-API acceptance requires an explicit fixture')
    return recovery_execution(source,output,sender=sender)


def recovery_configuration(plan):
    return fingerprint({k:v for k,v in plan.items() if k not in ('run_id','scope')})


def prepare_recovery(source, output, mock_run):
    plan,*_ = recovery_plan(source,output,mock=False)
    mock_plan = read(mock_run/'protocol.json')
    acceptance = read(mock_run/'acceptance.json')
    if (mock_plan['scope']!='MOCK_B_SOURCE_ONLY' or acceptance['paid_requests']!=0
            or acceptance['protocol_sha256']!=fingerprint(mock_plan)
            or acceptance['result']['status']!='SOURCE_ONLY_COMPLETE'
            or acceptance['result']['evidence']!=16
            or acceptance['result']['grounded_hypotheses']<MIN_GROUNDED_HYPOTHESES
            or acceptance['result']['rejected_evidence']<1
            or acceptance['metrics']['local_repairs']<1
            or recovery_configuration(mock_plan)!=recovery_configuration(plan)):
        raise PermissionError('current zero-API source evidence required')
    output.mkdir(mode=0o700,parents=True)
    save(output/'protocol.json',plan)
    save(output/'mock_acceptance.json',dict(configuration_sha256=recovery_configuration(plan),
                                            acceptance_sha256=sha(mock_run/'acceptance.json')))
    save(output/'authorization.template.json',dict(run_id=plan['run_id'],protocol_hash=fingerprint(plan),
        model=MODEL,protocol=RECOVERY_VERSION,max_cost_microusd=plan['max_cost_microusd'],paid_api_authorized=False))
    print(canonical(dict(status='READY_PENDING_EXPLICIT_AUTHORIZATION',protocol_hash=fingerprint(plan),
                         paid_requests=0,**RECOVERY_LIMITS)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['mock', 'mock-recovery', 'prepare-recovery', 'run-recovery', 'gate-inventory'])
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--history', type=Path)
    parser.add_argument('--mock-run', type=Path)
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args()
    if args.action == 'mock':
        from test_alfworld_skill_acquisition import fixture_sender
        results = acceptance(args.source, args.output, fixture_sender)
        print(json.dumps({arm:dict(status=result['status'], checks=[r['status'] for r in result.get('checks', [])])
                          for arm, result in results.items()}))
    elif args.action == 'mock-recovery':
        from test_alfworld_recovery_acquisition import fixture_sender
        result = recovery_acceptance(args.source,args.output,fixture_sender)
        print(canonical(dict(status=result['status'],localized=result['localized'],
                             mechanisms=result.get('mechanisms'),paid_requests=0)))
    elif args.action == 'prepare-recovery':
        if args.mock_run is None:
            parser.error('prepare-recovery requires --mock-run')
        prepare_recovery(args.source,args.output,args.mock_run)
    elif args.action == 'run-recovery':
        if args.authorization is None:
            parser.error('run-recovery requires --authorization')
        recovery_execution(args.source,args.output,authorization=read(args.authorization))
    else:
        if args.history is None:
            parser.error('gate-inventory requires --history')
        inventory(args.source, args.history, args.output)
