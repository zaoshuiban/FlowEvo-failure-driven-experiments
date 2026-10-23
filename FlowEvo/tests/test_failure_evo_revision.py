"""End-to-end mocked generation/revision. Never executes generated source."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from failure_evo import PersistentBudget, BoundedCompiler
from failure_evo.compiler_contract import build_compiler_contract
from failure_evo.candidate_revision import compile_candidate
from failure_evo.model_api import DeepSeekGenerator
from test_failure_evo_b2 import CONFIG, artifact, CONDITIONAL

BAD='''def repair_operator(context):
    for case in context['public_feedback']['public_cases']:
        if case.get('status') == 'PASS':
            return {'status':'declined'}
    return {'status':'declined'}
'''

class RevisionTests(unittest.TestCase):
    def exercise(self, outputs, *, max_calls=2, fail_transport=False, design_checker=None):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        budget=PersistentBudget(root/'budget',**dict(CONFIG,max_calls=max_calls))
        calls=[]
        def transport(body,key,timeout):
            calls.append(body)
            self.assertTrue(budget.reservations)
            if fail_transport:raise TimeoutError('mock')
            return dict(model='deepseek-flash',id=str(len(calls)),usage={'total_tokens':50},choices=[dict(finish_reason='stop',message={'content':json.dumps(outputs[len(calls)-1])})])
        provider=DeepSeekGenerator(budget,authorization=dict(api_spend_authorized=True,run_id=CONFIG['run_id'],protocol_hash=CONFIG['protocol_hash'],max_cost_microusd=CONFIG['max_cost_microusd']),transport=transport)
        compiler=BoundedCompiler(provider,budget,root/'compiler','deepseek-flash')
        job=dict(stream_id='s',family_id='f',host_contract=build_compiler_contract())
        spec=root/'spec';spec.write_text('mock spec');job['specification']=compiler.import_specification(job,spec,1)
        with patch.dict('os.environ',{'DEEPSEEK_API_KEY':'mock-key'}):
            result=compile_candidate(compiler,job,0,root/'versions',design_checker=design_checker)
        return root,budget,compiler,job,calls,result
    def test_functional_failure_drives_one_revision(self):
        checks=iter([{'eligible':False,'reason':'source still fails'},{'eligible':True}])
        *_,calls,result=self.exercise([artifact(),artifact()],design_checker=lambda p:next(checks))
        self.assertEqual(len(calls),2)
        self.assertEqual(result['functional_acceptance'],'DEVELOPMENT_PASSED_NOT_GATE')
        request=json.loads(calls[1]['messages'][1]['content'])
        self.assertEqual(request['functional_diagnostics']['reason'],'source still fails')
    def test_repeated_functional_failure_stops(self):
        *_,calls,result=self.exercise([artifact(),artifact()],design_checker=lambda p:{'eligible':False})
        self.assertEqual(len(calls),2)
        self.assertEqual(result['source_acceptance'],'NOT_ACCEPTED')
        self.assertEqual(result['functional_acceptance'],'DEVELOPMENT_FAILED')
        self.assertEqual(result['stop_reason'],'REVISION_DEVELOPMENT_REJECTED')
    def test_functional_revision_cannot_use_modified_diagnostics(self):
        root,budget,compiler,job,calls,result=self.exercise([artifact()],max_calls=1,design_checker=lambda p:{'eligible':False})
        request=json.loads((root/'versions/revision_input.json').read_text())
        request['functional_diagnostics']={'eligible':True}
        with self.assertRaises(ValueError):compiler.request(request,'revision',0,4)
        self.assertEqual(len(calls),1)
    def test_wire_preflight_failure_does_not_consume_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);budget=PersistentBudget(root/'budget',**CONFIG)
            class Provider:
                @staticmethod
                def prepare(request):raise ValueError('invalid frozen wire request')
                def __call__(self,request):raise AssertionError('transport must not run')
            compiler=BoundedCompiler(Provider(),budget,root/'compiler','deepseek-flash')
            with self.assertRaises(ValueError):compiler.request({'stream_id':'s','family_id':'f'},'induction',0,1)
            self.assertEqual(budget.calls,0)
            self.assertEqual(compiler.events.records(),[])
    def test_escaped_source_reserved_from_wire_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);budget=PersistentBudget(root/'budget',**CONFIG);bodies=[]
            def transport(body,key,timeout):
                bodies.append(body)
                from failure_evo.contracts import canonical
                self.assertGreaterEqual(next(iter(budget.reservations.values())),len(canonical(body).encode())+4096)
                return dict(model='deepseek-flash',usage={'total_tokens':30},choices=[dict(finish_reason='stop',message={'content':'{"specification":"fixture"}'})])
            approval=dict(api_spend_authorized=True,run_id=CONFIG['run_id'],protocol_hash=CONFIG['protocol_hash'],max_cost_microusd=CONFIG['max_cost_microusd'])
            compiler=BoundedCompiler(DeepSeekGenerator(budget,authorization=approval,transport=transport),budget,root/'compiler','deepseek-flash')
            with patch.dict('os.environ',{'DEEPSEEK_API_KEY':'mock'}):
                compiler.request(dict(stream_id='s',family_id='f',text='\\"'*4000),'induction',0,1)
            self.assertEqual(len(bodies),1)
    def test_error_drives_single_successful_revision(self):
        root,budget,compiler,job,calls,result=self.exercise([artifact(BAD),artifact()])
        self.assertEqual(len(calls),2);self.assertEqual(result['accepted_phase'],'revision')
        self.assertEqual(result['functional_acceptance'],'NOT_RUN')
        request=json.loads(calls[1]['messages'][1]['content'])
        self.assertEqual(request['revision_parent']['code'],BAD)
        self.assertEqual(request['static_diagnostics']['errors'],['COMPILE_CONTEXT_CONTRACT_ERROR'])
        self.assertEqual(request['host_contract'],build_compiler_contract())
        self.assertEqual((root/'versions/candidate.py').read_text(),BAD)
        self.assertEqual((root/'versions/revision.py').read_text(),CONDITIONAL)
        restored=PersistentBudget(root/'budget',**dict(CONFIG,max_calls=2))
        self.assertEqual(restored.calls,2);self.assertGreater(restored.snapshot()['charged_or_reserved_cost_microusd'],0)
        with self.assertRaises(FileExistsError):compile_candidate(compiler,job,0,root/'versions')
        with self.assertRaises(ValueError):compiler.request(job,'revision',0,4)
        self.assertEqual(len(calls),2)
    def test_extra_field_is_revised_without_silent_normalization(self):
        bad=artifact();bad['specification']='extra forbidden compile field'
        root,budget,compiler,job,calls,result=self.exercise([bad,artifact()])
        self.assertEqual(len(calls),2)
        self.assertEqual(result['accepted_phase'],'revision')
        self.assertEqual(result['versions'][0]['review']['errors'],['COMPILE_OUTPUT_CONTRACT_ERROR'])
        saved=json.loads((root/'versions/candidate.json').read_text())
        self.assertEqual(saved['response']['rejected_compile_output'],bad)
        request=json.loads(calls[1]['messages'][1]['content'])
        self.assertEqual(request['static_diagnostics']['errors'],['COMPILE_OUTPUT_CONTRACT_ERROR'])

    def test_initial_pass_has_no_revision(self):
        *_,calls,result=self.exercise([artifact()]);self.assertEqual(len(calls),1);self.assertEqual(result['accepted_phase'],'candidate')
    def test_second_failure_stops(self):
        *_,calls,result=self.exercise([artifact(BAD),artifact(BAD)]);self.assertEqual(len(calls),2);self.assertEqual(result['stop_reason'],'REVISION_STATIC_REJECTED')
    def test_no_source_action_json_not_repaired(self):
        *_,calls,result=self.exercise([{'status':'declined'}]);self.assertEqual(len(calls),1);self.assertEqual(result['source_acceptance'],'NOT_ACCEPTED')
    def test_budget_exhaustion_blocks_revision(self):
        *_,calls,result=self.exercise([artifact(BAD)],max_calls=1);self.assertEqual(len(calls),1);self.assertEqual(result['source_acceptance'],'NOT_ACCEPTED')
    def test_transport_failure_is_not_revision_or_retry(self):
        *_,calls,result=self.exercise([],fail_transport=True);self.assertEqual(len(calls),1);self.assertEqual(result['stop_reason'],'REQUEST_FAILED_NO_RETRY')
    def test_host_projection_drops_invented_fields(self):
        c=build_compiler_contract();self.assertEqual(set(c['case_fields']),{'input','expected','actual','exception_class'})
        self.assertNotIn('status',c['examples']['public_pass']['public_cases'][0]);self.assertIn('candidate_ledger',c['payload_fields'])
    def test_changed_parent_or_diagnostics_block_before_call(self):
        root,budget,compiler,job,calls,result=self.exercise([artifact(BAD)],max_calls=1)
        revision=json.loads((root/'versions/revision_input.json').read_text())
        for field in ('revision_parent','static_diagnostics'):
            altered=json.loads(json.dumps(revision))
            if field=='revision_parent':altered[field]['code']='tampered'
            else:altered[field]['errors']=[]
            with self.assertRaises(ValueError):compiler.request(altered,'revision',0,4)
        self.assertEqual(len(calls),1)

class RevisionRunnerTests(unittest.TestCase):
    def test_frozen_runner_authorization_and_mock_revision(self):
        import importlib.util
        root=Path(__file__).resolve().parents[2]
        spec=importlib.util.spec_from_file_location('revision_runner_test',root/'scripts/generate_s12_revision.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(dir=root/'runs') as tmp:
            run=Path(tmp)/'mock-run';config=module.prepare(run);module.check(run)
            with self.assertRaises(PermissionError):module.generate(run,run/'authorization.pending.json')
            self.assertFalse((run/'budget.jsonl').exists())
            approval=module.read(run/'authorization.pending.json');approval.update(api_spend_authorized=True,user_authorization_text='MOCK ONLY')
            module.write(run/'mock-approval.json',approval)
            calls=[]
            def transport(body,key,timeout):
                calls.append(body);value=artifact(BAD) if len(calls)==1 else artifact()
                return dict(model='deepseek-flash',usage={'total_tokens':50},choices=[dict(finish_reason='stop',message={'content':json.dumps(value)})])
            def provider(budget,authorization):return DeepSeekGenerator(budget,authorization=authorization,transport=transport)
            with patch.object(module,'DeepSeekGenerator',wraps=DeepSeekGenerator) as cls,patch.dict('os.environ',{'DEEPSEEK_API_KEY':'mock-key'}):
                cls.side_effect=provider
                result=module.generate(run,run/'mock-approval.json')
                self.assertEqual(result['source_acceptance'],'SHADOW_STATIC_ONLY')
                self.assertEqual(len(calls),2);self.assertTrue((run/'shadow_registry.jsonl').exists())
                with self.assertRaises(FileExistsError):module.generate(run,run/'mock-approval.json')
            source=run/'host_contract.json';source.write_text('{}')
            with self.assertRaises(ValueError):module.check(run)

if __name__=='__main__':unittest.main()
