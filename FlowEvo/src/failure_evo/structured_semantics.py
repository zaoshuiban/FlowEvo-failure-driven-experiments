"""Default-off structured semantics transport; no mathematical matching rules.
The schema and match(facts) are model-produced. Trusted facts use an offline-only
entry point; the runtime path accepts only provenance-bound model parses.
"""
import json
import jsonschema
from .contracts import fingerprint,canonical
from .semantic_contract import SplitRunner

def check_parse(semantics, problem, parsed):
 if set(parsed)!={'task_id','facts','evidence'}:raise ValueError('PARSER_ENVELOPE')
 facts=parsed['facts'];jsonschema.validate(facts,semantics['schema'])
 ev=parsed['evidence']
 if not isinstance(ev,dict) or set(ev)!=set(facts):raise ValueError('EVIDENCE_FIELDS')
 for k,value in facts.items():
  qs=ev[k]
  if not isinstance(qs,list) or any(not isinstance(q,str) or not q or q not in problem for q in qs):raise ValueError('UNBOUND_QUOTE:'+k)
  unknown=value is None or (isinstance(value,str) and value.upper()=='UNKNOWN')
  if not unknown and not qs:raise ValueError('UNSUPPORTED_ASSERTION:'+k)
 return facts

class StructuredRunner:
 def __init__(self,split,semantics):
  if not isinstance(split,SplitRunner):raise TypeError('existing SplitRunner required')
  self.split=split;self.semantics=semantics
 def _execute(self,a,facts):
  jsonschema.validate(facts,self.semantics['schema'])
  if a['provenance']['semantics_sha256']!=fingerprint(self.semantics):raise PermissionError('semantic version changed')
  raw=self.split.component(a,'match',facts);v=raw.get('value')
  required={'status','parameters','reason','assumption_quotes','requested_quantity'}
  if raw.get('status')!='OK' or not isinstance(v,dict) or set(v)!=required or v.get('status') not in ('MATCH','DECLINE','UNKNOWN') or not isinstance(v.get('parameters'),dict) or not isinstance(v.get('reason'),str) or v.get('assumption_quotes')!=[] or not isinstance(v.get('requested_quantity'),str) or len(canonical(v))>16384:
   return dict(status='ERROR',match=dict(status='ERROR',reason='STRUCTURED_MATCH_CONTRACT'))
  if v['status']=='MATCH':
   if v['requested_quantity']!=a['contract']['requested_quantity']:return dict(status='ERROR',match=dict(status='ERROR',reason='QUANTITY_BINDING'))
   result=self.split.solve(a,v['parameters'])
  else:result=dict(status='DECLINED',reason=v['reason'])
  return dict(result,match=v,code_sha256=a['code_sha256'],gold_exposed=False)
 def run(self,a,public_task,parsed,provenance):
  if provenance.get('origin')!='MODEL_PARSE' or provenance.get('problem_sha256')!=fingerprint(public_task['problem']) or provenance.get('parsed_sha256')!=fingerprint(parsed) or not provenance.get('response_sha256'):raise PermissionError('runtime requires bound real parser response; trusted facts forbidden')
  if parsed.get('task_id')!=public_task['task_id']:raise PermissionError('parser task identity')
  try:facts=check_parse(self.semantics,public_task['problem'],parsed)
  except (ValueError,jsonschema.ValidationError) as e:return dict(status='DECLINED',match=dict(status='UNKNOWN',reason='PARSER_VALIDATION:'+str(e)[:400]),gold_exposed=False)
  return self._execute(a,facts)
 def diagnose_trusted(self,a,facts,*,offline_attribution=False):
  if offline_attribution is not True:raise PermissionError('trusted facts are offline only')
  return dict(self._execute(a,facts),diagnostic_only=True,eligible_for_runtime=False)
