"""Offline/default-off typed goal checker; no domain predicates or text matching.
Tree equality is conservative structural agreement, NOT semantic truth or admission.
Vocabulary, capability declaration and problem interpretation require independent review.
"""
import re
import jsonschema
from .contracts import fingerprint

VERSION='typed-goal-consistency-v1'

def _exact(value,keys):
    if not isinstance(value,dict) or set(value)!=set(keys):raise ValueError('ENVELOPE_FIELDS')

def vocabulary_check(vocab):
    if not isinstance(vocab,dict) or not 1<=len(vocab)<=128:raise ValueError('VOCABULARY_SIZE')
    for key,v in vocab.items():
        if not isinstance(key,str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,63}',key):raise ValueError('SYMBOL_ID')
        _exact(v,('inputs','output','definition'))
        if not isinstance(v['inputs'],list) or len(v['inputs'])>8 or any(not isinstance(x,str) or not x for x in v['inputs']+[v['output']]):raise ValueError('SYMBOL_TYPES')
        if not isinstance(v['definition'],str) or not v['definition'].strip():raise ValueError('SYMBOL_DEFINITION')

def term_type(term,vocab,depth=0):
    if depth>12:raise ValueError('TERM_DEPTH')
    if term is None:return None
    _exact(term,('symbol','arguments'))
    key=term['symbol'];args=term['arguments']
    if not isinstance(key,str) or key not in vocab:raise ValueError('UNDECLARED_SYMBOL')
    if not isinstance(args,list) or len(args)!=len(vocab[key]['inputs']):raise ValueError('ARITY')
    types=[term_type(x,vocab,depth+1) for x in args]
    if None in types:return None
    if types!=vocab[key]['inputs']:raise ValueError('TYPE_MISMATCH')
    return vocab[key]['output']

def _terms(goal,conditions,vocab):
    kind=term_type(goal,vocab)
    if not isinstance(conditions,dict) or len(conditions)>32:raise ValueError('CONDITIONS')
    unknown=kind is None
    for name,term in conditions.items():
        if not isinstance(name,str) or not name:raise ValueError('CONDITION_NAME')
        typ=term_type(term,vocab)
        if typ is None:unknown=True
        elif typ!='proposition':raise ValueError('CONDITION_TYPE')
    return unknown

def compare_goal(capability,parsed,vocabulary,*,code_sha256,problem_sha256):
    """Already acquired facts only. No execution/permission change on MATCH.
    Raw request separation and evidence verification are caller responsibilities.
    """
    def decision(status,reason):
        return dict(protocol=VERSION,status=status,reason=reason,
            execute_authorized=False,semantic_truth_verified=False,
            capability_sha256=fingerprint(capability),parse_sha256=fingerprint(parsed),
            vocabulary_sha256=fingerprint(vocabulary))
    try:
        vocabulary_check(vocabulary)
        _exact(capability,('code_sha256','vocabulary_sha256','goal','requires','parameter_schema','limitations'))
        _exact(parsed,('problem_sha256','vocabulary_sha256','goal','conditions','parameters','uncertain'))
        vh=fingerprint(vocabulary)
        if capability['code_sha256']!=code_sha256 or parsed['problem_sha256']!=problem_sha256 or capability['vocabulary_sha256']!=vh or parsed['vocabulary_sha256']!=vh:
            return decision('UNKNOWN','PROVENANCE_MISMATCH')
        if type(parsed['uncertain']) is not bool or not isinstance(capability['limitations'],list) or any(not isinstance(x,str) for x in capability['limitations']):raise ValueError('DECLARATION_TYPES')
        if _terms(capability['goal'],capability['requires'],vocabulary) or _terms(parsed['goal'],parsed['conditions'],vocabulary) or parsed['uncertain']:
            return decision('UNKNOWN','UNRESOLVED_PREMISE_OR_GOAL')
        # No contains(), synonyms, model-produced Python, or heuristic algebra.
        if fingerprint(capability['goal'])!=fingerprint(parsed['goal']):
            return decision('DECLINE','GOAL_STRUCTURE_DIFFERS')
        if set(capability['requires'])!=set(parsed['conditions']):
            return decision('UNKNOWN','MISSING_OR_UNSUPPORTED_CONDITION')
        if fingerprint(capability['requires'])!=fingerprint(parsed['conditions']):
            return decision('DECLINE','PREMISE_STRUCTURE_DIFFERS')
        schema=capability['parameter_schema']
        if not isinstance(schema,dict) or schema.get('type')!='object' or schema.get('additionalProperties') is not False:raise ValueError('CLOSED_PARAMETER_SCHEMA_REQUIRED')
        # External schemas/references cannot become a hidden network channel.
        def no_refs(x):
            if isinstance(x,dict):
                if any(k in x for k in ('$ref','$dynamicRef','$recursiveRef')):raise ValueError('SCHEMA_REFERENCE_FORBIDDEN')
                for v in x.values():no_refs(v)
            elif isinstance(x,list):
                for v in x:no_refs(v)
        no_refs(schema);jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(parsed['parameters'])
        return decision('MATCH','TYPED_STRUCTURAL_AGREEMENT_ONLY')
    except (ValueError,TypeError,KeyError,jsonschema.ValidationError,jsonschema.SchemaError):
        return decision('UNKNOWN','INVALID_SEMANTIC_CONTRACT')


def declaration_view(code):
    """Only source/interface; no new tasks, test answers or selection labels."""
    if not isinstance(code,str) or not code.strip():raise ValueError('source required')
    return dict(protocol=VERSION,source=code,instruction='Describe the actual implemented computation, input types, mathematical object, output quantity, necessary conditions and limitations. Do not infer desired capability from tests. A declaration is unverified; do not claim permission.')

def problem_view(problem,vocabulary):
    """Parser has shared vocabulary, NOT candidate declarations or source code."""
    if not isinstance(problem,str) or not problem.strip():raise ValueError('problem required')
    vocabulary_check(vocabulary)
    return dict(protocol=VERSION,problem=problem,vocabulary=vocabulary,
        instruction='Describe the requested mathematical object, output quantity, parameters and constraints faithfully. Retain explicit negation, missing information and uncertainty. Unsupported true requirements must not be coerced into a supported value. Attach evidence for a separate host review; do not choose an operator.')
