"""Read-only historical evidence -> compiler wire acceptance; NEVER sends model API.
Real learning success cannot be inferred from this test or the engineering Mock loop.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import canonical,fingerprint
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.symptom_learning import SymptomLearning
from failure_evo.compile_queue import CompileQueue,BoundedCompiler
from failure_evo.autonomous_generation import GPTCompilerAdapter
from failure_evo.autonomous_mvp import discover_jobs
from failure_evo.runtime import Budget
from s24_input_legality import validate


def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    protocol=ROOT/'runs/s23_context_probe_20261026_01/protocol.json'
    storepath=ROOT/'runs/s19_stream20_20261024_01/evidence_F.jsonl'
    packet=json.loads(protocol.read_text())['tasks'][0]['checkpoint']
    assert packet['task_id']=='s18_taco-test-91'
    store=FailureEvidenceStore(storepath)
    fact=next(e for e in store.visible(1e12) if e['event_id']==packet['event_id'])
    artifact=store.artifacts/(fact['candidate_sha256']+'.py')
    oldhash={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (protocol,storepath,artifact)}
    at=fact['available_from']
    tests=packet['public_cases']
    legality=[validate(packet['task_id'],c['input']) for c in tests]
    assert all(x['valid'] for x in legality)
    cp=dict(event_id=fact['event_id'],task=packet['task_public'],code=packet['code'],
        feedback=dict(visibility='public',status=packet['feedback']['status'],cases=[dict(c,visibility='public',legal_verified=True) for c in packet['feedback']['public_cases']]),
        observed_at=fact['observed_at'],lineage_id=fact['provenance_group_id'])
    audit=out/'legality.json';audit.write_text(canonical(dict(passed=True,checkpoint_sha256=fingerprint(cp),checks=legality,
        method='existing s24 input grammar for s18_taco-test-91; no model/generated answers'))+'\n')
    cp['legality_audit']=dict(path=str(audit),sha256=hashlib.sha256(audit.read_bytes()).hexdigest(),passed=True,checkpoint_sha256=fingerprint(cp))
    index=SymptomLearning(out/'symptoms.jsonl',store,fact['stream_id'])
    queue=CompileQueue(out/'queue.jsonl')
    jobs=discover_jobs(store,index,queue,{fact['event_id']:cp},at=at,completed_tasks=1)
    assert len(jobs)==1
    budget=Budget(max_calls=3,max_tokens=300000)
    def no_network(_):raise AssertionError('ZERO API acceptance must never send')
    provider=GPTCompilerAdapter(out/'gpt.jsonl',budget,model='gpt-5.4-2026-03-05',mock=True,sender=no_network)
    request=dict(jobs[0],phase='induction',slot=0,max_tokens=4096)
    wire=provider.preflight(request)
    compiler_upper=max(len(str(request).encode())+4096,len(canonical(wire).encode())+256)
    assert compiler_upper<=32768
    (out/'discovery_job.json').write_text(canonical(jobs[0])+'\n')
    (out/'wire.json').write_text(canonical(wire)+'\n')
    # True real-mode preflight must refuse absent authorization before reserving.
    real=GPTCompilerAdapter(out/'real_guard.jsonl',budget,model='gpt-5.4-2026-03-05')
    compiler=BoundedCompiler(real,budget,out/'compiler.jsonl',real.model,max_input_upper=32768)
    blocked=False
    try:compiler.request(jobs[0],'induction',0,at)
    except PermissionError:blocked=True
    assert blocked and budget.calls==0
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in oldhash.items())
    report=dict(status='PASS_ZERO_API_REAL_EVIDENCE_TO_WIRE',new_model_requests=0,
        historical_selection='First source of frozen S23 protocol; engineering replay only, not a new efficacy sample',
        source_event=fact['event_id'],time_cutoff=at,source_hashes=oldhash,
        legal_public_cases=len(tests),wire_sha256=fingerprint(wire),wire_bytes=len(canonical(wire).encode()),
        input_upper=len(canonical(wire).encode())+256,compiler_input_upper=compiler_upper,input_limit=32768,
        raw_source_unchanged=True,unauthorized_real_request_blocked=blocked,
        hypothesis='NOT_GENERATED',operator='NOT_GENERATED',H1='NOT_TESTED',
        source_scope='Only earliest original public checkpoint; no S23 treatment outcomes or final/sealed tests')
    (out/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    main(parser.parse_args().output)
