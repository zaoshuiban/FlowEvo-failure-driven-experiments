"""Boundaries for the ALFWorld adapter on existing permission infrastructure."""
from dataclasses import replace
from pathlib import Path
import tempfile
import time
import unittest

from alfworld_.failure_learning import static_check,context_view,EnvironmentCompilerAdapter
from failure_evo.contracts import Fingerprint
from failure_evo.failure_registry import FailureOperator,ENVIRONMENT_HOOK
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.math_skill_transfer import replay_train_generation
from failure_evo.math_stream import budget
from failure_evo.runtime import BudgetExhausted


class EnvironmentLearningTests(unittest.TestCase):
    def card(self):
        return FailureOperator('id','version','/absent','digest',Fingerprint('a','b','c','d','e'),'scope',
                               ('event',),('group',),hooks=(ENVIRONMENT_HOOK,),stages=('environment',),
                               allowed_actions=('environment_action',),operator_kind='environment_policy')

    def test_environment_permissions_do_not_leak_into_code_repair(self):
        card=self.card()
        with self.assertRaises(ValueError):
            replace(card,operator_kind='code_repair')
        with self.assertRaises(ValueError):
            replace(card,allowed_actions=('candidate_code',))
        with self.assertRaises(ValueError):
            replace(card,hooks=('before_native_retry',))

    def test_static_rejects_io_dynamic_execution_and_nonlocal(self):
        good="def environment_operator(c):\n return {'status':'declined','state':{},'reason':'uncertain'}"
        self.assertTrue(static_check(good)['passed'])
        for prefix in ('import socket\n','import os\n','open("/etc/passwd")\n'):
            self.assertFalse(static_check(prefix+good)['passed'])
        self.assertFalse(static_check(good+'\nexec("x=1")')['passed'])

    def test_context_has_no_registry_identity_or_hidden_data(self):
        view=context_view('goal','observation',['look'],[dict(action='look',observation='room',secret='private')],{})
        self.assertEqual(set(view),{'goal','observation','admissible_commands','history','state'})
        self.assertEqual(view['history'],[dict(action='look',observation='room')])
        with self.assertRaises(ValueError):
            context_view('goal','room',['look'],[],{'x':'a'*4097})

    def test_no_mechanism_settles_and_replays_without_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            b=budget(root/'budget.jsonl','engineering:alf-compile','fixture',calls=1)
            calls=[]
            def sender(wire):
                calls.append(wire)
                import json
                value=dict(decision='NO_MECHANISM',operator_category='unknown',common_failure='unconfirmed',
                    root_cause_hypothesis='unknown',executable_suggestion='none',applicability='unknown',
                    exclusions='unknown',uncertainties='one event')
                return dict(id='MOCK',model='deepseek-flash',usage=dict(prompt_tokens=10,completion_tokens=10,total_tokens=20),
                            choices=[dict(message=dict(content=json.dumps(value)),finish_reason='stop')])
            p=EnvironmentCompilerAdapter(root/'provider.jsonl',b,model='deepseek-flash',mock=True,sender=sender)
            c=BoundedCompiler(p,b,root/'compiler.jsonl','deepseek-flash')
            job=dict(stream_id='engineering:alf-compile',family_id='source',
                     discovery=dict(shared_cause='UNVERIFIED',evidence=[dict(evidence_id='e',goal='g',
                       initial_observation='o',steps=[dict(action='look',observation='room',decision_output='look',actor='MODEL')],
                       won=False,trace_sha256='hash',omitted_steps=0)]))
            result=replay_train_generation(c,job,'induction')
            self.assertEqual(replay_train_generation(c,job,'induction'),result)
            self.assertEqual(len(calls),1)
            with self.assertRaises(BudgetExhausted):
                c.request(dict(job,family_id='extra'),'induction',0,time.time())

    def test_private_fields_rejected_before_model_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            b=budget(root/'budget.jsonl','engineering:alf-compile','fixture',calls=1)
            p=EnvironmentCompilerAdapter(root/'provider.jsonl',b,model='deepseek-flash',mock=True,
                                         sender=lambda _:self.fail('must not send'))
            request=dict(phase='induction',max_tokens=4096,discovery=dict(shared_cause='UNVERIFIED',evidence=[
                dict(evidence_id='e',goal='g',initial_observation='o',steps=[],won=False,trace_sha256='h',
                     omitted_steps=0,expert_plan=['oracle'])]))
            with self.assertRaises(PermissionError):
                p.preflight(request)

    def test_other_source_witness_cannot_be_used_as_independent_gate(self):
        import hashlib
        from types import SimpleNamespace
        from alfworld_.learning_runtime import validate_and_publish

        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            code="def environment_operator(c):\n return {'status':'declined','state':{},'reason':'uncertain'}"
            path=root/'policy.py'
            path.write_text(code)
            card=replace(self.card(),artifact_path=str(path),artifact_sha256=hashlib.sha256(code.encode()).hexdigest(),
                         source_group_ids=('game:a','game:b'))
            registry=SimpleNamespace(evidence=SimpleNamespace(visible=lambda at:[dict(event_id='event',task_id='source')]))
            with self.assertRaisesRegex(PermissionError,'overlaps learning'):
                validate_and_publish(card,dict(task_id='source',game_sha256='a'),
                    [dict(task_id='another-source',game_sha256='b')],root=root,data_root=root,
                    registry=registry,runner=None,client_factory=lambda _:self.fail('must not evaluate'),
                    stream_id='s',experiment_id='e',after_sequence=0)
            self.assertFalse((root/'validation.jsonl').exists())

    def test_native_fallback_success_cannot_hide_a_policy_contract_error(self):
        import hashlib
        from types import SimpleNamespace
        from unittest.mock import patch
        from alfworld_.learning_runtime import validate_and_publish
        from alfworld_.schemas import AlfWorldTrace

        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            code="def environment_operator(c):\n return {'status':'declined','state':{},'reason':'uncertain'}"
            path=root/'policy.py'
            path.write_text(code)
            card=replace(self.card(),artifact_path=str(path),artifact_sha256=hashlib.sha256(code.encode()).hexdigest(),
                         source_group_ids=('game:a',))
            registry=SimpleNamespace(evidence=SimpleNamespace(visible=lambda at:[dict(event_id='event',task_id='source')]),
                                     authorize_experiment=lambda *a,**k:self.fail('must not publish'))
            runner=SimpleNamespace(backend=SimpleNamespace(manifest=lambda:{'worker':'fixture'}))
            traces=[(AlfWorldTrace(success=False),'initial'),
                    (AlfWorldTrace(success=True,direct_use_count=1,direct_failure_count=1),'initial')]
            with patch('alfworld_.learning_runtime.execute_episode',side_effect=traces) as execute:
                result=validate_and_publish(card,dict(task_id='source',game_sha256='a'),
                    [dict(task_id='gate',game_sha256='b')],root=root,data_root=root,
                    registry=registry,runner=runner,client_factory=lambda _:None,
                    stream_id='s',experiment_id='e',after_sequence=0,engineering=True)
                self.assertEqual(execute.call_count,2)
                self.assertEqual(result['status'],'SHADOW_SOURCE_NOT_REPAIRED')

    def test_paired_regression_suspends_the_exact_used_version(self):
        from types import SimpleNamespace
        from alfworld_.learning_stream import LearningStream
        from failure_evo.evidence import EvidenceStore

        with tempfile.TemporaryDirectory() as tmp:
            card=self.card()
            stopped=[]
            registry=SimpleNamespace(
                events=SimpleNamespace(records=lambda:[dict(kind='SHADOW_REGISTERED',payload={'card':card.to_dict()})]),
                state=lambda c:{'permission':'suspended' if stopped else 'experimental'},
                suspend=lambda c,reason,at:stopped.append((c.version,reason)))
            controller=LearningStream.__new__(LearningStream)
            controller.registry=registry
            controller.events=EvidenceStore(Path(tmp)/'events.jsonl')
            event=dict(record_hash='paired-receipt',payload=dict(task_id='later',regression=True,
                G={'trace':{'success':True,'llm_call_count':4}},
                F={'trace':{'success':False,'llm_call_count':3,'used_skills':[card.version]}}))
            controller.record_paired_use(event)
            controller.record_paired_use(event)
            self.assertEqual(stopped,[(card.version,'paired_future_reliability_regression')])
            self.assertEqual(len(controller.events.records()),1)

    def test_identical_source_cannot_reset_an_old_version_permission(self):
        import hashlib,json
        from types import SimpleNamespace
        from unittest.mock import patch
        from alfworld_.failure_learning import create_candidate

        with tempfile.TemporaryDirectory() as tmp:
            code="def environment_operator(c):\n return {'status':'declined','state':{},'reason':'uncertain'}"
            digest=hashlib.sha256(code.encode()).hexdigest()
            fields=('operator_category','common_failure','root_cause_hypothesis','executable_suggestion',
                    'applicability','exclusions','uncertainties')
            hypothesis=dict(decision='PROPOSE',**{k:'unverified fixture' for k in fields})
            store=SimpleNamespace(visible=lambda at,stream:[dict(event_id='e',provenance_group_id='g')])
            view=dict(goal='goal',initial_observation='room',steps=[dict(action='look',observation='room',
                      decision_output='look',actor='MODEL')],won=False)
            views=SimpleNamespace(records=lambda:[dict(kind='ENVIRONMENT_FAILURE_IMPORTED',
                                                       payload=dict(event_id='e',public=view))])
            registry=SimpleNamespace(events=SimpleNamespace(records=lambda:[dict(kind='SHADOW_REGISTERED',
                payload={'card':{'artifact_sha256':digest,'version':'old-version'}})]),
                register=lambda *a:self.fail('duplicate source must not re-register'))
            compiler=SimpleNamespace(provider=SimpleNamespace(mock=True),
                                     budget=SimpleNamespace(config={'run_id':'engineering:fixture'}))
            with patch('alfworld_.failure_learning.replay_train_generation',
                       side_effect=[{'specification':json.dumps(hypothesis)},{'code':code}]):
                result=create_candidate(Path(tmp),compiler,store,views,stream_id='engineering:fixture',
                    evidence_ids=['e'],worker_manifest={},registry=registry,engineering=True)
            self.assertEqual(result['status'],'DUPLICATE_SOURCE_REJECTED')


if __name__=='__main__':
    unittest.main()
