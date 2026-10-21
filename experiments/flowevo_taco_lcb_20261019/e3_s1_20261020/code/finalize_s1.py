import pathlib,json,hashlib,collections,ast,csv,time,sys,shutil
W=pathlib.Path.cwd();R=W/'experiments/flowevo_taco_lcb_20261019/e3_s1_20261020'
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(R/'review_manifest.json');suite=read(R/'public_suite.json')['cases'];legacy=read(R/'legacy_failure_evidence.json');rows=[];counts=collections.Counter()
for t in m['tasks']:
 tid=t['task_id'];d=R/'review_cards'/tid;d.mkdir(parents=True,exist_ok=True);task=read(R/'source/tasks'/(tid+'.json'))
 (d/'statement.md').write_text(task.get('prompt',task.get('question',json.dumps(task,ensure_ascii=False))))
 programs=[]
 for a in t['historical_programs']:
  src=(R/a['source_path']).resolve();assert sha(src)==a['code_sha256'];shutil.copy2(src,d/(a['stage']+'.py'))
  v=read(R/'verdicts'/tid/(a['stage']+'.json'));sp=R/'stress_verdicts_v2'/tid/(a['stage']+'.json');stress=read(sp) if sp.exists() else None
  status=stress['status'] if stress and stress['status']!='PASS' else v['status'];counts[status]+=1
  try:tree=ast.parse(src.read_text());features=collections.Counter(type(n).__name__ for n in ast.walk(tree))
  except SyntaxError:features={'syntax_error':1}
  programs.append({**a,'combined_status':status,'base_verdict':v,'stress_v2_verdict':stress,'ast_features':dict(features),'legal_counterexample': 'counterfactuals/taco_0966/legal_case.json' if tid=='taco_0966' and a['stage']=='l1' else None,'minimal_patch':'counterfactuals/taco_0966/minimal.diff' if tid=='taco_0966' and a['stage']=='l1' else None})
 packets=[x for x in legacy if x['task_id']==tid];evaln=sum(x['classification']=='VERIFIED_EVALUATION_PROBLEM' for x in packets)
 classification='VERIFIED_ALGORITHM_FAILURE' if tid=='taco_0966' else 'ARTIFACT_FAILURE' if all(x['combined_status'] in ['NO_COMPLETE_CODE','COMPILE_ERROR'] for x in programs) else 'VERIFIED_EVALUATION_PROBLEM' if evaln else 'ROOT_CAUSE_UNKNOWN'
 result={**t,'classification':classification,'classification_scope':'functional defect in l1 only' if tid=='taco_0966' else 'specific legacy candidate/case packets only; not all failures of this task' if evaln else 'finite probe evidence; full-domain root cause not established','public_case_count':len(suite[tid]),'oracle_evidence':'public_suite.json and code/legal_suite.py; prior cases preserve prior_case provenance','programs':programs,'legacy_case_evidence':packets,'evaluation_counterfactual':'Use statement-valid inputs and independently calculated or semantic expected results; retain original bad cases for audit' if evaln else None,'limitations':['Finite PASS does not prove program correctness.','No failed input or patch fabricated for unconfirmed causes.']+(['Scraped statement has contradictory relation symbols; legal probes conditional on restored interpretation.'] if tid=='taco_0445' else [])}
 write(d/'review.json',result);(d/'review.md').write_text('# '+tid+'\n\n结论：`'+classification+'`。适用范围：'+result['classification_scope']+'。\n\n公开基础用例 '+str(len(suite[tid]))+' 个；历史程序 '+str(len(programs))+' 份。逐程序结果、原始程序、错误输出与旧评测用例证据见同目录 review.json。有限测试通过不等于全域正确；未确证项保留未知。\n')
 rows.append({'task_id':tid,'stratum':t['sampling_group'],'dataset':t['dataset'],'difficulty':t['difficulty'],'programs':len(programs),'public_cases':len(suite[tid]),'classification':classification,'verified_legacy_case_packets':evaln,'statuses':dict(collections.Counter(x['combined_status'] for x in programs))})
write(R/'逐题审查表.json',rows)
with (R/'逐题审查表.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
sys.path.insert(0,str(W/'FlowEvo/src'));from failure_evo.evidence import MechanismStore,REQUIRED_FILES
cf=R/'counterfactuals/taco_0966';names={'original_code':'original.py','patched_code':'patched.py','minimal_patch':'minimal.diff'};files={k:{'path':str((cf/names.get(k,k+'.json')).relative_to(R)),'sha256':sha(cf/names.get(k,k+'.json'))} for k in REQUIRED_FILES}
store=MechanismStore(R/'mechanism_evidence.jsonl');mid='multi_case_parser_cursor_prepass_desynchronization';t=next(x for x in m['tasks'] if x['task_id']=='taco_0966');at=time.time()
if not store.events.records():store.certify({'witness_id':'s1_taco0966_l1_public_multicase','mechanism_id':mid,'problem_id':'taco_0966','provenance_group_id':t['provenance_group_id'],'provenance_reviewed':False,'synthetic':False,'purpose':'HISTORICAL_FUNCTIONAL_FAILURE','observed_at':(cf/'original_run.json').stat().st_mtime,'code_sha256':sha(cf/'original.py'),'files':files},at)
try:store.publish(mid,time.time());raise AssertionError('must reject')
except ValueError as e:reason=str(e)
write(R/'mechanisms_verified.json',{'verified_current_singletons':[{'mechanism_id':mid,'support':store.supports(mid,time.time())}],'cross_task_supported':[],'headroom_ready':[],'active_operators':0,'publish_rejection':reason,'decision':'STOP_BEFORE_S2','prior_context_singletons':['abc301_f factorial capacity','taco_0875 recursion depth'],'prior_context_counts_as_current_support':False})
checks={}
for fn in ['replay_frozen.json','stress_frozen_v2.json']:
 obj=read(R/fn)
 if 'hashes' in obj:checks[fn]=all(sha(R/k)==v for k,v in obj['hashes'].items())
 else:checks[fn]=sha(R/'stress_suite_v2.json')==obj['suite_sha256'] and sha(R/'code/stress_checks_v2.py')==obj['code_sha256'] and sha(R/'review_manifest.json')==obj['sampling_manifest_sha256']
assert all(checks.values());assert len(rows)==48 and sum(x['programs'] for x in rows)==224
write(R/'exclusions.json',{'stress_v1':{'files':['stress_summary.json','stress_verdicts','stress_suite.json','stress_frozen.json'],'status':'REJECTED_DRAFT','reason':'float outputs compared as tokens for taco_0543 produced five false WA; only stress_v2 authoritative'},'synthetic_engineering_fixtures_excluded_from_mechanisms':True})
summary={'status':'S1_OFFLINE_COMPLETE','tasks':48,'historical_programs':224,'base_public_inputs':sum(map(len,suite.values())),'combined_program_status':dict(counts),'task_primary_labels':dict(collections.Counter(x['classification'] for x in rows)),'legacy_packets':dict(collections.Counter(x['classification'] for x in legacy)),'new_verified_functional_failures':1,'counterfactual_validation_cases':99,'new_model_calls':0,'new_model_tokens':0,'next_stage':'STOP_BEFORE_S2','integrity':checks,'server_final_sync':'See delivery_verification.json on each host','unavailable_local_server_results':[],'scoring_validation':read(R/'scoring_validation.json')['status'],'prior_multicase_counts':read(R/'prior_multicase_results.json')['status_counts'],'provider':'injectable interface; no live API backend configured'}
write(R/'summary.json',summary)
impl={str(p.relative_to(W)):sha(p) for p in (W/'FlowEvo/src/failure_evo').glob('*.py')};impl.update({str(p.relative_to(W)):sha(p) for p in [W/'FlowEvo/tests/test_failure_evo.py',W/'FlowEvo/benchmark_failure_evo.py']});write(R/'implementation_manifest.json',impl)
report='''# E3-S1 离线实施报告

S1 已完成本地机制实现与冻结样本复核；不进入 S2。新增模型调用 0 次，新增模型 Token 0。

冻结 48 题、224 份历史程序：持续 WA 24 题、运行异常 8 题、评分翻转 8 题、对照 8 题。公开基础测试 2,222 个输入，运行 8,922 次；另有 24 题、36 个边界测试，运行 155 次。逐题原始程序、哈希、运行结果与证据在 review_cards，汇总见逐题审查表。

综合基础和有效边界测试：205 份有限测试 PASS、16 份无完整代码、2 份编译错误、1 份运行异常。有限测试 PASS 不能解释为全域正确，也不能用来重新估计 800 题成功率。旧案例形成 184 个程序—用例审查包：128 个明确评测/数据问题，56 个未知；这些标签只适用于对应案例。非法/歧义输入统计不应全部解释成严格非法输入。

## 新确证的功能缺陷

taco_0966 的 l1 在处理多组输入时，废弃的预解析循环没有消费 X，把 X 当成下一组 N，触发 IndexError。独立公开最小输入及原始 traceback 保存在 counterfactuals/taco_0966。删除这个废弃循环后，同一反例和其余公开测试合计 99 个通过，另检查了 2 个原程序可通过的相邻案例。该修复仅保存在反事实程序中，没有改写历史候选。

这是一个题目的实现缺陷，尚非跨题稳定机制。固定历史响应的干净基线在 l2a 已恢复该题，因此不能宣称 l3 算子能提高系统成功率。

## 系统实现与验收

新增 failure_evo 模块包括公开/私有信息投影、带时间与哈希链的证据库、跨题机制准入、版本失效、类型化修复接口、单算子路由、预算与回退、候选保留、沙箱插件执行。历史 benchmark 与原 vendor 源码保持不变。

55 项单元验收、48 题固定历史响应策略回放、3 项 Linux 沙箱验收通过。策略回放只验证给定保存响应时的执行政策，不是新生成效果或反馈因果实验。当前生成接口可注入 provider，未配置真实 API 后端。错误程序工程夹具与单元测试均不计入机制支持。

## 可信性与停止决定

首轮压力测试对浮点输出使用了错误的逐 token 比较，产生 5 个假 WA；整版已隔离为 REJECTED_DRAFT，结论仅使用修正后的 v2。taco_0445 抓取题面符号存在冲突，其测试依赖修复解释，不能据此确证算法失败。复杂度、资源校准及未覆盖合法域仍有未知。

当前只有 1 个确证任务，来源独立性尚未人工认证；未达到至少 3 个不同原题、2 个经审核来源组的发布门槛，headroom 实验也未开展。机制发布被实际准入检查拒绝，活跃算子为 0。下一步应扩大独立合法反例审查，先补齐跨题证据，再决定是否进入 S2；不启动付费实验。

服务器恢复后，已取回评分正负对照：48 题均有正向一致性见证，48 份故意错误夹具全部被拒绝，额外执行 137 次。abc399_e 的正向程序来自既有 E2 参考程序，不属于本次 224 份历史候选，也不是新增生成。另对 5 题的 21 份程序补查多测：18 PASS、3 无完整代码，未新增功能缺陷。评分夹具不计入机制支持。最终同步与完整性结果见 delivery_verification.json。
'''
(R/'E3-S1报告.md').write_text(report)
print(json.dumps(summary,ensure_ascii=False,indent=2))
