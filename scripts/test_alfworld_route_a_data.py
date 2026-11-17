"""Zero-API A1 audit tests. These are not the future A2 learning acceptance."""

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from failure_evo.math_stream import read
from audit_alfworld_route_a_data import S1, assess_context, data_readiness, freeze, fresh_failure, trace_hits


def record(label, game, **extra):
    return dict(label=label, game_id=game, confidence_or_review_status='EVIDENCE_REVIEWED',
                label_evidence=[{'kind':'TEST_FIXTURE_ONLY'}], **extra)


class DataFreezeTest(unittest.TestCase):
    def test_nine_real_contexts_do_not_become_hard_negative_labels(self):
        records = read(S1/'historical_training.private.json')['rows']
        self.assertEqual(len(records), 9)
        for row in records:
            before = deepcopy(row)
            result = assess_context(row)
            self.assertFalse(result['fresh_failed_placement'])
            self.assertIsNone(result['label'])
            self.assertEqual(result['exclusion_reason'], 'OUTSIDE_FAILED_PLACEMENT_HOOK')
            self.assertEqual(row, before)

    def test_missing_processing_and_multiple_instances_are_not_proof(self):
        rows = read(S1/'historical_training.private.json')['rows']
        for kind in ('PROCESS_NOT_CONFIRMED', 'DISTINCT_PUBLIC_INSTANCES', 'INCOMPATIBLE_NATIVE_PLACEMENT'):
            found = [r for r in rows if r['kind'] == kind]
            self.assertEqual(len(found), 2)
            self.assertTrue(all(assess_context(r)['label_provenance']=='NOT_ADJUDICATED' for r in found))

    def test_hidden_fields_refused(self):
        row = deepcopy(read(S1/'historical_training.private.json')['rows'][0])
        row['public_context']['expert_plan'] = 'forbidden'
        with self.assertRaises(PermissionError):
            assess_context(row)

    def test_hook_requires_real_failed_move_and_current_receipt(self):
        ctx = dict(history=[{'action':'move apple 1 to fridge 1','observation':'Nothing happens.'}],
                   observation='Nothing happens.')
        self.assertTrue(fresh_failure(ctx))
        ctx['observation'] = 'You open the fridge 1.'
        self.assertFalse(fresh_failure(ctx))
        self.assertEqual(trace_hits({'actions':ctx['history']})[0]['step'],1)
        self.assertEqual(trace_hits({'actions':[{'action':'open fridge 1','observation':'Nothing happens.'}]}),[])

    def test_no_labels_never_produce_ready(self):
        self.assertEqual(data_readiness([],[])['status'],'BLOCKED_DATA_INSUFFICIENT')
        rows = [record(k,'train-'+k) for k in ('MATCH','DECLINE','UNKNOWN')]
        val = [record(k,'validation-'+k) for k in ('MATCH','DECLINE','UNKNOWN')]
        self.assertEqual(data_readiness(rows,val)['status'],'DATA_READY')
        rows[0]['confidence_or_review_status'] = 'MODEL_SELF_REPORT'
        self.assertIn('TRAIN_MATCH_EVIDENCE_MISSING',data_readiness(rows,val)['blockers'])

    def test_same_game_counterfactuals_cannot_cross_roles(self):
        train = [record(k,'same-game') for k in ('MATCH','DECLINE','UNKNOWN')]
        val = deepcopy(train)
        self.assertIn('TRAIN_VALIDATION_GAME_OVERLAP',data_readiness(train,val)['blockers'])

    def test_freeze_is_idempotent_and_does_not_overwrite(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'audit.private.json'
            freeze(p,{'v':1})
            before = p.read_bytes()
            freeze(p,{'v':1})
            self.assertEqual(p.read_bytes(),before)
            with self.assertRaises(PermissionError):
                freeze(p,{'v':2})
            self.assertEqual(p.read_bytes(),before)


if __name__=='__main__':
    unittest.main()
