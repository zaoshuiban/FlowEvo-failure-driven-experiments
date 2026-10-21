import concurrent.futures,hashlib,json,os,pathlib,requests,time
ROOT=pathlib.Path(__file__).resolve().parent
BASE='https://hf-mirror.com/datasets/livecodebench/code_generation_lite/resolve/0fe84c3912ea0c4d4a78037083943e8f0c4dd505/'
expected=json.loads((ROOT/'data/expected_sha256.json').read_text())
def fetch_file(i,size):
 name=f'lcb_test{i}.jsonl';dest=ROOT/'data/raw'/name
 if dest.exists():return
 folder=ROOT/'data/ranges'/name;folder.mkdir(parents=True,exist_ok=True)
 r=requests.get(BASE+f'test{i}.jsonl?parallel=1',headers={'Range':'bytes=0-0'},stream=True,timeout=(15,30));r.raise_for_status();url=r.url;r.close()
 chunk_size=2*1024*1024
 def chunk(start):
  end=min(start+chunk_size,size)-1;p=folder/str(start)
  if p.exists() and p.stat().st_size==end-start+1:return p
  for attempt in range(6):
   try:
    r=requests.get(url,headers={'Range':f'bytes={start}-{end}'},timeout=(15,20))
    r.raise_for_status();assert r.status_code==206 and len(r.content)==end-start+1
    assert r.headers['Content-Range'].startswith(f'bytes {start}-{end}/')
    p.write_bytes(r.content);print(name,start,'OK',flush=True);return p
   except Exception as e:
    print(name,start,'retry',attempt,type(e).__name__,flush=True);time.sleep(3*(attempt+1))
  raise RuntimeError('Chunk failed')
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:parts=list(pool.map(chunk,range(0,size,chunk_size)))
 assembled=folder/'complete';h=hashlib.sha256()
 with open(assembled,'wb') as f:
  for part in parts:
   data=part.read_bytes();h.update(data);f.write(data)
 assert h.hexdigest()==expected[name],name+' sha256 mismatch'
 try:os.link(assembled,dest)
 except FileExistsError:pass
 print('SHA256_VERIFIED',name,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 list(pool.map(lambda spec:fetch_file(*spec),[(5,557699297),(6,134303240)]))
print('REMAINING_FILES_READY',flush=True)
