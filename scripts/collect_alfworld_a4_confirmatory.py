"""C1-only bounded collection using unchanged A1d probes and label reviewer.

Collect strict cohort first. Failure of strict coverage stops; it never causes
outcome-selected replacement or execution of the supplementary cohort.
"""
import argparse
import fcntl
import sys
import time
from pathlib import Path
import run_alfworld_a4_confirmatory as A
import collect_alfworld_a4_checkpoints as C
D=C.D


def freeze(root):
    out=root/'collection'
    if out.exists():raise FileExistsError(out)
    audit=A.read(root/'metadata_audit.json')
    if audit['missing_log_integrity']:raise PermissionError('audit incomplete')
    rows=[dict(r,role='INDEPENDENT_CONFIRMATORY') for r in A.read(root/'candidate_metadata.private.json') if r['stratum']=='strict_scene']
    if not rows:raise PermissionError('no new strict cohort')
    out.mkdir(mode=0o700)
    A.commit(out/'selection.private.json',dict(tasks=rows,rule='ALL_ELIGIBLE_STRICT_TRAIN_CONTAINER_GAMES_PATH_ORDER_NO_REPLACEMENT',seed=None))
    limits={**C.LIMITS,'games':len(rows),'resets':9*len(rows),'environment_steps':450*len(rows),'wall_seconds':3600}
    files={str(Path(m.__file__).resolve()):A.sha(m.__file__) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(A.ROOT) and str(m.__file__).endswith('.py')}
    files[str(Path(__file__).resolve())]=A.sha(__file__)
    for p in (root/'exposure.private.json',root/'Candidate_Freeze.json',root/'scoring_regression.json',root/'candidate_metadata.private.json'):
        files[str(p.resolve())]=A.sha(p)
    if not A.read(root/'scoring_regression.json')['passed']:raise PermissionError('scorer inconsistency')
    data=A.read(A.COLLECTION/'protocol.json')['data_root']
    plan=dict(version='a4-confirmatory-collection-v1',data_root=data,limits=limits,files=files,
        selection_sha256=A.sha(out/'selection.private.json'),environment=D.environment_manifest(data),
        original_scorer_sha256=A.sha(A.ROOT/'scripts/resume_alfworld_a4_scoring.py'),
        gate='four games and two strict scenes for EACH MATCH/DECLINE/UNKNOWN; simple and processed coverage before C2',
        scope='C1_HOST_REFERENCE_ONLY_NO_CANDIDATE_EXECUTION',candidate_execution_allowed=False,model_requests=0,
        label_rule='unchanged A1d; unresolved remains unresolved; UNKNOWN requires incomplete public evidence',
        public_inputs='original goal, public observations and legal commands only; no expert plans',
        downstream_comparison='C2_NOT_AUTHORIZED_BY_C1_FREEZE; require complete labelled data/resources/retention/worker checks',
        supplementary='unseen-game metadata retained; no collection if strict admission fails',
        interruption='unresolved game/step blocks; committed games replay receipts only; no new version after results',
        scoring='same frozen compatibility scorer from first checkpoint; no runtime fixes under same confirmation identity')
    A.commit(out/'protocol.json',plan)
    return dict(protocol_sha256=A.sha(out/'protocol.json'),games=len(rows),limits=limits)


def verify(root):
    out=root/'collection';p=A.read(out/'protocol.json');s=A.read(out/'selection.private.json')
    if p['version']!='a4-confirmatory-collection-v1' or p['model_requests']!=0 or p['candidate_execution_allowed']:raise PermissionError('scope')
    if A.sha(out/'selection.private.json')!=p['selection_sha256']:raise PermissionError('selection drift')
    for f,h in p['files'].items():
        if A.sha(f)!=h:raise PermissionError('frozen source/data drift: '+f)
    for f,h in A.read(root/'exposure.private.json')['files'].items():
        if A.sha(f)!=h:raise PermissionError('historical exposure changed: '+f)
    if D.environment_manifest(p['data_root'])!=p['environment']:raise PermissionError('environment drift')
    protected=A.read(root/'exposure.private.json');blocked={x['task']['game_sha256'] for x in protected['protected_games']}
    groups={x['task']['group'] for x in protected['protected_games']};scenes=set(protected['protected_scenes'])
    for r in s['tasks']:
        t=r['task']
        if r['role']!='INDEPENDENT_CONFIRMATORY' or t['game_sha256'] in blocked or t['group'] in groups or t['scene'] in scenes:raise PermissionError('isolation')
        C.verify_game(p['data_root'],dict(row=t))
    return p,s


def check_pending(events):
    starts={e['payload']['id'] for e in events if e['kind']=='GAME_STARTED'}
    done={e['payload']['id']:e['payload'] for e in events if e['kind']=='GAME_COMPLETED'}
    if starts!=set(done):raise D.RunUnhealthy('unfinished game: preserve and stop, no automatic re-execution')
    return done


def collect(root):
    p,s=verify(root);out=root/'collection';limits=p['limits']
    D.LIMITS={**D.LIMITS,**limits};D.previous.LIMITS={**D.previous.LIMITS,**limits}
    with (out/'collection.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        events=D.EvidenceStore(out/'collection.jsonl');old=events.records();done=check_pending(old)
        receipts=D.EnvironmentReceipts(out/'environment.jsonl',limits['environment_steps'])
        if not old:events.append('RUN_STARTED',dict(protocol_sha256=A.sha(out/'protocol.json')),time.time())
        deadline=events.records()[0]['at']+limits['wall_seconds']
        for i,row in enumerate(s['tasks']):
            tid=row['task']['task_id'];dest=out/'games'/f'{tid}.private.json'
            if tid in done:
                if A.sha(dest)!=done[tid]['sha256']:raise PermissionError('receipt drift')
                continue
            if time.time()>deadline:raise D.BudgetExhausted('wall limit')
            events.append('GAME_STARTED',dict(id=tid,index=i),time.time())
            env=C.CollectionEnv(p['data_root'],row['task']['split'],max_steps=50)
            try:
                env.initialize(frozen_game_files=[str(C.verify_game(p['data_root'],dict(row=row['task'])))])
                probe,goal,initial=D.previous.start(env,row['task'],receipts,events,tid+'/search',deadline)
                subject,error=D.previous.find_subject(probe,goal)
                origin=dict(row=row['task'],goal=goal,initial=initial,steps=list(probe.history));branches=[]
                if not error:
                    for mode in limits['modes']:
                        try:b=D.collect(p,row,env,origin,subject,mode,receipts,events,deadline)
                        except D.BudgetExhausted as e:
                            if str(e)!='episode exhausted':raise
                            b=dict(status='NOT_CONSTRUCTED',reason='EPISODE_LIMIT',branch=tid+'/'+mode)
                        b['mode']=mode
                        if b['status']=='COLLECTED':
                            b['execution_receipt_sha256']=D.fingerprint([e['record_hash'] for e in events.records() if e['kind']=='TRANSITION' and e['payload']['branch']==b['branch']])
                            b.update(D.previous.replay(env,row,b,receipts,events,deadline))
                        branches.append(b)
                A.commit(dest,dict(task=row['task'],role=row['role'],stratum=row['stratum'],origin=origin,search_error=error,branches=branches))
                events.append('GAME_COMPLETED',dict(id=tid,sha256=A.sha(dest)),time.time())
                print(i+1,tid,error or [b['status'] for b in branches],flush=True)
            finally:env.close()
        if (out/'collection_summary.json').exists():return A.read(out/'collection_summary.json')
        return A.commit(out/'collection_summary.json',dict(games=len(s['tasks']),environment_steps=sum(receipts.started.values()),
            scopes=dict(receipts.started),resets=sum(e['kind']=='RESET_CONFIRMED' for e in events.records()),
            elapsed_seconds=time.time()-events.records()[0]['at'],paid_requests=0,candidate_executions=0))


def review(root):
    p,s=verify(root);out=root/'collection';events=D.EvidenceStore(out/'collection.jsonl').records();done=check_pending(events)
    D.EnvironmentReceipts(out/'environment.jsonl',p['limits']['environment_steps'])
    if len(done)!=len(s['tasks']):raise D.RunUnhealthy('collection incomplete')
    samples=[];unresolved=[]
    for row in s['tasks']:
        task=row['task'];path=out/'games'/f"{task['task_id']}.private.json"
        if A.sha(path)!=done[task['task_id']]['sha256']:raise PermissionError('receipt drift')
        game=A.read(path);valid=[]
        for b in game['branches']:
            if b['status']!='COLLECTED':unresolved.append(dict(game_sha256=task['game_sha256'],**b));continue
            expected=b['prefix']+[b['failure']]+b['recovery_probe']
            actual=[e for e in events if e['kind']=='TRANSITION' and e['payload']['branch']==b['branch']]
            replay=[e['payload']['after'] for e in events if e['kind']=='TRANSITION' and e['payload']['branch']==b['branch']+'/verification']
            if ([e['payload']['after'] for e in actual]!=expected or replay!=expected or D.fingerprint(expected)!=b['replay_sha256']
                or D.fingerprint([e['record_hash'] for e in actual])!=b['execution_receipt_sha256']):raise PermissionError('unverified branch')
            valid.append(b)
        positives=[b for b in valid if D.inherited_review(b)['label']=='MATCH']
        for b in valid:
            same=[x for x in positives if D.command(x['failure']['action'])[1][0]==D.command(b['failure']['action'])[1][0]]
            label=D.inherited_review(dict(b,positive_witness=dict(verified=bool(same),same_subject=bool(same),won=bool(same))))
            common=dict(game_sha256=task['game_sha256'],trajectory_sha256=task['trajectory_sha256'],task_group=task['group'],
                task_type=task['task_type'],scene_id=task['scene'],stratum=row['stratum'],role=row['role'],
                physical_state_group_id=D.fingerprint([task['game_sha256'],b['prefix']]),source_receipt_sha256=A.sha(path),source_key=b['branch'])
            sample=dict(common,**label,sample_id='a4c/'+b['branch']+'/full',candidate_context=D.context(b['original_goal'],b['prefix']+[b['failure']]))
            if label['label'] is None:unresolved.append(sample);continue
            samples.append(sample)
            if b['mode']=='READY' and D.goal_parts(b['original_goal'])[2]:
                samples.extend(dict(common,**v,sample_id='a4c/'+b['branch']+f'/view{i}') for i,v in enumerate(D.matched_views(b,label)))
        if game['search_error']:unresolved.append(dict(game_sha256=task['game_sha256'],reason=game['search_error']))
    A.commit(out/'review.private.json',dict(samples=samples,unresolved=unresolved))
    result=A.coverage(samples)
    return A.commit(root/'C1_Readiness.json',dict(result,status='C1_DATA_TARGETS_MET_PENDING_EXECUTION_FREEZE' if result['passed'] else 'C1_BLOCKED_DATA_COVERAGE',
        review_sha256=A.sha(out/'review.private.json'),records=len(samples),unresolved=len(unresolved),candidate_executions=0,
        C2_authorized=False,paid_requests=0,no_automatic_expansion=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze','verify','collect','review']);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    r=globals()[args.command](args.output.resolve());print(D.canonical(r if args.command!='verify' else {'status':'VERIFIED'}))
