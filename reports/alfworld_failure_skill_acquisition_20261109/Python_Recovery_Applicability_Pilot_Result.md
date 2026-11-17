# ALFWorld S1 适用边界学习 Pilot 报告

**S1 保留了 11/11 来源修复，明确开发负例仍误触发 3/18。** 同检查点的人工 Rule 保留 11/11 来源修复并阻断三次误触发。模型交付了可执行的适用性判断，但其判断未使用当前任务目标。本轮结果来自已曝光开发状态。 [逐检查点结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_container_boundary_learning_20261113_02/result.json>)、[上一轮边界审查](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_failure_skill_acquisition_20261109/Python_Recovery_Applicability_Boundary_Audit.md>)

## 1. 冻结新增学习证据

取样规则在模型请求和开发比较之前确定。读取已结案的 120 局正式基线与 16 局校准归档中的公开环境回执，按任务和步数排序，每类最多两局，每局最多一条。排除原 11 个来源游戏和所有旧边界所依赖的游戏。新增记录保留原目标、截至该步的公开历史、实际观察和合法命令。 [取样规则](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_container_boundary_learning_20261113_02/selection_rules.json>)、[历史训练清单](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_container_boundary_learning_20261113_02/historical_training.private.json>)

第一次离线核查发现，单物体解析器会把“双物体数量”误读成对象类别，导致有效投递被当作不相容。修正了该识别规则后，使用新目录 `_02` 冻结输入，`_01` 只保留离线准备记录。正式选取的 9 条记录均来自 9 个不同游戏。

| 自然公开证据 | 冻结条数 | 证据含义 |
| --- | ---: | --- |
| 投递参数与最终任务目标不一致 | 2 | 可能是合法的中间操作，未标为失败。 |
| 取物后尚无对应加工回执 | 2 | 加工尚未得到公开确认。 |
| 对同一实例的成功加工回执 | 2 | 证实该实例已执行目标所需的加工。 |
| 多个同类目标实例同时可开 | 2 | 记录可见实例歧义。 |
| 非投递任务中出现合法打开动作 | 1 | 打开动作合法，任务目标要求的是检查。 |

筛选未找到新的真实无效果投递或明确目标实例冲突。实例歧义与显式冲突分开记。新增前缀未附未来后缀。已有 11 条来源仍使用原先允许的公开恢复证据。18 条旧负例和 3 条信息不足样例仅参与回归，Rule 源码、标签及独立游戏材料均未进入模型输入。 [冻结的模型输入](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_container_boundary_learning_20261113_02/learning_input.private.json>)

## 2. 同检查点三组比较

S0 使用归档策略。S1 与 Rule 都在介入前给出适用判断，只有 MATCH 才沿用同一份恢复源码。DeepSeek 只生成 S1 的 `applicability_gate(context)`，只能输出 MATCH、DECLINE 或 UNKNOWN。独立 Worker 运行模型原始门控源码与固定的输出适配层。恢复源码 SHA-256 始终为 `233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37`。 [冻结协议](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_container_boundary_learning_20261113_02/protocol.json>)、[门控适配层](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/recovery_applicability.py:59>)、[独立冻结的 Rule](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/recovery_applicability_rule.py:9>)

| 指标 | S0 | S1 | Rule |
| --- | ---: | ---: | ---: |
| 正确介入并局部修复 | 11/11 | 11/11 | 11/11 |
| 整局获胜 | 11/11 | 11/11 | 11/11 |
| 明确负例选择动作 | 3/18 | 3/18 | 0/18 |
| 明确负例拒绝 / UNKNOWN | 15 / 0 | 15 / 0 | 17 / 1 |
| 信息不足样例选择动作 | 0/3 | 0/3 | 0/3 |
| 信息不足样例拒绝 / UNKNOWN | 3 / 0 | 2 / 1 | 2 / 1 |
| 门控执行错误 | 0 | 0 | 0 |

S1 获准的 11 个来源均从相同的失败后状态重新进行 TextWorld 验证。S0 使用绑定相同起点的归档回执，Rule 在 MATCH 时沿用该同起点回执。边界测试记录是否选择动作，未将负例动作发送给环境。

- 对比 S0，S1 的来源修复没有改善或退化，3 次误触发完全重合。
- 对比 Rule，S1 在相同的 11 个来源上都成功，但新增 3 次明确负例的错误动作选择。
- S1 在一条证据不足样例上输出 UNKNOWN。三条明确误触发仍分别是目标错误、阶段不符和实例冲突。

生成的门控从历史投递、关闭观察和合法打开命令推断可介入，未读取 `goal`，也未核对目标的加工前提。三个负例共享同一物理状态，只有任务目标发生变化，因此这份代码对三条输入作出相同判断。本轮只有一次模型提交，结论限于这份生成门控。 [模型生成的判断源码](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_container_boundary_learning_20261113_02/candidate_0/applicability/gate.py:73>)

## 3. 独立评价材料

游戏清单由固定种子 `20261113` 选取，使用元数据和曝光记录。两层清单按游戏哈希、轨迹哈希和任务组排除已知重叠，且避开本轮训练、来源和旧边界回归场景。模型请求阶段不读取这份评价清单。 [隔离评价清单](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_container_boundary_learning_20261113_02/independent_inventory.private.json>)

| 清单 | 游戏 | 场景 | 任务组 | 场景身份 |
| --- | ---: | ---: | ---: | --- |
| 原严格场景隔离池 | 34 | 3 | 14 | 与全部已知项目曝光场景隔离 |
| 扩充池 | 46 | 28 | 46 | 游戏、轨迹和任务组未见。场景在项目其他历史运行中已曝光，与本轮开发场景隔离 |
| 合计 | 80 | 31 | 60 | 两层分别报告 |

扩充部分包括保险柜 6 局、抽屉 8 局、冰箱 8 局、微波炉 8 局、橱柜 8 局、其他目标 8 局。保险柜按固定的场景和任务组上限留到 6 局，低于原定 8 局配额。合并清单仍保留 13 局橱柜目标。

当前冻结的是游戏身份和目的地分层。独立正负标签与原生公开检查点尚未建立，独立游戏执行数为 0。扩充层可为未见游戏迁移提供材料，严格的全项目未见场景覆盖仍不足。后续验证需要先锁定无干预前缀及正、负、不确定标签，再让三组面对同一批状态。主要指标同时记录目标相关的实际修复与错误介入。

## 4. 验收与资源

- 11 项零 API 专项及既有回归通过。包含证据来源绑定、原源码和 Rule 隔离、严格门控、离线请求恢复、UNKNOWN 阻断，以及真实 Worker 与 TextWorld 的工程回放。 [真实环境工程验收日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_applicability_acceptance.yUQ1Ac/console.log>)
- 真实运行共一次 DeepSeek 请求，13,024 输入和 1,643 输出 Token。峰时无缓存费用估算 **$0.0058788**，账本费用占用 **$0.064343**，硬上限 **$0.10**。未知或待结算请求为 0。 [运行预算账本](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_container_boundary_learning_20261113_02/budget.jsonl>)、[DeepSeek 官方计价](https://api-docs.deepseek.com/quick_start/pricing/)
- 真实 Worker 共 51 次，29 次为适用性判断、22 次为冻结恢复动作的选择。环境执行 225 步原始前缀及 22 步恢复动作。旧结果的 SHA-256 复核一致，S1 保留 Shadow。 [运行结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_container_boundary_learning_20261113_02/result.json>)

运行身份为 `real:alfworld_container_boundary_learning_20261113_02`。规范化协议 SHA-256 为 `d62b9310d3bce0646b49fcf2159204f051b9d59a3956d173bcd36c56e3a8a882`。结果文件 SHA-256 为 `6e118333586d983a46c4d717064bcee3e461e578a93d00c218cb03b019ee742c`。
