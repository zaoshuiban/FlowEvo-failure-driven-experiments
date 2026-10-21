import argparse, base64, collections, hashlib, io, json, pathlib, pickle, re, time, zlib
ROOT=pathlib.Path(__file__).resolve().parent
SEED=20261019
REV={'taco':'d593ed0a2becbbc952230bb89be09189bf1056dc','lcb':'0fe84c3912ea0c4d4a78037083943e8f0c4dd505'}
LEVELS={'taco':['EASY','MEDIUM','MEDIUM_HARD','HARD','VERY_HARD'],'lcb':['easy','medium','hard']}
def wait_file(p):
 while not p.exists():time.sleep(5)
 expected=json.loads((ROOT/"data/expected_sha256.json").read_text())[p.name]
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for block in iter(lambda:f.read(8*1024*1024),b""):h.update(block)
 assert h.hexdigest()==expected,"SHA256 mismatch: "+p.name
 print("HASH_VERIFIED",p.name,flush=True)
def rank(dataset,difficulty,source_id):return hashlib.sha256(f'{SEED}|{dataset}|{difficulty}|{source_id}'.encode()).hexdigest()
def dump(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8');tmp.replace(path)
class StringsOnly(pickle.Unpickler):
 def find_class(self,module,name):raise ValueError('Unexpected executable pickle object')
def decode_private(s):
 try:return json.loads(s)
 except json.JSONDecodeError:return json.loads(StringsOnly(io.BytesIO(zlib.decompress(base64.b64decode(s)))).load())
def prepare(dataset):
 raw=ROOT/'data/raw'; dest=ROOT/'data/tasks';dest.mkdir(parents=True,exist_ok=True)
 rows=[]
 if dataset=='taco':
  wait_file(raw/'taco_test.parquet')
  import pyarrow.parquet as pq
  columns=['question','difficulty','input_output','starter_code']
  table=pq.read_table(raw/'taco_test.parquet',columns=columns)
  for i,row in enumerate(table.to_pylist()):
   rows.append({'source_id':str(i),'difficulty':row['difficulty'],'row':row,'id':f'taco_{i:04d}'})
 else:
  for fno in range(1,7):
   path=raw/f'lcb_test{fno}.jsonl';wait_file(path)
   with open(path,'rb') as f:
    while True:
     offset=f.tell();line=f.readline()
     if not line:break
     row=json.loads(line)
     source_id=f"{row['platform']}:{row['question_id']}"
     taskid='lcb_'+re.sub(r'[^A-Za-z0-9_-]','_',source_id)
     rows.append({'source_id':source_id,'difficulty':row['difficulty'],'file':str(path),'offset':offset,'id':taskid})
  assert len({x['id'] for x in rows})==len(rows),'Duplicate LCB IDs'
 counts=dict(collections.Counter(r['difficulty'] for r in rows)); print(dataset,'available',counts,flush=True)
 assert set(counts)==set(LEVELS[dataset]),counts
 selected=[];qa=[]
 for difficulty in LEVELS[dataset]:
  subset=sorted([r for r in rows if r['difficulty']==difficulty],key=lambda r:rank(dataset,difficulty,r['source_id']))[:100]
  for order,meta in enumerate(subset):
   if dataset=='taco':
    row=meta['row'];tests=json.loads(row['input_output']);prompt=row['question'];starter=row.get('starter_code') or ''
   else:
    with open(meta['file'],'rb') as f:f.seek(meta['offset']);row=json.loads(f.readline())
    cases=json.loads(row['public_test_cases'])+decode_private(row['private_test_cases'])
    tests={'inputs':[x['input'] for x in cases],'outputs':[x['output'] for x in cases],'fn_name':json.loads(row['metadata']).get('func_name')}
    prompt=row['question_content'];starter=row.get('starter_code') or ''
   assert len(tests['inputs'])==len(tests['outputs']) and len(tests['inputs'])>0,meta['id']
   record={'dataset':dataset,'task_id':meta['id'],'source_id':meta['source_id'],'difficulty':difficulty,'order':order,'num_tests':len(tests['inputs']),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'function_name':tests.get('fn_name'),'rank':rank(dataset,difficulty,meta['source_id'])}
   task={**record,'prompt':prompt,'starter_code':starter,'input_output':json.dumps(tests,ensure_ascii=False)}
   dump(dest/(meta['id']+'.json'),task);selected.append(record)
 manifest={'dataset':dataset,'revision':REV[dataset],'release':'test' if dataset=='taco' else 'release_v6','seed':SEED,'sampling':'smallest SHA256(seed|dataset|difficulty|source_id), ordered by that hash','available':counts,'selected':dict(collections.Counter(r['difficulty'] for r in selected)),'tasks':selected}
 dump(ROOT/'data'/f'{dataset}_manifest.json',manifest)
 print(dataset,'SELECTED',manifest['selected'],flush=True)
 if dataset=='taco':
  import pyarrow.parquet as pq
  schema=pq.read_schema(raw/'taco_test.parquet')
  if 'solutions' in schema.names:
   soltable=pq.read_table(raw/'taco_test.parquet',columns=['solutions'])
   for functional in [False,True]:
    candidates=[r for r in selected if bool(r['function_name'])==functional]
    for r in candidates[:3]:
     sols=soltable['solutions'][int(r['source_id'])].as_py()
     if isinstance(sols,str):sols=json.loads(sols)
     if sols:
      qa.append({'task_id':r['task_id'],'code':sols[0]})
   dump(ROOT/'data'/'taco_reference_qa.json',qa)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('dataset',choices=['taco','lcb']);a=p.parse_args();prepare(a.dataset)
