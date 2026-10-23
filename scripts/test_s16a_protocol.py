"""Zero-provider protocol regression tests; fake senders and temporary budgets."""
import copy, dataclasses, json, tempfile, unittest
from pathlib import Path
from unittest.mock import Mock
import learn_reuse30 as old
from failure_evo.workflow_protocol_v2 import *
from failure_evo.workflow_runtime_v2 import PreparedController
from failure_evo.runtime import Budget
from failure_evo.contracts import Fingerprint
from review_s16a_protocol import S15, normalize, review_blocks, review_memory, review_revision, snapshot

def response(text='```python\nprint(1)\n```',finish='stop'):
    return dict(model='deepseek-flash',usage=dict(prompt_tokens=4,completion_tokens=3,total_tokens=7),choices=[dict(message=dict(content=text),finish_reason=finish)])

class SharedProtocolTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.d=Path(self.tmp.name)
    def transport(self,calls=8,sender=None):
        ledger=old.PersistentBudget(self.d/f'{len(list(self.d.iterdir()))}.jsonl',run_id='mock-only',protocol_hash='test',**old.config(calls,0,1000000,65536))
        sender=sender or Mock(return_value=response());audit=[]
        tr=SharedTransport(ledger,sender,authorized=dict(run_id='mock-only',protocol_hash='test'),audit=audit)
        return tr,sender,ledger
    def prepared(self,text='task',**kw):return prepare([dict(role='user',content=text)],**kw)
    def test_prose_and_arithmetic_not_source(self):
        for text in ['Let us think. We need to solve the following problem.', '```\nx + y\n```','```\n(their total living value) - (opponents total living value)\n```']:
            self.assertEqual(delivery(text,'length')['code'],'')
    def test_valid_length_source_not_rejected(self):
        self.assertEqual(delivery('```python\nprint(1)','length')['code'],'print(1)')
        note=delivery('```python\ndef solve():\n    pass\n```','length')
        self.assertTrue(note['syntax_ok']);self.assertTrue(note['definitions_and_imports_only'])
    def test_partial_typed_source_not_fabricated(self):
        self.assertEqual(delivery('```python\ndef f(\n```')['code'],'def f(')
        self.assertFalse(delivery('```python\ndef f(\n```')['syntax_ok'])
    def test_bare_program_and_multiple_fences(self):
        self.assertEqual(delivery('import sys\nprint(sys.stdin.read())')['code'],'import sys\nprint(sys.stdin.read())')
        self.assertEqual(delivery('```\nx+y\n```\n```python\nprint(2)\n```')['code'],'print(2)')
        self.assertEqual(delivery('```python\nprint(1)\n```\n```python\nprint(2)\n```')['code'],'print(1)')
    def test_missing_code_feedback_is_not_false_compile(self):
        msg,a=repair_messages(dict(problem_id='t',prompt='problem'),'Long prose.',dict(status='COMPILE_ERROR',public_cases=[]),finish_reason='length')
        self.assertIn('NO_COMPLETE_CODE',msg[-1]['content']);self.assertNotIn('COMPILE_ERROR',msg[-1]['content']);self.assertEqual(a['code'],'')
    def test_body_copy_cannot_change_prepared_wire(self):
        p=self.prepared();p.body['messages'][0]['content']='changed'
        self.assertEqual(p.body['messages'][0]['content'],'task')
        self.assertEqual(p.measures['serialized_utf8_bytes'],len(p.wire.encode()))
    def test_preflight_before_both_reservations(self):
        tr,sender,ledger=self.transport();local=Budget();before=ledger.snapshot()
        with self.assertRaises(PreflightRejected):
            p=self.prepared('x'*40000);tr.send(p,task_budget=local,request_id='x',capability='test')
        self.assertEqual(local.calls,0);self.assertEqual(ledger.snapshot(),before);sender.assert_not_called()
    def test_distinct_wire_and_token_upper(self):
        with self.assertRaises(PreflightRejected) as cm:self.prepared('x'*100,limits=Limits(input_token_upper=65536,wire_bytes=10))
        self.assertEqual(cm.exception.reason,'WIRE_BYTES_LIMIT')
        p=self.prepared('中文',limits=Limits(envelope_margin=100))
        tr,sender,ledger=self.transport();tr.send(p,request_id='custom-margin',capability='test')
        self.assertEqual(sender.call_args.args[0],p.wire.encode())
    def test_exact_sent_bytes_single_charge(self):
        tr,sender,ledger=self.transport();b=Budget(max_calls=1);p=self.prepared('quote " slash \\ newline\n 中文')
        tr.send(p,task_budget=b,request_id='1',capability='test')
        self.assertEqual(sender.call_args.args[0],p.wire.encode());self.assertEqual(b.calls,1);self.assertEqual(b.used_tokens,7);self.assertEqual(ledger.calls,1)
        self.assertEqual(tr.audit[-1]['status'],'COMPLETED')
    def test_task_rejection_before_run_reserve(self):
        tr,sender,ledger=self.transport();b=Budget(max_calls=0)
        with self.assertRaises(PreflightRejected):tr.send(self.prepared(),task_budget=b,request_id='x',capability='test')
        self.assertEqual(ledger.calls,0);self.assertEqual(b.calls,0);sender.assert_not_called()
    def test_run_rejection_rolls_back_unsent_local(self):
        tr,sender,ledger=self.transport(calls=0);b=Budget();before=b.snapshot()
        with self.assertRaises(BudgetExhausted):tr.send(self.prepared(),task_budget=b,request_id='x',capability='test')
        self.assertEqual(before,b.snapshot());self.assertEqual(ledger.calls,0);sender.assert_not_called()
    def test_unknown_send_is_charged_no_auto_retry(self):
        sender=Mock(side_effect=TimeoutError('unknown after send'));tr,_,ledger=self.transport(sender=sender);b=Budget();p=self.prepared()
        with self.assertRaises(TimeoutError):tr.send(p,task_budget=b,request_id='x',capability='test')
        self.assertEqual(ledger.snapshot()['unknown_or_pending_requests'],['x']);self.assertEqual(b.used_tokens,p.input_upper+p.output_upper)
        with self.assertRaises(ValueError):tr.send(p,task_budget=b,request_id='x',capability='test')
        self.assertEqual(b.calls,1);self.assertEqual(sender.call_count,1)
    def test_usage_contract_keeps_unknown_reservation(self):
        bad=response();bad['usage']['completion_tokens']=9000;bad['usage']['total_tokens']=9004
        tr,sender,ledger=self.transport(sender=Mock(return_value=bad));b=Budget()
        with self.assertRaises(ValueError):tr.send(self.prepared(),task_budget=b,request_id='bad',capability='test')
        self.assertEqual(ledger.snapshot()['unknown_or_pending_requests'],['bad']);self.assertEqual(tr.audit[-1]['status'],'UNKNOWN')
    def test_run_authorization_and_tamper_fail_closed(self):
        tr,sender,ledger=self.transport();p=self.prepared();tr.authorized={'run_id':'old','protocol_hash':'test'}
        with self.assertRaises(PermissionError):tr.send(p,request_id='x',capability='test')
        tr.authorized={'run_id':'mock-only','protocol_hash':'test'}
        with self.assertRaises(ValueError):tr.send(dataclasses.replace(p,input_upper=1),request_id='x',capability='test')
        sender.assert_not_called();self.assertEqual(ledger.calls,0)
    def test_memory_structured_errors(self):
        self.assertEqual(validate_memory(dict(text='{"memory":"'+('x'*6001)+'"}'))['over_by'],1)
        for value,reason in [(dict(text='{}'),'MEMORY_SCHEMA_MISMATCH'),(dict(text='{'),'MEMORY_JSON_INVALID'),(dict(text='{"memory":" "}'),'MEMORY_EMPTY'),(dict(text='{"memory":"ok"}',finish_reason='length'),'MEMORY_OUTPUT_TRUNCATED')]:
            self.assertEqual(validate_memory(value)['error'],reason)
        self.assertTrue(validate_memory(dict(text='{"memory":"ok"}'))['passed'])
    def test_memory_one_repair_in_same_budget(self):
        sender=Mock(side_effect=[response(json.dumps({'memory':'x'*6001})),response('{"memory":"public evidence only"}')])
        tr,_,ledger=self.transport(calls=2,sender=sender)
        value=update_memory(tr,{'old':'kept'},[],request_prefix='M',allow_revision=True)
        self.assertTrue(value['updated']);self.assertEqual(len(value['versions']),2);self.assertEqual(ledger.calls,2)
        self.assertEqual(value['versions'][0]['diagnosis']['error'],'MEMORY_TEXT_TOO_LONG')
    def test_memory_failed_repair_keeps_previous_no_third_request(self):
        sender=Mock(return_value=response(json.dumps({'memory':'x'*6001})));tr,_,ledger=self.transport(sender=sender)
        previous={'old':'kept'};value=update_memory(tr,previous,[],request_prefix='M',allow_revision=True)
        self.assertFalse(value['updated']);self.assertEqual(value['memory'],previous);self.assertEqual(sender.call_count,2)
        with self.assertRaises(ValueError):memory_messages(previous,[],revision=2,failed_response={})
    def test_memory_budget_not_extended_for_revision(self):
        tr,sender,ledger=self.transport(calls=1,sender=Mock(return_value=response(json.dumps({'memory':'x'*6001}))))
        value=update_memory(tr,'old',[],request_prefix='M',allow_revision=True)
        self.assertFalse(value['updated']);self.assertEqual(value['memory'],'old');self.assertEqual(sender.call_count,1);self.assertEqual(ledger.calls,1)
    def test_controller_actual_shared_path_no_phantom_call(self):
        tr,sender,ledger=self.transport(sender=Mock(side_effect=[response('Long prose with no program.','length'),response()]))
        client=WorkflowClient(tr,'t');b=Budget(max_calls=2);fp=Fingerprint('b','d','deepseek-flash','w','p')
        ctrl=PreparedController(client,lambda *a:dict(visibility='public',status='PUBLIC_PASS'),fp,max_output=8192)
        result=ctrl.solve(dict(problem_id='t',prompt='Print 1'),b)
        self.assertEqual(result['status'],'PUBLIC_ACCEPTED');self.assertEqual(b.calls,2);self.assertEqual(ledger.calls,2);self.assertEqual(b.used_tokens,14)
        self.assertEqual(result['events'][0]['public_feedback']['status'],'NO_COMPLETE_CODE')
        self.assertNotIn('Long prose with no program.',json.loads(sender.call_args.args[0])['messages'][-1]['content'])
    def test_controller_preflight_failure_not_counted(self):
        tr,sender,ledger=self.transport();b=Budget();fp=Fingerprint('b','d','deepseek-flash','w','p')
        ctrl=PreparedController(WorkflowClient(tr,'t',limits=Limits(input_token_upper=10)),lambda *a:self.fail('evaluation'),fp)
        r=ctrl.solve(dict(problem_id='t',prompt='task'),b)
        self.assertEqual(r['events'][0]['request_state'],'NOT_SENT');self.assertEqual(b.calls,0);self.assertEqual(ledger.calls,0);sender.assert_not_called()
    def test_G_M_F_share_base_builder_and_budget(self):
        wires=[]
        for arm in ['G','M','F']:
            tr,sender,ledger=self.transport();client=WorkflowClient(tr,'t',memory='experience' if arm=='M' else '');b=Budget(max_calls=1)
            payload=dict(task=dict(problem_id='t',prompt='p'),stage='l2a',temperature=0,previous_candidate='print(0)',feedback=dict(status='WRONG_ANSWER'))
            client(payload,b);self.assertEqual(b.calls,1);self.assertEqual(ledger.calls,1);wires.append(json.loads(sender.call_args.args[0]))
        self.assertEqual(wires[0],wires[2]);self.assertEqual(wires[1]['messages'][1]['content'],wires[0]['messages'][1]['content']+'\nPreviously learned failure experience (advice, not proof):\nexperience')
    def test_policy_host_request_shares_native_allowance(self):
        tr,sender,ledger=self.transport();client=WorkflowClient(tr,'t');b=Budget(max_calls=1)
        client.host_repair(dict(task_public=dict(problem_id='t',prompt='p'),candidate_code='print(0)',public_feedback=dict(status='WRONG_ANSWER')),'Use actual feedback',b)
        with self.assertRaises(PreflightRejected):client(dict(task=dict(problem_id='t',prompt='p'),stage='l1',temperature=0),b)
        self.assertEqual(ledger.calls,1);self.assertEqual(sender.call_count,1)
    def test_compact_contexts_lossless_and_delivery_present(self):
        d=S15/'operators/public_feedback_repair_policy/b0-c1-r0';ev=old.read(d/'functional.json');code=(d/'repaired_source.py').read_text();resp=normalize(old.read(d/'source_execution/response_1.json'))
        c=compact_diagnosis(ev,solver_response=resp,proposed_code=code)
        for a,b in zip(ev['checks'],c['checks']):self.assertEqual(a['input'],restore_context(c['context_base'],b['input_patch']))
        self.assertEqual(c['delivery']['finish_reason'],'stop');self.assertEqual(c['proposed_program'],code)
    def test_static_diagnosis_preserved_and_revision_slot_unique(self):
        tr,sender,ledger=self.transport()
        diag=dict(passed=False,findings=['line 4: forbidden getattr'])
        result=revise_policy(tr,'frozen contract','original output',diag,request_prefix='candidate-1')
        self.assertIn('line 4: forbidden getattr',json.loads(sender.call_args.args[0])['messages'][-1]['content'])
        with self.assertRaises(ValueError):revise_policy(tr,'frozen contract','original output',diag,request_prefix='candidate-1')
        self.assertEqual(sender.call_count,1)
    def test_three_arms_share_persistent_ledger_without_id_collision(self):
        tr,sender,ledger=self.transport();budgets=[]
        for arm in ('G','M','F'):
            b=Budget(max_calls=1);budgets.append(b)
            WorkflowClient(tr,f'{arm}/same-task')(dict(task=dict(problem_id='t',prompt='p'),stage='l1',temperature=0),b)
        self.assertEqual(ledger.calls,3);self.assertEqual(sender.call_count,3)
        self.assertEqual([b.calls for b in budgets],[1,1,1])
        self.assertEqual(len({r['request_id'] for r in tr.audit}),3)
    def test_memory_unknown_send_not_recorded_as_unsent_or_retried(self):
        tr,sender,ledger=self.transport(sender=Mock(side_effect=BudgetExhausted('unknown provider failure')))
        with self.assertRaises(BudgetExhausted):update_memory(tr,'old',[],request_prefix='M',allow_revision=True)
        self.assertEqual(sender.call_count,1);self.assertEqual(tr.audit[-1]['status'],'UNKNOWN')
        self.assertEqual(ledger.snapshot()['unknown_or_pending_requests'],['M/r0'])
    def test_historical_real_preflights(self):
        self.assertEqual(len(review_blocks()),8);self.assertEqual(len(review_memory()),2)
        self.assertEqual(review_revision()['contexts_restored'],6);self.assertFalse(snapshot()['changed'])

if __name__=='__main__':unittest.main()
