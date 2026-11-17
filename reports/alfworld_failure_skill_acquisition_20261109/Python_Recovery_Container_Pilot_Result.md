# ALFWorld 单机制 Python 恢复技能真实 Pilot 报告

**实验已完成。** DeepSeek 在第一次修订中移除了全部静态违规，生成的源码通过 Linux Worker 在 11 个真实 TextWorld 来源状态上执行。策略在 11 个状态全部拒绝介入，局部修复和整局获胜均为 0。第二次修订收到拒绝回执后，返回了字节相同的源码。 [运行结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/result.json>)

## 1. 实验范围

| 项目 | 实际设置 |
| --- | --- |
| Run ID | `real:python_recovery_container_pilot_20261112_01` |
| 协议 SHA-256 | `2be1114573c96f296cf46776c4c658c4cc9ef69aab3b13290abfc113921d314e` |
| 机制与数据 | 已归纳的容器前置条件机制，11 个已曝光的失败后来源检查点，另有 21 条开发边界 |
| 模型 | `deepseek-flash`，非思考模式，temperature 0 |
| 请求范围 | 初稿 1 次、修订 2 次，三次响应均为 HTTP 200、`finish_reason=stop` |
| 模型请求时间 | 2026-11-12 14:44:32–14:46:03 UTC |
| 权限范围 | Shadow 来源验证，独立 Gate 游戏 0 局，正式发布 0 个 |

本轮固定历史机制，检查真实模型能否交付合规源码、执行首个恢复动作，以及能否利用候选自身的反馈改善策略。来源状态用于开发验证，边界结果在最后一次模型请求之后生成。 [实验协议](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_failure_skill_acquisition_20261109/Python_Recovery_Container_Pilot_Protocol.md>)、[运行配置](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/protocol.json>)

## 2. 三次真实提交

| 提交 | JSON 交付 | 静态检查 | 来源实际执行 | 局部修复 / 获胜 |
| --- | --- | --- | --- | --- |
| 初稿 | 通过 | 拒绝，4 处模块级 `re.compile(...)` | 未触达 | 未触达 |
| 修订 1 | 通过 | 通过，0 处违规 | Worker 调用 11 次，均拒绝介入，候选动作 0 次 | 0/11 · 0/11 |
| 修订 2 | 通过 | 通过，与修订 1 的源码 SHA-256 完全一致 | 复用修订 1 的 11 条回执，新增 Worker 调用 0 次 | 复用 0/11 · 0/11 |

初稿的违规位置为 4:12、5:12、6:14、7:14。第一次修订收到这四处位置和规则诊断后，交付了合规的完整源码。三次响应产生两份不同源码，其中一份通过静态检查并注册为 Shadow。此前结案的三机制 Pilot 有 7 次真实请求和 0 次 Worker 执行，本轮首次在这个容器 Pilot 中触达了真实模型源码的 Worker 验证。两次 Pilot 的结果属于不同运行，当前证据记录了交付路径上的进展。 [初稿回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/candidate_0/initial/attempt.json>)、[修订 1 回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/candidate_0/revision_01/attempt.json>)、[修订 2 回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/candidate_0/revision_02/attempt.json>)

## 3. 为什么 11 次都拒绝

修订 1 能从失败的投递动作解析目标容器，也找到了当前合法的打开命令。它随后要求投递命令在打开之前就已合法。这个检查提前使用了下一阶段的前置条件。11 次实际拒绝的原因均为 `repeat move not admissible`。 [策略代码](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/candidate_0/revision_01/decoded.py:115>)

| 目标容器 | 来源序号 | 失败后打开目标容器合法 | 失败后投递合法 | 历史打开后投递变为合法 |
| --- | --- | ---: | ---: | ---: |
| 保险柜 | 33、54 | 2/2 | 0/2 | 2/2 |
| 抽屉 | 40、47、66、70 | 4/4 | 0/4 | 4/4 |
| 微波炉 | 72、86 | 2/2 | 0/2 | 2/2 |
| 冰箱 | 88、94、106 | 3/3 | 0/3 | 3/3 |
| 合计 | 11 个来源 | **11/11** | **0/11** | **11/11** |

最后一列来自已归档的真实恢复后缀，仅用于只读核查。环境共执行 225 步原始前缀重放，本轮候选产生的新环境动作数为 0。 [冻结来源清单](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/protocol.json>)、[来源执行回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/candidate_0/revision_01/source_1.json>)

修订 2 收到 11 条完整投影的来源拒绝回执。逐步反馈只有 `status=declined` 和 `worker_status=OK`，具体的拒绝原因保存在宿主回执中。修订 2 返回相同源码，按相同上下文复用原评估。局部修复、恢复完成和获胜的配对改善与退化均为 0。现有记录无法判断，把具体拒绝原因纳入反馈是否会改变模型输出。 [反馈投影](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/python_recovery_feedback.py:247>)、[配对结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/result.json>)

## 4. 开发边界、账本与隔离

修订 1 在 18 条明确不适用状态和 3 条信息不足状态上均拒绝介入，误触发和接口错误均为 0。11 个适用来源也均被拒，因此这组边界结果只记录了实际拒绝行为。29 次真实 Worker 调用包含 11 次来源调用和 18 个不同的边界执行上下文。21 条边界中有 3 条复用同上下文的 Worker 回执。 [边界回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/candidate_0/revision_01/boundaries.private.json>)

| 请求 | 输入 Token | 输出 Token | 峰时无缓存费用估算 | 账本费用占用 |
| --- | ---: | ---: | ---: | ---: |
| 初稿 | 5,708 | 1,943 | $0.0040440 | $0.031604 |
| 修订 1 | 8,113 | 1,857 | $0.0046623 | $0.042627 |
| 修订 2 | 7,925 | 1,858 | $0.0046071 | $0.042010 |
| 合计 | **21,746** | **5,658** | **$0.0133134** | **$0.116241** |

实际记录 **27,404 Token**，其中缓存命中输入 6,272 Token。峰时无缓存估算使用运行时的冻结计价口径。账本按保守费率记录费用占用，硬上限为 $0.20，供应商实际账单未取得。3 次请求均已结算，未知和待结算请求均为 0。逐项核对了请求、响应、源码及协议哈希，旧 Pilot 的 77 份文件与验收前的清单一致。 [供应商回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/provider.jsonl>)、[费用账本](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/budget.jsonl>)

## 5. 研究结论

- **Q1 静态交付已达成。** 一次有界修订使模型源码通过既有静态安全规则，随后由真实 Worker 执行。
- **Q2 首动作与来源修复未达成。** 策略统一拒绝了 11 个可打开目标容器的来源状态。阻断发生在动作选择，TextWorld 未接收候选动作。
- **Q3 拒绝反馈修订未观察到改善。** 第二次修订提交了相同源码。本轮没有候选动作后的环境反馈，执行失败后的纠错能力仍待观测。
- **独立跨游戏迁移未触达。** 本轮证据来自已曝光来源及开发边界，唯一可执行候选保持 Shadow。

结果文件 SHA-256 为 `674a9f63f9008ce69f35fca6094410f185cc72cb965d4815f711d6b31a4d40cc`。 [机器可读结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/result.json>)
