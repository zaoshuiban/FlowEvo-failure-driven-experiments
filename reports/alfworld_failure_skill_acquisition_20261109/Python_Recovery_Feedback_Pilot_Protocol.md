# Python 恢复技能与执行反馈修订 Pilot 协议

**状态为 READY_PENDING_AUTHORIZATION。** 本轮已有独立真实 Run 冻结、零 API 预检和待批准额度。到本报告时，真实模型请求为 0。

| 冻结项 | 值 |
| --- | --- |
| Run ID | `real:python_recovery_feedback_pilot_20261112_01` |
| 协议版本 | `alfworld-python-recovery-feedback-pilot-v1` |
| 协议规范化 SHA-256 | `cae5f6020997a54ad2b22bbc4ea43ca49d3c592f217fbe0934c402f1ec2eb2ae` |
| 授权 | 独立模板的 `paid_api_authorized=false`，申请硬上限 **$0.60** |
| 运行范围 | `REAL_SOURCE_ONLY`，所有候选保持 Shadow |

冻结目录权限为 0700，并由 Git 排除。协议文件的字节 SHA-256 为 `a1c319c35e3a19c25f2f15df55a189513b2f8b5486c45385adeb2d06f8d85415`。程序使用规范化 JSON 的哈希校验授权。 [冻结协议](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/protocol.json>)、[未启用的授权模板](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/authorization.template.json>)、[本机预检回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/preflight.json>)

## 1. 研究问题与数据

本轮检验模型能否在固定机制下生成普通 Python 恢复策略，并在收到自己程序实际执行的公开反馈后，用至多两次修订获得来源修复证据。独立 Gate、在线 FlowEvo 介入和新增机制归纳均在本轮范围之外。

| 现有机制 | 已曝光来源序号 | 来源数 | 单版候选动作槽位 |
| --- | --- | ---: | ---: |
| 容器前置条件 | 33、40、47、54、66、70、72、86、88、94、106 | 11 | 169 |
| 台灯交互 | 55、74、111 | 3 | 54 |
| 导航无效果 | 56、62、71、78、85、95、96、113、119 | 9 | 162 |

顺序沿用 B v14，来源绑定原游戏和轨迹哈希、原失败后步数及来源回执。三类名称只用于研究记录，模型读取历史模型提出的机制和获准公开轨迹。21 条已曝光开发边界含 18 条明确负例和 3 条信息不足控制，列表哈希为 `0aa3dd88e88a9220ec89a585eb2a5c0e4ca630d6db53f967551b9fe81727c268`。B v14 父协议哈希为 `dd049687410f4df774f0541fd5caace1bf9a70e9f764a0b26fb5217be1a4b629`。本轮核验绑定的 1,004 份历史文件，包括 B v9 账本。 [来源重建与核对](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:91>)、[题序及私有清单哈希](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/protocol.json>)

## 2. 真实入口与生成调度

`prepare` 写冻结协议和 false 授权模板。`preflight` 重算当前源码、提示、依赖、来源与边界绑定，检查本机 Linux Docker、固定 Worker 镜像和本地凭据存在性。`run` 要求新账本和精确授权，`resume` 要求现有账本及同一授权。授权精确绑定 Run ID、规范化协议哈希、模型、协议版本和微美元上限。真实路径使用现有 `RecoveryAdapter`、`BoundedCompiler`、`PersistentBudget` 与 DeepSeek 受控传输。注入 Mock sender 的测试路径使用独立 scope 与 Run ID。 [真实入口](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:822>)

模型采用 `deepseek-flash`，厂商公布对应 `DeepSeek-V4.1-Flash-1017`。请求采用 Chat Completions JSON 对象模式，温度 0、关闭 Thinking、输出上限 4,096 Token。保存原始响应、响应 ID、返回模型、返回的 `system_fingerprint` 和供应商用量。实际模型别名返回、后台指纹及真实用量有待获准后的响应确认。 [DeepSeek 模型与报价](https://api-docs.deepseek.com/quick_start/pricing/)、[Chat Completions 字段](https://api-docs.deepseek.com/api/create-chat-completion/)

冻结运行环境为 Python 3.11.14 arm64、ALFWorld 0.4.2、TextWorld 1.7.0、Pydantic 2.14.3。协议同时绑定依赖版本、ALFWorld 逻辑文件、来源游戏以及不可变 Worker 镜像和脚本哈希。候选仍用 `environment_operator(context)` 返回当前一条合法动作或拒绝。环境由宿主持有，状态按实际步传递。每一新版本从同一失败后检查点和空状态开始。 [环境与 Worker 清单](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/protocol.json>)

每组固定一次初稿、至多两次修订，额度不转移。`PROPOSE` 的完整源码按字节保存，通过既有静态检查后才进入 Worker。`ABSTAIN` 结案。完整但格式拒收、静态拒绝、候选错误、非法动作、无进展、循环、未完成便拒绝及预算内动作耗尽，都可提供新的来源诊断。修订依据新证据触发。全组来源按既有规则完成恢复、重复诊断、同源码同执行上下文、额度用尽、输入超限或输出截断均停止该组。账本异常、未知发送、Worker 基础设施故障或重放分歧阻断运行。边界评价在全部学习请求结束后执行。 [修订及版本身份](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:620>)

## 3. 反馈选择、限制与留档

完整来源和 Worker 回执留在私有运行目录。修订包的原始学习输入、上一版完整源码、交付和静态诊断保持原值。反馈按冻结来源顺序，每个来源按事件发生顺序列出真实观察、合法性、状态变化、退出状态和获胜状态。模型看不到人工替代路线、私有见证、边界标签、独立 Gate 或宿主路径。已通过旧静态规则的候选代码也不能越过执行隔离。

按以下固定顺序选择第一个能放入请求的档位。所有档位均保留每条有反馈来源的身份和退出状态，起点证据保留在原始学习输入。

| 档位 | 每条来源保留步骤 | 每条观察上限 |
| --- | --- | --- |
| `FULL` | 全部 | 完整 |
| `EDGE_2_1024` | 首尾各 2 步，重叠只保留一次 | 1,024 UTF-8 字节 |
| `EDGE_1_512` | 首尾各 1 步 | 512 UTF-8 字节 |
| `EDGE_1_128` | 首尾各 1 步 | 128 UTF-8 字节 |

省略事件记一基序号和闭区间，省略观察记 UTF-8 字节半开区间、原因和来源 ID。截取落在完整字符边界。私有投影回执绑定未压缩公开反馈哈希、完整旧源码哈希和逐条原始来源文件哈希。最终序列化 UTF-8 字节数加 256 必须在 65,536 内。最小档仍超限则写 `INPUT_LIMIT` 并终止本组，旧源码完整留存。 [确定性投影](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/python_recovery_feedback.py:365>)

| 压力探针 | 全包字节代理 | 固定档位后 | 档位 |
| --- | ---: | ---: | --- |
| 容器 169 个槽位 | 5,245,994 | 52,901 | `EDGE_1_128` |
| 台灯 54 个槽位 | 1,707,550 | 35,479 | `EDGE_1_512` |
| 导航 162 个槽位 | 5,076,854 | 60,287 | `EDGE_1_512` |

探针填满本组全部步骤槽位，使用每步 8 KiB 的转义密集观察和 4,096 字节的整段合成源码，最终载荷由实际 adapter 重新序列化核对。额外测试保存了原样 64 KiB 源码并确认超限组没有发送修订。实际修订的完整源码和反馈长度由真实交付决定。 [本机预检回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01/preflight.json>)

## 4. 最终版本与评价

主要结果是各机制在冻结调度下的最后一次提交。最后提交为弃权、截断或交付拒绝时，主要结果按该状态记。相同源码与上下文引用既有执行回执，费用和复用单列。每版保留父版本、实际 wire 与响应哈希、原始源码、执行和边界回执，边界表现不参与追加、择优或发布。

| 层次 | 记录口径 |
| --- | --- |
| 交付和安全 | 提案、弃权、格式拒绝、输出截断，静态通过或拒绝原因 |
| 来源执行 | 返回动作、环境实际执行、首步可观察效果和动作效果、Worker 错误、无进展或拒绝 |
| 来源效果 | 局部见证、恢复完成和官方获胜。未触达保留在 11、3、9 的各组分母内 |
| 机制级审查 | 容器核对目标实例、投递合法性、实际投递与获胜。台灯核对获取交互机会与有效交互。导航核对真实后续任务进展，单次移动可记录为 `PROGRESS_UNVERIFIED` |
| 边界和资源 | 18 条明确负例误触发、3 条不确定触发及接口错误。每版的请求、Token、实际 Worker、环境动作和费用估算单列 |

真实结果报告会按同一来源逐版比较改善、退化、新错误和边界代价。本轮比较的单位是开发过程中先后产生的程序。反馈与额外模型调用共同变化，独立因果对照与迁移验证留在后续。

## 5. 预算与恢复

| 项 | 冻结上界与构成 |
| --- | --- |
| 请求 | 3 初稿 + 6 修订，最多 **9** 次 |
| 输入预留 | 三个初稿分别 22,240、10,028、18,258，六个修订各 65,536，共 443,742 字节代理上界 |
| 输出与总预留 | 最多 36,864 输出 Token，账本总预留上限 480,606 |
| 供应商报价上界 | 峰时无缓存输入 $0.30/M、输出 $1.20/M，按全部预算计算 **$0.1773594** |
| 保守账本预留 | 每请求全部预留量按 $1.20/M 向上取整至微美元，合计 **$0.576732** |
| 建议申请硬上限 | **$0.60**，对应 `600000` 微美元 |
| Worker | 三版来源 `3 × (169+54+162) = 1,155`。边界按三机制三版每版 21 条计 `189`。合计 **1,344** 槽位，每次账本上限 15 秒，累计 20,160 秒 |
| 环境 | 三版原始前缀 `3 × 297 = 891` 步，候选 1,155 步，另留 1,404 步供中断恢复。硬上限 **3,450** 步 |
| 单来源分支与时限 | `min(18, 50 - 原始前缀已执行步数)`。持久账本开启后整轮时限 24 小时 |

价格在 2026-11-12 核对，授权前如厂商报价或别名版本有变，需重做冻结。实际供应商 Token、缓存比例、计费时段和账单金额尚未产生。记录供应商用量及按冻结峰价的估算，账本预留单列。 [DeepSeek 官方价格表](https://api-docs.deepseek.com/quick_start/pricing/)

恢复使用同目录、同协议与同授权。可验证的本地编译回执直接复用。收到 HTTP 但原始归档缺失记 `HTTP_RECEIVED_RAW_REVIEW_REQUIRED`，原始响应已归档但计量未清记 `RECEIVED_USAGE_REVIEW_REQUIRED`，已结算但缺可重放编译提交记 `LOCAL_COMMIT_REVIEW_REQUIRED`。这几种情况保留已有回执，等待核查。POST 之后状态不明确保留 `SEND_UNKNOWN` 及原预算占用，禁止补发。只有持久账本能证明还未发送的连接故障，才可沿用冻结的最多 3 次连接尝试、2/5 秒退避、15 秒连接和 120 秒响应设置。 [响应核查路径](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:362>)、[受控传输](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/failure_evo/network_transport.py>)

## 6. 终端命令

本目录已完成 `prepare` 和 `preflight`。复核现有冻结可直接运行下面的预检。新 Run 才执行注释中的 `prepare`，并使用新目录与独立授权。

```zsh
repo="/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments"
pilot_dir="/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_feedback_pilot_20261112_01"
py="$HOME/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python"
entry="$repo/scripts/run_alfworld_python_recovery_feedback.py"
export PYTHONPATH="$repo/FlowEvo/src:$repo/scripts" PYTHONDONTWRITEBYTECODE=1
# "$py" "$entry" prepare --output "$pilot_dir"
"$py" "$entry" preflight --output "$pilot_dir"
```

以下两个命令均需本轮明确授权后生成的 `authorization.json`。当前只有 false 模板。`run` 和 `resume` 已用该模板验证会在发送前拒绝。

```zsh
# 首次启动
caffeinate -i "$py" -u "$entry" run --output "$pilot_dir" --authorization "$pilot_dir/authorization.json"

# 原 Run 安全续跑
caffeinate -i "$py" -u "$entry" resume --output "$pilot_dir" --authorization "$pilot_dir/authorization.json"
```
