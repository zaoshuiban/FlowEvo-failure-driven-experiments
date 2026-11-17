"""A1d validation-only controlled collection. No model calls or test-pool execution."""
import argparse
from collections import Counter
import fcntl
from pathlib import Path
import random
import time
import prepare_alfworld_route_a_expanded as previous
from prepare_alfworld_route_a_expanded import (ROOT,BASE,TYPES,TARGETS,inventory,commit,read,sha,
    fingerprint,canonical,EvidenceStore,EnvironmentReceipts,StrictTrainEnv,verify_source_game,
    environment_manifest,goal_parts,command,entity,compatible,receipt_effect,context,matched_views,model_projection)
from alfworld_.route_a_expanded_labels import review as inherited_review
from alfworld_.recovery_applicability_learning import validate_rows,load_dataset
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted

A1C=ROOT/'runs/alfworld_route_a_a1c_20261113_01'
VERSION='route-a-a1d-validation-v1'
LIMITS=dict(games=16,max_target_visits=4,episode_steps=50,environment_steps=12000,
            resets=160,wall_seconds=10800,modes=['READY','TARGET_CONFLICT','UNPROCESSED','OTHER_INSTANCE'])


def freeze(output):
    if output.exists():raise FileExistsError('new run required')
    found=inventory(BASE);blocked=set()
    for root in (A1C,ROOT/'runs/alfworld_route_a_a1b_collection_20261113_01'):
        path=root/'selection.private.json';found['files'][str(path)]=sha(path)
        blocked.update(r['task']['scene'] for r in read(path)['tasks'] if r['role']=='TRAIN')
    pool=sorted((r for r in found['eligible'] if r['scene'] not in blocked and r['task_type'] in TYPES
        and r['group'].rsplit('-',2)[-2] in TARGETS),key=lambda r:r['game'])
    random.Random(2026111304).shuffle(pool);selected=[];groups=set();kinds=Counter();scenes=Counter();targets=Counter()
    for _ in range(LIMITS['games']):
        available=[r for r in pool if r['group'] not in groups]
        if not available:raise ValueError('new validation pool insufficient')
        row=min(available,key=lambda r:(kinds[r['task_type']],scenes[r['scene']],targets[r['group'].rsplit('-',2)[-2]]))
        groups.add(row['group']);kinds[row['task_type']]+=1;scenes[row['scene']]+=1;targets[row['group'].rsplit('-',2)[-2]]+=1
        selected.append(dict(task=row,role='TRAIN_VALIDATION',collection_mode='CONTROLLED_INTERVENTION'))
    output.mkdir(mode=0o700,parents=True)
    commit(output/'inventory.private.json',dict(found,validation_eligible=pool,blocked_train_scenes=sorted(blocked)))
    commit(output/'selection.private.json',dict(seed=2026111304,tasks=selected,method='metadata-only diversity seeded ties; no replacement'))
    files=[Path(__file__),Path(previous.__file__),ROOT/'FlowEvo/src/alfworld_/route_a_expanded_labels.py',
           ROOT/'FlowEvo/src/alfworld_/route_a_training_labels.py',ROOT/'scripts/prepare_alfworld_route_a_training_checkpoints.py',
           ROOT/'FlowEvo/src/alfworld_/env.py',ROOT/'FlowEvo/src/alfworld_/success_baseline.py',
           ROOT/'scripts/run_alfworld_python_recovery_feedback.py']
    return commit(output/'protocol.json',dict(version=VERSION,run_id=output.name,data_root=found['data_root'],limits=LIMITS,
        selection_sha256=sha(output/'selection.private.json'),inventory_sha256=sha(output/'inventory.private.json'),
        source_sha256={str(p.resolve()):sha(p) for p in files},environment=environment_manifest(found['data_root']),
        source_dataset_sha256=sha(A1C/'dataset.json'),review_version='a1d-held-retry-review-v1:inherits-a1c-v2',
        scope='VALIDATION_ONLY_CONTROLLED_INTERVENTIONS',paid_api_authorized=False,
        target_rule='visit first four public instances in order; require live open after optional close; no hidden state',
        no_replacement=True,independent_test_execution=False))


def verify(output):
    p=read(output/'protocol.json');s=read(output/'selection.private.json');inv=read(output/'inventory.private.json')
    if p['version']!=VERSION or p['limits']!=LIMITS or p['run_id']!=output.name:raise PermissionError('protocol drift')
    if sha(output/'selection.private.json')!=p['selection_sha256'] or sha(output/'inventory.private.json')!=p['inventory_sha256']:raise PermissionError('selection drift')
    for f,h in {**p['source_sha256'],**inv['files']}.items():
        if sha(f)!=h:raise PermissionError('frozen file changed: '+f)
    if sha(A1C/'dataset.json')!=p['source_dataset_sha256'] or environment_manifest(p['data_root'])!=p['environment']:raise PermissionError('environment or source data drift')
    for r in s['tasks']:
        if r['role']!='TRAIN_VALIDATION' or r['task'] not in inv['validation_eligible']:raise PermissionError('role/isolation')
        verify_source_game(p['data_root'],dict(row=r['task']))
    return p,s


def collect(plan,row,env,origin,subject,mode,receipts,events,deadline):
    key=row['task']['task_id']+'/'+mode
    p,goal,initial=previous.start(env,row['task'],receipts,events,key,deadline)
    if goal!=origin['goal'] or initial!=origin['initial']:raise RunUnhealthy('reset drift')
    for step in origin['steps']:p.step(step['action'],'prefix',expected=step)
    parts=goal_parts(goal)
    if mode=='UNPROCESSED' and not parts[2]:return dict(status='NOT_CONSTRUCTED',reason='NO_PROCESSING_REQUIRED')
    if mode!='UNPROCESSED' and not previous.process(p,subject,parts[2]):return dict(status='NOT_CONSTRUCTED',reason='NO_PUBLIC_PROCESSING_ACTION')
    p.step('inventory','setup')
    choices=sorted({c[6:] for c in p.current['commands'] if c.startswith('go to ') and entity(c[6:])
        and entity(c[6:]).category.capitalize() in TARGETS
        and (entity(c[6:]).category!=parts[1].category if mode=='TARGET_CONFLICT' else compatible(parts[1],entity(c[6:])))})
    if mode=='OTHER_INSTANCE':choices=choices[1:]
    target=None;visits=[]
    for candidate in choices[:LIMITS['max_target_visits']]:
        if len(p.history)>42:break
        if 'go to '+candidate in p.current['commands']:p.step('go to '+candidate,'target_binding')
        if 'close '+candidate in p.current['commands']:p.step('close '+candidate,'target_binding')
        allowed='open '+candidate in p.current['commands'] and 'examine '+candidate in p.current['commands']
        visits.append(dict(instance=candidate,openable=allowed,receipt_sha256=fingerprint(p.current)))
        if allowed:target=candidate;break
    if target is None:return dict(status='NOT_CONSTRUCTED',reason='NO_OPENABLE_PUBLIC_INSTANCE_WITHIN_BUDGET',visits=visits)
    p.step('examine '+target,'setup');prefix=list(p.history)
    failure=p.step('move '+subject.name+' to '+target,'intervention',allow_invalid=True)
    if failure['observation']!='Nothing happens.' or failure['done']:return dict(status='NOT_A_FAILURE',reason='NO_FAILURE_ANCHOR')
    probes=[p.step('open '+target,'reference_probe'),p.step(failure['action'],'reference_probe',allow_invalid=True)]
    return dict(status='COLLECTED',branch=key,original_goal=goal,prefix=prefix,failure=failure,recovery_probe=probes,
        collection_mode='CONTROLLED_INTERVENTION',mode=mode,task=row['task'],role=row['role'],initial=initial,visits=visits)


def probe(output):
    plan,selection=verify(output)
    with (output/'collection.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        events=EvidenceStore(output/'collection.jsonl');old=events.records()
        starts={r['payload']['id'] for r in old if r['kind']=='GAME_STARTED'}
        complete={r['payload']['id']:r['payload'] for r in old if r['kind']=='GAME_COMPLETED'}
        if starts!=set(complete):raise RunUnhealthy('unresolved game; no automatic replay')
        receipts=EnvironmentReceipts(output/'environment.jsonl',LIMITS['environment_steps'])
        if not old:events.append('RUN_STARTED',dict(protocol_sha256=fingerprint(plan)),time.time())
        deadline=events.records()[0]['at']+LIMITS['wall_seconds']
        for i,row in enumerate(selection['tasks']):
            tid=row['task']['task_id'];path=output/'games'/f'{tid}.private.json'
            if tid in complete:
                if sha(path)!=complete[tid]['sha256']:raise PermissionError('receipt drift')
                continue
            if sum(r['kind']=='RESET_CONFIRMED' for r in events.records())+9>LIMITS['resets']:raise BudgetExhausted('reset limit')
            events.append('GAME_STARTED',dict(id=tid,index=i),time.time())
            env=StrictTrainEnv(plan['data_root'],max_steps=50)
            try:
                env.initialize(frozen_game_files=[str(verify_source_game(plan['data_root'],dict(row=row['task'])))])
                p,goal,initial=previous.start(env,row['task'],receipts,events,tid+'/search',deadline)
                subject,error=previous.find_subject(p,goal)
                origin=dict(row=row['task'],goal=goal,initial=initial,steps=list(p.history));branches=[]
                if not error:
                    for mode in LIMITS['modes']:
                        b=collect(plan,row,env,origin,subject,mode,receipts,events,deadline);b['mode']=mode
                        if b['status']=='COLLECTED':
                            b['execution_receipt_sha256']=fingerprint([r['record_hash'] for r in events.records() if r['kind']=='TRANSITION' and r['payload']['branch']==b['branch']])
                            b.update(previous.replay(env,row,b,receipts,events,deadline))
                        branches.append(b)
                commit(path,dict(task=row['task'],role=row['role'],origin=origin,search_error=error,branches=branches))
                events.append('GAME_COMPLETED',dict(id=tid,sha256=sha(path)),time.time())
                print(i+1,tid,error or Counter(b['status'] for b in branches),flush=True)
            finally:env.close()
        return commit(output/'collection_summary.json',dict(games=len(selection['tasks']),environment_steps=sum(receipts.started.values()),
            by_scope=dict(receipts.started),resets=sum(r['kind']=='RESET_CONFIRMED' for r in events.records()),
            elapsed_seconds=time.time()-events.records()[0]['at'],paid_requests=0,independent_test_games=0))


def audit(output):
    plan,sel=verify(output);events=EvidenceStore(output/'collection.jsonl').records()
    complete={r['payload']['id']:r['payload']['sha256'] for r in events if r['kind']=='GAME_COMPLETED'}
    if len(complete)!=len(sel['tasks']):raise RunUnhealthy('collection incomplete')
    samples=[];unresolved=[]
    for r in sel['tasks']:
        path=output/'games'/f"{r['task']['task_id']}.private.json"
        if sha(path)!=complete[r['task']['task_id']]:raise PermissionError('receipt drift')
        g=read(path);valid=[]
        for b in g['branches']:
            if b['status']!='COLLECTED':unresolved.append(dict(game=r['task']['task_id'],**b));continue
            expected=b['prefix']+[b['failure']]+b['recovery_probe']
            actual=[x for x in events if x['kind']=='TRANSITION' and x['payload']['branch']==b['branch']]
            verified=[x['payload']['after'] for x in events if x['kind']=='TRANSITION' and x['payload']['branch']==b['branch']+'/verification']
            if ([x['payload']['after'] for x in actual]!=expected or verified!=expected or fingerprint(expected)!=b['replay_sha256']
                or fingerprint([x['record_hash'] for x in actual])!=b['execution_receipt_sha256']):raise PermissionError('unexecuted branch')
            valid.append(b)
        positives=[b for b in valid if inherited_review(b)['label']=='MATCH']
        for b in valid:
            same=[p for p in positives if command(p['failure']['action'])[1][0]==command(b['failure']['action'])[1][0]]
            label=inherited_review(dict(b,positive_witness=dict(verified=bool(same),same_subject=bool(same),won=bool(same))))
            label['reviewer']=plan['review_version']
            common=dict(game_sha256=r['task']['game_sha256'],scene_id=r['task']['scene'],task_type=r['task']['task_type'],role=r['role'],
                collection_mode='CONTROLLED_INTERVENTION',physical_state_group_id=fingerprint([r['task']['game_sha256'],b['prefix']]),
                checkpoint_sha256=fingerprint(b['prefix']+[b['failure']]),source_receipt_sha256=sha(path),source_key=b['branch'],
                source_dataset=str(output.resolve()),original_goal=b['original_goal'],actual_failed_action=b['failure']['action'])
            sample=dict(common,**label,sample_id='a1d/'+b['branch']+'/full',candidate_context=context(b['original_goal'],b['prefix']+[b['failure']]),
                public_history_scope=dict(complete=True,first_step=1,last_step=len(b['prefix'])+1,omitted_steps=0,rule='FULL_PUBLIC_PREFIX'))
            if label['label'] is None:unresolved.append(sample);continue
            samples.append(sample)
            if b['mode']=='READY' and goal_parts(b['original_goal'])[2]:
                samples.extend(dict(common,**v,sample_id='a1d/'+b['branch']+f'/view{i}') for i,v in enumerate(matched_views(b,label)))
        if g['search_error']:unresolved.append(dict(game=r['task']['task_id'],reason=g['search_error']))
    commit(output/'new_review.private.json',dict(samples=samples,unresolved=unresolved))
    # A new combined manifest; do not rewrite A1c roles, labels or IDs.
    old=load_dataset(A1C)
    combined=[dict(r,source_dataset=str(A1C)) for rows in old.values() for r in rows]+samples
    roles={role:[r for r in combined if r['role']==role] for role in ('TRAIN','TRAIN_VALIDATION')};validate_rows(roles)
    commit(output/'review.private.json',dict(samples=combined,unresolved=unresolved))
    for role,rows in roles.items():
        commit(output/(role.lower()+'.private.json'),rows)
        commit(output/(role.lower()+'_model_view.private.json'),[model_projection(r) for r in rows])
    neg=[r for r in samples if r['label']=='DECLINE'];ready=len({r['game_sha256'] for r in neg})>=3 and len({r['scene_id'] for r in neg})>=2
    return commit(output/'dataset.json',dict(status='A3_DATA_READY_DIAGNOSTIC_MINIMUM' if ready else 'A3_DATA_NOT_READY',
        review_file='review.private.json',review_sha256=sha(output/'review.private.json'),
        files={r:sha(output/(r.lower()+'.private.json')) for r in roles},model_files={r:sha(output/(r.lower()+'_model_view.private.json')) for r in roles},
        parent_dataset_sha256=sha(A1C/'dataset.json'),protocol_sha256=fingerprint(plan),
        new_negative_games=len({r['game_sha256'] for r in neg}),new_negative_scenes=len({r['scene_id'] for r in neg}),
        coverage={role:dict(labels=dict(Counter(r['label'] for r in rows)),games=len({r['game_sha256'] for r in rows}),
            physical_groups=len({r['physical_state_group_id'] for r in rows}),samples=len(rows)) for role,rows in roles.items()},
        A3_data_ready=ready,A3_authorized=False,paid_requests=0,independent_games_executed=0))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('freeze','probe','audit'));p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=globals()[a.command](a.output.resolve());print(canonical({k:v for k,v in result.items() if k in ('run_id','status','coverage','environment_steps')}))
