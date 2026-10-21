"""Restore exact archived inputs; never expose hidden tests to generation providers."""
import pathlib,json,hashlib,tarfile,shutil
R=pathlib.Path(__file__).resolve().parents[1];D=R/'datasets'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
manifest=json.loads((D/'archive_parts.json').read_text());archive=D/'extracted/flowevo_800_tasks.tar.gz';archive.parent.mkdir(exist_ok=True)
with archive.open('wb') as out:
 for row in manifest['parts']:
  p=D/row['name'];assert sha(p)==row['sha256'],str(p)
  with p.open('rb') as f:shutil.copyfileobj(f,out)
assert sha(archive)==manifest['archive_sha256']
with tarfile.open(archive,'r:gz') as t:
 for member in t:
  p=pathlib.PurePosixPath(member.name)
  assert not p.is_absolute() and '..' not in p.parts and (member.isfile() or member.isdir()),member.name
  if member.isdir():continue
  target=archive.parent/p;target.parent.mkdir(parents=True,exist_ok=True)
  with t.extractfile(member) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
rows=json.loads((D/'task_manifest.json').read_text());assert len(rows)==800
for row in rows:assert sha(archive.parent/row['path'])==row['sha256'],row['path']
base=R/'experiments/flowevo_taco_lcb_20261019';full=archive.parent/'data/tasks'
for dest in [base/'audit/data/tasks',base/'e3_s1_20261020/source/tasks']:
 dest.mkdir(parents=True,exist_ok=True)
 names=list(json.loads((base/'e3_s1_20261020/source/task_hashes.json').read_text())) if 'source' in dest.parts else [p.name for p in full.glob('*.json')]
 for name in names:shutil.copy2(full/name,dest/name)
print('Verified and restored all 800 dataset tasks and historical relative paths.')
