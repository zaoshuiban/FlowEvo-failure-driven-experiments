"""Translate frozen pipeline evidence into the existing registry review contract.

Only trusted host checkers may provide assertions and paired results. Building a
review document never grants permission; authorize_experiment remains mandatory.
"""
import hashlib
from .contracts import fingerprint
from .data_roles import validate_data_roles


def build_admission_evidence(pipeline, card, *, public_job, data_manifest,
                             revise, experiment_id, metadata):
    manifest_hash = validate_data_roles(data_manifest)
    if metadata != public_job.get('environment'):
        raise ValueError('environment must be frozen in the original job')
    for name in ('baseline_version', 'model_version', 'scorer_version', 'resource_limits'):
        if not metadata.get(name):
            raise ValueError('missing frozen environment metadata: ' + name)
    rows = pipeline.events.records()
    def completed(key, request=None):
        matches = [(i, r) for i, r in enumerate(rows) if r['payload'].get('key') == key]
        if len(matches) != 2 or [r['kind'] for _, r in matches] != ['STEP_STARTED', 'STEP_DONE']:
            raise ValueError('step not completed exactly once: ' + key)
        if request is not None and matches[0][1]['payload']['request_hash'] != fingerprint(request):
            raise ValueError('frozen request mismatch')
        return matches[0][0], matches[1][0], matches[1][1]
    job_id = public_job['job_id']
    protocol = dict(public_job=public_job, revise=revise, data_manifest=data_manifest,
                    **{r: data_manifest[r] for r in ('design', 'gate', 'regression')})
    _, protocol_end, _ = completed(job_id + ':protocol', protocol)
    winner_start, winner_end, winner_row = completed(job_id + ':winner')
    winner = winner_row['payload']['result']
    completed(job_id + ':winner', winner)
    digest = hashlib.sha256(winner['code'].encode()).hexdigest()
    if not card.intact() or digest != card.artifact_sha256 or not protocol_end < winner_start:
        raise ValueError('winner artifact or ordering differs')
    if list(card.evidence_ids) != public_job['evidence_ids']:
        raise ValueError('discovery evidence differs')
    development = set(data_manifest['discovery']['source_groups']) | set(data_manifest['design']['source_groups'])
    if not development <= set(card.source_group_ids):
        raise ValueError('card must include all development provenance')
    outcomes = []
    for role in ('gate', 'regression'):
        data = data_manifest[role]
        start, end, row = completed('shard:' + data['shard_id'],
            dict(job_id=job_id, role=role, code=winner['code'], data=data))
        if start <= winner_end:
            raise ValueError('validation preceded winner freeze')
        outcomes.append(row)
    gate, regression = [r['payload']['result'] for r in outcomes]
    allowed_pairs = {(item['problem_id'], item['source_group']) for item in data_manifest['gate']['items']}
    if any((pair.get('problem_id'), pair.get('source_group')) not in allowed_pairs
           for pair in gate.get('paired_results', [])):
        raise ValueError('paired result outside frozen gate data')
    gate_passed = gate.get('eligible') is True
    regression_passed = regression.get('eligible') is True
    return dict(role='PILOT_ADMISSION', operator_id=card.operator_id, version=card.version,
        artifact_sha256=digest, fingerprint=card.evidence_fingerprint.to_dict(),
        scope=card.evidence_scope, evidence_ids=list(card.evidence_ids), experiment_id=experiment_id,
        design_selection_id=winner_row['record_hash'], shard_id=data_manifest['gate']['shard_id'],
        regression_shard=data_manifest['regression']['shard_id'], data_manifest_sha256=manifest_hash,
        pipeline_record_hash=rows[-1]['record_hash'], evaluated_at=max(r['at'] for r in outcomes),
        validation_source_groups=data_manifest['gate']['source_groups'],
        frozen_before_evaluation=True, independent_validation=True, generation_data_isolated=True,
        contract_checks_passed=gate_passed and gate.get('contract_checks_passed') is True,
        scope_checks_passed=gate_passed and gate.get('scope_checks_passed') is True,
        regression_passed=regression_passed, gate_passed=gate_passed,
        paired_results=gate.get('paired_results', []), benefit_route=gate.get('benefit_route'),
        cost_unit=gate.get('cost_unit'), reliability_result=gate.get('reliability_result'),
        cost_result=gate.get('cost_result'), authorization_decision='PENDING_REGISTRY_REVIEW',
        active_deployment_allowed=False,
        **{name: metadata[name] for name in ('baseline_version', 'model_version', 'scorer_version', 'resource_limits')})
