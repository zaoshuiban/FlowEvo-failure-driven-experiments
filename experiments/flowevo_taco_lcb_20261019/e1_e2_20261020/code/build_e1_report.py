import ast,collections,hashlib,json,pathlib,shutil
from review_notes import EVAL,RESCUE,UNKNOWN
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT.parent
ALG='VERIFIED_ALGORITHM_FAILURE';EV='VERIFIED_EVALUATION_PROBLEM';UNK='ROOT_CAUSE_UNKNOWN'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 sample=json.loads((ROOT/'sample_frozen.json').read_text());cat={x['task_id']:x for x in json.loads((BASE/'repair_v2/catalog.json').read_text())};proofs=json.loads((ROOT/'independent_evidence.json').read_text());cards=[]
 for x in sample['selected']:
  tid=x['task_id'];p=ROOT/'private_e1'/tid;v=json.loads((p/'replay.json').read_text());pre=json.loads((p/'preflight.json').read_text());old=json.loads((p/'history.json').read_text());source=(p/'original.py').read_text();syntax='OK'
  try:ast.parse(source)
  except SyntaxError as exc:syntax=str(exc)
  if tid in ['taco_0291','lcb_atcoder_abc399_e']:
   assert syntax!='OK';label=ALG;subtype='truncated_generation_compile_error';note='历史最终输出达到 32768 Token 上限，未闭合代码块被提取为含 Markdown 围栏的截断程序；对任意合法输入均编译失败。确证的是实现/工作流完整性缺陷，不是算法选择错误。'
  elif tid in UNKNOWN:label=UNK;subtype='evidence_insufficient';note=UNKNOWN[tid]
  elif tid in RESCUE:label=EV;subtype,note=RESCUE[tid]
  elif tid.replace('taco_', '', 1) in EVAL:label=EV;subtype,note=EVAL[tid.replace('taco_', '', 1)]
  elif x['sampling_group']=='rescued_pass' and pre['invalid_cases']:
   label=EV;subtype='invalid_input';note='预审发现显式输入契约违例，具体非法索引、输入摘要和规则见 preflight.json；原始旧失败重放的反馈另附。新 PASS 仅覆盖剩余测试，不能证明程序全域正确。'
  else:raise RuntimeError('Missing review '+tid)
  trace=BASE/'audit/audit_20261020'/('trace_'+tid+'.json')
  if not trace.exists():trace=BASE/'audit/audit_20261020'/(tid+'.json')
  if trace.exists():shutil.copyfile(trace,p/'old_evaluator_trace.json')
  (p/'statement.txt').write_text(cat[tid]['prompt'])
  files={f.name:sha(f) for f in p.iterdir() if f.is_file() and f.suffix in ['.json','.py','.txt'] and f.name!='card.json'}
  card={**x,'label':label,'root_subtype':subtype,'finding':note,'static_syntax':syntax,'independent_evidence':proofs.get(tid),'review_scope':'task statement, original final code, test/expected contract, replay actual output/exception, old feedback and full candidate history; unknown retained where evidence insufficient','candidate_universally_correct':None,'program_defect_excluded':False,'new_status_observed':v['status'],'source_code_sha256':sha(p/'original.py'),'task_sha256':v['original_task_sha256'],'evidence_file_hashes':files,'reproduction':f'cd /opt/flowevo-benchmark-20261019 && venv/bin/python repair_v2d_20261020/code/adapter.py --task data/tasks/{tid}.json --candidate e1_e2_20261020/private_e1/{tid}/original.py --policies repair_v2d_20261020/policies.json --out /tmp/e1_{tid}.json','root_cause_certainty':'confirmed specific defect' if label!=UNK else 'insufficient independent evidence'}
  (p/'card.json').write_text(json.dumps(card,ensure_ascii=False,indent=2)+'\n')
  text=f"# {tid}\n\n抽样层：{x['sampling_group']} / {x['dataset']} / {x['difficulty']} / {x['family']}\n\n分类：`{label}`\n\n根因：{subtype}\n\n{note}\n\n原程序 SHA256：{card['source_code_sha256']}\n\n独立证据：{json.dumps(card['independent_evidence'],ensure_ascii=False)}\n\n原程序：[original.py](original.py)；题面：[statement.txt](statement.txt)；原历史：[history.json](history.json)；新重放：[replay.json](replay.json)；输入预审：[preflight.json](preflight.json)。隐藏失败输入及完整实际输出保存在本题 private 文件，不得进入 E2 提示。\n\n复现：\n```sh\n{card['reproduction']}\n```\n\n此分类只确证记录中的具体缺陷，不证明候选程序在所有合法输入上正确，也不排除并存的其他缺陷。\n"
  (p/'证据卡.md').write_text(text);cards.append(card)
 counts=collections.Counter(c['label'] for c in cards);group={g:dict(collections.Counter(c['label'] for c in cards if c['sampling_group']==g)) for g in sample['frames']};sub=collections.Counter(c['root_subtype'] for c in cards)
 summary={'tasks':len(cards),'counts':dict(counts),'percent_of_reviewed_tasks':{k:100*v/93 for k,v in counts.items()},'by_sampling_group':group,'root_subtype_counts':dict(sub),'new_model_calls':0,'note':'93-task stratified sample, not a simple random population estimate; confirmed evaluation defects do not certify algorithm correctness. Family tags are coarse prompt keyword strata. Small cells can receive zero quota.'}
 (ROOT/'e1_cards.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2)+'\n');(ROOT/'e1_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':build()
