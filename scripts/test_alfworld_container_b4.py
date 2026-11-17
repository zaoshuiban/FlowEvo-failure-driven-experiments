"""B4 zero API tests; no Mock result is a learned skill."""
import json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from collections import Counter
import prepare_alfworld_container_b4 as D
import run_alfworld_container_b4 as R
from test_alfworld_container_information import response,proposal,DECLINE
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from alfworld_.route_b_compact_projection import decode
P=D.P;M=D.M;PRE=D.ROOT/'runs/alfworld_route_b4_preparation_20261116_03'

def evaluate(row,p,cases,role,budget,out):
    sources=[dict(source_ref=c['id'],stop='DECLINED',won=False,actions=[],decisions=[dict(operator=dict(status='declined',state={},reason='own:'+row['version']),worker_status='OK',selected_action=None,receipt=None)]) for c in cases if c['label']=='MATCH']
    return dict(role=role,case_ids=[c['id'] for c in cases],candidate_version=row['version'],code_sha256=row['code_sha256'],sources=sources,controls=[],
        metrics=dict(repairs=0,deliveries=0,won=0,errors=0,incompatible=0,unsupported=0,actions=0,controls_declined=0,worker_ok=len(cases),worker_calls=len(cases)),permission='shadow')

class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.p=P.read(PRE/'protocol.json');cls.d22=cls.p['train']['FR22'];cls.d11=cls.p['train']['FR11']
    def test_01_twenty_two_verified_sources(self):
        self.assertEqual(len(self.d22),22);self.assertTrue(all(c['replay_verification']['verified'] for c in self.d22))
    def test_02_stratified_fixed_subset(self):
        self.assertEqual(len(self.d11),11);self.assertLessEqual(set(self.p['d11']),set(self.p['d22']))
        self.assertEqual(Counter(c['source_provenance'] for c in self.d11),{'NATURAL_AGENT_FAILURE':6,'CONTROLLED_INTERVENTION':5})
    def test_03_game_and_state_dedup(self):
        self.assertEqual(len({M.identity(c) for c in self.d22}),22);self.assertEqual(len({c['physical_group'] for c in self.d22}),22)
    def test_04_reserved_pool_isolation(self):
        future=P.read(D.PROSPECTIVE)['tasks'];D.disjoint(self.d22,self.p['validation'],future)
        with self.assertRaises(PermissionError):D.disjoint(self.d22,self.d11,future)
    def test_05_natural_controlled_identity(self):
        self.assertEqual(Counter(c['source_provenance'] for c in self.d22),{'NATURAL_AGENT_FAILURE':11,'CONTROLLED_INTERVENTION':11})
    def test_06_same_recovery(self):
        for rows in (self.d11,self.d22):
            packs=M.packets(rows)
            for s,fr in zip(packs['S']['examples'],packs['FR']['examples']):self.assertEqual(s['R'],fr['R'])
    def test_07_same_failed_prefix(self):
        for rows in (self.d11,self.d22):
            packs=M.packets(rows)
            for f,fr in zip(packs['F']['examples'],packs['FR']['examples']):self.assertEqual(f['F'],fr['F'])
    def test_08_success_no_omitted_failure(self):
        for r in M.packets(self.d22)['S']['examples']:
            self.assertNotIn('F',r);self.assertNotIn('Nothing happens.',r['C']['observation']);self.assertFalse(r['R']['start_context']['observation_included'])
    def test_09_failure_no_suffix_and_lossless(self):
        for r in M.packets(self.d22)['F']['examples']:self.assertNotIn('R',r)
        for cell in M.CELLS:
            w=P.read(PRE/'inputs'/f'{cell}.wire.private.json');self.assertEqual(decode(json.loads(w['messages'][1]['content'])),P.read(PRE/'inputs'/f'{cell}.private.json'))
    def test_10_same_prompt(self):
        self.assertEqual(len({P.read(PRE/'inputs'/f'{c}.wire.private.json')['messages'][0]['content'] for c in M.CELLS}),1)
    def test_11_offline_runtime_contract_not_model_understanding(self):
        for word in ('OFFLINE SKILL AUTHORING','No live observation','FUTURE RUNTIME','Empty state','ABSTAIN'):
            self.assertIn(word,M.COMMON)
        self.assertNotIn('Shared task: continue',M.COMMON)
    def test_12_parameterized_mock_without_live_context(self):
        self.assertTrue(D.E.P.static_check_detailed(DECLINE)['passed'])
        for c in M.CELLS:self.assertNotIn('current_context',P.read(PRE/'inputs'/f'{c}.private.json'))
    def test_13_frozen_budget_uniform_limits(self):
        self.assertEqual(self.p['max_calls'],54);self.assertEqual(self.p['max_tokens'],54*(524544+4096));self.assertFalse(self.p['paid_authorization'])
        self.assertTrue(all(self.p['measurements'][c]['wire_bytes']<=524288 for c in M.CELLS))
    def test_14_four_drafts_each(self):self.assertEqual(self.p['initial_per_cell'],4);self.assertEqual(len(M.CELLS),6)
    def test_15_early_stop_exactly_twelve_valid_abstentions(self):
        a=[dict(status='ABSTAIN')]*12;self.assertTrue(M.early_stop(a));self.assertFalse(M.early_stop(a[:11]));self.assertFalse(M.early_stop(a[:11]+[dict(status='DELIVERY_REJECTED')]))
    def test_16_no_success_required_for_behavior_revision(self):
        x=dict(id='x',train_evaluation=dict(metrics=dict(worker_ok=1,repairs=0,errors=0,incompatible=0,unsupported=0)))
        self.assertIs(M.behavior_parent([x],11),x)
    def test_17_feedback_own_only_no_validation(self):
        row=dict(version='own',code_sha256='s');ev=evaluate(row,self.p,self.d11,'TRAIN',None,None)
        ev['validation_labels']='CANARY';payload=M.behavior_payload(DECLINE,'own',self.d11,ev,lambda _:True)
        self.assertNotIn('CANARY',P.canonical(payload));self.assertEqual(len(payload['own_execution_feedback']),11)
        with self.assertRaises(PermissionError):M.behavior_payload(DECLINE,'other',self.d11,ev,lambda _:True)
    def test_18_all_decline_never_selected(self):
        x=dict(id='x',version='v',lineage_tokens=10,validation_evaluation=evaluate(dict(version='v',code_sha256='s'),self.p,self.p['validation'],'TRAIN_VALIDATION',None,None))
        self.assertIsNone(M.select_validation([x])['selected'])
        x['validation_evaluation']['metrics']['repairs']=1;self.assertEqual(M.select_validation([x])['permission'],'SHADOW')
    def test_19_historical_hashes(self):P.verify_history(self.p['historical_sha256'])
    def test_24_registry_trusted_receipts_only_and_shadow(self):
        with tempfile.TemporaryDirectory(dir=D.ROOT/'runs') as d:
            out=Path(d);(out/'fixture.py').write_text(DECLINE)
            registry=P.FailureOperatorRegistry(out/'registry.jsonl',P.FailureEvidenceStore(out/'evidence.jsonl'))
            row=dict(id='fixture',version=P.fingerprint(DECLINE),path=str(out/'fixture.py'),code_sha256=P.sha(out/'fixture.py'),cell='S11')
            card=R.register(row,self.p,out,registry)
            self.assertEqual(registry.state(card)['permission'],'shadow')
            events=registry.evidence.visible(1);self.assertEqual(len(events),11)
            self.assertEqual(Counter(e['family_id'] for e in events),{'NATURAL_AGENT_FAILURE':6,'CONTROLLED_INTERVENTION':5})
            before=P.sha(out/'evidence.jsonl');R.register(row,self.p,out,registry);self.assertEqual(before,P.sha(out/'evidence.jsonl'))


class SchedulerTests(unittest.TestCase):
    def test_20_all_abstain_early_stop_no_execution(self):
        calls=[]
        def sender(w):calls.append(w);return response(dict(decision='ABSTAIN',reason='MOCK_ONLY'),len(calls))
        with tempfile.TemporaryDirectory(dir=D.ROOT/'runs') as d:
            out=Path(d)/'run';r=R.run_mock(PRE,out,sender=sender,evaluate=lambda *a:self.fail('unexpected evaluation'))
            self.assertEqual(len(calls),12);self.assertEqual(r['status'],'MOCK_EARLY_STOP_ALL_ABSTAIN')
            hashes={str(f):P.sha(f) for f in out.rglob('*.jsonl')}
            self.assertEqual(R.run_mock(PRE,out,sender=lambda w:self.fail('resent'),evaluate=lambda *a:self.fail('executed')),r)
            self.assertEqual(hashes,{str(f):P.sha(f) for f in out.rglob('*.jsonl')})
    def test_21_full_fifty_four_stages_feedback_recovery(self):
        calls=[];executions=[]
        def sender(w):
            phase=next(k for k,v in M.PROMPTS.items() if v==w['messages'][0]['content']);calls.append(phase)
            payload=decode(json.loads(w['messages'][1]['content']))
            if phase=='engineering':self.assertEqual(set(payload),{'parent_version','previous_source_or_delivery','engineering_diagnostics'})
            if phase=='behavior':
                self.assertIn(len(payload['own_execution_feedback']),(11,22))
                for s in payload['own_execution_feedback']:self.assertEqual(s['decisions'][0]['candidate_self_report']['reason'],'own:'+payload['parent_version'])
            return response(proposal(('import os\n' if phase=='initial' else '')+DECLINE+('\n# revised\n' if phase=='behavior' else '')),len(calls))
        def evaluator(row,p,cases,role,budget,out):
            self.assertTrue((out/'initials_engineering_complete.json').exists());executions.append((role,row['version']))
            if role=='TRAIN_VALIDATION':self.assertTrue((out/'all_learning_complete.json').exists());self.assertEqual(len(calls),54)
            return evaluate(row,p,cases,role,budget,out)
        with tempfile.TemporaryDirectory(dir=D.ROOT/'runs') as d:
            out=Path(d)/'run';once=[]
            def fault(*a):
                if not once:once.append(True);raise InterruptedError('settled response checkpoint')
            with self.assertRaises(InterruptedError):R.run_mock(PRE,out,sender=sender,evaluate=evaluator,fault=fault)
            self.assertEqual(len(calls),1)
            r=R.run_mock(PRE,out,sender=sender,evaluate=evaluator)
            self.assertEqual(Counter(calls),{'initial':24,'engineering':24,'behavior':6});self.assertEqual(len(executions),60)
            self.assertEqual(Counter(x['cell'] for x in r['lineages']),{c:4 for c in M.CELLS})
            self.assertTrue(all(v['selected'] is None for v in r['selection'].values()))
            R.run_mock(PRE,out,sender=lambda w:self.fail('resent'),evaluate=lambda *a:self.fail('rerun'))
    def test_22_unknown_budget_paid_block(self):
        with tempfile.TemporaryDirectory(dir=D.ROOT/'runs') as d:
            calls=[]
            def sender(w):calls.append(w);raise TimeoutError('MOCK_UNKNOWN')
            with self.assertRaises(TimeoutError):R.run_mock(PRE,Path(d)/'u',sender=sender,evaluate=evaluate)
            with self.assertRaises(RunUnhealthy):R.run_mock(PRE,Path(d)/'u',sender=sender,evaluate=evaluate)
            self.assertEqual(len(calls),1)
            with self.assertRaises(PermissionError):R.run_mock(PRE,Path(d)/'paid',sender=None,evaluate=evaluate)
            p=P.read(PRE/'protocol.json');budget=R.account(Path(d)/'b',dict(p,max_cost_microusd=0),'S11')
            with self.assertRaises(BudgetExhausted):budget.reserve(1,1)
    def test_23_foreign_role_evaluation_rejected(self):
        def sender(w):return response(proposal(DECLINE))
        def wrong(row,p,cases,role,b,out):
            ev=evaluate(row,p,cases,role,b,out);ev['role']='TEST';return ev
        with tempfile.TemporaryDirectory(dir=D.ROOT/'runs') as d:
            with self.assertRaises(PermissionError):R.run_mock(PRE,Path(d)/'run',sender=sender,evaluate=wrong)

if __name__=='__main__':unittest.main()
