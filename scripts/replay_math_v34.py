"""Zero-model historical regression only. Never repairs missing facts or old files.
The two old meta-review fields are migrated to a whole-source review channel.
Original model facts supplied to the frozen matcher remain byte-equivalent JSON.
"""
import json,time,copy
from run_math_v34 import OUT,OLD,ROOT,WORKER,IMAGE,load,save,sha,fingerprint
from failure_evo.semantic_evidence_v2 import validate_packet
from failure_evo.structured_semantics import StructuredRunner
from failure_evo.semantic_contract import SplitRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
META={'explicit_contradiction','missing_premises'}
def migrate(t,p,oldschema):
 facts={k:(None if v=='UNKNOWN' else v) for k,v in p['facts'].items() if k not in META};ev={}
 for k,v in facts.items():
  quotes=p['evidence'][k]
  ev[k]=dict(kind=('UNRESOLVED' if v is None else 'EXPLICIT_NEGATION' if v=='NO' else 'EXPLICIT_AFFIRMATION'),quotes=quotes,scope='FULL_PROBLEM' if v is None else 'QUOTED_TEXT',rule=None,from_field=None)
 audit={k:p['facts'][k] for k in META};conflict=audit['explicit_contradiction']=='YES'
 review=dict(status='CONFLICT' if conflict else 'NO_ISSUE_OBSERVED' if all(v=='NO' for v in audit.values()) else 'UNRESOLVED',quotes=p['evidence']['explicit_contradiction'] if conflict else [],scope='FULL_PROBLEM')
 schema=copy.deepcopy(oldschema);schema['required']=[k for k in schema['required'] if k not in META];schema['properties']={k:v for k,v in schema['properties'].items() if k not in META}
 for spec in schema['properties'].values():
  typ=spec['type'];spec['type']=list(dict.fromkeys((typ if isinstance(typ,list) else [typ])+['null']))
  if 'enum' in spec:spec['enum']=spec['enum']+[None]
 return dict(task_id=t['task_id'],facts=facts,evidence=ev,review=review),dict(schema=schema)
def run():
 dest=OUT/'historical_replay'
 if dest.exists():raise RuntimeError('replay consumed')
 sem=load(OLD/'semantics.json');a=load(OLD/'FS/artifact.json');split=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),dest/'worker.jsonl');runner=StructuredRunner(split,sem);allrows=[]
 save(dest/'policy.json',dict(at=time.time(),meta_fields=sorted(META),role='Historical protocol compatibility replay, not new confirmation',conversion='No new semantic inference. Old NO whole-source meta claims allowed empty quote; no operational constraint can use this exemption. Existing old UNKNOWN mapped to null for validation only.',matcher_and_solver_unchanged=True,new_model_requests=0))
 for role in ['development','confirmation']:
  tasks=load(OLD/f'data/public/{role}.json');parses={p['task_id']:p for p in load(OLD/f'parsing/{role}.json')};previous={r['task_id']:r for r in load(OLD/f'evaluation/{role}/scores.json') if r['candidate']=='FS' and r['path']=='runtime'}
  for t in tasks:
   p=parses[t['task_id']];packet,schema=migrate(t,p,sem['schema']);reason=None
   try:validate_packet(schema,t['problem'],packet);valid=True
   except Exception as e:valid=False;reason=str(e)
   if not valid:o=dict(status='DECLINED',match=dict(status='UNKNOWN',reason=reason))
   elif packet['review']['status']!='NO_ISSUE_OBSERVED':o=dict(status='DECLINED',match=dict(status='UNKNOWN',reason='REVIEW_UNRESOLVED'))
   else:o=runner._execute(a,p['facts'])
   allrows.append(dict(role=role,task_id=t['task_id'],original_parse_sha256=fingerprint(p),migrated_packet=packet,evidence_valid=valid,evidence_reason=reason,previous=previous[t['task_id']]['observation'],observation=o,diagnostic_only=True))
 save(dest/'outputs_locked.json',allrows);save(dest/'lock.json',dict(at=time.time(),sha256=sha(dest/'outputs_locked.json')))
 from code_math.private_math_scoring import normalized
 labels={p['task_id']:p for role in ['development','confirmation'] for p in load(OLD/f'data/private/{role}.json')}
 for r in allrows:
  l=labels[r['task_id']];o=r['observation'];r.update(supported=l['supported'],correct_accept=l['supported'] is True and o['status']=='APPLIED' and normalized(o['answer'])==normalized(l['answer']),false_accept=l['supported'] is False and o['status']=='APPLIED',ambiguous_accept=l['supported'] is None and o['status']=='APPLIED')
 save(dest/'scores.json',allrows);summary={}
 for role in ['development','confirmation']:
  rs=[r for r in allrows if r['role']==role];summary[role]={k:sum(bool(r[k]) for r in rs) for k in ['evidence_valid','correct_accept','false_accept','ambiguous_accept']};summary[role]['unknown']=sum(r['observation']['match']['status']=='UNKNOWN' for r in rs)
 save(dest/'summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':run()
