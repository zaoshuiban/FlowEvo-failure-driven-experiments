"""Zero-model functional audit. Freeze code/tasks, execute, lock, then private score."""
import argparse,hashlib,json,sys,time,subprocess,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_operators import MathOperatorRunner,validate_math_source
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from code_math.no_gold import PublicMathTask
DATA=ROOT/'reports/math_no_gold_p0_20261027/data'
P2=ROOT/'runs/math_p2_all12_20261027_01'
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
IMAGE='sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def readlines(p):return [json.loads(x) for x in p.read_text().splitlines()]
def prepare(out):
 if out.exists():raise ValueError('new audit directory required')
 reviews=[r['payload'] for r in EvidenceStore(P2/'candidates_bound/engineering.jsonl').records() if r['kind']=='CANDIDATE_ENGINEERING']
 sources=json.loads((P2/'source_failures.json').read_text());source_by={r['evidence_id']:r for r in sources}
 design=readlines(DATA/'public/design.jsonl');assert len(design)==48
 assert not {r['task_id'] for r in sources}&{r['task_id'] for r in design}
 assert not {' '.join(r['task']['problem'].split()) for r in sources}&{' '.join(r['problem'].split()) for r in design}
 artifacts=[];jobs=[]
 for rev in reviews:
  a=rev['artifact'];assert sha(a['source_path'])==a['code_sha256'];assert validate_math_source(Path(a['source_path']).read_text())['passed']
  artifacts.append(dict(slot=rev['slot'],operator_id=a['operator_id'],source_path=a['source_path'],code_sha256=a['code_sha256'],origin=a['origin']))
  for e in a['source_event_ids']:jobs.append(dict(slot=rev['slot'],role='Source',task=source_by[e]['task']))
  for task in design:PublicMathTask.parse(task);jobs.append(dict(slot=rev['slot'],role='Design',task=task))
 assert len(jobs)==156
 manifest=json.loads((DATA/'manifest.json').read_text())
 # Only hash authorized scoring files; no Gate/Legacy/Fresh access.
 inputs={str(p.relative_to(ROOT)):sha(p) for p in [DATA/'public/design.jsonl',DATA/'private/design.jsonl',DATA/'private/discovery.jsonl']}
 for rel,d in inputs.items():assert d==manifest['files'][str(Path(rel).relative_to(DATA.relative_to(ROOT)))]
 freeze=dict(version='math-p3-frozen-functional-audit-v1',created_at=time.time(),artifacts=artifacts,jobs=jobs,input_hashes=inputs,
  script_sha256=sha(__file__),worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),
  selection='all original per-mechanism sources + all 48 P0 Design tasks, original order, no replacement',
  no_model_calls=True,no_revision=True,no_admission=True,gate_legacy_fresh_untouched=True,
  scorer='exact rational match/mismatch; symbolic nonmatch unverified',
  limitation='Design is held-out from generation but same targeted parameterized distribution, not independent original problem families',
  historical_hashes={str(p.relative_to(ROOT)):sha(p) for p in P2.rglob('*') if p.is_file() and not p.name.endswith('.lock')})
 save(out/'freeze.json',freeze);save(out/'freeze_receipt.json',dict(sha256=fingerprint(freeze)))
 print('Frozen',len(jobs),'executions',fingerprint(freeze),flush=True)
def execute(out):
 f=json.loads((out/'freeze.json').read_text());assert fingerprint(f)==json.loads((out/'freeze_receipt.json').read_text())['sha256'];assert sha(__file__)==f['script_sha256']
 journal=EvidenceStore(out/'execution.jsonl')
 if journal.records():raise RuntimeError('audit already started; do not silently rerun')
 artifacts={a['slot']:a for a in f['artifacts']};runner=MathOperatorRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER));results=[]
 for i,j in enumerate(f['jobs']):
  a=artifacts[j['slot']];assert sha(a['source_path'])==a['code_sha256']
  result=runner.run(a,PublicMathTask.parse(j['task']))
  row=dict(index=i,slot=j['slot'],role=j['role'],task_id=j['task']['task_id'],problem_sha256=fingerprint(j['task']['problem']),result=result)
  journal.append('OUTPUT_LOCKED',row,time.time());results.append(row)
  if (i+1)%20==0:print('executed',i+1,flush=True)
 save(out/'outputs_locked.json',results);save(out/'outputs_lock.json',dict(sha256=sha(out/'outputs_locked.json'),count=len(results),at=time.time()))
 subprocess.run([sys.executable,__file__,'score','--out',str(out)],check=True)
 checks={p:sha(ROOT/p)==d for p,d in f['historical_hashes'].items()};assert all(checks.values());save(out/'historical_integrity.json',checks)
def score(out):
 # Separate process: private data is first loaded after all operator outputs are locked.
 from code_math.private_math_scoring import normalized
 assert sha(out/'outputs_locked.json')==json.loads((out/'outputs_lock.json').read_text())['sha256']
 f=json.loads((out/'freeze.json').read_text());results=json.loads((out/'outputs_locked.json').read_text());assert len(results)==len(f['jobs'])
 private={}
 for role,file in [('Source','discovery.jsonl'),('Design','design.jsonl')]:
  p=DATA/'private'/file;assert sha(p)==f['input_hashes'][str(p.relative_to(ROOT))]
  private[role]={r['task_id']:r for r in readlines(p)}
 scores=[]
 for r in results:
  q=private[r['role']][r['task_id']];assert q['problem_sha256']==r['problem_sha256']
  value=r['result'];status=value['status'];matched=None
  if status=='APPLIED':
   pred=normalized(value['answer']);gold=normalized(q['gold_answer'])
   if pred==gold:status='CORRECT';matched=True
   elif pred[0]==gold[0]=='rational':status='WRONG';matched=False
   else:status='UNVERIFIED'
  scores.append(dict(index=r['index'],slot=r['slot'],role=r['role'],task_id=r['task_id'],status=status,correct=matched,code_sha256=value['code_sha256']))
 save(out/'scores.json',scores)
 summary={}
 for slot in range(3):
  summary[str(slot+1)]={role:dict(collections.Counter(r['status'] for r in scores if r['slot']==slot and r['role']==role)) for role in ('Source','Design')}
 save(out/'summary.json',dict(operators=summary,model_calls=0,total_worker_calls=len(results),worker_seconds=sum(r['result']['seconds'] for r in results),gold_sent_to_operator=False,source_modified=False,experimental=0))
 print(json.dumps(summary),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','execute','score']);p.add_argument('--out',required=True);a=p.parse_args();globals()[a.mode](Path(a.out).resolve())
