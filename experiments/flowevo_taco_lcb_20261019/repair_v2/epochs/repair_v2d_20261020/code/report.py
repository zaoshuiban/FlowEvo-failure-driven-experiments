import argparse,collections,csv,datetime,hashlib,json,pathlib

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--primary',type=pathlib.Path,required=True);p.add_argument('--supplement',type=pathlib.Path,required=True);p.add_argument('--additional',type=pathlib.Path,nargs='*',default=[]);p.add_argument('--out',type=pathlib.Path,required=True);args=p.parse_args();args.out.mkdir(exist_ok=True,parents=True)
 files=sorted(args.primary.glob('tasks/*.json'));rows=[];verdicts=[];cases=[];transitions=[];unresolved=[];timing=[]
 for f in files:
  base=json.loads(f.read_text());tid=base['task_id'];folder=args.primary
  for candidate in [args.supplement,*args.additional]:
   if (candidate/'tasks'/f.name).exists():folder=candidate
  r=json.loads((folder/'tasks'/f.name).read_text());r['evaluation_epoch']=folder.name
  r['timing_unstable']=base['new_original_final_status']!=r['new_original_final_status'] and 'TIME_LIMIT' in [base['new_original_final_status'],r['new_original_final_status']]
  if r['timing_unstable']:timing.append(tid)
  r['reported_final_status']='TIMING_UNSTABLE' if r['timing_unstable'] else r['new_original_final_status']
  rows.append(r)
  pre=json.loads((folder/'preflight'/f.name).read_text())
  for kind in ['invalid_cases','reference_issues','reference_corrections']:
   for entry in pre.get(kind,[]):cases.append({'task_id':tid,'kind':kind,'epoch':folder.name,**entry})
  for vf in sorted((folder/'verdicts'/tid).glob('*.json')):
   v=json.loads(vf.read_text());v['epoch']=folder.name;verdicts.append(v)
  if r['old_final_pass']!=(r['reported_final_status']=='PASS'):transitions.append(r)
  if r['reported_final_status'] in ['CHECKER_UNSUPPORTED','PROTOCOL_UNSUPPORTED','NO_VALID_TESTS','REFERENCE_DISPUTE','EVALUATOR_ERROR','TIMING_UNSTABLE']:unresolved.append(r)
 assert len(rows)==800,len(rows)
 assert sum(r['attempts'] for r in rows)==len(verdicts)==2132
 def aggregate(a):
  statuses=collections.Counter(r['reported_final_status'] for r in a);scorable=sum(statuses[k] for k in ['PASS','WRONG_ANSWER','TIME_LIMIT','RUNTIME_ERROR','COMPILE_ERROR','NO_COMPLETE_CODE','OUTPUT_LIMIT'])
  return {'tasks':len(a),'old_first_pass':sum(r['old_first_pass'] for r in a),'old_final_pass':sum(r['old_final_pass'] for r in a),'new_first_pass':sum(r['new_first_status']=='PASS' for r in a),'new_original_final_pass':statuses['PASS'],'any_saved_candidate_pass':sum(r['any_saved_candidate_pass'] and not r['timing_unstable'] for r in a),'statuses':dict(statuses),'scorable_tasks':scorable,'diagnostic_final_rate_among_scorable':statuses['PASS']/scorable if scorable else None,'pass_with_excluded_invalid_tests':sum(r['reported_final_status']=='PASS' and r['invalid_cases']>0 for r in a),'task_specific_input_checks':sum(r['input_coverage']=='task_specific_checks' for r in a),'structural_signature_only':sum(r['input_coverage']=='structural_and_signature_only' for r in a)}
 summary={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_model_calls':0,'tasks':800,'candidates':2132,'overall':aggregate(rows),'datasets':{ds:aggregate([r for r in rows if r['dataset']==ds]) for ds in ['taco','lcb']},'difficulty_groups':{ds+'_'+d:aggregate([r for r in rows if r['dataset']==ds and r['difficulty']==d]) for ds,d in sorted({(r['dataset'],r['difficulty']) for r in rows})},'candidate_statuses':dict(collections.Counter(v['status'] for v in verdicts)),'invalid_test_cases':sum(c['kind']=='invalid_cases' for c in cases),'corrected_reference_cases':sum(c['kind']=='reference_corrections' for c in cases),'reference_issues':sum(c['kind']=='reference_issues' for c in cases),'tasks_with_invalid_tests':sum(r['invalid_cases']>0 for r in rows),'tasks_with_reference_corrections':sum(r['reference_corrections']>0 for r in rows),'old_fail_to_new_pass':sum(not r['old_final_pass'] and r['reported_final_status']=='PASS' for r in rows),'old_pass_to_new_nonpass':sum(r['old_final_pass'] and r['reported_final_status']!='PASS' for r in rows),'timing_unstable_tasks':timing}
 for name,obj in [('summary.json',summary),('task_results.json',rows),('candidate_results.json',verdicts),('test_quality_findings.json',cases),('unresolved.json',unresolved),('transitions.json',transitions)]: (args.out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
 for name,data in [('task_results.csv',rows),('transitions.csv',transitions),('unresolved.csv',unresolved)]:
  if not data:continue
  keys=sorted({k for r in data for k in r})
  with (args.out/name).open('w',encoding='utf-8-sig',newline='') as stream:
   w=csv.DictWriter(stream,fieldnames=keys);w.writeheader();w.writerows(data)
 inventory=json.loads((args.primary/'frozen_inventory.json').read_text());changed=[];task_hashes={}
 for item in inventory:
  paths=list(args.source.glob('runs/*/'+item['task_id']+'/result.json'));assert len(paths)==1;parent=paths[0].parent
  for suffix,key in [('.py','code_sha256'),('.response.json','response_sha256'),('.verdict.json','old_verdict_sha256')]:
   f=parent/(item['stage']+suffix)
   if hashlib.sha256(f.read_bytes()).hexdigest()!=item[key]:changed.append(str(f))
  task_hashes[item['task_id']]=item['task_sha256']
 for tid,expected in task_hashes.items():
  f=args.source/'data/tasks'/(tid+'.json')
  if hashlib.sha256(f.read_bytes()).hexdigest()!=expected:changed.append(str(f))
 assert not changed,changed
 (args.out/'integrity.json').write_text(json.dumps({'tasks_checked':len(task_hashes),'candidate_records_checked':len(inventory),'source_files_changed':changed,'new_model_calls':0},indent=2))
 text=['# 全部800题评测修复与离线重评','','本报告覆盖全部800题、2132个已保存候选，新增模型调用0。保留旧数据、响应、代码与判分哈希，未改写历史结果。','', '| 数据集 | 题数 | 旧最终通过 | 新规则原最终程序通过 | 可判分题数 | 已保存候选任一通过 |','|---|---:|---:|---:|---:|---:|']
 for ds,a in summary['datasets'].items():text.append(f"| {ds} | {a['tasks']} | {a['old_final_pass']} | {a['new_original_final_pass']} | {a['scorable_tasks']} | {a['any_saved_candidate_pass']} |")
 text+=['','这些是旧生成轨迹在修复规则下的离线诊断，不能等同于修复反馈后重新运行FlowEvo的成功率。原先通过的题也已检查，转移详见transitions.csv。','', '## 计分口径与未完成覆盖','', '整数保持精确比较；25题使用经题面登记的浮点容差；标准输出按有序token比较空白；函数返回值按显式包裹规则和递归类型比较。多解按任务约束及最优性判定，未实现可靠checker的题标记CHECKER_UNSUPPORTED。', '', '非法输入依据已登记的结构/范围/图/字符串规则隔离，保留索引、规则与输入哈希；参考值仅在独立证明的oracle下更正。不得把“隔离后通过”说成原测试全部通过。', '', f"发现非法测试 {summary['invalid_test_cases']} 条，涉及 {summary['tasks_with_invalid_tests']} 题；独立修正参考输出 {summary['corrected_reference_cases']} 条，涉及 {summary['tasks_with_reference_corrections']} 题。",'', '最终状态：`'+json.dumps(summary['overall']['statuses'],ensure_ascii=False)+'`。', '', f"输入契约覆盖：{summary['overall']['task_specific_input_checks']}题有专项检查，其余{summary['overall']['structural_signature_only']}题仅有通用结构/签名检查，不能据此宣称全部测试语义合法。",'', '无法可靠判分的题及计时变化单列unresolved.csv；不静默从800题中删除。可判分分母上的比率仅作诊断，输入/参考仍有上述覆盖限制。','', '## 执行与反馈修复','', '标准输入题在隔离进程中以真实文件描述符执行，支持buffer及连续readline；函数题使用指定入口并保留调用间状态。候选命名空间仅挂载程序、worker和运行时，不挂载题目/标准答案JSON。', '', 'TACO与LCB错误码分别解析；语法、运行、超时、框架错误分开。保留诊断异常，发送给求解器的反馈由白名单生成，不包含隐藏输入/标准输出。新入口为code/adapter.py，历史benchmark.py保持原样供复现，不会自动把旧响应当作新反馈后的重跑。', '', '## 版本与复现','', 'primary是全量冻结版本；supplement仅覆盖后续补齐checker或顺序复核的任务。task_results.csv记录每题实际epoch，两个run_manifest.json保留代码及规则哈希。', '', '修复有确定性正反例测试、服务分组/分堆最优性的小规模穷举，以及真实I/O、EOF、大输出、异常、超时和答案文件隔离的Linux集成测试。测试日志随两个epoch保存。', '', '本地交付目录保留reports、epochs、policies及代码；服务器原实验目录保留完整输入与生成轨迹。恢复离线评分必须使用同一epoch的代码与规则；新版入口拒绝混用旧缓存。']
 (args.out/'修复与全量重评报告.md').write_text('\n'.join(text)+'\n')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
