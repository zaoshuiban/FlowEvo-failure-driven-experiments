"""Read-only aggregation of the frozen experiment and provider evidence."""
import collections, hashlib, json, math, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'runs/s13_compare30_20261022_01'
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def wilson(k,n):
 z=1.96;mid=(k/n+z*z/(2*n))/(1+z*z/n);half=z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/(1+z*z/n);return [mid-half,mid+half]
p=read(R/'protocol.json');d=read(R/'results.json');rows=d['rows'];tasks=read(R/'tasks.json');arms=p['arms'];summary={};pair={};unknown=[];requests=[]
for f in (R/'branches').glob('*/*/requests.json'):
 for i,r in enumerate(read(f)):
  requests.append(r)
  if r.get('status')!='COMPLETED':unknown.append(str(f.relative_to(R))+':'+str(i+1))
for a in arms:
 rr=[x for x in rows if x['arm']==a];n=len(rr);k=sum(x['audit_pass'] for x in rr)
 summary[a]=dict(completed=n,passed=k,pass_rate=k/n if n else None,descriptive_wilson_95=wilson(k,n) if n else None,model_calls=sum(x['model_calls'] for x in rr),input_tokens=sum(x['input_tokens'] for x in rr),output_tokens=sum(x['output_tokens'] for x in rr),estimated_usd=sum(x['estimated_usd'] for x in rr),online_seconds=sum(x['online_seconds'] for x in rr),median_online_seconds=statistics.median(x['online_seconds'] for x in rr) if rr else None,online_tool_calls=sum(x['online_tool_calls'] for x in rr),audit_seconds=sum(x['audit_seconds'] for x in rr),operator_hook_events=sum(x['operator_calls'] for x in rr),dataset={ds:dict(n=sum(x['dataset']==ds for x in rr),passed=sum(x['audit_pass'] and x['dataset']==ds for x in rr)) for ds in ['taco','lcb']})
bytask={t['task_id']:{x['arm']:x for x in rows if x['task_id']==t['task_id']} for t in tasks}
for a,b in [('FlowEvo','AFlow'),('FlowEvo','FailureLearning'),('AFlow','FailureLearning')]:
 both=[v for v in bytask.values() if a in v and b in v];aw=sum(v[a]['audit_pass'] and not v[b]['audit_pass'] for v in both);bw=sum(v[b]['audit_pass'] and not v[a]['audit_pass'] for v in both);n=aw+bw
 pair[a+' vs '+b]=dict(n=len(both),a_only=aw,b_only=bw,both_pass=sum(v[a]['audit_pass'] and v[b]['audit_pass'] for v in both),both_fail=sum(not v[a]['audit_pass'] and not v[b]['audit_pass'] for v in both),exploratory_exact_mcnemar_p=min(1,2*sum(math.comb(n,i) for i in range(min(aw,bw)+1))/2**n) if n else 1)
facts=[]
if (R/'failure_evidence.jsonl').exists():facts=[json.loads(x) for x in (R/'failure_evidence.jsonl').read_text().splitlines()]
factcounts=dict(collections.Counter(x['kind'] for x in facts));queries=read(R/'registry_queries.json') if (R/'registry_queries.json').exists() else []
agg=dict(status=d['status'],summary=summary,pairs=pair,provider_requests=len(requests),known_usage_responses=sum(r.get('status')=='COMPLETED' for r in requests),unknown_requests=unknown,returned_models=dict(collections.Counter(r.get('model','UNKNOWN') for r in requests)),finish_reasons={},failure_events=factcounts,registry_queries=len(queries),eligible_operator_counts=[q['eligible_operator_count'] for q in queries],budget=d['budget'])
finish=[]
for f in (R/'branches').glob('*/*/response_*.json'):
 rr=read(f);finish.extend(c.get('finish_reason','unknown') for c in rr.get('choices',[]))
agg['finish_reasons']=dict(collections.Counter(finish));write(R/'summary.json',agg)
complete=d['status']=='COMPLETE' and len(rows)==90
lines=['# 30题三组开发性对比实验报告','',f"运行：`{R.name}`。状态：**{d['status']}**，已完成 {len(rows)}/90 个分支。",'', '## 结论与范围','', '本实验比较统一公开反馈下的 FlowEvo、适配版 AFlow 和当前失败学习版，记录真实模型请求、隔离执行及算子调用。采用已有评分审查材料中的 24 道 TACO、6 道 LiveCodeBench；全部标记为既有开发材料，不作为未见泛化评测。','', '**当前没有获得安全使用权限的算子。失败学习版启用了实际注册表查询、候选记录和失败证据写入，但生成预算为 0；这是当前可运行系统的对比，不是完整在线自动学习机制的效果实验。**','', '## 主要结果','', '| 组别 | 离线复核全通过 | TACO | LCB | 模型请求 | 输入/输出Token | 估算API费用 | 在线工具调用 | 中位在线时间 |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for a,s in summary.items():
 ds=s['dataset'];lines.append(f"| {a} | {s['passed']}/{s['completed']} | {ds['taco']['passed']}/{ds['taco']['n']} | {ds['lcb']['passed']}/{ds['lcb']['n']} | {s['model_calls']} | {s['input_tokens']:,} / {s['output_tokens']:,} | ${s['estimated_usd']:.6f} | {s['online_tool_calls']} | {s['median_online_seconds'] or 0:.2f}s |")
lines+=['','离线复核全通过要求最终锁定程序通过全部该题冻结复核输入。它不是官方完整隐藏测试通过率，也不是复杂度或全输入域正确性的证明。各题最多24个复核输入，全部在锁定程序后评分。','', '## 协议与公平性','', '- 抽样：以固定字符串 `compare30-20261022` 的 SHA256 排序，从审查过的题池选题。TACO难度 EASY/MEDIUM/MEDIUM_HARD/HARD/VERY_HARD 分别5/5/5/5/4题；LCB 5道hard、1道medium。排除已用于容量算子生成的 abc301_f 和有题面歧义的 taco_0445。抽样受既有可审查材料限制，不能代表两个完整数据集。','- 每题冻结3个合法公开检查，其余去重后最多24个输入用于离线复核。原题公开样例仍保留在题面；新增公开检查对三组一致。题单和角色分割在任何新模型请求前冻结。既有复核材料此前参与过项目开发，不称作独立封存新测试。','- 同一实际模型别名 `deepseek-flash`，关闭thinking，单次输出4096 Token，输入保守上界32768 Token。保留原FlowEvo阶段温度；AFlow使用其适配器温度0。供应商不保证相同提示完全确定，未强行复用任何一组的模型响应。','- 每分支共同上限8次请求、294912 Token、600秒；FlowEvo天然最多5阶段，AFlow天然最多8请求。比较原生流程成本，不强迫所有组消耗相同请求数。三组轮换先后顺序。','- FlowEvo与失败学习版沿用相同NativeBenchmarkSession/Controller，按公开测试提前停止，每个组、数据集和难度维护独立成功程序库。l3/l4可检索此前公开通过的解答，不使用离线复核结果决定是否入库。','- AFlow使用本地归档官方MBPP round14：三次生成→集成选择→公开测试/反思→必要时最终修复。保留原控制图，仅适配模型传输、任务接口和安全执行边界。这不是对TACO/LCB重新搜索出的最佳图，也不是原论文MetaGPT环境的复现。','- FlowEvo最终使用公开通过程序，否则使用最后候选；AFlow只接受控制图正式返回的最终源码，错误时不将中间候选冒充结果。任何分支都不能依据离线得分重选。','', '## 评分与隔离证据','', f"运行前30道题的历史正例和错误测试程序均通过评分器验收，共 {sum(x['positive']['tests_run']+x['negative']['tests_run'] for x in read(R/'scoring_acceptance.json')['rows'])} 次隔离输入测试。正例一致性不是独立参考的正确性证明；参考规则继承既有题面推导审查。特殊题使用浮点容差、合法拓扑序、构造有效性等相应检查器，不将所有输出都作字符串相等比较。",'', '未知源码仅在已经完成12项隔离验收的本地Linux Docker Worker中执行。使用冻结镜像和Worker哈希、无网络、只读挂载、非root、权限清空、进程/内存/CPU限制和单例5秒超时。期望答案留在宿主评分器，不挂载到容器。','', '## 失败学习版的实际活动','',f"- 冻结注册表中有 {len(read(R/'operator_inventory.json'))} 个版本，权限均为 Shadow 或 Suspended；未更改旧版本权限。",f"- 实际任务边界注册表查询：{len(queries)}；可用算子数量：{sorted(set(q['eligible_operator_count'] for q in queries))}。",f"- 失败事件统计：`{json.dumps(factcounts,ensure_ascii=False)}`。",f"- 算子Hook执行事件：{summary['FailureLearning']['operator_hook_events']}；新算子生成请求：0；新生代授权：0。",'- 因无算子实际介入，失败学习组与FlowEvo的差异只能描述为本次独立模型运行差异及记录开销，不能作为Operator增益或在线学习成功的证据。','', '## 配对结果','', '| 对比（A vs B） | A独有通过 | B独有通过 | 同时通过 | 同时失败 |','|---|---:|---:|---:|---:|']
for k,v in pair.items():lines.append(f"| {k} | {v['a_only']} | {v['b_only']} | {v['both_pass']} | {v['both_fail']} |")
lines+=['','只有30道任务、每组一次运行；90个分支不等于90道独立题。摘要JSON附探索性配对检验和Wilson区间，但抽样不是总体随机样本，不能用其宣称完整基准或未知任务上的统计收益。','', '## 费用与停止规则','', f"新运行总请求上限540、货币硬上限$24，通过PersistentBudget预留并跨进程持久化。实际已记录 {len(requests)} 次请求，已返回已知usage {sum(r.get('status')=='COMPLETED' for r in requests)} 次，未知请求 {len(unknown)} 次。",f"报价估算合计 **${sum(s['estimated_usd'] for s in summary.values()):.6f}**；按2026-10-22冻结最高时段非缓存输入$0.30/M、输出$1.20/M估算，忽略缓存优惠，不是供应商账单。账本仍保留货币预留 **${d['budget']['charged_or_reserved_cost_microusd']/1e6:.6f}**，不能将其理解为实付。",'', f"返回模型统计：`{json.dumps(agg['returned_models'])}`；结束原因：`{json.dumps(agg['finish_reasons'])}`。本地工具费用未知，仅报告执行次数及时间。构建算子历史费用未计入本次求解费用，也不据此计算算子摊销收益。",'', '完成30题三组后停止；不自动重试失败分支、不追加生成预算、不晋级算子、不启动60题流。','', '## 逐题结果','', '| 题目 | 难度 | FlowEvo | AFlow | FailureLearning |','|---|---|---|---|---|']
for t in tasks:
 v=bytask[t['task_id']];cells=[]
 for a in arms:
  r=v.get(a);cells.append(('通过' if r['audit_pass'] else '失败')+f"（{r['model_calls']}调用）" if r else '未完成')
 lines.append('| '+t['task_id']+' | '+t['difficulty']+' | '+' | '.join(cells)+' |')
lines+=['','## 复核入口','', '- `protocol.json`：完整冻结配置、文件哈希及预算。','- `tasks.json`：30道题、公开/离线角色分割及参考程序谱系。','- `scoring_acceptance.json`：正例和错误测试程序的实际执行结果。','- `operator_inventory.json`、`registry_queries.json`、`failure_evidence.jsonl`：实际权限及失败记录。','- `branches/<task>/<arm>/`：每次请求、原始响应、公开检查、最终程序哈希及离线评分。','- `budget.jsonl`：新运行独立持久化预算；`summary.json`、`results.json`：可复算聚合结果。','', '价格来源：[DeepSeek官方价格页](https://api-docs.deepseek.com/quick_start/pricing/)。']
if (R/'integrity_audit.json').exists() and (R/'extraction_diagnostic.json').exists():
 ia=read(R/'integrity_audit.json');ed=read(R/'extraction_diagnostic.json');lost=[x for x in ed['rows'] if x['classification']=='VALID_PYTHON_BLOCK_LOST_BY_ADAPTER']
 section=['## 截断与适配器诊断','', '**本轮结果明显受4096 Token输出上限及AFlow适配器解析策略影响，不宜用来给三种算法作能力排名。**', '', '| 组别 | 截断响应 | 遇到截断的分支 | 截断后仍复核通过 | 无最终程序失败 |', '|---|---:|---:|---:|---:|']
 for a,c in ia['failure_categories'].items():section.append(f"| {a} | {c.get('truncated_responses',0)} | {c.get('branches_with_truncation',0)} | {c.get('recovered_despite_truncation',0)} | {c.get('no_final_program',0)} |")
 section += ['',f"AFlow共有 {len(lost)} 例静态确认的提取损失：响应含可解析的Python代码块，但既有适配器拼接公式等其他代码块后拒绝。涉及任务：{', '.join(x['task_id'] for x in lost) or '无'}。这些代码块只经过静态旁路检查，未被晋升为正式结果，不能声称它们本会答对。",'', 'FlowEvo提取首个匹配代码块，并在后续阶段继续尝试；AFlow当前适配器在部分结构化输出失败时直接结束。二者适配层和错误恢复策略不同，本轮比较的是已冻结实现组合，不能把所有差异归因于工作流算法。后续如修复提取或改变输出上限，必须建立新实验，不能改写本轮结果。','',f"完整性审计：{ia['status']}，{ia['checks']} 项文件/结果核对；{len(ia['first_requests'])} 组FlowEvo与失败学习版首轮请求逐字一致。",'']
 at=lines.index('## 配对结果');lines[at:at]=section
 lines[6:6]=['**解释边界：失败学习组算子实际调用为0；AFlow受截断和解析失败影响。因此下表是当前实现的开发性运行结果，不是失败学习增益证明或算法能力排名。**','']
(R/'30题三组开发性对比实验报告.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(status=d['status'],completed=len(rows),summary=summary,unknown_requests=unknown),ensure_ascii=False,indent=2))
