"""Engineering fixtures only: these tests do not admit any research operator."""
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import unittest

import test_failure_evo_v2 as fixtures
from failure_evo import FailureOperator, FailureOperatorRegistry, FailureEvidenceStore
from failure_evo.generations import generation_decision


def competing_reservations(root):
    registry = FailureOperatorRegistry(Path(root) / 'registry.jsonl', FailureEvidenceStore(Path(root) / 'facts.jsonl'))
    card = FailureOperator.from_dict(registry.events.records()[0]['payload']['card'])
    return sum(bool(registry.reserve_opportunity(card, stream_id='s', experiment_id='pilot', task_index=1,
        task_id=f'{os.getpid()}-{i}', checkpoint='l2a', hook='before_native_retry', program_sha256='a'*64, at=3)) for i in range(5))


class GenerationTests(unittest.TestCase):
    setUp = fixtures.V2Acceptance.setUp
    tearDown = fixtures.V2Acceptance.tearDown
    fact = fixtures.V2Acceptance.fact
    card = fixtures.V2Acceptance.card
    gate = fixtures.V2Acceptance.gate
    solve = fixtures.V2Acceptance.solve
    runner = fixtures.V2Acceptance.runner

    def acceptance(self, card):
        raw = self.root / 'raw-acceptance.json'
        raw.write_text('{"engineering_fixture_only":true}')
        sha = hashlib.sha256(raw.read_bytes()).hexdigest()
        checks = {name: dict(passed=True, evidence_sha256=sha, artifact_sha256=card.artifact_sha256,
                  execution='isolated_actual_source') for name in
                  ('isolated_worker', 'static_contract', 'source_repair', 'boundary', 'inapplicable', 'host_fallback')}
        event = self.store.visible(2)[0]
        checks['source_repair'].update(event_id=event['event_id'], original_sha256=event['candidate_sha256'],
            host_public_outcome='passed', action='applied', tests_run=1, tests_passed=1)
        data = dict(role='NURSERY_ADMISSION', operator_id=card.operator_id, version=card.version,
            artifact_sha256=card.artifact_sha256, fingerprint=card.evidence_fingerprint.to_dict(),
            scope=card.evidence_scope, evidence_ids=list(card.evidence_ids), experiment_id='pilot',
            evaluated_at=2, files=[dict(path=str(raw), sha256=sha)], checks=checks)
        path = self.root / 'acceptance.json'; path.write_text(json.dumps(data))
        return path

    def admitted(self, limit=5):
        card = self.card(); self.registry.register(card, 1)
        path = self.acceptance(card)
        self.registry.admit_nursery(card, path, experiment_id='pilot', stream_id='s',
            after_task=0, effective_from=1, at=2, opportunity_limit=limit)
        return card

    def reserve(self, card, task='other', at=3):
        return self.registry.reserve_opportunity(card, stream_id='s', experiment_id='pilot', task_index=1,
            task_id=task, checkpoint='l2a', hook='before_native_retry',
            program_sha256=hashlib.sha256(task.encode()).hexdigest(), at=at)

    def complete(self, card, token, status='applied', at=3, **extra):
        self.registry.complete_opportunity(card, token, outcome=dict(status=status,
            public_check_outcome='passed', actual_cost=dict(tool_calls=2, elapsed_seconds=.1, model_calls=0), **extra), at=at)

    def test_source_only_admission_and_no_automatic_active(self):
        c = self.admitted(); state = self.registry.review(c)
        self.assertEqual((state['generation'], state['permission']), ('nursery', 'experimental'))
        self.assertEqual(state['opportunities_remaining'], 5)
        self.assertEqual(state['recommendation'], 'no_opportunities_not_ineffective')
        self.assertIsNone(state['savings_claim'])
        self.assertEqual(self.registry.snapshot(stream_id='s', task_index=1, at=3).cards, ())
        self.assertEqual(len(self.registry.snapshot(stream_id='s', task_index=1, experiment_id='pilot', at=3).cards), 1)

    def test_mock_static_or_failed_source_cannot_admit(self):
        for name, change in [('source_repair', {'execution':'mock'}), ('boundary', {'passed':False}),
                             ('source_repair', {'tests_run':0}), ('source_repair', {'original_sha256':'wrong'})]:
            with self.subTest(name=name, change=change):
                self.tearDown(); self.setUp()
                c = self.card(); self.registry.register(c, 1); p = self.acceptance(c)
                data = json.loads(p.read_text()); data['checks'][name].update(change); p.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    self.registry.admit_nursery(c, p, experiment_id='pilot', stream_id='s', after_task=0, effective_from=1, at=2)
                self.assertEqual(self.registry.state(c)['permission'], 'shadow')

    def test_task_barrier(self):
        c = self.card(); self.registry.register(c, 1)
        self.registry.admit_nursery(c, self.acceptance(c), experiment_id='pilot', stream_id='s', after_task=1, effective_from=2, at=2)
        self.assertFalse(self.reserve(c))
        self.assertEqual(self.registry.snapshot(stream_id='s', task_index=1, experiment_id='pilot', at=3).cards, ())

    def test_exact_five_with_last_attempt_still_valid(self):
        c = self.admitted()
        for i in range(5):
            token = self.reserve(c, str(i)); self.assertTrue(token)
            self.assertTrue(self.registry.valid(c, None))
            self.complete(c, token)
        self.assertFalse(self.reserve(c, 'six'))
        self.assertEqual(self.registry.snapshot(stream_id='s', task_index=1, experiment_id='pilot', at=3).cards, ())
        self.assertEqual(self.registry.review(c)['actual_applied'], 5)
        self.assertEqual(self.registry.state(c)['generation'], 'nursery')

    def test_multi_process_quota_and_hash_chain(self):
        c = self.admitted()
        with ProcessPoolExecutor(3, mp_context=multiprocessing.get_context('fork')) as pool:
            counts = list(pool.map(competing_reservations, [str(self.root)] * 3))
        self.assertEqual(sum(counts), 5)
        self.assertEqual(self.registry.state(c)['opportunities_used'], 5)
        self.assertEqual(len(self.registry.events.records()), 7)

    def test_crash_restart_duplicate_and_cold_do_not_refund(self):
        c = self.admitted(1); token = self.reserve(c)
        self.registry = FailureOperatorRegistry(self.root / 'registry.jsonl', self.store)
        self.assertFalse(self.reserve(c))
        self.registry.set_generation(c, 'cold', reason='wait for opportunities', at=3)
        self.assertFalse(self.registry.valid(c, None))
        self.registry.set_generation(c, 'nursery', reason='resume trial', at=3)
        self.assertFalse(self.reserve(c, 'different'))
        self.complete(c, token, status='declined')
        with self.assertRaises(ValueError): self.complete(c, token)
        self.assertEqual(self.registry.review(c)['actual_refusals'], 1)

    def test_no_reauthorization_quota_reset(self):
        c = self.admitted(); path = self.root / 'acceptance.json'
        with self.assertRaises(ValueError):
            self.registry.admit_nursery(c, path, experiment_id='pilot', stream_id='s', after_task=0, effective_from=1, at=3)
        with self.assertRaises(ValueError):
            self.registry.authorize_experiment(c, self.gate(c), experiment_id='pilot', stream_id='s', after_task=0, effective_from=1, at=3)

    def test_revoke_and_raw_evidence_changes_suspend(self):
        c = self.admitted(); (self.root / 'raw-acceptance.json').write_text('changed')
        self.assertFalse(self.registry.reconcile(c, 3))
        self.assertEqual(self.registry.state(c)['permission'], 'suspended')
        self.assertFalse(self.reserve(c))

    def test_source_evidence_revoke_suspends(self):
        c = self.admitted(); self.store.revoke(c.evidence_ids[0], 'invalid evidence', 3)
        self.assertFalse(self.registry.reconcile(c, 3))
        self.assertEqual(self.registry.state(c)['permission'], 'suspended')

    def test_cold_retirement_and_suspension_preserve_history(self):
        c = self.admitted(); self.registry.suspend(c, 'trusted negative transfer', 3)
        self.registry.set_generation(c, 'cold', reason='investigate', at=3)
        self.registry.set_generation(c, 'nursery', reason='cannot restore permission', at=3)
        self.assertFalse(self.registry.valid(c, None))
        self.registry.retire(c, reason='generic-equivalent with higher measured cost', at=3)
        with self.assertRaises(ValueError): self.registry.set_generation(c, 'nursery', reason='reset', at=3)

    def test_savings_are_not_inferred(self):
        c = self.admitted(); self.complete(c, self.reserve(c), paired_savings=100, money_saved=100)
        result = self.registry.events.records()[-1]['payload']['outcome']
        self.assertIsNone(result['paired_savings']); self.assertIsNone(result['monetary_cost'])
        self.assertNotIn('money_saved', result)

    def test_promotion_requires_actual_reuse_and_independent_gate(self):
        c = self.admitted()
        with self.assertRaises(ValueError):
            self.registry.authorize_experiment(c, self.gate(c), experiment_id='pilot', stream_id='s', after_task=1, effective_from=2, at=3, promote_mature=True)
        for task in ('0', '1'): self.complete(c, self.reserve(c, task))
        self.registry.authorize_experiment(c, self.gate(c), experiment_id='pilot', stream_id='s', after_task=1, effective_from=2, at=3, promote_mature=True)
        self.assertEqual(self.registry.state(c)['generation'], 'mature')
        self.assertEqual(self.registry.state(c)['permission'], 'experimental')
        self.assertFalse(self.reserve(c, 'too-early'))

    def test_mature_continues_logging_and_cold_resume(self):
        c = self.admitted()
        for task in ('0', '1'): self.complete(c, self.reserve(c, task))
        self.registry.authorize_experiment(c, self.gate(c), experiment_id='pilot', stream_id='s', after_task=1, effective_from=2, at=3, promote_mature=True)
        self.registry.set_generation(c, 'cold', reason='no current opportunity', at=3)
        self.assertFalse(self.registry.valid(c, None))
        self.registry.set_generation(c, 'mature', reason='resume known mature', at=3)
        for i in range(6):
            token = self.registry.reserve_opportunity(c, stream_id='s', experiment_id='pilot', task_index=2,
                task_id='mature-' + str(i), checkpoint='l2a', hook='before_native_retry', program_sha256=str(i), at=3)
            self.assertTrue(token); self.complete(c, token)
        self.assertEqual(self.registry.review(c)['actual_applied'], 8)
        (self.root / 'raw-acceptance.json').write_text('invalidated old proof')
        self.assertFalse(self.registry.reconcile(c, 3))

    def test_plugin_records_host_applied_and_quota(self):
        c = self.admitted(1)
        result, calls = self.solve(runner=self.runner({'status':'applied', 'candidate_code':'print(1)'}))
        self.assertEqual(self.registry.review(c)['actual_applied'], 1)
        self.assertEqual(self.registry.state(c)['opportunities_remaining'], 0)

    def test_plugin_refusal_and_unauthorized_decline(self):
        c = self.admitted()
        self.solve(runner=self.runner({'status':'declined', 'permission':'active'}))
        self.assertEqual(self.registry.state(c)['permission'], 'suspended')
        self.assertEqual(self.registry.state(c)['opportunities_used'], 1)

    def test_plugin_budget_skip_does_not_use_opportunity(self):
        c = self.admitted(); self.solve(runner=None)
        self.assertEqual(self.registry.state(c)['opportunities_used'], 0)

    def test_shadow_cannot_be_marked_mature_by_host_shortcut(self):
        c = self.admitted()
        with self.assertRaises(ValueError):
            self.registry.set_generation(c, 'mature', reason='one useful source', at=3)

    def test_failed_gate_does_not_grant_mature_or_refill_quota(self):
        c = self.admitted()
        for task in ('0', '1'): self.complete(c, self.reserve(c, task))
        p = self.gate(c); data = json.loads(p.read_text())
        data['paired_results'][0]['operator_correct'] = False; p.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.registry.authorize_experiment(c, p, experiment_id='pilot', stream_id='s', after_task=1, effective_from=2, at=3, promote_mature=True)
        self.assertEqual(self.registry.state(c)['generation'], 'nursery')
        self.assertEqual(self.registry.state(c)['opportunities_remaining'], 3)
        self.assertFalse(self.registry.valid(c, None))
        self.assertEqual(self.registry.state(c)['permission'], 'suspended')

    def test_synthetic_reuse_cannot_promote(self):
        c = self.admitted()
        for task in ('0', '1'): self.complete(c, self.reserve(c, task), synthetic=True)
        with self.assertRaises(ValueError):
            self.registry.authorize_experiment(c, self.gate(c), experiment_id='pilot', stream_id='s', after_task=1, effective_from=2, at=3, promote_mature=True)

    def test_registry_write_failure_returns_native_fallback(self):
        c = self.admitted()
        def fail(*args, **kwargs): raise OSError('fixture disk failure')
        self.registry.complete_opportunity = fail
        result, calls = self.solve(runner=self.runner({'status':'applied', 'candidate_code':'print(1)'}))
        self.assertGreater(len(calls), 1)
        self.assertGreater(self.registry.state(c)['opportunities_used'], 0)

    def test_generic_coverage_is_not_generation_veto(self):
        for generic in (True, False):
            self.assertEqual(generation_decision(reachable=True, trusted_failure=True, generic_covers=generic), 'READY_FOR_BOUNDED_GENERATION')
        self.assertEqual(generation_decision(reachable=False, trusted_failure=True, generic_covers=False), 'BLOCKED_NO_TRUSTED_INTERVENTION')


if __name__ == '__main__': unittest.main()
