# ALFWorld 失败驱动学习闭环接入报告

状态为 **ENGINEERING_CLOSED_LOOP_READY_PENDING_NEW_REAL_AUTHORIZATION**。本轮真实模型请求 0 次。已接入真实生成通道，工程验收使用固定 Mock 响应。

| 环节 | 实际实现和验收 |
| --- | --- |
| 失败入库 | 原 120 题中的 20 条完整环境失败进入现有 FailureEvidenceStore，绑定原 episode 与模型响应。9 条截断缺失被排除。原始记录全部保留。 |
| 自动归纳与生成 | EnvironmentCompilerAdapter 复用 BoundedCompiler、DeepSeek 持久化适配器及预算。每作业一次归纳、一次代码生成，允许 NO_MECHANISM。源码、作用域与拒绝条件由模型输出。 |
| 安全执行 | environment_operator(context) 在原有 Docker Worker 执行精确生成源码。宿主检查输出结构、状态大小和动作是否属于当前合法动作。无效动作不会送入环境。 |
| 环境验证 | 来源任务及 Gate 上实际运行 G/F，使用相同动作 Token 与步数额度，由官方 won 信号判定。源任务效果、配对回归、执行错误分别记录。 |
| 注册与授权 | 复用 FailureOperatorRegistry 的 Shadow、独立配对 Gate、实验授权、机会消耗及暂停状态。默认最多五个未来任务机会。 |
| 后续调用与反馈 | 新 Hook 在每个环境动作前调用候选，拒绝或冲突时回退。两组结束后记录配对结果；观察到已介入策略的配对退化会暂停对应版本。新的可信 F 失败持续入库。 |

公开上下文只包含 goal、observation、admissible_commands、history、state。模型和算子均不能获得游戏文件、expert plan、隐藏事实、正确动作序列或评分器句柄。学习提示不含人工算法、旧 ALFWorld 蓝图或固定目标算子名称。相同源码不能通过改变元数据重新注册或重置权限。

工程验收在真实 ALFWorld 与 Linux Docker Worker 上完成。固定人工测试策略仅存在于 Mock 验收脚本。本次最新验收得到一个 Shadow 候选、一个通过实际来源与两道独立游戏检查的受限版本，并在一个后续游戏实际执行 28 个策略动作。整个夹具使用 117 次 Worker、2 次 Mock 生成和 48 次 Mock 动作响应。完整回放没有新增模型请求。该夹具的 G/F 差异只证明流程可执行，不能作为自主学习或收益证据。

32 项专项及历史回归全部通过，包含原有实际 Linux Worker 回归。另在实际 Worker 检查了不适用拒绝、非法动作拒绝，在权限层检查来源题排除、旧版本无权限和额度耗尽。系统临时目录下的旧 stdio 回归曾出现 Worker 创建失败；设置受控本地 TMPDIR 后，32 项均通过，权限设置保持严格。

实际修改的核心文件如下。

| 文件 | 改动 |
| --- | --- |
| alfworld_/failure_learning.py | 可信轨迹投影、现有证据库导入、模型生成适配器、源码与 Worker 契约 |
| alfworld_/learning_runtime.py | 策略 Hook、公开状态、冲突与回退、真实环境配对验证、注册发布 |
| alfworld_/learning_stream.py | 累积证据、有限调度、G/F 顺序、后续反馈、配对退化暂停和完整成本 |
| failure_evo/failure_registry.py | 在同一个注册表新增隔离的环境动作权限类型 |
| alfworld_/generator.py、executor.py | 可选生成设置、区分策略动作与真实 LLM 调用计数 |
| alfworld_/audited_baseline.py | 复用请求通道并隔离不同验证和实验分支的请求命名空间 |
| scripts/run_alfworld_failure_learning.py | 数据冻结、预检、独立授权及真实运行入口 |
| scripts/accept_alfworld_failure_learning.py | 明确标记为 Mock 的完整闭环验收 |

新真实 Pilot 已冻结到本地 pilot_final。历史来源为 20 条完整失败，最多两个候选，独享 12 道 Gate，随后六道 G/F 配对任务。Gate 与后续任务均排除历史 12/120 题及工程计划相同内容哈希的游戏。本实验按官方游戏身份划分，属于开发性跨游戏验证，不宣称新场景泛化。

为处理已有交付截断，新 Pilot 的全部环境 G/F 动作请求共同固定为 1024 输出 Token；旧来源轨迹保持原 256 Token 协议，并新增同额度 G 来源对照。最多 2004 次模型请求；动作费用 29.60 美元、学习费用共 0.40 美元，总硬上限 30 美元。Worker 单列调用与时间。独立新授权缺失时，入口在创建真实 Run 和发送请求前拒绝。旧 baseline 的 80 美元授权不适用。

当前恢复策略允许重用已结算模型与完成阶段。Worker、Gate 或环境 episode 的未完成状态会停下等待审计，防止隐式重放。真实模型是否发现机制、生成候选是否通过验证、后续是否有收益仍未实测，允许最终零候选、零授权或零介入。验证阶段不足时维持 Shadow。

验收后又冻结了未用于工程演练的 Gate 和后续任务。预检为 READY_PENDING_NEW_AUTHORIZATION，现有 DeepSeek 凭据已检测到。真实学习实验的调用及费用仍为 0。
