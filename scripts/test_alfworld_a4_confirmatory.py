import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import run_alfworld_a4_confirmatory as A
import collect_alfworld_a4_confirmatory as C
import resume_alfworld_a4_scoring as S

class Tests(unittest.TestCase):
    def test_zero_denominators_block(self):
        r=A.coverage([]);self.assertFalse(r['passed']);self.assertEqual(len(r['blockers']),3)
    def test_expanded_never_substitutes_strict(self):
        rows=[dict(stratum='expanded_game_group',label=l,label_status='EVIDENCE_REVIEWED',game_sha256=str(i),scene_id=i,physical_state_group_id=str(i)) for l in ['MATCH','DECLINE','UNKNOWN'] for i in range(10)]
        self.assertFalse(A.coverage(rows)['passed'])
    def test_repeated_windows_not_independent(self):
        rows=[dict(stratum='strict_scene',label=l,label_status='EVIDENCE_REVIEWED',game_sha256='one',scene_id=1,physical_state_group_id='one') for l in ['MATCH','DECLINE','UNKNOWN'] for _ in range(100)]
        r=A.coverage(rows);self.assertFalse(r['passed']);self.assertEqual(r['coverage']['strict_scene']['MATCH']['games'],1)
    def test_targets_met_all_labels(self):
        rows=[dict(stratum='strict_scene',label=l,label_status='EVIDENCE_REVIEWED',game_sha256=str(i),scene_id=i%2,physical_state_group_id=str(i)) for l in ['MATCH','DECLINE','UNKNOWN'] for i in range(4)]
        self.assertTrue(A.coverage(rows)['passed'])
    def test_unresolved_not_unknown(self):
        r=A.coverage([dict(stratum='strict_scene',label=None,label_status='UNRESOLVED_LABEL')]);self.assertEqual(r['coverage']['strict_scene']['UNKNOWN']['records'],0)
    def test_pending_blocks(self):
        with self.assertRaises(C.D.RunUnhealthy):C.check_pending([dict(kind='GAME_STARTED',payload={'id':'x'})])
        self.assertIn('x',C.check_pending([dict(kind=k,payload={'id':'x'}) for k in ['GAME_STARTED','GAME_COMPLETED']]))
    def test_commits_immutable(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';A.commit(p,{'x':1});A.commit(p,{'x':1})
            with self.assertRaises(PermissionError):A.commit(p,{'x':2})
    def test_exposure_does_not_require_successful_label(self):
        with tempfile.TemporaryDirectory() as d:
            top=Path(d);row=dict(game='x',game_sha256='a'*64,trajectory_sha256='b'*64,task_id='alf-'+'c'*20,scene=1,group='g')
            (top/'collection.jsonl').write_text(json.dumps(dict(kind='GAME_STARTED',payload={'id':row['task_id']}))+'\n')
            r=A.protection([row],[top],top/'new');self.assertEqual(len(r['eligible']),0)
    def test_reserved_is_not_available(self):
        with tempfile.TemporaryDirectory() as d:
            top=Path(d);row=dict(game='x',game_sha256='a'*64,trajectory_sha256='b'*64,task_id='alf-'+'c'*20,scene=1,group='g')
            (top/'selection.private.json').write_text(json.dumps({'tasks':[{'task':row}]}))
            self.assertFalse(A.protection([row],[top],top/'new')['eligible'])
    def test_eligible_inventory_not_falsely_exposed(self):
        with tempfile.TemporaryDirectory() as d:
            top=Path(d);row=dict(game='x',game_sha256='a'*64,trajectory_sha256='b'*64,task_id='alf-'+'c'*20,scene=1,group='g')
            (top/'inventory.private.json').write_text(json.dumps({'eligible':[row]}))
            self.assertEqual(len(A.protection([row],[top],top/'new')['eligible']),1)
    def score(self,actions,decisions,stop='DECLINED',decisive_error=True):
        origin={'initial':{},'steps':[]};prefix=[{'commands':[]}]
        with patch.object(S,'local_repair_witness',return_value=None),patch.object(S.PREVIOUS,'_decisive',side_effect=StopIteration if decisive_error else None,return_value={'action':'move x 1 to y 1'}):
            return S.score_source(origin,prefix,decisions,actions,stop)
    def test_missing_witness_refusal_not_math_failure(self):
        self.assertEqual(self.score([],[])['outcome'],'DECLINED')
    def test_state_change_is_not_repair(self):
        d=dict(score_or_win_progress=False,effect='TRUE',receipt={'commands':[]},selected_action='open x 1',public_state_changed=True)
        r=self.score([{'won':False}],[d],stop='WINDOW_EXHAUSTED');self.assertEqual(r['outcome'],'PROGRESS_UNVERIFIED');self.assertFalse(r['local_repair_verified'])
    def test_existing_decisive_no_progress(self):
        d=dict(score_or_win_progress=False,effect='TRUE',receipt={'commands':[]},selected_action='open x 1',public_state_changed=True)
        self.assertFalse(self.score([{'won':False}],[d],stop='WINDOW_EXHAUSTED',decisive_error=False)['local_repair_verified'])
    def test_unknown_win_never_promotes_label(self):
        sample={'label':'UNKNOWN'};d=dict(score_or_win_progress=True,effect='TRUE',receipt={'commands':[]},selected_action='move x 1 to y 1',public_state_changed=True)
        result=self.score([{'won':True}],[d],stop='WON');self.assertTrue(result['local_repair_verified']);self.assertEqual(sample['label'],'UNKNOWN');self.assertNotIn('label',result)
    def test_all_archived_live_scores_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            r=A.scoring_regression(Path(d));self.assertTrue(r['passed']);self.assertEqual(r['checked'],174)
    def test_all_four_candidates_intact(self):
        for x in A.read(A.PREP/'Candidate_Freeze.json')['arms'].values():self.assertEqual(A.sha(x['original_path']),x['sha256'])

if __name__=='__main__':unittest.main()
