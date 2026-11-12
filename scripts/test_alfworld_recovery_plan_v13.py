"""Zero-API v13 tests. Plans here are engineering fixtures, never learned skills."""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from alfworld_.recovery_plan import compile_plan, inspect_phase
from failure_evo.math_stream import read, sha
from failure_evo.run_health import RunUnhealthy
from run_alfworld_recovery_plan_v13 import PREVIOUS, authorization_for, configuration, prepare, run, validate_source
from test_alfworld_skill_acquisition import response


BASE = Path.home()/'.local/share/flowevo'


def fact(op, **args):
    return dict(op=op, args=args)


def step(verb, *args, requires=()):
    return dict(verb=verb, args=list(args), requires=list(requires))


def fixture(payload, group):
    plan = dict(decision='PROPOSE', obstacle='Mock obstacle', completion='Mock observable completion',
        failed_action='go_to', evidence=[row['failure_step_id'] for row in payload['source_receipts']],
        roles={}, facts={}, entry=[], stop_if=[], steps=[])
    if group == 'container_precondition':
        plan.update(failed_action='move', roles={key: {'select':key} for key in ('goal_object','goal_target','held_object')},
            facts=dict(object_matches=fact('category_equal', left='goal_object', right='failed_first'),
                       target_matches=fact('category_equal', left='goal_target', right='failed_second'),
                       holding=fact('instance_equal', left='held_object', right='failed_first'),
                       closed=fact('state_is', entity='failed_second', state='closed')),
            entry=['object_matches','target_matches','holding','closed'],
            steps=[step('open','failed_second',requires=['closed']), step('move','failed_first','failed_second')])
    elif group == 'lamp_interaction':
        roles = {key: {'select':key} for key in ('goal_object','goal_target','held_object')}
        roles['destination'] = {'select':'first_unvisited','verb':'go_to'}
        plan.update(roles=roles,
            facts=dict(tool_matches=fact('category_equal', left='goal_target', right='failed_first'),
                       holding=fact('category_equal', left='held_object', right='goal_object'),
                       tool_ready=fact('action_available',verb='use',entities=['failed_first']),
                       examining=fact('goal_requires', operation='examine')),
            entry=['tool_matches','holding','examining'],
            steps=[dict(step('go_to','destination'), repeat_until='tool_ready'), step('use','failed_first')])
    else:
        plan.update(roles=dict(destination={'select':'first_unvisited','verb':'go_to'}),
            facts=dict(placing=fact('goal_requires',operation='place')), entry=['placing'],
            steps=[step('go_to','destination')])
    return plan


def sources(payload):
    return ({row['evidence_id']:row['failure_step_id'] for row in payload['source_receipts']},
            {step[0] for row in payload['source_receipts'] for step in row['steps']})


class RecoveryPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, _, cls.host, cls.schedule, _, _ = configuration(BASE, BASE/'v13_test_context', True)

    def sample(self, index):
        group, selected, payload, _ = self.schedule[index]
        row = selected[0]
        origin = self.host[row['evidence_id']]
        prefix = origin['steps'][:row['anchor']]
        public = PREVIOUS.public_state('fixture', origin['projected']['goal'], prefix[-1], prefix, row['anchor']-1)
        return fixture(payload, group), public, sources(payload)

    def test_field_and_reference_diagnostics(self):
        plan, _, inputs = self.sample(0)
        cases = (
            ('unavailable role', {'steps':[step('open','undeclared')]}, '$.steps[0].args[0]', 'ROLE_REFERENCE'),
            ('wrong arity', {'steps':[step('move','failed_first')]}, '$.steps[0].args', 'ACTION_ARITY'),
            ('fake citation', {'evidence':['fabricated']}, '$.evidence[0]', 'UNKNOWN_REFERENCE'),
            ('unexpected field', {'verified':True}, '$', 'UNEXPECTED_FIELD'),
            ('missing dependency', {'roles':{'item':{'select':'admissible_instance','verb':'take','category_from':'absent'}}},
             '$.roles.item.category_from', 'ROLE_DEPENDENCY'),
        )
        for label, delta, field, code in cases:
            with self.subTest(label):
                result = compile_plan(dict(plan, **delta), *inputs)
                self.assertEqual((result['diagnostics'][0]['field'], result['diagnostics'][0]['code']), (field, code))
        self.assertEqual(compile_plan({'decision':'ABSTAIN','reason':'No evidence.'}, *inputs)['status'], 'ABSTAIN')
        self.assertEqual(compile_plan(plan, *inputs)['status'], 'COMPILED')  # More than six valid plan-level IDs.

    def test_temporal_and_logic_conflicts(self):
        plan, _, inputs = self.sample(0)
        plan['stop_if'] = ['closed']
        self.assertEqual(compile_plan(plan, *inputs)['diagnostics'][0]['code'], 'ENTRY_STOP_CONFLICT')
        plan['stop_if'] = ['can_deliver']
        plan['facts']['can_deliver'] = fact('action_available',verb='move',entities=['failed_first','failed_second'])
        self.assertEqual(compile_plan(plan, *inputs)['diagnostics'][0]['code'], 'PHASE_STOP_CONFLICT')
        plan['stop_if'] = ['closed_again']
        del plan['facts']['can_deliver']
        plan['facts']['closed_again'] = fact('event_is',verb='open',entities=['failed_second'],
                                            window='after_failure',outcome='effect')
        self.assertEqual(compile_plan(plan, *inputs)['diagnostics'][0]['code'], 'EMPTY_POST_FAILURE_PREFIX')

    def test_no_history_is_distinct_from_uncertain_stop_and_stale_anchor(self):
        plan, public, inputs = self.sample(0)
        plan['stop_if'] = ['delivered']
        plan['facts']['delivered'] = fact('event_recorded',verb='move',entities=['failed_first','failed_second'],
                                        window='after_failure',outcome='effect')
        skill = compile_plan(plan, *inputs)['candidate']['skill']
        self.assertEqual(inspect_phase(skill, public, 0)['stop'], 'FALSE')
        self.assertIsNotNone(inspect_phase(skill, public, 0)['selection'])
        next_step = dict(step_id='step_099', evidence_id='fixture:step_099', action=public['failed_action'],
                         observation='Unrecognized public receipt.')
        public['history'].append(next_step)
        self.assertEqual(inspect_phase(skill, public, 0)['block'], 'STALE_OR_MISSING_FAILURE')
        self.assertEqual(inspect_phase(skill, public, 1)['block'], 'STOP_UNKNOWN')

    def test_unary_argument_and_public_binary_binding(self):
        plan, public, inputs = self.sample(2)
        bad = dict(plan, steps=[step('go_to','failed_second')])
        self.assertEqual(compile_plan(bad, *inputs)['diagnostics'][0]['code'], 'ROLE_REFERENCE')
        good = compile_plan(plan, *inputs)['candidate']['skill']
        self.assertEqual(inspect_phase(good, public, 0)['bindings']['failed_first']['entity'],
                         public['failed_action'].removeprefix('go to '))
        plan['roles'].update(object_type={'select':'goal_object'},
            item={'select':'admissible_instance','verb':'take','category_from':'object_type'},
            location={'select':'command_argument','verb':'take','match_from':'item','match_position':0,'select_position':1})
        plan['steps'] = [step('go_to','destination'), step('take','item','location')]
        compiled = compile_plan(plan, *inputs)['candidate']['skill']
        public['goal'] = 'put some book in safe.'
        public['admissible_commands'] = ['take book 7 from desk 4', 'take pen 8 from drawer 3']
        self.assertEqual(inspect_phase(compiled, public, 1)['selection'], dict(index=1, values=['book 7','desk 4']))
        public['admissible_commands'].append('take book 7 from shelf 1')
        self.assertIsNone(inspect_phase(compiled, public, 1)['selection'])

    def test_noop_or_unclear_receipt_cannot_advance_phase(self):
        plan, _, inputs = self.sample(0)
        compiled = compile_plan(plan, *inputs)['candidate']
        origin = self.host[self.schedule[0][1][0]['evidence_id']]
        current = origin['steps'][origin['projected']['anchor']-1]
        command = 'open '+current['action'].split(' to ')[-1]
        selection = dict(selection=dict(index=0, values=[command.removeprefix('open ')]))
        card = Mock(version='mock-version')
        registry = Mock()
        registry.state.return_value = {'permission':'shadow'}
        runner = Mock()
        runner.backend.manifest.return_value = {}
        for observation, stop in [('Nothing happens.', 'NO_EFFECT'), ('Unrecognized receipt.', 'EFFECT_UNKNOWN')]:
            with self.subTest(stop), TemporaryDirectory() as tmp, patch.multiple('run_alfworld_recovery_plan_v13',
                    StrictTrainEnv=Mock(), verify_source_game=Mock(), _reset=Mock(), _replay=Mock(),
                    decide=Mock(return_value=(selection, {'status':'applied','action':command})),
                    _step=Mock(return_value=dict(current, observation=observation, commands=[]))):
                result = validate_source('', origin, compiled, card, runner, registry, Path(tmp)/'receipt.json', 8)
                self.assertEqual((result['stop'], len(result['actions']), result['confirmed_phases']), (stop,1,0))
                self.assertTrue(result['first_action_executed'])
                self.assertFalse(result['first_action_verified'] or result['plan_completed'])

    def test_real_environment_and_worker_with_one_mock_revision(self):
        plans = {tuple(row['failure_step_id'] for row in payload['source_receipts']):fixture(payload, group)
                 for group, _, payload, _ in self.schedule}
        calls = []

        def sender(wire):
            packet = json.loads(wire['messages'][1]['content'])
            calls.append(packet)
            if 'previous_plan' in packet:
                self.assertEqual(set(packet), {'previous_plan','diagnostics','allowed_step_ids'})
                self.assertEqual(packet['diagnostics'][0]['code'], 'ROLE_REFERENCE')
                self.assertFalse((output/'worker.jsonl').exists())
                return response(plans[tuple(json.loads(packet['previous_plan'])['evidence'])])
            self.assertEqual(set(packet), {'mechanism','source_receipts'})
            value = deepcopy(plans[tuple(row['failure_step_id'] for row in packet['source_receipts'])])
            if value['failed_action'] == 'move':
                value['steps'][0]['args'] = ['missing_role']
            return response(value)

        # The Colima Linux Worker can mount the experiment directory under HOME.
        with TemporaryDirectory(dir=BASE) as tmp:
            output = Path(tmp)/'mock_plan'
            result = run(BASE, output, sender=sender)
            self.assertEqual(result['paid_requests'], 0)
            self.assertEqual(result['independent_gate_games'], 0)
            self.assertEqual(len(calls), 4)
            self.assertEqual([row['status'] for row in result['candidates']], ['SHADOW']*3)
            container, lamp, navigation = [row['metrics'] for row in result['candidates']]
            self.assertEqual(container['plan_completed'], 11)
            self.assertEqual(lamp['first_action_verified'], 3)
            self.assertEqual(lamp['plan_completed'], 3)
            self.assertEqual(navigation['first_action_verified'], 9)
            self.assertEqual(navigation['won'], 0)
            self.assertEqual(navigation['local_repair_verified'], 0)
            self.assertEqual([row['result']['status'] for row in result['candidates'][0]['attempts']],
                             ['STATIC_REJECTED','COMPILED'])
            self.assertEqual(result['candidates'][0]['attempts'][1]['revision_changes']['changed_fields'], ['steps'])
            self.assertGreater(result['budget']['tool_calls'], 0)
            for row in result['candidates']:
                self.assertTrue(all(case['operator']['status']=='declined' for case in row['boundaries']
                                    if case['category']=='stale_failure'))
            ledger, worker = sha(output/'budget.jsonl'), sha(output/'worker.jsonl')
            self.assertEqual(run(BASE, output, sender=sender), result)
            self.assertEqual((len(calls),sha(output/'budget.jsonl'),sha(output/'worker.jsonl')), (4,ledger,worker))

    def test_abstention_and_revision_is_bounded(self):
        calls = []

        def sender(wire):
            calls.append(json.loads(wire['messages'][1]['content']))
            if len(calls) == 1:
                return response(dict(decision='ABSTAIN',reason='No evidence.'))
            return response(dict(decision='PROPOSE'))

        with TemporaryDirectory() as tmp:
            result = run(BASE, Path(tmp)/'mock_bounded', sender=sender)
            self.assertEqual(len(calls), 5)
            self.assertEqual([len(row['attempts']) for row in result['candidates']], [1,2,2])
            self.assertEqual(result['budget']['tool_calls'], 0)

    def test_truncation_does_not_trigger_static_revision(self):
        def sender(wire):
            self.assertNotIn('previous_plan', json.loads(wire['messages'][1]['content']))
            incomplete = response({'decision':'PROPOSE'})
            incomplete['choices'][0]['finish_reason'] = 'length'
            return incomplete

        with TemporaryDirectory() as tmp:
            result = run(BASE, Path(tmp)/'mock_truncated', sender=sender)
            self.assertEqual([row['status'] for row in result['candidates']], ['PROVIDER_DELIVERY_REJECTED']*3)
            self.assertEqual(result['budget']['calls'], 3)

    def test_unknown_and_real_authorization(self):
        calls = []

        def sender(wire):
            calls.append(wire)
            if len(calls) == 1:
                return response(dict(decision='PROPOSE'))
            raise TimeoutError('mock unknown revision send')

        with TemporaryDirectory() as tmp:
            output = Path(tmp)/'real_prepared'
            plan = prepare(BASE, output)
            self.assertEqual(plan['max_calls'], 6)
            self.assertFalse(read(output/'authorization.template.json')['paid_api_authorized'])
            with patch('run_alfworld_recovery_plan_v13.stage_request', side_effect=AssertionError('unexpected send')):
                with self.assertRaises(PermissionError):
                    run(BASE, output, authorization={**authorization_for(plan),'paid_api_authorized':False})
            self.assertFalse((output/'provider.jsonl').exists())
            output = Path(tmp)/'mock_unknown'
            with self.assertRaises(TimeoutError):
                run(BASE, output, sender=sender)
            ledger = sha(output/'budget.jsonl')
            with self.assertRaises(RunUnhealthy):
                run(BASE, output, sender=sender)
            self.assertEqual((len(calls), sha(output/'budget.jsonl')), (2, ledger))


if __name__ == '__main__':
    unittest.main()
