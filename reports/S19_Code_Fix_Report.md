# S19 源码修复报告

基准：`ad834c79e5d5d16d98f1f91880ccafd9b4bb6e1e`。独立分支：`feat/s19-trusted-learning-loop`。本轮真实模型 API 请求：**0**。

## 结论与适用范围

| 判断 | 本轮证据 |
| --- | --- |
| ENGINEERING_READY | 新版入口的公开边界、预算、恢复与真实 Linux 程序评分联调通过；题中中断按协议 fail-closed |
| LEARNING_LOOP_READY | **工程链路就绪**：模拟提供商驱动连续失败、内容更新、有界修订、未来任务试用和暂停；真实模型在自然连续任务上的学习有效性尚待 Pilot |
| RESEARCH_EFFECT_UNVERIFIED | 没有新增付费模型实验，没有证明跨任务可靠性、净收益或代际管理优势 |

这里的“真实执行”指程序在既有隔离 Worker 执行；规则与求解响应均由模拟发送器提供。不能把这些固定工程响应称为模型发现了机制，也不能把四个同模板工程任务称为四道独立自然失败。

## 修改清单

| 文件 / 主要函数 | 修改及原因 |
| --- | --- |
| `contracts.py::strict_public_task/strict_public_case/strict_stream_task/strict_feedback` | 新连续入口递归拒绝未知字段、非标量内容及无可信来源的公开样例；来源绑定 input/expected 哈希。保留比较器和大小写语义；旧宽松投影不用于新入口的输入验收 |
| `contracts.py::atomic_json` | 状态、响应及报告使用同目录临时文件、fsync 和原子替换 |
| `repair_choice_v2.py`（新增） | 显式 `repair-choice-json-v2`，统一产物状态、资格和 choose；NO_ENTRY 不按完整 WA 处理，缺失程序只可 fresh，语法错误可有源码修复路径；保留一个原生回退调用预算 |
| `symptom_learning.py::ingest/learn_content/effect` | 分开症状、证据集合、可变假设内容和功能反馈；重复症状不能变成动作支持。反馈核验实际任务、事件及候选哈希；v2 不接受仅以人工 supports 布尔值确认假设 |
| `compile_queue.py::schedule_hypotheses` | 新证据或新诊断才调度；记录 JOB_SCHEDULED；消耗过的来源诊断不造成无限重编译 |
| `repair_choice_memory.py::add/annotate_assessment/finish` | 独立 parent/version/diff/cost 元数据；相同规则追加证据和生成记录，不重置权限或虚增能力；以宿主评分布尔结果判断公开退化 |
| `repair_choice_hook.py::invoke` | 记录匹配冲突、固定顺序选择、原生动作、实际干预与成本；反馈绑定干预前 stage/hash；公开退化暂停 |
| `workflow_runtime_v2.py` | 仅增加原检查点预算及宿主评分结果记录，未重写五阶段 Controller |
| `run_workflow_v2.py::ExperimentRunner/RunTransport/zero_api_runtime_probes` | 新协议显式注入；响应和未知状态及时落盘；复用原 SharedTransport/PersistentBudget；可信宿主实际运行未知请求和原生回退探针 |
| `run_learning_stream.py` | 深投影、原状态来源评估、假设与规则共同生成、有界诊断修订、幂等恢复、M 更新恢复、任务间发布；Worker 参数从冻结配置读取 |
| `test_s19_v2.py/test_s19_stream.py` | 新版连续路径、污染拒绝、预算、响应恢复、规则去重、反馈身份及三臂隔离测试 |
| `accept_s19_real_worker.py` | 模拟模型、真实 Linux 评分的连续验收入口 |
| `prepare_s19_pilot.py/accept_s19_pilot_public.py` | 固定开发题序、预算提案、公开评分器等价性与隔离正反验收；不调用模型 |

未新增工作流动作、Agent、AST 修复算法、成熟代际阈值或新的预算管理器。`repair_choice.py` 的 v1 解释与规则协议未改写；S1–S18 冻结结果、原始响应和账本未加入本轮修改。

## 关键修复证据

1. 第一轮真实 Worker 联调发现：输出 `0\n` 与期望 `0` 在 token 评分器中正确，但用字符串相等重算结果会丢失退化证据。改为携带宿主 `correct` 布尔结果；失败记录保留于 `s19_v2_acceptance/first_worker_failure.json`。
2. 新发送边界检查的是最终序列化请求。嵌套 task_public、样例及来源中的私有字段在三臂构造阶段即拒绝，模拟发送次数保持 0。
3. 来源评估恢复 max_calls/calls、Token、工具和剩余时间。一个需要 3 次剩余额度的规则，在实际只剩 2 次的检查点拒绝，不再用任意固定 Budget 使之通过。
4. 已保存生成响应必须与 COMPLETED 请求记录及消息哈希一致；篡改或缺少结算凭据立即停止。真实未知请求不自动重发。
5. Pilot 旧用例的 `comparison=prior` 需要保留原比较器。首轮评分适配失败后，改为经过等价检查的解包，保留相同 OLD.accepts 评分逻辑；没有删除失败题或更换样本。

## 测试结果与限制

- 核心模块：212 项通过。
- S19 专项：15 项通过。
- 协议专项：32 项通过（与全量 scripts 测试有重叠，不累计为独立总数）。
- 真实 Worker 连续链路：10/10 检查通过；40/40 开发任务公开评分正反验收通过。
- 全量 scripts：84 项中 78 通过，2 个 failure、4 个 error，**不是全绿**。

两项失败要求当前代码仍等于 S13 冻结哈希；基准提交中 compile_queue/failure_events 已与旧冻结值不同。四项错误来自 S16 测试假定旧 v0 仍是可续期 experimental，但历史注册表已将其 suspended。制品和授权文件哈希仍有效，不能把这四项解释成源码哈希故障。诊断见 `legacy_baseline_hash_differences.json`、`legacy_registry_diagnosis.json` 与完整测试日志；未恢复已暂停权限、未改旧冻结哈希。

新主线不承诺从任何题中断恢复；持久化部分响应但结算未知也不重试。完整长期公平比较与独立确认仍需新授权和新实验。
