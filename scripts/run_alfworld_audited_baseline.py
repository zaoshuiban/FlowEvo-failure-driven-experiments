"""Freeze and run an isolated ALFWorld baseline with a bounded episode count."""
import argparse
import dataclasses
from decimal import Decimal
import importlib.metadata
import json
import os
from pathlib import Path
import random
import time

from alfworld_.audited_baseline import AuditedActionClient, classify_trace, summarize
from alfworld_.env import AlfWorldEnv, _task_type_from_game_file
from alfworld_.executor import AlfWorldExecutor
from alfworld_.generator import AlfWorldGenerator
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, save, sha
from failure_evo.network_transport import DEFAULT_POLICY
from failure_evo.persistent_budget import PersistentBudget

ROOT = Path(__file__).resolve().parents[1]
TYPES = ('pick_and_place_simple','look_at_obj_in_light','pick_clean_then_place_in_recep',
         'pick_heat_then_place_in_recep','pick_cool_then_place_in_recep','pick_two_obj_and_place')


def select_games(inventory, data, *, limit, seed, excluded):
    if type(limit) is not int or not 1<=limit<=len(inventory):
        raise ValueError('invalid requested task count')
    eligible=[p for p in inventory if str(Path(p).relative_to(data)) not in excluded]
    if len(eligible)<limit:
        raise ValueError('insufficient unexposed games after exclusions')
    rng=random.Random(seed)
    if limit==12 and not excluded:
        selection=[]
        for kind in TYPES:
            candidates=sorted(p for p in eligible if _task_type_from_game_file(p)==kind)
            if len(candidates)<2:
                raise ValueError('insufficient official tasks')
            selection.extend(rng.sample(candidates,2))
        rng.shuffle(selection)
        return selection
    return rng.sample(sorted(eligible),limit)


def freeze(root, data, *, limit=12, seed=20261107, exclude_runs=(), max_cost_usd=8):
    if (root/'protocol.json').exists():
        raise FileExistsError('frozen protocol already exists')
    from alfworld.agents.environment import get_environment
    wrapper = AlfWorldEnv(alfworld_data=str(data))
    official = get_environment('AlfredTWEnv')(wrapper._build_config(),train_eval=wrapper.split)
    inventory = sorted(official.game_files)
    excluded=set()
    exclusion_manifests=[]
    for previous in exclude_runs:
        old=read(previous/'protocol.json')
        if old['split']!=wrapper.split:
            raise PermissionError('exclusion split mismatch')
        for row in old['tasks']:
            if sha(data/row['game'])!=row['game_sha256']:
                raise PermissionError('exclusion dataset mismatch')
            excluded.add(row['game'])
        exclusion_manifests.append(dict(run_id=old['run_id'],protocol_sha256=fingerprint(old)))
    selection=select_games(inventory,data,limit=limit,seed=seed,excluded=excluded)
    groups={kind:sum(_task_type_from_game_file(p)==kind for p in inventory) for kind in TYPES}
    cost=Decimal(str(max_cost_usd))*1000000
    if not cost.is_finite() or cost<=0 or cost!=cost.to_integral_value():
        raise ValueError('positive USD budget with at most six decimal places required')
    records = [dict(task_id='alf-'+fingerprint(str(Path(p).relative_to(data)))[:20],
                    game=str(Path(p).relative_to(data)),game_sha256=sha(p),
                    trajectory_sha256=sha(Path(p).parent/'traj_data.json'),
                    task_type=_task_type_from_game_file(p)) for p in selection]
    sources = [Path(__file__).relative_to(ROOT),
               *[p.relative_to(ROOT) for d in ('alfworld_','failure_evo','runtime')
                 for p in (ROOT/'FlowEvo/src'/d).glob('*.py')]]
    cfg = dict(protocol='alfworld-pure-dynamic-baseline-v2',run_id=root.name,condition='pure_dynamic',
               seed=seed,episode_count=limit,excluded_games=len(excluded),exclusion_manifests=exclusion_manifests,split='eval_out_of_distribution',max_steps=50,model='deepseek-flash',
               input_upper=10000,output_tokens=256,max_calls=limit*50,max_cost_microusd=int(cost),
               data_root=str(data.resolve()),inventory_sha256=fingerprint(
                   [str(Path(p).relative_to(data)) for p in inventory]),
               type_counts=groups,tasks=records,network_policy=DEFAULT_POLICY,
               source_sha256={str(p):sha(ROOT/p) for p in sources},
               packages={k:importlib.metadata.version(k) for k in ('alfworld','textworld','numpy','PyYAML')})
    root.mkdir(mode=0o700,parents=True,exist_ok=True)
    save(root/'protocol.json',cfg)
    print(json.dumps(dict(frozen=len(records),types=groups,protocol_sha256=fingerprint(cfg)),indent=2))


def load(root,continuation=None):
    cfg = read(root/'protocol.json')
    if (cfg['protocol'] not in ('alfworld-pure-dynamic-baseline-v1','alfworld-pure-dynamic-baseline-v2')
            or len(cfg['tasks'])!=cfg.get('episode_count',12)
            or len({r['task_id'] for r in cfg['tasks']})!=len(cfg['tasks'])
            or cfg['max_calls']!=len(cfg['tasks'])*cfg['max_steps']):
        raise PermissionError('protocol mismatch')
    if continuation is not None:
        from alfworld_.continuation import validate
        validate(root,ROOT,continuation,cfg)
    else:
        for p,h in cfg['source_sha256'].items():
            if sha(ROOT/p)!=h:
                raise PermissionError('source changed '+p)
    for k,v in cfg['packages'].items():
        if importlib.metadata.version(k)!=v:
            raise PermissionError('dependency drift')
    for row in cfg['tasks']:
        path=Path(cfg['data_root'])/row['game']
        if sha(path)!=row['game_sha256'] or sha(path.parent/'traj_data.json')!=row['trajectory_sha256']:
            raise PermissionError('game changed')
    return cfg


def budget(root,cfg,engineering=False):
    return PersistentBudget(root/'budget.jsonl',run_id=('engineering:' if engineering else '')+cfg['run_id'],
                            protocol_hash=fingerprint(cfg),max_calls=cfg['max_calls'],
                            max_tokens=cfg['max_calls']*(cfg['input_upper']+cfg['output_tokens']),max_tools=0,
                            max_cost_microusd=cfg['max_cost_microusd'],token_rate_microusd_per_million=1200000,
                            tool_cost_upper_microusd=0,max_tool_milliseconds=0,
                            tool_milliseconds_upper=1000,wall_seconds=7*86400)


def run(root,authorization,continuation=None):
    import fcntl
    cfg=load(root,continuation)
    expected=dict(run_id=cfg['run_id'],protocol_sha256=fingerprint(cfg),
                  max_cost_microusd=cfg['max_cost_microusd'],paid_api_authorized=True)
    if read(authorization)!=expected:
        raise PermissionError('matching independent ALFWorld authorization required')
    with (root/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        account=budget(root,cfg)
        client=AuditedActionClient(root,account,cfg)
        journal=EvidenceStore(root/'episodes.jsonl')
        client.health()
        if continuation is not None:
            overlay=read(continuation)
            value=dict(continuation_sha256=fingerprint(overlay),policy=overlay['policy'])
            prior=[r['payload'] for r in journal.records() if r['kind']=='CONTINUATION_APPLIED']
            if prior and prior!=[value]:
                raise PermissionError('conflicting continuation')
            if not prior:
                journal.append('CONTINUATION_APPLIED',value,time.time())
        completed=[r['payload'] for r in journal.records() if r['kind']=='EPISODE_LOCKED']
        if [e['task_id'] for e in completed]!=[r['task_id'] for r in cfg['tasks'][:len(completed)]]:
            raise PermissionError('completed episodes differ from frozen order')
        for row in cfg['tasks'][len(completed):]:
            if continuation is not None and (root/'STOP.json').exists():
                stopped=read(root/'STOP.json')
                if stopped['task_id']==row['task_id']:
                    from alfworld_.continuation import truncation_receipt
                    receipt=truncation_receipt(root,account,row['task_id'])
                    record=dict(stopped,isolation=receipt,continuation_sha256=fingerprint(read(continuation)))
                    journal.append('EPISODE_LOCKED',record,time.time())
                    completed.append(record)
                    save(root/'summary.json',summarize(completed,account))
                    print(json.dumps(dict(episode=len(completed),status='DELIVERY_TRUNCATED_ISOLATED',
                                          calls=account.snapshot()['calls'])),flush=True)
                    continue
            env=AlfWorldEnv(alfworld_data=cfg['data_root'],max_steps=cfg['max_steps'])
            started=time.monotonic()
            try:
                path=str(Path(cfg['data_root'])/row['game'])
                env.initialize(frozen_game_files=[path])
                task,obs,commands=env.reset()
                if task.game_file!=path:
                    raise PermissionError('environment reset differs from frozen task')
                task.task_id=row['task_id']
                client.begin(task.task_id)
                trace=AlfWorldExecutor(env,AlfWorldGenerator(client),max_steps=cfg['max_steps']).run(
                    task,obs,commands,planning_mode='pure_dynamic')
                client.health()
                status=classify_trace(trace)
                record=dict(task_id=task.task_id,task_type=row['task_type'],status=status,
                            elapsed_seconds=time.monotonic()-started,trace=dataclasses.asdict(trace))
                if status=='INFRASTRUCTURE_OR_DELIVERY_ERROR':
                    save(root/'STOP.json',record)
                    if continuation is None:
                        raise RuntimeError('episode blocked by infrastructure or delivery')
                    from alfworld_.continuation import truncation_receipt
                    receipt=truncation_receipt(root,account,row['task_id'])
                    record.update(isolation=receipt,continuation_sha256=fingerprint(read(continuation)))
                journal.append('EPISODE_LOCKED',record,time.time())
                completed.append(record)
                save(root/'summary.json',summarize(completed,account))
                print(json.dumps(dict(episode=len(completed),status=status,steps=trace.total_steps,
                                      calls=account.snapshot()['calls'])),flush=True)
            finally:
                env.close()
        save(root/'summary.json',summarize(completed,account))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['freeze','preflight','authorize','prepare-continuation','run'])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--data',type=Path)
    parser.add_argument('--authorization',type=Path)
    parser.add_argument('--continuation',type=Path)
    parser.add_argument('--limit',type=int,default=12)
    parser.add_argument('--seed',type=int,default=20261107)
    parser.add_argument('--exclude-run',type=Path,action='append',default=[])
    parser.add_argument('--max-cost-usd',type=Decimal)
    args=parser.parse_args()
    if args.action=='freeze':
        if not args.data:
            parser.error('freeze requires --data')
        freeze(args.output,args.data,limit=args.limit,seed=args.seed,exclude_runs=args.exclude_run,
               max_cost_usd=args.max_cost_usd if args.max_cost_usd is not None else 8)
    elif args.action=='prepare-continuation':
        from alfworld_.continuation import prepare
        cfg=read(args.output/'protocol.json')
        print(prepare(args.output,ROOT,budget(args.output,cfg)))
    elif args.action=='preflight':
        cfg=load(args.output,args.continuation)
        print(json.dumps(dict(status='READY_PENDING_MATCHING_AUTHORIZATION',tasks=len(cfg['tasks']),
                              protocol_sha256=fingerprint(cfg),max_calls=cfg['max_calls'],
                              max_cost_usd=cfg['max_cost_microusd']/1_000_000,paid_requests=0)))
    elif args.action=='authorize':
        cfg=load(args.output)
        if args.max_cost_usd is None or args.max_cost_usd*1_000_000!=cfg['max_cost_microusd']:
            parser.error('authorize requires --max-cost-usd equal to the frozen cap')
        expected=dict(run_id=cfg['run_id'],protocol_sha256=fingerprint(cfg),
                      max_cost_microusd=cfg['max_cost_microusd'],paid_api_authorized=True)
        destination=args.output/'authorization.json'
        if destination.exists() and read(destination)!=expected:
            raise PermissionError('existing authorization differs')
        if not destination.exists():
            save(destination,expected)
            destination.chmod(0o400)
        print('Authorization recorded; model requests have not started.')
    elif not args.authorization:
        parser.error('run requires --authorization')
    else:
        run(args.output,args.authorization,args.continuation)
