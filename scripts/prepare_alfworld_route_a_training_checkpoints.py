"""Bounded controlled-intervention data preparation. No model or skill execution."""
import argparse
from collections import Counter
import fcntl
from pathlib import Path
import random
import time

from alfworld_.route_a_training_labels import (VERSION as LABEL_VERSION, goal_parts, compatible,
    processed, context, review, window_sample, model_projection)
from alfworld_.precondition_diagnostic import command, receipt_effect, entity
from alfworld_.skill_acquisition import StrictTrainEnv, _reset, verify_source_game
from alfworld_.env import _goal_from_observation
from failure_evo.contracts import fingerprint, canonical
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, sha
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from run_alfworld_success_baseline import game_row
from run_alfworld_python_recovery_feedback import commit, EnvironmentReceipts, environment_manifest

ROOT=Path(__file__).resolve().parents[1]
BASE=Path.home()/'.local/share/flowevo'
S1=ROOT/'runs/alfworld_container_boundary_learning_20261113_02'
A1=ROOT/'runs/alfworld_route_a_a1_20261113_01'
VERSION='route-a-controlled-training-v1'
RUNS=('alfworld_full_library_online120_20261109_01','alfworld_full_library_calibration_20261109_04')
TYPES=('pick_and_place_simple','pick_heat_then_place_in_recep','pick_cool_then_place_in_recep','pick_clean_then_place_in_recep')
MODES=('READY','UNPROCESSED','WRONG_NOT_HELD','WRONG_HELD')
LIMITS=dict(max_games=16,games_per_type=4,max_checkpoints_per_game=4,
            intervention_steps_per_checkpoint=3,episode_steps=50,total_environment_steps=6400,
            total_resets=128,wall_seconds=1800,automatic_expansion=False,
            replay_policy='one exact validation replay per completed branch; interrupted branch blocks')


def records(path):
    if not path.is_file(): raise FileNotFoundError(path)
    return EvidenceStore(path).records()


def protected(base):
    a=read(A1/'data_audit_v2.private.json')
    inv=read(S1/'independent_inventory.private.json')
    rows=inv['strict_scene']+inv['expanded_game_group']
    files={str(A1/'data_audit_v2.private.json'):sha(A1/'data_audit_v2.private.json'),
           str(S1/'independent_inventory.private.json'):sha(S1/'independent_inventory.private.json')}
    # Include the original Gate pools and shards, not only the recently expanded pool.
    for top in sorted(base.glob('alfworld*')):
        if not top.is_dir(): continue
        for file in sorted(top.rglob('candidate_pool.private.json')):
            data=read(file)
            rows+=data.get('candidate_pool',[])
            files[str(file)]=sha(file)
        for file in sorted(top.rglob('learning_protocol.json')):
            data=read(file)
            rows += [r for shard in data.get('gate_shards',[]) for r in shard]
            files[str(file)]=sha(file)
    return dict(games=sorted(set(a['roles']['EXPOSED_REGRESSION']['excluded_games'])|
                            {r['game_sha256'] for r in rows}),
                trajectories=sorted({r['trajectory_sha256'] for r in rows}),
                groups=sorted({r.get('group',Path(r['game']).parent.parent.name) for r in rows}),
                scenes=sorted({r['scene'] for r in rows if 'scene' in r}),files=files)


def discover(base,output):
    output.mkdir(mode=0o700,parents=True,exist_ok=False)
    protection=protected(base)
    inventory=[];excluded=[]; files=dict(protection['files'])
    data=None
    for name in RUNS:
        root=base/name; protocol=read(root/'protocol.json')
        data=protocol['data_root'] if data is None else data
        if data!=protocol['data_root']: raise PermissionError('data root differs')
        files[str(root/'protocol.json')]=sha(root/'protocol.json')
        files[str(root/'episodes.jsonl')]=sha(root/'episodes.jsonl')
        for sequence,task in enumerate(protocol['tasks'],1):
            if game_row(Path(data)/task['game'],Path(data))!=task: raise PermissionError('game manifest drift')
            destination=task['group'].rsplit('-',2)[-2]
            reasons=[]
            if task['split']!='train' or task['task_type'] not in TYPES: reasons.append('TASK_SCOPE')
            if destination not in ('Safe','Drawer','Fridge','Microwave','Cabinet'): reasons.append('CONTAINER_SCOPE')
            if task['game_sha256'] in protection['games']: reasons.append('PROTECTED_GAME')
            if task['trajectory_sha256'] in protection['trajectories']: reasons.append('PROTECTED_TRAJECTORY')
            if task['group'] in protection['groups']: reasons.append('PROTECTED_GROUP')
            if task['scene'] in protection['scenes']: reasons.append('RESERVED_EVALUATION_SCENE')
            row=dict(task=task,historical_run=str(root),sequence=sequence,container_type=destination,
                     historical_exposure='EXPOSED_NATIVE_RUN',selection_does_not_read_episode_outcome=True)
            if reasons: excluded.append(dict(row,reasons=reasons))
            else: inventory.append(row)
    return commit(output/'discovery.private.json',dict(version=VERSION,inventory=inventory,excluded=excluded,
                  protected=protection,files=files,data_root=data))


def load_origin(row):
    root=Path(row['historical_run']);task=row['task']
    commits=[r for r in records(root/'episodes.jsonl') if r['kind']=='EPISODE_COMMITTED']
    entry=commits[row['sequence']-1]['payload']
    if entry['task_id']!=task['task_id']: raise PermissionError('source task differs')
    journal=root/'episodes'/task['task_id']/'environment.jsonl'
    history=records(journal)
    if history[0]['kind']!='RESET' or any(r['kind']!='STEP' for r in history[1:]): raise PermissionError('source event type')
    steps=[r['payload'] for r in history[1:]]
    if _goal_from_observation(history[0]['payload']['observation'])!=entry['outcome']['trace']['goal']:
        raise PermissionError('original goal differs from real reset observation')
    for actual, trace in zip(steps,entry['outcome']['trace']['actions'],strict=True):
        if any(actual[k]!=trace[k] for k in ('action','observation','done','score')):raise PermissionError('trace drift')
    return dict(row=task,sequence=row['sequence'],initial=history[0]['payload'],steps=steps,
                goal=entry['outcome']['trace']['goal'],journal=str(journal),journal_sha256=sha(journal))


def freeze_selection(output):
    found=read(output/'discovery.private.json'); rng=random.Random(2026111301)
    chosen=[];groups=set();games=set()
    for kind in TYPES:
        candidates=sorted((r for r in found['inventory'] if r['task']['task_type']==kind),key=lambda r:r['task']['game'])
        rng.shuffle(candidates); n=0
        for row in candidates:
            task=row['task']
            if task['group'] in groups or task['game_sha256'] in games:continue
            groups.add(task['group']);games.add(task['game_sha256'])
            chosen.append(dict(row,role='TRAIN' if n%2==0 else 'TRAIN_VALIDATION'))
            n+=1
            if n==LIMITS['games_per_type']:break
    # Freeze identities before loading any public prefixes, then freeze search code.
    commit(output/'selection.private.json',dict(seed=2026111301,discovery_sha256=sha(output/'discovery.private.json'),
        tasks=chosen,selection='stratified seeded metadata draw, alternate roles, one game per task group, no replacement',
        expansion=False))
    files=dict(found['files'])
    for row in chosen:
        p=Path(row['historical_run'])/'episodes'/row['task']['task_id']/'environment.jsonl'
        files[str(p)]=sha(p)
    sources=[Path(__file__),ROOT/'FlowEvo/src/alfworld_/route_a_training_labels.py',
             ROOT/'FlowEvo/src/alfworld_/skill_acquisition.py',ROOT/'FlowEvo/src/alfworld_/env.py',
             ROOT/'FlowEvo/src/alfworld_/success_baseline.py',ROOT/'scripts/run_alfworld_python_recovery_feedback.py',
             ROOT/'scripts/run_alfworld_success_baseline.py',ROOT/'FlowEvo/src/alfworld_/precondition_diagnostic.py',
             ROOT/'FlowEvo/src/failure_evo/evidence.py']
    plan=dict(version=VERSION,run_id=output.name,limits=LIMITS,
        selection_sha256=sha(output/'selection.private.json'),files=files,
        code_sha256={str(p):sha(p) for p in sources},data_root=found['data_root'],
        environment=environment_manifest(found['data_root']),modes=MODES,
        goal_policy='unchanged native goal, no goal substitution',
        search='first publicly confirmed target take; READY uses first same-instance required processing receipt; public legal navigation to first target instance; close if open; inventory; one failed placement then open and retry',
        negative_policy='other publicly seen object; wrong held remains unresolved if useful intermediate action cannot be ruled out; not-held negative requires actual failed retry',
        unknown_policy='last two observed transitions, explicit incomplete history, required processing omitted; no inference from private full state',
        reference_probes='HOST_ONLY_NOT_MODEL_TRAINING_SUFFIX',paid_api_authorized=False,model_calls=0)
    return commit(output/'protocol.json',plan)


def verify(output, *, audit_only=False):
    if output.stat().st_mode & 0o077:raise PermissionError('private collection directory required')
    plan=read(output/'protocol.json');selection=read(output/'selection.private.json')
    if plan['version']!=VERSION or plan['limits']!=LIMITS or sha(output/'selection.private.json')!=plan['selection_sha256']:
        raise PermissionError('selection or resource freeze differs')
    expected={**plan['files'],**plan['code_sha256']}
    amendment=output/'audit_amendment.json'
    if audit_only and amendment.is_file():
        change=read(amendment);script=str(Path(__file__).resolve())
        if (change['scope']!='GROUPING_ONLY_NO_RELABEL_NO_EXECUTION'
                or change['protocol_sha256']!=fingerprint(plan)
                or sha(output/'frozen_collection_script.py')!=expected[script]
                or change['old_source_sha256']!=expected[script]):
            raise PermissionError('invalid read-only audit amendment')
        expected[script]=change['new_source_sha256']
    for path,digest in expected.items():
        if sha(path)!=digest:raise PermissionError('frozen file changed: '+path)
    if environment_manifest(plan['data_root'])!=plan['environment']:raise PermissionError('environment version differs')
    check_isolation(selection['tasks'],read(output/'discovery.private.json')['protected'])
    return plan,selection


def check_isolation(tasks,protection):
    games=[r['task']['game_sha256'] for r in tasks]
    if len(games)!=len(set(games)):raise PermissionError('same game across roles/checkpoints')
    if set(games)&set(protection['games']):raise PermissionError('protected game')
    if any(r['task']['trajectory_sha256'] in protection['trajectories'] or r['task']['group'] in protection['groups'] for r in tasks):
        raise PermissionError('protected provenance')


def search_prefix(origin,mode):
    parts=goal_parts(origin['goal'])
    if parts is None:return None,'UNSUPPORTED_PUBLIC_GOAL'
    obj,_,operation=parts
    if mode=='UNPROCESSED' and not operation:return None,'NO_PROCESSING_REQUIRED'
    for i,s in enumerate(origin['steps']):
        p=command(s['action'])
        if not p or p[0]!='take' or not compatible(obj,p[1][0]) or receipt_effect(p,s['observation'])!='TRUE':continue
        subject=p[1][0]
        if mode in ('UNPROCESSED','WRONG_HELD') or operation is None:return (i+1,subject.name),None
        for j,t in enumerate(origin['steps'][i+1:],i+1):
            q=command(t['action'])
            if q and q[0]==operation and q[1][0]==subject and receipt_effect(q,t['observation'])=='TRUE':
                return (j+1,subject.name),None
        return None,'NO_PUBLIC_PROCESS_RECEIPT'
    return None,'NO_CONFIRMED_TARGET_TAKE'


class ProbeSteps:
    """Use the existing environment step ledger; the extra journal stores raw receipts."""
    def __init__(self,env,initial,receipts,events,key,deadline):
        self.env,self.current,self.receipts,self.events,self.key,self.deadline=env,initial,receipts,events,key,deadline
        self.history=[]

    def step(self,action,scope,expected=None,allow_invalid=False):
        if time.time()>self.deadline:raise BudgetExhausted('collection wall limit')
        if self.current.get('done') or len(self.history)>=50:raise BudgetExhausted('episode exhausted')
        if not allow_invalid and action not in self.current['commands'] and expected is None:
            raise RunUnhealthy('probe setup must be admissible')
        before=self.current
        receipt=self.receipts.step(self.env,action,branch=self.key,scope=scope,expected=expected)
        self.events.append('TRANSITION',dict(branch=self.key,index=len(self.history)+1,
            before=before,after=receipt,scope=scope,admissible=action in before['commands']),time.time())
        self.current=receipt;self.history.append(receipt)
        return receipt


def collect_branch(plan,row,mode,origin,receipts,events,deadline,env_factory=StrictTrainEnv):
    found,error=search_prefix(origin,mode)
    if error:return dict(status='NOT_CONSTRUCTED',reason=error)
    cut,subject=found;parts=goal_parts(origin['goal']);dest=parts[1]
    if cut>40:return dict(status='NOT_CONSTRUCTED',reason='PREFIX_RESERVE_INSUFFICIENT')
    key=fingerprint([row['task']['game_sha256'],mode,fingerprint(plan)])
    env=env_factory(plan['data_root'],max_steps=50)
    try:
        env.initialize(frozen_game_files=[str(verify_source_game(plan['data_root'],origin))])
        _reset(env,origin)
        events.append('RESET_CONFIRMED',dict(branch=key,initial=origin['initial']),time.time())
        p=ProbeSteps(env,origin['initial'],receipts,events,key,deadline)
        for s in origin['steps'][:cut]:p.step(s['action'],'prefix',expected=s)
        # Alternatives derive only from already observed public take commands.
        seen=[origin['initial'],*p.history]
        alternatives=sorted({q[1][0].name for s in seen for c in s['commands']
            if (q:=command(c)) and q[0]=='take' and q[1][0].category!=parts[0].category})
        attempted=subject
        if mode=='WRONG_NOT_HELD':
            if not alternatives:return dict(status='NOT_CONSTRUCTED',reason='NO_PUBLIC_OTHER_OBJECT')
            attempted=alternatives[0]
        if mode=='WRONG_HELD':
            # Intentional data intervention, never a generated skill or repair answer.
            drops=sorted(c for c in p.current['commands'] if (q:=command(c)) and q[0]=='move'
                         and q[1][0].name==subject and not compatible(dest,q[1][1]))
            if not drops:return dict(status='NOT_CONSTRUCTED',reason='NO_LEGAL_HAND_RELEASE')
            p.step(drops[0],'setup')
            takes=sorted(c for c in p.current['commands'] if (q:=command(c)) and q[0]=='take' and q[1][0].category!=parts[0].category)
            if not takes:return dict(status='NOT_CONSTRUCTED',reason='NO_LEGAL_OTHER_PICKUP')
            attempted=command(takes[0])[1][0].name
            p.step(takes[0],'setup')
        p.step('inventory','setup')
        targets=sorted({c.removeprefix('go to ') for c in p.current['commands'] if c.startswith('go to ')
                        and entity(c[6:]) and compatible(dest,entity(c[6:]))}|
                       {q[1][0].name for c in p.current['commands'] if (q:=command(c)) and q[0] in ('open','close')
                        and compatible(dest,q[1][0])})
        if not targets:return dict(status='NOT_CONSTRUCTED',reason='NO_PUBLIC_TARGET')
        target=targets[0]
        if 'go to '+target in p.current['commands']:p.step('go to '+target,'setup')
        if 'close '+target in p.current['commands']:p.step('close '+target,'setup')
        if 'open '+target not in p.current['commands']:return dict(status='NOT_CONSTRUCTED',reason='TARGET_NOT_OPENABLE')
        if 'examine '+target not in p.current['commands']:return dict(status='NOT_CONSTRUCTED',reason='NO_PUBLIC_CLOSED_CHECK')
        p.step('examine '+target,'setup')
        if len(p.history)>47:return dict(status='NOT_CONSTRUCTED',reason='CHECKPOINT_BUDGET_EXHAUSTED')
        prefix=list(p.history)
        failed=p.step('move '+attempted+' to '+target,'intervention',allow_invalid=True)
        if failed['observation']!='Nothing happens.' or failed['done']:
            return dict(status='NOT_A_FAILURE_ANCHOR',failure=failed)
        probe=[p.step('open '+target,'recovery_probe')]
        probe.append(p.step(failed['action'],'recovery_probe',allow_invalid=True))
        return dict(status='COLLECTED',branch=key,collection_mode='CONTROLLED_INTERVENTION',
            original_goal=origin['goal'],prefix=prefix,failure=failed,recovery_probe=probe,
            original_prefix_steps=cut,auto_label_status='PENDING_INDEPENDENT_EVIDENCE_REVIEW',
            proposed_label='MATCH' if probe[-1]['won'] else 'DECLINE' if mode=='WRONG_NOT_HELD' else None)
    finally:env.close()


def replay_branch(plan,row,origin,branch,receipts,events,deadline,env_factory=StrictTrainEnv):
    env=env_factory(plan['data_root'],max_steps=50)
    key=branch['branch']+'/verification'
    try:
        env.initialize(frozen_game_files=[str(verify_source_game(plan['data_root'],origin))])
        _reset(env,origin)
        events.append('RESET_CONFIRMED',dict(branch=key,initial=origin['initial']),time.time())
        p=ProbeSteps(env,origin['initial'],receipts,events,key,deadline)
        for s in branch['prefix']+[branch['failure']]+branch['recovery_probe']:
            p.step(s['action'],'verification',expected=s,allow_invalid=True)
        return dict(replay_verified=True,replay_sha256=fingerprint(p.history))
    finally:env.close()


def probe(output):
    plan,selection=verify(output)
    with (output/'probe.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        journal=EvidenceStore(output/'probe.jsonl');existing=journal.records()
        started={r['payload']['key'] for r in existing if r['kind']=='BRANCH_STARTED'}
        finished={r['payload']['key'] for r in existing if r['kind']=='BRANCH_COMPLETED'}
        if started!=finished:raise RunUnhealthy('unfinished controlled branch requires review; no automatic resend')
        receipts=EnvironmentReceipts(output/'environment.jsonl',plan['limits']['total_environment_steps'])
        if not existing:journal.append('RUN_STARTED',dict(protocol_sha256=fingerprint(plan)),time.time())
        deadline=journal.records()[0]['at']+plan['limits']['wall_seconds']
        for i,row in enumerate(selection['tasks']):
            origin=load_origin(row)
            for mode in MODES:
                key=f'{i:02d}_{mode}';path=output/'branches'/f'{key}.private.json'
                if key in finished:
                    saved=next(r['payload'] for r in existing if r['kind']=='BRANCH_COMPLETED' and r['payload']['key']==key)
                    if sha(path)!=saved['sha256']:raise PermissionError('branch receipt changed')
                    continue
                if time.time()>deadline:raise BudgetExhausted('collection wall budget')
                reset_count=sum(r['kind']=='RESET_CONFIRMED' for r in journal.records())
                if reset_count+2>plan['limits']['total_resets']:raise BudgetExhausted('reset budget')
                journal.append('BRANCH_STARTED',dict(key=key,game_sha256=row['task']['game_sha256'],mode=mode),time.time())
                result=collect_branch(plan,row,mode,origin,receipts,journal,deadline)
                result.update(task=row['task'],role=row['role'],mode=mode,origin_journal_sha256=origin['journal_sha256'])
                if result['status']=='COLLECTED':
                    raw=[r['record_hash'] for r in journal.records() if r['kind']=='TRANSITION' and r['payload']['branch']==result['branch']]
                    result['execution_receipt_sha256']=fingerprint(raw)
                    result.update(replay_branch(plan,row,origin,result,receipts,journal,deadline))
                commit(path,result)
                journal.append('BRANCH_COMPLETED',dict(key=key,sha256=sha(path)),time.time())
                print(key,result['status'],flush=True)
        return commit(output/'probe_summary.json',dict(protocol_sha256=fingerprint(plan),
            environment_steps=dict(receipts.started),total_environment_steps=sum(receipts.started.values()),
            resets=sum(r['kind']=='RESET_CONFIRMED' for r in journal.records()),
            elapsed_seconds=time.time()-journal.records()[0]['at'],paid_requests=0,independent_games_executed=0))


def audit(output):
    plan,selection=verify(output,audit_only=True);journal=records(output/'probe.jsonl')
    completed={r['payload']['key']:r['payload']['sha256'] for r in journal if r['kind']=='BRANCH_COMPLETED'}
    if len(completed)!=len(selection['tasks'])*len(MODES):raise RunUnhealthy('probe incomplete')
    candidates=[];rejected=[]
    for key,digest in completed.items():
        path=output/'branches'/f'{key}.private.json'
        if sha(path)!=digest:raise PermissionError('branch mutated')
        branch=read(path)
        if branch['status']!='COLLECTED':rejected.append(dict(key=key,status=branch['status'],reason=branch.get('reason')));continue
        transitions=[r for r in journal if r['kind']=='TRANSITION' and r['payload']['branch']==branch['branch']]
        replay=[r for r in journal if r['kind']=='TRANSITION' and r['payload']['branch']==branch['branch']+'/verification']
        expected=branch['prefix']+[branch['failure']]+branch['recovery_probe']
        if ([r['payload']['after'] for r in transitions]!=expected or [r['payload']['after'] for r in replay]!=expected
                or fingerprint([r['record_hash'] for r in transitions])!=branch['execution_receipt_sha256']
                or fingerprint(expected)!=branch['replay_sha256']):raise PermissionError('unexecuted or unreplayable checkpoint')
        label=review(branch)
        if label['label'] is not None and branch['proposed_label'] != label['label']:
            label=dict(label,label=None,label_status='UNRESOLVED_LABEL',reason='proposed label and evidence review conflict')
        # All no-effect interventions from the same pre-action state share a
        # group, even when the attempted object/action differs.
        physical=fingerprint([branch['task']['game_sha256'],branch['prefix']])
        common=dict(game_sha256=branch['task']['game_sha256'],scene_id=branch['task']['scene'],
                    task_type=branch['task']['task_type'],role=branch['role'],original_goal=branch['original_goal'],
                    collection_mode=branch['collection_mode'],physical_state_group_id=physical,
                    checkpoint_sha256=fingerprint(branch['prefix']+[branch['failure']]),
                    source_receipt_sha256=digest,actual_failed_action=branch['failure']['action'],
                    actual_failure_receipt=branch['failure'],source_key=key)
        full=dict(common,**label, sample_id=key+'/full',candidate_context=context(branch['original_goal'],branch['prefix']+[branch['failure']]),
                  public_history_scope=dict(complete=True,first_step=1,last_step=len(branch['prefix'])+1,omitted_steps=0,rule='FULL_PUBLIC_PREFIX'))
        if label['label_status']=='EVIDENCE_REVIEWED':candidates.append(full)
        else:rejected.append(full)
        window=window_sample(branch,label)
        if window:candidates.append(dict(common,**window,sample_id=key+'/last2'))
    # Two modes may reach the same physical state. Never count the duplicate twice.
    unique={};duplicates=[]
    for row in candidates:
        identity=fingerprint([row['game_sha256'],row['candidate_context'],row['public_history_scope']])
        if identity in unique:duplicates.append(dict(sample_id=row['sample_id'],same_as=unique[identity]['sample_id']))
        else:unique[identity]=row
    result=dict(status='REVIEW_COMPLETE',reviewer_version=LABEL_VERSION,samples=list(unique.values()),
                unresolved=rejected,duplicates=duplicates,probe_summary_sha256=sha(output/'probe_summary.json'))
    target='review_grouped.private.json' if (output/'audit_amendment.json').is_file() else 'review.private.json'
    return commit(output/target,result)


def freeze_dataset(output):
    plan,selection=verify(output,audit_only=True)
    review_path=output/('review_grouped.private.json' if (output/'audit_amendment.json').is_file() else 'review.private.json')
    reviewed=read(review_path)
    sets={role:[r for r in reviewed['samples'] if r['role']==role] for role in ('TRAIN','TRAIN_VALIDATION')}
    groups={role:{r['game_sha256'] for r in rows} for role,rows in sets.items()}
    if groups['TRAIN']&groups['TRAIN_VALIDATION']:raise PermissionError('game leakage')
    coverage={role:{label:dict(samples=sum(r['label']==label for r in rows),
                  games=len({r['game_sha256'] for r in rows if r['label']==label})) for label in ('MATCH','DECLINE','UNKNOWN')}
              for role,rows in sets.items()}
    ready=all(x['games'] for c in coverage.values() for x in c.values())
    for role,rows in sets.items():
        commit(output/(role.lower()+'.private.json'),rows)
        commit(output/(role.lower()+'_model_view.private.json'),[model_projection(r) for r in rows])
    return commit(output/'dataset.json',dict(status='DATA_READY_CONTROLLED_ONLY' if ready else 'PARTIAL_COVERAGE',
        protocol_sha256=fingerprint(plan),review_file=review_path.name,review_sha256=sha(review_path),coverage=coverage,
        audit_amendment_sha256=sha(output/'audit_amendment.json') if (output/'audit_amendment.json').is_file() else None,
        files={role:sha(output/(role.lower()+'.private.json')) for role in sets},
        model_files={role:sha(output/(role.lower()+'_model_view.private.json')) for role in sets},
        known_limitations=['controlled not spontaneous failures','not-held negatives may be easier than wrong-held goal conflicts',
                          'partial-history UNKNOWN views are grouped derivatives','no independent transfer evidence'],
        A3_ready=False,A3_remaining=['A2 engineering acceptance','new paid learning protocol and explicit authorization'],
        paid_requests=0,independent_games_executed=0))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('discover','freeze_selection','probe','audit','freeze_dataset'))
    parser.add_argument('--base',type=Path,default=BASE)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=args.output.resolve()
    result=discover(args.base,output) if args.command=='discover' else globals()[args.command](output)
    print(canonical({k:v for k,v in result.items() if k in ('status','coverage','total_environment_steps','resets','run_id')}))


if __name__=='__main__':main()
