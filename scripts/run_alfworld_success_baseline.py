"""Freeze and execute a success-learning baseline under the existing ALFWorld ledger."""
import argparse
import fcntl
import importlib.metadata
import json
import random
from decimal import Decimal
from itertools import combinations
from pathlib import Path

from alfworld_.success_baseline import StrictTrainEnv, run_stream
from failure_evo.contracts import fingerprint
from failure_evo.math_stream import read, save, sha
from failure_evo.network_transport import DEFAULT_POLICY
from run_alfworld_audited_baseline import ROOT, TYPES, budget

VERSION = 'alfworld-audited-full-library-v3-online'
KIND = 'pick_two_obj_and_place'
PACKAGES = ('alfworld', 'textworld', 'numpy', 'PyYAML')
SETTINGS = dict(condition='full_library', model='deepseek-flash', thinking='disabled',
                temperature=0, input_upper=10000, output_tokens=1024, compiler_output_tokens=500,
                max_steps=50, network_policy=DEFAULT_POLICY, evaluation_holdout=False,
                reference_rates_per_million=dict(hit='0.003', miss='0.15', output='0.6'))


def game_row(path, data):
    path = path.resolve()
    trajectory = path.parent/'traj_data.json'
    metadata = read(trajectory)
    game = str(path.relative_to(data))
    scene = metadata['scene']['scene_num']
    if type(scene) is not int:
        raise ValueError('scene identity unavailable')
    return dict(task_id='alf-'+fingerprint(game)[:20], game=game, split=Path(game).parts[1],
                game_sha256=sha(path), trajectory_sha256=sha(trajectory),
                scene=scene, group=path.parent.parent.name, trial=path.parent.name,
                task_type=metadata['task_type'])


def exposure(history, data):
    manifests = sorted(p for directory in history.glob('alfworld*') if directory.is_dir()
                       for name in ('protocol.json', 'learning_protocol.json') for p in directory.rglob(name))
    if not manifests:
        raise ValueError('no historical ALFWorld exposure manifests')
    games = {}
    for path in manifests:
        protocol = read(path)
        rows = protocol.get('tasks', []) + protocol.get('future_tasks', [])
        rows += [r for shard in protocol.get('gate_shards', []) for r in shard]
        for row in rows:
            item = game_row(data/row['game'], data)
            if item['game_sha256'] != row['game_sha256'] or item['trajectory_sha256'] != row['trajectory_sha256']:
                raise PermissionError('historical dataset drift')
            games[item['game']] = item
    return list(games.values()), [dict(path=str(p), sha256=sha(p)) for p in manifests]


def sample(rows, *, online, evaluation, seed, purpose):
    rng = random.Random(seed)
    by_scene = {}
    for r in sorted(rows, key=lambda r:r['game']):
        by_scene.setdefault(r['scene'], []).append(r)
    scenes = sorted(by_scene)
    rng.shuffle(scenes)
    if purpose == 'calibration':
        # Use a compact set of calibration scenes so the formal cohort can
        # retain entirely different scenes. Tie breaks follow the seeded order.
        partitions = [(a,b,c) for a in scenes if len(by_scene[a]) >= online
                      for b,c in combinations([x for x in scenes if x != a],2)
                      if len(by_scene[b])+len(by_scene[c]) >= evaluation]
        if not partitions:
            raise ValueError('no three-scene calibration partition fits the declared counts')
        a,b,c = min(partitions,key=lambda group:sum(len(by_scene[x]) for x in group))
        return rng.sample(by_scene[a],online)+rng.sample(by_scene[b]+by_scene[c],evaluation), scenes, [b,c]
    if evaluation or len(rows) < online:
        raise ValueError('formal online sampling requires a single sufficient pool')
    tasks = rng.sample(sorted(rows, key=lambda r:r['game']), online)
    if {r['task_type'] for r in tasks} != set(TYPES):
        raise ValueError('frozen draw lacks a task type; no outcome-based redraw')
    return tasks, scenes, []


def freeze(root, data, history, *, purpose, seed, max_cost_usd):
    from alfworld.agents.environment import get_environment
    if root.exists():
        raise FileExistsError('new baseline Run required')
    data = data.resolve()
    history = history.resolve()
    online, evaluation = (120, 0) if purpose == 'formal' else (12, 4)
    old, manifests = exposure(history, data)
    if purpose == 'formal' and not any(read(Path(p['path'])).get('purpose') == 'calibration' for p in manifests):
        raise PermissionError('freeze a separate calibration plan first')
    used = {k:{r[k] for r in old} for k in ('game_sha256','trajectory_sha256','group','scene')}
    env = StrictTrainEnv(data)
    native = get_environment('AlfredTWEnv')(env._build_config(), train_eval='train')
    # Inventory is the exact native loader output with strict path validation.
    kinds = (KIND,) if purpose == 'calibration' else TYPES
    inventory = [game_row(Path(p), data) for p in sorted(native.game_files)
                 if purpose == 'formal' or '/'+KIND+'-' in p]
    if any(r['split'] != 'train' or r['task_type'] not in kinds for r in inventory):
        raise PermissionError('inventory contains mixed split or task type')
    eligible, exclusions, seen = [], [], {k:set() for k in ('game_sha256','trajectory_sha256')}
    for row in inventory:
        reasons = [k for k in used if row[k] in used[k]]
        reasons += ['duplicate_'+k for k in seen if row[k] in seen[k]]
        if reasons:
            exclusions.append(dict(game=row['game'], reasons=reasons))
        else:
            eligible.append(row)
            for k in seen:
                seen[k].add(row[k])
    tasks, scenes, heldout = sample(eligible, online=online, evaluation=evaluation, seed=seed, purpose=purpose)
    cost = Decimal(str(max_cost_usd))*1000000
    if not cost.is_finite() or cost <= 0 or cost != cost.to_integral_value():
        raise ValueError('positive cap with at most six decimal places required')
    sources = [Path(__file__), ROOT/'scripts/run_alfworld_audited_baseline.py',
               *[p for d in ('alfworld_', 'failure_evo', 'runtime') for p in (ROOT/'FlowEvo/src'/d).glob('*.py')]]
    selection = dict(method=('single-eligible-pool-seeded-uniform-v1' if purpose == 'formal'
                             else 'scene-reservation-then-game-sample-v3'), seed=seed, task_types=list(kinds),
                     inventory=inventory, exclusions=exclusions, eligible=[r['game'] for r in eligible],
                     shuffled_scenes=scenes, heldout_scenes=heldout, exposure_manifests=manifests)
    cfg = dict(SETTINGS, protocol=VERSION, purpose=purpose, run_id=root.name, online=online,
               episode_count=len(tasks), max_calls=50*len(tasks)+online, max_cost_microusd=int(cost),
               seed=seed, data_root=str(data), history_root=str(history), tasks=tasks,
               selection_sha256=fingerprint(selection), source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},
               environment_files={n:sha(data/n) for n in ('logic/alfred.pddl','logic/alfred.twl2')},
               packages={p:importlib.metadata.version(p) for p in PACKAGES})
    root.mkdir(mode=0o700, parents=True)
    save(root/'selection.json', selection)
    save(root/'protocol.json', cfg)
    return load(root)


def load(root):
    cfg = read(root/'protocol.json')
    selection = read(root/'selection.json')
    count = (120,120) if cfg['purpose']=='formal' else (12,16)
    tasks = cfg['tasks']
    if (cfg['protocol'] != VERSION or cfg['run_id'] != root.name
            or cfg['purpose'] not in ('calibration','formal')
            or any(cfg[k] != v for k,v in SETTINGS.items())
            or (cfg['online'],len(tasks)) != count or cfg['episode_count'] != len(tasks)
            or cfg['max_calls'] != 50*len(tasks)+cfg['online']
            or fingerprint(selection) != cfg['selection_sha256']):
        raise PermissionError('protocol drift')
    for k in ('task_id','game_sha256','trajectory_sha256'):
        if len({r[k] for r in tasks}) != len(tasks):
            raise PermissionError('duplicate frozen identity')
    data = Path(cfg['data_root'])
    kinds = (KIND,) if cfg['purpose'] == 'calibration' else TYPES
    if selection['task_types'] != list(kinds):
        raise PermissionError('task type sampling frame differs')
    for row in tasks:
        if (row['split'] != 'train' or row['task_type'] not in kinds
                or game_row(data/row['game'], data) != row):
            raise PermissionError('invalid or changed frozen game')
    for k in ('scene','group'):
        if {r[k] for r in tasks[:cfg['online']]} & {r[k] for r in tasks[cfg['online']:]}:
            raise PermissionError('online/evaluation provenance overlap')
    for name,digest in cfg['environment_files'].items():
        if sha(data/name) != digest:
            raise PermissionError('environment data drift')
    for name,digest in cfg['source_sha256'].items():
        if sha(ROOT/name) != digest:
            raise PermissionError('source drift: '+name)
    for name,version in cfg['packages'].items():
        if importlib.metadata.version(name) != version:
            raise PermissionError('dependency drift: '+name)
    _, manifests = exposure(Path(cfg['history_root']), data)
    # Scan only other manifests. The frozen plan itself is not prior exposure;
    # subsequent calibration/formal manifests must also be disjoint.
    own = str((root/'protocol.json').resolve())
    others = {entry['path']:entry['sha256'] for entry in manifests if entry['path']!=own}
    if any(others.get(m['path']) != m['sha256'] for m in selection['exposure_manifests']):
        raise PermissionError('exposure manifest missing or changed')
    reserved = {k:{r[k] for r in tasks} for k in ('game_sha256','trajectory_sha256','scene','group')}
    eligible = set(selection['eligible'])
    sampled, scenes, heldout = sample([r for r in selection['inventory'] if r['game'] in eligible],
                                     online=cfg['online'], evaluation=len(tasks)-cfg['online'], seed=cfg['seed'], purpose=cfg['purpose'])
    if (sampled, scenes, heldout) != (tasks, selection['shuffled_scenes'], selection['heldout_scenes']):
        raise PermissionError('frozen sample does not reproduce')
    for path in others:
        p = read(Path(path))
        rows = p.get('tasks', [])+p.get('future_tasks', [])+[r for sh in p.get('gate_shards', []) for r in sh]
        for r in rows:
            previous = game_row(data/r['game'], data)
            if any(previous[k] in values for k,values in reserved.items()):
                raise PermissionError('frozen tasks overlap another exposure manifest')
    return cfg


def expected_authorization(cfg):
    return dict(run_id=cfg['run_id'], purpose=cfg['purpose'], protocol_sha256=fingerprint(cfg),
                max_cost_microusd=cfg['max_cost_microusd'], paid_api_authorized=True)


def run(root, cfg, authorization, pause_after=None):
    if authorization is None or read(authorization) != expected_authorization(cfg):
        raise PermissionError('separate explicit matching authorization required')
    if cfg['purpose'] == 'formal':
        prior = [read(Path(m['path'])) for m in read(root/'selection.json')['exposure_manifests']]
        passed = False
        for p in prior:
            if p.get('protocol') != VERSION or p.get('purpose') != 'calibration':
                continue
            calibration = Path(cfg['history_root'])/p['run_id']
            path = calibration/'summary.json'
            if not path.is_file():
                continue
            summary = read(path)
            pause = calibration/'pause.json'
            if (summary['status'] == 'COMPLETED' and summary['protocol_sha256'] == fingerprint(p)
                    and summary['phases']['total']['uses']['L2_requests'] > 0 and pause.is_file()
                    and read(pause)['protocol_sha256'] == fingerprint(p)):
                passed = True
        if not passed:
            raise PermissionError('completed independent calibration with observed L2 delivery and pause required')
    if pause_after is not None and not 1 <= pause_after < len(cfg['tasks']):
        raise ValueError('pause boundary outside task sequence')
    with (root/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return run_stream(root, cfg, budget(root,cfg), pause_after=pause_after)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze','preflight','run'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--history-root', type=Path, default=Path.home()/'.local/share/flowevo')
    parser.add_argument('--data', type=Path)
    parser.add_argument('--purpose', choices=('formal','calibration'), default='calibration')
    parser.add_argument('--seed', type=int, default=20261109)
    parser.add_argument('--max-cost-usd', type=Decimal)
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--pause-after', type=int)
    args=parser.parse_args()
    if args.action=='freeze':
        if args.data is None or args.max_cost_usd is None:
            parser.error('freeze requires --data and --max-cost-usd')
        cfg=freeze(args.output,args.data,args.history_root,purpose=args.purpose,seed=args.seed,max_cost_usd=args.max_cost_usd)
    else:
        cfg=load(args.output)
    if args.action=='run':
        summary=run(args.output,cfg,args.authorization,pause_after=args.pause_after)
        print(json.dumps(summary['phases'],ensure_ascii=False))
    else:
        print(json.dumps(dict(status='FROZEN_AWAITING_AUTHORIZATION', tasks=len(cfg['tasks']),
                              online=cfg['online'], max_calls=cfg['max_calls'],
                              protocol_sha256=fingerprint(cfg), paid_requests=0)))
