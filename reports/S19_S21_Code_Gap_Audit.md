# S19–S21系统功能差距审查

基准：`cc965f8366b23cdc9533918b409fc4e2df13cc24`（cc965f83），分支feat/failure-learning-v2。已执行rev-parse、status、show --stat；基准仅新增S18两个运行脚本，183行。开始时没有已跟踪文件改动，有大量未跟踪历史runs及experiments/workflow_pilot；本次不覆盖或清理这些目录。审查对象为该commit的已跟踪源码，不是main。新改动与基准用git diff比较。

## 实际调用关系与差距

下表行号指基准版本；新增接口另见Implementation。

|功能|基准位置与调用路径|基准分类|已有测试及证据限制|优先级/处置|
|---|---|---|---|---|
|公开投影与失败事实|contracts.PublicFeedback.project → failure_events.py:69 FailureEvidenceStore.record/visible/revoke|IMPLEMENTED_AND_TESTED|test_failure_evo_v2.py:269、280、test_failure_evo_s12a2.py；事实不等于根因|保留；补未知异常类型拒绝|
|历史机制认证|evidence.MechanismStore.certify/supports/publish|IMPLEMENTED_AND_TESTED|历史严格跨题机制路径；不是当前单见证Shadow入口|保留，不恢复三题硬门槛|
|题末编译队列|compile_queue.py:11 CompileQueue.due/compile|PARTIALLY_IMPLEMENTED|去重、两族和预算已有；按外部传入family_id分组，不更新假设|P0扩展现有队列，不新造预算器|
|学习循环|learning.py:6 LearningLoop.pending/public_input/run_pending/run_pipeline|IMPLEMENTED_NOT_INTEGRATED|test_failure_evo_v2.py:341；Python归纳/流水线可用，但JSON真实入口不调用|P0连接JSON生成与任务边界|
|候选流水线|pipeline.py、pipeline_admission.py；不存在learning_pipeline.py|IMPLEMENTED_AND_TESTED|test_failure_evo_pipeline.py、test_failure_evo_admission.py；受控Python设计/门控路径|保留，不强行套到JSON表示|
|跨任务症状/假设演化|没有独立SymptomGroup/版本化Hypothesis索引|MISSING|原family_id是调用方标识，WA不是根因证据|P0新增轻量公开索引|
|JSON生成|repair_choice.py generate_rule/validate_rule/action_messages|IMPLEMENTED_AND_TESTED|test_repair_choice.py；有候选及一次格式诊断修订；调用者手工提供证据|P0自动选可见证据，固定预算|
|JSON记忆|repair_choice_memory.py:36 RuleMemory.add/record_assessment/authorize/reserve_action|IMPLEMENTED_AND_TESTED|test_repair_choice.py；Shadow/experimental、局部改善、配对效率、额度、报告哈希已有|保留；增加公开退化反馈决策|
|反馈闭环|RuleMemory.finish仅记录结果；propose_relearning需手调|PARTIALLY_IMPLEMENTED|暂停/冷藏API已有，非自动假设回流|P1连公开反例与暂停|
|真实Hook|repair_choice_hook.py begin/invoke；PreparedController._run|IMPLEMENTED_AND_TESTED|accept_s18_hook.py；任务开始快照、暂停复查、原生回退|保留，仅补成本与前后公开结果|
|Python代际与注册表|failure_registry.py:86、generations.py、plugin.py|IMPLEMENTED_AND_TESTED|test_failure_evo_generations.py/v2；权限/题间发布/暂停已有|不复活历史Suspended制品|
|JSON老年代路由|reserve_action仅nursery/experimental；无成熟授权路由|MISSING|不能宣称成熟算子已验证|S20后续，不阻断S19|
|持久预算|persistent_budget.py PersistentBudget；SharedTransport.send|IMPLEMENTED_AND_TESTED|test_failure_evo_persistent_budget.py、test_s16a_protocol.py|保留，新验证账本用同实现|
|连续入口|run_workflow_v2.py:68 solve；dispatch仅顺序手工job|PARTIALLY_IMPLEMENTED|accept_s16b_entry.py；S18脚本手动记录，不自动学习|P0薄题间/批间编排|
|恢复|ExperimentRunner.__init__拒绝已有目录；save不保存成功库|MISSING|预算可恢复不等于整个运行可恢复|P0显式恢复计划/成功库/审计；题中断仍有限制|
|G/M/F隔离|独立store和成功库key，M memory及预算在Runner级共享|PARTIALLY_IMPLEMENTED|多臂同Runner不适合独立长期流|每臂独立Runner/目录/账本，拒绝跨臂复用manifest|
|封存复核|S18在线锁后外部评分|IMPLEMENTED_AND_TESTED|真实P1/P2记录；不是学习上下文|连续入口不读取外部评分|
|长期可靠性/成本优势|无系统级确认|UNVERIFIED|S1–S18不替代S19–S21证据|不宣称优势|

## 最小修改与不改范围

修改公开症状/假设索引、现有CompileQueue的JSON调度接口、Runner可恢复状态、薄LearningStream、Hook反馈。保持五阶段Controller、Linux Worker、计费/预留实现、JSON两个动作、Python注册表/权限机制不变。无新增AST修复器或Agent。未知异常字符串不再自动成为可信运行时根因事实。

## 本轮之后仍需正视的阻断

1. `LearningStream.run`遇TASK_STARTED但无TASK_FINALIZED安全停止；不能自动恢复题中尚未保存的Controller状态。复现：test_s19_stream.Tests.test_no_replay_interrupted_task。预算不重复扣费不等于完成任务续跑。
2. `SymptomLearning.start`持久标记后中断，作业不会重发；没有自动协调“响应已到但评估/注册未完成”的状态机。具体JOB_STARTED无JOB_FINISHED被判IN_FLIGHT，需对已存响应做审计恢复。
3. 新入口源验证真实路径已接现有Judge，但本轮多任务测试使用模拟评分器；未进行新增JSON候选与真实Worker的来源验证联调。既有Worker验收不等于这条新增路径已验收。
4. 新生代需要冻结的`validated_action_safety`宿主验收声明，不能由模型填写；CLI已要求安全报告路径、SHA256、表示版本与检查项一致；本轮尚无新增入口的真实Worker安全报告，禁止借Mock声明开启真实试用。

因此整体结论是PARTIALLY_IMPLEMENTED，不是S19付费执行就绪。此结论针对具体恢复及准入链路，不是“没有生成成功Operator”。
