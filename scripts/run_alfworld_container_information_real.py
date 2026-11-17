"""Route B3 authorized transport binding; frozen learning rules are unchanged."""
import argparse,fcntl,time,json
from pathlib import Path
from types import SimpleNamespace
import run_alfworld_container_information as E
from failure_evo.network_transport import DEFAULT_POLICY
from failure_evo.model_api import configured_api_key
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.run_health import assert_run_healthy
from alfworld_.recovery_acquisition import stage_request
from alfworld_.python_recovery_feedback import parse_delivery
from alfworld_.route_b_compact_projection import encode
from failure_evo.wire_input_policy import check_wire
P=E.P;B=E.B;M=E.M;POLICY=E.POLICY;wire=E.wire;old_wire=E.old_wire;assessment=E.assessment
PRE=E.ROOT/'runs/alfworld_route_b3_container_preparation_20261116_03'
EXPECTED='15372aaa8cd924572a4b05c4daba270c8c9624d1cad747dce7343d2cf80f363b'
AUTH_TEXT='授权 Route B3 真实生成，上限12美元，按冻结协议运行 S/F/FR 三组及开发验证，暂不运行新游戏和原生 G 对照。'

def freeze(out,mock=False):
    base=P.read(PRE/'protocol.json')
    if P.fingerprint(base)!=EXPECTED:raise PermissionError('preparation protocol drift')
    P.verify_history(base['historical_sha256'])
    accepted=P.read(PRE/'Preparation_Acceptance.json')
    for path,h in accepted['files'].items():
        if P.sha(E.ROOT/path)!=h:raise PermissionError('acceptance binding drift: '+path)
    out.mkdir(mode=0o700,parents=True,exist_ok=True)
    source_paths=[Path(__file__),Path(E.__file__),Path(M.__file__),Path(P.__file__),
        E.ROOT/'FlowEvo/src/alfworld_/recovery_acquisition.py',
        E.ROOT/'FlowEvo/src/failure_evo/autonomous_generation.py',
        E.ROOT/'FlowEvo/src/failure_evo/network_transport.py']
    plan=dict(base,run_id=out.name,scope='GENERATION_AND_EXPOSED_DEVELOPMENT_ONLY',
        preparation_protocol_sha256=EXPECTED,network_policy=DEFAULT_POLICY,
        paid_authorization=not mock,mock=mock,real_binding_version='b3-authorized-transport-v1',
        runtime_hashes={str(f.resolve()):P.sha(f) for f in source_paths})
    P.commit(out/'protocol.json',plan)
    P.commit(out/'authorization.json',dict(instruction=AUTH_TEXT if not mock else 'MOCK_ONLY',
        protocol_sha256=P.fingerprint(plan),max_cost_microusd=12000000,paid_api_authorized=not mock,
        scope=plan['scope'],new_games_authorized=False,native_G_authorized=False))
    return plan

def account(out,p):
    return PersistentBudget(out/'budget.jsonl',run_id=p['run_id']+':'+out.name,
        protocol_hash=P.fingerprint(p),max_calls=p['max_calls'],max_tokens=p['max_tokens'],
        max_tools=p['worker_calls'],max_cost_microusd=p['max_cost_microusd'],
        token_rate_microusd_per_million=p['reservation_rate'],tool_cost_upper_microusd=0,
        max_tool_milliseconds=p['worker_calls']*15000,tool_milliseconds_upper=15000,wall_seconds=86400)

def run(out,*,mock_sender=None,evaluate=None,fault=None):
    p=freeze(out,mock=mock_sender is not None)
    preparation=PRE
    evaluate=evaluate or real_evaluator
    if mock_sender is None and not configured_api_key():raise PermissionError("credential unavailable")
    out.mkdir(mode=0o700,parents=True,exist_ok=True);P.commit(out/'protocol.json',p)
    b=account(out,dict(p,max_calls=0,max_tokens=0,max_cost_microusd=0))
    accounts={a:account(out/a,dict(p,max_calls=12,max_tokens=p['max_tokens']//3,max_cost_microusd=p['max_cost_microusd']//3,worker_calls=0)) for a in M.ARMS}
    providers=[SimpleNamespace(events=P.EvidenceStore(out/a/'provider.jsonl')) for a in M.ARMS]
    def healthy():assert_run_healthy(budgets=[b,*accounts.values()],providers=providers,network_policy=p['network_policy'])
    def request(name,phase,payload,parent=None):
        healthy();w=wire(out,payload,phase);P.commit(out/name/'wire.private.json',w)
        arm=name.split('_')[0]
        print(f'{name}: request or settled replay',flush=True)
        barm=accounts[arm]
        auth=dict(run_id=barm.config['run_id'],protocol_hash=barm.config['protocol_hash'],model=p['model'],protocol=M.VERSION,max_cost_microusd=barm.config['max_cost_microusd'],paid_api_authorized=True)
        response=stage_request(out/arm,name,'analyze',encode(payload),parse_delivery,barm,sender=mock_sender,authorization=None if mock_sender is not None else auth,network_policy=None if mock_sender is not None else p['network_policy'],
            protocol=M.VERSION,analysis_prompt=M.PROMPTS[phase],temperature=p['temperature'],input_policy=POLICY)
        if fault:fault('after_response',name)
        row=assessment(out,name,response,parent)
        print(f'{name}: {row["status"]}',flush=True)
        return row
    def execute(row):
        if row['status']!='STATIC_PASS':return None
        path=out/row['id']/'evaluation.private.json'
        if path.exists():value=P.read(path)
        else:
            print(f'{row["id"]}: development execution',flush=True)
            value=evaluate(row,p,b,out);P.commit(path,value)
            print(f'{row["id"]}: {value["metrics"]}',flush=True)
        if value['candidate_version']!=row['version'] or value['code_sha256']!=row['code_sha256']:
            raise PermissionError('foreign evaluator/version')
        return value
    with (out/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        parents=[]
        for arm in M.ARMS:
            for i in range(4):
                name=f'{arm}_{i}';attempt=request(name+'/initial','initial',P.read(preparation/'inputs'/f'{arm}.private.json'))
                lineage=dict(id=name,arm=arm,attempts=[attempt],model_tokens=attempt['tokens'])
                if attempt['status'] in ('STATIC_REJECTED','DELIVERY_REJECTED'):
                    payload=dict(parent_version=attempt['version'],previous_source_or_delivery=Path(attempt['path']).read_text() if attempt['path'] else attempt['raw_content'],engineering_diagnostics=attempt['diagnostics'])
                    try:wire(out,payload,'engineering')
                    except ValueError:lineage['engineering_not_sent']='INPUT_LIMIT'
                    else:
                        attempt=request(name+'/engineering','engineering',payload,attempt['version']);lineage['attempts'].append(attempt);lineage['model_tokens']+=attempt['tokens']
                lineage.update(current=attempt,version=attempt['version']);parents.append(lineage)
        # This barrier precedes every environment evaluation and behavior call.
        P.commit(out/'initials_complete.json',[x['current']['version'] for x in parents])
        for x in parents:x['initial_evaluation']=execute(x['current'])
        for x in parents:
            row=x['current'];evaluation=x['initial_evaluation']
            if evaluation:
                m=evaluation['metrics']
                complete=m['repairs']==len(p['cases']) and m['errors']==0 and m['controls_declined']==len(p['controls'])
                if not complete:
                    def fits(payload):
                        try:check_wire(old_wire(out,payload,M.PROMPTS['behavior']),POLICY);return True
                        except ValueError:return False
                    try:payload=M.behavior_payload(Path(row['path']).read_text(),row['version'],p['cases'],evaluation,fits)
                    except ValueError:x['behavior_not_sent']='INPUT_LIMIT'
                    else:
                        updated=request(x['id']+'/behavior','behavior',payload,row['version'])
                        x['attempts'].append(updated);x['model_tokens']+=updated['tokens'];x['current']=updated;x['version']=updated['version']
                else:x['behavior_not_sent']='FROZEN_COMPLETION_REACHED'
        for x in parents:
            x['evaluation']=execute(x['current'])
            # Failed behavioral delivery is a failed final attempt; no hidden fourth request.
            P.commit(out/'lineages'/(x['id']+'.json'),x)
        healthy()
        raw=[r['payload']['response'] for pr in providers for r in pr.events.records() if r['kind']=='RAW_RESPONSE']
        result=dict(status='MOCK_ENGINEERING_ONLY' if mock_sender is not None else 'COMPLETED_GENERATION_AND_DEVELOPMENT',paid_requests=0 if mock_sender is not None else len(raw),mock=mock_sender is not None,lineages=parents,
            selection={a:M.choose(M.evaluated_versions([x for x in parents if x['arm']==a])) for a in M.ARMS},
            budget=dict(worker=b.snapshot(),models={a:v.snapshot() for a,v in accounts.items()}))
        P.verify_history(p['historical_sha256'])
        P.commit(out/'result.json',result);return result

def real_evaluator(row,p,budget,out):
    """Existing source execution + strict B2 scoring; only containers and controls."""
    backend=B.B.FrozenLinuxBackend(image=B.IMAGE,worker_script=B.WORKER)
    if backend.manifest()!=p['worker'] or P.environment_manifest(p['data_root'])!=p['environment']:raise PermissionError('runtime drift')
    runner=P.EnvironmentPolicyRunner(backend,out/'worker.jsonl',budget)
    registry=P.FailureOperatorRegistry(out/'registry.jsonl',P.FailureEvidenceStore(out/'evidence.jsonl'))
    _,arms,host=B.load_source(B.SOURCE);sequences={c['origin']['sequence'] for c in p['cases']}
    events=[e for e in arms['B'] if host[e['evidence_id']]['sequence'] in sequences]
    ids=B.import_source_events('B3_DEVELOPMENT_EVALUATION',events,host,out,registry.evidence,p['run_id'])
    known=registry.evidence.visible(time.time())
    card=B.FailureOperator(row['id'],row['version'],row['path'],row['code_sha256'],
        B.Fingerprint('full_library','B3-development',p['model'],P.fingerprint(p['worker']),M.VERSION),
        'SEE_FROZEN_ARM_INPUT_FOR_LEARNING_PROVENANCE',tuple(ids.values()),tuple(sorted({e['provenance_group_id'] for e in known})),
        hooks=(B.ENVIRONMENT_HOOK,),stages=('environment',),allowed_actions=('environment_action',),operator_kind='environment_policy')
    if not registry._rows(card):registry.register(card,time.time())
    receipts=P.EnvironmentReceipts(out/'environment.jsonl',p['environment_steps']);P.check_run(budget,SimpleNamespace(events=P.EvidenceStore(out/'provider.jsonl')),runner)
    sources=[];controls=[];m=dict(repairs=0,deliveries=0,won=0,errors=0,incompatible=0,unsupported=0,actions=0,controls_declined=0,control_relevance_unverified=0)
    for case in p['cases']+p['controls']:
        result=P.validate_source(p,p['data_root'],case['origin'],case['id'],card,runner,registry,receipts,
            out/row['id']/'executions',P.StrictTrainEnv,None,public_history_indices=case['ids'])
        score=B.score(case,result);m['errors']+=score['candidate_error'];m['actions']+=len(result['actions'])
        o=case['origin'];failed=o['steps'][o['projected']['anchor']-1]['action']
        delivery=any(a['action']==failed and P.receipt_truth(P.parse_command(a['action']),a['observation'])=='TRUE' for a in result['actions'])
        if case['label']=='MATCH':
            m['repairs']+=bool(score['local_repair']);m['won']+=score['won'];m['deliveries']+=delivery;sources.append(result)
        else:
            scoped={failed,'open '+failed.rsplit(' to ',1)[-1]}
            first=result['actions'][0]['action'] if result['actions'] else None
            # UNKNOWN is a label on the initial public state, never a permanent
            # label on a later state after active information gathering.
            entry_unsupported=case['label']=='UNKNOWN' and first in scoped
            later_unreviewed=case['label']=='UNKNOWN' and bool(score['scoped_unsupported_action']) and not entry_unsupported
            m['incompatible']+=bool(score['scoped_false_applicability']);m['unsupported']+=entry_unsupported
            m['controls_declined']+=score['declined'];m['control_relevance_unverified']+=later_unreviewed or score['unrelated_action_intervention_unverified']
            controls.append(dict(score=score,entry_unsupported=entry_unsupported,later_state_requires_review=later_unreviewed,result=result))
    return dict(candidate_version=row['version'],code_sha256=row['code_sha256'],sources=sources,controls=controls,metrics=m,permission=registry.state(card)['permission'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--authorized-usd',type=float,required=True)
    parser.add_argument('--preflight-only',action='store_true')
    a=parser.parse_args()
    if a.authorized_usd!=12:parser.error('current $12 authorization required')
    out=a.output.resolve()
    try:
        if a.preflight_only:
            p=freeze(out)
            if not configured_api_key():raise PermissionError('credential unavailable')
            backend=B.B.FrozenLinuxBackend(image=B.IMAGE,worker_script=B.WORKER)
            if backend.manifest()!=p['worker'] or P.environment_manifest(p['data_root'])!=p['environment']:raise PermissionError('runtime drift')
            print(P.canonical(dict(status='READY_AUTHORIZED',protocol_sha256=P.fingerprint(p),paid_requests=0,max_cost_usd=12)))
        else:
            r=run(out);print(P.canonical(dict(status=r['status'],paid_requests=r['paid_requests'],selection=r['selection'])))
    except BaseException as exc:
        if out.exists():
            P.commit(out/('STOP_'+str(time.time_ns())+'.json'),dict(error_type=type(exc).__name__,reason=str(exc),at=time.time()))
        raise
