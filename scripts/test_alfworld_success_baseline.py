"""Zero-API checks for the success-learning integration and fail-closed boundaries."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import Mock

from alfworld_.env import AlfWorldStepResult
from alfworld_.executor import AlfWorldExecutor
from alfworld_.generator import AlfWorldStepOutput
from alfworld_.schemas import AlfWorldSkillTemplate, AlfWorldTask
from alfworld_.skill_library import SkillLibrary
from alfworld_.success_baseline import BaselineClient, draw_holdout, route, run_stream
from failure_evo.evidence import EvidenceStore
from failure_evo.run_health import RunUnhealthy
from run_alfworld_audited_baseline import budget
from run_alfworld_success_baseline import SETTINGS

SIMPLE = 'pick_and_place_simple'
DUAL = 'pick_two_obj_and_place'


def response(text='Act: look', finish='stop'):
    return dict(model='deepseek-flash', choices=[dict(message=dict(content=text), finish_reason=finish)],
                usage=dict(prompt_tokens=40, completion_tokens=10, total_tokens=50))


def fixture_config():
    rows = [dict(task_id='fixture', task_type=SIMPLE, game='fixture-game')]
    return dict(SETTINGS, run_id='fixture', online=1, data_root='/fixture', tasks=rows,
                max_calls=51, max_cost_microusd=1000000)


class FixtureEnv:
    outcome = AlfWorldStepResult('Timeout', 0, True, False, ['look'])

    def __init__(self, *_):
        self.path = None

    def initialize(self, *, frozen_game_files):
        self.path = frozen_game_files[0]

    def reset(self):
        return AlfWorldTask('', SIMPLE, 'put a book on desk.', game_file=self.path), 'Room', ['look']

    def step(self, action):
        return self.outcome

    def close(self):
        pass


class SuccessBaselineTests(TestCase):
    def test_done_without_won_does_not_compile(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp)
            cfg = fixture_config()
            calls = Mock(return_value=response())
            s = run_stream(path, cfg, budget(path,cfg,engineering=True), sender=calls, env_factory=FixtureEnv)
            self.assertEqual(calls.call_count, 1)
            self.assertEqual(s['results'][0]['status'], 'NO_PROGRESS')
            self.assertEqual(s['results'][0]['produced'], {})
            self.assertEqual(s['phases']['total']['successes'], 0)
            state = EvidenceStore(path/'episodes.jsonl').records()[0]['payload']['library']
            self.assertFalse(state['trace_stats'][SIMPLE][0]['success'])

    def test_native_direct_template_controls_an_action_without_model(self):
        task = AlfWorldTask('test', SIMPLE, 'put a book on desk.')
        library = SkillLibrary()
        library.add_template(AlfWorldSkillTemplate('t',SIMPLE,['go to desk 1'],[]))
        commands = ['go to desk 1']
        layers, bindings = route(library,task,'Room',commands,False)
        env = Mock()
        env.step.return_value = AlfWorldStepResult('Goal reached',1,True,True,[])
        generator = Mock()
        trace = AlfWorldExecutor(env,generator).run(task,'Room',commands,
                                                   skill_library_result=layers,skill_bindings=bindings)
        env.step.assert_called_once_with('go to desk 1')
        generator.step.assert_not_called()
        self.assertTrue(trace.success)
        self.assertEqual(trace.direct_success_count,1)

    def test_full_online_stream_recovers_after_90_and_commits_120(self):
        import random
        from failure_evo.math_stream import read
        from alfworld_.run_20task_validation import HOLDOUT_RATE, HOLDOUT_RNG_SEED

        class OnlineEnv(FixtureEnv):
            def reset(self):
                self.seq = int(Path(self.path).name)
                goal = f'put two books on desk [goal-{self.seq:03d}].'
                return AlfWorldTask('', DUAL, goal, game_file=self.path), 'Room', ['take book 1 from desk 1']

            def step(self, action):
                assert action == 'take book 1 from desk 1'
                won = self.seq != 95
                return AlfWorldStepResult('Fixture end', int(won), True, won, [])

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = dict(fixture_config(), online=120, max_calls=6120, max_cost_microusd=85_000_000,
                       tasks=[dict(task_id=f'task-{i}', task_type=DUAL, game=str(i))
                              for i in range(1,121)])
            account = budget(root,cfg,engineering=True)
            requests = []

            def sender(wire):
                requests.append(wire)
                assert 'expert_plan' not in str(wire)
                if wire['max_tokens'] == 1024:
                    goal_line = wire['messages'][-1]['content'].splitlines()[0]
                    seq = int(goal_line.split('[goal-')[1][:3])
                    assert all(f'[goal-{i:03d}]' not in str(wire) for i in range(seq+1,121))
                    return response('Act: take book 1 from desk 1')
                assert wire['max_tokens'] == 500
                return response('1. Track distinct items before repeating a placement.')

            def stop(phase, seq):
                if phase == 'before_commit' and seq == 91:
                    raise InterruptedError('after the 91st compile')

            with self.assertRaises(InterruptedError):
                run_stream(root,cfg,account,sender=sender,env_factory=OnlineEnv,fault=stop)
            self.assertEqual(account.calls,182)
            before = read(root/'checkpoints/080.json')
            self.assertEqual(before['snapshot']['current_episode'],80)
            summary = run_stream(root,cfg,account,sender=sender,env_factory=OnlineEnv)
            rows = EvidenceStore(root/'episodes.jsonl').records()
            self.assertEqual([r['kind'] for r in rows],['EPISODE_COMMITTED']*120)
            self.assertEqual(account.calls,len(requests))
            self.assertEqual(account.calls,239)
            self.assertEqual(account.snapshot()['charged_or_reserved_tokens'],239*50)
            self.assertEqual(summary['phases']['online']['completed'],120)
            self.assertEqual(summary['phases']['evaluation']['completed'],0)
            self.assertEqual(summary['phases']['total']['successes'],119)
            rng = random.Random(HOLDOUT_RNG_SEED)
            holdouts = [False]+[rng.random()<HOLDOUT_RATE for _ in range(119)]
            self.assertEqual([r['holdout'] for r in summary['results']],holdouts)
            self.assertEqual(summary['results'][0]['retrieved'],[])
            self.assertIn('exemplar', summary['results'][1]['retrieved'])
            self.assertGreater(sum(r['use']['L2_requests'] for r in summary['results'][90:]),0)
            self.assertEqual(summary['windows'][-1]['skill_generation']['L2'],20)
            self.assertEqual(summary['results'][-1]['compile_calls'],1)
            self.assertEqual(len(list((root/'checkpoints').glob('*.json'))),6)
            final = read(root/'final_bank.json')
            self.assertEqual(final['seq'],120)
            self.assertEqual(final['snapshot']['current_episode'],120)
            self.assertEqual(final['library_sha256'],rows[-1]['payload']['library_sha256'])
            self.assertFalse(final['library']['trace_stats'][DUAL][94]['success'])
            self.assertEqual(final['rng'][1],list(rng.getstate()[1]))
            self.assertFalse((root/'frozen_bank.json').exists())
            (root/'final_bank.json').unlink()
            self.assertEqual(run_stream(root,cfg,account,sender=sender,env_factory=OnlineEnv),summary)
            self.assertEqual(read(root/'final_bank.json'),final)
            self.assertEqual(len(requests),239)

    def test_evaluation_does_not_draw_holdout_or_update_bank(self):
        from unittest.mock import patch
        with TemporaryDirectory() as tmp:
            path = Path(tmp)
            cfg = dict(fixture_config(), online=0)
            with patch('alfworld_.success_baseline.draw_holdout', side_effect=AssertionError('evaluation RNG draw')):
                summary = run_stream(path, cfg, budget(path,cfg,engineering=True),
                                     sender=Mock(return_value=response()), env_factory=FixtureEnv)
            frozen, episode = [r['payload'] for r in EvidenceStore(path/'episodes.jsonl').records()]
            self.assertFalse(frozen['evaluation_holdout'])
            self.assertFalse(episode['holdout'])
            self.assertEqual(frozen['rng'], episode['rng'])
            self.assertEqual(frozen['library_sha256'], episode['library_sha256'])
            self.assertEqual(summary['results'][0]['produced'], {})

    def test_direct_fallback_uses_latest_environment_observation(self):
        task = AlfWorldTask('test', SIMPLE, 'put a book on desk.')
        template = AlfWorldSkillTemplate('t', SIMPLE, ['go to desk 1'], [])
        lib = SkillLibrary()
        lib.add_template(template)
        layers, bindings = route(lib,task,'Room',['go to desk 1','look'],False)
        env = Mock()
        env.step.side_effect = [AlfWorldStepResult('At desk',0,False,False,['look']),
                                AlfWorldStepResult('Goal reached',1,True,True,[])]
        generator = Mock()
        generator.step.return_value = AlfWorldStepOutput(action='look')
        trace = AlfWorldExecutor(env,generator,max_steps=50).run(task,'Room',['go to desk 1','look'],
                                                                skill_library_result=layers,skill_bindings=bindings)
        self.assertTrue(trace.success)
        self.assertEqual(trace.planning_mode,'direct_then_dynamic')
        self.assertEqual(trace.direct_failure_count,1)
        self.assertEqual(generator.step.call_args.kwargs['observation'],'At desk')

    def test_native_governance_holdout_and_suppression(self):
        lib = SkillLibrary()
        trace = Mock(task_id='source', trace_id='source-trace', task_type=DUAL,
                     success=True, total_steps=1, actions=[Mock(action='take book 1 from desk 1')])
        for _ in range(3):
            lib.record_trace_stats(trace)
        self.assertIsNotNone(lib.retrieve(DUAL)['insight'])
        rng = Mock()
        rng.random.return_value = .1
        self.assertTrue(draw_holdout(lib,DUAL,rng))
        self.assertIsNone(route(lib,AlfWorldTask('task',DUAL,'goal'),'',['look'],True)[0]['insight'])
        for _ in range(5):
            lib.record_guided(DUAL,False)
        for _ in range(3):
            lib.record_unguided(DUAL,True)
        self.assertIsNone(lib.retrieve(DUAL)['insight'])
        self.assertIn(DUAL,lib.to_dict()['injection_suppressed'])
        tpl = AlfWorldSkillTemplate('unused', SIMPLE, ['look'], [])
        lib.add_template(tpl)
        for _ in range(3):
            lib.record_template_usage('unused',False)
        lib.periodic_audit()
        self.assertIsNone(lib.retrieve(SIMPLE)['template'])

    def test_unknown_and_incomplete_delivery_cannot_commit(self):
        for sender in (Mock(side_effect=OSError('simulated unknown')),
                       Mock(return_value=response(finish='length'))):
            with self.subTest(sender=sender), TemporaryDirectory() as tmp:
                p = Path(tmp)
                cfg = fixture_config()
                account = budget(p,cfg,engineering=True)
                for _ in range(2):
                    with self.assertRaises((RunUnhealthy,OSError)):
                        run_stream(p,cfg,account,sender=sender,env_factory=FixtureEnv)
                self.assertEqual(sender.call_count,1)
                self.assertEqual(EvidenceStore(p/'episodes.jsonl').records(),[])

    def test_budget_exhaustion_and_environment_exception_cannot_commit(self):
        class Broken(FixtureEnv):
            def step(self, action):
                raise OSError('environment fault')
        for config, env, expected_calls in ((dict(max_cost_microusd=1),FixtureEnv,0),({},Broken,1)):
            with TemporaryDirectory() as tmp:
                p = Path(tmp)
                cfg = dict(fixture_config(),**config)
                calls = Mock(return_value=response())
                with self.assertRaises(Exception):
                    run_stream(p,cfg,budget(p,cfg,engineering=True),sender=calls,env_factory=env)
                self.assertEqual(calls.call_count,expected_calls)
                self.assertEqual(EvidenceStore(p/'episodes.jsonl').records(),[])

    def test_recover_after_settlement_without_parsed_receipt(self):
        from runtime.config import GenerationSettings
        from failure_evo.workflow_protocol_v2 import Limits,prepare
        import time
        with TemporaryDirectory() as tmp:
            p = Path(tmp)
            cfg = fixture_config()
            account = budget(p,cfg,engineering=True)
            sender = Mock(side_effect=AssertionError('must not send'))
            client = BaselineClient(p/'action',account,cfg,sender=sender,request_prefix='action/')
            client.begin('fixture')
            key = 'action/fixture/0'
            wire = prepare([dict(role='system',content='system'),dict(role='user',content='user')],
                           limits=Limits(input_token_upper=10000,output_tokens=1024))
            account.reserve(wire.input_upper,wire.output_upper,request_id=key,request_hash=wire.sha256)
            client.events.append('ACTION_REQUEST',dict(request_id=key,wire=wire.body,wire_sha256=wire.sha256),time.time())
            client.events.append('RAW_RESPONSE',dict(request_id=key,response=response()),time.time())
            account.settle(key,50)
            ans = client.generate(instructions='system',input_text='user',
                                  settings=GenerationSettings(temperature=0,max_output_tokens=1024))
            self.assertEqual(ans.text,'Act: look')
            self.assertEqual(account.calls,1)
            sender.assert_not_called()


if __name__=='__main__':
    main()
