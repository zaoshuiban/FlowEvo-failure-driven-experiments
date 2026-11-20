# 共同机制判断与算法候选判断解耦

日期：2026-11-03。零付费API修改；真实学习效果尚未测试。

## 决策含义

新的归纳输出包含两个独立对象，不再使用单一PROPOSE/HYPOTHESIS_ONLY决定一切：

- mechanism_assessment：SUPPORTED / SUSPECTED / UNSUPPORTED，包含依据和已提供证据引用。这是模型对证据的判断，不是宿主确认共同根因。
- algorithm_candidate：GENERATE / NEEDS_SPECIFICATION / NOT_GENERATABLE，包含判断理由；GENERATE必须交付具体算法规格。

|原因判断|算法判断|处理|
|---|---|---|
|SUPPORTED|GENERATE|在预算内生成候选，仍需验证|
|SUSPECTED|GENERATE|在预算内生成候选，根因继续未确认|
|UNSUPPORTED|GENERATE|允许作为可检验计算建议生成，不能宣称失败原因已经成立|
|任意|NEEDS_SPECIFICATION|保留假设，不生成源码|
|任意|NOT_GENERATABLE|记录拒绝，不强行实现|

主机没有将旧HYPOTHESIS_ONLY映射为GENERATE。旧格式会被新协议拒绝；第20、180窗口的历史输出和成绩保持原样，未重发、重归纳或提升权限。

## GENERATE的必要交付字段

必须包含：闭合且无引用的非空参数JSON Schema、输出目标与角色、具体计算步骤（操作/输入/输出）、必要前提、拒绝条件、资源界限、独立验证方法/独立性依据/验证局限。

缺少规格、空步骤、没有独立验证依据、开放参数对象、引用未提供的证据、附加verified或权限字段都会拒绝。泛泛建议应由模型返回NEEDS_SPECIFICATION；宿主检查只能证明规格结构完整，不能证明自然语言步骤真正正确或可行。即便填满这些字段，数学正确性仍必须由实际执行及独立验证决定。

生成Prompt没有预置极值检查、约数枚举等专项算法。具体算法由模型提出。已有工程夹具算法仅在Mock测试文件中使用，未进入生产Prompt。

## 两处门控同步修改

1. 候选簇关联输出也使用双判断；队列按algorithm_candidate调度，不以共同原因支持程度作为生成门槛。
2. 实际归纳再次输出双判断；代码编译入口只允许GENERATE，不再要求旧PROPOSE。T/F使用相同Schema、参数接口、预算、静态检查、Worker和Gate规则。

算法规格与判断原文保存在hypothesis.json及原始模型响应，生成工件绑定assessment_sha256和output_role。机制簇、调度作业及wire均使用新版本：math-cumulative-v2-dual-assessment / math-cumulative-evidence-v2-dual-assessment；不能在旧Run里静默切换。

## 验证程序不冒充求解器

算法输出角色分为ANSWER和DIAGNOSTIC。有限规模验证器可以是DIAGNOSTIC：允许生成源码、静态检查、Worker执行、保存Shadow，但不将它的数值结果与原题Gold比较，也不进入答案算子的自动发布路径。当前协议记录为SHADOW_DIAGNOSTIC_ONLY；未来若要将诊断工具用于工作流，需另设明确的执行协议。

ANSWER候选沿用既有来源检查、独立计算/路由/端到端Gate和题间授权。根因“已支持”、来源正确或代码可执行都不能直接获得Experimental。无可信独立Gate材料仍为Shadow。

## 验收范围

- 9种原因/算法判断组合，其中SUPPORTED+不可生成不会编译，SUSPECTED/UNSUPPORTED+GENERATE可以进入代码生成。
- 旧HYPOTHESIS_ONLY不被转换；缺字段、虚假证据引用、伪造验证权限、旧协议复用被拒绝。
- T/F使用共同的新编译协议；未准备好的算法不能进入candidate请求。
- Mock模型+真实Docker：疑似机制生成答案型源码并通过既有工程Gate路径；不支持共同根因的诊断型候选实际生成与执行，但不评分为答案、不发布。
- 原有累积证据、去重、跨窗口、成对题包、反例、未知请求和授权测试保留。

全部测试为工程验收，不是第20/180题机制获得正向结果，也不是失败学习收益证据。本轮不调用真实模型、不修改旧实验或旧窗口式实现。

## 主要文件

- FlowEvo/src/failure_evo/math_candidate_decision.py：双判断Schema、严格解析、证据绑定。
- FlowEvo/src/failure_evo/math_cumulative.py：簇记录与队列生成条件。
- FlowEvo/src/failure_evo/math_cumulative_learning.py：模型归纳/编译、来源验证与诊断型隔离。
- FlowEvo/src/failure_evo/math_cumulative_stream.py：新协议版本。
- scripts/test_math_candidate_decision.py：双判断边界测试。
- scripts/test_math_cumulative_learning.py：真实Worker集成测试。
- scripts/math_candidate_mock.py：明确标注的人工作业夹具，仅供测试。

新真实实验仍需新Run、冻结的任务与协议、独立验证材料和新授权；本轮没有自动启动。

最终验收：双判断单元测试12/12、累积队列与证据边界测试13/13、端到端检查44/44通过；真实Linux Worker组件执行82次，付费API调用0。原200题冻结源码SHA逐项核对一致。验收机器数据见acceptance.json。
