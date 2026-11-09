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
