"""Resumable pinned data acquisition only; no model API."""
import pathlib,json,hashlib,requests,time,concurrent.futures,shutil
P=pathlib.Path(__file__).parent;D=pathlib.Path('/Users/majiatong/lab/AFlow/data/sources/s20_external_v2')
repos={'apps':('codeparrot/apps','21e74ddf8de1a21436da12e3e653065c5213e9d1'),'cc':('deepmind/code_contests','802411c3010cb00d1b05bad57ca77365a3c699d6'),'lcb':('livecodebench/code_generation_lite','0fe84c3912ea0c4d4a78037083943e8f0c4dd505')}
jobs=[]
for ds in repos:
 for x in json.loads((P/(ds+'_tree.json')).read_text()):
  name=x['path'];base=name.split('/')[-1]
  if ds=='apps' and base=='train.jsonl' or ds=='cc' and name.endswith('.parquet') and '/test-' not in name or ds=='lcb' and base in ['test.jsonl','test2.jsonl','test3.jsonl','test4.jsonl','test5.jsonl']:jobs.append((ds,x))
def get(job):
 ds,x=job;repo,rev=repos[ds];f=D/(ds+'_'+x['path'].split('/')[-1]);u=f'https://huggingface.co/datasets/{repo}/resolve/{rev}/{x["path"]}';tmp=f.with_name(f.name+'.resume.part')
 if not f.exists():
  parts=[z for z in [f.with_suffix('.part'),f.with_suffix('.tail.part'),f.with_suffix(f.suffix+'.part'),tmp] if z.exists()]
  if parts:
   best=max(parts,key=lambda p:p.stat().st_size)
   if best!=tmp:best.replace(tmp)
  for attempt in range(30):
   offset=tmp.stat().st_size if tmp.exists() else 0
   if offset==x['size']:break
   try:
    headers={'Range':f'bytes={offset}-'} if offset else {}
    with requests.get(u,headers=headers,stream=True,timeout=(30,45)) as r:
     r.raise_for_status()
     if offset and r.status_code==206:
      assert r.headers.get('Content-Range','').startswith('bytes '+str(offset)+'-');mode='ab'
     else:mode='wb'
     with tmp.open(mode) as out:
      for c in r.iter_content(1024*1024):out.write(c)
    if tmp.stat().st_size==x['size']:break
   except Exception as exc:print('RETRY',f.name,attempt,type(exc).__name__,flush=True);time.sleep(min(10,attempt+1))
  assert tmp.stat().st_size==x['size'],f
  tmp.replace(f)
 assert f.stat().st_size==x['size'],f
 h=hashlib.sha256()
 with f.open('rb') as inp:
  for c in iter(lambda:inp.read(1024*1024),b''):h.update(c)
 expected=x.get('lfs',{}).get('oid')
 if expected:assert h.hexdigest()==expected,(f,'SHA mismatch')
 (P/(f.name+'.receipt.json')).write_text(json.dumps(dict(dataset=ds,url=u,revision=rev,path=str(f),sha256=h.hexdigest(),bytes=f.stat().st_size,official_lfs_sha256=expected),indent=2));print('VERIFIED',f.name,flush=True)
with concurrent.futures.ThreadPoolExecutor(6) as ex:list(ex.map(get,jobs))
(P/'downloads_complete.json').write_text(json.dumps({'files':len(jobs),'status':'complete','model_requests':0}));print('DOWNLOADS COMPLETE',flush=True)
