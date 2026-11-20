# T/F统一算子工程修复与开发验证报告

## 结论

真实修订 6/6 份；静态通过 6/6；来源与开发全量验收通过 6/6。

本轮只证明交付与工程修复流程使候选获得了真实执行机会。工程通过不等于失败信息增量有效，也不等于跨原题迁移。

## 冻结与对称性

新Run：`math_symmetric_repair_20261031_01`；协议 SHA256：`8a907fa08b085a86bf7b7c265264fc85c6bdbd06c84dd6fc721ac84d14a2321a`。原六份候选、原始响应和各自归纳原文作为历史模型产物导入；不重新归纳或生成初始算法。

T/F各三份；保持旧轮冻结顺序，每份仅一次修订、8192输出上限、65536保守输入上限；相同模型deepseek-flash、非推理模式、温度0、接口、安全检查和诊断算法。六个独立账户各0.20美元，合计1.20美元硬上限，不转移旧预算。

修订模型只获得该候选原始源码、统一静态诊断、同一组来源/已曝光Design题面及接口要求。不追加历史假设、失败轨迹、评分结果、Gold、可信参数、Gate或Test材料。原始T/F源码保留各自的生成信息差异。修订失败不追加采样。

## 验证结果

|候选|静态|来源计算/联合（5）|开发计算/联合（20）|参数正确（25）|工程负例拒绝/错误接受（2）|状态|
|---|---|---|---|---|---|---|
|0-T|通过|5/5|20/20|25|2/0|READY_PENDING_INDEPENDENT_GATE|
|0-F|通过|5/5|20/20|25|2/0|READY_PENDING_INDEPENDENT_GATE|
|1-F|通过|5/5|20/20|25|2/0|READY_PENDING_INDEPENDENT_GATE|
|1-T|通过|5/5|20/20|25|2/0|READY_PENDING_INDEPENDENT_GATE|
|2-T|通过|5/5|20/20|25|2/0|READY_PENDING_INDEPENDENT_GATE|
|2-F|通过|5/5|20/20|25|2/0|READY_PENDING_INDEPENDENT_GATE|

每列计算与联合数字是两种测量，不是分子/分母。分母见表头。静态失败未执行记为未测，汇总JSON的0计数不能解释为数学0分。五道来源和20道Design为同一人工数学机制的参数实例，并非25道不同原题。

## 工程修复与算法版本

所有模型源码原样保存。对源码SHA、去位置及文档字符串后的AST、顶层函数差异分别记录。只有AST未变才标记格式/说明变化；其他统一标记SUBSTANTIVE_OR_UNRESOLVED，不能证明数学逻辑等价，也不能宣称只是去掉nonlocal。未继承任何旧验证或试用权限。

计算：真实Worker直接调用生成的solve(parameters)，可信参数仅宿主离线诊断可见。映射：调用生成的map_parameters(problem)，与独立参数逐字段比较。联合：调用生成的math_operator，使用现有MathOperatorRunner。所有执行都绑定完整生成源码SHA；宿主没有另写等价数学算法。

## Gate及研究边界

开发通过仅产生READY_FOR_INDEPENDENT_GATE收据，不自动授予Experimental。开发阶段的两个负例只是无题目/越权请求工程控制，不能替代数学语义近似负例。六份源码冻结后，另立零API Gate协议：使用原先冻结且未执行的20道支持输入，加上在Gate执行前冻结的6道目标量变更负例。所有负例由研究者审查其目标与冻结算法接口不符；没有把模型自报答案作为Oracle。负例由其中6道支持题变体产生，共享参数谱系，不算26道独立原题。

Gate与开发/修订题面不重叠，但仍是同机制人工参数分布。新增负例属于开发后设计的压力测试，并非所有数据从最初生成前就盲法预注册；已在Gate前固定，结果不回流任何修订。60道Test未执行，也未进行Generic端到端收益比较。

## 成本及完整性

真实响应6次；输入23,462、输出8,125、合计31,587 Tokens。峰价估算$0.016412280，非峰价估算$0.008206140；账本保守占用上界$0.174536。估算不是实际账单。

真实Worker调用474次，账本工具耗时98.143秒。旧Run全部文件哈希保持不变：True。

[供应商报价](https://api-docs.deepseek.com/quick_start/pricing/)已于冻结时保存pricing.html；峰价输入未缓存0.3、缓存0.006、输出1.2美元/百万Tokens。

## 工程验收与交付

零API人工夹具22项检查通过，使用真实Linux Worker；另通过现有BoundedCompiler与新Adapter的Mock完整调用。人工夹具不计真实学习。测试覆盖具体nonlocal/缺导入诊断、对称输入、原始/修订留档、版本分类、私有字段阻断、UNKNOWN不重发、交付失败与传输未知分离、参数/算法错误分离、验证绑定和源码变更失效。

代码：`FlowEvo/src/failure_evo/math_engineering_repair.py`；真实入口：`scripts/run_math_symmetric_repair.py`；验收：`scripts/test_math_engineering_repair.py`；报告：`scripts/report_math_symmetric_repair.py`。

所有真实请求/响应见各候选provider.jsonl；修订链见repair/；开发执行见validation.jsonl、development.json；账本见budget.jsonl。原始与修订源码分别为repair/original.py与repair/revised.py。

## 冻结源码的独立保留输入与语义压力Gate

|候选|计算正确/20|参数正确/20|联合正确/20|错误接受/6|正确拒绝/6|Gate|
|---|---|---|---|---|---|---|
|0-T|20|20|20|6|0|未通过|
|0-F|20|20|20|6|0|未通过|
|1-F|20|20|20|6|0|未通过|
|1-T|20|20|20|0|6|通过|
|2-T|20|20|20|0|6|通过|
|2-F|20|20|20|6|0|未通过|

计算组件获得了新参数输入上的功能性证据；适用性不能只依据合法参数JSON。目标量改变后仍接受，属于语义门控失败。所有未通过版本保留Shadow，不因计算20/20而发布，不再围绕本Gate修订。T中1-T、2-T通过，F三份均未通过；本轮不支持失败信息优于Task-Only。仅三对生成及单机制人工数据，不能泛化为T总体更优。通过者也没有端到端Generic收益证据，暂不发布。

Gate额外Worker账本：`runs/math_symmetric_repair_20261031_01/independent_gate/budget.jsonl`。没有模型请求。Gate结果：2/6通过；Experimental仍为0。

原六候选生成轮另有12次响应、77,386 Tokens，峰价估算$0.018077448；加本轮六次修订后，合计18次响应、108,973 Tokens、峰价估算$0.034489728。该合计只覆盖这两轮生成/修订，不是全部历史研发总成本。两轮账本均保留。

## 最终工程审计

新增22项零API验收通过；P1/P2兼容回归26/26通过（包含继承的无Gold测试，不重复累计21项）。最初测试环境缺少pydantic/PyYAML/requests，已在临时依赖目录安装后完成回归，没有更改系统全局依赖或数学算法。

六份provider与预算账本均为HEALTHY，未知/待定请求0；旧Run文件哈希全部一致。计算/开发474次Worker调用，Gate432次，合计906次，账本工具耗时187.049秒，不含单元回归及人工成本。

原始源码、各候选修订版和实验运行时工程源码已冻结。实验结束后只收紧运行入口的ValueError捕获范围：只有明确的交付解析错误可作为普通交付失败继续，模型漂移等错误必须传播停止。该后续工程变更没有重发模型或重跑评分，运行时/当前源码哈希分别保存在final_audit.json与frozen_source。

|候选|AST发生变化的函数|
|---|---|
|0-T|_count, map_parameters, math_operator, solve|
|0-F|_parse, map_parameters, math_operator, solve|
|1-F|_count_primes, map_parameters, math_operator, solve|
|1-T|_count, map_parameters, math_operator, solve|
|2-T|_count, map_parameters, math_operator, solve|
|2-F|_count, map_parameters, math_operator, solve|

0-F的原计算辅助函数AST未变，主要新增/修改解析与接口；其余五份的计算辅助函数也发生结构变化。该比较是语法树证据，不是数学等价性证明，所有修订均作为新代码版本重新验证。
