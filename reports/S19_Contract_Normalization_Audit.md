# S19生成契约规范化审计

## 结论及证据等级

本轮新增真实模型调用 **0**。四份Pilot真实保存响应，按新协议事后只读重放 **4/4通过完整编译协议**；规则去重后 **1种**，4/4在各自来源公开状态上与Generic动作相同：`NO_DISTINCT_ACTION_VALUE`。这不是四个新能力，不是来源修复证明。旧Pilot仍是0/4，未补登任何规则。

## 源码与请求复核

修改前核心源码与 `ed28e6e9c6478329074ba959c9b1b6d708e785d0` 一致；报告提交e765615a未更改源码。逐一复核Pilot冻结的182个依赖，原Git版本/未改动冻结文件全部匹配。审计`baseline.json`明确记录每个文件的验证来源。

读取了四份完整请求、原始响应、末次拒绝诊断；请求字节SHA与已结算transport receipt一致，messages与作业文件一致，嵌套来源包通过现有严格公开投影。四份响应均有六个合法非空hypothesis字段和合法rule，但顶层额外带有`type: json_object`。旧入口要求恰好两个字段，诊断仅为`unknown/private/missing public field`，两次修订未消除此字段。

## 新协议

显式计划字段 `compile_protocol=s19-compile-envelope-v2`，仍使用 `repair-choice-json-v2`动作语义。默认legacy-strict保留；不允许旧Run凭新代码静默恢复成新版。流首条清单也绑定新协议字段。

只剥离顶层、值恰好为字符串`json_object`的`type`。其它值、其它字段、嵌套type、权限/预算字段、重复JSON键、非有限数、缺字段、空字符串、截断及非stop结果拒绝。hypothesis、rule和when逐层检查；rule仍通过原validate_rule，未放宽动作/预算/权限。

每份响应保留完整文件及SHA；另存原始文本SHA、规范化理由、规范化对象及规范化SHA、规则SHA。失败明确标出字段路径和unknown/missing字段；不修改原响应。元数据从不传给注册表授权逻辑。

## 事后重放的边界

四份rule均为STRUCTURAL_PASS + RUNTIME_ERROR + remaining_calls_min=1 → REPAIR_EXISTING，fallback=NATIVE。只在来源包上做确定性选择比较，无模型修复和功能收益推断。四份假设文字不同，不等于动作能力不同。

原Run共108个文件前后SHA一致；完整清单见`s19_contract_revision_20261024_03/old_run_integrity.json`。各份`replay-*.json`含原响应、完整请求路径与哈希。所有事后结果保存在新审计目录，不触及旧Pilot。

四次历史学习响应累计12,313 Token，沿用旧报告周末报价估算$0.002301168（非账单）。新重放0 API，不免除或重置旧生成成本；同文规则聚合也不减少历史实际费用。
