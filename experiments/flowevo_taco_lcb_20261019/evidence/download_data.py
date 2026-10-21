import concurrent.futures, hashlib, json, os, pathlib, time, urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
RAW=ROOT/'data/raw'; RAW.mkdir(parents=True,exist_ok=True)
SPECS=[('BAAI/TACO','d593ed0a2becbbc952230bb89be09189bf1056dc','ALL/test-00000-of-00001.parquet','taco_test.parquet',245784461)]+[('livecodebench/code_generation_lite','0fe84c3912ea0c4d4a78037083943e8f0c4dd505',f'test{i if i>1 else ""}.jsonl',f'lcb_test{i}.jsonl',size) for i,size in enumerate([1252609773,713377060,623360766,1204644685,557699297,134303240],1)]
def download(spec):
 repo,rev,name,local,size=spec
 dest=RAW/local; part=dest.with_suffix(dest.suffix+'.part')
 if dest.exists() and dest.stat().st_size==size:return {'file':local,'size':size,'sha256':hashlib.file_digest(open(dest,'rb'),'sha256').hexdigest()} if hasattr(hashlib,'file_digest') else {'file':local,'size':size}
 for attempt in range(10):
  try:
   offset=part.stat().st_size if part.exists() else 0
   url=f'https://hf-mirror.com/datasets/{repo}/resolve/{rev}/{name}?download=true&attempt={attempt}'
   req=urllib.request.Request(url,headers={'Range':f'bytes={offset}-'} if offset else {})
   with urllib.request.urlopen(req,timeout=60) as resp:
    if offset and resp.status!=206: offset=0
    with open(part,'ab' if offset else 'wb') as f:
     while True:
      chunk=resp.read(4*1024*1024)
      if not chunk:break
      f.write(chunk)
   if part.stat().st_size!=size:raise ValueError(f'length mismatch {part.stat().st_size}/{size}')
   part.replace(dest)
   h=hashlib.sha256()
   with open(dest,'rb') as f:
    for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
   record={'repo':repo,'revision':rev,'filename':name,'local':local,'size':size,'sha256':h.hexdigest()}
   print(json.dumps(record),flush=True)
   return record
  except Exception as e:
   print(local,'retry',attempt,type(e).__name__,str(e)[:100],flush=True);time.sleep(min(5*(attempt+1),30))
 raise RuntimeError('download failed '+local)
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: records=list(pool.map(download,SPECS))
 (ROOT/'data/download_manifest.json').write_text(json.dumps(records,indent=2))
 print('DOWNLOADS_COMPLETE',flush=True)
