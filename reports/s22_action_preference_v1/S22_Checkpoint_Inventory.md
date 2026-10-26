# S22 可用失败检查点盘点

## 范围与口径

穷举runs顶层真实公共FailureEvidenceStore（含S13旧名failure_evidence.jsonl），并补充有真实运行声明的Controller归档及S13 FlowEvo/FailureLearning归档。共检查368个workflow；AFlow不同Controller不纳入FlowEvo动作机会，嵌套Worker fixture、已保存来源重放不作为新任务。没有新增模型求解、没有审查原800题全部原始输出。后续仅在Worker重执行选中的已存失败源码。这里是现有可审计结构化归档的全量盘点，不是所有下载数据上的失败率。

|项目|数量|
|---|---:|
|真实公共失败事实|276|
|Controller有失败但无绑定事实包的补充记录|34|
|合计记录|310|
|原题ID/现有题面及URL去重组件|70|
|源码、反馈/状态与阶段去重后的检查点键|288|
|WA/Runtime Error记录|193|
|交付/编译失败记录|117|
|完整可恢复且双动作合法|84|
|上述涉及原题组件|25|
|新A/B模板预检通过|78|
|预检通过的原题组件|24|
|首批选定独立任务ID|10|
|旧探索A/B对|5|
|符合S22模板的旧完整对/单侧结果|0/0|

其中S20-A另发现4条G组Controller失败未进原事实库；这是新增审计发现，不将旧S21的175条账本回放改成179条。

70是当前身份资料的工作计数，不是已证明70个无近重复算法谱系。按相同任务ID、规范化题面哈希、已审查original_url合并；旧记录资料不足处保留UNKNOWN，不仅凭数字尾号合并。逐行原题/源码/预算/反馈引用及排除理由见checkpoint_inventory.json。288也不是288个独立任务。

78条可运行状态都需要新的A和B调用，不能把已有原生后续请求当作新模板下的一侧结果。部分旧记录可关联旧配对的同题源码，但缺完整恢复信息或不匹配S22请求，关联不等于可直接复用的反事实。

## 分布

数据集：TACO292条、LiveCodeBench18条。失败类型：WA157、Runtime Error36、Compile Error63、No Complete Code54。继承难度标签：HARD95、MEDIUM43、MEDIUM_HARD37、VERY_HARD79、hard18、UNKNOWN38；大小写保留，部分是项目分层标签，不能统一冒称官方标尺。

旧LCB条目存在真实失败，但没有本轮所需完整checkpoint_budget/公开包，未纳入候选。当前首批仅TACO，不能外推跨数据集。无预算时间的旧记录不通过编造remaining_seconds补齐。

## 外部池边界

只读取External-v2汇总和419学习题的lineage元数据：APPS282、CodeContests88、LCB49。未找到这些ID对应真实失败轨迹，故419不是419个失败机会。119确认题仅保留原汇总数量，不读取其题面或测试。未启动新的外部自然求解。若将来需要LCB/APPS覆盖，须另行授权按元数据冻结的观察流，保持原身份、许可、判分、去重和测试隔离，不能先试跑再挑失败题。

## 首批规则与清单

先固定完整可恢复、可信公共失败、A/B双合法、两份新wire均通过输入和剩余Token预算的条件。每原题取首次合格事件；按数据集/继承难度/失败类型的排序轮转，层内时间顺序取10个。此选择不使用paired结果、最终正确答案、旧M成功与否。工程评分验收之后未换题。

|顺序|任务|原run / 组:阶段|难度|失败类型|
|---|---|---|---|---|
|1|s19g_taco-train-s00-r0298|s20_taco80_m_20261025_01 / M:l1|HARD|RUNTIME_ERROR|
|2|s19g_taco-train-s00-r2038|s20_taco80_g_20261025_01 / G:l2a|HARD|WRONG_ANSWER|
|3|s19g_taco-train-s00-r0236|s20_taco80_g_20261025_01 / G:l1|MEDIUM|RUNTIME_ERROR|
|4|s18_taco-test-91|s19_stream20_20261024_01 / F:l1|MEDIUM|WRONG_ANSWER|
|5|s19g_taco-train-s00-r2411|s20_taco80_m_20261025_01 / M:l2a|MEDIUM_HARD|COMPILE_ERROR|
|6|s19g_taco-train-s00-r0712|s20_taco80_g_20261025_01 / G:l1|MEDIUM_HARD|WRONG_ANSWER|
|7|taco_0313|s19_stream20_20261024_01 / F:l1|UNKNOWN_NOT_IN_PUBLIC_RECORD|WRONG_ANSWER|
|8|s19g_taco-train-s00-r1248|s20_taco80_g_20261025_01 / G:l1|VERY_HARD|COMPILE_ERROR|
|9|s18_taco-test-909|s19_real_pilot_20261024_01 / F:l1|VERY_HARD|RUNTIME_ERROR|
|10|s19g_taco-train-s00-r0838|s20_taco80_m_20261025_01 / M:l2a|VERY_HARD|WRONG_ANSWER|

完整源码、当时公开反馈、允许的前缀和预算及两份wire冻结在frozen/01..10.json。均为已曝光开发题；有些参与过以往机制研究，不能称未见验证。

未准入逐行保留NO_RESTORABLE_PUBLIC_PACKET、NO_BOUND_FAILURE_FACT_AND_PACKET、BOTH_ACTIONS_NOT_LEGAL、INPUT_TOKEN_UPPER_LIMIT及LATER_SAME_TASK_COMPONENT。规则可能重叠，不将原因数相加冒充排除任务数。10题公开失败已在Linux重新复现；各自最终复核12例（0313为24例），与公开输入无交集，仍是已有开发复核而非新独立确认。
