# S19-E：Generic差异审计

日期：2026-10-24。源码提交：`cedf3e57e0a55fb2bb78d4d41e3d0ba6daf719e0`。本轮真实模型API请求 **0**；无付费实验授权文件。

## 真实历史输出的事后审查

旧Run真实生成2次，得到1个不同规则；hypothesis六字段内容完全相同，when、action、fallback均相同。唯一匹配来源为456:l1缺程序状态，选择REGENERATE_FRESH，与Generic动作相同。其余当前可见完整程序/NO_ENTRY失败没有被该规则匹配。

两次来源验证最终wire SHA均为：
`147b458e6c9569c010ca43a04e92395ec8faf449224d7fe3644677babfb1b9e5`。

原生456下一次真实求解请求SHA：
`8f0fd89638a6dfd904f45fe98fc666ece20b2c4aba5dd9ab014ba2c6c2e1a0a3`。

**动作相同，但messages和最终wire均不同。** 原生请求可携带上一轮响应/成功经验并使用原阶段温度；固定动作和learned rule在同动作、同检查点下则共用action_messages。这里比较的是历史实际请求协议，不是随机配对G/F效果，后续原生轨迹只用于外部审计，没有送入学习器。

因此标记：`NO_DISTINCT_ACTION_VALUE / REQUEST_DIFFERENCE_WITHOUT_VERIFIED_BENEFIT`。不能因为wire不同认定收益；也不能因为动作相同忽略请求差异。

2次来源验证均失败、0授权、0未来实际使用。生成5,610 Token，验证11,989 Token，全部保留。按旧报告冻结价格分别估算$0.001353150与$0.006236304，合计$0.007589454；非实际账单，本地成本未货币化。本轮新增API费用为0，重复生成费用没有抹除。

## 新系统记录

每次生成记录规范规则SHA、同文重复计数、相对prior的条件/动作变化、公开状态下匹配及与Generic动作差异、固定动作执行器关系。来源评估后追加实际发送wire SHA、来源完全修复/局部改善/无收益及成本。

只凭来源packet无法重建当时原生success-library/last-response时，明确记录UNAVAILABLE，不编造相等性。

真实未来Hook在执行前调用与原生发送器共用的纯`native_messages`构造器，冻结同一状态下不发送的原生请求；分别比较messages与含温度等参数的final wire。执行后核对实际transport receipt与被审计请求哈希一致。此Generic预览不消耗模型预算、不等于真实G组效果。

未来匹配机会在原有routing/任务轨迹中记录；实际执行、回退、暂停、来源效果和模型成本分别记录，不能用匹配次数代替收益。相同规则由现有RuleMemory聚合，所有等价生成账目继续累积。

## 验收与研究边界

Mock模型+真实Worker已验证新Hook的请求预览、实际发送一致性和回退/暂停。真实模型的跨任务差异仍未知；本轮没有新规则或未来试用。完整证据见[generic_distinctness.json](s19e_zero_api_replay_20261024_03/generic_distinctness.json)。
