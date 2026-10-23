"""Frozen B2 candidate-only batch; requires separately recorded run-bound authorization.
Never executes generated code. A stopped/attempted run cannot be automatically retried.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo import PersistentBudget, BoundedCompiler, FailureEvidenceStore, FailureOperatorRegistry, FailureOperator, Fingerprint
from failure_evo.contracts import fingerprint
from failure_evo.model_api import DeepSeekGenerator, validate_compile_output

def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def check_frozen(run):
    config=read(run/'protocol.json')
    if fingerprint({k:v for k,v in config.items() if k!='protocol_hash'})!=config['protocol_hash']:
        raise ValueError('protocol integrity failure')
    for path,digest in config['frozen_files'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('frozen file changed: '+path)
    job=read(run/'generation_input.json')
    for slot in range(3):
        preview=DeepSeekGenerator.prepare(dict(job,phase='candidate',slot=slot,max_tokens=4096))
        if preview!=read(run/f'request_{slot+1}.json'):raise ValueError('wire preview changed')
    return config,job

def generate(run,authorization):
    config,job=check_frozen(run)
    if any((run/name).exists() for name in ('result.json','budget.jsonl','compiler.jsonl')):
        raise FileExistsError('already started; preserve evidence, no automatic retry')
    approval=read(authorization)
    expected=dict(api_spend_authorized=True,run_id=config['run_id'],protocol_hash=config['protocol_hash'],max_cost_microusd=config['budget']['max_cost_microusd'])
    if any(approval.get(k)!=v for k,v in expected.items()) or not approval.get('user_authorization_text'):
        raise PermissionError('new explicit user spending authorization is required')
    store=FailureEvidenceStore(ROOT/config['facts_path'])
    known={e['event_id']:e for e in store.visible(time.time())}
    if any(e not in known or known[e]['synthetic'] for e in job['evidence_ids']):raise ValueError('trusted failure evidence unavailable')
    budget=PersistentBudget(run/'budget.jsonl',run_id=config['run_id'],protocol_hash=config['protocol_hash'],**config['budget'])
    compiler=BoundedCompiler(DeepSeekGenerator(budget,authorization=approval),budget,run/'compiler.jsonl',config['model'])
    registry=FailureOperatorRegistry(run/'shadow_registry.jsonl',store)
    result=dict(run_id=config['run_id'],status='RUNNING',candidates=[],real_execution='NOT_RUN',public_check_outcome='unavailable',independent_gate='NOT_RUN',experimental_authorizations=0)
    def save():
        result['budget']=budget.snapshot();write(run/'result.json',result)
    save()
    try:
        spec=compiler.import_specification(job,run/'specification_v2.txt',time.time())
        if job['specification']!=spec:raise ValueError('specification mismatch')
        for slot in range(3):
            item=dict(slot=slot,state='Shadow',execution='NOT_RUN');result['candidates'].append(item)
            try:
                response=compiler.request(job,'candidate',slot,time.time())
                write(run/f'candidate_{slot+1}.response.json',response)
                value={k:response.get(k) for k in ('code','description','applicability')}
                review=validate_compile_output(value,response.get('finish_reason'))
                code=value['code'];path=run/f'candidate_{slot+1}.py';path.write_text(code)
                digest=hashlib.sha256(code.encode()).hexdigest()
                item.update(artifact_path=str(path.relative_to(ROOT)),sha256=digest,review=review,model=response['model'],usage=response.get('usage',{}))
                if not review['static_pass']:
                    item['acceptance']='STATIC_REJECTED';result['status']='STOPPED_STATIC_REJECTION';save();break
                card=FailureOperator('b2-shadow-recovery-'+str(slot+1),'v2',str(path),digest,
                    Fingerprint('public-feedback-adapted-v2','not-executed',response['model'],config['base_commit'],'S1.2-B2-static'),
                    'historical-incomplete-artifact-development',tuple(job['evidence_ids']),('lcb_atcoder_abc371_f',))
                registry.register(card,time.time());item['acceptance']='SHADOW_STATIC_ONLY'
                print(f'Candidate {slot+1}: SHADOW_STATIC_ONLY',flush=True);save()
            except Exception as exc:
                # Raw responses and their wire request already reside in compiler.jsonl.
                item.update(acceptance='REJECTED',error_type=type(exc).__name__)
                request_hash=fingerprint(dict(job,phase='candidate',slot=slot,max_tokens=4096))
                rows=[r['payload']['response'] for r in compiler.events.records() if r['kind']=='GENERATION_RESPONSE' and r['payload']['request_sha256']==request_hash]
                if rows:
                    item['parse_status']=rows[-1].get('parse_status');write(run/f'candidate_{slot+1}.response.json',rows[-1])
                result['status']='STOPPED_NO_RETRY';save();break
        else:result['status']='COMPLETED_SHADOW_STATIC_ONLY'
        result['conclusion']='PARTIAL' if any(c.get('acceptance')=='SHADOW_STATIC_ONLY' for c in result['candidates']) else 'NO-GO'
    except Exception as exc:result.update(status='STOPPED_NO_RETRY',error_type=type(exc).__name__,conclusion='NO-GO')
    finally:save()
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',default='runs/s12b2_20261021_01');parser.add_argument('--authorization',type=Path)
    args=parser.parse_args();run=ROOT/args.run
    if args.authorization is None:
        config,_=check_frozen(run);print(json.dumps(dict(status='PREPARED_NO_API',run_id=config['run_id'],protocol_hash=config['protocol_hash'])));return
    print(json.dumps(generate(run,args.authorization),ensure_ascii=False))
if __name__=='__main__':main()
