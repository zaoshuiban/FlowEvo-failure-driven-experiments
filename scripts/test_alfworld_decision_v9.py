"""B v9 tests use the frozen public cohort and injected model responses only."""

from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from alfworld_.binding_diagnostic import parse_rows as parse_v8_rows
from alfworld_.decision_diagnostic import PROMPTS, consistency, parse_rows, project, replay_v8
from failure_evo.math_stream import read, save, sha
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from run_alfworld_decision_v9 import (
    create_accounts, grant, load_v8, plan_for, prepare, reference, run, stage_request,
)
from test_alfworld_skill_acquisition import response

V8 = Path.home()/'.local/share/flowevo/alfworld_binding_v8_pilot_20261111_01'


def fixture_row(case, arm):
    ref = reference(case)
    facts = ref.pop('facts')
    public = project(case['public'])
    row = dict(id=public['id'], **ref, evidence_steps=[public['current_evidence_id']],
               uncertainty='Mock response for engineering acceptance.')
    if arm == 'S':
        row['facts'] = dict(facts, post_failure_evidence_steps=[])
    return row


def fixture_sender(cases, calls):
    lookup = {case['public']['id']: case for case in cases}

    def send(wire):
        arm = next(arm for arm, prompt in PROMPTS.items() if wire['messages'][0]['content'] == prompt)
        payload = json.loads(wire['messages'][1]['content'])
        public = payload['cases']
        assert payload == {'cases': [project(lookup[row['id']]['public']) for row in public]}
        calls.append((arm, [row['id'] for row in public], wire['max_tokens']))
        rows = [fixture_row(lookup[row['id']], arm) for row in public]
        for row in rows:
            if row['id'] == 'case_005' and arm == 'D':
                row['evidence_steps'] = row['evidence_steps'][0]
            if row['id'] in {'case_020', 'case_022', 'case_024'}:
                row['recovery_needed'] = 'YES'
        return response(dict(rows=rows))

    return send


class DecisionV9Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_plan, cls.cases, cls.original = load_v8(V8)

    def test_replay_and_original_score(self):
        paths = [V8/name for name in ('result.json', 'budget.jsonl', 'provider.jsonl', 'protocol.json')]
        before = {p: sha(p) for p in paths}
        audit = replay_v8(self.cases, self.original)
        for receipt in self.original['receipts']:
            start = receipt['batch'] * 6
            raw = json.loads(receipt['result']['raw_response']['choices'][0]['message']['content'])
            public = [case['public'] for case in self.cases[start:start+6]]
            replay = parse_v8_rows(raw, receipt['arm'], public)
            self.assertEqual(replay, json.loads(receipt['result']['specification']))
        failures = [row for row in audit if row['arm'] == 'B' and not row['original_accepted']]
        self.assertEqual(len(failures), 13)
        self.assertTrue(all(r['errors'] == [{'field': 'evidence_steps', 'code': 'EXPECTED_ARRAY'}] for r in failures))
        self.assertEqual(Counter(row['original_decision'] for row in failures), {'NO': 9, 'UNKNOWN': 4})
        self.assertEqual(sum(bool(row['errors']) for row in audit if row['arm'] == 'A'), 2)
        self.assertEqual({p: sha(p) for p in paths}, before)

    def test_evidence_and_row_isolation(self):
        a, b = self.cases[:2]
        valid = fixture_row(b, 'D')
        public = [project(case['public']) for case in (a, b)]
        for refs, error in [
            ('case_001:current', 'EXPECTED_ARRAY'),
            ('case_001:step_001,case_001:current', 'EXPECTED_ARRAY'),
            (['case_002:step_001'], 'CROSS_CASE_EVIDENCE'),
            (['case_001:step_999'], 'UNKNOWN_EVIDENCE'),
            (['step_001'], 'UNKNOWN_EVIDENCE'),
            (['case_001:current']*2, 'DUPLICATE_EVIDENCE'),
        ]:
            with self.subTest(refs=refs):
                broken = dict(fixture_row(a, 'D'), evidence_steps=refs)
                result = parse_rows(dict(rows=[broken, valid]), 'D', public)
                self.assertEqual(set(result['rows']), {valid['id']})
                self.assertEqual(result['rejected'][0]['errors'][0]['code'], error)

    def test_envelope_missing_fields_and_duplicate(self):
        case = self.cases[0]
        row = fixture_row(case, 'S')
        public = [project(case['public'])]
        self.assertEqual(parse_rows({}, 'S', public)['envelope'], 'INVALID_ENVELOPE')
        self.assertEqual(len(parse_rows(dict(rows=[row, row]), 'S', public)['rejected']), 2)
        del row['facts']['object_category_match']
        row['obstacle_present'] = 1
        checks = parse_rows(dict(rows=[row]), 'S', public)['rejected'][0]['errors']
        self.assertIn(dict(field='facts.object_category_match', code='MISSING_FIELD'), checks)
        self.assertIn(dict(field='obstacle_present', code='EXPECTED_STRING'), checks)

    def test_post_failure_timeline(self):
        case = self.cases[21]
        row = fixture_row(case, 'S')
        public = [project(case['public'])]
        row['facts']['post_failure_evidence_steps'] = ['case_022:step_002']
        self.assertTrue(parse_rows(dict(rows=[row]), 'S', public)['rows'])
        row['facts']['post_failure_evidence_steps'] = ['case_022:step_001']
        self.assertFalse(parse_rows(dict(rows=[row]), 'S', public)['rows'])

    def test_model_consistency_keeps_raw_decision(self):
        for i, code in [(19, 'YES_WITH_BINDING_CONFLICT'), (21, 'YES_WITH_RESOLVED_OBSTACLE'),
                        (23, 'YES_WITH_CHANGED_HELD_OBJECT'), (32, 'YES_WITH_UNCERTAIN_LOCAL_TARGET')]:
            with self.subTest(case=i):
                case = self.cases[i]
                row = dict(fixture_row(case, 'S'), recovery_needed='YES')
                result = parse_rows(dict(rows=[row]), 'S', [project(case['public'])])
                self.assertEqual(result['rows'][row['id']], row)
                check = result['consistency'][row['id']]
                self.assertEqual(check['status'], 'INCONSISTENT_OUTPUT')
                self.assertIn(code, {issue['code'] for issue in check['issues']})

    def test_category_instance_possession_and_uncertainty_are_distinct(self):
        facts = reference(self.cases[30])['facts']
        self.assertEqual(facts['object_category_match'], 'CONFLICT')
        self.assertEqual(facts['object_instance_match'], 'UNKNOWN')
        self.assertEqual(facts['held_object_matches_goal'], 'CONFLICT')
        self.assertEqual(facts['held_failed_object_match'], 'MATCH')
        self.assertEqual(facts['phase_match'], 'UNKNOWN')
        facts = reference(self.cases[32])['facts']
        self.assertEqual(facts['container_category_match'], 'MATCH')
        self.assertEqual(facts['container_instance_match'], 'UNKNOWN')
        self.assertEqual(facts['local_target_binding'], 'UNKNOWN')
        row = fixture_row(self.cases[32], 'S')
        row['facts']['binding_consistent'] = 'YES'
        self.assertIn('BINDING_WITH_UNCERTAINTY', {issue['code'] for issue in consistency(row)})

    def test_paid_authorization_and_history_directory_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []
            mock = root/'mock'
            run(V8, mock, sender=fixture_sender(self.cases, calls))
            plan = prepare(V8, root/'real', mock)
            self.assertFalse(read(root/'real'/'authorization.template.json')['paid_api_authorized'])
            with patch('run_alfworld_decision_v9.stage_request', side_effect=AssertionError('attempted provider call')):
                with self.assertRaises(PermissionError):
                    run(V8, root/'real', authorization=read(V8/'authorization.json'))
                with self.assertRaises(PermissionError):
                    run(V8, root/'real', authorization={**grant(plan), 'paid_api_authorized': False})
                save(root/'real'/'references.private.json', {})
                with self.assertRaisesRegex(PermissionError, 'reference copy drift'):
                    run(V8, root/'real', authorization=grant(plan))
            self.assertFalse((root/'real'/'provider.jsonl').exists())
            with self.assertRaises(PermissionError):
                plan_for(V8, V8/'nested', mock=True)

    def test_budget_exact_reservations_and_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan, _, _, _ = plan_for(V8, root, mock=True)
            budget = create_accounts(root, plan)
            with self.assertRaises(BudgetExhausted):
                budget.reserve(1, plan['max_tokens'])
            for batch in plan['schedule']:
                budget.reserve(batch['input_upper'], batch['output_upper'])
            snapshot = budget.snapshot()
            self.assertEqual(snapshot['remaining_tokens'], 0)
            self.assertEqual(snapshot['remaining_cost_microusd'], 0)
            with self.assertRaises(BudgetExhausted):
                budget.reserve(1, 1)

    def test_timeout_blocks_resume_without_resend(self):
        calls = []

        def sender(wire):
            calls.append(wire)
            raise TimeoutError('mock unknown send')

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(TimeoutError):
                run(V8, root, sender=sender)
            ledger = (root/'budget.jsonl').read_bytes()
            with self.assertRaises(RunUnhealthy):
                run(V8, root, sender=sender)
            self.assertEqual(len(calls), 1)
            self.assertEqual((root/'budget.jsonl').read_bytes(), ledger)

    def test_malformed_model_json_is_settled_and_other_batches_run(self):
        calls = []
        fixture = fixture_sender(self.cases, calls)

        def sender(wire):
            raw = fixture(wire)
            if len(calls) == 1:
                raw['choices'][0]['message']['content'] = '{"rows":'
            return raw

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = run(V8, root, sender=sender)
            self.assertEqual(len(calls), 12)
            self.assertEqual(result['delivery']['D']['requests']['invalid_json'], 1)
            self.assertEqual(result['delivery']['D']['requests']['missing_expected_rows'], 6)
            self.assertEqual(result['budget']['unknown_or_pending_requests'], [])
            self.assertEqual(run(V8, root, sender=sender), result)
            self.assertEqual(len(calls), 12)

    def test_pairing_mock_interruption_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []
            sender = fixture_sender(self.cases, calls)

            def interrupt_after_settlement(*args, **kwargs):
                if len(calls) == 1:
                    raise InterruptedError('Mock process stopped before the second batch')
                return stage_request(*args, **kwargs)

            with patch('run_alfworld_decision_v9.stage_request', side_effect=interrupt_after_settlement):
                with self.assertRaises(InterruptedError):
                    run(V8, root, sender=sender)
            result = run(V8, root, sender=sender)
            self.assertEqual(len(calls), 12)
            self.assertEqual([x[1:] for x in calls[:6]], [x[1:] for x in calls[6:]])
            self.assertEqual(len(result['model_predictions']['D']), 35)
            self.assertEqual(len(result['model_predictions']['S']), 36)
            self.assertEqual(result['delivery']['D']['rejected_rows_by_error'], {'EXPECTED_ARRAY': 1})
            metrics = result['reference_evaluation']
            self.assertEqual(metrics['arms']['D']['all']['false_trigger'], 3)
            self.assertEqual(metrics['arms']['S']['all']['false_trigger'], 3)
            self.assertEqual(metrics['paired']['both_delivered']['records'], 35)
            self.assertEqual(metrics['paired']['all']['S_only_delivered'], 1)
            self.assertEqual(metrics['arms']['S']['inconsistent_rows'], 3)
            ledger = (root/'budget.jsonl').read_bytes()
            self.assertEqual(run(V8, root, sender=sender), result)
            self.assertEqual(len(calls), 12)
            self.assertEqual((root/'budget.jsonl').read_bytes(), ledger)


if __name__ == '__main__':
    unittest.main()
