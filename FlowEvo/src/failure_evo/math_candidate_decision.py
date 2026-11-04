"""Two independent MODEL assessments. Neither is mathematical verification or permission.
Legacy HYPOTHESIS_ONLY/PROPOSE envelopes are deliberately not normalized into this schema.
"""
from .contracts import canonical
VERSION='math-dual-assessment-v1'
def obj(properties):return dict(type='object',additionalProperties=False,required=list(properties),properties=properties)
S={'type':'string','minLength':1,'maxLength':6000}
ARRAY=dict(type='array',items=S,maxItems=32)
DETAILS=obj(dict(parameters=obj(dict(description=S,json_schema=S)),output=obj(dict(role=dict(type='string',enum=['ANSWER','DIAGNOSTIC']),description=S)),
                computation_steps=dict(type='array',minItems=1,maxItems=32,items=obj(dict(operation=S,inputs=S,outputs=S))),
                preconditions=ARRAY,rejection_conditions=ARRAY,resource_bound=S,
                independent_validation=obj(dict(method=S,independence_basis=S,limitations=S))))
SCHEMA=obj(dict(mechanism_assessment=obj(dict(status=dict(type='string',enum=['SUPPORTED','SUSPECTED','UNSUPPORTED']),reason=S,evidence_refs=ARRAY)),
                algorithm_candidate=obj(dict(decision=dict(type='string',enum=['GENERATE','NEEDS_SPECIFICATION','NOT_GENERATABLE']),reason=S,details=dict(anyOf=[DETAILS,dict(type='null')])))))
INSTRUCTIONS=('Make TWO independent assessments. mechanism_assessment judges evidence for a shared failure cause; SUPPORTED is only your evidence assessment, never host verification. '
 'algorithm_candidate judges whether there is a specific parameterized deterministic computation worth IMPLEMENTING AND TESTING. '
 'SUSPECTED or UNSUPPORTED cause does not prohibit GENERATE. A plausible common cause does not imply an executable algorithm. '
 'GENERATE requires a closed parameter JSON schema, explicit output role/quantity, concrete computational steps with inputs/outputs, premises, rejection conditions, finite resource bounds and an independently checkable validation plan. '
 'Advice such as check carefully, find a construction or prove optimality without an implementable procedure must be NEEDS_SPECIFICATION or NOT_GENERATABLE. '
 'You may propose a bounded verifier without solving the full problem; use DIAGNOSTIC, not ANSWER. A diagnostic is not a replacement answer solver. '
 'Do not assume or assert oracle availability, validated correctness, admission or common causality. Proposed tests or expected answers are not trusted oracles. '
 'No algorithm name, count, success or predefined mathematical implementation is required. Do not use gold, future tasks, fixed answers or task-ID lookup. '
 'Host clipping is not model truncation. Return the exact JSON schema: ')

def parse_decision(value):
    import json,jsonschema
    jsonschema.Draft202012Validator(SCHEMA).validate(value)
    c=value['algorithm_candidate']
    if c['decision']=='GENERATE' and c['details'] is None:raise ValueError('GENERATE requires concrete algorithm details')
    if c['details'] is not None:
        try:
            schema=json.loads(c['details']['parameters']['json_schema'])
            if schema.get('type')!='object' or schema.get('additionalProperties') is not False or not isinstance(schema.get('properties'),dict) or not schema['properties']:raise ValueError('closed nonempty parameter schema required')
            if not isinstance(schema.get('required'),list) or not set(schema['required'])<=set(schema['properties']):raise ValueError('parameter required fields')
            if '$ref' in canonical(schema) or '$dynamicRef' in canonical(schema):raise ValueError('parameter schema references forbidden')
            jsonschema.Draft202012Validator.check_schema(schema)
        except (TypeError,AttributeError,json.JSONDecodeError,jsonschema.exceptions.SchemaError) as exc:raise ValueError('invalid parameter schema') from exc
    return value

def validate_decision(value):
    try:return parse_decision(value)
    except Exception as exc:
        # Adapter classifies this as received-but-invalid, never as network UNKNOWN.
        if isinstance(exc,ValueError):raise
        raise ValueError('dual assessment schema invalid: '+str(exc)[:250]) from exc

def generatable(value):return validate_decision(value)['algorithm_candidate']['decision']=='GENERATE'

def bind_evidence(value,allowed):
    refs=value['mechanism_assessment']['evidence_refs']
    if not set(refs)<=set(allowed):raise ValueError('mechanism cites unavailable evidence')
    if value['mechanism_assessment']['status']=='SUPPORTED' and not refs:raise ValueError('SUPPORTED assessment requires evidence references')
    return value
