# Python 恢复策略的开发反馈闭环与零 API 验收

基线分支为 `feat/v4-reliability-capability`，提交为 `c7e3514481a19960ec8c4efa958a34f56bce08c9`。验收使用 B v14 已冻结的 23 个来源检查点和 21 条已曝光开发边界。源码由测试中的 Mock 返回，动作由 Linux Worker 选出、由真实 TextWorld 执行。真实模型调用、独立 Gate 游戏与技能发布均为 0。

## 1. 实际调用链与改动

| 新增文件 | 职责 |
| --- | --- |
| [python_recovery_feedback.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/python_recovery_feedback.py>) | 用同一份 Pydantic 定义生成初稿和修订 Schema，严格接收 `PROPOSE` 或 `ABSTAIN`。组织已冻结证据、完整上一版源码、字段及安全诊断和候选公开回执。 |
| [run_alfworld_python_recovery_feedback.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py>) | 校验冻结来源，调度初稿与最多两轮修订，保存精确源码、父版本、来源执行与预算回执，最后评估开发边界。入口只接受注入的 Mock sender。 |
| [test_alfworld_python_recovery_feedback.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/test_alfworld_python_recovery_feedback.py>) | 测试交付、证据隔离、账本和中断恢复。四份手写策略夹具覆盖三类机制，真实 Worker 和 TextWorld 的闭环案例单独标记。 |

`frozen_sources` 读取原机制归纳的供应商回执和 B v14 冻结题序。 `initial_payload` 投影学习证据。 `acquire_group` 调用已有 `stage_request`、`BoundedCompiler` 和 `PersistentBudget`。传输复用可传入解析器的 `analyze` 路径，实际线上载荷的任务字段固定为 `initial`、`revision_01` 或 `revision_02`，提示和 Schema 有独立哈希。供应商原始回执先归档，解码源码按 UTF-8 字节另存并计算 SHA-256，拒收封套中可解码的源码也会保留。格式未通过时，静态和执行检查保持 `NOT_CHECKED` 或 `NOT_RUN`。 [交付解析](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/python_recovery_feedback.py:107>)、[调度入口](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:471>)

`register_environment_candidate` 保留现有静态规则和 Shadow Registry。 `validate_source` 复用 `StrictTrainEnv`、原始重放及 `EnvironmentPolicyRunner`。每个版本重新打开同一个游戏，逐步核对失败前缀。候选从空状态开始，只能返回一个当前合法动作或拒绝。宿主将实际动作、观察与上一轮 JSON 状态用于下一次调用。退出时记录控制权交还边界。环境步回执沿用现有 `EvidenceStore` 格式，模型和 Worker 仍由同一个既有持久账本计量。 [来源执行](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:293>)、[现有 Worker 接口](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/failure_learning.py:101>)

LearnAct 只提供失败回执与旧源码组织、有界修订的流程参考。运行入口没有加载上游手写宏、任务示例、环境对象或额外模型，也没有进入 B v13/v14 的计划编译器。开发边界在全部学习请求结束后才执行，其标签和结果不参与反馈、调度或候选择优。原生 FlowEvo 求解及成功学习路径的回归测试单独运行。

## 2. 实际 Mock 请求与修订证据

容器组的初稿请求采用初稿提示和封套 Schema。用户载荷只有 `stage=initial`、原机制假设和允许的公开轨迹。修订请求采用修订提示与同一 Schema，携带 `original_learning_input`、`previous_code`、`diagnostics` 和 `source_feedback`。完整发送内容、供应商回执以及每次尝试的父版本均可核对。 [完整 Mock 请求](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/mock_requests.private.json>)、[请求及原始响应账本](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/provider.jsonl>)

初稿的首条来源为 `source_1`，目标是 `put some vase on safe.`。失败引用 `s003` 对应 `move vase 3 to safe 1`、`Nothing happens.` 以及 `was_admissible=false`。初稿请求的 wire SHA-256 为 `4b636bb7cfeb79511009d4b213e416701b5a8caf9dfcdc3302417dc55a067574`，修订请求为 `4b4eb057758391b1e4d6a2d25ae8ca7a88a77061788545bcf270eca838a046e9`。

容器 `source_1` 的首个 Mock 初稿执行了合法的 `look`。真实环境返回了当前可见容器，随后 Worker 收到更新后的观察及 `{"looked": true}` 并报告候选 `ValueError`。下列内容摘自实际修订请求。

```json
{
  "stage": "revision_01",
  "source_feedback": [{
    "source_ref": "source_1",
    "steps": [
      {"action": "look", "admissible": true, "status": "applied",
       "observation": "You are facing the drawer 6, drawer 5, drawer 4, and safe 1. Next to it, you see nothing.",
       "public_state_changed": true, "done": false, "won": false, "worker_status": "OK"},
      {"status": "error", "worker_status": "RUNTIME_ERROR",
       "candidate_error": {"category": "EXCEPTION", "exception": "ValueError", "line": 4}}
    ],
    "stop": "CANDIDATE_ERROR",
    "won": false
  }]
}
```

测试核对了初稿和修订首个 Worker 上下文的哈希一致，修订版从空状态和同一个 `Nothing happens.` 检查点开始。修订版打开目标容器后，下一次调用确实收到新的开门观察、更新后的合法动作和上一轮的投递状态，再由宿主执行投递。修订包中没有给出下一步答案、历史决定性动作、私有评分见证或原始异常文本。可见状态来自本次执行，原历史恢复后缀仍只作为获准的学习证据。 [初稿来源回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/candidate_0/initial/source_1.json>)、[修订来源回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/candidate_0/revision_01/source_1.json>)

## 3. 三类来源与完整版本结果

这些数值衡量手写夹具在闭环中的工程表现。已曝光开发边界的分母为 18 条明确负例和 3 条信息不足控制，各已执行版本重复同一批边界。

| 机制与版本 | 来源数 | 返回动作 / 实际执行首步 | 首步效果可观察 / 任务动作已确认 | 局部修复 | 恢复完成 / 获胜 | 明确误触发 / 不确定触发 / 错误 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 容器 初稿 | 11 | 11 / 11 | 11 / 0 | 0 | 0 / 0 | 3 / 1 / 0 |
| 容器 修订 1 | 11 | 11 / 11 | 11 / 11 | 11 | 11 / 11 | 3 / 0 / 0 |
| 台灯 初稿 | 3 | 3 / 3 | 3 / 3 | 3 | 3 / 3 | 2 / 0 / 0 |
| 导航 初稿 | 9 | 9 / 8 | 8 / 8 | 0 | 0 / 0 | 2 / 0 / 1 |
| 导航 修订 1（引用初稿） | 9 | 9 / 8 | 8 / 8 | 0 | 0 / 0 | 未重复执行 |

容器初稿 11 次执行 `look` 后出现候选异常。修订版在 11 个来源均执行开门和投递。台灯夹具通过真实环境探索取得交互机会，共执行 23 次移动和 3 次 `use`。导航夹具的 8 次有效移动停在 `PROGRESS_UNVERIFIED`，另一次非法返回由宿主拒绝，未向环境执行。导航修订返回同一份源码，核对完整执行上下文后复用初稿回执，产生 0 次新增 Worker 或环境动作。 [版本结果与成本](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/result.json>)

评分分别保存返回动作、实际动作、公开观察变化、动作效果、局部见证、恢复完成和官方 `won`。局部见证沿用原有严格见证或 B v14 的确定性口径。后者要求已确认的动作效果使历史决定性动作首次变为合法，或环境实际分数增加或获胜。恢复完成要求环境分数增加或获胜，本次数据上两个计数相同。`done`、候选自述、合法动作及一次有效移动均各自记录。 [评分实现](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:376>)

## 4. 零 API 验收及恢复

- **交付与权限。** 一份错误封套同时返回四条字段诊断，原响应保持原样。弃权结束本机制。拒收源码按字节归档，静态规则继续拒绝导入越权与顶层执行。注册、解码源码和 Worker 工件的 SHA-256 一致。
- **修订控制。** 最多两轮，需有新的交付、安全或来源问题。两次修订的界限用不同诊断的 Mock 序列验证。相同源码只在来源、环境、窗口和 Worker 完整身份一致时复用。跨机制重复源码遇到既有 Registry 的不同来源绑定限制时结案为未执行。
- **异常与循环。** 真实测试覆盖候选异常和非法动作。候选计时器已确认的超时可形成诊断，宿主等不到 Worker 回执则阻断。环境失败、回放分歧、未决请求或 Worker 均停止。循环规则要求相同公开状态与动作已两次产生无效果或无公开状态变化，第三次选择不执行，并记录选择与执行的区别。
- **恢复。** 在响应已入账、来源动作已提交、来源检查点已提交三个位置分别注入中断。重入复用已结算响应及已完成检查点。未完分支从原前缀重放，重放已提交的候选动作并逐条核对，重放费用单列。整轮完成后再次运行，模型发送数、账本、回执文件和返回结果保持一致。Mock `SEND_UNKNOWN` 的重入继续阻断。B v9 的旧 UNKNOWN 与预算账本包含在只读哈希核验中。
- **测试结果。** 新套件 11 项通过，其中一项在真实 Linux Worker 和 TextWorld 跑完三类来源。原生成功学习回归 9 项通过。首轮实跑发现返回对象的元组与 JSON 重入列表有差异，已统一序列化并重新通过整套验收。原工作树的未提交改动和历史冻结工件通过前后校验，最终冻结协议绑定了 1,004 份历史文件。 [最终测试日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/console.log>)、[原生成功学习回归日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_acceptance.gVo0af/success_baseline_regression.log>)

## 5. 预算与审计工件

| 资源 | 本轮冻结上限 | 真实来源验收实测 |
| --- | --- | --- |
| 模型请求和 Token | 三组各一次初稿和最多两次修订，共 9 次。单请求最多 65,536 输入预留、4,096 输出，全局 626,688 Token。 | 5 次 Mock 发送，500 输入、500 输出，均为 Mock 回执用量。真实模型请求与费用为 0。 |
| Worker | 1,155 次来源调用槽位和 189 次开发边界调用槽位，合计 1,344。 | 159 次实际调用，38.95 秒。完整来源评估复用 1 次。 |
| TextWorld | 三版普通前缀最多 891 步，候选最多 1,155 步。另为恢复重放预留空间，总硬上限 3,450 步。每个分支最多 `min(18, 50 - 原始前缀步数)` 个候选动作。 | 原前缀 522 步、候选 67 步、中断恢复前缀 5 步、恢复候选动作 1 步。 |

输入预留按最终序列化请求字节数加 256 计入现有账本。表中的上限为本次 Mock 冻结和安全余量。实际 Worker 调用和耗时用回执计量。环境每步先记录占用，再保存实际回执，恢复重放使用同一个环境总上限。各版本的 Worker 和环境消耗在结果中单列。真实报价和付费上限留待下一阶段独立冻结。 [冻结协议](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/protocol.json>)、[预算账本](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/budget.jsonl>)

完整工件位于私有、Git 排除的测试目录。以下为文件字节的 SHA-256。

| 工件 | SHA-256 |
| --- | --- |
| [protocol.json](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/protocol.json>) | `46e9bb5dee4530cbef5744413295ddfd39738278787339d3d8b685d96ba2c132` |
| [result.json](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/result.json>) | `404d58c14195943e220f358f0a211641c7f397ce1139edbbcc67d8d108053b7b` |
| [mock_requests.private.json](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/mock_requests.private.json>) | `cd861f712dcef46f77b025623b7509e75f2b61fd8af62dc288ecb9076879259e` |
| [provider.jsonl](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/provider.jsonl>) | `5c48cdec211182ffe7ed94d4f11ba52f5f9281f4f4eb816aebad9b21b4e31552` |
| [worker.jsonl](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/worker.jsonl>) | `5afe01dbdb06de8f059be89987dceb5e03d97cffe4a46298a783703e415d882b` |
| [environment.jsonl](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/environment.jsonl>) | `a9c4b36967bf46a66b5aa5c55e8557b78496d012c2bd29e580090beaf7168633` |
| [budget.jsonl](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/budget.jsonl>) | `39a48b8141b41b9898206a3188447b6b98369dd819a7c4b6c4081ac3c10b5946` |
| [registry.jsonl](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_verified.PXRYWj/real_sources/registry.jsonl>) | `5e0ea38da76e40e34d6fc27c0c2cf473fb9d36eee3763c410949ff8e51336aaf` |

## 6. 结论与下一阶段

1. **已绕开自定义计划语言。** 恢复交付和执行走普通 Python 路径。
2. **封套直接交付 Python 源码。** 解码后原样归档并执行。
3. **逐步状态传递已验证。** 同一程序读取前一次状态、新观察与当前合法动作，来源之间从空状态独立开始。
4. **实际开发反馈进入修订。** 已核对真实 `look` 观察、候选异常、修订请求和从原点运行的新版本。
5. **上游只复用流程设计。** 新入口没有引入手写恢复宏或额外的外部知识，手写程序位于测试文件。
6. **开发边界与独立 Gate 隔离。** 21 条边界只做开发评价，独立 Gate 零执行，所有已注册版本保持 Shadow。
7. **零 API 工程验收通过，可以准备小规模真实 Pilot。** 当前入口只支持 Mock。下一阶段还需冻结真实模型与返回版本、付费授权、报价与 Token 上限、完整修订包的尺寸规则、候选源码和 Worker 版本、来源与边界身份及停止条件。供应商响应已持久化但缺编译完成凭据的中断窗口沿用现有阻断语义，需人工核查后处理。真实模型自主修复和独立迁移仍待验证。
