"""Synthetic compile-protocol cases. No candidate execution or live API calls."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from failure_evo import PersistentBudget, BoundedCompiler
from failure_evo.model_api import DeepSeekGenerator, validate_compile_output

DECLINE='def repair_operator(context):\n    return {"status":"declined","reason":"unavailable"}\n'
CONDITIONAL='''def repair_operator(context):
    if context.get("candidate_code"):
        return {"status":"declined","reason":"outside scope"}
    for row in context.get("candidate_ledger", []):
        if row.get("code") and row.get("public_feedback", {}).get("status") == "PUBLIC_PASS":
            return {"status":"applied","selected_candidate_id":row["candidate_id"]}
    return {"status":"declined","reason":"unavailable"}
'''
def artifact(code=CONDITIONAL):
    return dict(code=code,description='Synthetic protocol fixture',applicability='Prior verified candidate or decline')
CONFIG=dict(run_id='mock-b2',protocol_hash='mock-protocol',max_calls=3,max_tokens=208896,
 max_tools=0,max_cost_microusd=300000,token_rate_microusd_per_million=1200000,
 tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=10000,wall_seconds=3600)

class B2ProtocolTests(unittest.TestCase):
    def test_correct_code_json(self):self.assertTrue(validate_compile_output(artifact())['static_pass'])
    def test_action_json_is_contract_error(self):
        self.assertEqual(validate_compile_output({'status':'declined'})['errors'],['COMPILE_OUTPUT_CONTRACT_ERROR'])
    def test_missing_code(self):
        value=artifact();del value['code'];self.assertFalse(validate_compile_output(value)['output_contract_pass'])
    def test_empty_code(self):self.assertFalse(validate_compile_output(artifact('  '))['output_contract_pass'])
    def test_syntax_error(self):self.assertIn('COMPILE_SYNTAX_ERROR',validate_compile_output(artifact('def broken('))['errors'])
    def test_interface_error(self):self.assertIn('COMPILE_INTERFACE_ERROR',validate_compile_output(artifact(DECLINE.replace('(context)','(context, other)')))['errors'])
    def test_illegal_permissions(self):
        for code in ('import os\n'+DECLINE,DECLINE.replace('return ', 'open("/tmp/x"); return ')):
            self.assertIn('COMPILE_PERMISSION_ERROR',validate_compile_output(artifact(code))['errors'])
    def test_truncated_output(self):
        self.assertEqual(validate_compile_output(artifact(),'length')['errors'],['COMPILE_OUTPUT_TRUNCATED'])
    def test_conditional_decline_is_not_functional_proof(self):
        result=validate_compile_output(artifact());self.assertTrue(result['static_pass']);self.assertEqual(result['execution'],'NOT_RUN')
        self.assertEqual(result['recovery_capability'],'APPLIED_BRANCH_PRESENT_EXECUTION_UNVERIFIED')
    def test_unconditional_decline_is_not_recovery(self):
        result=validate_compile_output(artifact(DECLINE));self.assertTrue(result['static_pass'])
        self.assertEqual(result['recovery_capability'],'DECLINE_ONLY_NO_RECOVERY_ESTABLISHED')
    def test_wrong_return_and_dynamic_return_rejected(self):
        for code in (DECLINE.replace('"declined"','"success"'), 'def repair_operator(context):\n    return context\n', 'def repair_operator(context):\n    if context:\n        return {"status":"declined"}\n'):
            self.assertIn('COMPILE_RETURN_PROTOCOL_ERROR',validate_compile_output(artifact(code))['errors'])
    def test_import_and_mock_transport_preserve_contract_failures(self):
        for content,finish,expected in [(json.dumps(artifact()),'stop',None),('{"status":"declined"}','stop','COMPILE_OUTPUT_CONTRACT_ERROR'),('{"code":','length','COMPILE_OUTPUT_TRUNCATED')]:
            with self.subTest(expected=expected),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);budget=PersistentBudget(root/'budget',**CONFIG);calls=[]
                def transport(*args):
                    calls.append(args[0]);self.assertEqual(budget.calls,1)
                    return dict(model='deepseek-flash',usage={'total_tokens':30},choices=[dict(finish_reason=finish,message={'content':content})])
                approval=dict(api_spend_authorized=True,run_id='mock-b2',protocol_hash='mock-protocol',max_cost_microusd=300000)
                compiler=BoundedCompiler(DeepSeekGenerator(budget,authorization=approval,transport=transport),budget,root/'compiler','deepseek-flash')
                job=dict(stream_id='s',family_id='f');spec=root/'spec';spec.write_text('reviewed fixture')
                job['specification']=compiler.import_specification(job,spec,1);self.assertEqual(budget.calls,0)
                with patch.dict('os.environ',{'DEEPSEEK_API_KEY':'mock-key'}):
                    if expected:
                        with self.assertRaisesRegex(ValueError,expected):compiler.request(job,'candidate',0,2)
                    else:self.assertTrue(compiler.request(job,'candidate',0,2)['compile_review']['static_pass'])
                self.assertEqual(len(calls),1);self.assertIn('raw_response',(root/'compiler').read_text())
                self.assertNotIn('mock-key',(root/'compiler').read_text())
                spec.write_text('changed')
                with self.assertRaisesRegex(ValueError,'specification changed'):compiler.request(job,'candidate',1,3)
                self.assertEqual(budget.calls,1)

class B2BatchTests(unittest.TestCase):
    def test_first_failure_stops_and_success_allows_only_three(self):
        import importlib.util
        from unittest.mock import MagicMock
        path=Path(__file__).resolve().parents[2]/'scripts/generate_s12_b2.py'
        spec=importlib.util.spec_from_file_location('b2_batch_test',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for first,expected_calls in [({'status':'declined'},1),(artifact(),3),(artifact('def bad('),1)]:
            with self.subTest(expected_calls=expected_calls),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);run=root/'run';run.mkdir();(run/'specification_v2.txt').write_text('fixture')
                approval=dict(api_spend_authorized=True,run_id='mock-b2',protocol_hash='mock-protocol',max_cost_microusd=300000,user_authorization_text='SYNTHETIC TEST ONLY')
                module.write(root/'authorization.json',approval)
                config=dict(run_id='mock-b2',protocol_hash='mock-protocol',budget={k:v for k,v in CONFIG.items() if k not in ('run_id','protocol_hash')},facts_path='fixture',model='deepseek-flash',base_commit='fixture')
                job=dict(stream_id='s',family_id='f',evidence_ids=['e'],specification='fixture')
                store=MagicMock();store.visible.return_value=[dict(event_id='e',synthetic=False)]
                calls=[]
                def transport(*args):
                    calls.append(args[0]);return dict(model='deepseek-flash',usage={'total_tokens':30},choices=[dict(finish_reason='stop',message={'content':json.dumps(first)})])
                def provider(budget,authorization):return DeepSeekGenerator(budget,authorization=authorization,transport=transport)
                with patch.object(module,'ROOT',root),patch.object(module,'check_frozen',return_value=(config,job)),patch.object(module,'FailureEvidenceStore',return_value=store),patch.object(module,'FailureOperatorRegistry'),patch.object(module,'DeepSeekGenerator',side_effect=provider),patch.dict('os.environ',{'DEEPSEEK_API_KEY':'mock-key'}):
                    result=module.generate(run,root/'authorization.json')
                    self.assertEqual(len(calls),expected_calls)
                    self.assertEqual(result['real_execution'],'NOT_RUN')
                    with self.assertRaises(FileExistsError):module.generate(run,root/'authorization.json')
                    self.assertEqual(len(calls),expected_calls)

if __name__=='__main__':unittest.main()
