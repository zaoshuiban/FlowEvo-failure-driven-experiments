"""Post-Worker data-quality review, before any model experiment; shrink, never outcome-select replacements."""
import pathlib,json,hashlib,collections,shutil
P=pathlib.Path(__file__).parent
assert (P/'final_data_audit.json').exists()
def read(n):return json.loads((P/n).read_text())
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
archive=P/'pre_semantic_review';archive.mkdir(exist_ok=False)
for f in list(P.glob('*.json'))+list(P.glob('*.md')):shutil.copy2(f,archive/f.name)
rs=read('worker_results.json');original=read('selected_metadata.json');exclusions={}
for r in rs:
 if not r['human_reference_agreement'] and any(c['worker_status']=='OK' and not c['correct'] for x in r['references'] for c in x['result'].get('cases',[])):
  exclusions[r['id']]=['REFERENCE_OUTPUT_CONFLICT_PENDING_DIAGNOSIS']
nonunique=['apps-test-3839','cc-train-801ffd58e50305c7','cc-train-b210257b9e8ece3d','cc-train-3df0358e752df45f','apps-train-2069','apps-test-1834','apps-train-2083','apps-test-536','apps-test-55','apps-train-2022','apps-train-2047','cc-train-89a58b0402cddb86','apps-train-2009','apps-test-3873','cc-test-4fd84eac01f5ff05','apps-test-455','apps-test-3787','apps-test-3923','apps-test-1312','cc-train-04eaa556af206086','apps-train-2175','apps-train-2111','lcb-atcoder-abc363_f','lcb-atcoder-abc335_d']
for tid in nonunique:exclusions.setdefault(tid,[]).append('CONSTRUCTIVE_WITNESS_REQUIRES_SPECIAL_CHECKER')
for tid in ['apps-test-2030','cc-train-27e7242a0a4f9c31','cc-train-ae8fe56c3b602517']:exclusions.setdefault(tid,[]).append('EXPLICIT_NUMERIC_TOLERANCE_NOT_IMPLEMENTED')
for tid in ['apps-train-2150','apps-test-3709']:exclusions.setdefault(tid,[]).append('CASE_EQUIVALENCE_NOT_IMPLEMENTED_FOR_APPS')
exclusions.setdefault('cc-test-187271c60a4d6d9f',[]).append('INTERACTION_PROTOCOL_NOT_STDIO_TASK')
exclusions.setdefault('apps-test-925',[]).append('REQUIRED_DIGIT_DIAGRAM_MISSING')
allids={r['id'] for rows in original.values() for r in rows};assert set(exclusions)<=allids
review=[]
for tid,reasons in exclusions.items():
 t=read('candidates/'+tid+'.json');review.append(dict(id=tid,reasons=reasons,output_contract=t['output_contract'],question_sha256=t['question_sha256'],decision='QUARANTINE_C',basis='official task contract and reference execution; no target model outputs'))
write('semantic_quarantine.json',review)
write('reviewed_unique_exceptions.json',[dict(id=tid,decision='RETAIN',reason=why) for tid,why in [('lcb-atcoder-arc183_a','specified lexicographic median sequence uniquely determined'),('lcb-atcoder-abc370_c','lexicographically smallest minimum-length transformation array'),('apps-train-2122','deterministic earliest free repair schedule specified'),('cc-valid-83818a0a83a35cb8','p_k explicitly defined by modular sum; not constructive permutation'),('apps-test-3933','next term of integer arithmetic progression or last integer temperature'),('apps-train-2160','statement explicitly guarantees unique partition if exists'),('cc-train-28585ab72c77ac4d','output tiling only when unique; otherwise literal Not unique')]])
selected={k:[r for r in v if r['id'] not in exclusions] for k,v in original.items()};write('selected_metadata.json',selected)
for role in selected:
 for suffix,field in [('public_tasks','task_id'),('sealed_tasks','task_id'),('lineage','id')]:write(role+'_'+suffix+'.json',[r for r in read(role+'_'+suffix+'.json') if r[field] not in exclusions])
inv=read('inventory.json')
for r in inv:
 if r['id'] in exclusions:r['tier']='C';r['reasons']+=exclusions[r['id']]
write('inventory.json',inv)
write('worker_results_all_candidates.json',rs);kept=[r for r in rs if r['id'] not in exclusions];write('worker_results.json',kept)
a=read('acceptance_summary.json');a.update(tasks=len(kept),passed=sum(r['passed'] for r in kept),human_reference_agreement=sum(r['human_reference_agreement'] for r in kept),official_oracle_only=sum(not r['human_reference_agreement'] for r in kept),examined_candidates=len(rs),quarantined=len(exclusions),local_seconds=sum(r['positive_replay']['seconds']+r['negative']['seconds']+sum(x['result']['seconds'] for x in r['references']) for r in rs),data_revision='post-semantic-review-v1');write('acceptance_summary.json',a)
s=read('inventory_summary.json');s.update(tiers=dict(collections.Counter(r['tier'] for r in inv)),tier_difficulty=dict(collections.Counter(r['dataset']+':'+r['official_split']+':'+r['difficulty']+':'+r['tier'] for r in inv)),reasons_overlap=dict(collections.Counter(w for r in inv for w in r['reasons'])),selected={k:len(v) for k,v in selected.items()},quota_counts={k:dict(collections.Counter(r['quota'] for r in v)) for k,v in selected.items()});write('inventory_summary.json',s)
write('post_worker_admission.json',dict(initial_selection_sha256=hashlib.sha256((archive/'selected_metadata.json').read_bytes()).hexdigest(),final_selection_sha256=hashlib.sha256((P/'selected_metadata.json').read_bytes()).hexdigest(),initial_candidates=len(rs),retained=len(kept),quarantined=len(exclusions),selection_method='remove known scoring/statement ambiguity, keep relative order, no replacements, no target model selection',model_calls=0,worker_result_inheritance='final pool is a strict subset of the pre-Worker frozen candidates; immutable original Worker protocol and ledgers retained'))
print('FINAL SEMANTIC ADMISSION',s['selected'],'quarantined',len(exclusions))
