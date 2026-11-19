"""P0 host-only semantics audit. No policy generation, candidate or new-game API.

Uses immutable, exposed receipts and the actual embedded TextWorld logic. The
optional three continuations are researcher probes, never learned skill results.
"""
import argparse
from collections import Counter
import fcntl
from pathlib import Path
import re
import time

import run_alfworld_route_a_independent_confirmation as C
import collect_alfworld_a4_checkpoints as K

A=C.A; P=C.V.P; ROOT=C.ROOT
PARENT=ROOT/'runs/alfworld_route_a_targeted_revision_20261117_01'
PHASE=PARENT/'confirmation'
OUT=ROOT/'runs/alfworld_route_a_semantic_audit_20261117_01'
EXPECTED_GATE='32feddc3d43c357bf0e84235d3b9d89e2822ca7b5efe06c66b0c74c20f816553'
EXPECTED_RECOVERY='233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37'
EXPECTED_ONLINE='bed5de02c727edc21aa0333a3c820993b693b9e52a85221b9b07f328e14be62d'
EXPECTED_BANK='ab79b9a482d9458e02cb3bd18432191a778183b8d47fb670c11a1b05c4da2f51'
LIMITS=dict(environment_steps=300,resets=3,episode_steps=50,wall_seconds=900,model_calls=0,worker_calls=0,new_games=0)


def sexprs(text):
    tokens=re.findall(r'\(|\)|[^\s()]+',re.sub(r';[^\n]*','',text).lower())
    stack=[];roots=[]
    for t in tokens:
        if t=='(':
            n=[]
            if stack:stack[-1].append(n)
            else:roots.append(n)
            stack.append(n)
        elif t==')':
            if not stack:raise ValueError('unbalanced PDDL')
            stack.pop()
        else:
            if not stack:raise ValueError('PDDL token outside form')
            stack[-1].append(t)
    if stack:raise ValueError('unbalanced PDDL')
    return roots


def nodes(x):
    if isinstance(x,list):
        yield x
        for n in x:yield from nodes(n)


def form(text,head,second=None):
    found=[x for x in nodes(sexprs(text)) if x and x[0]==head and (second is None or len(x)>1 and x[1]==second)]
    if len(found)!=1:raise ValueError('expected one '+head+': '+str(second))
    return found[0]


def goal_signature(problem):
    goal=form(problem,':goal');ns=list(nodes(goal))
    atoms=[x for x in ns if x and all(isinstance(t,str) for t in x)]
    objects=[x[1] for x in atoms if x[0]=='objecttype']
    destinations=[x[1] for x in atoms if x[0]=='receptacletype']
    processing=[x for x in atoms if x[0] in ('ishot','iscool','isclean')]
    deliveries=[x for x in atoms if x[0]=='inreceptacle']
    return dict(goal=goal,existential=any(x and x[0]=='exists' for x in ns),
        concrete_goal_entity=any(not t.startswith('?') for t in objects+destinations),
        equalities=[x for x in atoms if x[0]=='='],
        typed_subjects=objects,typed_destinations=destinations,processing=processing,deliveries=deliveries,
        same_processed_delivery_variable=bool(processing) and all(any(d[1]==q[1] for d in deliveries) for q in processing))


def action_class(action):
    # Descriptive HOST audit vocabulary, never used to route or choose an action.
    if action.startswith('open '):return 'OPEN_PREPARATION'
    if action.startswith('move '):return 'PLACEMENT_CANDIDATE_FOR_FINAL_DELIVERY'
    if action.startswith(('clean ','heat ','cool ')):return 'PROCESSING_ACTION'
    if action in ('look','inventory') or action.startswith('examine '):return 'INFORMATION_GATHERING'
    return 'OTHER'


def scoped_claim(action,processing_required=False,evidence='UNKNOWN',fixed_instance=False,different_instance=False):
    """Do not infer a negative from mode names, missing evidence or an open."""
    scope=action_class(action)
    if scope=='OPEN_PREPARATION':
        return dict(status='NOT_A_NEGATIVE',scope=scope,claim='Processing absence alone does not forbid preparation.')
    if scope=='PLACEMENT_CANDIDATE_FOR_FINAL_DELIVERY' and processing_required:
        if evidence=='CONFIRMED_ABSENT':
            return dict(status='VALID_NEGATIVE_POSSIBLE',scope='FINAL_DELIVERY',claim='Not a completed processed-object final delivery; intermediate placement may remain useful.')
        if evidence=='UNKNOWN':
            return dict(status='UNRESOLVED',scope='FINAL_DELIVERY',claim='Missing public evidence is not proof of physical absence.')
    if different_instance and not fixed_instance:
        return dict(status='NOT_A_NEGATIVE',scope=scope,claim='Number difference alone does not contradict an existential category goal.')
    return dict(status='UNRESOLVED',scope=scope,claim='Needs task and same-instance state evidence.')


def check_history():
    C.verify(PARENT)
    for p in (PARENT/'Closeout_Integrity.json',PHASE/'Closeout_Integrity.json'):
        P.verify_history(A.read(p)['files'])
    old=C.V.N.OLD;method=A.read(old/'online/Method_Freeze.json')
    checks={PARENT/'frozen_candidate/gate.py':EXPECTED_GATE,C.V.B.CODE:EXPECTED_RECOVERY,
        old/'online/selection.private.json':EXPECTED_ONLINE,Path(method['initial_native_bank']['path']):EXPECTED_BANK}
    for f,h in checks.items():
        if A.sha(f)!=h:raise PermissionError('immutable binding changed '+str(f))
    if A.read(PHASE/'Readiness.json')['passed']:raise PermissionError('historical NO-GO changed')
    return checks


def verified_branches():
    events=P.EvidenceStore(PHASE/'collection/collection.jsonl').records()
    done={e['payload']['id']:e['payload']['sha256'] for e in events if e['kind']=='GAME_COMPLETED'}
    result=[]
    for f in sorted((PHASE/'collection/games').glob('*.private.json')):
        g=A.read(f)
        if A.sha(f)!=done[g['task']['task_id']]:raise PermissionError('source receipt changed')
        for b in g['branches']:
            if b['status']!='COLLECTED':continue
            expected=b['prefix']+[b['failure']]+b['recovery_probe']
            actual=[e for e in events if e['kind']=='TRANSITION' and e['payload']['branch']==b['branch']]
            replay=[e['payload']['after'] for e in events if e['kind']=='TRANSITION' and e['payload']['branch']==b['branch']+'/verification']
            if ([e['payload']['after'] for e in actual]!=expected or replay!=expected or
                A.digest(expected)!=b['replay_sha256'] or A.digest([e['record_hash'] for e in actual])!=b['execution_receipt_sha256']):
                raise PermissionError('unverified historical witness')
            result.append((f,g,b))
    return result


def prepare(out=OUT):
    if (out/'protocol.json').exists():return verify(out)
    checks=check_history();plan=A.read(PHASE/'protocol.json');data=Path(plan['data_root'])
    branches=verified_branches();goals=[];witnesses=[];jobs=[];used=set();files={str(f):h for f,h in checks.items()}
    for f in sorted((PHASE/'collection/games').glob('*.private.json')):
        g=A.read(f);game=data/g['task']['game']
        if A.sha(game)!=g['task']['game_sha256']:raise PermissionError('embedded game changed')
        raw=A.read(game) # HOST ONLY; never exported to any learner, gate or solver.
        goal=goal_signature(raw['pddl_problem'])
        actions={name:form(raw['pddl_domain'],':action',name) for name in ('openobject','putobject','cleanobject','heatobject','coolobject','pickupobject')}
        goals.append(dict(task=g['task'],public_goal=g['origin']['goal'],signature=goal,
            actions=actions,domain_sha256=A.digest(raw['pddl_domain']),grammar_sha256=A.digest(raw['grammar'])))
        files[str(game)]=A.sha(game);files[str(f)]=A.sha(f)
    for f,g,b in branches:
        failed=b['failure'];probe=b['recovery_probe'];sub,target=failed['action'][5:].split(' to ')
        witnesses.append(dict(game=g['task']['task_id'],type=g['task']['task_type'],mode=b['mode'],
            source_path=str(f),source_sha256=A.sha(f),branch=b['branch'],goal=b['original_goal'],
            prefix=b['prefix'],failure=failed,probe=probe,replay_verified=True,
            open_effect=probe[0]['observation']!='Nothing happens.',retry_legal=failed['action'] in probe[0]['commands'],
            retry_effect=probe[-1]['observation']!='Nothing happens.',won=probe[-1]['won'],done=probe[-1]['done'],
            subject=sub,target=target))
        typ=g['task']['task_type'];take='take '+sub+' from '+target
        if b['mode']!='UNPROCESSED' or typ in used or take not in probe[-1]['commands']:continue
        ready=next((x for x in g['branches'] if x['mode']=='READY' and x['status']=='COLLECTED'),None)
        op={'pick_clean_then_place_in_recep':'clean','pick_heat_then_place_in_recep':'heat','pick_cool_then_place_in_recep':'cool'}.get(typ)
        if not ready or not op:continue
        steps=ready['prefix'];idx=next((i for i,s in enumerate(steps) if s['action'].startswith(op+' '+sub+' with ')),None)
        if idx is None or not idx or not steps[idx-1]['action'].startswith('go to '):continue
        # Explicit HOST branch, composed from exposed READY actions, not a skill.
        continuation=[take,steps[idx-1]['action'],steps[idx]['action'],'go to '+target,failed['action']]
        replay=b['prefix']+[failed]+probe
        if len(replay)+len(continuation)>50:continue
        jobs.append(dict(task=g['task'],goal=b['original_goal'],initial=b['initial'],replay=replay,
            continuation=continuation,source_path=str(f),source_sha256=A.sha(f),
            purpose='HOST_SEMANTIC_CONTINUATION_NOT_CANDIDATE_PERFORMANCE'))
        used.add(typ)
    if len(jobs)!=3:raise PermissionError('three exposed processing witnesses not available')
    import alfworld, textworld
    site=Path(alfworld.__file__).parent;tw=Path(textworld.__file__).parent
    sources=[site/'gen/goal_library.py',site/'gen/game_states/task_game_state.py',site/'agents/utils/misc.py',
        site/'agents/environment/alfred_tw_env.py',site/'data/alfred.pddl',site/'data/alfred.twl2',tw/'envs/pddl/pddl.py',
        ROOT/'FlowEvo/src/alfworld_/env.py',ROOT/'FlowEvo/src/alfworld_/route_a_expanded_labels.py',
        ROOT/'scripts/prepare_alfworld_route_a_a1d.py',Path(__file__).resolve(),ROOT/'scripts/test_alfworld_route_a_semantic_boundaries.py']
    files.update({str(p):A.sha(p) for p in sources})
    out.mkdir(parents=True,exist_ok=True)
    A.commit(out/'audit.private.json',dict(goals=goals,witnesses=witnesses,jobs=jobs,source_files=[str(p) for p in sources]))
    frozen=dict(version='route-a-p0-semantics-v1',scope='EXPOSED_HOST_AUDIT_ONLY_STOP_AFTER_P0',data_root=str(data),
        limits=LIMITS,files=files,audit_sha256=A.sha(out/'audit.private.json'),
        online_game_sha256s=[x['task']['game_sha256'] for x in A.read(C.V.N.OLD/'online/selection.private.json')['tasks']],
        candidate_execution_allowed=False,new_game_collection_allowed=False,p1_p2_p3_executed=False,
        selection='Lexicographically first exposed UNPROCESSED per processing type with an actual legal take-back and existing READY processing witness; no candidate-output selection.',
        environment=K.D.environment_manifest(str(data)))
    return A.commit(out/'protocol.json',frozen)


def verify(out=OUT):
    check_history();p=A.read(out/'protocol.json');P.verify_history(p['files'])
    if p['limits']!=LIMITS or p['audit_sha256']!=A.sha(out/'audit.private.json'):raise PermissionError('audit freeze changed')
    if K.D.environment_manifest(p['data_root'])!=p['environment']:raise PermissionError('environment changed')
    for j in A.read(out/'audit.private.json')['jobs']:
        if j['task']['game_sha256'] in p['online_game_sha256s']:raise PermissionError('online game forbidden')
        if len(j['replay'])+len(j['continuation'])>50:raise PermissionError('episode cap')
    return p


def replay(out=OUT):
    p=verify(out);jobs=A.read(out/'audit.private.json')['jobs']
    with (out/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        events=P.EvidenceStore(out/'audit_events.jsonl');old=events.records()
        starts={e['payload']['id'] for e in old if e['kind']=='JOB_STARTED'}
        dones={e['payload']['id']:e['payload'] for e in old if e['kind']=='JOB_COMPLETED'}
        if starts!=dones.keys():raise P.RunUnhealthy('unfinished P0 job; no automatic replay')
        receipts=P.EnvironmentReceipts(out/'environment.jsonl',LIMITS['environment_steps'])
        if (out/'result.json').exists():
            for d in dones.values():
                if A.sha(d['path'])!=d['sha256']:raise PermissionError('completed receipt changed')
            return A.read(out/'result.json')
        if not old:events.append('RUN_STARTED',dict(protocol_sha256=A.digest(p)),time.time())
        deadline=events.records()[0]['at']+LIMITS['wall_seconds'];results=[]
        for j in jobs:
            key=j['task']['task_id'];dest=out/'receipts'/(key+'.private.json')
            if key in dones:
                if A.sha(dest)!=dones[key]['sha256']:raise PermissionError('completed job changed')
                results.append(A.read(dest));continue
            if time.time()>deadline:raise K.D.BudgetExhausted('P0 wall limit')
            events.append('JOB_STARTED',dict(id=key),time.time())
            env=K.CollectionEnv(p['data_root'],'train',max_steps=50)
            try:
                env.initialize(frozen_game_files=[str(K.verify_game(p['data_root'],dict(row=j['task'])))])
                probe,goal,initial=K.D.previous.start(env,j['task'],receipts,events,key,deadline)
                if goal!=j['goal'] or initial!=j['initial']:raise P.RunUnhealthy('P0 reset drift')
                for s in j['replay']:probe.step(s['action'],'exposed_prefix',expected=s,allow_invalid=True)
                suffix=[]
                for action in j['continuation']:suffix.append(probe.step(action,'host_continuation'))
                result=dict(game=key,type=j['task']['task_type'],goal=goal,job_sha256=A.digest(j),
                    trajectory=probe.history,premature_move=j['replay'][-1],suffix=suffix,
                    won=probe.current['won'],steps=len(probe.history),candidate_executed=False)
                A.commit(dest,result);events.append('JOB_COMPLETED',dict(id=key,path=str(dest),sha256=A.sha(dest)),time.time())
                results.append(result)
            finally:env.close()
        verify(out)
        return A.commit(out/'result.json',dict(status='P0_HOST_REPLAY_COMPLETED',rows=results,
            environment_steps=sum(receipts.started.values()),resets=3,new_games=0,model_calls=0,worker_calls=0,paid_usd=0,
            candidate_permission='SHADOW',online_executed=False,stopped_at='P0'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','verify','replay']);parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args();result=globals()[args.command](args.output.resolve());print(A.digest(result))
