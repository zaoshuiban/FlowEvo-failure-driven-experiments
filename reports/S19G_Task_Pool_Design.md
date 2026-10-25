# S19-G 任务池准备

本轮真实模型请求0；旧实验未修改。当前结论为 **PARTIAL_POOL_NOT_AUTHORIZED**。

目标60–100题未达到：排除583个曝光任务后，满足当前严格元数据、题面样例和至少24个独立评分输入条件的候选只有29题；实际验收29题，合格 **19题**。不能把这些结果称为已完成60题长期池。

固定顺序见[候选序列](../runs/s19g_preparation_20261024_01/candidate_order.json)，最终顺序见[任务清单](../runs/s19g_preparation_20261024_01/stream_tasks.json)。种子S19G-long-stream-v1；官方MEDIUM/MEDIUM_HARD/HARD/VERY_HARD分别按SHA排序，轮转取样，不使用目标模型表现。最多200次候选准入，目标80题。实际难度分布：{'MEDIUM': 7, 'MEDIUM_HARD': 5, 'HARD': 7}。

源为固定官方TACO test Parquet，SHA `5d99adc603500c05751aff9f61bed7bbd54a9ad5ea569d108b645346655aae44`。沿用已有任务级曝光账本，并保守排除全部80个S18候选（含未正式观察/预留/验收失败）。没有重新审查800题的解答效果。描述长度、约束表述与题面保留在原始准入材料中；不将描述长度当作已证明的困难度。

原题URL、规范化题面精确哈希及词5-gram Jaccard≥0.85进行近重复检查，当前29个候选无超阈值匹配。该方法不能证明无语义改写重复；参见[审计](../runs/s19g_preparation_20261024_01/near_duplicate_audit.json)。曝光结论限于可取得的项目记录，不声称模型训练未见。

缩减方案：仅把这19题作为新候选小流，按10题批次连续执行，明确不足原定研究规模。优先方案：另行固定官方训练分片或其他来源，以同样的曝光、谱系及Worker验收规则补到60–100题，再冻结最终完整顺序；不得直接拼入旧开发任务，当前未验证的外部题目不计数。尚未授权执行缩减流。

## 实际合格任务

|顺序|原题ID|官方难度|在线用例|封存用例|
|---|---|---|---:|---:|
|1|taco-test-80|MEDIUM|14|12|
|2|taco-test-758|MEDIUM_HARD|14|12|
|3|taco-test-692|HARD|15|12|
|4|taco-test-21|MEDIUM|15|12|
|5|taco-test-670|MEDIUM_HARD|13|12|
|6|taco-test-897|HARD|15|12|
|7|taco-test-549|MEDIUM_HARD|16|12|
|8|taco-test-788|HARD|15|12|
|9|taco-test-682|MEDIUM|14|12|
|10|taco-test-69|MEDIUM_HARD|14|12|
|11|taco-test-68|MEDIUM_HARD|15|12|
|12|taco-test-361|MEDIUM|15|12|
|13|taco-test-803|HARD|13|12|
|14|taco-test-612|HARD|14|12|
|15|taco-test-737|MEDIUM|14|12|
|16|taco-test-932|HARD|14|12|
|17|taco-test-126|MEDIUM|13|12|
|18|taco-test-435|MEDIUM|14|12|
|19|taco-test-281|HARD|13|12|
