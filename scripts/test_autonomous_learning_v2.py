"""Zero-API new integration. Mock programs are test fixtures, never learned evidence."""
import copy,hashlib,json,os,sys,tempfile,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import canonical,fingerprint,Fingerprint,PublicFeedback
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.trusted_learning_evidence import InputValidator,TrustedLearningEvidence
from failure_evo.autonomous_mechanism import GeneratorConfig,MechanismCompilerAdapter,VERSION,parse_mechanism
from failure_evo.autonomous_pipeline import ExecutableLearningPipeline,ExecutableOperatorHook,verify_controller_fallback
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.compile_queue import CompileQueue,BoundedCompiler
from failure_evo.learning import LearningLoop
from failure_evo.symptom_learning import SymptomLearning
from failure_evo.failure_registry import FailureOperatorRegistry,FailureOperator
from failure_evo.runtime import Budget
from failure_evo.workflow_runtime_v2 import PreparedController
from failure_evo.data_roles import validate_data_roles
from prepare_autonomous_pilot import legal

IMAGE=os.environ.get('AUTONOMOUS_TEST_IMAGE','')
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'
CONFIG=GeneratorConfig('gpt-engineering-fixture','MOCK_ONLY',1,1,'engineering-not-price','2026-10-27')
CTX=Fingerprint('native-v2','stdio-public-tokens','deepseek-mock-solver','frozen-linux',VERSION)

def history():
    packet=json.loads((ROOT/'reports/s22_action_preference_v1/frozen/01.json').read_text())['public_checkpoint']
    store=FailureEvidenceStore(ROOT/'runs/s20_taco80_m_20261025_01/evidence_M.jsonl')
    fact=next(x for x in store.visible(time.time()) if x['event_id']==packet['event_id'])
    # Complete original public observations; no independent/hidden material.
    task=dict(packet['task_public']);task['public_examples']=[dict(input=c['input'],expected=c['expected'],visibility='public',legal_verified=True) for c in packet['public_cases']]
    feedback=dict(visibility='public',status=packet['feedback']['status'],cases=[dict(c,visibility='public',legal_verified=True) for c in packet['feedback']['public_cases']])
    cp=dict(event_id=fact['event_id'],task=task,code=packet['code'],feedback=feedback,observed_at=fact['observed_at'],lineage_id=fact['provenance_group_id'])
    return store,fact,cp

def grammar(tid,text):
    try:return {'valid':bool(text.split()) and all(-100<=int(t)<=100 for t in text.split())}
    except ValueError:return {'valid':False,'reason':'NON_INTEGER_TOKEN'}

def validator(task,real=False):
    path=ROOT/'scripts/prepare_autonomous_pilot.py' if real else Path(__file__)
    return InputValidator('statement-grammar' if real else 'engineering-integer-grammar','v1',task['problem_id'],fingerprint(task['prompt']),str(path),hashlib.sha256(path.read_bytes()).hexdigest(),'explicit task and statement hash','statement constraints; engineering fixtures separately labelled',legal if real else grammar)

def hyp(event,decision='PROPOSE',kind='task_solver'):
    return dict(decision=decision,suggested_operator_kind=kind,source_evidence_ids=[event],failure_pattern='engineering fixture hypothesis, NOT real inference',root_cause_hypothesis='UNVERIFIED fixture',transferable_operation='fixture implementation',expected_benefit='unknown',applicability_conditions=['fixture'],refusal_conditions=['unrecognized structure'],counterexamples=[],unresolved_uncertainties=['MOCK cannot establish learned mechanism'])

def response(value):
    return dict(model=CONFIG.model,id='MOCK-'+fingerprint(value)[:16],status='completed',usage=dict(input_tokens=1,output_tokens=1,total_tokens=2),output=[dict(type='message',content=[dict(type='output_text',text=canonical(value))])])

def cases_and_manifest(cp):
    # Distinct engineering tasks exercise role plumbing, not natural transfer.
    fixtures=[('design','sum integers','1 2 3','6','pass','repair'),('gate','maximum integer','4 1 2','4','pass','repair'),('regression','echo integer','5','5','print(input())','decline'),('test','sort integers','3 1 2','1 2 3','pass','repair')]
    m={'discovery':dict(shard_id='discovery',source_groups=[cp['lineage_id']],items=[dict(problem_id=cp['task']['problem_id'],problem_family='historical-segment-combinatorics',source_lineage=cp['lineage_id'],generation_source='historical-model',source_group=cp['lineage_id'],provenance_reviewed=True,development_exposed=True)])}
    validators={cp['task']['problem_id']:validator(cp['task'],True)}
    for role,label,inp,expected,code,expect in fixtures:
        tid='engineering:'+role
        task=dict(problem_id=tid,prompt='ENGINEERING '+label,public_examples=[dict(input=inp,expected=expected,visibility='public',legal_verified=True)])
        c=dict(case_id=tid,task=task,code=code,lineage_id=tid,expectation=expect)
        m[role]=dict(shard_id=role,source_groups=[tid],cases=[c],items=[dict(problem_id=tid,problem_family=label,source_lineage=tid,generation_source=tid,source_group=tid,provenance_reviewed=True,development_exposed=False,engineering_only=True)])
        validators[tid]=validator(task)
    return m,validators

def mock_source():
    # Reference is ONLY a fixed mocked model RESPONSE. It never enters discovery
    # or a real generation prompt. This is not autonomous algorithm discovery.
    reference=(ROOT/'runs/s19g_train_expansion_20261024_01/tasks/taco-train-s00-r0298/reference_0.py').read_text()
    return '''def repair_operator(context):
    prompt = context['task_public']['prompt']
    if 'Peter has a sequence' in prompt:
        return {'status':'applied','candidate_code':%s}
    if prompt == 'ENGINEERING sum integers':
        return {'status':'applied','candidate_code':'print(sum(map(int, input().split())))'}
    if prompt == 'ENGINEERING maximum integer':
        return {'status':'applied','candidate_code':'print(max(map(int, input().split())))'}
    if prompt == 'ENGINEERING sort integers':
        return {'status':'applied','candidate_code':"print(' '.join(map(str, sorted(map(int, input().split())))))"}
    return {'status':'declined','reason':'out of engineering fixture scope'}
''' % repr(reference)

class SelectedStore:
    def __init__(self,store,eid):self.store=store;self.eid=eid;self.events=store.events;self.artifacts=store.artifacts
    def visible(self,at,stream_id=None):return tuple(x for x in self.store.visible(at,stream_id) if x['event_id']==self.eid)

def setup(root,*,kind='task_solver',decision='PROPOSE',source=None):
    store,fact,cp=history();selected=SelectedStore(store,fact['event_id']);m,validators=cases_and_manifest(cp)
    # Project an actual historical completion receipt into a NEW task-end journal.
    completion=next(r for r in map(json.loads,(ROOT/'runs/s20_taco80_m_20261025_01/stream.jsonl').read_text().splitlines()) if r['kind']=='TASK_FINALIZED' and r['payload']['task_id']==fact['task_id'])
    selected.events=EvidenceStore(root/'task_end_projection.jsonl')
    selected.events.append('TASK_COMPLETED',dict(stream_id=fact['stream_id'],task_id=fact['task_id'],historical_receipt_hash=completion['record_hash']),time.time())
    admission=TrustedLearningEvidence(selected,root/'admission.jsonl',validators)
    index=SymptomLearning(root/'symptoms.jsonl',selected,fact['stream_id'])
    admitted=admission.admit(cp,at=time.time())
    f=admitted['feedback'];feedback=PublicFeedback(f['status'],f['summary'],tuple(canonical(c) for c in f['public_cases']))
    index.ingest(fact,feedback,cp['code'],remaining_calls=0,at=time.time())
    queue=CompileQueue(root/'queue.jsonl');loop=LearningLoop(queue,selected,fact['stream_id'],root/'loop.jsonl')
    sent=[];values=[hyp(fact['event_id'],decision,kind),dict(code=source or mock_source(),description='MOCK fixture only',applicability='engineering scaffolding')]
    def sender(wire):
        sent.append(wire)
        return response(values[len(sent)-1])
    b=Budget(max_calls=7,max_tokens=400000,wall_seconds=300)
    adapter=MechanismCompilerAdapter(root/'provider.jsonl',b,config=CONFIG,mock=True,sender=sender)
    compiler=BoundedCompiler(adapter,b,root/'compiler.jsonl',CONFIG.model,max_input_upper=32768)
    registry=FailureOperatorRegistry(root/'registry.jsonl',selected)
    backend=FrozenLinuxBackend(image=IMAGE or 'unused',worker_script=WORKER)
    pipeline=ExecutableLearningPipeline(root/'pipeline',compiler,Budget(max_tools=200,wall_seconds=600),registry,CTX,backend,input_validators=validators)
    def run():return loop.run_pipeline(pipeline,design=m['design'],gate=m['gate'],regression=m['regression'],at=time.time(),data_manifest=m,public_builder=lambda job,at:admission.build(job,{cp['event_id']:cp},at=at))
    return run,pipeline,registry,sent,m,cp

class AdmissionTests(unittest.TestCase):
    def test_real_source_and_unknown_grammar(self):
        with tempfile.TemporaryDirectory() as td:
            store,fact,cp=history();a=TrustedLearningEvidence(store,Path(td)/'a',{})
            self.assertIsNone(a.admit(cp,at=time.time()))
            a.validators[cp['task']['problem_id']]=validator(cp['task'],True)
            self.assertEqual(a.admit(cp,at=time.time())['classification'],'PROGRAM_FAILURE')
    def test_illegal_SAMPLE_flag_does_not_certify(self):
        with tempfile.TemporaryDirectory() as td:
            store,fact,cp=history();cp['feedback']['cases'][0]['input']='3 SAMPLE 2'
            a=TrustedLearningEvidence(store,Path(td)/'a',{cp['task']['problem_id']:validator(cp['task'],True)})
            self.assertIsNone(a.admit(cp,at=time.time()))
            self.assertEqual(a.events.records()[-1]['kind'],'EVIDENCE_ERRATUM')
            self.assertEqual(a.events.records()[-1]['payload']['classification'],'INPUT_OR_SCORING_ERROR')
    def test_time_private_and_source_hash(self):
        with tempfile.TemporaryDirectory() as td:
            store,fact,cp=history();a=TrustedLearningEvidence(store,Path(td)/'a',{cp['task']['problem_id']:validator(cp['task'],True)})
            with self.assertRaises(ValueError):a.admit(cp,at=fact['observed_at']-1)
            c=copy.deepcopy(cp);c['task']['gold_answer']='SECRET'
            with self.assertRaises(ValueError):a.admit(c,at=time.time())
            c=copy.deepcopy(cp);c['code']+='\npass'
            with self.assertRaises(ValueError):a.admit(c,at=time.time())
    def test_three_decisions_and_no_verification_claim(self):
        for d in ('PROPOSE','HYPOTHESIS_ONLY','NO_MECHANISM'):self.assertEqual(parse_mechanism(hyp('fact',d))['decision'],d)
        with self.assertRaises(ValueError):parse_mechanism(dict(hyp('fact'),verified=True))
    def test_empty_evidence_not_sent(self):
        with tempfile.TemporaryDirectory() as td:
            a=MechanismCompilerAdapter(Path(td)/'p',Budget(),config=CONFIG,mock=True,sender=lambda _:self.fail('network'))
            with self.assertRaises(ValueError):a.preflight(dict(phase='induction',max_tokens=4096,discovery={'evidence':[]}))
    def test_no_mechanism_and_hypothesis_only_stop(self):
        for d in ('NO_MECHANISM','HYPOTHESIS_ONLY'):
            with tempfile.TemporaryDirectory() as td:
                run,p,reg,sent,m,cp=setup(Path(td),decision=d)
                result=run();self.assertEqual(len(sent),1);self.assertFalse(reg.events.records())
                self.assertEqual(result['status'],'no_mechanism' if d=='NO_MECHANISM' else 'shadow_retained')
                self.assertNotIn('ENGINEERING maximum',canonical(sent));self.assertNotIn('gold_answer',canonical(sent))
    def test_role_case_membership_and_no_private_generation(self):
        with tempfile.TemporaryDirectory() as td:
            run,p,reg,sent,m,cp=setup(Path(td))
            m['gate']['cases'][0]['task']['problem_id']='unauthorized-task'
            with self.assertRaises(ValueError):run()
            self.assertEqual(sent,[])
    def test_generation_key_and_version_separate_from_solver(self):
        self.assertNotEqual(CONFIG.model,CTX.model)
        with tempfile.TemporaryDirectory() as td:
            a=MechanismCompilerAdapter(Path(td)/'p',Budget(),config=CONFIG)
            with self.assertRaises(PermissionError):a.preflight({'phase':'induction','max_tokens':4096,'discovery':{'evidence':[{}]}})
    def test_unknown_generation_cannot_repeat(self):
        with tempfile.TemporaryDirectory() as td:
            run,p,reg,sent,_,_=setup(Path(td))
            calls=[]
            def broken(wire):calls.append(wire);raise ConnectionError('injected UNKNOWN')
            p.compiler.provider.sender=broken
            with self.assertRaises(ConnectionError):run()
            with self.assertRaises((ValueError,RuntimeError)):run()
            self.assertEqual(len(calls),1)
    def test_disabled_controller_identical(self):
        task={'problem_id':'fixture','prompt':'fixture'}
        def evaluate(t,c):return dict(visibility='public',status='PUBLIC_PASS',tests_run=1,tests_passed=1,cases=[])
        def generator(p,b):return dict(code='print(1)',model=CTX.model)
        class Disabled:
            enabled=False
            def begin(self,*a):raise AssertionError('disabled plugin executed')
        a=PreparedController(generator,evaluate,CTX,clock=lambda:1).solve(task,Budget(clock=lambda:0))
        b=PreparedController(generator,evaluate,CTX,clock=lambda:1,plugin=Disabled(),allow_task_start=True).solve(task,Budget(clock=lambda:0))
        self.assertEqual(a,b)
    def test_role_overlap_rejected(self):
        _,_,cp=history();m,_=cases_and_manifest(cp);m['test']['items'][0]['source_lineage']=m['gate']['items'][0]['source_lineage']
        with self.assertRaises(ValueError):validate_data_roles(m)

@unittest.skipUnless(IMAGE,'actual Linux image required')
class WorkerTests(unittest.TestCase):
    def test_real_source_mock_full_pipeline_and_future(self):
        output=os.environ.get('AUTONOMOUS_V2_OUTPUT')
        with tempfile.TemporaryDirectory() as td:
            root=Path(output).resolve() if output else Path(td)
            if output:root.mkdir(parents=True,exist_ok=False)
            run,p,reg,sent,m,cp=setup(root)
            result=run();self.assertEqual(result['status'],'ready_for_experimental_review')
            self.assertEqual(len(sent),2)
            self.assertNotIn('ENGINEERING maximum',canonical(sent))
            self.assertTrue(result['winner']['evaluation']['source_effective'])
            receipt=verify_controller_fallback(p,result);self.assertTrue(receipt['passed'])
            with self.assertRaises(PermissionError):p.authorize(result,experiment_id='research',stream_id='research',after_task=0,effective_from=1,at=time.time())
            card=p.authorize(result,experiment_id='engineering:pilot',stream_id='engineering:pilot',after_task=1,effective_from=2,at=time.time(),engineering=True)
            self.assertFalse(reg.snapshot(stream_id='engineering:pilot',experiment_id='engineering:pilot',task_index=1,at=time.time()).cards)
            future_store=FailureEvidenceStore(root/'future.jsonl')
            future_store.events.append('TASK_COMPLETED',dict(stream_id='engineering:pilot',task_id=cp['task']['problem_id'],task_index=1),time.time())
            hook=ExecutableOperatorHook(reg,future_store,CTX,stream_id='engineering:pilot',experiment_id='engineering:pilot',runner=p.runner,synthetic=True)
            # The source task is excluded even after publication at task index 2.
            hook.begin(__import__('failure_evo.contracts',fromlist=['PublicTaskView']).PublicTaskView.project(dict(cp['task'],problem_id='excluded-development')),time.time())
            self.assertFalse(hook.current['snapshot'].cards);hook.finish(time.time())
            def no_solver(*args):raise AssertionError('future Mock operator should solve without model')
            result2=PreparedController(no_solver,p.evaluator,CTX,plugin=hook,allow_task_start=True).solve(m['test']['cases'][0]['task'],Budget(max_tools=30,wall_seconds=120))
            self.assertEqual(result2['status'],'PUBLIC_ACCEPTED');self.assertEqual(result2['budget']['calls'],0)
            self.assertTrue(any(h['status']=='applied' for h in result2['hook_events']))
            self.assertEqual(reg.state(card)['opportunities_used'],1)
            (root/'future_result.json').write_text(canonical(result2)+'\n')
            reg.suspend(card,'engineering explicit negative-transfer governance probe',time.time())
            self.assertFalse(reg.snapshot(stream_id='engineering:pilot',experiment_id='engineering:pilot',task_index=3,at=time.time()).cards)
            (root/'acceptance.json').write_text(canonical(dict(status='REAL_WORKER_VERIFIED_MOCK_ONLY',real_failure_source=cp['event_id'],model_calls=0,independent_tasks='engineering fixtures, not natural transfer',future_solver_calls=0,origin='MOCK',production_authorized=False))+'\n')
    def test_invalid_or_forbidden_source_not_executed(self):
        for code in ('def broken(', "import os\ndef repair_operator(c):\n return {'status':'declined','reason':'no'}"):
            with tempfile.TemporaryDirectory() as td:
                run,p,reg,sent,_,_=setup(Path(td),source=code)
                result=run();self.assertEqual(result['status'],'shadow_retained')
                self.assertFalse(reg.events.records())
                self.assertEqual(p.budget.tool_calls,1)  # host static checker only
                self.assertEqual(len([r for r in p.events.records() if r['kind']=='GENERATED_OPERATOR']),1)
    def test_code_repair_kind_uses_existing_retry_contract(self):
        with tempfile.TemporaryDirectory() as td:
            run,p,reg,sent,_,_=setup(Path(td),kind='code_repair')
            result=run();self.assertEqual(result['status'],'ready_for_experimental_review')
            self.assertEqual(result['winner']['evaluation']['card']['hooks'],('before_native_retry',))
            self.assertTrue(verify_controller_fallback(p,result)['passed'])
    def test_source_no_effect_retained_shadow(self):
        with tempfile.TemporaryDirectory() as td:
            run,p,reg,sent,_,_=setup(Path(td),source="def repair_operator(c):\n return {'status':'declined','reason':'none'}")
            result=run();self.assertEqual(result['status'],'shadow_retained');self.assertEqual(len(sent),2)
            self.assertEqual(len(reg.events.records()),1)
    def test_independent_failure_no_permission(self):
        with tempfile.TemporaryDirectory() as td:
            source=mock_source().replace("print(max(map(int, input().split())))","print(0)")
            run,p,reg,sent,_,_=setup(Path(td),source=source)
            r=run();self.assertEqual(r['status'],'shadow_retained')
            self.assertEqual(len(sent),2)
            with self.assertRaises(ValueError):p.authorize(r,experiment_id='engineering:p',stream_id='engineering:p',after_task=0,effective_from=1,at=time.time(),engineering=True)

if __name__=='__main__':unittest.main(verbosity=2)
