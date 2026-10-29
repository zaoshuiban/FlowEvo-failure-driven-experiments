# 数学计算开发验证

本轮为已曝光来源与 Design48 的开发验证；未读取 Gate/Legacy/Fresh，没有性能对照，没有新增 Experimental 权限。用户中途明确切换 DeepSeek，因此原 GPT 机制归纳与 DeepSeek 组件生成分开归因。原 P0–P3、旧 V3 结果不修改。

使用独立于 matcher 的已冻结题目参数映射，Worker只接收 parameters；输出锁定后私有评分器比较答案。没有从候选输出推导 Gold。

|候选|来源独立计算正确|来源联合正确|Design独立计算正确|Design联合正确|Design适用性计数|
|---|---:|---:|---:|---:|---|
|GPT F1|7|3|8|2|{'CORRECT_REFUSAL': 39, 'UNKNOWN': 7, 'CORRECT_MATCH': 2}|
|DS F1|7|5|8|1|{'UNKNOWN': 45, 'CORRECT_REFUSAL': 2, 'CORRECT_MATCH': 1}|
|DS F2|2|0|8|0|{'CORRECT_REFUSAL': 40, 'DECLINE': 8}|
|DS F3|3|0|8|0|{'ERROR': 48}|
|DS T2|2|0|8|0|{'NOT_GENERATED': 48}|
|DS T3|3|1|8|4|{'CORRECT_REFUSAL': 38, 'CORRECT_MATCH': 4, 'UNKNOWN': 6}|

DeepSeek 5个算法共17次来源计算全部正确，涉及12道唯一来源题（F/T共享来源不能当17道）；40次Design计算全部正确，涉及16道唯一目标题。其余题不调用不适用的独立计算，不计数学错误。GPT F1额外7次来源和8次Design计算正确。

特别是F2替代算法在2个原错误来源计算2/2，原V0为0/2；这是已曝光开发来源上的纠错证据，不是迁移。匹配器拒绝这两题，因此端到端来源修复仍0/2。代码审查见完整区间集合运算，没有旧提前化简步骤。

评分依据沿用P0私有参考，非定理证明。参数表达的空白和无零时leading-zero布尔差异经单独语义核对，修正适用性统计见parameter_equivalence_review.json；原Worker输出、原始scores均保留。
