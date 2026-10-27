"""Zero-API regression of final wire accounting, including the saved pilot."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.autonomous_generation import DeepSeekCompilerAdapter
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.contracts import canonical
from failure_evo.runtime import Budget,BudgetExhausted

class RecordingBudget(Budget):
    def reserve(self,i,o):
        self.last_bound=(i,o)
        return super().reserve(i,o)

class WireTests(unittest.TestCase):
    def test_saved_candidate_uses_final_wire(self):
        run=ROOT/'runs/autonomous_mvp_pilot_20261027_01'
        job=json.loads((run/'learning/frozen_plan.json').read_text())['job']
        raw=next(x['payload']['response'] for x in map(json.loads,(run/'provider.jsonl').read_text().splitlines()) if x['kind']=='RAW_RESPONSE')
        seen=[]
        def sender(wire):
            seen.append(wire)
            if len(seen)==1:return raw  # historical output replay, no new inference
            return dict(model='deepseek-flash',id='MOCK_ONLY',choices=[dict(finish_reason='stop',message=dict(content=json.dumps(dict(code='def repair_operator(c):\n return {"status":"declined","reason":"fixture"}',description='engineering fixture',applicability='none'))))],usage=dict(prompt_tokens=1,completion_tokens=1,total_tokens=2))
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);b=RecordingBudget(max_calls=3,max_tokens=200000)
            a=DeepSeekCompilerAdapter(root/'provider',b,model='deepseek-flash',mock=True,sender=sender)
            c=BoundedCompiler(a,b,root/'compiler',a.model,max_input_upper=32768)
            spec=c.request(job,'induction',0,1)
            candidate=dict(job,specification=spec['specification'])
            req=dict(candidate,phase='candidate',slot=0,max_tokens=4096)
            self.assertEqual(len(str(req).encode())+4096,33151)
            c.request(candidate,'candidate',0,2)
            self.assertEqual(seen[1],json.loads((run/'candidate_not_sent_wire.json').read_text()))
            self.assertEqual(b.last_bound,(31847,4096))
            row=[r['payload'] for r in c.events.records() if r['kind']=='WIRE_PREFLIGHT'][-1]
            self.assertEqual(row['input_token_upper'],31847)
            self.assertEqual(row['input_accounting'],'final-wire-utf8-plus-256-v1')

    def _run_bound(self,wire,limit,metadata=''):
        class Provider:
            calls=0
            def preflight(self,request):return wire
            def __call__(self,request):
                self.calls+=1
                return dict(model='mock',specification='fixture',usage={'total_tokens':1})
        with tempfile.TemporaryDirectory() as td:
            b=RecordingBudget(max_calls=1,max_tokens=100000);p=Provider()
            c=BoundedCompiler(p,b,Path(td)/'compiler','mock',max_input_upper=limit)
            job=dict(stream_id='mock',family_id='f',job_id='j',internal_metadata=metadata)
            if len(canonical(wire).encode())+256>limit:
                with self.assertRaises(BudgetExhausted):c.request(job,'induction',0,1)
                self.assertEqual(b.calls,0);self.assertEqual(p.calls,0)
                self.assertEqual(c.events.records(),[])
            else:
                c.request(job,'induction',0,1)
                self.assertEqual(b.last_bound,(len(canonical(wire).encode())+256,4096))
                self.assertEqual(p.calls,1)
    def test_boundary_and_unicode_escaping(self):
        wire={'messages':[{'content':'中文\\"\n'*40}]}
        n=len(canonical(wire).encode())+256
        self._run_bound(wire,n)
        self._run_bound(wire,n-1)
    def test_host_only_metadata_does_not_inflate_wire(self):
        self._run_bound({'model':'mock'},1000,'host audit only'*10000)
    def test_large_real_wire_rejected_before_reservation(self):
        self._run_bound({'content':'x'*33000},32768)
    def test_legacy_provider_retains_conservative_fallback(self):
        class Provider:
            def __call__(self,r):raise AssertionError('must not send')
        with tempfile.TemporaryDirectory() as td:
            b=RecordingBudget(max_calls=1,max_tokens=100000)
            c=BoundedCompiler(Provider(),b,Path(td)/'compiler','mock',max_input_upper=32768)
            with self.assertRaises(BudgetExhausted):c.request(dict(stream_id='s',family_id='f',large='x'*33000),'induction',0,1)
            self.assertEqual(b.calls,0)
if __name__=='__main__':unittest.main(verbosity=2)
