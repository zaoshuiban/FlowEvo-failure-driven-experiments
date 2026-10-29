# V3 续跑最终报告

结论：**交付修复成功，算法纠错有开发证据；语义适用性仍不足，0个候选获准进入独立Gate。**

本轮为已曝光来源与 Design48 的开发验证；未读取 Gate/Legacy/Fresh，没有性能对照，没有新增 Experimental 权限。用户中途明确切换 DeepSeek，因此原 GPT 机制归纳与 DeepSeek 组件生成分开归因。原 P0–P3、旧 V3 结果不修改。

## 五个问题的回答

1. 5份PROPOSE全部转为DeepSeek完整算法源码；另有1份GPT F1算法。按原机制计5/5，不把重复模型版本算新增机制。HYPOTHESIS_ONLY保持不生成。
2. 独立参数下5/5算法在各自来源全部计算正确，合计17/17调用、12道唯一来源。F组联合来源修复只有F1的5/7，F2为0/2，F3为0/3（接口错误）；T3为1/3，T2无合法联合制品。
3. Design已知近似负例没有观察到错误接受，但契约常过度拒绝/UNKNOWN，F3接口失败；不能因此认定4份契约均有效。T3自动提案暴露3次不确定前提接受。
4. 自动测试识别了过度拒绝、接口类型错误和歧义接受；23次可信正例算法计算全对，未识别数学计算反例。8条歧义保持UNVERIFIED。
5. **0个**满足本轮进入Gate条件。全部继续Shadow，没有恢复任何旧Suspended版本。

## 成本与完整性

本轮真实响应22次（GPT3、DeepSeek19），总Token 204,685，响应费用估算合计约 **$0.24668708**。GPT使用供应商usage.cost，DeepSeek按官方当前Flash峰谷报价和UTC请求时间估算，不是实际账单。DeepSeek价格快照在执行后核实，发送前沿用更高的$15/百万Token保守预留；这不是精准事前价格冻结，应作为过程限制披露。

另有1次本轮GPT HTTP402 UNKNOWN，旧V3另1次402 UNKNOWN；二者不重发、不清零、不冒充收费或成功。当前客户端能确认HTTP402但旧响应正文/供应商request id未保存，无法确认结算。未知费用与保守预留另列，不加进已知响应费用。每分支$4为PersistentBudget工程预留，不是实际支出。

旧V3历史生成成本约$1.3296475另列，不消失；本轮后续所有生成、无效输出、工程修订均入costs.json。无DeepSeek求解器新调用、无P1再收集、无Gate或大规模性能实验。

|候选|来源独立计算正确|来源联合正确|Design独立计算正确|Design联合正确|Design适用性计数|
|---|---:|---:|---:|---:|---|
|GPT F1|7|3|8|2|{'CORRECT_REFUSAL': 39, 'UNKNOWN': 7, 'CORRECT_MATCH': 2}|
|DS F1|7|5|8|1|{'UNKNOWN': 45, 'CORRECT_REFUSAL': 2, 'CORRECT_MATCH': 1}|
|DS F2|2|0|8|0|{'CORRECT_REFUSAL': 40, 'DECLINE': 8}|
|DS F3|3|0|8|0|{'ERROR': 48}|
|DS T2|2|0|8|0|{'NOT_GENERATED': 48}|
|DS T3|3|1|8|4|{'CORRECT_REFUSAL': 38, 'CORRECT_MATCH': 4, 'UNKNOWN': 6}|

## 可复核文件

- costs.json：每次响应、Token、报价依据、费用。
- summary.json、GPT_reviewed_scores.json、DS_reviewed_scores.json：完整开发评分。
- generated_test_summary.json及对应Run：自动提案、私有审查和真实Worker。
- unknown_requests.json：本轮未知请求记录；原V3 STOP和账本保持不变。
- completion_manifest.json：交付源码、报告及数据哈希。

## 下一步边界

不再重发相同生成请求。本轮已做一次有界工程修订；剩余问题是契约语义、接口遵循与资源边界，不能通过宿主偷偷解析字符串或补人工规则放行。若继续，应单独设计契约更新实验，保持算法冻结，之后再申请独立Gate；当前结果不证明泛化或相对Generic收益。


## 执行与验收补充

实际Linux Worker合计 457 次函数执行，宿主等待累计 89.758 秒；不是CPU账单，未货币化。详见worker_costs.json。16项零API回归通过（含显式DeepSeek切换、无Gold请求投影、授权阻断）。

原始402与本轮402的完整请求标识、预留金额见http402_audit.json；历史文件逐项哈希未变见history_integrity_summary.json。
