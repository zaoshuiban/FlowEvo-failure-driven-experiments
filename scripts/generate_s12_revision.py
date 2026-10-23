"""Prepare or execute one candidate + one optional revision under a fresh budget."""
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
from failure_evo.model_api import DeepSeekGenerator, CANDIDATE_SYSTEM_PROMPT, COMPILE_OUTPUT_SCHEMA
from failure_evo.compiler_contract import build_compiler_contract
from failure_evo.candidate_revision import compile_candidate, REVISION_INSTRUCTION


def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare(run):
    run.mkdir(parents=True,exist_ok=False)
    source=ROOT/'runs/s12b2_20261021_01'
    job=read(source/'generation_input.json')
    job.update(stream_id=run.name,job_id=fingerprint([job['job_id'],run.name]),host_contract=build_compiler_contract())
    write(run/'generation_input.json',job)
    (run/'specification.txt').write_text(job['specification'])
    (run/'candidate_prompt.txt').write_text(CANDIDATE_SYSTEM_PROMPT)
    (run/'revision_instruction.txt').write_text(REVISION_INSTRUCTION)
    write(run/'host_contract.json',job['host_contract']);write(run/'compile_schema.json',COMPILE_OUTPUT_SCHEMA)
    write(run/'candidate_request.json',DeepSeekGenerator.prepare(dict(job,phase='candidate',slot=0,max_tokens=4096)))
    # Exact revision input is unknown until the candidate arrives; freeze its algorithm,
    # template and full input ceiling, then persist the constructed input before calling.
    budget=dict(max_calls=2,max_tokens=139264,max_tools=0,max_cost_microusd=200000,
        token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,
        max_tool_milliseconds=0,tool_milliseconds_upper=10000,wall_seconds=3600)
    paths=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__).resolve()]
    paths+=list((ROOT/'FlowEvo/tests').glob('test_failure_evo*.py'))+list(run.glob('*'))
    paths+=[source/'generation_input.json',source/'specification_v2.txt',ROOT/'runs/s12a2_20261021_01/data/discovery_facts.jsonl']
    original=read(ROOT/'runs/s12a2_20261021_01/data/discovery_input.json')
    paths += [ROOT/r['source_path'] for r in original['checkpoint']['candidate_ledger']]
    config=dict(run_id=run.name,model='deepseek-flash',budget=budget,
        facts_path='runs/s12a2_20261021_01/data/discovery_facts.jsonl',
        input_upper=65536,output_upper=4096,candidates=1,revisions_per_candidate=1,retries=0,
        scope='one family; static-only Shadow; no execution, gate or Experimental',
        stop_policy='No source/transport failure: stop. Static failure with complete source: one revision. Revision rejected: stop. No unconditional applied requirement.',
        quote=dict(date='2026-10-21',source='https://api-docs.deepseek.com/quick_start/pricing/',input_usd_per_million=.3,output_usd_per_million=1.2,conservative_upper_microusd=167118),
        frozen_files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))})
    config['protocol_hash']=fingerprint(config);write(run/'protocol.json',config)
    write(run/'authorization.pending.json',dict(api_spend_authorized=False,run_id=run.name,
        protocol_hash=config['protocol_hash'],max_cost_microusd=200000,user_authorization_text=''))
    return config


def check(run):
    config=read(run/'protocol.json')
    if fingerprint({k:v for k,v in config.items() if k!='protocol_hash'})!=config['protocol_hash']:raise ValueError('protocol changed')
    for path,digest in config['frozen_files'].items():
        if sha(ROOT/path)!=digest:raise ValueError('frozen file changed: '+path)
    job=read(run/'generation_input.json')
    if job['host_contract']!=build_compiler_contract():raise ValueError('host contract changed')
    if DeepSeekGenerator.prepare(dict(job,phase='candidate',slot=0,max_tokens=4096))!=read(run/'candidate_request.json'):raise ValueError('wire request changed')
    return config,job


def generate(run,approval_path):
    config,job=check(run)
    if any((run/p).exists() for p in ('result.json','budget.jsonl','compiler.jsonl','candidate_1')):raise FileExistsError('run already attempted; no automatic restart')
    approval=read(approval_path)
    expected=dict(api_spend_authorized=True,run_id=config['run_id'],protocol_hash=config['protocol_hash'],max_cost_microusd=config['budget']['max_cost_microusd'])
    if any(approval.get(k)!=v for k,v in expected.items()) or not approval.get('user_authorization_text'):raise PermissionError('new run-bound spending authorization required')
    store=FailureEvidenceStore(ROOT/config['facts_path']);known={e['event_id']:e for e in store.visible(time.time())}
    if any(e not in known or known[e]['synthetic'] for e in job['evidence_ids']):raise ValueError('trusted failure evidence unavailable')
    budget=PersistentBudget(run/'budget.jsonl',run_id=config['run_id'],protocol_hash=config['protocol_hash'],**config['budget'])
    compiler=BoundedCompiler(DeepSeekGenerator(budget,authorization=approval),budget,run/'compiler.jsonl',config['model'])
    compiler.import_specification(job,run/'specification.txt',time.time())
    result=compile_candidate(compiler,job,0,run/'candidate_1')
    result['conclusion']='PARTIAL' if result['source_acceptance']=='SHADOW_STATIC_ONLY' else 'NO-GO'
    result['experimental_authorizations']=0
    if result['source_acceptance']=='SHADOW_STATIC_ONLY':
        card=FailureOperator(run.name+'-candidate-1',result['accepted_phase'],result['accepted_artifact'],result['accepted_sha256'],
            Fingerprint('public-feedback-adapted-v2','not-executed',config['model'],config['protocol_hash'],'S1.2-diagnostic-revision'),
            'historical-incomplete-artifact-development',tuple(job['evidence_ids']),('lcb_atcoder_abc371_f',))
        FailureOperatorRegistry(run/'shadow_registry.jsonl',store).register(card,time.time())
    write(run/'result.json',result);return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--prepare',action='store_true');p.add_argument('--authorization',type=Path)
    args=p.parse_args();run=ROOT/args.run
    if args.prepare:
        if args.authorization:p.error('prepare does not accept spending authorization')
        config=prepare(run);print(json.dumps(dict(status='PREPARED_NO_API',protocol_hash=config['protocol_hash'])));return
    if args.authorization:print(json.dumps(generate(run,args.authorization),ensure_ascii=False))
    else:
        config,_=check(run);print(json.dumps(dict(status='FROZEN_NO_API',protocol_hash=config['protocol_hash'])))
if __name__=='__main__':main()
