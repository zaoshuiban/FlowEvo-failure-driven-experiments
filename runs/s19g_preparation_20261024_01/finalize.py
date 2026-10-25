import json,pathlib,hashlib,collections,math,subprocess
P=pathlib.Path(__file__).parent;R=P.parents[1]
def rd(p):return json.loads(p.read_text())
def wr(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tasks=rd(P/'tasks.json');summary=rd(P/'acceptance_summary.json');near=rd(P/'near_duplicate_audit.json');assert all(x['pass'] for x in near['results'])
import sys
sys.path.insert(0,str(R/'FlowEvo/src'))
from failure_evo.contracts import strict_stream_task,fingerprint
public=[];sealed=[]
for t in tasks:
 online=t.pop('audit_cases');sealed.append({'task_id':t['task_id'],'cases':online,'role':'final_evaluator_only','never_online':True})
 assert not { ' '.join(x['input'].split()) for x in online}&{' '.join(x['input'].split()) for x in t['public_cases']}
 for c in t['public_cases']:
  c.update(visibility='public',legal_verified=True,source={'kind':'public_statement' if c['provenance']=='verbatim statement sample' else 'public_dataset','id':t['original_id'],'case_sha256':fingerprint([c['input'],c['expected']])})
 t['role']='prospective_stream_candidate'
 for c in t['public_cases']:c.pop('provenance',None)
 t['task_public']['public_examples']=[dict(c) for c in t['public_cases'] if c['source']['kind']=='public_statement']
 public.append(strict_stream_task({k:t[k] for k in ('task_id','dataset','difficulty','task_public','public_cases','role')}))
wr(P/'stream_tasks.json',public);wr(P/'sealed_final_tasks.json',sealed)
n=len(tasks);b=math.ceil(n/10);calls=5*n+8*b;cap=math.ceil(calls*.049152);pool=rd(P/'selection_protocol.json');probe=rd(P/'cross_task_probe/freeze.json')
plan={'status':'PARTIAL_POOL_NOT_AUTHORIZED','qualified_tasks':n,'target_tasks':[60,100],'target_met':n>=60,'batches':[ [t['task_id'] for t in public[i:i+10]] for i in range(0,n,10)],'continuous_single_run':True,'cold_start_only_once':True,'model':'deepseek-flash','documented_version':'DeepSeek-V4.1-Flash-1017','input_upper':32768,'output_upper':8192,'solve_request_cap':5*n,'generation_request_cap':4*b,'source_validation_request_cap':4*b,'total_request_cap':calls,'conservative_reservation_usd':calls*.049152,'hard_budget_proposal_usd':cap,'authorized_usd':0,'model_calls_this_phase':0,'historical_probe_separate_proposal_usd':.25,'pricing_url':'https://api-docs.deepseek.com/quick_start/pricing/','peak_usd_per_million':{'input_hit':.006,'input_miss':.30,'output':1.20},'reservation_all_tokens_per_million':1.20,'price_rechecked':'2026-10-24 America/New_York','protocols':['learning-evidence-bundle-v1','s19-compile-envelope-v2','evidence-diversity-v1','repair-choice-json-v2'],'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'task_sha256':sha(P/'stream_tasks.json'),'sealed_sha256':sha(P/'sealed_final_tasks.json'),'selection_sha256':sha(P/'selection_protocol.json'),'probe_wire_sha256':probe['wire_sha256']}
wr(P/'experiment_proposal.json',plan)
reports=R/'reports';base='../runs/'+P.name+'/'
def report(name,text):(reports/name).write_text(text)
report('S19G_Task_Pool_Design.md',f'''# S19-G 任务池准备

本轮真实模型请求0；旧实验未修改。当前结论为 **PARTIAL_POOL_NOT_AUTHORIZED**。

目标60–100题未达到：排除583个曝光任务后，满足当前严格元数据、题面样例和至少24个独立评分输入条件的候选只有29题；实际验收{summary['examined']}题，合格 **{n}题**。不能把这些结果称为已完成60题长期池。

固定顺序见[候选序列]({base}candidate_order.json)，最终顺序见[任务清单]({base}stream_tasks.json)。种子S19G-long-stream-v1；官方MEDIUM/MEDIUM_HARD/HARD/VERY_HARD分别按SHA排序，轮转取样，不使用目标模型表现。最多200次候选准入，目标80题。实际难度分布：{dict(collections.Counter(t['difficulty'] for t in tasks))}。

源为固定官方TACO test Parquet，SHA `{pool['source_sha256']}`。沿用已有任务级曝光账本，并保守排除全部80个S18候选（含未正式观察/预留/验收失败）。没有重新审查800题的解答效果。描述长度、约束表述与题面保留在原始准入材料中；不将描述长度当作已证明的困难度。

原题URL、规范化题面精确哈希及词5-gram Jaccard≥0.85进行近重复检查，当前29个候选无超阈值匹配。该方法不能证明无语义改写重复；参见[审计]({base}near_duplicate_audit.json)。曝光结论限于可取得的项目记录，不声称模型训练未见。

缩减方案：仅把这{n}题作为新候选小流，按10题批次连续执行，明确不足原定研究规模。优先方案：另行固定官方训练分片或其他来源，以同样的曝光、谱系及Worker验收规则补到60–100题，再冻结最终完整顺序；不得直接拼入旧开发任务，当前未验证的外部题目不计数。尚未授权执行缩减流。
''')
report('S19G_Public_Evaluation_Protocol.md',f'''# S19-G 公开评价与隔离验收

合格{n}题；每题保留题面真实样例，增加12个事前指定为在线开发的原benchmark judge输入，另留12个最终封存输入。两组及题面样例按规范化输入完全不重叠。最终集共{12*n}例。原judge输入不冒称官方题面公开样例。

按固定S19G-role-split哈希顺序取24例并分成12/12，无模型输出参与分组。它增加检测覆盖，但不是语义边界覆盖证明。合法性依据为固定官方benchmark输入来源、标准stdin接口、SPJ/图片等元数据排除和参考程序一致通过；没有声称逐条形式化证明题面全部约束。输出采用既有tokens比较器，未更改评分规则。

每题至少两份AST结构不同的原始Python参考在真实Linux Worker通过全部样例、在线开发及封存输入；无效输出程序在相同集合通过0例。源代码哈希不同或AST不同不等于算法谱系独立，因此参考正确性仍是benchmark与一致性证据，而非数学证明。失败候选保留原因和原始结果，未以求解模型表现换题。

[完整验收]({base}scoring_acceptance.json)、[工具账本]({base}acceptance_budget.jsonl)、[汇总]({base}acceptance_summary.json)。首次参考在taco-test-788出现函数外return，AST能解析但不可编译；记录保留在initial_acceptance.log。只给准备脚本加入不执行源码的编译过滤，复用原账本续验；未改Worker或评分器。

实际Worker使用现有非root、断网、只读源码、资源受限容器和固定镜像，配置复用reports/s19_v2_acceptance/worker_environment.json。程序只在隔离Worker运行；宿主仅解析/编译检查源码。工具毫秒和预算见汇总，本地计算未货币化，不能写成零计算成本。

在线任务文件stream_tasks.json不含最终测试或参考源码；sealed_final_tasks.json及验收日志、参考源码只供离线评价器审计，禁止整目录注入学习器。G/M/F必须使用同一在线集及token/调用额度。最终复核只在程序/规则冻结后执行；结果用于独立报告及外部治理，不能回流在线假设、路由或修订。验收器历史字段visibility=public表示该次离线测试可供评分器读取，不授予最终用例在线可见权限；角色以独立清单为准。
''')
report('S19G_Cross_Task_Learning_Probe.md',f'''# S19-G 历史跨任务机制诊断冻结

**零新API；未授权。** 复用91与0313真实历史公开失败，共2道原题、5个事件。它们是开发材料，不是独立泛化任务。

[冻结清单]({base}cross_task_probe/freeze.json)保留原S19-E的bundle、messages、完整wire和宿主追溯清单，逐文件验证复制哈希。再次调用现有prepare验证同一wire SHA `{probe['wire_sha256']}`，保守输入上界17,878≤32,768，输出上限8,192。未创建发送器、未登记Operator、未修改旧NOT_SENT。

时序及来源沿用原JOB_STARTED cutoff和已验收事件引用；length/stop及不同任务公开表现保持分开，源码片段不冒充全文。未来轨迹、封存答案不进入请求。现有假设、规则及公开反例只使用当时可见版本。

下一步仅建议一个初始候选、最多一次诊断修订；每版本最多一次原有来源验证，合计最多4次新请求。按所有Token每百万$1.20保守预留上界$0.196608，独立硬预算提案 **$0.25**，当前授权为$0。不得转移S19-F余额。

来源按原最早合法checkpoint固定，禁止输出后换来源；分别记录完整修复、局部改善、无收益。规则合法只获Shadow，既有来源和安全要求通过才可有限授权。比较规则条件、动作、最终请求与Generic，不把文字变化或相同请求认作新能力。无配对求解证据不宣称因果增益。两次均无效则归档，不扩Prompt、不追加求解。

本轮只确认跨任务材料可发送；尚未证明模型读到后能生成有差异、有来源效果的Operator。
''')
report('S19G_Long_Stream_Experiment_Proposal.md',f'''# S19-G 连续学习实验提案

**数据准备部分完成，未达到60–100题目标，未授权真实API。** 当前{n}题通过隔离评分验收。推荐先补充独立来源达到目标并重新冻结；若采用缩减方案，必须承认样本量限制。

[机器可读提案]({base}experiment_proposal.json)冻结当前{n}题顺序、{b}批（每批最多10题）、源码提交、任务及封存集哈希。同一Run、一个失败池和Operator库，只在Run开始冷启动；批间不清空状态。维持既有四个协议、五阶段FlowEvo、成功经验库及Shadow/Experimental权限，不恢复Suspended版本。

缩减F组请求硬上界：求解{5*n}、学习{4*b}、来源验证{4*b}，合计{calls}次。学习各批最多2个作业，每作业初始+1次修订；来源每版本1次。试用求解及回退占用原任务求解额度，不叠加。每请求输入≤32768、输出≤8192，按统一$1.20/百万保守预留共${calls*.049152:.6f}；建议硬上限 **${cap}**，授权$0。历史诊断另提$0.25，互不挪用。80题示意上界464请求、预留$22.806528，可提$24，但尚无80题合格清单，不是可启动计划。

价格已查官方[DeepSeek价格页](https://api-docs.deepseek.com/quick_start/pricing/)，deepseek-flash对应DeepSeek-V4.1-Flash-1017。使用峰值保护预算，按实际cache hit/miss、输入输出及时段结算，未知费用保持未决不计零。工具耗时独立报告，不把API节省当总成本。正式启动需再次确认价格、Worker、依赖哈希、任务与明确新授权。

每批记录完整漏斗：任务/事件公开失败→独立原题证据族→单/多见证学习作业→实际送达→机制假设内容差异→规则条件/动作差异→来源公开效果→有限授权→未来匹配→实际介入及回退→暂停→完整成本。相同Generic动作与相同wire分开审计；无Operator的题不能归因学习。任务最终程序与Operator介入分支在锁定后接受封存复核；封存结果不回流在线。

没有失败或前几批没有成功Operator不提前停；仅按安全异常、污染、未知请求、无法恢复状态、Worker异常、硬预算等停止。不能执行中修改任务、Prompt、调度、压缩、评价。F-only不支持相对G/M因果收益；后续对照必须另冻预算并共享相同公开集。无充分复用不研发复杂老年代或成本路由。本轮不启动S20/S21。
''')
with (reports/'S19G_Task_Pool_Design.md').open('a') as f:
 f.write('\n## 实际合格任务\n\n|顺序|原题ID|官方难度|在线用例|封存用例|\n|---|---|---|---:|---:|\n')
 for i,t in enumerate(tasks,1):f.write(f"|{i}|{t['original_id']}|{t['difficulty']}|{len(t['public_cases'])}|12|\n")
with (reports/'S19G_Public_Evaluation_Protocol.md').open('a') as f:f.write('\n本轮重新执行12项隔离探针全部PASS，见worker_probes.json；159份历史Run文件逐一哈希一致，见historical_integrity.json。source_dependencies.json记录现有源码依赖哈希；没有修改这些依赖。\n')
files={str(p.relative_to(R)):sha(p) for p in P.rglob('*') if p.is_file() and 'tmp' not in p.parts and p.name!='artifact_manifest.json'}
wr(P/'artifact_manifest.json',files);print(n,calls,cap)
