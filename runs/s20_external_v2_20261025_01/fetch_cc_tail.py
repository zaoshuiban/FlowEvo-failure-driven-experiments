# Independent tail shards; original worker processes ascending shards.
import pathlib,json,requests,concurrent.futures,hashlib
P=pathlib.Path(__file__).parent;D=pathlib.Path('/Users/majiatong/lab/AFlow/data/sources/s20_external_v2')
files=[x for x in json.loads((P/'cc_tree.json').read_text()) if x['path'].endswith('.parquet') and ('/valid-' in x['path'] or '/train-' in x['path'] and int(x['path'].split('train-')[1][:5])>=20)]
def get(x):
 name=x['path'];u='https://huggingface.co/datasets/deepmind/code_contests/resolve/802411c3010cb00d1b05bad57ca77365a3c699d6/'+name;f=D/('cc_'+name.split('/')[-1]);tmp=f.with_suffix('.tail.part')
 if not f.exists():
  with requests.get(u,stream=True,timeout=(20,120)) as r:
   r.raise_for_status()
   with tmp.open('wb') as out:
    for c in r.iter_content(1024*1024):out.write(c)
  assert tmp.stat().st_size==x['size'];tmp.replace(f)
 h=hashlib.sha256()
 with f.open('rb') as inp:
  for c in iter(lambda:inp.read(1024*1024),b''):h.update(c)
 (P/(f.name+'.receipt.json')).write_text(json.dumps(dict(dataset='cc',url=u,path=str(f),sha256=h.hexdigest(),bytes=f.stat().st_size),indent=2));print('DONE',f.name,flush=True)
with concurrent.futures.ThreadPoolExecutor(8) as ex:list(ex.map(get,reversed(files)))
