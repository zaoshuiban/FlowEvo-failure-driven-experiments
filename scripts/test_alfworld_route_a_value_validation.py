"""No model calls. Fixtures do not count as independent validation evidence."""
import unittest
from unittest.mock import patch
import run_alfworld_route_a_value_validation as V


class Tests(unittest.TestCase):
    def test_sampling_reproducible_and_disjoint(self):
        a=V.A.read(V.ROOT/'runs/alfworld_route_a_online_value_20261117_01/exposure.private.json')
        first=V.select(a);self.assertEqual(first,V.select(a));validation,online=first
        self.assertEqual(len(validation),48);self.assertEqual(len(online),60)
        self.assertFalse({r['task']['group'] for r in validation}&{r['task']['group'] for r in online})
        self.assertEqual(len({r['task']['group'] for r in validation}),48)
        self.assertEqual(len({r['task']['task_type'] for r in online}),6)

    def test_sampling_cannot_read_outcomes(self):
        a=V.A.read(V.ROOT/'runs/alfworld_route_a_online_value_20261117_01/exposure.private.json')
        with patch.object(V.A,'read',side_effect=AssertionError('must be metadata only')):self.assertEqual(len(V.select(a)[0]),48)

    def thresholds(self):
        return dict(match_games=12,control_games=12,decline_games=6,unknown_games=6,positive_scenes=6,positive_containers=3,positive_task_types=3,game_all_positive_repair_rate=.8)

    def rows(self):
        return [dict(game=str(i),label=label,scene=i,container=str(i%3),task_type=str(i%3),gate_error=False,
            score=dict(completed_repair=label=='MATCH',false_final_delivery_recovery=False,unsupported_recovery=False,safety_unresolved=False,candidate_error=False)) for label in ('MATCH','DECLINE','UNKNOWN') for i in range(12)]

    def test_complete_fixtures_allow_only_preparation(self):
        a=V.assess(self.rows(),self.thresholds());self.assertTrue(a['eligible_for_online_preparation'])
        self.assertFalse(a['publication_authorized']);self.assertFalse(a['paid_online_authorized'])

    def test_single_violation_blocks_all(self):
        rs=self.rows();rs[-1]['score']['unsupported_recovery']=True
        self.assertFalse(V.assess(rs,self.thresholds())['SAFETY_READY'])

    def test_zero_denominator_not_ready(self):
        a=V.assess([],self.thresholds());self.assertFalse(a['eligible_for_online_preparation']);self.assertIsNone(a['zero_error_one_sided95_upper'])

    def test_duplicate_states_not_independent_games(self):
        a=V.assess(self.rows()[:1]*100,self.thresholds());self.assertEqual(a['coverage']['match_games'],1);self.assertFalse(a['COVERAGE_READY'])

    def test_partial_game_not_full_success(self):
        rs=self.rows();extra=dict(rs[0],score=dict(rs[0]['score'],completed_repair=False));rs.append(extra)
        self.assertEqual(V.assess(rs,self.thresholds())['fully_repaired_games'],11)

    def test_uncertainty_and_errors_block(self):
        rs=self.rows();rs[0]['score']['safety_unresolved']=True
        self.assertFalse(V.assess(rs,self.thresholds())['SAFETY_READY'])
        rs=self.rows();rs[0]['gate_error']=True
        self.assertFalse(V.assess(rs,self.thresholds())['SAFETY_READY'])

    def test_parent_candidate_hashes(self):
        self.assertEqual(V.A.sha(V.X.A3/'frozen_candidate/gate.py'),V.X.EXPECTED['Route_A'])
        self.assertEqual(V.A.sha(V.B.CODE),V.X.EXPECTED['S0'])


if __name__=='__main__':unittest.main()
