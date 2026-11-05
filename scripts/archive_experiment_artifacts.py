"""Content-addressed local archive. Public receipt contains no private file inventory."""
import argparse,json,hashlib,tarfile,tempfile,os,subprocess,stat
from pathlib import Path

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def archive(root,storage):
 root=Path(root).resolve();storage=Path(storage).expanduser().resolve()
 if storage==root or root in storage.parents:raise ValueError('archive must be outside source tree')
 git=subprocess.run(['git','-C',str(root),'rev-parse','--show-toplevel'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
 if git.returncode==0:
  repository=Path(git.stdout.strip()).resolve()
  if storage==repository or repository in storage.parents:raise ValueError('archive must be outside the entire Git repository')
 storage.mkdir(parents=True,exist_ok=True);storage.chmod(0o700)
 files=sorted(p for p in root.rglob('*') if p.is_file())
 if any(p.is_symlink() for p in root.rglob('*')):raise ValueError('symlinks require independent review')
 records=[dict(path=str(p.relative_to(root)),sha256=digest(p),bytes=p.stat().st_size) for p in files]
 manifest=json.dumps(dict(version='controlled-artifact-archive-v1',files=records),sort_keys=True,separators=(',',':')).encode()
 manifest_sha=hashlib.sha256(manifest).hexdigest()
 with tempfile.TemporaryDirectory(dir=storage) as tmp:
  tarpath=Path(tmp)/'archive.tar.gz'
  with tarfile.open(tarpath,'w:gz') as tf:
   for p in files:tf.add(p,arcname=str(p.relative_to(root)),recursive=False)
  # Verify every archived member before touching Git tracking.
  with tarfile.open(tarpath,'r:gz') as tf:
   members={m.name:m for m in tf.getmembers()}
   if set(members)!={r['path'] for r in records}:raise ValueError('archive inventory mismatch')
   for r in records:
    if hashlib.sha256(tf.extractfile(members[r['path']]).read()).hexdigest()!=r['sha256']:raise ValueError('archive content mismatch')
  if sorted(p for p in root.rglob('*') if p.is_file())!=files:raise ValueError('source inventory changed during archive')
  for p,r in zip(files,records):
   if digest(p)!=r['sha256']:raise ValueError('source changed during archive')
  archive_sha=digest(tarpath);folder=storage/archive_sha;folder.mkdir(exist_ok=True);folder.chmod(0o700)
  dest=folder/'artifacts.tar.gz';mp=folder/'manifest.json'
  if dest.exists():
   if digest(dest)!=archive_sha:raise ValueError('existing archive drift')
  else:os.replace(tarpath,dest)
  if mp.exists():
   if mp.read_bytes()!=manifest:raise ValueError('existing manifest drift')
  else:mp.write_bytes(manifest)
  for p in (dest,mp):
   p.chmod(0o400)
   if hasattr(os,'chflags'):os.chflags(p,p.stat().st_flags | stat.UF_IMMUTABLE)
  return dict(version='controlled-artifact-archive-v1',archive_sha256=archive_sha,manifest_sha256=manifest_sha,
   files=len(records),uncompressed_bytes=sum(r['bytes'] for r in records),compressed_bytes=dest.stat().st_size,
   storage_class='LOCAL_OWNER_ONLY_CONTENT_ADDRESSED',read_only=True,
   filesystem_immutable=bool(getattr(dest.stat(),'st_flags',0)&getattr(stat,'UF_IMMUTABLE',0)),
   limitation='Owner can explicitly clear immutable flags; not a remote WORM or backup service')

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--storage',required=True);p.add_argument('--public-receipt',required=True);a=p.parse_args()
 receipt=archive(a.root,a.storage);Path(a.public_receipt).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
