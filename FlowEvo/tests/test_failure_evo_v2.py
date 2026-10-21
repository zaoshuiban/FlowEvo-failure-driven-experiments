"""S1.1 boundary tests. Temporary fixtures are engineering data, not research results."""
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from failure_evo import (Budget, Controller, Fingerprint, PublicFeedback, FailureEvidenceStore,
    CompileQueue, BoundedCompiler, FailureOperator, FailureOperatorRegistry, FailureLearningPlugin,
    SandboxOperatorRunner, checked_public_feedback)
from failure_evo.runtime import BudgetExhausted


class V2Acceptance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.fp = Fingerprint('native-adapter', 'public-v2', 'fixture', 'deps', 's1.1')
        self.store = FailureEvidenceStore(self.root / 'facts.jsonl')
        self.registry = FailureOperatorRegistry(self.root / 'registry.jsonl', self.store)
        self.task = {'task_id': 'target', 'prompt': 'return one', 'input_output': {'secret': 'HIDDEN'}, 'final_score': True}

    def tearDown(self):
        self.tmp.cleanup()

    def fact(self, code='', task='source', family='artifact_recovery', at=1, synthetic=False, feedback=None, **kw):
        return self.store.record(stream_id='s', task_id=task, family_id=family, stage='l1', code=code,
            feedback=feedback or PublicFeedback('NO_COMPLETE_CODE'), observed_at=at,
            available_from=at, provenance_group_id='source-group', synthetic=synthetic, **kw)

    def card(self, fact=None, **kw):
        fact = fact or self.fact()
        p = self.root / 'operator.py'
        p.write_text('def repair_operator(payload):\n    return {"status":"declined"}\n')
        return FailureOperator('recover', 'v1', str(p), hashlib.sha256(p.read_bytes()).hexdigest(),
            self.fp, 'audited-incomplete', (fact['event_id'],), ('source-group',), **kw)

    def gate(self, card, shard='g1', route='efficiency', pairs=None):
        pairs = pairs or [dict(checkpoint_id=str(i), source_group='gate-group', baseline_correct=True,
                              operator_correct=True, problem_id=str(i), baseline_cost=10, operator_cost=5) for i in range(2)]
        gate = dict(role='PILOT_ADMISSION', shard_id=shard, frozen_before_evaluation=True,
            independent_validation=True, contract_checks_passed=True, scope_checks_passed=True,
            generation_data_isolated=True, regression_passed=True, operator_id=card.operator_id,
            version=card.version, artifact_sha256=card.artifact_sha256,
            fingerprint=self.fp.to_dict(), scope=card.evidence_scope, evidence_ids=list(card.evidence_ids),
            experiment_id='pilot', evaluated_at=2, validation_source_groups=['gate-group'],
            benefit_route=route, cost_unit='fixture-token-units', paired_results=pairs)
        path = self.root / (shard + '.json'); path.write_text(json.dumps(gate)); return path

    def authorized(self, **kw):
        c = self.card(**kw); self.registry.register(c, 1)
        self.registry.authorize_experiment(c, self.gate(c), experiment_id='pilot', stream_id='s',
            after_task=0, effective_from=1, at=2)
        return c

    def solve(self, codes=None, feedback=None, runner=None, enabled=True, experiment='pilot', callback=None, **kw):
        requests = []
        responses = iter(codes if codes is not None else ['', '', '', '', ''])
        def generate(q):
            requests.append(copy.deepcopy(q))
            if callback: callback(len(requests))
            return {'code': next(responses), 'model': 'fixture', 'usage': {'total_tokens': 1}, 'finish_reason': 'length'}
        def evaluate(t, code):
            return feedback or {'visibility': 'public', 'status': 'PUBLIC_PASS', 'tests_run': 1, 'tests_passed': 1}
        plugin = FailureLearningPlugin(self.registry, self.store, self.fp, stream_id='s',
            experiment_id=experiment, runner=runner, enabled=enabled)
        result = Controller(generate, evaluate, self.fp, plugin=plugin, clock=lambda: 3, max_output=10).solve(
            kw.get('task', self.task), kw.get('budget', Budget(clock=lambda: 0)))
        return result, requests

    def runner(self, result, on_run=None):
        class Runner:
            def run(self, card, payload, timeout):
                if on_run: on_run(payload)
                return copy.deepcopy(result)
        return Runner()

    def test_single_artifact_fact_can_compile_without_mechanism_gate(self):
        f = self.fact()
        q = CompileQueue(self.root / 'queue.jsonl')
        jobs = q.due(self.store, 's', 1, 1)
        self.assertEqual(jobs[0]['evidence_ids'], [f['event_id']])
        out = q.compile(jobs[0], lambda j: {'status': 'shadow', 'usage': {'total_tokens': 1}}, Budget(clock=lambda: 0), at=1)
        self.assertEqual(out['status'], 'shadow')
        self.assertEqual(q.due(self.store, 's', 20, 2), ())

    def test_signal_private_and_length_complete_do_not_certify(self):
        self.assertIsNone(self.fact('x=1', feedback=PublicFeedback('WRONG_ANSWER')))
        self.assertIsNone(self.fact('', task='private', feedback=PublicFeedback('PRIVATE_RESULT_WITHHELD')))
        self.assertIsNone(self.fact('x=1', task='length', finish_reason='length'))
        self.assertEqual(self.store.visible(10), ())

    def test_synthetic_evidence_never_enters_queue_or_registry(self):
        f = self.fact(synthetic=True)
        self.assertEqual(CompileQueue(self.root / 'queue').due(self.store, 's', 1, 1), ())
        with self.assertRaises(ValueError): self.registry.register(self.card(f), 1)

    def test_evidence_available_from_and_dependencies(self):
        self.store.record(stream_id='s', task_id='a', family_id='artifact', stage='l1', code='',
            feedback=PublicFeedback('NO_COMPLETE_CODE'), observed_at=1, available_from=5)
        self.assertEqual(self.store.visible(4), ())
        self.assertEqual(len(self.store.visible(5)), 1)
        with self.assertRaises(ValueError): self.fact(task='b', at=6, source_evidence_ids=('future',))

    def test_queue_cooldown_new_evidence_and_family_limit(self):
        self.fact(); q = CompileQueue(self.root / 'queue')
        job = q.due(self.store, 's', 1, 1)[0]
        q.compile(job, lambda j: {'usage': {'total_tokens': 1}}, Budget(clock=lambda: 0), at=1)
        self.fact(task='new', at=2)
        self.assertEqual(q.due(self.store, 's', 2, 2), ())
        self.assertEqual(len(q.due(self.store, 's', 20, 2)), 1)

    def test_learning_failure_is_charged_and_not_retried(self):
        self.fact(); q = CompileQueue(self.root / 'queue'); job = q.due(self.store, 's', 1, 1)[0]
        b = Budget(clock=lambda: 0)
        def fail(j): raise ConnectionError('fixture')
        with self.assertRaises(ConnectionError): q.compile(job, fail, b, at=1)
        self.assertGreater(b.used_tokens, 0)
        with self.assertRaises(ValueError): q.compile(job, fail, b, at=1)

    def test_bounded_compiler_fourteen_requests_and_restart(self):
        b = Budget(max_calls=14, clock=lambda: 0)
        path = self.root / 'compiler'
        provider = lambda q: {'model': 'fixture', 'specification':'unit-only spec', 'code':'def repair_operator(p): return {"status":"declined"}', 'usage': {'total_tokens': 1}}
        for family in ['artifact', 'capacity']:
            job = dict(stream_id='s', family_id=family, evidence_ids=['unit-only'])
            compiler = BoundedCompiler(provider, b, path, 'fixture')
            compiler.request(job, 'induction', 0, 1)
            for phase in ('candidate', 'revision'):
                for slot in range(3): compiler.request(job, phase, slot, 1)
        self.assertEqual(b.calls, 14)
        with self.assertRaises(ValueError): compiler.request(job, 'candidate', 0, 1)
        with self.assertRaises(ValueError): compiler.request(dict(job, family_id='third'), 'induction', 0, 1)

    def test_compiler_unknown_usage_and_model_drift(self):
        b = Budget(max_calls=14, clock=lambda: 0)
        compiler = BoundedCompiler(lambda j: {'model': 'different'}, b, self.root / 'compiler', 'fixture')
        with self.assertRaises(ValueError): compiler.request(dict(stream_id='s', family_id='a'), 'induction', 0, 1)
        self.assertGreater(b.used_tokens, 0)

    def test_disabled_plugin_matches_legacy_entire_result(self):
        codes = ['x=1'] * 5
        out, req = self.solve(codes=codes, enabled=False)
        calls = []
        def generate(q): calls.append(q); return {'code': 'x=1', 'model': 'fixture', 'usage': {'total_tokens': 1}}
        old = Controller(generate, lambda t,c: {'visibility':'public', 'status':'PUBLIC_PASS', 'tests_run':1, 'tests_passed':1},
                         self.fp, clock=lambda:3, max_output=10).solve(self.task, Budget(clock=lambda:0))
        self.assertEqual(out, old); self.assertEqual(req, calls)
        self.assertEqual(self.store.events.records(), [])

    def test_shadow_and_unapproved_experiment_do_not_change_requests(self):
        c = self.card(); self.registry.register(c, 1)
        out, req = self.solve(runner=self.runner({'status':'applied','candidate_code':'x=1'}))
        self.assertEqual(out['budget']['calls'], 5)
        self.assertEqual(out['hook_events'], [])
        self.assertTrue(all('operator_proposal' not in q for q in req))

    def test_next_task_barrier_and_snapshot_freezes_midtask_publication(self):
        c = self.card(); self.registry.register(c, 1)
        def publish(n):
            if n == 1:
                self.registry.authorize_experiment(c, self.gate(c), experiment_id='pilot', stream_id='s',
                    after_task=1, effective_from=2, at=2)
        out, req = self.solve(callback=publish, runner=self.runner({'status':'applied','candidate_code':'x=1'}))
        self.assertEqual(out['budget']['calls'], 5)
        out2, req2 = self.solve(task=dict(self.task, task_id='next'), runner=self.runner({'status':'applied','candidate_code':'x=1'}))
        self.assertEqual(out2['budget']['calls'], 1)
        self.assertEqual(out2['selected']['code'], 'x=1')

    def test_current_task_publication_rejected(self):
        c = self.card(); self.registry.register(c, 1)
        with self.assertRaises(ValueError):
            self.registry.authorize_experiment(c, self.gate(c), experiment_id='pilot', stream_id='s', after_task=1, effective_from=1, at=2)

    def test_efficiency_pilot_does_not_require_correctness_wins(self):
        self.authorized()
        snap = self.registry.snapshot(stream_id='s', task_index=1, experiment_id='pilot', at=3)
        self.assertEqual(len(snap.cards), 1)
        self.assertEqual(self.registry.snapshot(stream_id='s', task_index=1, at=3).cards, ())

    def test_failed_gate_consumed_no_second_candidate_fishing(self):
        c = self.card(); self.registry.register(c, 1)
        gate = self.gate(c); data=json.loads(gate.read_text());data['regression_passed']=False;gate.write_text(json.dumps(data))
        with self.assertRaises(ValueError): self.registry.authorize_experiment(c, gate, experiment_id='pilot',stream_id='s',after_task=0,effective_from=1,at=2)
        gate = self.gate(c)
        with self.assertRaisesRegex(ValueError, 'consumed'): self.registry.authorize_experiment(c, gate, experiment_id='pilot',stream_id='s',after_task=0,effective_from=1,at=2)

    def test_gate_tamper_and_artifact_drift_revoke(self):
        c = self.authorized()
        self.assertTrue(self.registry.valid(c, 3))
        (self.root / 'g1.json').write_text('{}')
        self.assertFalse(self.registry.valid(c, 3))

    def test_evidence_drift_revokes(self):
        c = self.authorized()
        (self.store.artifacts / (self.store.visible(3)[0]['candidate_sha256']+'.py')).write_text('changed')
        self.assertFalse(self.registry.valid(c, 3))

    def test_hook_applies_host_validated_candidate(self):
        self.authorized()
        out, req = self.solve(runner=self.runner({'status':'applied','candidate_code':'x=1','validation_status':'not_checked'}))
        self.assertEqual(out['status'], 'PUBLIC_ACCEPTED')
        self.assertEqual(len(req), 1)
        self.assertEqual(out['hook_events'][0]['validation_status'], 'public_tests_pass')
        self.assertEqual(len(out['candidate_ledger']), 2)

    def test_false_self_pass_and_empty_checks_cannot_accept(self):
        self.authorized()
        out, req = self.solve(runner=self.runner({'status':'applied','candidate_code':'x=1','validation_status':'public_tests_pass'}),
                              feedback={'visibility':'public','status':'PUBLIC_PASS','tests_run':0,'tests_passed':0})
        self.assertIsNone(out['selected']); self.assertEqual(len(req), 5)
        self.assertEqual(out['status'], 'UNRESOLVED')
        self.assertEqual(len(out['candidate_ledger']), 10)

    def test_private_feedback_bit_not_exposed_to_hook_or_learning(self):
        self.authorized(); payloads=[]
        out, req = self.solve(runner=self.runner({'status':'declined'}, payloads.append),
            codes=['x=1']*5, feedback={'visibility':'private','status':'PUBLIC_PASS','secret':'HIDDEN'})
        self.assertEqual(out['status'], 'UNRESOLVED')
        self.assertNotIn('HIDDEN', json.dumps(payloads)+json.dumps(req))
        self.assertEqual(self.store.visible(3)[0]['task_id'], 'source')
        self.assertEqual(len(self.store.visible(3)), 1)

    def test_decline_and_exception_keep_native_calls_and_budget(self):
        self.authorized()
        out, req = self.solve(runner=self.runner({'status':'declined'}))
        self.assertEqual(len(req), 5);self.assertEqual(out['budget']['tool_calls'], 5)
        self.assertEqual(len(out['candidate_ledger']), 5)

    def test_invalid_candidate_and_extra_permissions_cannot_replace(self):
        self.authorized()
        out, req = self.solve(runner=self.runner({'status':'applied','candidate_code':'x=1','max_calls':999}))
        self.assertIsNone(out['selected']);self.assertEqual(len(req),5)
        self.assertTrue(all(e['status']=='error' for e in out['hook_events']))

    def test_final_hook_and_existing_candidate_selection(self):
        self.authorized(hooks=('before_final_return',), structural_statuses=(), prompt_terms=('return',),
                        allowed_feedback=('WRONG_ANSWER',))
        calls=[0]
        def evaluation(t,c):
            calls[0]+=1
            return {'visibility':'public','status':'WRONG_ANSWER'} if calls[0]<=5 else {'visibility':'public','status':'PUBLIC_PASS','tests_run':1,'tests_passed':1}
        plugin=FailureLearningPlugin(self.registry,self.store,self.fp,stream_id='s',experiment_id='pilot',runner=self.runner({'status':'applied','selected_candidate_id':'c1'}))
        out=Controller(lambda q:{'code':'x=1','model':'fixture','usage':{'total_tokens':1}},evaluation,self.fp,clock=lambda:3,max_output=10,plugin=plugin).solve(self.task,Budget(clock=lambda:0))
        self.assertEqual(out['selected']['stage'],'final');self.assertEqual(out['budget']['calls'],5)
        self.assertEqual(out['hook_events'][0]['hook'],'before_final_return')

    def test_tool_exhaustion_keeps_original_artifact(self):
        self.authorized()
        out, req=self.solve(runner=self.runner({'status':'applied','candidate_code':'x=1'}),budget=Budget(max_tools=0,clock=lambda:0))
        self.assertEqual(len(req),5);self.assertIsNone(out['selected'])
        self.assertEqual(len(out['candidate_ledger']),5)

    def test_finish_reason_length_does_not_discard_complete_code(self):
        out, req=self.solve(codes=['x=1']*5)
        self.assertEqual(len(req),1);self.assertEqual(out['status'],'PUBLIC_ACCEPTED')

    def test_suspension_inside_task_is_respected(self):
        c=self.authorized()
        def revoke(n):
            if n==1:self.registry.suspend(c,'fixture revoke',3)
        out,req=self.solve(callback=revoke,runner=self.runner({'status':'applied','candidate_code':'x=1'}))
        self.assertEqual(len(req),5);self.assertEqual(out['hook_events'],[])

    def test_evidence_only_available_after_task_finishes(self):
        during=[]
        out,req=self.solve(callback=lambda n:during.append(len(self.store.visible(3))))
        self.assertEqual(during,[0]*5);self.assertEqual(len(self.store.visible(3)),5)
        self.assertEqual(out['candidate_ledger'][0]['code'],'')

    def test_signature_break_declines(self):
        self.authorized()
        out,req=self.solve(task=dict(self.task,function_name='solve'),runner=self.runner({'status':'applied','candidate_code':'x=1'}))
        self.assertIsNone(out['selected']);self.assertEqual(len(req),5)

    def test_revoked_evidence_invalidates_dependents_and_operator(self):
        c=self.authorized()
        self.store.revoke(c.evidence_ids[0],'retracted fixture',3)
        self.assertEqual(self.store.visible(3),())
        self.assertFalse(self.registry.valid(c,3))
        self.assertFalse(self.registry.valid(c,None))

    def test_model_drift_artifact_retained_but_not_learned(self):
        plugin=FailureLearningPlugin(self.registry,self.store,self.fp,stream_id='s')
        out=Controller(lambda q:{'code':'','model':'wrong','usage':{'total_tokens':1}},
            lambda t,c:None,self.fp,clock=lambda:3,max_output=10,plugin=plugin).solve(self.task,Budget(clock=lambda:0))
        self.assertEqual(len(out['candidate_ledger']),1)
        self.assertEqual(self.store.visible(3),())
        self.assertEqual(out['hook_events'],[])

    def test_native_prompt_matches_archived_prompt_function(self):
        import ast
        from failure_evo.native_adapter import prompt_for
        source=Path(__file__).resolve().parents[2]/'experiments/flowevo_taco_lcb_20261019/evidence/benchmark.py'
        tree=ast.parse(source.read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prompt_for')
        namespace={};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),namespace)
        for starter,name in [('', ''),('def solve(x): pass','solve')]:
            task=dict(prompt='public problem',starter_code=starter,function_name=name)
            self.assertEqual(prompt_for(task),namespace['prompt_for'](task))

    def test_native_success_library_and_shadow_parity(self):
        from failure_evo import NativeBenchmarkSession
        class Library:
            def __init__(self):self.added=[]
            def retrieve(self,t):return {'context':'previous-public-success'}
            def add(self,t,c):self.added.append((t,c))
        all_requests=[]
        for enable in [False,True]:
            local_store=FailureEvidenceStore(self.root/str(enable)/'facts')
            registry=FailureOperatorRegistry(self.root/str(enable)/'registry',local_store)
            plugin=FailureLearningPlugin(registry,local_store,self.fp,stream_id='s',enabled=enable)
            library=Library();requests=[];counter=[0]
            def model(q):requests.append(copy.deepcopy(q));return {'text':'x=1','model':'fixture','usage':{'total_tokens':1}}
            def evaluate(t,c):
                counter[0]+=1
                return {'visibility':'public','status':'PUBLIC_PASS','tests_run':1,'tests_passed':1} if counter[0]==4 else {'visibility':'public','status':'WRONG_ANSWER'}
            out=NativeBenchmarkSession(model,evaluate,self.fp,library=library,instance_factory=lambda t:t,
                extract_code=lambda t,i:t,plugin=plugin,clock=lambda:3,max_output=10).solve(self.task,Budget(clock=lambda:0))
            self.assertEqual(len(library.added),1);self.assertEqual(len(requests),4)
            self.assertNotIn('HIDDEN',json.dumps(requests));self.assertIn('previous-public-success',requests[3]['prompt'])
            self.assertNotIn('previous-public-success',requests[0]['prompt']);all_requests.append(requests)
        self.assertEqual(all_requests[0],all_requests[1])

    def test_native_prompt_context_is_reserved_in_budget(self):
        from failure_evo import NativeBenchmarkSession
        class Library:
            def retrieve(self,t):return {'context':'x'*10000}
            def add(self,*a):raise AssertionError('no public acceptance')
        calls=[]
        session=NativeBenchmarkSession(lambda q:calls.append(q) or {'text':'x=1','model':'fixture','usage':{'total_tokens':1}},
            lambda t,c:{'visibility':'public','status':'WRONG_ANSWER'},self.fp,library=Library(),
            instance_factory=lambda t:t,extract_code=lambda t,i:t,clock=lambda:3,max_output=10)
        out=session.solve(self.task,Budget(max_tokens=10000,clock=lambda:0))
        self.assertEqual(len(calls),3);self.assertEqual(out['budget']['calls'],3)

    def test_learning_loop_is_task_end_only_and_resolves_pinned_sources(self):
        from failure_evo import LearningLoop
        self.fact();q=CompileQueue(self.root/'queue');loop=LearningLoop(q,self.store,'s',self.root/'learning')
        self.assertEqual(loop.pending(1),())
        self.store.events.append('TASK_COMPLETED',dict(stream_id='s',task_id='source',task_index=1),1)
        jobs=loop.pending(1);public=loop.public_input(jobs[0],1)
        self.assertEqual(len(public['source_programs']),1)
        compiler=BoundedCompiler(lambda j:{'model':'fixture','specification':'unit-only specification','usage':{'total_tokens':1}},
            Budget(max_calls=14,clock=lambda:0),self.root/'compiler','fixture')
        out=loop.run_pending(compiler,at=1)
        self.assertEqual(len(out),1);self.assertEqual(loop.pending(1),())
        completed=[r for r in compiler.events.records() if r['kind']=='GENERATION_COMPLETED']
        self.assertEqual(completed[0]['payload']['content'],'unit-only specification')

    def test_provider_artifact_retained_when_public_tool_budget_exhausted(self):
        out,req=self.solve(codes=['x=1']*5,budget=Budget(max_tools=0,clock=lambda:0))
        self.assertEqual(len(req),1)
        self.assertEqual(out['candidate_ledger'][0]['code'],'x=1')
        self.assertIsNone(out['selected'])

    def test_declined_invalid_operator_candidate_stays_in_ledger(self):
        self.authorized()
        out,req=self.solve(runner=self.runner({'status':'applied','candidate_code':'def broken('}))
        self.assertEqual(len(req),5)
        self.assertEqual(len(out['candidate_ledger']),10)
        self.assertEqual(out['candidate_ledger'][1]['structural_status'],'COMPILE_ERROR')

    def test_budget_invalid_numeric_values_rejected(self):
        for value in [float('nan'),float('inf'),True,-1]:
            with self.assertRaises(ValueError):Budget(wall_seconds=value)
        b=Budget(clock=lambda:0)
        for a,z in [(-1,2),(True,2),(1,-1),(1,1.5)]:
            with self.assertRaises(ValueError):b.reserve(a,z)
        self.assertEqual(b.calls,0)

    def test_expired_operator_cannot_accept_or_refund(self):
        self.authorized()
        now=[0]
        def overrun(payload):now[0]=100
        out,req=self.solve(runner=self.runner({'status':'applied','candidate_code':'x=1'},overrun),
            budget=Budget(wall_seconds=10,clock=lambda:now[0]))
        self.assertEqual(len(req),1);self.assertIsNone(out['selected'])
        self.assertEqual(out['budget']['tool_calls'],1)

    def test_sandbox_v2_contract_and_source_snapshot(self):
        c=self.card()
        class Worker:
            def __init__(self,p):self.path=p
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def call(self,q):return {'status':'OK','value':{'status':'applied','candidate_code':'x=1'}}
        self.assertEqual(SandboxOperatorRunner(Worker,protocol='v2').run(c,{},1)['status'],'applied')


if __name__=='__main__':unittest.main()
