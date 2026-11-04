"""Model proposals and host evidence are separate; no proposal grants permissions."""
import copy
import hashlib
from .contracts import fingerprint

FIELDS={'artifact_kind','input_schema','preconditions','output_schema','algorithm',
        'complexity_bound','failure_modes','source_evidence'}
PERMISSIONS={'validation_status','verified','gate_passed','execution_authorized'}
STAGES=('STATIC_SAFETY','SOURCE','INDEPENDENT_GATE','SHADOW_OBSERVATION')

def receive_contract(value):
    def inspect(x):
        if isinstance(x,dict):
            if PERMISSIONS & set(x):raise ValueError('host-only permission field')
            for v in x.values():inspect(v)
        elif isinstance(x,list):
            for v in x:inspect(v)
    inspect(value)
    if not isinstance(value,dict) or set(value)!=FIELDS:raise ValueError('exact operator contract fields required')
    if value['artifact_kind'] not in ('INSTANCE_SOLVER','REUSABLE_CANDIDATE'):raise ValueError('candidate kind')
    for key in ('input_schema','output_schema','complexity_bound'):
        if not isinstance(value[key],dict) or not value[key]:raise ValueError(key)
    for key in ('preconditions','failure_modes','source_evidence'):
        if not isinstance(value[key],list) or not value[key] or any(not isinstance(v,str) or not v.strip() for v in value[key]):raise ValueError(key)
    if not isinstance(value['algorithm'],str) or not value['algorithm'].strip():raise ValueError('algorithm')
    return copy.deepcopy(value)

def binding(artifact):
    contract=receive_contract(artifact['operator_contract'])
    digest=hashlib.sha256(artifact['code'].encode()).hexdigest()
    if digest!=artifact['code_sha256']:raise ValueError('source hash mismatch')
    return fingerprint(dict(code_sha256=digest,contract_sha256=fingerprint(contract)))

def record_stage(registry,artifact,*,stage,passed,data_hash,worker_hash,source_original_ids,independent=False):
    if stage not in STAGES or type(passed) is not bool:raise ValueError('stage result')
    if not data_hash or not worker_hash:raise ValueError('versioned data and Worker required')
    if stage=='INDEPENDENT_GATE':
        sources=artifact.get('source_original_ids',[])
        if (not independent or not source_original_ids or not sources or
            'UNKNOWN' in list(source_original_ids)+list(sources) or
            set(sources)&set(source_original_ids)):
            raise PermissionError('known disjoint original provenance required')
    payload=dict(binding=binding(artifact),stage=stage,passed=passed,data_hash=data_hash,
                 worker_hash=worker_hash,source_original_ids=list(source_original_ids),independent=independent)
    import time
    registry.events.append('OPERATOR_CONTRACT_REVIEW',payload,time.time())
    return payload

def require_release(registry,artifact):
    if 'operator_contract' not in artifact:return  # Explicit legacy protocol compatibility.
    if receive_contract(artifact['operator_contract'])['artifact_kind']!='REUSABLE_CANDIDATE':raise PermissionError('instance solver cannot receive reuse permission')
    key=binding(artifact)
    rows=[r['payload'] for r in registry.events.records() if r['kind']=='OPERATOR_CONTRACT_REVIEW' and r['payload']['binding']==key]
    for stage in STAGES:
        evidence=[r for r in rows if r['stage']==stage]
        if not evidence or evidence[-1]['passed'] is not True:raise PermissionError('missing successful '+stage)
