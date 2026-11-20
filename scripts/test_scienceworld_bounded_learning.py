"""Offline checks of experimental validity, never ScienceWorld learning data.

The simulator, model transport and Worker are mocked: this file starts no JVM,
container or network request.
"""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import run_scienceworld_bounded_learning as C
import scienceworld_study_support as S


def row(action, response, *, done=False, score=0, moves=1):
    return C.feedback(action, response, done,
                      dict(look='public room', inv='empty', score=score, moves=moves))


def case(prefix=0):
    return dict(variation=0, goal='synthetic harness fixture', templates=['look around'],
                initial=row('', 'initial public observation'),
                steps=[row('look around', 'prefix ' + str(i), moves=i + 2)
                       for i in range(prefix)])


class Credibility(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.object(S, 'post_deepseek', side_effect=AssertionError('network forbidden')).start()
        patch.object(C, 'new_env', side_effect=AssertionError('JVM forbidden')).start()

    def test_trigger_ignores_look_requires_connect_and_is_prefix_local(self):
        connect = row('connect a to b', 'attempt response')
        look = row('look around', 'unchanged room')
        electrical = row('activate a', 'unchanged electrical response')
        self.assertEqual(C.triggers([connect, look, look, look]), [])
        self.assertEqual(C.triggers([electrical] * 3), [])
        seq = [connect, electrical, look, electrical, electrical]
        self.assertEqual(C.triggers(seq), [5])
        for n in range(1, len(seq) + 1):
            self.assertEqual(C.triggers(seq[:n]), [x for x in C.triggers(seq) if x <= n])
        terminal = copy.deepcopy(seq)
        terminal[-1]['done'] = True
        self.assertEqual(C.triggers(terminal), [])
        changed_score = copy.deepcopy(seq)
        for step in changed_score:
            step['score'] = 99
            step['won'] = True
        self.assertEqual(C.triggers(changed_score), [5])

    def test_progress_anchor_requires_successful_live_connection(self):
        seq = [row('connect a to b', 'Cannot connect a to b.'),
               row('connect a to b', 'a is already connected to b.'),
               row('connect a to b', 'a is now connected to b.')]
        self.assertIsNone(C.normal_anchor(seq[:2]))
        self.assertEqual(C.normal_anchor(seq), 3)
        seq[-1]['done'] = True
        self.assertIsNone(C.normal_anchor(seq))

    def test_failed_skill_action_survives_fallback_and_consumes_original_budget(self):
        for fallback_status in ('declined', 'error'):
            with self.subTest(fallback_status=fallback_status), TemporaryDirectory() as tmp:
                actions, model_contexts, worker_contexts = [], [], []
                physical = {'broken': False}

                def step(action):
                    actions.append(action)
                    if action == 'disconnect a from b':
                        physical['broken'] = True
                    state = 'broken circuit' if physical['broken'] else 'original circuit'
                    return state, 0, False, dict(look=state, inv='empty', score=0,
                                                 moves=58 + len(actions))

                def model(ident, messages, **kwargs):
                    model_contexts.append(json.loads(messages[-1]['content']))
                    return dict(text='{"action":"look around","reason":"fixture"}', cache=False)

                def worker(code, context, path):
                    worker_contexts.append(copy.deepcopy(context))
                    if len(worker_contexts) == 1:
                        return dict(status='applied', action='disconnect a from b',
                                    state={'attempted': True}, reason='fixture bad action')
                    return dict(status=fallback_status, state={}, reason='fixture fallback')

                env = SimpleNamespace(step=step, close=lambda: None)
                io = SimpleNamespace(root=Path(tmp), model=model, worker=worker)
                original = case(C.LIMIT - 3)
                with patch.object(C, 'reset', return_value=env) as reset_mock:
                    result = C.branch(io, original, 'fallback', 'F', Path('unused-fixture.py'))
                reset_mock.assert_called_once_with(original)
                self.assertEqual(actions, ['disconnect a from b', 'look around', 'look around'])
                self.assertEqual([x['remaining_steps'] for x in worker_contexts], [3, 2])
                self.assertEqual([x['remaining_steps'] for x in model_contexts], [2, 1])
                self.assertIn('broken circuit', model_contexts[0]['observation'])
                self.assertEqual(model_contexts[0]['history'][-1]['action'], 'disconnect a from b')
                self.assertEqual(result['suffix_steps'], 3)
                self.assertEqual(result['logical_model_calls'], 2)
                self.assertEqual(result['worker_calls'], 2)
                self.assertEqual(result['policy_errors'], int(fallback_status == 'error'))
                self.assertFalse(result['won'])
                self.assertEqual(len(original['steps']), C.LIMIT - 3)

    def test_development_decline_never_buys_native_success(self):
        with TemporaryDirectory() as tmp:
            env = SimpleNamespace(step=lambda _: self.fail('decline cannot take an action'),
                                  close=lambda: None)
            io = SimpleNamespace(root=Path(tmp),
                model=lambda *a, **k: self.fail('development fallback model forbidden'),
                worker=lambda *a: dict(status='declined', state={}, reason='fixture'))
            with patch.object(C, 'reset', return_value=env):
                result = C.branch(io, case(10), 'development', 'F', Path('unused'), development=True)
            self.assertEqual(result['logical_model_calls'], 0)
            self.assertEqual(result['suffix_steps'], 0)
            self.assertFalse(result['won'])

    def test_candidate_metadata_is_inert_and_rejected_source_is_preserved(self):
        with TemporaryDirectory() as tmp:
            marker = Path(tmp) / 'must-not-exist'
            source = "def environment_operator(context):\n return {'status':'declined','state':{},'reason':'fixture'}\n"
            payload = dict(code=source, description='fixture', applicability='fixture',
                           type='json_object', permissions={'network': True},
                           postprocess="__import__('pathlib').Path(%r).touch()" % str(marker))
            parsed = S.parse_candidate(json.dumps(payload))
            self.assertTrue(parsed['passed'])
            self.assertEqual(parsed['code'], source)
            self.assertEqual(parsed['ignored_metadata'],
                             {k: payload[k] for k in ('type', 'permissions', 'postprocess')})
            self.assertNotIn('permissions', parsed)
            self.assertFalse(marker.exists())
            del payload['applicability']
            rejected = S.parse_candidate(json.dumps(payload))
            self.assertFalse(rejected['passed'])
            self.assertIn('MISSING_FIELD: applicability', rejected['errors'])
            self.assertEqual(rejected['code'], source)

    def test_native_and_skill_both_reject_reset_actions(self):
        for action in ('reset task', ' RESET task '):
            with self.subTest(action=action), TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):
                    C.parse_action(json.dumps({'action': action}))
                root = Path(tmp).resolve()
                code = root / 'fixture.py'
                code.write_text('# inert mocked Worker fixture\n')
                value = dict(status='applied', action=action, state={}, reason='fixture')

                class Backend:
                    def __call__(self, _): return self
                    def __enter__(self): return self
                    def __exit__(self, *args): return False
                    def call(self, _): return dict(status='OK', value=value)

                io = S.StudyIO.__new__(S.StudyIO)
                io.root = root
                io.p = dict(action_mode='free_text', network_policy={})
                io.backend = Backend()
                io.budget = SimpleNamespace(blocking_requests=lambda _: [],
                    tool=lambda **kwargs: 'fixture-request', settle=lambda *a, **k: None)
                outcome = io.worker(code, C.context(case(), []), root / 'receipt.json')
                self.assertEqual(outcome['status'], 'error')
                self.assertEqual(outcome['reason'], 'ACTION_CONTRACT_ERROR')


if __name__ == '__main__':
    unittest.main()
