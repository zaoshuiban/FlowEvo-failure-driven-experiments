"""One-time provenance alias repair; no new induction, no algorithm edits."""
import copy,hashlib,json,sys,time
from pathlib import Path
from run_math_p2_all12 import ROOT,sha,save,budget,IMAGE,WORKER
from failure_evo.contracts import fingerprint,canonical
from failure_evo.evidence import EvidenceStore
from failure_evo.math_p2_all_failures import AllFailuresGPTAdapter,AllFailuresEngineering,parse_discovery,evidence_view
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.math_operators import MathOperatorRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend

def bind_aliases(h,rows):
 result=copy.deepcopy(h);aliases={r['task_id']:r['evidence_id'] for r in rows};known={r['evidence_id'] for r in rows};changes=[]
 if len(aliases)!=len(rows):raise ValueError('ambiguous task aliases')
 for i,m in enumerate(result['mechanisms']):
  for j,key in enumerate(m['source_event_ids']):
   if key in known:continue
   if key not in aliases:raise ValueError('unknown source, cannot normalize')
   m['source_event_ids'][j]=aliases[key];changes.append(dict(mechanism=i,index=j,original=key,evidence_id=aliases[key]))
  if len(set(m['source_event_ids']))!=len(m['source_event_ids']):raise ValueError('duplicate normalized sources')
 return parse_discovery(result),changes

def main(root):
 if (root/'source_binding_recovery.json').exists():raise RuntimeError('recovery already consumed')
 p=json.loads((root/'protocol.json').read_text());ph=fingerprint(p)
 for rel,d in p['source_hashes'].items():
  if sha(ROOT/rel)!=d:raise RuntimeError('frozen code changed')
 rows=json.loads((root/'source_failures.json').read_text());evidence_view(rows)
 cr=EvidenceStore(root/'compiler.jsonl').records()
 requested=[x for x in cr if x['kind']=='GENERATION_REQUESTED']
 assert len(requested)==1 and requested[0]['payload']['phase']=='induction'
 raw=[x['payload']['response'] for x in EvidenceStore(root/'provider.jsonl').records() if x['kind']=='RAW_RESPONSE']
 assert len(raw)==1 and raw[0]['choices'][0]['finish_reason']=='stop'
 h=parse_discovery(json.loads(raw[0]['choices'][0]['message']['content']));bound,mapping=bind_aliases(h,rows)
 # Verify this transformation changes provenance identifiers ONLY.
 undo=copy.deepcopy(bound)
 for x in mapping:undo['mechanisms'][x['mechanism']]['source_event_ids'][x['index']]=x['original']
 assert undo==h
 b=budget(root,ph);assert b.snapshot()['calls']==1 and not b.snapshot()['unknown_or_pending_requests']
 grant=json.loads((root/'authorization.json').read_text())
 a=AllFailuresGPTAdapter(root/'provider.jsonl',b,model='gpt-5.4',authorization=grant,max_wire_input_upper=65536)
 real=BoundedCompiler(a,b,root/'compiler.jsonl','gpt-5.4',max_input_upper=65536,max_output_upper=8192)
 amendment=dict(kind='PROVENANCE_ONLY_NORMALIZATION',at=time.time(),raw_response_sha256=fingerprint(raw[0]),original_hypothesis_sha256=fingerprint(h),normalized_hypothesis_sha256=fingerprint(bound),
  mapping=mapping,normalization_rule='Only exact unique task_id already present in frozen input maps to its evidence_id; unknown/ambiguous references reject.',
  algorithm_text_unchanged=True,prompt_unchanged=True,new_induction_requests=0,total_request_limit=7,shared_original_budget=True,
  recovery_script_sha256=sha(__file__),prior_stop_preserved=True,post_response_protocol_amendment=True)
 save(root/'source_binding_recovery.json',amendment);save(root/'normalized_hypothesis.json',bound)
 (root/'frozen_source'/'resume_math_p2_bound_sources.py').write_bytes(Path(__file__).read_bytes())
 real.events.append('PROVENANCE_ONLY_NORMALIZATION',amendment,time.time())
 class ReuseInduction:
  budget=b
  def request(self,job,phase,slot,at,output_upper=8192):
   if phase=='induction':
    return dict(specification=canonical(bound),origin='GPT_VIA_OPENROUTER_REUSED_WITH_PROVENANCE_NORMALIZATION',raw_response=raw[0],usage=raw[0]['usage'],new_model_calls=0,response_sha256=fingerprint(raw[0]))
   return real.request(job,phase,slot,at,output_upper=output_upper)
 try:
  result=AllFailuresEngineering(root/'candidates_bound',ReuseInduction(),MathOperatorRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),budget=b)).run({'events':rows})
  save(root/'COMPLETE.json',dict(result=result,budget=b.snapshot(),at=time.time(),provenance_amendment=True));print(json.dumps(result),flush=True)
 except BaseException as e:
  save(root/'RECOVERY_STOP.json',dict(error=type(e).__name__,message=str(e)[:500],budget=b.snapshot(),no_retry=True));raise
 finally:save(root/'historical_integrity.json',{rel:sha(ROOT/rel)==d for rel,d in p['old_run_hashes'].items()})
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
