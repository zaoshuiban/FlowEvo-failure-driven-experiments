"""One-time paired evaluation. Score only after role outputs lock; no learning."""
import json,time,jsonschema
from run_math_v34 import OUT,OLD,ROOT,WORKER,IMAGE,load,save,sha,fingerprint,verify
from failure_evo.semantic_contract import SplitRunner
from failure_evo.semantic_evidence_v2 import EvidenceRunner,validate_packet
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from code_math.no_gold import PublicMathTask

def evaluate():
 if (OUT/'evaluation_started.json').exists():raise RuntimeError('evaluation consumed')
 plan=verify();sem=load(OUT/'semantics.json');frozen=load(OUT/'candidate_freeze.json');arts=frozen['artifacts'];annlock=load(OUT/'annotation_freeze.json');assert all(sha(OUT/f'annotations/{r}.json')==h for r,h in annlock['files'].items());assert annlock['semantics_sha256']==fingerprint(sem)
 save(OUT/'evaluation_started.json',dict(at=time.time(),candidate_sha256=fingerprint(frozen),semantics_sha256=fingerprint(sem),script_sha256=sha(__file__),runtime_sha256=sha(ROOT/'FlowEvo/src/failure_evo/semantic_evidence_v2.py'),parsed_hashes={r:sha(OUT/f'parsing/{r}.json') for r in ['development','confirmation']},no_post_score_model_calls=True))
 baseline=load(ROOT/'runs/math_v32_semantic_20261028_01/data_v2/manifest.json')['old_artifact']
 for role in ['development','confirmation']:
  tasks=load(OUT/f'data/public/{role}.json');parses={p['task_id']:p for p in load(OUT/f'parsing/{role}.json')};ann={p['task_id']:p for p in load(OUT/f'annotations/{role}.json')};rows=[];parsing=[]
  split=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),OUT/f'evaluation/{role}/worker.jsonl');runner=EvidenceRunner(split,sem)
  for i,t in enumerate(tasks):
   p=parses[t['task_id']];a=ann[t['task_id']];response=load(OUT/f'calls/parse-{role}-{i//4}/response.json');raw=next(r for r in json.loads(response['code'])['records'] if r['task_id']==t['task_id']);assert raw==p
   try:jsonschema.validate(p['facts'],sem['schema']);schema_ok=True;schema_error=None
   except jsonschema.ValidationError as e:schema_ok=False;schema_error=e.message
   try:validate_packet(sem,t['problem'],p);valid=True;error=None
   except (ValueError,jsonschema.ValidationError) as e:valid=False;error=str(e)[:1000]
   parsing.append(dict(task_id=t['task_id'],schema_valid=schema_ok,schema_error=schema_error,evidence_valid=valid,evidence_error=error,parameter_values_exact=(p['facts'].get('operands')==a['facts']['operands'] and p['facts'].get('operators')==a['facts']['operators']),field_exact_differences={k:dict(reference=v,parsed=p['facts'].get(k)) for k,v in a['facts'].items() if p['facts'].get(k)!=v},exact_text_is_not_semantic_accuracy=True,review=p['review']))
   rows.append(dict(task_id=t['task_id'],candidate='R',path='runtime',observation=split.run(baseline,PublicMathTask.parse(t))))
   for key,art in arts.items():
    o=runner.run(art,t,p,dict(origin='MODEL_PARSE',problem_sha256=fingerprint(t['problem']),parsed_sha256=fingerprint(p),response_sha256=response['response_sha256']))
    rows.append(dict(task_id=t['task_id'],candidate=key,path='runtime',observation=o))
    # Gold-free trusted facts are OFFLINE ONLY. Ambiguous review is retained.
    if a['review']!='NO_ISSUE_OBSERVED':o=dict(status='DECLINED',match=dict(status='UNKNOWN',reason='TRUSTED_REVIEW_CONFLICT'),diagnostic_only=True)
    else:o=runner.diagnose_trusted(art,a['facts'],offline_attribution=True)
    rows.append(dict(task_id=t['task_id'],candidate=key,path='trusted_offline',observation=o))
  d=OUT/f'evaluation/{role}';save(d/'outputs_locked.json',rows);save(d/'lock.json',dict(at=time.time(),sha256=sha(d/'outputs_locked.json')))
  from code_math.private_math_scoring import normalized
  private={p['task_id']:p for p in load(OUT/f'data/private/{role}.json')}
  for r in rows:
   l=private[r['task_id']];o=r['observation'];m=o['match'];s=l['supported'];correct=None
   if s is True and o['status']=='APPLIED':correct=normalized(o['answer'])==normalized(l['answer'])
   r.update(supported=s,correct=correct,correct_accept=s is True and correct is True,incorrect_compute=s is True and o['status']=='APPLIED' and correct is False,false_accept=s is False and o['status']=='APPLIED',ambiguous_accept=s is None and m['status']=='MATCH',unknown=m['status']=='UNKNOWN',interface_error=m['status']=='ERROR',execution_error=o['status']=='ERROR' and m['status']!='ERROR',correct_reject=s is False and m['status']=='DECLINE',safe_nonintervention=s is False and o['status']=='DECLINED')
  summary={}
  for key in sorted({(r['candidate'],r['path']) for r in rows}):
   rr=[r for r in rows if (r['candidate'],r['path'])==key];summary['/'.join(key)]=dict(n=len(rr),supported=sum(r['supported'] is True for r in rr),unsupported=sum(r['supported'] is False for r in rr),ambiguous=sum(r['supported'] is None for r in rr),**{k:sum(bool(r[k]) for r in rr) for k in ['correct_accept','incorrect_compute','false_accept','ambiguous_accept','unknown','interface_error','execution_error','correct_reject','safe_nonintervention']})
  save(d/'scores.json',rows);save(d/'summary.json',summary);save(d/'parser_audit.json',parsing);print(role,json.dumps(summary),flush=True)
 save(OUT/'COMPLETE.json',dict(at=time.time(),paired_executable_conditions=sorted(arts),experimental=0,solver_unchanged=all(sha(a['solver_path'])==plan['solver_sha256'] for a in arts.values()),no_post_score_learning=True,confirmation_once=True))
if __name__=='__main__':evaluate()
