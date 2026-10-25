# S19-G后续：完整连续任务流冻结提案

**80题任务池达标；付费运行尚未授权。** 完整顺序、难度和原题谱系已固定，不再根据前批失败率换题。

任务SHA `0da6844165c653fe752356a25352e9fa6865a91b9a8c0b2661e3e3d04b96fd85`；封存SHA `9de88d8b71ae3ff35e1c88b865e263f6ccde461729780e7efe96f9b389c70559`；代码提交 `b7dcc9554dd27cd9a56f189fdc787ed00a84090e`，全部依赖另有文件SHA绑定。见[长期提案](../runs/s19g_train_expansion_20261024_01/long_stream_proposal.json)、[在线任务](../runs/s19g_train_expansion_20261024_01/stream_tasks.json)、[谱系与顺序](../runs/s19g_train_expansion_20261024_01/task_lineage_manifest.json)。

G、M、F为同一研究实验下三个独立持久Run，每组只冷启动一次，8批、每批10题，同题同序。各自成功经验库、失败库、文本记忆、假设、Operator隔离；不共享别组未来解答。批次间保留所有允许状态。历史跨任务probe的规则不偷偷注入冷启动F。固定组顺序G→M→F，记录供应商版本、时段和延迟；这是每题每组一次观测，仍有模型随机性和时间漂移限制，不宣称统计优势。

维持learning-evidence-bundle-v1、s19-compile-envelope-v2、evidence-diversity-v1、repair-choice-json-v2及五阶段Controller。不改动作、优先级或修订次数。现有普通求解温度0、thinking disabled、输出8192、输入32768，每题5次调用/204800Token；工具每题128，墙钟600秒，三组一致。工具额度按更大公开集提高，避免40旧额度使后续验证被人为截断；不是减少模型预算制造失败。

G使用现有原生通用决策；M自动更新文本经验并计费；F自主聚合失败、生成规则、来源评价及受限试用。三组共有底层repair/fresh执行能力，但Generic原生策略与学到的条件选择可能不同；必须同时报告固定动作与实际wire，不把任何Prompt差别都称为规划创新。

公开失败批次为0仍继续；没有Operator不虚构收益；无未来匹配不视为负迁移。停止仅按冻结安全/污染/未知请求/无法恢复/Worker异常/硬预算条件。三组在线状态全部锁定后，最终程序、来源验证产物和实际Operator介入候选使用相应任务的封存集复核。研究问题为前瞻性连续学习信号，不以必须产生成功算子为目标。无充分复用，不开展复杂老年代或S20/S21。

执行前仍需新预算授权、Worker即时确认和plan依赖一致检查；配置是提案，绝不等同allow_real_api。M现有全文证据更新的输入上界65536，与F压缩学习的32768不同，保留并明确报告，未偷偷改造记忆系统。历史5事件零API检查见memory_protocol_preflight.json；未来更长证据仍可能预检拒绝，必须按现有规则保留旧记忆并计入失败机会，不能静默扩大输入或宣称理想化M比较。必须单独报告M的证据送达率和记忆更新成功率；M的输入预检失败不等于文本经验机制无效。这是现有完整系统的比较，不是排除所有实现因素后的纯表示形式对照。

## 固定任务顺序

|序号|任务|难度|原题|
|---|---|---|---|
|1|taco-test-435|MEDIUM|[原题](https://codeforces.com/problemset/problem/920/C)|
|2|taco-train-s00-r0384|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/1082/B)|
|3|taco-train-s00-r2749|HARD|[原题](https://codeforces.com/problemset/problem/965/D)|
|4|taco-train-s00-r0838|VERY_HARD|[原题](https://codeforces.com/problemset/problem/1237/E)|
|5|taco-train-s00-r0236|MEDIUM|[原题](https://codeforces.com/problemset/problem/456/C)|
|6|taco-train-s00-r0712|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/948/C)|
|7|taco-train-s00-r2038|HARD|[原题](https://codeforces.com/problemset/problem/261/C)|
|8|taco-train-s00-r1290|VERY_HARD|[原题](https://codeforces.com/problemset/problem/1091/F)|
|9|taco-train-s00-r2452|MEDIUM|[原题](https://codeforces.com/problemset/problem/609/C)|
|10|taco-train-s00-r1704|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/830/B)|
|11|taco-train-s00-r0354|HARD|[原题](https://codeforces.com/problemset/problem/946/E)|
|12|taco-train-s00-r2134|VERY_HARD|[原题](https://codeforces.com/problemset/problem/961/G)|
|13|taco-train-s00-r1661|MEDIUM|[原题](https://codeforces.com/problemset/problem/436/B)|
|14|taco-train-s00-r1204|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/778/A)|
|15|taco-train-s00-r0298|HARD|[原题](https://codeforces.com/problemset/problem/466/D)|
|16|taco-train-s00-r1959|VERY_HARD|[原题](https://codeforces.com/problemset/problem/923/D)|
|17|taco-train-s00-r1817|MEDIUM|[原题](https://codeforces.com/problemset/problem/580/B)|
|18|taco-test-68|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/845/D)|
|19|taco-train-s00-r1698|HARD|[原题](https://codeforces.com/problemset/problem/803/D)|
|20|taco-train-s00-r0493|VERY_HARD|[原题](https://codeforces.com/problemset/problem/1340/C)|
|21|taco-train-s00-r0263|MEDIUM|[原题](https://codeforces.com/problemset/problem/525/B)|
|22|taco-train-s00-r1199|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/1000/C)|
|23|taco-train-s00-r2670|HARD|[原题](https://codeforces.com/problemset/problem/976/E)|
|24|taco-train-s00-r1248|VERY_HARD|[原题](https://codeforces.com/problemset/problem/338/D)|
|25|taco-train-s00-r1465|MEDIUM|[原题](https://codeforces.com/problemset/problem/397/B)|
|26|taco-train-s00-r1593|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/15/B)|
|27|taco-train-s00-r2102|HARD|[原题](https://codeforces.com/problemset/problem/1263/E)|
|28|taco-train-s00-r2748|VERY_HARD|[原题](https://codeforces.com/problemset/problem/1194/F)|
|29|taco-train-s00-r0704|MEDIUM|[原题](https://codeforces.com/problemset/problem/1097/C)|
|30|taco-test-549|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/758/C)|
|31|taco-test-897|HARD|[原题](https://codeforces.com/problemset/problem/1015/F)|
|32|taco-test-80|MEDIUM|[原题](https://codeforces.com/problemset/problem/485/A)|
|33|taco-train-s00-r0615|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/1011/E)|
|34|taco-test-932|HARD|[原题](https://codeforces.com/problemset/problem/1105/E)|
|35|taco-train-s00-r0556|MEDIUM|[原题](https://codeforces.com/problemset/problem/229/A)|
|36|taco-train-s00-r1806|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/337/C)|
|37|taco-train-s00-r1841|HARD|[原题](https://codeforces.com/problemset/problem/1409/F)|
|38|taco-train-s00-r1271|MEDIUM|[原题](https://codeforces.com/problemset/problem/1419/C)|
|39|taco-train-s00-r2411|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/949/B)|
|40|taco-test-803|HARD|[原题](https://codeforces.com/problemset/problem/817/D)|
|41|taco-train-s00-r1680|MEDIUM|[原题](https://codeforces.com/problemset/problem/276/C)|
|42|taco-train-s00-r1612|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/606/C)|
|43|taco-train-s00-r1030|HARD|[原题](https://codeforces.com/problemset/problem/985/E)|
|44|taco-train-s00-r2547|MEDIUM|[原题](https://codeforces.com/problemset/problem/1196/D1)|
|45|taco-test-758|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/630/M)|
|46|taco-test-281|HARD|[原题](https://codeforces.com/problemset/problem/1545/B)|
|47|taco-test-682|MEDIUM|[原题](https://codeforces.com/problemset/problem/289/B)|
|48|taco-train-s00-r2225|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/30/B)|
|49|taco-train-s00-r0001|HARD|[原题](https://codeforces.com/problemset/problem/1057/C)|
|50|taco-test-361|MEDIUM|[原题](https://codeforces.com/problemset/problem/507/B)|
|51|taco-train-s00-r0834|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/1393/C)|
|52|taco-test-612|HARD|[原题](https://codeforces.com/problemset/problem/301/B)|
|53|taco-train-s00-r2766|MEDIUM|[原题](https://codeforces.com/problemset/problem/1453/B)|
|54|taco-train-s00-r0337|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/1038/D)|
|55|taco-train-s00-r1953|HARD|[原题](https://codeforces.com/problemset/problem/1511/E)|
|56|taco-test-737|MEDIUM|[原题](https://codeforces.com/problemset/problem/650/A)|
|57|taco-train-s00-r1222|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/958/E1)|
|58|taco-train-s00-r2804|HARD|[原题](https://codeforces.com/problemset/problem/1216/E1)|
|59|taco-train-s00-r0684|MEDIUM|[原题](https://codeforces.com/problemset/problem/496/C)|
|60|taco-train-s00-r0923|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/1373/D)|
|61|taco-train-s00-r1475|HARD|[原题](https://codeforces.com/problemset/problem/321/B)|
|62|taco-train-s00-r0329|MEDIUM|[原题](https://codeforces.com/problemset/problem/1438/E)|
|63|taco-test-69|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/768/B)|
|64|taco-train-s00-r2292|HARD|[原题](https://codeforces.com/problemset/problem/1303/D)|
|65|taco-test-126|MEDIUM|[原题](https://codeforces.com/problemset/problem/1759/D)|
|66|taco-train-s00-r1275|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/448/D)|
|67|taco-train-s00-r1225|HARD|[原题](https://codeforces.com/problemset/problem/388/C)|
|68|taco-train-s00-r2049|MEDIUM|[原题](https://codeforces.com/problemset/problem/677/B)|
|69|taco-train-s00-r0770|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/333/A)|
|70|taco-test-788|HARD|[原题](https://codeforces.com/problemset/problem/1214/D)|
|71|taco-train-s00-r2491|MEDIUM|[原题](https://codeforces.com/problemset/problem/1350/B)|
|72|taco-test-670|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/1348/C)|
|73|taco-train-s00-r0077|HARD|[原题](https://codeforces.com/problemset/problem/474/F)|
|74|taco-train-s00-r1470|MEDIUM|[原题](https://codeforces.com/problemset/problem/26/B)|
|75|taco-train-s00-r0180|MEDIUM_HARD|[原题](https://codeforces.com/problemset/problem/1225/D)|
|76|taco-train-s00-r2340|HARD|[原题](https://codeforces.com/problemset/problem/380/C)|
|77|taco-train-s00-r1653|MEDIUM|[原题](https://codeforces.com/problemset/problem/887/C)|
|78|taco-test-692|HARD|[原题](https://codeforces.com/problemset/problem/1139/D)|
|79|taco-test-21|MEDIUM|[原题](https://codeforces.com/problemset/problem/1468/C)|
|80|taco-train-s00-r0324|MEDIUM|[原题](https://codeforces.com/problemset/problem/978/F)|
