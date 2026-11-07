# FlowEvo v4 迁移实验 · 现有代码审计

审计基线为 feat/v4-reliability-capability 的 080e8ad8。以下路径相对仓库根目录。

| 边界 | 当前实际调用链 | 迁移方案 |
| --- | --- | --- |
| 启动与预算 | scripts/run_math_cumulative.py main → validate_experiment_mode → CumulativeStream。prepare 绑定源码、数据、分析协议、Worker。run/resume 验证授权，network_state 检查未知请求。 | 保留原入口和已完成 Run。迁移实验使用单独协议与目录。 |
| 原生求解 | failure_evo/math_cumulative_stream.py CumulativeStream.run → StreamRuntime.solve → code_math/no_gold.py NoGoldMathController.solve → solver_messages → DurableSolver.generate_no_gold。NoGoldMathController 独立锁答案。 | 用同一原生锁定答案分叉。现有控制器没有共同检查点上的文本和技能结果注入接口。 |
| 评分与失败 | code_math/private_math_scoring.py PrivateMathScorer.score 校验原生锁后用 grade_continuation。CumulativeLearner.ingest → CumulativeMemory.ingest，F 仅接收可信完整错误。 | 从已有 F 评分、答案锁和失败账本交叉核验，冻结所有组共享的训练投影。 |
| 关联与候选 | CumulativeLearner.discover → AssociationAdapter → CumulativeMemory.associate → CumulativeQueue.schedule → CumulativeLearner.execute。生成依赖 generatable，单见证已有有限探索资格，但仍从关联簇进队列。 | A 保留关联调度。B/D 新增直接从单失败形成规格的入口，C 使用同样投影提取纯文本。 |
| 源码和交付 | BundleCompilerAdapter.preflight → BoundedCompiler.request → DeepSeekCompilerAdapter → receive_source → diagnosis → semantic_contract.artifact → attach_contract。 | 复用计费和严格交付。技能规格另记角色和验证目标。 |
| 安全与发布 | validate_safety → SplitRunner → FrozenLinuxBackend/DockerWorker。ReviewedRelease.attempt 使用 Development 与独立 Gate 的宿主参考，经 ContractShadow、MathPublicationGate、VersionGate 完成授权。 | 复用现有边界。子任务成功和最终答案正确分账，禁止把 SOURCE 诊断直接升为独立验证。 |
| 现有对照 | G 原生。T 历史公开题面学习。F 可信失败学习。R 依据上一窗口 F 实际调用数做额外原生求解。 | T 不是新 C。R 不是共享检查点的预算匹配参照。 |
| 运行模式 | LEARNING_DIAGNOSTIC 关闭路由与发布。INDEPENDENT_GENERALIZATION 要求自动独立 Gate。现有签名路径仍保留。 | 迁移试验需要单独冻结 TRAIN/DEV/TEST、技能版本和访问权限。 |
| 配对分析 | scripts/analyze_math_reuse_outcomes.py 核验原账本、冻结评分和 G/T/F/R 配对，可比较 Shadow 和同题原生。 | 新实验需 A/B/C/D/R 从同一冻结原生轨迹分叉，测试期禁止更新。 |
| 文本记忆 | 代码任务已有 memory/workflow_memory_store.py。数学 no_gold 当前没有对应的检索注入接口。 | 新建窄范围纯文本索引，结果只能作为解题上下文。 |

最小新增接口是数据划分和冻结、单失败规格、纯文本注入、版本演化及共同检查点的评估。历史代码、Gate 和 Worker 继续作为现有路径。
