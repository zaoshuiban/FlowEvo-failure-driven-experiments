"""Zero-model-API, single-thread Linux Worker acceptance; explicit oracle provenance."""
import json,pathlib,sys,tempfile,time,hashlib
P=pathlib.Path(__file__).resolve().parent;R=P.parents[1];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import configure_worker
from failure_evo.persistent_budget import PersistentBudget
from scorer import accepts
configure_worker(e.read(R/'reports/s19_v2_acceptance/worker_environment.json'))
(P/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(P/'tmp')
def run(j,ds,code,cases,stop_on_failure=False):
 start=time.monotonic();rows=[]
 with tempfile.TemporaryDirectory(prefix='external-v2-') as tmp:
  src=pathlib.Path(tmp)/'candidate.py';src.write_text(code)
  with j.ev.factory(src) as w:
   c=j.ev._charged('compile',lambda:w.call(dict(mode='compile_stdio',timeout=5)))
   if c.get('status')!='OK':return dict(passed=False,compile=c,seconds=time.monotonic()-start,tests_passed=0)
   for case in cases:
    raw=j.ev._charged('program-test',lambda:w.call(dict(mode='stdio',input=case['input'],timeout=5)))
    if raw.get('status') in ('EVALUATOR_ERROR','WORKER_ERROR'):raise RuntimeError('Worker infrastructure failure')
    good=raw.get('status')=='OK' and accepts(ds,case['expected'],raw.get('output',''))
    rows.append(dict(input_sha256=hashlib.sha256(case['input'].encode()).hexdigest(),expected_sha256=hashlib.sha256(case['expected'].encode()).hexdigest(),actual_sha256=hashlib.sha256(raw.get('output','').encode()).hexdigest(),worker_status=raw.get('status'),correct=good,stderr=raw.get('stderr','')[-500:]))
    if stop_on_failure and not good:break
 return dict(passed=len(rows)==len(cases) and all(r['correct'] for r in rows),tests_run=len(rows),tests_passed=sum(r['correct'] for r in rows),cases=rows,seconds=time.monotonic()-start)
while not (P/'selection_finalized.json').exists():time.sleep(20)
selection=e.read(P/'selected_metadata.json');protocol=dict(selection_sha256=e.sha(P/'selected_metadata.json'),inventory_sha256=e.sha(P/'inventory.json'),protocol_sha256=e.sha(P/'protocol.json'),scorer_sha256=e.sha(P/'scorer.py'),runner_sha256=e.sha(pathlib.Path(__file__)),worker_environment=e.read(R/'reports/s19_v2_acceptance/worker_environment.json'),model_calls=0,threads=1,initial_sealed_acceptance_count=6,reference_policy='Run up to two available human programs; agreement evidence separate from official IO provenance. No reference requirement.',positive_fixture='Exact input/output replay; tests Worker transport/scorer only, NOT algorithm correctness',negative='constant sentinel must be rejected on every checked case')
if (P/'worker_protocol.json').exists():assert e.read(P/'worker_protocol.json')==protocol
else:e.write(P/'worker_protocol.json',protocol)
rows=e.read(P/'worker_results.json') if (P/'worker_results.json').exists() else [];done={r['id'] for r in rows}
for role,items in selection.items():
 for meta in items:
  tid=meta['id']
  if tid in done:continue
  task=e.read(P/'candidates'/(tid+'.json'));cases=task['public_cases']+task['sealed_cases'][:6]
  b=PersistentBudget(P/'worker_ledgers'/(tid+'.jsonl'),run_id='external-v2-'+tid,protocol_hash=e.sha(P/'worker_protocol.json'),**e.prior.config(0,max(100,5*(len(cases)+1)),0));j=e.prior.Judge(b)
  mapping={c['input']:c['expected'] for c in cases}
  fixture='import sys\nanswers='+repr(mapping)+'\nsys.stdout.write(answers[sys.stdin.read()])\n'
  positive=run(j,task['dataset'],fixture,cases);negative=run(j,task['dataset'],"print('EXTERNAL_V2_INVALID_OUTPUT_SENTINEL')\n",cases)
  references=[]
  for ref in task['references']:
   result=run(j,task['dataset'],ref['code'],cases,stop_on_failure=True);references.append(dict(sha256=ref['sha256'],ast_sha256=ref['ast_sha256'],result=result))
   if result['passed']:break
  passed=positive['passed'] and negative['tests_passed']==0
  row=dict(id=tid,role=role,passed=passed,oracle='official expected output; replay fixture is not independent reference',positive_replay=positive,negative=negative,references=references,human_reference_agreement=any(r['result']['passed'] for r in references),budget=b.snapshot())
  rows.append(row);e.write(P/'worker_results.json',rows);print('WORKER',len(rows),tid,passed,'reference',row['human_reference_agreement'],flush=True)
  if not passed:raise RuntimeError('Per-task scoring/transport acceptance failed; no silent replacement')
# Separate runtime-visible data from final test and reference artifacts.
for role,items in selection.items():
 public=[];sealed=[];lineage=[]
 for meta in items:
  t=e.read(P/'candidates'/(meta['id']+'.json'))
  public.append(dict(task_id=t['id'],dataset=t['dataset'],difficulty=t['difficulty'],prompt=t['prompt'],public_cases=t['public_cases'],scorer='external-scorer-v2',official_split=t['official_split'],evidence_tier='B_STANDARD'))
  sealed.append(dict(task_id=t['id'],cases=t['sealed_cases'],visibility='sealed-final-only-after-online-lock'))
  lineage.append(meta)
 e.write(P/(role+'_public_tasks.json'),public);e.write(P/(role+'_sealed_tasks.json'),sealed);e.write(P/(role+'_lineage.json'),lineage)
e.write(P/'acceptance_summary.json',dict(status='DATA_READY_NO_MODEL_API',tasks=len(rows),passed=sum(r['passed'] for r in rows),human_reference_agreement=sum(r['human_reference_agreement'] for r in rows),official_oracle_only=sum(not r['human_reference_agreement'] for r in rows),model_requests=0,local_seconds=sum(r['positive_replay']['seconds']+r['negative']['seconds']+sum(x['result']['seconds'] for x in r['references']) for r in rows),limitations=['Metadata output-contract screening is conservative but not a semantic proof','Oracle replay tests transport, not reference algorithm correctness','Initial sealed Worker checks cover six per task; all remaining official tests preserved','Approximate near-duplicate retrieval can miss paraphrases','Already exposed strict 60 retained separately; no historical results rewritten']))
print('COMPLETE',flush=True)
