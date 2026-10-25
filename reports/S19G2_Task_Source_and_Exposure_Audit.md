# S19-G后续：任务来源和曝光审计

已冻结**80题：新train 61题＋前轮已验收test 19题**。与此前Operator归纳/调参/选优材料分开；本轮参考评分和元数据筛查是数据准备曝光，不是目标模型求解或Operator开发。TACO train为官方训练划分，绝不声称模型预训练未见。

新源固定官方版本`d593ed0a2becbbc952230bb89be09189bf1056dc`的`ALL/train-00000-of-00009.parquet`，2,827行；SHA `bee336c14dda183b1f700d54a149173418c7b3def295666159dd72c32aa8b326`，大小及SHA与HuggingFace官方LFS记录一致。下载不执行任何远程代码，模型调用0。见[来源凭据](../runs/s19g_train_expansion_20261024_01/download_ledger.json)。

对train保守排除全部1,000个TACO test原题身份，再匹配项目任务元数据及已有LCB题面；规范化原题URL、题面SHA、词5-gram Jaccard≥0.85、原参考源码及AST哈希作为近重复和程序谱系代理。候选间同样去重。原19题按用户要求保留，但新train不重复它们。现有路径中未找到此前taco-train任务研究记录，见[曝光基线](../runs/s19g_train_expansion_20261024_01/exposure_baseline.json)、[搜索审计](../runs/s19g_train_expansion_20261024_01/train_history_search.json)。代理方法不能证明不存在语义改写或缺失的外部曝光记录。

固定难度分层和SHA顺序，不用目标模型试跑。难度分布：{'MEDIUM': 26, 'MEDIUM_HARD': 23, 'HARD': 24, 'VERY_HARD': 7}。研究分布偏向中高难Codeforces、stdin、可精确判分任务，不能外推到所有TACO/编程题。新增候选同时受公开输入输出总字节≤16000的事前通信约束，因而偏向可紧凑表示的验证材料；这不是任务难度或自然失败率的保证。所有原题URL、题面哈希、参考源码/AST谱系、分片行号及测试角色见[清单](../runs/s19g_train_expansion_20261024_01/task_lineage_manifest.json)。

train没有经过证实的官方SPJ索引可直接复用，未错误套用test的1000行索引。另在参考执行前逐一审查188个输出规范，排除非唯一构造答案、大小写宽松规则及其他现有精确比较器无法可靠覆盖的题，原文与原因保留。
