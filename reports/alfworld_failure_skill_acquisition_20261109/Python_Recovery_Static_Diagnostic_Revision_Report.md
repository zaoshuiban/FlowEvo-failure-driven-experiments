# Python 恢复技能静态诊断与修订回归报告

本次修复完成零 API 验收。新版能定位同一错误类别下的多个违规节点，允许有剩余额度的部分修复继续，并在格式拒收后携带最近一次正式解码的源码。旧 Pilot 的 6 份源码仍被原安全规则拒绝。真实模型请求和独立 Gate 执行均为 0。

## 1. 修改范围

| 文件 | 主要函数与变更 |
| --- | --- |
| [math_operators.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/failure_evo/math_operators.py:101>) | `validate_math_source` 共用原安全谓词。按需增加逐节点诊断，保留旧调用的结果字典。 |
| [failure_learning.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/failure_learning.py:77>) | `static_check_detailed` 在相同准入结果上增加位置、片段和检查状态。注册与 Worker 仍调用既有权威检查。 |
| [python_recovery_feedback.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/python_recovery_feedback.py:340>) | `revision_payload` 关联最近合法源码、拒收回执与未解决诊断。`compare_static` 和 `revision_signature` 分别记录变化、生成去重依据。 |
| [run_alfworld_python_recovery_feedback.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:646>) | `record_revision_progress`、`next_step` 将完整诊断接入原有限调度。新协议标记为 `pilot-v2`。 |
| [test_alfworld_python_recovery_feedback.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/test_alfworld_python_recovery_feedback.py>) | 用原 Pilot 响应做只读回放，增加诊断位置、格式变动、预算及合法源码继承测试。 |

新入口比较历史来源时，旧协议中两个静态检查模块的哈希仍按归档校验。新版冻结绑定的是当前源码，来源和边界的核对范围保持原样。此处只变更诊断及版本绑定，候选源码、权限判定、预算账本和 Worker 执行接口沿用既有规则。 [历史绑定核对](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:103>)

## 2. 静态诊断与真实源码回放

旧反馈把所有 `TOP_LEVEL_EXECUTION` 折叠为一个类别。新反馈逐处记录错误代码、规则 ID、行号、列号、AST 节点类型、最长 192 字节的源码片段、规则及允许的结构说明。行号与 UTF-8 字节列号从 1 开始。没有可靠位置时保留空位置，语法解析失败时，后续接口和权限检查标为 `NOT_CHECKED`。已有规则仍拒绝模块级执行。 [逐节点记录器](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/failure_evo/math_operators.py:57>)、[离线历史回放](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_static_diagnostic_verified.upriI2/saved_static_pilot/result.json>)

| 机制 | 初稿违规位置 | 后续版本违规位置 | 结构比较与调度 |
| --- | --- | --- | --- |
| 容器 | 3:12、4:12，共 2 处 `Call` | 修订 1 为 3:12，共 1 处 | `ERRORS_REDUCED`。去掉一处，未引入新节点。回放允许用剩余的第 2 次修订。 |
| 台灯 | 3:16、4:10、5:8，共 3 处 `Call` | 修订 1 为 3:16、4:10、5:11，共 3 处 | `ERRORS_CHANGED`。删去一处旧节点，同时出现一处新节点。静态仍拒绝，未记为安全改善。 |
| 导航 | 3:10、4:16，共 2 处 `Call` | 修订 1 格式拒收。修订 2 为 4:10，共 1 处 | 修订 1 的静态状态为 `NOT_CHECKED`。修订 2 相对初稿移除一处违规，仍被拒绝，达到修订上限。 |

以上位置均来自归档的真实候选。历史回放使用 7 份原始响应，容器和台灯新增可达的槽位各用一个测试夹具 `ABSTAIN` 结案。这两个回执只用于证明调度能到达剩余额度，历史正式结果仍保留原终止原因。 [原 Pilot 结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/result.json>)、[回放请求](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_static_diagnostic_verified.upriI2/saved_static_pilot/captured_wires.private.json>)

## 3. 导航格式拒收后的上下文

导航修订 1 的整份响应继续拒收。新版诊断记录 `INVALID_JSON`、`EXTRA_DATA_AFTER_JSON` 及原响应第 3 行第 1 列。完整原始响应留在供应商日志，修订请求只接收定长的响应哈希、阶段和版本引用。拒收回复的附加文字与其中的源码均不进入候选。拒收封套中可单独归档的源码也只供私下审计。

历史回放中，修订 2 的 `previous_code` 与导航初稿完全一致，SHA-256 为 `5719afedf95fa9e46b2869fe5d1f51f6b747989eb6213e0a4fdc572affcec5ce`。同一请求携带当前 JSON 错误、初稿的两处未解决静态违规、最新拒收响应引用、当前与父版本、源码所属版本及剩余额度。字节代理为 24,237，低于 65,536 上限。之前没有正式解码源码时，该字段保持空值。 [修订 2 请求归档](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_static_diagnostic_verified.upriI2/saved_static_pilot/captured_wires.private.json>)、[拒收原始归档](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/provider.jsonl>)

若上一次正式源码已执行，格式拒收后的回退上下文还保留该源码实际产生的公开回执，并绑定到对应的旧版本。开发边界、私有评分见证和人工恢复路线仍隔离。输入上限沿用既有投影，正式源码保持完整，超限按 `INPUT_LIMIT` 结案。

## 4. 停止与恢复

对比逐项记录源码字节变化、违规数、位置、规范化 AST 结构、引入或消除的节点及新的执行反馈。去重签名使用规则与节点摘要的多重集，保留重复节点的计数。行号变化、空行和注释不产生新的静态证据。AST 摘要使用迭代遍历，深层违规节点也能返回诊断。

部分违规消除和同类别节点实质变化可使用仍未消费的修订额度。相同完整诊断及执行证据继续终止。初稿最多一次，修订最多两次。静态通过的候选进入原来源执行流程，同源码且同执行上下文复用既有结果。预算不足和 `SEND_UNKNOWN` 仍阻断派发，完整且可重放的已结算响应仍按原回执恢复。 [调度判定](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:658>)

## 5. 测试、执行链与历史完整性

- 通过 **34 项零 API 测试**。覆盖历史响应、授权前阻断、父版本链、已结算响应复用、预算耗尽、`SEND_UNKNOWN`、同上下文去重、不同上下文区分和原生成功学习。 [最终测试日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_static_diagnostic_verified.upriI2/console.log>)
- 将修改前和修改后的静态检查结果逐项比对 **952 例**。数学检查 509 例，环境检查 443 例，均保持原结果字典。六份真实归档源码仍为拒绝。格式改动测试和 1,600 层 AST 诊断测试也通过。
- 既有 Mock 策略完成真实 Linux Worker 与 TextWorld 回归。合法动作由宿主执行，下一步读取新观察与状态。容器初稿 11 次真实观察后触发夹具异常，局部修复 0/11。修订从原点重跑，11/11 局部修复并获胜。台灯 3/3 获胜。导航 8 次首步执行，局部修复 0/9，另有 1 次非法动作拒绝。四份可执行版本的开发边界回执仍单列。 [真实环境回归](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_static_diagnostic_verified.upriI2/real_sources/result.json>)
- 真实环境工程回归累计 5 次 Mock 生成、159 次实际 Worker 调用、595 步环境执行，其中 6 步为中断恢复。候选均按既有安全和 Shadow 路径运行。独立 Gate 和真实模型请求为 0。
- 开发边界按每版 18 条明确负例和 3 条信息不足例计数。容器初稿、容器修订、台灯初稿、导航初稿的明确误触发分别为 3、3、2、2，信息不足触发分别为 1、0、0、0。导航另有 1 次边界接口错误。导航同源码修订引用原评估。
- 旧 Pilot 整个目录的 **77 个文件**前后 SHA-256 一致，包括结果、响应、源码、账本和原授权文件。验收记录放在新的 Git 排除测试目录。未生成正式新 Run 授权。 [旧结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/result.json>)、[旧预算账本](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/budget.jsonl>)

| 核心回执 | 文件 SHA-256 |
| --- | --- |
| [测试日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_static_diagnostic_verified.upriI2/console.log>) | `0198321b4a1e886640bda29e40746f50cf3389f2c94f6c75b980c2fae484689a` |
| [静态历史回放](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_static_diagnostic_verified.upriI2/saved_static_pilot/result.json>) | `c0a42f0a81df1abc56b931faadfb36cfb42b9bcabe98355ed1368d9ca68f2836` |
| [回放修订请求](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_static_diagnostic_verified.upriI2/saved_static_pilot/captured_wires.private.json>) | `7ff19cfb04c9e2be25d0cbd4e133cca4d5c73906f13410296cbc7457e8bbc990` |
| [真实环境工程回归](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_static_diagnostic_verified.upriI2/real_sources/result.json>) | `62ce2d6493005ad891b7bed31e270db33cc067239ad2cec8c23b0894b62d8fb5` |

## 6. 工程结论与下一步

静态合规夹具已验证能够进入 Worker、执行并接收下一步反馈。原 Pilot 的真实候选依然没有跨过静态检查。新版是否能让真实模型利用这些诊断交付合规源码，仍待单独实验。

下一轮建议只冻结原序第一个机制，也就是 11 个已曝光容器检查点。使用一次初稿、最多两次修订。静态通过后才执行来源回放，失败时才把候选自身的实际公开反馈用于余下修订。单轮结论限定为交付和执行闭环。若需评估新诊断的独立效果，另设预算匹配的反馈对照。本次停在零 API 验收。
