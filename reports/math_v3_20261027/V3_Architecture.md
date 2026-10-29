# V3架构

A：真实Discovery投影 → GPT纠错契约 → CorrectiveDifferenceCheck（仅风险提示，永不自授正确性）。
B：proposed_corrective_operation等纠错字段 → GPT solve源码 + match源码 + SemanticApplicabilityContract。
C：GPT测试提案 → 独立语义/答案来源审查 → 分别运行match、solve与联合apply → 保留全部通过、失败和UNVERIFIED。
D：组件SHA + 契约SHA → 联合制品SHA → 现有注册表Shadow → 开发两维度验收 → 事前冻结Gate候选集合 → 独立Gate与配对价值证据 → 有限Experimental。

失败描述不会直接用作代码规格；生成请求只把提议替代操作、前提、论证及不确定性作为算法规格。相同文字只提示ERROR_REPRODUCTION_RISK，文字不同仍CORRECTION_UNVERIFIED。

match(problem)与solve(parameters)在不同隔离进程执行，不能共享私有评分状态。match输出MATCH/DECLINE/UNKNOWN、参数、目标量及题面原文前提引文。宿主校验参数JSON Schema、目标量契约一致性和引文确实存在；这些结构检查不等于证明数学语义，独立评价仍必需。

solve仅接收结构化参数并返回答案字符串。apply由通用SplitRunner组合，不含专用算法：MATCH后solve；其余拒绝或ERROR。既有NoGoldMathController只在APPLIED时锁定；DECLINED/ERROR回退固定原生流程，不读取Gold判断是否补救。

修改计算代码、语义代码或契约任何一项均改变联合哈希。未经对应新版本验证，不继承Experimental。Gate集合必须预先冻结，旧已曝光Design不能成为Gate。全部拒绝无法证明计算能力；正确计算但误触发也不能准入。

当前限制：前提引文只绑定文字位置，不能证明前提推理正确；自动新题没有独立Oracle时UNVERIFIED；旧单体源码没有天然可交换组件，V1/V2必须另证拆分一致性，不默认存在。
