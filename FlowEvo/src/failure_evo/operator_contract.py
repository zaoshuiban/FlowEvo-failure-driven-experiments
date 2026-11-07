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
    import jsonschema
    for key in ('input_schema','output_schema'):
        # Same bounded JSON-Schema capabilities as the existing semantic contract.
        # In particular, arbitrary regex/pattern validators must not run in host Python.
        def bounded_schema(v,depth=0):
            if depth>12 or not isinstance(v,dict):raise ValueError('bounded schema object required')
            allowed={'type','properties','required','additionalProperties','items','enum','const','minimum','maximum','minItems','maxItems','minLength','maxLength','description','title','uniqueItems'}
            if set(v)-allowed:raise ValueError('unsupported schema capability')
            if isinstance(v.get('additionalProperties'),dict):raise ValueError('closed schema capability')
            properties=v.get('properties',{})
            if not isinstance(properties,dict):raise ValueError('schema properties object required')
            for child in properties.values():bounded_schema(child,depth+1)
            if 'items' in v:bounded_schema(v['items'],depth+1)
        bounded_schema(value[key])
        try:jsonschema.Draft202012Validator.check_schema(value[key])
        except jsonschema.SchemaError as exc:raise ValueError('invalid '+key+' schema') from exc
    for key in ('preconditions','failure_modes','source_evidence'):
        if not isinstance(value[key],list) or not value[key] or any(not isinstance(v,str) or not v.strip() for v in value[key]):raise ValueError(key)
    if not isinstance(value['algorithm'],str) or not value['algorithm'].strip():raise ValueError('algorithm')
    return copy.deepcopy(value)

def binding(artifact):
    contract=receive_contract(artifact['operator_contract'])
    if 'code' in artifact:
        digest=hashlib.sha256(artifact['code'].encode()).hexdigest()
    else:
        from pathlib import Path
        solver=hashlib.sha256(Path(artifact['solver_path']).read_bytes()).hexdigest()
        matcher=hashlib.sha256(Path(artifact['matcher_path']).read_bytes()).hexdigest()
        if solver!=artifact['solver_sha256'] or matcher!=artifact['matcher_sha256']:
            raise ValueError('split component hash mismatch')
        digest=fingerprint(dict(solver_sha256=solver,matcher_sha256=matcher,
                                contract_sha256=fingerprint(artifact['contract'])))
    if digest!=artifact['code_sha256']:raise ValueError('source hash mismatch')
    return fingerprint(dict(code_sha256=digest,contract_sha256=fingerprint(contract),
        generation_protocol=artifact.get('generation_protocol','LEGACY'),
        source_evidence_identity=artifact.get('source_evidence_ids',contract['source_evidence']),
        source_original_ids=artifact.get('source_original_ids',[])))


def candidate_identity(artifact):
    """Versioned contracts never inherit code-only historical cache entries."""
    if 'operator_contract' not in artifact:return artifact['code_sha256']
    identity=binding(artifact)
    if artifact.get('candidate_version',identity)!=identity:
        raise PermissionError('declared candidate version does not match full binding')
    return identity


def attach_contract(artifact, value, *, evidence_ids, protocol, original_ids):
    contract=receive_contract(value)
    if set(contract['source_evidence'])!=set(evidence_ids):
        raise ValueError('contract source evidence must equal frozen generation input')
    result=copy.deepcopy(artifact)
    result.update(operator_contract=contract,source_evidence_ids=list(evidence_ids),
                  generation_protocol=protocol,source_original_ids=list(original_ids))
    result['candidate_version']=binding(result)
    return result

def record_stage(registry,artifact,*,stage,passed,data_hash,worker_hash,source_original_ids,independent=False,receipt=None):
    if stage not in STAGES or type(passed) is not bool:raise ValueError('stage result')
    if not data_hash or not worker_hash:raise ValueError('versioned data and Worker required')
    if stage=='INDEPENDENT_GATE':
        sources=artifact.get('source_original_ids',[])
        if (not independent or not source_original_ids or not sources or
            'UNKNOWN' in list(source_original_ids)+list(sources) or
            set(sources)&set(source_original_ids)):
            raise PermissionError('known disjoint original provenance required')
    trusted=[r['payload'] for r in registry.events.records() if r['kind']=='OPERATOR_VALIDATOR_EXECUTED']
    if (not isinstance(receipt,dict) or receipt not in trusted or
        receipt.get('binding')!=binding(artifact) or receipt.get('stage')!=stage or
        receipt.get('passed') is not passed or receipt.get('data_hash')!=data_hash or
        receipt.get('worker_hash')!=worker_hash or
        receipt.get('source_original_ids')!=list(source_original_ids) or
        receipt.get('independent') is not independent):
        raise PermissionError('executed validator receipt required; boolean claims cannot authorize')
    payload=dict(validator_receipt_sha256=fingerprint(receipt),binding=binding(artifact),stage=stage,passed=passed,data_hash=data_hash,
                 worker_hash=worker_hash,source_original_ids=list(source_original_ids),independent=independent)
    import time
    if any(r['kind']=='OPERATOR_CONTRACT_REVIEW' and r['payload']==payload for r in registry.events.records()):return payload
    registry.events.append('OPERATOR_CONTRACT_REVIEW',payload,time.time())
    return payload

def require_release(registry,artifact):
    if 'operator_contract' not in artifact:return  # Explicit legacy protocol compatibility.
    if receive_contract(artifact['operator_contract'])['artifact_kind']!='REUSABLE_CANDIDATE':raise PermissionError('instance solver cannot receive reuse permission')
    originals=set(artifact.get('source_original_ids',[]))
    if len(originals)<2 or 'UNKNOWN' in originals:raise PermissionError('two known source originals required for reuse')
    require_stages(registry,artifact,STAGES)

def require_stages(registry,artifact,stages):
    key=binding(artifact)
    events=registry.events.records()
    completed={r['payload'].get('execution_id') for r in events if r['kind']=='OPERATOR_VALIDATOR_EXECUTED'}
    if any(r['kind']=='OPERATOR_VALIDATOR_STARTED' and r['payload'].get('binding')==key and r['payload'].get('stage') in stages and r['payload'].get('execution_id') not in completed for r in events):
        raise PermissionError('unresolved validator execution prevents permission')
    rows=[r['payload'] for r in events if r['kind']=='OPERATOR_CONTRACT_REVIEW' and r['payload']['binding']==key]
    for stage in stages:
        evidence=[r for r in rows if r['stage']==stage]
        if not evidence or evidence[-1]['passed'] is not True:raise PermissionError('missing successful '+stage)
        receipts=[r['payload'] for r in registry.events.records() if r['kind']=='OPERATOR_VALIDATOR_EXECUTED' and fingerprint(r['payload'])==evidence[-1].get('validator_receipt_sha256')]
        if not receipts:raise PermissionError('missing executed validator receipt')
        if artifact.get('origin')!='MOCK' and receipts[-1].get('engineering') is not False:
            raise PermissionError('engineering receipt cannot authorize real candidate')


def validate_computation_stage(registry, artifact, runner, cases, *, stage,
                               source_original_ids, independent=False, engineering=False):
    """Execute the existing split validator; private oracle stays in host evaluate()."""
    from .semantic_contract import SplitRunner
    from .operator_dual_validation import evaluate, development_passed
    import time
    if type(runner) is not SplitRunner:
        raise PermissionError('existing real SplitRunner required')
    if stage not in ('SOURCE','DEV','INDEPENDENT_GATE'):
        raise ValueError('computation validator stage')
    if artifact.get('origin')=='MOCK' and not engineering:
        raise PermissionError('Mock cannot certify real candidate')
    key=binding(artifact); data_hash=fingerprint(cases)
    execution_id=fingerprint([key,stage,data_hash,fingerprint(runner.backend.manifest()),list(source_original_ids),independent])
    prior=registry.events.records()
    if stage=='INDEPENDENT_GATE':
        sources=artifact.get('source_original_ids',[])
        if not independent or not sources or not source_original_ids or 'UNKNOWN' in sources+list(source_original_ids) or set(sources)&set(source_original_ids):raise PermissionError('independent original provenance required')
        gate_manifest=dict(binding=key,data_hash=data_hash,source_original_ids=list(source_original_ids))
        frozen=[r['payload'] for r in prior if r['kind']=='OPERATOR_VALIDATOR_GATE_FROZEN' and r['payload']['binding']==key]
        if frozen and frozen[0]!=gate_manifest:raise PermissionError('Gate manifest already consumed/frozen for candidate version')
        if not frozen:registry.events.append('OPERATOR_VALIDATOR_GATE_FROZEN',gate_manifest,time.time())
    finished=[r['payload'] for r in prior if r['kind']=='OPERATOR_VALIDATOR_EXECUTED' and r['payload'].get('execution_id')==execution_id]
    if finished:
        receipt=finished[-1]
    else:
        if any(r['kind']=='OPERATOR_VALIDATOR_STARTED' and r['payload'].get('execution_id')==execution_id for r in prior):
            raise PermissionError('interrupted validator requires audit; no replay')
        if stage=='INDEPENDENT_GATE':
            sources=artifact.get('source_original_ids',[])
            if not independent or not sources or not source_original_ids or 'UNKNOWN' in sources+list(source_original_ids) or set(sources)&set(source_original_ids):
                raise PermissionError('independent original provenance required before execution')
        registry.events.append('OPERATOR_VALIDATOR_STARTED',dict(execution_id=execution_id,binding=key,stage=stage,data_hash=data_hash),time.time())
        rows=evaluate(runner,artifact,cases)
        receipt=dict(execution_id=execution_id,binding=key,stage=stage,data_hash=data_hash,
            worker_hash=fingerprint(runner.backend.manifest()),validator_identity='operator_dual_validation.evaluate',
            validator_version='executed-computation-v1',result_manifest_sha256=fingerprint(rows),
            passed=development_passed(rows),engineering=engineering,rows=rows,
            source_original_ids=list(source_original_ids),independent=independent)
        registry.events.append('OPERATOR_VALIDATOR_EXECUTED',receipt,time.time())
    if stage=='DEV':
        return receipt
    result=record_stage(registry,artifact,stage=stage,passed=receipt['passed'],data_hash=data_hash,
        worker_hash=receipt['worker_hash'],source_original_ids=source_original_ids,independent=independent,receipt=receipt)
    return dict(result,rows=receipt['rows'])
