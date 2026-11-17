"""Authorized Route B generation only. No Worker/environment or registry publication."""
import argparse,fcntl,json,time
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
from prepare_alfworld_route_b_generation import VERSION,PROMPT,REVISION,POLICY,make_wire
from alfworld_.route_b_compact_projection import encode
from alfworld_.recovery_acquisition import stage_request
from alfworld_.python_recovery_feedback import parse_delivery
from alfworld_.failure_learning import static_check
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read,sha,save
from failure_evo.contracts import canonical,fingerprint
from failure_evo.run_health import assert_run_healthy
from run_alfworld_a4_confirmatory import commit

PRE=Path('runs/alfworld_route_b_generation_preflight_20261116_03')
INPUT=Path('runs/alfworld_route_b_b01_20261116_02')

def freeze(root,mock):
    p=read(PRE/'protocol.json');s=read(PRE/'summary.json')
    assert fingerprint(p)==s['protocol_sha256']=='910490edb5effeb5a163faeed74a9df84242c141b416fb500402b499301e4d48'
    assert all(sha(f)==h for f,h in read(PRE/'source_manifest.json').items())
    assert all(sha(f)==h for f,h in read(INPUT/'source_binding.private.json').items())
    source=read(INPUT/'projection.private.json');assert fingerprint(source)==p['source_packet_sha256']
    root.mkdir(mode=0o700,parents=True,exist_ok=True)
    paths=[__file__,'FlowEvo/src/alfworld_/failure_learning.py','FlowEvo/src/alfworld_/route_b_compact_projection.py',
        'FlowEvo/src/alfworld_/python_recovery_feedback.py','FlowEvo/src/failure_evo/network_transport.py']
    plan=dict(preflight_protocol=p,run_id=root.name,mock=mock,input_sha256=fingerprint(source),
        runtime_source_sha256={str(Path(x).resolve()):sha(x) for x in paths},
        order='preflight jobs order; each permitted revision immediately follows own initial')
    commit(root/'protocol.json',plan)
    if not mock:commit(root/'authorization.json',dict(user_instruction='授权路线B三组生成，上限8美元',
        authorized_date='2026-11-16',max_cost_microusd=8000000,protocol_sha256=fingerprint(plan),
        scope='GENERATION_AND_ENGINEERING_REVISION_ONLY',paid_api_authorized=True))
    return plan,source

def run(root,mock=False):
    plan,source=freeze(root,mock);p=plan['preflight_protocol']
    accounts={a:PersistentBudget(root/a/'budget.jsonl',run_id=('engineering:' if mock else '')+root.name+':'+a,
        protocol_hash=fingerprint(plan),**p['arm_allocations'][a],max_tools=0,
        token_rate_microusd_per_million=p['reservation_rate_microusd_per_million'],
        tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=1000,wall_seconds=86400) for a in 'TSF'}
    providers=[SimpleNamespace(events=EvidenceStore(root/a/'provider.jsonl')) for a in 'TSF']
    outputs=[];seen={};sent=[]
    def healthy():assert_run_healthy(budgets=list(accounts.values()),providers=providers,network_policy=None if mock else p['network_policy'])
    def sender(w):
        sent.append(fingerprint(w));content=(dict(decision='ABSTAIN',reason='Mock only') if w['messages'][0]['content']==REVISION else
            dict(decision='PROPOSE',code=f"import os\ndef environment_operator(c):\n return {{'status':'declined','state':{{}},'reason':'fixture{len(sent)}'}}",description='Mock only',applicability='Mock only'))
        return dict(id='MOCK-'+str(len(sent)),model='deepseek-flash',usage=dict(prompt_tokens=100,completion_tokens=20,total_tokens=120),
            choices=[dict(message=dict(content=canonical(content)),finish_reason='stop')])
    with (root/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            for job in p['jobs']:
                arm=job['arm'];b=accounts[arm];healthy()
                auth=None if mock else dict(run_id=b.config['run_id'],protocol_hash=b.config['protocol_hash'],
                    model=p['model'],protocol=VERSION,max_cost_microusd=b.config['max_cost_microusd'],paid_api_authorized=True)
                payload=json.loads(read(PRE/f'{arm}_wire.private.json')['messages'][1]['content'])
                assert fingerprint(make_wire(root,payload,PROMPT))==job['wire_sha256']
                attempts=[]
                for revision in range(2):
                    healthy();name=job['name']+('_revision' if revision else '')
                    try:make_wire(root,payload,REVISION if revision else PROMPT)
                    except ValueError:
                        attempts.append(dict(name=name,status='INPUT_LIMIT',no_send=True));break
                    print(f"{name}: sending or recovering settled request",flush=True)
                    response=stage_request(root/arm,name,'analyze',payload,parse_delivery,b,
                        sender=sender if mock else None,authorization=auth,network_policy=None if mock else p['network_policy'],
                        protocol=VERSION,analysis_prompt=REVISION if revision else PROMPT,temperature=0.6,input_policy=POLICY)
                    location=root/arm/name;commit(location/'response.json',response)
                    raw=response.get('raw_response',{});text=raw.get('choices',[{}])[0].get('message',{}).get('content') or ''
                    decoded=None
                    try:
                        if response.get('finish_reason')!='stop':raise ValueError('MODEL_INCOMPLETE')
                        delivery=parse_delivery(json.loads(text))
                        decoded=delivery.get('proposal')
                        if decoded is None:raise ValueError(canonical(delivery.get('schema',{})))
                    except (ValueError,TypeError) as exc:
                        diagnostics=dict(passed=False,errors=[dict(path='$',code='DELIVERY_REJECTED',message=str(exc))])
                        status='DELIVERY_REJECTED';code=None
                    else:
                        code=decoded.get('code');diagnostics=static_check(code) if code else None
                        status='ABSTAIN' if decoded['decision']=='ABSTAIN' else 'STATIC_PASS' if diagnostics['passed'] else 'STATIC_REJECTED'
                    version=fingerprint([name,response.get('response_sha256'),code])
                    row=dict(name=name,status=status,version=version,parent_version=attempts[-1]['version'] if attempts else None,
                        source_sha256=fingerprint(code) if code else None,diagnostics=diagnostics,
                        decoded=decoded,worker='NOT_RUN',environment='NOT_RUN',permission='UNVERIFIED_NOT_REGISTERED',
                        response_sha256=fingerprint(raw))
                    if code:commit(location/'source_record.json',dict(code=code,sha256=fingerprint(code)))
                    if code:
                        path=location/'candidate.py'
                        if path.exists():assert path.read_text()==code
                        else:path.write_text(code)
                    duplicate=seen.get((arm,row['source_sha256'])) if code else None
                    if duplicate:row['duplicate_of']=duplicate
                    elif code:seen[(arm,row['source_sha256'])]=name
                    commit(location/'assessment.json',row);attempts.append(row)
                    print(f"{name}: {status}"+(f' duplicate of {duplicate}' if duplicate else ''),flush=True)
                    if status in ('ABSTAIN','STATIC_PASS') or duplicate or revision:break
                    payload=encode(dict(original_learning_input=source['inputs'][arm],parent_version=version,
                        previous_source_or_delivery=code if code is not None else text,engineering_diagnostics=diagnostics))
                item=dict(arm=arm,candidate_id=job['name'],attempts=attempts)
                commit(root/'candidates'/f"{job['name']}.json",item);outputs.append(item)
            healthy()
        except BaseException as exc:
            save(root/'STOP.json',dict(error_type=type(exc).__name__,reason=str(exc),at=time.time(),
                completed_candidates=len(outputs),budgets={a:b.snapshot() for a,b in accounts.items()}))
            raise
    raw=[r['payload']['response'] for pr in providers for r in pr.events.records() if r['kind']=='RAW_RESPONSE']
    usage=dict(input_tokens=0,output_tokens=0,total_tokens=0)
    for r in raw:
        u=r.get('usage',{});usage['input_tokens']+=u.get('prompt_tokens',0);usage['output_tokens']+=u.get('completion_tokens',0);usage['total_tokens']+=u.get('total_tokens',0)
    result=dict(status='COMPLETED_GENERATION_ONLY',mock=mock,paid_requests=0 if mock else len(raw),
        returned_responses=len(raw),usage=usage,peak_no_cache_cost_estimate_usd=(usage['input_tokens']*.3+usage['output_tokens']*1.2)/1e6,
        budgets={a:b.snapshot() for a,b in accounts.items()},candidates=outputs,
        arms={a:dict(Counter(x['attempts'][-1]['status'] for x in outputs if x['arm']==a)) for a in 'TSF'},
        winner=None,worker_calls=0,environment_steps=0,actual_local_repairs='NOT_EVALUATED',authorization_cap_usd=8)
    commit(root/'result.json',result);print(canonical({k:v for k,v in result.items() if k not in ('candidates','budgets')}),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mock',action='store_true')
    p.add_argument('--authorized-usd',type=float);a=p.parse_args()
    if not a.mock and a.authorized_usd!=8:p.error('explicit current authorization --authorized-usd 8 required')
    run(a.output.resolve(),a.mock)
