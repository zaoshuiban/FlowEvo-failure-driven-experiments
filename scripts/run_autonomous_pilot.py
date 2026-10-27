"""Authorized, bounded DeepSeek variant of autonomous MVP. No automatic retries."""
import argparse,hashlib,json,os,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import canonical,fingerprint,Fingerprint
from failure_evo.autonomous_generation import PROTOCOL,DeepSeekCompilerAdapter
from failure_evo.autonomous_mvp import AutonomousMVP,FrozenLinuxBackend,DeterministicRunner,LinuxPublicEvaluator,AutonomousHook
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperatorRegistry
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.runtime import Budget
from failure_evo.model_api import DeepSeekGenerator,configured_api_key
from failure_evo.evidence import EvidenceStore
from failure_evo.workflow_protocol_v2 import SharedTransport,WorkflowClient
from failure_evo.workflow_runtime_v2 import PreparedController
RUN=ROOT/'runs/autonomous_mvp_pilot_20261027_01'
def save(p,v):
    text=canonical(v)+'\n'
    if p.exists() and p.read_text()!=text:raise ValueError('immutable file differs: '+str(p))
    p.write_text(text)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
    data=json.loads((RUN/'preparation_v2/data.json').read_text())
    job=json.loads((ROOT/'reports/autonomous_mvp_v1/historical_replay_accepted/discovery_job.json').read_text())
    for path,h in data['source_files'].items():
        if digest(Path(path))!=h:raise ValueError('source hash changed')
    files=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/prepare_autonomous_pilot.py']
    deps={str(p.relative_to(ROOT)):digest(p) for p in sorted(files)}
    protocol=dict(run_id=RUN.name,variant='DEEPSEEK_AUTONOMOUS_PYTHON_NOT_GPT',model='deepseek-flash',
        generation_protocol=PROTOCOL,provider_contract='deepseek-json-object-client-strict-v1',
        data_sha256=digest(RUN/'preparation_v2/data.json'),discovery_sha256=fingerprint(job),dependencies=deps,
        worker=data['worker'],max_cost_microusd=2000000,generation_calls=3,future_solver_calls=4,
        generation_output_limit=4096,input_upper=32768,future_output_limit=8192,
        generation_budget_microusd=1700000,future_budget_microusd=300000,
        quote=dict(input_cache_miss_usd_per_million=.30,output_usd_per_million=1.20,
            url='https://api-docs.deepseek.com/quick_start/pricing/',checked_date='2026-10-27'),
        task_ids={k:[x['task']['problem_id'] for x in v] for k,v in data['groups'].items()},
        scope='exposed development; held out from this generation only; no causal cost comparison',
        stops=['NO_MECHANISM','generation contract failure','source ineffective after one revision',
               'independent gate failure','UNKNOWN request','worker fault','frozen hard budget'],
        future_condition='source and both independent repairs pass; both negatives decline; host gate passes',
        authorization='User explicitly authorized $2 and selected existing DeepSeek as generator; no GPT calls')
    save(RUN/'protocol.json',protocol)
    # Zero-API final induction wire; mock preflight never sends.
    a=DeepSeekCompilerAdapter(RUN/'preflight_provider.jsonl',Budget(),model='deepseek-flash',mock=True,sender=lambda _:None)
    req=dict(job,phase='induction',slot=0,max_tokens=4096);wire=a.preflight(req)
    upper=len(canonical(wire).encode())+256
    assert upper<=32768
    save(RUN/'frozen_induction_wire.json',wire)
    save(RUN/'preflight.json',dict(protocol_sha256=fingerprint(protocol),wire_sha256=fingerprint(wire),input_upper=upper,new_api_calls=0))
    return protocol,data,job

def budget(path,p,calls,cost,tools=100):
    return PersistentBudget(path,run_id=RUN.name,protocol_hash=fingerprint(p),max_calls=calls,
        max_tokens=calls*40960,max_tools=tools,max_cost_microusd=cost,
        token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,
        max_tool_milliseconds=2400000,tool_milliseconds_upper=120000,wall_seconds=3600)

def execute():
    p,data,job=prepare()
    if not configured_api_key():raise RuntimeError('DeepSeek key unavailable; no send')
    if (RUN/'execution_started.json').exists():raise RuntimeError('execution already started; audit before any resumption')
    save(RUN/'execution_started.json',dict(at=time.time(),protocol_sha256=fingerprint(p),authorized=True))
    tmp=RUN/'tmp';tmp.mkdir(exist_ok=True);tempfile.tempdir=str(tmp)
    b=budget(RUN/'generation_budget.jsonl',p,3,1700000)
    grant=dict(run_id=RUN.name,protocol_hash=fingerprint(p),model=p['model'],protocol=PROTOCOL,max_cost_microusd=1700000,paid_api_authorized=True)
    save(RUN/'authorization.json',dict(generation=grant,total_cap_microusd=2000000,future_cap_microusd=300000))
    provider=DeepSeekCompilerAdapter(RUN/'provider.jsonl',b,model=p['model'],authorization=grant)
    compiler=BoundedCompiler(provider,b,RUN/'compiler.jsonl',p['model'],max_input_upper=32768)
    backend=FrozenLinuxBackend(image=data['worker']['image'],worker_script=Path(data['worker']['worker_script']))
    assert backend.manifest()==data['worker']
    ev=FailureEvidenceStore(ROOT/'runs/s19_stream20_20261024_01/evidence_F.jsonl')
    registry=FailureOperatorRegistry(RUN/'registry.jsonl',ev)
    ctx=Fingerprint('native-five-stage','public-stdio-tokens-v1','deepseek-flash',fingerprint(p['dependencies']),PROTOCOL)
    m=AutonomousMVP(RUN/'learning',compiler,DeterministicRunner(backend),LinuxPublicEvaluator(backend),registry,ctx,b)
    start=time.monotonic()
    try:
        result=m.run(job,source=data['groups']['source'],independent=data['groups']['independent'],negative=data['groups']['negative'],at=time.time(),revise=True)
        save(RUN/'result.json',result)
        if result['status']=='READY_FOR_HOST_LIMITED_REVIEW':
            future={c['task']['problem_id']:c['lineage_id'] for c in data['groups']['future']}
            m.authorize(result,experiment_id=RUN.name,stream_id=RUN.name,after_task=0,effective_from=1,at=time.time(),future_tasks=future)
            solve_budget=budget(RUN/'future_budget.jsonl',p,4,300000)
            future_ev=FailureEvidenceStore(RUN/'future_evidence.jsonl')
            hook=AutonomousHook(registry,future_ev,ctx,stream_id=RUN.name,experiment_id=RUN.name,runner=m.runner)
            sender_log=EvidenceStore(RUN/'future_transport.jsonl')
            def sender(wire):
                sender_log.append('SEND_STARTED',dict(wire=json.loads(wire)),time.time())
                try:raw=DeepSeekGenerator._post(json.loads(wire),configured_api_key(),min(120,solve_budget.remaining_seconds))
                except BaseException as e:
                    sender_log.append('UNKNOWN',dict(error=type(e).__name__),time.time());raise
                sender_log.append('RAW_RESPONSE',dict(response=raw),time.time());return raw
            transport=SharedTransport(solve_budget,sender,authorized={'run_id':RUN.name,'protocol_hash':fingerprint(p)})
            for i,c in enumerate(data['groups']['future']):
                client=WorkflowClient(transport,f'{RUN.name}/future/{i}')
                def evaluate(task,code):return m._tool('future_public',lambda:m.evaluate(task,code))
                out=PreparedController(client,evaluate,ctx,plugin=hook).solve(c['task'],Budget(max_calls=2,max_tokens=81920,max_tools=50,wall_seconds=600))
                save(RUN/f'future_{i}.json',dict(result=out,transport=transport.audit))
        save(RUN/'completion.json',dict(status=result['status'],seconds=time.monotonic()-start,budget=b.snapshot()))
    except BaseException as e:
        save(RUN/'stopped.json',dict(error_type=type(e).__name__,reason=str(e),seconds=time.monotonic()-start,budget=b.snapshot()))
        raise
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--execute-authorized',action='store_true');a=parser.parse_args()
    if a.execute_authorized:execute()
    else:
        p,_,_=prepare();print('ZERO_API_FROZEN',fingerprint(p))
