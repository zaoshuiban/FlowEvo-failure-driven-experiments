"""B2 frozen exposed-state evaluation, no model calls and no candidate editing."""
import argparse,time,fcntl
from pathlib import Path
from collections import Counter
from dataclasses import replace
from types import SimpleNamespace
import run_alfworld_python_recovery_feedback as P
import run_alfworld_applicability_multicandidate as B
from alfworld_.skill_acquisition import load_source,import_source_events,local_repair_witness
from alfworld_.recovery_applicability_learning import load_dataset
from failure_evo.contracts import Fingerprint
from failure_evo.failure_registry import FailureOperator,ENVIRONMENT_HOOK
from run_alfworld_skill_acquisition import IMAGE,WORKER,create_accounts

ROOT=P.ROOT
B1=ROOT/'runs/alfworld_route_b_generation_real_20261116_01'
DATA=ROOT/'runs/alfworld_route_a_a1d_20261113_01'
SOURCE=Path.home()/'.local/share/flowevo/alfworld_full_library_online120_20261109_01'
VERSION='route-b2-exposed-frozen-v1'

def prepare(out):
    if out.exists():raise FileExistsError('new freeze required')
    source,arms,host=load_source(SOURCE);audit=P.read(B1/'read_only_audit.json');cases=[];excluded=[]
    bindings={str(B1/'read_only_audit.json'):P.sha(B1/'read_only_audit.json'),str(B1/'result.json'):P.sha(B1/'result.json')}
    for path,h in P.read(ROOT/'runs/alfworld_route_b_b01_20261116_02/source_binding.private.json').items():
        if P.sha(path)!=h:raise PermissionError('source drift')
        bindings[path]=h
    for eid,origin in sorted(host.items(),key=lambda x:x[1]['sequence']):
        if origin['projected']['anchor'] is None:
            excluded.append(dict(id=eid,sequence=origin['sequence'],reason='NO_FROZEN_NONTERMINAL_LOCAL_FAILURE_ANCHOR'));continue
        P.start_state(origin,dict(environment_type='TEXTWORLD_TRAIN',source_window=18,episode_limit=50))
        cases.append(dict(id='native_'+str(origin['sequence']),origin=origin,ids=None,label='MATCH',
            mechanism='lamp' if origin['row']['task_type']=='look_at_obj_in_light' else 'container',
            provenance='EXPOSED_NATIVE_DEVELOPMENT',physical_group=P.fingerprint([origin['row']['game_sha256'],origin['projected']['anchor']]),
            score_basis='strict historical decisive-state witness OR official won; no generic state-change credit'))
    roles=load_dataset(DATA);seen=set();selected=Counter()
    for row in sorted(roles['TRAIN'],key=lambda x:P.fingerprint(x['sample_id'])):
        if row['label'] not in ('DECLINE','UNKNOWN'):continue
        group=(row['label'],row['source_key'].split('/')[-1])
        reason=None
        try:
            dataset,origin,ids=B.source_origin(row,dict(dataset=str(DATA)))
            P.start_state(origin,dict(environment_type='TEXTWORLD_TRAIN',source_window=18,episode_limit=50))
        except (ValueError,PermissionError,KeyError) as exc:reason='INVALID_TRIGGER_OR_PROVENANCE:'+str(exc)
        if not reason and (group in seen or selected[row['label']]>=3):reason='FROZEN_MODE_DIVERSITY_CAP_3_PER_LABEL'
        if reason:excluded.append(dict(id=row['sample_id'],reason=reason));continue
        seen.add(group);selected[row['label']]+=1
        game=row['source_key'].split('/')[0];file=dataset/'games'/(game+'.private.json')
        bindings[str(file)]=P.sha(file)
        cases.append(dict(id='control_'+P.fingerprint(row['sample_id'])[:16],origin=origin,ids=ids,label=row['label'],
            mechanism='container_control',provenance='EXPOSED_A1_CONTROLLED_NOT_SPONTANEOUS',
            physical_group=row['physical_state_group_id'],review=row,
            score_basis='label scoped to failed-final-delivery recovery, other actions NOT_EVALUABLE for false applicability'))
    for file in ('dataset.json','review.private.json','train.private.json','train_model_view.private.json','train_validation.private.json','train_validation_model_view.private.json'):
        bindings[str(DATA/file)]=P.sha(DATA/file)
    candidates=[]
    for c in audit['candidate_sources']:
        path=Path(c['file']);resp=path.parent/'response.json';raw=P.read(resp)['raw_response'];proposal=P.parse_delivery(__import__('json').loads(raw['choices'][0]['message']['content']))['proposal']
        if path.read_text()!=proposal['code'] or P.sha(path)!=c['file_sha256']:raise PermissionError('model/source mismatch')
        bindings[str(path.resolve())]=P.sha(path);bindings[str(resp.resolve())]=P.sha(resp)
        candidates.append(dict(c,original_path=str(path.resolve()),response_sha256=P.fingerprint(raw),static=P.static_check_detailed(path.read_text())))
    backend=B.FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
    files=[__file__,P.__file__,B.__file__,ROOT/'FlowEvo/src/alfworld_/skill_acquisition.py',ROOT/'FlowEvo/src/alfworld_/failure_learning.py']
    bindings.update({str(Path(f).resolve()):P.sha(f) for f in files})
    out.mkdir(mode=0o700,parents=True)
    plan=dict(version=VERSION,run_id='b2:'+out.name,cases=cases,excluded=excluded,candidates=candidates,
        historical_sha256=bindings,worker=backend.manifest(),environment=P.environment_manifest(source['data_root']),
        data_root=source['data_root'],environment_type='TEXTWORLD_TRAIN',source_window=18,episode_limit=50,max_stagnant_repeats=2,
        max_calls=0,max_tokens=0,max_cost_microusd=0,worker_calls=len(cases)*5*18+20,
        environment_steps=(len(cases)*5*50+sum(x['origin']['projected']['anchor'] for x in cases)+100)*2,
        permission='SHADOW_DEVELOPMENT_ONLY',score_version='strict-witness-and-scoped-control-v1',
        global_source_pass='all frozen native MATCH states repaired, zero scoped control violations/errors; not promotion',
        evaluation_order='frozen cases then S0 S1 S2 S3 F2; stop on unresolved infrastructure')
    P.commit(out/'protocol.json',plan);return plan

def setup(out):
    p=P.read(out/'protocol.json');P.verify_history(p['historical_sha256'])
    backend=B.FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
    if backend.manifest()!=p['worker'] or P.environment_manifest(p['data_root'])!=p['environment']:raise PermissionError('runtime drift')
    budget=create_accounts(out,p);runner=P.EnvironmentPolicyRunner(backend,out/'worker.jsonl',budget)
    registry=P.FailureOperatorRegistry(out/'registry.jsonl',P.FailureEvidenceStore(out/'evidence.jsonl'))
    source,arms,host=load_source(SOURCE)
    ids=import_source_events('B2_EVALUATION_NOT_GENERATION',arms['B'],host,out,registry.evidence,p['run_id'])
    known={x['event_id']:x for x in registry.evidence.visible(time.time())};cards={}
    for c in p['candidates']:
        card=FailureOperator(c['candidate_id'],c['version'],c['original_path'],c['file_sha256'],
            Fingerprint('full_library','B2-host-scoring','deepseek-flash',P.fingerprint(p['worker']),VERSION),
            'B2_EVALUATION_CHECKPOINTS_NOT_LEARNING_SOURCES',tuple(ids.values()),tuple(sorted({v['provenance_group_id'] for v in known.values()})),
            hooks=(ENVIRONMENT_HOOK,),stages=('environment',),allowed_actions=('environment_action',),operator_kind='environment_policy')
        if not registry._rows(card):registry.register(card,time.time())
        cards[c['candidate_id']]=card
    receipts=P.EnvironmentReceipts(out/'environment.jsonl',p['environment_steps'])
    P.check_run(budget,SimpleNamespace(events=P.EvidenceStore(out/'provider.jsonl')),runner,None)
    return p,runner,registry,receipts,cards

def preflight(out):
    p,runner,registry,receipts,cards=setup(out)
    for case in p['cases']:
        path=out/'preflight'/f"{case['id']}.json"
        if path.exists():continue
        origin=case['origin'];prefix,start,h=P.start_state(origin,p)
        env=P.StrictTrainEnv(p['data_root'],max_steps=50)
        try:
            env.initialize(frozen_game_files=[str(P.verify_source_game(p['data_root'],origin))]);P._reset(env,origin)
            for step in prefix:receipts.step(env,step['action'],branch='preflight:'+case['id'],scope='preflight',expected=step)
            if prefix[-1]['observation']!='Nothing happens.' or prefix[-1]['done']:raise PermissionError('invalid trigger')
            P.commit(path,dict(state_sha256=h,prefix_steps=len(prefix),verified=True))
        finally:env.close()
        print('checkpoint verified',case['id'],flush=True)
    # Real Linux Worker fixture, never a model skill, no environment step.
    fixture=out/'preflight/fixture.py';code="def environment_operator(c):\n return {'status':'declined','state':{},'reason':'ENGINEERING_ONLY'}\n"
    if not fixture.exists():fixture.write_text(code)
    card=replace(next(iter(cards.values())),version=P.fingerprint(code),artifact_path=str(fixture),artifact_sha256=P.sha(fixture))
    context=P.start_state(p['cases'][0]['origin'],p)[1];first=runner.run(card,context);before=runner.budget.tool_calls
    assert runner.run(card,context)==first and runner.budget.tool_calls==before and first['status']=='declined'
    P.commit(out/'preflight_pass.json',dict(checkpoints=len(p['cases']),worker_smoke=True,worker_cache_no_repeat=True,
        all_candidates_unchanged=True,protocol_sha256=P.fingerprint(p)))

def score(case,result):
    o=case['origin'];a=o['projected']['anchor'];prefix=o['steps'][:a];before=prefix[-2] if a>1 else o['initial']
    witness=local_repair_witness(before,prefix[-1],o['steps'][a:],result['actions'])
    won=bool(result['actions'] and result['actions'][-1]['won'])
    actions=[x['action'] for x in result['actions']];failed=prefix[-1]['action']
    scoped=[failed]+(['open '+failed.rsplit(' to ',1)[1]] if failed.startswith('move ') and ' to ' in failed else [])
    boundary=case['label'] in ('DECLINE','UNKNOWN') and any(a in scoped for a in actions)
    relevant=('TASK_COMPLETION_VERIFIED' if won else 'LOCAL_REPAIR_WITNESS' if witness and case['label']=='MATCH' else
        'SCOPED_BOUNDARY_VIOLATION' if boundary else 'NOT_EVALUABLE')
    return dict(label=case['label'],mechanism=case['mechanism'],won=won,
        local_repair=bool(witness) if case['label']=='MATCH' else None,strict_witness=witness,
        declined=result['stop']=='DECLINED' and not actions,actual_actions=len(actions),stop=result['stop'],
        candidate_error=result['stop']=='CANDIDATE_ERROR',goal_relevance=relevant,
        scoped_false_applicability=bool(boundary) if case['label']=='DECLINE' else None,
        scoped_unsupported_action=bool(boundary) if case['label']=='UNKNOWN' else None,
        unrelated_action_intervention_unverified=bool(actions and not boundary and relevant=='NOT_EVALUABLE'),
        generic_false_intervention='NOT_EVALUABLE_WITH_FINAL_DELIVERY_ONLY_LABELS')

def run(out):
    p,runner,registry,receipts,cards=setup(out)
    assert P.read(out/'preflight_pass.json')['protocol_sha256']==P.fingerprint(p)
    assert P.read(out/'regression_pass.json')['passed']
    rows=[]
    with (out/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for case in p['cases']:
            for name,card in cards.items():
                result=P.validate_source(p,p['data_root'],case['origin'],case['id'],card,runner,registry,receipts,
                    out/'executions'/name,P.StrictTrainEnv,None,public_history_indices=case['ids'])
                scored=score(case,result);row=dict(candidate=name,checkpoint=case['id'],physical_group=case['physical_group'],
                    game_sha256=case['origin']['row']['game_sha256'],score=scored,source_receipt_sha256=P.sha(out/'executions'/name/(case['id']+'.json')))
                P.commit(out/'scores'/name/(case['id']+'.json'),row);rows.append(row)
                print(name,case['id'],scored['stop'],'repair',scored['local_repair'],'won',scored['won'],flush=True)
        P.verify_history(p['historical_sha256'])
        P.commit(out/'result.json',dict(status='COMPLETED_DEVELOPMENT_ONLY',rows=rows,budget=runner.budget.snapshot(),
            environment_steps=dict(receipts.started),T_generation_abstentions=4,paid_requests=0,independent_games=0,
            permissions={k:registry.state(v)['permission'] for k,v in cards.items()}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','preflight','run']);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();globals()[a.mode](a.output.resolve())
