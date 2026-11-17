# ALFWorld 单机制 Python 恢复技能 Pilot 零 API 验收

**READY_PENDING_EXPLICIT_AUTHORIZATION**。容器单机制已冻结并通过本地预检。真实 DeepSeek 请求、独立 Gate 游戏和正式发布均为 0。新 Run 为 `real:python_recovery_container_pilot_20261112_01`，规范化协议 SHA-256 为 `2be1114573c96f296cf46776c4c658c4cc9ef69aab3b13290abfc113921d314e`。 [预检回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/preflight.json>)、[冻结协议](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_failure_skill_acquisition_20261109/Python_Recovery_Container_Pilot_Protocol.md>)

## 1. 修改范围

| 文件 | 变更 |
| --- | --- |
| [run_alfworld_python_recovery_container_pilot.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_container_pilot.py>) | 薄入口，复用 `prepare`、`preflight`、`run`、`resume`。 |
| [run_alfworld_python_recovery_feedback.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:161>) | 先完成原三机制校验，再按机制身份和清单哈希筛选容器。新版本绑定调度、证据导入、预算、候选和执行回执，追加来源配对里程碑。默认入口保留三机制。 |
| [python_recovery_feedback.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/python_recovery_feedback.py:383>) | 沿用结构差异比较，补记移除与新增节点的规则、结构哈希和数量。 |
| [test_alfworld_python_recovery_container_pilot.py](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/test_alfworld_python_recovery_container_pilot.py>) | 单机制选择、历史响应、授权、恢复、静态安全、Worker 和 TextWorld 专项回归。 |

原有 Prompt、静态准入规则、Worker 隔离、Registry、来源计分和原生求解器均沿用现有实现。新增配置和验收产物保存在 Git 排除目录。

## 2. 逐项验收

| 验收 | 实际证据 | 状态 |
| --- | --- | --- |
| A 单机制隔离 | 核对历史清单、初稿 wire 和游戏证据，颠倒三组顺序仍能准确找到容器。缺失、重复或变更锚点会被拒。只导入 11 条容器证据。满额回放仅有容器初稿及两次修订，台灯与导航模型调用和预算占用均为 0。 | 通过 |
| B 详细静态反馈 | 原容器初稿在 3:12 与 4:12 有两个拒绝节点，原修订 1 在 3:12 仍有一个，两份原源码均拒绝。修订 1 记录 `ERRORS_REDUCED`，移除一个节点且未新增，仍可进入修订 2。修订 2 用离线弃权夹具结案。 | 通过 |
| C Worker 与环境 | 两份明确标记的 Mock 源码经同一规则静态通过并注册为 Shadow。真实 Linux Worker 按源码 SHA 执行，TextWorld 宿主核对合法动作，后续 Worker 请求读到新观察与上一动作写入的 JSON 状态。 | 通过 |
| D 执行反馈修订 | Mock 初稿执行后产生真实观察及可确认的 `ValueError`，修订请求准确收到投影后的异常类别和观察。两版 11 个起点逐一同哈希。局部修复、恢复完成和获胜各有 11 个改善、0 个退化。 | 通过 |
| E 授权和安全恢复 | 空授权、false 模板、错金额、错协议、错 SHA 均在派发前被拒。模拟生产传输中已结算响应只发送一次。模拟 POST 后丢失响应保留 `SEND_UNKNOWN` 和预留，恢复保持原账本。Worker 基础设施异常停止，未生成候选失败反馈或续发。代码及协议变更被阻断。已确认的环境动作可确定性重放且 Worker 回执不重复。 | 通过 |

格式回归另验证，供应商完整响应附有额外文本时正式拒收。后续修订获得最近正式解码源码、格式诊断及原有两处静态诊断。供应商报告 `length` 时记录 `DELIVERY_INCOMPLETE`，静态和来源均未触达。 [静态回放结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_acceptance.ki8feB/fast_final/container_historical_static/result.json>)、[快速回归日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_acceptance.ki8feB/fast_final.log>)

## 3. 真实 Worker 和 TextWorld 的 Mock 回放

| 源码版本 | 来源首动作执行 | 已确认局部修复 | 恢复完成 | 环境获胜 | 明确负例误触发 | 信息不足触发 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Mock 初稿 | 11/11 | 0/11 | 0/11 | 0/11 | 3/18 | 1/3 |
| Mock 修订 1 | 11/11 | 11/11 | 11/11 | 11/11 | 3/18 | 0/3 |

来源与边界共消费 80 次 Worker 实际调用，累计 Worker 时间约 20.45 秒。环境共执行 489 步，含 450 步前缀、33 步候选动作与 6 步中断重放。两次离线回复对应初稿与修订 1。修订阶段重新打开同一个原始失败后状态。完成后重新进入同一测试 Run，费用、请求、Worker 与环境回执保持不变。

两个版本的 21 条边界分别执行，晚于最后一次学习请求。表中局部修复和误触发均是手写工程夹具的验收证据。真实模型交付、真实模型策略的来源修复及真实模型反馈改善仍待本轮授权后观测。 [单机制执行结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_acceptance.ki8feB/worker_final/container_source_replay/result.json>)、[真实环境测试日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_acceptance.ki8feB/worker_final.log>)

## 4. 三机制回归与历史完整性

当前验收 **34 项通过**，包括 9 项单机制专项和 25 项原入口回归。32 项快速回归通过，两条真实 Worker/TextWorld 测试分别通过。测试中发现的两处夹具问题已修正，一处是临时输出目录的权限，另一处是把公开反馈的 `exception` 字段误断言为宿主内部字段名。两项修正后均通过复测。原三机制集成用例在初次合并日志中单独显示 `ok`。 [快速回归日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_acceptance.ki8feB/fast_final.log>)、[单机制复测日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_acceptance.ki8feB/worker_final.log>)、[原三机制执行日志](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_acceptance.ki8feB/worker_tests.log>)

| 项目 | 默认三机制 | 新容器模式 |
| --- | ---: | ---: |
| 调度来源 | 容器 11、台灯 3、导航 9 | 容器 11 |
| 最大模型请求 | 9 | 3 |
| 账本费用硬上限 | $0.60 | $0.20 |
| 开发边界 | 每个可执行版本 21 条 | 每个可执行版本 21 条 |
| 实际回归 Worker 调用 | 159 | 80 |
| 实际回归环境步数 | 595 | 489 |

结案的旧正式 Pilot 目录共 77 个文件，运行前后 SHA-256 完全一致。另逐一复核新协议绑定的 1,004 份上游历史文件。旧 Pilot 仍保留 7 次真实请求、0 次 Worker 执行的正式记录。新入口拒绝使用旧 Run 身份或目录。 [默认三机制回归结果](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_acceptance.ki8feB/real_sources/result.json>)

## 5. 启动判断

本地预检确认 DeepSeek 凭据已配置、Linux Docker 镜像可用，修订压力样本符合输入上界。新 Run 只有协议、false 授权模板和预检回执。直接用 false 模板运行 `run` 或 `resume` 均在派发前拒绝，未建立请求或执行账本。下一步需要匹配该协议及 **$0.20** 硬上限的本轮明确授权。供应商实时可达性、返回模型指纹和真实响应行为留待授权后记录。 [授权模板](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/authorization.template.json>)、[启动拒绝回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_acceptance.ki8feB/rejected_run.log>)、[恢复拒绝回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_acceptance.ki8feB/rejected_resume.log>)

复现本地测试可在仓库中执行以下命令。该验收使用离线模型回复、本地 Docker 和已曝光来源游戏。

```zsh
repo="/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments"
cd "$repo"
py="$HOME/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python"
export PYTHONPATH="$repo/FlowEvo/src:$repo/scripts" PYTHONDONTWRITEBYTECODE=1
export PYTHON_RECOVERY_TEST_ROOT="$(mktemp -d "$repo/runs/python_recovery_container_acceptance.XXXXXX")"
"$py" -m unittest -v test_alfworld_python_recovery_container_pilot test_alfworld_python_recovery_feedback
```
