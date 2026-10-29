"""One component per model call; no mathematical algorithm supplied by host."""
import json
from .math_operator_v3_pipeline import CorrectiveAdapter
from .semantic_contract import FIELDS
from .contracts import canonical
VERSION='math-v3-component-generation-v1'
SAFETY=('Complete Python, no annotations/default arguments/classes/decorators. Helpers and literal constants allowed. No files/network/models/reflection/dunder attributes/eval/exec. Allowed imports math,collections,itertools,functools,re,heapq,bisect,fractions,statistics,json. Keep the implementation concise and reject unsupported inputs, rather than attempting every possible wording.')
class ComponentAdapter(CorrectiveAdapter):
 protocol=VERSION
 def preflight(self,request):
  if request['phase']!='candidate':raise ValueError('imported real mechanism; component candidates only')
  b=super().preflight(request);payload=json.loads(b['messages'][1]['content']);slot=request['slot']
  if slot==0:
   system=SAFETY+' Generate only the deterministic corrective algorithm. code: complete def solve(parameters) returning a nonempty answer string. applicability: JSON-encoded parameter JSON Schema, type object, additionalProperties false, no schema references. description: required mathematical assumptions, resource limits and uncertainty. Do not generate a matcher or tests in this request. Implement proposed_corrective_operation, never the invalid operation. Choose parameters yourself. Return exactly code, description, applicability as strings.'
  elif slot==1:
   payload.update(generated_solver=request['solver_code'],solver_parameter_schema=request['parameter_schema'],algorithm_assumptions=request['algorithm_assumptions'])
   system=SAFETY+' Generate only a semantic matcher for the supplied frozen algorithm; do not change its parameters or algorithm. code: complete def match(problem) returning exactly status (MATCH/DECLINE/UNKNOWN), parameters (object), reason (string), assumption_quotes (list of exact substrings of the input confirming required conditions), requested_quantity (string). Missing or ambiguous required constraints must yield UNKNOWN or DECLINE. Identify the requested mathematical quantity, not mere keywords. description: JSON-encoded semantic contract with exactly these nonempty string fields: '+','.join(FIELDS)+'. parameter_schema must encode the supplied schema unchanged. applicability: concise uncertainty note. MATCH requested_quantity must equal contract requested_quantity. Do not generate tests. Return exactly code, description, applicability as strings.'
  elif slot==2:
   payload.update(generated_contract=request['contract'])
   system='Propose at most 8 diverse tests for this declared computation. Include positive, negative, single-semantic-dimension near miss, resource boundary and ambiguous cases. Do not give numerical expected answers; all proposals require independent semantic/oracle review. Do not use hidden data. code: a JSON-encoded array of objects, each with exactly kind (POSITIVE/NEGATIVE/NEAR_MISS/BOUNDARY/AMBIGUOUS), problem, base_problem, changed_dimension, claimed_behavior, invariant; all fields strings. description: limitations. applicability: uncertainty. Return exactly code, description, applicability as strings.'
  else:raise ValueError('component slot')
  b['reasoning']={'effort':'low'}
  b['messages']=[dict(role='system',content=system),dict(role='user',content=canonical(payload))]
  if len(canonical(b).encode())+256>self.max_wire_input_upper:raise ValueError('wire bound')
  return b


class DeepSeekComponentAdapter(ComponentAdapter):
 """Explicit user-authorized model change; same components, no new mechanisms."""
 provider_origin='DEEPSEEK'
 protocol='math-v3-component-deepseek-v1'
 from .autonomous_generation import DeepSeekCompilerAdapter as _Transport
 _authorize=_Transport._authorize
 _post=_Transport._post
 _normalize_response=_Transport._normalize_response
 def preflight(self,request):
  from .model_api import configured_api_key
  if not self.mock and not configured_api_key():raise PermissionError('DeepSeek credential missing')
  b=super().preflight(request)
  b.pop('provider');b.pop('reasoning');b['model']=self.model
  b['response_format']={'type':'json_object'}
  b.update(thinking={'type':'disabled'},reasoning_effort='none',temperature=0)
  b['messages'][0]['content']+=' Return one JSON object with exactly nonempty string fields code, description, applicability.'
  if len(canonical(b).encode())+256>self.max_wire_input_upper:raise ValueError('wire bound')
  return b
