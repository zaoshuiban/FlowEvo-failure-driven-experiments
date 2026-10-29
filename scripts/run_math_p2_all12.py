"""Freeze then run a separately authorized engineering-only P2. No scorer input."""
import argparse,hashlib,json,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.math_p2_all_failures import *
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.math_operators import MathOperatorRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
SOURCE=ROOT/'runs/math_p1_remaining82_20261027_01'
IMAGE='sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8'
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def budget(root,ph):return PersistentBudget(root/'budget.jsonl',run_id=root.name,protocol_hash=ph,max_calls=7,max_tokens=516096,max_tools=78,max_cost_microusd=8000000,token_rate_microusd_per_million=15000000,tool_cost_upper_microusd=0,max_tool_milliseconds=1560000,tool_milliseconds_upper=20000,wall_seconds=3600)
def freeze(root):
 if root.exists():raise RuntimeError('new empty run required')
 rows=json.loads((SOURCE/'confirmed_failures.json').read_text());view=evidence_view(rows)
 locked={x['payload']['locked_sha256']:x['payload'] for x in EvidenceStore(SOURCE/'controller.jsonl').records() if x['kind']=='MATH_ANSWER_LOCKED'}
 scores={x['payload']['evidence_id']:x['payload'] for x in EvidenceStore(SOURCE/'scores.jsonl').records() if x['kind']=='DISCOVERY_SCORED'}
 for r in rows:
  assert scores[r['evidence_id']]==r
  lock=locked[r['locked_sha256']]
  assert fingerprint({k:v for k,v in lock.items() if k!='locked_sha256'})==r['locked_sha256']
  assert lock['responses']==r['responses'] and lock['task_id']==r['task_id']
 backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
 image=json.loads(subprocess.check_output(['docker','image','inspect',IMAGE]))[0]
 assert image['Id']==IMAGE
 catalog=json.load(urllib.request.urlopen('https://openrouter.ai/api/v1/models',timeout=30))
 model=next(x for x in catalog['data'] if x['id']=='openai/gpt-5.4')
 assert float(model['pricing']['prompt'])<=0.0000025 and float(model['pricing']['completion'])<=0.000015
 files=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+list((ROOT/'FlowEvo/src/code_math').glob('*.py'))+[Path(__file__).resolve(),WORKER]
 hashes={str(p.relative_to(ROOT)):sha(p) for p in files}
 protocol=dict(version=VERSION,run_id=root.name,model='gpt-5.4',provider='OpenRouter restricted OpenAI; no fallback',model_catalog=model,
  git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_hashes=hashes,
  evidence_file_sha256=sha(SOURCE/'confirmed_failures.json'),evidence_view_sha256=fingerprint(view),
  old_run_hashes={str(p.relative_to(ROOT)):sha(p) for p in SOURCE.glob('*') if p.is_file()},
  max_calls=7,max_candidates=3,max_revisions_each=1,max_output_tokens=8192,max_wire_input_upper=65536,hard_usd=8,
  conservative_reservation_usd=7.74144,uncached_directional_max_usd=2.00704,worker=backend.manifest(),
  engineering_only=True,source_gold_scoring=False,independent_tasks=False,gate=False,performance_comparison=False,
  permission='SHADOW_ONLY',stop_on_unknown=True,selection='all twelve confirmed final failures in time order',
  revision_policy='one engineering-only revision per proposed mechanism; no answer scoring; no manual algorithm changes')
 ph=fingerprint(protocol);root.mkdir(parents=True)
 save(root/'protocol.json',protocol);save(root/'freeze.json',dict(protocol_sha256=ph,at=time.time()))
 save(root/'source_failures.json',rows);save(root/'learning_view.json',view)
 for rel in hashes:
  p=root/'frozen_source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/rel).read_bytes())
 # Zero API final-wire validation with explicit mock transport, not a paid grant.
 b=budget(root,ph);a=AllFailuresGPTAdapter(root/'preflight.jsonl',b,model='gpt-5.4',mock=True,sender=lambda w:None,max_wire_input_upper=65536)
 wire=a.preflight(dict(discovery={'events':rows},arm='F',phase='induction',slot=0,max_tokens=8192))
 save(root/'induction_wire.json',wire);save(root/'preflight_summary.json',dict(wire_sha256=fingerprint(wire),wire_upper=len(canonical(wire).encode())+256,events=12,paid_requests=0))
 print(json.dumps(dict(protocol_sha256=ph,wire_upper=len(canonical(wire).encode())+256,events=12)))
def run(root):
 p=json.loads((root/'protocol.json').read_text());ph=fingerprint(p);assert ph==json.loads((root/'freeze.json').read_text())['protocol_sha256']
 for rel,digest in p['source_hashes'].items():
  if sha(ROOT/rel)!=digest:raise RuntimeError('frozen code drift: '+rel)
 rows=json.loads((root/'source_failures.json').read_text());assert fingerprint(evidence_view(rows))==p['evidence_view_sha256']
 b=budget(root,ph);grant=json.loads((root/'authorization.json').read_text())
 a=AllFailuresGPTAdapter(root/'provider.jsonl',b,model='gpt-5.4',authorization=grant,max_wire_input_upper=65536)
 wire=a.preflight(dict(discovery={'events':rows},arm='F',phase='induction',slot=0,max_tokens=8192))
 assert wire==json.loads((root/'induction_wire.json').read_text())
 c=BoundedCompiler(a,b,root/'compiler.jsonl','gpt-5.4',max_input_upper=65536,max_output_upper=8192)
 r=MathOperatorRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),budget=b)
 try:
  result=AllFailuresEngineering(root/'candidates',c,r).run({'events':rows})
  save(root/'COMPLETE.json',dict(result=result,budget=b.snapshot(),at=time.time()))
  print(json.dumps(result),flush=True)
 except BaseException as e:
  save(root/'STOP.json',dict(error=type(e).__name__,message=str(e)[:500],budget=b.snapshot(),no_retry=True));raise
 finally:
  save(root/'historical_integrity.json',{rel:sha(ROOT/rel)==d for rel,d in p['old_run_hashes'].items()})
if __name__=='__main__':
 q=argparse.ArgumentParser();q.add_argument('mode',choices=['freeze','run']);q.add_argument('--run',required=True);a=q.parse_args()
 (freeze if a.mode=='freeze' else run)(Path(a.run).resolve())
