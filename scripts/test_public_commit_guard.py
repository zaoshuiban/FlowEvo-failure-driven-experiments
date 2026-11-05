"""Staged-index boundary tests, no model/API calls."""
import unittest,tempfile,subprocess,json,os
from pathlib import Path
from check_public_commit import inspect,staged
from archive_experiment_artifacts import archive,digest

class GuardTests(unittest.TestCase):
 def test_sensitive_paths(self):
  for name in ['runs/new/state.json','datasets/new/answers.json','reports/x/private/scores.jsonl','reports/x/reviewed_cases.private.json','reports/x/private_publication.jsonl','.env.local','keys/server.pem','reports/x/attempt01/compiler.jsonl','private-backup.tar.gz']:
   self.assertTrue(inspect(name,b'{}'),name)
 def test_public_summaries_and_source(self):
  for name in ['FlowEvo/src/failure_evo/operator_contract.py','scripts/test_mock.py','reports/x/summary.md','reports/x/source_manifest.json','reports/x/validation_matrix.json']:
   self.assertEqual(inspect(name,b'{}'),[],name)
 def test_answer_material_in_public_filename_blocked(self):
  self.assertIn('PRIVATE_ANSWER_FIELD',inspect('reports/x/source_manifest.json',json.dumps({'gold_answer':'do-not-publish'}).encode()))
 def test_credential_in_source_blocked(self):
  key=('sk-'+'A'*40).encode()
  self.assertIn('PROVIDER_KEY',inspect('scripts/example.py',key))
 def test_no_field_name_false_positive(self):
  self.assertEqual(inspect('scripts/config.py',b'key = os.environ.get("OPENAI_API_KEY")'),[])
 def test_index_not_worktree(self):
  with tempfile.TemporaryDirectory() as d:
   def git(*a):return subprocess.run(['git',*a],cwd=d,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   git('init');p=Path(d)/'safe.py';p.write_text('print(1)');git('add','safe.py')
   p.write_text('sk-'+'A'*40);self.assertEqual(staged(d),[])
   git('add','safe.py');p.write_text('print(1)');self.assertTrue(staged(d))
 def test_commit_content_checked_without_staged_diff(self):
  with tempfile.TemporaryDirectory() as d:
   subprocess.run(['git','init'],cwd=d,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   (Path(d)/'.env.local').write_text('FIXTURE_ONLY=1')
   subprocess.run(['git','add','-f','.env.local'],cwd=d,check=True)
   subprocess.run(['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','--quiet','-m','fixture'],cwd=d,check=True)
   self.assertEqual(staged(d),[])
   self.assertTrue(staged(d,'HEAD'))
 def test_archive_inventory_drift_rejected(self):
  import tarfile
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'source';root.mkdir();(root/'first.txt').write_text('fixture')
   original=tarfile.TarFile.add
   def changing(tf,*args,**kwargs):
    result=original(tf,*args,**kwargs);(root/'new.txt').write_text('new');return result
   with patch.object(tarfile.TarFile,'add',changing):
    with self.assertRaises(ValueError):archive(root,Path(d)/'vault')
 def test_forced_add_cannot_bypass_path_guard(self):
  with tempfile.TemporaryDirectory() as d:
   subprocess.run(['git','init'],cwd=d,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   p=Path(d)/'.env';p.write_text('NOT_A_REAL_SECRET=1')
   subprocess.run(['git','add','-f','.env'],cwd=d,check=True)
   self.assertTrue(staged(d))
 def test_archive_checksums_outside_tree(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'source';root.mkdir();(root/'record.json').write_text('{"fixture":true}')
   storage=Path(d)/'vault'
   receipt=archive(root,storage)
   dest=storage/receipt['archive_sha256']/'artifacts.tar.gz'
   self.assertEqual(digest(dest),receipt['archive_sha256']);self.assertEqual(receipt['files'],1)
   # Clear only the newly created test fixture flags for TemporaryDirectory cleanup.
   if hasattr(os,'chflags'):
    for p in dest.parent.iterdir():os.chflags(p,0)
 def test_archive_elsewhere_in_repository_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   repo=Path(d)/'repo';repo.mkdir();subprocess.run(['git','init'],cwd=repo,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   source=repo/'runs'/'fixture';source.mkdir(parents=True)
   with self.assertRaises(ValueError):archive(source,repo/'archive')
 def test_archive_inside_source_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):archive(d,Path(d)/'vault')
 def test_symlink_archive_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'source';root.mkdir();(root/'link').symlink_to('/dev/null')
   with self.assertRaises(ValueError):archive(root,Path(d)/'vault')
if __name__=='__main__':unittest.main()
