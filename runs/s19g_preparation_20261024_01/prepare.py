import json,pathlib,re,hashlib,sys,itertools
import pyarrow.parquet as pq
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=pathlib.Path(__file__).parent
AF=pathlib.Path('/Users/majiatong/lab/AFlow/results');D0=AF/'experiment_d0_20261019_s0_v1';RAW=D0/'data/taco_ALL_test-00000-of-00001.parquet'
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(s):return re.sub(r'\s+',' ',s).strip()
def write(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2))
excluded={};oldprompts=set()
# IDs and hashes only: do not reread 800 trajectories or their outcomes.
for f in (ROOT/'datasets/extracted/data/tasks').glob('taco_*.json'):
 t=json.loads(f.read_text());excluded.setdefault(int(t['source_id']),[]).append('FlowEvo E3-S0 audited cohort');oldprompts.add(sha(norm(t['prompt']).encode()))
ignore={'duplicate_groups.json','full_pool_inventory.json','reserve_order.json','duplicate_edges.json','taco_references.json','dataset_inventory.json','taco_parsed_admitted.json','lcb_public_tasks.json','lcb_private_cases.json','artifact_manifest.json','history_before.json','protected_before.json','protected_after.json','source_hashes.json','artifact_hashes.json','final_integrity_audit.json'}
for directory in sorted(AF.glob('experiment_d0*'))+sorted(AF.glob('experiment_e3*')):
 for f in directory.rglob('*'):
  if not f.is_file() or f.name in ignore or any(s in ('data','frozen_code','__pycache__') for s in f.relative_to(directory).parts) or f.suffix not in ('.json','.jsonl','.csv','.md','.log'):continue
  text=f.read_text(errors='replace')
  for value in set(re.findall(r'taco-test-(\d+)\b',text)):excluded.setdefault(int(value),[]).append(str(f))
for c in json.loads((ROOT/'runs/s18_data_freeze_20261023_01/candidate_order.json').read_text()):
 excluded.setdefault(int(c['id'].split('-')[-1]),[]).append('S18 prior admission candidate; conservatively exposed')
# Metadata-only inventory does not exclude. It supplies official SPJ/image flags.
inv={int(t['id'].split('-')[-1]):t for t in json.loads((D0/'dataset_inventory.json').read_text()) if t['source']=='TACO'}
rows=[];idx=0
for batch in pq.ParquetFile(RAW).iter_batches(batch_size=32):
 for t in batch.to_pylist():
  t['_index']=idx;idx+=1;rows.append(t)
seen_urls={str(rows[i].get('url') or '').rstrip('/') for i in excluded if i<len(rows)}-{''}
plan={'seed':'S19G-long-stream-v1','source':'official frozen TACO test Parquet, streamed locally in batches32','source_sha256':sha(RAW.read_bytes()),'source_url':json.loads((D0/'data/download_ledger.json').read_text())[0]['url'],'exposure':'exclude actual project study records and E3-S0 audited task IDs; metadata-only inventory not exclusion','selection':'round robin MEDIUM/MEDIUM_HARD/HARD/VERY_HARD, SHA256(seed|url|normalized_question_hash); at most200 candidate admissions, first80 passing; single continuous stream; no model outcome selection; no new solver results','scoring':'unique-output tokens; exact public statement examples; 12 predesignated online development judge inputs plus12 disjoint final judge inputs; never called statement samples; two original independent source hashes pass both splits; invalid output must fail','model_api_calls':0}
write('selection_protocol.json',plan);write('exposure.json',{str(k):sorted(set(v)) for k,v in excluded.items()})
candidates=[]
for t in rows:
 i=t['_index'];url=str(t.get('url') or '').rstrip('/');qhash=sha(norm(t['question']).encode());meta=inv[i]
 if i in excluded or url in seen_urls or qhash in oldprompts or not meta['admitted_metadata'] or meta['interface']!='stdin' or t['difficulty']=='EASY':continue
 # Restrict parsable Codeforces style sample sections, not raw test prefix.
 q=t['question'];sample=q.split('-----Examples-----')[-1] if '-----Examples-----' in q else q.split('-----Example-----')[-1] if '-----Example-----' in q else ''
 matches=re.findall(r'(?:^|\n)Input\s*\n(.*?)\nOutput\s*\n(.*?)(?=\nInput\s*\n|\n(?:Note|-----)|\Z)',sample,re.S)
 public=[]
 for a,b in matches:
  b=b.split('-----Note-----')[0].strip();a=a.strip()
  if a and b:public.append({'input':a+'\n','expected':b,'comparison':'tokens','scorer':'s1','provenance':'verbatim statement sample'})
 if not public:continue
 io=json.loads(t['input_output']);aud=[];pubkeys={norm(c['input']) for c in public}
 for a,b in zip(io['inputs'],io['outputs']):
  if not isinstance(a,str) or not isinstance(b,str) or norm(a) in pubkeys:continue
  if norm(a) in {norm(c['input']) for c in aud}:continue
  aud.append({'input':a,'expected':b,'comparison':'tokens','scorer':'s1','provenance':'official raw evaluator-only case'})
 aud=sorted(aud,key=lambda c:sha(('S19G-role-split|'+c['input']).encode()))[:24]
 if len(aud)<24:continue
 for x in aud[:12]:x['provenance']='benchmark judge input predesignated online-visible development; not statement sample'
 development=aud[:12];aud=aud[12:]
 rank=sha(('S19G-long-stream-v1|'+url+'|'+qhash).encode())
 candidates.append({'id':'taco-test-'+str(i),'difficulty':t['difficulty'],'url':url,'question_hash':qhash,'prompt':q,'public':public+development,'statement_samples':public,'review':aud,'solutions':json.loads(t['solutions']),'rank':rank})
groups=[iter(sorted([c for c in candidates if c['difficulty']==d],key=lambda c:c['rank'])) for d in ['MEDIUM','MEDIUM_HARD','HARD','VERY_HARD']]
ordered=[x for row in itertools.zip_longest(*groups) for x in row if x is not None][:200]
write('candidate_order.json',[{k:v for k,v in c.items() if k not in ('solutions','public','review','prompt','statement_samples')} for c in ordered]);write('admission_inputs.json',ordered)
print('excluded',len(excluded),'eligible metadata+sample',len(candidates),'bounded admissions',len(ordered))
