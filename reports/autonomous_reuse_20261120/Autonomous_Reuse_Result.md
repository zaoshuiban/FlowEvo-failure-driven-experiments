# 已有技能自主复用诊断：实际结果

**1. 未人工指定函数，Actor 是否找到并实际调用 HumanEval/31？** 本轮没有。核心 HumanEval/39 的 R 组正常召回 1、20、21，未召回 31，记录为 `RETRIEVAL_MISS`。75 和 72 展示了 31，但均为 `PRESENTED_NOT_USED`。8 个最终程序的公开及完整评分均没有冻结模块调用，`ACTOR_SELECTED_REUSE=false`。

**2. 能否从真实超时状态完成 HumanEval/39？** 可以。G、R 均在一次正常 repair 请求后通过公开检查和固定完整 base+plus 评分。两次独立供应商响应生成相同源码 SHA，修复方式是先排除偶数、再按奇数试除；没有调用归档 31。它证明本次普通修订能够恢复，不能把恢复归因于技能复用。

**3. 自主复用未发生，问题在哪一层？** 39 的可观测阻断在检索：正确旧操作没有进入本次候选展示。不能据此断言 Actor 拒绝了已展示的正确工具，也不能把参数、绑定、返回组合或旧算法记为失败；这些阶段在真实 Actor 运行中未发生。通用调用及官方 guard 下的日志已由预检验证，但预检调用不是自主使用。

**4. 下一轮最值得强教师补学的独立缺口是什么？** 当前尚无已完成资格核查的新算法项。优先核查 MATH 的“保持运算次序的括号可达结果集合”：有 5 份真实最终错误，但也已有模型生成的区间集合程序，且独立来源未确认。应先验证旧实现及来源；只有明确留下能力缺口后才考虑 Teacher。当前新学习项为 0，不为 39 另求素性算法。

本轮已按新授权执行并结案，状态 `CLOSED_COMPLETED`。冻结协议 SHA 为 `957c3bfdc5cfdffdf7b30fb6c089ee3cd7a51a22703f51c4e78fefcd9331c111`。冻结配置和协议保留授权前的历史状态文字，当前执行状态以原始结果及结案审计为准，不事后重写冻结材料。

这是 4 个已曝光开发任务的配对诊断，不是独立泛化确认。39 为真实失败恢复；75、96 为相关开发任务；72 为普通任务。92 因 bool/整数契约歧义在 Actor 执行前排除，没有按运行成绩替换题目。两组均从相同旧库副本开始，每题最多 3 次尝试，组别顺序交替。R 增加正常检索获得的 draft 可调用接口，未人工补入 31，也没有 oracle 候选组。

| 任务 | G 公开 / 完整评分 | R 公开 / 完整评分 | 完整 base / plus（每组） | R 展示的原生任务编号 | 31 的状态 | 冻结模块实际调用（G / R） |
|---|---|---|---|---|---|---|
| HumanEval/39 | PASS / PASS | PASS / PASS | 10/10；2/2 | 1、20、21 | RETRIEVAL_MISS | 0 / 0 |
| HumanEval/75 | PASS / PASS | PASS / PASS | 4/4；93/93 | 31、56、1 | PRESENTED_NOT_USED | 0 / 0 |
| HumanEval/96 | PASS / PASS | PASS / PASS | 10/10；180/180 | 1、20、21 | RETRIEVAL_MISS | 0 / 0 |
| HumanEval/72 | PASS / PASS | PASS / PASS | 6/6；691/691 | 0、31、56 | PRESENTED_NOT_USED | 0 / 0 |

两组都成功 **4**；仅 R 成功 **0**；仅 G 成功 **0**；两组都失败 **0**；未完成或评分异常 **0**。增加成功任务 **0**，相对于 G 损坏的任务 **0**。普通任务 72 也没有错误介入；其未使用素性操作本身不构成问题。总计 1,992 个 base+plus 案例检查只是这 4 个任务的评分，不能作为 1,992 个独立复用来源。PASS 仅表示通过本轮可用检查。

所有程序均无冻结模块选择、开始或返回事件，源码复核也未发现该模块调用。参数合约及返回组合标记为 `NOT_APPLICABLE_NO_CALL`；没有实际返回操作，因此按协议执行的返回替换检查为 0，不追加无对象的消融作业。

39 的两组最终源码 SHA 均为 `8ae50e34d7ab0a5313ab761af6192caf23ba162cc27114078c8d9103c6506a42`。R 的增强子集耗时 4.861724 秒，G 为 4.888134 秒，接近单案例 5 秒限额；这里只报告一次运行通过，不声称稳定性能裕量，也不以数十毫秒差异主张加速。没有追加重复、改变时间限制或换提示词。先前宿主 B2 的成功仍只记 `HOST_ASSISTED_REUSE`，A1/A2/B1/B2 全部保留。

| 成本 | G | R | R − G |
|---|---:|---:|---:|
| 解题 / 修订请求 | 4 | 4 | 0 |
| 原生策略请求 | 0 | 0 | 0 |
| 输入 token | 2,175 | 6,178 | +4,003 |
| 输出 token | 407 | 395 | −12 |
| 总 token | 2,582 | 6,573 | +3,991 |
| 峰时未缓存单价费用上界 | $0.001143 | $0.002329 | +$0.001186 |
| Docker 作业 | 8 | 8 | 0 |
| Worker 账本耗时 | 7.466 秒 | 7.122 秒 | −0.344 秒 |

合计 **8 次 Actor、0 次 Teacher、9,155 token、16 个真实隔离作业**（8 次公开检查＋8 次完整评分）；峰时单价保守核算 **$0.003472**，不是供应商账单。Worker 账本合计 14.588 秒，账本开启至末次结算约 23.637 秒。请求与作业均已结算，无未知已发送或待定请求。另计授权前零模型预检 2 个作业、1.022 秒，不混入 G/R 效果。本轮余量随结案关闭，不用于新实验。

8 份响应的供应商 ID 互不相同；回执 model 均为 `deepseek-flash`，system_fingerprint 为 `bc19ba97cbe016479903222bb1578db6`。冻结时文档版本为 DeepSeek-V4.1-Flash-1017；这不是可验证的权重 SHA。成本按冻结协议单价计算，没有用事后价格改账。

原生成功学习入口保持启用。8 份成功程序均以 `seeded_shadow_compile` 保存到 shadow，新增 active 程序 0、新 primitive 0；没有触发原生策略请求。未把 shadow 程序、单来源 draft 包装或已有 legacy 程序报成 `NEW_SKILL_ACQUIRED`，未绕过两来源准入，也未发布试验库。

所有 8 个最终输出均先锁定，再做私有评分，版本为冻结的 EvalPlus v0.3.1 / HumanEvalPlus v0.1.10。真实 39 请求核查确认含相同失败源码和允许的超时反馈，不含宿主 B 绑定源码、指定 31 调用指令或私有反例。完整评分的执行代码、输入与期望值保存在独立 private 目录，没有回传 Actor、Compiler、技能卡或检索材料。

结案核对了 **1,930 份旧文件哈希不变**、冻结源代码与基础库哈希不变，以及最终源码、依赖包、trace 和完整评分回执的绑定。旧 Pilot、增强审计、宿主能力诊断、TACO 停止状态及保留任务没有改写或续跑。必要接线仅覆盖可信日志、开发权限、真实失败恢复输入、正常检索接口、评分及预算记录；未修改旧素性模块算法。

该固定路径没有展示自主复用，也未增加成功或减少请求，额外消耗 3,991 token。这个结果限定于本次规则与曝光开发样本；不能外推为所有自主复用都不可能。39 的开发诊断到此结束。

证据与交付：

- [冻结协议](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/autonomous_reuse_20261120/Autonomous_Reuse_Protocol.md)
- [原始运行结果](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/autonomous_reuse_20261120/Autonomous_Reuse_Result.json)
- [逐题源码、依赖、回执与费用审计](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/autonomous_reuse_20261120/Execution_Audit.json)
- [封存运行文件哈希](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/autonomous_reuse_20261120/Closed_Run_Manifest.json)
- [历史能力缺口清单](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/autonomous_reuse_20261120/Capability_Gap_Inventory.json)
- [下一轮决策](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/autonomous_reuse_20261120/Next_Learning_Decision.md)
- [空的新学习项清单](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/autonomous_reuse_20261120/Next_Learning_Items.json)
- [本轮必要代码差异](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/autonomous_reuse_20261120/Necessary_Code.diff)

以下是本轮已执行命令的留档，不是再次运行建议；授权仅覆盖已结案的这一次运行：

```sh
PYTHONHASHSEED=0 /Users/majiatong/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python scripts/run_autonomous_reuse.py run --authorization runs/autonomous_reuse_20261120/authorization.json
```
