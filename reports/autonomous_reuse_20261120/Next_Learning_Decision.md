# 下一轮机制选择：自主复用小试结案后

本轮真实 G/R 已完成：两组各 4/4 通过完整评分，冻结技能实际调用 0，增加成功 0、损坏任务 0、少用请求 0；R 多用 3,991 token。HumanEval/39 的 R 组未召回 31，两组均自行修复并通过。39 保留 `EXISTING_CAPABILITY_REUSE_GAP` 以描述已知的检索缺口，但当前没有待求新算法的证据；不再追加提示词、时间限制、算法或 Teacher 实验。

当前可以直接启动强教师新能力获取的合格项目为 **0**，`Next_Learning_Items.json` 明确为空。只读盘点保留以下两类机制，未凑满三个，也未在本轮执行它们。

| 优先级 | 机制与可信失败 | 已有程序覆盖 | 尚缺的证据及最小接线 |
|---|---|---|---|
| 1 | MATH 保持原次序的括号可达结果集合；5 份锁定最终答案为 CONFIRMED_WRONG | 历史模型已生成 43cda… 区间集合实现；904210… 有提前化简风险。均只有工程验证 | 先核对来源谱系与评分权限，冻结验证旧源码的函数行为；必要时只增加 ordered operands/operators → exact results/count 的薄适配。第二独立来源尚未确认 |
| 2 | ALFWorld 已放置实例被重复取放，两个不同目标实例未完成 | D4 选定程序已维护 placed 身份，D5 有整局复用记录 | 先用既有 replay/adapter 绑定旧失败状态和冻结程序，区分已有恢复覆盖与残余问题；不新建环境运行器，遵守曝光和封存清单 |

最值得继续的是 MATH 括号集合运算的**旧候选资格核查**。拟验证的既有操作为 `_count_distinct_values(nums, ops)`，候选源码 SHA 为 `43cda71416fe598643a93400f493c22ad510b0e5232a44d5927cbe2d9ebe43f8`。保留整数精确运算及原操作次序，明确大小限制；先验证这份模型已有实现，再判断需要新算法、修订、参数化整理，还是仅需复用。不能因为原 Actor 答错就断言库中不存在可用程序。

MATH 来源保留 2026-10-27 的原始时间、scorer、Discovery/development 曝光与无 gold 暴露事实。5 个 task_id 是参数化材料，尚不能当作 5 个独立来源。旧 P2 的 `source_gold_scoring=false` 不被事后改写；新的训练反馈使用必须明确协议和权限，不能通过改数据角色绕过。当前分类为 `CAPABILITY_STATUS_UNKNOWN`，不是已经确认缺少算法。

最小下一步应有一个独立的冻结资格清单：既有模型源码 SHA、公开函数契约、允许反馈、私有评分隔离、来源/近重复关系及有上限的零模型执行。如果旧实现通过就复用；只有发现可信未解决缺口且存在独立支持任务，再提出有界 Teacher 获取或修订预算。第二来源作为训练/准入材料，不作为独立泛化评价。本轮没有启动该验证，也没有预先申请无合格来源的付费比较。

ALFWorld 的冻结恢复源码 SHA 为 `c0d6ea0b3c9848cc52ed69a94c31554a271b73e09a5bcf574cf6c9f3c3b68079`，其身份账本与整局复用使“缺少账本算法”不能直接成立。不同游戏可能提供后续支持，但原封存 60 局继续封存，未据本轮结果选取或运行新游戏。

代码域仍无合格新来源：HumanEval/39 已有旧能力且本次普通修订也成功；TACO 0003、144、1454 的指定无效输入证据继续为 `REVOKED_INVALID_INPUT`；0875 人工补丁仅作工程回归。原 TACO 未知请求不重发，剩余训练、开发和保留任务未运行；旧 HumanEval 保留任务也未启用。

本轮新授权已消耗 8 次 Actor、0 次 Teacher、16 个 Worker，保守费用 $0.003472；全部正常阶段已完成，剩余预算关闭。后续不同机制的验证或学习需按其实际来源另定范围，不延长本轮。

证据：[实际配对结果](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/autonomous_reuse_20261120/Autonomous_Reuse_Result.md)；[含逐来源引用和哈希的清单](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/autonomous_reuse_20261120/Capability_Gap_Inventory.json)；[当前学习项为空](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/autonomous_reuse_20261120/Next_Learning_Items.json)。
