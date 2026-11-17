"""Freeze A3 data/input/resource preparation. No model send or effective authorization."""
import argparse
from pathlib import Path
from collections import Counter
from alfworld_ import recovery_learning_input as I
from alfworld_ import recovery_applicability_learning as L
from failure_evo.math_stream import read,sha
from failure_evo.contracts import canonical,fingerprint
import run_alfworld_applicability_multicandidate as study

DATA=study.ROOT/'runs/alfworld_route_a_a1d_20261113_01'


def stress_feedback(rows):
    # Serialization fixture ONLY: no score, no candidate, never supplied to a model.
    source='#'+'\\'*65500
    a=dict(candidate_id='ENGINEERING_CONTEXT_STRESS',version='NOT_MODEL_GENERATED',code=source,
        code_sha256=fingerprint(source),delivery={'status':'PROPOSE'},static={'passed':False,'error':'ENGINEERING_CONTEXT_ONLY'},train=[])
    for r in rows:
        actual='DECLINE' if r['label']=='MATCH' else 'MATCH'
        a['train'].append(dict(candidate_id=a['candidate_id'],version=a['version'],role='TRAIN',sample_id=fingerprint(r['sample_id']),
            actual=actual,reason='ENGINEERING SELF-REPORT NOT ENVIRONMENT FACT',expected=r['label'],classification=L.classify(r['label'],actual),
            execution_id='MOCK',worker_status='OK',context_sha256=fingerprint(r['candidate_context']),live={'actions':[]},recovery_verified=False))
    return a


def resources(roles):
    result={}
    for role,rows in roles.items():
        matches=[r for r in rows if r['label']=='MATCH'];lengths=[]
        for row in matches:
            _,origin,_=study.source_origin(row,{'dataset':str(DATA)})
            lengths.append(origin['projected']['anchor'])
        steps=sum(min(18,50-n) for n in lengths)
        result[role]=dict(gates_upper=8*len(rows),recovery_worker_upper=8*steps,
            prefix_environment_steps_upper=8*sum(lengths),recovery_environment_steps_upper=8*steps,
            one_restart_prefix_upper=8*sum(n+min(18,50-n) for n in lengths),
            matches=len(matches),physical_groups=len({r['physical_state_group_id'] for r in rows}),
            max_prefix=max(lengths),min_prefix=min(lengths))
    result['EXPOSED_REGRESSION']=dict(gates_upper=32,recovery_worker_upper=11*18+21,
        prefix_and_recovery_environment_steps_upper=11*50,one_restart_upper=11*50,
        note='11 sources +21 boundary decisions; boundary recovery Worker has no environment execution')
    result['limits']=dict(worker_calls=8*(sum(map(len,roles.values()))+18*sum(r['label']=='MATCH' for rs in roles.values() for r in rs))+11*19+42,
        environment_steps=2*(8*sum(r['label']=='MATCH' for rs in roles.values() for r in rs)*50+11*50),
        episode_limit=50,source_window=18,worker_milliseconds_per_call_upper=15000,wall_seconds=86400,
        model_call_upper=8,environment_restart_policy='one complete replay per branch is reserved; further restarts consume same global bound, never expand it',
        local_compute_cost_usd=None,local_compute_note='count/time measured; no cash tariff configured, not claimed free')
    return result


def prepare(output,dataset=DATA):
    roles=L.load_dataset(dataset)
    if not read(dataset/'dataset.json').get('A3_data_ready'):raise PermissionError('A3_DATA_NOT_READY')
    comparison={name:I.organize(roles['TRAIN'],study.CODE.read_text(),k) for name,k in [('F',None),('S-64',64),('S-128',128),('S-256',256)]}
    # Select full evidence before any model result. More space for full source + own feedback.
    p,q=I.policy(256),I.policy(384)
    plan=study.prepare(output,dataset=dataset,input_policy=p,revision_policy=q,input_scheme='F')
    for name,o in comparison.items():
        payload=dict(candidate_id='candidate_0',training_input=o['packet'])
        bound=p if name=='F' else I.policy(int(name.split('-')[1]))
        actual=study.wire(output,payload,L.INITIAL_PROMPT,0.6,bound)
        if actual!=I.wire(payload,L.INITIAL_PROMPT):raise PermissionError('measured and actual adapter differ')
    fixture=stress_feedback(roles['TRAIN']);rev=I.revision(fixture,roles['TRAIN'],q)
    revwire=study.wire(output,rev,L.REVISION_PROMPT,0.6,q)
    bounds=dict(initial_input_tokens=p['max_input_tokens'],revision_input_tokens=q['max_input_tokens'],output_tokens=4096,
        total_tokens=plan['max_tokens'],calls=8,
        peak_price_upper_usd=(4*p['max_input_tokens']*.30+4*q['max_input_tokens']*.30+8*4096*1.20)/1000000,
        uniform_ledger_reservation_upper_usd=plan['max_tokens']*1.2/1000000,
        proposed_cap_usd=plan['max_cost_microusd']/1000000,actual_provider_tokens=None,actual_api_cost_usd=0,
        pricing=I.PRICE,price_recheck_required_at_authorization=True)
    study.pilot.commit(output/'input_comparison.private.json',comparison)
    study.pilot.commit(output/'revision_stress.private.json',dict(scope='ENGINEERING_SERIALIZATION_NOT_LEARNING',
        source_bytes=len(fixture['code'].encode()),measurement=I.measure(rev,L.REVISION_PROMPT),
        selected=len(rev['own_train_feedback']),omitted=rev['omitted_feedback'],wire_sha256=fingerprint(revwire),payload=rev))
    study.pilot.commit(output/'resource_budget.json',dict(model=bounds,execution=resources(roles)))
    template=dict(run_id=plan['run_id'],protocol_hash=fingerprint(plan),model=plan['model'],
        protocol=study.VERSION+':'+fingerprint(plan),max_cost_microusd=plan['max_cost_microusd'],paid_api_authorized=False)
    study.pilot.commit(output/'authorization.template.json',template)
    study.preflight(output)
    try:study.preflight(output,paid=True,authorization=template)
    except PermissionError as e:
        if str(e)!='A3_PENDING_EXPLICIT_AUTHORIZATION':raise
    else:raise AssertionError('false template authorized paid run')
    return study.pilot.commit(output/'preflight.json',dict(data='A3_DATA_READY_DIAGNOSTIC_MINIMUM',
        engineering='PENDING_FINAL_ZERO_API_REPORT',authorization='A3_PENDING_AUTHORIZATION',protocol_sha256=fingerprint(plan),
        paid_requests=0,independent_gate_executions=0,selection_scope='CONTROLLED_DEVELOPMENT_ONLY',
        input_comparison_sha256=sha(output/'input_comparison.private.json'),resource_budget_sha256=sha(output/'resource_budget.json')))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--dataset',type=Path,default=DATA)
    a=p.parse_args();print(canonical(prepare(a.output.resolve(),a.dataset.resolve())))
