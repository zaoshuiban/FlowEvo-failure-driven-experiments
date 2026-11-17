"""B4 injected-model scheduler and exposed-source replay. Paid CLI intentionally absent."""
import argparse,fcntl,time
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.run_health import assert_run_healthy
from failure_evo.contracts import PublicFeedback
from alfworld_.recovery_acquisition import stage_request
from alfworld_.python_recovery_feedback import parse_delivery
from alfworld_.route_b_compact_projection import encode
import prepare_alfworld_container_b4 as D
E=D.E;P=D.P;M=D.M

def account(out,p,cell=None):
    return PersistentBudget(out/'budget.jsonl',run_id='MOCK:'+p['run_id']+':'+(cell or 'worker'),protocol_hash=P.fingerprint(p),
        max_calls=9 if cell else 0,max_tokens=p['max_tokens']//6 if cell else 0,max_tools=0 if cell else p['worker_calls'],
        max_cost_microusd=p['max_cost_microusd']//6 if cell else 0,token_rate_microusd_per_million=p['reservation_rate'],
        tool_cost_upper_microusd=0,max_tool_milliseconds=0 if cell else p['worker_calls']*15000,tool_milliseconds_upper=15000,wall_seconds=p['wall_seconds'])

def run_mock(preparation,out,*,sender,evaluate,fault=None):
    if sender is None:raise PermissionError('B4 has no paid authorization or real sender')
    p=P.read(preparation/'protocol.json');P.verify_history(p['historical_sha256'])
    out.mkdir(mode=0o700,parents=True,exist_ok=True);P.commit(out/'protocol.json',p)
    models={c:account(out/c,p,c) for c in M.CELLS};tools=account(out,p)
    providers=[SimpleNamespace(events=P.EvidenceStore(out/c/'provider.jsonl')) for c in M.CELLS]
    def healthy():assert_run_healthy(budgets=[tools,*models.values()],providers=providers)
    def request(cell,i,phase,payload,parent=None):
        healthy();name=f'{cell}_{i}/{phase}';D.wire(out,payload,phase)
        P.commit(out/name/'wire.private.json',D.wire(out,payload,phase))
        result=stage_request(out/cell,name,'analyze',encode(payload),parse_delivery,models[cell],sender=sender,
            protocol=M.VERSION,analysis_prompt=M.PROMPTS[phase],temperature=p['temperature'],input_policy=p['input_policy'])
        if fault:fault('after_response',name)
        row=E.assessment(out,name,result,parent);row.update(cell=cell,index=i)
        return row
    def execute(row,cases,role):
        healthy();file=out/row['id']/(role.lower()+'_evaluation.private.json')
        if file.exists():ev=P.read(file)
        else:ev=evaluate(row,p,cases,role,tools,out);P.commit(file,ev)
        if (ev['candidate_version']!=row['version'] or ev['code_sha256']!=row['code_sha256'] or ev['role']!=role
            or ev['case_ids']!=[c['id'] for c in cases]):raise PermissionError('evaluation role/version/source mismatch')
        return ev
    with (out/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);healthy();lineages=[]
        for wave in (range(2),range(2,4)):
            for cell in M.CELLS:
                for i in wave:
                    row=request(cell,i,'initial',P.read(preparation/'inputs'/f'{cell}.private.json'))
                    lineages.append(dict(id=f'{cell}_{i}',cell=cell,index=i,attempts=[row],current=row,lineage_tokens=row['tokens']))
            if len(lineages)==12:
                stop=M.early_stop([x['current'] for x in lineages]);P.commit(out/'first_wave.json',dict(early_stop=stop,versions=[x['current']['version'] for x in lineages]))
                if stop:
                    result=dict(status='MOCK_EARLY_STOP_ALL_ABSTAIN',paid_requests=0,lineages=lineages,selection={c:M.select_validation([]) for c in M.CELLS})
                    P.commit(out/'result.json',result);return result
        # Engineering after ALL initials; no behavior result available yet.
        for x in lineages:
            row=x['current']
            if row['status'] in ('STATIC_REJECTED','DELIVERY_REJECTED'):
                payload=dict(parent_version=row['version'],previous_source_or_delivery=Path(row['path']).read_text() if row['path'] else row['raw_content'],engineering_diagnostics=row['diagnostics'])
                try:D.wire(out,payload,'engineering')
                except ValueError:x['engineering_not_sent']='INPUT_LIMIT'
                else:
                    row=request(x['cell'],x['index'],'engineering',payload,row['version']);x['attempts'].append(row);x['current']=row;x['lineage_tokens']+=row['tokens']
        P.commit(out/'initials_engineering_complete.json',[x['current']['version'] for x in lineages])
        for x in lineages:
            row=x['current']
            if row['status']=='STATIC_PASS':row['train_evaluation']=execute(row,p['train'][x['cell']],'TRAIN')
        for cell in M.CELLS:
            parent=M.behavior_parent([x['current'] for x in lineages if x['cell']==cell],len(p['train'][cell]))
            P.commit(out/'behavior_choices'/f'{cell}.json',dict(parent=parent['version'] if parent else None))
            if parent is None:continue
            x=next(x for x in lineages if x['current']['version']==parent['version'])
            def fits(encoded):
                from failure_evo.wire_input_policy import check_wire
                # behavior_payload already encodes its trial; avoid double encoding.
                try:
                    from alfworld_.route_b_compact_projection import decode
                    check_wire(D.wire(out,decode(encoded),'behavior'),p['input_policy']);return True
                except ValueError:return False
            try:payload=M.behavior_payload(Path(parent['path']).read_text(),parent['version'],p['train'][cell],parent['train_evaluation'],fits)
            except ValueError:x['behavior_not_sent']='INPUT_LIMIT';continue
            revised=request(cell,x['index'],'behavior',payload,parent['version']);x['attempts'].append(revised);x['lineage_tokens']+=revised['tokens'];x['current']=revised
            if revised['status']=='STATIC_PASS':revised['train_evaluation']=execute(revised,p['train'][cell],'TRAIN')
        P.commit(out/'all_learning_complete.json',[x['current']['version'] for x in lineages])
        versions=[]
        # Common validation only AFTER all model calls, never into feedback.
        for x in lineages:
            for row in x['attempts']:
                if 'train_evaluation' not in row:continue
                row['validation_evaluation']=execute(row,p['validation'],'TRAIN_VALIDATION');row['lineage_tokens']=x['lineage_tokens'];versions.append(row)
            P.commit(out/'lineages'/f"{x['id']}.json",x)
        healthy();P.verify_history(p['historical_sha256'])
        result=dict(status='MOCK_ENGINEERING_ONLY',paid_requests=0,lineages=lineages,
            selection={c:M.select_validation([v for v in versions if v['cell']==c]) for c in M.CELLS},
            budget=dict(worker=tools.snapshot(),models={c:b.snapshot() for c,b in models.items()}))
        P.commit(out/'result.json',result);return result

def register(row,p,out,registry):
    known={}
    for c in p['train'][row['cell']]:
        prefix,ctx,h=P.start_state(c['origin'],p)
        event=registry.evidence.record(stream_id=p['run_id'],task_id=c['id'],family_id=c['source_provenance'],stage='environment',code=P.canonical(ctx),
            feedback=PublicFeedback('WRONG_ANSWER','Recorded unsuccessful environment action; cause unverified; '+c['source_provenance'],
                (P.canonical(dict(expected='progress',actual=prefix[-1]['observation'],action=prefix[-1]['action'])),)),
            observed_at=0,available_from=0,finish_reason='stop',parent_sha256=c['source_hash'],provenance_group_id='game:'+M.identity(c))
        if event is None:raise PermissionError('trusted public failure receipt required')
        known[event['event_id']]=event
    card=E.B.FailureOperator(row['id'],row['version'],row['path'],row['code_sha256'],
        E.B.Fingerprint('full_library','B4-exposed-development','MOCK_ZERO_API',P.fingerprint(p['worker']),M.VERSION),
        'ONLY_OWN_CELL_TRAIN_EVIDENCE',tuple(known),tuple(sorted({e['provenance_group_id'] for e in known.values()})),
        hooks=(E.B.ENVIRONMENT_HOOK,),stages=('environment',),allowed_actions=('environment_action',),operator_kind='environment_policy')
    if not registry._rows(card):registry.register(card,time.time())
    if registry.state(card)['permission']!='shadow':raise PermissionError('unverified permission')
    return card

def real_evaluate(row,p,cases,role,budget,out):
    if cases!=(p['train'][row['cell']] if role=='TRAIN' else p['validation']):raise PermissionError('role leakage')
    backend=E.B.B.FrozenLinuxBackend(image=E.B.IMAGE,worker_script=E.B.WORKER)
    if backend.manifest()!=p['worker'] or P.environment_manifest(p['data_root'])!=p['environment']:raise PermissionError('runtime drift')
    runner=P.EnvironmentPolicyRunner(backend,out/'worker.jsonl',budget)
    registry=P.FailureOperatorRegistry(out/'registry.jsonl',P.FailureEvidenceStore(out/'evidence.jsonl'))
    card=register(row,p,out,registry);receipts=P.EnvironmentReceipts(out/'environment.jsonl',p['environment_steps'])
    P.check_run(budget,SimpleNamespace(events=P.EvidenceStore(out/'provider.jsonl')),runner)
    sources=[];controls=[];m=dict(repairs=0,deliveries=0,won=0,errors=0,incompatible=0,unsupported=0,actions=0,controls_declined=0,control_relevance_unverified=0,worker_ok=0,worker_calls=0)
    for c in cases:
        result=P.validate_source(p,p['data_root'],c['origin'],c['id'],card,runner,registry,receipts,out/row['id']/role.lower(),P.StrictTrainEnv,None,public_history_indices=c['ids'])
        score=E.B.score(c,result);m['errors']+=score['candidate_error'];m['actions']+=len(result['actions'])
        m['worker_ok']+=sum(d['worker_status']=='OK' for d in result['decisions']);m['worker_calls']+=len(result['decisions'])
        failed=c['origin']['steps'][c['origin']['projected']['anchor']-1]['action']
        if c['label']=='MATCH':
            m['repairs']+=bool(score['local_repair']);m['won']+=score['won'];m['deliveries']+=any(a['action']==failed and P.receipt_truth(P.parse_command(a['action']),a['observation'])=='TRUE' for a in result['actions']);sources.append(result)
        else:
            scoped={failed,'open '+failed.rsplit(' to ',1)[-1]};first=result['actions'][0]['action'] if result['actions'] else None
            unsupported=c['label']=='UNKNOWN' and first in scoped
            later=c['label']=='UNKNOWN' and bool(score['scoped_unsupported_action']) and not unsupported
            m['incompatible']+=bool(score['scoped_false_applicability']);m['unsupported']+=unsupported;m['controls_declined']+=score['declined']
            m['control_relevance_unverified']+=later or score['unrelated_action_intervention_unverified']
            controls.append(dict(score=score,entry_unsupported=unsupported,later_state_requires_review=later,result=result))
    return dict(role=role,case_ids=[c['id'] for c in cases],candidate_version=row['version'],code_sha256=row['code_sha256'],sources=sources,controls=controls,metrics=m,permission=registry.state(card)['permission'])

def replay(preparation,out):
    p=P.read(preparation/'protocol.json');P.verify_history(p['historical_sha256']);out.mkdir(mode=0o700,parents=True,exist_ok=True)
    P.commit(out/'protocol.json',dict(parent_sha256=P.fingerprint(p),max_environment_steps=p['preflight_environment_steps'],scope='EXPOSED_REPLAY_ZERO_API'))
    receipts=P.EnvironmentReceipts(out/'environment.jsonl',p['preflight_environment_steps'])
    cases=p['train']['FR22']+p['validation']
    for c in cases:
        path=out/(c['id']+'.json');o=c['origin'];branch='B4_REPLAY:'+c['id']
        if branch in receipts.committed:
            if P.sha(path)!=receipts.committed[branch]:raise PermissionError('replay receipt drift')
            continue
        if branch in receipts.started_branches:raise RuntimeError('unfinished replay requires audit; no blind replay')
        env=P.StrictTrainEnv(p['data_root'],max_steps=50)
        try:
            env.initialize(frozen_game_files=[str(P.verify_source_game(p['data_root'],o))]);P._reset(env,o)
            for s in o['steps']:receipts.step(env,s['action'],branch=branch,scope='exposed_original',expected=s)
            receipts.finish(branch,path,dict(case=c['id'],game=M.identity(c),steps=len(o['steps']),replay_verified=True,won=o['steps'][-1]['won'],source_provenance=c['source_provenance']))
        finally:env.close()
        print('verified',c['id'],flush=True)
    P.commit(out/'result.json',dict(cases=len(cases),training=22,validation=len(p['validation']),environment_steps=dict(receipts.started),paid_requests=0,new_games=0))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['replay']);parser.add_argument('--preparation',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    replay(a.preparation.resolve(),a.output.resolve())
