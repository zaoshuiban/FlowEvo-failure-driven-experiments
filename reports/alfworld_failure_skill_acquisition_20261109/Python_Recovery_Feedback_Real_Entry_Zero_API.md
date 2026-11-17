# Python 恢复技能真实入口的零 API 验收

**真实 Pilot 预检通过，等待本轮授权。** 已实际冻结 `real:python_recovery_feedback_pilot_20261112_01`。本机确认有 DeepSeek 凭据配置、Linux Docker 和冻结 Worker 镜像。核验未探测账户余额或调用 DeepSeek。正式目录只有协议、预检回执和 false 授权模板，尚未建立付费账本。 [本机预检](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/preflight.json>)、[协议与待批准方案](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_failure_skill_acquisition_20261109/Python_Recovery_Feedback_Pilot_Protocol.md>)

## 1. 实现增量与验证层次

| 文件 | 增量 |
| --- | --- |
| [python_recovery_feedback.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/python_recovery_feedback.py:365>) | 完整反馈优先的确定性投影、按 UTF-8 字节截取观察、全量与省略范围审计、修订压力包 |
| [run_alfworld_python_recovery_feedback.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:211>) | 准备、预检、授权启动和同 Run 恢复，真实受控传输、响应待核查分类、逐版本费用和未触达计数 |
| [test_alfworld_python_recovery_feedback.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/test_alfworld_python_recovery_feedback.py>) | 真实路径的离线传输替身，以及保留的真实 TextWorld、Docker Worker 与 Mock 策略回归 |

真实入口按冻结协议使用现有 DeepSeek transport，并要求匹配的独立授权。新增 8 项测试把 TCP/HTTPS 连接换成进程内替身，沿用真实 adapter、序列化、账本、请求身份及恢复检查。带来源和边界的传输测试使用工程来源回执来核验调度。离线目录中真实入口生成的 `paid_requests` 字段表示走过付费入口逻辑的派发槽位。所有连接都由测试替身截获，实际 API 请求与费用为 0。单独的来源回归用真实 Worker 和 TextWorld，模型侧用 Mock sender。两类证据分别归档。 [离线连接捕获](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_zero_api.zHXEWv/real_wire_and_boundary_order/offline_wires.private.json>)、[真实环境工程回归](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_source_regression.URcZxn/real_sources/result.json>)

## 2. 验收结果

| 项目 | 观察证据 |
| --- | --- |
| 未授权、错授权、缺凭据 | 授权缺失、false 模板、整数冒充布尔值，以及 Run、协议、模型或金额不一致均在发送前拒绝。缺凭据也不创建付费请求。实际对冻结目录执行 `run` 和 `resume` 加 false 模板，两者均拒绝且未产生账本。 |
| 真实发送路径的请求与来源隔离 | 离线替身收到 5 个真实格式 POST。容器依次是 `initial`、`revision_01`、`revision_02`，其他两组各一次初稿。检查请求哈希、父版本、提示及来源字段，并校验原始 wire 与冻结上界。真实输入来自冻结公开证据，策略测试夹具留在测试代码。 |
| 压力包、源码与调用边界 | 三类全部步骤槽位的压力包均经实际序列化通过。固定最低档仍超限的 64 KiB 源码原样留存，该组仅有初稿 POST，状态为 `INPUT_LIMIT`。 |
| 实际反馈和最终版本 | 修订载荷包含上一版本源码及该版本公开回执。最后一次弃权的测试仍保留初稿回执，最终版本身份指向弃权版本，11 个来源按未触达计入分母。 |
| 边界顺序与权限 | 捕获的 5 次学习派发全部结束后，才进行 21 条边界评价。开发边界标签和私有见证未进入初稿或修订，候选保持 Shadow。 |
| 已提交结果和中断 | 重入复用已完成的编译和结算回执。已结算原始响应缺编译完成凭据时，写本地待核查记录并阻断。收到 HTTP 但归档中断时也保留明确的接收状态。 |
| 发送状态未知 | 假连接在 POST 后丢失响应，保留 `SEND_UNKNOWN` 和账本预留。重入时 POST 仍只有第一次，账本和供应商日志哈希不变。 |
| 历史完整性 | 122 份冻结源码和 1,004 份历史绑定文件通过校验。第二部分的协议、成绩和预算账本哈希与原报告匹配。B v9 未知请求继续保留。原工作树已有的修改未覆盖。 |

18 项非 Docker 测试通过，其中 8 项为新增真实入口验收。真实 Linux Worker 和 TextWorld 的单项完整回归通过，另有 9 项原生成功学习回归通过。 [增量测试日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_zero_api.zHXEWv/console.log>)、[来源集成日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_source_regression.URcZxn/console.log>)、[成功学习回归日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_zero_api.zHXEWv/success_baseline_regression.log>)

### 来源回归实测

Mock 容器初稿执行实际 `look` 后失败，修订读取公开观察和脱敏候选错误，从同一起点得到 11/11 获胜。台灯夹具 3/3 获胜。导航执行 8 次有效首步，局部修复为 0/9。同源码导航修订复用了原回执。共 5 次 Mock 生成、159 次真实 Worker 调用和 595 个实际环境步，其中 6 步来自中断恢复重放。以上为已有接口在真实环境中的回归结果。 [逐版本回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_source_regression.URcZxn/real_sources/result.json>)

## 3. 恢复边界

| 可核验的状态 | 处理 |
| --- | --- |
| 编译完成或可重放的已结算交付拒绝 | 现有编译器回放相同结果，保持请求身份和账本 |
| 已收到 HTTP，原始响应尚无完整归档 | `HTTP_RECEIVED_RAW_REVIEW_REQUIRED`，保留接收记录并等待核查 |
| 原始响应在，结算无法核对 | `RECEIVED_USAGE_REVIEW_REQUIRED`，保留原始响应和预留 |
| 原始响应完整且已结算，缺可重放本地完成记录 | `LOCAL_COMMIT_REVIEW_REQUIRED`，等待核查，原始响应与账本不重写 |
| 已过发送边界，供应商响应未知 | `SEND_UNKNOWN`，阻断并保留预算，不补发 |
| 账本明确证明未发送 | 仅允许现有受控传输按冻结的连接预算恢复 |

本地中断测试分别注入了“HTTP 接收完成但 RAW 尚未落盘”和“RAW 已归档且结算完成，编译提交前中断”。两例均只有一次离线 POST，状态归为接收后的核查。 [HTTP 接收核查回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_zero_api.zHXEWv/real_raw_archive_gap/candidate_0/initial/response_review.private.json>)、[本地提交核查回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_zero_api.zHXEWv/real_local_commit/candidate_0/initial/response_review.private.json>)

## 4. 工件与授权后的验证

| 证据 | 文件字节 SHA-256 |
| --- | --- |
| [本机 preflight.json](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/preflight.json>) | `0d24a733007b853600de15c3200d43b7ab0660ea5ab306241c5deebccbc8baa6` |
| [未启用授权模板](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/authorization.template.json>) | `f624a9729bd17353959c3f830b9419b8aefb8bf1932cf2ce4778d4c246dc5ec6` |
| [18 项测试日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_zero_api.zHXEWv/console.log>) | `d3bf00b40d7ebea452799355697dc8dfa8696810607c2aeb92aff2e28126045f` |
| [离线完整 wire](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_zero_api.zHXEWv/real_wire_and_boundary_order/offline_wires.private.json>) | `346cb6f67c77e550a50eebbfae5aeb905651233b47da2d6af4bfa65bbb7abcd6` |
| [来源回归结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_source_regression.URcZxn/real_sources/result.json>) | `8c44ebefdcff37165fb8c4f85835ddbf81fcdc4453b1ad5c5c5794d4b9b38898` |
| [来源回归日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_source_regression.URcZxn/console.log>) | `5fc843917204b2442498229980c0bc1f5d01b96f18a0ee8279e9720e72b14921` |
| [原生成功学习回归日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_pilot_zero_api.zHXEWv/success_baseline_regression.log>) | `1c90e3eb1e8bde3935a9954951b0f1aa64a5d417da10301277b5a08b91f00293` |

下一步需要对冻结 Run 明确授权，建议硬上限 **$0.60**。供应商实际响应、模型指纹、实际用量与账单、真实生成程序的修复效果和边界表现有待本轮授权后的单次 Pilot。当前独立 Gate 执行数为 0，所有结果只支持工程准入。
