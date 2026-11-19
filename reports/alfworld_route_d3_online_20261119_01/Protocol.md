# Route D3：执行前冻结协议

本轮回答失败及真实恢复经历所生成程序的整局复用效用，不识别失败信息相对恢复示范的独立贡献。日期 2026-11-19。候选只用 D2 实际执行的 D1 v2，SHA256 `59ff438fafdb2675fc33d4a1543bce38088b59703cd9a85840cdd26407f67e04`；来源链、Worker 和组件哈希见 Candidate_Freeze.json。候选、原生生成器、动作解析器、context_view 与 Worker 均未修改。新学习与修订请求为 0。

## 样本

刷新既有元数据曝光审计，保护 835 个已曝光或预留游戏及对应任务组。当前可用同类 train 池为 465 个游戏、203 个任务组；不是沿用 D2 的 476。以 ROUTE_D3_ONLINE_V1，按已选场景数、已选物品类别数、SHA256(canonical([seed,game_sha256])) 排序，选 12 个不同组。排除 D2 四组及原封存60局，任务身份、游戏与轨迹哈希、组均无重叠。允许已见场景，记录为9已见/3本地记录未见；不声称未见场景迁移或官方 test split。未读取封存60局内容。无结果替换，无新任务预跑收集。12 游戏为样本单位，36 条正式轨迹不是36个独立样本。

|序号|游戏身份|任务组|场景曾见|组别执行顺序|
|---|---|---|---|---|
|0|alf-f69cbdece3ce3fbad830|pick_two_obj_and_place-SoapBar-None-Cabinet-428|True|G → H → F|
|1|alf-cdfc43fbac4a74d415c7|pick_two_obj_and_place-PepperShaker-None-DiningTable-19|True|G → F → H|
|2|alf-00268866f0906a547a8d|pick_two_obj_and_place-KeyChain-None-Dresser-318|False|H → G → F|
|3|alf-732434f4218285a995f7|pick_two_obj_and_place-CellPhone-None-Bed-324|True|H → F → G|
|4|alf-1223a0f5eb51c8ef00ff|pick_two_obj_and_place-WineBottle-None-GarbageCan-1|True|F → G → H|
|5|alf-0909e1ad33b60c22f480|pick_two_obj_and_place-HandTowel-None-CounterTop-409|True|F → H → G|
|6|alf-7fe07321187b84a5080b|pick_two_obj_and_place-Bowl-None-Dresser-327|False|G → H → F|
|7|alf-dd0967b047adcfc756de|pick_two_obj_and_place-Book-None-Bed-304|False|G → F → H|
|8|alf-0044b69a3171a9654014|pick_two_obj_and_place-SaltShaker-None-SideTable-21|True|H → G → F|
|9|alf-ef90dfef52a17a057bfb|pick_two_obj_and_place-RemoteControl-None-CoffeeTable-227|True|H → F → G|
|10|alf-b94d045ea70585b04b9b|pick_two_obj_and_place-TissueBox-None-DiningTable-230|True|F → G → H|
|11|alf-0cb1943a345e528e1d18|pick_two_obj_and_place-CD-None-Dresser-303|True|F → H → G|

## 实际基线与三个组

基线身份是 D2 已验证的“带冻结成功经验库的 Flash 控制器”，不是完整 FlowEvo。复用原生 _build_system、_build_step_user、_parse_single_action、L2 exemplar/L3 insight 检索、现有3×3循环/连续3次 nothing happens 停止规则。该路径原来没有跨游戏成功经验更新、治理突变或额外模型纠错请求；本轮不打开这些功能。G/H/F 各保存相同库的独立副本，均不更新，不存在跨游戏库学习依赖。原生解析器的合法性回退原样保留并记账。

G 保持最近10个动作和每条观察前120字符。H 仅改历史可见范围：保留完整初始公开观察、全部真实动作和未截断观察回执，当前目标/观察/合法动作、经验提示及系统提示不变，不加规划、总结、正确路线或其他组的信息。序列化复用原生文本结构 Recent actions，每条 > action 后接完整 observation；初始观察单独列在历史首条。

F 的原生部分与 H 完全相同，技能收到相同公开范围的 goal/current observation/current admissible commands/history。Worker 继续调用原 context_view，字段和状态协议不变；完整历史第一条用空 action 表示初始公开观察（不占环境步），其后是已发生的动作/观察对。相对 D2，这是为满足 D3 完整历史范围显式加入初始观察，并未改写目标或提供恢复提示。Worker 收到的 state 在接管时为空，之后原样传递。

模型 wire 上限65536 UTF8字节；Worker context 原上限65536字节、state4096字节、输出8192字节。任何容量溢出结束该轨迹并记录失败，不静默截断。G 同用模型输入上限。候选内置 put two… 解析不足原样保留。

主比较 F−H；解释比较 H−G；组合比较 F−G。D3 F 回退 H，区别于 D2 F 回退 G，结果不合并。三组各独立reset同一初态，每游戏比较 game/goal/observation/commands/bank/start哈希。各组按相同游戏顺序，六种组别排列各两次；不共享状态、响应、未来信息或另一组结果。

## 入口与执行

每局最多50个环境动作。F 入口只看已经公开的目标、move 回执及未终止状态：首次成功把目标类别物品放到目标类别容器。复用 D2 的目的地与回执匹配，补充目标物品类别核验（D2原助手仅检测目的容器）；无模型门控，无私有状态参与。仅识别目标含 two + 物品类型、末尾 in/on + 容器类型的现有公开句式；不能识别则记录原因并继续 H。

每局最多触发一次；拒绝、候选异常或非法动作后回到 H，保留状态与消耗步数，不reset、不退还预算、不重入。Worker基础设施故障属于完整性停止。沿用D2整局循环/无进展规则，触发这些规则直接结束整局，不能额外赠送回退步数。环境 won=true 是唯一成功依据。到达入口前失败、提前成功、无入口均保留计入全样本，不制造取回或补样本。

执行前只使用两个已曝光 D2 正常夹具：重放 SoapBottle 的5步和 SaltShaker 的8步，分别检查一次 Worker 行动与原样解析拒绝；验证目标物品/非终态入口及历史不截断。共13环境步、2 Worker、0模型；纳入总账。夹具不提供新学习反馈。正式运行不另收集原生轨迹。

## 配置、价格、预算和停止

DeepSeek 官方 api.deepseek.com，deepseek-flash，文档版本 DeepSeek-V4.1-Flash-1017（别名实际权重不可观测）；thinking disabled，reasoning_effort none，temperature0，max_tokens1024，stream false，无应用级响应缓存。供应商 prompt cache 可能存在。温度0不保证独立轨迹确定性。

上限：12游戏、36正式轨迹、2100模型请求、1800正式环境动作、含验收2000环境动作、650 Worker、$17请求前保守预留、3小时、单请求绝对600秒。统一逐请求以 wire字节+256 为输入token保守上界，加1024输出，按最高$1.20/百万预留；它是保守上界而非实际token计数。达到任意上限停止，不补预算或换游戏。请求上限不表示$17可保证跑满2100次大输入请求。未知发送状态保留预留，不自动重发。

已核对[官方价格](https://api-docs.deepseek.com/quick_start/pricing/)，Flash峰时未缓存参考输入$0.30/百万、输出$1.20/百万。价格及配置快照保存在 Price_Snapshot.json/protocol.json。实际token读取供应商usage；按token参考报价、请求前预留、供应商账单分别报告，账单不可取得则未知。Worker没有美元报价，报告次数与时间，不称免费。

普通失败（动作循环、环境步数耗尽、零动作拒绝后的原生失败、容量或已完整收到但不可用的响应）记录后继续固定清单。源码/身份变化、状态错位、未知未决请求、运行完整性问题和总预算耗尽则停止并准确报告部分结果。

## 汇总与结案

先报完成率、H胜F败、H败F胜，再报请求/input-output token/参考费用/环境动作/Worker与端到端时间；同时保留全部游戏与H/F共同成功子集（明确n）的成本差。区分无入口、零动作拒绝、动作后回退、技能接管直接完成、技能执行后失败；不能把F胜利全归给技能。记录已放置目标重新取回、公开放置撤销、非法提议/执行、无进展导航、循环、异常、原生解析改写，以及入口前/技能/回退的阶段成本。

追溯 D2→D1→Route D 的来源与费用，包含直接恢复发现、失败编译、生成修订及验收；缺失更早费用明确未知。研究开销与候选直接获取成本分开。仅在成本可追溯且全游戏平均节省为正时提供带假设的参考摊销，不用成功接管子集作分母。

同初态独立运行中，H败F胜仅为配对差异；未接管时不能归于技能。12局只做可行性、覆盖和代价诊断，不声称统计显著、非劣性或未来无害。结束后不修订v2、不追加样本、不把已曝光D3游戏再称独立评价。
