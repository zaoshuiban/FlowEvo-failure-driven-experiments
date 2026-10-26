import pathlib,json,hashlib,collections,re,time
import pyarrow.parquet as pq
P=pathlib.Path(__file__).parent
def read(n):return json.loads((P/n).read_text())
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
while not (P/'inventory_summary.json').exists():time.sleep(20)
# Preserve the earlier metadata-only draft. No Worker/model outcomes have been used.
for n in ['selected_metadata.json','inventory_summary.json']:(P/(n+'.draft')).write_text((P/n).read_text())
records=read('inventory.json');cfg=read('protocol.json');seed=cfg['seed'];review=[]
for r in records:
 if r['tier']=='C':
  if not r['reasons']:r['reasons'].append('NO_DISJOINT_ONLINE_AND_SEALED_TESTS')
  continue
 t=read('candidates/'+r['id']+'.json');contract=t['output_contract']
 # Preserve all statement samples, but do not spend scarce sealed cases on optional extra online inputs.
 target_online=max(2,r['statement_sample_count'])
 if r['tier']=='B_THIN' and r['online_count']>target_online and r['online_count']+r['sealed_count']-target_online>=6:
  moved=t['public_cases'][target_online:];t['public_cases']=t['public_cases'][:target_online];t['sealed_cases']=moved+t['sealed_cases']
  r.update(tier='B_STANDARD',online_count=len(t['public_cases']),sealed_count=len(t['sealed_cases']),stored_sealed_count=len(t['sealed_cases']))
  t.update({k:r[k] for k in ['tier','online_count','sealed_count','stored_sealed_count']});write('candidates/'+r['id']+'.json',t)
 bad=bool(re.search(r'any order|arbitrary|(?:print|output) any|any (?:of|one)|absolute error|relative error|order (?:does not|doesn.t) matter|in whichever order',contract,re.I))
 if r['dataset']!='cc' and re.search(r'case.insensitive|any case',contract,re.I):bad=True
 if bad:
  r['tier']='C';r['reasons'].append('UNSUPPORTED_OUTPUT_EQUIVALENCE');t['tier']='C';t['reasons']=r['reasons'];write('candidates/'+r['id']+'.json',t)
 review.append(dict(id=r['id'],accepted=not bad,output_contract=contract,reason='unsupported equivalence' if bad else 'metadata contract screening only'))
write('output_contract_review.json',review)
# Exhaustive selected-to-history shingle checks supplement approximate full-pool retrieval.
R=P.resolve().parents[1];T=pathlib.Path('/Users/majiatong/lab/AFlow/results/experiment_d0_20261019_s0_v1/data')
def grams(q):
 w=re.findall(r'[a-z0-9]+',q.lower());return set(zip(w,w[1:],w[2:],w[3:],w[4:]))
texts=[]
for batch in pq.ParquetFile(T/'taco_ALL_test-00000-of-00001.parquet').iter_batches(batch_size=64,columns=['question']):texts.extend(t['question'] for t in batch.to_pylist())
texts.extend(t['prompt'] for t in json.loads((R/'runs/s19g_train_expansion_20261024_01/admission_inputs.json').read_text()))
for f in (R/'datasets/extracted/data/tasks').glob('*.json'):texts.append(json.loads(f.read_text()).get('prompt',''))
for line in (T/'lcb_test6.jsonl').open():texts.append(json.loads(line)['question_content'])
a=json.loads((R/'runs/s20_preparation_20261025_01/external_acceptance.json').read_text());oldids={i for ids in a['selected'].values() for i in ids}
texts.extend(t['prompt'] for t in json.loads((R/'runs/s20_preparation_20261025_01/external_candidates.json').read_text()) if t['id'] in oldids)
history=[grams(q) for q in texts];chosen_grams=[];extra_rejections=[]
def full_near_check(r):
 g=grams(read('candidates/'+r['id']+'.json')['prompt'])
 for label,others in [('HISTORICAL',history),('ALREADY_SELECTED',chosen_grams)]:
  for z in others:
   if min(len(g),len(z))/max(1,len(g),len(z))<.85:continue
   if len(g&z)/max(1,len(g|z))>=.85:
    extra_rejections.append(dict(id=r['id'],reason='FULL_JACCARD_'+label));return None
 return g
used=set();selected={'learning':[],'confirmation':[]} 
def eligible(r,role,quota):
 if r['tier']!='B_STANDARD' or r['component_exposed'] or r['component'] in used:return False
 ds=r['dataset'];diff=r['difficulty'];part=int(sha(r['identity']),16)%3
 if not quota.startswith(ds+'_'):return False
 if ds=='apps':
  allowed=(r['official_split']=='train' or r['official_split']=='test' and part!=0) if role=='learning' else r['official_split']=='test' and part==0
  return allowed and quota=='apps_'+diff
 if ds=='cc':
  if (r['official_split']=='train')!=(role=='learning'):return False
  rating=int(diff or 0);return (1600<=rating<2000 if quota=='cc_1600_1999' else 2000<=rating<2400 if quota=='cc_2000_2399' else rating>=2400 if quota=='cc_2400_plus' else rating>=1600)
 return quota=='lcb_'+diff and ((part==0)==(role=='confirmation'))
for role,key in [('learning','long_stream_targets'),('confirmation','confirmation_targets')]:
 for quota,target in cfg[key].items():
  ranked=sorted((r for r in records if eligible(r,role,quota)),key=lambda r:(0 if r['official_split']=='train' else 1,sha(seed+'|'+role+'|'+r['id'])))
  n=0
  for r in ranked:
   if r['component'] in used:continue
   if n>=target:break
   g=full_near_check(r)
   if g is None:continue
   chosen_grams.append(g)
   used.add(r['component']);selected[role].append(dict(r,quota=quota,selection_hash=sha(seed+'|'+role+'|'+r['id'])));n+=1
for role in selected:selected[role].sort(key=lambda r:sha(seed+'|stream|'+r['id']))
assert not ({r['component'] for r in selected['learning']}&{r['component'] for r in selected['confirmation']})
write('inventory.json',records);write('selected_metadata.json',selected)
s=read('inventory_summary.json');s.update(tiers=dict(collections.Counter(r['tier'] for r in records)),tier_difficulty=dict(collections.Counter(r['dataset']+':'+r['official_split']+':'+r['difficulty']+':'+r['tier'] for r in records)),reasons_overlap=dict(collections.Counter(w for r in records for w in r['reasons'])),selected={k:len(v) for k,v in selected.items()},quota_counts={k:dict(collections.Counter(r['quota'] for r in v)) for k,v in selected.items()});write('inventory_summary.json',s)
write('selected_near_duplicate_audit.json',dict(historical_texts=len(history),selected_texts=len(chosen_grams),exhaustive_selected_history_and_selected_pairs=True,jaccard=.85,rejected=extra_rejections))
write('selection_finalized.json',dict(status='FROZEN_BEFORE_WORKER',model_calls=0,selection_sha256=sha((P/'selected_metadata.json').read_text()),protocol_sha256=sha((P/'protocol.json').read_text())))
print('FINAL SELECTION',s['selected'],flush=True)
