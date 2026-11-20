本轮原样执行了旧 v1、v2，并从同一原 v0 分别完成 SUMMARY 三次、TRACE 两次修订；TRACE 第三次完整输入超出冻结上限，在发送前停止。
所有已执行候选的三个来源续跑均为 0/3，因此没有得到能完成来源恢复的程序。
没有候选达到开发通过条件，已曝光回归未执行，目前没有依据进入新的迁移评价。

Run ID：`alfworld_skill_revision_feedback_20261118_01`。执行日期：2026-11-18。状态：按输入限制结案，无未决模型请求。

下表的动作数按第 41 / 12 / 107 / 23 局排列，只计检查点后的技能动作；各局原剩余额度分别为 34 / 24 / 26 / 37。费用列只计本轮新模型请求的保守预留，不是供应商实际账单。旧 v0 的历史动作不进入本轮资源总数。

| 组／版本 | 实际执行 | 第 41 局完成 | 第 12 局完成 | 第 107 局完成 | 第 23 局拒绝 | 提前错误声明完成 | 动作数 | 新请求数／保守预留 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| legacy_v0 | 历史执行已核验；本轮复用 | 否 | 否 | 否 | 是，0 动作 | 是，第 41 局 | 7 / 24 / 0 / 0 | 0 / $0.000000 |
| legacy_v1 | 本轮实际执行 | 否 | 否 | 否 | 是，0 动作 | 未观察到 | 34 / 24 / 26 / 0 | 0 / $0.000000 |
| legacy_v2 | 本轮实际执行 | 否 | 否 | 否 | 是，0 动作 | 未观察到 | 34 / 24 / 0 / 0 | 0 / $0.000000 |
| SUMMARY_r1 | 本轮实际执行 | 否 | 否 | 否 | 是，0 动作 | 是，第 41 局 | 8 / 24 / 0 / 0 | 1 / $0.071678 |
| SUMMARY_r2 | 本轮实际执行 | 否 | 否 | 否 | 是，0 动作 | 是，第 41 局 | 8 / 24 / 26 / 0 | 1 / $0.072354 |
| SUMMARY_r3 | 本轮实际执行 | 否 | 否 | 否 | 是，0 动作 | 是，第 41 局 | 8 / 24 / 26 / 0 | 1 / $0.071528 |
| TRACE_r1 | 本轮实际执行 | 否 | 否 | 否 | 是，0 动作 | 未观察到 | 34 / 24 / 0 / 0 | 1 / $0.101038 |
| TRACE_r2 | 本轮实际执行 | 否 | 否 | 否 | 是，0 动作 | 未观察到 | 34 / 24 / 26 / 0 | 1 / $0.118136 |

这八个版本记录都成功提取唯一源码并通过静态检查。七个版本在本轮执行，v0 复用经源码、输入和执行回执核验的历史结果。所有分支均无运行异常；所有第 23 局边界检查均为无动作拒绝。源码从原始响应无损提取，没有人工修改策略。SUMMARY r2、r3 源码逐字相同，仍按两次真实请求、两个提交版本如实计数。

**旧修订的交付障碍确实存在，但没有遮住一个已成功的恢复程序。**旧 v1、v2 在新规则下都可执行，三来源仍各为 0/3。v1 在第 107 局识别了原 v0 拒绝的目标句式，实际放回 soapbar 1、拾取不同实例 soapbar 2，这是局部行为改善；随后仍持物探索至额度耗尽。v1 在第 41 局的 34 个动作全是移动。v2 在第 41、12 局都先发生“放下—取回—放下—取回—放下”，之后自行离开局部重复，但拾取第二件物品后仍持续移动至耗尽；第 107 局仍零动作错误拒绝。这些结果来自真实动作和环境反馈，详见 [旧修订诊断](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_skill_revision_feedback_20261118_01/Legacy_Revision_Diagnostic.json) 与 [旧修订行为证据](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_skill_revision_feedback_20261118_01/Legacy_Behavior_Notes.json)。

**SUMMARY 修改了部分识别与搜索行为，没有修好完成条件和投递。**r1 在第 107 局仍错误拒绝；r2 扩大了目标句式识别，能放回第一件并拾取第二件，但剩余行为仍是探索。第 12 局拿到第二张 creditcard 后，也继续在已见位置间移动到第 50 步。三版在第 41 局均把两件 keychain 分别放到 shelf 1 和 shelf 5，随后返回 `two target items already placed`，环境仍未完成。该证据说明完成声明错误，不把某个历史容器实例硬编码为唯一正确答案。r3 与 r2 的源码及四个检查点公开执行后缀完全相同，第三次修订没有产生新的可执行行为。

**TRACE 的细化反馈没有在两次实际修订中带来恢复成功。**r2 也不再错误拒绝第 107 局，但两版所有实际动作只有移动和少量开柜，没有一次拾取或投递。源码将投递命令与无编号的容器类型作全等比较，例如目标为 `shelf`，真实合法命令却是 `move keychain 2 to shelf 1`；这些记录中的投递分支因此无法匹配，程序保持持物并探索。两版没有观察到错误完成声明，但也没有新增投递，不能据此认定完成判断学会了。两组程序仍没有可靠维护“当前物品位于哪个容器实例、取回后进展是否撤销”的完成状态。上述解释是在执行结束后对源码和公开记录的核对，没有作为人工根因提示反馈给学习器；代码行与动作证据保存在 [新修订行为证据](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_skill_revision_feedback_20261118_01/Revision_Behavior_Notes.json)。

终止原因可直接归纳如下；错误拒绝也是未完成，不算恢复。

| 版本 | 第 41 局 | 第 12 局 | 第 107 局 |
| --- | --- | --- | --- |
| 原 v0（历史） | 错误声明完成后退出 | 步数耗尽 | 错误拒绝目标 |
| 旧 v1 | 步数耗尽 | 步数耗尽 | 步数耗尽 |
| 旧 v2 | 步数耗尽 | 步数耗尽 | 错误拒绝目标 |
| SUMMARY r1 | 错误声明完成后退出 | 步数耗尽 | 错误拒绝目标 |
| SUMMARY r2、r3 | 错误声明完成后退出 | 步数耗尽 | 步数耗尽 |
| TRACE r1 | 步数耗尽 | 步数耗尽 | 错误拒绝目标 |
| TRACE r2 | 步数耗尽 | 步数耗尽 | 步数耗尽 |

第 41 局首次恢复所需请求数：SUMMARY 在 3 次实际请求内未达到；TRACE 在 2 次实际请求内未达到。不存在“第三次 TRACE 失败候选”：其完整请求为 105,430 字节，超过预先冻结的 100,000 字节上限，未创建逻辑请求槽、未预留调用费用、未发送、无响应或源码。保留了 [完整未发送输入](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_skill_revision_feedback_20261118_01/revision_inputs/TRACE_r3.json) 与 [输入大小检查](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_skill_revision_feedback_20261118_01/requests/revision/TRACE/r3/Input_Size.json)；没有截断、改反馈格式或增加请求。此限制是本次实验的本地冻结输入限制，不能解释为供应商模型上下文能力上限。

两组都从原 v0 出发，使用相同的原始学习材料、四个检查点和配置：`deepseek-flash`、官方 `/chat/completions`、temperature=0、thinking disabled、JSON object、输出上限 8192 tokens、cache=False。旧 v1/v2 的新增诊断没有进入任一组，回归记录和 ScienceWorld 记录没有进入学习输入。每次反馈均明确绑定上一实际执行源码；完整待修订源码保留。TRACE 额外包含真实逐步动作、是否执行、观察、状态、理由、预算和合法动作的无损字典表示。两组最大请求数相同，但实际为 3 次对 2 次，不能声称完成了等次数的三轮对三轮比较，也不能据此认定详细反馈普遍无效或更差。

回归单独记录如下，空缺结果不能写成失败率或成功率。

| 回归角色 | 原有可用游戏／检查点 | 本轮实际执行 | 完成、拒绝或破坏进展结果 |
| --- | --- | --- | --- |
| 正常进展状态 | 8 个游戏／8 个检查点 | 0 | 未评价 |
| 受控取回状态 | 与上述游戏共享／2 个检查点 | 0 | 未评价 |
| 合计 | 8 个去重游戏／10 个检查点 | 0 | 无开发通过候选，未启动 |

本轮没有执行新的原生续跑或 G／R／F 比较，没有拼接旧 G 后缀。因此可以报告“相对原 v0，没有增加来源恢复成功数”，但不能报告节省了原生模型调用，或保证正常可成功任务没有被破坏。边界第 23 局无动作拒绝只支持该检查点未被技能改变。旧实验事实保留：冻结 v0，开发 0/3；旧 v1/v2 当时因交付格式拒绝而未执行；旧正常状态 G=8/8、F=6/8。这些都是历史结果，不回填为本轮成绩。

数据量按来源与活动分别计数，详见 [Data_Roles_and_Counts.json](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_skill_revision_feedback_20261118_01/Data_Roles_and_Counts.json)。

| 计数对象 | 数量与含义 |
| --- | --- |
| 原始学习来源 | 3 个去重游戏、3 条轨迹、131 条动作反馈 |
| 来源结局 | 第 41 局完整失败 50 步；第 12、107 局最终成功且含真实恢复，分别 32、49 步 |
| 开发边界 | 第 23 局，1 个额外来源、1 个检查点 |
| 原有回归 | 8 个游戏、10 个检查点：8 正常自然进展，2 受控取回；自然失败回归检查点为 0 |
| 全部可用角色 | 12 个去重游戏、14 个检查点：12 个自然记录检查点、2 个受控检查点；不是本轮执行量 |
| 本轮实际环境范围 | 4 个既有游戏、4 个开发检查点；28 次独立 reset 与分支评价；新增游戏 0 |
| 新增执行反馈 | 28 条分支摘要、432 条实际动作反馈、445 条 Worker 决策回执；这是三种计量单位，不相加成样本量 |
| 候选记录 | 3 个旧版本＋5 个新提交版本，共 8 个版本记录、7 份不同源码；本轮实际执行 7 个版本，v0 历史复用 |
| 新模型活动 | 5 个逻辑请求、5 次真实发送、5 份完整响应；缓存命中 0，未知或未决请求 0 |
| 项目累计 | 累计去重数尚未核实 |

重复重放、不同检查点、两条修订链和裁剪投影没有增加独立来源数；28 条新增分支反馈也不等于 28 个新游戏。复用 v0 的 4 条分支摘要、31 个后缀动作和 34 条 Worker 回执不计入本轮新增执行。

| 资源组 | 新请求 | 实际 tokens | 保守费用预留（USD） | 环境动作，含前缀 | Worker |
| --- | ---: | ---: | ---: | ---: | ---: |
| 旧 v1/v2 诊断 | 0 | 0 | $0.000000 | 300 | 145 |
| SUMMARY | 3 | 45,432 | $0.215560 | 385 | 155 |
| TRACE | 2 | 48,722 | $0.219174 | 300 | 145 |
| 合计 | 5 | 94,154 | $0.434734 | 985 | 445 |

985 次环境动作包含 553 次前缀重放、432 次技能后缀；全部有返回，无异常或状态未知尝试。Worker 记账时间合计 124,112 毫秒。各项低于 6 请求、$3 保守预留、3000 环境动作、3000 Worker、2 小时墙钟的本轮上限。供应商实际扣费未知；不能把 $0.434734 写成实际账单。TRACE 仅两次请求已使用多于 SUMMARY 三次的 tokens 和保守预留，因此相同轮次上限不意味着相同计算成本。

最小验收覆盖源码无损、交付失败后保留代码、反馈与版本及分支预算绑定，三项通过后进入实验。结案只读核对的 10 项检查通过，67 个旧资产散列未变；新冻结源码、公共材料、反馈投影与执行版本一致。[Validation.json](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_skill_revision_feedback_20261118_01/Validation.json) 保留具体核对和验证器自身一次投影重建纠正说明，实验输入、候选与执行记录未因此改变。新增环境装载修复仅限制官方构造器加载清单中的单个游戏，避免扫描未授权的训练任务内容；评分、环境物理和任务接口未更换。

本轮直接结果是：从真实失败及恢复过程出发，模型产生了可执行的局部修订，但 SUMMARY 三次、TRACE 两次实际修订均未形成有效的来源恢复程序；详细反馈的额外恢复收益未被本次记录观察到。输入长度上限阻止了 TRACE 第三次修订，所以该组尚未完成其三轮上限内的完整尝试。两条链各仅一次探索，开发案例已参与修订，不是独立迁移证据。本轮据此结案，不选失败候选开展新迁移，不扩大为对纯失败信息、整个 FlowEvo、跨场景稳定性或模型能力上限的判断。

完整交付入口：[冻结协议](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_skill_revision_feedback_20261118_01/Protocol.md)、[机器结果 JSON](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_skill_revision_feedback_20261118_01/Results.json)、[开发结果 CSV](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_skill_revision_feedback_20261118_01/Results.csv)、[原始响应与模型请求](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_skill_revision_feedback_20261118_01/requests)、[原样候选源码与版本绑定](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_skill_revision_feedback_20261118_01/candidates)、[分支动作与环境反馈](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_skill_revision_feedback_20261118_01/evaluations)、[费用账本](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_skill_revision_feedback_20261118_01/budget.jsonl)、[环境动作账本](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_skill_revision_feedback_20261118_01/environment_actions.jsonl)、[停止与结案说明](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_skill_revision_feedback_20261118_01/Closure.json)。未生成虚构的回归结果或正常完成执行回执。
