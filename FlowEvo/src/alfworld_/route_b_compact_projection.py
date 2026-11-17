"""B0.1 lossless public packets; no transport or permission creation.

Scarce types remain explicit exploratory strata, never duplicated examples.
Old B0 selection and artifacts are not changed.
"""
import re
from failure_evo.contracts import canonical,fingerprint
from alfworld_.route_b_information import ARMS,packet,wire,measure

VERSION='route-b-compact-scarce-strata-v1'
CODEC='all-string-values-dictionary-v1'
INSTRUCTION=('Evidence encoding: every string VALUE in data is a reference $N to strings[N] '
 'using zero-based indices. JSON field names, numbers, booleans and null remain literal. '
 'Resolve references before interpreting evidence. The dictionary contains original verbatim text, '
 'not extra examples. Repeated references are not independent observations.')

def encode(packet):
    table=[];index={}
    def visit(value):
        if isinstance(value,str):
            if value not in index:index[value]=len(table);table.append(value)
            return '$'+str(index[value])
        if isinstance(value,list):return [visit(x) for x in value]
        if isinstance(value,dict):return {k:visit(value[k]) for k in sorted(value)}
        if value is None or type(value) in (bool,int,float):return value
        raise ValueError('unsupported JSON value')
    data=visit(packet)
    return dict(encoding=CODEC,strings=table,data=data)

def decode(value):
    if set(value)!={'encoding','strings','data'} or value['encoding']!=CODEC:
        raise ValueError('encoding contract')
    table=value['strings']
    if not isinstance(table,list) or not all(type(x)is str for x in table) or len(set(table))!=len(table):
        raise ValueError('dictionary contract')
    def visit(v):
        if isinstance(v,str):
            if not re.fullmatch(r'\$(0|[1-9][0-9]*)',v):raise ValueError('invalid string reference')
            i=int(v[1:])
            if i>=len(table):raise ValueError('unbound string reference')
            return table[i]
        if isinstance(v,list):return [visit(x) for x in v]
        if isinstance(v,dict):return {k:visit(x) for k,x in v.items()}
        if v is None or type(v) in (bool,int,float):return v
        raise ValueError('unsupported encoded value')
    result=visit(value['data'])
    if encode(result)!=value:raise ValueError('noncanonical or unused dictionary entries')
    return result

def prepare(cohort,*,max_wire_bytes=262144,per_type=2):
    full={a:packet(cohort,a) for a in ARMS}
    byref={e['task_ref']:e for e in cohort['episodes']}
    pools={a:{} for a in ('S','F')}
    for a in pools:
        for row in full[a]['examples']:
            kind=byref[row['task_ref']]['task']['task_type']
            pools[a].setdefault(kind,[]).append(row)
    chosen={a:[] for a in ARMS};strata=[]
    for kind in sorted(set(pools['S'])|set(pools['F'])):
        counts={a:len(pools[a].get(kind,[])) for a in pools};n=min(per_type,*counts.values())
        strata.append(dict(task_type=kind,available=counts,per_arm_selected=n,
            status='QUOTA_MET' if n==per_type else 'SCARCE_EXPLORATORY_ONLY' if n else 'BLOCKED_NO_PAIRED_SOURCE'))
        for a in pools:
            ordered=sorted(pools[a].get(kind,[]),key=lambda x:fingerprint(['route-b-quota-v1',x['task_ref']]))
            chosen[a]+=ordered[:n]
    inputs={a:dict(full[a],examples=chosen[a]) for a in ARMS}
    wires={};checks={}
    for a in ARMS:
        # Also checks all original hashes via the old strict full-packet validator.
        w=wire(cohort,a);compressed=encode(inputs[a])
        assert decode(compressed)==inputs[a]
        w['messages'][0]['content']+='\n'+INSTRUCTION
        w['messages'][1]['content']=canonical(compressed)
        wires[a]=w;checks[a]=measure(w)
    return dict(version=VERSION,inputs=inputs,wires=wires,measurements=checks,strata=strata,
        selection={a:[x['task_ref'] for x in chosen[a]] for a in ARMS},
        limits=dict(max_wire_bytes=max_wire_bytes,nominal_per_type=per_type),
        byte_limit_passed=all(x['wire_bytes']<=max_wire_bytes for x in checks.values()),
        full_quota_coverage=all(s['status']=='QUOTA_MET' for s in strata),
        paid_authorization=False,status='EXPLORATORY_INPUT_ONLY_NOT_GENERALIZATION_READY')

def validate(prepared,cohort):
    expected=prepare(cohort,
        max_wire_bytes=prepared['limits']['max_wire_bytes'],per_type=prepared['limits']['nominal_per_type'])
    if canonical(prepared)!=canonical(expected):raise PermissionError('projection/source/selection drift')
    return prepared
