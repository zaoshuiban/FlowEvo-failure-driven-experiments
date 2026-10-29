"""All candidates fixed, exact generated code in existing Worker, score after lock."""
import time,json,collections
from run_algorithm_evidence import OUT,ROOT,WORKER,IMAGE,load,save,sha,fingerprint,verify
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.semantic_contract import component_check
from failure_evo.evidence import EvidenceStore

def evaluate():
 p=verify();freeze=load(OUT/'candidate_freeze.json');cases=load(OUT/'private/cases.json');inp=load(OUT/'inputs.json');d=OUT/'evaluation'
 if d.exists():raise RuntimeError('one evaluation only')
 save(d/'start.json',dict(at=time.time(),candidates_sha256=fingerprint(freeze),script_sha256=sha(__file__),worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest()))
 journal=EvidenceStore(d/'worker.jsonl');backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER);results=[]
 for a in freeze['results']:
  family=inp[str(a['group'])]['family'];selected=[c for c in cases if (c['role']=='source' and c['group']==a['group']) or (c['role']!='source' and c['family']==family)]
  if a['status']!='STATIC_VALID_SHADOW':
   results.extend(dict(key=a['key'],arm=a['arm'],group=a['group'],replica=a['replica'],case_id=c['case_id'],role=c['role'],raw=dict(status='NOT_EXECUTED',generation_status=a['status'])) for c in selected);continue
  path=__import__('pathlib').Path(a['solver_path']);assert sha(path)==a['solver_sha256'] and component_check(path.read_text(),'solve')['passed']
  with backend(path) as w:
   for c in selected:
    request=dict(mode='function',function='solve',args=[c['parameters']],timeout=2);start=time.monotonic();raw=w.call(request);elapsed=time.monotonic()-start
    if raw.get('status') in ['WORKER_ERROR','EVALUATOR_ERROR']:save(d/'STOP.json',dict(key=a['key'],case_id=c['case_id'],raw=raw));raise RuntimeError('WORKER_INFRASTRUCTURE')
    journal.append('ALGORITHM_EXECUTED',dict(key=a['key'],case_id=c['case_id'],solver_sha256=a['solver_sha256'],input_sha256=fingerprint(request),seconds=elapsed,raw=raw,gold_exposed=False),time.time())
    results.append(dict(key=a['key'],arm=a['arm'],group=a['group'],replica=a['replica'],case_id=c['case_id'],role=c['role'],raw=raw,seconds=elapsed,solver_sha256=a['solver_sha256']))
  print('EXECUTED',a['key'],len(selected),flush=True)
 save(d/'outputs_locked.json',results);save(d/'lock.json',dict(at=time.time(),sha256=sha(d/'outputs_locked.json')))
 from code_math.private_math_scoring import normalized
 labels={c['case_id']:c for c in cases}
 for r in results:
  raw=r['raw'];v=raw.get('value');c=labels[r['case_id']];r['correct']=False;r['safe_reject']=False
  if c['role']=='invalid':
   # Explicit supported errors only; arbitrary exceptions/timeouts are not successful refusal.
   r['safe_reject']=(raw.get('status')=='OK' and v=='DECLINED') or (raw.get('status')=='RUNTIME_ERROR' and raw.get('error','').split(':',1)[0] in ['ValueError','TypeError'])
  elif raw.get('status')=='OK' and isinstance(v,str) and v.strip() and len(v)<4096 and v!='DECLINED':r['correct']=normalized(v)==normalized(c['answer'])
  r['answer_contract_valid']=raw.get('status')=='OK' and isinstance(v,str) and bool(v.strip())
 summary={}
 for a in freeze['results']:
  rr=[r for r in results if r['key']==a['key']];record=dict(a)
  for role in ['source','new_parameters','invalid']:
   rs=[r for r in rr if r['role']==role];record[role]=dict(n=len(rs),correct=sum(r['correct'] for r in rs),safe_reject=sum(r['safe_reject'] for r in rs),status_counts=dict(collections.Counter(r['raw']['status'] for r in rs)))
  record['all_valid_correct']=all(r['correct'] for r in rr if r['role']!='invalid')
  record['all_invalid_rejected']=all(r['safe_reject'] for r in rr if r['role']=='invalid')
  record['fully_qualified']=record['all_valid_correct'] and record['all_invalid_rejected'];summary[a['key']]=record
 save(d/'scores.json',results);save(d/'summary.json',summary);save(OUT/'COMPLETE.json',dict(at=time.time(),attempts=len(summary),actual_executions=sum(r['raw']['status']!='NOT_EXECUTED' for r in results),experimental=0,no_post_score_generation=True));print('COMPLETE',sum(r['fully_qualified'] for r in summary.values()),flush=True)
if __name__=='__main__':evaluate()
