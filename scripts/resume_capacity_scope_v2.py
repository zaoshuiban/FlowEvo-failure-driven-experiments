"""One remaining revision after LOCAL oversized request; original evidence stays intact."""
import argparse, copy, json, shutil, time
from pathlib import Path
from experiment_capacity_scope_v2 import ROOT, OLD, ScopeStudy, PROMPT, read, write, sha, freeze, base_config
from failure_evo import BoundedCompiler
from failure_evo.contracts import canonical, fingerprint
from failure_evo.model_api import DeepSeekGenerator, validate_compile_output

class CompactScopeGenerator(DeepSeekGenerator):
    @staticmethod
    def prepare(request):
        compact=copy.deepcopy(request)
        parent=compact.get('version_parent',{})
        if 'code' in parent:
            parent['omitted_code_sha256']=fingerprint(parent.pop('code'))
            parent['omission']='Superseded version; actual revision_parent source remains complete.'
        for failure in compact.get('functional_diagnostics',{}).get('failure_diagnostics',[]):
            code=failure.pop('diagnostic_program',None)
            if code is not None:
                failure['diagnostic_program_sha256']=fingerprint(code)
                failure['omission']='Repeated same-reason source variants; full host diagnostic archived, source failure and current Operator remain complete.'
        return DeepSeekGenerator.prepare(compact,system_prompt=PROMPT)


def prepare(run,parent):
    run.mkdir(exist_ok=False);(run/'tmp').mkdir()
    previous=read(parent/'candidate_1/result.json')
    assert previous['versions'][-1]['error_type']=='ValueError'
    requests=[r for r in (read_lines(parent/'compiler.jsonl')) if r['kind']=='GENERATION_REQUESTED']
    assert len(requests)==1 and requests[0]['payload']['phase']=='candidate'
    for name in ['worker_acceptance.json','specification.txt','development_cases.json','sealed_cases.json','controls.json','frame_specs.json','scope_diagnostics.json','compile_prompt.txt']:
        shutil.copy2(parent/name,run/name)
    job=read(parent/'generation_input.json');job.update(stream_id=run.name,job_id=fingerprint([run.name,job['job_id']]))
    write(run/'generation_input.json',job)
    req=read(parent/'candidate_1/revision_input.json');req.update(stream_id=run.name,job_id=job['job_id'])
    req['host_source_review']=['Static inspection: only direct fact bounded-index reads enter target_tables; inverse table dependency/alias is not included.',
        'Static inspection: existing Transformer does not change table allocation RHS, though capacity expansion requires coherent allocations and initialization.',
        'Observed runtime: mixed_initializer decline prevents every source/positive repair. Preserve independent non-target recurrence rather than widening its bounds; decline remains correct if safety cannot be established.']
    write(run/'revision_input.json',req)
    wire=CompactScopeGenerator.prepare(dict(req,phase='revision',slot=0,max_tokens=4096))
    upper=max(len(str(dict(req,phase='revision',slot=0,max_tokens=4096)).encode())+4096,len(canonical(wire).encode())+256)
    assert upper<=65536
    write(run/'revision_wire.json',wire)
    config=base_config(run,1)
    config.update(experiment_type='same_v2_experiment_remaining_revision_after_local_preflight_failure',parent_run=parent.name,
        total_experiment_request_cap=2,total_experiment_currency_cap_microusd=250000,
        compaction='Only redundant superseded source and repeated diagnostic program bodies omitted from WIRE; full original request/feedback archived and hash bound; current revision source and real failures retained.',
        frozen_wire_sha256=fingerprint(wire),wire_bytes=len(canonical(wire).encode()),input_token_upper=upper)
    config['generation_budget'].update(max_calls=1,max_tokens=69632,max_cost_microusd=100000)
    spent=read(parent/'budget_snapshots.json')['generation']['charged_or_reserved_cost_microusd']
    assert spent+100000<=250000
    config['parent_closed_charged_or_reserved_microusd']=spent
    freeze(run,config,[Path(__file__).resolve(),parent/'candidate_1/candidate.py',parent/'candidate_1/candidate.json',parent/'candidate_1/candidate-design-review.json',parent/'compiler.jsonl'])
    print('FROZEN_REMAINING_ONE_REQUEST',upper,len(canonical(wire).encode()),flush=True)


def read_lines(path):return [json.loads(l) for l in path.read_text().splitlines()]


def execute(run):
    if (run/'compiler.jsonl').exists():raise FileExistsError('one remaining revision already attempted')
    study=ScopeStudy(run);b=study.budgets['generation'];a=read(run/'authorization.json');parent=ROOT/'runs'/study.config['parent_run']
    def transport(body,key,timeout):
        assert fingerprint(body)==study.config['frozen_wire_sha256']
        write(run/'transport_audit.json',dict(wire_sha256=fingerprint(body),wire_bytes=len(canonical(body).encode()),send_started=True))
        return DeepSeekGenerator._post(body,key,timeout)
    compiler=BoundedCompiler(CompactScopeGenerator(b,authorization=dict(a,run_id=b.config['run_id']),transport=transport),b,run/'compiler.jsonl',study.config['model'])
    req=read(run/'revision_input.json');compiler.import_specification(study.job,run/'specification.txt',time.time())
    compiler.import_candidate(req,0,parent/'candidate_1/candidate.py',parent/'candidate_1/candidate.json',time.time())
    functional=read(parent/'candidate_1/candidate-design-review.json')
    assert req['functional_diagnostics']==functional
    compiler.events.append('CANDIDATE_FUNCTIONAL_REVIEW',dict(stream_id=req['stream_id'],family_id=req['family_id'],slot=0,phase='candidate',artifact_sha256=sha(parent/'candidate_1/candidate.py'),review=functional),time.time())
    directory=run/'candidate_1';directory.mkdir()
    result=dict(slot=0,versions=[],source_acceptance='NOT_ACCEPTED',functional_acceptance='NOT_RUN')
    final=dict(conclusion='NO_GO_V2_REVISION',nursery=False,sealed_consumed=False,old_winner='suspended_unchanged',parent_run=parent.name)
    try:
        response=compiler.request(req,'revision',0,time.time())
        path=directory/'revision.py';path.write_text(response['code'])
        review=validate_compile_output(response.get('rejected_compile_output',{k:response.get(k) for k in ('code','description','applicability')}),response['finish_reason'])
        write(directory/'revision.json',dict(response=response,review=review))
        version=dict(phase='revision',artifact_path=str(path.resolve()),sha256=sha(path),review=review,usage=response.get('usage'),model=response.get('model'));result['versions'].append(version)
        if review['static_pass']:
            result['source_acceptance']='SHADOW_STATIC_ONLY'
            dev=study.inspect_version(path,'design');version['functional_review']=dev
            result['functional_acceptance']='DEVELOPMENT_PASSED_NOT_GATE' if dev['eligible'] else 'DEVELOPMENT_FAILED'
            print('REVISION_DEVELOPMENT',dev['eligible'],dev['source_reason'],flush=True)
        write(run/'p1.json',[result]);registry=study.register_shadows()
        if result['functional_acceptance']=='DEVELOPMENT_PASSED_NOT_GATE':
            result.update(accepted_artifact=str(path.resolve()),accepted_sha256=sha(path),accepted_phase='revision')
            write(run/'winner.json',result)
            sealed=study.inspect_version(path,'sealed');write(run/'p2.json',sealed)
            final.update(conclusion='PARTIAL_SEALED_FAILED_NO_RESELECTION',sealed_consumed=True,artifact_sha256=sha(path))
            if sealed['eligible']:
                admitted=study.admit(result,registry)
                final.update(conclusion='GO_BOUNDED_NURSERY_SCOPE_V2' if admitted else 'PARTIAL_HOST_FAILED',nursery=admitted)
    except Exception as exc:
        result.update(error_type=type(exc).__name__,error=str(exc));raise
    finally:
        write(run/'p1.json',[result]);write(directory/'result.json',result);write(run/'decision.json',final)
        write(run/'budget_snapshots.json',{k:v.snapshot() for k,v in study.budgets.items()});print(json.dumps(final),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--parent');p.add_argument('--prepare',action='store_true');a=p.parse_args()
    if a.prepare:prepare(ROOT/a.run,ROOT/a.parent)
    else:execute(ROOT/a.run)
