"""Prepare/execute the default-off failure-learning stream. Preparation sends no API."""
import argparse
from pathlib import Path
import random
import importlib.metadata
import json
import fcntl

from alfworld_.env import AlfWorldEnv,_task_type_from_game_file
from alfworld_.failure_learning import VERSION
from alfworld_.learning_stream import LearningStream
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read,save,sha
from failure_evo.network_transport import DEFAULT_POLICY
from failure_evo.model_api import configured_api_key
from run_alfworld_audited_baseline import TYPES
from run_math_v3_development import IMAGE,WORKER

ROOT=Path(__file__).resolve().parents[1]


def prepare(root,source,data,*,exclude_protocols=(),exclude_baselines=(),future_count=6):
    if future_count not in (6,20,120):
        raise ValueError('supported Pilot sizes are 6, 20 or 120')
    if root.exists():
        raise FileExistsError('new learning Run required')
    old=read(source/'protocol.json')
    audit=read(source/'READ_ONLY_FINAL_AUDIT.json')
    if (audit['request_tail_sha256']!=EvidenceStore(source/'requests.jsonl').records()[-1]['record_hash']
            or audit['episode_tail_sha256']!=EvidenceStore(source/'episodes.jsonl').records()[-1]['record_hash']
            or audit['budget_tail_sha256']!=EvidenceStore(source/'budget.jsonl').records()[-1]['record_hash']
            or audit['protocol_sha256']!=fingerprint(old) or audit['unknown_requests']!=0):
        raise PermissionError('historical source audit no longer matches')
    for row in old['tasks']:
        if sha(data/row['game'])!=row['game_sha256']:
            raise PermissionError('historical game changed')
    from alfworld.agents.environment import get_environment
    rng=random.Random(20261108)
    shards=[[],[]]
    future=[]
    used_hashes={row['game_sha256'] for row in old['tasks']}
    exposure_manifests=[]
    excluded_baseline_manifests=[]
    for baseline in exclude_baselines:
        previous=read(baseline/'protocol.json')
        for row in previous['tasks']:
            if sha(data/row['game'])!=row['game_sha256']:
                raise PermissionError('baseline exclusion data changed')
            used_hashes.add(row['game_sha256'])
        excluded_baseline_manifests.append(fingerprint(previous))
    for path in exclude_protocols:
        previous=read(path)
        used_hashes.update(r['game_sha256'] for shard in previous['gate_shards'] for r in shard)
        used_hashes.update(r['game_sha256'] for r in previous['future_tasks'])
        exposure_manifests.append(fingerprint(previous))
    def record(path,prefix):
        p=Path(path)
        return dict(task_id=prefix+'-'+fingerprint(str(p.relative_to(data)))[:20],game=str(p.relative_to(data)),split=split,
                    game_sha256=sha(p),trajectory_sha256=sha(p.parent/'traj_data.json'),
                    task_type=_task_type_from_game_file(str(p)))
    for split,prefix in (('eval_in_distribution','gate'),('train','future')):
        env=AlfWorldEnv(split=split,alfworld_data=str(data))
        native=get_environment('AlfredTWEnv')(env._build_config(),train_eval=split)
        for type_index,kind in enumerate(TYPES):
            options=sorted(p for p in native.game_files if _task_type_from_game_file(p)==kind)
            rng.shuffle(options)
            chosen=[]
            per_type,remainder=divmod(future_count,len(TYPES))
            needed=2 if prefix=='gate' else per_type+int(type_index<remainder)
            for option in options:
                digest=sha(option)
                if digest not in used_hashes:
                    chosen.append(option)
                    used_hashes.add(digest)
                if len(chosen)==needed:
                    break
            if len(chosen)!=needed:
                raise PermissionError('insufficient game-content-disjoint validation material')
            if prefix=='gate':
                for i,p in enumerate(chosen):
                    shards[i].append(record(p,'gate'))
            else:
                future.extend(record(p,'future') for p in chosen)
    rng.shuffle(future)
    roles=[set(r['game_sha256'] for r in old['tasks']),
           set(r['game_sha256'] for shard in shards for r in shard),set(r['game_sha256'] for r in future)]
    if any(roles[i]&roles[j] for i in range(3) for j in range(i)):
        raise PermissionError('source/Gate/future game collision')
    backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
    code=[Path(__file__).relative_to(ROOT),
          Path('scripts/run_alfworld_audited_baseline.py'),Path('scripts/run_math_v3_development.py'),
          *[p.relative_to(ROOT) for d in ('alfworld_','failure_evo','runtime')
            for p in (ROOT/'FlowEvo/src'/d).glob('*.py')]]
    plan=dict(version=VERSION,run_id=root.name,source_run=str(source.resolve()),data_root=str(data.resolve()),
              model='deepseek-flash',action_calls=1400+100*future_count,input_upper=10000,output_tokens=1024,
              max_candidates=2,worker_calls=2000,max_cost_microusd=80_000_000 if future_count==120 else 30_000_000,
              source_rows={r['task_id']:r for r in old['tasks']+future},gate_shards=shards,future_tasks=future,
              source_hashes={name:sha(source/name) for name in ('protocol.json','requests.jsonl','episodes.jsonl',
                            'budget.jsonl','READ_ONLY_FINAL_AUDIT.json')},
              network_policy=DEFAULT_POLICY,worker=backend.manifest(),worker_script=str(WORKER.relative_to(ROOT)),
              source_code_sha256={str(p):sha(ROOT/p) for p in code},
              packages={k:importlib.metadata.version(k) for k in ('alfworld','textworld','numpy','PyYAML')},
              scope='DEVELOPMENT_GAME_ID_DISJOINT_NOT_UNSEEN_SCENE_CLAIM',excluded_preparation_manifests=exposure_manifests,excluded_baseline_manifests=excluded_baseline_manifests)
    root.mkdir(mode=0o700,parents=True)
    save(root/'learning_protocol.json',plan)
    print(json.dumps(dict(prepared=True,trusted_source_failures=20,gate_tasks=12,future_tasks=future_count,
                          model_request_cap=1404+100*future_count,max_cost_usd=plan['max_cost_microusd']/1000000,paid_requests=0),indent=2))


def load(root):
    plan=read(root/'learning_protocol.json')
    if (plan['version']!=VERSION or plan['max_candidates']!=2 or plan['max_cost_microusd']!=(80_000_000 if len(plan['future_tasks'])==120 else 30_000_000)
            or len(plan['future_tasks']) not in (6,20,120)
            or plan['action_calls']!=1400+100*len(plan['future_tasks']) or plan['output_tokens']!=1024):
        raise PermissionError('learning protocol differs')
    for name,digest in plan['source_code_sha256'].items():
        if sha(ROOT/name)!=digest:
            raise PermissionError('learning source changed: '+name)
    for name,digest in plan['source_hashes'].items():
        if sha(Path(plan['source_run'])/name)!=digest:
            raise PermissionError('historical evidence changed')
    for row in list(plan['source_rows'].values())+[r for g in plan['gate_shards'] for r in g]:
        p=Path(plan['data_root'])/row['game']
        if sha(p)!=row['game_sha256'] or sha(p.parent/'traj_data.json')!=row['trajectory_sha256']:
            raise PermissionError('frozen game changed')
    for k,v in plan['packages'].items():
        if importlib.metadata.version(k)!=v:
            raise PermissionError('environment dependency changed')
    source_protocol=read(Path(plan['source_run'])/'protocol.json')
    source_ids={row['game_sha256'] for row in source_protocol['tasks']}
    gate_ids=[r['game_sha256'] for group in plan['gate_shards'] for r in group]
    future_ids=[r['game_sha256'] for r in plan['future_tasks']]
    if (len(gate_ids)!=12 or len(set(gate_ids))!=12 or len(future_ids) not in (6,20,120) or len(set(future_ids))!=len(future_ids)
            or set(gate_ids)&source_ids or set(future_ids)&source_ids or set(gate_ids)&set(future_ids)):
        raise PermissionError('frozen learning roles overlap')
    backend=FrozenLinuxBackend(image=plan['worker']['image'],worker_script=ROOT/plan['worker_script'])
    if backend.manifest()!=plan['worker']:
        raise PermissionError('Worker changed')
    return plan,backend


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','preflight','authorize','run'])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--data',type=Path)
    parser.add_argument('--authorization',type=Path)
    parser.add_argument('--exclude-protocol',type=Path,action='append',default=[])
    parser.add_argument('--exclude-baseline-run',type=Path,action='append',default=[])
    parser.add_argument('--future-tasks',type=int,choices=[6,20,120],default=6)
    args=parser.parse_args()
    if args.action=='prepare':
        if not args.source or not args.data:
            parser.error('prepare requires frozen source Run and official data')
        prepare(args.output,args.source,args.data,exclude_protocols=args.exclude_protocol,exclude_baselines=args.exclude_baseline_run,future_count=args.future_tasks)
    elif args.action=='preflight':
        plan,backend=load(args.output)
        path=args.output/'ENGINEERING_ACCEPTANCE.json'
        accepted=path.exists() and read(path).get('protocol_sha256')==fingerprint(plan) and read(path).get('passed') is True
        ready=accepted and bool(configured_api_key())
        print(json.dumps(dict(status='READY_PENDING_NEW_AUTHORIZATION' if ready else 'PREPARED_PENDING_ENGINEERING_ACCEPTANCE',
                              protocol_sha256=fingerprint(plan),credential_configured=bool(configured_api_key()),
                              paid_requests=0)))
    else:
        plan,backend=load(args.output)
        expected=dict(run_id=plan['run_id'],protocol_sha256=fingerprint(plan),
                      max_cost_microusd=plan['max_cost_microusd'],paid_api_authorized=True)
        if args.action=='authorize':
            acceptance=read(args.output/'ENGINEERING_ACCEPTANCE.json')
            if acceptance.get('protocol_sha256')!=fingerprint(plan) or acceptance.get('passed') is not True:
                raise PermissionError('engineering acceptance required before authorization')
            target=args.output/'authorization.json'
            if target.exists() and read(target)!=expected:
                raise PermissionError('existing authorization differs')
            save(target,expected)
            print('Authorization recorded; no model requests sent. Hard cap USD '+str(plan['max_cost_microusd']/1000000))
            raise SystemExit(0)
        if not args.authorization or read(args.authorization)!=expected:
            raise PermissionError('new independent ALFWorld learning authorization required')
        if not (args.output/'ENGINEERING_ACCEPTANCE.json').exists():
            raise PermissionError('engineering acceptance required')
        acceptance=read(args.output/'ENGINEERING_ACCEPTANCE.json')
        if acceptance.get('protocol_sha256')!=fingerprint(plan) or acceptance.get('passed') is not True:
            raise PermissionError('acceptance is not bound to this protocol')
        with (args.output/'run.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            stream=LearningStream(args.output/'run',plan,backend)
            stream.run()
            print(json.dumps(stream.report(),indent=2))
