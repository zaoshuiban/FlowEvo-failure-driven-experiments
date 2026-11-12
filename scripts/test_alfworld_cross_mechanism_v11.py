"""Zero-API v11 tests. Handwritten Mock proposals demonstrate interface coverage only."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from alfworld_.generic_recovery_skill import inspect, parse_skill, worker_source
from alfworld_.failure_learning import static_check
from alfworld_.skill_acquisition import replay_source
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, sha
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from run_alfworld_cross_mechanism_v11 import (
    GROUPS, V9, cohort, create_accounts, grant, plan_for, prepare, public_state, run,
)
from test_alfworld_skill_acquisition import response

BASE = Path.home()/'.local/share/flowevo'


def leaf(name):
    return {'condition':name}


def all_of(*names):
    return {'all':[leaf(name) for name in names]}


def fixture_skill(payload, kind):
    traces = payload['source_receipts']
    anchor = traces[0]['failure_step_id']

    def atom(key, op, **args):
        return dict(id=key,op=op,args=args,sources=[anchor])

    def rule(when, verb, *entities):
        return dict(when=when,action=dict(verb=verb,entities=list(entities)))

    roles = dict(task_object={'select':'goal_object'},task_target={'select':'goal_target'},
                 held={'select':'held_object'},subject={'select':'failed_subject'})
    if kind == GROUPS[0]:
        roles['target'] = {'select':'failed_target'}
        atoms = [
            atom('matched_object','category_equal',left='task_object',right='subject'),
            atom('matched_target','category_equal',left='task_target',right='target'),
            atom('holding','instance_equal',left='held',right='subject'),
            atom('closed','state_is',entity='target',state='closed'),
            atom('failed','event_is',verb='move',entities=['subject','target'],window='at_failure',outcome='noop'),
            atom('can_move','action_available',verb='move',entities=['subject','target']),
        ]
        entry = all_of('matched_object','matched_target','holding','closed','failed')
        rules = [rule(leaf('closed'),'open','target'),rule(leaf('can_move'),'move','subject','target')]
    else:
        roles.update(device={'select':'admissible_instance','verb':'use','category_from':'task_target'},
                     next_position={'select':'first_unvisited','verb':'go_to'})
        atoms = [
            atom('matched_tool','category_equal',left='task_target',right='subject'),
            atom('holding','category_equal',left='held',right='task_object'),
            atom('goal_stage','goal_requires',operation='examine'),
            atom('failed','event_is',verb='go_to',entities=['subject'],window='at_failure',outcome='noop'),
            atom('tool_here','bound',entity='device'),
            atom('can_explore','bound',entity='next_position'),
        ]
        entry = all_of('matched_tool','holding','goal_stage','failed')
        rules = [rule(leaf('tool_here'),'use','device'),rule(leaf('can_explore'),'go_to','next_position')]
    return dict(decision='PROPOSE',evidence_ids=[row['evidence_id'] for row in traces],
        failure_evidence=[row['failure_step_id'] for row in traces],roles=roles,conditions=atoms,
        entry=entry,stop=None,rules=rules,scope='Mock interface fixture',
        refusal='No action when its evidence is missing.')


def fixture_sender(calls, checkpoints):
    selected = {row['evidence_id']:row['group'] for row in checkpoints if row['sequence'] in (33,55)}

    def sender(wire):
        payload=json.loads(wire['messages'][1]['content'])
        calls.append(payload)
        if 'events' in payload:
            assert set(payload)=={'events'}
            rows=[]
            for event in payload['events']:
                assert set(event)=={'evidence_id','goal','initial_observation','steps','failure_step_id','anchor_admissible_commands'}
                anchor=event['failure_step_id']
                is_selected=event['evidence_id'] in selected
                later=next(step[0] for step in event['steps'] if step[0]>anchor)
                rows.append(dict(evidence_id=event['evidence_id'],decision='HYPOTHESIS' if is_selected else 'ABSTAIN',
                    failure_evidence_id=anchor,recovery_evidence_ids=[later] if is_selected else [],
                    cause='Mock cause',repair='Mock repair',uncertainty='Mock only'))
            return response(dict(analyses=rows))
        if 'analyses' in payload:
            assert set(payload)=={'analyses'} and len(payload['analyses'])==2
            rows=[]
            for row in payload['analyses']:
                rows.append(dict(evidence_ids=[row['evidence_id']],cause='Mock cause',
                    compatibility='Singleton test fixture',trigger='Mock trigger',required_state='Mock public state',
                    action_policy='Mock learned operation',decline='Mock refusal',
                    expected_change='Mock progress',scope='Mock mechanism'))
            return response(dict(mechanisms=rows,uncertainty='Mock only'))
        assert set(payload)=={'mechanism','source_receipts'}
        eid=payload['mechanism']['evidence_ids'][0]
        return response(fixture_skill(payload,selected[eid]))

    return sender


class GenericSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.events, cls.host, cls.views, cls.checkpoints, cls.boundaries=cohort(BASE)

    def sample(self, sequence):
        cp=next(row for row in self.checkpoints if row['sequence']==sequence)
        view=next(row for row in self.views if row['evidence_id']==cp['evidence_id'])
        skill=fixture_skill({'source_receipts':[view]},cp['group'])
        origin=self.host[cp['evidence_id']]
        prefix=origin['steps'][:cp['anchor']]
        public=public_state('fixture',view['goal'],prefix[-1],prefix,cp['anchor']-1)
        return skill,view,public

    def test_schema_and_anchor_timing(self):
        skill,view,public=self.sample(33)
        anchors={view['evidence_id']:view['failure_step_id']}
        refs={row[0] for row in view['steps']}
        self.assertEqual(parse_skill(skill,anchors,refs)['status'],'STRUCTURED_DELIVERED')
        self.assertTrue(static_check(worker_source(skill))['passed'])
        self.assertEqual(inspect(skill,public,starting=True)['entry'],'TRUE')
        self.assertEqual(inspect(skill,public,starting=True)['selection']['values'],['safe 1'])
        next(a for a in skill['conditions'] if a['id']=='failed')['args']['window']='before_failure'
        self.assertEqual(inspect(skill,public,starting=True)['entry'],'UNKNOWN')
        self.assertIsNone(inspect(skill,public,starting=True)['selection'])

    def test_unsupported_and_invalid_are_distinct(self):
        skill,view,_=self.sample(55)
        anchors={view['evidence_id']:view['failure_step_id']}
        refs={row[0] for row in view['steps']}
        skill['conditions'][0]['op']='unavailable_capability'
        self.assertEqual(parse_skill(skill,anchors,refs)['status'],'UNSUPPORTED_REPRESENTATION')
        skill['conditions'][0]['sources']=[view['evidence_id']]
        self.assertEqual(parse_skill(skill,anchors,refs)['status'],'INVALID_DELIVERY')
        self.assertEqual(parse_skill(dict(decision='ABSTAIN',reason='uncertain'),anchors,refs)['status'],'ABSTAIN')

    def test_dynamic_navigation_uses_public_history_and_commands(self):
        skill,view,public=self.sample(55)
        self.assertIsNotNone(inspect(skill,public,starting=True)['selection'])
        self.assertEqual(inspect(skill,public,starting=True)['selection']['index'],1)
        public['admissible_commands']=['look']
        self.assertIsNone(inspect(skill,public,starting=True)['selection'])
        public['admissible_commands']=['use desklamp 2','use desklamp 3']
        self.assertIsNone(inspect(skill,public,starting=True)['selection'])
        public['admissible_commands']=['use desklamp 2']
        self.assertEqual(inspect(skill,public,starting=True)['selection']['values'],['desklamp 2'])
        public['admissible_commands']=['use desklamp 2']
        public['history'].append(dict(step_id='step_004',evidence_id='fixture:step_004',
            action='take towel 1 from bed 1',observation='You pick up the towel 1 from the bed 1.'))
        self.assertEqual(inspect(skill,public,starting=True)['entry'],'FALSE')

    def test_full_source_receipt_replay(self):
        for cp in self.checkpoints:
            with self.subTest(sequence=cp['sequence']):
                replay_source(self.source['data_root'],self.host[cp['evidence_id']])

    def test_mock_worker_pipeline(self):
        with TemporaryDirectory(dir=BASE) as tmp:
            output=Path(tmp)
            calls=[]
            result=run(BASE,output,sender=fixture_sender(calls,self.checkpoints))
            self.assertEqual(len(calls),5)
            self.assertEqual(len(result['analyses']),16)
            self.assertEqual(result['paid_requests'],0)
            self.assertTrue(result['cross_mechanism_source_witness'])
            self.assertEqual(result['disposition'],'SHADOW_SOURCE_ONLY')
            self.assertEqual([len(row['boundary_validation']) for row in result['candidates']],[14,14])
            self.assertTrue(all(any(row['status']=='declined' for row in c['boundary_validation'])
                                for c in result['candidates']))
            self.assertEqual({row['group'] for c in result['candidates'] for row in c['source_validation']
                              if row['local_repair_verified']},set(GROUPS))
            ledger=sha(output/'budget.jsonl')
            self.assertEqual(run(BASE,output,sender=fixture_sender(calls,self.checkpoints)),result)
            self.assertEqual(len(calls),5)
            self.assertEqual(sha(output/'budget.jsonl'),ledger)
            budget=create_accounts(output,read(output/'protocol.json'))
            with self.assertRaises(BudgetExhausted):
                budget.reserve(1,1)
            self.assertTrue(all(row['kind']=='SHADOW_REGISTERED'
                                for row in EvidenceStore(output/'registry.jsonl').records()))
            real=output/'real'
            plan=prepare(BASE,real,output)
            self.assertFalse(read(real/'authorization.template.json')['paid_api_authorized'])
            with patch('run_alfworld_cross_mechanism_v11.stage_request',side_effect=AssertionError('unexpected send')):
                with self.assertRaises(PermissionError):
                    run(BASE,real,authorization=read(BASE/V9/'authorization.json'))
                with self.assertRaises(PermissionError):
                    run(BASE,real,authorization={**grant(plan),'paid_api_authorized':False})
            self.assertFalse((real/'provider.jsonl').exists())

    def test_unknown_stops_without_resend(self):
        with TemporaryDirectory() as tmp:
            output=Path(tmp)
            calls=[]
            def sender(wire):
                calls.append(wire)
                raise TimeoutError('Mock post-send interruption')
            with self.assertRaises(TimeoutError):
                run(BASE,output,sender=sender)
            ledger=sha(output/'budget.jsonl')
            with self.assertRaises(RunUnhealthy):
                run(BASE,output,sender=sender)
            self.assertEqual(len(calls),1)
            self.assertEqual(sha(output/'budget.jsonl'),ledger)


if __name__ == '__main__':
    unittest.main()
