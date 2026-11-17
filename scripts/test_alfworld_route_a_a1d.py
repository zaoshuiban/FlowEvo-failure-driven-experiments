"""A1d data and A3 input tests; synthetic candidates are ENGINEERING ONLY."""
from copy import deepcopy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from alfworld_ import recovery_applicability_learning as L
from alfworld_ import recovery_learning_input as I
from alfworld_.route_a_training_labels import model_projection
from alfworld_.route_a_expanded_labels import review
from alfworld_.recovery_acquisition import stage_request
from alfworld_.python_recovery_feedback import parse_delivery
from alfworld_.failure_learning import static_check_detailed
from failure_evo.contracts import canonical,fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read,sha
from failure_evo.runtime import BudgetExhausted
from failure_evo.run_health import RunUnhealthy
from failure_evo.wire_input_policy import check_wire,validate_wire_input_policy
from run_alfworld_skill_acquisition import create_accounts
import run_alfworld_applicability_multicandidate as study
from test_alfworld_applicability_multicandidate import fixtures,sender_for
from test_alfworld_skill_acquisition import response
DATA=study.ROOT/'runs/alfworld_route_a_a1d_20261113_01'


def feedback_fixture(rows,code='def applicability_gate(context):\n    return {"status":"MATCH","reason":"MOCK"}\n'):
    a=dict(candidate_id='fixture',version='v',code=code,code_sha256=fingerprint(code),delivery={'status':'PROPOSE'},static={'passed':True},train=[])
    for r in rows:
        a['train'].append(dict(candidate_id='fixture',version='v',role='TRAIN',sample_id=fingerprint(r['sample_id']),
            actual='MATCH',reason='MOCK self-report',expected=r['label'],classification=L.classify(r['label'],'MATCH'),
            execution_id='mock',worker_status='OK',context_sha256=fingerprint(r['candidate_context']),
            live={'actions':[]},recovery_verified=True if r['label']=='MATCH' else None))
    return a


class DataTests(unittest.TestCase):
    def setUp(self):self.roles=L.load_dataset(DATA)
    def test_new_negative_minimum_real_receipts(self):
        rows=[r for r in self.roles['TRAIN_VALIDATION'] if r['label']=='DECLINE']
        self.assertGreaterEqual(len({r['game_sha256'] for r in rows}),3)
        self.assertGreaterEqual(len({r['scene_id'] for r in rows}),2)
        for r in rows:
            game,mode=r['source_key'].split('/');branches=read(DATA/'games'/(game+'.private.json'))['branches']
            b=deepcopy(next(b for b in branches if b['mode']==mode))
            from alfworld_.precondition_diagnostic import command
            positives=[p for p in branches if p['status']=='COLLECTED' and review(p)['label']=='MATCH'
                       and command(p['failure']['action'])[1][0]==command(b['failure']['action'])[1][0]]
            self.assertTrue(positives)
            b['positive_witness']=dict(verified=bool(positives),same_subject=bool(positives),won=bool(positives))
            self.assertEqual(review(b)['label'],'DECLINE');self.assertTrue(b['replay_verified'])
            self.assertEqual(b['failure']['observation'],'Nothing happens.')
            self.assertEqual(b['recovery_probe'][1]['observation'],'Nothing happens.')
            self.assertTrue(b['positive_witness']['won'])
            bad=deepcopy(b);bad['positive_witness']={};self.assertIsNone(review(bad)['label'])
            bad=deepcopy(b);bad['recovery_probe'][0]['observation']='Nothing happens.';self.assertIsNone(review(bad)['label'])
    def test_train_unchanged_and_roles_scenes_isolated(self):
        old=L.load_dataset(study.ROOT/'runs/alfworld_route_a_a1c_20261113_01')['TRAIN']
        self.assertEqual([{k:v for k,v in r.items() if k!='source_dataset'} for r in self.roles['TRAIN']],old)
        for key in ('game_sha256','physical_state_group_id','scene_id'):
            self.assertFalse({r[key] for r in self.roles['TRAIN']}&{r[key] for r in self.roles['TRAIN_VALIDATION']})
    def test_protected_pool_not_used(self):
        inv=read(DATA/'inventory.private.json');selected=read(DATA/'selection.private.json')['tasks']
        for row in selected:
            t=row['task'];self.assertIn(t,inv['validation_eligible']);self.assertEqual(row['role'],'TRAIN_VALIDATION')
            for key,items in (('game_sha256','games'),('trajectory_sha256','trajectories'),('group','groups'),('scene','scenes')):
                self.assertNotIn(t[key],inv['protected'][items])
    def test_all_source_mappings_exact(self):
        for rows in self.roles.values():
            for row in rows:study.source_origin(row,{'dataset':str(DATA)})
        bad=deepcopy(self.roles['TRAIN'][0]);bad['candidate_context']['goal']='tampered'
        with self.assertRaises(PermissionError):study.source_origin(bad,{'dataset':str(DATA)})
    def test_unknown_and_unresolved_are_distinct(self):
        self.assertTrue(read(DATA/'new_review.private.json')['unresolved'])
        for rows in self.roles.values():
            for r in rows:self.assertEqual(r['label_status'],'EVIDENCE_REVIEWED')
        pairs=[(u,m) for rows in self.roles.values() for u in rows if u['label']=='UNKNOWN'
               for m in rows if m['label']=='MATCH' and u['physical_state_group_id']==m['physical_state_group_id']
               and len(u['candidate_context']['history'])==len(m['candidate_context']['history'])]
        self.assertGreaterEqual(len(pairs),18)
    def test_historical_artifacts_unchanged(self):
        for p,h in read(DATA/'historical_artifacts.private.json').items():self.assertEqual(sha(p),h,p)
    def test_closed_collection_original_sources_retained(self):
        plan=read(DATA/'protocol.json')
        for p,h in plan['source_sha256'].items():
            f=DATA/'collection_source'/Path(p).name
            self.assertEqual(sha(f),h)
    def test_new_runtime_cannot_restart_old_frozen_collection(self):
        from prepare_alfworld_route_a_a1d import verify
        with self.assertRaisesRegex(PermissionError,'frozen file changed'):verify(DATA)
        from prepare_alfworld_route_a_training_checkpoints import verify as old_verify
        with self.assertRaisesRegex(PermissionError,'frozen file changed'):old_verify(study.DATA)
        from prepare_alfworld_route_a_expanded import verify as expanded_verify
        with self.assertRaisesRegex(PermissionError,'frozen source/manifest drift'):
            expanded_verify(study.ROOT/'runs/alfworld_route_a_a1c_20261113_01',audit_only=True)


class InputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=L.load_dataset(DATA)['TRAIN'];cls.code=study.CODE.read_text()
    def test_full_and_stratified_coverage_and_wire(self):
        for k in (None,64,128,256):
            o=I.organize(self.rows,self.code,k);self.assertEqual(o,I.organize(self.rows,self.code,k))
            c=o['coverage'];self.assertEqual(set(c['labels']),{'MATCH','DECLINE','UNKNOWN'});self.assertEqual(len(c['task_types']),4)
            self.assertEqual(c['samples'],len(set(o['selected_ids'])))
            with TemporaryDirectory() as d:
                payload=dict(candidate_id='candidate_0',training_input=o['packet'])
                w=study.wire(Path(d),payload,L.INITIAL_PROMPT,0.6,I.policy(k or 256))
                self.assertEqual(w,I.wire(payload,L.INITIAL_PROMPT));self.assertEqual(len(canonical(w).encode()),o['measurement']['wire_bytes'])
                self.assertIsNone(o['measurement']['provider_input_tokens'])
            for r in o['packet']['training']:
                self.assertIn(r,[model_projection(row) for row in self.rows])
            self.assertNotIn('recovery_probe',canonical(o['packet']))
    def test_old_default_and_new_bound_and_source_safety(self):
        payload={'evidence':'x'*70000}
        with TemporaryDirectory() as d:
            with self.assertRaises(ValueError):study.wire(Path(d),payload,'prompt',0.6)
            study.wire(Path(d),payload,'prompt',0.6,I.policy(128))
            with self.assertRaises(ValueError):study.wire(Path(d),{'evidence':'x'*262144},'prompt',0.6,I.policy(256))
        p=I.policy(256);p['model_context_tokens']=1000
        with self.assertRaises(ValueError):validate_wire_input_policy(p,'deepseek-flash')
        self.assertFalse(static_check_detailed('def environment_operator(context):\n    return {}\n#'+'a'*65536)['passed'])
    def test_full_previous_code_and_training_only_feedback(self):
        a=feedback_fixture(self.rows,code='#'+'x'*65500)
        p=I.revision(a,self.rows,I.policy(384))
        self.assertEqual(p['previous_code'],a['code']);self.assertEqual(p['parent_version'],'v')
        self.assertTrue(p['omitted_feedback']);self.assertLessEqual(I.measure(p,L.REVISION_PROMPT)['wire_bytes'],384*1024)
        val={fingerprint(r['sample_id']) for r in L.load_dataset(DATA)['TRAIN_VALIDATION']}
        self.assertFalse(any(i in canonical(p) for i in val));self.assertNotIn('recovery_probe',canonical(p))
        a['train'][0]['candidate_id']='other'
        with self.assertRaises(PermissionError):I.revision(a,self.rows,I.policy(384))
    def test_failed_recovery_not_dropped_as_correct_control(self):
        a=feedback_fixture(self.rows)
        for x in a['train']:
            if x['expected']=='MATCH':x['recovery_verified']=False
        p=I.revision(a,self.rows,I.policy(384))
        self.assertEqual(sum(x['execution']['recovery_verified'] is False for x in p['own_train_feedback']),47)
    def test_large_wire_budget_binding_and_settled_replay(self):
        with TemporaryDirectory() as d:
            root=Path(d);p=I.policy(256);payload={'text':'x'*70000};calls=[]
            b=create_accounts(root,dict(run_id='mock:a1d',max_calls=1,max_tokens=p['max_input_tokens']+4096,max_cost_microusd=400000,worker_calls=0))
            def sender(w):calls.append(w);return response({'decision':'ABSTAIN','reason':'MOCK'})
            a=stage_request(root,'j','analyze',payload,parse_delivery,b,sender=sender,input_policy=p)
            snap=b.snapshot();z=stage_request(root,'j','analyze',payload,parse_delivery,b,sender=sender,input_policy=p)
            self.assertEqual(a,z);self.assertEqual(len(calls),1);self.assertEqual(b.snapshot(),snap)
            with self.assertRaises(BudgetExhausted):stage_request(root,'new','analyze',payload,parse_delivery,b,sender=sender,input_policy=p)
            self.assertEqual(len(calls),1)
            rows=EvidenceStore(root/'j/compiler.jsonl').records();self.assertTrue(any('WIRE' in r['kind'] for r in rows))
    def test_new_policy_send_unknown_still_blocks(self):
        with TemporaryDirectory() as d:
            root=Path(d);calls=[];p=I.policy(256)
            b=create_accounts(root,dict(run_id='mock:a1d-unknown',max_calls=8,max_tokens=3000000,max_cost_microusd=3500000,worker_calls=0))
            def sender(w):calls.append(w);raise TimeoutError('MOCK SEND UNKNOWN')
            with self.assertRaises(Exception):stage_request(root,'first','analyze',{'text':'x'*70000},parse_delivery,b,sender=sender,input_policy=p)
            before=b.snapshot()
            with self.assertRaises(RunUnhealthy):stage_request(root,'second','analyze',{},parse_delivery,b,sender=sender,input_policy=p)
            self.assertEqual(len(calls),1);self.assertEqual(b.snapshot(),before);self.assertTrue(before['unknown_or_pending_requests'])
    def test_a3_template_has_no_paid_authority(self):
        p=study.ROOT/'runs/alfworld_route_a_a3_preparation_20261113_01'
        if not p.exists():self.skipTest('A3 preparation not frozen')
        template=read(p/'authorization.template.json')
        self.assertFalse(template['paid_api_authorized']);study.preflight(p)
        with self.assertRaisesRegex(PermissionError,'PENDING_EXPLICIT_AUTHORIZATION'):
            study.preflight(p,paid=True,authorization=template)


class RetainedChainTests(unittest.TestCase):
    def test_partial_public_history_and_full_physical_replay(self):
        p=DATA/'zero_api_chain_03';result=read(p/'result.json');roles=read(p/'roles.private.json')
        rows={fingerprint(r['sample_id']):r for rs in roles.values() for r in rs}
        partial=next((i,r) for i,r in rows.items() if r['label']=='MATCH' and r['public_history_scope'].get('retained_step_ids'))
        event_rows=EvidenceStore(p/'environment.jsonl').records();seen=[]
        for a in result['attempts']:
            for x in a.get('train',[]):
                if x['sample_id']!=partial[0] or not x['live'].get('actions'):continue
                _,origin,ids=study.source_origin(partial[1],read(p/'protocol.json'))
                branch=x['live']['evaluation_branch']
                prefixes=[e for e in event_rows if e['kind']=='STEP_STARTED' and e['payload']['branch']==branch and e['payload']['scope']=='prefix']
                self.assertEqual(len(prefixes),origin['projected']['anchor']);self.assertLess(len(ids),len(prefixes))
                self.assertTrue(x['recovery_verified']);seen.append(branch)
        self.assertEqual(len(set(seen)),3)


@unittest.skipUnless(os.getenv('ALFWORLD_A1D_REAL_ACCEPTANCE')=='1','explicit Linux/TextWorld zero-API test')
class RealChainTests(unittest.TestCase):
    def test_four_candidate_chain_new_and_partial_checkpoints(self):
        root=Path(os.environ['ALFWORLD_A1D_OUTPUT']);roles=L.load_dataset(DATA)
        subset={}
        for role,rows in roles.items():
            subset[role]=[next(r for r in rows if r['label']==label) for label in ('MATCH','DECLINE','UNKNOWN')]
        partial=next(r for r in roles['TRAIN'] if r['label']=='MATCH' and r['public_history_scope'].get('retained_step_ids'))
        if partial not in subset['TRAIN']:subset['TRAIN'].append(partial)
        new=next(r for r in roles['TRAIN_VALIDATION'] if r['label']=='MATCH' and r['source_dataset']==str(DATA))
        if new not in subset['TRAIN_VALIDATION']:subset['TRAIN_VALIDATION'].append(new)
        plan=(read(root/'protocol.json') if (root/'protocol.json').exists() else
              study.prepare(root,dataset=DATA,fixture_roles=subset,input_policy=I.policy(256),revision_policy=I.policy(384)))
        with self.assertRaises(PermissionError):study.preflight(root,paid=True,authorization={'paid_api_authorized':False})
        wires=[];result=study.run(root,sender=sender_for(fixtures(),wires))
        sends=[r for r in EvidenceStore(root/'provider.jsonl').records() if r['kind']=='SEND_STARTED']
        self.assertEqual(len(sends),8)
        self.assertEqual(result['paid_requests'],0);self.assertEqual(result['selection']['status'],'SELECTED_PENDING_REGRESSION')
        self.assertEqual(result['selection']['engineering_status'],'ENGINEERING_SELECTION_VALID')
        self.assertIsNone(result['selection']['research_winner'])
        self.assertTrue(all(a['registration']['status']=='SHADOW' for a in result['attempts'] if 'registration' in a))
        executions=[r for a in result['attempts'] for r in a.get('train',[])+a.get('validation',[]) if r.get('live',{}).get('actions')]
        self.assertGreaterEqual(len(executions),3);self.assertTrue(any(r['recovery_verified'] for r in executions))
        for a in result['attempts']:
            if a['revision']:
                parent=next(p for p in result['attempts'] if p['version']==a['parent_version'])
                payload=read(root/a['candidate_id']/'v1/request.private.json')['payload'];self.assertEqual(payload['previous_code'],parent['code'])
        before={str(p):sha(p) for p in root.rglob('*.jsonl')}
        self.assertEqual(study.run(root,sender=lambda _:self.fail('repeated request')),result)
        self.assertEqual(before,{str(p):sha(p) for p in root.rglob('*.jsonl')})

if __name__=='__main__':unittest.main()
