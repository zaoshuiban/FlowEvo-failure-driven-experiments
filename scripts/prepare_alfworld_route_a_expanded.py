"""A1c: new training-only games, bounded public-state interventions, no model calls."""
import argparse
from collections import Counter, defaultdict
import fcntl
from pathlib import Path
import random
import time

from alfworld_.route_a_training_labels import goal_parts, compatible, context, model_projection
from alfworld_.route_a_expanded_labels import review, matched_views, VERSION as LABEL_VERSION, SCOPE
from alfworld_.precondition_diagnostic import command, entity, receipt_effect
from alfworld_.skill_acquisition import StrictTrainEnv, _reset, verify_source_game
from failure_evo.contracts import fingerprint, canonical
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, sha
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from prepare_alfworld_route_a_training_checkpoints import protected, ProbeSteps, TYPES
from run_alfworld_success_baseline import exposure, game_row
from run_alfworld_python_recovery_feedback import commit, EnvironmentReceipts, environment_manifest

ROOT=Path(__file__).resolve().parents[1]
BASE=Path.home()/'.local/share/flowevo'
VERSION='route-a-a1c-training-pool-v1'
SEED=2026111303
TARGETS=('Cabinet','Drawer','Fridge','Microwave','Safe')
LIMITS=dict(games=45,train_games=32,validation_games=13,episode_steps=50,
    search_steps=28,environment_steps=16000,resets=450,wall_seconds=14400,
    modes=['READY','TARGET_CONFLICT','UNPROCESSED','OTHER_INSTANCE'],
    max_branches_per_game=4,max_samples_per_game=4,no_replacement=True)


def extract_rows(value):
    if isinstance(value,dict):
        if all(k in value for k in ('game','game_sha256','trajectory_sha256','group')):
            yield value
        else:
            for v in value.values():yield from extract_rows(v)
    elif isinstance(value,list):
        for v in value:yield from extract_rows(v)


def inventory(base):
    data=Path(read(base/'alfworld_full_library_online120_20261109_01/protocol.json')['data_root'])
    protection=protected(base)
    old, manifests=exposure(base,data)
    files={x['path']:x['sha256'] for x in manifests};files.update(protection['files'])
    # Conservative metadata-only exposure scan, including repo-local development
    # runs. Frozen-but-not-executed games are also excluded; no result selection.
    names={'protocol.json','selection.private.json','candidate_pool.private.json',
           'independent_inventory.private.json','learning_protocol.json'}
    for top in (ROOT/'runs',base):
        for file in sorted(top.glob('alfworld*/**/*.json')):
            if file.name not in names:continue
            rows=list(extract_rows(read(file)))
            if rows:old.extend(rows);files[str(file)]=sha(file)
    used={k:{r[k] for r in old} for k in ('game_sha256','trajectory_sha256','group')}
    rows=[];excluded=[]
    for file in sorted((data/'json_2.1.1/train').glob('*/*/game.tw-pddl')):
        row=game_row(file,data);reasons=[]
        if row['split']!='train':raise PermissionError('mixed split')
        for key,field in (('game_sha256','games'),('trajectory_sha256','trajectories'),('group','groups')):
            if row[key] in used[key]:reasons.append('PRIOR_MANIFEST_'+key)
            if row[key] in protection[field]:reasons.append('SEALED_'+key)
        if row['scene'] in protection['scenes']:reasons.append('SEALED_SCENE')
        if reasons:excluded.append(dict(task=row,reasons=reasons))
        else:rows.append(row)
    return dict(data_root=str(data),eligible=rows,excluded=excluded,protected=protection,files=files)


def choose(rows):
    rng=random.Random(SEED)
    candidates=[r for r in rows if r['task_type'] in TYPES and r['group'].rsplit('-',2)[-2] in TARGETS]
    scenes=sorted({r['scene'] for r in candidates})
    # Feasibility search uses metadata only, before ANY game execution. Keep
    # the first seeded scene partition meeting all four task-group quotas.
    quotas={'TRAIN':[8,8,8,8],'TRAIN_VALIDATION':[4,3,3,3]}
    parts=None
    for attempt in range(1000):
        shuffled=list(scenes);rng.shuffle(shuffled)
        val_scenes=set(shuffled[::3]);trial={'TRAIN':set(scenes)-val_scenes,'TRAIN_VALIDATION':val_scenes}
        if all(len({r['group'] for r in candidates if r['scene'] in trial[role] and r['task_type']==kind})>=n
               for role in trial for kind,n in zip(TYPES,quotas[role])):
            parts=trial;break
    if parts is None:raise ValueError('no metadata-feasible disjoint scene partition')
    selected=[];used_groups=set()
    for role in parts:
        scene_counts=Counter();target_counts=Counter()
        for kind,n in zip(TYPES,quotas[role]):
            pool=sorted((r for r in candidates if r['scene'] in parts[role] and r['task_type']==kind),key=lambda r:r['game'])
            rng.shuffle(pool)
            for _ in range(n):
                allowed=[r for r in pool if r['group'] not in used_groups]
                if not allowed:break
                # Diversity only: fewer scenes/target types first, seeded ties.
                r=min(allowed,key=lambda r:(target_counts[r['group'].rsplit('-',2)[-2]],scene_counts[r['scene']]))
                pool.remove(r);used_groups.add(r['group']);scene_counts[r['scene']]+=1
                target_counts[r['group'].rsplit('-',2)[-2]]+=1
                selected.append(dict(task=r,role=role,collection_mode='CONTROLLED_INTERVENTION'))
    return selected,dict(train=sorted(parts['TRAIN']),validation=sorted(val_scenes),metadata_partition_attempt=attempt+1)


def freeze(base,output):
    if output.exists():raise FileExistsError('new A1c run required')
    found=inventory(base);tasks,partition=choose(found['eligible'])
    counts=Counter(r['role'] for r in tasks)
    if counts!=dict(TRAIN=32,TRAIN_VALIDATION=13):raise ValueError('metadata pool insufficient; no outcome-based replacement')
    output.mkdir(mode=0o700,parents=True)
    commit(output/'inventory.private.json',found)
    commit(output/'selection.private.json',dict(seed=SEED,tasks=tasks,scene_partition=partition,
        method='prepartitioned scenes; four task strata; metadata-only container/scene diversity; seeded ties',
        no_replacement=True))
    paths=[Path(__file__),ROOT/'FlowEvo/src/alfworld_/route_a_expanded_labels.py',
        ROOT/'FlowEvo/src/alfworld_/route_a_training_labels.py',
        ROOT/'scripts/prepare_alfworld_route_a_training_checkpoints.py',
        ROOT/'scripts/run_alfworld_python_recovery_feedback.py',
        ROOT/'FlowEvo/src/alfworld_/success_baseline.py',ROOT/'FlowEvo/src/alfworld_/env.py',
        ROOT/'FlowEvo/src/alfworld_/precondition_diagnostic.py']
    return commit(output/'protocol.json',dict(version=VERSION,run_id=output.name,
        selection_sha256=sha(output/'selection.private.json'),inventory_sha256=sha(output/'inventory.private.json'),
        source_sha256={str(p):sha(p) for p in paths},data_root=found['data_root'],limits=LIMITS,
        environment=environment_manifest(found['data_root']),label_version=LABEL_VERSION,label_scope=SCOPE,
        semantic_limits=['no-win alone is not DECLINE','unfinished processing may be preparation: unresolved',
                         'category-only goal cannot prove numbered-instance conflict'],
        public_search='lexicographic public exploration until first goal-object take; no expert/location metadata',
        paid_requests=0,A3_authorized=False,independent_test_execution=False))


def verify(output,*,audit_only=False):
    plan=read(output/'protocol.json');selection=read(output/'selection.private.json')
    if plan['version']!=VERSION or plan['limits']!=LIMITS or plan['run_id']!=output.name:
        raise PermissionError('protocol identity')
    for name,key in (('selection.private.json','selection_sha256'),('inventory.private.json','inventory_sha256')):
        if sha(output/name)!=plan[key]:raise PermissionError('frozen metadata differs')
    found=read(output/'inventory.private.json')
    expected={**plan['source_sha256'],**found['files']}
    amendment=output/'audit_amendment.json'
    if audit_only and amendment.exists():
        change=read(amendment)
        if (change['scope']!='LABEL_REVIEW_ONLY_NO_ENVIRONMENT_EXECUTION'
                or change['protocol_sha256']!=fingerprint(plan)):
            raise PermissionError('invalid audit-only amendment')
        for file,binding in change['sources'].items():
            if (expected.get(file)!=binding['old_sha256']
                    or sha(output/'collection_source'/Path(file).name)!=binding['old_sha256']):
                raise PermissionError('original collection code not preserved')
            expected[file]=binding['new_sha256']
    for file,digest in expected.items():
        if sha(file)!=digest:raise PermissionError('frozen source/manifest drift: '+file)
    if environment_manifest(plan['data_root'])!=plan['environment']:raise PermissionError('environment drift')
    used={};seen=set()
    for r in selection['tasks']:
        t=r['task']
        if game_row(Path(plan['data_root'])/t['game'],Path(plan['data_root']))!=t:raise PermissionError('game drift')
        if t not in found['eligible'] or t['game_sha256'] in seen:raise PermissionError('ineligible/duplicate')
        seen.add(t['game_sha256'])
        if t['scene'] in used and used[t['scene']]!=r['role']:raise PermissionError('cross-role scene')
        used[t['scene']]=r['role']
    return plan,selection


def start(env,task,receipts,events,key,deadline):
    if sum(x['kind']=='RESET_CONFIRMED' for x in events.records())>=LIMITS['resets']:raise BudgetExhausted('reset cap')
    actual,obs,commands=env.reset()
    initial=dict(observation=obs,commands=list(commands),score=0.0,done=False,won=False)
    events.append('RESET_CONFIRMED',dict(branch=key,initial=initial,game_sha256=task['game_sha256']),time.time())
    return ProbeSteps(env,initial,receipts,events,key,deadline),actual.goal,initial


def find_subject(p,goal):
    parts=goal_parts(goal)
    if not parts:return None,'PUBLIC_GOAL_UNSUPPORTED'
    visited=set()
    while len(p.history)<LIMITS['search_steps']:
        takes=sorted(c for c in p.current['commands'] if (q:=command(c)) and q[0]=='take' and compatible(parts[0],q[1][0]))
        if takes:
            action=takes[0];s=p.step(action,'public_search')
            if receipt_effect(command(action),s['observation'])=='TRUE':return command(action)[1][0],None
            return None,'TAKE_NOT_CONFIRMED'
        opens=sorted(c for c in p.current['commands'] if c.startswith('open ') and c not in visited)
        nav=sorted(c for c in p.current['commands'] if c.startswith('go to ') and c not in visited)
        actions=opens or nav
        if not actions:return None,'NO_PUBLIC_SEARCH_ACTION'
        visited.add(actions[0]);p.step(actions[0],'public_search')
    return None,'PUBLIC_SEARCH_BUDGET'


def process(p,subject,operation):
    if not operation:return True
    choices=sorted(c for c in p.current['commands'] if (q:=command(c)) and q[0]==operation and q[1][0]==subject)
    if not choices:
        # Tool names are taken only from public navigation commands. This is
        # collection setup, not a generated or deployed recovery skill.
        tool={'heat':'microwave','cool':'fridge','clean':'sinkbasin'}[operation]
        nav=sorted(c for c in p.current['commands'] if c.startswith('go to '+tool+' '))
        if nav:p.step(nav[0],'processing_setup')
        choices=sorted(c for c in p.current['commands'] if (q:=command(c)) and q[0]==operation and q[1][0]==subject)
    if not choices:return False
    s=p.step(choices[0],'processing_setup')
    return receipt_effect(command(choices[0]),s['observation'])=='TRUE'


def collect(plan,row,env,origin,base_prefix,subject,mode,receipts,events,deadline):
    key=row['task']['task_id']+'/'+mode
    p,goal,initial=start(env,row['task'],receipts,events,key,deadline)
    if goal!=origin['goal'] or initial!=origin['initial']:raise RunUnhealthy('reset changed')
    for s in base_prefix:p.step(s['action'],'prefix',expected=s)
    parts=goal_parts(goal)
    if mode=='UNPROCESSED' and not parts[2]:return dict(status='NOT_CONSTRUCTED',reason='NO_PROCESSING_REQUIRED')
    if mode!='UNPROCESSED' and not process(p,subject,parts[2]):
        return dict(status='NOT_CONSTRUCTED',reason='NO_PUBLIC_PROCESSING_ACTION')
    p.step('inventory','setup')
    targets=sorted({c[6:] for c in p.current['commands'] if c.startswith('go to ') and entity(c[6:])
                    and entity(c[6:]).category.capitalize() in TARGETS})
    if mode=='TARGET_CONFLICT':targets=[x for x in targets if entity(x).category!=parts[1].category]
    else:targets=[x for x in targets if compatible(parts[1],entity(x))]
    index=1 if mode=='OTHER_INSTANCE' else 0
    if len(targets)<=index:return dict(status='NOT_CONSTRUCTED',reason='NO_PUBLIC_TARGET_INSTANCE')
    target=targets[index]
    if 'go to '+target in p.current['commands']:p.step('go to '+target,'setup')
    if 'close '+target in p.current['commands']:p.step('close '+target,'setup')
    if 'open '+target not in p.current['commands']:return dict(status='NOT_CONSTRUCTED',reason='TARGET_NOT_OPENABLE')
    if 'examine '+target not in p.current['commands']:return dict(status='NOT_CONSTRUCTED',reason='NO_PUBLIC_CLOSED_CHECK')
    p.step('examine '+target,'setup')
    if len(p.history)>47:return dict(status='NOT_CONSTRUCTED',reason='REMAINING_STEPS')
    prefix=list(p.history);failure=p.step('move '+subject.name+' to '+target,'intervention',allow_invalid=True)
    if failure['observation']!='Nothing happens.' or failure['done']:return dict(status='NOT_A_FAILURE',reason='NO_FAILURE_ANCHOR')
    probe=[p.step('open '+target,'reference_probe'),p.step(failure['action'],'reference_probe',allow_invalid=True)]
    return dict(status='COLLECTED',branch=key,original_goal=goal,prefix=prefix,failure=failure,recovery_probe=probe,
        collection_mode='CONTROLLED_INTERVENTION',mode=mode,task=row['task'],role=row['role'],
        initial=initial,proposed_label=None)


def replay(env,row,branch,receipts,events,deadline):
    p,goal,initial=start(env,row['task'],receipts,events,branch['branch']+'/verification',deadline)
    if goal!=branch['original_goal'] or initial!=branch['initial']:raise RunUnhealthy('verification reset drift')
    for s in branch['prefix']+[branch['failure']]+branch['recovery_probe']:
        p.step(s['action'],'verification',expected=s,allow_invalid=True)
    return dict(replay_verified=True,replay_sha256=fingerprint(p.history))


def probe(output):
    plan,selection=verify(output)
    with (output/'collection.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        events=EvidenceStore(output/'collection.jsonl');old=events.records()
        started={r['payload']['id'] for r in old if r['kind']=='GAME_STARTED'}
        complete={r['payload']['id']:r['payload'] for r in old if r['kind']=='GAME_COMPLETED'}
        if started!=set(complete):raise RunUnhealthy('unresolved game: preserve receipts, no automatic replay')
        receipts=EnvironmentReceipts(output/'environment.jsonl',LIMITS['environment_steps'])
        if not old:events.append('RUN_STARTED',dict(protocol_sha256=fingerprint(plan)),time.time())
        deadline=events.records()[0]['at']+LIMITS['wall_seconds']
        for index,row in enumerate(selection['tasks']):
            tid=row['task']['task_id'];path=output/'games'/f'{tid}.private.json'
            if tid in complete:
                if sha(path)!=complete[tid]['sha256']:raise PermissionError('completed game changed')
                continue
            events.append('GAME_STARTED',dict(id=tid,index=index),time.time())
            env=StrictTrainEnv(plan['data_root'],max_steps=50)
            try:
                env.initialize(frozen_game_files=[str(verify_source_game(plan['data_root'],dict(row=row['task'])))])
                p,goal,initial=start(env,row['task'],receipts,events,tid+'/search',deadline)
                subject,error=find_subject(p,goal)
                origin=dict(row=row['task'],goal=goal,initial=initial,steps=list(p.history))
                branches=[]
                if not error:
                    for mode in LIMITS['modes']:
                        b=collect(plan,row,env,origin,origin['steps'],subject,mode,receipts,events,deadline)
                        b['mode']=mode
                        if b['status']=='COLLECTED':
                            raw=[r['record_hash'] for r in events.records() if r['kind']=='TRANSITION' and r['payload']['branch']==b['branch']]
                            b['execution_receipt_sha256']=fingerprint(raw)
                            b.update(replay(env,row,b,receipts,events,deadline))
                        branches.append(b)
                result=dict(task=row['task'],role=row['role'],origin=origin,search_error=error,branches=branches)
                commit(path,result)
                events.append('GAME_COMPLETED',dict(id=tid,sha256=sha(path)),time.time())
                print(index+1,tid,error or Counter(b['status'] for b in branches),flush=True)
            finally:env.close()
        return commit(output/'collection_summary.json',dict(games=len(selection['tasks']),
            environment_steps=sum(receipts.started.values()),by_scope=dict(receipts.started),
            resets=sum(r['kind']=='RESET_CONFIRMED' for r in events.records()),
            elapsed_seconds=time.time()-events.records()[0]['at'],paid_requests=0,independent_test_games=0))


def audit(output):
    plan,selection=verify(output,audit_only=True);events=EvidenceStore(output/'collection.jsonl').records()
    completions={x['payload']['id']:x['payload']['sha256'] for x in events if x['kind']=='GAME_COMPLETED'}
    if len(completions)!=len(selection['tasks']):raise RunUnhealthy('collection incomplete')
    accepted=[];unresolved=[];duplicates=[]
    for row in selection['tasks']:
        path=output/'games'/f"{row['task']['task_id']}.private.json"
        if sha(path)!=completions[row['task']['task_id']]:raise PermissionError('raw game changed')
        game=read(path);valid=[]
        for b in game['branches']:
            if b['status']!='COLLECTED':unresolved.append(dict(game=row['task']['task_id'],**b));continue
            expected=b['prefix']+[b['failure']]+b['recovery_probe']
            actual=[r for r in events if r['kind']=='TRANSITION' and r['payload']['branch']==b['branch']]
            replayed=[r['payload']['after'] for r in events if r['kind']=='TRANSITION' and r['payload']['branch']==b['branch']+'/verification']
            if ([r['payload']['after'] for r in actual]!=expected or replayed!=expected
                or fingerprint(expected)!=b['replay_sha256'] or fingerprint([r['record_hash'] for r in actual])!=b['execution_receipt_sha256']):
                raise PermissionError('receipt not executed/replayed')
            valid.append(b)
        positives=[b for b in valid if review(b)['label']=='MATCH']
        game_samples=[]
        for b in valid:
            same=[x for x in positives if command(x['failure']['action'])[1][0]==command(b['failure']['action'])[1][0]]
            evaluated=dict(b,positive_witness=dict(verified=bool(same),same_subject=bool(same),won=bool(same),
                branch_sha256=fingerprint(same[0]) if same else None))
            label=review(evaluated)
            physical=fingerprint([row['task']['game_sha256'],b['prefix']])
            common=dict(game_sha256=row['task']['game_sha256'],scene_id=row['task']['scene'],task_type=row['task']['task_type'],
                role=row['role'],collection_mode='CONTROLLED_INTERVENTION',physical_state_group_id=physical,
                checkpoint_sha256=fingerprint(b['prefix']+[b['failure']]),source_receipt_sha256=sha(path),
                source_key=b['branch'],actual_failed_action=b['failure']['action'],original_goal=b['original_goal'])
            sample=dict(common,**label,sample_id=b['branch']+'/full',
                candidate_context=context(b['original_goal'],b['prefix']+[b['failure']]),
                public_history_scope=dict(complete=True,first_step=1,last_step=len(b['prefix'])+1,omitted_steps=0,rule='FULL_PUBLIC_PREFIX'))
            if label['label'] is None:unresolved.append(sample);continue
            # A different instance is not intrinsically a conflict. Preserve
            # a replay-proven positive if the fixed per-game cap has space;
            # never relabel it DECLINE to fill the requested conflict category.
            game_samples.append(sample)
            if b['mode']=='READY' and goal_parts(b['original_goal'])[2]:
                for i,v in enumerate(matched_views(b,label)):
                    game_samples.append(dict(common,**v,sample_id=b['branch']+f'/view{i}'))
        accepted.extend(game_samples[:LIMITS['max_samples_per_game']])
        duplicates.extend(dict(sample_id=r['sample_id'],reason='fixed per-game cap; reviewed label retained',label=r['label'])
                          for r in game_samples[LIMITS['max_samples_per_game']:])
        if game['search_error']:unresolved.append(dict(game=row['task']['task_id'],reason=game['search_error']))
    from alfworld_.recovery_applicability_learning import validate_rows
    roles={role:[r for r in accepted if r['role']==role] for role in ('TRAIN','TRAIN_VALIDATION')}
    validate_rows(roles)
    reviewed=dict(samples=accepted,unresolved=unresolved,duplicates=duplicates,reviewer=LABEL_VERSION)
    commit(output/'review.private.json',reviewed)
    for role,rows in roles.items():
        commit(output/(role.lower()+'.private.json'),rows)
        commit(output/(role.lower()+'_model_view.private.json'),[model_projection(r) for r in rows])
    coverage={role:dict(samples=len(rows),games=len({r['game_sha256'] for r in rows}),
        physical_groups=len({r['physical_state_group_id'] for r in rows}),scenes=len({r['scene_id'] for r in rows}),
        labels=dict(Counter(r['label'] for r in rows)),task_types=dict(Counter(r['task_type'] for r in rows)),
        history_lengths={label:dict(Counter(len(r['candidate_context']['history']) for r in rows if r['label']==label)) for label in ('MATCH','DECLINE','UNKNOWN')}) for role,rows in roles.items()}
    return commit(output/'dataset.json',dict(status='A1C_CONTROLLED_DATA_PARTIAL_PENDING_REVIEW',version=VERSION,
        protocol_sha256=fingerprint(plan),review_file='review.private.json',review_sha256=sha(output/'review.private.json'),
        files={role:sha(output/(role.lower()+'.private.json')) for role in roles},
        model_files={role:sha(output/(role.lower()+'_model_view.private.json')) for role in roles},coverage=coverage,
        label_scope=SCOPE,audit_amendment_sha256=sha(output/'audit_amendment.json') if (output/'audit_amendment.json').exists() else None,
        known_limitations=['target-conflict label additionally requires opening to leave the held-subject retry illegal and ineffective',
            'phase conflict and numbered-instance conflict not assumed','controlled not spontaneous',
            'A2 source executor and larger input budgets require A3 integration'],
        A3_ready=False,paid_requests=0,independent_games_executed=0))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('freeze','preflight','probe','audit'))
    p.add_argument('--output',type=Path,required=True);p.add_argument('--base',type=Path,default=BASE)
    a=p.parse_args();out=a.output.resolve()
    result=freeze(a.base,out) if a.command=='freeze' else dict(status='READY_ZERO_API_COLLECTION',games=len(verify(out)[1]['tasks'])) if a.command=='preflight' else globals()[a.command](out)
    print(canonical({k:v for k,v in result.items() if k in ('status','run_id','games','coverage','environment_steps')}))


if __name__=='__main__':main()
