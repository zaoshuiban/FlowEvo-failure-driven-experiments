"""v3 validation extensions on existing MathOperatorRegistry journal."""
import time
from .math_operators import MathOperatorRegistry,FrozenMathLibrary
from .contracts import fingerprint
from .operator_dual_validation import development_passed
class VersionGate(MathOperatorRegistry):
 def freeze_gate(self,artifacts,*,data_hash,development_ids,gate_ids):
  if set(development_ids)&set(gate_ids) or not gate_ids:raise PermissionError('role overlap')
  if any(r['kind']=='V3_GATE_FREEZE' and r['payload']['data_hash']==data_hash for r in self.events.records()):raise PermissionError('Gate already frozen')
  self.events.append('V3_GATE_FREEZE',dict(data_hash=data_hash,versions=[a['code_sha256'] for a in artifacts],gate_ids=gate_ids),time.time())
 def record_review(self,a,rows,*,role,data_hash,exposed,paired_generic=False):
  if role not in ('Development','Gate'):raise ValueError('role')
  if role=='Gate' and exposed:raise PermissionError('exposed Gate')
  prior=self.events.records()
  if role=='Gate' and not any(x['kind']=='V3_GATE_FREEZE' and x['payload']['data_hash']==data_hash and a['code_sha256'] in x['payload']['versions'] for x in prior):raise PermissionError('version not pre-frozen for Gate')
  if role=='Gate' and any(x['kind']=='V3_VALIDATION' and x['payload']['code_sha256']==a['code_sha256'] and x['payload']['role']=='Gate' and x['payload']['data_hash']==data_hash for x in prior):raise PermissionError('Gate shard consumed')
  p=dict(code_sha256=a['code_sha256'],rows=rows,role=role,data_hash=data_hash,exposed=exposed,paired_generic=paired_generic,passed=development_passed(rows))
  self.events.append('V3_VALIDATION',p,time.time());return p
 def admit(self,a,validation,*,after_sequence):
  rows=self.events.records()
  if not any(r['kind']=='MATH_SHADOW' and r['payload']==a for r in rows):raise PermissionError('unregistered shadow')
  receipts=[r['payload'] for r in rows if r['kind']=='V3_VALIDATION' and r['payload']['code_sha256']==a['code_sha256']]
  if validation not in receipts or validation['role']!='Gate' or validation['exposed'] or not validation['passed'] or not validation['paired_generic']:raise PermissionError('bound independent paired Gate required')
  if not any(r['role']=='Development' and r['passed'] for r in receipts):raise PermissionError('both development dimensions required')
  if any(r['kind']=='MATH_SUSPENDED' and r['payload']['code_sha256']==a['code_sha256'] for r in rows):raise PermissionError('suspended')
  self.events.append('MATH_EXPERIMENTAL',dict(artifact=a,validation=validation,effective_after=after_sequence),time.time())
# FrozenMathLibrary and NoGoldMathController already provide default-off routing,
# match/solve failure fallback, and no hidden-answer rescue. No second library.

 def authorize_trial(self,a,*,future_task_ids,max_uses,after_sequence):
  if not future_task_ids or len(set(future_task_ids))!=len(future_task_ids) or type(max_uses) is not int or not 1<=max_uses<=len(future_task_ids):raise ValueError('finite future permission')
  if set(future_task_ids)&set(a['excluded_task_ids']):raise PermissionError('source cannot be future trial')
  if not any(r['kind']=='MATH_EXPERIMENTAL' and r['payload']['artifact']==a for r in self.events.records()):raise PermissionError('Gate-qualified Experimental required')
  if any(r['kind']=='V3_TRIAL_AUTHORIZATION' and r['payload']['code_sha256']==a['code_sha256'] for r in self.events.records()):raise PermissionError('explicit new review needed for renewal')
  self.events.append('V3_TRIAL_AUTHORIZATION',dict(code_sha256=a['code_sha256'],task_ids=future_task_ids,max_uses=max_uses,effective_after=after_sequence),time.time())
 def eligible(self,task,sequence):
  rows=self.events.records();out=[]
  for a in super().eligible(task,sequence):
   grants=[r['payload'] for r in rows if r['kind']=='V3_TRIAL_AUTHORIZATION' and r['payload']['code_sha256']==a['code_sha256']]
   used=sum(r['kind']=='V3_TRIAL_RESERVED' and r['payload']['code_sha256']==a['code_sha256'] for r in rows)
   if grants and task.task_id in grants[-1]['task_ids'] and sequence>grants[-1]['effective_after'] and used<grants[-1]['max_uses']:out.append(a)
  return out
 def claim_trial(self,a,task,sequence):
  # Single-controller contract; durable consumption before any execution.
  if not any(x==a for x in self.eligible(task,sequence)):raise PermissionError('no trial permission')
  self.events.append('V3_TRIAL_RESERVED',dict(code_sha256=a['code_sha256'],task_id=task.task_id,sequence=sequence),time.time())

class V3FrozenLibrary(FrozenMathLibrary):
 def run(self,task,*,sequence):
  results=[]
  for a in self.registry.eligible(task,sequence):
   if a['origin']=='MOCK' and not self.engineering:raise PermissionError('Mock cannot enter real tasks')
   self.registry.claim_trial(a,task,sequence)
   result=self.runner.run(a,task);results.append(result)
   if result['status']=='APPLIED':break
  return results
