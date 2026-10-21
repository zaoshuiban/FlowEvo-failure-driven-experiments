"""Freeze S1 sampling before examining new task-level execution evidence."""
import collections,hashlib,json,pathlib,re
R=pathlib.Path(__file__).resolve().parents[1];B=R.parent
def read(p):return json.loads(p.read_text())
def h(s):return hashlib.sha256(s.encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cat={x['task_id']:x for x in read(B/'repair_v2/catalog.json')}
 tasks={x['task_id']:x for x in read(B/'repair_v2/epochs/repaired_reports_20261020/task_results.json')}
 events=[json.loads(s) for s in (B/'e3_s0_20261020/events.jsonl').read_text().splitlines()]
 ev=collections.defaultdict(list)
 for e in events:ev[e['task_id']].append(e)
 trusted={x['task_id']:x for x in read(B/'trusted_rgf_20261020/trusted_tasks.json')}
 # Conservative exact/near-duplicate source grouping, explicitly provisional.
 parent={tid:tid for tid in cat}
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 def union(a,b):a,b=find(a),find(b);parent[max(a,b)]=min(a,b)
 tokens={tid:re.findall(r'[a-z]+|#',re.sub(r'\d+','#',t['prompt'].lower()))[:600] for tid,t in cat.items()}
 shingles={tid:{tuple(ts[i:i+5]) for i in range(len(ts)-4)} for tid,ts in tokens.items()}
 pairs=[];ids=sorted(cat)
 for i,a in enumerate(ids):
  for b in ids[i+1:]:
   aa,bb=shingles[a],shingles[b]
   if not aa or not bb or min(len(aa),len(bb))/max(len(aa),len(bb))<.9:continue
   score=len(aa&bb)/len(aa|bb)
   if score>=.9:union(a,b);pairs.append({'a':a,'b':b,'jaccard_5gram_first600_tokens':score})
 groups={tid:'source_'+h(find(tid))[:16] for tid in cat}
 pools={}
 pools['positive_control']=[tid for tid in trusted if not any(e['root_family_retrospective'] for e in ev[tid])]
 pools['flip_oldpass_newfail']=[tid for tid,t in tasks.items() if t['old_final_pass'] and t['new_original_final_status']!='PASS']
 pools['flip_oldfail_newpass']=[tid for tid,t in tasks.items() if not t['old_final_pass'] and t['new_original_final_status']=='PASS']
 pools['unresolved_exception']=[tid for tid in cat if any(e['repaired_status'] in ['RUNTIME_ERROR','TIME_LIMIT'] and not e['root_family_retrospective'] and e['E1_exact_code_label']!='VERIFIED_EVALUATION_PROBLEM' for e in ev[tid])]
 pools['unresolved_WA']=[tid for tid,t in tasks.items() if t['new_original_final_status']=='WRONG_ANSWER' and not any(e['stage']==ev[tid][-1]['stage'] and e['E1_exact_code_label'] in ['VERIFIED_EVALUATION_PROBLEM','VERIFIED_ALGORITHM_FAILURE'] for e in ev[tid])]
 quotas={'positive_control':8,'flip_oldpass_newfail':4,'flip_oldfail_newpass':4,'unresolved_exception':8,'unresolved_WA':24}
 selected=[];used=set();sampling=[]
 # Rare/control strata first. Balanced round-robin across nonempty dataset×difficulty cells.
 for layer,quota in quotas.items():
  cells=collections.defaultdict(list)
  for tid in pools[layer]:cells[cat[tid]['dataset']+'_'+cat[tid]['difficulty']].append(tid)
  for values in cells.values():values.sort(key=lambda tid:h('20261020|E3-S1|'+tid))
  ordered=[]
  while any(cells.values()):
   for cell in sorted(cells):
    if cells[cell]:ordered.append(cells[cell].pop(0))
  chosen=[]
  for tid in ordered:
   if len(chosen)==quota:break
   if groups[tid] in used:continue
   chosen.append(tid);used.add(groups[tid]);selected.append({'task_id':tid,'sampling_group':layer,'dataset':cat[tid]['dataset'],'difficulty':cat[tid]['difficulty'],'source_id':cat[tid]['source_id'],'provenance_group_id':groups[tid],'source_group_status':'conservative automated grouping; manual independence not certified','selection_hash':h('20261020|E3-S1|'+tid),'historical_programs':[{'stage':e['stage'],'code_sha256':e['code_sha256'],'old_status':'PASS' if e['old_passed'] else e['old_feedback'],'repaired_status':e['repaired_status'],'source_path':'../e3_s0_20261020/'+e['paths']['code']} for e in ev[tid]]})
  sampling.append({'stratum':layer,'requested':quota,'pool_tasks':len(pools[layer]),'selected':len(chosen),'ranked_pool':ordered})
 result={'status':'FROZEN_BEFORE_NEW_REPLAY','seed':20261020,'sampling':'SHA256(seed|E3-S1|task_id) within dataset-difficulty cell, round-robin sorted cells; priority control/flips/exception/WA; no post-review replacement','requested_tasks':48,'selected_tasks':len(selected),'selected_programs':sum(len(x['historical_programs']) for x in selected),'new_model_calls':0,'strata':sampling,'tasks':selected,'source_hashes':{str(p.relative_to(B)):sha(p) for p in [B/'repair_v2/catalog.json',B/'repair_v2/epochs/repaired_reports_20261020/task_results.json',B/'e3_s0_20261020/events.jsonl',B/'trusted_rgf_20261020/trusted_tasks.json']}}
 R.mkdir(parents=True,exist_ok=True)
 dest=R/'review_manifest.json'
 if dest.exists():assert read(dest)==result,'frozen manifest differs'
 else:dest.write_text(json.dumps(result,ensure_ascii=False,indent=2))
 (R/'provenance_groups.json').write_text(json.dumps({'task_groups':groups,'near_duplicate_pairs':pairs,'policy':'conservative approximation; not semantic independence certification'},indent=2))
 print('FROZEN',len(selected),'tasks',result['selected_programs'],'programs')
 for t in selected:print(t['sampling_group'],t['task_id'],t['difficulty'])
if __name__=='__main__':main()
