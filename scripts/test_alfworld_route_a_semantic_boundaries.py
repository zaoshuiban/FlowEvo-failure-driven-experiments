"""P0 classification tests, not model or learned-skill scores."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import audit_alfworld_route_a_semantic_boundaries as M


class Semantics(unittest.TestCase):
    def test_category_goal(self):
        g=M.goal_signature('(define (problem x) (:goal (exists (?o - object ?r - receptacle) (and (objectType ?o AppleType) (receptacleType ?r FridgeType) (inReceptacle ?o ?r)))))')
        self.assertTrue(g['existential']);self.assertFalse(g['concrete_goal_entity'])

    def test_fixed_entity_is_different(self):
        g=M.goal_signature('(:goal (and (objectType apple1 AppleType) (receptacleType fridge1 FridgeType) (inReceptacle apple1 fridge1)))')
        self.assertTrue(g['concrete_goal_entity'])

    def test_processing_same_variable(self):
        for target,expected in [('?o',True),('?p',False)]:
            g=M.goal_signature(f'(:goal (and (objectType ?o AppleType) (isHot {target}) (inReceptacle ?o ?r)))')
            self.assertEqual(g['same_processed_delivery_variable'],expected)

    def test_malformed_does_not_guess(self):
        for text in ['(:goal',')','abc','(:goal x) (:goal y)']:
            with self.assertRaises(ValueError):M.form(text,':goal')

    def test_open_not_stage_negative(self):
        for evidence in ('UNKNOWN','CONFIRMED_ABSENT','CONFIRMED_PRESENT'):
            self.assertEqual(M.scoped_claim('open cabinet 1',True,evidence)['status'],'NOT_A_NEGATIVE')

    def test_final_delivery_requires_scope(self):
        r=M.scoped_claim('move cup 1 to cabinet 1',True,'CONFIRMED_ABSENT')
        self.assertEqual(r['status'],'VALID_NEGATIVE_POSSIBLE');self.assertEqual(r['scope'],'FINAL_DELIVERY')

    def test_missing_is_not_absent(self):
        self.assertEqual(M.scoped_claim('move cup 1 to cabinet 1',True,'UNKNOWN')['status'],'UNRESOLVED')

    def test_number_difference_is_not_conflict(self):
        self.assertEqual(M.scoped_claim('move apple 2 to fridge 2',different_instance=True)['status'],'NOT_A_NEGATIVE')

    def test_fixed_identity_still_requires_evidence(self):
        self.assertEqual(M.scoped_claim('move apple 2 to fridge 2',fixed_instance=True,different_instance=True)['status'],'UNRESOLVED')

    def test_four_scopes(self):
        self.assertEqual(M.action_class('heat apple 1 with microwave 1'),'PROCESSING_ACTION')
        self.assertEqual(M.action_class('inventory'),'INFORMATION_GATHERING')
        self.assertEqual(M.action_class('open fridge 1'),'OPEN_PREPARATION')
        self.assertEqual(M.action_class('move apple 1 to fridge 1'),'PLACEMENT_CANDIDATE_FOR_FINAL_DELIVERY')

    def test_unknown_environment_step_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'environment.jsonl'
            M.P.EvidenceStore(f).append('STEP_STARTED',dict(index=1,branch='x',scope='host'),0)
            with self.assertRaises(M.P.RunUnhealthy):M.P.EnvironmentReceipts(f,300)

    def test_budget_stops_before_environment(self):
        with tempfile.TemporaryDirectory() as d:
            r=M.P.EnvironmentReceipts(Path(d)/'env.jsonl',0)
            with self.assertRaises(M.K.D.BudgetExhausted):r.step(None,'open cabinet 1',branch='x',scope='host')

    def test_unfinished_job_cannot_retry(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);M.A.commit(p/'audit.private.json',dict(jobs=[]))
            M.P.EvidenceStore(p/'audit_events.jsonl').append('JOB_STARTED',dict(id='x'),0)
            with patch.object(M,'verify',return_value={}):
                with self.assertRaises(M.P.RunUnhealthy):M.replay(p)

    def test_no_model_or_worker_execution_in_audit(self):
        import ast
        tree=ast.parse(Path(M.__file__).read_text())
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertFalse(calls & {'stage_request','invoke','learned_decision','validate_source','authorize'})


if __name__=='__main__':unittest.main()
