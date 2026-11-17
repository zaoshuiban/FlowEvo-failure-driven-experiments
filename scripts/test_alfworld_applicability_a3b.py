"""A3b engineering tests: no model sender; no exposed/A4 data."""
import ast,json,os,unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import run_alfworld_applicability_a3b as S
from alfworld_.applicability_semantic_feedback import instrument,decode_trace,paired_feedback
from failure_evo.contracts import fingerprint,canonical
from failure_evo.math_stream import read
from test_alfworld_applicability_multicandidate import gate,propose
from test_alfworld_skill_acquisition import response

OLD=S.OLD
class Core(unittest.TestCase):
    def test_trace_nested_returns_and_collision(self):
        source="def applicability_gate(context):\n    def nested():\n        return 1\n    if nested()==1:\n        return {'status':'DECLINE','reason':'x'}\n"
        code,branches=instrument(source);self.assertEqual(set(branches),{'5'});self.assertEqual(code.count('_a3b_return_receipt('),2)
        self.assertTrue(S.B.static_check_detailed(S.B.worker_artifact(code))['passed'])
        with self.assertRaisesRegex(ValueError,'COLLISION'):instrument(source+'\ndef _a3b_return_receipt(x):\n    return x\n')
    def test_trace_never_claims_deepest_root(self):
        self.assertEqual(decode_trace({'status':'DECLINE','reason':'claimed goal conflict'}, {},{'actual':'DECLINE'})['status'],'UNDETERMINED')
    def test_paired_feedback_exact_parent_ids_and_isolation(self):
        a=read(OLD/'result.json')['attempts'][0];roles=read(OLD/'roles.private.json');pol=S.I.policy(384)
        r0,r1,binding=paired_feedback(a,roles['TRAIN'],pol,{})
        self.assertEqual(r0['own_train_feedback'],r1['own_train_feedback'])
        self.assertEqual(r0['previous_code'],a['code']);self.assertEqual(r1['parent_version'],a['version'])
        forbidden={fingerprint(r['sample_id']) for r in roles['TRAIN_VALIDATION']}
        self.assertFalse(forbidden&set(binding['sample_ids']))
        self.assertEqual([r['sample_id'] for r in r1['structured_counterexamples']],binding['sample_ids'])
        self.assertTrue(all(x['reached_code_branch']['status']=='UNDETERMINED' for x in r1['structured_counterexamples']))
        sid=binding['sample_ids'][0]
        with self.assertRaises(PermissionError):paired_feedback(a,roles['TRAIN'],pol,{sid:dict(candidate_version='sibling',split='TRAIN',sample_id=sid)})
        with self.assertRaises(PermissionError):paired_feedback(a,roles['TRAIN_VALIDATION'],pol,{})
    def test_complete_source_and_no_hidden_field_added(self):
        a=read(OLD/'result.json')['attempts'][0];r0,r1,b=paired_feedback(a,read(OLD/'roles.private.json')['TRAIN'],S.I.policy(384),{})
        for payload in (r0,r1):
            self.assertEqual(payload['previous_code'],a['code'])
            w=S.B.wire(Path('/private/tmp/a3b-wire'),payload,S.prompts()[1],.6,S.I.policy(384))
            self.assertEqual(w['temperature'],.6);self.assertEqual(w['thinking'],{'type':'disabled'})
        wrapper=S.B.worker_artifact(gate('UNKNOWN'))
        self.assertNotIn('public_history_scope',wrapper)
    def test_original_qualification_unchanged(self):
        old=read(OLD/'result.json');roles=read(OLD/'roles.private.json')
        self.assertEqual(S.B.learning.select(old['attempts'],roles)['status'],'NO_ELIGIBLE_CANDIDATE')
    def test_counterfactual_is_one_factor_not_runtime_helper(self):
        from diagnose_alfworld_a3b_counterfactual import copy_source
        a=read(OLD/'result.json')['attempts'][1];s=copy_source(a['code'],'grammar');tree=ast.parse(s)
        f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_goal_object')
        self.assertIsInstance(f.body[1],ast.If)
        self.assertIn('re.match',ast.unparse(f.body[2]))
        self.assertNotIn('_diagnostic_binding',S.prompts()[0])
    def test_metrics_pairing_and_zero_denominators(self):
        from alfworld_.applicability_paired_metrics import rows_metrics,comparison
        self.assertEqual(rows_metrics([])['correct_match']['status'],'NOT_EVALUABLE')
        r=dict(sample_id='s',game_sha256='g',physical_state_group_id='p',expected='MATCH',actual='DECLINE')
        v=comparison({'train':[r]},{'train':[dict(r,actual='MATCH')]},'train')
        self.assertEqual((v['changed'],v['corrected'],v['degraded'],v['improved_games']),(1,1,0,1))
        with self.assertRaises(PermissionError):comparison({'train':[r]},{'train':[dict(r,expected='UNKNOWN')]},'train')
    def test_frozen_limits_old_authorization_rejected(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)/'run';p=S.prepare(root,fixture_roles=small_roles());self.assertEqual(p['max_calls'],12)
            self.assertEqual(p['max_tokens'],4246528);self.assertFalse(read(root/'authorization.template.json')['paid_api_authorized'])
            with self.assertRaises(PermissionError):S.preflight(root,read(OLD/'authorization.json'),paid=True)
            packet=read(root/'learning.private.json');packet['tamper']=True;(root/'learning.private.json').write_text(canonical(packet))
            with self.assertRaisesRegex(PermissionError,'packet'):S.preflight(root)


def small_roles():
    roles=read(OLD/'roles.private.json')
    # Real previously exposed A1d records only; subset is explicitly engineering.
    return {k:[next(r for r in rows if r['label']==label) for label in ('MATCH','DECLINE','UNKNOWN')] for k,rows in roles.items()}

@unittest.skipUnless(os.environ.get('A3B_REAL_WORKER')=='1','explicit zero-API Docker/TextWorld')
class Runtime(unittest.TestCase):
    def test_twelve_branches_and_safe_resume(self):
        root=Path(os.environ['A3B_TEST_OUTPUT']);S.prepare(root,fixture_roles=small_roles());wires=[]
        def sender(w):
            wires.append(w);p=json.loads(w['messages'][1]['content']);branch=('R1' if 'structured_counterexamples' in p else 'R0') if 'parent_version' in p else 'initial'
            # One MATCH initial exercises real source replay; others test abstention/error/denial without artificial repair code.
            status='MATCH' if p['candidate_id']=='candidate_0' and branch=='initial' else 'DECLINE'
            return response(propose(gate(status,'# '+p['candidate_id']+' '+branch+'\n')))
        calls=[0]
        def crash(a):
            calls[0]+=1
            if calls[0]==1:raise RuntimeError('ENGINEERING_CHECKPOINT_INTERRUPT')
        with self.assertRaisesRegex(RuntimeError,'CHECKPOINT'):S.run(root,sender=sender,after_attempt=crash)
        result=S.run(root,sender=sender)
        self.assertEqual(len(wires),12);self.assertEqual(len(result['attempts']),12)
        self.assertEqual(result['paid_requests'],0);self.assertEqual(result['A4'],'NOT_RUN');self.assertEqual(result['exposed_regression'],'PROHIBITED_NOT_RUN')
        self.assertTrue(result['environment'])
        parents={a['candidate_id']:a for a in result['attempts'][:4]}
        for a in result['attempts'][4:]:
            self.assertEqual(a['parent_version'],parents[a['base_id']]['version'])
            self.assertEqual(a['parent_source_sha256'],parents[a['base_id']]['code_sha256'])
        for cid in parents:
            pair=read(root/cid/'paired_feedback.private.json');self.assertEqual(pair['R0']['own_train_feedback'],pair['R1']['own_train_feedback'])
            self.assertEqual(pair['R0']['previous_code'],pair['R1']['previous_code'])
        before=result['budget'];again=S.run(root,sender=lambda _:self.fail('duplicate request'));self.assertEqual(again['budget'],before)
        self.assertTrue(all(a['registration']['status']=='SHADOW' for a in result['attempts']))

if __name__=='__main__':unittest.main()
