# S20 外部任务准入

本轮实际合格：**APPS40、CodeContests20、LiveCodeBench0，共60题**。目标90未达成，不能称为完整三数据集迁移池。

|来源|固定版本及划分|元数据审查|候选|隔离通过/选入|
|---|---|---:|---:|---:|
|APPS|codeparrot/apps `21e74ddf8de1a21436da12e3e653065c5213e9d1` test|5000|80|40/40|
|CodeContests|deepmind/code_contests `802411c3010cb00d1b05bad57ca77365a3c699d6` test|165|29|20/20|
|LCB Lite|`0fe84c3912ea0c4d4a78037083943e8f0c4dd505`，release_v6|源码schema/发布映射复核|参考前置条件未满足|0|

固定元数据顺序为原始ID/行号，无目标模型试跑。APPS准入范围interview/competition，但前40个实际合格均为**interview**，未实现competition分层配额，不能声称40道高难竞赛题。CodeContests仅CF rating≥1600、stdin/stdout，实际1700–3500。没有因为目标模型失败率调题。

来源下载URL、revision、大小、SHA在`external_downloads.json`；原始大文件在本地缓存，未混入运行时Prompt。APPS官方发布使用JSONL；CodeContests使用官方Parquet。未执行远端dataset脚本。

## 曝光、谱系和比较器

与全部1000 TACO test、既有项目任务元数据、S19G train候选188题及LCB test6元数据核对；依据canonical原题URL、规范化题面SHA、5-gram Jaccard≥0.85、参考源码/AST代理。CF contest URL统一为problemset URL。APPS和CodeContests之间继续排重。原题身份和near score保存在`external_lineage.json`。

本方法可排除记录中的同原题及明显近重复，不证明模型预训练未见，也不保证语义同题查全。不同AST参考实现不等于独立算法证明。

109份候选输出契约逐项复核：排除APPS66缺公式图、APPS108非唯一构造、CodeContests31/90/152非唯一输出。其余采用既有tokens比较器。允许词典序唯一最优、排序集合、计数或固定大小写结果；不把一般构造题塞进精确比较器。

每个选入题：两份不同AST Python源码在Linux Worker通过全部冻结输入；常量错误程序全部拒绝。60题参考及反例共执行记录见`external_worker_results.json`，未把这些人类程序视为FlowEvo自然失败。

## LCB缺口及缩减方案

官方Lite release_v6包含test.jsonl至test6.jsonl，不能用本地175题test6增量冒充全release。该固定schema提供题面及公私测试，但没有两份可信参考实现。现有test6亦已纳入历史曝光基线。故本轮在参考前置条件停止，不进行缺参考的合格宣称，也未用模型补写参考。

这不是“LCB全体没有合格题”的结论。补齐带来源的参考提交后，才能继续新题原题排重及Worker准入。本轮可提出60题、两个外部数据集的缩减池；外部付费任务和顺序仍须在S20-A门槛通过后另行冻结授权。

`external_public_tasks.json`与`external_sealed_tasks.json`分离，当前只用于准入准备。B1/B2未来需预先划分不重叠确认/开发集合，不能将同题用于修订及独立确认。
