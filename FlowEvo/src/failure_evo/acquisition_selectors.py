"""Outcome-directed versus outcome-independent selection over one frozen pool."""
import hashlib
import json
from pathlib import Path

ENGINEERING = {'generation_error', 'DNS', 'NOT_SENT', 'SEND_UNKNOWN', 'evaluator_error'}

def revoked_evidence(record, ledger=None):
    """Revoke a specific historical receipt, never an entire problem identity."""
    path = Path(ledger) if ledger else Path(__file__).resolve().parents[3] / 'reports/failure_acquisition_prepare_20261119/Evidence_Revocations.json'
    if not path.exists():
        return False
    for rev in json.loads(path.read_text())['records']:
        old = rev['original_evidence']
        if record.get('evidence_id') == rev['evidence_id']:
            return True
        hashes = {old.get('evidence_sha256'), rev.get('original_receipt_sha256')} - {None, ''}
        if any(record.get(k) in hashes for k in ('evidence_sha256','source_evidence_sha256','receipt_sha256')):
            return True
        if record.get('evidence_ref') == old.get('evidence_ref'):
            return True
    return False

def eligible_failure(record):
    if record.get('capability_status') in {'EXISTING_CAPABILITY_REUSE_GAP', 'CAPABILITY_STATUS_UNKNOWN', 'NON_ALGORITHMIC_FAILURE'}:
        return False  # Retrieval/binding absence is not evidence for a new algorithm.
    if 'evidence_qualification' in record:
        q=record['evidence_qualification']
        return bool(not revoked_evidence(record) and record.get('data_role')=='train'
            and isinstance(q,dict) and q.get('evidence_valid') is True
            and q.get('acquisition_eligible') is True
            and q.get('compatibility') in {'COMPATIBLE','SCOPED_COMPATIBLE'}
            and q.get('input_contract_valid') is True and q.get('expected_result_trusted') is True
            and q.get('reproduced') is True
            and all(record.get(k) for k in ('final_source_sha256','dependency_bundle_sha256','scoring_suite_sha256','evidence_id')))
    return (not revoked_evidence(record) and record['data_role'] in {'train', 'development'} and record.get('success') is False
            and record.get('failure_type') not in ENGINEERING and record.get('execution_confirmed') is True)

def select(pool, mode, limit, seed):
    if mode not in {'G', 'G+F', 'G+U'}:
        raise ValueError('UNKNOWN_GROUP')
    ordered = sorted(pool, key=lambda r: hashlib.sha256((seed + r['problem_id']).encode()).hexdigest())
    allowed = [r for r in ordered if not revoked_evidence(r) and r['data_role'] == 'train' and r.get('formal_training_eligible',True)
               and ('evidence_qualification' not in r or eligible_failure(r))
               and (mode == 'G+U' or mode == 'G+F' and eligible_failure(r))]
    chosen = allowed[:limit] if mode != 'G' else []
    ids = {r['problem_id'] for r in chosen}
    return chosen, [dict(problem_id=r['problem_id'], selected=r['problem_id'] in ids,
                         reason='selected_by_' + mode if r['problem_id'] in ids else 'not_eligible_or_budget',
                         capability_family_id=r['capability_family_id']) for r in ordered]

def validate_roles(rows):
    for r in rows:
        if r.get('data_role') not in {'train','development','evaluation'} or not r.get('capability_family_id'):
            raise ValueError('MISSING_ROLE_OR_CAPABILITY')
        if r['data_role'] != 'development' and (r.get('formal_training_eligible') is False or any(str(r.get(k,'')).startswith('UNRESOLVED') for k in ['source_lineage_id','duplicate_group_id'])):
            raise ValueError('UNRESOLVED_FORMAL_LINEAGE')
        if r['data_role']=='evaluation' and r.get('exposure_status') not in {None,'unexposed'}:
            raise ValueError('EXPOSED_EVALUATION')
    # Mechanism families MAY cross roles; concrete identity / lineage may not.
    for key in ['problem_id', 'source_lineage_id', 'duplicate_group_id']:
        roles = {}
        for r in rows:
            if not r.get(key):raise ValueError('MISSING_IDENTITY:' + key)
            roles.setdefault(r[key], set()).add(r['data_role'])
        if any(len(v)>1 for v in roles.values()):raise ValueError('ROLE_LEAKAGE:' + key)
