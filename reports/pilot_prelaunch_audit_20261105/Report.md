# FlowEvo f20d3220 启动前完成度复核

## 补齐后的状态

真实启动仍为 **NO-GO**。已交付评审签名、盲审材料导出、逐题结果、Shadow 原生配对、配对效应区间和两套协议。真实评审者及公钥、独立 Gate 来源和曝光记录、新题、模型报价、预算与授权尚未冻结。实际介入前的同检查点原生答案缺失，相关因果指标不可评价。

签名绑定运行计划、组别、候选完整版本和评审内容。真实新契约必须提供签名。盲审导出包含题面、任务标识和契约。真实人员独立性及账户隔离还需交接验收。

111 项零 API 组合测试通过。只读回放的 6 道工程题中，T 和 F 各有 1 组 Shadow 正确而原生错误的配对。G、R 的 Shadow 配对分母为零。两套协议均未启动。

参见 [Protocol A](../../docs/research_evaluation/PROTOCOL_A_REAL_MECHANISM_PILOT.md)、[Protocol B](../../docs/research_evaluation/PROTOCOL_B_INDEPENDENT_GENERALIZATION.md) 和 [评审交接](../../docs/research_evaluation/INDEPENDENT_GATE_REVIEW.md)。

## 修订前基线

启动结论为 **NO-GO**。候选版本修复和产物隔离已有验收证据。真实独立评审尚未建立可信身份链，Protocol A 和 B 尚未交付，收益分析仍缺介入前原生路径的冻结配对结果。

| 任务 | 状态 | 当前证据与缺口 |
| --- | --- | --- |
| 1. 候选版本身份 | 已实现并验收 | 基线用源码哈希读取评审和发布缓存，同源码的不同契约可能碰撞。当前工作树按完整版本索引和复核。真实 Linux Worker 工程夹具中，A 发布后，同源码的 B 要求新评审，评审前未执行 Worker。已有证据指向缓存碰撞风险，未观察到未授权执行。15 个专项场景覆盖新旧身份混用、旧收据和恢复。 |
| 2. 保密边界 | 基线范围已完成 | 检查了 f20d3220 的 2,871 个变更文件。私有命名的相关工件有工程 Mock 来源证据，凭据扫描无命中。Git 排除、暂存内容检查、仓库外受控归档和公开校验凭据已落地。更早历史未全量审计，远端强制检查尚未配置。 |
| 3. 独立评审 | 部分完成 | 已有版本与池哈希绑定、整池覆盖、原题和谱系隔离、待审暂停、评审冻结以及工程恢复证据。当前以 JSON 自填姓名匹配允许名单，缺少可信提交来源及独立身份认证。评审模板禁止先执行 Gate，真实盲审隔离和评审者身份仍缺验收。 |
| 4. 科研收益分析 | 部分完成 | 已有只读冻结快照核验、F/G/T/R 配对、介入及介入后正确统计、独立复用、适用性、成本账本、缺失处理与固定精确检验。内部逐题状态尚未导出到结果。缺少冻结的同检查点原生对照，输出明确不可评价。现有检验提供 p 值，缺配对效应区间。Worker 按实耗时间统计，金额依赖冻结单价。 |
| 5. 实验启动协议 | 未完成 | 旧计划仍是工程验收前的通用说明，另附 50 题预算示例。没有独立的 20–30 题机制 Pilot 协议及正式泛化协议。源码、任务、Gate、模型报价和预算未按新 Run 绑定，正式实验样本量方案及 Pilot 转入正式实验的门槛未冻结。 |
| 6. 最后验收 | 部分完成 | 本轮复跑 108 项组合单元测试和四组累积学习工程流程，均通过。版本冲突、旧收据、归档边界和只读统计已有测试。可信评审身份、真实盲审和新协议完整性仍缺验收。 |

主要运行代码改动位于 `operator_contract.py`、`math_gate_pool.py`、`math_stream_learning.py`、`operator_version_gate.py`、`math_cumulative_stream.py`。隔离改动包括 `.gitignore`、`.githooks/pre-commit` 及归档和暂存扫描脚本。新增专项工具和测试包括 `accept_gate_candidate_version.py`、`test_math_gate_candidate_version.py`、`test_public_commit_guard.py`、`analyze_math_reuse_outcomes.py` 和 `test_math_outcome_audit.py`。版本修复和收益工具仍在工作树，隔离变更已有本地提交。

详细证据见 [版本修复](../gate_candidate_version_fix_20261105/Report.md)、[保密审计](../repository_isolation_20261105/Audit_Report.md) 和 [收益工具](../readonly_outcome_audit_20261105/Report.md)。本次复核使用工程夹具和只读 Git 对照。指定数据与报告路径的 Git 差异为空，这项检查不覆盖仓库外历史账本。付费请求数为 0，Protocol A 和 B 均未启动。
