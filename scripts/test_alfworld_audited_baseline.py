"""Regression checks for no-retry ALFWorld actions and official completion."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from alfworld_.audited_baseline import AuditedActionClient, classify_trace
from alfworld_.generator import AlfWorldGenerator
from alfworld_.schemas import AlfWorldTrace
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.network_transport import DEFAULT_POLICY
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.run_health import RunUnhealthy
from runtime.config import GenerationSettings


class AlfBaselineTests(unittest.TestCase):
    def make(self,root,sender):
        cfg=dict(input_upper=10000,output_tokens=256,network_policy=DEFAULT_POLICY)
        b=PersistentBudget(root/'budget.jsonl',run_id='engineering:alf',protocol_hash='fixture',max_calls=2,
                           max_tokens=20512,max_tools=0,max_cost_microusd=30000,
                           token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,
                           max_tool_milliseconds=0,tool_milliseconds_upper=1000,wall_seconds=60)
        return AuditedActionClient(root,b,cfg,sender=sender),b

    def test_action_replays_without_a_second_send(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            def sender(wire):
                calls.append(wire)
                return dict(model='deepseek-flash',choices=[dict(message=dict(content='Think: Inspect.\nAct: look'),
                             finish_reason='stop')],usage=dict(prompt_tokens=50,completion_tokens=10,total_tokens=60))
            client,b=self.make(Path(tmp),sender)
            client.begin('task')
            generator=AlfWorldGenerator(client)
            self.assertEqual(generator.step('Public goal','Public room',['look']).action,'look')
            client.begin('task')
            self.assertEqual(generator.step('Public goal','Public room',['look']).action,'look')
            self.assertEqual(len(calls),1)
            self.assertEqual(b.snapshot()['calls'],1)
            client.begin('task')
            with self.assertRaises(PermissionError):
                generator.step('Changed goal','Public room',['look'])
            self.assertNotIn('expert_plan',str(calls))

    def test_unknown_prevents_new_send(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            def sender(wire):
                calls.append(wire)
                raise OSError('mock transport')
            client,_=self.make(Path(tmp),sender)
            client.begin('task')
            with self.assertRaises(OSError):
                AlfWorldGenerator(client).step('goal','room',['look'])
            client.begin('task')
            with self.assertRaises(RunUnhealthy):
                AlfWorldGenerator(client).step('goal','room',['look'])
            self.assertEqual(len(calls),1)

    def test_done_without_won_does_not_count_as_success(self):
        trace=AlfWorldTrace(success=False,total_steps=50,max_steps=50)
        self.assertEqual(classify_trace(trace),'STEP_LIMIT')
        trace.success=True
        self.assertEqual(classify_trace(trace),'SUCCESS')


if __name__=='__main__':
    unittest.main()


class AlfSelectionTests(unittest.TestCase):
    def test_120_task_selection_is_deterministic_and_excludes_pilot(self):
        from run_alfworld_audited_baseline import select_games

        data=Path('/mock-data')
        inventory=[str(data/('game-'+str(i))) for i in range(134)]
        excluded={'game-'+str(i) for i in range(12)}
        selected=select_games(inventory,data,limit=120,seed=20261108,excluded=excluded)
        self.assertEqual(len(selected),120)
        self.assertEqual(len(set(selected)),120)
        self.assertTrue(all(str(Path(p).relative_to(data)) not in excluded for p in selected))
        self.assertEqual(selected,select_games(inventory,data,limit=120,seed=20261108,excluded=excluded))
        with self.assertRaisesRegex(ValueError,'insufficient'):
            select_games(inventory,data,limit=123,seed=20261108,excluded=excluded)


class AlfContinuationTests(unittest.TestCase):
    def test_only_metered_truncation_can_be_isolated(self):
        from alfworld_.continuation import truncation_receipt
        import time

        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            client,account=AlfBaselineTests().make(root,lambda _:None)
            request='task/0'
            key=account.reserve(100,256,request_id=request,request_hash='fixture')
            response=dict(model='deepseek-flash',choices=[dict(finish_reason='length')],
                          usage=dict(prompt_tokens=50,completion_tokens=256,total_tokens=306))
            account.settle(key,306)
            client.events.append('RAW_RESPONSE',dict(request_id=request,response=response),time.time())
            self.assertEqual(truncation_receipt(root,account,'task')['reason'],'METERED_LENGTH')
            client.events.append('SEND_UNKNOWN',dict(request_id='task/1'),time.time())
            with self.assertRaises(PermissionError):
                truncation_receipt(root,account,'task')

    def test_unmetered_output_cannot_be_isolated(self):
        from alfworld_.continuation import truncation_receipt
        import time

        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            client,account=AlfBaselineTests().make(root,lambda _:None)
            key=account.reserve(100,256,request_id='task/0',request_hash='fixture')
            account.settle(key,50)
            response=dict(model='deepseek-flash',choices=[dict(finish_reason='length')])
            client.events.append('RAW_RESPONSE',dict(request_id='task/0',response=response),time.time())
            with self.assertRaises(PermissionError):
                truncation_receipt(root,account,'task')
