"""New authorized real DeepSeek source diagnostic; no independent gate fabrication.
Old development controls are frozen BEFORE calls and cannot grant Experimental.
"""
import argparse,json,hashlib,sys,time,tempfile,urllib.request
from pathlib import Path
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import canonical,fingerprint,Fingerprint
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.evidence import EvidenceStore
from failure_evo.trusted_learning_evidence import InputValidator,TrustedLearningEvidence
from failure_evo.symptom_learning import SymptomLearning
from failure_evo.compile_queue import BoundedCompiler,CompileQueue
from failure_evo.learning import LearningLoop
from failure_evo.autonomous_mechanism import VERSION
from failure_evo.autonomous_deepseek_v2 import DeepSeekMechanismConfig,DeepSeekMechanismAdapter
from failure_evo.autonomous_pipeline import ExecutableLearningPipeline
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.failure_registry import FailureOperatorRegistry
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.runtime import Budget
from prepare_autonomous_pilot import legal,IMAGE,WORKER
RUN=ROOT/'runs/autonomous_v2_deepseek_source_20261027_01'
OLD=ROOT/'runs/autonomous_mvp_pilot_20261027_01/preparation_v2/data.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj):
 p=RUN/name;data=canonical(obj)+'\n'
 if p.exists() and p.read_text()!=data:raise ValueError('immutable artifact changed: '+name)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
def validator(task):
 p=ROOT/'scripts/prepare_autonomous_pilot.py'
 return InputValidator('reviewed-statement-grammar','v1',task['problem_id'],fingerprint(task['prompt']),str(p),sha(p),'exact task and statement','statement bounds; imports pinned in protocol',legal)
def prepare():
 RUN.mkdir(exist_ok=True);(RUN/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(RUN/'tmp')
 store=FailureEvidenceStore(ROOT/'runs/s19_stream20_20261024_01/evidence_F.jsonl')
 eid='3d4039df0e43985b4a9b79a1aa61041c89612570595096effc2130b4a5073195'
 fact=next(e for e in store.visible(time.time()) if e['event_id']==eid)
 # Reuse the original earliest visible evidence, not S22's later outcome.
 prior=json.loads((ROOT/'reports/autonomous_mvp_v1/historical_replay_accepted/discovery_job.json').read_text())
 row=prior['discovery']['evidence'][0];task=dict(row['task'])
 task['public_examples']=[dict(input=c['input'],expected=c['expected'],visibility='public',legal_verified=True) for c in task['public_examples']]
 cases=row['feedback']['public_cases']
 cases=[json.loads(c) if isinstance(c,str) else c for c in cases]
 cp=dict(event_id=eid,task=task,code=row['code'],observed_at=fact['observed_at'],lineage_id=fact['provenance_group_id'],
   feedback=dict(status=row['feedback']['status'],summary=row['feedback']['summary'],visibility='public',cases=[dict(c,visibility='public',legal_verified=True) for c in cases]))
 old=json.loads(OLD.read_text());development=old['groups']['independent']+old['groups']['negative']
 vals={c['task']['problem_id']:validator(c['task']) for c in development};vals[task['problem_id']]=validator(task)
 for c in development:
  assert all(vals[c['task']['problem_id']].verify(c['task'],x['input'])['valid'] for x in c['task']['public_examples'])
 # Only a selected real historical event is exposed to scheduling; no model results involved.
 class Selected:
  def __init__(self):self.artifacts=store.artifacts;self.events=EvidenceStore(RUN/'task_end_projection.jsonl')
  def visible(self,at,stream_id=None):return tuple(x for x in store.visible(at,stream_id) if x['event_id']==eid)
 selected=Selected()
 # Bind a real task completion; keep historical ledgers read-only.
 original_events=store.events.records()
 completions=[r for r in original_events if r['kind']=='TASK_COMPLETED' and r['payload'].get('task_id')==fact['task_id']]
 if not completions:
  stream=ROOT/'runs/s19_stream20_20261024_01/stream.jsonl'
  completions=[r for r in map(json.loads,stream.read_text().splitlines()) if r['kind']=='TASK_FINALIZED' and r['payload']['task_id']==fact['task_id']]
 if not completions:raise ValueError('actual task-end receipt missing')
 if not selected.events.records():selected.events.append('TASK_COMPLETED',dict(stream_id=fact['stream_id'],task_id=fact['task_id'],historical_receipt_hash=fingerprint(completions[0])),time.time())
 queue=CompileQueue(RUN/'queue.jsonl');loop=LearningLoop(queue,selected,fact['stream_id'],RUN/'loop.jsonl')
 jobs=loop.pending(time.time());assert len(jobs)==1
 admission=TrustedLearningEvidence(selected,RUN/'admission.jsonl',vals)
 # Deterministic admission cutoff: historical evidence prefix, not future outcomes.
 cutoff=max(fact['available_from'],fact['observed_at'])
 public=admission.build(loop.public_input(jobs[0],time.time()),{eid:cp},at=cutoff)
 save('public_job.json',public);save('development_controls.json',development)
 # Official pricing page only; zero model requests for metadata preparation.
 quote_path=RUN/'pricing_official.html'
 if not quote_path.exists():
  quote_path.write_bytes(urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing/',timeout=30).read())
 metadata=dict(model='deepseek-flash',official_version='DeepSeek-V4.1-Flash-1017',
   peak_input_cache_miss_usd_per_million=.30,peak_input_cache_hit_usd_per_million=.006,peak_output_usd_per_million=1.20,
   off_peak_input_cache_miss_usd_per_million=.15,off_peak_input_cache_hit_usd_per_million=.003,off_peak_output_usd_per_million=.60,
   source='https://api-docs.deepseek.com/quick_start/pricing/',checked_date='2026-10-27',page_sha256=sha(quote_path),
   peak_hours_utc='Mon-Fri 01-04 and 06-10 except Chinese holidays; peak quote retained as conservative estimate')
 save('model_metadata.json',metadata)
 cfg=DeepSeekMechanismConfig('deepseek-flash','DeepSeek-V4.1-Flash-1017',300000,1200000,metadata['source'],'2026-10-27')
 # Same public learning material and same controls as GPT; never copy GPT output.
 prior=ROOT/'runs/autonomous_v2_gpt_source_20261027_04'
 assert public==json.loads((prior/'public_job.json').read_text())
 assert development==json.loads((prior/'development_controls.json').read_text())
 save('input_parity.json',dict(source_public_job_identical=True,development_controls_identical=True,gpt_hypothesis_injected=False,gpt_code_injected=False))
 files=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__),ROOT/'scripts/prepare_autonomous_pilot.py',ROOT/'scripts/s24_input_legality.py',WORKER]
 historical=[OLD,ROOT/'reports/autonomous_mvp_v1/historical_replay_accepted/discovery_job.json',ROOT/'runs/s19_stream20_20261024_01/evidence_F.jsonl']
 p=dict(run_id=RUN.name,protocol=VERSION,model=asdict(cfg),provider='DeepSeek official API; no retry',reasoning_effort='none',thinking='disabled',temperature=0,response_format='json_object + strict host schema validation',
   max_calls=3,max_input_upper=65536,max_output_upper=8192,candidate_limit=1,max_revisions=1,
   max_cost_microusd=3*((73728*max(cfg.input_microusd_per_million,cfg.output_microusd_per_million)+999999)//1000000),
   cost_policy='derived reservation envelope for bounded calls, not a user-imposed spending limit',
   solver='deepseek-flash unchanged; no solving calls in source-only diagnostic',
   user_authorization='换成DeepSeek试一下；承接本次实验不再询问预算授权',authorization_scope='new real generation and source diagnostic; no repeated generations beyond frozen count',
   source_event=eid,source_cutoff=cutoff,public_job_sha256=fingerprint(public),development_controls_sha256=fingerprint(development),
   independent_data_status='UNAVAILABLE: existing natural controls are development-exposed; never relabel unexposed',
   stop_after_source=True,permission_ceiling='shadow',confirmation119_used=False,external419_used=False,
   no_target_algorithm_provided=True,no_reference_source_in_generation=True,
   worker={'image':IMAGE,'script_sha256':sha(WORKER)},dependencies={str(f.relative_to(ROOT)):sha(f) for f in files},
   historical_inputs={str(f.relative_to(ROOT)):sha(f) for f in historical},
   stops=['NO_MECHANISM','HYPOTHESIS_ONLY','contract rejection','UNKNOWN','Worker fault','source failure after one revision','bounded requests exhausted'],
   research_scope='exposed-source mechanism development, not H1 independent confirmation')
 save('protocol.json',p)
 a=DeepSeekMechanismAdapter(RUN/'preflight_provider.jsonl',Budget(),config=cfg,mock=True,sender=lambda _:None,max_wire_input_upper=65536)
 wire=a.preflight(dict(public,phase='induction',slot=0,max_tokens=8192));save('frozen_induction_wire.json',wire)
 save('preflight.json',dict(protocol_sha256=fingerprint(p),wire_sha256=fingerprint(wire),wire_input_upper=len(canonical(wire).encode())+256,new_model_calls=0))
 return p,public,cfg,selected,loop,vals,development

def execute():
 p,job,cfg,store,loop,vals,development=prepare()
 if (RUN/'execution_started.json').exists():raise ValueError('run already consumed; no automatic resume')
 save('execution_started.json',dict(at=time.time(),protocol_sha256=fingerprint(p)))
 b=PersistentBudget(RUN/'budget.jsonl',run_id=RUN.name,protocol_hash=fingerprint(p),max_calls=3,max_tokens=221184,max_tools=100,
   max_cost_microusd=p['max_cost_microusd'],token_rate_microusd_per_million=max(cfg.input_microusd_per_million,cfg.output_microusd_per_million),
   tool_cost_upper_microusd=0,max_tool_milliseconds=12000000,tool_milliseconds_upper=120000,wall_seconds=3600)
 auth=dict(run_id=RUN.name,protocol_hash=fingerprint(p),model=cfg.model,protocol=VERSION,max_cost_microusd=p['max_cost_microusd'],paid_api_authorized=True)
 save('authorization.json',auth)
 adapter=DeepSeekMechanismAdapter(RUN/'provider.jsonl',b,config=cfg,authorization=auth,max_wire_input_upper=65536)
 compiler=BoundedCompiler(adapter,b,RUN/'compiler.jsonl',cfg.model,max_input_upper=65536,max_output_upper=8192)
 backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
 registry=FailureOperatorRegistry(RUN/'registry.jsonl',store)
 ctx=Fingerprint('native-five-stage','public-stdio-tokens-v1','deepseek-flash',fingerprint(p['dependencies']),VERSION)
 pipe=ExecutableLearningPipeline(RUN/'pipeline',compiler,b,registry,ctx,backend,input_validators=vals)
 pipe.job=job;pipe.at=time.time()
 pipe.manifest={'discovery':{'source_groups':sorted({e['lineage_id'] for e in job['discovery']['evidence']})},'design':{'source_groups':[]}}
 pipe.sources=[dict(case_id=e['event_id'],task=dict(e['task'],public_examples=[dict(c,visibility='public',legal_verified=True) for c in e['task']['public_examples']]),code=e['code'],lineage_id=e['lineage_id'],expectation='repair') for e in job['discovery']['evidence']]
 results=[];status='STARTING'
 try:
  # Real native baseline must be reproducible BEFORE first generation.
  source=pipe.sources[0]
  from failure_evo.contracts import PublicTaskView
  baseline=pipe._engine._tool('source_baseline_preflight',lambda:pipe.evaluator(PublicTaskView.project(source['task']),source['code']))
  save('baseline.json',baseline)
  if baseline['status'] in ('PUBLIC_PASS','EVALUATOR_ERROR'):raise RuntimeError('source no longer valid failure')
  spec=compiler.request(job,'induction',0,time.time(),output_upper=8192)
  h=pipe._hypothesis(spec['specification'],job)
  if h['decision']!='PROPOSE':status=h['decision']
  else:
   payload=dict(job,specification=spec['specification'])
   for version in range(2):
    phase='candidate' if version==0 else 'revision'
    resp=compiler.request(payload,phase,0,time.time(),output_upper=8192)
    review=pipe._design(resp['code'],{'cases':[]},b.remaining_seconds)
    save('source_review_v'+str(version)+'.json',review);results.append(review)
    if review['source_effective']:
     controls=[];card=pipe._card(resp['code'])
     for i,c in enumerate(development):
      c=dict(c,expectation='repair' if i<2 else 'decline')
      controls.extend(pipe._cases(card,[c]))
     save('exposed_development_validation.json',dict(rows=controls,independent_confirmation=False,authorization=False))
     status='SOURCE_EFFECTIVE_SHADOW_INDEPENDENT_DATA_REQUIRED';break
    status='SOURCE_INEFFECTIVE_SHADOW' if review['static']['static_pass'] else 'STATIC_REJECTED'
    if version==0:
     # Only actual source diagnostics; no reference repair or future validation feedback.
     diagnostics=dict(static=review['static'],source=review['source'],source_effective=False)
     payload=dict(payload,code=resp['code'],design_feedback=diagnostics)
  save('result.json',dict(status=status,versions=len(results),source_effective=any(r['source_effective'] for r in results),experimental=0,future_calls=0,
    independent_validation='NOT_RUN_NO_FRESH_FROZEN_DATA',budget=b.snapshot()))
 except BaseException as exc:
  save('stopped.json',dict(status='STOPPED',error=type(exc).__name__,reason=str(exc),budget=b.snapshot()));raise
 finally:
  loop.queue.events.append('COMPILE_ATTEMPTED',{k:job[k] for k in ('job_id','stream_id','family_id','evidence_ids','completed_tasks')},time.time())
  save('historical_integrity_after.json',{f:sha(ROOT/f)==h for f,h in p['historical_inputs'].items()})
 if any(not v for v in json.loads((RUN/'historical_integrity_after.json').read_text()).values()):raise RuntimeError('historical mutation')
 print(status,flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--execute-authorized',action='store_true');args=a.parse_args()
 if args.execute_authorized:execute()
 else:
  p,*_=prepare();print('ZERO_API_FROZEN',fingerprint(p))
