"""Resume exact pinned byte ranges, validate official SHA before atomic publication."""
import pathlib,json,requests,hashlib,time,concurrent.futures,shutil,subprocess,sys
P=pathlib.Path(__file__).parent;D=pathlib.Path('/Users/majiatong/lab/AFlow/data/sources/s20_external_v2')
repos={'cc':('deepmind/code_contests','802411c3010cb00d1b05bad57ca77365a3c699d6'),'lcb':('livecodebench/code_generation_lite','0fe84c3912ea0c4d4a78037083943e8f0c4dd505')};files=[];jobs=[]
for ds,(repo,rev) in repos.items():
 for x in json.loads((P/(ds+'_tree.json')).read_text()):
  name=x['path'];base=name.split('/')[-1]
  if not (ds=='cc' and name.endswith('.parquet') and '/test-' not in name or ds=='lcb' and base in ['test.jsonl','test2.jsonl','test3.jsonl','test4.jsonl','test5.jsonl']):continue
  f=D/(ds+'_'+base)
  if f.exists():continue
  part=f.with_name(f.name+'.resume.part');start=part.stat().st_size if part.exists() else 0
  folder=D/'ranges'/f.name;folder.mkdir(parents=True,exist_ok=True);u=f'https://huggingface.co/datasets/{repo}/resolve/{rev}/{name}'
  chunks=[]
  for off in range(start,x['size'],32*1024*1024):
   end=min(x['size'],off+32*1024*1024)-1;chunk=folder/(str(off)+'-'+str(end));jobs.append((u,off,end,chunk));chunks.append(chunk)
  files.append((x,f,part,start,chunks))
def get(job):
 u,start,end,f=job
 for attempt in range(12):
  off=start+(f.stat().st_size if f.exists() else 0)
  if off==end+1:return
  try:
   with requests.get(u,headers={'Range':f'bytes={off}-{end}'},stream=True,timeout=(25,30)) as r:
    r.raise_for_status();assert r.status_code==206 and r.headers.get('Content-Range','').startswith(f'bytes {off}-'),r.headers.get('Content-Range')
    with f.open('ab') as out:
     for c in r.iter_content(1024*1024):out.write(c)
   assert f.stat().st_size==end-start+1;print('RANGE',f.parent.name,start,end,flush=True);return
  except Exception as exc:print('RETRY_RANGE',f.parent.name,start,attempt,type(exc).__name__,flush=True);time.sleep(min(5,attempt+1))
 raise RuntimeError('range download failed '+str(f))
print('RANGES',len(jobs),'files',len(files),flush=True)
with concurrent.futures.ThreadPoolExecutor(8) as ex:list(ex.map(get,jobs))
for x,f,part,start,chunks in files:
 tmp=f.with_name(f.name+'.assembled')
 with tmp.open('wb') as out:
  if start:
   assert part.stat().st_size==start
   with part.open('rb') as inp:shutil.copyfileobj(inp,out,1024*1024)
  for c in chunks:
   with c.open('rb') as inp:shutil.copyfileobj(inp,out,1024*1024)
 assert tmp.stat().st_size==x['size']
 h=hashlib.sha256()
 with tmp.open('rb') as inp:
  for b in iter(lambda:inp.read(1024*1024),b''):h.update(b)
 expected=x.get('lfs',{}).get('oid');assert expected and h.hexdigest()==expected
 tmp.replace(f);print('ASSEMBLED_VERIFIED',f.name,flush=True)
 # Only redundant download fragments created by this task are removed after verification.
 if part.exists():part.unlink()
 for c in chunks:c.unlink()
subprocess.run([sys.executable,str(P/'resume_downloads.py')],check=True)
