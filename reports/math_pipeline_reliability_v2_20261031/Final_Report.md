# 生成—工程修复—功能验证链路可靠性加固

## 结果

完成 `symmetric-math-engineering-repair-v2`，新增故障注入39/39通过、原工程验收22/22通过、P1/P2兼容回归26/26通过。4项请求投影/授权检查通过。上述测试存在共享路径，不应相加描述为相互独立实验。

本轮新增付费模型请求0。使用真实Linux Worker完成工程夹具执行，并只读重放上一轮六份模型响应；6/6均通过新接收规则。没有重跑或改写旧候选的数学成绩、Gate结果及权限。

## 修改及原因

|环节|加固内容|防止的问题|
|---|---|---|
|生成交付|检查响应类型、finish_reason、交付状态、源码大小、原始响应哈希及源码一致性|截断但有代码被误接收；宿主修改后的代码冒充模型产物|
|持久化|请求占位、原始/修订源码、响应、版本记录采用独占写入并fsync|崩溃覆盖工件、并发重复发送；UNKNOWN后自动重发|
|工程诊断|缺失导入、缺失/重复入口、入口被重新赋值、签名错误均阻断组件执行|静态检查通过却在每个样本上重复接口报错|
|修订公平性|T/F共用接收、诊断、Prompt、预算；未知数学前提须拒绝或UNKNOWN|为某一组特设修复规则；参数JSON合法被当成语义适用|
|功能验证|整批检查可信标签、参数和答案类型、重复题、跨角色重叠后才花费Worker额度|不可信或污染样本进入评分；部分执行后才发现数据错误|
|参数比较|采用保留JSON类型的规范化指纹比较|Python将True与1视为相等导致参数映射误判|
|分层诊断|分别记录映射、计算、联合执行和失败类别|把运行异常、参数错误统称为算法错误|
|适用性|检查map_parameters与math_operator决策一致；拒绝时不允许残留参数|映射声明拒绝但仍输出答案；拒绝所有题被当成成功|
|验证恢复|每个源码/角色预先写入不可覆盖的执行标记；中断结果逐条保存|在同一角色上悄悄重跑挑选成绩|
|版本准入|v2只认同版本、同源码、完整且无重叠的来源/开发收据；Gate拒绝继承v1收据|修订代码自动继承旧成绩或旧试用权限|

`SUBSTANTIVE_OR_UNRESOLVED`仍用于AST实质变化：没有证明数学等价时，不把修订称为纯格式调整。所有源码由模型提供，宿主未增加数学算法。

## 真实Worker故障注入

覆盖布尔/整数参数错配、计算除零、映射拒绝而最终仍计算、拒绝携带参数、缺导入、重复入口、入口覆盖、未知组件调用、重复评价、角色重叠及运行中断后的重放阻断。

明确失败类别：`MAPPING_CONTRACT_ERROR`、`PARAMETER_MISMATCH`、`COMPUTATION_EXECUTION_ERROR`、`COMPUTATION_MISMATCH`、`END_TO_END_EXECUTION_ERROR`、`ROUTING_INCONSISTENT`、`FALSE_ACCEPT`、`SUPPORTED_INPUT_REFUSED`。类别属于执行观察，不自动证明数学根因。

## 历史与研究边界

上一轮仍为：六份修订源码可执行，全部在20道支持Gate上正确；两份T通过语义负例，其余一份T和三份F失败。该结果不因本轮工程改动发生变化。

新通用提示要求检查目标量和前提，但未做新的真实模型生成实验，不能宣称模型因此减少了误触发。版本绑定、静态检查和参考评分也不等于形式化正确性证明。可信标签仍需要独立审查；不能由待测算子自行提供标准答案。

本轮没有恢复旧权限、扩大修订次数、放宽沙箱，亦没有把历史已曝光Gate重新当作未见数据。要评价v2对真实生成成功率的影响，需要另起冻结Run及新的独立验证数据。

## 文件与复现

- 实现：`FlowEvo/src/failure_evo/math_engineering_repair.py`
- 工程修订入口：`scripts/run_math_symmetric_repair.py`
- Gate入口：`scripts/gate_math_symmetric_repair.py`
- 故障测试：`scripts/test_math_reliability_v2.py`
- 最终故障验收：`runs/math_reliability_v2_20261031_03/summary.json`
- 基线回归：`runs/math_reliability_v2_base_20261031_02/summary.json`
- 请求投影验收及源码哈希：本目录 `wire_acceptance.json`、`acceptance.json`

真实运行入口现在必须显式指定 `--out` 新Run路径，防止默认指向历史实验。`freeze`不会发送模型请求；`run`仍须满足既有供应商授权和预算检查。历史复现应使用旧Run内的冻结工程源码，而非用v2重新解释旧收据。

零API测试命令示例（输出目录必须不存在）：

```sh
/opt/homebrew/bin/python3.11 scripts/test_math_reliability_v2.py runs/NEW_ZERO_API_RUN
```
