import pathlib,json,requests,hashlib,concurrent.futures,time
P=pathlib.Path(__file__).parent;D=pathlib.Path('/Users/majiatong/lab/AFlow/data/sources/s20_external_v2');D.mkdir(parents=True,exist_ok=True)
repos={'apps':('codeparrot/apps','21e74ddf8de1a21436da12e3e653065c5213e9d1'),'cc':('deepmind/code_contests','802411c3010cb00d1b05bad57ca77365a3c699d6'),'lcb':('livecodebench/code_generation_lite','0fe84c3912ea0c4d4a78037083943e8f0c4dd505')}
for key,(repo,rev) in repos.items():
 r=requests.get(f'https://huggingface.co/api/datasets/{repo}/tree/{rev}?recursive=true',timeout=45);r.raise_for_status();(P/(key+'_tree.json')).write_text(r.text)
# Fetch pinned evaluator sources without executing any repository code.
for key,repo in [('cc','google-deepmind/code_contests'),('lcb','LiveCodeBench/LiveCodeBench'),('apps','hendrycks/apps')]:
 r=requests.get(f'https://api.github.com/repos/{repo}/commits/HEAD',timeout=45);r.raise_for_status();rev=r.json()['sha'];r=requests.get(f'https://api.github.com/repos/{repo}/git/trees/{rev}?recursive=1',timeout=45);r.raise_for_status();(P/(key+'_scorer_tree.json')).write_text(json.dumps(dict(repo=repo,revision=rev,tree=r.json()),indent=2));print('scorer',key,rev,flush=True)
jobs=[('apps','train.jsonl')]+[('lcb',n) for n in ['test.jsonl','test2.jsonl','test3.jsonl','test4.jsonl','test5.jsonl']]
def download(job):
 key,name=job;repo,rev=repos[key];url=f'https://huggingface.co/datasets/{repo}/resolve/{rev}/{name}';dest=D/(key+'_'+name);tmp=dest.with_suffix(dest.suffix+'.part');h=hashlib.sha256();size=0
 if not dest.exists():
  with requests.get(url,stream=True,timeout=(20,90)) as r:
   r.raise_for_status()
   with tmp.open('wb') as out:
    for chunk in r.iter_content(1024*1024):out.write(chunk)
  tmp.replace(dest)
 with dest.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c);size+=len(c)
 row=dict(dataset=key,url=url,revision=rev,path=str(dest),sha256=h.hexdigest(),bytes=size);(P/(key+'_'+name+'.receipt.json')).write_text(json.dumps(row,indent=2));print('downloaded',key,name,size,flush=True)
with concurrent.futures.ThreadPoolExecutor(3) as ex:list(ex.map(download,jobs))
