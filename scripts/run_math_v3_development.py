"""Finite F/T development generation. No hidden reference data in request process."""
import json,sys,time,hashlib,subprocess,urllib.request,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import fingerprint,canonical
from failure_evo.evidence import EvidenceStore
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.math_operator_v3_pipeline import CorrectiveAdapter,VERSION
from failure_evo.corrective_mechanism import parse,difference_check
from failure_evo.semantic_contract import artifact,SplitRunner
from failure_evo.operator_test_generation import parse_proposals,IndependentOracle
from failure_evo.operator_version_gate import VersionGate
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from code_math.no_gold import PublicMathTask
P2=ROOT/'runs/math_p2_all12_20261027_01';DATA=ROOT/'reports/math_no_gold_p0_20261027/data'
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
IMAGE='sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def freeze(out):
 if out.exists():raise RuntimeError('new run only')
 evidence=json.loads((P2/'source_failures.json').read_text());h=json.loads((P2/'normalized_hypothesis.json').read_text())
 groups=[m['source_event_ids'] for m in h['mechanisms']]
 model=next(x for x in json.load(urllib.request.urlopen('https://openrouter.ai/api/v1/models',timeout=30))['data'] if x['id']=='openai/gpt-5.4')
 assert float(model['pricing']['completion'])<=.000015 and float(model['pricing']['prompt'])<=.0000025
 files=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__).resolve()]
 p=dict(version=VERSION,created_at=time.time(),git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  groups=groups,order=[dict(arm=a,group=i) for i in range(3) for a in ('F','T')],model=model,
  max_requests_per_group_arm=3,output_upper=12288,input_upper=65536,derived_reservation_usd_per_job=4,
  authorization='Current user v3 implementation explicitly requests real GPT development; finite calls, no funding-based research success criterion',
  source_hashes={str(p.relative_to(ROOT)):sha(p) for p in files},evidence_sha256=fingerprint(evidence),
  design_sha256=sha(DATA/'public/design.jsonl'),worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),
  history_hashes={str(p.relative_to(ROOT)):sha(p) for d in [P2,ROOT/'runs/math_p3_functional_audit_20261027_01'] for p in d.rglob('*') if p.is_file() and not p.name.endswith('.lock')},
  reference_alias_policy='Exact unique supplied task IDs may map to evidence IDs; record both. No mechanism text edits.',
  revision='One engineering-only correction at most; do not alter algorithm by hand',gate='Only if both independently reviewed computation and applicability pass; otherwise no Gate exposure',
  task_only='Identical source questions and interfaces; no failures, old code or F hypotheses. Historical source grouping is development selection.',
  ablations='V0 immutable; component swaps only if input interfaces compatible and baseline separation substantiated, else NOT_GENERATED')
 save(out/'protocol.json',p);save(out/'freeze.json',dict(sha256=fingerprint(p)));save(out/'evidence.json',evidence)
 for rel in p['source_hashes']:
  q=out/'frozen_source'/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/rel).read_bytes())
 print('Frozen',fingerprint(p),flush=True)
def run(out,resume=False):
 p=json.loads((out/'protocol.json').read_text());ph=fingerprint(p)
 assert ph==json.loads((out/'freeze.json').read_text())['sha256']
 for rel,d in p['source_hashes'].items():
  if resume and rel==str(Path(__file__).resolve().relative_to(ROOT)):
   assert sha(__file__)==json.loads((out/'orchestration_amendment.json').read_text())['new_script_sha256']
  else:assert sha(ROOT/rel)==d,rel
 evidence=json.loads((out/'evidence.json').read_text());assert fingerprint(evidence)==p['evidence_sha256']
 if (out/'STARTED.json').exists() and not resume:raise RuntimeError('run already consumed; no automatic resend')
 if not resume:save(out/'STARTED.json',dict(at=time.time()))
 results=[]
 try:
  for spec in p['order']:
   arm=spec['arm'];g=spec['group'];d=out/(arm+str(g+1))
   if d.exists():
    if not resume:raise RuntimeError('existing job')
    old=EvidenceStore(d/'provider.jsonl').records()
    if any(x['kind']=='SEND_UNKNOWN' for x in old):raise RuntimeError('UNKNOWN cannot resume')
    starts=[x for x in old if x['kind']=='SEND_STARTED'];responses=[x for x in old if x['kind']=='RAW_RESPONSE']
    if len(starts)!=len(responses):raise RuntimeError('pending/unknown cannot resume')
    if (d/'result.json').exists():results.append(json.loads((d/'result.json').read_text()));continue
    if (d/'artifact.json').exists():raise RuntimeError('unrecorded artifact requires review')
    last=responses[-1]['payload']['response']
    if last['choices'][0]['finish_reason']!='length':raise RuntimeError('unrecognized recovery')
    result=dict(arm=arm,group=g,status='NOT_GENERATED',reason='known truncated response; not resent')
    save(d/'result.json',result);results.append(result);continue
   d.mkdir()
   b=PersistentBudget(d/'budget.jsonl',run_id=d.name+':'+out.name,protocol_hash=ph,max_calls=3,max_tokens=233472,max_tools=0,max_cost_microusd=4000000,token_rate_microusd_per_million=15000000,tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=20000,wall_seconds=1800)
   grant=dict(run_id=b.config['run_id'],protocol_hash=ph,model='gpt-5.4',protocol=VERSION,max_cost_microusd=4000000,paid_api_authorized=True);save(d/'authorization.json',grant)
   a=CorrectiveAdapter(d/'provider.jsonl',b,model='gpt-5.4',authorization=grant,max_wire_input_upper=65536)
   c=BoundedCompiler(a,b,d/'compiler.jsonl','gpt-5.4',max_input_upper=65536,max_output_upper=12288)
   job=dict(stream_id=b.config['run_id'],family_id='v3',arm=arm,source_ids=p['groups'][g],discovery={'events':evidence})
   response=c.request(job,'induction',0,time.time(),output_upper=12288)
   m=parse(json.loads(response['specification']));original=copy.deepcopy(m);aliases={r['task_id']:r['evidence_id'] for r in evidence if r['evidence_id'] in p['groups'][g]}
   m['source_evidence_ids']=[aliases.get(x,x) for x in m['source_evidence_ids']]
   if not set(m['source_evidence_ids'])<=set(p['groups'][g]):raise ValueError('unknown source reference')
   save(d/'mechanism.json',dict(raw=original,normalized=m,difference=difference_check(m),response_sha256=response['response_sha256']))
   if m['generation_decision']!='PROPOSE_CORRECTION':
    results.append(dict(arm=arm,group=g,status=m['generation_decision']));continue
   job['specification']=canonical(m)
   for attempt in range(2):
    try:r=c.request(job,'candidate' if attempt==0 else 'revision',0,time.time(),output_upper=12288)
    except ValueError as exc:
     if str(exc)!='COMPILE_OUTPUT_CONTRACT_ERROR':raise
     results.append(dict(arm=arm,group=g,status='NOT_GENERATED',reason='known structured output rejection',error=str(exc)));break
    save(d/f'generation_{attempt}.json',r)
    try:
     metadata=json.loads(r['description'])
     if set(metadata)!={'contract','tests'}:raise ValueError('description contract/tests required')
     parse_proposals(metadata['tests'])
     art=artifact(d/'artifacts',r['code'],r['applicability'],metadata['contract'],provenance=dict(origin=r['origin'],response_sha256=r['response_sha256'],request_sha256=r['wire_sha256'],source_evidence_ids=m['source_evidence_ids'],excluded_task_ids=[x['task_id'] for x in evidence],model=r['model']),parent=None)
     runner=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),d/'worker.jsonl')
     controls=[runner.run(art,PublicMathTask('source',x['task']['problem'])) for x in evidence if x['evidence_id'] in p['groups'][g]]
     controls.append(runner.run(art,PublicMathTask('no-question','No mathematical question is supplied.')))
     if any(x['status']=='ERROR' for x in controls):raise ValueError('Component execution/return contract error')
     if controls[-1]['status']!='DECLINED':raise ValueError('nonmathematical refusal control')
     save(d/'artifact.json',art);save(d/'engineering.json',controls)
     tests=IndependentOracle([],candidate_hashes=[art['solver_sha256'],art['matcher_sha256']]).audit_all(metadata['tests']);save(d/'test_proposals.json',tests)
     VersionGate(out/'registry.jsonl').shadow(art)
     results.append(dict(arm=arm,group=g,status='SHADOW_ENGINEERING',joint_sha256=art['code_sha256'],test_proposals=len(tests),test_oracles_verified=0));break
    except (ValueError,TypeError,KeyError) as e:
     save(d/f'engineering_rejection_{attempt}.json',dict(error=str(e),no_gold=True))
     if attempt==1:results.append(dict(arm=arm,group=g,status='NOT_GENERATED',error=str(e)));break
     job.update(previous=dict(code=r['code'],description=r['description'],applicability=r['applicability']),engineering_errors=[str(e)])
   save(d/'result.json',results[-1]);print(json.dumps(results[-1]),flush=True)
  save(out/'COMPLETE.json',results)
 except BaseException as e:
  stop=dict(type=type(e).__name__,message=str(e),completed=results,no_resend=True)
  EvidenceStore(out/'stops.jsonl').append('STOP',stop,time.time())
  save(out/('STOP_'+str(time.time_ns())+'.json'),stop);raise
 finally:save(out/'history_integrity.json',{rel:sha(ROOT/rel)==d for rel,d in p['history_hashes'].items()})
if __name__=='__main__':
 mode=sys.argv[1];out=Path(sys.argv[2]).resolve()
 if mode=='freeze':freeze(out)
 else:run(out,resume=mode=='resume')
