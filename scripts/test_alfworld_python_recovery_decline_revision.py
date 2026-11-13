"""Zero-API checks of public feedback provenance and the one-request entry."""

from copy import deepcopy
import json
import unittest

from alfworld_.failure_learning import context_view
from alfworld_.recovery_execution_feedback import with_decline_context
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read
from failure_evo.network_transport import SendUnknown
from failure_evo.run_health import RunUnhealthy
import run_alfworld_python_recovery_decline_revision as trial
from test_alfworld_python_recovery_feedback import (
    ABSTAIN, BASE, private_output, real_entry_fixture_transport, receipt_hashes,
)
from test_alfworld_skill_acquisition import response
from test_network_recovery import Connection


class DeclineRevisionTest(unittest.TestCase):
    def test_actual_archive_enrichment_preserves_original_packet(self):
        with private_output('decline_projection') as output:
            plan, packet, *_, baseline = trial.configuration(BASE, trial.PARENT, output.resolve())
        self.assertEqual(plan['max_calls'], 1)
        self.assertEqual(plan['packet_sha256'], fingerprint(packet))
        self.assertEqual(packet['previous_code'], baseline['delivery']['proposal']['code'])
        entries = packet['source_feedback']
        self.assertEqual(len(entries), 11)
        for source, archived in zip(entries,baseline['sources'],strict=True):
            step, = source['steps']
            context = step['public_context_at_decline']
            self.assertTrue(context['admissible_commands'])
            self.assertEqual(context['original_failure'],context['latest_observed_transition'])
            self.assertFalse(step['executed'])
            self.assertFalse(step['candidate_action_returned'])
            self.assertEqual(step['candidate_self_report'],
                             dict(origin='CANDIDATE_OUTPUT',environment_fact=False,
                                  reason=archived['decisions'][0]['operator']['reason']))
        for field in ('local_witness','expected','expert_plan','artifact_path','boundary_evaluation'):
            self.assertNotIn(f'"{field}"',canonical(packet))
        previous = [row['payload']['wire'] for row in EvidenceStore(trial.PARENT/'provider.jsonl').records()
                    if row['kind']=='SEND_STARTED'][-1]
        old = deepcopy(packet)
        for source in old['source_feedback']:
            for step in source['steps']:
                for field in ('executed','candidate_action_returned','candidate_self_report','public_context_at_decline'):
                    del step[field]
        self.assertEqual(old,json.loads(previous['messages'][-1]['content']))

    def test_executed_transition_and_later_decline_use_distinct_public_states(self):
        with private_output('decline_timing') as output:
            _, packet, *_, original = trial.configuration(BASE,trial.PARENT,output.resolve())
        baseline = deepcopy(original)
        learning = deepcopy(packet['original_learning_input'])
        learning['public_traces'] = learning['public_traces'][:1]
        prefix = [dict(action='go to site', observation='Nothing happens.')]
        goal = 'inspect a device'
        first = context_view(goal,'Nothing happens.',['go to hall'],prefix,{})
        observation = dict(action='go to hall',observation='You arrive at the hall.',done=False,won=False,
                           commands=['look','go to site'])
        state = {'visited':'hall'}
        next_context = context_view(goal,observation['observation'],observation['commands'],
                                    prefix+[observation],state)
        baseline['sources'] = [dict(source_ref='source_1',start_sha256='start',stop='DECLINED',won=False,
            decisions=[
                dict(operator=dict(status='applied',action='go to hall',state=state), worker_status='OK',
                     selected_action='go to hall',receipt=observation,context_sha256=fingerprint(first)),
                dict(operator=dict(status='declined',reason='only public observations are known'),worker_status='OK',
                     selected_action=None,receipt=None,context_sha256=fingerprint(next_context)),
            ])]
        starts = {'source_1':(prefix,first,'start')}
        revised = with_decline_context(learning,baseline,starts,stage=trial.STAGE)
        applied, declined = revised['source_feedback'][0]['steps']
        self.assertTrue(applied['executed'])
        self.assertEqual(applied['action'],'go to hall')
        self.assertFalse(declined['executed'])
        context = declined['public_context_at_decline']
        self.assertEqual(context['admissible_commands'], ['look','go to site'])
        self.assertEqual(context['latest_observed_transition']['action'], 'go to hall')
        self.assertEqual(context['original_failure']['action'], 'go to site')
        self.assertNotIn('state',context)
        baseline['sources'][0]['decisions'][1]['context_sha256'] = fingerprint(first)
        with self.assertRaisesRegex(PermissionError,'public context differs'):
            with_decline_context(learning,baseline,starts,stage=trial.STAGE)

    def test_one_request_and_safe_resume(self):
        with (
            private_output('one_revision_offline') as output,
            real_entry_fixture_transport([Connection(value=response(ABSTAIN))]) as (wires,offline),
        ):
            output = output.resolve()
            plan = trial.prepare(BASE,trial.PARENT,output)
            grant = trial.pilot.authorization_for(plan)
            with self.assertRaises(PermissionError):
                trial.run(BASE,trial.PARENT,output,authorization=read(output/'authorization.template.json'))
            self.assertFalse(wires)
            result = trial.run(BASE,trial.PARENT,output,authorization=grant)
            self.assertEqual(result['attempt']['disposition'],'ABSTAIN')
            self.assertEqual(result['paired_source_comparison']['status'],'NOT_REACHED')
            self.assertEqual(result['budget']['calls'],1)
            self.assertEqual(result['budget']['tool_calls'],0)
            self.assertEqual(fingerprint(wires[0]),plan['wire_sha256'])
            hashes = receipt_hashes(output)
            self.assertEqual(trial.run(BASE,trial.PARENT,output,authorization=grant,resume=True),result)
            self.assertEqual(receipt_hashes(output),hashes)
            self.assertEqual((len(wires),offline.call_count),(1,1))

    def test_unknown_send_remains_blocked(self):
        with (
            private_output('one_revision_unknown') as output,
            real_entry_fixture_transport([Connection(read_error=TimeoutError('OFFLINE'))]) as (wires,offline),
        ):
            output = output.resolve()
            plan = trial.prepare(BASE,trial.PARENT,output)
            grant = trial.pilot.authorization_for(plan)
            with self.assertRaises(SendUnknown):
                trial.run(BASE,trial.PARENT,output,authorization=grant)
            hashes = receipt_hashes(output)
            with self.assertRaises(RunUnhealthy):
                trial.run(BASE,trial.PARENT,output,authorization=grant,resume=True)
            self.assertEqual(receipt_hashes(output),hashes)
            self.assertEqual((len(wires),offline.call_count),(1,1))


if __name__=='__main__':
    unittest.main()
