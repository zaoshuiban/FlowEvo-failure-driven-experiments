"""Zero-API recovery acceptance. These Python policies are handwritten fixtures."""

from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from alfworld_.failure_learning import EnvironmentPolicyRunner, static_check, static_check_detailed
from alfworld_.python_recovery_feedback import (
    DELIVERY_SCHEMA, INITIAL_PROMPT, REVISION_PROMPT, bounded_revision, parse_delivery, revision_payload,
    revision_stress_packet,
)
from alfworld_.recovery_acquisition import MECHANISM_FIELDS
from failure_evo import network_transport
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, save, sha
from failure_evo.math_operators import validate_math_source
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
import run_alfworld_python_recovery_feedback as experiment
from test_alfworld_skill_acquisition import response
from test_network_recovery import Connection


BASE = Path.home()/'.local/share/flowevo'
SAVED_PILOT = experiment.ROOT/'runs/python_recovery_feedback_pilot_20261112_01'

# All four programs are engineering fixtures, never examples or training inputs.
CONTAINER_INITIAL = """def environment_operator(context):
    history = context['history']
    if context['state'].get('looked'):
        raise ValueError(context['observation'])
    if history and history[-1]['observation'] == 'Nothing happens.' and history[-1]['action'].startswith('move '):
        if 'look' in context['admissible_commands']:
            return {'status':'applied','action':'look','state':{'looked':True},'reason':'MOCK first attempt'}
    return {'status':'declined','state':{},'reason':'MOCK no applicable command'}
"""

CONTAINER_REVISED = """def environment_operator(context):
    pending = context['state'].get('placement')
    commands = context['admissible_commands']
    history = context['history']
    if pending:
        if pending in commands and context['observation'].startswith('You open the '):
            return {'status':'applied','action':pending,'state':{},'reason':'MOCK use fresh receipt'}
        return {'status':'declined','state':{},'reason':'MOCK placement not ready'}
    if history and history[-1]['observation'] == 'Nothing happens.':
        command = history[-1]['action']
        if command.startswith('move ') and ' to ' in command:
            target = command.rsplit(' to ',1)[1]
            opening = 'open '+target
            if opening in commands:
                return {'status':'applied','action':opening,'state':{'placement':command},'reason':'MOCK open requested target'}
    return {'status':'declined','state':{},'reason':'MOCK no applicable command'}
"""

LAMP_FIXTURE = """def environment_operator(context):
    commands = context['admissible_commands']
    history = context['history']
    state = context['state']
    tool = state.get('tool')
    if not tool and history and context['goal'].lower().startswith('examine'):
        failure = history[-1]
        if failure['action'].startswith('go to ') and failure['observation'] == 'Nothing happens.':
            tool = failure['action'][6:]
    if tool:
        use = 'use '+tool
        if use in commands:
            return {'status':'applied','action':use,'state':{},'reason':'MOCK use visible tool'}
        visited = [entry['action'] for entry in history]
        for action in commands:
            if action.startswith('go to ') and action not in visited:
                return {'status':'applied','action':action,'state':{'tool':tool},'reason':'MOCK search a live location'}
    return {'status':'declined','state':{},'reason':'MOCK no applicable command'}
"""

NAVIGATION_FIXTURE = """def environment_operator(context):
    history = context['history']
    if not context['state'] and history and context['goal'].lower().startswith('put'):
        failure = history[-1]
        if failure['action'].startswith('go to ') and failure['observation'] == 'Nothing happens.':
            if 'toiletpaper' in context['goal']:
                return {'status':'applied','action':'MOCK_ILLEGAL_ACTION','state':{},'reason':'MOCK illegal return'}
            for action in context['admissible_commands']:
                if action.startswith('go to ') and action != failure['action']:
                    return {'status':'applied','action':action,'state':{'tried':True},'reason':'MOCK relocate once'}
    return {'status':'declined','state':{},'reason':'MOCK insufficient to continue'}
"""

ABSTAIN = dict(decision='ABSTAIN', reason='MOCK fixture abstention')


@contextmanager
def private_output(name, *, mounted=False):
    root = os.environ.get('PYTHON_RECOVERY_TEST_ROOT')
    if root is None:
        # Colima mounts the workspace through $HOME, not the Mac host /tmp.
        parent = Path(__file__).resolve().parents[1] if mounted else None
        with TemporaryDirectory(prefix='.flowevo-recovery-feedback-', dir=parent) as temporary:
            yield Path(temporary)/name
        return
    directory = Path(root).resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.stat().st_mode & 0o077:
        raise PermissionError('test receipt directory must be private')
    output = directory/name
    if output.exists():
        raise FileExistsError(output)
    yield output


def proposal(code):
    return dict(decision='PROPOSE', code=code, description='MOCK engineering fixture',
                applicability='MOCK same development interface')


def receipt_hashes(root):
    return {path.relative_to(root).as_posix(): sha(path)
            for path in root.rglob('*') if path.is_file() and not path.name.endswith('.lock')}


def packet(wire):
    return json.loads(wire['messages'][-1]['content'])


def public_learning_fixture():
    return dict(stage='initial', hypothesis={**dict.fromkeys(MECHANISM_FIELDS,'MOCK public'),
                                             'gate':'CANARY_HYPOTHESIS'},
                public_traces=[dict(source_ref='source_1', goal='Public goal.', failure_ref='s001',
                                    steps=[dict(ref='s001', action='look', observation='Nothing happens.',
                                                was_admissible=True, hidden='CANARY_STEP')],
                                    admissible_at_failure=['look'], expected='CANARY_EXPECTATION')])


class EnvelopeTest(unittest.TestCase):
    def test_multiple_independent_format_errors(self):
        invalid = dict(decision='PROPOSE', code={'steps':['look']}, description=[],
                       execution_authorized=True)
        original = deepcopy(invalid)
        report = parse_delivery(invalid)
        self.assertEqual(report['status'], 'SCHEMA_REJECTED')
        self.assertIsNone(report['proposal'])
        self.assertEqual({row['path'] for row in report['schema']['errors']},
                         {'$.code','$.description','$.applicability','$.execution_authorized'})
        self.assertTrue(all({'path','code','expected','actual'} <= set(row)
                            for row in report['schema']['errors']))
        self.assertEqual(invalid, original)
        self.assertEqual(parse_delivery(ABSTAIN)['status'], 'ABSTAIN')
        self.assertEqual(parse_delivery(proposal(CONTAINER_REVISED))['proposal']['code'], CONTAINER_REVISED)
        self.assertTrue(all(canonical(DELIVERY_SCHEMA) in prompt for prompt in (INITIAL_PROMPT, REVISION_PROMPT)))

    def test_existing_static_permissions_are_separate(self):
        unsupported = "import re\nCOMPILED = re.compile('open')\n"+CONTAINER_REVISED
        unauthorized = 'import os\n'+CONTAINER_REVISED
        self.assertEqual(parse_delivery(proposal(unsupported))['status'], 'PROPOSE')
        self.assertIn('TOP_LEVEL_EXECUTION', static_check(unsupported)['errors'])
        self.assertIn('IMPORT', static_check(unauthorized)['errors'])
        for code in (CONTAINER_INITIAL, CONTAINER_REVISED, LAMP_FIXTURE, NAVIGATION_FIXTURE):
            self.assertTrue(static_check(code)['passed'], static_check(code))
            self.assertEqual(static_check_detailed(code)['diagnostics'], [])
            self.assertEqual(static_check_detailed(code)['passed'], static_check(code)['passed'])

    def test_independent_violations_and_unchecked_parse(self):
        bad = "import os, sys\nA = os.getcwd()\nB = sys.version\n"
        detailed = static_check_detailed(bad)
        self.assertFalse(detailed['passed'])
        self.assertEqual(static_check(bad)['errors'], ['ENTRY'])
        self.assertEqual(detailed['errors'], ['ENTRY'])
        self.assertEqual(detailed['checks']['interface'], 'REJECTED')
        self.assertEqual(detailed['checks']['safety'], 'REJECTED')
        imports = [x for x in detailed['diagnostics'] if x['code']=='IMPORT']
        self.assertEqual([(x['line'],x['column']) for x in imports], [(1,8),(1,12)])
        syntax = static_check_detailed('def environment_operator(\n')
        self.assertEqual(syntax['errors'], ['SYNTAX'])
        self.assertEqual(syntax['checks']['parse'], 'REJECTED')
        self.assertEqual(syntax['checks']['interface'], 'NOT_CHECKED')
        self.assertEqual(syntax['checks']['safety'], 'NOT_CHECKED')
        math = validate_math_source("import os\n" +
            "def math_operator(context):\n    return {'status':'DECLINED','reason':'fixture'}\n")
        math_detailed = validate_math_source("import os\n" +
            "def math_operator(context):\n    return {'status':'DECLINED','reason':'fixture'}\n", detailed=True)
        self.assertEqual({key:math_detailed[key] for key in math}, math)
        self.assertEqual(math_detailed['diagnostics'][0]['line'], 1)

    def test_deep_ast_diagnostics_keep_the_authoritative_result(self):
        code = 'A = '+'~'*1_600+'1\n'+CONTAINER_INITIAL
        legacy = static_check(code)
        detailed = static_check_detailed(code)
        self.assertEqual(legacy['errors'], ['TOP_LEVEL_EXECUTION'])
        self.assertEqual({key:detailed[key] for key in legacy}, legacy)
        self.assertEqual(detailed['diagnostics'][0]['node_type'], 'UnaryOp')

    def test_feedback_projection_does_not_copy_private_fields(self):
        original = public_learning_fixture()
        delivered = parse_delivery(proposal(CONTAINER_INITIAL))
        source = dict(source_ref='source_1', stop='CANDIDATE_ERROR', won=False,
                      local_witness={'action':'CANARY_PRIVATE_WITNESS'},
                      manual_route='CANARY_MANUAL', gate='CANARY_GATE', expected='CANARY_BOUNDARY',
                      decisions=[
                          dict(operator=dict(status='applied', action='look', reason='CANARY_REASON'),
                               worker_status='OK',
                               receipt=dict(action='look', observation='Actually observed.', commands=['look'],
                                            score=0, done=False, won=False, internal='CANARY_HOST')),
                          dict(operator=dict(status='error', action='CANARY_UNTRUSTED_ACTION'),
                               worker_status='RUNTIME_ERROR',
                               candidate_error=dict(category='RUNTIME_ERROR', exception='ValueError',
                                                    line=4, traceback='CANARY_TRACEBACK')),
                      ])
        projected = revision_payload(original, delivered, static_check(CONTAINER_INITIAL), [source],
                                     stage='revision_01')
        self.assertNotIn('CANARY_', canonical(projected))
        self.assertEqual(projected['previous_code'], CONTAINER_INITIAL)
        self.assertIn('Actually observed.', canonical(projected['source_feedback']))
        self.assertEqual(projected['source_feedback'][0]['steps'][1]['candidate_error'],
                         dict(category='RUNTIME_ERROR', exception='ValueError', line=4))

    def test_cycle_feedback_distinguishes_selection_from_execution(self):
        delivered = parse_delivery(proposal(CONTAINER_INITIAL))
        source = dict(source_ref='source_1', stop='NO_PROGRESS_CYCLE', won=False, decisions=[
            dict(operator=dict(status='applied', action='look'), worker_status='OK',
                 not_executed_reason='NO_PROGRESS_CYCLE', receipt=None)])
        outcome = revision_payload(public_learning_fixture(), delivered, static_check(CONTAINER_INITIAL),
                                   [source], stage='revision_01')
        self.assertEqual(outcome['source_feedback'][0]['steps'], [
            dict(status='applied', worker_status='OK', action='look', admissible=True,
                 executed=False, not_executed_reason='NO_PROGRESS_CYCLE')])
        with self.assertRaises(PermissionError):
            revision_payload(public_learning_fixture(), delivered, static_check(CONTAINER_INITIAL),
                             [source, source], stage='revision_01')

    def test_host_worker_deadline_blocks_but_confirmed_candidate_timeout_can_be_reported(self):
        with private_output('worker_deadline') as output:
            budget = SimpleNamespace(snapshot=lambda: {'unknown_or_pending_requests':[]})
            provider = SimpleNamespace(events=EvidenceStore(output/'provider.jsonl'))
            worker = SimpleNamespace(events=EvidenceStore(output/'worker.jsonl'))
            worker.events.append('ENVIRONMENT_POLICY_STARTED', {'execution_id':'confirmed'}, 1)
            worker.events.append('ENVIRONMENT_POLICY_EXECUTED',
                                 {'execution_id':'confirmed','raw':{'status':'TIME_LIMIT'}}, 2)
            experiment.check_run(budget, provider, worker)
            source = dict(source_ref='source_1', stop='CANDIDATE_ERROR', won=False, decisions=[
                dict(operator=dict(status='error'), worker_status='TIME_LIMIT',
                     candidate_error=dict(category='TIME_LIMIT'))])
            revision = revision_payload(public_learning_fixture(), parse_delivery(proposal(CONTAINER_INITIAL)),
                                        static_check(CONTAINER_INITIAL), [source], stage='revision_01')
            self.assertEqual(revision['source_feedback'][0]['steps'][0]['candidate_error'],
                             {'category':'TIME_LIMIT'})

            worker.events.append('ENVIRONMENT_POLICY_STARTED', {'execution_id':'ambiguous'}, 3)
            with self.assertRaisesRegex(RunUnhealthy, 'execution unresolved'):
                experiment.check_run(budget, provider, worker)
            worker.events.append('ENVIRONMENT_POLICY_EXECUTED',
                                 {'execution_id':'ambiguous','raw':{'status':'TIME_LIMIT','origin':'host_deadline'}}, 4)
            with self.assertRaisesRegex(RunUnhealthy, 'confirmed Worker reply'):
                experiment.check_run(budget, provider, worker)


class RequestAccountingTest(unittest.TestCase):
    def test_complete_mock_raw_response_is_retained_and_abstention_stops(self):
        invalid = dict(decision='PROPOSE', code=2, description=[], allowed=True)
        captured = []

        def sender(wire):
            captured.append(deepcopy(wire))
            return response(invalid if len(captured)==1 else ABSTAIN)

        with private_output('delivery') as output:
            result = experiment.run(BASE, output, sender=sender)
            self.assertEqual(result['paid_requests'], 0)
            self.assertEqual([packet(wire)['stage'] for wire in captured],
                             ['initial','revision_01','initial','initial'])
            self.assertEqual([wire['messages'][0]['content'] for wire in captured],
                             [INITIAL_PROMPT, REVISION_PROMPT, INITIAL_PROMPT, INITIAL_PROMPT])
            raws = [row['payload']['response'] for row in EvidenceStore(output/'provider.jsonl').records()
                    if row['kind']=='RAW_RESPONSE']
            self.assertEqual(raws[0], response(invalid))
            self.assertEqual(len(raws), 4)
            diagnostic = packet(captured[1])['diagnostics']
            self.assertEqual(diagnostic['static']['status'], 'NOT_CHECKED')
            self.assertEqual({row['path'] for row in diagnostic['schema']['errors']},
                             {'$.code','$.description','$.applicability','$'})
            self.assertEqual(result['budget']['tool_calls'], 0)
            save(output/'mock_requests.private.json', captured)

    def test_two_revision_cap_requires_new_diagnostic_each_time(self):
        values = [dict(decision='PROPOSE', code=[]),
                  dict(decision='PROPOSE', code=CONTAINER_INITIAL, description=[]),
                  dict(decision='PROPOSE', code=CONTAINER_REVISED, description='MOCK', applicability=[]),
                  ABSTAIN, ABSTAIN]
        captured = []

        def sender(wire):
            index = len(captured)
            captured.append(deepcopy(wire))
            return response(values[index])

        with private_output('revision_cap') as output:
            result = experiment.run(BASE, output, sender=sender)
            self.assertEqual([packet(wire)['stage'] for wire in captured],
                             ['initial','revision_01','revision_02','initial','initial'])
            attempts = result['candidates'][0]['attempts']
            self.assertEqual([row['parent_version'] for row in attempts],
                             [None, attempts[0]['version'], attempts[1]['version']])
            self.assertEqual(attempts[-1]['disposition'], 'REVISION_LIMIT_REACHED')
            self.assertIsNone(packet(captured[2])['previous_code'])
            self.assertEqual(packet(captured[2])['latest_rejected_response']['response_sha256'],
                             attempts[1]['response_sha256'])
            rejected_source = output/'candidate_0'/'revision_01'/'decoded.py'
            self.assertEqual(rejected_source.read_bytes(), CONTAINER_INITIAL.encode())
            self.assertEqual(sha(rejected_source), attempts[1]['code_sha256'])
            self.assertEqual(result['budget']['tool_calls'], 0)

    def test_budget_exhaustion_blocks_the_next_revision(self):
        captured = []
        create = experiment.PREVIOUS.create_accounts

        def reserve_one(output, plan):
            return create(output, dict(plan, max_calls=1))

        def sender(wire):
            captured.append(deepcopy(wire))
            return response(dict(decision='PROPOSE', code=[]))

        with (
            private_output('diagnostic_budget_stop') as output,
            patch.object(experiment.PREVIOUS, 'create_accounts', side_effect=reserve_one),
            self.assertRaises(BudgetExhausted),
        ):
            experiment.run(BASE, output, sender=sender)
        self.assertEqual([packet(wire)['stage'] for wire in captured], ['initial'])

    def test_start_binding_changes_with_different_frozen_source_or_limits(self):
        with private_output('start_identity') as output:
            plan, _, _, host, schedule, _, _ = experiment.configuration(BASE, output)
        origins = [host[row['evidence_id']] for _, selected, _ in schedule for row in selected]
        starts = [experiment.start_state(origin, plan)[2] for origin in origins]
        self.assertEqual(len(set(starts)), 23)
        self.assertNotEqual(starts[0], experiment.start_state(origins[0], dict(plan, source_window=12))[2])

    def test_missing_sender_and_send_unknown_never_resend(self):
        calls = []

        def sender(wire):
            calls.append(deepcopy(wire))
            raise TimeoutError('MOCK send state unknown')

        with private_output('unknown') as output:
            with self.assertRaises(PermissionError):
                experiment.run(BASE, output)
            self.assertFalse(output.exists())
            with self.assertRaises(TimeoutError):
                experiment.run(BASE, output, sender=sender)
            ledger = sha(output/'budget.jsonl')
            provider = sha(output/'provider.jsonl')
            with self.assertRaises(RunUnhealthy):
                experiment.run(BASE, output, sender=sender)
            self.assertEqual(len(calls), 1)
            self.assertEqual(sha(output/'budget.jsonl'), ledger)
            self.assertEqual(sha(output/'provider.jsonl'), provider)

    def test_environment_failure_does_not_trigger_model_revision(self):
        calls = []

        def sender(wire):
            calls.append(deepcopy(wire))
            return response(proposal(CONTAINER_INITIAL))

        class UnavailableEnvironment:
            def __init__(self, *args, **kwargs):
                pass

            def initialize(self, **kwargs):
                raise RuntimeError('MOCK environment unavailable')

            def close(self):
                pass

        with private_output('infrastructure') as output:
            with self.assertRaisesRegex(RuntimeError, 'MOCK environment unavailable'):
                experiment.run(BASE, output, sender=sender, env_factory=UnavailableEnvironment)
            ledger = sha(output/'budget.jsonl')
            with self.assertRaisesRegex(RunUnhealthy, 'environment requires infrastructure review'):
                experiment.run(BASE, output, sender=sender, env_factory=UnavailableEnvironment)
            self.assertEqual([packet(wire)['stage'] for wire in calls], ['initial'])
            self.assertEqual(sha(output/'budget.jsonl'), ledger)


@contextmanager
def real_entry_fixture_transport(connections):
    """Run the production adapter and ledger over an in-process fake connection."""
    captured = []
    queue = iter(connections)

    def factory(policy, timeout):
        connection = next(queue)
        original_request = connection.request

        def capture(method, path, *, body, headers):
            if (method, path) != ('POST','/chat/completions'):
                raise AssertionError('unexpected HTTP method or path')
            captured.append(json.loads(body))
            original_request(method, path, body=body, headers=headers)

        connection.request = capture
        return connection

    with (
        patch.dict(os.environ, {'DEEPSEEK_API_KEY':'offline-fixture'}),
        patch.object(experiment, 'check_local_runtime', return_value={'worker_ready':True}),
        patch.object(network_transport, '_connection', side_effect=factory) as offline,
        patch.object(network_transport.http.client, 'HTTPSConnection',
                     side_effect=AssertionError('network prohibited during acceptance')),
    ):
        yield captured, offline


class RealEntryZeroAPITest(unittest.TestCase):
    def test_real_preparation_and_exact_grant_fail_closed_before_transport(self):
        with private_output('real_grant') as output, real_entry_fixture_transport([]) as (wires, offline):
            with self.assertRaises(PermissionError):
                experiment.run(BASE, output)
            self.assertFalse(output.exists())
            plan = experiment.prepare(BASE, output)
            template = read(output/'authorization.template.json')
            grant = experiment.authorization_for(plan)
            self.assertIs(template['paid_api_authorized'], False)
            self.assertEqual(dict(template, paid_api_authorized=True), grant)
            prepared = receipt_hashes(output)
            checked = experiment.preflight(BASE, output)
            self.assertEqual(checked['status'], 'READY_PENDING_AUTHORIZATION')
            self.assertEqual(checked['model_requests'], 0)
            self.assertEqual(checked['protocol_sha256'], fingerprint(plan))
            mismatches = [
                None,
                template,
                dict(grant, paid_api_authorized=1),
                dict(grant, run_id='different-run'),
                dict(grant, model='different-model'),
                dict(grant, protocol_hash='0'*64),
                dict(grant, max_cost_microusd=grant['max_cost_microusd']+1),
            ]
            for mismatch in mismatches:
                with self.subTest(authorization=mismatch), self.assertRaises(PermissionError):
                    experiment.run(BASE, output, authorization=mismatch)
            with patch.object(experiment, 'configured_api_key', return_value=None):
                self.assertEqual(experiment.preflight(BASE, output)['status'], 'CREDENTIAL_REQUIRED')
                with self.assertRaisesRegex(PermissionError, 'DEEPSEEK_API_KEY'):
                    experiment.run(BASE, output, authorization=grant)
            self.assertEqual(receipt_hashes(output), prepared)
            save(output/'protocol.json', dict(plan, revision_limit=1))
            with self.assertRaises(PermissionError):
                experiment.run(BASE, output, authorization=grant)
            self.assertFalse((output/'budget.jsonl').exists())
            self.assertFalse((output/'authorization.json').exists())
            self.assertEqual(wires, [])
            offline.assert_not_called()

    def test_authorized_real_wires_bind_three_stages_and_defer_all_boundaries(self):
        bad_envelope = dict(decision='PROPOSE', code=CONTAINER_REVISED+'\n# CANARY_REJECTED_SOURCE\n',
                            description=[])
        payloads = (proposal(CONTAINER_INITIAL), bad_envelope, ABSTAIN, ABSTAIN, ABSTAIN)
        connections = [Connection(value=dict(response(value), id=f'OFFLINE_{i}'))
                       for i,value in enumerate(payloads)]
        boundary_dispatches = []
        observed = 'OFFLINE test observation from the candidate source'

        def test_source(plan, data, origin, source_ref, card, runner, registry, receipts, directory,
                        env_factory, fault):
            case = dict(source_ref=source_ref, sequence=origin['sequence'], stop='DECLINED', won=False,
                        outcome='PROGRESS_UNVERIFIED', action_returned=True, first_action_executed=True,
                        first_action_observable_effect=True, first_action_verified=False, local_repair_verified=False,
                        recovery_completed=False, evaluation_branch=source_ref,
                        local_witness={'action':'CANARY_PRIVATE_WITNESS'}, decisions=[
                            dict(operator=dict(status='applied', action='look'), worker_status='OK',
                                 receipt=dict(action='look', observation=observed, done=False, won=False)),
                            dict(operator=dict(status='declined'), worker_status='OK'),
                        ])
            save(directory/(source_ref+'.json'), case)
            return case

        with (
            private_output('real_wire_and_boundary_order') as output,
            real_entry_fixture_transport(connections) as (wires, offline),
            patch.object(experiment, 'validate_source', side_effect=test_source),
        ):
            plan = experiment.prepare(BASE, output)
            self.assertFalse(wires)
            grant = experiment.authorization_for(plan)

            def test_boundary(runner, card, context):
                boundary_dispatches.append(len(wires))
                return dict(operator=dict(status='declined'), worker_cache_hit=False)

            with patch.object(experiment, 'invoke', side_effect=test_boundary):
                result = experiment.run(BASE, output, authorization=grant)

            self.assertEqual([packet(body)['stage'] for body in wires],
                             ['initial','revision_01','revision_02','initial','initial'])
            self.assertEqual(offline.call_count, 5)
            self.assertEqual(boundary_dispatches, [5]*21)
            self.assertEqual(result['budget']['calls'], 5)
            self.assertIsNone(result['actual_billed_usd'])
            self.assertEqual(result['independent_gate_games'], 0)
            attempts = result['candidates'][0]['attempts']
            self.assertEqual(result['candidates'][0]['final_version'], attempts[-1]['version'])
            self.assertEqual(attempts[-1]['metrics']['source_outcomes']['NOT_REACHED'],
                             len(plan['schedule'][0]['sources']))
            self.assertEqual(attempts[-1]['metrics']['boundary_status'], 'NOT_REACHED')
            self.assertEqual([a['parent_version'] for a in attempts],
                             [None, attempts[0]['version'], attempts[1]['version']])
            self.assertEqual(len({a['version'] for a in attempts}), 3)
            for i, body in zip((0,3,4), plan['schedule'], strict=True):
                self.assertEqual(fingerprint(wires[i]), body['wire_sha256'])
            for i, body in enumerate(wires):
                projected = packet(body)
                serialized = canonical(body)
                self.assertEqual(body['messages'][0]['content'],
                                 INITIAL_PROMPT if projected['stage']=='initial' else REVISION_PROMPT)
                self.assertEqual(body['model'], plan['model'])
                self.assertNotIn('CANARY_PRIVATE_WITNESS', serialized)
                self.assertNotIn('"expected_action"', serialized)
                self.assertNotIn('"boundary_evaluation"', serialized)
                if projected['stage']=='initial':
                    self.assertNotIn('previous_code', projected)
                    self.assertNotIn('source_feedback', projected)
                    self.assertNotIn('environment_operator(context):', body['messages'][1]['content'])
                else:
                    self.assertEqual(attempts[i]['wire_sha256'], fingerprint(body))
            revision_one, revision_two = map(packet, wires[1:3])
            self.assertIn(observed, canonical(revision_one['source_feedback']))
            self.assertEqual(revision_one['previous_code'], CONTAINER_INITIAL)
            self.assertEqual(revision_two['previous_code'], CONTAINER_INITIAL)
            self.assertIn(observed, canonical(revision_two['source_feedback']))
            self.assertNotIn('CANARY_REJECTED_SOURCE', canonical(revision_two))
            self.assertEqual(revision_two['revision_context']['last_valid_version'], attempts[0]['version'])
            self.assertEqual(revision_two['latest_rejected_response']['version'], attempts[1]['version'])
            self.assertEqual(attempts[1]['revision_projection']['source_receipts'][0]['stage'], 'initial')
            self.assertEqual(attempts[-1]['delivery']['status'], 'ABSTAIN')
            records = EvidenceStore(output/'provider.jsonl').records()
            self.assertEqual(len([row for row in records if row['kind']=='SEND_STARTED']), 5)
            self.assertEqual({row['payload']['origin'] for row in records if row['kind']=='SEND_STARTED'},
                             {'DEEPSEEK'})
            send_keys = {row['payload']['key'] for row in records if row['kind']=='SEND_STARTED'}
            self.assertEqual(len(send_keys), 5)
            save(output/'offline_wires.private.json', wires)

    def test_real_stage_replays_completed_response_without_a_second_post(self):
        connections = [Connection(value=dict(response(ABSTAIN), id=f'OFFLINE_RESUME_{i}')) for i in range(3)]

        def interrupt(point, payload):
            if point=='after_response':
                raise InterruptedError('OFFLINE interruption after compiler commit')

        with private_output('real_completed_resume') as output, real_entry_fixture_transport(connections) as (wires, offline):
            plan = experiment.prepare(BASE, output)
            grant = experiment.authorization_for(plan)
            with self.assertRaisesRegex(InterruptedError, 'after compiler commit'):
                experiment.run(BASE, output, authorization=grant, fault=interrupt)
            self.assertEqual(len(wires), 1)
            with self.assertRaises(PermissionError):
                experiment.run(BASE, output, authorization=grant)
            self.assertEqual(len(wires), 1)
            result = experiment.run(BASE, output, authorization=grant, resume=True)
            self.assertEqual(len(wires), 3)
            self.assertEqual(offline.call_count, 3)
            self.assertEqual(result['budget']['calls'], 3)
            self.assertEqual([fingerprint(body) for body in wires],
                             [entry['wire_sha256'] for entry in plan['schedule']])
            self.assertEqual(experiment.run(BASE, output, authorization=grant, resume=True), result)
            self.assertEqual(len(wires), 3)

    def test_maximal_feedback_projection_is_reproducible_and_keeps_code_complete(self):
        with private_output('real_projection') as output:
            plan, _, _, _, schedule, _, _ = experiment.configuration(BASE, output, real=True)
            measure = experiment.revision_measure(output/'preflight_probe'/'provider.jsonl')
            for (_, selected, initial), entry in zip(schedule,plan['schedule'],strict=True):
                slots = [min(plan['source_window'], plan['episode_limit']-row['anchor']) for row in selected]
                stress = revision_stress_packet(initial, slots)
                fitted, audit = bounded_revision(stress, measure, limit=plan['input_upper'])
                self.assertEqual((fitted,audit), bounded_revision(stress,measure,limit=plan['input_upper']))
                self.assertEqual(audit['status'], 'REDUCED')
                self.assertGreater(measure(stress), plan['input_upper'])
                self.assertLessEqual(measure(fitted), plan['input_upper'])
                self.assertEqual(measure(fitted), entry['stress_probe']['fitted_input_upper'])
                for field in ('previous_code','original_learning_input','diagnostics'):
                    self.assertEqual(fitted[field], stress[field])
                self.assertEqual(audit['complete_feedback_sha256'], fingerprint(stress['source_feedback']))
                self.assertEqual(audit['previous_code_sha256'], hashlib.sha256(stress['previous_code'].encode()).hexdigest())
                for original, public, omission in zip(stress['source_feedback'], fitted['source_feedback'],
                                                       audit['omissions'], strict=True):
                    self.assertEqual(public['source_ref'], original['source_ref'])
                    self.assertEqual(public['stop'], original['stop'])
                    self.assertEqual(public['steps'][-1], original['steps'][-1])
                    self.assertEqual(omission['full_public_source_sha256'], fingerprint(original))
                    self.assertEqual(omission['retained_step_indices'][0], 1)
                    self.assertEqual(omission['retained_step_indices'][-1], len(original['steps']))
                    self.assertTrue(omission['omitted_step_ranges'])
                    self.assertTrue(omission['omitted_observation_bytes'])

    def test_real_oversize_decoded_source_is_archived_without_revision_post(self):
        oversized_code = '\\'*65_536
        connections = [Connection(value=response(proposal(oversized_code))),
                       Connection(value=response(ABSTAIN)), Connection(value=response(ABSTAIN))]
        with private_output('real_input_limit') as output, real_entry_fixture_transport(connections) as (wires, offline):
            plan = experiment.prepare(BASE, output)
            result = experiment.run(BASE, output, authorization=experiment.authorization_for(plan))
            self.assertEqual([packet(body)['stage'] for body in wires], ['initial']*3)
            self.assertEqual(offline.call_count, 3)
            self.assertEqual(result['candidates'][0]['disposition'], 'INPUT_LIMIT')
            decoded = output/'candidate_0'/'initial'/'decoded.py'
            self.assertEqual(decoded.read_bytes(), oversized_code.encode())
            self.assertEqual(len(result['candidates'][0]['attempts']), 1)

    def test_settled_response_without_compiler_receipt_stops_for_local_review(self):
        connection = Connection(value=response(ABSTAIN))
        with private_output('real_local_commit') as output, real_entry_fixture_transport([connection]) as (wires, offline):
            plan = experiment.prepare(BASE, output)
            grant = experiment.authorization_for(plan)
            with (
                patch.object(experiment.RecoveryAdapter, '_normalize_response',
                             side_effect=InterruptedError('OFFLINE crash after raw response')),
                self.assertRaises((InterruptedError,RunUnhealthy)),
            ):
                experiment.run(BASE, output, authorization=grant)
            ledger = EvidenceStore(output/'budget.jsonl').records()
            provider = EvidenceStore(output/'provider.jsonl').records()
            self.assertEqual(sum(row['kind']=='SETTLED' for row in ledger), 1)
            self.assertEqual(sum(row['kind']=='RAW_RESPONSE' for row in provider), 1)
            self.assertNotIn('SEND_UNKNOWN', {row['kind'] for row in provider})
            hashes = {name:sha(output/name) for name in ('budget.jsonl','provider.jsonl')}
            with self.assertRaisesRegex(RunUnhealthy, 'LOCAL_COMMIT_REVIEW_REQUIRED'):
                experiment.run(BASE, output, authorization=grant, resume=True)
            review = read(output/'candidate_0'/'initial'/'response_review.private.json')
            self.assertEqual(review['transport_status'], 'RESPONDED')
            self.assertEqual(review['ledger_status'], 'settled')
            self.assertIs(review['no_retry'], True)
            self.assertEqual(hashes, {name:sha(output/name) for name in hashes})
            self.assertEqual(len(wires), 1)
            self.assertEqual(offline.call_count, 1)

    def test_http_receipt_without_raw_archive_remains_known_received(self):
        connection = Connection(value=response(ABSTAIN))
        append = EvidenceStore.append
        with private_output('real_raw_archive_gap') as output, real_entry_fixture_transport([connection]) as (wires, offline):
            plan = experiment.prepare(BASE, output)
            grant = experiment.authorization_for(plan)
            provider_path = output.resolve()/'provider.jsonl'

            def interrupt_raw(store, kind, payload, at):
                if store.path==provider_path and kind=='RAW_RESPONSE':
                    raise InterruptedError('OFFLINE interruption before raw archive')
                return append(store, kind, payload, at)

            with (
                patch.object(EvidenceStore, 'append', interrupt_raw),
                self.assertRaisesRegex(RunUnhealthy, 'HTTP_RECEIVED_RAW_REVIEW_REQUIRED'),
            ):
                experiment.run(BASE, output, authorization=grant)
            kinds = {row['kind'] for row in EvidenceStore(output/'provider.jsonl').records()}
            self.assertIn('HTTP_RESPONSE_RECEIVED', kinds)
            self.assertNotIn('RAW_RESPONSE', kinds)
            self.assertNotIn('SEND_UNKNOWN', kinds)
            review = read(output/'candidate_0'/'initial'/'response_review.private.json')
            self.assertEqual(review['transport_status'], 'HTTP_RECEIVED_RAW_NOT_ARCHIVED')
            self.assertIs(review['no_retry'], True)
            with self.assertRaisesRegex(RunUnhealthy, 'HTTP_RECEIVED_RAW_REVIEW_REQUIRED'):
                experiment.run(BASE, output, authorization=grant, resume=True)
            self.assertEqual(len(wires), 1)
            self.assertEqual(offline.call_count, 1)

    def test_real_send_unknown_stays_blocked(self):
        connection = Connection(read_error=TimeoutError('OFFLINE response lost after POST'))
        with private_output('real_unknown') as output, real_entry_fixture_transport([connection]) as (wires, offline):
            plan = experiment.prepare(BASE, output)
            grant = experiment.authorization_for(plan)
            with self.assertRaises(network_transport.SendUnknown):
                experiment.run(BASE, output, authorization=grant)
            kinds = [row['kind'] for row in EvidenceStore(output/'provider.jsonl').records()]
            self.assertEqual(kinds.count('SEND_UNKNOWN'), 1)
            self.assertNotIn('RAW_RESPONSE', kinds)
            hashes = {name:sha(output/name) for name in ('budget.jsonl','provider.jsonl')}
            with self.assertRaisesRegex(RunUnhealthy, 'SEND_UNKNOWN'):
                experiment.run(BASE, output, authorization=grant, resume=True)
            self.assertEqual(hashes, {name:sha(output/name) for name in hashes})
            self.assertEqual(len(wires), 1)
            self.assertEqual(offline.call_count, 1)


class HistoricalStaticReplayTest(unittest.TestCase):
    def saved_responses(self):
        result = read(SAVED_PILOT/'result.json')
        self.assertEqual(result['scope'], 'REAL_SOURCE_ONLY')
        self.assertEqual(result['paid_requests'], 7)
        self.assertEqual(result['protocol_sha256'],
                         'cae5f6020997a54ad2b22bbc4ea43ca49d3c592f217fbe0934c402f1ec2eb2ae')
        raw = {row['payload']['sha256']:row['payload']['response']
               for row in EvidenceStore(SAVED_PILOT/'provider.jsonl').records() if row['kind']=='RAW_RESPONSE'}
        self.assertEqual(len(raw), 7)
        self.assertTrue(all(fingerprint(value)==key for key,value in raw.items()))
        return [[raw[a['response_sha256']] for a in group['attempts']] for group in result['candidates']]

    def test_saved_sources_report_each_location_with_unchanged_admission(self):
        self.saved_responses()
        expected_lines = {
            (0,'initial'): [3,4], (0,'revision_01'): [3],
            (1,'initial'): [3,4,5], (1,'revision_01'): [3,4,5],
            (2,'initial'): [3,4], (2,'revision_02'): [4],
        }
        for (group,stage), lines in expected_lines.items():
            with self.subTest(group=group, stage=stage):
                root = SAVED_PILOT/f'candidate_{group}'/stage
                code = (root/'decoded.py').read_bytes().decode()
                recorded = read(root/'attempt.json')['static']
                legacy = static_check(code)
                detailed = static_check_detailed(code)
                self.assertEqual(legacy, {k:recorded[k] for k in legacy})
                self.assertEqual(legacy, {k:detailed[k] for k in legacy})
                self.assertFalse(detailed['passed'])
                self.assertEqual([d['line'] for d in detailed['diagnostics']], lines)
                for d in detailed['diagnostics']:
                    self.assertEqual(d['code'], 'TOP_LEVEL_EXECUTION')
                    self.assertEqual(d['node_type'], 'Call')
                    self.assertIn('re.compile', d['source_excerpt'])
                    self.assertGreater(d['column'], 0)
                    self.assertLessEqual(len(d['source_excerpt'].encode()), 192)
                    self.assertTrue(d['rule'] and d['alternative'])

    def test_historical_partial_repair_and_format_rejection_through_scheduler(self):
        original = self.saved_responses()
        before = receipt_hashes(SAVED_PILOT)
        # Two explicit fixture abstentions exercise the remaining slots newly
        # reachable in replay. The seven archived replies are replayed unchanged.
        replies = [*original[0],response(ABSTAIN),*original[1],response(ABSTAIN),*original[2]]
        captured = []

        def sender(wire):
            captured.append(deepcopy(wire))
            return replies[len(captured)-1]

        with (
            private_output('saved_static_pilot') as output,
            patch.object(experiment, 'validate_source', side_effect=AssertionError('rejected source executed')),
        ):
            result = experiment.run(BASE, output, sender=sender)
            self.assertEqual(result['paid_requests'], 0)
            self.assertEqual(result['budget']['tool_calls'], 0)
            self.assertEqual([packet(wire)['stage'] for wire in captured], ['initial','revision_01','revision_02']*3)
            container, lamp, navigation = [group['attempts'] for group in result['candidates']]
            reduction = container[1]['revision_progress']
            self.assertEqual((reduction['status'], reduction['before_count'], reduction['after_count']),
                             ('ERRORS_REDUCED',2,1))
            self.assertEqual(container[1]['disposition'], 'REVISION_SCHEDULED')
            self.assertEqual(len(packet(captured[2])['diagnostics']['static']['violations']), 1)
            changed = lamp[1]['revision_progress']
            self.assertEqual((changed['status'], changed['before_count'], changed['after_count']),
                             ('ERRORS_CHANGED',3,3))
            self.assertFalse(lamp[1]['static']['passed'])
            self.assertEqual(navigation[1]['delivery']['status'], 'SCHEMA_REJECTED')
            self.assertEqual(navigation[1]['static']['status'], 'NOT_CHECKED')
            self.assertFalse((output/'candidate_2/revision_01/decoded.py').exists())
            nav = packet(captured[8])
            self.assertEqual(nav['previous_code'], navigation[0]['delivery']['proposal']['code'])
            self.assertEqual(nav['revision_context']['last_valid_version'], navigation[0]['version'])
            self.assertEqual(nav['revision_context']['remaining_after_revision'], 0)
            self.assertEqual(nav['latest_rejected_response']['response_sha256'], fingerprint(original[2][1]))
            self.assertEqual(nav['latest_rejected_response']['projection'], 'ARCHIVE_REFERENCE_ONLY')
            self.assertEqual(nav['diagnostics']['schema']['errors'][0]['detail'], 'EXTRA_DATA_AFTER_JSON')
            self.assertEqual([row['line'] for row in nav['diagnostics']['static']['violations']], [3,4])
            self.assertEqual(navigation[2]['parent_version'], navigation[1]['version'])
            self.assertEqual(navigation[2]['disposition'], 'REVISION_LIMIT_REACHED')
            raw = [row['payload']['response'] for row in EvidenceStore(output/'provider.jsonl').records()
                   if row['kind']=='RAW_RESPONSE']
            self.assertEqual(raw, replies)
            save(output/'captured_wires.private.json', captured)
            self.assertEqual(experiment.run(BASE, output, sender=sender), result)
            self.assertEqual(len(captured), 9)
        self.assertEqual(receipt_hashes(SAVED_PILOT), before)

    def test_line_shifts_and_comments_do_not_create_new_static_evidence(self):
        code = (SAVED_PILOT/'candidate_0/initial/decoded.py').read_text()
        replies = [response(proposal(code)),response(proposal('\n# layout only\n'+code)),
                   response(ABSTAIN),response(ABSTAIN)]
        captured = []

        def sender(wire):
            captured.append(deepcopy(wire))
            return replies[len(captured)-1]

        with private_output('static_layout_only') as output:
            result = experiment.run(BASE, output, sender=sender)
            revised = result['candidates'][0]['attempts'][1]
            self.assertEqual(revised['revision_progress']['status'], 'ERRORS_UNCHANGED')
            self.assertTrue(revised['revision_progress']['source_changed'])
            self.assertTrue(revised['revision_progress']['node_locations_changed'])
            self.assertFalse(revised['revision_progress']['node_structures_changed'])
            self.assertEqual(revised['disposition'], 'NO_NEW_DIAGNOSTIC')
            self.assertEqual([packet(wire)['stage'] for wire in captured],
                             ['initial','revision_01','initial','initial'])


class SourceFeedbackIntegrationTest(unittest.TestCase):
    def test_real_sources_worker_feedback_revision_and_recovery(self):
        captured = []
        calls_by_stage = defaultdict(list)
        execution_contexts = defaultdict(list)
        program_by_group = (CONTAINER_INITIAL, LAMP_FIXTURE, NAVIGATION_FIXTURE)
        groups = ('container_precondition', 'lamp_interaction', 'navigation_no_effect')
        current_group = -1
        model_stage = None

        def sender(wire):
            nonlocal current_group, model_stage
            captured.append(deepcopy(wire))
            value = packet(wire)
            model_stage = value['stage']
            self.assertEqual(wire['messages'][0]['content'],
                             INITIAL_PROMPT if model_stage=='initial' else REVISION_PROMPT)
            if model_stage=='initial':
                current_group += 1
                self.assertNotIn('source_feedback', value)
                code = program_by_group[current_group]
            elif current_group==0:
                self.assertIn(value['previous_code'], (CONTAINER_INITIAL, CONTAINER_REVISED))
                code = CONTAINER_REVISED
            else:
                code = program_by_group[current_group]
            calls_by_stage[groups[current_group]].append((model_stage, value, code))
            return response(proposal(code))

        original_runner = EnvironmentPolicyRunner.run

        def tracked_worker(runner, card, context):
            path = Path(card.artifact_path)
            self.assertEqual(sha(path), card.artifact_sha256)
            context_hash = fingerprint(context)
            self.assertEqual(set(context), {'goal','observation','admissible_commands','history','state'})
            self.assertTrue(all(set(row)=={'action','observation'} for row in context['history']))
            result = original_runner(runner, card, context)
            execution_contexts[card.artifact_sha256].append((context_hash, deepcopy(context), deepcopy(result)))
            return result

        def interrupt_at(target):
            def interrupt(point, payload):
                if point==target:
                    raise InterruptedError(f'MOCK interrupted at {target}')
            return interrupt

        with private_output('real_sources', mounted=True) as output, patch.object(EnvironmentPolicyRunner,'run',tracked_worker):
            with self.assertRaisesRegex(InterruptedError, 'after_response'):
                experiment.run(BASE, output, sender=sender, fault=interrupt_at('after_response'))
            self.assertEqual([packet(wire)['stage'] for wire in captured], ['initial'])
            with self.assertRaisesRegex(InterruptedError, 'after_action'):
                experiment.run(BASE, output, sender=sender, fault=interrupt_at('after_action'))
            self.assertEqual([packet(wire)['stage'] for wire in captured], ['initial'])
            first_worker = [row for row in EvidenceStore(output/'worker.jsonl').records()
                            if row['kind']=='ENVIRONMENT_POLICY_EXECUTED']
            self.assertEqual(len(first_worker), 1)
            with self.assertRaisesRegex(InterruptedError, 'after_source'):
                experiment.run(BASE, output, sender=sender, fault=interrupt_at('after_source'))
            self.assertEqual([packet(wire)['stage'] for wire in captured], ['initial'])

            result = experiment.run(BASE, output, sender=sender)
            self.assertEqual(result['paid_requests'], 0)
            self.assertEqual(result['independent_gate_games'], 0)
            self.assertEqual(current_group, 2)
            self.assertEqual([candidate['group'] for candidate in result['candidates']], list(groups))
            container, lamp, navigation = result['candidates']
            initial, revised = container['attempts'][:2]
            self.assertEqual(revised['parent_version'], initial['version'])
            self.assertNotEqual(revised['code_sha256'], initial['code_sha256'])
            self.assertEqual(initial['sources'][0]['start_sha256'], revised['sources'][0]['start_sha256'])
            self.assertFalse(initial['sources'][0]['local_repair_verified'])
            self.assertTrue(revised['sources'][0]['local_repair_verified'])
            self.assertTrue(revised['sources'][0]['recovery_completed'])
            self.assertTrue(revised['sources'][0]['won'])
            self.assertEqual([len(row['attempts'][0]['sources']) for row in (container,lamp,navigation)], [11,3,9])
            navigation_initial, navigation_unchanged = navigation['attempts'][:2]
            self.assertEqual(navigation_initial['evaluation_id'], navigation_unchanged['evaluation_id'])
            self.assertEqual(navigation_initial['code_sha256'], navigation_unchanged['code_sha256'])
            self.assertTrue(any(row['outcome']=='PROGRESS_UNVERIFIED' and not row['won']
                                for row in navigation_initial['sources']))
            self.assertTrue(any(row['stop']=='CANDIDATE_ERROR' and not row['actions']
                                for row in navigation_initial['sources']))
            all_attempts = [attempt for candidate in result['candidates'] for attempt in candidate['attempts']]
            self.assertEqual({attempt['wire_sha256'] for attempt in all_attempts},
                             {fingerprint(wire) for wire in captured})
            for index, candidate in enumerate(result['candidates']):
                for attempt in candidate['attempts']:
                    if attempt['registration']['status']!='SHADOW':
                        continue
                    decoded = output/f'candidate_{index}'/attempt['stage']/'decoded.py'
                    registered = Path(attempt['registration']['card']['artifact_path'])
                    self.assertEqual(decoded.read_bytes(), registered.read_bytes())
                    self.assertEqual(sha(decoded), attempt['code_sha256'])
            first_revision = calls_by_stage[groups[0]][1]
            self.assertEqual(first_revision[0], 'revision_01')
            self.assertEqual(first_revision[1]['previous_code'], CONTAINER_INITIAL)
            initial_contexts = execution_contexts[hashlib.sha256(CONTAINER_INITIAL.encode()).hexdigest()]
            revised_contexts = execution_contexts[hashlib.sha256(CONTAINER_REVISED.encode()).hexdigest()]
            lamp_contexts = execution_contexts[hashlib.sha256(LAMP_FIXTURE.encode()).hexdigest()]
            navigation_contexts = execution_contexts[hashlib.sha256(NAVIGATION_FIXTURE.encode()).hexdigest()]
            # Both versions receive the original post-failure state, independently of the earlier look.
            self.assertEqual(initial_contexts[0][0], revised_contexts[0][0])
            self.assertEqual(revised_contexts[0][1]['state'], {})
            self.assertEqual(revised_contexts[0][1]['history'][-1]['observation'], 'Nothing happens.')
            subsequent = revised_contexts[1][1]
            self.assertTrue(subsequent['observation'].startswith('You open the '))
            self.assertIn(subsequent['state']['placement'], subsequent['admissible_commands'])
            self.assertEqual(subsequent['history'][-1]['observation'], subsequent['observation'])
            self.assertTrue(any(context['state']=={} and context_hash!=revised_contexts[0][0]
                                and context['history'][-1]['observation']=='Nothing happens.'
                                for context_hash,context,_ in revised_contexts))
            self.assertTrue(any(row[2].get('action','').startswith('use ') for row in lamp_contexts))
            self.assertTrue(any(row[2].get('action','').startswith('go to ') for row in navigation_contexts))
            self.assertTrue(any(row[2]['status']=='declined' and row[1]['state']=={'tried':True}
                                for row in navigation_contexts))

            public = first_revision[1]['source_feedback']
            first_look = next(step for step in public[0]['steps'] if step.get('action')=='look')
            looked = next(context['observation'] for _,context,_ in initial_contexts if context['state']=={'looked':True})
            self.assertEqual(first_look['observation'], looked)
            self.assertTrue(any(step.get('worker_status')=='RUNTIME_ERROR' for step in public[0]['steps']))
            for wire in captured:
                payload = packet(wire)
                text = canonical(payload)
                for field in ('local_witness', 'expected_action', 'probe_location', 'gate', 'boundary_expected',
                              'worker_script', 'source_receipt_sha256'):
                    self.assertNotIn(f'"{field}"', text)
                self.assertNotIn(str(BASE), text)
                self.assertNotIn('/candidate.py', text)

            records = [row['payload'] for row in EvidenceStore(output/'worker.jsonl').records()
                       if row['kind']=='ENVIRONMENT_POLICY_EXECUTED']
            self.assertEqual(len({row['execution_id'] for row in records}), len(records))
            self.assertEqual(sum(row['execution_id']==first_worker[0]['payload']['execution_id']
                                 for row in records), 1)
            self.assertEqual({row['artifact_sha256'] for row in records}, set(execution_contexts))
            self.assertEqual(result['budget']['tool_calls'], len(records))
            registry = EvidenceStore(output/'registry.jsonl').records()
            self.assertTrue(registry)
            self.assertEqual({row['kind'] for row in registry}, {'SHADOW_REGISTERED'})
            self.assertFalse((output/'authorization.json').exists())
            self.assertFalse((output/'authorization.template.json').exists())
            self.assertTrue(any(stage=='revision_01' for stage,_,_ in calls_by_stage[groups[2]]))
            save(output/'mock_requests.private.json', captured)
            saved_hashes = receipt_hashes(output)
            sent = len(captured)
            self.assertEqual(experiment.run(BASE, output, sender=sender), result)
            self.assertEqual(len(captured), sent)
            self.assertEqual(receipt_hashes(output), saved_hashes)


if __name__ == '__main__':
    unittest.main()
