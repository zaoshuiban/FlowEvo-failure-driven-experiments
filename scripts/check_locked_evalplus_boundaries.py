"""Zero-model checks of new evidence boundaries and stop-state persistence.

No task solutions or private tests are executed here. Fixtures test interfaces,
not research success. Closed experiment ledgers are never opened for mutation.
"""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / 'FlowEvo/src'), str(REPO / 'scripts')]
from failure_evo.acquisition_adapters import CodeAdapter
from failure_evo.acquisition_selectors import eligible_failure, select
from failure_evo.pilot_data import task_from_manifest
from failure_evo.pilot_runtime import write_json
from failure_evo.runtime import BudgetExhausted
from failure_evo.skill_runtime import sha
import run_taco_function_acquisition as taco
from evaluate_locked_humaneval_plus import check_prior, source_hashes, read, ROOT, OUT


def main():
    checks = {}
    manifest = read(REPO / 'reports/failure_acquisition_pilot_20261120/Pilot_Data_Manifest.json')
    row = next(x for x in manifest['tasks'] if x['problem_id'] == 'HumanEval/39')
    source = (ROOT / 'locked/HumanEval_39/solution.py').read_text()
    fixture = dict(problem_id=row['problem_id'], data_role='train',
        capability_family_id='number_theory', final_source_sha256=sha(source),
        dependency_bundle_sha256='fixture-only', scoring_suite_sha256='fixture-only',
        evidence_id='INTERFACE_FIXTURE_NOT_RESEARCH_EVIDENCE',
        private_feedback={'executed_code': 'PRIVATE_CANARY', 'input': 'PRIVATE_CANARY'},
        evidence_qualification=dict(evidence_valid=True, acquisition_eligible=True,
            compatibility='SCOPED_COMPATIBLE', input_contract_valid=True,
            expected_result_trusted=True, reproduced=True))
    adapter = CodeAdapter()
    payload = adapter.enhanced_training_projection(task_from_manifest(row), source, fixture)
    assert 'PRIVATE_CANARY' not in json.dumps(payload)
    assert set(payload) == {'task', 'actor_source', 'independent_training_feedback',
        'evidence_id', 'source_sha256', 'dependency_bundle_sha256', 'scoring_suite_sha256'}
    checks['private_projection_is_explicit_allowlist'] = True
    for dimension in ('evidence_valid', 'acquisition_eligible', 'input_contract_valid',
                      'expected_result_trusted', 'reproduced'):
        bad = copy.deepcopy(fixture)
        bad['evidence_qualification'][dimension] = False
        assert not eligible_failure(bad)
        for mode in ('G+F', 'G+U'):
            assert not select([bad], mode, 1, 'boundary-check')[0]
        try:
            adapter.enhanced_training_projection(task_from_manifest(row), source, bad)
        except ValueError:
            pass
        else:
            raise AssertionError('unqualified feedback leaked')
    try:
        adapter.enhanced_training_projection(task_from_manifest(row), source + '\n', fixture)
    except ValueError:
        checks['source_binding_and_all_qualification_dimensions_required'] = True
    else:
        raise AssertionError('source drift accepted')

    revoked = read(REPO / 'reports/failure_acquisition_prepare_20261119/Evidence_Revocations.json')
    for rev in revoked['records'][-2:]:
        assert rev['status'] == 'REVOKED_INVALID_INPUT'
        old = dict(rev['original_evidence'], evidence_id=rev['evidence_id'])
        for mode in ('G+F', 'G+U'):
            assert not select([old], mode, 1, 'boundary-check')[0]
        future = dict(problem_id=old['problem_id'], data_role='train', success=False,
            execution_confirmed=True, failure_type='wrong_answer',
            capability_family_id=old['capability_family_id'],
            evidence_ref='fixture/new-valid-receipt', evidence_sha256='new-receipt')
        for mode in ('G+F', 'G+U'):
            assert select([future], mode, 1, 'boundary-check')[0] == [future]
    checks['both_selectors_revoke_receipts_not_problem_ids'] = True

    old_root, old_stages = taco.ROOT, taco.STAGES
    try:
        with tempfile.TemporaryDirectory(prefix='stop_check_', dir=ROOT) as temp:
            for name, exception, expected in (
                ('complete', None, 'COMPLETED'),
                ('interrupt', KeyboardInterrupt(), 'INTERRUPTED'),
                ('error', ValueError('fixture'), 'EXCEPTION_STOP'),
                ('budget', BudgetExhausted('persistent run budget exhausted'), 'BUDGET_STOP')):
                taco.ROOT = Path(temp) / name
                taco.STAGES = ('collect',)
                write_json(taco.ROOT / 'collect_progress.json', [dict(row={'problem_id': 'fixture'}, final_public_passed=False)])
                write_json(taco.ROOT / 'jobs/pending.json', {'status': 'started'})
                state = {'unknown_or_pending_requests': ['fixture/pending'], 'reserved': 123}
                exp = object.__new__(taco.Experiment)
                exp.budget = SimpleNamespace(snapshot=lambda: copy.deepcopy(state))
                def phase():
                    if exception is not None:
                        raise exception
                    return {'fixture': True}
                exp.collect = phase
                exp.phase = lambda name: {'fixture': True}
                try:
                    exp.run()
                except BaseException as caught:
                    assert caught is exception
                snapshot = read(taco.ROOT / 'stop_snapshot.json')
                assert snapshot['status'] == expected and snapshot['budget'] == state
                assert snapshot['task_jobs']['pending'] == {'status': 'started'}
                assert snapshot['training_tasks'][0]['task_id'] == 'fixture'
                checks['stop_snapshot_' + name] = True
    finally:
        taco.ROOT, taco.STAGES = old_root, old_stages
    assert source_hashes() == read(ROOT / 'protocol.json')['source_hashes']
    checks['frozen_scorer_sources_unchanged'] = True
    prior_files = check_prior()
    result = dict(status='PASS', checks=checks, unchanged_prior_files=prior_files,
        new_model_requests=0, task_solution_executions=0,
        fixture_status='interface checks only; not acquisition evidence')
    write_json(OUT / 'Engineering_Boundary_Checks.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
