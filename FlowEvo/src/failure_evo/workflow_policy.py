"""Versioned host-mediated workflow policies. Workers retain zero model/network calls.

The model writes the applicability/repair instruction; this host only validates,
charges, executes and judges it. Old S1 Python repair contracts are unchanged.
"""
import ast
import copy
import hashlib
import time
from dataclasses import dataclass, fields
from pathlib import Path
from .contracts import canonical, fingerprint, PublicFeedback
from .failure_registry import FailureOperator, FailureOperatorRegistry, OperatorSnapshot
from .failure_events import checked_public_feedback, structural_status
from .plugin import FailureLearningPlugin
from .runtime import BudgetExhausted
from .static_contract import exit_paths

REPRESENTATION = 'python_host_repair_policy_v1'
SAFE_IMPORTS = {'ast','json','math','collections','itertools','functools','re','heapq','bisect','fractions','statistics'}
FORBIDDEN = {'open','eval','exec','compile','getattr','setattr','globals','locals','vars','input','breakpoint','help'}
CONTRACT = {
 'representation': REPRESENTATION, 'entry': 'repair_operator(context)',
 'input': {'task_public': ['problem_id','prompt','starter_code','function_name','public_examples'],
           'candidate_code': 'str', 'public_feedback': {'status':'str','summary':'str','public_cases':[{'input':'str','expected':'str','actual':'str','exception_class':'str or null'}]},
           'generation_metadata': {'finish_reason':'stop/length/unknown/error'},
           'remaining_budget': {'remaining_calls':'int', 'remaining_tokens':'int', 'remaining_seconds':'float'},
           'hook': 'before_native_retry', 'stage':'l2a/l2b/l3/l4'},
 'output': {'request': {'status':'request_repair','instruction':'nonempty str <= 6000 UTF8 bytes','reason':'str'},
            'decline': {'status':'declined','reason':'str'}, 'error': {'status':'error','reason':'str'}},
 'worker_model_calls':0, 'host_model_calls_per_invocation':1,
 'host': 'Host prepends actual task, current code and public feedback; your instruction is supplemental. Host validates full proposed program on public tests. Failure falls back within SAME task allowance. Never return applied yourself.',
 'permissions': {'imports':sorted(SAFE_IMPORTS),'forbidden_names':sorted(FORBIDDEN),'dunder_names_attributes':False},
}

def validate_source(source):
 findings=[]
 try: tree=ast.parse(source)
 except (SyntaxError,ValueError) as e:return {'passed':False,'findings':[str(e)]}
 entry=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='repair_operator']
 if len(entry)!=1 or len(entry[0].args.args)!=1 or entry[0].args.args[0].arg!='context' or entry[0].args.vararg or entry[0].args.kwarg or entry[0].args.kwonlyargs or entry[0].args.posonlyargs or entry[0].args.defaults:
  findings.append('exact entry repair_operator(context) required')
 for node in ast.walk(tree):
  if isinstance(node,ast.Import) and any(x.name.split('.')[0] not in SAFE_IMPORTS for x in node.names):findings.append(f'line {node.lineno}: forbidden import')
  if isinstance(node,ast.ImportFrom) and (node.level or (node.module or '').split('.')[0] not in SAFE_IMPORTS):findings.append(f'line {node.lineno}: forbidden import')
  if isinstance(node,ast.Name) and (node.id.startswith('__') or node.id in FORBIDDEN):findings.append(f'line {node.lineno}: forbidden {node.id}')
  if isinstance(node,ast.Attribute) and node.attr.startswith('__'):findings.append(f'line {node.lineno}: forbidden attribute')
 if entry and bool({'NEXT','UNVERIFIED'} & exit_paths(entry[0].body)):findings.append('entry can fall through')
 return dict(passed=not findings, findings=findings, representation=REPRESENTATION,
             limitation='syntax/entry/permissions only; functional checks independently required')

def validate_decision(result):
 if not isinstance(result,dict) or len(canonical(result).encode())>8192:raise ValueError('invalid decision size/type')
 if result.get('status')=='request_repair':
  if set(result)!= {'status','instruction','reason'} or not isinstance(result['instruction'],str) or not result['instruction'].strip() or len(result['instruction'].encode())>6000:raise ValueError('invalid repair request')
 elif result.get('status') in ('declined','error'):
  if set(result)!= {'status','reason'}:raise ValueError('action on refusal or unknown fields')
 else:raise ValueError('unknown action/status')
 if not isinstance(result['reason'],str):raise ValueError('reason must be text')
 return result

@dataclass(frozen=True)
class WorkflowPolicy(FailureOperator):
 allowed_actions: tuple = ('request_repair',)
 hooks: tuple = ('before_native_retry',)
 stages: tuple = ('l2a','l2b','l3','l4')
 max_seconds: float = 5.0
 operator_kind: str = 'prompt_policy'
 representation: str = REPRESENTATION
 max_host_model_requests: int = 1
 def __post_init__(self):
  if self.representation!=REPRESENTATION or self.max_host_model_requests!=1 or self.allowed_actions!=('request_repair',) or self.max_model_calls!=0:raise ValueError('unsupported workflow capability')
  # Reuse metadata validation without granting the old contract a new capability.
  metadata={f.name:getattr(self,f.name) for f in fields(FailureOperator)}
  metadata['allowed_actions']=('candidate_code',)
  FailureOperator(**metadata)

class WorkflowRegistry(FailureOperatorRegistry):
 def snapshot(self, *, stream_id, task_index, experiment_id='', at):
  if type(task_index) is not int or task_index<1:raise ValueError('positive task index required')
  cards=[]
  for row in self.events.visible(at):
   if row['kind']!='SHADOW_REGISTERED':continue
   card=WorkflowPolicy.from_dict(row['payload']['card']);state=self.state(card,at);auth=state['authorization']
   if auth and auth['stream_id']==stream_id and auth['experiment_id']==experiment_id and auth['effective_from']<=task_index and state['opportunities_remaining'] and self.valid(card,at):cards.append(card)
  cards=tuple(sorted(cards,key=lambda c:(-c.priority,c.operator_id,c.version)))
  return OperatorSnapshot(fingerprint([stream_id,task_index,[c.to_dict() for c in cards]]),stream_id,task_index,cards,experiment_id,at)

def worker_context(task, code, feedback, metadata, budget, stage='l2a'):
 return dict(task_public=task, candidate_code=code, public_feedback=feedback,
             generation_metadata=metadata, hook='before_native_retry',stage=stage,
             remaining_budget=dict(remaining_calls=max(0,budget.max_calls-budget.calls),
                 remaining_tokens=max(0,budget.max_tokens-budget.used_tokens-sum(budget.reservations.values())),remaining_seconds=budget.remaining_seconds))

class WorkflowPlugin(FailureLearningPlugin):
 """Policy requests exactly one charged repair, with one native fallback reserved."""
 def __init__(self,*args,host_repair,decision_runner,allow_actions=True,**kw):
  super().__init__(*args,**kw);self.host_repair=host_repair;self.decision_runner=decision_runner;self.allow_actions=allow_actions
 def invoke(self,hook,checkpoint,stage,code,feedback,budget,evaluator,at):
  s=self.current
  if not self.allow_actions or hook!='before_native_retry' or feedback.status=='PUBLIC_PASS':return None
  # At most one invocation per policy version per task, not per failed stage.
  eligible=[c for c in s['snapshot'].cards if (c.operator_id,c.version) not in s['attempted'] and feedback.status in c.allowed_feedback and structural_status(code) in c.structural_statuses and self.registry.valid(c,None)]
  if not eligible:return None
  card=eligible[0]
  if budget.max_calls-budget.calls<2 or budget.remaining_seconds<20:return None
  reservation=self.registry.reserve_opportunity(card,stream_id=self.stream_id,experiment_id=self.experiment_id,task_index=s['snapshot'].task_index,task_id=s['task'].problem_id,checkpoint=checkpoint,hook=hook,program_sha256=hashlib.sha256(code.encode()).hexdigest(),at=at)
  if not reservation:return None
  s['attempted'].add((card.operator_id,card.version))
  audit=dict(operator_id=card.operator_id,version=card.version,hook=hook,stage=stage,checkpoint=checkpoint,snapshot_id=s['snapshot'].snapshot_id,status='error',public_check_outcome='unavailable')
  s['hooks'].append(audit);started=time.monotonic();before=budget.snapshot()
  payload=worker_context(s['task'].to_dict(),code,feedback.to_dict(),s['ledger'][-1]['generation_metadata'] if s['ledger'] else {},budget,stage)
  audit['input']=copy.deepcopy(payload)
  try:
   budget.tool();decision=validate_decision(self.decision_runner(card,payload));audit['decision']=decision
   if decision['status']!='request_repair':audit.update(status=decision['status'],reason=decision['reason']);return None
   if not self.registry.valid(card,None):raise ValueError('authorization invalidated')
   response=self.host_repair(payload,decision['instruction'],budget)
   proposed=response['code'];audit.update(proposed=True,proposed_sha256=hashlib.sha256(proposed.encode()).hexdigest())
   candidate=self.observe(proposed,stage+':workflow_policy',PublicFeedback('UNKNOWN'),response,time.time(),hashlib.sha256(code.encode()).hexdigest())
   budget.tool();raw=evaluator(s['task'],proposed);public=checked_public_feedback(raw);candidate['public_feedback']=public.to_dict();candidate['validation_cost']['tool_calls']=1
   audit.update(public_check_outcome='passed' if public.status=='PUBLIC_PASS' else 'failed',verification=public.to_dict())
   if public.status!='PUBLIC_PASS':audit.update(status='declined',reason='host_public_validation_failed');return None
   if not self.registry.valid(card,None):raise ValueError('authorization invalidated')
   audit.update(status='applied',reason='host_verified_repair')
   return dict(stage=stage+':workflow_policy',code=proposed,code_sha256=candidate['code_sha256'],public_feedback=public)
  except ValueError as exc:
   audit.update(status='error',reason=str(exc));self.registry.suspend(card,'workflow_contract_violation',time.time());return None
  except Exception as exc:
   audit.update(status='error',reason=type(exc).__name__);return None
  finally:
   audit['actual_cost']=dict(model_calls=budget.calls-before['calls'],model_tokens=budget.used_tokens-before['charged_or_reserved_tokens'],tool_calls=budget.tool_calls-before['tool_calls'],elapsed_seconds=time.monotonic()-started)
   self.registry.complete_opportunity(card,reservation,outcome=audit,at=time.time())
