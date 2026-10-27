"""Zero-API provider parity, raw provenance and client contract tests."""
import json, tempfile, unittest
from pathlib import Path
from test_autonomous_mvp import setup, HYP
from failure_evo.autonomous_generation import DeepSeekCompilerAdapter
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.runtime import Budget

class ProviderTests(unittest.TestCase):
    def test_wire_parse_raw_and_origin(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p); _,_,job,_,_,_=setup(root,[])
            seen=[]
            raw=dict(id='mock-ds',model='deepseek-flash',choices=[dict(finish_reason='stop',message=dict(content=json.dumps(dict(HYP,decision='NO_MECHANISM'))))],usage=dict(prompt_tokens=100,completion_tokens=50,total_tokens=150))
            def sender(body):seen.append(body);return raw
            b=Budget(max_calls=3,max_tokens=200000)
            a=DeepSeekCompilerAdapter(root/'ds.jsonl',b,model='deepseek-flash',mock=True,sender=sender)
            c=BoundedCompiler(a,b,root/'ds-compiler.jsonl',a.model,max_input_upper=32768)
            r=c.request(job,'induction',0,3)
            self.assertEqual(r['raw_response'],raw);self.assertEqual(r['origin'],'MOCK')
            self.assertEqual(r['response_sha256'],__import__('failure_evo.contracts',fromlist=['fingerprint']).fingerprint(raw))
            self.assertEqual(seen[0]['response_format'],{'type':'json_object'})
            self.assertEqual(json.loads(r['specification'])['decision'],'NO_MECHANISM')
            self.assertEqual(r['usage']['total_tokens'],150)
            self.assertEqual(a.provider_origin,'DEEPSEEK')
            with self.assertRaises(ValueError):c.request(job,'induction',0,4)
            self.assertEqual(len(seen),1)
    def test_unauthorized(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p);_,_,j,_,_,_=setup(root,[])
            a=DeepSeekCompilerAdapter(root/'ds.jsonl',Budget(),model='deepseek-flash')
            with self.assertRaises(PermissionError):a.preflight(dict(j,phase='induction',slot=0,max_tokens=4096))
    def test_truncation_not_success(self):
        with tempfile.TemporaryDirectory() as p:
            a=DeepSeekCompilerAdapter(Path(p)/'ds',Budget(),model='deepseek-flash',mock=True,sender=lambda _:None)
            self.assertEqual(a._normalize_response({'choices':[{'finish_reason':'length'}]})['status'],'incomplete')
if __name__=='__main__':unittest.main(verbosity=2)
