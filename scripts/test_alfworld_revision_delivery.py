"""Minimal offline acceptance checks; fixtures are not learning evidence."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from alfworld_revision_delivery import extract_candidate


ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT/'runs/alfworld_route_c_bounded_learning_20261118_01'


class DeliveryAcceptance(unittest.TestCase):
    def test_legacy_source_extraction_changes_no_bytes(self):
        for version in range(3):
            with self.subTest(version=version):
                response = json.loads((LEGACY/f'requests/learning/v{version}/response.json').read_text())
                raw = response['choices'][0]['message']['content']
                expected = json.loads(raw)['code'].encode('utf-8')
                candidate = extract_candidate(raw)
                self.assertTrue(candidate['passed'], candidate['errors'])
                self.assertEqual(candidate['raw_text'], raw)
                self.assertEqual(candidate['code'].encode('utf-8'), expected)
                self.assertEqual(candidate['code_sha256'], hashlib.sha256(expected).hexdigest())
                if version:
                    self.assertEqual(candidate['ignored_metadata']['type'], 'json_object')
        source = '\r\n# 中文\r\ndef environment_operator(context):\r\n    return {}  \r\n'
        self.assertEqual(extract_candidate(json.dumps({'code': source}))['code'].encode(), source.encode())

    def test_rejection_preserves_sources_without_selecting_an_answer(self):
        first = "def environment_operator(context):\n    return {'status':'declined'}\n"
        second = first + '# different complete submission\n'
        joined = json.dumps({'code': first}) + json.dumps({'code': second})
        rejected = extract_candidate(joined)
        self.assertFalse(rejected['passed'])
        self.assertIsNone(rejected['code'])
        self.assertEqual(rejected['raw_text'], joined)
        self.assertEqual(rejected['errors'][0]['code'], 'INVALID_JSON')
        self.assertEqual(rejected['errors'][0]['message'], 'Extra data')
        conflicting = '{"code":' + json.dumps(first) + ',"code":' + json.dumps(second) + '}'
        rejected = extract_candidate(conflicting)
        self.assertFalse(rejected['passed'])
        self.assertIsNone(rejected['code'])
        self.assertEqual(rejected['raw_text'], conflicting)
        self.assertEqual([field['value'] for field in rejected['source_fields']], [first, second])
        self.assertEqual(rejected['errors'][0]['code'], 'CONFLICTING_CODE_FIELDS')
        # A complete source stays available even when later static admission fails;
        # extraction deliberately does not rewrite Python into something executable.
        invalid_python = 'def environment_operator(context)\n    broken syntax\n'
        candidate = extract_candidate(json.dumps({'code': invalid_python, 'type': 'json_object'}))
        with self.assertRaises(SyntaxError):
            compile(candidate['code'], '<fixture>', 'exec')
        self.assertEqual(candidate['code'], invalid_python)
        self.assertEqual(candidate['raw_text'], json.dumps({'code': invalid_python, 'type': 'json_object'}))

    def test_feedback_versions_and_real_branch_budgets_stay_separate(self):
        import run_alfworld_revision_feedback as R

        def row(index):
            return dict(action='prefix '+str(index), observation='observation '+str(index),
                        commands=['look'], won=False, done=False, score=0)

        checkpoint = dict(goal='synthetic task', historical_sequence=41,
            initial=dict(observation='initial', commands=['look']), steps=[row(i) for i in range(48)],
            task=dict(game_sha256='fixture-game-hash'), skills=dict(exemplar=None, insight=None))
        with TemporaryDirectory() as tmp:
            root = Path(tmp)

            def store(name, value):
                path = root/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value))

            original = 'def environment_operator(context):\n    return {}\n'
            rejected = 'def environment_operator(context)\n    invalid syntax\n'
            for version, source, passed in (('legacy_v0', original, True), ('SUMMARY_r1', rejected, False)):
                store('candidates/'+version+'/submission.json', dict(code_sha256=hashlib.sha256(source.encode()).hexdigest(),
                    extraction=dict(code=source, errors=[]),
                    static=dict(passed=passed, errors=[] if passed else ['SYNTAX: missing colon'])))
            original_hash = hashlib.sha256(original.encode()).hexdigest()
            summary = dict(source_sequence=41, executed_version='legacy_v0', code_sha256=original_hash,
                           environment_won=False, used_actions=1, remaining_actions=1,
                           stop_reason='POLICY_DECLINED', exit_reason='fixture')
            trace = [dict(step=49, returned_action='look', executed=True, observation='actual response',
                legal_before=['look'], decision=dict(status='applied', action='look', state={'seen': True}, reason='fixture'),
                raw=dict(status='OK'), used_actions=1, remaining_actions=1, environment_won=False)]
            store('evaluations/legacy_v0/evaluation.json',
                  dict(code_sha256=original_hash, branches=[dict(summary=summary, trace=trace)]))
            store('learning_input.json', {'fixture': 'only common original learning material'})
            store('development.json', [checkpoint])
            for group in ('SUMMARY', 'TRACE'):
                payload = R.feedback_payload(root, group, 'SUMMARY_r1', 'SUMMARY_r1', 'legacy_v0')
                self.assertEqual(payload['source_to_revise']['code'], rejected)
                self.assertEqual(payload['source_to_revise']['version'], 'SUMMARY_r1')
                self.assertEqual(payload['latest_submission']['version'], 'SUMMARY_r1')
                self.assertFalse(payload['latest_submission']['static_diagnostics']['passed'])
                self.assertEqual(payload['behavior_feedback']['executed_version'], 'legacy_v0')
                self.assertEqual(payload['behavior_feedback']['code_sha256'], original_hash)
                self.assertEqual(payload['behavior_feedback']['branches'][0]['executed_version'], 'legacy_v0')
                self.assertEqual('step_traces' in payload['behavior_feedback'], group == 'TRACE')
            # No unique source in a newer delivery must retain the previous full
            # source under its real version, without borrowing its behavior label.
            store('candidates/SUMMARY_r2/submission.json', dict(code_sha256=None,
                extraction=dict(code=None, errors=[{'code': 'CONFLICTING_CODE_FIELDS'}]),
                static=dict(passed=False, errors=['delivery rejected'])))
            payload = R.feedback_payload(root, 'SUMMARY', 'SUMMARY_r2', 'SUMMARY_r1', 'legacy_v0')
            self.assertEqual(payload['latest_submission']['version'], 'SUMMARY_r2')
            self.assertEqual(payload['source_to_revise']['version'], 'SUMMARY_r1')
            self.assertEqual(payload['source_to_revise']['code'], rejected)
            self.assertEqual(payload['behavior_feedback']['executed_version'], 'legacy_v0')

            study = R.RevisionStudy.__new__(R.RevisionStudy)
            study.root = root
            states, environments = {}, []

            def reset(case):
                actions = []
                environments.append(actions)

                def step(action):
                    actions.append(action)
                    return SimpleNamespace(observation='actual '+str(len(actions)),
                        admissible_commands=['look'], won=False, done=False, score=0)

                return SimpleNamespace(step=step, close=lambda: None), 'checkpoint', ['look']

            def worker(code, context, path):
                branch = study.active_branch
                states.setdefault(branch, []).append(dict(context['state']))
                return dict(status='applied', action='look',
                            state={'owner': branch, 'count': len(states[branch])}, reason='fixture')

            study.reset = reset
            study.worker = worker
            study.model = lambda *args, **kwargs: self.fail('skill-only branch called a model')
            results = [study.skill_branch(checkpoint, group+'/branch', Path('unused-code.py'))
                       for group in ('SUMMARY', 'TRACE')]
            self.assertEqual(environments, [['look', 'look'], ['look', 'look']])
            self.assertEqual(states['SUMMARY/branch'][0], {})
            self.assertEqual(states['TRACE/branch'][0], {})
            self.assertEqual(states['SUMMARY/branch'][1]['owner'], 'SUMMARY/branch')
            self.assertEqual(states['TRACE/branch'][1]['owner'], 'TRACE/branch')
            self.assertEqual([x['remaining'] for x in results], [2, 2])
            self.assertEqual([x['suffix_steps'] for x in results], [2, 2])
            self.assertEqual([x['logical_model_calls'] for x in results], [0, 0])
            self.assertEqual(len(checkpoint['steps']), 48)


if __name__ == '__main__':
    unittest.main()
