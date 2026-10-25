# S19-G 公开评价与隔离验收

合格19题；每题保留题面真实样例，增加12个事前指定为在线开发的原benchmark judge输入，另留12个最终封存输入。两组及题面样例按规范化输入完全不重叠。最终集共228例。原judge输入不冒称官方题面公开样例。

按固定S19G-role-split哈希顺序取24例并分成12/12，无模型输出参与分组。它增加检测覆盖，但不是语义边界覆盖证明。合法性依据为固定官方benchmark输入来源、标准stdin接口、SPJ/图片等元数据排除和参考程序一致通过；没有声称逐条形式化证明题面全部约束。输出采用既有tokens比较器，未更改评分规则。

每题至少两份AST结构不同的原始Python参考在真实Linux Worker通过全部样例、在线开发及封存输入；无效输出程序在相同集合通过0例。源代码哈希不同或AST不同不等于算法谱系独立，因此参考正确性仍是benchmark与一致性证据，而非数学证明。失败候选保留原因和原始结果，未以求解模型表现换题。

[完整验收](../runs/s19g_preparation_20261024_01/scoring_acceptance.json)、[工具账本](../runs/s19g_preparation_20261024_01/acceptance_budget.jsonl)、[汇总](../runs/s19g_preparation_20261024_01/acceptance_summary.json)。首次参考在taco-test-788出现函数外return，AST能解析但不可编译；记录保留在initial_acceptance.log。只给准备脚本加入不执行源码的编译过滤，复用原账本续验；未改Worker或评分器。

实际Worker使用现有非root、断网、只读源码、资源受限容器和固定镜像，配置复用reports/s19_v2_acceptance/worker_environment.json。程序只在隔离Worker运行；宿主仅解析/编译检查源码。工具毫秒和预算见汇总，本地计算未货币化，不能写成零计算成本。

在线任务文件stream_tasks.json不含最终测试或参考源码；sealed_final_tasks.json及验收日志、参考源码只供离线评价器审计，禁止整目录注入学习器。G/M/F必须使用同一在线集及token/调用额度。最终复核只在程序/规则冻结后执行；结果用于独立报告及外部治理，不能回流在线假设、路由或修订。验收器历史字段visibility=public表示该次离线测试可供评分器读取，不授予最终用例在线可见权限；角色以独立清单为准。

本轮重新执行12项隔离探针全部PASS，见worker_probes.json；159份历史Run文件逐一哈希一致，见historical_integrity.json。source_dependencies.json记录现有源码依赖哈希；没有修改这些依赖。
