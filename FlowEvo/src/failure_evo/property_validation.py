"""Default-off candidate properties. Finite tests NEVER establish a universal theorem."""
from .contracts import fingerprint

def parse_property_proposal(value):
    if not isinstance(value,dict) or set(value)!={'diagnosis','replacement_hypothesis','properties'}:
        raise ValueError('exact proposal fields')
    if any(not isinstance(value[k],str) or not value[k].strip() for k in ('diagnosis','replacement_hypothesis')):
        raise ValueError('nonempty hypotheses required')
    if not isinstance(value['properties'],list) or len(value['properties'])>3:raise ValueError('property bound')
    count=0
    for p in value['properties']:
        if not isinstance(p,dict) or set(p)!={'id','claim','preconditions','tests'}:raise ValueError('property fields')
        if any(not isinstance(p[k],str) or not p[k].strip() for k in ('id','claim','preconditions')):raise ValueError('property text')
        if not isinstance(p['tests'],list):raise ValueError('tests list')
        for t in p['tests']:
            if not isinstance(t,dict) or set(t)!={'relation','left','right'}:raise ValueError('test fields; no model gold accepted')
            if t['relation'] not in ('oracle_correct','equal','different'):raise ValueError('relation')
            if not isinstance(t['left'],dict) or (t['right'] is not None and not isinstance(t['right'],dict)):raise ValueError('parameters')
            if t['relation']!='oracle_correct' and t['right'] is None:raise ValueError('pair required')
            count+=1
    if count>8:raise ValueError('at most eight test specifications')
    return value

def adjudicate(relation, references, executions):
    """Host reference strings supplied only here, never returned as model feedback."""
    if any(r is None for r in references):return dict(status='UNVERIFIED',reason='NO_TRUSTED_REFERENCE')
    if relation in ('equal','different'):
        actual_relation=references[0]==references[1]
        if actual_relation!=(relation=='equal'):
            return dict(status='PROPERTY_COUNTEREXAMPLE',reason='INDEPENDENT_REFERENCE_REFUTES_PROPOSED_RELATION')
    if any(e.get('status')!='EXECUTED_UNSCORED' for e in executions):
        return dict(status='EXECUTION_FAILURE',reason='CLASSIFY_EXECUTION_SEPARATELY')
    if any(e['raw']['value']!=r for e,r in zip(executions,references)):
        return dict(status='ALGORITHM_COUNTEREXAMPLE',reason='TRUSTED_REFERENCE_DISAGREES')
    return dict(status='FINITE_SAMPLE_SUPPORTED',reason='NOT_A_UNIVERSAL_PROOF')

def bind_validation(source_sha256,proposal,records,role):
    return dict(source_sha256=source_sha256,proposal_sha256=fingerprint(proposal),
        evidence_sha256=fingerprint(records),role=role,records=records,
        status='FINITE_EVIDENCE_ONLY',experimental=False)

def check_binding(receipt,source_sha256):
    if receipt['source_sha256']!=source_sha256:raise ValueError('validation belongs to another source version')
    if receipt['evidence_sha256']!=fingerprint(receipt['records']):raise ValueError('validation records changed')
    return True
