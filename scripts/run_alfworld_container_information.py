"""Route B3 preparation / injected-sender acceptance. No paid CLI is exposed."""
import argparse,json,time,fcntl,subprocess
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
from alfworld_ import container_information as M
from alfworld_.route_b_compact_projection import encode
from alfworld_.recovery_acquisition import stage_request
from alfworld_.python_recovery_feedback import parse_delivery
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.run_health import assert_run_healthy
from failure_evo.wire_input_policy import check_wire
import run_alfworld_route_b_b2 as B
from prepare_alfworld_route_b_generation import POLICY,make_wire as old_wire
P=B.P;ROOT=B.ROOT
B2=ROOT/'runs/alfworld_route_b_b2_20261116_02'
CALIBRATION=ROOT/'runs/python_recovery_decline_revision_20261112_01/candidate_0/revision_02/decoded.py'
CALIBRATION_SHA='233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37'

def wire(out,payload,phase):return old_wire(out,encode(payload),M.PROMPTS[phase])

def prepare(out):
    if out.exists():raise FileExistsError('new identity required')
    p=P.read(B2/'protocol.json');P.verify_history(p['historical_sha256'])
    cases=[c for c in p['cases'] if c['mechanism']=='container'];controls=[c for c in p['cases'] if c['label']!='MATCH']
    if len(cases)!=11 or P.sha(CALIBRATION)!=CALIBRATION_SHA:raise PermissionError('known source or calibration identity')
    packets=M.packets(cases);out.mkdir(parents=True,mode=0o700)
    status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
    P.commit(out/'working_tree_start.json',dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),status=status))
    measurements={}
    for arm in M.ARMS:
        w=wire(out,packets[arm],'initial');P.commit(out/'inputs'/f'{arm}.private.json',packets[arm]);P.commit(out/'inputs'/f'{arm}.wire.private.json',w)
        measurements[arm]=check_wire(w,POLICY)
    # Complete source must fit; feedback is deterministically projected later.
    stress=dict(parent_version='a'*64,previous_source_or_delivery='x'*65536,
        engineering_diagnostics=dict(errors=['x'*2048]))
    measurements['engineering_64KiB_stress']=check_wire(wire(out,stress,'engineering'),POLICY)
    hashes=dict(p['historical_sha256'])
    for root in (B.B1,B2,ROOT/'runs/python_recovery_container_pilot_20261112_01',CALIBRATION.parents[2]):
        hashes.update({str(f.resolve()):P.sha(f) for f in root.rglob('*') if f.is_file() and f.suffix in ('.json','.jsonl','.py')})
    for f in (Path(__file__),Path(M.__file__),Path(P.__file__),ROOT/'FlowEvo/src/alfworld_/route_b_runtime.py'):
        hashes[str(f.resolve())]=P.sha(f)
    for f in (out/'inputs').glob('*'):hashes[str(f.resolve())]=P.sha(f)
    plan=dict(version=M.VERSION,run_id=out.name,model='deepseek-flash',documented_version='DeepSeek-V4.1-Flash-1017',
        thinking='disabled',temperature=0.6,output_tokens=4096,input_policy=POLICY,
        arms=list(M.ARMS),initial_per_arm=4,engineering_revisions=1,behavior_revisions=1,max_calls=36,
        max_tokens=36*(POLICY['max_input_tokens']+4096),max_cost_microusd=12000000,
        reservation_rate=1200000,price=dict(checked='2026-11-16',input_peak=0.30,output_peak=1.20,
            cache_hit_peak=0.006,url='https://api-docs.deepseek.com/quick_start/pricing/'),
        max_peak_quote_usd=36*(POLICY['max_input_tokens']*.30+4096*1.20)/1e6,
        max_uniform_reservation_usd=36*(POLICY['max_input_tokens']+4096)*1.20/1e6,
        paid_authorization=False,source_window=18,episode_limit=50,max_stagnant_repeats=2,
        data_root=p['data_root'],environment=p['environment'],worker=p['worker'],environment_type=p['environment_type'],
        cases=cases,controls=controls,worker_calls=24*13*18+30,environment_steps=24*13*50*2,
        scope='PREPARATION_AND_ZERO_API_ONLY',historical_sha256=hashes,measurements=measurements,
        development_completion='11 strict repairs, zero errors, both controls declined without action',
        behavior_projection='complete code/all starts; chronological round-robin decisions; prefix stop at wire cap; omissions recorded',
        selection='all evaluated parent/revised versions; positive repair; no runtime errors; max repairs, min scoped incompatible, unsupported, actions, full-lineage tokens, fixed version ID; no promotion',
        test_stage=dict(status='NOT_COLLECTED_NOT_AUTHORIZED',games=12,max_checkpoints=36,
            new_game_primary=True,unseen_scene_required=False,collection_env_steps=5400,
            candidate_worker_upper=3*36*18,paired_native_request_upper=4*36*18,
            raw_input_upper=65536+256,output_upper=1024,paid_authorization=False))
    P.commit(out/'protocol.json',plan)
    P.commit(out/'projection_audit.json',dict(same_R=all(s['R']==fr['R'] for s,fr in zip(packets['S']['examples'],packets['FR']['examples'])),
        same_F=all(f['F']==fr['F'] for f,fr in zip(packets['F']['examples'],packets['FR']['examples'])),
        excluded_sources=[],sources=11,fragments_contain_original_steps_only=True,paid_requests=0,
        note='R start observation/history omitted explicitly; C at pre-failure step; no synthetic continuous history'))
    return plan

def account(out,p):
    return PersistentBudget(out/'budget.jsonl',run_id='MOCK:'+out.name,protocol_hash=P.fingerprint(p),
        max_calls=p['max_calls'],max_tokens=p['max_tokens'],max_tools=p['worker_calls'],max_cost_microusd=p['max_cost_microusd'],
        token_rate_microusd_per_million=p['reservation_rate'],tool_cost_upper_microusd=0,
        max_tool_milliseconds=p['worker_calls']*15000,tool_milliseconds_upper=15000,wall_seconds=86400)

def assessment(out,name,response,parent=None):
    raw=response.get('raw_response',{});choice=raw.get('choices',[{}])[0];text=choice.get('message',{}).get('content') or ''
    code=None;diagnostic=None
    try:
        if choice.get('finish_reason')!='stop':raise ValueError('INCOMPLETE_PROVIDER_RESPONSE')
        parsed=parse_delivery(json.loads(text));proposal=parsed.get('proposal')
        if proposal is None:raise ValueError(P.canonical(parsed['schema']))
        if proposal['decision']=='ABSTAIN':status='ABSTAIN'
        else:
            code=proposal['code'];diagnostic=P.static_check_detailed(code)
            status='STATIC_PASS' if diagnostic['passed'] else 'STATIC_REJECTED'
    except (ValueError,TypeError,KeyError) as exc:
        status='DELIVERY_REJECTED';diagnostic=dict(errors=[dict(path='$',code='DELIVERY',message=str(exc))])
    version=P.fingerprint([name,P.fingerprint(raw),code,parent])
    folder=out/name;P.commit(folder/'response.json',response)
    if code:P.save_exact_source(folder/'candidate.py',code)
    row=dict(id=name,status=status,version=version,parent_version=parent,provider_finish_reason=choice.get('finish_reason'),
        response_sha256=P.fingerprint(raw),code_sha256=P.sha(folder/'candidate.py') if code else None,
        path=str(folder/'candidate.py') if code else None,diagnostics=diagnostic,raw_content=text,
        tokens=raw.get('usage',{}).get('total_tokens',0))
    P.commit(folder/'assessment.json',row);return row

def run_mock(preparation,out,*,sender,evaluate,fault=None):
    """Full scheduler with injected Mock transport. No real transport fallback."""
    if sender is None:raise PermissionError('paid execution not enabled by B3 preparation')
    p=P.read(preparation/'protocol.json');P.verify_history(p['historical_sha256'])
    out.mkdir(mode=0o700,parents=True,exist_ok=True);P.commit(out/'protocol.json',p)
    b=account(out,dict(p,max_calls=0,max_tokens=0,max_cost_microusd=0))
    accounts={a:account(out/a,dict(p,max_calls=12,max_tokens=p['max_tokens']//3,max_cost_microusd=p['max_cost_microusd']//3,worker_calls=0)) for a in M.ARMS}
    providers=[SimpleNamespace(events=P.EvidenceStore(out/a/'provider.jsonl')) for a in M.ARMS]
    def healthy():assert_run_healthy(budgets=[b,*accounts.values()],providers=providers)
    def request(name,phase,payload,parent=None):
        healthy();w=wire(out,payload,phase);P.commit(out/name/'wire.private.json',w)
        arm=name.split('_')[0]
        response=stage_request(out/arm,name,'analyze',encode(payload),parse_delivery,accounts[arm],sender=sender,
            protocol=M.VERSION,analysis_prompt=M.PROMPTS[phase],temperature=p['temperature'],input_policy=POLICY)
        if fault:fault('after_response',name)
        return assessment(out,name,response,parent)
    def execute(row):
        if row['status']!='STATIC_PASS':return None
        path=out/row['id']/'evaluation.private.json'
        if path.exists():value=P.read(path)
        else:
            value=evaluate(row,p,b,out);P.commit(path,value)
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
        result=dict(status='MOCK_ENGINEERING_ONLY',paid_requests=0,lineages=parents,
            selection={a:M.choose(M.evaluated_versions([x for x in parents if x['arm']==a])) for a in M.ARMS},
            budget=dict(worker=b.snapshot(),models={a:v.snapshot() for a,v in accounts.items()}))
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
        B.Fingerprint('full_library','B3-development','MOCK',P.fingerprint(p['worker']),M.VERSION),
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
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare']);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();print(P.canonical(prepare(a.output.resolve())['measurements']))
