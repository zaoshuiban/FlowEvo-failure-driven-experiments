"""Offline annotations written before parser outputs; never model-visible.
Labels are host-reviewed explicit data specifications, not routing code.
No claim of independent third-party human annotation.
"""
from run_math_v33 import OUT,load,save,sha,fingerprint
import jsonschema,time

def facts(nums,ops,target='COUNT_DISTINCT_VALUES',paren='YES',reorder='NO',unique='YES',conflict='NO',missing='NO'):
 return dict(operands=nums,operators=ops,operand_count=len(nums) if nums is not None else None,operator_count=len(ops) if ops is not None else None,parenthesization_allowed=paren,rearrangement_allowed=reorder,duplicate_results_counted_once=unique,target_quantity=target,explicit_contradiction=conflict,missing_premises=missing)
def annotate():
 if (OUT/'trusted_semantics').exists() or (OUT/'parsing').exists():raise RuntimeError('annotations must precede parsed outcomes')
 s=load(OUT/'semantics.json');allrows={}
 for role in ['development','confirmation']:
  pub=load(OUT/f'data/public/{role}.json');labels=load(OUT/f'data/private/{role}.json');rows=[]
  for t,p in zip(pub,labels):
   i=int(t['task_id'].split('-')[-1]);reason=None
   if p['supported'] is True:f=facts(p['parameters']['operands'],p['parameters']['operators'])
   elif role=='development':
    if i==6:f=facts([15,8,3,7],['-','*','+'],target='OTHER')
    elif i==7:f=None;reason='Known division cannot be represented truthfully: operators enum excludes /; UNKNOWN is defined as unidentified, not known unsupported.'
    elif i==8:f=facts([13,4,7,2],['+','*','-'],target='COUNT_PARENTHESIZATIONS',unique='NO')
    elif i==9:f=facts([24,9,5,2],['-','*','+'],paren='NO')
    elif i==10:f=facts([16,5,8,3],['-','*','+'],reorder='UNKNOWN',conflict='YES')
    else:f=facts([25,9,4,2],None,missing='YES')
   else:
    if i==6:f=facts([28,7,5,2],['-','*','+'],target='OTHER',unique='UNKNOWN')
    elif i==7:f=None;reason='Known exponentiation cannot be represented truthfully: enum excludes **.'
    elif i==8:f=facts([31,8,6,3],['-','+','*'],reorder='YES')
    elif i==9:f=None;reason='Known exact decimal 2.5 is excluded by integer-only operand facts; replacing it by integer or null would lose known information.'
    elif i==10:f=facts([33,5,7,9],['+','*','-'],target='UNKNOWN',unique='UNKNOWN',missing='YES')
    else:f=facts([42,6,2,5],['-','*','+'],target='UNKNOWN',unique='UNKNOWN',conflict='YES')
   if f is not None:jsonschema.validate(f,s['schema'])
   rows.append(dict(task_id=t['task_id'],problem_sha256=fingerprint(t['problem']),facts=f,unrepresentable_reason=reason,review='Host semantic annotation from literal public problem; no candidate match output; no answer field; not a second blinded human review'))
  save(OUT/f'trusted_semantics/{role}.json',rows);allrows[role]=sha(OUT/f'trusted_semantics/{role}.json')
 save(OUT/'annotation_freeze.json',dict(at=time.time(),schema_sha256=fingerprint(s),files=allrows,code_sha256=sha(__file__),model_visible=False))
if __name__=='__main__':annotate()
