"""Zero-API acceptance of the container-only Pilot with archived and Mock replies."""

from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from alfworld_.failure_learning import EnvironmentPolicyRunner
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, save, sha
from failure_evo.network_transport import SendUnknown
from failure_evo.run_health import RunUnhealthy
import run_alfworld_python_recovery_feedback as pilot
from test_alfworld_python_recovery_feedback import (
    ABSTAIN, BASE, CONTAINER_INITIAL, CONTAINER_REVISED, SAVED_PILOT,
    packet, private_output, proposal, real_entry_fixture_transport, receipt_hashes,
)
from test_alfworld_skill_acquisition import response
from test_network_recovery import Connection


def archived_container():
    original = read(SAVED_PILOT/'result.json')
    group, = [row for row in original['candidates'] if row['group']==pilot.CONTAINER_GROUP]
    raw = {row['payload']['sha256']:row['payload']['response']
           for row in EvidenceStore(SAVED_PILOT/'provider.jsonl').records() if row['kind']=='RAW_RESPONSE'}
    return [raw[attempt['response_sha256']] for attempt in group['attempts']]


def payloads(path, kind):
    return [row['payload'] for row in EvidenceStore(path).records() if row['kind']==kind]


class ContainerScopeTest(unittest.TestCase):
    def test_scope_identity_and_budget_preserve_legacy_schedule(self):
        with private_output('container_scope') as output:
            legacy, _, legacy_events, _, legacy_schedule, legacy_boundaries, _ = pilot.configuration(
                BASE, output, real=True)
            plan, _, events, host, schedule, boundaries, _ = pilot.configuration(
                BASE, output, real=True, container_only=True)
        self.assertEqual(legacy['version'], pilot.VERSION)
        self.assertEqual([row['group'] for row in legacy['schedule']],
                         ['container_precondition','lamp_interaction','navigation_no_effect'])
        self.assertEqual((len(legacy_events),legacy['max_calls'],legacy['max_cost_microusd']), (28,9,600000))
        self.assertEqual(legacy['environment_steps'], 3450)
        self.assertEqual(plan['version'], pilot.CONTAINER_VERSION)
        self.assertEqual(schedule, pilot.container_schedule(list(reversed(legacy_schedule))))
        entry, = plan['schedule']
        historical, = [row for row in read(SAVED_PILOT/'protocol.json')['schedule']
                       if row['group']==pilot.CONTAINER_GROUP]
        self.assertEqual(entry['sources'], historical['sources'])
        self.assertEqual(entry['wire_sha256'], historical['wire_sha256'])
        self.assertEqual([row['sequence'] for row in entry['sources']], list(pilot.CONTAINER_SEQUENCES))
        self.assertEqual({event['evidence_id'] for event in events}, set(host))
        self.assertEqual(len(host), 11)
        self.assertEqual(boundaries, legacy_boundaries)
        self.assertEqual(len(boundaries), 21)
        self.assertEqual(plan['input_bounds'], [22240,65536,65536])
        self.assertEqual((plan['max_calls'],plan['max_tokens']), (3,165600))
        self.assertEqual((plan['conservative_cost_upper_microusd'],plan['max_cost_microusd']), (198722,200000))
        self.assertEqual((plan['worker_calls'],plan['worker_milliseconds_total']), (570,8550000))
        self.assertEqual((plan['initial_prefix_steps'],plan['source_action_slots']), (225,507))
        self.assertEqual((plan['uninterrupted_environment_steps'],plan['recovery_environment_steps'],
                          plan['environment_steps']), (1182,468,1650))
        changed = deepcopy(schedule)
        changed[0][1][0]['anchor']+=1
        for invalid in (changed, [], schedule*2):
            with self.subTest(count=len(invalid)), self.assertRaises(PermissionError):
                pilot.container_schedule(invalid)
        with self.assertRaisesRegex(PermissionError, 'new run directory'):
            pilot.configuration(BASE, SAVED_PILOT, container_only=True)

    def test_archived_partial_static_repair_uses_remaining_slot(self):
        archived = archived_container()
        captured = []
        replies = [*archived,response(ABSTAIN)]

        def sender(wire):
            captured.append(wire)
            return replies[len(captured)-1]

        with (
            private_output('container_historical_static') as output,
            patch.object(pilot, 'validate_source', side_effect=AssertionError('rejected source executed')),
        ):
            result = pilot.run(BASE, output, sender=sender, container_only=True)
            self.assertEqual([packet(body)['stage'] for body in captured], ['initial','revision_01','revision_02'])
            self.assertEqual([row['response'] for row in payloads(output/'provider.jsonl','RAW_RESPONSE')], replies)
            self.assertEqual(len(read(output/'evidence_binding.json')['ids']), 11)
            group, = result['candidates']
            initial, revision, final = group['attempts']
            self.assertEqual(group['group'], pilot.CONTAINER_GROUP)
            self.assertEqual([a['static']['status'] for a in (initial,revision)], ['REJECTED','REJECTED'])
            self.assertEqual([(item['line'],item['column']) for item in packet(captured[1])['diagnostics']['static']['violations']],
                             [(3,12),(4,12)])
            pending, = packet(captured[2])['diagnostics']['static']['violations']
            self.assertEqual((pending['line'],pending['column']), (3,12))
            self.assertEqual(packet(captured[2])['previous_code'], revision['delivery']['proposal']['code'])
            change = revision['revision_progress']
            self.assertEqual((change['status'],change['before_count'],change['after_count']), ('ERRORS_REDUCED',2,1))
            self.assertEqual((change['removed_count'],change['introduced_count']), (1,0))
            self.assertEqual(change['removed_nodes'][0]['node_sha256'],
                             initial['static']['diagnostics'][1]['node_sha256'])
            self.assertEqual(change['introduced_nodes'], [])
            self.assertEqual(revision['remaining_revisions'], 1)
            self.assertEqual(revision['disposition'], 'REVISION_SCHEDULED')
            self.assertEqual(final['disposition'], 'ABSTAIN')
            self.assertEqual((result['budget']['calls'],result['budget']['tool_calls'],result['paid_requests']), (3,0,0))
            self.assertEqual(result['milestones'], dict(first_static_pass=None, first_source_worker=None,
                first_source_action=None, feedback_revision_comparisons=[]))
            save(output/'captured_wires.private.json', captured)

    def test_format_rejection_preserves_last_formally_decoded_source(self):
        original = archived_container()[0]
        invalid = deepcopy(original)
        invalid['choices'][0]['message']['content']+='\nEXTRA OFFLINE TEXT'
        replies = iter([original,invalid,response(ABSTAIN)])
        wires = []

        def sender(wire):
            wires.append(wire)
            return next(replies)

        with private_output('container_bad_format') as output:
            result = pilot.run(BASE, output, sender=sender, container_only=True)
            first, rejected, _ = result['candidates'][0]['attempts']
            revision = packet(wires[-1])
            self.assertEqual(rejected['delivery']['status'], 'SCHEMA_REJECTED')
            self.assertFalse((output/'candidate_0/revision_01/decoded.py').exists())
            self.assertEqual(revision['previous_code'], first['delivery']['proposal']['code'])
            self.assertEqual(revision['diagnostics']['schema']['errors'][0]['detail'], 'EXTRA_DATA_AFTER_JSON')
            self.assertEqual(len(revision['diagnostics']['static']['violations']), 2)
            self.assertEqual(revision['latest_rejected_response']['response_sha256'], fingerprint(invalid))
            self.assertNotIn('EXTRA OFFLINE TEXT', canonical(revision))

    def test_truncated_response_stops_without_static_or_environment_execution(self):
        reply = response(proposal(CONTAINER_REVISED))
        reply['choices'][0]['finish_reason'] = 'length'
        captured = []

        def sender(wire):
            captured.append(wire)
            return reply

        with private_output('container_truncated') as output:
            result = pilot.run(BASE, output, sender=sender, container_only=True)
            attempt, = result['candidates'][0]['attempts']
            self.assertEqual(attempt['provider_finish_reason'], 'length')
            self.assertEqual(attempt['disposition'], 'DELIVERY_INCOMPLETE')
            self.assertEqual(attempt['static']['status'], 'NOT_CHECKED')
            self.assertEqual(attempt['metrics']['source_outcomes']['NOT_REACHED'], 11)
            self.assertEqual(len(captured), 1)
            self.assertEqual(result['budget']['tool_calls'], 0)


class ContainerRecoveryTest(unittest.TestCase):
    def test_authorization_binding_and_completed_response_resume(self):
        def interrupt(point, _):
            if point=='after_response':
                raise InterruptedError('OFFLINE after response commit')

        with (
            private_output('container_real_resume') as output,
            real_entry_fixture_transport([Connection(value=response(ABSTAIN))]) as (wires, offline),
        ):
            plan = pilot.prepare(BASE, output, container_only=True)
            grant = pilot.authorization_for(plan)
            template = read(output/'authorization.template.json')
            self.assertIs(template['paid_api_authorized'], False)
            self.assertEqual(pilot.preflight(BASE, output, container_only=True)['status'],
                             'READY_PENDING_EXPLICIT_AUTHORIZATION')
            for invalid in (None, template, dict(grant, max_cost_microusd=600000),
                            dict(grant, protocol_hash='0'*64),dict(grant, protocol=pilot.VERSION)):
                with self.subTest(grant=invalid), self.assertRaises(PermissionError):
                    pilot.run(BASE, output, authorization=invalid, container_only=True)
            with self.assertRaises(PermissionError):
                pilot.run(BASE, output, authorization=grant)
            self.assertFalse(wires)
            self.assertFalse((output/'budget.jsonl').exists())
            with self.assertRaisesRegex(InterruptedError, 'after response commit'):
                pilot.run(BASE, output, authorization=grant, fault=interrupt, container_only=True)
            ledger = sha(output/'budget.jsonl')
            result = pilot.run(BASE, output, authorization=grant, resume=True, container_only=True)
            self.assertEqual((len(wires),offline.call_count,result['budget']['calls']), (1,1,1))
            self.assertEqual(fingerprint(wires[0]), plan['schedule'][0]['wire_sha256'])
            self.assertEqual(ledger, sha(output/'budget.jsonl'))
            self.assertEqual(pilot.run(BASE, output, authorization=grant, resume=True, container_only=True), result)
            self.assertEqual(len(wires), 1)

    def test_send_unknown_preserves_reservation_and_blocks_resume(self):
        with (
            private_output('container_send_unknown') as output,
            real_entry_fixture_transport([Connection(read_error=TimeoutError('OFFLINE lost after POST'))])
                as (wires, offline),
        ):
            plan = pilot.prepare(BASE, output, container_only=True)
            grant = pilot.authorization_for(plan)
            with self.assertRaises(SendUnknown):
                pilot.run(BASE, output, authorization=grant, container_only=True)
            hashes = receipt_hashes(output)
            self.assertEqual(len(payloads(output/'provider.jsonl','SEND_UNKNOWN')), 1)
            self.assertFalse(payloads(output/'provider.jsonl','RAW_RESPONSE'))
            with self.assertRaises(RunUnhealthy):
                pilot.run(BASE, output, authorization=grant, resume=True, container_only=True)
            self.assertEqual((len(wires),offline.call_count), (1,1))
            self.assertEqual(receipt_hashes(output), hashes)

    def test_protocol_and_code_drift_are_blocked(self):
        with private_output('container_frozen_binding') as output:
            plan, *_ = pilot.configuration(BASE, output, container_only=True)
            output.mkdir(mode=0o700)
            save(output/'protocol.json', plan)
            pilot.verify_container_freeze(output, plan)
            source = pilot.ROOT/'scripts/run_alfworld_python_recovery_container_pilot.py'
            original_sha = pilot.sha

            def different_sha(path):
                return '0'*64 if path==source else original_sha(path)

            with patch.object(pilot,'sha',side_effect=different_sha), self.assertRaises(RunUnhealthy):
                pilot.verify_container_freeze(output, plan)

            calls = []

            def sender(wire):
                calls.append(wire)
                save(output/'protocol.json',dict(plan, revision_limit=1))
                return response(proposal(CONTAINER_INITIAL))

            with self.assertRaisesRegex(RunUnhealthy, 'protocol or code changed'):
                pilot.run(BASE, output, sender=sender, container_only=True)
            with self.assertRaisesRegex(PermissionError, 'committed receipt differs'):
                pilot.run(BASE, output, sender=sender, container_only=True)
            self.assertEqual(len(calls), 1)
            self.assertFalse((output/'worker.jsonl').exists())

    def test_worker_fault_stops_without_candidate_feedback_or_more_requests(self):
        calls = []

        def sender(wire):
            calls.append(wire)
            return response(proposal(CONTAINER_INITIAL))

        with (
            private_output('container_worker_fault') as output,
            patch.object(pilot.PREVIOUS.FrozenLinuxBackend, '__call__',
                         side_effect=RunUnhealthy('OFFLINE Worker infrastructure unavailable')),
        ):
            with self.assertRaisesRegex(RunUnhealthy, 'Worker infrastructure'):
                pilot.run(BASE, output, sender=sender, container_only=True)
            self.assertEqual(len(payloads(output/'worker.jsonl','ENVIRONMENT_POLICY_STARTED')), 1)
            self.assertFalse(payloads(output/'worker.jsonl','ENVIRONMENT_POLICY_EXECUTED'))
            self.assertFalse((output/'candidate_0/initial/attempt.json').exists())
            ledger = sha(output/'budget.jsonl')
            with self.assertRaisesRegex(RunUnhealthy, 'Worker execution unresolved'):
                pilot.run(BASE, output, sender=sender, container_only=True)
            self.assertEqual(len(calls), 1)
            self.assertEqual(ledger, sha(output/'budget.jsonl'))

    def test_worker_textworld_and_same_state_feedback_revision(self):
        wires = []
        inputs = {}
        source_wires = [CONTAINER_INITIAL,CONTAINER_REVISED]

        def sender(wire):
            self.assertFalse(list(output.glob('candidate_*/*/boundaries.private.json')))
            wires.append(wire)
            return response(proposal(source_wires[len(wires)-1]))

        def interrupt(point, _):
            if point=='after_action':
                raise InterruptedError('MOCK committed environment action')

        original_runner = EnvironmentPolicyRunner.run

        def track(runner, card, context):
            self.assertEqual(sha(card.artifact_path), card.artifact_sha256)
            self.assertEqual(set(context), {'goal','observation','admissible_commands','history','state'})
            self.assertTrue(all(set(step)=={'action','observation'} for step in context['history']))
            inputs[fingerprint([card.version, context])]=deepcopy(context)
            return original_runner(runner, card, context)

        with (
            private_output('container_source_replay', mounted=True) as output,
            patch.object(EnvironmentPolicyRunner, 'run', track),
        ):
            with self.assertRaisesRegex(InterruptedError, 'committed environment action'):
                pilot.run(BASE, output, sender=sender, fault=interrupt, container_only=True)
            first_worker, = payloads(output/'worker.jsonl','ENVIRONMENT_POLICY_EXECUTED')
            self.assertEqual(len(wires), 1)
            result = pilot.run(BASE, output, sender=sender, container_only=True)
            plan = read(output/'protocol.json')
            self.assertEqual((result['paid_requests'],result['independent_gate_games']), (0,0))
            self.assertEqual([packet(wire)['stage'] for wire in wires], ['initial','revision_01'])
            candidate, = result['candidates']
            initial, revised = candidate['attempts']
            self.assertEqual(candidate['disposition'], 'SOURCE_RECOVERY_COMPLETE')
            self.assertEqual(revised['parent_version'], initial['version'])
            self.assertNotEqual(revised['code_sha256'], initial['code_sha256'])
            self.assertEqual([row['start_sha256'] for row in initial['sources']],
                             [row['start_sha256'] for row in revised['sources']])
            self.assertEqual((initial['metrics']['first_action_executed'],initial['metrics']['local_repair_verified']), (11,0))
            self.assertEqual((revised['metrics']['local_repair_verified'],revised['metrics']['won']), (11,11))
            self.assertEqual([a['boundary_evaluation']['cases'] for a in (initial,revised)], [21,21])
            revision = packet(wires[1])
            self.assertEqual(revision['previous_code'], CONTAINER_INITIAL)
            self.assertEqual(len(revision['source_feedback']), 11)
            observed = initial['sources'][0]['actions'][0]
            self.assertEqual(revision['source_feedback'][0]['steps'][0]['action'], observed['action'])
            self.assertEqual(revision['source_feedback'][0]['steps'][0]['observation'], observed['observation'])
            self.assertEqual(revision['source_feedback'][0]['steps'][1]['candidate_error']['exception'], 'ValueError')
            for wire in wires:
                text = canonical(packet(wire))
                for field in ('local_witness','expected_action','gate','boundaries','source_receipt','probe_location'):
                    self.assertNotIn(f'"{field}"', text)
                self.assertNotIn(str(BASE), text)
            anchors = {row['sequence']:row['anchor'] for row in plan['schedule'][0]['sources']}
            for attempt in (initial,revised):
                card = attempt['registration']['card']
                decoded = output/'candidate_0'/attempt['stage']/'decoded.py'
                self.assertEqual(sha(decoded), sha(card['artifact_path']))
                for case in attempt['sources']:
                    limit = min(plan['source_window'],plan['episode_limit']-anchors[case['sequence']])
                    self.assertLessEqual(len(case['actions']), limit)
                    self.assertTrue(all(row['artifact_sha256']==attempt['code_sha256'] for row in case['decisions']))
            card = revised['registration']['card']
            first, second = revised['sources'][0]['decisions']
            first_context = next(ctx for ctx in inputs.values() if fingerprint(ctx)==first['context_sha256'])
            next_context = next(ctx for ctx in inputs.values() if fingerprint(ctx)==second['context_sha256'])
            self.assertEqual(first_context['state'], {})
            self.assertEqual(first_context['observation'], 'Nothing happens.')
            self.assertEqual(next_context['observation'], first['receipt']['observation'])
            self.assertIn(next_context['state']['placement'], next_context['admissible_commands'])
            workers = payloads(output/'worker.jsonl','ENVIRONMENT_POLICY_EXECUTED')
            self.assertEqual(sum(row['execution_id']==first_worker['execution_id'] for row in workers), 1)
            self.assertEqual(len({row['execution_id'] for row in workers}), len(workers))
            self.assertEqual({row['artifact_sha256'] for row in workers},
                             {initial['code_sha256'],card['artifact_sha256']})
            self.assertEqual(result['budget']['tool_calls'], len(workers))
            self.assertEqual(result['resources']['environment']['resume_candidate'], 1)
            self.assertEqual({row['kind'] for row in EvidenceStore(output/'registry.jsonl').records()},
                             {'SHADOW_REGISTERED'})
            milestones = result['milestones']
            for key in ('first_static_pass','first_source_worker','first_source_action'):
                self.assertEqual(milestones[key]['version'], initial['version'])
            comparison, = milestones['feedback_revision_comparisons']
            self.assertEqual(comparison['status'], 'PAIRED')
            self.assertEqual(comparison['metrics']['local_repair_verified'],
                             dict(improved=list(pilot.CONTAINER_SEQUENCES), regressed=[]))
            save(output/'mock_wires.private.json', wires)
            hashes = receipt_hashes(output)
            self.assertEqual(pilot.run(BASE, output, sender=sender, container_only=True), result)
            self.assertEqual(len(wires), 2)
            self.assertEqual(receipt_hashes(output), hashes)


if __name__ == '__main__':
    unittest.main()
