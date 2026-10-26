# S22 历史A/B证据审计

## 覆盖范围

检索本地runs中所有`branches/*/A|B/result.json`，只有S17-B三对及S18-P2两对，共10个真实分支。逐一读取源checkpoint、冻结A/B wire、初次request hash、各步response usage、公开评分及已发布summary。详细逐字段表见existing_ab_audit.json，输入SHA见input_hashes.json。

S17-B2只筛查20条、1条合格、0次API，不是配对结果。S20 action_pair_preflight是未发送请求重建；M/G、G/M/P是记忆提示对照，不改名为A/B。来源修复、容量修复、R/G/F比较没有同协议A/B对，不作为额外动作偏好标签。

五对都可追溯到同一宿主起始源码/公开反馈。冻结初次请求与实际请求SHA一致，A/B配置为deepseek-flash、temperature=0、thinking disabled、max_tokens8192。原始请求与实际响应模型标识分列在JSON。无UNKNOWN请求。

## 结果（探索性，不能直接训练S22标签）

|任务|初次公开类别|完整分支严格类别|调用A/B|A输入/输出Token|B输入/输出Token|
|---|---|---|---|---|---|
|taco_0118|B-only|Both-success|2/1|3035/1171|801/1584|
|taco_0657|B-only|B-only|2/1|4416/1206|1285/6763|
|taco_0517|B-only|B-only|2/1|4312/1211|1464/8192|
|s18_taco-test-425|B-only|Both-fail|3/1|5492/2325|913/3058|
|s18_taco-test-463|Both-fail|Both-fail|3/3|11168/16588|1892/24576|

初次公开结果：B-only=4、Both-fail=1、A-only=0。完整分支严格结果：Both-success=1、B-only=2、Both-fail=2、A-only=0。两者不能混用：A通常用了2或3次，B成功时只用1次；虽每对总调用上限相同，但不是S22要求的各一次修复机会。初次A制品未全部单独做最终复核，因此不能重建严格单次标签。

历史两次以上分支的严格discordant计数为0对2，精确双侧McNemar p=0.5；初次公开为0对4，p=0.125。仅描述旧探索样本，不能消除请求混杂，也不构成固定B统计优势证明。

## 影响归因的差异

A请求含原始代码和actual/exception反馈；B删除了它们，同时改了动作指令。它们具有相同宿主检查点，但模型获得的上下文不同。S17每侧最多2次，S18最多3次，不能跨实验合并成同预算单次效应。推理Token未由旧usage明确提供时记NOT_REPORTED，而非估算为0。

初次请求数、各分支公开结果、同题复核数量、总输入/输出、费用估算和预算阻断均保留；旧账本不改。现有5对对S22的有效匹配标签数为0，不代表这些旧实验没有探索价值。

## 指定两例

M r0236:l2b重复停滞后，l3原生M路径PUBLIC_PASS；没有同检查点B结果，不能标B优或A优。test-549的G/F后续仍WA，但没有对应B反事实；重复两条轨迹仍是同一原题。两例沿用S21的公开审查，不把后续结果输入新条件。S22首批r0236由首次合格G:l1选入，并非刻意选择此前M:l2b的后续成功状态。
