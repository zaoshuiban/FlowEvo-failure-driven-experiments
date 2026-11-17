"""B4 frozen TRAIN expansion from archived real receipts; no model calls."""
import argparse,subprocess
from pathlib import Path
from collections import Counter
from copy import deepcopy
import run_alfworld_container_information as E
from alfworld_ import container_information_b4 as M
from alfworld_.recovery_acquisition import RecoveryAdapter
from alfworld_.python_recovery_feedback import parse_delivery
from alfworld_.route_b_compact_projection import encode,decode
from failure_evo.wire_input_policy import check_wire
from failure_evo.network_transport import DEFAULT_POLICY
from prepare_alfworld_route_a_training_checkpoints import protected
P=E.P;ROOT=E.ROOT
B3=ROOT/'runs/alfworld_route_b3_container_preparation_20261116_03'
B3REAL=ROOT/'runs/alfworld_route_b3_container_real_20261116_01'
A1C=ROOT/'runs/alfworld_route_a_a1c_20261113_01'
A1D=ROOT/'runs/alfworld_route_a_a1d_20261113_01'
POLICY=dict(E.POLICY,max_wire_input_bytes=524288,max_input_tokens=524544)
PROSPECTIVE=B3/'prospective_metadata/selection.private.json'

def wire(out,payload,phase):
    content=encode(payload)
    adapter=RecoveryAdapter(out/'unused_provider.jsonl',None,model='deepseek-flash',mock=True,sender=lambda _:None,
        stage='analyze',payload=content,parser=parse_delivery,protocol=M.VERSION,analysis_prompt=M.PROMPTS[phase],
        temperature=.6,max_wire_input_upper=POLICY['max_input_tokens'],wire_input_policy=POLICY)
    return adapter.preflight(dict(phase='induction',max_tokens=4096,discovery=dict(stage='analyze',payload_sha256=P.fingerprint(content))))

def checked_case(row,dataset):
    dataset,origin,ids=E.B.B.source_origin(row,dict(dataset=str(dataset)))
    name=row['source_key'].split('/')[0];file=dataset/'games'/(name+'.private.json')
    record=P.read(file);branch=next(b for b in record['branches'] if b.get('branch')==row['source_key'])
    expected=branch['prefix']+[branch['failure']]+branch['recovery_probe']
    journal=P.EvidenceStore(dataset/'collection.jsonl').records()
    actual=[x for x in journal if x['kind']=='TRANSITION' and x['payload']['branch']==branch['branch']]
    replay=[x['payload']['after'] for x in journal if x['kind']=='TRANSITION' and x['payload']['branch']==branch['branch']+'/verification']
    if (not branch['replay_verified'] or replay!=expected or [x['payload']['after'] for x in actual]!=expected
        or P.fingerprint(expected)!=branch['replay_sha256']
        or P.fingerprint([x['record_hash'] for x in actual])!=branch['execution_receipt_sha256']):raise PermissionError('unverified actual/replay receipts')
    if row['label']=='MATCH' and not expected[-1]['won']:raise PermissionError('no genuine recovery outcome')
    P.start_state(origin,dict(environment_type='TEXTWORLD_TRAIN',source_window=18,episode_limit=50))
    return dict(id='controlled_'+P.fingerprint(row['sample_id'])[:16],origin=origin,ids=ids,label=row['label'],mechanism='container',
        source_provenance='CONTROLLED_INTERVENTION',provenance='EXPOSED_A1_CONTROLLED',
        physical_group=row['physical_state_group_id'],source_row=row,
        source_file=str(file),source_hash=P.sha(file),replay_verification=dict(verified=True,sha256=branch['replay_sha256'],journal=str(dataset/'collection.jsonl')),
        role=row['role'],score_basis='existing strict witness or won; scoped negative/unknown labels')

def disjoint(training,validation,test):
    for key in ('game_sha256','trajectory_sha256','group'):
        a={c['origin']['row'][key] for c in training};b={c['origin']['row'][key] for c in validation};t={r['task'][key] for r in test}
        if a&b or a&t or b&t:raise PermissionError('role overlap: '+key)
    if {c['physical_group'] for c in training}&{c['physical_group'] for c in validation}:raise PermissionError('physical overlap')

def prepare(out):
    if out.exists():raise FileExistsError('immutable new preparation ID required')
    old=P.read(B3/'protocol.json');P.verify_history(old['historical_sha256'])
    natural=[dict(deepcopy(c),source_provenance='NATURAL_AGENT_FAILURE',role='TRAIN',source_hash=c['origin']['receipt_sha256'],
        replay_verification=dict(verified=True,source='B3 archived exact replay')) for c in old['cases']]
    if len(natural)!=11:raise PermissionError('old natural cohort changed')
    protection=protected(Path.home()/'.local/share/flowevo')
    future=P.read(PROSPECTIVE)['tasks']
    blocked={k:set(protection[v])|{r['task'][k] for r in future} for k,v in [('game_sha256','games'),('trajectory_sha256','trajectories'),('group','groups')]}
    pool=[];excluded=[]
    train=E.B.load_dataset(A1C)['TRAIN']
    for row in sorted(train,key=lambda x:x['sample_id']):
        if row['label']!='MATCH' or not row['public_history_scope'].get('complete') or not row['source_key'].endswith('/READY'):continue
        c=checked_case(row,A1C);r=c['origin']['row']
        reason=[k for k in blocked if r[k] in blocked[k] or r[k] in {x['origin']['row'][k] for x in natural}]
        if reason:excluded.append(dict(id=c['id'],reason='PROTECTED_OR_OLD_IDENTITY',fields=reason));continue
        pool.append(c)
    new=M.diversity(pool,11,'B4_NEW_TRAIN_V1')
    d22=natural+new
    for i,c in enumerate(d22,1):c['model_ref']=f'source_{i:02}'
    d11=M.diversity(natural,6,'B4_D11_NATURAL_V1')+M.diversity(new,5,'B4_D11_CONTROLLED_V1')
    d11=[c for c in d22 if c['id'] in {x['id'] for x in d11}]
    if len({M.identity(c) for c in d22})!=22:raise PermissionError('distinct-game shortage')
    # Existing validation roles are not changed or moved into training. Scores
    # are never used to choose checkpoints; all candidate code is still absent.
    valpool=[]
    for row in sorted(E.B.load_dataset(A1D)['TRAIN_VALIDATION'],key=lambda x:x['sample_id']):
        c=checked_case(row,A1D)
        if any(c['origin']['row'][k] in blocked[k] for k in blocked):raise PermissionError('protected validation identity')
        valpool.append(c)
    validation=[]
    for label,n in [('MATCH',6),('DECLINE',4),('UNKNOWN',4)]:
        validation+=M.diversity([c for c in valpool if c['label']==label],n,'B4_VALIDATION_'+label)
    disjoint(d22,validation,future)
    out.mkdir(mode=0o700,parents=True)
    P.commit(out/'working_tree_start.json',dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)))
    P.commit(out/'source_selection.private.json',dict(old=natural,new=new,d11=[c['id'] for c in d11],eligible_new=pool,excluded=excluded,
        method='metadata diversity task_type,target,scene; SHA tie; one game/task group; no model outputs',validation=validation))
    measurements={};inputs={}
    for n,cases in [(11,d11),(22,d22)]:
        packets=M.packets(cases)
        for arm,payload in packets.items():
            cell=arm+str(n);w=wire(out,payload,'initial')
            if decode(__import__('json').loads(w['messages'][1]['content']))!=payload:raise PermissionError('encoding drift')
            P.commit(out/'inputs'/f'{cell}.private.json',payload);P.commit(out/'inputs'/f'{cell}.wire.private.json',w)
            measurements[cell]=check_wire(w,POLICY);inputs[cell]=cases
    measurements['engineering_64KiB_stress']=check_wire(wire(out,dict(parent_version='a'*64,previous_source_or_delivery='x'*65536,engineering_diagnostics=dict(errors=['x'*2048])),'engineering'),POLICY)
    bindings=dict(old['historical_sha256']);bindings.update(protection['files'])
    for folder in (B3REAL,A1C,A1D):
        for f in folder.rglob('*'):
            if f.is_file() and f.suffix in ('.py','.json','.jsonl'):bindings[str(f.resolve())]=P.sha(f)
    for f in [PROSPECTIVE,Path(__file__),Path(M.__file__),ROOT/'scripts/run_alfworld_container_b4.py',ROOT/'FlowEvo/src/failure_evo/wire_input_policy.py',ROOT/'FlowEvo/src/alfworld_/recovery_acquisition.py',ROOT/'FlowEvo/src/failure_evo/autonomous_generation.py',ROOT/'FlowEvo/src/failure_evo/network_transport.py']:
        bindings[str(f.resolve())]=P.sha(f)
    for folder in (ROOT/'FlowEvo/src/alfworld_',ROOT/'FlowEvo/src/failure_evo'):
        for f in folder.glob('*.py'):bindings[str(f.resolve())]=P.sha(f)
    for f in (out/'inputs').glob('*'):bindings[str(f.resolve())]=P.sha(f)
    maximum=(POLICY['max_input_tokens']+4096)*54
    # 12 D11 parents +3 revisions, 12 D22 parents +3 revisions; all 30
    # evaluated versions share fourteen validation states after all revisions.
    train_branches=15*11+15*22;validation_branches=30*len(validation)
    plan=dict(version=M.VERSION,run_id=out.name,scope='PREPARATION_AND_ZERO_API_ONLY',paid_authorization=False,
        cells=list(M.CELLS),initial_per_cell=4,first_wave=2,early_stop='12/12 valid ABSTAIN',engineering_per_initial=1,behavior_per_cell=1,
        model='deepseek-flash',documented_version='DeepSeek-V4.1-Flash-1017',temperature=.6,thinking='disabled',output_tokens=4096,input_policy=POLICY,network_policy=DEFAULT_POLICY,
        max_calls=54,max_tokens=maximum,max_cost_microusd=36000000,reservation_rate=1200000,
        budgets_by_stage=dict(generation=dict(calls=48,tokens=48*(POLICY['max_input_tokens']+4096)),behavior=dict(calls=6,tokens=6*(POLICY['max_input_tokens']+4096)),transfer=dict(calls=0,authorized=False)),
        max_peak_quote_usd=54*(POLICY['max_input_tokens']*.30+4096*1.20)/1e6,max_uniform_reservation_usd=maximum*1.20/1e6,
        price=dict(checked='2026-11-16',input_peak=.30,output_peak=1.20,cache_hit_peak=.006,url='https://api-docs.deepseek.com/quick_start/pricing/'),
        train={k:v for k,v in inputs.items()},validation=validation,d11=[c['id'] for c in d11],d22=[c['id'] for c in d22],
        data_root=old['data_root'],environment=old['environment'],worker=old['worker'],environment_type=old['environment_type'],
        source_window=18,episode_limit=50,max_stagnant_repeats=2,worker_calls=(train_branches+validation_branches)*18+60,
        environment_steps=(train_branches+validation_branches)*100,wall_seconds=172800,
        preflight_environment_steps=4000,historical_sha256=bindings,measurements=measurements,
        behavior_selection='worker_ok>0; incomplete TRAIN; repairs descending, errors/incompatible/unsupported ascending, fixed ID; zero repairs allowed',
        final_selection='common validation repairs>0, errors=0; repairs desc, incompatible/unsupported/actions/worker_calls/full-lineage tokens/ID asc; SHADOW only',
        prospective=dict(source=str(PROSPECTIVE),sha256=P.sha(PROSPECTIVE),games=12,role='RESERVED_NOT_EXECUTED',checkpoints_cap=36,
            candidate_worker_cap=6*36*18,environment_step_cap=7*36*100,model_calls=0,new_native_G=False))
    P.commit(out/'protocol.json',plan)
    return plan

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=prepare(a.output.resolve());print(P.canonical(dict(cells=list(r['train']),measurements=r['measurements'],budget=r['max_uniform_reservation_usd'],protocol_sha256=P.fingerprint(r))))
