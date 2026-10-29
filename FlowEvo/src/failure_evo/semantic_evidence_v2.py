"""Default-off generic evidence protocol. No mathematical domain predicates.
Whole-source review is not evidence for any operational premise. Derivations are
restricted to mechanically checked copy/list length; arbitrary inference fails.
"""
import jsonschema
from .structured_semantics import StructuredRunner
from .contracts import fingerprint

KINDS={'EXPLICIT_AFFIRMATION','EXPLICIT_NEGATION','NOT_STATED','UNRESOLVED','DERIVED'}
def validate_packet(semantics,problem,p):
 if set(p)!={'task_id','facts','evidence','review'}:raise ValueError('PACKET_FIELDS')
 facts=p['facts'];jsonschema.validate(facts,semantics['schema'])
 ev=p['evidence']
 if not isinstance(ev,dict) or set(ev)!=set(facts):raise ValueError('EVIDENCE_FIELDS')
 visiting=set();checked=set()
 def check(k):
  if k in checked:return
  if k in visiting:raise ValueError('DERIVATION_CYCLE')
  visiting.add(k);e=ev[k];value=facts[k]
  if not isinstance(e,dict) or set(e)!={'kind','quotes','scope','rule','from_field'} or e['kind'] not in KINDS:raise ValueError('EVIDENCE_TYPE:'+k)
  qs=e['quotes']
  if not isinstance(qs,list) or any(not isinstance(q,str) or not q or q not in problem for q in qs):raise ValueError('QUOTE_BINDING:'+k)
  if e['kind'].startswith('EXPLICIT_'):
   if value is None or not qs or e['scope']!='QUOTED_TEXT' or e['rule'] is not None or e['from_field'] is not None:raise ValueError('EXPLICIT_EVIDENCE:'+k)
  elif e['kind'] in ('NOT_STATED','UNRESOLVED'):
   if value is not None or e['scope']!='FULL_PROBLEM' or e['rule'] is not None or e['from_field'] is not None:raise ValueError('UNKNOWN_MUST_REMAIN_NULL:'+k)
   if e['kind']=='NOT_STATED' and qs:raise ValueError('ABSENCE_HAS_NO_QUOTE:'+k)
  else:
   src=e['from_field']
   if e['scope']!='DERIVED_FIELDS' or qs or src not in facts or e['rule'] not in ('EXACT_COPY','LIST_LENGTH'):raise ValueError('DERIVATION_NOT_ALLOWED:'+k)
   check(src)
   if facts[src] is None:raise ValueError('UNKNOWN_DERIVATION:'+k)
   if e['rule']=='EXACT_COPY':expected=facts[src]
   elif isinstance(facts[src],list):expected=len(facts[src])
   else:raise ValueError('DERIVATION_TYPE:'+k)
   if type(value)!=type(expected) or value!=expected:raise ValueError('DERIVATION_VALUE:'+k)
  visiting.remove(k);checked.add(k)
 for k in facts:check(k)
 review=p['review']
 if not isinstance(review,dict) or set(review)!={'status','quotes','scope'} or review['status'] not in ('NO_ISSUE_OBSERVED','CONFLICT','UNRESOLVED') or review['scope']!='FULL_PROBLEM':raise ValueError('REVIEW_FIELDS')
 qs=review['quotes']
 if not isinstance(qs,list) or any(not isinstance(q,str) or not q or q not in problem for q in qs):raise ValueError('REVIEW_QUOTES')
 if review['status']=='CONFLICT' and not qs:raise ValueError('CONFLICT_NEEDS_QUOTES')
 return facts

class EvidenceRunner(StructuredRunner):
 def run(self,a,public_task,parsed,provenance):
  if provenance.get('origin')!='MODEL_PARSE' or provenance.get('problem_sha256')!=fingerprint(public_task['problem']) or provenance.get('parsed_sha256')!=fingerprint(parsed) or not provenance.get('response_sha256'):raise PermissionError('model response provenance required')
  if parsed.get('task_id')!=public_task['task_id']:raise PermissionError('task identity')
  try:facts=validate_packet(self.semantics,public_task['problem'],parsed)
  except (ValueError,jsonschema.ValidationError) as e:return dict(status='DECLINED',match=dict(status='UNKNOWN',reason='EVIDENCE_VALIDATION:'+str(e)[:400]),gold_exposed=False,stage='EVIDENCE_REJECTED')
  if parsed['review']['status']!='NO_ISSUE_OBSERVED':return dict(status='DECLINED',match=dict(status='UNKNOWN',reason='WHOLE_SOURCE_REVIEW_UNRESOLVED'),gold_exposed=False,stage='REVIEW_UNRESOLVED')
  required=a['provenance']['required_facts']
  if not required or any(k not in facts for k in required):raise PermissionError('required facts contract')
  if any(facts[k] is None for k in required):return dict(status='DECLINED',match=dict(status='UNKNOWN',reason='NECESSARY_PREMISE_NOT_KNOWN'),gold_exposed=False,stage='PREMISE_UNKNOWN')
  return dict(self._execute(a,facts),stage='CONTRACT_EXECUTED')
