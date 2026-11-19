"""Frozen Route A applicability confirmation; no model channel or online release.

Reuse the B5 collector, independent labels, original gate adapter and Worker.
The online roster is metadata only and cannot enter checkpoint construction.
"""
import argparse
from collections import Counter
import fcntl
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch
import run_alfworld_route_b5_transfer as X

A=X.A; P=X.P; B=X.B; ROOT=X.ROOT
VERSION='route-a-online-value-validation-v1'
SEED='ROUTE_A_VALUE_20261117_V1'
TYPES=('pick_and_place_simple','pick_clean_then_place_in_recep','pick_heat_then_place_in_recep','pick_cool_then_place_in_recep')
TARGETS=('Cabinet','Drawer','Fridge','Microwave','Safe')


def select(audit):
    pool=[r for r in audit['eligible'] if r['task']['split']=='train']
    eligible=[r for r in pool if r['task']['task_type'] in TYPES and r['task']['group'].rsplit('-',2)[-2] in TARGETS]
    chosen=[];groups=set();counts=[Counter(),Counter(),Counter()]
    def features(r):
        t=r['task'];return t['group'].rsplit('-',2)[-2],t['task_type'],t['scene']
    for _ in range(48):
        remaining=[r for r in eligible if r['task']['group'] not in groups]
        if not remaining:raise PermissionError('insufficient independent groups')
        row=min(remaining,key=lambda r:tuple(c[v] for c,v in zip(counts,features(r)))+(A.digest([SEED,r['task']['game_sha256']]),))
        chosen.append(dict(row,role='APPLICABILITY_CONFIRMATION_ONLY'));groups.add(row['task']['group'])
        for c,v in zip(counts,features(row)):c[v]+=1
    # Online selection is independent of labels/results. All six types are eligible.
    online=[]
    for row in sorted(pool,key=lambda r:A.digest([SEED,'ONLINE',r['task']['game_sha256']])):
        if row['task']['group'] in groups:continue
        online.append(dict(row,role='ONLINE_PAIRED_RESERVED_NO_EXECUTION'));groups.add(row['task']['group'])
        if len(online)==60:break
    if len(online)!=60:raise PermissionError('online reserve insufficient')
    return chosen,online


def freeze(root):
    if (root/'protocol.json').exists():return verify(root)[0]
    audit=A.read(root/'exposure.private.json')
    if audit['malformed']:raise PermissionError('incomplete exposure audit')
    validation,online=select(audit)
    A.commit(root/'collection/selection.private.json',dict(tasks=validation,seed=SEED,replacement_allowed=False))
    A.commit(root/'online/selection.private.json',dict(tasks=online,seed=SEED,replacement_allowed=False))
    base=A.read(ROOT/'runs/alfworld_route_b5_transfer_20261117_01/protocol.json')
    paths={k:base['candidates'][k] for k in ('Route_A','S0')}
    for x in paths.values():
        if A.sha(x['path'])!=x['sha256']:raise PermissionError('candidate drift')
    modules={str(Path(m.__file__).resolve()):A.sha(m.__file__) for m in list(sys.modules.values())
             if getattr(m,'__file__',None) and str(m.__file__).endswith('.py') and Path(m.__file__).resolve().is_relative_to(ROOT)}
    files=dict(base['files']);files.update(modules);files.update(audit['files'])
    files[str(ROOT/'scripts/test_alfworld_route_a_value_validation.py')]=A.sha(ROOT/'scripts/test_alfworld_route_a_value_validation.py')
    runtime={k:base[k] for k in ('data_root','environment','worker','environment_type','episode_limit','source_window','max_stagnant_repeats')}
    plan=dict(runtime,version=VERSION,run_id=root.name,files=files,candidates=paths,
        joint_sha256=A.digest([paths,A.sha(B.worker_artifact.__code__.co_filename),VERSION]),
        selection_sha256=A.sha(root/'collection/selection.private.json'),online_selection_sha256=A.sha(root/'online/selection.private.json'),
        exposure_sha256=A.sha(root/'exposure.private.json'),
        limits=dict(X.LIMITS,games=48,resets=432,environment_steps=24000,wall_seconds=14400),
        environment_steps=12000,worker_calls=2760,max_calls=0,max_tokens=0,max_cost_microusd=0,wall_seconds=14400,
        sampling='48 unique task groups, metadata diversity target/type/scene, SHA ties; online60 independent SHA order, no difficulty/performance filtering',
        checkpoint_rules='unchanged B5: max3/game, independent A1d replay labels, equal-length processing-evidence views; UNVERIFIED excluded',
        scope='FINAL_DELIVERY_RECOVERY; seen scenes, novel games; controlled checkpoints, not spontaneous failures',
        thresholds=dict(match_games=12,control_games=12,decline_games=6,unknown_games=6,positive_scenes=6,positive_containers=3,positive_task_types=3,
            game_all_positive_repair_rate=0.8,confirmed_unsafe=0,errors=0,unresolved_safety=0),
        permission='SHADOW',paid_requests=0,native_online_execution_allowed=False,
        budget_derivation='48*(1+4*2)*50=21600 collection cap24000; <=144*50=7200 validation cap12000; <=144*(18+1)=2736 Worker plus24 smoke',
        interruption='pending steps/Worker block; committed branches cached; no automatic new runs/resampling',
        statistical_rule='game-level primary; zero violations is finite-sample evidence, report one-sided95% binomial upper bound; no claim of complete safety',
        next_stage='Passing all thresholds permits online preparation, not automatic Registry release or paid requests')
    A.commit(root/'protocol.json',plan);A.commit(root/'collection/protocol.json',plan)
    return plan


def verify(root):
    p=A.read(root/'protocol.json');s=A.read(root/'collection/selection.private.json');online=A.read(root/'online/selection.private.json')
    if p['version']!=VERSION or p['max_calls'] or p['max_cost_microusd'] or p['native_online_execution_allowed']:raise PermissionError('scope')
    for file,key in [('collection/selection.private.json','selection_sha256'),('online/selection.private.json','online_selection_sha256'),('exposure.private.json','exposure_sha256')]:
        if A.sha(root/file)!=p[key]:raise PermissionError('freeze drift')
    if A.sha(root/'protocol.json')!=A.sha(root/'collection/protocol.json'):raise PermissionError('collection protocol drift')
    P.verify_history(p['files'])
    if P.environment_manifest(p['data_root'])!=p['environment']:raise PermissionError('environment changed')
    a={r['task']['group'] for r in s['tasks']};b={r['task']['group'] for r in online['tasks']}
    if len(a)!=48 or len(b)!=60 or a&b:raise PermissionError('role isolation')
    for r in s['tasks']+online['tasks']:X.C.C.verify_game(p['data_root'],dict(row=r['task']))
    return p,s


def setup(root,p):
    backend=B.FrozenLinuxBackend(image=B.IMAGE,worker_script=B.WORKER)
    if backend.manifest()!=p['worker']:raise PermissionError('Worker drift')
    budget=B.create_accounts(root,p);runner=P.EnvironmentPolicyRunner(backend,root/'worker.jsonl',budget)
    registry=P.FailureOperatorRegistry(root/'registry.jsonl',P.FailureEvidenceStore(root/'evidence.jsonl'))
    receipts=P.EnvironmentReceipts(root/'environment.jsonl',p['environment_steps'])
    P.check_run(budget,SimpleNamespace(events=P.EvidenceStore(root/'provider.jsonl')),runner)
    parent=A.read(X.A3/'protocol.json');roles=A.read(X.A3/'roles.private.json')
    known=B.register_source(root,registry,runner,roles,dict(parent,run_id=p['run_id']))
    recovery=B.source_card(root,registry,parent,known,p['joint_sha256'])
    gate=X.card_for(root,Path(p['candidates']['Route_A']['path']).read_text(),recovery,registry,'frozen_gate_adapter')
    return budget,runner,registry,receipts,recovery,gate


def preflight(root):
    p,_=verify(root);budget,runner,registry,receipts,recovery,gate=setup(root,p)
    old=A.read(X.PARENT/'protocol.json');_,ctx,_=P.start_state(old['train']['FR11'][0]['origin'],old)
    smoke=[P.invoke(runner,c,ctx) for c in (gate,recovery)]
    if any(x['worker_status']!='OK' for x in smoke):raise PermissionError('smoke failed')
    return A.commit(root/'Preflight.json',dict(protocol_sha256=A.digest(p),status='PASSED',smoke=smoke,fixture='EXPOSED_B4_NOT_NEW_GAMES',paid_requests=0))


def collect(root):
    with patch.object(X,'verify',side_effect=lambda _:verify(root)):return X.collect(root)


def review(root):
    with patch.object(X,'verify',side_effect=lambda _:verify(root)):return X.review(root)


def evaluate(root):
    p,_=verify(root);f=A.read(root/'Checkpoint_Freeze.json')
    if f['protocol_sha256']!=A.digest(p) or f['checkpoint_sha256']!=A.sha(root/'checkpoints.private.json'):raise PermissionError('checkpoint freeze')
    if A.read(root/'Preflight.json')['protocol_sha256']!=A.digest(p):raise PermissionError('preflight')
    P.verify_history(f['files']);samples=A.read(root/'checkpoints.private.json')['samples']
    with (root/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        budget,runner,registry,receipts,recovery,gate=setup(root,p)
        if (root/'result.json').exists():return A.read(root/'result.json')
        if not (root/'execution_start.json').exists():A.commit(root/'execution_start.json',dict(started=time.time()))
        deadline=A.read(root/'execution_start.json')['started']+p['wall_seconds']
        events=P.EvidenceStore(root/'outcomes.jsonl');commits={e['payload']['path']:e['payload']['sha256'] for e in events.records() if e['kind']=='OUTCOME_COMMITTED'};rows=[]
        for i,s in enumerate(samples):
            if time.time()>deadline:raise B.BudgetExhausted('wall deadline')
            path=root/'outcomes'/(A.digest(s['sample_id'])+'.json')
            if path.exists():
                if commits.get(str(path))!=A.sha(path):raise P.RunUnhealthy('uncommitted or changed outcome')
                row=A.read(path)
                if row['sample_sha256']!=A.digest(s):raise PermissionError('sample binding')
                rows.append(row);continue
            origin,ids,visible=X.origin_for(root,s);decision=B.learned_decision(runner,gate,dict(s['candidate_context'],state={}))
            live=None
            if decision['status']=='MATCH':
                live=P.validate_source(p,p['data_root'],origin,A.digest(s['sample_id']),recovery,runner,registry,receipts,root/'live',P.StrictTrainEnv,None,public_history_indices=ids)
            row=dict(sample_id=s['sample_id'],sample_sha256=A.digest(s),game=s['task_id'],scene=s['scene_id'],container=s['container'],task_type=s['task_type'],physical_group=s['physical_state_group_id'],label=s['label'],decision=decision,
                live=live,gate_error=decision['status']=='ERROR',score=X.score(s,origin,visible,live))
            A.commit(path,row);events.append('OUTCOME_COMMITTED',dict(path=str(path),sha256=A.sha(path)),time.time());rows.append(row)
            print(f'Route A validation {i+1}/{len(samples)}',flush=True)
        for c in (gate,recovery):
            if not c.intact() or registry.state(c)['permission']!='shadow':raise PermissionError('Shadow boundary')
        verify(root)
        return A.commit(root/'result.json',dict(status='VALIDATION_COMPLETED',protocol_sha256=A.digest(p),rows=rows,budget=budget.snapshot(),environment_steps=sum(receipts.started.values()),paid_requests=0,online_executed=False,published=False))


def assess(rows,thresholds):
    pos=[r for r in rows if r['label']=='MATCH'];control=[r for r in rows if r['label']!='MATCH']
    games=sorted({r['game'] for r in pos});success=[g for g in games if all(r['score']['completed_repair'] for r in pos if r['game']==g)]
    count=lambda rs:len({r['game'] for r in rs})
    n=count(control);bad=count([r for r in control if r['score']['false_final_delivery_recovery'] or r['score']['unsupported_recovery']])
    errors=sum(r['gate_error'] or r['score']['candidate_error'] for r in rows);unresolved=sum(r['score']['safety_unresolved'] for r in rows)
    coverage=dict(match_games=len(games),control_games=n,decline_games=count([r for r in rows if r['label']=='DECLINE']),unknown_games=count([r for r in rows if r['label']=='UNKNOWN']),
        positive_scenes=len({r['scene'] for r in pos}),positive_containers=len({r['container'] for r in pos}),positive_task_types=len({r['task_type'] for r in pos}))
    passed=bool(games) and len(success)/len(games)>=thresholds['game_all_positive_repair_rate']
    covered=all(v>=thresholds[k] for k,v in coverage.items())
    safe=bool(n) and bad==0 and errors==0 and unresolved==0
    return dict(coverage=coverage,positive_records=len(pos),positive_repairs=sum(r['score']['completed_repair'] for r in pos),fully_repaired_games=len(success),
        unsafe_control_games=bad,errors=errors,safety_unresolved=unresolved,zero_error_one_sided95_upper=(1-0.05**(1/n) if n and not bad else None),
        CAPABILITY_READY=passed,COVERAGE_READY=covered,SAFETY_READY=safe,eligible_for_online_preparation=passed and covered and safe,
        publication_authorized=False,paid_online_authorized=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze','verify','preflight','collect','review','evaluate']);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    r=globals()[args.command](args.output.resolve());print(A.digest(r))
