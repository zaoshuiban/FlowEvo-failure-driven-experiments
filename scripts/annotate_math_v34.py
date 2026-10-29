"""Offline-only new-task semantics, before parser/evaluation outputs.
Canonical vocabulary uses model schema's own examples. No candidate code consulted.
"""
import jsonschema,time
from run_math_v34 import OUT,load,save,sha,fingerprint

def annotate():
 if (OUT/'annotations').exists() or (OUT/'parsing').exists():raise RuntimeError('annotation must precede parser outputs')
 s=load(OUT/'semantics.json');expected={'operands','operators','requested_quantity','allowed_transformations','order_constraint','counting_rule'}
 if set(s['schema']['properties'])!=expected:raise RuntimeError('annotate actual model vocabulary; never silently rename fields')
 extras={
 'development':[
 ([90,19,12,6],['-','-','-']),([67,4,19,8],['/','+','-']),([72,14,5,5],['-','+','*']),([1.25,16,7,3],['*','-','+']),([91,28,6,9],['+','*','+']),([59,26,8,4],None)],
 'confirmation':[
 ([62,29,11,2],['+','*','-']),([5,3,17,6],['**','-','+']),([69,28,11,2],['-','*','*']),([73,21,14,5],['-','*','+']),([98,26,9,2],['*','+','+']),([84,25,12,3],['*','-','+'])]}
 hashes={}
 for role in ['development','confirmation']:
  ts=load(OUT/f'data/public/{role}.json');labels=load(OUT/f'data/private/{role}.json');rows=[]
  for i,(t,l) in enumerate(zip(ts,labels)):
   n,o=(l['parameters']['operands'],l['parameters']['operators']) if i<6 else extras[role][i-6]
   f=dict(operands=n,operators=o,requested_quantity='number of distinct obtainable values',allowed_transformations=['fully parenthesize'],order_constraint='order of numbers and operations must not change',counting_rule='count distinct values');review='NO_ISSUE_OBSERVED'
   if i==6:f['requested_quantity']='sum of distinct values' if role=='development' else 'minimum obtainable value'
   if role=='development' and i==8:f['allowed_transformations']=['fully parenthesize','rearrange numbers'];f['order_constraint']='operation order is fixed; operands may be permuted'
   if role=='confirmation' and i==8:f['requested_quantity']='number of full binary tree structures';f['counting_rule']='count equal results separately for each tree'
   if role=='confirmation' and i==9:f['allowed_transformations']=[];f['order_constraint']='fixed grouping and fixed token order'
   if i==10:f['order_constraint']=None
   if role=='confirmation' and i==11:f['requested_quantity']=None;f['counting_rule']=None;review='CONFLICT'
   jsonschema.validate(f,s['schema'])
   rows.append(dict(task_id=t['task_id'],problem_sha256=fingerprint(t['problem']),facts=f,review=review,annotation_basis='Host interpretation of literal new task; canonical phrases follow model-generated field definitions, no candidate code/output consulted. Single-terminal cases imply vacuous fixed order; explicitness remains an annotation limitation. No numeric answer here.'))
  save(OUT/f'annotations/{role}.json',rows);hashes[role]=sha(OUT/f'annotations/{role}.json')
 save(OUT/'annotation_freeze.json',dict(at=time.time(),files=hashes,script_sha256=sha(__file__),semantics_sha256=fingerprint(s),before_model_parser=True,third_party_blinded=False))
if __name__=='__main__':annotate()
