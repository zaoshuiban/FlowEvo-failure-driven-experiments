"""Zero-API tests. All candidate rules in this file are engineering fixtures."""

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import patch

from alfworld_.recovery_skill_v12 import inspect, parse_skill
from failure_evo.math_stream import read, sha
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from run_alfworld_recovery_v12 import GROUPS, configuration, grant, prepare, previous, run
from test_alfworld_cross_mechanism_v11 import fixture_skill, response, leaf

BASE=Path.home()/'.local/share/flowevo'


def fixture(payload,group):
    if group==GROUPS[0]:
        result=fixture_skill(payload,group)
        aliases=['subject','target']
        verb='move'
    elif group==GROUPS[1]:
        result=fixture_skill(payload,group)
        aliases=['subject']
        verb='use'
    else:
        return navigation_fixture(payload)
    result['conditions'].append(dict(id='completed',op='event_recorded',
        args=dict(verb=verb,entities=aliases,window='after_failure',outcome='effect'),
        sources=[payload['source_receipts'][0]['failure_step_id']]))
    result['stop']=leaf('completed')
    return result


def navigation_fixture(payload):
    traces=payload['source_receipts']
    anchor=traces[0]['failure_step_id']

    def atom(key,op,**args):
        return dict(id=key,op=op,args=args,sources=[anchor])

    def all_of(*keys):
        return {'all':[leaf(key) for key in keys]}

    roles={
        'task_object':{'select':'goal_object'},'task_target':{'select':'goal_target'},
        'failed':{'select':'failed_subject'},'held':{'select':'held_object'},
        'pickup':{'select':'admissible_instance','verb':'take','category_from':'task_object'},
        'pickup_surface':{'select':'command_argument','verb':'take','match_from':'pickup',
                          'match_position':0,'select_position':1},
        'destination':{'select':'admissible_instance','verb':'go_to','category_from':'task_target'},
        'delivery':{'select':'command_argument','verb':'move','match_from':'held','filter_from':'task_target',
                    'match_position':0,'select_position':1},
        'next_position':{'select':'first_unvisited','verb':'go_to'},
    }
    conditions=[
        atom('anchor_failed','event_is',verb='go_to',entities=['failed'],window='at_failure',outcome='noop'),
        atom('placement','goal_requires',operation='place'),
        atom('correct_item','category_equal',left='held',right='task_object'),
        atom('can_move','action_available',verb='move',entities=['held','delivery']),
        atom('can_go','action_available',verb='go_to',entities=['destination']),
        atom('can_take','action_available',verb='take',entities=['pickup','pickup_surface']),
        atom('can_explore','bound',entity='next_position'),
    ]
    rules=[
        (all_of('correct_item','can_move'),'move',['held','delivery']),
        (all_of('correct_item','can_go'),'go_to',['destination']),
        (leaf('can_take'),'take',['pickup','pickup_surface']),
        (leaf('can_explore'),'go_to',['next_position']),
    ]
    return dict(decision='PROPOSE',evidence_ids=[row['evidence_id'] for row in traces],
        failure_evidence=[row['failure_step_id'] for row in traces],scope='Mock navigation only',
        refusal='Decline when no eligible public action exists.',roles=roles,conditions=conditions,
        entry=all_of('anchor_failed','placement'),stop=None,
        rules=[dict(when=when,action=dict(verb=verb,entities=entities)) for when,verb,entities in rules])


def sender_for(schedule,calls):
    groups={tuple(row['evidence_id'] for row in payload['source_receipts']):group
            for group,_,payload,_ in schedule}
    def sender(wire):
        payload=json.loads(wire['messages'][1]['content'])
        assert set(payload)=={'mechanism','source_receipts'}
        group=groups[tuple(row['evidence_id'] for row in payload['source_receipts'])]
        calls.append(group)
        return response(fixture(payload,group))
    return sender


class ReliabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,_,cls.host,cls.schedule,_,_=configuration(BASE,BASE/'v12_read_only_context',True)

    def sample(self,group):
        _,selected,payload,_=next(row for row in self.schedule if row[0]==group)
        cp=selected[0]
        origin=self.host[cp['evidence_id']]
        steps=origin['steps'][:cp['anchor']]
        public=previous.public_state('fixture',origin['projected']['goal'],steps[-1],steps,cp['anchor']-1)
        anchors={row['evidence_id']:row['failure_step_id'] for row in payload['source_receipts']}
        ids={step[0] for row in payload['source_receipts'] for step in row['steps']}
        return fixture(payload,group),public,anchors,ids

    def test_known_empty_prefix_is_not_unknown(self):
        skill,public,anchors,ids=self.sample(GROUPS[1])
        self.assertEqual(parse_skill(skill,anchors,ids)['status'],'STRUCTURED_DELIVERED')
        state=inspect(skill,public,starting=True)
        self.assertEqual(state['stop'],'FALSE')
        self.assertIsNotNone(state['selection'])
        skill['conditions'][-1]['op']='event_is'
        result=inspect(skill,public,starting=True)
        self.assertEqual(result['block'],'STOP_UNKNOWN')
        self.assertIsNone(result['selection'])
        skill['conditions'][-1]['op']='event_recorded'
        public['history'].append(dict(action='use desklamp 1',observation='Unrecognized feedback.',
                                      step_id='step_099',evidence_id='fixture:step_099'))
        self.assertEqual(inspect(skill,public,starting=False)['block'],'STOP_UNKNOWN')
        public['history'][-1]['observation']='You turn on the desklamp 1.'
        self.assertEqual(inspect(skill,public,starting=False)['block'],'STOP_TRUE')

    def test_contradictory_entry_and_stop_rejected(self):
        skill,_,anchors,ids=self.sample(GROUPS[0])
        skill['stop']={'any':[skill['entry'],leaf('completed')]}
        result=parse_skill(skill,anchors,ids)
        self.assertEqual(result['status'],'LOGIC_REJECTED')
        self.assertEqual(result['logic']['hard_conflicts'],['NO_ENTRY_RULE_WITH_STOP_FALSE'])

    def test_dead_continuation_rule_reported_without_disabling_other_rule(self):
        skill,_,anchors,ids=self.sample(GROUPS[0])
        skill['rules'][1]['when']=leaf('completed')
        # The replaced guard was the only use of can_move, so drop that unused atom.
        skill['conditions']=[row for row in skill['conditions'] if row['id']!='can_move']
        result=parse_skill(skill,anchors,ids)
        self.assertEqual(result['status'],'STRUCTURED_DELIVERED')
        self.assertEqual(result['logic']['unreachable_continuation_rules'],[1])

    def test_tool_binding_and_observed_support(self):
        skill,public,anchors,ids=self.sample(GROUPS[1])
        skill['roles']['support']={'select':'observed_support','entity_from':'subject'}
        self.assertEqual(parse_skill(skill,anchors,ids)['status'],'STRUCTURED_DELIVERED')
        self.assertIsNone(inspect(skill,public,starting=True)['bindings']['support']['entity'])
        public['observation']='You arrive at table 2. On the table 2, you see a book 4 and a desklamp 1.'
        public['admissible_commands']=['use desklamp 1']
        view=inspect(skill,public,starting=False)
        self.assertEqual(view['bindings']['task_object']['entity'],'book')
        self.assertEqual(view['bindings']['support']['entity'],'table 2')
        self.assertEqual(view['selection']['values'],['desklamp 1'])

    def test_binary_action_binding_independent_of_json_key_order(self):
        skill,public,anchors,ids=self.sample(GROUPS[2])
        skill=json.loads(json.dumps(skill,sort_keys=True))
        self.assertEqual(parse_skill(skill,anchors,ids)['status'],'STRUCTURED_DELIVERED')
        self.assertIsNone(inspect(skill,public,starting=True)['bindings']['pickup_surface']['entity'])
        public['admissible_commands']=['take spraybottle 1 from garbagecan 1','take book 1 from desk 1']
        self.assertEqual(inspect(skill,public,starting=True)['selection']['values'],['spraybottle 1','garbagecan 1'])
        public['admissible_commands'].append('take spraybottle 1 from desk 1')
        self.assertIsNone(inspect(skill,public,starting=True)['selection'])

    def test_mock_transport_unknown_stops_without_retry(self):
        calls=[]
        def sender(wire):
            calls.append(wire)
            raise TimeoutError('mock send status unknown')
        with TemporaryDirectory() as tmp:
            output=Path(tmp)
            with self.assertRaises(TimeoutError):
                run(BASE,output,sender=sender)
            ledger=sha(output/'budget.jsonl')
            with self.assertRaises(RunUnhealthy):
                run(BASE,output,sender=sender)
            self.assertEqual(len(calls),1)
            self.assertEqual(sha(output/'budget.jsonl'),ledger)

    def test_budget_and_authorization(self):
        with TemporaryDirectory() as tmp:
            output=Path(tmp)
            plan,*_=configuration(BASE,output,True)
            budget=previous.create_accounts(output,plan)
            for spec in plan['schedule']:
                budget.reserve(spec['input_upper'],spec['output_upper'])
            self.assertEqual(budget.snapshot()['remaining_cost_microusd'],0)
            with self.assertRaises(BudgetExhausted):
                budget.reserve(1,1)
            with patch('run_alfworld_recovery_v12.stage_request',side_effect=AssertionError('unexpected request')):
                with self.assertRaises(PermissionError):
                    run(BASE,output,authorization={**grant(plan),'paid_api_authorized':False})
            self.assertFalse((output/'provider.jsonl').exists())


if __name__=='__main__':
    unittest.main()
