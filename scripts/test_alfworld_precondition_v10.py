"""Zero-API acceptance. The intentionally incomplete conditions below are mock fixtures."""

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import patch

from alfworld_.binding_diagnostic import public_case
from alfworld_.decision_diagnostic import project
from alfworld_.precondition_diagnostic import FALSE, TRUE, UNKNOWN, check, evaluate_development, parse_candidate
from failure_evo.math_stream import read, sha
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from run_alfworld_precondition_v10 import (
    SOURCE, V9, create_accounts, grant, prepare, protocol, run, source_payload,
)
from test_alfworld_skill_acquisition import response

BASE = Path.home()/'.local/share/flowevo'


def leaf(key):
    return {'condition': key}


def atom(key, op, args, source):
    return dict(id=key, op=op, args=args, sources=[source], claim='Mock fact',
                supports='Explicit public evidence', contradicts='Explicit incompatible evidence')


def fixture(source):
    return dict(
        decision='PROPOSE',
        roles={'task': 'goal_object', 'item': 'failed_subject', 'destination': 'failed_target'},
        conditions=[
            atom('category', 'same_category', {'left': 'task', 'right': 'item'}, source),
            atom('state', 'state_is', {'entity': 'destination', 'state': 'closed'}, source),
        ],
        require={'all': [leaf('category'), leaf('state')]}, abstain=None,
        recovery='Mock only.', refusal='Decline failed checks.', uncertainty='Missing evidence stays unknown.',
        scope='Incomplete engineering fixture.',
    )


def snapshot(*, goal='put some cup in cabinet.', observation='The cabinet 4 is closed.', history=None):
    steps = history if history is not None else [{'action':'move cup 2 to cabinet 4','observation':'Nothing happens.'}]
    anchor = next(i for i, row in enumerate(steps) if row['action']=='move cup 2 to cabinet 4')
    return project(public_case('sample', goal, observation, ['look', 'open cabinet 4'], steps, anchor))


class ConditionUnitTest(unittest.TestCase):
    def test_real_receipt_vs_absence_and_conflict(self):
        candidate = fixture('origin:step_001')
        self.assertEqual(check(candidate, snapshot())['truth'], TRUE)
        self.assertEqual(check(candidate, snapshot(observation='The cabinet 4 is open.'))['truth'], FALSE)
        self.assertEqual(check(candidate, snapshot(observation='Nothing happens.'))['truth'], UNKNOWN)
        conflict = check(candidate, snapshot(observation='The cabinet 4 is open. The cabinet 4 is closed.'))
        self.assertEqual(conflict['truth'], UNKNOWN)
        self.assertTrue(conflict['conflict'])
        self.assertEqual(check(candidate, snapshot(goal='put some book in cabinet.'))['truth'], FALSE)

    def test_category_and_explicit_identity(self):
        candidate = fixture('origin:step_001')
        candidate['conditions'][0]['op']='same_instance'
        self.assertEqual(check(candidate, snapshot())['truth'], UNKNOWN)
        self.assertEqual(check(candidate, snapshot(goal='put the cup 3 in cabinet.'))['truth'], FALSE)
        self.assertEqual(check(candidate, snapshot(goal='put the cup 2 in cabinet.'))['truth'], TRUE)

    def test_state_provenance_and_staleness(self):
        candidate = fixture('origin:step_001')
        history=[
            dict(action='go to cabinet 4', observation='You arrive at cabinet 4. The cabinet 4 is closed.'),
            dict(action='move cup 2 to cabinet 4', observation='Nothing happens.'),
        ]
        result = check(candidate, snapshot(observation='Nothing happens.',history=history))
        self.assertEqual(result['truth'],TRUE)
        self.assertIn('sample:step_001',result['conditions']['state']['evidence_ids'])
        later = history+[dict(action='look', observation='You see nothing of interest.')]
        self.assertEqual(check(candidate,snapshot(observation=later[-1]['observation'],history=later))['truth'],UNKNOWN)
        bad=snapshot(history=history)
        bad['history'][0]['evidence_id']='another:step_001'
        with self.assertRaises(PermissionError):
            check(candidate,bad)

    def test_holding_processing_and_after_anchor(self):
        source='origin:step_001'
        candidate=fixture(source)
        candidate['roles']['held']='held_object'
        candidate['conditions'] = [
            atom('holding','same_instance',dict(left='held',right='item'),source),
            atom('processing','goal_requires',dict(operation='clean'),source),
            atom('cleaned','observed_event',dict(verb='clean',entities=['item'],window='before_failure'),source),
            atom('opened','observed_event',dict(verb='open',entities=['destination'],window='after_failure'),source),
        ]
        candidate['require']={'all':[leaf('holding'),leaf('processing'),leaf('cleaned'),{'not':leaf('opened')}]}
        self.assertEqual(parse_candidate(candidate,{source})['status'],'CANDIDATE_DELIVERED')
        history=[
            dict(action='take cup 2 from table 1', observation='You pick up the cup 2 from the table 1.'),
            dict(action='clean cup 2 with sinkbasin 1', observation='You clean the cup 2 using the sinkbasin 1.'),
            dict(action='move cup 2 to cabinet 4', observation='Nothing happens.'),
            dict(action='open cabinet 4', observation='The cabinet 4 is open.'),
        ]
        result=check(candidate,snapshot(goal='put a clean cup in cabinet.',history=history))
        self.assertEqual([result['conditions'][key]['truth'] for key in ('holding','processing','cleaned','opened')],[TRUE]*4)
        self.assertEqual(result['conditions']['cleaned']['evidence_ids'],['sample:step_003','sample:step_002'])
        self.assertEqual(result['truth'],FALSE)
        self.assertEqual(check(candidate,snapshot(goal='put a clean cup in cabinet.',history=history[:-1]))['truth'],UNKNOWN)

    def test_unique_visible_binding_uses_command_scope_only(self):
        source='origin:step_001'
        candidate=fixture(source)
        candidate['conditions'][0] = atom('category','unique_command_binding',
            dict(verb='open',entity='destination',position='first'),source)
        self.assertEqual(parse_candidate(candidate,{source})['status'],'CANDIDATE_DELIVERED')
        current=snapshot()
        self.assertEqual(check(candidate,current)['truth'],TRUE)
        current['admissible_commands'].append('open cabinet 5')
        result=check(candidate,current)
        self.assertEqual(result['truth'],FALSE)
        self.assertIn('sample:admissible_commands',result['conditions']['category']['evidence_ids'])
        candidate['conditions'][0]['args']['position']='second'
        self.assertEqual(parse_candidate(candidate,{source})['status'],'INVALID_CONDITION')

    def test_format_provenance_and_unsupported_are_distinct(self):
        source='origin:step_001'
        candidate=fixture(source)
        self.assertEqual(parse_candidate(candidate,{'another:step_001'})['status'],'INVALID_CONDITION')
        candidate['conditions'][0]['args']['left']='cup 2'
        self.assertEqual(parse_candidate(candidate,{source})['status'],'INVALID_CONDITION')
        candidate['conditions'][0].update(op='future_predicate',args={'entity':'item'})
        parsed=parse_candidate(candidate,{source})
        self.assertEqual(parsed['unsupported_conditions'],['category'])
        candidate['require']={'any':[leaf('category'),leaf('state')]}
        result=check(candidate,snapshot())
        self.assertEqual(result['required'],TRUE)
        self.assertEqual(result['status'],'UNSUPPORTED_CONDITION')
        self.assertFalse(result['recovery_allowed'])
        self.assertEqual(parse_candidate({'decision':'ABSTAIN','reason':'insufficient'},{source})['status'],'MODEL_ABSTAINED')

    def test_reject_all_never_looks_safe_and_refs_do_not_change_checks(self):
        candidate=fixture('origin:step_001')
        candidate['abstain']=leaf('state')
        public=[snapshot()]
        yes={'sample':dict(role='source',recovery_needed='YES')}
        no={'sample':dict(role='source',recovery_needed='NO')}
        a=evaluate_development(candidate,public,yes)
        b=evaluate_development(candidate,public,no)
        self.assertEqual(a['decisions'],b['decisions'])
        self.assertEqual(a['by_role']['all']['conflicts'],1)
        self.assertEqual(a['by_role']['all']['over_rejected'],1)
        self.assertEqual(a['by_role']['all']['false_trigger'],0)
        self.assertEqual(a['development_screen'],'INSUFFICIENT_DEVELOPMENT_EVIDENCE')
        with self.assertRaises(PermissionError):
            check(candidate,dict(public[0],recovery_needed='YES'))


class PreconditionPilotTest(unittest.TestCase):
    def test_mock_freeze_resume_budget_and_history(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            mock, real=root/'mock', root/'real'
            payload,ids,_=source_payload(BASE,mock)
            self.assertEqual(len(payload['source_receipts']),11)
            calls=[]

            def sender(wire):
                data=json.loads(wire['messages'][1]['content'])
                self.assertEqual(data,payload)
                self.assertEqual(set(data),{'mechanism','source_receipts'})
                self.assertEqual(set(data['source_receipts'][0]),{'evidence_id','goal','initial_observation',
                    'failure_step_id','steps','anchor_admissible_commands'})
                calls.append(wire)
                return response(fixture(sorted(ids)[0]))

            original={name:sha(BASE/V9/name) for name in ('budget.jsonl','provider.jsonl','protocol.json')}
            result=run(BASE,mock,sender=sender)
            self.assertEqual(result['proposal']['status'],'CANDIDATE_DELIVERED')
            self.assertEqual(result['disposition'],'SHADOW_DIAGNOSTIC_ONLY')
            totals=result['validation']['by_role']['all']
            self.assertGreater(totals['positive_covered'],0)
            self.assertGreater(totals['matrix']['NO'][FALSE],0)
            self.assertGreater(totals['matrix']['UNKNOWN'][UNKNOWN],0)
            self.assertEqual(totals['evaluable'],36)
            self.assertEqual(result['paid_requests'],0)
            ledger=sha(mock/'budget.jsonl')
            self.assertEqual(run(BASE,mock,sender=sender),result)
            self.assertEqual(len(calls),1)
            self.assertEqual(sha(mock/'budget.jsonl'),ledger)
            self.assertEqual({name:sha(BASE/V9/name) for name in original},original)
            plan=prepare(BASE,real,mock)
            self.assertFalse(read(real/'authorization.template.json')['paid_api_authorized'])
            with patch('run_alfworld_precondition_v10.stage_request',side_effect=AssertionError('unexpected send')):
                with self.assertRaises(PermissionError):
                    run(BASE,real,authorization=read(BASE/V9/'authorization.json'))
                with self.assertRaises(PermissionError):
                    run(BASE,real,authorization={**grant(plan),'paid_api_authorized':False})
            self.assertFalse((real/'provider.jsonl').exists())
            budget=create_accounts(mock,read(mock/'protocol.json'))
            with self.assertRaises(BudgetExhausted):
                budget.reserve(1,1)

    def test_transport_unknown_blocks_without_resend(self):
        calls=[]

        def sender(wire):
            calls.append(wire)
            raise TimeoutError('mock post-send unknown')

        with TemporaryDirectory() as temp:
            output=Path(temp)
            with self.assertRaises(TimeoutError):
                run(BASE,output,sender=sender)
            ledger=sha(output/'budget.jsonl')
            with self.assertRaises(RunUnhealthy):
                run(BASE,output,sender=sender)
            self.assertEqual(len(calls),1)
            self.assertEqual(sha(output/'budget.jsonl'),ledger)

    def test_historical_destination_refused(self):
        with self.assertRaises(PermissionError):
            protocol(BASE,BASE/SOURCE/'nested',True)


if __name__=='__main__':
    unittest.main()
