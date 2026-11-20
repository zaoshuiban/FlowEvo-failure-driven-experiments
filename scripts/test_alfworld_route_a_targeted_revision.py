import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import run_alfworld_route_a_targeted_revision as V
from scripts.test_alfworld_applicability_multicandidate import response,propose,gate


class Tests(unittest.TestCase):
    def test_packet_is_small_and_source_complete(self):
        p=V.packet()
        self.assertEqual(len(p['feedback']),7)
        self.assertEqual(p['previous_code'],(V.PARENT/'generation/candidate.py').read_text())
        self.assertEqual(p['recovery_sha256'],V.N.X.EXPECTED['S0'])
        self.assertIn('_processing_required',p['diagnostics']['current_requirement_function'])
        wire=V.B.wire(V.PARENT,p,V.PROMPT,0,V.POLICY)
        self.assertLessEqual(len(V.B.canonical(wire).encode()),48000)
        self.assertEqual(wire['max_tokens'],4096)

    def test_no_future_or_synthetic_cases_in_feedback(self):
        p=V.packet()
        self.assertNotIn('Morphology',str(p));self.assertNotIn('recovery_probe',str(p))
        for r in p['feedback']:
            self.assertEqual(set(r['public_context']),{'goal','observation','admissible_commands','history'})
            self.assertNotIn('won',str(r));self.assertNotIn('game_sha256',str(r))

    def test_old_configuration_restored(self):
        old=(V.N.VERSION,V.N.PROMPT,V.N.POLICY,V.N.verify_preparation)
        with V.adapter():self.assertEqual(V.N.VERSION,V.VERSION)
        self.assertEqual(old,(V.N.VERSION,V.N.PROMPT,V.N.POLICY,V.N.verify_preparation))

    def test_both_executions_required(self):
        for a in (False,True):
            for b in (False,True):
                r=V.semantic_acceptance(dict(candidate_version='v',passed=a),dict(candidate_version='v',passed=b),'v')
                self.assertEqual(r['passed'],a and b)
                self.assertFalse(r['published']);self.assertFalse(r['online_authorized'])
                self.assertFalse(r['independent_validation_passed'])

    def test_old_source_cannot_reuse_new_acceptance(self):
        with self.assertRaises(PermissionError):V.semantic_acceptance(dict(candidate_version='old',passed=True),dict(candidate_version='v',passed=True),'v')

    def plan(self):
        return dict(run_id='mock-targeted-v3',model='deepseek-flash',max_calls=1,max_tokens=52352,
            max_cost_microusd=1000000,worker_calls=0,parent_candidate={'sha256':'parent'},frozen_recovery={'sha256':V.N.X.EXPECTED['S0']})

    def test_authorization_is_new_protocol_and_one_request(self):
        p=self.plan();auth=V.authorization(p)
        self.assertEqual(auth['protocol'],V.VERSION+':'+V.A.digest(p))
        with tempfile.TemporaryDirectory() as tmp,patch.object(V,'verify',return_value=p):
            with self.assertRaises(PermissionError):V.generate(Path(tmp))
            self.assertFalse((Path(tmp)/'generation/budget.jsonl').exists())

    def test_mock_generated_source_parent_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(V,'verify',return_value=self.plan()):
            root=Path(tmp);V.A.commit(root/'generation/input.private.json',{'engineering':'only'})
            calls=[]
            def sender(wire):calls.append(wire);return response(propose(gate('UNKNOWN')))
            r=V.generate(root,sender=sender)
            self.assertEqual(r['origin'],'MOCK_ENGINEERING_ONLY');self.assertEqual(r['parent_sha256'],'parent')
            self.assertEqual(r['status'],'STATIC_PASSED_PENDING_DEVELOPMENT')
            before=V.A.sha(root/'generation/budget.jsonl')
            self.assertEqual(r,V.generate(root,sender=lambda _:self.fail('resend')))
            self.assertEqual(before,V.A.sha(root/'generation/budget.jsonl'));self.assertEqual(len(calls),1)

    def test_unknown_not_resubmitted(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(V,'verify',return_value=self.plan()):
            root=Path(tmp);V.A.commit(root/'generation/input.private.json',{'engineering':'only'});calls=[]
            def sender(wire):calls.append(wire);raise TimeoutError('mock SEND_UNKNOWN')
            with self.assertRaises(Exception):V.generate(root,sender=sender)
            with self.assertRaises(V.P.RunUnhealthy):V.generate(root,sender=sender)
            self.assertEqual(len(calls),1)


if __name__=='__main__':unittest.main()
