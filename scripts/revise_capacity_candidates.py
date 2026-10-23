"""Fresh diagnostic run: revise saved candidates 1 then conditionally 3, once each.
No new induction, initial generation, P3 paid comparison or sealed-data reselection.
"""
import argparse, ast, copy, json, shutil, sys, time
from pathlib import Path
from experiment_capacity_nursery import (ROOT, BASE, Study, CapacityGenerator, read, write, sha, h, IMAGE)
from failure_evo import BoundedCompiler, FailureOperatorRegistry, FailureEvidenceStore
from failure_evo.contracts import fingerprint, canonical
from failure_evo.compiler_contract import build_compiler_contract
from failure_evo.model_api import validate_compile_output, DeepSeekGenerator
from failure_evo.candidate_revision import REVISION_INSTRUCTION
OLD=ROOT/'runs/s12g_capacity_20261022_01'


def diagnostics(code):
    return [dict(line=n.lineno,operation=n.attr if isinstance(n,ast.Attribute) else n.id)
            for n in ast.walk(ast.parse(code)) if
            (isinstance(n,ast.Attribute) and n.attr.startswith('__')) or
            (isinstance(n,ast.Name) and n.id in {'getattr','setattr','open','exec','eval','compile','vars','globals','locals','input'})]


def prepare(run):
    run.mkdir(exist_ok=False);(run/'tmp').mkdir()
    config=copy.deepcopy(read(OLD/'protocol.json'))
    for name in ('worker_acceptance.json','development_cases.json','sealed_cases.json','controls.json','specification.txt'):
        shutil.copy2(OLD/name,run/name)
    job=read(OLD/'generation_input.json');job.update(job_id=fingerprint([run.name,job['job_id']]),stream_id=run.name,host_contract=build_compiler_contract())
    write(run/'generation_input.json',job)
    requests={}
    for number,slot in [(1,0),(3,2)]:
        request=read(OLD/f'candidate_{number}/revision_input.json')
        request.update(job_id=job['job_id'],stream_id=run.name,host_contract=job['host_contract'],specification=(run/'specification.txt').read_text())
        request['exact_permission_diagnostics']=diagnostics(request['revision_parent']['code'])
        request['revision_instruction']=REVISION_INSTRUCTION+'\nThis is a diagnostic revision of an existing real artifact, not fresh generation. Fix the attached line-specific prohibited operations using permitted Python syntax. Preserve input-length meaning and the declared scope. No model calls inside the Operator. Return exactly code, description, applicability; no specification field.'
        request.update(phase='revision',slot=slot,max_tokens=4096)
        wire=CapacityGenerator.prepare(request)
        upper=max(len(str(request).encode())+4096,len(canonical(wire).encode())+256)
        assert upper<=65536
        write(run/f'revision_{number}_input.json',request);write(run/f'revision_{number}_wire.json',wire)
        requests[str(number)]=dict(wire_sha256=fingerprint(wire),wire_bytes=len(canonical(wire).encode()),input_token_upper=upper,output_token_upper=4096)
    config.update(run_id=run.name,experiment_type='saved_failed_candidate_diagnostic_revision_not_fresh_generation',
        order=[1,3],second_request_condition='Candidate 1 revision fails static or development; never after sealed review failure',
        max_real_requests=2,quote=read(OLD/'protocol.json')['quote'],requests=requests,
        scope='one revision per selected saved candidate; immediate isolated development; first eligible winner; one sealed review; optional bounded nursery; no P3/P4',
        selection='First revision in frozen order passing static and development; no model feedback from sealed cases; no reselection',
        authorization_basis='Current user explicitly requests bounded real revision and verification: 修复; new 0.20 USD maximum, no inherited budget')
    config['p3']={'status':'OUT_OF_SCOPE','max_calls':0};config['p4']={'status':'OUT_OF_SCOPE','max_calls':0}
    config['candidate_count']=0
    config['generation_budget'].update(max_calls=2,max_tokens=139264,max_cost_microusd=200000)
    config['continuation_budget'].update(max_calls=0,max_tokens=0,max_cost_microusd=0)
    config['evaluation_budget'].update(max_tools=500,max_tool_milliseconds=5000000)
    paths=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/experiment_capacity_nursery.py']+list(run.glob('*.json'))+[run/'specification.txt',OLD/'compiler.jsonl']
    for number in (1,3):paths += [OLD/f'candidate_{number}/candidate.py',OLD/f'candidate_{number}/candidate.json',OLD/f'candidate_{number}/revision_input.json']
    config['frozen_files']={str(p.resolve().relative_to(ROOT)):sha(p) for p in paths}
    config.pop('protocol_hash',None);config['protocol_hash']=fingerprint(config);write(run/'protocol.json',config)
    write(run/'authorization.json',dict(api_spend_authorized=True,run_id=run.name,protocol_hash=config['protocol_hash'],max_cost_microusd=200000,user_authorization_text='修复',maximum_requests=2))
    archive=run/'frozen_sources'
    for name,digest in config['frozen_files'].items():
        target=archive/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    print('FROZEN_NO_API',json.dumps(requests),flush=True)


def execute(run):
    if (run/'compiler.jsonl').exists():raise FileExistsError('diagnostic run already attempted')
    study=Study(run);budget=study.budgets['generation'];approval=read(run/'authorization.json')
    assert approval['api_spend_authorized'] is True and approval['protocol_hash']==study.config['protocol_hash']
    auth=dict(approval,run_id=budget.config['run_id'])
    expected={r['wire_sha256'] for r in study.config['requests'].values()}
    def transport(body,key,timeout):
        digest=fingerprint(body)
        if digest not in expected:raise ValueError('transport differs from frozen final preflight')
        with (run/'transport_audit.jsonl').open('a') as out:
            out.write(canonical(dict(event='SEND_STARTED',at=time.time(),wire_sha256=digest,wire_bytes=len(canonical(body).encode())))+'\n')
        return DeepSeekGenerator._post(body,key,timeout)
    compiler=BoundedCompiler(CapacityGenerator(budget,authorization=auth,transport=transport),budget,run/'compiler.jsonl',study.config['model'])
    compiler.import_specification(dict(study.job),run/'specification.txt',time.time())
    registry=FailureOperatorRegistry(run/'registry.jsonl',FailureEvidenceStore(BASE/'failure_facts.jsonl'))
    results=[];final=dict(conclusion='NO_GO_THIS_DIAGNOSTIC_RUN',winner=None,nursery=False,functional_recovery='NOT_ESTABLISHED',p3='NOT_RUN_BY_SCOPE')
    try:
        for number,slot in [(1,0),(3,2)]:
            request=read(run/f'revision_{number}_input.json');directory=run/f'candidate_{number}';directory.mkdir()
            item=dict(original_candidate=number,versions=[],source_acceptance='NOT_ACCEPTED',functional_acceptance='NOT_RUN');results.append(item)
            compiler.import_candidate(request,slot,OLD/f'candidate_{number}/candidate.py',OLD/f'candidate_{number}/candidate.json',time.time())
            try:
                response=compiler.request(request,'revision',slot,time.time())
                code=response['code'];path=directory/'revision.py';path.write_text(code)
                review=validate_compile_output({k:response.get(k) for k in ('code','description','applicability')},response['finish_reason'])
                write(directory/'revision.json',dict(response=response,review=review))
                item.update(accepted_artifact=str(path.resolve()),accepted_sha256=sha(path),accepted_phase='revision',static_review=review)
                if not review['static_pass']:
                    item['stop_reason']='REVISION_STATIC_REJECTED';continue
                card=study.card(path);registry.register(card,time.time());item['source_acceptance']='SHADOW_STATIC_ONLY'
                development=study.inspect_version(path,'design');item['development']=development
                print('candidate',number,'static PASS; development',development['eligible'],'source',development['source_passed'],flush=True)
                if not development['eligible']:
                    item['stop_reason']='REVISION_DEVELOPMENT_FAILED';continue
                item['functional_acceptance']='DEVELOPMENT_PASSED_NOT_GATE';write(run/'winner.json',item)
                sealed=study.inspect_version(path,'sealed');write(run/'p2.json',sealed);item['sealed']=sealed
                final.update(winner=number,functional_recovery='SOURCE_DEVELOPMENT_PASSED')
                if not sealed['eligible']:
                    final.update(conclusion='PARTIAL_SEALED_REVIEW_FAILED_NO_RESELECTION');break
                admitted=study.admit(item,registry)
                final.update(conclusion='GO_BOUNDED_NURSERY' if admitted else 'PARTIAL_HOST_ACCEPTANCE_FAILED',nursery=admitted)
                break
            except Exception as exc:
                item.update(stop_reason='REVISION_OR_EVALUATION_ERROR',error_type=type(exc).__name__,error=str(exc))
                print('candidate',number,type(exc).__name__,str(exc),flush=True)
            finally:
                write(run/'results.json',results);write(run/'budget_snapshots.json',{k:v.snapshot() for k,v in study.budgets.items()})
    finally:
        write(run/'decision.json',final)
        write(run/'budget_snapshots.json',{k:v.snapshot() for k,v in study.budgets.items()})
        print(json.dumps(final),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    (prepare if args.prepare else execute)(ROOT/args.run)
