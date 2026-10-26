"""Full pinned-source inventory and metadata-only role selection. No model client."""
import json,pathlib,re,hashlib,collections,base64,zlib,pickle,io,sys,ast,time
import pyarrow.parquet as pq
from functools import lru_cache
P=pathlib.Path(__file__).resolve().parent; R=P.parents[1]
D=pathlib.Path('/Users/majiatong/lab/AFlow/data/sources/s20_external_v2'); OLD=D.parent/'s20_external'
T=pathlib.Path('/Users/majiatong/lab/AFlow/results/experiment_d0_20261019_s0_v1/data')
from scorer import accepts
cfg=json.loads((P/'protocol.json').read_text());seed=cfg['seed']
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def norm(s):return re.sub(r'\s+',' ',s).strip()
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def canonical(u):
 u=str(u).lower().replace('http://','https://').replace('www.','').rstrip('/')
 m=re.search(r'codeforces.com/(?:contest/(\d+)/problem/|problemset/problem/(\d+)/)([a-z0-9]+)',u)
 if m:return 'cf:'+str(m[1] or m[2])+':'+m[3]
 m=re.search(r'atcoder.jp/contests/[^/]+/tasks/([^/?#]+)',u)
 return 'atcoder:'+m[1] if m else u
class Safe(pickle.Unpickler):
 def find_class(self,*a):raise ValueError('pickle global forbidden')
 def persistent_load(self,*a):raise ValueError('pickle persistent forbidden')
def private(v):
 try:return json.loads(v)
 except Exception:pass
 raw=base64.b64decode(v,validate=True);d=zlib.decompressobj();out=d.decompress(raw,32*1024*1024+1)
 if len(out)>32*1024*1024 or not d.eof or d.unused_data:raise ValueError('compressed payload limit')
 obj=Safe(io.BytesIO(out)).load()
 if not isinstance(obj,(str,bytes)):raise ValueError('unexpected pickle value')
 return json.loads(obj)
def cases(inputs,outputs,role):
 if len(inputs)!=len(outputs):raise ValueError('case lengths')
 return [{'input':a,'expected':b,'provenance':role} for a,b in zip(inputs,outputs)]
def refs(sol):
 out=[]
 for s in sol:
  if not isinstance(s,str):continue
  try:tree=ast.parse(s);compile(tree,'reference','exec')
  except Exception:continue
  h=sha(ast.dump(tree,include_attributes=False))
  if h not in [x['ast_sha256'] for x in out]:out.append({'code':s,'sha256':sha(s),'ast_sha256':h})
  if len(out)==2:break
 return out
# Frozen historical exposure, distinct from merely reading full new source metadata.
old=json.loads((R/'runs/s19g_train_expansion_20261024_01/exposure_baseline.json').read_text())
exurls={canonical(u) for u in old['canonical_urls']};exhash=set(old['question_hashes']);extexts=[];exrefs=set()
for b in pq.ParquetFile(T/'taco_ALL_test-00000-of-00001.parquet').iter_batches(batch_size=64,columns=['question']):
 for t in b.to_pylist():extexts.append(t['question']);exhash.add(sha(norm(t['question'])))
for t in json.loads((R/'runs/s19g_train_expansion_20261024_01/admission_inputs.json').read_text()):
 extexts.append(t['prompt']);exhash.add(sha(norm(t['prompt'])));exurls.add(canonical(t['url']))
 for s in t['solutions']:exrefs.add(sha(s))
for f in (R/'datasets/extracted/data/tasks').glob('*.json'):
 t=json.loads(f.read_text());q=t.get('prompt','');extexts.append(q);exhash.add(sha(norm(q)))
for l in (T/'lcb_test6.jsonl').open():
 t=json.loads(l);extexts.append(t['question_content']);exhash.add(sha(norm(t['question_content'])))
strict=json.loads((R/'runs/s20_preparation_20261025_01/external_candidates.json').read_text())
# Old selected strict tasks, not all metadata-screened tasks.
a=json.loads((R/'runs/s20_preparation_20261025_01/external_acceptance.json').read_text());strictids={i for ids in a['selected'].values() for i in ids}
for t in strict:
 if t['id'] in strictids:exhash.add(t['question_hash']);exurls.add(canonical(t['url']));extexts.append(t['prompt'])
records=[];texts=[];parent=[];identity={};qhmap={};refmap={};buckets=collections.defaultdict(list)
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
def union(a,b):
 a,b=root(a),root(b)
 if a!=b:parent[max(a,b)]=min(a,b)
@lru_cache(maxsize=32768)
def grams(q):
 w=re.findall(r'[a-z0-9]+',q.lower());return {sha(' '.join(w[i:i+5]))[:16] for i in range(max(0,len(w)-4))}
# Bottom-k shingle candidate retrieval; full Jaccard for retrieved pairs.
exg=[grams(q) for q in extexts];exindex=collections.defaultdict(set)
for i,g in enumerate(exg):
 for h in sorted(g)[:32]:exindex[h].add(i)
(P/'candidates').mkdir(exist_ok=True)
def add(ds,split,tid,q,url,difficulty,samples,tests,solutions,meta,reason=None):
 idx=len(records);parent.append(idx);qhash=sha(norm(q));key=canonical(url);why=list(reason or []);g=grams(q);signature=sorted(g)[:32]
 exposed=key in exurls or qhash in exhash
 hits=collections.Counter(j for h in signature for j in exindex[h]);possible={j for j,n in hits.items() if n>=8}
 if not exposed:
  exposed=any(min(len(g),len(exg[j]))/max(1,len(g),len(exg[j]))>=.85 and len(g&exg[j])/max(1,len(g|exg[j]))>=.85 for j in possible)
 if re.search(r'interactive|<img|<image',q,re.I):why.append('INTERACTIVE_OR_IMAGE')
 m=re.search(r'(?:^|\n)[#\- ]*Output(?: Format)?[#\- ]*\n(.*?)(?=\n[#\- ]*(?:Examples?|Sample|Constraints|Input)\b|\Z)',q,re.S|re.I)
 contract=m.group(1) if m else ''
 if not contract:why.append('OUTPUT_CONTRACT_REQUIRES_REVIEW')
 if re.search(r'any (?:valid|possible|correct|suitable|solution|answer)|multiple (?:answers|solutions)|several (?:answers|solutions)|print any|output any|absolute or relative|relative or absolute|precision|special judge',contract,re.I):why.append('NONUNIQUE_OR_UNSUPPORTED_TOLERANCE')
 unique={};samplekeys=[]
 for c in samples+tests:
  if not isinstance(c.get('input'),str) or not isinstance(c.get('expected'),str) or not c['expected'].strip():why.append('MALFORMED_CASE');continue
  k=norm(c['input'])
  if not k:why.append('EMPTY_INPUT');continue
  if k in unique and not accepts(ds,unique[k]['expected'],c['expected']):why.append('CONTRADICTORY_EXPECTATIONS')
  if k not in unique:unique[k]=c
 for c in samples:
  if isinstance(c.get('input'),str) and norm(c['input']) in unique:samplekeys.append(norm(c['input']))
 # Any official input visibly embedded in the statement is online, never sealed.
 if ds=='apps':
  nq=' '+norm(q)+' '
  for k,c in unique.items():
   if len(k)<=len(nq) and k in nq and re.search(r'(?<!\w)'+re.escape(k)+r'(?!\w)',nq):
    samplekeys.append(k);c['provenance']='APPS official IO with input visible in statement; conservative online designation'
 samplekeys=list(dict.fromkeys(samplekeys));remaining=sorted(set(unique)-set(samplekeys),key=lambda k:sha(seed+'|'+tid+'|'+k))
 onlinekeys=samplekeys+remaining[:min(2,max(0,len(remaining)-1))];sealedkeys=remaining[len(onlinekeys)-len(samplekeys):]
 # Avoid a 1+7 split when 2+6 is available.
 if len(onlinekeys)<2 and len(sealedkeys)>1:onlinekeys.append(sealedkeys.pop(0))
 online=[unique[k] for k in onlinekeys];sealed=[unique[k] for k in sealedkeys]
 if any(len(c['input'].encode())+len(c['expected'].encode())>1024*1024 for c in online+sealed[:6]):why.append('CASE_RESOURCE_LIMIT')
 rr=refs(solutions)
 if any(r['sha256'] in exrefs for r in rr):exposed=True
 tier='C' if why or not online or not sealed else ('B_STANDARD' if len(online)>=2 and len(sealed)>=6 else 'B_THIN')
 rec=dict(id=tid,dataset=ds,official_split=split,difficulty=difficulty,url=url,identity=key,question_sha256=qhash,tier=tier,reasons=sorted(set(why)),historically_exposed=exposed,online_count=len(online),sealed_count=len(sealed),statement_sample_count=len(samplekeys),stored_sealed_count=min(24,len(sealed)),reference_count=len(rr),reference_hashes=[r['sha256'] for r in rr],metadata=meta,source_index=idx)
 for mapping,k in [(identity,key),(qhmap,qhash)]+[(refmap,r['sha256']) for r in rr]:
  if not k:continue
  if k in mapping:union(idx,mapping[k])
  else:mapping[k]=idx
 hits=collections.Counter(j for h in signature for j in buckets[h]);cand={j for j,n in hits.items() if n>=8}
 for j in cand:
  gj=grams(texts[j])
  if min(len(g),len(gj))/max(1,len(g),len(gj))>=.85 and len(g&gj)/max(1,len(g|gj))>=.85:union(idx,j)
 for h in signature:buckets[h].append(idx)
 texts.append(q);records.append(rec)
 if tier!='C':write('candidates/'+tid+'.json',dict(rec,prompt=q,public_cases=online,sealed_cases=sealed[:24],unused_official_tests=dict(count=max(0,len(sealed)-24),sha256=sha(json.dumps(sealed[24:],ensure_ascii=False,sort_keys=True)),reconstruction='pinned source row + build_pool deterministic role algorithm; not online'),references=rr,output_contract=contract))
 if idx%1000==0:print('inventory',idx,tid,flush=True)
for split,path in [('train',D/'apps_train.jsonl'),('test',OLD/'apps_test.jsonl')]:
 for line in path.open():
  t=json.loads(line);why=[]
  try:ss=json.loads(t.get('solutions') or '[]')
  except (ValueError,TypeError):ss=[]
  if not isinstance(ss,list):ss=[]
  try:
   v=json.loads(t['input_output']);tests=cases(v.get('inputs',[]),v.get('outputs',[]),'APPS official tests: research role reassignment')
   if v.get('fn_name'):why.append('CALL_BASED_UNSUPPORTED')
  except Exception:tests=[];why.append('MALFORMED_OFFICIAL_IO')
  add('apps',split,'apps-'+split+'-'+str(t['id']),t['question'],t.get('url',''),t['difficulty'],[],tests,ss,{},why)
while len(list(D.glob('cc_*.parquet')))<40:
 print('Waiting for all 40 remaining pinned CC shards',len(list(D.glob('cc_*.parquet'))),flush=True);time.sleep(30)
for path in sorted(list(D.glob('cc_*.parquet'))+list(OLD.glob('contests_test*.parquet'))):
 split='train' if 'train-' in path.name else 'valid' if 'valid-' in path.name else 'test';row=0
 for batch in pq.ParquetFile(path).iter_batches(batch_size=16):
  for t in batch.to_pylist():
   samples=cases(t['public_tests']['input'],t['public_tests']['output'],'CodeContests official public tests')
   tests=sum([cases(t[k]['input'],t[k]['output'],'CodeContests '+k+': research role reassignment') for k in ['private_tests','generated_tests']],[])
   url=f'https://codeforces.com/problemset/problem/{t["cf_contest_id"]}/{t["cf_index"]}' if t['source']==2 else 'codecontests:'+t['name']
   ss=[s for l,s in zip(t['solutions']['language'],t['solutions']['solution']) if l==3]
   add('cc',split,'cc-'+split+'-'+sha(t['name'])[:16],t['description'],url,str(t['cf_rating']),samples,tests,ss,{'name':t['name'],'source_shard':path.name,'row':row,'raw_difficulty':t['difficulty']},['FILE_IO_UNSUPPORTED'] if t['input_file'] or t['output_file'] else [])
   row+=1
while len(list(D.glob('lcb_test*.jsonl')))<5:
 print('Waiting for full LCB release',flush=True);time.sleep(30)
for path in sorted(D.glob('lcb_test*.jsonl'))+[T/'lcb_test6.jsonl']:
 for line in path.open():
  t=json.loads(line);why=[]
  try:
   pub=json.loads(t['public_test_cases']);priv=private(t['private_test_cases']);samples=cases([c['input'] for c in pub],[c['output'] for c in pub],'LCB official public samples');tests=cases([c['input'] for c in priv],[c['output'] for c in priv],'LCB official private tests: research role reassignment')
   if any(c['testtype']!='stdin' for c in pub+priv):why.append('CALL_BASED_UNSUPPORTED')
  except Exception as exc:samples=[];tests=[];why.append('SAFE_DECODE_FAILED:'+type(exc).__name__)
  qid=str(t['question_id']);platform=t['platform'];url='https://atcoder.jp/contests/'+qid.rsplit('_',1)[0]+'/tasks/'+qid if platform=='atcoder' else 'lcb:'+platform+':'+qid
  if platform=='codeforces':
   match=re.fullmatch(r'(\d+)[_-]?([A-Za-z][A-Za-z0-9]*)',qid)
   if match:url=f'https://codeforces.com/problemset/problem/{match[1]}/{match[2]}'
  add('lcb','test','lcb-'+platform+'-'+qid,t['question_content'],url,t['difficulty'].lower(),samples,tests,[],{'release':'release_v6','source_file':path.name,'contest_date':str(t.get('contest_date'))},why)
components=collections.defaultdict(list)
for i,r in enumerate(records):components[root(i)].append(i)
for k,ids in components.items():
 exp=any(records[i]['historically_exposed'] for i in ids)
 for i in ids:records[i]['component']=k;records[i]['component_exposed']=exp
write('inventory.json',records)
used=set();selected={'learning':[],'confirmation':[]}
def eligible(r,role,quota):
 if r['tier']!='B_STANDARD' or r['component_exposed'] or r['component'] in used:return False
 ds=r['dataset'];diff=r['difficulty']
 if not quota.startswith(ds+'_'):return False
 if ds=='apps':return r['official_split']==('train' if role=='learning' else 'test') and quota=='apps_'+diff
 if ds=='cc':
  if (r['official_split']=='train')!=(role=='learning'):return False
  rating=int(diff or 0);return (1600<=rating<2000 if quota=='cc_1600_1999' else 2000<=rating<2400 if quota=='cc_2000_2399' else rating>=2400 if quota=='cc_2400_plus' else rating>=1600)
 return quota=='lcb_'+diff and ((int(sha(r['identity']),16)%3==0)==(role=='confirmation'))
for role,key in [('learning','long_stream_targets'),('confirmation','confirmation_targets')]:
 for quota,target in cfg[key].items():
  ranked=sorted((r for r in records if eligible(r,role,quota)),key=lambda r:sha(seed+'|'+role+'|'+r['id']))
  n=0
  for r in ranked:
   if r['component'] in used:continue
   if n>=target:break
   used.add(r['component']);selected[role].append(dict(r,quota=quota,selection_hash=sha(seed+'|'+role+'|'+r['id'])));n+=1
for role in selected:selected[role].sort(key=lambda r:sha(seed+'|stream|'+r['id']))
write('selected_metadata.json',selected)
write('inventory_summary.json',{'total':len(records),'source_split_counts':dict(collections.Counter(r['dataset']+':'+r['official_split'] for r in records)),'tiers':dict(collections.Counter(r['tier'] for r in records)),'tier_difficulty':dict(collections.Counter(r['dataset']+':'+r['official_split']+':'+r['difficulty']+':'+r['tier'] for r in records)),'reasons_overlap':dict(collections.Counter(w for r in records for w in r['reasons'])),'exposed_components_tasks':sum(r['component_exposed'] for r in records),'selected':{k:len(v) for k,v in selected.items()},'quota_counts':{k:dict(collections.Counter(r['quota'] for r in v)) for k,v in selected.items()},'model_calls':0,'status':'METADATA_ONLY_PENDING_WORKER','near_duplicate_method':'bottom32 SHA256 five-word shingles with >=8 shared hashes candidate retrieval; verified Jaccard >=0.85; approximate retrieval can miss pairs'})
print(json.dumps(json.loads((P/'inventory_summary.json').read_text()),ensure_ascii=False),flush=True)
