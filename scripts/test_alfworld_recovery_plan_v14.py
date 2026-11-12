"""Zero-API tests. All plans below are fixtures, separate from real model results."""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from alfworld_.recovery_plan import inspect_phase
from alfworld_.recovery_plan_v14 import compile_plan, first_decision, review_public_sources
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, sha
from failure_evo.run_health import RunUnhealthy
from run_alfworld_recovery_plan_v14 import (
    PARENT_RUN, authorization_for, configuration, prepare, public_cases, revision_audit, run, schedule_revision,
)
import run_alfworld_recovery_plan_v13 as v13
from test_alfworld_skill_acquisition import response


BASE = Path.home()/'.local/share/flowevo'


def fixture(packet, group):
    plan = dict(decision='PROPOSE',obstacle='Mock obstacle',completion='Mock observable completion',
                evidence=[trace['failure_ref'] for trace in packet['public_traces']],steps=[])
    if group=='container_precondition':
        plan.update(entry=['same_kind goal_object failed_first','same_kind goal_target failed_second',
                           'same_instance held_object failed_first','state failed_second closed'],
                    steps=[{'do':'open failed_second','when':['state failed_second closed']},
                           {'do':'move failed_first failed_second'}])
    elif group=='lamp_interaction':
        plan.update(roles={'destination':'unvisited'},entry=['same_kind goal_target failed_first',
                    'same_kind held_object goal_object','goal examine'],
                    steps=[{'do':'go to destination','until':'available use failed_first'},{'do':'use failed_first'}])
    else:
        plan.update(roles={'destination':'unvisited'},entry=['goal place'],steps=[{'do':'go to destination'}])
    return plan


def errors(receipt, stage):
    return {(row['path'],row['code']) for row in receipt[stage]['errors']}


class CompactPlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,_,_,cls.host,cls.schedule,_,_ = configuration(BASE,BASE/'v14_test_context',True)

    def sample(self, index):
        group,selected,packet,context = self.schedule[index]
        return fixture(packet,group), context, public_cases(selected,self.host)

    def test_full_schema_diagnostics_and_dependencies(self):
        plan,context,_ = self.sample(0)
        plan.update(evidence=['a trace ID','invalid step'],roles={'container':{'select':'goal_target'}},
                    steps=[{'do':'open container'},{'do':'move undeclared'},
                           {'do':'close failed_second','when':{'field':'wrong type'}}],gate_passed=True)
        result = compile_plan(plan,context)
        self.assertEqual(result['status'],'SCHEMA_REJECTED')
        self.assertEqual(result['semantics']['status'],'BLOCKED')
        self.assertIsNone(result['candidate'])
        self.assertTrue({('$.evidence[0]','EXPECTED_STEP_ID'),('$.evidence[1]','EXPECTED_STEP_ID'),
            ('$.roles.container','INVALID_SELECTOR_TYPE'),('$.steps[1].do','ACTION_ARITY'),
            ('$.steps[1].do','UNDECLARED_ROLE'),('$.steps[2].when','EXPECTED_ARRAY'),
            ('$.gate_passed','UNEXPECTED_FIELD')} <= errors(result,'schema'))
        self.assertIn(dict(path='$.steps[0].do',code='CHECK_BLOCKED',check='ROLE_BINDING',
                           depends_on=['$.roles.container']),result['schema']['blocked'])
        self.assertTrue(all(set(row)=={'path','code','expected','actual'} for row in result['schema']['errors']))
        evidence_issue = next(row for row in result['schema']['errors'] if row['path']=='$.evidence[0]')
        self.assertEqual(evidence_issue['actual'],'a trace ID')

    def test_semantic_errors_aggregated_after_schema_pass(self):
        plan,context,_ = self.sample(0)
        plan['roles'] = {'explore':'unvisited','surface':'support_of explore','target':'failed_second'}
        plan['entry'] += ['state target open','recorded after_failure effect open target']
        plan['stop_if'] = ['state target closed','available move failed_first target',
                           'last after_failure effect open target']
        result = compile_plan(plan,context)
        self.assertEqual(result['schema']['status'],'PASSED')
        self.assertEqual(result['status'],'SEMANTIC_REJECTED')
        self.assertTrue({('$.roles.surface','ROLE_DEPENDENCY_KIND'),('$.entry[4]','CONTRADICTORY_CURRENT_STATE'),
            ('$.entry[5]','UNREACHABLE_POST_FAILURE_RECEIPT'),('$.stop_if[2]','STOP_RECEIPT_MISSING_AT_ENTRY'),
            ('$.steps[0]','PHASE_STOP_CONFLICT'),('$.steps[1]','PHASE_STOP_CONFLICT')} <= errors(result,'semantics'))

    def test_invalid_parent_type_blocks_only_dependent_checks(self):
        plan,context,_ = self.sample(0)
        before = compile_plan(dict(plan,roles=[]),context)
        after = compile_plan(dict(plan,roles={'target':'invalid selector'}),context)
        for result in (before,after):
            result['source'] = dict(status='BLOCKED',errors=[],blocked=[])
        audit = revision_audit(before,after)
        self.assertEqual([row['code'] for row in audit['newly_checkable']],['UNKNOWN_SELECTOR'])
        self.assertEqual(audit['newly_reported'],[])

    def test_source_checks_category_without_inventing_an_instance(self):
        plan,context,cases = self.sample(0)
        plan.update(entry=['state goal_target closed'],steps=[{'do':'open goal_target'}])
        result = compile_plan(plan,context)
        self.assertEqual(result['status'],'COMPILED')
        review = review_public_sources(result['candidate'],cases)
        self.assertEqual((review['status'],review['selectable']),('NO_FIRST_ACTION',0))
        self.assertTrue(any(row['code']=='INSTANCE_UNRESOLVED' and row['actual']['binding']=='CATEGORY_ONLY'
                            for row in review['errors']))
        self.assertNotIn('safe 1',canonical(review))
        plan,context,cases = self.sample(0)
        compiled = compile_plan(plan,context)['candidate']
        phase,checks = first_decision(compiled,cases[0])
        self.assertEqual(phase,0)
        self.assertEqual(checks['selection']['values'],[cases[0]['failed_action'].split(' to ')[-1]])
        self.assertEqual(review_public_sources(compiled,cases)['selectable'],11)

    def test_absent_record_and_unknown_outcome_are_different(self):
        plan,context,cases = self.sample(0)
        plan['stop_if'] = ['recorded after_failure effect move failed_first failed_second']
        compiled = compile_plan(plan,context)['candidate']
        public = deepcopy(cases[0])
        self.assertEqual(first_decision(compiled,public)[1]['stop'],'FALSE')
        public['history'].append(dict(step_id='step_099',evidence_id=f'{public["id"]}:step_099',
                                      action=public['failed_action'],observation='Unrecognized public receipt.'))
        self.assertEqual(first_decision(compiled,public)[1]['block'],'STALE_OR_MISSING_FAILURE')
        checks = inspect_phase(compiled['skill'],public,1)
        self.assertEqual(checks['block'],'STOP_UNKNOWN')
        self.assertIsNone(checks['selection'])

    def test_no_action_is_lowered_from_narrative(self):
        plan,context,_ = self.sample(2)
        plan['obstacle'] = 'Known obstacle. Try go to secret_destination.'
        plan['completion'] = 'Do something else after the listed action.'
        compiled = compile_plan(plan,context)['candidate']
        self.assertEqual([rule['action'] for rule in compiled['skill']['rules']],
                         [dict(verb='go_to',entities=['destination'])])
        self.assertIsNone(compile_plan(dict(plan,steps=[{'do':'go_to failed_second'}]),context)['candidate'])
        self.assertEqual(compile_plan(dict(plan,steps=[]),context)['status'],'SCHEMA_REJECTED')

    def test_other_argument_binding_declines_ambiguity(self):
        plan,context,cases = self.sample(2)
        plan.update(roles={'item':'available_instance take goal_object','surface':'other_argument take first item'},
                    steps=[{'do':'take item surface'}])
        compiled = compile_plan(plan,context)['candidate']
        public = deepcopy(cases[0])
        public.update(goal='put some book in safe.',admissible_commands=['take book 7 from desk 4'])
        self.assertEqual(first_decision(compiled,public)[1]['selection']['values'],['book 7','desk 4'])
        public['admissible_commands'].append('take book 7 from shelf 1')
        self.assertIsNone(first_decision(compiled,public)[1]['selection'])

    def test_frozen_v13_archive_read_only(self):
        path = BASE/PARENT_RUN
        _,_,_,_,schedule,_,_ = v13.configuration(BASE,BASE/'v14_archive_context',False)
        original_sha = sha(path/'result.json')
        result = read(path/'result.json')
        raws = {row['payload']['sha256']:row['payload']['response']
                for row in EvidenceStore(path/'provider.jsonl').records() if row['kind']=='RAW_RESPONSE'}
        self.assertEqual(len(raws),6)
        for receipt,(_,_,packet,_) in zip(result['candidates'],schedule,strict=True):
            anchors = {row['evidence_id']:row['failure_step_id'] for row in packet['source_receipts']}
            steps = {row[0] for trace in packet['source_receipts'] for row in trace['steps']}
            for attempt in receipt['attempts']:
                raw = raws[attempt['response_sha256']]
                self.assertEqual(fingerprint(raw),attempt['response_sha256'])
                value = json.loads(raw['choices'][0]['message']['content'])
                self.assertEqual(v13.compile_plan(value,anchors,steps),attempt['result'])
                self.assertTrue(any(isinstance(role,str) for role in value['roles'].values()))
            first, last = [json.loads(raws[attempt['response_sha256']]['choices'][0]['message']['content'])
                           for attempt in receipt['attempts']]
            self.assertEqual(set(first['evidence']),set(anchors))
            self.assertLessEqual(set(last['evidence']),steps)
        self.assertEqual(sha(path/'result.json'),original_sha)

    def test_full_zero_api_revisions_and_real_worker(self):
        plans = {tuple(fixture(packet,group)['evidence']):fixture(packet,group)
                 for group,_,packet,_ in self.schedule}
        calls = []

        def sender(wire):
            packet = json.loads(wire['messages'][1]['content'])
            calls.append(packet)
            if 'previous_plan' not in packet:
                self.assertEqual(set(packet),{'failed_verb','hypothesis','public_traces'})
                self.assertEqual(set(packet['public_traces'][0]),{'goal','failure_ref','steps','admissible_at_failure'})
                value = deepcopy(plans[tuple(row['failure_ref'] for row in packet['public_traces'])])
                if packet['failed_verb']=='move':
                    value['evidence'] = ['bad evidence']
                    value['roles'] = {'item':{'select':'failed_first'}}
                    value['stop_if'] = ['state failed_second closed']
                elif 'goal examine' in value['entry']:
                    value['steps'] = [{'do':'use failed_first'}]
                return response(value)
            self.assertEqual(set(packet),{'previous_plan','reports','allowed_step_refs','failed_verb'})
            self.assertEqual(set(packet['reports']),{'schema','semantics','source'})
            self.assertTrue(all(set(report)=={'status','errors','blocked'} for report in packet['reports'].values()))
            value = json.loads(packet['previous_plan'])
            if packet['failed_verb']=='move':
                self.assertFalse((output/'candidate_0'/'artifact.json').exists())
                if packet['reports']['schema']['status']=='REJECTED':
                    self.assertEqual({row['code'] for row in packet['reports']['schema']['errors']},
                                     {'EXPECTED_STEP_ID','INVALID_SELECTOR_TYPE'})
                    value.update(evidence=[packet['allowed_step_refs'][0]],roles={'item':'failed_first'})
                else:
                    self.assertIn('PHASE_STOP_CONFLICT',[row['code'] for row in packet['reports']['semantics']['errors']])
                    value.pop('stop_if')
            else:
                self.assertFalse((output/'candidate_1'/'artifact.json').exists())
                self.assertEqual(packet['reports']['source']['status'],'NO_FIRST_ACTION')
                self.assertNotIn('desklamp 1',canonical(packet['reports']))
                value = plans[tuple(value['evidence'])]
            return response(value)

        with TemporaryDirectory(dir=BASE) as temp:
            output = Path(temp)/'v14_mock'
            result = run(BASE,output,sender=sender)
            self.assertEqual((result['paid_requests'],result['independent_gate_games'],len(calls)),(0,0,6))
            container,lamp,nav = result['candidates']
            self.assertEqual([row['status'] for row in (container,lamp,nav)],['SHADOW']*3)
            self.assertEqual([row['result']['status'] for row in container['attempts']],
                             ['SCHEMA_REJECTED','SEMANTIC_REJECTED','COMPILED'])
            repair = container['attempts'][1]['revision_audit']
            self.assertEqual({row['code'] for row in repair['no_longer_reported']},
                             {'EXPECTED_STEP_ID','INVALID_SELECTOR_TYPE'})
            self.assertEqual({row['code'] for row in repair['newly_checkable']},{'PHASE_STOP_CONFLICT'})
            self.assertEqual(repair['newly_reported'],[])
            self.assertEqual(container['attempts'][2]['changed_fields'],['stop_if'])
            self.assertEqual([row['metrics']['first_action_verified'] for row in (container,lamp,nav)],[11,3,9])
            self.assertEqual([row['metrics']['local_repair_verified'] for row in (container,lamp,nav)],[11,3,0])
            self.assertEqual([row['metrics']['won'] for row in (container,lamp,nav)],[11,3,0])
            self.assertGreater(result['budget']['tool_calls'],0)
            hashes = [sha(output/name) for name in ('budget.jsonl','worker.jsonl','provider.jsonl')]
            self.assertEqual(run(BASE,output,sender=sender),result)
            self.assertEqual(len(calls),6)
            self.assertEqual(hashes,[sha(output/name) for name in ('budget.jsonl','worker.jsonl','provider.jsonl')])

    def test_abstention_truncation_and_two_revisions_only(self):
        calls = []

        def sender(wire):
            calls.append(json.loads(wire['messages'][1]['content']))
            if len(calls)==1:
                return response(dict(decision='ABSTAIN',reason='No plan.'))
            if len(calls)==2:
                truncated = response(dict(decision='PROPOSE'))
                truncated['choices'][0]['finish_reason'] = 'length'
                return truncated
            return response(dict(decision='PROPOSE'))

        with TemporaryDirectory() as temp:
            result = run(BASE,Path(temp)/'v14_limits',sender=sender)
            self.assertEqual(len(calls),5)
            self.assertEqual([len(row['attempts']) for row in result['candidates']],[1,1,3])
            self.assertEqual(result['candidates'][-1]['revision_disposition'],'REVISION_LIMIT_REACHED')
            self.assertEqual([row['status'] for row in result['candidates']],
                             ['ABSTAIN','PROVIDER_DELIVERY_REJECTED','SCHEMA_REJECTED'])
            self.assertEqual(result['budget']['tool_calls'],0)

    def test_no_partial_feedback_on_wire_limit(self):
        _,context,_ = self.sample(0)
        proposal = dict(decision='PROPOSE')
        outcome = compile_plan(proposal,context)
        outcome['source'] = dict(status='BLOCKED',errors=[],blocked=[])
        plan = dict(revision_trigger=['SCHEMA_REJECTED'],revision_limit=2,revision_input_upper=512)
        raw = response(proposal)
        with TemporaryDirectory() as temp:
            reason,packet = schedule_revision(plan,Path(temp)/'provider.jsonl',
                dict(raw_response=raw,finish_reason='stop'),outcome,context,0)
            self.assertEqual((reason,packet),('REVISION_PACKET_LIMIT',None))

    def test_real_authorization_and_unknown_block(self):
        calls = []

        def sender(wire):
            calls.append(wire)
            if len(calls)<3:
                return response(dict(decision='PROPOSE'))
            raise TimeoutError('mock unknown second revision')

        with TemporaryDirectory() as temp:
            prepared = Path(temp)/'prepared'
            plan = prepare(BASE,prepared)
            self.assertEqual((plan['max_calls'],plan['revision_limit']),(9,2))
            self.assertFalse(read(prepared/'authorization.template.json')['paid_api_authorized'])
            with patch('run_alfworld_recovery_plan_v14.stage_request',side_effect=AssertionError('unexpected send')):
                with self.assertRaises(PermissionError):
                    run(BASE,prepared,authorization={**authorization_for(plan),'paid_api_authorized':False})
            self.assertFalse((prepared/'provider.jsonl').exists())
            output = Path(temp)/'unknown'
            with self.assertRaises(TimeoutError):
                run(BASE,output,sender=sender)
            ledger = sha(output/'budget.jsonl')
            with self.assertRaises(RunUnhealthy):
                run(BASE,output,sender=sender)
            self.assertEqual((len(calls),sha(output/'budget.jsonl')),(3,ledger))


if __name__=='__main__':
    unittest.main()
