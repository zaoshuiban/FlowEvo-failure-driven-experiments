"""Transport and host-contract tests only; never certify Linux isolation."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from failure_evo import PersistentBudget, BoundedCompiler
from failure_evo.model_api import DeepSeekGenerator
from failure_evo.checkpoint_evaluator import resolve_action, compare_output, CheckpointEvaluator

CONFIG=dict(run_id='fixture-new-run',protocol_hash='frozen',max_calls=7,max_tokens=487424,
 max_tools=128,max_cost_microusd=600000,token_rate_microusd_per_million=1200000,
 tool_cost_upper_microusd=1000,max_tool_milliseconds=1280000,
 tool_milliseconds_upper=10000,wall_seconds=3600)

class S12A2Acceptance(unittest.TestCase):
    def test_wire_prompt_no_tools_and_frozen_reasoning(self):
        q=dict(stream_id='s',family_id='f',phase='candidate',slot=0,max_tokens=4096)
        body=DeepSeekGenerator.prepare(q)
        self.assertEqual(body['thinking'],{'type':'disabled'})
        self.assertEqual(body['reasoning_effort'],'none')
        self.assertNotIn('tools',body)
        with self.assertRaises(ValueError):DeepSeekGenerator.prepare(dict(q,max_tokens=32768))

    def test_unauthorized_does_not_read_key_or_send(self):
        with tempfile.TemporaryDirectory() as tmp:
            budget=PersistentBudget(Path(tmp)/'budget',**CONFIG)
            def forbidden(*a):self.fail('transport must not run')
            provider=DeepSeekGenerator(budget,transport=forbidden)
            with self.assertRaises(PermissionError):provider({})
            self.assertEqual(budget.calls,0)

    def test_one_request_reserved_before_transport_and_raw_response_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);budget=PersistentBudget(root/'budget',**CONFIG);calls=[]
            approval=dict(api_spend_authorized=True,run_id=CONFIG['run_id'],protocol_hash='frozen',max_cost_microusd=600000)
            def transport(body,key,timeout):
                self.assertEqual(budget.calls,1);self.assertEqual(len(budget.reservations),1)
                calls.append(body)
                return dict(model='deepseek-flash',id='fixture',usage={'total_tokens':50},choices=[dict(finish_reason='stop',message={'content':'{"specification":"fixture spec"}'})])
            provider=DeepSeekGenerator(budget,authorization=approval,transport=transport)
            compiler=BoundedCompiler(provider,budget,root/'compiler','deepseek-flash')
            with patch.dict('os.environ',{'DEEPSEEK_API_KEY':'synthetic-test-key'}):
                compiler.request(dict(stream_id='s',family_id='f',job_id='j'),'induction',0,1)
                with self.assertRaises(ValueError):compiler.request(dict(stream_id='s',family_id='f',job_id='j'),'induction',0,1)
            self.assertEqual(len(calls),1)
            self.assertNotIn('synthetic-test-key',(root/'compiler').read_text())
            self.assertIn('raw_response',(root/'compiler').read_text())
            self.assertGreater(budget.snapshot()['charged_or_reserved_cost_microusd'],0)

    def test_transport_failure_not_retried_or_refunded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);budget=PersistentBudget(root/'budget',**CONFIG);calls=[]
            approval=dict(api_spend_authorized=True,run_id=CONFIG['run_id'],protocol_hash='frozen',max_cost_microusd=600000)
            def failure(*a):calls.append(1);raise TimeoutError('fixture')
            compiler=BoundedCompiler(DeepSeekGenerator(budget,authorization=approval,transport=failure),budget,root/'compiler','deepseek-flash')
            with patch.dict('os.environ',{'DEEPSEEK_API_KEY':'synthetic-test-key'}):
                with self.assertRaises(TimeoutError):compiler.request(dict(stream_id='s',family_id='f'),'induction',0,1)
            self.assertEqual(calls,[1]);self.assertEqual(len(budget.reservations),1)

    def test_malformed_provider_response_is_preserved(self):
        responses=[[],dict(model='deepseek-flash',usage={'total_tokens':1},choices=[dict(finish_reason='stop',message={'content':'[]'})])]
        for raw in responses:
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);budget=PersistentBudget(root/'budget',**CONFIG)
                approval=dict(api_spend_authorized=True,run_id=CONFIG['run_id'],protocol_hash='frozen',max_cost_microusd=600000)
                provider=DeepSeekGenerator(budget,authorization=approval,transport=lambda *a:raw)
                compiler=BoundedCompiler(provider,budget,root/'compiler','deepseek-flash')
                with patch.dict('os.environ',{'DEEPSEEK_API_KEY':'synthetic-test-key'}):
                    with self.assertRaises(ValueError):compiler.request(dict(stream_id='s',family_id='f'),'induction',0,1)
                self.assertIn('raw_response',(root/'compiler').read_text())
                self.assertEqual(budget.calls,1)

    def test_operator_cannot_forge_test_success(self):
        result=dict(status='applied',selected_candidate_id='c1',validation_status='passed',actual_cost=0)
        self.assertEqual(resolve_action(result,[dict(candidate_id='c1',code='print(0)')]),'print(0)')
        self.assertFalse(compare_output('0','1','whitespace_token_exact'))
        with self.assertRaises(ValueError):resolve_action(dict(result,registry_permission='Active'),[])
        with self.assertRaises(ValueError):resolve_action(result,[])
        with self.assertRaises(ValueError):resolve_action(dict(status='declined',candidate_code='print(0)'),[])
        with self.assertRaises(ValueError):compare_output('1','1','unreviewed_checker')

    def test_blocked_worker_cannot_construct_real_evaluator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);proof=root/'worker.json';proof.write_text('{"status":"BLOCKED"}')
            budget=PersistentBudget(root/'budget',**CONFIG)
            with self.assertRaises(RuntimeError):
                CheckpointEvaluator(root,budget,image='none',worker_script=__file__,acceptance_path=proof)

if __name__=='__main__':unittest.main()
