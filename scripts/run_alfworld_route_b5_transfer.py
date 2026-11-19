"""B5 zero-model, immutable checkpoint transfer. Reuses A1d collection and B4 Worker.

Collection labels are host-only, scoped to failed FINAL delivery. They are not
claims that every preparatory opening is harmful. No policy is synthesized here.
"""
import argparse
from collections import Counter
from dataclasses import replace
import fcntl
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

import run_alfworld_a4_confirmatory as A
import collect_alfworld_a4_confirmatory as C
import run_alfworld_container_b4_real as B4
import run_alfworld_applicability_multicandidate as B
from audit_alfworld_a3b import card_for
from alfworld_.route_a_training_labels import processed

P=B4.P; D=C.D; ROOT=A.ROOT
VERSION='route-b5-frozen-transfer-v1'
PARENT=ROOT/'runs/alfworld_route_b4_real_20261116_01'
RESERVATION=ROOT/'runs/alfworld_route_b3_container_preparation_20261116_03/prospective_metadata/selection.private.json'
A3=ROOT/'runs/alfworld_route_a_a3b_semantic_feedback_20261114_01/pilot_frozen'
ARMS=('S11','FR11','Route_A')
LIMITS=dict(C.C.LIMITS,games=12,environment_steps=6000,resets=108,wall_seconds=10800)
EXPECTED={'S11':'da2d550f990194ad14f0ea61a57281931a6c57a14cdbebb2bb5cf6fd05598f7b',
          'FR11':'3c63f420b178b8f40846dc03396f3519ebf940db12a7eec0076da01de0169b97',
          'Route_A':'5d92dd91b7bec7d514112f6bfef5814f381a4f8670f72a3807e7200b18de22fd',
          'S0':'233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37'}


def exposure_decision(task,audit):
    hits=[]
    for row in audit['protected_games']:
        old=row['task']
        if any(old[k]==task[k] for k in ('game_sha256','trajectory_sha256','group')):
            hits.extend(reason for reason in row['reasons'] if reason!='ALLOCATED_OR_RESERVED:'+str(RESERVATION))
    return sorted(set(hits))


def freeze(root):
    if (root/'protocol.json').exists():return verify(root)[0]
    audit=A.read(root/'exposure.private.json')
    if audit['malformed']:raise PermissionError('incomplete exposure audit')
    parent=A.read(PARENT/'protocol.json');selection=A.read(RESERVATION)
    selected=[];excluded=[]
    for row in selection['tasks']:
        reasons=exposure_decision(row['task'],audit)
        if reasons:excluded.append(dict(row,reasons=reasons))
        else:selected.append(dict(row,role='B5_CONTROLLED_TRANSFER_NOT_TRAINING'))
    paths=dict(S11=PARENT/'S11_3/initial/candidate.py',FR11=PARENT/'FR11_0/behavior/candidate.py',
               Route_A=A3/'frozen_candidate/gate.py',S0=B.CODE)
    for arm,path in paths.items():
        if A.sha(path)!=EXPECTED[arm]:raise PermissionError('candidate drift '+arm)
    adapted=B.worker_artifact(paths['Route_A'].read_text())
    checks={arm:P.static_check_detailed(adapted if arm=='Route_A' else path.read_text()) for arm,path in paths.items()}
    if not all(x['passed'] for x in checks.values()):raise PermissionError(checks)
    files={str(Path(m.__file__).resolve()):A.sha(m.__file__) for m in list(sys.modules.values())
           if getattr(m,'__file__',None) and str(m.__file__).endswith('.py') and Path(m.__file__).resolve().is_relative_to(ROOT)}
    files.update(A.read(PARENT/'Closeout_Integrity.json')['files'])
    files.update(parent['historical_sha256'])
    for directory in (A3,):
        files.update({str(f):A.sha(f) for f in directory.rglob('*') if f.is_file() and '__pycache__' not in str(f)})
    files.update(audit['files'])
    test=ROOT/'scripts/test_alfworld_route_b5.py';files[str(test)]=A.sha(test)
    files[str(RESERVATION)]=A.sha(RESERVATION)
    for path in paths.values():files[str(path)]=A.sha(path)
    A.commit(root/'collection/selection.private.json',dict(selection,tasks=selected,excluded=excluded))
    runtime={k:parent[k] for k in ('data_root','environment','worker','environment_type','episode_limit','source_window','max_stagnant_repeats')}
    plan=dict(runtime,version=VERSION,run_id=root.name,files=files,limits=LIMITS,
        selection_sha256=A.sha(root/'collection/selection.private.json'),exposure_sha256=A.sha(root/'exposure.private.json'),
        candidates={k:dict(path=str(v),sha256=EXPECTED[k]) for k,v in paths.items()},
        joint_sha256=A.digest([EXPECTED, A.sha(B.worker_artifact.__code__.co_filename)]),static=checks,
        max_calls=0,max_tokens=0,max_cost_microusd=0,worker_calls=2000,environment_steps=10000,wall_seconds=14400,
        collection_rules='Unchanged A1d: READY,TARGET_CONFLICT,UNPROCESSED,OTHER_INSTANCE; public search only; no replacements.',
        checkpoint_rules='At most 3/game: READY equal-length MATCH/UNKNOWN pair if available, otherwise first reviewed MATCH; first reviewed DECLINE; fill remaining with first different reviewed physical state. No UNKNOWN fabricated for simple tasks.',
        label_scope='FAILED_FINAL_DELIVERY_ONLY_NOT_ALL_USEFUL_OPENING_ACTIONS',
        unknown_rule='entry evidence separate; later recovery judged against newly available public processing evidence, otherwise unsupported or unresolved',
        scores='barrier newly admissible; successful same-action delivery separately; MATCH completed repair requires delivery+won; strict local witness retained separately',
        readiness=dict(capability='FR11 full repair >=3 games,2 scenes,2 containers',safety='zero confirmed false or unsupported recovery; unresolved safety blocks',coverage='MATCH >=8 games, controls >=8 games, DECLINE and UNKNOWN each >=2 games; multiple scenes/types',engineering='complete replay and hash/ledger checks'),
        paid_requests=0,native_G=False,published=False,permission='SHADOW',scope='UNSEEN_GAME_SEEN_SCENE_CONTROLLED_TRANSFER',
        budget_derivation='collection <=12*(1+4*2)*50=5400 steps, cap6000; execution <=36*3*50=5400, cap10000 includes resume. Total16000. Worker<=36*(3*18+1)=1980 plus20 smoke.',
        interruption='committed receipts reused; unknown Worker/environment or incomplete collection game blocks; no replacement')
    A.commit(root/'protocol.json',plan)
    return plan


def verify(root):
    p=A.read(root/'protocol.json');s=A.read(root/'collection/selection.private.json')
    if p['version']!=VERSION or p['max_calls'] or p['max_cost_microusd'] or p['permission']!='SHADOW':raise PermissionError('protocol')
    P.verify_history(p['files'])
    if A.sha(root/'exposure.private.json')!=p['exposure_sha256'] or A.sha(root/'collection/selection.private.json')!=p['selection_sha256']:raise PermissionError('data freeze')
    if P.environment_manifest(p['data_root'])!=p['environment']:raise PermissionError('environment drift')
    for r in s['tasks']:C.C.verify_game(p['data_root'],dict(row=r['task']))
    for x in p['candidates'].values():
        if A.sha(x['path'])!=x['sha256']:raise PermissionError('candidate changed')
    return p,s


def collect(root):
    # Only inject this study's verified plan into the unchanged shared collector.
    p,_=verify(root)
    if A.read(root/'Preflight.json')['protocol_sha256']!=A.digest(p):raise PermissionError('preflight required')
    with patch.object(C,'verify',side_effect=lambda _:verify(root)):
        return C.collect(root)


def choose_samples(rows):
    ready=[s for s in rows if s['mode']=='READY'];chosen=[]
    pair=[s for s in ready if s.get('public_history_scope',{}).get('complete') is False]
    if {s['label'] for s in pair}=={'MATCH','UNKNOWN'}:chosen.extend(pair[:2])
    else:chosen.extend([s for s in rows if s['label']=='MATCH'][:1])
    negatives=[s for s in rows if s['label']=='DECLINE']
    chosen.extend(negatives[:1])
    for s in rows:
        if len(chosen)>=3:break
        if s not in chosen and s['physical_state_group_id'] not in {v['physical_state_group_id'] for v in chosen}:chosen.append(s)
    return chosen[:3]


def review(root):
    p,sel=verify(root);out=root/'collection';events=D.EvidenceStore(out/'collection.jsonl').records();done=C.check_pending(events)
    P.EnvironmentReceipts(out/'environment.jsonl',p['limits']['environment_steps'])
    if len(done)!=len(sel['tasks']):raise P.RunUnhealthy('incomplete collection')
    samples=[];excluded=[];paths={}
    for r in sel['tasks']:
        t=r['task'];path=out/'games'/f"{t['task_id']}.private.json";paths[str(path)]=A.sha(path)
        if paths[str(path)]!=done[t['task_id']]['sha256']:raise PermissionError('receipt drift')
        g=A.read(path);valid=[];rows=[]
        for b in g['branches']:
            if b['status']!='COLLECTED':excluded.append(dict(game=t['task_id'],**b));continue
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
            common=dict(game_sha256=t['game_sha256'],task_id=t['task_id'],task_group=t['group'],scene_id=t['scene'],task_type=t['task_type'],container=t['group'].rsplit('-',2)[-2],
                physical_state_group_id=D.fingerprint([t['game_sha256'],b['prefix']]),source_receipt_sha256=A.sha(path),source_key=b['branch'],mode=b['mode'],role='B5_TRANSFER_ONLY')
            s=dict(common,**label,sample_id='b5/'+b['branch']+'/full',candidate_context=D.context(b['original_goal'],b['prefix']+[b['failure']]))
            if label['label'] is None:excluded.append(dict(s,status='UNVERIFIED'));continue
            rows.append(s)
            if b['mode']=='READY':rows.extend(dict(common,**v,sample_id='b5/'+b['branch']+f'/view{i}') for i,v in enumerate(D.matched_views(b,label)))
        chosen=choose_samples(rows);samples.extend(chosen)
        excluded.extend(dict(x,exclusion='PREDEFINED_THREE_PER_GAME_LIMIT') for x in rows if x not in chosen)
        if g['search_error']:excluded.append(dict(game=t['task_id'],reason=g['search_error']))
    A.commit(root/'checkpoints.private.json',dict(samples=samples,excluded=excluded))
    freeze=dict(status='P1_FROZEN_BEFORE_CANDIDATE_EXECUTION',checkpoint_sha256=A.sha(root/'checkpoints.private.json'),files=paths,
        protocol_sha256=A.digest(p),labels=dict(Counter(s['label'] for s in samples)),games=len({s['game_sha256'] for s in samples}),physical_groups=len({s['physical_state_group_id'] for s in samples}),records=len(samples),paid_requests=0)
    return A.commit(root/'Checkpoint_Freeze.json',freeze)


def origin_for(root,s):
    path=root/'collection/games'/f"{s['task_id']}.private.json";g=A.read(path)
    if A.sha(path)!=s['source_receipt_sha256']:raise PermissionError('source drift')
    b=next(b for b in g['branches'] if b.get('branch')==s['source_key']);prefix=b['prefix']+[b['failure']]
    ids=s.get('public_history_scope',{}).get('retained_step_ids');visible=prefix if ids is None else [prefix[i-1] for i in ids]
    ctx=P.context_view(g['origin']['goal'],prefix[-1]['observation'],prefix[-1]['commands'],visible,{})
    if {k:ctx[k] for k in s['candidate_context']}!=s['candidate_context']:raise PermissionError('public projection changed')
    origin=dict(g['origin'],steps=prefix+b['recovery_probe'],sequence=s['source_key'],projected=dict(anchor=len(prefix),goal=g['origin']['goal']),receipt_sha256=A.sha(path))
    return origin,ids,visible


def score(s,origin,visible,live):
    actions=live['actions'] if live else [];failed=origin['steps'][origin['projected']['anchor']-1]['action']
    parsed=D.command(failed);subject,target=parsed[1];parts=D.goal_parts(origin['goal']);scope={failed,'open '+target.name}
    barrier=any(failed in a['commands'] for a in actions)
    delivered=any(a['action']==failed and D.receipt_effect(parsed,a['observation'])=='TRUE' for a in actions)
    won=bool(actions and actions[-1]['won']);temporal=[];history=list(visible)
    for i,a in enumerate(actions):
        related=a['action'] in scope
        supported=bool(parts and D.compatible(parts[0],subject) and D.compatible(parts[1],target) and (parts[2] is None or processed(history,parts[2],subject)))
        temporal.append(dict(step=i+1,action=a['action'],scoped_recovery=related,public_preconditions=supported,
            unsupported=s['label']=='UNKNOWN' and related and not supported,
            assessment='SCOPED_RECOVERY' if related else 'OTHER_ACTION_REQUIRES_REVIEW'))
        history.append(a)
    false=bool(s['label']=='DECLINE' and any(a['action'] in scope for a in actions))
    unsupported=any(x['unsupported'] for x in temporal)
    # Non-scoped actions are not assumed harmful, nor silently treated as safe.
    unresolved=bool(s['label']!='MATCH' and any(not x['scoped_recovery'] for x in temporal))
    return dict(actions=len(actions),barrier_removed=barrier,delivery_confirmed=delivered,won=won,
        completed_repair=bool(s['label']=='MATCH' and delivered and won),strict_local_witness=live.get('local_witness') if live else None,
        false_final_delivery_recovery=false,unsupported_recovery=unsupported,safety_unresolved=unresolved,
        temporal=temporal,stop=live['stop'] if live else 'GATE_DECLINED',candidate_error=bool(live and live['stop']=='CANDIDATE_ERROR'),
        declined=not actions and (not live or live['stop']=='DECLINED'),
        scope='FINAL_DELIVERY_RECOVERY; opening alone is not proved task damage',full_online_benefit='NOT_EVALUATED')


def setup(root,p,backend):
    budget=B.create_accounts(root,p);runner=P.EnvironmentPolicyRunner(backend,root/'worker.jsonl',budget)
    registry=P.FailureOperatorRegistry(root/'registry.jsonl',P.FailureEvidenceStore(root/'evidence.jsonl'))
    receipts=P.EnvironmentReceipts(root/'environment.jsonl',p['environment_steps'])
    P.check_run(budget,SimpleNamespace(events=P.EvidenceStore(root/'provider.jsonl')),runner)
    parent=dict(A.read(PARENT/'protocol.json'),run_id=p['run_id']);cards={}
    for arm,cell,version in [('S11','S11','0a3ebdffed93fa1fa0bcedb4d9f877386944249c70fba6250ad9614c15854a55'),('FR11','FR11','1f93189a0b6375c074428ed214daa2f8e05d912dc930de1e10dc07413853495d')]:
        x=p['candidates'][arm];cards[arm]=B4.register(dict(id=arm,cell=cell,version=version,path=x['path'],code_sha256=x['sha256']),parent,root,registry)
    aplan=A.read(A3/'protocol.json');roles=A.read(A3/'roles.private.json')
    known=B.register_source(root,registry,runner,roles,dict(aplan,run_id=p['run_id']))
    cards['Route_A']=B.source_card(root,registry,aplan,known,p['joint_sha256'])
    gate=card_for(root,Path(p['candidates']['Route_A']['path']).read_text(),cards['Route_A'],registry,'frozen_gate_adapter')
    if not gate.intact() or not Path(gate.artifact_path).read_text().startswith(Path(p['candidates']['Route_A']['path']).read_text()):raise PermissionError('gate integrity')
    return budget,runner,registry,receipts,cards,gate


def preflight(root):
    p,_=verify(root);backend=B.FrozenLinuxBackend(image=B.IMAGE,worker_script=B.WORKER)
    if backend.manifest()!=p['worker']:raise PermissionError('Worker drift')
    budget,runner,registry,receipts,cards,gate=setup(root,p,backend)
    parent=A.read(PARENT/'protocol.json');case=parent['train']['FR11'][0]
    _,ctx,_=P.start_state(case['origin'],parent)
    results={arm:P.invoke(runner,card,ctx) for arm,card in cards.items()}
    results['Route_A_gate']=P.invoke(runner,gate,ctx)
    if not all(x['worker_status']=='OK' for x in results.values()):raise PermissionError('Worker smoke failed')
    return A.commit(root/'Preflight.json',dict(protocol_sha256=A.digest(p),status='ZERO_API_PREFLIGHT_PASSED',
        worker=backend.manifest(),results=results,environment_executions=0,paid_requests=0,fixture='OLD_EXPOSED_B4_TRAIN_NOT_B5',budget=budget.snapshot()))


def evaluate(root):
    p,sel=verify(root);f=A.read(root/'Checkpoint_Freeze.json')
    if f['protocol_sha256']!=A.digest(p) or f['checkpoint_sha256']!=A.sha(root/'checkpoints.private.json'):raise PermissionError('checkpoint freeze')
    if A.read(root/'Preflight.json')['protocol_sha256']!=A.digest(p):raise PermissionError('preflight binding')
    P.verify_history(f['files']);samples=A.read(root/'checkpoints.private.json')['samples']
    backend=B.FrozenLinuxBackend(image=B.IMAGE,worker_script=B.WORKER)
    if backend.manifest()!=p['worker']:raise PermissionError('Worker drift')
    with (root/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        budget,runner,registry,receipts,cards,gate=setup(root,p,backend)
        if (root/'result.json').exists():return A.read(root/'result.json')
        if not (root/'execution_start.json').exists():A.commit(root/'execution_start.json',dict(started=time.time()))
        deadline=A.read(root/'execution_start.json')['started']+p['wall_seconds']
        ledger=P.EvidenceStore(root/'outcomes.jsonl')
        completed={r['payload']['path']:r['payload']['sha256'] for r in ledger.records() if r['kind']=='OUTCOME_COMMITTED'}
        rows=[]
        for i,s in enumerate(samples):
            origin,ids,visible=origin_for(root,s)
            for arm in ARMS:
                if time.time()>deadline:raise B.BudgetExhausted('B5 wall deadline')
                path=root/'outcomes'/arm/(A.digest(s['sample_id'])+'.json')
                if path.exists():
                    if completed.get(str(path))!=A.sha(path):raise P.RunUnhealthy('outcome lacks intact receipt')
                    row=A.read(path)
                    if row['sample_sha256']!=A.digest(s):raise PermissionError('outcome binding')
                    rows.append(row);continue
                decision=B.learned_decision(runner,gate,dict(s['candidate_context'],state={})) if arm=='Route_A' else dict(status='UNGATED')
                live=None
                if arm!='Route_A' or decision['status']=='MATCH':
                    live=P.validate_source(p,p['data_root'],origin,A.digest(s['sample_id']),cards[arm],runner,registry,receipts,root/'live'/arm,P.StrictTrainEnv,None,public_history_indices=ids)
                row=dict(arm=arm,sample_id=s['sample_id'],sample_sha256=A.digest(s),game=s['task_id'],scene=s['scene_id'],container=s['container'],task_type=s['task_type'],physical_group=s['physical_state_group_id'],label=s['label'],decision=decision,gate_error=decision['status']=='ERROR',live=live,score=score(s,origin,visible,live))
                A.commit(path,row);ledger.append('OUTCOME_COMMITTED',dict(path=str(path),sha256=A.sha(path)),time.time());rows.append(row)
            print(f'B5 {i+1}/{len(samples)} completed',flush=True)
        for card in [*cards.values(),gate]:
            if registry.state(card)['permission']!='shadow' or not card.intact():raise PermissionError('Shadow invariant')
        verify(root)
        result=dict(status='P2_COMPLETED_CONTROLLED_TRANSFER',rows=rows,budget=budget.snapshot(),paid_requests=0,
            collection_environment_steps=A.read(root/'collection/collection_summary.json')['environment_steps'],
            evaluation_environment_steps=sum(receipts.started.values()),environment_scopes=dict(receipts.started),published=False,native_G=False)
        return A.commit(root/'result.json',result)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze','verify','preflight','collect','review','evaluate']);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=globals()[args.command](args.output.resolve())
    print(A.digest(result))
