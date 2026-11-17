"""Offline tests of the applicability-only Pilot and its evidence boundary."""

import json
import shutil
import unittest
from unittest.mock import patch

from alfworld_.failure_learning import static_check_detailed
from alfworld_.recovery_applicability import worker_artifact
from alfworld_.recovery_applicability_rule import check_rule
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, sha
from failure_evo.network_transport import SendUnknown
from failure_evo.run_health import RunUnhealthy
from prepare_alfworld_applicability_data import EVAL_FILE, evidence_categories
import run_alfworld_applicability_pilot as study
from test_alfworld_python_recovery_feedback import (
    ABSTAIN, private_output, proposal, real_entry_fixture_transport, receipt_hashes,
)
from test_alfworld_skill_acquisition import response
from test_network_recovery import Connection


FROZEN = study.ROOT/'runs/alfworld_container_boundary_learning_20261113_02'
GATE = """def applicability_gate(context):
    if set(context) != {'goal', 'observation', 'admissible_commands', 'history'}:
        return {'status':'UNKNOWN','reason':'MOCK context mismatch'}
    return {'status':'MATCH','reason':'MOCK gate deliberately permits all contexts'}
"""


def prepared(output):
    output.mkdir(mode=0o700)
    for name in ('selection_rules.json',study.TRAIN_FILE):
        shutil.copyfile(FROZEN/name,output/name)
    return study.prepare(study.BASE,output)


class EvidenceTest(unittest.TestCase):
    def test_natural_historical_input_and_independent_pool_are_disjoint(self):
        plan,packet,_,_,_,_,_,_ = study.configuration(study.BASE,FROZEN)
        training = read(FROZEN/study.TRAIN_FILE)
        independent = read(FROZEN/EVAL_FILE)
        public = packet['natural_development_prefixes']
        self.assertEqual(len(public),9)
        self.assertEqual(len({r['provenance']['task']['game_sha256'] for r in training['rows']}),9)
        self.assertEqual(packet['frozen_recovery_source'].encode(),
                         (study.S0/'candidate_0/revision_02/decoded.py').read_bytes())
        self.assertEqual(fingerprint(packet),plan['packet_sha256'])
        self.assertEqual(training['available']['ACTUAL_NO_EFFECT_MOVE']['games'],0)
        self.assertEqual(training['available']['EXPLICIT_INSTANCE_CONFLICT']['games'],0)
        train_games = {r['provenance']['task']['game_sha256'] for r in training['rows']}
        reserved = independent['strict_scene']+independent['expanded_game_group']
        self.assertFalse(train_games & {r['game_sha256'] for r in reserved})
        self.assertTrue(set(training['development_scenes']).isdisjoint(row['scene'] for row in reserved))
        self.assertEqual(len(reserved),80)
        wire = canonical(packet)
        self.assertNotIn('"expected":',wire)
        for excluded in ('game_sha256','traj_data','expert_plan','dev_001','candidate_pool',
                         'archive_sha256','check_rule','independent_inventory'):
            self.assertNotIn(excluded,wire)
        for row,projected in zip(training['rows'],public,strict=True):
            ref = row['provenance']
            steps = EvidenceStore(ref['journal']).records()
            current = steps[ref['step']]
            self.assertEqual(current['record_hash'],ref['receipt_sha256'])
            ctx = projected['public_context']
            self.assertEqual(ctx['history'][-1]['action'],current['payload']['action'])
            self.assertEqual(ctx['observation'],current['payload']['observation'])
            self.assertEqual(ctx['admissible_commands'],current['payload']['commands'])

    def test_counted_goal_is_not_mislabeled_as_incompatible_placement(self):
        labels = evidence_categories('put two creditcard in sofa.',dict(
            action='move creditcard 1 to sofa 1',observation='You move the creditcard 1 to the sofa 1.',
            commands=[]),set())
        self.assertEqual(labels,[])

    def test_rule_uses_goal_phase_and_instance_and_preserves_sources(self):
        plan,_,_,_,host,boundaries,_,_ = study.configuration(study.BASE,FROZEN)
        for spec in plan['sources']:
            with self.subTest(sequence=spec['sequence']):
                _,context,_ = study.pilot.start_state(host[spec['evidence_id']],plan)
                self.assertEqual(check_rule(context),'MATCH')
        results = {c['public']['id']:check_rule(study.checkpoint_context(c)) for c in boundaries}
        self.assertEqual([results[key] for key in ('dev_001','dev_004','dev_005','dev_006')],
                         ['DECLINE','UNKNOWN','DECLINE','UNKNOWN'])
        self.assertNotIn('MATCH',results.values())


class GateTest(unittest.TestCase):
    def test_original_gate_bytes_and_existing_static_rules(self):
        artifact = worker_artifact(GATE)
        self.assertTrue(artifact.startswith(GATE))
        self.assertTrue(static_check_detailed(artifact)['passed'])
        for prefix in ('import os\n','import re\nA = re.compile("x")\n'):
            self.assertFalse(static_check_detailed(worker_artifact(prefix+GATE))['passed'])
        with self.assertRaisesRegex(ValueError,'GATE_ENTRY'):
            worker_artifact(GATE+'\ndef environment_operator(context):\n    return {}\n')

    def test_resume_after_one_settled_response_and_not_reached_metrics(self):
        with (
            private_output('applicability_resume') as output,
            real_entry_fixture_transport([Connection(value=response(ABSTAIN))]) as (wires,offline),
        ):
            output = output.resolve()
            plan = prepared(output)
            template = read(output/'authorization.template.json')
            with self.assertRaises(PermissionError):
                study.run(study.BASE,output,authorization=template)
            self.assertEqual(wires,[])
            grant = study.pilot.authorization_for(plan)
            result = study.run(study.BASE,output,authorization=grant)
            self.assertEqual((result['budget']['calls'],result['resources']['worker_calls']), (1,0))
            self.assertIsNone(result['arms']['S1']['local_repairs'])
            self.assertIsNone(result['arms']['S1']['false_action_selections'])
            self.assertEqual(result['arms']['Rule']['local_repairs'],11)
            self.assertEqual(result['arms']['Rule']['false_action_selections'],0)
            self.assertEqual(result['arms']['S0']['false_action_selections'],3)
            self.assertEqual(fingerprint(wires[0]),plan['wire_sha256'])
            self.assertEqual(len(result['paired']['S0']['SOURCE']['NOT_REACHED']),11)
            before = receipt_hashes(output)
            self.assertEqual(study.run(study.BASE,output,authorization=grant,resume=True),result)
            self.assertEqual((len(wires),offline.call_count),(1,1))
            self.assertEqual(receipt_hashes(output),before)

    def test_unknown_response_remains_blocked(self):
        with (
            private_output('applicability_unknown') as output,
            real_entry_fixture_transport([Connection(read_error=TimeoutError('OFFLINE'))]) as (wires,offline),
        ):
            output = output.resolve()
            grant = study.pilot.authorization_for(prepared(output))
            with self.assertRaises(SendUnknown):
                study.run(study.BASE,output,authorization=grant)
            before = receipt_hashes(output)
            with self.assertRaises(RunUnhealthy):
                study.run(study.BASE,output,authorization=grant,resume=True)
            self.assertEqual((len(wires),offline.call_count),(1,1))
            self.assertEqual(receipt_hashes(output),before)

    def test_mock_gate_uses_real_worker_and_unchanged_recovery(self):
        with (
            private_output('applicability_textworld',mounted=True) as output,
            real_entry_fixture_transport([Connection(value=response(proposal(GATE)))]) as (wires,_),
        ):
            plan = prepared(output)
            result = study.run(study.BASE,output,authorization=study.pilot.authorization_for(plan))
            self.assertEqual(len(wires),1)
            self.assertEqual(result['attempt']['status'],'STATIC_PASSED')
            self.assertEqual(result['arms']['S1']['local_repairs'],11)
            self.assertEqual(result['arms']['S1']['false_action_selections'],3)
            self.assertEqual(result['arms']['S1']['negative_status'],{'MATCH':18})
            self.assertEqual(result['arms']['Rule']['false_action_selections'],0)
            for row in result['rows']:
                if row['role']=='SOURCE':
                    source = read(output/study.JOB/(row['id']+'.json'))
                    self.assertEqual(source['start_sha256'],row['start_sha256'])
                    self.assertEqual({step['artifact_sha256'] for step in source['decisions']},{study.S0_CODE_SHA})
            registry = EvidenceStore(output/'registry.jsonl').records()
            self.assertEqual({row['kind'] for row in registry},{'SHADOW_REGISTERED'})
            self.assertEqual(result['resources']['environment']['candidate'],22)
            self.assertTrue(all(row['S1']['receipt_origin']=='NEW_TEXTWORLD' for row in result['rows']
                                if row['role']=='SOURCE'))
            self.assertEqual(sha(output/study.JOB/'gate.py'),result['attempt']['submitted_code_sha256'])
            self.assertEqual(json.loads(wires[0]['messages'][1]['content']),
                             read(output/study.LEARNING))


if __name__=='__main__':
    unittest.main()
