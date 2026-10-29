import hashlib,json,sys,tempfile,unittest,time,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from code_math.no_gold import *
from code_math.private_math_scoring import *
from failure_evo.math_operators import *
from failure_evo.math_learning import *
from failure_evo.math_transport import NoGoldSolverChannel
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.autonomous_mvp import FrozenLinuxBackend

IMAGE='sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8'
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
# Engineering fixture only; never injected into real induction, dataset or primary results.
CODE='''def math_operator(context):
    p = context['problem']
    if not p.startswith('Sum integers: '):
        return {'status': 'DECLINED', 'reason': 'unsupported'}
    parts = p[14:].split(',')
    try:
        total = sum(int(x) for x in parts)
    except ValueError:
        return {'status': 'DECLINED', 'reason': 'not integers'}
    return {'status': 'APPLIED', 'answer': str(total)}
'''
H=dict(decision='PROPOSE',**{k:'Engineering mock: bounded integer addition; unverified.' for k in FIELDS})

def budget(path,n=14):
    return PersistentBudget(path,run_id='engineering:'+path.stem,protocol_hash='math-p0',max_calls=n,max_tokens=2000000,max_tools=1000,max_cost_microusd=100000000,token_rate_microusd_per_million=15000000,tool_cost_upper_microusd=0,max_tool_milliseconds=1000000,tool_milliseconds_upper=10000,wall_seconds=3600)
def ds(text='The answer is 0'):
    return dict(model='deepseek-flash',id='mock',choices=[dict(message={'content':text},finish_reason='stop')],usage=dict(prompt_tokens=40,completion_tokens=10,total_tokens=50))
def gpt(v):
    return dict(model='gpt-5.4-2026-03-05',id='mock',status='completed',output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(v))])],usage=dict(input_tokens=50,output_tokens=40,total_tokens=90))
def private(t,gold):return dict(task_id=t.task_id,problem_sha256=fingerprint(t.problem),gold_answer=gold)

class MathTests(unittest.TestCase):
    def setUp(self):
        if os.environ.get('MATH_P0_ARTIFACT_DIR'):
            self.tmp=None;self.p=Path(os.environ['MATH_P0_ARTIFACT_DIR'])/self._testMethodName;self.p.mkdir(parents=True)
        else:
            self.tmp=tempfile.TemporaryDirectory(dir=ROOT,prefix='.math-p0-');self.p=Path(self.tmp.name)
    def tearDown(self):
        if self.tmp:self.tmp.cleanup()
    def channel(self,text='The answer is 0',sender=None,name='solve'):
        self.wires=[]
        def send(w):self.wires.append(w);return ds(text)
        return NoGoldSolverChannel(budget(self.p/(name+'.budget')),self.p/(name+'.requests'),mock=True,sender=sender or send)
    def discover(self):
        t=PublicMathTask('source','Sum integers: 2,3');client=self.channel()
        c=NoGoldMathController(client,self.p/'controller');locked=c.solve(t,episode_id='s',sequence=0)
        scorer=PrivateMathScorer([private(t,'5')],self.p/'controller',self.p/'score');v=scorer.score(t,locked)
        evidence=MathFailureEvidenceStore(self.p/'failures',self.p/'score');evidence.record(t,locked,v,role='Discovery',origin='MOCK',at=time.time())
        return t,evidence.bundle(after_sequence=1,allow_mock=True)
    def pipeline(self,outputs=None):
        t,bundle=self.discover();design=PublicMathTask('design','Sum integers: 7,4');gate=PublicMathTask('gate','Sum integers: 11,8')
        output=iter(outputs or [gpt(H),gpt(dict(code=CODE,description='mock computation',applicability='engineering integer input'))])
        self.gpt_wires=[]
        def send(w):self.gpt_wires.append(w);return next(output)
        b=budget(self.p/'compiler.budget',7);adapter=MathGPTAdapter(self.p/'gpt',b,model='gpt-5.4-2026-03-05',mock=True,sender=send,max_wire_input_upper=65536)
        compiler=BoundedCompiler(adapter,b,self.p/'compiler',adapter.model,max_input_upper=65536,max_output_upper=8192)
        registry=MathOperatorRegistry(self.p/'registry');runner=MathOperatorRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER))
        pipe=MathLearningPipeline(self.p/'pipeline',compiler,registry,runner,arm='F',source_tasks=[t],design_tasks=[design],gate_tasks=[gate],private_rows=[private(t,'5'),private(design,'11'),private(gate,'19')])
        return pipe,bundle
    def test_fixed_schedule_counterfactual_gold(self):
        wires=[];outputs=[]
        for i,gold in enumerate(('0','PRIVATE_SENTINEL_987654321')):
            client=self.channel(name='ch'+str(i));t=PublicMathTask('t','Compute a sum.');journal=self.p/('controller'+str(i))
            locked=NoGoldMathController(client,journal).solve(t,episode_id='t',sequence=0)
            score=PrivateMathScorer([private(t,gold)],journal,self.p/('score'+str(i))).score(t,locked)
            self.assertEqual(locked['model_calls'],2);self.assertEqual(score['correct'],i==0);wires.append(self.wires.copy());outputs.append(locked['final_output'])
        self.assertEqual(wires[0],wires[1]);self.assertEqual(outputs[0],outputs[1]);self.assertNotIn('PRIVATE_SENTINEL',json.dumps(wires))
    def test_no_private_projection(self):
        with self.assertRaises(ValueError):PublicMathTask.parse(dict(task_id='t',problem='p',gold_answer='x'))
        with self.assertRaises(ValueError):PublicMathTask.parse(dict(task_id='t',problem='p',family='x'))
    def test_unknown_never_resent(self):
        calls=[]
        def fail(w):calls.append(w);raise OSError('mock TLS failure')
        client=self.channel(sender=fail);c=NoGoldMathController(client,self.p/'controller');t=PublicMathTask('t','p')
        with self.assertRaises(OSError):c.solve(t,episode_id='e',sequence=0)
        with self.assertRaises(RuntimeError):c.solve(t,episode_id='e',sequence=0)
        self.assertEqual(len(calls),1)
    def test_unauthorized_before_send(self):
        calls=[];client=NoGoldSolverChannel(budget(self.p/'b'),self.p/'req',sender=lambda w:calls.append(w))
        with self.assertRaises(PermissionError):client.generate_no_gold(messages=solver_messages(PublicMathTask('t','p')),policy=NoGoldPolicy(),request_id='r')
        self.assertEqual(calls,[])
        adapter=MathGPTAdapter(self.p/'gpt',budget(self.p/'g'),model='gpt-5.4-2026-03-05',sender=lambda w:calls.append(w))
        with self.assertRaises(PermissionError):adapter.preflight({})
        self.assertEqual(calls,[])
    def test_score_requires_lock(self):
        t=PublicMathTask('t','p');v=dict(task_id='t',episode_id='e',final_output='5');v['locked_sha256']=fingerprint(v)
        with self.assertRaises(PermissionError):PrivateMathScorer([private(t,'5')],self.p/'c',self.p/'s').score(t,v)
    def test_actual_evidence_and_task_only(self):
        t,b=self.discover();f=discovery_view(b,'F');q=discovery_view(b,'T')
        self.assertEqual(f['questions'],q['questions']);self.assertNotIn('observations',q);self.assertIn('observations',f)
        self.assertNotIn('gold_answer',canonical(f));self.assertNotIn('family',canonical(f))
        with self.assertRaises(PermissionError):MathFailureEvidenceStore(self.p/'failures',self.p/'score').bundle(after_sequence=1)
    def test_static_denies_unsafe(self):
        self.assertTrue(validate_math_source(CODE)['passed'])
        for prefix in ('import os\n','import socket\n','x=open("/tmp/x")\n'):
            self.assertFalse(validate_math_source(prefix+CODE)['passed'])
        self.assertFalse(validate_math_source(CODE.replace("p = context['problem']","p = getattr(context, 'x')"))['passed'])
    def test_no_mechanism_and_hypothesis_only(self):
        for decision in ('NO_MECHANISM','HYPOTHESIS_ONLY'):
            sub=self.p/decision;sub.mkdir();old=self.p;self.p=sub
            pipe,b=self.pipeline([gpt(dict(H,decision=decision))]);self.assertIsNone(pipe.induce(b));self.assertEqual(len(self.gpt_wires),1)
            self.p=old
    def test_invalid_source_shadow(self):
        pipe,b=self.pipeline([gpt(H),gpt(dict(code='not python !',description='mock',applicability='mock'))]);job=pipe.induce(b);r=pipe.candidate(job,0)
        self.assertFalse(r['development_passed']);self.assertEqual(pipe.registry.eligible(PublicMathTask('future','p'),5),[])
    def test_real_worker_end_to_end(self):
        pipe,b=self.pipeline();job=pipe.induce(b);r=pipe.candidate(job,0);self.assertTrue(r['development_passed'],r)
        self.assertEqual(pipe.registry.eligible(PublicMathTask('future','p'),5),[])
        gate=pipe.gate(r,after_sequence=2);self.assertTrue(gate['gate_passed'])
        a=r['artifact'];self.assertEqual(Path(a['source_path']).read_text(),CODE)
        self.assertNotIn(pipe.roles['Gate'][0].problem,canonical(self.gpt_wires))
        self.assertNotIn('gold_answer',canonical(self.gpt_wires))
        library=FrozenMathLibrary(pipe.registry,pipe.runner,engineering=True)
        self.assertEqual(library.run(PublicMathTask('future','Sum integers: 10,20'),sequence=2),[])
        self.assertEqual(library.run(pipe.roles['Source'][0],sequence=3),[])
        out=library.run(PublicMathTask('future','Sum integers: 10,20'),sequence=3);self.assertEqual(out[-1]['answer'],'30')
        client=self.channel(name='future');c=NoGoldMathController(client,self.p/'futurecontroller',policy=NoGoldPolicy(operators_enabled=True),library=library)
        t=PublicMathTask('future2','Sum integers: 4,9');locked=c.solve(t,episode_id='future2',sequence=4)
        self.assertEqual(locked['model_calls'],0)
        # Deliberately changed private grade cannot cause a fallback or retry.
        score=PrivateMathScorer([private(t,'999')],self.p/'futurecontroller',self.p/'futuregrade').score(t,locked)
        self.assertFalse(score['correct']);self.assertEqual(len(self.wires),0)
        t2=PublicMathTask('negative','Not in mock domain');l2=c.solve(t2,episode_id='negative',sequence=5)
        self.assertTrue(l2['fallback']);self.assertEqual(l2['model_calls'],2)
        pipe.registry.suspend(a['code_sha256'],'external governance regression');self.assertEqual(library.run(t,sequence=6),[])
        with self.assertRaises(PermissionError):pipe.candidate(job,0,revision=True)
        with self.assertRaises(PermissionError):pipe.gate(r,after_sequence=4)
    def test_gate_failure_not_revised(self):
        pipe,b=self.pipeline();job=pipe.induce(b);r=pipe.candidate(job,0)
        pipe.private['gate']['gold_answer']='wrong-for-mock-negative-control'
        v=pipe.gate(r,after_sequence=2);self.assertFalse(v['gate_passed'])
        self.assertEqual(pipe.registry.eligible(PublicMathTask('future','p'),5),[])
        with self.assertRaises(PermissionError):pipe.candidate(job,0,revision=True)
    def test_source_failure_then_one_revision(self):
        wrong=CODE.replace('total = sum','total = 1 + sum')
        pipe,b=self.pipeline([gpt(H),gpt(dict(code=wrong,description='mock',applicability='mock')),gpt(dict(code=CODE,description='mock',applicability='mock'))])
        job=pipe.induce(b);r=pipe.candidate(job,0);self.assertFalse(r['development_passed'])
        v=pipe.candidate(job,0,revision=True);self.assertTrue(v['development_passed'])
        self.assertEqual(v['artifact']['parent_sha256'],r['artifact']['code_sha256'])
        with self.assertRaises(PermissionError):pipe.candidate(job,0,revision=True)
        self.assertNotIn('gold_answer',canonical(self.gpt_wires))
    def test_worker_error_and_hash_tamper(self):
        p=self.p/'error.py';code="def math_operator(context):\n    x=1/0\n    return {'status':'APPLIED','answer':str(x)}\n";p.write_text(code)
        a=dict(source_path=str(p),code_sha256=hashlib.sha256(code.encode()).hexdigest(),operator_id='mock')
        runner=MathOperatorRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER));r=runner.run(a,PublicMathTask('t','p'));self.assertEqual(r['status'],'ERROR')
        p.write_text(CODE)
        with self.assertRaises(RuntimeError):runner.run(a,PublicMathTask('t','p'))
    def test_existing_runner_opt_in_and_old_verify(self):
        from code_math.runner import run_condition,verify
        from core.schemas import CodeTaskInstance
        from runtime.llm_client import LLMClient
        llm=LLMClient.__new__(LLMClient);llm.no_gold_channel=self.channel('The answer is 0')
        task=CodeTaskInstance(task_id='entry',benchmark='math',prompt='Compute zero.',metadata={'gold_answer':'PRIVATE_SENTINEL'},canonical_solution='PRIVATE_REFERENCE')
        rows=run_condition('math','G',{'no_gold':True,'reflection_calls':1},llm,[task],self.p/'entry')
        self.assertEqual(rows[0]['model_calls'],2);self.assertFalse(rows[0]['passed'])
        self.assertNotIn('PRIVATE_',canonical(self.wires))
        old=verify(task,'The answer is 0',None);self.assertIn('gold=PRIVATE_SENTINEL',old[1])
    def test_module_off_never_calls_library(self):
        class ExplodingLibrary:
            def run(self,*args,**kw):raise AssertionError('disabled hook called')
        c=NoGoldMathController(self.channel(),self.p/'c',library=ExplodingLibrary())
        self.assertEqual(c.solve(PublicMathTask('t','p'),episode_id='e',sequence=0)['model_calls'],2)
    def test_gate_diagnostics_rejected_by_adapter(self):
        pipe,b=self.pipeline();job=pipe.induce(b)
        request=dict(job,phase='revision',slot=0,max_tokens=8192,code=CODE,source_diagnostics=[{'role':'Gate','correct':False}])
        with self.assertRaises(PermissionError):pipe.compiler.provider.preflight(request)
        request['source_diagnostics']=[{'role':'Source','gold_answer':'private'}]
        with self.assertRaises(PermissionError):pipe.compiler.provider.preflight(request)
    def test_worker_timeout(self):
        code="def math_operator(context):\n    while True:\n        pass\n    return {'status':'DECLINED','reason':'unreachable'}\n"
        p=self.p/'timeout.py';p.write_text(code)
        a=dict(source_path=str(p),code_sha256=hashlib.sha256(code.encode()).hexdigest(),operator_id='timeout',origin='MOCK')
        runner=MathOperatorRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER))
        self.assertEqual(runner.run(a,PublicMathTask('t','p'),timeout=0.2)['status'],'ERROR')
    def test_gpt_unknown_not_resent(self):
        pipe,b=self.pipeline();calls=[]
        def fail(w):calls.append(w);raise OSError('mock unknown')
        pipe.compiler.provider.sender=fail
        with self.assertRaises(OSError):pipe.induce(b)
        with self.assertRaises(RuntimeError):pipe.induce(b)
        self.assertEqual(len(calls),1)
    def test_symbolic_nonmatch_not_false_failure(self):
        t=PublicMathTask('symbolic','Simplify an expression.')
        c=NoGoldMathController(self.channel('The answer is x+x'),self.p/'c')
        locked=c.solve(t,episode_id='s',sequence=0)
        scorer=PrivateMathScorer([private(t,'2x')],self.p/'c',self.p/'s');v=scorer.score(t,locked)
        self.assertFalse(v['credible_failure']);self.assertEqual(v['score_class'],'UNVERIFIED_NONMATCH')
        e=MathFailureEvidenceStore(self.p/'e',self.p/'s')
        self.assertIsNone(e.record(t,locked,v,role='Discovery',origin='MOCK',at=time.time()))
    def test_exact_scoring(self):
        self.assertTrue(answer_equal(r'The answer is \boxed{\frac{2}{4}}','0.5'))
        self.assertFalse(answer_equal('100000000000000000001','100000000000000000000'))
        self.assertFalse(answer_equal('','0'))
    def test_frozen_data(self):
        root=ROOT/'reports/math_no_gold_p0_20261027/data';m=json.loads((root/'manifest.json').read_text())
        seen=set()
        for role in ('discovery','design','gate','legacy_test','fresh_test'):
            rows=[json.loads(x) for x in (root/'public'/(role+'.jsonl')).read_text().splitlines()]
            keys={r['task_id'] for r in rows};self.assertFalse(keys&seen);seen|=keys
            for r in rows:PublicMathTask.parse(r)
        self.assertEqual(len(seen),672)
        for name,sha in m['files'].items():self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),sha)

if __name__=='__main__':unittest.main(verbosity=2)
