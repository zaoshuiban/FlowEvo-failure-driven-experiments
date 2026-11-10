"""B v7 acceptance. Historical artifacts are returned only by a Mock sender."""
from collections import Counter
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from alfworld_.failure_learning import EnvironmentPolicyRunner, context_view, static_check
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_registry import FailureOperator
from failure_evo.math_stream import read, sha
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from run_alfworld_recovery_v7 import freeze, prepare, run
from run_alfworld_skill_acquisition import create_accounts
from test_alfworld_recovery_v6 import BASE, INPUTS
from test_alfworld_skill_acquisition import response

REVISION = BASE/'alfworld_recovery_v6_engineering_revision_20261110_01'


def fixture(code):
    return response(dict(code=code,description='Mock regression fixture',applicability='test only'))


@unittest.skipUnless(REVISION.exists() and all(p.exists() for p in INPUTS),'frozen ALFWorld receipts required')
class RecoveryV7Test(unittest.TestCase):
    def test_frozen_replay_and_authorization(self):
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            root=Path(temp)
            output=Path(os.environ.get('ALFWORLD_V7_ACCEPTANCE',str(root/'mock')))
            plan,payload,_,_,_,checkpoints,negatives=freeze(*INPUTS,output,mock=True)
            self.assertEqual(fingerprint([checkpoints,negatives]),plan['validation_sha256'])
            calls=[]
            def sender(wire):
                calls.append(wire)
                self.assertEqual(json.loads(wire['messages'][-1]['content']),payload)
                self.assertEqual(len(payload['analyses']),11)
                for name in ('stale_pairs','negative_cases','expert_plan','candidate_pool','source_receipt'):
                    self.assertNotIn(name,wire['messages'][-1]['content'])
                for rule in ('Failure Validity','Target Binding','Recovery Decision','No import-time calls',
                             're.compile','literal pattern strings'):
                    self.assertIn(rule,wire['messages'][0]['content'])
                return fixture((REVISION/'revised_policy.py').read_text())
            result=run((*INPUTS,output),sender=sender)
            self.assertEqual((result['generated_complete'],result['static_rejected'],result['shadow_registered']),
                             (1,0,1))
            self.assertEqual((result['local_repairs'],result['wins'],result['false_triggers']),(4,4,7))
            self.assertEqual(len(result['negatives']),20)
            self.assertFalse(result['development_pass'])
            self.assertEqual(Counter(x['group'] for x in result['negatives'] if x['actual']['status']=='applied'),
                             {'original_11':1,'stale_pairs':4,'new_state_change':2})
            self.assertEqual(result['paid_requests'],0)
            self.assertEqual({r['kind'] for r in EvidenceStore(output/'registry.jsonl').records()},
                             {'SHADOW_REGISTERED'})
            ledger=(output/'budget.jsonl').read_bytes()
            self.assertEqual(result,run((*INPUTS,output),sender=sender))
            self.assertEqual(ledger,(output/'budget.jsonl').read_bytes())
            self.assertEqual(len(calls),1)
            target=root/'real'
            args=SimpleNamespace(paths=(*INPUTS,target),output=target,mock_run=output)
            prepare(args)
            with self.assertRaises(PermissionError):
                run(args.paths,authorization=read(target/'authorization.template.json'))
            self.assertFalse((target/'provider.jsonl').exists())
            self.assertTrue(all(sha(BASE/path)==digest for path,digest in plan['historical_sha256'].items()))

    def test_original_static_rejection_is_not_execution(self):
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            output=Path(temp)/'static'
            code=(REVISION/'original_model_policy.py').read_text()
            result=run((*INPUTS,output),sender=lambda _:fixture(code))
            self.assertEqual(result['candidate']['check']['errors'],['TOP_LEVEL_EXECUTION'])
            self.assertEqual((result['generated_complete'],result['static_rejected'],result['worker_calls']),(1,1,0))
            saved,=(output/'candidate_v6/generated_artifacts').glob('*.py')
            self.assertEqual(saved.read_text(),code)
            self.assertFalse((output/'registry.jsonl').exists())

    def test_unknown_blocks_retry(self):
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            output=Path(temp)/'unknown'
            calls=[]
            def sender(wire):
                calls.append(wire)
                raise TimeoutError('mock loss')
            with self.assertRaises(TimeoutError):
                run((*INPUTS,output),sender=sender)
            ledger=(output/'budget.jsonl').read_bytes()
            with self.assertRaises(RunUnhealthy):
                run((*INPUTS,output),sender=sender)
            self.assertEqual(len(calls),1)
            self.assertEqual((output/'budget.jsonl').read_bytes(),ledger)

    def test_worker_illegal_action_exception_and_budget(self):
        with tempfile.TemporaryDirectory(dir=BASE) as temp:
            root=Path(temp)
            card=FailureOperator.from_dict(read(REVISION/'artifact.json')['card'])
            spec=read(REVISION/'protocol.json')['worker']
            backend=FrozenLinuxBackend(image=spec['image'],worker_script=spec['worker_script'])
            budget=create_accounts(root,dict(run_id='v7_worker_mock',max_calls=0,max_tokens=0,
                max_cost_microusd=0,worker_calls=2))
            runner=EnvironmentPolicyRunner(backend,root/'worker.jsonl',budget)
            ctx=context_view('fixture','fixture',['look'],[],{})
            for name,source in (
                ('illegal',"def environment_operator(c):\n return {'status':'applied','action':'invalid','state':{},'reason':'test'}\n"),
                ('exception',"def environment_operator(c):\n raise ValueError('mock')\n"),
            ):
                file=root/(name+'.py')
                file.write_text(source)
                self.assertTrue(static_check(source)['passed'])
                test_card=replace(card,artifact_path=str(file),artifact_sha256=sha(file),version=fingerprint(name))
                result=runner.run(test_card,ctx)
                self.assertEqual(result['status'],'error')
                if name=='illegal':
                    self.assertEqual(result['reason'],'ACTION_NOT_ADMISSIBLE')
            with self.assertRaises(BudgetExhausted):
                runner.run(test_card,dict(ctx,observation='new context'))
            self.assertEqual(budget.tool_calls,2)


if __name__=='__main__':
    unittest.main()
