"""Zero-API tests. Handwritten source below is a test fixture, never a learning seed."""
import json
import os
import time
from pathlib import Path
import tempfile
import unittest

from alfworld_.skill_acquisition import AcquisitionAdapter, INPUT_LIMIT, MODEL, SCHEMA, load_source
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.contracts import fingerprint
from failure_evo.math_skill_transfer import replay_train_generation
from failure_evo.math_stream import read
from failure_evo.runtime import BudgetExhausted
from failure_evo.run_health import RunUnhealthy
from run_alfworld_skill_acquisition import acceptance, create_accounts

SOURCE = Path.home()/'.local/share/flowevo/alfworld_full_library_online120_20261109_01'
FIXTURE = """def environment_operator(context):
    dest = context['goal'].split()[-1].rstrip('.')
    for action in context['admissible_commands']:
        if action.startswith('open '+dest+' ') or (action.startswith('move ') and ' to '+dest+' ' in action):
            return {'status':'applied','action':action,'state':{},'reason':'MOCK'}
    return {'status':'declined','state':{},'reason':'MOCK'}
"""


def response(payload):
    return dict(model=MODEL, id='MOCK', choices=[dict(message=dict(content=json.dumps(payload)),
                finish_reason='stop')], usage=dict(prompt_tokens=100, completion_tokens=100, total_tokens=200))


def fixture_sender(wire):
    payload = json.loads(wire['messages'][-1]['content'])
    if 'hypothesis' in payload:
        return response(dict(code=FIXTURE, description='MOCK fixture', applicability='MOCK fixture'))
    if payload['arm'] == 'A':
        return response(dict(decision='NO_MECHANISM', uncertainty='MOCK abstention'))
    event = payload['events'][0]
    proposal = {k:'MOCK' for k in SCHEMA}
    proposal.update(decision='PROPOSE', checkpoints=[dict(evidence_id=event['evidence_id'],
        step=event['anchor'], quote=event['steps'][event['anchor']-1][1])])
    return response(proposal)


@unittest.skipUnless(SOURCE.exists(), 'locked historical run required')
class AcquisitionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.arms, cls.host = load_source(SOURCE)

    def test_projection_roles_and_wires(self):
        self.assertEqual([len(self.arms[k]) for k in ('A','B')], [7,16])
        self.assertEqual(sum(len(e['steps']) for e in self.host.values()),673)
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as temp:
            root=Path(temp)
            budget=create_accounts(root, dict(run_id='projection'))
            adapter=AcquisitionAdapter(root/'provider.jsonl',budget,model=MODEL,mock=True,sender=fixture_sender,
                                       max_wire_input_upper=INPUT_LIMIT,
                                       evidence_sha256={a:fingerprint(v) for a,v in self.arms.items()})
            for arm,events in self.arms.items():
                request=dict(phase='induction',max_tokens=4096,discovery=dict(arm=arm,events=events))
                wire=adapter.preflight(request)
                self.assertEqual(json.loads(wire['messages'][-1]['content']),request['discovery'])
                self.assertNotIn('game_sha256',str(wire))
                self.assertNotIn('state_after',str(wire))
                self.assertNotIn('expert_plan',str(wire))
                self.assertNotIn('candidate_pool',str(wire))
                request['discovery']['events']=[dict(events[0],probe='CANARY')]+events[1:]
                with self.assertRaises(PermissionError):
                    adapter.preflight(request)
            self.assertFalse(adapter.events.records())

    def test_unauthorized_and_unknown_and_budget(self):
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as temp:
            root=Path(temp)
            budget=create_accounts(root, dict(run_id='fault'))
            real=AcquisitionAdapter(root/'real.jsonl',budget,model=MODEL,evidence_sha256={})
            with self.assertRaises(PermissionError):
                real.preflight({})
            calls=[]
            def broken(wire):
                calls.append(wire)
                raise TimeoutError('MOCK transport loss')
            adapter=AcquisitionAdapter(root/'mock.jsonl',budget,model=MODEL,mock=True,sender=broken,
                                       max_wire_input_upper=INPUT_LIMIT,
                                       evidence_sha256={a:fingerprint(v) for a,v in self.arms.items()})
            compiler=BoundedCompiler(adapter,budget,root/'compiler.jsonl',MODEL)
            job=dict(stream_id='fault',family_id='first',discovery=dict(arm='A',events=self.arms['A']))
            with self.assertRaises(TimeoutError):
                replay_train_generation(compiler,job,'induction')
            with self.assertRaises(RunUnhealthy):
                replay_train_generation(compiler,job,'induction')
            self.assertEqual(len(calls),1)
            for _ in range(3):
                budget.reserve(1,1)
            with self.assertRaises(BudgetExhausted):
                budget.reserve(1,1)

    def test_a_candidate_illegal_action(self):
        from alfworld_.failure_learning import EnvironmentPolicyRunner, context_view
        from alfworld_.skill_acquisition import acquire
        from failure_evo.autonomous_mvp import FrozenLinuxBackend
        from failure_evo.failure_events import FailureEvidenceStore
        from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
        from run_math_v3_development import IMAGE, WORKER

        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as temp:
            root = Path(temp)
            events = self.arms['A']
            event = events[0]
            original = self.host[event['evidence_id']]
            def sender(wire):
                payload = json.loads(wire['messages'][-1]['content'])
                if 'hypothesis' in payload:
                    return response(dict(description='MOCK', applicability='MOCK',
                        code="def environment_operator(c):\n return {'status':'applied','action':'not admissible','state':{},'reason':'MOCK'}\n"))
                proposal = {k:'MOCK' for k in SCHEMA}
                return response(dict(proposal, decision='PROPOSE', checkpoints=[dict(
                    evidence_id=event['evidence_id'], step=1, quote=event['steps'][0][1][:40])]))
            budget = create_accounts(root, dict(run_id='mock-illegal'))
            adapter = AcquisitionAdapter(root/'provider.jsonl', budget, model=MODEL, mock=True,
                sender=sender, max_wire_input_upper=INPUT_LIMIT, evidence_sha256={'A':fingerprint(events)})
            compiler = BoundedCompiler(adapter, budget, root/'compiler.jsonl', MODEL)
            registry = FailureOperatorRegistry(root/'registry.jsonl', FailureEvidenceStore(root/'evidence.jsonl'))
            backend = FrozenLinuxBackend(image=IMAGE, worker_script=WORKER)
            candidate = acquire('A', events, self.host, root/'A', compiler, registry, backend.manifest())
            self.assertEqual(candidate['status'], 'SHADOW')
            card = FailureOperator.from_dict(candidate['card'])
            ctx = context_view(event['goal'], original['initial']['observation'],
                               original['initial']['commands'], [], {})
            runner = EnvironmentPolicyRunner(backend, root/'worker.jsonl', budget)
            self.assertEqual(runner.run(card, ctx)['reason'], 'ACTION_NOT_ADMISSIBLE')
            self.assertEqual(budget.tool_calls, 1)
            self.assertEqual(runner.run(card, ctx)['reason'], 'ACTION_NOT_ADMISSIBLE')
            self.assertEqual(budget.tool_calls, 1)

    def test_end_to_end_and_resume(self):
        with tempfile.TemporaryDirectory(dir=SOURCE.parent) as temp:
            root=Path(os.environ.get('ALFWORLD_ACQUISITION_ACCEPTANCE', temp))
            calls=[]
            def sender(wire):
                calls.append(wire)
                return fixture_sender(wire)
            results=acceptance(SOURCE,root,sender)
            self.assertEqual(results['A']['status'],'NO_MECHANISM')
            self.assertEqual(results['B']['status'],'SHADOW')
            self.assertEqual(results['B']['checks'][0]['status'],'ALTERNATIVE_WON')
            self.assertEqual(len(calls),3)
            self.assertEqual(read(root/'source_replay.json')['steps'],673)
            self.assertEqual(results,acceptance(SOURCE,root,sender))
            self.assertEqual(len(calls),3)
            from failure_evo.evidence import EvidenceStore
            from failure_evo.failure_events import FailureEvidenceStore
            from failure_evo.failure_registry import FailureOperatorRegistry
            registry=FailureOperatorRegistry(root/'B/registry.jsonl',FailureEvidenceStore(root/'B/failures.jsonl'))
            self.assertFalse(registry.snapshot(stream_id='mock',task_index=121,experiment_id='mock',
                                               at=time.time()).cards)
            self.assertEqual(len([r for r in EvidenceStore(root/'worker.jsonl').records()
                                  if r['kind']=='ENVIRONMENT_POLICY_EXECUTED']),2)
            self.assertEqual(len(FailureEvidenceStore(root/'B/failures.jsonl').visible(time.time())),16)


if __name__=='__main__':
    unittest.main()
