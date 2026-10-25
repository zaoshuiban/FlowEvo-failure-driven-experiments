import pathlib,json
P=pathlib.Path(__file__).parent;D=P/'reports';D.mkdir(exist_ok=True)
def read(n):return json.loads((P/n).read_text())
def write(n,s):(D/n).write_text(s.strip()+'\n')
f=read('freeze_checks.json');prop=read('execution_proposal.json');ext=read('external_acceptance.json');results=read('external_worker_results.json');plans='\n'.join(f"- {a}: `{v['run_id']}`，协议 `{v['protocol_hash']}`。" for a,v in prop['plans'].items())
write('S20_Code_and_Baseline_Compatibility_Audit.md',f'''
# S20 源码与基线兼容性审查

日期：2026-10-25。基线提交：`2614b9274efcc8c4b0ff482dcdeba9bb9d5c245a`。本轮真实模型请求为0，所有发送器联调均为模拟响应；公开数据HTTP下载不计作模型请求。

## 最小改动及其原因

1. `scripts/run_learning_stream.py` 新增绝对批次号 `--stop-after-batch N`。每个批次完成题间学习、保存Runner后写入持久 `BATCH_FINALIZED`；恢复时跳过已完成批次。旧入口对已完成任务会再次调用boundary，因此仅增加一个循环break不足以保证恢复不重复调度。中间暂停不写ONLINE_LOCKED，最后一批完成才锁定。
2. `repair_choice_hook.py` 仅追加实际介入前的公开任务投影与预算快照。动作、准入、额度、暂停和Controller逻辑没有改变。
3. `scripts/s20_action_pair_preflight.py` 根据实际Hook前缀重建固定Generic与学习动作的最终wire，使用同一 `action_messages`、temperature=0和Limits。它没有模型发送入口，拒绝非法动作、变更源码哈希及不匹配Generic。显式只读before字段，忽略future/proposed/final字段。

`production.patch`保存两处生产改动；新文件另由`source_dependencies.json`冻结。原S19-G2计划没有被覆盖，因依赖变化其旧哈希不能用于新工作区开跑。新计划如下：

{plans}

## 已完成验收

- 原冻结清单在修改前复核：80题、1137在线、960封存；参考源码哈希、三臂预算、旧20题159文件保持一致。
- FlowEvo核心测试212项通过；S19脚本回归28项通过；S20新增3项通过，覆盖G/M/F批次恢复、已完成请求不重发、manifest不匹配拒绝、非法暂停参数以及配对请求隔离。
- 真实Linux Worker安全资源探针12/12通过；模拟模型＋真实Worker完成生成、来源修复、跨题试用、公开退化暂停、缺失程序、编译错误、正常和错误程序检查。原有Shadow/Experimental与未知请求保护未放松。
- `worker_batch_acceptance.json`：真实Controller在第2批暂停并恢复，已完成发送计数不变；2条实际Hook前缀重建的学习wire与当时发送wire哈希一致。此处“真实”指Controller/Worker执行，**不指真实模型效果**。
- 新增快照首次复核暴露了PublicTaskView已投影样例不含visibility标签的问题；配对工具现直接校验投影格式并重建对象，不再次投影丢样例。早期失败日志保留，最终验收单独记录。

## 仍然存在的比较边界

G/M使用原生五阶段恢复及各自成功Skill库；F另有受限Hook。系统级分数差异包含调用时机、请求内容和学习成本，不能直接归因于规则表示。动作级配对工具只证明相同状态可构建请求，尚未进行付费干预比较。

Generic对NO_ENTRY等状态可能选择当前A/B权限不允许的动作；工具将明确拒绝这类配对，不能把不合法分支强行执行。未来配对必须冻结合法适用范围、独立预算和相同回退续跑协议。

本轮未重写Controller、EvidenceBundle、调度、代际管理，未恢复任何历史Suspended版本。
''')
write('S20_TACO80_Execution_Readiness.md',f'''
# S20-A TACO80 执行准备

结论：**工程准备通过，具体新计划尚未授权，不能现在发送模型请求。**

直接复制原冻结80题及顺序，不重新挑题：61道train＋19道原S19G test，8批×10。`stream_tasks.json`、`sealed_final_tasks.json`、`task_lineage_manifest.json`均与原文件逐字节同哈希。在线1137例＝177题面样例＋960研究协议事前开放开发输入；最终960例。按输入规范化排重，80题各有两份既有Worker验收通过的参考源码，其哈希本轮再次核对。未重复执行旧80题全部参考评分；复用了已冻结的逐题执行证据，并重新运行Worker安全与Controller联调。

运行时只加载公开任务文件；封存文件由离线评价器读取。三臂全部ONLINE_LOCKED后才能评价本轮模型生成程序的封存结果。参考程序的运行前评分验收不是在线模型反馈。

## 新冻结执行方式

{plans}

按G1→M1→F1→G2→M2→F2…→G8→M8→F8交错执行。每个臂只冷启动一次，后续批次使用相同plan/tasks和`--resume --stop-after-batch N`。N为绝对批次号。运行目录、成功经验、失败证据、规则、M记忆与PersistentBudget均独立。不得从历史Run继承规则或余额。

授权前最后检查：代码与`source_dependencies.json`一致、Worker socket和镜像可用、报价未变、新授权文件精确匹配run_id/protocol_hash/model/budgets。真实入口已经校验任务哈希、冻结依赖和授权；暂停参数不增加预算。

现有未知请求或中断任务执行保持fail closed；不得靠重启补发。批次学习正常完成后可恢复；协议/安全/Worker/污染/未知状态/硬上限停止。0失败、0有效规则或0匹配不是提前停止理由。

## 对结果的约束

80题是事前选取的困难倾向开发分布，不是未见泛化。每臂一次运行是探索性系统比较。题目固定但模型随机性、缓存及供应商时间漂移仍需报告；交错不能消除这些因素。

暂未产生S20模型结果、学习作业、Operator或复用证据。旧计划$66及历史$.25诊断提案均不能充当新授权。
''')
write('S20_APPS_LCB_CodeContests_Admission_Plan.md',f'''
# S20 外部任务准入

本轮实际合格：**APPS40、CodeContests20、LiveCodeBench0，共60题**。目标90未达成，不能称为完整三数据集迁移池。

|来源|固定版本及划分|元数据审查|候选|隔离通过/选入|
|---|---|---:|---:|---:|
|APPS|codeparrot/apps `{read('apps_source.json')['sha']}` test|5000|80|40/40|
|CodeContests|deepmind/code_contests `{read('contests_source.json')['sha']}` test|165|29|20/20|
|LCB Lite|`{read('lcb_source.json')['sha']}`，release_v6|源码schema/发布映射复核|参考前置条件未满足|0|

固定元数据顺序为原始ID/行号，无目标模型试跑。APPS准入范围interview/competition，但前40个实际合格均为**interview**，未实现competition分层配额，不能声称40道高难竞赛题。CodeContests仅CF rating≥1600、stdin/stdout，实际1700–3500。没有因为目标模型失败率调题。

来源下载URL、revision、大小、SHA在`external_downloads.json`；原始大文件在本地缓存，未混入运行时Prompt。APPS官方发布使用JSONL；CodeContests使用官方Parquet。未执行远端dataset脚本。

## 曝光、谱系和比较器

与全部1000 TACO test、既有项目任务元数据、S19G train候选188题及LCB test6元数据核对；依据canonical原题URL、规范化题面SHA、5-gram Jaccard≥0.85、参考源码/AST代理。CF contest URL统一为problemset URL。APPS和CodeContests之间继续排重。原题身份和near score保存在`external_lineage.json`。

本方法可排除记录中的同原题及明显近重复，不证明模型预训练未见，也不保证语义同题查全。不同AST参考实现不等于独立算法证明。

109份候选输出契约逐项复核：排除APPS66缺公式图、APPS108非唯一构造、CodeContests31/90/152非唯一输出。其余采用既有tokens比较器。允许词典序唯一最优、排序集合、计数或固定大小写结果；不把一般构造题塞进精确比较器。

每个选入题：两份不同AST Python源码在Linux Worker通过全部冻结输入；常量错误程序全部拒绝。60题参考及反例共执行记录见`external_worker_results.json`，未把这些人类程序视为FlowEvo自然失败。

## LCB缺口及缩减方案

官方Lite release_v6包含test.jsonl至test6.jsonl，不能用本地175题test6增量冒充全release。该固定schema提供题面及公私测试，但没有两份可信参考实现。现有test6亦已纳入历史曝光基线。故本轮在参考前置条件停止，不进行缺参考的合格宣称，也未用模型补写参考。

这不是“LCB全体没有合格题”的结论。补齐带来源的参考提交后，才能继续新题原题排重及Worker准入。本轮可提出60题、两个外部数据集的缩减池；外部付费任务和顺序仍须在S20-A门槛通过后另行冻结授权。

`external_public_tasks.json`与`external_sealed_tasks.json`分离，当前只用于准入准备。B1/B2未来需预先划分不重叠确认/开发集合，不能将同题用于修订及独立确认。
''')
write('S20_External_Evaluation_Protocol.md',f'''
# S20 外部评分协议

冻结的60题共有**879在线输入＝159原题公开样例＋720研究协议开发输入**，另有**720封存输入**。每题12新增在线＋12封存，按输入规范化与原题样例去重，再按固定`S20-role-v1`哈希分角色。不同臂使用完全相同的公开文件。

APPS新增输入来自官方input_output；CodeContests逐例保留public_tests/private_tests/generated_tests原始身份。原private/generated输入只有在本研究事前明确重新指定后，才作为online development公开，绝不称其原本就是题面样例。未开放部分保持sealed_final，在线失败库和学习请求不得读取。

合法性与期望依据：固定官方数据原文和两份参考实现的一致实际执行；不造输入、不替换答案、不从模型表现选测试。这是可审计参考依据，不是对官方数据所有约束的形式化证明。样例解析仅接受字面Input/Output结构；特殊判分、非唯一输出、未解析公式和不能满足测试数的题不进入主轨。

Worker使用原不可变Linux镜像 `sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8`；无网络、非root、受限资源。Python参考源码只在Worker执行，宿主仅AST解析及compile语法检查。每例5秒，沿用既有s1/tokens比较器，不新增浮点容差或大小写豁免。

## 实际验收与等价性

- 60题×两份参考源码全部通过；60份常量错误输出全部拒绝；完整结果、源码哈希、工具账本可追溯。
- TACO80与此外部60题具有相同**研究评价角色与每题12/12基础强度**，评分接口和隔离器相同。
- 不同题测试覆盖能力、参考算法独立性、官方原评测规模并不等价。不能把tokens比较当作完整官方checker，更不能将LCB Lite等同完整LCB。
- LCB尚未准入，故当前不能声称三来源都已具备等价评分。

封存评价只在在线状态锁定后执行。复核可用于实验结论及外部治理，但不得回填学习Prompt。若有数据错误，记录受影响任务并停用冻结版；不得在看到F/G/M答案后偷偷改期望、换题或调整比较器。

用例多不等于独立任务多；正确率统计单位是原题。公开PASS、来源修复、最终封存PASS和自然迁移分别记录。
''')
write('S20_GMF_Cost_and_Attribution_Protocol.md',f'''
# S20 G/M/F 成本与归因

## 共同条件与不同处理

三臂同80题顺序、模型deepseek-flash、公开评分、五阶段正常求解最多5次/题。各自成功Skill库持续积累；预算和历史不跨臂共享。M文本更新及注入Token计费，F归纳、修订、来源验证、Hook、回退全部计费。

M现有学习输入上界65536，普通求解和F学习上界32768，输出均8192。未改变这个已有差异；它属于系统设计比较而非等输入表示消融。历史五事件M预检60936可发送，但长期重复材料可能越界：应记录NOT_SENT、保留旧记忆，不把记忆未送达误写为文本经验无效。F压缩请求仍按最终wire预检。

## 当前报价和硬预算

2026-10-25从[DeepSeek官方报价](https://api-docs.deepseek.com/quick_start/pricing/)保存网页：请求名deepseek-flash，文档服务版本DeepSeek-V4.1-Flash-1017。峰值每百万输入命中$0.006、未命中$0.30、输出$1.20；非峰值为一半。供应商实际响应模型名必须逐请求记录。

|臂|求解请求上限|额外学习/验证|硬美元上限|
|---|---:|---:|---:|
|G|400|0|20|
|M|400|16|22|
|F|400|64|24|
|总计|1200|80|66|

按全部Token统一$1.20/百万保守预留，总上界$63.5437056；按全峰值未命中实际输入/输出分别满额计价上界$25.3231104，均不是预计实付。保留按通道货币硬限额，不挪余额。所有预算**尚未授权**。来源与学习独立通道，未来F试用/回退消耗该任务正常5次额度，不额外赠送。

公开求解工具上限每臂10240，F验证4096；离线最终评分原提案最多4368工具单元、21600秒、0模型请求。记录工具墙钟及实际CPU/资源可得信息；未货币化部分不得记成0经济成本。

## 动作级对照

新增前缀记录与配对预检可重建实际F命中的before源码、公开反馈、任务及剩余预算。固定Generic动作与学习动作使用同一A/B执行器；分别保存action、wire、哈希。当前仅零发送验收，两个实际工程Hook的重建wire与发送记录相同。

未来动作级付费控制必须事前选取“前K个合法F命中”，不按结果挑成功题；冻结每分支相同剩余预算和回退路径，用独立状态真实执行。不得用已保存的Generic未来输出代替。$66仅含三臂系统流，不含额外重放对照；K、额外请求/货币硬限和授权需单独冻结，未获授权只报告请求差异。

## 报告规则

先比较封存全通过任务及公开PASS/封存FAIL，再比较等可靠性条件下成本。两失败分支中更便宜不算效率收益；无配对只能报告系统相关性，不能作单算子因果归因。F零介入时不得将组间正确率差异归因学习。动作同但wire不同应分开说明；同规则/同动作/同请求不得算新增能力，重复生成费用照计。

累计净节省必须扣除生成、修订、来源验证、路由及回退；本地成本未货币化时并列报告API及时间。一次80题各臂单次运行属于探索性证据，不宣称统计优势。
''')
write('S20_Stage_Gated_Execution_Plan.md',f'''
# S20 分阶段执行计划

本轮完成零模型API准备，尚无S20实验效果。总览：

|门槛|当前状态|允许的下一步|
|---|---|---|
|TACO80工程准备|通过，新哈希已冻结|等待具体计划费用授权|
|S20-A真实G/M/F|未运行|授权后8批交错持续运行|
|外部池|APPS40＋CodeContests20；LCB0|保留60题准入材料，补参考前置条件|
|B1冻结迁移|无S20来源有效Operator|不得直接启动|
|B2跨源持续学习|尚无B1信号|不得直接启动|
|S21消融|尚无S20实际介入证据|不得启动或人为晋级|

## S20-A

针对三个新Run及其协议哈希授权，合计上限$66；旧授权、S19-F余款、历史$.25 probe均不适用。每批完成题间学习后安全暂停，批次间保留该臂全部经验。无自然失败或无成功算子照计划继续；只按既有安全/未知请求/污染/Worker/不可恢复/预算停止。

每批归档失败机会漏斗、独立来源数、假设实质变化、发送结果、规则重复、来源完整/局部/无收益、有限授权、未来匹配及实际使用、Generic动作及wire差异、各通道费用。最终三臂在线锁定后运行封存复核。

## S20-B1与B2

B1须先获得TACO来源有效且安全门控合格的冻结版本，重新核验跨源适用范围，明确新任务allowlist、额度及授权。旧Experimental不能自动跨数据集生效。使用固定版本，不基于目标答案修订。若无可迁移版本则停止B1准备付费环节，记录生成/效果瓶颈。

现有外部60题只冻结准入池，不假装已完成90题迁移计划。B1付费计划应从池中事前划分确认任务和B2保留任务，任务ID/顺序/预算独立冻结；LCB缺口应明确缩减为两来源，或补齐可信参考后另版冻结。不能按S20-A/B模型表现换外部题。

只有B1有可检验信号才设计B2不同任务流；禁止同任务同时调优和确认。外部费用目前无授权、无可执行付费计划；不沿用$66剩余。

## S21

要求真实F介入、有价值且可评价的机制差异。再设计跨任务聚合、功能修订、固定/动态安全管理、同源文本与规则的消融，共享基础工具及门控。没有成熟算子就不研究人为晋级收益。

## 最终六问

1. TACO80工程上可用；新冻结计划仍待授权及开跑时环境/报价复核。
2. 三臂主比较是系统级；当前动作级只有零发送前缀/wire审计，不足以形成效果因果归因。
3. APPS40、LCB0、CodeContests20实际隔离准入。
4. 这60题具有相同12在线开发/12封存角色和Worker评分接口，但测试覆盖及数据分布不等价；LCB尚未具备。
5. A出现可评价Operator→重新安全授权B1；B1信号→独立B2；有真实机制差异→S21。
6. $66三臂、历史$.25诊断、外部迁移及额外动作配对均未获得本轮费用授权。真实模型请求0。
''')
print('wrote six reports')
