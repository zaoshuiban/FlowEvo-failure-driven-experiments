import pathlib,json,hashlib,collections,time
P=pathlib.Path(__file__).parent
while not (P/'README.md').exists():time.sleep(20)
def read(n):return json.loads((P/n).read_text())
def write(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def norm(s):return ' '.join(s.split())
inv=read('inventory.json');sel=read('selected_metadata.json');w=read('worker_results.json');issues=[];ids=[];comps=[];checks=[]
for role,meta in sel.items():
 public={t['task_id']:t for t in read(role+'_public_tasks.json')};sealed={t['task_id']:t for t in read(role+'_sealed_tasks.json')}
 assert list(public)==[r['id'] for r in meta]
 for r in meta:
  tid=r['id'];ids.append(tid);comps.append(r['component']);a=public[tid]['public_cases'];b=sealed[tid]['cases'];assert len(a)>=2 and len(b)>=6
  assert not ({norm(x['input']) for x in a}&{norm(x['input']) for x in b})
  assert not r['component_exposed']
  assert 'references' not in public[tid] and 'sealed_cases' not in public[tid]
  checks.append({'id':tid,'role':role,'online':len(a),'sealed':len(b),'passed':True})
assert len(ids)==len(set(ids))==len(set(comps));assert set(ids)=={x['id'] for x in w};assert all(x['passed'] for x in w)
assert all(x['budget']['calls']==0 and not x['budget']['unknown_or_pending_requests'] for x in w)
counts={}
for ds in ['apps','cc','lcb']:
 rows=[r for r in inv if r['dataset']==ds];standard=[r for r in rows if r['tier']=='B_STANDARD']
 counts[ds]={'all':len(rows),'B_standard':len(standard),'B_standard_fewer_than_two_parsable_refs':sum(r['reference_count']<2 for r in standard),'B_standard_fewer_than_24_total_tests':sum(r['online_count']+r['sealed_count']<24 for r in standard),'selected':sum(r['dataset']==ds for v in sel.values() for r in v)}
write('policy_ablation.json',counts);write('final_data_audit.json',dict(passed=True,tasks=len(ids),role_overlap=0,component_overlap=0,online_sealed_overlap=0,new_model_requests=0,checks=checks))
with (P/'S20_External_v2_Data_Inventory.md').open('a') as f:
 f.write('\n## 取消统一两参考与24测试门槛的实际影响\n\n| 来源 | 标准B | 其中少于两份可解析参考 | 其中总测试少于24 |\n| --- | ---: | ---: | ---: |\n')
 for ds,c in counts.items():f.write(f"| {ds} | {c['B_standard']} | {c['B_standard_fewer_than_two_parsable_refs']} | {c['B_standard_fewer_than_24_total_tests']} |\n")
 f.write('\n两个条件可能重叠，不能相加；这是新全量池上的门槛消融，不是重写旧60题筛查结论。最终任务级身份、组件和在线/封存输入交叉审计均通过，见final_data_audit.json。\n')
m=read('freeze_manifest.json')
for p in list(P.glob('*.md'))+[P/'policy_ablation.json',P/'final_data_audit.json']:
 m['files'][str(p.resolve().relative_to(P.resolve().parents[1]))]=hashlib.sha256(p.read_bytes()).hexdigest()
write('freeze_manifest.json',m)
print('FINAL AUDIT PASSED',len(ids),flush=True)
