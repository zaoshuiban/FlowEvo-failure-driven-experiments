import requests,pathlib,json,hashlib,concurrent.futures,time
P=pathlib.Path(__file__).parent;D=pathlib.Path('/Users/majiatong/lab/AFlow/data/sources/s20_external');D.mkdir(parents=True,exist_ok=True)
jobs=[]
for key,repo,names in [('apps','codeparrot/apps',['README.md','apps.py','test.jsonl']),('contests','deepmind/code_contests',['README.md','dataset_infos.json','data/test-00000-of-00001-9c49eeff30aacaa8.parquet']),('lcb','livecodebench/code_generation_lite',['README.md','code_generation_lite.py'])]:
 rev=json.loads((P/(key+'_source.json')).read_text())['sha']
 for name in names:jobs.append((key,repo,rev,name))
def get(j):
 k,repo,rev,name=j;u=f'https://huggingface.co/datasets/{repo}/resolve/{rev}/{name}';dest=D/(k+'_'+name.split('/')[-1]);h=hashlib.sha256();size=0
 with requests.get(u,stream=True,timeout=(20,60)) as r:
  r.raise_for_status()
  with dest.open('wb') as f:
   for chunk in r.iter_content(1024*1024):f.write(chunk);h.update(chunk);size+=len(chunk)
 print(k,name,size,flush=True);return dict(dataset=k,revision=rev,url=u,path=str(dest),sha256=h.hexdigest(),bytes=size)
with concurrent.futures.ThreadPoolExecutor(4) as ex:
 rows=[]
 for f in ex.map(get,jobs):rows.append(f);(P/'external_downloads.json').write_text(json.dumps(rows,indent=2))
