"""Fixed official test splits, metadata-only admission. No target model and no solution execution."""
import json,pathlib,re,hashlib,ast,collections
import pyarrow.parquet as pq
P=pathlib.Path(__file__).parent;R=P.parents[1];D=pathlib.Path('/Users/majiatong/lab/AFlow/data/sources/s20_external');BASE=R/'runs/s19g_train_expansion_20261024_01'
def wr(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def norm(s):return re.sub(r'\s+',' ',s).strip()
def url(s):return re.sub(r'/contest/(\d+)/problem/',r'/problemset/problem/\1/',str(s).rstrip('/')).replace('http://','https://').replace('www.','')
def grams(s):
 t=re.findall('[a-z0-9]+',s.lower());return set(zip(t,t[1:],t[2:],t[3:],t[4:]))
old=json.loads((BASE/'exposure_baseline.json').read_text());urls=set(old['canonical_urls']);hashes=set(old['question_hashes']);gs=[];oldrefs=set()
T=pathlib.Path('/Users/majiatong/lab/AFlow/results/experiment_d0_20261019_s0_v1/data')
for b in pq.ParquetFile(T/'taco_ALL_test-00000-of-00001.parquet').iter_batches(batch_size=64,columns=['question','solutions']):
 for t in b.to_pylist():
  gs.append(grams(t['question']));oldrefs.update(sha(s) for s in json.loads(t['solutions']) if isinstance(s,str))
for t in json.loads((BASE/'admission_inputs.json').read_text()):
 urls.add(url(t['url']));hashes.add(sha(norm(t['prompt'])));gs.append(grams(t['prompt']));oldrefs.update(sha(s) for s in t['solutions'])
for f in (R/'datasets/extracted/data/tasks').glob('*.json'):
 t=json.loads(f.read_text());q=t.get('prompt','');gs.append(grams(q))
for l in (T/'lcb_test6.jsonl').open():gs.append(grams(json.loads(l)['question_content']))
wr('external_selection_protocol.json',dict(version='s20-external-admission-v1',model_calls=0,sources={'apps':'test; interview/competition','contests':'test; Codeforces cf_rating >=1600','lcb':'official Lite release_v6; references prerequisite'},order='source rank APPS then CodeContests; original source row order, no model outcome ranking',max_candidates={'apps':80,'contests':40},target={'apps':40,'contests':20,'lcb':30},required_tests='literal samples plus12 online developer and12 sealed; normalized input disjoint',reference_limit=4,required_ast_distinct_references=2,near_jaccard=.85,comparator='existing s1 exact tokens; output contract review mandatory',role_seed='S20-role-v1',reference_policy='official Python3; no generated patches',prior_exposure=dict(urls=len(urls),question_hashes=len(hashes),reference_hashes=len(oldrefs))))
audit=[];candidates=[];seenurls=set();seeng=[];seenref=set()
def consider(dataset,i,q,u,diff,samples,tests,sol,extra=None):
 tid=f'{dataset}-test-{i}';why=[];u=url(u);qh=sha(norm(q));g=grams(q)
 if u in urls or qh in hashes:why.append('EXPOSED_IDENTITY')
 if u in seenurls:why.append('CROSS_SOURCE_DUPLICATE')
 if re.search('interactive|<img|<image',q,re.I):why.append('INTERACTIVE_OR_IMAGE')
 # Literal output section, requiring manual semantic review below.
 m=re.search(r'(?:^|\n)(?:[-# ]*)Output(?:[-# ]*)\n(.*?)(?=\n(?:[-# ]*)Examples?\b|\n(?:[-# ]*)Sample|\Z)',q,re.S|re.I)
 output=m.group(1).strip() if m else ''
 if not output:why.append('OUTPUT_CONTRACT_UNPARSED')
 if re.search(r'any (?:of|one|valid|possible|solution|answer)|multiple (?:answers|solutions)|several (?:answers|solutions)|absolute or relative|relative or absolute|precision|arbitrary|case.insensitive|any case',output,re.I):why.append('SPECIAL_JUDGE_OR_CASE_SEMANTICS')
 if not samples:why.append('NO_LITERAL_SAMPLES')
 seen={norm(c['input']) for c in samples};unique=[]
 for c in tests:
  if not isinstance(c['input'],str) or not isinstance(c['expected'],str) or not c['input'].strip() or not c['expected'].strip() or norm(c['input']) in seen:continue
  seen.add(norm(c['input']));unique.append(c)
 unique.sort(key=lambda c:sha('S20-role-v1|'+c['input']));chosen=unique[:24]
 if len(chosen)<24:why.append('FEWER_THAN_24_DISJOINT_TESTS')
 if sum(len(c['input'].encode())+len(c['expected'].encode()) for c in samples+chosen[:12])>16000:why.append('PUBLIC_BYTES_LIMIT')
 refs=[];ahs=set()
 for s in sol:
  if not isinstance(s,str):continue
  try:a=ast.dump(ast.parse(s),include_attributes=False);compile(s,'reference','exec')
  except (SyntaxError,ValueError,TypeError):continue
  ah=sha(a)
  if ah in ahs:continue
  ahs.add(ah);refs.append(s)
  if len(refs)==4:break
 if len(refs)<2:why.append('FEWER_THAN_TWO_PYTHON3_REFERENCES')
 if any(sha(s) in oldrefs for s in refs):why.append('EXPOSED_REFERENCE_LINEAGE')
 if ahs&seenref:why.append('CROSS_SOURCE_REFERENCE_LINEAGE')
 score=0.
 if not why:
  for z in gs+seeng:
   if min(len(z),len(g))/max(1,len(z),len(g))<.85:continue
   score=max(score,len(z&g)/max(1,len(z|g)))
  if score>=.85:why.append('NEAR_DUPLICATE')
 record=dict(id=tid,dataset=dataset,row=i,url=u,difficulty=diff,question_hash=qh,reasons=why,near_jaccard=score,unique_nonexample_tests=len(unique),reference_hashes=[sha(s) for s in refs],metadata=extra or {})
 audit.append(record)
 if not why:
  seenurls.add(u);seeng.append(g);seenref.update(ahs)
  if sum(x['dataset']==dataset for x in candidates)<({'apps':80,'contests':40}[dataset]):
   candidates.append(dict(record,prompt=q,public=samples+chosen[:12],statement_samples=samples,review=chosen[12:],solutions=refs,output_contract=output))
def parse_samples(q):
 # APPS/Codeforces literal Input/Output blocks only. Ambiguous markdown is excluded.
 h=re.search(r'(?:^|\n)(?:[-# ]*)Examples?(?:[-# ]*)\n',q,re.I)
 sample=q[h.end():] if h else ''
 return [dict(input=a.strip()+'\n',expected=b.strip(),comparison='tokens',scorer='s1',provenance='statement sample') for a,b in re.findall(r'(?:^|\n)Input\s*\n(.*?)\nOutput\s*\n(.*?)(?=\nInput\s*\n|\n(?:Note\b|-----)|\Z)',sample,re.S) if a.strip() and b.strip()]
for i,line in enumerate((D/'apps_test.jsonl').open()):
 t=json.loads(line)
 if t['difficulty'] not in ('interview','competition'):audit.append(dict(id=f'apps-test-{t["id"]}',dataset='apps',reasons=['DIFFICULTY_SCOPE']));continue
 try:io=json.loads(t['input_output']);sol=json.loads(t['solutions']);assert not io.get('fn_name') and not t.get('starter_code')
 except Exception:audit.append(dict(id=f'apps-test-{t["id"]}',dataset='apps',reasons=['NOT_STDIN_OR_MALFORMED']));continue
 tests=[dict(input=a,expected=b,comparison='tokens',scorer='s1',provenance='APPS official input_output, research reassignment') for a,b in zip(io.get('inputs',[]),io.get('outputs',[]))]
 consider('apps',t['id'],t['question'],t['url'],t['difficulty'],parse_samples(t['question']),tests,sol)
for i,t in enumerate(pq.read_table(D/'contests_test-00000-of-00001-9c49eeff30aacaa8.parquet').to_pylist()):
 if t['source']!=2 or t['cf_rating']<1600 or t['input_file'] or t['output_file']:audit.append(dict(id=f'contests-test-{i}',dataset='contests',reasons=['DIFFICULTY_OR_STDIN_SCOPE']));continue
 samples=[dict(input=a,expected=b,comparison='tokens',scorer='s1',provenance='CodeContests public_tests') for a,b in zip(t['public_tests']['input'],t['public_tests']['output'])]
 tests=[dict(input=a,expected=b,comparison='tokens',scorer='s1',provenance='CodeContests '+kind+', research reassignment') for kind in ('private_tests','generated_tests') for a,b in zip(t[kind]['input'],t[kind]['output'])]
 sol=[s for lang,s in zip(t['solutions']['language'],t['solutions']['solution']) if lang==3]
 consider('contests',i,t['description'],f'https://codeforces.com/problemset/problem/{t["cf_contest_id"]}/{t["cf_index"]}',str(t['cf_rating']),samples,tests,sol,dict(name=t['name'],raw_difficulty=t['difficulty']))
wr('external_admission_audit.json',audit);wr('external_candidates.json',candidates);wr('external_candidate_order.json',[x['id'] for x in candidates]);wr('external_funnel.json',{d:dict(examined=sum(x['dataset']==d for x in audit),metadata_candidates=sum(x['dataset']==d for x in candidates),reasons=dict(collections.Counter(r for x in audit if x['dataset']==d for r in x['reasons']))) for d in ('apps','contests')})
(P/'output_contracts.txt').write_text('\n\n'.join(x['id']+' '+x['url']+'\n'+x['output_contract'] for x in candidates))
print((P/'external_funnel.json').read_text())
