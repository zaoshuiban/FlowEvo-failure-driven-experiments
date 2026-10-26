import pathlib,json,requests,concurrent.futures,hashlib
P=pathlib.Path(__file__).parent;D=pathlib.Path('/Users/majiatong/lab/AFlow/data/sources/s20_external_v2');S=D/'scorers';S.mkdir(exist_ok=True)
files={'cc':['README.md','contest_problem.proto','execution/tester_sandboxer.cc','execution/tester_sandboxer.h','execution/tester_sandboxer_test.cc','execution/py_tester_sandboxer.cc'], 'lcb':['README.md','lcb_runner/evaluation/testing_util.py','lcb_runner/evaluation/compute_code_generation_metrics.py','lcb_runner/runner/custom_evaluator.py'],'apps':['eval/testing_util.py','eval/test_one_solution.py','eval/README.md']}
receipts=[]
for k,names in files.items():
 meta=json.loads((P/(k+'_scorer_tree.json')).read_text())
 for name in names:
  u=f'https://raw.githubusercontent.com/{meta["repo"]}/{meta["revision"]}/{name}';r=requests.get(u,timeout=45);r.raise_for_status();f=S/(k+'_'+name.replace('/','_'));f.write_bytes(r.content);receipts.append(dict(dataset=k,url=u,path=str(f),sha256=hashlib.sha256(r.content).hexdigest()))
(P/'scorer_receipts.json').write_text(json.dumps(receipts,indent=2));print('SCORER_SOURCES_PINNED',flush=True)
files=[x for x in json.loads((P/'cc_tree.json').read_text()) if x['path'].endswith('parquet') and '/test-' not in x['path']]
def get(x):
 name=x['path'];u='https://huggingface.co/datasets/deepmind/code_contests/resolve/802411c3010cb00d1b05bad57ca77365a3c699d6/'+name;f=D/('cc_'+name.split('/')[-1]);tmp=f.with_suffix('.part')
 if not f.exists():
  with requests.get(u,stream=True,timeout=(20,90)) as r:
   r.raise_for_status()
   with tmp.open('wb') as out:
    for c in r.iter_content(1024*1024):out.write(c)
  assert tmp.stat().st_size==x['size'];tmp.replace(f)
 h=hashlib.sha256()
 with f.open('rb') as inp:
  for c in iter(lambda:inp.read(1024*1024),b''):h.update(c)
 (P/(f.name+'.receipt.json')).write_text(json.dumps(dict(dataset='cc',url=u,path=str(f),sha256=h.hexdigest(),bytes=f.stat().st_size),indent=2));print('CC_DOWNLOADED',f.name,flush=True)
with concurrent.futures.ThreadPoolExecutor(4) as ex:list(ex.map(get,files))
