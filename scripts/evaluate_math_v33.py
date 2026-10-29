"""One-time frozen confirmation; no revision, deployment or gold-based retry."""
from run_math_v33 import OUT,OLD,ROOT,WORKER,IMAGE,load,save,sha,fingerprint
from failure_evo.semantic_contract import SplitRunner
from failure_evo.structured_semantics import StructuredRunner,check_parse
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from code_math.no_gold import PublicMathTask
import time,json,jsonschema

def evaluate():
 if (OUT/'evaluation_started.json').exists():raise RuntimeError('one evaluation only')
 plan=load(OUT/'protocol.json');assert all(sha(OUT/p)==h for p,h in plan['data_hashes'].items());assert all(sha(ROOT/p)==h for p,h in plan['source_hashes'].items())
 candidates=load(OUT/'candidate_freeze.json')['artifacts'];sem=load(OUT/'semantics.json');old=load(OLD/'data_v2/manifest.json')['old_artifact'];ann=load(OUT/'annotation_freeze.json')
 assert all(sha(OUT/f'trusted_semantics/{r}.json')==h for r,h in ann['files'].items())
 runtime=ROOT/'FlowEvo/src/failure_evo/structured_semantics.py'
 save(OUT/'evaluation_started.json',dict(at=time.time(),runtime_sha256=sha(runtime),evaluator_sha256=sha(__file__),candidate_freeze_sha256=sha(OUT/'candidate_freeze.json'),parsed_files={r:sha(OUT/f'parsing/{r}.json') for r in ['development','confirmation']},no_learning_after_this=True))
 for role in ['development','confirmation']:
  tasks=load(OUT/f'data/public/{role}.json');parses={r['task_id']:r for r in load(OUT/f'parsing/{role}.json')};trusted={r['task_id']:r for r in load(OUT/f'trusted_semantics/{role}.json')};rows=[];parse_scores=[]
  split=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),OUT/f'evaluation/{role}/worker.jsonl');runner=StructuredRunner(split,sem)
  for index,t in enumerate(tasks):
   p=parses[t['task_id']];a=trusted[t['task_id']];r=load(OUT/f'calls/parse-{role}-{index//6}/response.json');rawrow=next(v for v in json.loads(r['code']) if v['task_id']==t['task_id']);assert rawrow==p
   try:check_parse(sem,t['problem'],p);valid=True;reason=None
   except (ValueError,jsonschema.ValidationError) as e:valid=False;reason=str(e)
   diff={k:dict(expected=v,observed=p.get('facts',{}).get(k)) for k,v in (a['facts'] or {}).items() if p.get('facts',{}).get(k)!=v}
   parse_scores.append(dict(task_id=t['task_id'],schema_and_quote_valid=valid,validation_reason=reason,representable=a['facts'] is not None,field_differences=diff,all_fields_correct=not diff if a['facts'] is not None else None,representation_limit=a['unrepresentable_reason']))
   rows.append(dict(candidate='R',path='runtime',task_id=t['task_id'],observation=split.run(old,PublicMathTask.parse(t))))
   for key,art in candidates.items():
    obs=runner.run(art,t,p,dict(origin='MODEL_PARSE',problem_sha256=fingerprint(t['problem']),parsed_sha256=fingerprint(p),response_sha256=r['response_sha256']))
    rows.append(dict(candidate=key,path='runtime',task_id=t['task_id'],observation=obs))
    if a['facts'] is not None:
     obs=runner.diagnose_trusted(art,a['facts'],offline_attribution=True)
     rows.append(dict(candidate=key,path='trusted_offline',task_id=t['task_id'],observation=obs))
  dest=OUT/f'evaluation/{role}';save(dest/'outputs_locked.json',rows);save(dest/'lock.json',dict(at=time.time(),sha256=sha(dest/'outputs_locked.json')))
  # Private numeric reference first used after all outputs for this role locked.
  from code_math.private_math_scoring import normalized
  labels={r['task_id']:r for r in load(OUT/f'data/private/{role}.json')}
  for r in rows:
   p=labels[r['task_id']];o=r['observation'];m=o['match'];s=p['supported'];r.update(supported=s,correct=None)
   if s is True and o['status']=='APPLIED':r['correct']=normalized(o['answer'])==normalized(p['answer'])
   r.update(correct_accept=s is True and r['correct'] is True,incorrect_compute=s is True and o['status']=='APPLIED' and r['correct'] is False,false_accept=s is False and o['status']=='APPLIED',ambiguous_accept=s is None and m['status']=='MATCH',unknown=m['status']=='UNKNOWN',interface_error=m['status']=='ERROR',execution_error=o['status']=='ERROR' and m['status']!='ERROR',correct_reject=s is False and m['status']=='DECLINE',safe_nonintervention=s is False and o['status']=='DECLINED',parameter_match=(m.get('parameters')==p['parameters']) if s is True and m['status']=='MATCH' else None)
  summary={}
  for key in sorted({(r['candidate'],r['path']) for r in rows}):
   rs=[r for r in rows if (r['candidate'],r['path'])==key];summary['/'.join(key)]=dict(n=len(rs),supported=sum(r['supported'] is True for r in rs),unsupported=sum(r['supported'] is False for r in rs),ambiguous=sum(r['supported'] is None for r in rs),**{k:sum(bool(r[k]) for r in rs) for k in ['correct_accept','incorrect_compute','false_accept','ambiguous_accept','unknown','interface_error','execution_error','correct_reject','safe_nonintervention']})
  save(dest/'scores.json',rows);save(dest/'summary.json',summary);save(dest/'parser_scores.json',parse_scores);print(role,json.dumps(summary),flush=True)
 save(OUT/'COMPLETE.json',dict(at=time.time(),status='PARTIAL_NO_VALID_S_CONTRACT',experimental=0,solver_unchanged=all(sha(a['solver_path'])==plan['algorithm_sha256'] for a in [old,*candidates.values()]),no_gold_retry=True,no_post_score_generation=True))
if __name__=='__main__':evaluate()
