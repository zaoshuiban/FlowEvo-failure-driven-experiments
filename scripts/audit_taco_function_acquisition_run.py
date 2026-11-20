"""Zero-model post-stop audit. Never changes frozen submissions or scoring.

The two contract checks below validate input syntax/shape only. They neither
solve tasks nor repair scoring inputs/expected values. Private cases remain in
their original private files; public reports contain flags and receipt links.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / 'FlowEvo/src'), str(REPO / 'scripts')]
from core.schemas import ExecutionTrace
from failure_evo.acquisition_selectors import revoked_evidence, select
from failure_evo.contracts import fingerprint
from failure_evo.pilot_runtime import write_json
from failure_evo.skill_runtime import sha
from run_failure_acquisition_pilot import budget
from run_taco_function_acquisition import load_config


def read(path):
    return json.loads(Path(path).read_text())


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rpn_contract(cases):
    invalid = []
    for i, case in enumerate(cases):
        tokens = case['args'][0]
        depth, lexical_errors = 0, 0
        underflow = False
        for token in tokens:
            if token in ('+', '-', '*', '/'):
                underflow |= depth < 2
                depth -= 1
            else:
                try:
                    int(token)
                except (ValueError, TypeError):
                    lexical_errors += 1
                depth += 1
        if lexical_errors or underflow or depth != 1:
            invalid.append(dict(case_index=i, numeric_token_errors=lexical_errors,
                                stack_underflow=underflow, final_stack_depth=depth))
    return invalid


def binary_contract(cases):
    return [dict(case_index=i, binary_alphabet_valid=False)
            for i, c in enumerate(cases)
            if not isinstance(c['args'][0], str) or not c['args'][0]
            or not set(c['args'][0]) <= {'0', '1'}]


def main():
    cfg, manifest = load_config()
    root = REPO / cfg['run_root']
    audit = root / 'poststop_audit'
    out = REPO / cfg['reports']
    stop = read(audit / 'Stop_Notice.json')
    assert stop['status'] == 'STOPPED_INVALID_TRAINING_SCORING'
    stopped = read(audit / 'Stopped_Run_Manifest.json')
    assert all(file_sha(root / p) == h for p, h in stopped.items())
    prep = root.parent / 'preparation'
    old = read(prep / 'closed_runs_immutable.json')
    assert all(file_sha(REPO / p) == h for p, h in old.items())
    rows = read(root / 'collect_progress.json')
    teacher = list((root / 'requests').glob('*/*/teacher/*/request.json'))
    assert not teacher
    assert not (root / 'requests/transfer').exists()
    assert not (root / 'acquisition').exists()

    # Verify the frozen projection preserves the official archived inputs and
    # expected returns. Do not normalize quotes or invent corrected expectations.
    sys.path.insert(0, str(prep / 'python_deps'))
    import pyarrow.parquet as pq
    original = pq.read_table(prep / 'taco_train_shard00.parquet').to_pylist()
    evidence = []
    for index, checker, reason in [
        (144, rpn_contract, 'Private case violates public integer-token and valid-RPN contracts.'),
        (1454, binary_contract, 'Private case contains characters outside the public binary-string alphabet.'),
    ]:
        item = next(x for x in rows if x['row']['row_index'] == index)
        row = item['row']
        trace = ExecutionTrace.model_validate(read(item['result']['trace_file']))
        original_io = json.loads(original[index]['input_output'])
        scoring = read(REPO / row['private_scoring_ref'])
        assert scoring['original_input_output_sha256'] == fingerprint(original_io)
        assert len(scoring['cases']) == len(original_io['inputs']) == len(original_io['outputs'])
        assert all(c['args'] == args and c['expected'] == expected for c, args, expected in
                   zip(scoring['cases'], original_io['inputs'], original_io['outputs']))
        invalid = checker(scoring['cases'])
        assert invalid and len(invalid) == len(scoring['cases']) == 1
        assert item['final_public_passed'] and item['independent_training_score']['verdict'] == 'FULL_CHECK_FAIL'
        receipt = REPO / item['independent_training_score']['receipt_ref']
        binding = next((root / 'locked_submissions/collect').glob(f"{row['problem_id'].replace('/', '_')}_*/source.py"))
        assert file_sha(binding) == item['independent_training_score']['source_sha256']
        record = dict(problem_id=row['problem_id'], source_lineage_id=row['source_lineage_id'],
                      duplicate_group_id=row['duplicate_group_id'], capability_family_id=row['capability_family_id'],
                      evidence_ref=str(receipt.relative_to(REPO)), evidence_sha256=sha(trace.model_dump_json()),
                      failure_status='raw_full_check_fail_invalid_input', data_role='train',
                      formal_training_eligible=False, success=False, execution_confirmed=True,
                      failure_type='invalid_scoring_input')
        evidence.append(dict(evidence_id='taco_function_real_01:' + row['problem_id'] + ':postlock_score',
                             original_evidence=record, original_source_ref=str(binding.relative_to(REPO)),
                             original_source_sha256=file_sha(binding), original_receipt_ref=str(receipt.relative_to(REPO)),
                             original_receipt_sha256=file_sha(receipt), private_feedback_ref=str(receipt.with_name('feedback.json').relative_to(REPO)),
                             private_scoring_sha256=row['private_scoring_sha256'],
                             public_verdict='PASS', raw_full_verdict='FULL_CHECK_FAIL',
                             status='REVOKED_INVALID_INPUT', audited_source_kind='engineering_error',
                             reason=reason, input_contract_checks=invalid, upstream_projection_unchanged=True,
                             reference_control_pass_did_not_establish_validity=True,
                             scope='this specific scoring evidence, not every implementation or future valid case of the task'))
    write_json(audit / 'Evidence_Exclusions.json', dict(records=evidence, new_model_requests=0, new_executions=0))
    ledger_path = REPO / 'reports/failure_acquisition_prepare_20261119/Evidence_Revocations.json'
    ledger = read(ledger_path)
    prior_records = list(ledger['records'])
    for rev in evidence:
        if not any(x['evidence_id'] == rev['evidence_id'] for x in ledger['records']):
            ledger['records'].append(rev)
    write_json(ledger_path, ledger)
    assert ledger['records'][:len(prior_records)] == prior_records
    for e in evidence:
        assert revoked_evidence(e['original_evidence'])
        for mode in ('G+F', 'G+U'):
            assert not select([dict(e['original_evidence'], formal_training_eligible=True)], mode, 3, 'audit')[0]
        fresh = dict(e['original_evidence'], evidence_sha256='fresh-valid-receipt', evidence_ref='fresh-valid-receipt')
        assert not revoked_evidence(fresh)

    receipts = [read(p) for p in (root / 'requests').rglob('receipt.json')]
    snap = budget(cfg, root).snapshot()
    submitted = list((root / 'requests').rglob('request.json'))
    assert len(submitted) == snap['calls'] == 62 and len(receipts) == 61
    events = [read(p) for p in root.glob('**/executions/**/result.json') if 'poststop_audit' not in p.parts]
    assert len(events) == snap['tool_calls'] == 105
    ids = {x['row']['problem_id'] for x in rows}
    uncompleted = [r['problem_id'] for r in manifest['tasks'] if r['data_role'] == 'train' and r['problem_id'] not in ids]
    cases = Counter(x['row']['private_case_count'] for x in rows)
    per_task = []
    for x in rows:
        raw = x['independent_training_score']
        per_task.append(dict(task_id=x['row']['problem_id'], final_source_sha256=raw['source_sha256'],
            public_verdict='PASS' if x['final_public_passed'] else 'FAIL', raw_full_verdict=raw['verdict'],
            raw_source_kind=x['source_kind'],
            audited_source_kind='engineering_error' if x['row']['row_index'] in (144,1454) else x['source_kind'],
            full_score_receipt_ref=raw['receipt_ref'], dependency_bundle_sha256=raw['dependency_bundle_sha256'],
            intermediate_public_failure=x['intermediate_public_failure'],
            new_native_skill_admitted=x['result'].get('compiled_skill_admitted'),
            trace_ref=x['result']['trace_file'], private_case_count=x['row']['private_case_count']))
    funnel=dict(training_completed=len(rows), training_public_pass=sum(x['final_public_passed'] for x in rows),
        raw_full_pass=sum(x['independent_training_score']['verdict']=='FULL_CHECK_PASS' for x in rows),
        raw_full_fail=2, revoked_invalid_failures=2, credible_unresolved=0, recovered_sources=0,
        selected_sources=0, teacher_requests=0, new_teacher_implementations=0,
        reused_recovery_implementations=0, executable_acquisition_candidates=0,
        independent_support_pass=0, acquired_operations_admitted=0,
        autonomous_development_tasks=0, development_actor_calls=0)
    value=dict(status=stop['status'], protocol_sha256=cfg['protocol_sha256'],
        research_question_answered=False, learning_stage_attempted=False, effect_evaluated=False,
        funnel=funnel, completed_training=per_task, uncompleted_training=uncompleted,
        paired_complete_task_results=None, net_additional_success=None,
        exclusions_ref=str((audit/'Evidence_Exclusions.json').relative_to(REPO)),
        budget=snap, requests_sent=len(submitted), complete_response_receipts=len(receipts),
        known_model_tokens=sum(r['usage']['total_tokens'] for r in receipts),
        known_peak_price_bound_usd=sum(r['price_bound_microusd'] for r in receipts)/1e6,
        known_plus_pending_price_bound_usd=snap['charged_or_reserved_cost_microusd']/1e6,
        unknown_delivery_policy='Keep full reservation; do not retry or claim no provider charge.',
        worker_seconds=sum(e['seconds'] for e in events), executions=len(events),
        preparation_cost=read(out/'Preparation_Cost.json'), poststop_audit_model_requests=0, poststop_audit_executions=0,
        raw_scoring_case_count_distribution=dict(cases),
        retained_eval_executions=0, development_executions=0, closed_prior_files_verified=len(old),
        stopped_run_files_verified=len(stopped),
        base_library_disposition='Quarantined in stopped run; two invalid scores suppressed normal success admission. No export to G/G_plus or future base.',
        source_traceability='Both invalid case payloads and expected values match frozen official shard records; no adapter data repair performed.',
        next_step='Before another paid run, validate input contracts and scorer quality for a fixed pool, then freeze a new protocol. Do not reuse this run budget or silently replace tasks.',
        mechanism_claim='No learned mechanism; no positive or negative evidence about teacher acquisition or Actor transfer effectiveness.')
    write_json(out/'Experiment_Result.json', value)
    write_json(out/'Next_Learning_Items.json', dict(items=[], reason='NO_CREDIBLE_ACQUISITION_SOURCE_IN_COMPLETED_TASKS',
        training_pool_complete=False, protocol_sha256=cfg['protocol_sha256'], invalid_evidence_exclusions=[e['evidence_id'] for e in evidence]))
    assert all(file_sha(root / p) == h for p, h in stopped.items())
    print(json.dumps(dict(funnel=funnel,budget=snap,known_cost=value['known_peak_price_bound_usd'],
                         reserved_cost=value['known_plus_pending_price_bound_usd']),ensure_ascii=False))


if __name__ == '__main__':
    main()
