"""Zero-API B v6 acceptance using the unchanged v5 strategy as a regression fixture."""
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from failure_evo.contracts import fingerprint
from failure_evo.math_stream import read, sha
from failure_evo.run_health import RunUnhealthy
from run_alfworld_recovery_v6 import freeze, prepare, run
from test_alfworld_skill_acquisition import SOURCE, response

BASE=SOURCE.parent
INPUTS=(SOURCE, BASE/'alfworld_recovery_v4_pilot_20261110_01',
        BASE/'alfworld_recovery_v4_development_audit_20261110_01',
        BASE/'alfworld_recovery_v5_pilot_20261110_01',
        BASE/'alfworld_recovery_v5_post_failure_diagnostic_20261110_01')


@unittest.skipUnless(all(p.exists() for p in INPUTS),'frozen ALFWorld receipts required')
class RecoveryV6Test(unittest.TestCase):
    def test_zero_api_replay_and_launch_boundary(self):
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            root=Path(temp)
            mock=Path(os.environ.get('ALFWORLD_V6_ACCEPTANCE',str(root/'mock')))
            paths=(*INPUTS,mock)
            card=read(INPUTS[3]/'result.json')['result']['candidates'][0]['card']
            artifact=Path(card['artifact_path'])
            self.assertEqual(sha(artifact),card['artifact_sha256'])
            calls=[]
            def sender(wire):
                calls.append(wire)
                p=json.loads(wire['messages'][-1]['content'])
                self.assertEqual(set(p),{'mechanism','analyses'})
                self.assertEqual(len(p['analyses']),11)
                for forbidden in ('stale_pairs','negative_cases','expert_plan','candidate_pool',
                                  'source_receipt','audit_freeze','look after','wrong_number'):
                    self.assertNotIn(forbidden,wire['messages'][-1]['content'])
                self.assertIn('Trigger',wire['messages'][0]['content'])
                self.assertIn('Binding',wire['messages'][0]['content'])
                self.assertIn('Recovery',wire['messages'][0]['content'])
                return response(dict(code=artifact.read_text(),description='Frozen v5 regression',
                                     applicability='Mock only'))
            result=run(paths,sender=sender)
            self.assertEqual((result['local_repairs'],result['wins'],result['paid_requests']),(4,4,0))
            self.assertEqual(result['candidate']['status'],'SHADOW')
            self.assertFalse(result['development_pass'])
            self.assertEqual({x['family'] for x in result['positives']},{'safe','drawer','fridge','microwave'})
            self.assertTrue(all(x['trigger_observed'] and x['correct_target_open'] and
                                x['original_placement_completed'] for x in result['positives']))
            negative=result['negatives']
            original=[x for x in negative if x['group']=='original_11']
            stale=[x for x in negative if x['group']=='stale_pairs']
            self.assertEqual((len(original),len(stale),len(negative)),(11,6,20))
            self.assertEqual(sum(x['actual']['status']=='applied' for x in original),4)
            self.assertEqual([x['actual']['status'] for x in stale],['declined','applied','declined']*2)
            ledger=(mock/'budget.jsonl').read_bytes()
            self.assertEqual(result,run(paths,sender=sender))
            self.assertEqual(ledger,(mock/'budget.jsonl').read_bytes())
            self.assertEqual(len(calls),1)
            target=root/'real'
            args=SimpleNamespace(paths=(*INPUTS,target),output=target,mock_run=mock)
            prepare(args)
            with self.assertRaises(PermissionError):
                run(args.paths,authorization=read(target/'authorization.template.json'))
            self.assertFalse((target/'provider.jsonl').exists())

    def test_unknown_blocks_resume(self):
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            target=Path(temp)/'unknown'
            calls=[]
            def sender(wire):
                calls.append(wire)
                raise TimeoutError('mock response lost')
            with self.assertRaises(TimeoutError):
                run((*INPUTS,target),sender=sender)
            ledger=(target/'budget.jsonl').read_bytes()
            with self.assertRaises(RunUnhealthy):
                run((*INPUTS,target),sender=sender)
            self.assertEqual(len(calls),1)
            self.assertEqual(ledger,(target/'budget.jsonl').read_bytes())

    def test_post_feedback_freeze_and_legal_boundary(self):
        plan,_,_,_,host,checkpoints,negatives=freeze(*INPUTS,Path('/tmp/v6-unused'),mock=True)
        self.assertEqual(plan['validation_sha256'],fingerprint([checkpoints,negatives]))
        for c in checkpoints:
            origin=host[c['evidence_id']]
            self.assertEqual(origin['steps'][c['step']-1]['observation'],'Nothing happens.')
            self.assertFalse(origin['steps'][c['step']-1]['won'])
        self.assertEqual(plan['worker_calls'],68)


if __name__=='__main__':
    unittest.main()
