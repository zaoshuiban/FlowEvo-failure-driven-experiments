# V3开发对照：保留缺失版本，不制造完整四组

| 原算子 | V0原算法/原门控 | V1原算法/新门控 | V2新算法/原门控 | V3新算法/新门控 |
|---|---|---|---|---|
| 1 | P2原始冻结，P3既有评分 | NOT_GENERATED | NOT_GENERATED | NOT_GENERATED |
| 2 | P2原始冻结，P3既有评分 | NOT_GENERATED | NOT_GENERATED | NOT_GENERATED |
| 3 | P2原始冻结，P3既有评分 | NOT_GENERATED | NOT_GENERATED | NOT_GENERATED |

旧P3结果仅列为历史基线，不是本轮重跑：来源7/7、0/2、3/3；Design分别5对1错42拒绝、0对4错2异常42拒绝、8对4错36拒绝。

原P2源码是单体程序。没有经过可信拆分的原match/solve，不能把人工抽取或新解析器造成的差异冒充算法单因素贡献。本轮没有完整新源码，也没有合格的混合组件版本，因此没有运行真实V1/V2/V3比较。

工程双指标采用分开的调用：Computation以独立参数检查solve；Applicability检查match的接受/拒绝及参数；Combined同时要求语义、解析与数值正确。15项Mock测试证明计分与门控行为，不能作为上述真实研究对照。

F/T共同模型、上限和格式，但本轮交付失败且T3遇到基础设施计费拒绝，无法估计失败信息相对于题面的算法或适用性增益。T1返回HYPOTHESIS_ONLY不构成F有效性的证据。
