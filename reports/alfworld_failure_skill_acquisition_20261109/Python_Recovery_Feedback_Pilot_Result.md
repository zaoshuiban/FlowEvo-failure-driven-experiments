# Python 恢复技能与执行反馈修订 Pilot 结果

本轮按冻结协议完成。真实 DeepSeek 请求 7 次，6 份提交通过交付封套，0 份通过静态安全检查。所有提交均在 Worker 之前结案。23 个来源检查点和 21 条开发边界均未触达，独立 Gate 执行为 0。

| 运行身份 | 核对结果 |
| --- | --- |
| Run ID | `real:python_recovery_feedback_pilot_20261112_01` |
| 规范化协议 SHA-256 | `cae5f6020997a54ad2b22bbc4ea43ca49d3c592f217fbe0934c402f1ec2eb2ae` |
| 运行范围 | `REAL_SOURCE_ONLY`，发布权限为 `SHADOW_SOURCE_ONLY`，实际注册 0 个候选 |
| 供应商与计量 | 7 次 HTTP 200，7 次响应归档并结算 Token，所有 `finish_reason=stop`，未知及待结算请求 0 |
| 返回模型标识 | 7 次均为 `deepseek-flash`，返回的 `system_fingerprint` 均为 `bc19ba97cbe016479903222bb1578db6` |
| 首次发送至最后一份原始响应 | 2026-11-12 10:05:38–10:06:24 UTC |

所有来源、边界、参数、修订上限和评分保持冻结，未追加请求或修改生成源码。结案后逐项复核了协议绑定的 122 份源码和 1,004 份历史文件。 [逐版本结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/result.json>)、[冻结协议](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/protocol.json>)、[供应商原始回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/provider.jsonl>)

## 1. 三类机制的交付与终止

| 机制 | 请求 | 封套通过 | 静态通过 | 最后一次提交 | 停止原因 |
| --- | ---: | ---: | ---: | --- | --- |
| 容器前置条件 | 2 | 2 | 0 | 修订 1 静态拒绝 | `NO_NEW_DIAGNOSTIC` |
| 台灯交互 | 2 | 2 | 0 | 修订 1 静态拒绝 | `NO_NEW_DIAGNOSTIC` |
| 导航无效果 | 3 | 2 | 0 | 修订 2 静态拒绝 | `REVISION_LIMIT_REACHED` |

主要结果按各组最后一次提交计算。容器和台灯均在修订 1 后重复出现同一静态错误类别。导航的修订 1 产生新的格式诊断，触发了冻结额度内的修订 2。三组共剩余 2 个调用槽位，按协议结案。没有弃权或供应商标注的输出截断。 [调度和版本父链](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/result.json>)

| 版本 | 正式结果 | 只读定位 | 输入 / 输出 Token |
| --- | --- | --- | ---: |
| [容器初稿](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/candidate_0/initial/attempt.json>) | 封套通过，`TOP_LEVEL_EXECUTION` | 第 3、4 行两个模块级 `re.compile(...)` | 5,708 / 1,365 |
| [容器修订 1](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/candidate_0/revision_01/attempt.json>) | 封套通过，`TOP_LEVEL_EXECUTION` | 移除一处模块级调用，第 3 行仍有一处 | 6,877 / 1,414 |
| [台灯初稿](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/candidate_1/initial/attempt.json>) | 封套通过，`TOP_LEVEL_EXECUTION` | 第 3–5 行三处模块级 `re.compile(...)` | 2,438 / 1,390 |
| [台灯修订 1](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/candidate_1/revision_01/attempt.json>) | 封套通过，`TOP_LEVEL_EXECUTION` | 一处正则定义改变，第 3–5 行仍有三处模块级调用 | 3,592 / 1,339 |
| [导航初稿](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/candidate_2/initial/attempt.json>) | 封套通过，`TOP_LEVEL_EXECUTION` | 第 3、4 行两处模块级 `re.compile(...)` | 4,543 / 1,223 |
| [导航修订 1](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/candidate_2/revision_01/attempt.json>) | `SCHEMA_REJECTED`，静态未检查 | 完整 JSON 对象后接额外说明，原响应第 3 行第 1 列报 `Extra data` | 5,551 / 2,558 |
| [导航修订 2](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/candidate_2/revision_02/attempt.json>) | 封套通过，`TOP_LEVEL_EXECUTION` | 第 4 行仍有一处模块级 `re.compile(...)` | 4,692 / 1,092 |

六份正式交付的源码均可解析为 Python AST，归档源码字节与各自原始响应及记录哈希一致。冻结静态规则只允许模块级赋值初始化为字面量。正则模块本身允许导入，在模块加载时调用 `re.compile` 触发了执行限制。现行生成提示已明确列出这一约束。 [静态规则](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/failure_evo/math_operators.py:14>)、[生成提示](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/python_recovery_feedback.py:73>)

导航修订 1 的原始尾部文字准确指出模块级调用的问题。只读解析还确认，前置 JSON 对象里的源码与导航初稿的 SHA-256 完全相同，含相同的两处违规。冻结规则要求完整响应为单个 JSON 对象，该响应保持格式拒收。后续修订按原协议收到 `INVALID_JSON` 诊断，`previous_code=null`，因为上一份响应没有产生正式可解码源码。 [导航修订 1 回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/candidate_2/revision_01/attempt.json>)、[带原文的供应商归档](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/provider.jsonl>)

## 2. 反馈实际进入了哪一层

4 次修订请求均按冻结格式送达。三类机制的首轮修订各自带上一份完整源码及 `TOP_LEVEL_EXECUTION` 诊断。导航第二轮收到完整响应的格式错误。4 个 wire 的 `source_feedback` 均为空，且反馈投影未触发压缩。

容器修订确实减少了一个违规点，但静态错误类别保持不变。台灯修订更换了一个模块级正则，违规总数不变。静态反馈只提供类别，未给出仍在执行的具体行与节点。该诊断信息不足以区分“修掉其中一处”与“原错误类别完全未变”，冻结的 `NO_NEW_DIAGNOSTIC` 因此按类别终止了容器和台灯。模型如何利用真实环境执行反馈，在本轮没有可评价的观测。 [实际请求载荷与原始响应](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/provider.jsonl>)、[反馈投影](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/python_recovery_feedback.py:294>)、[修订触发与去重](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:620>)

## 3. 逐来源结果与适用边界

“未触达”表示对应版本在环境入口之前被拒，来源分母仍保留。 “未安排”表示该组提前终止，未产生该版本。

| 机制 | 来源序号 | 初稿 | 修订 1 | 修订 2 |
| --- | ---: | --- | --- | --- |
| 容器 | 33 | 未触达 | 未触达 | 未安排 |
| 容器 | 40 | 未触达 | 未触达 | 未安排 |
| 容器 | 47 | 未触达 | 未触达 | 未安排 |
| 容器 | 54 | 未触达 | 未触达 | 未安排 |
| 容器 | 66 | 未触达 | 未触达 | 未安排 |
| 容器 | 70 | 未触达 | 未触达 | 未安排 |
| 容器 | 72 | 未触达 | 未触达 | 未安排 |
| 容器 | 86 | 未触达 | 未触达 | 未安排 |
| 容器 | 88 | 未触达 | 未触达 | 未安排 |
| 容器 | 94 | 未触达 | 未触达 | 未安排 |
| 容器 | 106 | 未触达 | 未触达 | 未安排 |
| 台灯 | 55 | 未触达 | 未触达 | 未安排 |
| 台灯 | 74 | 未触达 | 未触达 | 未安排 |
| 台灯 | 111 | 未触达 | 未触达 | 未安排 |
| 导航 | 56 | 未触达 | 未触达 | 未触达 |
| 导航 | 62 | 未触达 | 未触达 | 未触达 |
| 导航 | 71 | 未触达 | 未触达 | 未触达 |
| 导航 | 78 | 未触达 | 未触达 | 未触达 |
| 导航 | 85 | 未触达 | 未触达 | 未触达 |
| 导航 | 95 | 未触达 | 未触达 | 未触达 |
| 导航 | 96 | 未触达 | 未触达 | 未触达 |
| 导航 | 113 | 未触达 | 未触达 | 未触达 |
| 导航 | 119 | 未触达 | 未触达 | 未触达 |

所有版本的返回动作、环境执行动作、首步观测和获胜记录均为 0。因为来源分支未启动，逐来源改善与退化、局部修复率、过度拒绝率均为 **不可评价**。容器尚无目标实例、解除投递阻碍及投递的真实证据。台灯尚无获得可交互状态及有效交互的真实证据。导航尚无合法移动或搜索进展的真实证据。21 条开发边界均未执行，误触发和接口错误率也不可评价。 [每版的未触达分母](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/result.json>)

## 4. Token、费用与实际执行资源

| 项 | 实际记录 |
| --- | --- |
| 模型请求 | 7 / 9，全部收到响应并结算 Token |
| 供应商输入 Token | 33,401，其中 3,200 命中缓存、30,201 未命中 |
| 供应商输出与总 Token | 10,381 输出，43,782 总计 |
| 冻结峰时无缓存估算 | **$0.0224775** |
| 按记录时段和缓存字段估算 | **$0.01076835**，7 次请求均在 UTC 10:00 后的公布谷时 |
| 账本费用占用 | **$0.194528**，保守预留口径 |
| 真实账单 | 未查询，`actual_billed_usd=null` |
| 本机资源 | Worker 0 次、0 秒。环境原始前缀、候选动作和恢复重放均为 0 步 |

按时段估算采用官方谷时每百万 Token $0.003 缓存命中、$0.15 未命中和 $0.60 输出。冻结账本的预留规则仍按本轮授权硬上限 $0.60 约束。 [预算账本](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/budget.jsonl>)、[DeepSeek 官方价格表](https://api-docs.deepseek.com/quick_start/pricing/)

## 5. 结论与下一步

1. **交付与静态通过数。** 容器 2 份交付通过、0 份安全通过。台灯 2 份、0 份。导航 2 份、0 份，另有 1 份格式拒收。
2. **真实环境动作。** 0 次。程序未进入 Worker。
3. **是否使用了上一版实际公开执行反馈。** 4 次修订都收到交付或静态诊断。实际环境反馈为零。
4. **来源改善或退化。** 23 个检查点均未触达，无可评价的配对。
5. **三种机制的证据层次。** 均到达真实模型源码交付和静态拒绝，尚未到达执行和来源修复。
6. **最终误触发或过度拒绝。** 未执行开发边界或来源，无法评价。
7. **下一步。** 来源执行仍受静态交付阻断，暂不进入独立迁移。若单独启动下一阶段，优先验证模块级违规位置的诊断能否识别剩余违规。现有安全规则与单对象交付契约继续作为前提。

本轮给出了真实交付、修订及静态阻断的证据。自主来源修复与真实执行反馈的增量仍未触达。结案后没有补发请求或开展下一轮实验。

### 冻结工件和字节 SHA-256

| 工件 | SHA-256 |
| --- | --- |
| [protocol.json](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/protocol.json>) | `a1c319c35e3a19c25f2f15df55a189513b2f8b5486c45385adeb2d06f8d85415` |
| [result.json](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/result.json>) | `0fc6beccf7f3df78d8160db490ba745923e4853b661911248887a5bde2e8931f` |
| [provider.jsonl](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/provider.jsonl>) | `bd1e055f80233dbd7a53e293090db6fe652a9f24051e1a4f1b48eabfa2246a6b` |
| [budget.jsonl](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/budget.jsonl>) | `2ff8a569003da03d81b0a50d3dd201878b617ae343f83207aebae72f1f5a4753` |
| [console.log](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/console.log>) | `e99b60c24a2c72bb39bf8173eec06ba63edd8e17a275c89cee3c3d4faf817ae9` |
