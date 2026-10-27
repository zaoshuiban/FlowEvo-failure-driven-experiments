"""Engineering fixtures only. No actual GPT calls or learning-success claims."""
import copy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.autonomous_generation import *
from failure_evo.autonomous_mvp import *
from failure_evo.compile_queue import BoundedCompiler, CompileQueue
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperatorRegistry
from failure_evo.symptom_learning import SymptomLearning
from failure_evo.runtime import Budget, Controller
from failure_evo.contracts import Fingerprint
from failure_evo.container_worker import DockerWorker

WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
IMAGE=os.environ.get('AUTONOMOUS_TEST_IMAGE')
HYP=dict(decision='PROPOSE',operator_category='engineering_fixture',common_failure='Engineering fixture: malformed integer conversion marker.',
    root_cause_hypothesis='Synthetic hypothesis only.',executable_suggestion='Replace a bounded marker in fixture source.',
    applicability='Engineering marker present.',exclusions='Marker absent.',uncertainties='No research evidence.')
# Deliberately HUMAN fixture; available ONLY to Mock sender, never the induction prompt.
CODE='''def repair_operator(context):
    code = context['candidate_code']
    if 'intt(' not in code:
        return {'status':'declined','reason':'fixture out of scope'}
    return {'status':'applied','candidate_code':code.replace('intt(', 'int(')}
'''
CTX=Fingerprint('engineering','public-tokens','mock-solver','worker-frozen',PROTOCOL)

def raw(value,model='gpt-mock'):
    return dict(id='mock-'+fingerprint(value)[:12],model=model,status='completed',
        output=[dict(type='message',content=[dict(type='output_text',text=canonical(value))])],
        usage=dict(input_tokens=100,output_tokens=100,total_tokens=200))

class Sender:
    def __init__(self,values):self.values=list(values);self.wires=[]
    def __call__(self,wire):
        self.wires.append(copy.deepcopy(wire));v=self.values.pop(0)
        if isinstance(v,BaseException):raise v
        return raw(v)


def case(name,code=None,expected='3\n'):
    code=code if code is not None else ('print(intt(input()))' if name=='source' else 'value = intt(input())\nprint(value)')
    return dict(case_id=name,task=dict(problem_id=name,prompt='Engineering fixture: echo an integer.',
        public_examples=[dict(visibility='public',legal_verified=True,input='3\n',expected=expected)]),
        code=code,lineage_id=name)

class EngineeringEvidence(FailureEvidenceStore):
    """Unit-test host trust double, NEVER used by the real replay/production path.

    Keep synthetic=True on disk; registry admission unit tests simulate verified
    host evidence via this view, in an explicitly engineering-only namespace.
    """
    def visible(self,at,stream_id=None):
        return tuple(dict(e,synthetic=False) for e in super().visible(at,stream_id))


def setup(root,values):
    evidence=EngineeringEvidence(root/'facts.jsonl')
    src=case('source')
    feedback=PublicFeedback.project(dict(visibility='public',status='RUNTIME_ERROR',cases=[dict(
        visibility='public',legal_verified=True,input='3\n',expected='3\n',actual='',exception_class='NameError')]))
    fact=evidence.record(stream_id='engineering:stream',task_id='source',family_id='public_failure',stage='l1',
        code=src['code'],feedback=feedback,observed_at=1,available_from=2,provenance_group_id='source',synthetic=True)
    cp=dict(event_id=fact['event_id'],task=src['task'],code=src['code'],feedback=dict(visibility='public',status='RUNTIME_ERROR',cases=[dict(
        visibility='public',legal_verified=True,input='3\n',expected='3\n',actual='',exception_class='NameError')]),
        observed_at=1,lineage_id='source')
    audit=root/'legality.json';audit.write_text(canonical(dict(passed=True,checkpoint_sha256=fingerprint(cp))))
    cp['legality_audit']=dict(path=str(audit),sha256=hashlib.sha256(audit.read_bytes()).hexdigest(),passed=True,checkpoint_sha256=fingerprint(cp))
    index=SymptomLearning(root/'symptoms.jsonl',evidence,'engineering:stream')
    queue=CompileQueue(root/'queue.jsonl')
    job=discover_jobs(evidence,index,queue,{fact['event_id']:cp},at=3,completed_tasks=1)[0]
    sender=Sender(values);budget=Budget(max_calls=3,max_tokens=300000,wall_seconds=300)
    provider=GPTCompilerAdapter(root/'gpt.jsonl',budget,model='gpt-mock',sender=sender,mock=True)
    compiler=BoundedCompiler(provider,budget,root/'compiler.jsonl','gpt-mock',max_input_upper=32768)
    return evidence,src,job,sender,compiler,cp

class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_no_mechanism_and_no_generation(self):
        evidence,src,job,sender,compiler,_=setup(self.root,[dict(HYP,decision='NO_MECHANISM')])
        m=AutonomousMVP(self.root/'m',compiler,None,None,None,CTX,Budget())
        result=m.run(job,source=[src],independent=[case('independent')],negative=[case('negative','print(input())')],at=4)
        self.assertEqual(result['status'],'NO_MECHANISM');self.assertEqual(len(sender.wires),1)
        self.assertNotIn('independent',canonical(sender.wires))
    def test_invalid_source_static_rejected(self):
        evidence,src,job,sender,compiler,_=setup(self.root,[HYP,dict(code='import os\ndef repair_operator(c): return {"status":"declined"}',description='fixture',applicability='fixture')])
        m=AutonomousMVP(self.root/'m',compiler,None,None,None,CTX,Budget())
        r=m.run(job,source=[src],independent=[case('independent')],negative=[case('negative')],at=4)
        self.assertFalse(r['validation']['static']['static_pass']);self.assertEqual(r['validation']['source'],())
    def test_unauthorized_before_budget_or_sender(self):
        sender=Sender([]);b=Budget(max_calls=3)
        p=GPTCompilerAdapter(self.root/'gpt',b,model='gpt-5.4',sender=sender)
        c=BoundedCompiler(p,b,self.root/'compiler','gpt-5.4')
        with self.assertRaises(PermissionError):c.request(dict(stream_id='s',family_id='f',discovery={}), 'induction',0,1)
        self.assertEqual(b.calls,0);self.assertEqual(sender.wires,[])
    def test_interrupted_send_not_repeated_after_restart(self):
        _,_,job,sender,compiler,_=setup(self.root,[TimeoutError('mock TLS')])
        with self.assertRaises(TimeoutError):compiler.request(job,'induction',0,4)
        restart=BoundedCompiler(compiler.provider,compiler.budget,self.root/'compiler.jsonl','gpt-mock')
        with self.assertRaises(ValueError):restart.request(job,'induction',0,5)
        self.assertEqual(len(sender.wires),1)
        self.assertIn('SEND_UNKNOWN',(self.root/'gpt.jsonl').read_text())
    def test_unknown_response_not_repeated(self):
        _,_,job,sender,compiler,_=setup(self.root,[{'unknown':True}])
        with self.assertRaises(ValueError):compiler.request(job,'induction',0,4)
        with self.assertRaises(ValueError):compiler.request(job,'induction',0,5)
        self.assertEqual(len(sender.wires),1)
    def test_time_hash_and_hidden_exclusion(self):
        evidence,src,job,sender,compiler,cp=setup(self.root,[])
        with self.assertRaises(ValueError):public_checkpoint(evidence,cp['event_id'],cp,at=1)
        bad=copy.deepcopy(cp);bad['hidden_answer']='sentinel'
        with self.assertRaises(ValueError):public_checkpoint(evidence,cp['event_id'],bad,at=3)
        bad=copy.deepcopy(cp);bad['code']+='\n# modified'
        with self.assertRaises(ValueError):public_checkpoint(evidence,cp['event_id'],bad,at=3)
        projected=runtime_projection(dict(task_public=src['task'],candidate_code=src['code'],public_feedback={'status':'WRONG_ANSWER','public_cases':[{'expected':'SECRET','input':'SECRET'}]}))
        self.assertNotIn('SECRET',canonical(projected))
    def test_independent_overlap_rejected_before_send(self):
        _,src,job,sender,compiler,_=setup(self.root,[])
        m=AutonomousMVP(self.root/'m',compiler,None,None,None,CTX,Budget())
        with self.assertRaises(ValueError):m.run(job,source=[src],independent=[src],negative=[case('negative')],at=4)
        self.assertFalse(sender.wires)
    def test_disabled_controller_identical(self):
        def generate(p):return dict(model='mock-solver',code='print(3)',usage={'total_tokens':1})
        def evaluate(t,c):return dict(visibility='public',status='PUBLIC_PASS',tests_run=1,tests_passed=1,cases=[])
        class Disabled:
            enabled=False
            def begin(self,*a):raise AssertionError('disabled touched')
        a=Controller(generate,evaluate,CTX).solve({'problem_id':'x','prompt':'x'},Budget(clock=lambda:0))
        b=Controller(generate,evaluate,CTX,plugin=Disabled()).solve({'problem_id':'x','prompt':'x'},Budget(clock=lambda:0))
        self.assertEqual(a,b)
    def test_budget_exhaustion_before_sender(self):
        _,_,job,sender,compiler,_=setup(self.root,[])
        compiler.budget.max_calls=0
        from failure_evo.runtime import BudgetExhausted
        with self.assertRaises(BudgetExhausted):compiler.request(job,'induction',0,4)
        self.assertEqual(sender.wires,[])
    def test_persistent_unknown_reservation_and_no_resend(self):
        from failure_evo.persistent_budget import PersistentBudget
        _,_,job,_,_,_=setup(self.root,[])
        b=PersistentBudget(self.root/'budget.jsonl',run_id='engineering:unknown',protocol_hash='frozen',
            max_calls=3,max_tokens=300000,max_tools=20,max_cost_microusd=2000000,
            token_rate_microusd_per_million=15000000,tool_cost_upper_microusd=0,
            max_tool_milliseconds=100000,tool_milliseconds_upper=5000,wall_seconds=300)
        sender=Sender([TimeoutError('fixture')])
        p=GPTCompilerAdapter(self.root/'durable-gpt.jsonl',b,model='gpt-mock',mock=True,sender=sender)
        c=BoundedCompiler(p,b,self.root/'durable-compiler.jsonl','gpt-mock',max_input_upper=32768)
        with self.assertRaises(TimeoutError):c.request(job,'induction',0,4)
        self.assertEqual(b.calls,1)
        self.assertEqual(len(b.snapshot()['unknown_or_pending_requests']),1)
        with self.assertRaises(ValueError):c.request(job,'induction',0,5)
        self.assertEqual(len(sender.wires),1)
    def test_wire_has_no_algorithm_or_heldout_answers(self):
        _,_,job,sender,compiler,_=setup(self.root,[HYP])
        compiler.request(job,'induction',0,4)
        wire=canonical(sender.wires)
        self.assertNotIn(CODE,wire)
        self.assertNotIn('target_operator',wire)
        self.assertNotIn('standard_answer',wire)
        self.assertIn('NO_MECHANISM',wire)

    def test_static_policy_no_relaxation(self):
        for code in ('def repair_operator(c):\n return {"status":"request_repair"}',
                     'def repair_operator(c):\n open("x")\n return {"status":"declined"}'):
            self.assertFalse(validate_compile_output(dict(code=code,description='x',applicability='x'))['static_pass'])

@unittest.skipUnless(IMAGE,'set AUTONOMOUS_TEST_IMAGE to run actual Linux Worker checks')
class LinuxLoopTests(unittest.TestCase):
    def setUp(self):
        output=os.environ.get('AUTONOMOUS_EVIDENCE_OUTPUT') if self._testMethodName=='test_full_loop_future_refusal_and_suspension' else None
        self.tmp=None
        if output:
            self.root=Path(output).resolve();self.root.mkdir(parents=True,exist_ok=False)
        else:
            self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):
        if self.tmp:self.tmp.cleanup()
    def factory(self,p):return DockerWorker(p,image=IMAGE,worker_script=WORKER)
    def make(self,code=CODE):
        evidence,src,job,sender,compiler,_=setup(self.root,[HYP,dict(code=code,description='mock deterministic fixture',applicability='marker only')])
        registry=FailureOperatorRegistry(self.root/'registry.jsonl',evidence)
        backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
        runner=DeterministicRunner(backend);evaluator=LinuxPublicEvaluator(backend)
        m=AutonomousMVP(self.root/'m',compiler,runner,evaluator,registry,CTX,Budget(max_tools=200,wall_seconds=300))
        return m,evidence,registry,src,job,sender
    def test_source_no_effect(self):
        m,ev,reg,src,job,sender=self.make('def repair_operator(c):\n return {"status":"declined","reason":"no mechanism"}')
        r=m.run(job,source=[src],independent=[case('independent')],negative=[case('negative')],at=4)
        self.assertEqual(r['status'],'SHADOW_NO_ADMISSION');self.assertEqual(reg.events.records(),[])
    def test_source_pass_independent_fail_shadow(self):
        m,ev,reg,src,job,sender=self.make()
        r=m.run(job,source=[src],independent=[case('independent','print(intt(input())+1)')],negative=[case('negative','print(input())')],at=4)
        self.assertTrue(r['validation']['source'][0]['source_effective'])
        self.assertFalse(r['validation']['independent'][0]['passed'])
        self.assertEqual(reg.state(FailureOperator.from_dict(r['card']))['permission'],'shadow')
        with self.assertRaises(ValueError):m.authorize(r,experiment_id='engineering:pilot',stream_id='engineering:stream',after_task=1,effective_from=2,at=5,future_tasks={'future':'future','regression':'regression'},engineering=True)
    def test_full_loop_future_refusal_and_suspension(self):
        m,ev,reg,src,job,sender=self.make()
        r=m.run(job,source=[src],independent=[case('independent')],negative=[case('negative','print(input())')],at=4)
        self.assertEqual(r['status'],'READY_FOR_HOST_LIMITED_REVIEW')
        self.assertEqual(Path(r['operator']['artifact_path']).read_text(),CODE)
        self.assertEqual(r['operator']['code_sha256'],sha(CODE))
        with self.assertRaises(PermissionError):m.authorize(r,experiment_id='real',stream_id='s',after_task=1,effective_from=2,at=5,future_tasks={'future':'future','regression':'regression'})
        card=m.authorize(r,experiment_id='engineering:pilot',stream_id='engineering:stream',after_task=1,effective_from=2,at=5,future_tasks={'future':'future','regression':'regression'},engineering=True)
        # Same task and same publication index cannot execute this newly compiled version.
        self.assertFalse(reg.snapshot(stream_id='engineering:stream',experiment_id='engineering:pilot',task_index=1,at=6).cards)
        ev.events.append('TASK_COMPLETED',dict(stream_id='engineering:stream',task_id='source',task_index=1),6)
        hook=AutonomousHook(reg,ev,CTX,stream_id='engineering:stream',experiment_id='engineering:pilot',runner=m.runner,synthetic=True)
        hook.begin(PublicTaskView.project(case('independent')['task']),7)
        self.assertEqual(hook.current['snapshot'].cards,());hook.finish(7)
        calls=[]
        def generator(p):
            calls.append(p);return dict(model='mock-solver',code='print(intt(input()))',usage={'total_tokens':1})
        result=Controller(generator,m.evaluate,CTX,plugin=hook,clock=lambda:8).solve(case('future')['task'],Budget(max_tools=100,wall_seconds=120))
        self.assertEqual(result['status'],'PUBLIC_ACCEPTED');self.assertEqual(len(calls),1)
        (self.root/'future_controller_result.json').write_text(canonical(result)+'\n')
        self.assertTrue(any(h['status']=='applied' for h in result['hook_events']))
        # Genuine execution on an out-of-scope task declines, preserving original code.
        refusal=m.runner.run(card,dict(task_public=case('no-match')['task'],candidate_code='print(input())',public_feedback={'status':'PUBLIC_PASS'}),5)
        self.assertEqual(refusal['status'],'declined')
        # Correct original includes the marker only as data: mock transform causes regression.
        bad=case('regression','print("intt(")','intt(\n')
        hook.begin(PublicTaskView.project(bad['task']),9)
        original=m.evaluate(PublicTaskView.project(bad['task']),bad['code'])
        result=hook.invoke('before_native_retry','l2a','l2a',bad['code'],PublicFeedback.project(original),Budget(max_tools=100),m.evaluate,9)
        self.assertIsNone(result);self.assertEqual(reg.state(card)['permission'],'suspended')
        hook.finish(9)
        self.assertFalse(reg.snapshot(stream_id='engineering:stream',experiment_id='engineering:pilot',task_index=10,at=10).cards)
        (self.root/'controller_result.json').write_text(canonical(result if isinstance(result,dict) else {'regression_fallback':True})+'\n')
    def test_one_bounded_revision_parent_chain(self):
        m,ev,reg,src,job,sender=self.make('def repair_operator(c):\n return {"status":"declined","reason":"fixture"}')
        sender.values.append(dict(code=CODE,description='Mock revision',applicability='marker'))
        r=m.run(job,source=[src],independent=[case('independent')],negative=[case('negative','print(input())')],at=4,revise=True)
        self.assertEqual(r['operator']['version'],'1')
        self.assertEqual(len(sender.wires),3)
        versions=json.loads((m.root/'versions.json').read_text())
        self.assertEqual(r['operator']['parent_sha256'],versions[0]['operator']['code_sha256'])
        self.assertNotIn('independent',sender.wires[-1]['input'][1]['content'])

    def test_artifact_tamper_and_worker_exception(self):
        m,ev,reg,src,job,sender=self.make()
        p=self.root/'throws.py';p.write_text('def repair_operator(c):\n raise ValueError("fixture")')
        card=FailureOperator('x','0',str(p),sha(p.read_text()),CTX,'test',(job['evidence_ids'][0],),('source',))
        result=m.runner.run(card,dict(task_public=src['task'],candidate_code=src['code'],public_feedback={'status':'WRONG_ANSWER'}),1)
        self.assertEqual(result['status'],'error')
        p.write_text(CODE)
        self.assertEqual(m.runner.run(card,dict(task_public=src['task'],candidate_code=src['code'],public_feedback={'status':'WRONG_ANSWER'}),1)['reason'],'artifact_changed_before_execution')

if __name__=='__main__':unittest.main(verbosity=2)
