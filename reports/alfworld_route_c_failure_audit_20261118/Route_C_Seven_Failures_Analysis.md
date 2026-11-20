# Route C：七局原生完整失败分析

日期：2026-11-18。范围：历史开发分析；新模型请求、Worker 执行、环境动作均为 **0**。没有运行封存 60 局，也没有修改 Route A/B、原生执行器或原 120 局成绩。

## 结论

七局失败不是同一种“容器打不开”。主要现象是搜索覆盖与状态记忆丢失、持有无关物品导致后续操作受阻、重复撤销已完成子目标、目标对象和加工流程理解错误。另有必须单独处理的工程问题：**模型提出非法动作时，原解析器可能静默执行另一条合法动作。** 因而“环境没有返回 Nothing happens”并不代表模型没有发生动作错误。

目前最有重复性的学习研究候选是“保留已查位置与已完成对象的公开状态，避免无进展循环”。但重复搜索本身也出现在成功游戏中，而且简单搜索去重、持久状态账本就是现成的工程对照。不能直接把加入这些功能的收益归为失败学习。

## 1. 原始证据与口径

重新从 `alfworld_full_library_online120_20261109_01` 的环境回执、模型实际请求/响应、锁定结果、逐局技能库导出全部 120 局，未从旧诊断文字还原轨迹。7 局失败共 **338 步**，113 局成功共 **1,730 步**；原动作模型响应 **838 次，finish_reason 全部为 stop**。原模型完整输出、合法动作、每步公开观察及技能注入均保存在本轮 `episodes.private.json`。

所有终态仅在宿主分组和结果分析时使用。候选触发扫描函数只接收截至当步的目标、动作、观察、合法动作，以及已收到的模型正文；不接收最终 won、评分、游戏身份、私有状态或未来后缀。逐前缀一致性测试通过。没有将这些诊断信号接入运行时。

为避免挑选最能衬托失败的成功案例，事先固定匹配规则：同任务类型，优先同样是否有 L1 前缀，再按总步数差、题序距离、任务 ID 排序，取前两局。并在**全部113局成功轨迹**上扫描同样信号。部分任务缺少接近的成功对照，匹配不等于随机配对或因果可比。

原生模型每次只看到最近10步的动作及每条观察前120字符；这已与838份真实请求逐一核对。宿主保存完整历史，不代表模型在决策时看到了完整历史。

代码定位：原生`generator.py:137–143`裁剪历史；`generator.py:190–207`提供全文匹配与首合法动作回退；`executor.py:275`固定初始导航列表，`executor.py:423–430`处理三轮动作循环终止。执行器和生成器仍与原120局冻结哈希一致；报告没有根据当前其他模块的改动假设旧行为。

## 2. 七局总览

| 原题序 / 来源 ID | 公开目标 | 原结果 | 实际 L1 / 含L2 / 含L3动作请求 | 未完成部分 |
| --- | --- | --- | --- | --- |
| 2 / `alf-6d8a1e94ae3cc3184cdd` | put some cloth on countertop. | 38步，ACTION_CYCLE | 0 / 0 / 0 | 持有towel，没有完成cloth投递 |
| 4 / `alf-e881ccc646dccd7835a8` | put a cool egg in microwave. | 50步，STEP_LIMIT | 0 / 0 / 0 | 未取得egg，未冷却、投递 |
| 10 / `alf-563a4d100a97a1943569` | put two keychain in armchair. | 50步，STEP_LIMIT | 0 / 0 / 0 | 持有box，没有投递keychain |
| 17 / `alf-3282b836b8e26309db8e` | heat some potato and put it in garbagecan. | 50步，STEP_LIMIT | 0 / 0 / 0 | 未取得、加热或投递potato |
| 41 / `alf-9a9afdd317ac02ab2203` | find two keychain and put them in shelf. | 50步，STEP_LIMIT | 0 / 50 / 50 | 仅同一个keychain 2反复拿放，未放入第二件 |
| 46 / `alf-3c723125fe3e16a38e76` | heat some potato and put it in fridge. | 50步，STEP_LIMIT | 39 / 11 / 11 | 未取得、加热或投递potato |
| 116 / `alf-2788e10c07186b653592` | heat some cup and put it in cabinet. | 50步，STEP_LIMIT | 39 / 0 / 0 | 拿取Mug，目标对应关系未确认；未出现加热回执或完成目标投递 |

第2局终点 `done=false, won=false`，由原生循环检测停止，仍有12步额度；其余6局 `done=true, won=false`，到达50步。循环保护确实在真实重复上触发，不能仅因还剩预算就认定它是错误终止。

7 个游戏只覆盖4个场景。第4、17、46、116局都来自场景6；特别是主要搜索失败的第4、17、46局虽是3个不同任务组，仍只有1个场景，不能称为已证明跨场景共同机制。

## 3. 第2局：对象误解与静默解析回退叠加

**证据。** 第2步拿起`towel 1`，模型称其“can serve as the cloth”。第4步模型输出`Act: put towel 1 on countertop 1`，该动作不在公开合法列表；原解析器实际执行`examine countertop 1`，环境正常返回台面内容。随后反复发生同类偏差。全局25次明确意图/执行不一致，其中24次执行第一条合法动作、1次从正文匹配到inventory。第30—38步连续查看同一台面，最终命中9动作循环保护。

**判断。** 目标理解错误有明确模型文本支持；宿主来源任务身份为Cloth，Towel不应未经证据直接视为相同对象。解析器静默替换是确定存在的控制流程风险；环境忠实执行了被送入的合法查看动作，尚无环境接口故障证据。解析问题不等于唯一失败原因，修正解析也不自动解决错误持物和目标识别。

**可检测性与机会。** 第4次模型响应时即可发现“所提动作不合法、实际动作将不同”，不需要终局。第12步满足较严格重复停滞代理信号，剩余38步。当前恢复context不包含原模型意图/解析诊断，需要通用工程可观测性接入，不能冒充已有容器门控已能发现。

**成功对照。** 第3局以4步完成handtowel放置，没有解析偏差；它明显更短，不能估计本局反事实收益。第106局45步获胜也有重复开关冰箱，说明重复不等于终局失败。原生成功的49/74/84局同样有解析偏差，不能声称修复解析必然增加3个成功。

**历史探针。** 首次归还毛巾后按字典序扫描未获胜；后续改搜索顺序的宿主分支7步获胜。这证明存在开发可行路线，未单独隔离“归还错误物品”和“改变搜索顺序”的效果，且不是模型学得策略。

## 4. 第4局：搜索覆盖丢失，反复检查已知无蛋的位置

**证据。** 第2步冰箱内容无egg；第3—23步搜索柜1—10和台面1；第24步回到冰箱，内容未变。模型继续搜索已经查过的柜和台面。全局22次相同内容重访，21次上次对应回执已超出模型最近10步；到50步仍未拾取任何物品，另有18个初始可导航位置未曾访问。

**判断。** 重复搜索和预算耗尽已确认；“全部是模型忘记”不成立，因为很多旧事实根本不在当前请求里。无持久搜索摘要是明确的信息边界；选择已查位置而非剩余位置是规划现象。未知目标真实位置不能作为当时的触发条件，也不能事后断言Agent本应先去某个正确位置。

**可检测性。** 第24步相同内容回访可观察；第26步满足10步停滞代理，剩余24步。只需要历史内容对照，不需要最终结果。该信号仍会出现在成功游戏中。

**成功对照。** 第18局7步完成冷却后投递；第72局40步完成并自行打开目的容器。没有证明这两局有相同搜索难度。第35局原生43步长搜索仍获胜，也说明长搜索本身不应判错。

**历史探针。** 第24步前的短字典序扫描没有找到目标；后续公开表面优先扫描10步获胜。它支持搜索调度可以影响结果，却没有证明“只要去重就能修复”。

## 5. 第10局：无关持物阻断拾取，加上搜索与动作解析问题

**证据。** 第13步拿起box 2，第14步看到空盒后始终没有放下；第20步开始返回已空的抽屉。第42步已经看到keychain 1，但第43步合法动作没有take，存在`move box 2 to coffeetable 1`。第44步模型明确写出放下box“doesn't help”，选择离开。第50步提出不可用的take，解析器执行`examine box 2`。另有第17、27步不合法的回原地导航被替换成关柜动作。

**判断。** 当前物品占用与目标拾取前提判断错误有真实证据。不是目标位置仍完全未知，也不是缺少合法动作列表。放下盒子后take变合法已由旧同状态环境回执支持。重复搜索、类型/实例混淆和静默解析均有影响，不能把所有50步损失归于单一机制。

**可检测性。** 公共历史保留持物回执，公开观察已出现目标，合法列表显示可放下当前物品而不可拾取。真正目标相关的占手检查点是第42步后，剩余8步；宽泛“手里有物品、不能再拿”信号第16步就出现，但在86个成功游戏中也出现，不能直接触发强制放下。

**成功对照。** 第12局32步、第107局49步完成双物体任务；都经历重复搜索与重拿已放物体，之后仍取得第二件。需要保留不伤害这些恢复机会的对照。

**历史探针。** 首次放下box确实解锁拾取，8步取得第二件但预算已尽；再次使用首次探针发现的位置，8步获胜。后者的目的地知识在原检查点不可见，不能算可部署的自主恢复证据。

## 6. 第17局：跨较长历史的重复搜索，未发现目标

**证据。** 第2步已看过无potato的冰箱，第13、16、27、34、40步多次返回。第31—50步主要重复已查柜和台面，未拾取物品。共28次相同内容回访，24次对应旧回执在最近10步之外；终点仍有20个初始可导航位置未访问。

**判断。** 目标方向没有明显读错，加热/投递阶段尚未开始。主要支持“搜索覆盖与记忆/选择脱节”，不能从失败倒推所有先查柜的动作都不合理。第17步停滞代理触发，剩余33步，有理论上的干预余量；保证找到目标仍未知。

**成功对照。** 第23局曾错误地将待加热土豆先放入微波炉，后来取回并执行heat，17步获胜；第35局长L1搜索43步获胜。两者说明应该分开搜索阶段和加工阶段，不能仅按同一任务类型合并错误。

**历史探针。** 短扫描失败；扩展扫描找到并加热土豆，但预算用尽。利用该探针后来发现的位置才在6步内获胜。只证明存在路线，不证明原检查点能选择该路线。

## 7. 第41局：已完成对象的身份与子目标没有稳定保留

**证据。** 第4步已把keychain 2放到shelf 1。第15次请求只含第5—14步，第4步放置回执已被裁掉；模型称“I haven't found any keychains yet”，第16步拿回keychain 2，第17步放回。其后23/31/36/44/49步再次拿回同一件，随后放回；没有取得第二个不同ID。共6次重拿已放物体。

**判断。** 状态/子目标维护问题强于“不会投递”。原生L2/L3在50次请求均注入；相关指南确实引导回原来源，但没有同状态开关实验，不能据此归因技能负迁移。部分后期拿放在当前窗口内已经有先前放置证据，因此不能把全部问题归于10步截断。

**可检测性。** 通过同一ID的放置—重新取回关系可以发现风险；第16步后剩余34步。但“重拿已放物体”不是普适错误：成功第23局正是取回未加工物品后才成功，必须检查已满足的目标和待加工条件。

**成功对照。** 第12、107局也重拿已放的第一件，最终发现第二件并获胜。差别在于后续是否真正扩大搜索覆盖、保持不同对象ID，而不是出现一次重拿就决定失败。

**历史探针。** 第16步前保留第一件、转查未搜索位置的5步宿主分支获胜。这是较强的来源可恢复性证据，但同时改变了子目标保护和搜索路线，尚未隔离两者贡献；完整失败来源仍只有本局。

## 8. 第46局：L1搜索耗时与回退上下文丢失叠加

**证据。** L1按初始导航列表遍历，39步仍未找到potato。模型第40次动作起接管时只看到第30—39步；早期柜1—15的搜索不在最近历史。第40—42步又去柜1—3，第47—50步又查台面和柜4。7次内容重访的原回执全部在最近10步之外。

**判断。** 静态遍历与有限上下文的交接限制已确认；没有证据说明导航列表数据损坏或缓存造假。固定顺序探索到预算上限是原设计的代价，不自动等于程序Bug。需要分别比较搜索开销与回退摘要，不能把新增摘要叫作自主学到的策略。

**可检测性。** 第40步后即有回访信号，剩余10步；第42步达到停滞代理，仅余8步。恢复程序即使能避免重复，也未必有足够时间完成寻找、加热和投递。

**成功对照。** 第35局同样长L1搜索但43步直接获胜；第94局37步L1后用2步回退完成。不能把“L1消耗很多步”本身作为失败标签。

**历史探针。** 首次未访问扫描找到并加热目标，但11步用尽；已知探针位置的7步路线获胜。后者含事后位置知识，不可用来宣布公开触发下的恢复已可实现。

## 9. 第116局：目标类型与加工前提是两个问题

**证据。** 原公开目标是cup，原任务组也明确为`pick_heat_then_place_in_recep-Cup-None-Cabinet-6`。L1探索39步没取得Cup。模型第40步将cup/mug等同，第41步取mug 2；第44步heat动作已经合法，却先把mug放进微波炉，之后heat消失，模型反复开关、查看，直到50步。

**判断。** **不能把L1没有将Mug匹配为Cup直接判成同义词解析Bug。** 原任务组标注Cup，历史探针对Mug加热并投递后仍未赢，支持目标错配的疑虑；但仅凭名称不同及这一条未获胜分支，也不足以独立证明对象语义是唯一原因。本轮没有用隐藏目标状态建立在线别名规则。加工接口误解另外成立：合法heat被忽略，放下后丢失其前提。二者必须分开，不能修正heat就声称任务修好。

**可检测性。** 第44步前，目标要求、持物和合法heat均为公开信息；回执后还剩6步。对象是否满足目标仍需可靠语义判断，不能由宿主直接强制Cup=Mug。原生成功第23局存在相同先放入微波炉的局部错误，后来通过取回再heat自行恢复。

**历史探针。** 第44步前改执行heat并投递，三步后仍`won=false`，只证明局部加工动作可执行。当前没有完成目标Cup的可信获胜分支，标记整局可恢复性未证。

## 10. 成功对照下的信号统计

以下是宿主探索性测量，不是已准入触发规则。成功局中的信号不必是误报，也可能是原生自行恢复的真实局部问题；这些数值不能直接叫作触发准确率。

| 公开信号 | 失败游戏 / 7 | 成功游戏 / 113 | 解释限制 |
| --- | ---: | ---: | --- |
| 已知内容重访 | 7 | 44 | 范围太宽；目标回访、物品搬运可能需要返回 |
| 最近10步至少3次内容重访且无取放/加工类回执 | 5 | 7 | 仅是停滞代理，非真实任务进度；对第41局反复拿放会漏检 |
| 明确Act与实际执行动作不同 | 3 | 3 | 应先作为工程诊断；成功组也能自行恢复 |
| 重拿先前已放置的同一物品 | 1 | 4 | 加工纠正、转移目的地等可能正当 |
| 任务加工动作可用但先放下该物品 | 1 | 1 | 应确认目标实例、阶段，成功第23局会自行恢复 |
| 持物、看见其他对象、无take但有move | 2 | 86 | 极宽，不能作为独立失败触发条件 |

解析器838次动作请求中：783次精确Act匹配、36次首合法动作回退、19次全文子串匹配。38次有明确的Act/执行偏差（失败局31次，成功局7次）；另17次包含与Think连在同一行的Act，不能统称为算法错误。全部供应商响应完整结束，不是截断或网络失败。

## 11. 已执行与未执行

本轮完成全部原始来源核验、成功对照扫描、旧探针39个工件的哈希检查及14条旧分支的前缀/合法动作链审查；没有新跑探针。旧七局原始步骤与本轮从原生日志重新导出的338步逐字段一致。旧探针中的已知位置路线单独标为宿主事后信息，未进入触发函数。

80项零API测试通过，包含原解析器重放、逐前缀无未来依赖、成功对照选择、历史窗口核验、旧探针来源隔离及原桥接回归。一次测试发现审计元数据漏标“first public probe”的事后位置来源，已在Supporting Evidence v2修正；v1与失败测试日志保留，未更改任何旧探针结果或本轮信号规则。

完整逐局动作、观察、模型正文、合法列表和公开状态见本地 `runs/alfworld_route_c_failure_audit_20261118_01/Case_*.private.md`；机器可读全量为`episodes.private.json`。下列附表直接由原回执提取末20步，长观察缩略仅用于显示，完整正文与SHA保持在私有附件中。

### 附表：第2局末20步（19—38）

[完整逐步原文及模型输出](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_c_failure_audit_20261118_01/Case_002.private.md)

| 步 | 执行者 | 实际动作 | 原环境观察（显示至120字符） | 原回执SHA前12位 |
| ---: | --- | --- | --- | --- |
| 19 | MODEL | `examine countertop 1` | On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybottle 3, and a spraybottle 2. | `dd9decfa523c` |
| 20 | MODEL | `examine countertop 1` | On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybottle 3, and a spraybottle 2. | `a59bbc9ec8cb` |
| 21 | MODEL | `go to cabinet 1` | You arrive at cabinet 1. The cabinet 1 is closed. | `53a8b8bc282f` |
| 22 | MODEL | `open cabinet 1` | You open the cabinet 1. The cabinet 1 is open. In it, you see nothing. | `6eb9f2b08123` |
| 23 | MODEL | `open cabinet 2` | You open the cabinet 2. The cabinet 2 is open. In it, you see a soapbar 3, a soapbar 2, and a soapbottle 1. | `fab1957436d2` |
| 24 | MODEL | `go to cabinet 3` | You arrive at cabinet 3. The cabinet 3 is closed. | `45e04c4e4727` |
| 25 | MODEL | `open cabinet 3` | You open the cabinet 3. The cabinet 3 is open. In it, you see a candle 1. | `1552ca2ff501` |
| 26 | MODEL | `go to towelholder 1` | You arrive at towelholder 1. On the towelholder 1, you see nothing. | `66432268c81f` |
| 27 | MODEL | `examine towel 1` | There's nothing special about towel 1. | `ba0b62487853` |
| 28 | MODEL | `inventory` | You are carrying: a towel 1. | `dbbd55fe18aa` |
| 29 | MODEL | `go to countertop 1` | You arrive at countertop 1. On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybo… | `caf525461df7` |
| 30 | MODEL | `examine countertop 1` | On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybottle 3, and a spraybottle 2. | `4f83e41ee302` |
| 31 | MODEL | `examine countertop 1` | On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybottle 3, and a spraybottle 2. | `3b3dcae47363` |
| 32 | MODEL | `examine countertop 1` | On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybottle 3, and a spraybottle 2. | `ea1cf3344a9c` |
| 33 | MODEL | `examine countertop 1` | On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybottle 3, and a spraybottle 2. | `f0781e0d4f41` |
| 34 | MODEL | `examine countertop 1` | On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybottle 3, and a spraybottle 2. | `f92eeb0d2d9f` |
| 35 | MODEL | `examine countertop 1` | On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybottle 3, and a spraybottle 2. | `2f89a22ab40a` |
| 36 | MODEL | `examine countertop 1` | On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybottle 3, and a spraybottle 2. | `437c21eabf12` |
| 37 | MODEL | `examine countertop 1` | On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybottle 3, and a spraybottle 2. | `40b39e193467` |
| 38 | MODEL | `examine countertop 1` | On the countertop 1, you see a candle 2, a dishsponge 2, a sink 1, a soapbottle 2, a spraybottle 3, and a spraybottle 2. | `ad9f29a1f561` |

### 附表：第4局末20步（31—50）

[完整逐步原文及模型输出](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_c_failure_audit_20261118_01/Case_004.private.md)

| 步 | 执行者 | 实际动作 | 原环境观察（显示至120字符） | 原回执SHA前12位 |
| ---: | --- | --- | --- | --- |
| 31 | MODEL | `go to cabinet 6` | You arrive at cabinet 6. The cabinet 6 is open. In it, you see nothing. | `8430be788341` |
| 32 | MODEL | `go to cabinet 7` | You arrive at cabinet 7. The cabinet 7 is open. In it, you see a saltshaker 1. | `e26eb2983af9` |
| 33 | MODEL | `go to fridge 1` | You arrive at fridge 1. The fridge 1 is open. In it, you see a apple 3, a apple 2, a pan 1, a potato 1, and a tomato 1. | `48741bbf325e` |
| 34 | MODEL | `go to countertop 2` | You arrive at countertop 2. On the countertop 2, you see a mug 1, a spatula 1, and a spoon 1. | `78cd3f27d307` |
| 35 | MODEL | `go to drawer 1` | You arrive at drawer 1. The drawer 1 is closed. | `82b411e0bd32` |
| 36 | MODEL | `open drawer 1` | You open the drawer 1. The drawer 1 is open. In it, you see nothing. | `0cebee99789f` |
| 37 | MODEL | `go to cabinet 1` | You arrive at cabinet 1. The cabinet 1 is open. In it, you see a dishsponge 2. | `9842563cad38` |
| 38 | MODEL | `go to cabinet 2` | You arrive at cabinet 2. The cabinet 2 is open. In it, you see a kettle 1. | `3f808a0e6426` |
| 39 | MODEL | `go to cabinet 3` | You arrive at cabinet 3. The cabinet 3 is open. In it, you see nothing. | `a2e98533d1fd` |
| 40 | MODEL | `go to cabinet 4` | You arrive at cabinet 4. The cabinet 4 is open. In it, you see a saltshaker 2. | `91b111018e6f` |
| 41 | MODEL | `go to cabinet 5` | You arrive at cabinet 5. The cabinet 5 is open. In it, you see nothing. | `9782d79ac718` |
| 42 | MODEL | `go to cabinet 6` | You arrive at cabinet 6. The cabinet 6 is open. In it, you see nothing. | `d1b8c83eb5ee` |
| 43 | MODEL | `go to cabinet 7` | You arrive at cabinet 7. The cabinet 7 is open. In it, you see a saltshaker 1. | `ac9013e0a0a3` |
| 44 | MODEL | `go to fridge 1` | You arrive at fridge 1. The fridge 1 is open. In it, you see a apple 3, a apple 2, a pan 1, a potato 1, and a tomato 1. | `43d2e1fd072a` |
| 45 | MODEL | `go to countertop 1` | You arrive at countertop 1. On the countertop 1, you see a dishsponge 1. | `56cbf709e59c` |
| 46 | MODEL | `go to drawer 2` | You arrive at drawer 2. The drawer 2 is closed. | `2bffa1c6695d` |
| 47 | MODEL | `open drawer 2` | You open the drawer 2. The drawer 2 is open. In it, you see nothing. | `c9c5870e8078` |
| 48 | MODEL | `go to cabinet 8` | You arrive at cabinet 8. The cabinet 8 is open. In it, you see a mug 2. | `f3ee0119a14b` |
| 49 | MODEL | `go to cabinet 9` | You arrive at cabinet 9. The cabinet 9 is open. In it, you see nothing. | `8b7aa542feb4` |
| 50 | MODEL | `go to cabinet 10` | You arrive at cabinet 10. The cabinet 10 is open. In it, you see a peppershaker 1, and a soapbottle 1. | `44b8fba1a574` |

### 附表：第10局末20步（31—50）

[完整逐步原文及模型输出](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_c_failure_audit_20261118_01/Case_010.private.md)

| 步 | 执行者 | 实际动作 | 原环境观察（显示至120字符） | 原回执SHA前12位 |
| ---: | --- | --- | --- | --- |
| 31 | MODEL | `examine cabinet 3` | The cabinet 3 is open. In it, you see a box 1. | `ad1248b3affe` |
| 32 | MODEL | `go to cabinet 1` | You arrive at cabinet 1. The cabinet 1 is open. In it, you see nothing. | `f0af03a68f75` |
| 33 | MODEL | `go to cabinet 2` | You arrive at cabinet 2. The cabinet 2 is open. In it, you see nothing. | `975890d35948` |
| 34 | MODEL | `go to drawer 1` | You arrive at drawer 1. The drawer 1 is open. In it, you see nothing. | `e7745e593fe7` |
| 35 | MODEL | `go to drawer 2` | You arrive at drawer 2. The drawer 2 is open. In it, you see nothing. | `a369c12e7b34` |
| 36 | MODEL | `go to drawer 3` | You arrive at drawer 3. The drawer 3 is open. In it, you see nothing. | `232ec795900f` |
| 37 | MODEL | `go to drawer 4` | You arrive at drawer 4. The drawer 4 is open. In it, you see nothing. | `d5c1dd0fc419` |
| 38 | MODEL | `go to cabinet 3` | You arrive at cabinet 3. The cabinet 3 is open. In it, you see a box 1. | `24a0687b3492` |
| 39 | MODEL | `examine cabinet 3` | The cabinet 3 is open. In it, you see a box 1. | `b0464972d31b` |
| 40 | MODEL | `examine box 2` | This is a normal box 2. In it, you see nothing. | `31d25200d8cc` |
| 41 | MODEL | `go to dresser 1` | You arrive at dresser 1. On the dresser 1, you see a houseplant 1, a laptop 1, and a television 1. | `4ba702828257` |
| 42 | MODEL | `go to coffeetable 1` | You arrive at coffeetable 1. On the coffeetable 1, you see a creditcard 1, a keychain 1, a remotecontrol 2, and a statue… | `18b2f1d0306b` |
| 43 | MODEL | `examine coffeetable 1` | On the coffeetable 1, you see a creditcard 1, a keychain 1, a remotecontrol 2, and a statue 1. | `4f0266ee573c` |
| 44 | MODEL | `go to armchair 1` | You arrive at armchair 1. On the armchair 1, you see nothing. | `33863bdb4730` |
| 45 | MODEL | `go to coffeetable 1` | You arrive at coffeetable 1. On the coffeetable 1, you see a creditcard 1, a keychain 1, a remotecontrol 2, and a statue… | `bdad2ab5609a` |
| 46 | MODEL | `examine coffeetable 1` | On the coffeetable 1, you see a creditcard 1, a keychain 1, a remotecontrol 2, and a statue 1. | `225658196b60` |
| 47 | MODEL | `go to armchair 1` | You arrive at armchair 1. On the armchair 1, you see nothing. | `ecce75f82771` |
| 48 | MODEL | `go to coffeetable 1` | You arrive at coffeetable 1. On the coffeetable 1, you see a creditcard 1, a keychain 1, a remotecontrol 2, and a statue… | `983aac121ce6` |
| 49 | MODEL | `examine coffeetable 1` | On the coffeetable 1, you see a creditcard 1, a keychain 1, a remotecontrol 2, and a statue 1. | `8d96177ba1ef` |
| 50 | MODEL | `examine box 2` | This is a normal box 2. In it, you see nothing. | `b705d09e9463` |

### 附表：第17局末20步（31—50）

[完整逐步原文及模型输出](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_c_failure_audit_20261118_01/Case_017.private.md)

| 步 | 执行者 | 实际动作 | 原环境观察（显示至120字符） | 原回执SHA前12位 |
| ---: | --- | --- | --- | --- |
| 31 | MODEL | `go to cabinet 3` | You arrive at cabinet 3. The cabinet 3 is open. In it, you see a saltshaker 1. | `1bb02fef9219` |
| 32 | MODEL | `go to cabinet 4` | You arrive at cabinet 4. The cabinet 4 is open. In it, you see nothing. | `dc71cc6a29d6` |
| 33 | MODEL | `go to cabinet 5` | You arrive at cabinet 5. The cabinet 5 is open. In it, you see nothing. | `12ce60ba36da` |
| 34 | MODEL | `go to fridge 1` | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 3, a bread 1, and a plate 2. | `725af632aaa5` |
| 35 | MODEL | `go to countertop 2` | You arrive at countertop 2. On the countertop 2, you see a egg 1, a mug 1, and a pan 1. | `40b461b9412d` |
| 36 | MODEL | `go to countertop 3` | You arrive at countertop 3. On the countertop 3, you see a bowl 1, a butterknife 2, a fork 1, a kettle 1, a knife 2, a k… | `61ca71489018` |
| 37 | MODEL | `go to countertop 4` | You arrive at countertop 4. On the countertop 4, you see a apple 1, a bread 2, a lettuce 1, a papertowelroll 1, a plate … | `8fdb262a7b19` |
| 38 | MODEL | `go to countertop 3` | You arrive at countertop 3. On the countertop 3, you see a bowl 1, a butterknife 2, a fork 1, a kettle 1, a knife 2, a k… | `9a1a5a4d920d` |
| 39 | MODEL | `go to countertop 1` | You arrive at countertop 1. On the countertop 1, you see a spatula 1. | `0c3d4a2d146c` |
| 40 | MODEL | `go to fridge 1` | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 3, a bread 1, and a plate 2. | `e33604ab67af` |
| 41 | MODEL | `go to cabinet 1` | You arrive at cabinet 1. The cabinet 1 is open. In it, you see a plate 1. | `c420286e8fd9` |
| 42 | MODEL | `go to cabinet 2` | You arrive at cabinet 2. The cabinet 2 is open. In it, you see nothing. | `9cbcfef3dec1` |
| 43 | MODEL | `go to cabinet 3` | You arrive at cabinet 3. The cabinet 3 is open. In it, you see a saltshaker 1. | `85110f7e74de` |
| 44 | MODEL | `go to cabinet 4` | You arrive at cabinet 4. The cabinet 4 is open. In it, you see nothing. | `d1c5e13912a7` |
| 45 | MODEL | `go to cabinet 5` | You arrive at cabinet 5. The cabinet 5 is open. In it, you see nothing. | `f5fdb7ff1e84` |
| 46 | MODEL | `go to cabinet 6` | You arrive at cabinet 6. The cabinet 6 is open. In it, you see nothing. | `9b5bf86295fd` |
| 47 | MODEL | `go to cabinet 7` | You arrive at cabinet 7. The cabinet 7 is open. In it, you see nothing. | `12f4d7edb0f9` |
| 48 | MODEL | `go to countertop 2` | You arrive at countertop 2. On the countertop 2, you see a egg 1, a mug 1, and a pan 1. | `ceab5d61e980` |
| 49 | MODEL | `go to countertop 3` | You arrive at countertop 3. On the countertop 3, you see a bowl 1, a butterknife 2, a fork 1, a kettle 1, a knife 2, a k… | `4dcfbd8f15e4` |
| 50 | MODEL | `go to countertop 1` | You arrive at countertop 1. On the countertop 1, you see a spatula 1. | `1e87b9915564` |

### 附表：第41局末20步（31—50）

[完整逐步原文及模型输出](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_c_failure_audit_20261118_01/Case_041.private.md)

| 步 | 执行者 | 实际动作 | 原环境观察（显示至120字符） | 原回执SHA前12位 |
| ---: | --- | --- | --- | --- |
| 31 | MODEL | `take keychain 2 from shelf 1` | You pick up the keychain 2 from the shelf 1. | `43e1d023e438` |
| 32 | MODEL | `move keychain 2 to shelf 1` | You move the keychain 2 to the shelf 1. | `8bbc5d98e221` |
| 33 | MODEL | `go to shelf 2` | You arrive at shelf 2. On the shelf 2, you see nothing. | `deb979249724` |
| 34 | MODEL | `go to shelf 3` | You arrive at shelf 3. On the shelf 3, you see nothing. | `2052dae521c1` |
| 35 | MODEL | `go to shelf 1` | You arrive at shelf 1. On the shelf 1, you see a keychain 2. | `b4df1e4868ab` |
| 36 | MODEL | `take keychain 2 from shelf 1` | You pick up the keychain 2 from the shelf 1. | `4503283b525d` |
| 37 | MODEL | `move keychain 2 to shelf 1` | You move the keychain 2 to the shelf 1. | `26cc39be7cc6` |
| 38 | MODEL | `go to coffeetable 1` | You arrive at coffeetable 1. On the coffeetable 1, you see a houseplant 1, a remotecontrol 1, a watch 2, and a watch 1. | `baa40835c7ec` |
| 39 | MODEL | `go to shelf 4` | You arrive at shelf 4. On the shelf 4, you see nothing. | `6beddcaba5f9` |
| 40 | MODEL | `go to shelf 5` | You arrive at shelf 5. On the shelf 5, you see nothing. | `5211b6590f5f` |
| 41 | MODEL | `examine shelf 5` | On the shelf 5, you see nothing. | `493480bb994a` |
| 42 | MODEL | `examine shelf 5` | On the shelf 5, you see nothing. | `3cb3b749b2bf` |
| 43 | MODEL | `go to shelf 1` | You arrive at shelf 1. On the shelf 1, you see a keychain 2. | `cf80f28aa161` |
| 44 | MODEL | `take keychain 2 from shelf 1` | You pick up the keychain 2 from the shelf 1. | `c33482ce66ac` |
| 45 | MODEL | `move keychain 2 to shelf 1` | You move the keychain 2 to the shelf 1. | `82d402a1073d` |
| 46 | MODEL | `go to shelf 2` | You arrive at shelf 2. On the shelf 2, you see nothing. | `fde2cd3c7b1e` |
| 47 | MODEL | `go to shelf 3` | You arrive at shelf 3. On the shelf 3, you see nothing. | `3dc80d774682` |
| 48 | MODEL | `go to shelf 1` | You arrive at shelf 1. On the shelf 1, you see a keychain 2. | `2942b21e6e09` |
| 49 | MODEL | `take keychain 2 from shelf 1` | You pick up the keychain 2 from the shelf 1. | `94ba322c9819` |
| 50 | MODEL | `move keychain 2 to shelf 1` | You move the keychain 2 to the shelf 1. | `2e85ddd3a247` |

### 附表：第46局末20步（31—50）

[完整逐步原文及模型输出](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_c_failure_audit_20261118_01/Case_046.private.md)

| 步 | 执行者 | 实际动作 | 原环境观察（显示至120字符） | 原回执SHA前12位 |
| ---: | --- | --- | --- | --- |
| 31 | L1_PATH | `go to coffeemachine 1` | You arrive at coffeemachine 1. On the coffeemachine 1, you see a mug 2. | `e7b376491b04` |
| 32 | L1_PATH | `go to countertop 1` | You arrive at countertop 1. On the countertop 1, you see a papertowelroll 1. | `cfe676563877` |
| 33 | L1_PATH | `go to countertop 2` | You arrive at countertop 2. On the countertop 2, you see a bowl 1, a kettle 1, a mug 2, and a saltshaker 1. | `4cf2249101a0` |
| 34 | L1_PATH | `go to countertop 3` | You arrive at countertop 3. On the countertop 3, you see a fork 3, a fork 2, a lettuce 1, a pan 2, a peppershaker 2, a p… | `0d77a1318257` |
| 35 | L1_PATH | `go to countertop 4` | You arrive at countertop 4. On the countertop 4, you see a bowl 2, a bread 2, a butterknife 1, a egg 1, a fork 1, a lett… | `f8f501ceab8f` |
| 36 | L1_PATH | `go to drawer 1` | You arrive at drawer 1. The drawer 1 is closed. | `956fd10c3c14` |
| 37 | L1_PATH | `open drawer 1` | You open the drawer 1. The drawer 1 is open. In it, you see a knife 1, and a spoon 2. | `a1095b9c9720` |
| 38 | L1_PATH | `go to drawer 2` | You arrive at drawer 2. The drawer 2 is closed. | `70a996469112` |
| 39 | L1_PATH | `open drawer 2` | You open the drawer 2. The drawer 2 is open. In it, you see a knife 2. | `570b78b1626d` |
| 40 | MODEL | `go to cabinet 1` | You arrive at cabinet 1. The cabinet 1 is open. In it, you see a cup 1, and a dishsponge 1. | `00e383a39f69` |
| 41 | MODEL | `go to cabinet 2` | You arrive at cabinet 2. The cabinet 2 is open. In it, you see nothing. | `dbc17bde7f36` |
| 42 | MODEL | `go to cabinet 3` | You arrive at cabinet 3. The cabinet 3 is open. In it, you see nothing. | `a439508cce15` |
| 43 | MODEL | `go to microwave 1` | You arrive at microwave 1. The microwave 1 is closed. | `dcea25f4947f` |
| 44 | MODEL | `open microwave 1` | You open the microwave 1. The microwave 1 is open. In it, you see nothing. | `7a0f326c6801` |
| 45 | MODEL | `go to fridge 1` | You arrive at fridge 1. The fridge 1 is closed. | `3a7f7670171a` |
| 46 | MODEL | `open fridge 1` | You open the fridge 1. The fridge 1 is open. In it, you see a apple 2, a apple 1, a bread 1, and a plate 1. | `818af62c71cf` |
| 47 | MODEL | `go to countertop 1` | You arrive at countertop 1. On the countertop 1, you see a papertowelroll 1. | `1f7593c459a5` |
| 48 | MODEL | `go to countertop 2` | You arrive at countertop 2. On the countertop 2, you see a bowl 1, a kettle 1, a mug 2, and a saltshaker 1. | `14d0c4d39e69` |
| 49 | MODEL | `go to countertop 3` | You arrive at countertop 3. On the countertop 3, you see a fork 3, a fork 2, a lettuce 1, a pan 2, a peppershaker 2, a p… | `8bb267ebfcb4` |
| 50 | MODEL | `go to cabinet 4` | You arrive at cabinet 4. The cabinet 4 is open. In it, you see a kettle 3. | `5884196737a3` |

### 附表：第116局末20步（31—50）

[完整逐步原文及模型输出](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_c_failure_audit_20261118_01/Case_116.private.md)

| 步 | 执行者 | 实际动作 | 原环境观察（显示至120字符） | 原回执SHA前12位 |
| ---: | --- | --- | --- | --- |
| 31 | L1_PATH | `go to coffeemachine 1` | You arrive at coffeemachine 1. On the coffeemachine 1, you see a mug 2. | `b05c607124f9` |
| 32 | L1_PATH | `go to countertop 1` | You arrive at countertop 1. On the countertop 1, you see a butterknife 1, a papertowelroll 1, and a tomato 1. | `a1b639904cca` |
| 33 | L1_PATH | `go to countertop 2` | You arrive at countertop 2. On the countertop 2, you see a butterknife 2, a fork 1, a kettle 2, and a mug 2. | `9120364c40b1` |
| 34 | L1_PATH | `go to countertop 3` | You arrive at countertop 3. On the countertop 3, you see a bowl 2, a butterknife 3, a mug 3, and a saltshaker 1. | `19b2f718b0cc` |
| 35 | L1_PATH | `go to countertop 4` | You arrive at countertop 4. On the countertop 4, you see a bread 1, a lettuce 1, a peppershaker 2, a plate 2, a plate 1,… | `a94d1d595575` |
| 36 | L1_PATH | `go to drawer 1` | You arrive at drawer 1. The drawer 1 is closed. | `0ba7f19850ae` |
| 37 | L1_PATH | `open drawer 1` | You open the drawer 1. The drawer 1 is open. In it, you see nothing. | `57523ea0718c` |
| 38 | L1_PATH | `go to drawer 2` | You arrive at drawer 2. The drawer 2 is closed. | `0fdfc4531a0b` |
| 39 | L1_PATH | `open drawer 2` | You open the drawer 2. The drawer 2 is open. In it, you see a knife 1. | `d5a596ec6e0f` |
| 40 | MODEL | `go to coffeemachine 1` | You arrive at coffeemachine 1. On the coffeemachine 1, you see a mug 2. | `d9720e7a8775` |
| 41 | MODEL | `take mug 2 from coffeemachine 1` | You pick up the mug 2 from the coffeemachine 1. | `1313e5bec467` |
| 42 | MODEL | `go to microwave 1` | You arrive at microwave 1. The microwave 1 is closed. | `e181969d25f0` |
| 43 | MODEL | `open microwave 1` | You open the microwave 1. The microwave 1 is open. In it, you see a apple 1, and a egg 2. | `9d112c8a2fac` |
| 44 | MODEL | `move mug 2 to microwave 1` | You move the mug 2 to the microwave 1. | `752a172a36cc` |
| 45 | MODEL | `close microwave 1` | You close the microwave 1. | `b88fc6340dea` |
| 46 | MODEL | `examine microwave 1` | The microwave 1 is closed. | `7484fd93c0af` |
| 47 | MODEL | `examine microwave 1` | The microwave 1 is closed. | `91fb955e0ad0` |
| 48 | MODEL | `open microwave 1` | You open the microwave 1. The microwave 1 is open. In it, you see a apple 1, a egg 2, and a mug 2. | `00ddacd1fd58` |
| 49 | MODEL | `close microwave 1` | You close the microwave 1. | `c37efc5563c8` |
| 50 | MODEL | `examine microwave 1` | The microwave 1 is closed. | `1df5dae99d7b` |

