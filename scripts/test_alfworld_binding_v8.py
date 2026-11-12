import json
from pathlib import Path
import tempfile
import unittest
from alfworld_.binding_diagnostic import *
from run_alfworld_binding_v8 import dataset, run, plan_for, grant, create_accounts
from alfworld_.recovery_acquisition import RecoveryAdapter
from failure_evo.run_health import RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from test_alfworld_skill_acquisition import SOURCE,response
V7=SOURCE.parent/'alfworld_recovery_v7_pilot_20261110_01'

class BindingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.cases=dataset(SOURCE,V7)
    def output(self,c,arm):
        r=dict(c[arm],id=c['public']['id'])
        r.update(dict(confidence_basis='MOCK public annotation') if arm=='A' else dict(evidence_steps=['current'],uncertainty='MOCK public annotation'))
        return r
    def test_coverage(self):
        self.assertEqual(Counter(c['role'] for c in self.cases),{'source':4,'v7_regression':20,'fresh_synthetic':12})
        self.assertEqual(len({c['public']['id'] for c in self.cases}),36)
        self.assertEqual(Counter(c['category'] for c in self.cases if c['role']=='fresh_synthetic'),dict.fromkeys(['object_category','container_category','explicit_conflict','object_conflict','multiple_instances','insufficient'],2))
        for c in self.cases: self.assertEqual(set(c['public']),INPUT_FIELDS)
    def test_partial_accept_and_evidence_ids(self):
        cases=self.cases[:2]; rows=[self.output(c,'B') for c in cases]
        rows[0]['evidence_steps']=['step_999']
        r=parse_rows(dict(rows=rows),'B',[c['public'] for c in cases])
        self.assertEqual(len(r['rows']),1);self.assertEqual(len(r['rejected']),1)
    def test_conflict_and_unknown(self):
        cases={c['case_key']:c for c in self.cases}
        self.assertEqual(cases['fresh_explicit_conflict_0']['A']['target_match'],'CONFLICT')
        self.assertEqual(cases['fresh_multiple_instances_0']['A']['target_match'],'UNKNOWN')
        self.assertEqual(cases['fresh_insufficient_0']['B']['recovery_needed'],'UNKNOWN')
    def test_metrics(self):
        p={a:{c['public']['id']:self.output(c,a) for c in self.cases} for a in ('A','B')}
        p['B'][self.cases[0]['public']['id']]['recovery_needed']='NO'
        p['B'][next(c['public']['id'] for c in self.cases if c['case_key']=='fresh_explicit_conflict_0')]['recovery_needed']='YES'
        s=score(self.cases,p)['all']['B']['errors']
        self.assertEqual(s['false_reject']['numerator'],1);self.assertEqual(s['false_trigger']['numerator'],1)
        self.assertIsNone(score([],{'A':{},'B':{}})['all']['A']['delivery']['rate'])
    def test_interface_boundary(self):
        p=self.cases[0]['public']
        self.assertEqual(same_information_view(p,lambda x: {})['public_sha256'],fingerprint(p))
        with self.assertRaises(PermissionError): same_information_view(dict(p,answer='private'),lambda x: {})
    def test_real_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PermissionError): run(SOURCE,V7,Path(d))
    def test_unknown_blocks_without_resend(self):
        calls=[]
        def sender(wire):
            calls.append(wire)
            raise TimeoutError('MOCK unknown response')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(TimeoutError): run(SOURCE,V7,Path(d),sender=sender)
            before=(Path(d)/'budget.jsonl').read_bytes()
            with self.assertRaises(RunUnhealthy): run(SOURCE,V7,Path(d),sender=sender)
            self.assertEqual(len(calls),1)
            self.assertEqual(before,(Path(d)/'budget.jsonl').read_bytes())
    def test_authorized_preflight_no_send_and_budget(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); plan,cases=plan_for(SOURCE,V7,root)
            budget=create_accounts(root,plan)
            payload=dict(cases=[c['public'] for c in cases[:6]])
            adapter=RecoveryAdapter(root/'provider.jsonl',budget,model=plan['model'],
                stage='analyze',payload=payload,parser=lambda x:x,protocol=VERSION,
                authorization=grant(plan),analysis_prompt=PROMPTS['A'])
            request=dict(phase='induction',max_tokens=4096,discovery=dict(stage='analyze',payload_sha256=fingerprint(payload)))
            wire=adapter.preflight(request)
            self.assertEqual(json.loads(wire['messages'][1]['content']),payload)
            self.assertFalse((root/'provider.jsonl').exists())
            for _ in range(12): budget.reserve(1,1)
            with self.assertRaises(BudgetExhausted): budget.reserve(1,1)
    def test_schema_drift_and_duplicate(self):
        c=self.cases[0]; public=[c['public']]
        r=self.output(c,'A')
        self.assertFalse(parse_rows(dict(rows=[r,r]),'A',public)['rows'])
        r['execution_authorized']=True
        self.assertFalse(parse_rows(dict(rows=[r]),'A',public)['rows'])

    def test_mock_and_resume(self):
        lookup={c['public']['id']:c for c in self.cases}; calls=[]
        def sender(wire):
            arm='A' if wire['messages'][0]['content']==PROMPTS['A'] else 'B'
            public=json.loads(wire['messages'][1]['content'])['cases']
            for p in public: self.assertEqual(p,lookup[p['id']]['public'])
            calls.append(wire)
            return response(dict(rows=[self.output(lookup[p['id']],arm) for p in public]))
        with tempfile.TemporaryDirectory() as d:
            first=run(SOURCE,V7,Path(d),sender=sender)
            self.assertEqual(len(calls),12)
            self.assertEqual(len(first['predictions']['A']),36)
            before=(Path(d)/'budget.jsonl').read_bytes()
            self.assertEqual(run(SOURCE,V7,Path(d),sender=sender),first)
            self.assertEqual(len(calls),12); self.assertEqual(before,(Path(d)/'budget.jsonl').read_bytes())

if __name__=='__main__': unittest.main()
