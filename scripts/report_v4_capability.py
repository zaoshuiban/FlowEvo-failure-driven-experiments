"""Read-only aggregate and Chinese research reports; no model or candidate execution."""
import json,hashlib,collections,datetime,time,subprocess,sys
from pathlib import Path
from run_hard10_algorithm import ROOT,load,save,sha,canonical,fingerprint,EvidenceStore
OUT=ROOT/'runs/flowevo_v4_20261028'
SLUGS=['algebra-330','counting_and_probability-351','intermediate_algebra-289']
def md(name,text):(OUT/name).write_text(text.strip()+'\n')
def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)
def main():
 arts=load(OUT/'artifact_manifest.json');rows=load(OUT/'private/execution_results.json');joint=load(OUT/'private/joint_results.json');allrows=rows+joint
 history=load(OUT/'history_hashes.json');changed=[p for p,h in history.items() if sha(ROOT/p)!=h];assert not changed
 save(OUT/'history_integrity_final.json',dict(files=len(history),changed=changed,at=time.time()))
 costs=[]
 for r in EvidenceStore(OUT/'mapping_provider.jsonl').records():
  if r['kind']!='RAW_RESPONSE':continue
  raw=r['payload']['response'];u=raw['usage'];dt=datetime.datetime.fromtimestamp(r['at'],datetime.timezone.utc);peak=dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10)
  hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit)
  usd=(hit*.006+miss*.3+u['completion_tokens']*1.2)/1e6*(1 if peak else .5)
  costs.append(dict(id=raw['id'],key=r['payload']['key'],usage=u,estimated_usd=usd,peak=peak,at=r['at']))
 assert len({r['id'] for r in costs})==len(costs)==34
 total=sum(r['usage']['total_tokens'] for r in costs);cost=sum(r['estimated_usd'] for r in costs)
 save(OUT/'costs.json',dict(requests=costs,total_tokens=total,estimated_usd=cost,reserved_upper=load(OUT/'MAPPING_COMPLETE.json')['budget']['charged_or_reserved_cost_microusd']/1e6,actual_invoice=None,pricing_url='https://api-docs.deepseek.com/quick_start/pricing/',pricing_sha256=sha(OUT/'pricing.html'),old_generation_cost_separate=load(ROOT/'reports/hard140_algorithm_20261028_01/request_costs.json')))
 wire=[]
 starts={r['payload']['key']:r['payload'] for r in EvidenceStore(OUT/'mapping_provider.jsonl').records() if r['kind']=='SEND_STARTED'}
 for j in load(OUT/'mapping_jobs.json'):
  w=starts[j['id']]['wire'];assert json.loads(w['messages'][1]['content'])==j['public_input'];assert set(j['public_input'])=={'problem','parameter_schema'}
  assert w['messages'][0]['content']==load(OUT/'protocol.json')['mapping_prompt']
  wire.append(dict(id=j['id'],wire_sha256=fingerprint(w),gold_exposed=False,exact_public_projection=True))
 save(OUT/'wire_audit.json',wire)
 matrix=[]
 for a in arts:
  rr=[r for r in allrows if r['candidate']==a['key']]
  matrix.append(dict(candidate=a['key'],delivery='DELIVERED',static=a['static'],layers={layer:dict(collections.Counter(x['classification'] for x in rr if x['layer']==layer)) for layer in sorted({x['layer'] for x in rr})},original_result=a['original_result'],sha256=a['sha256']))
 save(OUT/'result_matrix.json',matrix)
 # Public outcomes omit reference answers and raw inputs; full scored rows remain host-private.
 save(OUT/'execution_index.json',[{k:r[k] for k in ['candidate','case_id','layer','role','classification','seconds','parameter_status'] if k in r} for r in allrows])
 worker_rows=[r for r in allrows if 'raw' in r and isinstance(r['raw'],dict) and 'raw' in r['raw']]
 metrics=dict(model_calls=len(costs),model_tokens=total,estimated_api_usd=cost,worker_executions=len(worker_rows),worker_wall_seconds=sum(r['seconds'] for r in worker_rows),l1_planned_cases=120,l1_unique_parameter_cases=119,l2_model_calls=34,new_algorithms=0,historical_files_verified=len(history),history_changed=0,unknown_requests=0,automatic_routing=False,experimental=0)
 save(OUT/'metrics.json',metrics)
 md('V4_0_Code_Audit.md','''# V4.0 代码审计
基准：`10e85deeb98eb00e08c354c71376be475e28f5ed`；独立分支 `feat/v4-reliability-capability`。原工作树只有未跟踪历史文件，清单见 baseline_worktree.txt，未覆盖。

- autonomous_generation.py：旧版保存 RAW_RESPONSE 后直接调用自定义 `_normalize_response`，JSON/字段异常逃出且没有返回 usage；新版先提取可信原始 usage、结算，再归一化。内容失败仍保留响应 ID、原文、哈希和诊断。
- compile_queue.py：新增请求边界的持久化健康检查，拒绝已有 UNKNOWN/预留未决。兼容旧内存 Budget，不假设它具有持久账本字段。
- run_hard140_algorithm.py：在每个并发窗口前后、每个生成任务前及交付异常后核查整个 Run 的账本，不再只看当前 SEND_UNKNOWN。旧 Run 的冻结快照及执行结果不变，旧运行不会重新启动。
- run_health.py：核验请求/响应哈希、未决传输、账本、上层传入的污染/Worker 故障。超出可信预留保留未决，阻止下一请求。
- math_execution_v4.py：独立 extraction / schema / frozen solve 接口；宿主评分仅在 Worker 返回后进行。

回归发现旧内存 Budget 的 snapshot 不含持久账本字段，最终改为只对具有 consume_shard 接口的持久 Budget 使用该门控。该兼容补丁在本轮模型请求和候选执行全部完成后加入，详见 post_execution_compatibility_patch.json。实际执行代码完整保存在 frozen_source；报告不将事后补丁伪装为付费运行时版本。
''')
 md('V4_0_Request_Ledger_Fix.md','''# V4.0 请求、交付和账本
传输 SEND_STARTED → RAW_RESPONSE / RESPONSE_RECEIVED；失败传输为 SEND_UNKNOWN。
交付独立记录 PARSE_VALID、PARSE_INVALID、CONTRACT_INVALID、MODEL_INCOMPLETE。
原始 usage 要求输入、输出、总量均为非负整数，且输入+输出=总量；不能从输出字符数猜测。合法用量先 SETTLED，再验证内容。无可信 usage 保留 USAGE_UNAVAILABLE/UNKNOWN。

Hard140 两次响应只读重放均完成：geometry-551-T 为 PARSE_INVALID，intermediate_algebra-426-T 为 CONTRACT_INVALID。两次原始响应 ID 不变、usage 全部保留，新测试账本完成 Token 结算，发送器只是本地返回保存响应，新增 API 为0。重复同一请求被阻断。见 historical_response_replay.json。

真实未知请求、账本未决、哈希损坏、预算越界、并发窗口故障均有故障注入测试。已收到但契约不合格的响应可以作为已消费的失败交付；不伪装成未调用，也不自动重试。

旧 Hard140 两笔 UNKNOWN 及门控违规仍成立；没有追溯结算或改写历史。费用估算与保守预留不是实付账单。
''')
 md('V4_0_Execution_Contract.md','''# V4.0 统一执行契约
采用既有 math-scalar-operator-v1 静态权限与 Linux Worker，不为 T/F/FC 分别放宽。V4 分层接口默认不接入在线 Controller。

|能力|处理|理由|
|---|---|---|
|普通闭包|允许并真实执行|无额外权限|
|nonlocal|保留拒绝|语言本身非网络权限，但不在旧冻结交付规范中；本轮不为历史 T 特批|
|顶层函数调用/自测|拒绝|导入时执行；测试应由宿主隔离调用|
|动态执行、文件/网络、私有反射|拒绝|权限边界|
|math/fractions等白名单依赖|允许|共同规则|

`extract_parameters(problem,schema,extractor)`仅向模型发送题面和公开 Schema，返回 MAPPED/UNKNOWN；`validate_parameters`严格验证闭对象、类型、字段，禁止远程 schema 引用；`execute_frozen`核对原始SHA并在Worker执行solve。

返回分类独立：DELIVERY_FAILURE、STATIC_REJECTED、INTERFACE_ERROR、PARAMETER_SCHEMA_ERROR、RUNTIME_ERROR、RESOURCE_EXCEEDED、MATHEMATICAL_WRONG、MATHEMATICAL_CORRECT、UNVERIFIED。数学评分不得把合法不支持/非法输入直接算错。对非法参数同时保存宿主保护结果与隔离原始函数探测，后者不构成运行时放行。

Worker：固定镜像、非root、无网络、只读、256MB、1CPU、32pids、2秒单次限额。关闭后核查没有遗留容器。清理无法确认会抛出基础设施停止异常。
''')
 md('V4_0_Engineering_Acceptance.md',f'''# V4.0 工程验收
12项V4测试通过；5项原编译输入计量回归、3项DeepSeek适配器回归通过，共20项。详见 engineering_tests_final.log、compiler_regression_final.log、deepseek_regression_final.log。

真实Worker验收覆盖合法闭包、非法参数拒绝、死循环超时、错误返回类型；静态测试覆盖nonlocal、顶层执行、不安全导入和eval拒绝。清理失败和Worker异常分类采用明确标记的故障注入，不冒称真实容器发生了清理事故。

历史{len(history)}个文件哈希全部保持。34条真实参数提取wire逐条等于允许的公共投影，未发送Oracle、评分答案、历史题解或候选评分。新Worker计算{len(worker_rows)}次；工程Mock不计入模型学习成果。新增算法生成0。

后续生产使用仍需在所有入口调用同一门控；V4没有宣称完成整套长期在线Controller实验。当前入口及Hard140后继窗口路径已覆盖。
''')
 md('V4_1_Frozen_Artifact_Manifest.md','# V4.1 冻结候选\n\n9份真实DeepSeek原始源码，均未修改。完整分析、Schema、原参数、原静态和来源成绩见 artifact_manifest.json。\n\n'+table(['候选','SHA256','原静态'],[[a['key'],a['sha256'],a['static']['passed']] for a in arts])+'\n\n旧生成Token与费用从原request_costs.json保留为历史学习成本；本轮没有重新生成。')
 md('V4_1_Test_Design.md',f'''# V4.1 独立测试设计
冻结哈希：`{load(OUT/'freeze.json')['protocol_sha256']}`。随机种子{load(OUT/'protocol.json')['seed']}。测试冻结先于待测源码执行，没有按成绩换样本。

两类各40个合法新参数+20个边界/不支持输入，共120条、119组互异参数。随机游走生成器出现1条重复，审计见test_independence_audit.json；不在看到结果后替换，分母明确是执行条数。完整参数、语义依据、Oracle答案仅在private/tests.json；模型只读取public_mapping_tasks.json中的题面。原始结果全部保留。

表达式：生成AST后直接按节点求值；待测程序则解析字符串，不复制其递归下降实现。覆盖2/8/10/16/36进制、优先级、显隐乘、嵌套、空/坏括号/非法符号/类型/长度。合法深嵌套用于暴露Python递归资源边界。

随机游走：枚举完整路径，事件为包括时刻0在内曾命中；同一路径最多计一次。独立反向概率递归与可穷举实例逐项交叉核对；较大实例仅使用有界反向精确分数。移动列表是等概率选项，多次出现向量表示多个选项，不自动去重。输出为最简分数m/n的m+n；概率本身另存，不能把接口当作概率输出器。

负例：独立SymPy有理插值、系数分母LCM。整数节点的消失多项式是首一整数多项式，任何整数系数解对其取余仍是整数系数，故插值余式的分母LCM给出最小a。没有调用待测程序做Oracle。

L2固定各类前12合法题、9来源映射、1原题，共34次提取，无反馈/修订。L3有限筛查官方三个分片公开题面，详见l3_screen*.json；接受algebra-378简单加法，随机游走候选因图结构、时刻事件或目标量不一致拒绝。该L3题难度低，仅作狭窄能力证据，不代表竞赛难题迁移。
''')
 def count(cand,layer,role=None):return collections.Counter(r['classification'] for r in allrows if r['candidate']==cand and r['layer']==layer and (role is None or r.get('role')==role))
 capability=[]
 for slug in SLUGS[:2]:
  k='hard140-math-train-'+slug+'-FC';c=count(k,'L1','legal');b=count(k,'L1','boundary_legal');j=[r for r in joint if r['candidate']==k and r['case_id'].startswith(('expr-','walk-'))]
  capability.append([slug,str(dict(c)),str(dict(b)),str(sum(r['classification']=='MATHEMATICAL_CORRECT' for r in j))+'/'+str(len(j))])
 md('V4_1_Algorithm_Capability.md','# V4.1 计算、映射与跨题\n\n'+table(['FC候选','L1合法40题','L1合法边界','L2新参数联合'],capability)+'''

表达式40/40合法新参数正确；9个合法边界8个正确，600层括号触发RecursionError。长度上限100000不意味着任意该长度的语法深度都可运行。非法/不支持输入得到明确拒绝。L2有1次模型复制缺失右括号；来源再次映射也出现括号不平衡。可信参数都可算对，所以是映射损失。

随机游走40/40常规合法参数测试正确（39组互异参数；walk-07与walk-35重复，全部保留，不事后换题）；10个合法边界5个正确，5个起点即目标的案例错误。代码只从第1步开始累计，缺少时间0已命中处理。该边界属于真正的数学错误，不能静默排除后宣称全域正确。重复移动选项与零步非目标测试保留。

L3：冻结表达式FC在官方MATH train algebra-378的独立题面上，可信映射和真实模型映射都得到正确结果。该题不是来源改数字，但只是四个整数相加，属于有限的 CROSS_ORIGINAL_TRANSFER_OBSERVED。模型省略默认base/implicit字段仍语义等价，不应把字段非完全相同视为映射错误。

随机游走：CAPABILITY_CONFIRMED_WITH_LIMITS；CROSS_ORIGINAL_OPPORTUNITY_NOT_ESTABLISHED。不启用自动路由、不授予Experimental。
''')
 negative=[r for r in rows if r['layer']=='NEGATIVE_CONTROL']
 md('V4_1_Negative_Control.md','# V4.1 有害纠错保留\n\n'+table(['测试','T','F','FC'],[[f'poly-{n}']+[next(r for r in negative if r['case_id']==f'poly-{n}' and r['candidate'].endswith('-'+a))['classification'] for a in ['T','F','FC']] for n in [2,3,4,5,6,8]])+'''

来源重新执行：T=315，F=315，FC=39690。原始源码哈希均不变。FC在6个小型参数问题中2正确、4错误；这个集合含来源8节点问题，不能称6个独立原题。

独立整数系数见证（a=315）：
`-8x^7+252x^6-3248x^5+22050x^4-84392x^3+179928x^2-194592x+80325`。
在1至8依次取±315；其存在足以否定39690是最小值。分母LCM论证进一步支持315的最小性。

FC源码选择一个CRT代表c_r后把P(t0)=c_r作为额外插值点，没有枚举c_r+k*c_m；这是额外限制的可审计代码位置。当前结果证明输出错误和限制缺乏充分性依据，不将全部失败唯一归因于这一行，也不修改该算法。
''')
 pair=[]
 for a in arts:pair.append([a['slug'],a['arm'],a['static']['passed'],str(dict(count(a['key'],'SOURCE_ORIGINAL_MAPPING'))),str(dict(count(a['key'],'L1','legal')))])
 md('V4_1_Paired_Attribution.md','# V4.1 分层配对归因\n\n'+table(['来源','组','静态','原参数来源','新合法参数'],pair)+'''

Hard140全部21尝试：2交付拒绝，2静态拒绝，3运行异常，4明确错误输出，10正确输出。前4项交付/静态失败不能叫数学错误；3运行异常也没有提供可评分答案。4错误中的表达式T/F两例，本轮可信参数下均修复，因此至少涉及参数映射而不是必然的算法错误。

表达式共用10个可表达的均匀嵌套问题：T/F/FC均10/10。其余一般AST无法由T/F固定递推接口表示，标记NOT_COMPARABLE，不能给它们错误成绩。FC具有更广的接口表达能力，但这里没有证明失败信息相对Task-Only的总体因果优势。

随机游走：17个四方向可配对参数，F有11错误输出、6运行异常，FC均正确；T因原顶层_self_test()静态拒绝，未人工删除后重新冒称原T。不同移动选项题无法由T/F接口表达，标记不可比较。

L2仅对FC做两类各12新参数映射，另对9候选做来源映射。没有为所有T/F新参数执行同等付费提取，因此不能宣称得到全面题面到结果的三组因果比较。模型提取单次采样、不调整Prompt。差异含接口表达、映射和计算三层因素。
''')
 md('V4_1_Final_Report.md',f'''# FlowEvo V4.0–V4.1 总报告

工程修复通过，冻结能力验证完成。结果支持**有限参数化计算能力**，不支持“F-C总体优于T”或“已经可以自动跨题路由”。

{table(['结果','表达式FC','随机游走FC'],[['合法参数测试','40/40（40组互异）','40/40（39组互异）'],['合法边界','8/9；深递归异常','5/10；时间0命中错误'],['模型映射→计算，新参数','11/12','12/12'],['不同原题','1道简单加法正确','未建立合格机会']])}

Q1：Hard14021次生成尝试中2交付拒绝、2静态拒绝、3运行异常；这些不等于7个数学错误。4明确错误输出中表达式T/F两例在可信映射下正确。10原正确结果保持不变。两笔历史UNKNOWN仅在新环境重放验收，旧违规不改写。

Q2：两份FC均通过40条常规合法参数测试（表达式40组互异，随机游走39组互异、1组重复），表现不限于来源。但表达式存在深递归边界，随机游走存在起点即目标错误，不能宣称声明范围全面正确。

Q3：真实模型提取在expr-04与原嵌套来源复制错括号；冻结算法用可信输入正确，这是参数映射失败。随机游走起点目标与多项式FC属于给定可信参数仍错误的计算问题。

Q4：只观察到表达式在一个不同原题的简单求和上正确。它不是难题泛化，也不是自动选择能力。随机游走明确为 CROSS_ORIGINAL_OPPORTUNITY_NOT_ESTABLISHED。

Q5：多项式FC来源错误复现，6个参数控制中4错；两组T/F均6/6。随机游走边界也揭示新错误。所有反例保存，未修源码。

Q6：当前具备受控映射和冻结函数的离线验证基础；**不建议直接进入全面在线复用**。下一阶段若启动，需事前限定已支持范围、独立验证参数映射，并对已知时间0和深递归限制做明确版本治理。本轮未授予任何算子Experimental，不自动开展V4.2。

本轮真实模型请求{len(costs)}次，全部仅用于参数提取；{total:,} tokens，API估算${cost:.8f}。调用ID均唯一，UNKNOWN=0。保守账本占用另列costs.json，不是实付账单。历史生成成本单独保留，不把已发生学习成本当作0。Worker候选调用{len(worker_rows)}次，记录墙钟{metrics['worker_wall_seconds']:.3f}秒，尚未货币化；工程Worker测试另计。

算法源码改动0，算法生成请求0。原历史{len(history)}文件哈希不变。真实执行版本、后续兼容补丁、原基准版本分开保存。20项工程与回归测试通过。所有测试结果均保留，无结果驱动换题，无Gold送达模型。

重要限制：测试集是预注册的开发性能力审查，120条参数案例不是120道独立原题。不同原题仅1道且很简单；L2单次模型提取；算法来源选择已知正反例，因此不提供总体平均效应估计。参考Oracle经过独立实现及小规模交叉检查，但不能替代对全输入域的数学证明。
''')
 md('README.md','''# V4.0–V4.1 交付
入口：[V4_1_Final_Report.md](V4_1_Final_Report.md)。V4.0四份与V4.1六份报告齐备。
- protocol.json / freeze.json：事前协议与哈希。
- artifact_manifest.json：9份历史算法及原始结果，源码路径指向只读历史制品。
- private/tests.json、execution_results.json、joint_results.json：宿主评分材料，不供模型读取、不上传公开仓库。
- mapping_provider.jsonl / mapping_responses：34次真实模型请求响应。
- wire_audit.json / history_integrity_final.json：无Gold投影、历史完整性。
- result_matrix.json / execution_index.json / costs.json / metrics.json：机器可读结果。
- frozen_source：实际执行源码快照；post_execution_compatibility_patch.json：事后兼容补丁。
模型请求和测试都已消费，不应重发或重跑后覆盖此目录。
''')
 print(json.dumps(metrics,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
