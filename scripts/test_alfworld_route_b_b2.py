"""B2 engineering fixtures only; no model request or learned skill."""
import unittest, tempfile, time
from pathlib import Path
from dataclasses import replace
from collections import Counter
import run_alfworld_route_b_b2 as B
P=B.P
from failure_evo.runtime import BudgetExhausted
from failure_evo.run_health import RunUnhealthy

FROZEN=B.ROOT/'runs/alfworld_route_b_b2_20261116_02'

class FrozenEvaluationTests(unittest.TestCase):
    def test_budget_and_frozen_identity_fail_closed(self):
        with tempfile.TemporaryDirectory(dir=B.ROOT/'runs') as d:
            out=Path(d);p=P.read(FROZEN/'protocol.json')
            budget=B.create_accounts(out,dict(p,worker_calls=0))
            with self.assertRaises(BudgetExhausted):budget.tool()
            path=out/'unchanged.py';path.write_text('original')
            binding={str(path):P.sha(path)};path.write_text('modified')
            with self.assertRaises(PermissionError):P.verify_history(binding)
            with self.assertRaises(ValueError):B.create_accounts(out,dict(p,worker_calls=1))

    def test_sources_and_all_empty_branches_score(self):
        p=P.read(FROZEN/'protocol.json');P.verify_history(p['historical_sha256'])
        self.assertEqual(len(p['candidates']),5)
        for c in p['cases']:
            prefix,_,_=P.start_state(c['origin'],p)
            result=P.score_source(c['origin'],prefix,[],[],'DECLINED')
            s=B.score(c,result)
            self.assertTrue(s['declined']);self.assertFalse(s['won'])
            self.assertFalse(s['local_repair'])

    def test_scoped_labels_do_not_condemn_every_action(self):
        p=P.read(FROZEN/'protocol.json')
        for label in ('DECLINE','UNKNOWN'):
            c=next(c for c in p['cases'] if c['label']==label)
            step=dict(c['origin']['steps'][c['origin']['projected']['anchor']-1])
            step.update(action='look')
            s=B.score(c,dict(actions=[step],stop='ACTION_LIMIT'))
            self.assertEqual(s['goal_relevance'],'NOT_EVALUABLE')
            key='scoped_false_applicability' if label=='DECLINE' else 'scoped_unsupported_action'
            self.assertFalse(s[key])
            step['action']=c['origin']['steps'][c['origin']['projected']['anchor']-1]['action']
            self.assertTrue(B.score(c,dict(actions=[step],stop='ACTION_LIMIT'))[key])

    def test_actual_worker_environment_resume_budget_shadow(self):
        with tempfile.TemporaryDirectory(prefix='b2_fixture_',dir=B.ROOT/'runs') as d:
            out=Path(d);p=P.read(FROZEN/'protocol.json');P.commit(out/'protocol.json',p)
            p,runner,registry,receipts,cards=B.setup(out)
            with self.assertRaises(BudgetExhausted):runner.budget.reserve(1,1)
            path=out/'fixture.py'
            path.write_text("def environment_operator(c):\n if c['state'].get('looked'): return {'status':'declined','state':{},'reason':'ENGINEERING_ONLY'}\n return {'status':'applied','action':'look','state':{'looked':True},'reason':'ENGINEERING_ONLY'}\n")
            card=replace(next(iter(cards.values())),operator_id='engineering_fixture',version=P.sha(path),artifact_path=str(path),artifact_sha256=P.sha(path))
            registry.register(card,time.time());c=p['cases'][0]
            def fail(point,payload):
                if point=='after_action':raise InterruptedError('fixture interruption')
            args=(p,p['data_root'],c['origin'],'fixture',card,runner,registry,receipts,out/'execution',P.StrictTrainEnv)
            with self.assertRaises(InterruptedError):P.validate_source(*args,fail)
            count=runner.budget.tool_calls
            result=P.validate_source(*args,None)
            self.assertEqual(len(result['actions']),1)
            self.assertEqual(result['stop'],'DECLINED')
            self.assertEqual(runner.budget.tool_calls,count+1)
            self.assertGreater(receipts.started['resume_candidate'],0)
            hashes={str(f):P.sha(f) for f in out.rglob('*.jsonl')}
            self.assertEqual(P.validate_source(*args,None),result)
            self.assertEqual(hashes,{str(f):P.sha(f) for f in out.rglob('*.jsonl')})
            self.assertEqual(registry.state(card)['permission'],'shadow')
            self.assertEqual(runner.budget.calls,0)
            events=runner.events.records();executed=[r['payload']['execution_id'] for r in events if r['kind']=='ENVIRONMENT_POLICY_EXECUTED']
            self.assertEqual(len(executed),len(set(executed)))
            # Unresolved Worker state blocks the shared health entry.
            runner.events.append('ENVIRONMENT_POLICY_STARTED',dict(execution_id='unresolved_fixture'),time.time())
            from types import SimpleNamespace
            with self.assertRaises(RunUnhealthy):P.check_run(runner.budget,SimpleNamespace(events=P.EvidenceStore(out/'provider.jsonl')),runner)

if __name__=='__main__':unittest.main()
