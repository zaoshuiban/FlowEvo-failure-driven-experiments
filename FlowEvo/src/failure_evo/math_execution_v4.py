"""Default-off V4 interfaces. Extraction has no scorer/oracle access."""
import hashlib
import json
import jsonschema
from .semantic_contract import component_check
from .contracts import fingerprint
VERSION = 'math-execution-v4.0'

def extract_parameters(problem, schema, extractor):
    if not isinstance(problem, str) or not problem.strip():
        return dict(status='PARAMETER_SCHEMA_ERROR', reason='problem required')
    # Only these two public fields cross the extraction boundary.
    request = dict(problem=problem, parameter_schema=schema)
    result = extractor(request)
    if not isinstance(result, dict) or set(result) != {'status', 'parameters', 'reason'} or result['status'] not in ('MAPPED', 'UNKNOWN'):
        return dict(status='INTERFACE_ERROR', request_sha256=fingerprint(request))
    return dict(result, request_sha256=fingerprint(request), gold_exposed=False)

def validate_parameters(parameters, schema):
    # Reject remote/ref capabilities instead of letting a validator fetch them.
    def check(node):
        if isinstance(node, dict):
            if any(k in node for k in ('$ref', '$dynamicRef', '$id')):
                raise ValueError('schema reference forbidden')
            for value in node.values(): check(value)
        elif isinstance(node, list):
            for value in node: check(value)
    try:
        check(schema)
        if schema.get('type') != 'object' or schema.get('additionalProperties') is not False:
            raise ValueError('closed object required')
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(parameters)
        return dict(status='PARAMETERS_VALID')
    except (ValueError, jsonschema.ValidationError, jsonschema.SchemaError) as exc:
        return dict(status='PARAMETER_SCHEMA_ERROR', reason=str(exc)[:1000])

def classify_execution(raw):
    status = raw.get('status')
    if status in ('WORKER_ERROR', 'EVALUATOR_ERROR'):
        return 'INFRASTRUCTURE_ERROR'
    if status in ('TIME_LIMIT', 'OUTPUT_LIMIT', 'MEMORY_LIMIT'):
        return 'RESOURCE_EXCEEDED'
    if status != 'OK': return 'RUNTIME_ERROR'
    if not isinstance(raw.get('value'), str) or not raw['value'].strip() or len(raw['value']) > 4096:
        return 'INTERFACE_ERROR'
    return 'EXECUTED_UNSCORED'

def execute_frozen(path, sha256, parameters, backend, timeout=2):
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha256:
        raise RuntimeError('SOURCE_HASH_MISMATCH')
    check = component_check(path.read_text(), 'solve')
    if not check['passed']: return dict(status='STATIC_REJECTED', review=check)
    with backend(path) as worker:
        raw = worker.call(dict(mode='function', function='solve', args=[parameters], timeout=timeout))
    status = classify_execution(raw)
    if status == 'INFRASTRUCTURE_ERROR': raise RuntimeError('WORKER_INFRASTRUCTURE:' + json.dumps(raw))
    return dict(status=status, raw=raw, code_sha256=sha256, parameters_sha256=fingerprint(parameters), gold_exposed=False)
