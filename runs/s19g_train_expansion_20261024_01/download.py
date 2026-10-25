import pathlib,requests,hashlib,json,time
P=pathlib.Path(__file__).parent; cache=pathlib.Path('/Users/majiatong/lab/AFlow/data/sources/taco_d593ed0a_train');cache.mkdir(parents=True,exist_ok=True)
a=next(x for x in json.loads((P/'official_source_tree.json').read_text()) if x['path']=='ALL/train-00000-of-00009.parquet');dest=cache/pathlib.Path(a['path']).name
url='https://huggingface.co/datasets/BAAI/TACO/resolve/d593ed0a2becbbc952230bb89be09189bf1056dc/'+a['path']
if not dest.exists():
 with requests.get(url,stream=True,timeout=(20,90)) as r:
  r.raise_for_status()
  with dest.with_suffix('.partial').open('wb') as f:
   for chunk in r.iter_content(1024*1024):f.write(chunk)
 dest.with_suffix('.partial').replace(dest)
assert dest.stat().st_size==a['size'];h=hashlib.sha256(dest.read_bytes()).hexdigest();expected=a.get('lfs',{}).get('oid');assert not expected or expected==h
(P/'download_ledger.json').write_text(json.dumps({'url':url,'path':str(dest),'bytes':dest.stat().st_size,'sha256':h,'official_lfs_sha256':expected,'time':time.time(),'model_requests':0},indent=2));print(h,flush=True)
