"""Zero API checks for diagnostic isolation and the learning metrics."""
import unittest

from analyze_math_reuse_outcomes import diagnostic_learning
from failure_evo.math_cumulative_stream import CumulativeStream, DEFAULTS
from run_math_cumulative import validate_experiment_mode


class DiagnosticTests(unittest.TestCase):
    def test_diagnostic_cannot_attach_release_provider(self):
        plan = dict(experiment_mode='LEARNING_DIAGNOSTIC', cumulative=DEFAULTS)
        with self.assertRaisesRegex(PermissionError, 'DIAGNOSTIC forbids'):
            CumulativeStream('unused', plan, [], [], {}, release_factory=lambda *_: None)

    def test_diagnostic_rejects_gate_and_strict_requires_gate(self):
        with self.assertRaisesRegex(PermissionError, 'DIAGNOSTIC forbids'):
            validate_experiment_mode(dict(experiment_mode='LEARNING_DIAGNOSTIC', gate_mode='AUTOMATED_GATE'))
        with self.assertRaisesRegex(PermissionError, 'requires automated independent Gate'):
            validate_experiment_mode(dict(experiment_mode='INDEPENDENT_GENERALIZATION'))

    def test_diagnostic_rates_use_distinct_denominators(self):
        records = {
            'cumulative/association_attempts.jsonl': [
                dict(kind='ASSOCIATION_ATTEMPT', payload=dict(evidence_ids=['a', 'b'], outcome='ACCEPTED_UNVERIFIED')),
            ],
            'cumulative/clusters.jsonl': [
                dict(kind='CLUSTER_VERSION', payload=dict(links={'a': {'relation': 'SUPPORTS'}})),
            ],
            'cumulative/queue.jsonl': [
                dict(kind='CUMULATIVE_JOB_STARTED', payload=dict(job_id='one')),
                dict(kind='CUMULATIVE_JOB_FINISHED', payload=dict(job_id='one', result={'status': 'DELIVERY_REJECTED'})),
            ],
        }

        class Snapshot:
            def events(self, arm, name):
                return records.get(name, [])

        report = diagnostic_learning(Snapshot(), 'F', {
            (1, 'a'): {'status': 'CONFIRMED_WRONG'},
            (2, 'b'): {'status': 'CONFIRMED_CORRECT'},
            (3, 'c'): {'status': 'TRUNCATED'},
        })
        self.assertEqual(report['confirmed_math_failures'], 1)
        self.assertEqual(report['confirmed_accuracy']['value'], .5)
        self.assertEqual(report['accepted_association_attempts']['value'], 1)
        self.assertEqual(report['associated_evidence_rate']['value'], .5)
        self.assertEqual(report['candidate_generation_rate']['value'], 0)
        self.assertEqual(report['candidate_rejection_reasons'], {'DELIVERY_REJECTED': 1})
