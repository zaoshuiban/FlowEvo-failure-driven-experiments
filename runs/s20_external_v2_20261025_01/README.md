# S20-External-v2 数据包

全量元数据24665条；学习池419题；确认池119题；选定池Worker验收538/538；本数据准备0次模型API。

- [全量准入与曝光审计](S20_External_v2_Data_Inventory.md)
- [评分器与Worker验收](S20_External_v2_Scoring_Acceptance.md)
- [冻结任务流与使用协议](S20_External_v2_Stream_Protocol.md)
- freeze_manifest.json：源码、协议、任务、测试、官方来源与SHA256。
- learning_public_tasks.json / confirmation_public_tasks.json：在线入口材料。
- learning_sealed_tasks.json / confirmation_sealed_tasks.json：仅外部最终复核，禁止混入在线入口。
- candidates/：离线审计材料，包含参考和封存内容，禁止整体发送给模型。

这些是评分可信度分层的数据准备结果，不是模型泛化或失败学习收益结果。旧严格60及TACO80未改写。

初始候选577题经真实参考冲突及输出语义复核隔离39题，不按模型表现替换。candidates/是离线审计缓存，可能含被隔离或过期候选；正式准入以最终selected_metadata.json及分角色public_tasks文件为准。最终确认池119题低于150目标，不以旧曝光题补足。数据准备没有启动新的外部模型实验。
