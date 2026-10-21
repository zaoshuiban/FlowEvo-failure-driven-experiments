import hashlib
import json
import pathlib
import re
from comparison import stdio_equal, structured_equal
from contracts import (VALIDATED, InvalidTest, expected_value, function_args,
                       reference_oracle, std_input, validate)
from semantic import SUPPORTED


def preflight(task,policy):
    tests=json.loads(task['input_output'])
    if not isinstance(tests.get('inputs'),list) or not isinstance(tests.get('outputs'),list) or len(tests['inputs'])!=len(tests['outputs']):
        return {'task_id':task['task_id'],'status':'INVALID_TEST','error':'test arrays have inconsistent shapes'},[]
    report={'task_id':task['task_id'],'status':'READY','total_cases':len(tests['inputs']),
            'valid_cases':0,'invalid_cases':[],'reference_issues':[],'reference_corrections':[],
            'input_coverage':'task_specific_checks' if task['task_id'] in VALIDATED else 'structural_and_signature_only',
            'checker':policy['comparison'],'semantic_supported':task['task_id'] in SUPPORTED,
            'task_sha256':hashlib.sha256(json.dumps(task,sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
    if policy['protocol']=='interactive_unsupported':report['status']='PROTOCOL_UNSUPPORTED'
    if policy['comparison']=='semantic' and task['task_id'] not in SUPPORTED:report['status']='CHECKER_UNSUPPORTED'
    cases=[]
    for i,(inp,out) in enumerate(zip(tests['inputs'],tests['outputs'])):
        try:
            data=validate(task,inp)
            candidate_input=function_args(task,inp) if task.get('function_name') else std_input(inp)
        except (InvalidTest,ValueError,TypeError,IndexError,KeyError) as exc:
            report['invalid_cases'].append({'index':i,'rule':str(exc),'input_sha256':hashlib.sha256(json.dumps(inp,ensure_ascii=False).encode()).hexdigest(),'preview':str(inp)[:500]})
            continue
        try:expected=expected_value(task,out)
        except (InvalidTest,ValueError,TypeError) as exc:
            report['reference_issues'].append({'index':i,'reason':str(exc)})
            continue
        if policy['comparison']!='semantic' and not policy.get('epsilon') and policy.get('decimal_places') is None and policy.get('scientific_mantissa_places') is None:
            numbers=expected if isinstance(expected,str) else json.dumps(expected)
            if re.search(r'(?<![\w.])[-+]?\d+\.\d+(?:[eE][-+]?\d+)?(?![\w.])',numbers) and task.get('function_name') is None:
                report['reference_issues'].append({'index':i,'reason':'floating reference but no reviewed tolerance policy'})
                continue
        if policy.get('scientific_mantissa_places') is not None and not stdio_equal(expected,expected,policy):
            report['reference_issues'].append({'index':i,'reason':'reference violates declared scientific mantissa/exponent format','preview':str(expected)[:500]})
            continue
        oracle=reference_oracle(task,inp)
        if oracle is not None:
            value,proof=oracle
            if not stdio_equal(value,expected,policy):
                report['reference_corrections'].append({'index':i,'old':expected,'new':value,'proof':proof})
                expected=value
        cases.append({'index':i,'input':candidate_input,'semantic_data':data,'expected':expected})
    report['valid_cases']=len(cases)
    if not cases and report['status']=='READY':report['status']='NO_VALID_TESTS'
    # Ambiguous references are not silently removed to manufacture a passing task.
    if report['reference_issues'] and report['status']=='READY':report['status']='REFERENCE_DISPUTE'
    return report,cases
