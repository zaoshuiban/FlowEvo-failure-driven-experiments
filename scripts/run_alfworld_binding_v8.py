"""Frozen public-only diagnostic. Prepare is zero API; run requires a new exact grant."""
import argparse
import fcntl
import json
from pathlib import Path
from alfworld_.binding_diagnostic import *
from alfworld_.skill_acquisition import load_source, INPUT_LIMIT, MODEL
from alfworld_.recovery_acquisition import stage_request
from failure_evo.math_stream import read, save, sha
from failure_evo.network_transport import DEFAULT_POLICY
from run_alfworld_skill_acquisition import create_accounts

ROOT = Path(__file__).resolve().parents[1]


def dataset(source, v7):
    protocol, _, host = load_source(source)
    old = read(v7/'protocol.json')
    data = read(v7/'validation.private.json')
    if old['source_protocol_sha256'] != fingerprint(protocol) or old['validation_sha256'] != fingerprint([data['checkpoints'],data['negatives']]):
        raise PermissionError('historical identity mismatch')
    cases=[]
    for cp in data['checkpoints']:
        h=host[cp['evidence_id']]
        if cp['source_receipt']!=h['receipt_sha256'] or cp['step']!=h['projected']['anchor']:
            raise PermissionError('source checkpoint drift')
        prefix=h['steps'][:cp['step']]
        p=public_case('source_'+str(cp['sequence']),h['projected']['goal'],prefix[-1]['observation'],
                      prefix[-1]['commands'],prefix,len(prefix)-1)
        cases.append(annotation(p,['MATCH']*5,['YES']*4,role='source',category='public_prefix_binding',
            basis='Public pickup/processing/arrival prefix and unique accessible destination. Local binding, not world uniqueness.',source=cp))
    for row in data['negatives']:
        ctx=row['context']; hist=ctx['history']
        anchor=next((i for i,s in enumerate(hist) if s['action'].startswith('move ') and s['observation']=='Nothing happens.'),None)
        p=public_case(row['id'],ctx['goal'],ctx['observation'],ctx['admissible_commands'],hist,anchor)
        a=['UNKNOWN']*5; b=['NO','NO','UNKNOWN','NO']
        basis='No selected failed command. No failure-recovery intervention justified.'
        if anchor is not None:
            if 'fridge' in ctx['goal']:
                a=['CONFLICT']*4+['UNKNOWN']; b=['NO','UNKNOWN','NO','NO']; basis='Mug/fridge goal conflicts with vase/safe failure.'
            elif 'safe 3' in ctx['goal']:
                a=['MATCH','MATCH','UNKNOWN','CONFLICT','UNKNOWN']; b=['NO','UNKNOWN','NO','NO']; basis='Explicit safe 3 differs from failed safe 2; current possession unstated.'
            elif row['id']=='obstacle_already_resolved':
                a=['MATCH']*5; b=['YES','NO','YES','NO']; basis='Later open receipt resolves obstacle; legal move identifies held instance.'
            elif row['id']=='subgoal_already_completed':
                a=['MATCH','MATCH','CONFLICT','MATCH','CONFLICT']; b=['YES','NO','NO','NO']; basis='Later successful delivery removes held-object/delivery-phase precondition.'
            elif row['id']=='newly_held_object_differs':
                a=['MATCH','MATCH','CONFLICT','MATCH','CONFLICT']; b=['YES','UNKNOWN','NO','NO']; basis='Public later pickup replaces current held object.'
            else:
                raise ValueError('unreviewed regression reference')
        cases.append(annotation(p,a,b,role='v7_regression',category=row.get('category',row['group']),basis=basis,
                                source=dict(validation_sha256=sha(v7/'validation.private.json'),id=row['id'])))
    # Prespecified six coverage cells, two lexical instances each. No model outcome used.
    for category in ('object_category','container_category','explicit_conflict','object_conflict','multiple_instances','insufficient'):
        for j,(obj,target) in enumerate((('plate','cabinet'),('mug','drawer'))):
            held=f'{obj} {8+j}'; dest=f'{target} {5+j}'
            goal=f'put some {obj} in {target}.'
            obs=f'The {dest} is closed.'
            commands=['look',f'open {dest}']
            hist=[event(f'take {held} from desk 1',f'You pick up the {held} from desk 1.'),event(f'move {held} to {dest}','Nothing happens.')]
            a=['MATCH']*5; b=['YES']*4
            basis='Explicit possession, current closed destination and one available destination establish local binding.'
            if category=='explicit_conflict':
                goal=f'put the {held} in {target} {15+j}.'
                a[3]='CONFLICT'; b=['NO','YES','NO','NO']; basis='Goal explicitly names a different destination instance.'
            elif category=='object_conflict':
                goal=f'put some book in {target}.'
                a[0]=a[2]=a[4]='CONFLICT'; b=['NO','YES','NO','NO']; basis='Current and failed object are not the goal object.'
            elif category=='multiple_instances':
                obs+=f' The {target} {15+j} is closed.'; commands.append(f'open {target} {15+j}')
                a[3]='UNKNOWN'; b=['YES','YES','UNKNOWN','UNKNOWN']; basis='Two visible destination choices, no public disambiguation; do not invent a unique instance.'
            elif category=='insufficient':
                hist=hist[1:]; obs='You are in the room.'; commands=['look','inventory']
                a[2:]=['UNKNOWN']*3; b=['YES','UNKNOWN','UNKNOWN','UNKNOWN']; basis='Current possession, target location/state and task phase not established.'
            elif category=='container_category':
                hist.append(event('look',obs)); basis+=' A later look confirms rather than invalidates the obstacle.'
            p=public_case('fresh_'+category+'_'+str(j),goal,obs,commands,hist,0 if category=='insufficient' else 1,
                          None if category=='insufficient' else held)
            cases.append(annotation(p,a,b,role='fresh_synthetic',category=category,basis=basis))
    for i,c in enumerate(cases,1):
        c["case_key"]=c["public"]["id"]
        c["public"]["id"]=f"case_{i:03d}"
    return cases


def plan_for(source,v7,output,mock=False):
    cases=dataset(source,v7)
    files=[Path(__file__).resolve(),ROOT/'scripts/test_alfworld_binding_v8.py',ROOT/'scripts/run_alfworld_skill_acquisition.py']
    files += [p for d in ('alfworld_','failure_evo','runtime') for p in (ROOT/'FlowEvo/src'/d).glob('*.py')]
    plan=dict(version=VERSION,run_id=('mock:' if mock else 'real:')+output.name,
        scope='MOCK_DIAGNOSTIC' if mock else 'REAL_DIAGNOSTIC_NOT_STRATEGY',
        dataset_sha256=fingerprint(cases),prompts=PROMPTS,schemas=OUTPUTS,batch_size=6,
        model=MODEL,model_release_reference='DeepSeek-V4.1-Flash-1017',temperature=0,thinking='disabled',
        max_calls=12,max_tokens=12*(INPUT_LIMIT+4096),max_cost_microusd=1010000,worker_calls=0,
        max_input_upper=INPUT_LIMIT,max_output_tokens=4096,network_policy=DEFAULT_POLICY,
        code_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))},
        historical_sha256={str(p):sha(p) for version in range(3,8)
            for p in (v7.parent/f'alfworld_recovery_v{version}_pilot_20261110_01').rglob('*') if p.is_file()},
        price_reference=dict(uncached_input_per_million=.30,output_per_million=1.20),
        no_strategy_generation=True,no_gate=True,no_model_revision=True)
    return plan,cases


def grant(plan):
    return dict(paid_api_authorized=True,run_id=plan['run_id'],protocol_hash=fingerprint(plan),model=MODEL,protocol=VERSION,
                max_cost_microusd=plan['max_cost_microusd'])


def run(source,v7,output,*,sender=None,authorization=None):
    plan,cases=plan_for(source,v7,output,sender is not None)
    if sender is None and (authorization!=grant(plan) or read(output/'protocol.json')!=plan):
        raise PermissionError('new explicit diagnostic authorization required')
    output.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'protocol.json').exists() and read(output/'protocol.json')!=plan:
            raise PermissionError('frozen protocol drift')
        save(output/'protocol.json',plan); save(output/'dataset.private.json',cases)
        budget=create_accounts(output,plan)
        predictions={'A':{},'B':{}}; receipts=[]
        for arm in ('A','B'):
            for i in range(0,len(cases),6):
                public=[c['public'] for c in cases[i:i+6]]
                receipt=stage_request(output,f'{arm}_{i//6:02}', 'analyze',dict(cases=public),
                    lambda x:parse_rows(x,arm,public),budget,sender=sender,authorization=authorization,
                    network_policy=None if sender else plan['network_policy'],protocol=VERSION,analysis_prompt=PROMPTS[arm])
                receipts.append(dict(arm=arm,batch=i//6,result=receipt))
                if not receipt.get('parse_status'):
                    predictions[arm].update(json.loads(receipt['specification'])['rows'])
        input_tokens=sum(r['result']['raw_response']['usage']['prompt_tokens'] for r in receipts)
        output_tokens=sum(r['result']['raw_response']['usage']['completion_tokens'] for r in receipts)
        result=dict(budget=budget.snapshot(),usage=dict(input_tokens=input_tokens,output_tokens=output_tokens),
                    quote_estimated_usd=(input_tokens*.30+output_tokens*1.20)/1000000,
                    cost_scope='MOCK_NOT_REAL' if sender else 'QUOTE_ESTIMATE_NOT_INVOICE',
                    scope=plan['scope'],protocol_sha256=fingerprint(plan),receipts=receipts,
                    predictions=predictions,metrics=score(cases,predictions),paid_requests=0 if sender else None)
        save(output/'result.json',result)
        return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','run'])
    for k in ('source','v7','output'):
        parser.add_argument('--'+k,type=Path,required=True)
    parser.add_argument('--authorization',type=Path)
    args=parser.parse_args()
    if args.action=='prepare':
        plan,cases=plan_for(args.source,args.v7,args.output)
        args.output.mkdir(parents=True,mode=0o700,exist_ok=False)
        save(args.output/'protocol.json',plan);save(args.output/'dataset.private.json',cases)
        save(args.output/'authorization.template.json',dict(grant(plan),paid_api_authorized=False))
        print('PREPARED_NOT_AUTHORIZED',fingerprint(plan))
    else:
        if not args.authorization: parser.error('--authorization required')
        run(args.source,args.v7,args.output,authorization=read(args.authorization))
