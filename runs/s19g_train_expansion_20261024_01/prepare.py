"""Metadata-only train admission freeze. No target-model calls or generated solutions."""
import pathlib,json,re,hashlib,collections,itertools,ast,time
import pyarrow.parquet as pq
P=pathlib.Path(__file__).parent;R=P.parents[1];OLD=R/'runs/s19g_preparation_20261024_01';D=pathlib.Path('/Users/majiatong/lab/AFlow/results/experiment_d0_20261019_s0_v1/data')
def wr(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def norm(s):return re.sub(r'\s+',' ',s).strip()
def url(s):return re.sub(r'/contest/(\d+)/problem/',r'/problemset/problem/\1/',str(s).rstrip('/')).replace('http://','https://').replace('www.','')
def gram(s):
 t=re.findall(r'[a-z0-9]+',s.lower());return set(zip(t,t[1:],t[2:],t[3:],t[4:]))
plan={'version':'S19G-train-admission-v1','created_at':time.time(),'seed':'S19G-train-expansion-v1','source_revision':'d593ed0a2becbbc952230bb89be09189bf1056dc','shards':['ALL/train-00000-of-00009.parquet'],'target_new':61,'target_total':80,'max_admissions':200,'ordering':'MEDIUM/MEDIUM_HARD/HARD/VERY_HARD round robin, within stratum SHA256(seed|canonical_url|question_hash)','selection_uses_model_outputs':False,'exclude':'all1000 original TACO test identities conservatively; available LCB and project task identities; near duplicate Jaccard>=.85; exact/AST reference overlap; interactive/image/ambiguous output; malformed cases','sample_parser':'literal dashed or standalone Example(s)/Input/Output headings; no altered content','cases':'12 online developer tests +12 final tests by frozen hash after input dedup; statement samples excluded; all from official benchmark, not newly claimed statement examples','comparator':'unchanged tokens/s1; no floating tolerance or SPJ','public_bytes_max':16000,'reference_limit':4,'required_references':2,'reference_distinctness':'different normalized AST; no claim independent algorithms','negative':'constant impossible sentinel must fail all tests','max_reference_seconds_per_case':5,'model_requests':0}
wr('selection_protocol.json',plan)
# All TACO test identities are excluded regardless of whether individual test task was studied.
old=[]
for b in pq.ParquetFile(D/'taco_ALL_test-00000-of-00001.parquet').iter_batches(batch_size=32,columns=['question','url','solutions']):old.extend(b.to_pylist())
oldurls={url(t['url']) for t in old};oldhash={sha(norm(t['question'])) for t in old};oldgrams=[gram(t['question']) for t in old]
# Existing extracted task metadata adds non-TACO original identities, without reading outcomes.
for f in (R/'datasets/extracted/data/tasks').glob('*.json'):
 try:t=json.loads(f.read_text())
 except Exception:continue
 q=t.get('prompt','');u=t.get('url') or t.get('original_url')
 if q:oldhash.add(sha(norm(q)));oldgrams.append(gram(q))
 if u:oldurls.add(url(u))
# Available LCB source metadata (not outcomes); close cross-dataset original-identity gap.
for line in (D/'lcb_test6.jsonl').open():
 t=json.loads(line);q=t.get('question_content','');u=t.get('question_id','')
 if q:oldhash.add(sha(norm(q)));oldgrams.append(gram(q))
 if t.get('platform')=='atcoder':oldurls.add('https://atcoder.jp/contests/'+u.split('_')[0]+'/tasks/'+u)
source_hashes=set()
for t in old:
 for s in json.loads(t['solutions'] or '[]'):
  if isinstance(s,str):source_hashes.add(sha(s))
wr('exposure_baseline.json',{'excluded_all_test_rows':1000,'canonical_urls':sorted(oldurls),'question_hashes':sorted(oldhash),'statement_near_duplicate_threshold':.85,'gram_size':5,'old_reference_exact_hash_count':len(source_hashes),'available_project_metadata_files':len(list((R/'datasets/extracted/data/tasks').glob('*.json'))),'claim':'new to available project development records, not to model pretraining; all test split excluded for train selection'})
raw=pathlib.Path(json.loads((P/'download_ledger.json').read_text())['path']);audit=[];eligible=[];idx=0
for batch in pq.ParquetFile(raw).iter_batches(batch_size=32):
 for t in batch.to_pylist():
  i=idx;idx+=1;tid=f'taco-train-s00-r{i:04d}';q=t['question'];u=url(t.get('url'));qh=sha(norm(q));why=[]
  if t['source']!='codeforces':why.append('SOURCE_SCOPE_CODEFORCES')
  if t['difficulty'] not in ('MEDIUM','MEDIUM_HARD','HARD','VERY_HARD'):why.append('DIFFICULTY_SCOPE')
  if u in oldurls or qh in oldhash:why.append('EXPOSED_ORIGINAL_IDENTITY')
  if str(t.get('picture_num') or '0') not in ('0','0.0') or re.search(r'<image|<img|<span',q,re.I):why.append('IMAGE_OR_UNPARSED_HTML')
  if 'interactive' in (q+' '+str(t.get('raw_tags'))).lower():why.append('INTERACTIVE')
  try:io=json.loads(t['input_output']);sol=json.loads(t['solutions']);assert isinstance(io,dict) and len(io['inputs'])==len(io['outputs'])
  except Exception:why.append('MALFORMED_TESTS');io={};sol=[]
  if io.get('fn_name') or t.get('starter_code'):why.append('NOT_STDIN')
  header=re.search(r'(?:^|\n)(?:-----)?Examples?(?:-----)?\s*\n',q)
  oh=re.search(r'(?:^|\n)(?:-----)?Output(?:-----)?\s*\n',q)
  output=q[oh.end():header.start()].strip() if oh and header and oh.end()<header.start() else ''
  if not output:why.append('MISSING_OUTPUT_CONTRACT')
  if re.search(r'any (?:of|one|valid|possible|solution|answer)|multiple (?:answers|solutions)|several (?:answers|solutions)|absolute or relative|relative or absolute|precision|error.*10\^|arbitrary',output,re.I):why.append('SPJ_OR_NONUNIQUE_OUTPUT')
  sample=q[header.end():] if header else '';matches=re.findall(r'(?:^|\n)Input\s*\n(.*?)\nOutput\s*\n(.*?)(?=\nInput\s*\n|\n(?:Note\b|-----)|\Z)',sample,re.S)
  public=[dict(input=a.strip()+'\n',expected=b.strip(),comparison='tokens',scorer='s1',provenance='verbatim statement sample') for a,b in matches if a.strip() and b.strip()]
  if not public:why.append('NO_LITERAL_SAMPLES')
  seen={norm(x['input']) for x in public};tests=[]
  for a,b in zip(io.get('inputs',[]),io.get('outputs',[])):
   if not isinstance(a,str) or not isinstance(b,str) or not a.strip() or not b.strip() or norm(a) in seen:continue
   seen.add(norm(a));tests.append(dict(input=a,expected=b,comparison='tokens',scorer='s1',provenance='official benchmark judge test'))
  tests=sorted(tests,key=lambda c:sha('S19G-role-split|'+c['input']))[:24]
  if len(tests)!=24:why.append('FEWER_THAN_24_DISJOINT_TESTS')
  if sum(len(c['input'].encode())+len(c['expected'].encode()) for c in public+tests[:12])>16000:why.append('PUBLIC_BYTES_LIMIT')
  if any(not re.fullmatch(r'[-+0-9A-Za-z_\s]+',x['expected']) for x in public+tests):why.append('NON_TOKEN_EXACT_OUTPUT_SCOPE')
  valid=[];structures=set();compile_errors=[]
  for s in sol:
   if not isinstance(s,str):continue
   try:tree=ast.parse(s);compile(s,'reference','exec');ah=sha(ast.dump(tree,include_attributes=False))
   except (SyntaxError,ValueError,TypeError) as exc:compile_errors.append(type(exc).__name__);continue
   if ah in structures:continue
   structures.add(ah);valid.append({'code':s,'sha256':sha(s),'ast_sha256':ah})
   if len(valid)==4:break
  if len(valid)<2:why.append('FEWER_THAN_TWO_STATIC_REFERENCES')
  if any(x['sha256'] in source_hashes for x in valid):why.append('REFERENCE_LINEAGE_OVERLAP')
  nearest=None;score=0
  if not why:
   g=gram(q)
   for j,og in enumerate(oldgrams):
    if min(len(g),len(og))/max(1,max(len(g),len(og)))<.85:continue
    v=len(g&og)/max(1,len(g|og))
    if v>score:score=v;nearest=j
   if score>=.85:why.append('NEAR_EXPOSED_STATEMENT')
  rec={'id':tid,'row':i,'difficulty':t['difficulty'],'url':u,'question_hash':qh,'statement_bytes':len(q.encode()),'numeric_literal_count':len(re.findall(r'\d+',q)),'test_count':len(io.get('inputs',[])),'reasons':why,'near_jaccard':score,'near_baseline_index':nearest,'reference_hashes':[x['sha256'] for x in valid],'reference_ast_hashes':[x['ast_sha256'] for x in valid],'invalid_reference_syntax_count':len(compile_errors)};audit.append(rec)
  if not why:
   eligible.append(dict(rec,prompt=q,public=public+tests[:12],statement_samples=public,review=tests[12:],solutions=[v['code'] for v in valid],output_contract=output,rank=sha(plan['seed']+'|'+u+'|'+qh)))
groups=[iter(sorted([x for x in eligible if x['difficulty']==d],key=lambda x:x['rank'])) for d in ['MEDIUM','MEDIUM_HARD','HARD','VERY_HARD']]
ordered=[x for row in itertools.zip_longest(*groups) for x in row if x is not None]
accepted=[];gs=[];urls=set();refhash=set()
for c in ordered:
 reasons=[];g=gram(c['prompt'])
 if c['url'] in urls:reasons.append('DUPLICATE_TRAIN_ORIGINAL')
 if any(len(g&z)/max(1,len(g|z))>=.85 for z in gs):reasons.append('NEAR_TRAIN_DUPLICATE')
 if set(c['reference_ast_hashes'])&refhash:reasons.append('TRAIN_REFERENCE_LINEAGE_DUPLICATE')
 if reasons:
  next(x for x in audit if x['id']==c['id'])['reasons']+=reasons;continue
 accepted.append(c);urls.add(c['url']);gs.append(g);refhash.update(c['reference_ast_hashes'])
 if len(accepted)==200:break
wr('task_exposure_and_admission_audit.json',audit);wr('admission_inputs.json',accepted);wr('candidate_order.json',[{k:v for k,v in c.items() if k not in ('prompt','public','review','solutions','statement_samples')} for c in accepted]);wr('metadata_funnel.json',{'raw':idx,'eligible_before_train_dedup':len(eligible),'frozen_candidates':len(accepted),'rejection_reasons_nonexclusive':dict(collections.Counter(w for x in audit for w in x['reasons'])),'api_calls':0});print(idx,len(eligible),len(accepted),flush=True)
