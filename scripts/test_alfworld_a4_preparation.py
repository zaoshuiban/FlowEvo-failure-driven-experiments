import unittest, tempfile, copy
from pathlib import Path
import prepare_alfworld_a4_checkpoint_plan as P
class Preparation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=P.ROOT/'runs/alfworld_a4_preparation_20261115_01'
  cls.jobs=P.read(cls.root/'checkpoint_jobs.private.json');cls.roles=P.read(P.RUN/'roles.private.json')
 def test_01_frozen_identity(self):
  a=P.read(self.root/'Candidate_Freeze.json');self.assertEqual(a['selected']['selected']['candidate_id'],'candidate_0')
  for x in a['arms'].values():self.assertEqual(P.sha(x['original_path']),P.sha(x['snapshot']))
 def test_02_exact_order(self):
  old=P.read(P.OLD);self.assertEqual([j['task']['game_sha256'] for j in self.jobs],old['game_order']['strict_scene']+old['game_order']['expanded_game_group'])
 def test_03_no_fake_label(self):
  jobs=copy.deepcopy(self.jobs);jobs[0]['label']='MATCH'
  with self.assertRaises(ValueError):P.validate_jobs(jobs,self.roles)
 def test_04_no_overlap(self):
  roles=copy.deepcopy(self.roles);roles['TRAIN'][0]['game_sha256']=self.jobs[0]['task']['game_sha256']
  with self.assertRaises(ValueError):P.validate_jobs(self.jobs,roles)
 def test_05_no_duplicate(self):
  jobs=copy.deepcopy(self.jobs);jobs[1]=jobs[0]
  with self.assertRaises(ValueError):P.validate_jobs(jobs,self.roles)
 def test_06_no_release_or_execution(self):
  p=P.read(self.root/'A4_Preparation_Protocol.json');self.assertFalse(p['paid_api_authorized']);self.assertEqual(p['independent_games_executed'],0);self.assertEqual(p['retention_status'],'PENDING_NOT_WAIVED')
 def test_07_no_overwrite(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'x';P.commit(p,{'a':1});P.commit(p,{'a':1})
   with self.assertRaises(ValueError):P.commit(p,{'a':2})
 def test_08_replay(self):self.assertEqual(P.prepare(self.root),P.read(self.root/'Preparation_Audit.json'))
if __name__=='__main__':unittest.main()
