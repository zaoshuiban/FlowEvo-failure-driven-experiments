# Route D4：真实复用反馈修订与新任务配对验证

执行前冻结日期2026-11-19。研究当前程序的反馈修订流程，不识别失败信息相对恢复示范的独立贡献。原v2 SHA256：59ff438fafdb2675fc33d4a1543bce38088b59703cd9a85840cdd26407f67e04，来源为D3冻结链。只允许模型改候选，宿主不提供修好的解析、搜索或退出代码。

## 共同执行条件与旧夹具

H是带冻结成功经验库的Flash控制器，不是完整FlowEvo。沿用D3的full_user/public_history、原生提示/解析/合法回退、冻结成功库、首次非终态目标物品放置入口、50整局动作、3×3循环及连续3次nothing happens整局停止、Worker权限、context_view和state接口。初始公开观察以空action历史条目保留，之后全量真实action/observation；不截断。模型wire和Worker context各<=65536字节，state<=4096，返回<=8192。无新成功库更新、强制短接管、宿主搜索或反思。

学习前使用D3 TissueBox真实入口，单独的契约测试程序执行该归档中的一个合法移动，然后返回declined；验证H从实际改变的状态继续一个真实动作，所有前缀/已用步数/停止历史保留。人工测试程序仅验证宿主接口，明确不进入学习材料、不作为恢复候选。此契约已有实现，预期无需宿主修补；若验收不符，先停止核对，只允许共同契约修复后重冻结。

## 反馈与提交

Feedback_Package.json含完整原v2、原SOURCE_CONTRACT、五个put two目标拒绝的公开初态/增量前缀/Worker回执，以及CD、TissueBox的真实技能后缀和终止结果；SoapBar包含同一D3 F分支拒绝后的真实原生恢复示范。不是纯失败信息。来源文件路径/哈希齐全，不含其他分支未来正确动作、专家计划、私有状态或新评价目标。初始上下文加增量，未复制每次Worker的整份完整历史。

模型配置从D1实际成功v2请求读取：deepseek-v4-pro，thinking enabled，reasoning_effort low，max_tokens32768，JSON response_format，stream false，未额外加temperature。最多s1/s2两次提交，交付截断、静态失败均占额度，不换模型或配置。输入采用原D1本地tokenizer计量，ceil(tokens×1.25)+1024<=65536，完整请求不截断，输入容量不够停止。初稿预检上界52269 tokens。实际usage超过预留估计或发送状态未知则完整性停止。

仅首次未通过固定开发验收时提交s2，包含其完整源码及真实执行反馈；无第三次。先通过原有静态检查和人工只读参数化核对，再执行固定三个开发游戏各一次。源码按s1/s2和SHA留存，绝不人工修补。

开发顺序SoapBar、CD、TissueBox，均从D3 F的真实首次放置状态reset/replay，state为空，prefix+suffix<=50。SoapBar/TissueBox必须由程序完成后缀并获won=true。CD必须由程序完成，或在整局停止前主动declined且交回时至少剩10步；交回后由H真实继续，分别报告退出、继续和最终成败。没有非法实际动作或权限错误，不可物品/场景/实例/路线特判或全面拒绝。五个拒绝入口另做Worker输出检查，不记作恢复成功。首个全部通过的候选立即冻结；两次未通过则开发阶段结案，新游戏环境不加载。

## 正式样本与隔离

沿用曝光审计，排除全部已记录学习/开发/评价/预留组，含D3全部12组与封存60局。刷新后同类可用435游戏，按公开原始任务文本分层：put_two 228、other 207。只从游戏文件grammar.task读取公开原始目标用于分层，不运行环境、候选或专家walkthrough；不改写实际目标。目标与清单放在独立selection.private.json，编译请求构造不读取它。以ROUTE_D4_FEEDBACK_REVISION_V1按已选场景数/物品类别数/哈希顺序各选6组，共12不同组，交替排列两个层；选定清单先冻结，无结果筛选和替换。允许已见场景，仅主张本地记录中的新游戏/组，不声称官方test split或未见场景迁移。

|序号|层|游戏身份|任务组|
|---|---|---|---|
|0|put_two|alf-e46e7b40cb4d04f0a2cb|pick_two_obj_and_place-Kettle-None-DiningTable-18|
|1|other|alf-030b6c1205560b81c6a4|pick_two_obj_and_place-SoapBottle-None-Toilet-426|
|2|put_two|alf-686b4f4487be51eeb7df|pick_two_obj_and_place-CreditCard-None-ArmChair-311|
|3|other|alf-e1677e0ff06a9e27f792|pick_two_obj_and_place-Cup-None-Microwave-26|
|4|put_two|alf-150763151d642e468da9|pick_two_obj_and_place-Candle-None-Drawer-409|
|5|other|alf-da5473529e759201bac6|pick_two_obj_and_place-Bread-None-Fridge-7|
|6|put_two|alf-fbba445ec6c545af7407|pick_two_obj_and_place-Ladle-None-Drawer-2|
|7|other|alf-0503591109e82ea893a5|pick_two_obj_and_place-ToiletPaper-None-Cabinet-402|
|8|put_two|alf-ee0724713d54e1822ca3|pick_two_obj_and_place-Newspaper-None-ArmChair-230|
|9|other|alf-9126f34c880ba7e13359|pick_two_obj_and_place-WateringCan-None-Shelf-214|
|10|put_two|alf-e8240df4f8d1141ae674|pick_two_obj_and_place-RemoteControl-None-ArmChair-209|
|11|other|alf-bd601bde865cf9b766e0|pick_two_obj_and_place-DishSponge-None-Cart-430|

每游戏2次独立H公共前缀，24区组，最多72逻辑结果；独立游戏数为12。三组H/F2/F3，六种分支排列各4次，提前冻结。每个重复从初态真正执行H，到首次非终态目标放置保存prefix；三个分支独立reset/replay，核对逐步公开回执、目标、当前合法命令及起点签名，共享50−prefix预算。入口前已终止或用完预算，则同一真实终态引用给三策略，仍计入全部统计。不只保留到达入口的区组。

每个候选最多接管一次；state从空开始，动作真实改变环境。declined/error后H从实际状态续跑，不退还步数、不reset、不清循环/无进展计数。没有强制提前退出，主动交回必须来自程序返回。

零动作declined时，比较当前H完整输入、历史、库、剩余步数、控制器状态（本入口为无持久隐藏状态）、全部整局停止历史与共同起点签名。一致则引用本区组同一条真实H后缀，仅增加实际Worker开销；规则不看H成败，即便H尚未运行也先固定引用，待其运行后以轨迹路径及哈希解析。不复制API请求或伪造独立执行。若签名不一致视为状态完整性异常停止，不强行合并。非declined错误及执行过动作的候选均不共享后缀，独立继续H。

## 预算、成本与停止

独立新账本，不使用D3余额。硬上限：2候选提交，3开发案例×最多2轮，12新游戏×2重复、24区组/72逻辑结果；4000全部模型请求，5200全部环境动作（含重放/验收/开发），3000 Worker，$17保守预留，3小时，单请求绝对600秒。

为了同时使用现有固定费率账本，预先分配Pro生成账本<=2请求/$1、Flash原生账本<=3998请求/$16（Worker记在此账本），相加不超过4000/$17；不跨账本借额。Pro每请求按65536输入+32768输出、统一最高$3.96/百万预留；Flash沿用wire字节+256的输入保守上界加1024输出，统一$1.20/百万预留。两账本同一运行开始，使用较早截止。预算是停止线，不保证跑满所有上限。

价格按2026-11-19核对的[官方价格](https://api-docs.deepseek.com/quick_start/pricing/)：Flash峰时未缓存输入0.30/输出1.20，Pro输入1.32/输出3.96，单位USD/百万token。实际usage、参考价、保守预留、供应商账单分别报告；账单未知不得伪报。Worker美元价格未知，记录次数/时间。实际API目的地api.deepseek.com；生成请求Pro，原生请求Flash。新授权独立于D3。

每个策略逻辑任务成本=公共前缀+自身后缀（或引用同一H后缀）+自身Worker。前缀不免费，共享后缀也不免费；实际账本只计唯一发生请求/动作，reset重放仅计实验开销。端到端逻辑时间用公共前缀实际执行时间+后缀执行时间，剔除额外reset/replay；另报所有实验总时间。不得称72条独立在线轨迹。

普通候选失败和循环保留并继续预定样本；两次开发不通过、预算触顶、未知请求、源码变化、数据泄漏或重放不一致按规则停止。不自动重发，不换题，不追加第三版，不用正式结果再修订重测。

## 汇总

按put_two/other分别报入口、零动作拒绝、实际技能动作、程序直接完成、动作后主动交回、交回后原生成功/失败、技能循环或预算失败。F3/F2与F3/H各报四格配对结果和退化案例；两重复先游戏内汇总再跨游戏统计，报告重复一致性。全部样本与共同成功子集同时报完整请求、input/output token、参考费用、环境动作、Worker与时间；少调用若来自失败不称效率提升。整体是6+6设计分布，不代表任务池自然比例。

人工重点审阅候选源码中的硬编码、真实失败/异常/结果分歧；自动核验哈希、曝光排除、prefix签名及预算。最终分别回答覆盖、退出、整局完成、执行成本，不让其互相替代。结束后冻结结案，不自动追加任何学习或评价。
