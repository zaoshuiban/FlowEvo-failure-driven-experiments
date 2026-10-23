"""No API: real saved inputs cross frozen preflight and mock transport."""
import json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from experiment_capacity_nursery import ROOT, CapacityGenerator, read
from failure_evo import PersistentBudget, BoundedCompiler
from failure_evo.contracts import fingerprint, canonical
from test_failure_evo_b2 import CONFIG, artifact
OLD=ROOT/'runs/s12g_capacity_20261022_01'

class DiagnosticTests(unittest.TestCase):
    def setup_compiler(self,tmp,request,transport):
        root=Path(tmp);budget=PersistentBudget(root/'budget',**dict(CONFIG,max_calls=2))
        provider=CapacityGenerator(budget,authorization=dict(api_spend_authorized=True,run_id=CONFIG['run_id'],protocol_hash=CONFIG['protocol_hash'],max_cost_microusd=CONFIG['max_cost_microusd']),transport=transport)
        compiler=BoundedCompiler(provider,budget,root/'compiler','deepseek-flash')
        compiler.import_specification(request,OLD/'specification.txt',1)
        return compiler,provider,budget

    def test_saved_requests_wire_identity_and_single_revision(self):
        for number,slot in ((1,0),(3,2)):
            with self.subTest(number=number),tempfile.TemporaryDirectory() as tmp:
                request=read(OLD/f'candidate_{number}/revision_input.json');request.update(phase='revision',slot=slot,max_tokens=4096)
                wire=canonical(CapacityGenerator.prepare(request));calls=[]
                def transport(body,key,timeout):
                    self.assertEqual(canonical(body),wire);self.assertTrue(budget.reservations)
                    calls.append(body)
                    return dict(model='deepseek-flash',usage={'total_tokens':10},choices=[dict(finish_reason='stop',message={'content':json.dumps(artifact())})])
                compiler,provider,budget=self.setup_compiler(tmp,request,transport)
                review=compiler.import_candidate(request,slot,OLD/f'candidate_{number}/candidate.py',OLD/f'candidate_{number}/candidate.json',2)
                self.assertEqual(review,request['static_diagnostics'])
                with patch.dict('os.environ',{'DEEPSEEK_API_KEY':'mock'}):compiler.request(request,'revision',slot,3)
                with self.assertRaises(ValueError):compiler.request(request,'revision',slot,4)
                self.assertEqual(len(calls),1)
                preflight=next(r['payload'] for r in compiler.events.records() if r['kind']=='WIRE_PREFLIGHT')
                self.assertEqual(preflight['wire_sha256'],fingerprint(json.loads(wire)))

    def test_import_does_not_create_paid_generation_and_provenance_rejects_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            request=read(OLD/'candidate_1/revision_input.json');compiler,provider,budget=self.setup_compiler(tmp,request,lambda *args:None)
            source=Path(tmp)/'source.py';source.write_text((OLD/'candidate_1/candidate.py').read_text())
            compiler.import_candidate(request,0,source,OLD/'candidate_1/candidate.json',2)
            self.assertEqual(budget.calls,0)
            source.write_text(source.read_text()+'\n')
            with self.assertRaises(ValueError):compiler.request(request,'revision',0,3)
            self.assertEqual(budget.calls,0)

    def test_extra_field_is_importable_diagnostic_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            request=read(OLD/'candidate_1/revision_input.json');compiler,provider,budget=self.setup_compiler(tmp,request,lambda *args:None)
            saved=read(OLD/'candidate_1/candidate.json')
            value=json.loads(saved['response']['raw_response']['choices'][0]['message']['content']);value['specification']='extra'
            saved['response']['raw_response']['choices'][0]['message']['content']=json.dumps(value)
            path=Path(tmp)/'response.json';path.write_text(json.dumps(saved))
            review=compiler.import_candidate(request,0,OLD/'candidate_1/candidate.py',path,2)
            self.assertEqual(review['errors'],['COMPILE_OUTPUT_CONTRACT_ERROR'])
            self.assertFalse(review['static_pass']);self.assertEqual(budget.calls,0)

    def test_bare_assertion_failure_is_runtime_error(self):
        from types import SimpleNamespace
        from experiment_capacity_nursery import Study
        with tempfile.TemporaryDirectory() as temp:
            class Worker:
                def __enter__(self):return self
                def __exit__(self,*args):pass
                def call(self,q):
                    return {'status':'OK'} if q['mode']=='compile_stdio' else {'status':'RUNTIME_ERROR','stderr':'Traceback (most recent call last):\nAssertionError\n','output':''}
            study=object.__new__(Study)
            study.ev=SimpleNamespace(factory=lambda path:Worker(),_charged=lambda name,callback:callback())
            study.sequence=0;study.journals=Path(temp)
            result=study.evaluate('assert False',[dict(case_id='fixture',input='',expected='1',comparison='whitespace_token_exact')],'assertion')
            self.assertEqual(result['feedback']['status'],'RUNTIME_ERROR')
            self.assertEqual(result['cases'][0]['exception_class'],'AssertionError')

    def test_send_uses_cached_preflight_even_if_builder_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            request=read(OLD/'candidate_1/revision_input.json');request.update(phase='revision',slot=0,max_tokens=4096)
            wire=canonical(CapacityGenerator.prepare(request));calls=[]
            def transport(body,key,timeout):
                self.assertEqual(canonical(body),wire);calls.append(body)
                return dict(model='deepseek-flash',usage={'total_tokens':10},choices=[dict(finish_reason='stop',message={'content':json.dumps(artifact())})])
            compiler,provider,budget=self.setup_compiler(tmp,request,transport)
            compiler.import_candidate(request,0,OLD/'candidate_1/candidate.py',OLD/'candidate_1/candidate.json',2)
            original=provider.preflight
            def preflight(q):
                body=original(q)
                provider.prepare=lambda q: (_ for _ in ()).throw(AssertionError('must not rebuild after reservation'))
                return body
            provider.preflight=preflight
            with patch.dict('os.environ',{'DEEPSEEK_API_KEY':'mock'}):compiler.request(request,'revision',0,3)
            self.assertEqual(len(calls),1)
