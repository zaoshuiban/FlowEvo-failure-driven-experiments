"""Versioned, non-semantic specification normalization. No model or execution.

Only exact type=json_object metadata may be removed. Every required value is
preserved verbatim. Ambiguous JSON/unknown fields fail closed, with a diagnostic
suitable for one separately budgeted revision; this module never sends requests.
"""
import hashlib,json
from .contracts import canonical
FIELDS=('mechanism','conditions','repair_strategy','refusal_conditions','stop_rule','limitations')
POLICY={'version':'spec-normalization-v1','required_fields':list(FIELDS),'required_type':'nonempty string','removable_metadata':{'type':'json_object'},'unknown_fields':'reject','duplicate_keys':'reject','truncated_response':'reject','semantic_value_changes':False,'max_optional_budgeted_spec_revision':1}
class SpecificationError(ValueError):
    pass

def normalize(response):
    text=response.get('text')
    if response.get('finish_reason')!='stop':raise SpecificationError('SPEC_NOT_COMPLETE')
    if not isinstance(text,str):raise SpecificationError('SPEC_TEXT_REQUIRED')
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:raise SpecificationError('SPEC_DUPLICATE_KEY:'+k)
            d[k]=v
        return d
    try:value=json.loads(text,object_pairs_hook=unique)
    except SpecificationError:raise
    except (ValueError,TypeError) as exc:raise SpecificationError('SPEC_JSON_INVALID') from exc
    if not isinstance(value,dict):raise SpecificationError('SPEC_OBJECT_REQUIRED')
    for key in FIELDS:
        if key not in value:raise SpecificationError('SPEC_MISSING_FIELD:'+key)
        if not isinstance(value[key],str) or not value[key].strip():raise SpecificationError('SPEC_FIELD_TYPE_OR_EMPTY:'+key)
    extra=set(value)-set(FIELDS)
    if extra-{'type'}:raise SpecificationError('SPEC_UNKNOWN_FIELDS:'+','.join(sorted(extra-{'type'})))
    if 'type' in value and value['type']!='json_object':raise SpecificationError('SPEC_METADATA_VALUE_NOT_ALLOWLISTED')
    spec={key:value[key] for key in FIELDS}
    return dict(specification=spec,normalization=dict(policy=POLICY['version'],policy_sha256=hashlib.sha256(canonical(POLICY).encode()).hexdigest(),raw_text_sha256=hashlib.sha256(text.encode()).hexdigest(),normalized_sha256=hashlib.sha256(canonical(spec).encode()).hexdigest(),removed_fields={'type':'json_object'} if 'type' in extra else {},required_values_unchanged=all(spec[k]==value[k] for k in FIELDS),origin='historical_real_response_normalized_not_new_induction'))
