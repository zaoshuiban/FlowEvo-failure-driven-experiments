import unittest
import audit_alfworld_route_c_supporting_evidence as S


class SupportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.es=S.A.read(S.C.OUT/'episodes.private.json')

    def test_prior_branches_are_not_new_execution(self):
        r=S.prior_probes(self.es)
        self.assertEqual(len(r['branches']),14)
        self.assertEqual(r['original_failed_steps_compared'],338)
        self.assertTrue(all(not b['new_execution'] for b in r['branches']))

    def test_completed_subgoal_omitted_from_actual_prompt(self):
        rows=S.native_prompt_visibility(self.es[40]);r=next(x for x in rows if x['step']==15)
        self.assertIn(4,r['omitted_prior_history_steps'])
        self.assertNotIn(4,r['transmitted_history_steps'])

    def test_l1_handoff_drops_early_search_receipts(self):
        r=S.native_prompt_visibility(self.es[45])[0]
        self.assertEqual(r['step'],40);self.assertEqual(r['transmitted_history_steps'],list(range(30,40)))
        self.assertIn(2,r['omitted_prior_history_steps'])

    def test_cup_task_does_not_silently_become_mug(self):
        ep=self.es[115]
        self.assertIn('-Cup-',ep['source_task']['group'])
        branch=next(x for x in S.prior_probes(self.es)['branches'] if x['file']=='failure_116.json')
        self.assertFalse(branch['won']);self.assertIn('heat mug 2 with microwave 1',branch['actions'])

    def test_hindsight_location_not_online_evidence(self):
        rows=S.prior_probes(self.es)['branches']
        selected=[x for x in rows if x['prior_probe_location_used']]
        self.assertEqual({x['file'] for x in selected},{'followup_010.json','shortcut_017.json','shortcut_046.json'})
        self.assertTrue(all(x['role']=='HOST_RETROSPECTIVE_REPAIR_ONLY' for x in rows))


if __name__=='__main__':unittest.main()
