"""Generic v3 correction contracts; no task-family algorithms or conditions."""
import json
from .contracts import fingerprint
FIELDS=('failure_observation','failure_diagnosis','suspected_invalid_operation','why_operation_may_fail','proposed_corrective_operation','correctness_argument','required_assumptions','applicability_conditions','known_counterexamples','unresolved_uncertainties')
SCHEMA=dict(type='object',additionalProperties=False,required=['source_evidence_ids','generation_decision',*FIELDS],properties={
 'source_evidence_ids':dict(type='array',items=dict(type='string')),
 'generation_decision':dict(type='string',enum=['NO_MECHANISM','HYPOTHESIS_ONLY','PROPOSE_CORRECTION']),**{k:dict(type='string') for k in FIELDS}})
def parse(v):
 if not isinstance(v,dict) or set(v)!=set(SCHEMA['required']):raise ValueError('corrective mechanism exact fields')
 if v['generation_decision'] not in SCHEMA['properties']['generation_decision']['enum']:raise ValueError('decision')
 if not isinstance(v['source_evidence_ids'],list) or not v['source_evidence_ids'] or any(not isinstance(x,str) for x in v['source_evidence_ids']):raise ValueError('source IDs')
 if any(not isinstance(v[k],str) or not 1<=len(v[k])<=10000 for k in FIELDS):raise ValueError('text fields')
 return v
def difference_check(m):
 parse(m)
 same=' '.join(m['suspected_invalid_operation'].lower().split())==' '.join(m['proposed_corrective_operation'].lower().split())
 return dict(status='ERROR_REPRODUCTION_RISK' if same else 'CORRECTION_UNVERIFIED',reason='Identical operation descriptions' if same else 'Different text is not a proof of corrective computation',mechanism_sha256=fingerprint(m),verified=False)
def algorithm_spec(m):
 parse(m)
 if m['generation_decision']!='PROPOSE_CORRECTION':raise PermissionError('no executable proposal')
 return {k:m[k] for k in ('proposed_corrective_operation','correctness_argument','required_assumptions','applicability_conditions','known_counterexamples','unresolved_uncertainties')}
