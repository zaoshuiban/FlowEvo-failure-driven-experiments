"""Engineering checks; no paid requests and no new independent games."""
import json
import os
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import prepare_alfworld_route_a_prerequisites_v2 as N
import run_alfworld_route_a_prerequisites_v2 as R
from scripts.test_alfworld_applicability_multicandidate import response,propose,gate

ROOT=N.ROOT/'runs/alfworld_route_a_prerequisites_v2_20261117_01'


class Tests(unittest.TestCase):
    def test_parent_and_recovery_frozen(self):
        p=N.A.read(N.OLD/'protocol.json')
        for name in ('Route_A','S0'):
            self.assertEqual(N.A.sha(p['candidates'][name]['path']),N.X.EXPECTED[name])

    def test_known_unsafe_evidence_is_real_and_included(self):
        packet,ids=N.feedback_packet()
        old=N.A.read(N.OLD/'result.json')['rows']
        unsafe=[r for r in old if r['score']['unsupported_recovery']]
        self.assertEqual(len(unsafe),3)
        self.assertTrue(all(r['sample_id'] in ids for r in unsafe))
        self.assertTrue(all(r['live']['actions'][-1]['won'] for r in unsafe))
        self.assertEqual(packet['parent_gate_sha256'],N.X.EXPECTED['Route_A'])

    def test_feedback_has_no_future_or_private_probes(self):
        p,ids=N.feedback_packet()
        for row in p['feedback']:
            self.assertEqual(set(row),{'evidence_id','public_context','public_history_scope','supervision','candidate_self_report'})
            self.assertEqual(set(row['public_context']),{'goal','observation','admissible_commands','history'})
            self.assertNotIn('won',json.dumps(row));self.assertNotIn('recovery_probe',json.dumps(row))
        self.assertEqual(len(ids),len(set(ids)))

    def test_projection_rejects_hidden_fields(self):
        s=deepcopy(N.A.read(N.OLD/'checkpoints.private.json')['samples'][0])
        r=N.A.read(N.OLD/'result.json')['rows'][0]
        s['candidate_context']['expert_plan']='secret'
        with self.assertRaises(PermissionError):N.public_feedback(s,r)

    def test_sampling_is_disjoint_reproducible_and_result_free(self):
        audit=N.A.read(ROOT/'exposure.private.json')
        first=N.select(audit)
        with patch.object(N.A,'read',side_effect=AssertionError('sampling must not read results')):
            self.assertEqual(first,N.select(audit))
        groups={r['task']['group'] for r in first}
        self.assertEqual(len(groups),48)
        protected={r['task']['group'] for r in audit['protected_games']}
        self.assertFalse(groups&protected)
        online=N.A.read(N.OLD/'online/selection.private.json')
        self.assertFalse(groups&{r['task']['group'] for r in online['tasks']})

    def test_no_replacements_on_pool_exhaustion(self):
        with self.assertRaises(PermissionError):N.select({'eligible':[]})

    def test_request_is_one_bounded_revision(self):
        p,_=N.feedback_packet()
        wire=N.B.wire(ROOT,p,N.PROMPT,0,N.POLICY)
        self.assertEqual(wire['temperature'],0)
        self.assertEqual(wire['thinking'],{'type':'disabled'})
        self.assertEqual(wire['max_tokens'],4096)
        self.assertEqual(wire['response_format'],{'type':'json_object'})
        self.assertLessEqual(len(json.dumps(wire,ensure_ascii=False).encode()),N.POLICY['max_wire_input_bytes'])

    def test_no_authorization_no_request_or_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(N,'verify_preparation',return_value=self.plan()),patch.object(N,'stage_request',side_effect=AssertionError('no call')):
                with self.assertRaises(PermissionError):N.generate(Path(tmp))
            self.assertFalse((Path(tmp)/'generation/budget.jsonl').exists())

    def plan(self):
        return dict(run_id='mock-gate-v2',model='deepseek-flash',max_calls=1,
            max_tokens=94352,max_cost_microusd=1000000,worker_calls=0,
            parent_candidate={'sha256':N.X.EXPECTED['Route_A']},frozen_recovery={'sha256':N.X.EXPECTED['S0']})

    def mockrun(self,tmp,value):
        root=Path(tmp);(root/'generation').mkdir()
        N.A.commit(root/'generation/input.private.json',{'fixture':'ENGINEERING_ONLY'})
        wires=[]
        def sender(wire):wires.append(wire);return response(value)
        with patch.object(N,'verify_preparation',return_value=self.plan()):
            result=N.generate(root,sender=sender)
            files={str(p):N.A.sha(p) for p in (root/'generation').rglob('*') if p.is_file()}
            self.assertEqual(N.generate(root,sender=lambda _:self.fail('duplicate')),result)
            self.assertEqual(files,{str(p):N.A.sha(p) for p in (root/'generation').rglob('*') if p.is_file()})
        self.assertEqual(len(wires),1)
        return result

    def test_mock_delivery_and_settled_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=self.mockrun(tmp,propose(gate('UNKNOWN')))
            self.assertEqual(result['status'],'STATIC_PASSED_PENDING_DEVELOPMENT')
            self.assertEqual(result['origin'],'MOCK_ENGINEERING_ONLY')
            self.assertFalse(result['published'])
            with patch.object(N,'verify_preparation',return_value=self.plan()):
                with self.assertRaises(PermissionError):R.candidate(Path(tmp))

    def test_mock_abstention_no_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=self.mockrun(tmp,{'decision':'ABSTAIN','reason':'insufficient evidence'})
            self.assertEqual(r['status'],'ABSTAIN')
            self.assertNotIn('code_sha256',r)

    def test_static_refusal_cannot_be_execution_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=self.mockrun(tmp,propose('import os\n'+gate('MATCH')))
            self.assertEqual(r['status'],'STATIC_REJECTED')

    def test_unknown_blocks_reentry_without_resending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'generation').mkdir()
            N.A.commit(root/'generation/input.private.json',{'fixture':'ENGINEERING'})
            calls=[]
            def fail(wire):calls.append(wire);raise TimeoutError('MOCK SEND_UNKNOWN')
            with patch.object(N,'verify_preparation',return_value=self.plan()):
                with self.assertRaises(Exception):N.generate(root,sender=fail)
                with self.assertRaises(N.P.RunUnhealthy):N.generate(root,sender=fail)
            self.assertEqual(len(calls),1)

    def test_all_reviewed_samples_kept_without_results(self):
        samples=N.A.read(N.OLD/'checkpoints.private.json')['samples']
        self.assertEqual(R.all_samples(samples+samples),samples)

    def test_unresolved_stage_and_instance_not_relabelled(self):
        from alfworld_.route_a_expanded_labels import review
        root=N.OLD/'collection/games'
        count=0
        for p in root.glob('*.json'):
            for b in N.A.read(p)['branches']:
                if b['mode'] in ('UNPROCESSED','OTHER_INSTANCE') and b['status']=='COLLECTED':
                    outcome=review(b)
                    if outcome['label'] is None:
                        self.assertEqual(outcome['label_status'],'UNRESOLVED_LABEL');count+=1
        self.assertGreater(count,0)

    @unittest.skipUnless(os.environ.get('FLOWEVO_REAL_WORKER_ACCEPTANCE')=='1','explicit zero API Linux Worker test')
    def test_existing_gate_and_recovery_real_worker(self):
        # Old exposed state only. This tests the unchanged execution chain,
        # not a new real-model gate or independent transfer.
        audit=ROOT/'acceptance';audit.mkdir(parents=True,exist_ok=True)
        # Docker Desktop may not share macOS per-user temporary directories.
        # Keep receipts in the controlled workspace rather than deleting them.
        out=Path(tempfile.mkdtemp(prefix='worker-',dir=audit))
        if out.is_dir():
            p=N.A.read(N.OLD/'protocol.json')
            p=dict(p,run_id='mock-v2-worker-'+out.name)
            budget,runner,registry,receipts,recovery,gate_card=N.V.setup(out,p)
            old=N.A.read(N.X.PARENT/'protocol.json')
            _,ctx,_=N.P.start_state(old['train']['FR11'][0]['origin'],old)
            before=N.A.sha(N.B.CODE)
            first=[N.P.invoke(runner,c,ctx) for c in (gate_card,recovery)]
            self.assertTrue(all(x['worker_status']=='OK' for x in first))
            count=len(runner.events.records())
            for c in (gate_card,recovery):
                N.P.invoke(runner,c,ctx)
                self.assertEqual(registry.state(c)['permission'],'shadow')
            self.assertEqual(len(runner.events.records()),count)
            self.assertEqual(before,N.A.sha(N.B.CODE))
            self.assertEqual(budget.snapshot()['calls'],0)


if __name__=='__main__':unittest.main()
