"""A1c engineering fixtures are never inserted into real supervision."""
import copy
from pathlib import Path
import unittest
from alfworld_.route_a_expanded_labels import review, matched_views
from alfworld_.route_a_training_labels import model_projection
from alfworld_.recovery_applicability_learning import validate_rows
from failure_evo.math_stream import read
from failure_evo.math_stream import sha
from alfworld_.recovery_applicability_learning import load_dataset
from prepare_alfworld_route_a_expanded import choose, TYPES, extract_rows
from prepare_alfworld_route_a_expanded import verify

ROOT=Path(__file__).resolve().parents[1]


def branch():
    root=ROOT/'runs/alfworld_route_a_a1b_collection_20261113_01/branches'
    for path in sorted(root.glob('*.private.json')):
        b=read(path)
        if b.get('status')=='COLLECTED' and b['mode']=='READY' and b['recovery_probe'][-1]['won']:
            return copy.deepcopy(b)
    raise AssertionError('archived positive missing')


class ReviewTests(unittest.TestCase):
    def test_real_archived_positive(self):
        self.assertEqual(review(branch())['label'],'MATCH')

    def test_unexecuted_and_unreplayed_rejected(self):
        for field in ('replay_verified','execution_receipt_sha256'):
            b=branch();b[field]=None;self.assertIsNone(review(b)['label'])

    def test_not_held_is_not_easy_decline(self):
        b=branch()
        for s in b['prefix']:
            if s['action']=='inventory':s['observation']='You are carrying: a unrelated 9.'
        self.assertIsNone(review(b)['label'])

    def test_no_win_alone_not_negative(self):
        b=branch();b['recovery_probe'][-1]['won']=False
        self.assertIsNone(review(b)['label'])

    def test_target_conflict_requires_positive_witness(self):
        b=branch();b['original_goal']='put a soapbottle in fridge.'
        b['recovery_probe'][-1]['won']=False
        b['recovery_probe'][-1]['done']=False
        b['recovery_probe'][-1]['score']=b['failure']['score']
        b['recovery_probe'][-1]['observation']='Nothing happens.'
        b['recovery_probe'][0]['commands']=[c for c in b['recovery_probe'][0]['commands'] if c!=b['failure']['action']]
        self.assertIsNone(review(b)['label'])
        b['positive_witness']=dict(verified=True,same_subject=True,won=True)
        self.assertEqual(review(b)['label'],'DECLINE')

    def test_legal_intermediate_placement_is_not_false_applicability(self):
        b=branch();b['original_goal']='put a soapbottle in fridge.'
        b['recovery_probe'][-1]['won']=False
        b['positive_witness']=dict(verified=True,same_subject=True,won=True)
        self.assertIsNone(review(b)['label'])

    def test_phase_absence_stays_unresolved(self):
        b=branch();b['original_goal']='put a clean soapbottle in cabinet.'
        b['recovery_probe'][-1]['won']=False
        self.assertIsNone(review(b)['label'])

    def test_equal_length_different_labels_real_chronological_views(self):
        root=ROOT/'runs/alfworld_route_a_a1b_collection_20261113_01/branches'
        pairs=[]
        for path in sorted(root.glob('*.private.json')):
            b=read(path)
            if b.get('status')!='COLLECTED':continue
            label=review(b);views=matched_views(b,label)
            if {v['label'] for v in views}=={'MATCH','UNKNOWN'}:
                pairs.append(views)
                self.assertEqual(len(views[0]['candidate_context']['history']),len(views[1]['candidate_context']['history']))
                for v in views:
                    ids=v['public_history_scope']['retained_step_ids'];raw=b['prefix']+[b['failure']]
                    self.assertEqual(ids,sorted(set(ids)))
                    self.assertEqual(v['candidate_context']['history'],[dict(action=raw[i-1]['action'],observation=raw[i-1]['observation']) for i in ids])
        self.assertTrue(pairs)

    def test_projection_excludes_reference_and_metadata(self):
        b=branch();r=review(b)
        sample=dict(r,sample_id='private',candidate_context={'goal':b['original_goal'],'history':[]},public_history_scope={},recovery_probe='SECRET')
        p=model_projection(sample)
        self.assertNotIn('SECRET',str(p));self.assertNotIn('recovery_probe',p);self.assertNotIn('label_evidence',p)


class SelectionTests(unittest.TestCase):
    def test_deterministic_diversity_and_scene_isolation(self):
        rows=[dict(game=f'{scene}/{kind}/{i}',game_sha256=f'{scene}/{kind}/{i}',scene=scene,task_type=kind,
            group=f'{kind}-{i}-{target}-{scene}') for scene in range(30) for kind in TYPES
            for i,target in enumerate(('Cabinet','Drawer','Fridge','Microwave','Safe'))]
        a,p=choose(rows);b,q=choose(list(reversed(rows)))
        self.assertEqual(a,b);self.assertEqual(p,q);self.assertEqual(len(a),45)
        train={r['task']['scene'] for r in a if r['role']=='TRAIN'}
        val={r['task']['scene'] for r in a if r['role']=='TRAIN_VALIDATION'}
        self.assertFalse(train&val)

    def test_metadata_walker_handles_nested_roles(self):
        r=dict(game='x',game_sha256='g',trajectory_sha256='t',group='p')
        self.assertEqual(list(extract_rows({'a':{'rows':[{'task':r}]}})),[r])

    def test_cross_role_game_rejected(self):
        row=dict(label='MATCH',label_status='EVIDENCE_REVIEWED',sample_id='x',game_sha256='same',
            physical_state_group_id='physical',candidate_context=dict(goal='g',observation='o',admissible_commands=[],history=[]),label_evidence=[1])
        with self.assertRaises(PermissionError):validate_rows({'TRAIN':[dict(row,role='TRAIN')],'TRAIN_VALIDATION':[dict(row,role='TRAIN_VALIDATION')]})


class FrozenPoolTests(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/'runs/alfworld_route_a_a1c_20261113_01'
        if not self.root.exists():self.skipTest('local controlled run unavailable')

    def test_45_frozen_games_do_not_overlap_sealed_or_exposed(self):
        found=read(self.root/'inventory.private.json');tasks=read(self.root/'selection.private.json')['tasks']
        protected=found['protected']
        self.assertEqual(len(tasks),45)
        for r in tasks:
            t=r['task'];self.assertIn(t,found['eligible'])
            for key,items in (('game_sha256','games'),('trajectory_sha256','trajectories'),('group','groups'),('scene','scenes')):
                self.assertNotIn(t[key],protected[items])
        self.assertEqual(len({r['task']['group'] for r in tasks}),45)
        self.assertEqual(sum(r['role']=='TRAIN' for r in tasks),32)
        self.assertEqual(sum(r['role']=='TRAIN_VALIDATION' for r in tasks),13)

    def test_audit_amendment_cannot_restart_environment(self):
        if not (self.root/'audit_amendment.json').exists():self.skipTest('no audit-only amendment')
        verify(self.root,audit_only=True)
        with self.assertRaises(PermissionError):verify(self.root)


class CollectedDataTests(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/'runs/alfworld_route_a_a1c_20261113_01'
        if not (self.root/'dataset.json').exists():self.skipTest('real collection/audit not complete')
        self.roles=load_dataset(self.root)

    def test_real_hard_negatives_are_held_and_retried(self):
        negatives=[r for rows in self.roles.values() for r in rows if r['label']=='DECLINE']
        self.assertTrue(negatives)
        for r in negatives:
            game,mode=r['source_key'].split('/')
            b=next(b for b in read(self.root/'games'/f'{game}.private.json')['branches'] if b['mode']==mode)
            self.assertEqual(b['mode'],'TARGET_CONFLICT')
            self.assertNotIn(b['failure']['action'],b['recovery_probe'][0]['commands'])
            self.assertEqual(b['recovery_probe'][1]['observation'],'Nothing happens.')
            self.assertTrue(b['replay_verified'])

    def test_equal_length_pairs_in_both_roles(self):
        for rows in self.roles.values():
            pairs=[]
            for u in rows:
                if u['label']!='UNKNOWN':continue
                for m in rows:
                    if (m['label']=='MATCH' and m['physical_state_group_id']==u['physical_state_group_id']
                            and len(m['candidate_context']['history'])==len(u['candidate_context']['history'])):
                        for k in ('goal','observation','admissible_commands'):
                            self.assertEqual(m['candidate_context'][k],u['candidate_context'][k])
                        pairs.append((u,m))
            self.assertTrue(pairs)

    def test_public_projection_excludes_reference_probes(self):
        for rows in self.roles.values():
            for r in rows:
                p=model_projection(r)
                self.assertEqual(set(p['public_context']),{'goal','history','observation','admissible_commands'})
                for secret in ('HOST_ONLY','positive_witness','recovery_probe','private_review_note'):
                    self.assertNotIn(secret,str(p))
                self.assertFalse(any(k in p for k in ('scene_id','source_key','game_sha256')))

    def test_per_game_cap_and_scene_isolation(self):
        from collections import Counter
        for rows in self.roles.values():
            self.assertLessEqual(max(Counter(r['game_sha256'] for r in rows).values()),4)
        self.assertFalse({r['scene_id'] for r in self.roles['TRAIN']} & {r['scene_id'] for r in self.roles['TRAIN_VALIDATION']})

    def test_old_history_bytes_unchanged(self):
        for path,digest in read(self.root/'historical_before.private.json').items():self.assertEqual(sha(path),digest)

    def test_no_a3_authority_or_test_execution(self):
        d=read(self.root/'dataset.json');s=read(self.root/'collection_summary.json')
        self.assertFalse(d['A3_ready']);self.assertEqual(d['paid_requests'],0)
        self.assertEqual(s['independent_test_games'],0)


if __name__=='__main__':unittest.main()
