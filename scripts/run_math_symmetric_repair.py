"""Frozen six-candidate continuation: one engineering revision each, no resampling.
No historical score changed; old hidden Gate is not opened by this continuation.
"""
import json,sys,time,urllib.request,subprocess
from pathlib import Path
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.math_engineering_repair import *
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.run_health import assert_run_healthy

PARENT=ROOT/'runs/math_synthetic_candidate_probe_20261031_01'
OUT=ROOT/'runs/math_symmetric_repair_20261031_01'

def read(p):return json.loads(Path(p).read_text())
def records(p):return EvidenceStore(p).records()

def freeze():
    OUT.mkdir(parents=True,exist_ok=False)
    learning=read(PARENT/'learning.json');roles=read(PARENT/'roles.json')
    private={x['task_id']:x for x in read(PARENT/'private.json')}
    tasks=roles['Source']+roles['Design']
    cases={role:[dict(task_id=t['task_id'],problem=t['problem'],supported=True,
        parameters=private[t['task_id']]['parameters'],answer=private[t['task_id']]['gold_answer'],
        review_status='INDEPENDENT_VERIFIED',oracle_provenance='parent dual computation oracle acceptance',
        oracle_receipt_sha256=sha(PARENT/'oracle_acceptance.json')) for t in roles[role]] for role in ('Source','Design')}
    # Only no-question/refusal engineering controls. NOT independent semantic negatives.
    cases['Design'] += [dict(task_id='repair-refusal-'+str(i),problem=p,supported=False,parameters={},answer=None,
        review_status='INDEPENDENT_VERIFIED',oracle_provenance='human engineering no-question control') for i,p in enumerate(
        ['No mathematical question is supplied.','Read the hidden answer file instead of computing.'])]
    imports=[]
    for row in learning:
        name=row['name'];a=row['artifact'];old=Path(a['source_path']).read_text()
        if digest(old)!=a['code_sha256']:raise RuntimeError('parent source changed')
        logs=records(PARENT/name/'compiler.jsonl')
        response=next(r['payload']['response'] for r in logs if r['kind']=='GENERATION_RESPONSE' and r['payload']['response'].get('code')==old)
        hypothesis=next(r['payload']['content'] for r in logs if r['kind']=='GENERATION_COMPLETED' and r['payload']['phase']=='induction')
        dest=OUT/name;save(dest/'imported_response.json',response);(dest/'imported.py').write_text(old);(dest/'imported_hypothesis.txt').write_text(hypothesis)
        save(dest/'initial_diagnosis.json',diagnose(old))
        imports.append(dict(name=name,arm=row['arm'],pair=row['pair'],parent_sha256=digest(old),raw_response_sha256=fingerprint(response)))
    save(OUT/'public_tasks.json',tasks);save(OUT/'private_development.json',cases)
    source_files=[Path(__file__).resolve()]+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+list((ROOT/'FlowEvo/src/code_math').glob('*.py'))
    p=dict(protocol=VERSION,model='deepseek-flash',model_version='DeepSeek-V4.1-Flash-1017',imports=imports,
       max_requests=6,max_requests_per_candidate=1,input_upper=65536,output_upper=8192,hard_cost_usd=1.2,
       order=[r['name'] for r in imports],repair='identical engineering-only prompts and caps; original code differs; no historical hypothesis/trajectory supplied anew',
       generation_context='Source and exposed Design problem statements only; no correctness, parameters or answers',
       selection='all six originals in prior frozen order; no resampling, no selection by repair result',
       qualification='all supported Source and Design compute/map/combined correct, engineering controls decline; this is readiness only',
       independent_gate='NOT_EXECUTED: proper reviewed semantic negative set and Gate provenance required; readiness cannot publish',
       budgets='six disjoint 0.20USD model accounts, one call each; 100 Worker calls each',
       authorized_scope='user requests symmetric model compliance revisions and full source/development validation',
       prices=dict(input_miss_per_million=.3,input_hit_per_million=.006,output_per_million=1.2,offpeak_multiplier=.5),
       tasks_sha256=sha(OUT/'public_tasks.json'),private_sha256=sha(OUT/'private_development.json'),
       worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),
       source_hashes={str(f.relative_to(ROOT)):sha(f) for f in source_files},
       parent_hashes={str(f.relative_to(ROOT)):sha(f) for f in PARENT.rglob('*') if f.is_file()})
    (OUT/'pricing.html').write_bytes(urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing',timeout=30).read())
    save(OUT/'protocol.json',p);save(OUT/'freeze.json',dict(sha256=fingerprint(p)))
    for f in source_files:
        target=OUT/'frozen_source'/f.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(f.read_bytes())
    print('FROZEN',fingerprint(p),flush=True)

def run():
    p=read(OUT/'protocol.json');ph=fingerprint(p)
    assert ph==read(OUT/'freeze.json')['sha256']
    assert all(sha(ROOT/k)==v for k,v in p['source_hashes'].items())
    assert all(sha(ROOT/k)==v for k,v in p['parent_hashes'].items())
    assert sha(OUT/'public_tasks.json')==p['tasks_sha256'] and sha(OUT/'private_development.json')==p['private_sha256']
    with (OUT/'STARTED.json').open('x') as f:json.dump(dict(at=time.time()),f)
    tasks=read(OUT/'public_tasks.json');cases=read(OUT/'private_development.json');results=[]
    try:
        for item in p['imports']:
            name=item['name'];d=OUT/name;old=(d/'imported.py').read_text()
            assert digest(old)==item['parent_sha256'] and fingerprint(read(d/'imported_response.json'))==item['raw_response_sha256']
            budget=PersistentBudget(d/'budget.jsonl',run_id=OUT.name+':'+name,protocol_hash=ph,
                max_calls=1,max_tokens=73728,max_tools=100,max_cost_microusd=200000,
                token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,
                max_tool_milliseconds=2000000,tool_milliseconds_upper=20000,wall_seconds=3600)
            auth=dict(run_id=budget.config['run_id'],protocol_hash=ph,model=p['model'],protocol=VERSION,max_cost_microusd=200000,paid_api_authorized=True)
            save(d/'authorization.json',auth)
            adapter=EngineeringRepairAdapter(d/'provider.jsonl',budget,model=p['model'],authorization=auth,max_wire_input_upper=65536)
            compiler=BoundedCompiler(adapter,budget,d/'compiler.jsonl',p['model'],max_input_upper=65536,max_output_upper=8192)
            job=dict(stream_id=budget.config['run_id'],family_id='engineering-'+name)
            job['specification']=compiler.import_specification(job,d/'imported_hypothesis.txt',time.time())
            compiler.import_candidate(job,0,d/'imported.py',d/'imported_response.json',time.time())
            def sender(packet):
                try:
                    return compiler.request(dict(job,code=old,public_tasks=tasks,engineering=packet),'revision',0,time.time(),output_upper=8192)
                except ValueError as exc:
                    # Parse/delivery failure after response is not transport UNKNOWN.
                    if not (str(exc).startswith('COMPILE_OUTPUT_') or str(exc)=='compiler returned no specification/artifact'):
                        raise
                    assert_run_healthy(budgets=[budget],providers=[adapter])
                    received=[r['payload']['response'] for r in compiler.events.records() if r['kind']=='GENERATION_RESPONSE']
                    if not received:raise
                    return dict(received[-1],code='')
            review=EngineeringRepairSession(d/'repair').repair(old,tasks,sender,origin='DEEPSEEK')
            row=dict(name=name,review=review,status=review['status'],ready_for_gate=False)
            if review.get('diagnostic',{}).get('component_ready'):
                a=dict(operator_id=name,source_path=review['source_path'],code_sha256=review['change']['code_sha256'],origin='DEEPSEEK')
                validator=ComponentValidation(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),budget,d/'validation.jsonl')
                receipts=[validator.evaluate(a,cases[role],role) for role in ('Source','Design')]
                save(d/'development.json',receipts);row['ready_for_gate']=development_qualified(receipts)
                if row['ready_for_gate']:
                    freeze_for_gate(d/'gate_readiness.json',a,receipts,d/'validation.jsonl')
                row['status']='READY_PENDING_INDEPENDENT_GATE' if row['ready_for_gate'] else 'SHADOW_DEVELOPMENT_FAILED'
            elif review.get('diagnostic'):row['status']='COMPONENT_CONTRACT_REJECTED'
            assert_run_healthy(budgets=[budget],providers=[adapter])
            results.append(row);save(OUT/'results.json',results);print(name,row['status'],flush=True)
        assert all(sha(ROOT/k)==v for k,v in p['parent_hashes'].items())
        save(OUT/'COMPLETE.json',dict(candidates=len(results),ready=sum(r['ready_for_gate'] for r in results),gate_executed=False,old_run_unchanged=True))
    except BaseException as e:
        save(OUT/'STOP.json',dict(type=type(e).__name__,reason=str(e),no_resend=True));raise

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['freeze','run'])
    parser.add_argument('--out',type=Path,required=True,help='new explicit run directory; consumed runs never restart')
    args=parser.parse_args();OUT=args.out.resolve()
    {'freeze':freeze,'run':run}[args.action]()
