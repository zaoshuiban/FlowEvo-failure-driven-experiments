"""One real induction and three candidate requests; AST checks only, no execution."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo import PersistentBudget,BoundedCompiler,FailureEvidenceStore,FailureOperatorRegistry,FailureOperator,Fingerprint
from failure_evo.contracts import fingerprint
from failure_evo.model_api import DeepSeekGenerator,configured_api_key


def static_review(code):
    out=dict(executed=False,interface_runtime='NOT_TESTED',findings=[])
    try:
        tree=ast.parse(code)
        compile(tree,'<generated-shadow>','exec')  # Bytecode validation only; never execute.
    except (SyntaxError,ValueError,TypeError) as exc:
        return dict(out,syntax_pass=False,interface_static_pass=False,policy_static_pass=False,error_type=type(exc).__name__)
    funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='repair_operator']
    interface=len(funcs)==1
    if interface:
        f=funcs[0];a=f.args
        interface=(len(a.posonlyargs)+len(a.args)==1 and not a.vararg and not a.kwarg and
                   not a.kwonlyargs and not a.defaults and not f.decorator_list)
    allowed={'ast','json','math','collections','itertools','functools','re','heapq','bisect','fractions','statistics'}
    forbidden={'open','eval','exec','compile','getattr','setattr','globals','locals','vars','input','breakpoint','help'}
    for n in ast.walk(tree):
        if isinstance(n,ast.Import) and any(x.name.split('.')[0] not in allowed for x in n.names):out['findings'].append('forbidden_import')
        if isinstance(n,ast.ImportFrom) and (n.level or (n.module or '').split('.')[0] not in allowed):out['findings'].append('forbidden_import')
        if isinstance(n,ast.Name) and (n.id.startswith('__') or n.id in forbidden):out['findings'].append('forbidden_name:'+n.id)
        if isinstance(n,ast.Attribute) and n.attr.startswith('__'):out['findings'].append('dunder_attribute')
        if isinstance(n,(ast.AsyncFunctionDef,ast.Await,ast.Yield,ast.YieldFrom)):out['findings'].append('non_synchronous_interface')
    out['findings']=sorted(set(out['findings']))
    return dict(out,syntax_pass=True,interface_static_pass=interface,policy_static_pass=not out['findings'])


def main():
    run=ROOT/'runs/s12b_shadow_20261021_01'
    if (run/'result.json').exists():
        raise FileExistsError('run already attempted; preserve evidence, no automatic retry')
    config=json.loads((run/'protocol.json').read_text())
    if fingerprint({k:v for k,v in config.items() if k!='protocol_hash'})!=config['protocol_hash']:
        raise ValueError('protocol changed')
    if not configured_api_key():raise RuntimeError('credential unavailable')
    source=ROOT/config['input_path']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=config['input_sha256']:raise ValueError('discovery input changed')
    store=FailureEvidenceStore(ROOT/config['facts_path'])
    job=json.loads(source.read_text())
    known={e['event_id']:e for e in store.visible(time.time())}
    if any(e not in known or known[e]['synthetic'] for e in job['evidence_ids']):raise ValueError('trusted source evidence unavailable')
    for desc in job['checkpoint']['candidate_ledger']:
        if hashlib.sha256((ROOT/desc['source_path']).read_bytes()).hexdigest()!=desc['sha256']:raise ValueError('historical artifact changed')
    budget=PersistentBudget(run/'budget.jsonl',run_id=config['run_id'],protocol_hash=config['protocol_hash'],**config['budget'])
    approval=dict(api_spend_authorized=True,run_id=config['run_id'],protocol_hash=config['protocol_hash'],max_cost_microusd=config['budget']['max_cost_microusd'])
    provider=DeepSeekGenerator(budget,authorization=approval)
    compiler=BoundedCompiler(provider,budget,run/'compiler.jsonl','deepseek-flash')
    registry=FailureOperatorRegistry(run/'shadow_registry.jsonl',store)
    job=dict(job,stream_id=config['run_id'],execution_scope='SHADOW_ONLY_STATIC_REVIEW',
        additional_contract='Use the existing payload public_feedback status and candidate ledger public_feedback. Only host-verified PUBLIC_PASS counts as pass; unknown or failed validation must decline. Never assume unavailable historical public checks passed.')
    result=dict(run_id=config['run_id'],status='RUNNING',candidates=[],runtime_evaluation='NOT_RUN',independent_gate='NOT_RUN',experimental_authorizations=0)
    def save():
        result['budget']=budget.snapshot()
        (run/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    save()
    try:
        print('Requesting specification induction',flush=True)
        spec=compiler.request(job,'induction',0,time.time())['specification']
        (run/'specification.txt').write_text(spec)
        print('Specification saved; requesting three candidates',flush=True)
        for slot in range(3):
            item=dict(slot=slot,state='Shadow')
            try:
                response=compiler.request(dict(job,specification=spec), 'candidate',slot,time.time())
                code=response['code'];path=run/('candidate_'+str(slot+1)+'.py');path.write_text(code)
                digest=hashlib.sha256(code.encode()).hexdigest()
                review=static_review(code)
                item.update(artifact_path=str(path.relative_to(ROOT)),sha256=digest,review=review,model=response['model'],usage=response.get('usage',{}))
                card=FailureOperator('shadow-recovery-'+str(slot+1),'v1',str(path),digest,
                    Fingerprint('public-feedback-adapted-v2','not-executed',response['model'],config['base_commit'],'S1.2-shadow-static'),
                    'historical-incomplete-artifact-development',tuple(job['evidence_ids']),('lcb_atcoder_abc371_f',))
                registry.register(card,time.time())
                item['static_acceptance']=all(review[k] for k in ('syntax_pass','interface_static_pass','policy_static_pass'))
                print('Candidate',slot+1,'saved; static acceptance:',item['static_acceptance'],flush=True)
            except Exception as exc:
                item.update(generation_status='FAILED',error_type=type(exc).__name__)
                print('Candidate',slot+1,'failed:',type(exc).__name__,'(no retry)',flush=True)
            result['candidates'].append(item);save()
        result['status']='COMPLETED_SHADOW_ONLY' if all('sha256' in c for c in result['candidates']) else 'PARTIAL_SHADOW_ONLY'
    except Exception as exc:
        result.update(status='STOPPED',error_type=type(exc).__name__)
        print('Run stopped:',type(exc).__name__,'(no retry)',flush=True)
    finally:save()

if __name__=='__main__':main()
