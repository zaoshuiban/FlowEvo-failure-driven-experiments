"""One preregistered S engineering repair, no new evaluation examples/results.
Only MATCH requested_quantity output binding may differ in executable AST.
"""
import ast,copy,time,json
from run_math_v34 import OUT,load,save,sha,fingerprint,ROOT,IMAGE,WORKER,request,prior_text
from failure_evo.semantic_contract import SplitRunner,artifact
from failure_evo.autonomous_mvp import FrozenLinuxBackend

def normalized_tree(code):
 tree=ast.parse(code)
 for n in ast.walk(tree):
  if isinstance(n,ast.Dict):
   keys=[k.value if isinstance(k,ast.Constant) else None for k in n.keys]
   if 'status' in keys and 'requested_quantity' in keys:
    status=n.values[keys.index('status')]
    if isinstance(status,ast.Constant) and status.value=='MATCH':n.values[keys.index('requested_quantity')]=ast.Constant(value='__MATCH_OUTPUT_BINDING__')
 return ast.dump(tree,include_attributes=False)
def run():
 if (OUT/'evaluation_started.json').exists():raise RuntimeError('no post-scoring repair')
 old=load(OUT/'candidate_freeze.json');save(OUT/'candidate_freeze_initial.json',old)
 split=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),OUT/'interface_probe/worker.jsonl')
 probe=dict(operands=[1,2],operators=['+'],requested_quantity='number of distinct obtainable values',allowed_transformations=['fully parenthesize'],order_constraint='order of numbers and operations must not change',counting_rule='count distinct values')
 results={}
 for k,a in old['artifacts'].items():
  raw=split.component(a,'match',probe);v=raw.get('value',{});results[k]=dict(raw=raw,quantity_binding_valid=v.get('status')!='MATCH' or v.get('requested_quantity')==a['contract']['requested_quantity'])
 save(OUT/'interface_probe/results.json',dict(at=time.time(),probe=probe,source='Engineering-only synthetic interface probe; no new task IDs or answers; not functional validation',results=results))
 if results['S']['quantity_binding_valid']:return
 a=old['artifacts']['S'];code=__import__('pathlib').Path(a['matcher_path']).read_text()
 save(OUT/'engineering_timing_amendment.json',dict(at=time.time(),reason='Interface probe detected S output binding mismatch after initial candidate freeze and parser launch, before any new task score. Use already preregistered one engineering repair. New task text/parsed facts/labels/results not supplied to repair. Shared parser unchanged and not resent.',initial_freeze_sha256=fingerprint(old),initial_artifact=a,guard_changes_forbidden=True))
 v=dict(load(OUT/'base.json'),semantics=load(OUT/'semantics.json'),engineering_repair=dict(prior_response=prior_text('S-0'),diagnostic='Pure output-contract repair only: your MATCH return uses requested_quantity from input facts; this can differ from contract.requested_quantity and violates the declared interface. Change ONLY the requested_quantity VALUE in the MATCH return dict to the exact constant declared by your existing contract. Preserve every condition, helper, import, input check, parameter extraction, reason, and all contract and required_facts metadata unchanged. Do not add or improve semantic checks. No task score or new task is provided. Return full code and the exact prior contract, required_facts and limitations.'))
 r=request('S-1','contract',v)
 if r is None:raise RuntimeError('known failed repair; no further attempt')
 c=json.loads(r['description']);meta=json.loads(r['applicability']);orig=load(OUT/'S/version0/response.json');origmeta=json.loads(orig['applicability'])
 if c!=a['contract'] or meta!=origmeta or normalized_tree(code)!=normalized_tree(r['code']):
  save(OUT/'S/version1/REJECTED.json',dict(reason='Repair changed more than output binding'));return
 art=artifact(OUT/'S/version1/artifacts',load(OUT/'base.json')['solver_code'],r['code'],c,provenance=dict(a['provenance'],response_sha256=r['response_sha256'],wire_sha256=r['wire_sha256'],revision_parent=a['code_sha256']))
 raw=split.component(art,'match',probe)
 if raw.get('value',{}).get('requested_quantity')!=c['requested_quantity']:save(OUT/'S/version1/REJECTED.json',dict(reason='Binding still invalid',raw=raw));return
 save(OUT/'S/version1/response.json',r);save(OUT/'S/version1/artifact.json',art);old['artifacts']['S']=art;old['outcomes'].append(dict(arm='S',attempt=1,status='ENGINEERING_BINDING_REPAIRED',ast_only_binding_changed=True));old['at']=time.time();save(OUT/'candidate_freeze.json',old);print('S_REPAIR_BOUND_ONLY',art['code_sha256'])
if __name__=='__main__':run()
