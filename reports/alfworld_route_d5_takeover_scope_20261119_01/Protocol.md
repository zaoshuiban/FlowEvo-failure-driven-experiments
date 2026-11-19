# Route D5：冻结 s1 的接管范围实验

执行前冻结日期：2026-11-19。零候选生成／修订请求，唯一新增策略条件为宿主执行技能 8 个实际环境动作后交回 H。不搜索窗口，不改源码，不增加物品或案例例外。D4 原归档不变。

## 候选、入口和共同条件

s1 SHA-256：`c0d6ea0b3c9848cc52ed69a94c31554a271b73e09a5bcf574cf6c9f3c3b68079`。来源链由 D4 Selected_Candidate.json、Candidate_Host_Freeze.json 指向原始提交与选定副本；本轮 frozen/code.py 是逐字复制。Candidate_Identity.json 在采样前冻结源码、窗口和选择规则；具体组件哈希见 Candidate_Host_Freeze.json。

H 是带冻结成功经验库的 Flash 控制器，不是完整 FlowEvo。完整公开历史、原生提示、动作解析及合法回退、成功库、首次非终态目标物品放置入口、整局 50 动作、3×3 循环和连续 3 次 Nothing happens 停止、Worker 权限及 context_view/state 均沿用 D4。不更新成功库。模型 wire 和 Worker context 各不超过 65536 字节；state 4096、返回 8192；不截断输入。Worker 无网络、2 秒、256 MiB、1 CPU，沿用冻结镜像和脚本。

三个条件为 H、F_full、F8。F_full 沿用 D4 接管至程序退出或全局停止。F8 仅改变宿主单次接管动作上限为 8；不把窗口或新的提示放入程序输入、不重写整局剩余步数。state 从空开始，返回 state 正常传递。

每个实际环境动作后先处理 won、done、整局循环、无进展及 50 步用尽；仍可继续且已执行 8 个技能动作，才记录 HOST_WINDOW_EXHAUSTED、切换至 H，不调用第 9 次 Worker，不重入技能。程序主动 declined 记 CANDIDATE_DECLINED；错误单列；ENVIRONMENT_WON 和 TASK_BUDGET_EXHAUSTED 与交回事件分别记录。强制交回不是模型学会退出。

## 旧证据和技术验收

只读核对 D4 Kettle、Candle、Ladle 两次重复共六个入口。实际公开历史与 Worker 已解析状态均只显示已放置目标实例，未显示第二件未放置实例的位置；相关首次搜索及反馈见 Old_Public_Evidence.json 与 Old_Public_Evidence.md。未知具体位置不证明每个搜索动作必要；不把后来 H 成功路线当作入口知识，不据此改候选、门控、窗口或样本。

仅两项旧技术夹具：D4 formal/01/0 的 SoapBottle 入口验证短链在窗口内结束；formal/04/0 的 Candle 入口验证第 8 个实际技能动作后交回、H 从新状态真实继续。总计最多 100 环境动作，含重放；模型和 Worker 计入新账本。验收检查计数、状态和预算连续、停止原因，不按获胜情况选择窗口。

## 采样与配对

seed 为 ROUTE_D5_TAKEOVER_SCOPE_V1。复用曝光排除工具，刷新所有历史学习／开发／评价／预留任务组，明确排除 D4 全部 12 组和原封存 60 局。仅使用剩余 train/pick_two_obj_and_place 的元数据及 grammar.task 原始公开目标分层，不运行候选或读取专家路线筛题。取样前剩余 404 游戏、179 任务组，put_two 211、other 193。

按目标原文 startswith('put two ') 分层，各取 12 不同组；put_two 层先取，每次按已选场景数、已选物品类别数、SHA256(canonical [seed, game_sha256]) 的升序确定；另一层继续排除已选组，最终交替排列两层。原文不修改，不补样本，不换题。仅主张本地记录中的新游戏／任务组，非官方 test split，允许已见场景（本轮 20/24 场景已见）。全部均值只代表本轮 12＋12 设计分布。

每游戏只运行一次真实 H 公共前缀；24 独立游戏、24 配对区组、最多 72 逻辑策略结果。三组六种排列各使用四次，见冻结清单。入口前终止／耗尽保留整局分母，三组引用同一真实终态。到达入口则各自 reset/replay，核验完整逐步公开反馈、当前物理重放与控制签名，剩余预算相同。所有实际重放计实验环境账本，部署成本不重复计。

F8 交回后 H 使用当前真实状态、技能期间全部动作与观察、原完整历史、真实剩余步数及原停止历史，使用既有 H 提示，无专家建议或反思。只有零动作 declined 且完整控制签名与本区组 H 起点一致，才允许原有的 outcome-blind H 后缀引用；不因属于同一游戏而共享。已执行技能动作后始终真实调用 H，绝不拼接入口 H 后缀。F_full 与 F8 截断前逐动作比较输入 hash、返回状态／决策和实际反馈；无法解释的分歧停止。

## 独立预算与停止

本轮新账本，不沿用 D4 余额／授权。硬上限：学习请求 0；24 新游戏／区组，最多 72 逻辑结果；Flash 请求 4000，全部环境动作 5000（含重放与旧夹具），Worker 1600，模型保守预留 $17，运行 3 小时，单请求绝对截止 600 秒。仅访问 DeepSeek 官方 api.deepseek.com，deepseek-flash 非思考、temperature 0、max_tokens 1024，保持 D4 配置。

Flash 逐请求按 wire 字节＋256 输入上界及 1024 输出、统一最高 $1.20/百万 token 预留并按真实 usage 结算；未知 usage／未决请求停止，不自动重发。开始每个区组前须至少剩 200 请求、200 环境动作、58 Worker、$0.08018 最大单请求预留额度和正剩余时间；每次请求仍单独检查所有硬上限。此门槛不保证费用和时间能完成整区组；中途触顶必须留存并标记不完整，不纳入完整配对统计。全部原始开销仍计账。

参考价格按 2026-11-19 [DeepSeek 官方价格](https://api-docs.deepseek.com/quick_start/pricing/)核对：峰时未缓存输入 $0.30、输出 $1.20／百万 token，统一使用此参考价，不冒充供应商真实账单（缓存和非峰时可能更低）。Worker 与环境无可靠美元单价，单独报次数／耗时，不能视作零成本或合成自定义总收益。

普通失败是结果，继续预定样本；源码变化、泄漏、重放不一致、未知请求／状态及其他完整性问题停止。执行开始后不改窗口、样本、评分口径，不追加源码修订、新候选、新窗口或下一轮。

## 预定评分

主要单位为 24 任务组。F8 对 H、F8 对 F_full 各报双方成功、仅 F8 成功、仅对方成功、双方失败；列全退化案例。分别统计窗口内直接完成、主动退出、主动退出后 H 成败、强制交回、强制交回后 H 成败、全局预算耗尽未交回、全局循环／其他失败。按两种句式分层。

全部游戏和两两共同成功子集同时报告模型请求、输入／输出 token、参考费用、部署环境动作、Worker 次数／毫秒、逻辑任务耗时；另报唯一实际调用、重放动作和实验总耗时。每组逻辑成本包含公共前缀一次、真实自身后缀或引用 H 后缀、该组 Worker，不能把前缀免费；逻辑时间为前缀实际执行时间＋后缀首个请求／Worker 至结束的执行时间，额外 reset/replay 排除。实际账本仅计唯一发生调用，不把 72 条逻辑结果当成独立执行样本。

窗口案例逐个检查是否限制了长搜索、是否截断实际 F_full 本来能够完成的动作链，并对照真实 H 接续动作与结果。提前失败的少调用不称效率改善；固定窗口不能改善前八步本身的动作质量。结论只归于冻结 s1＋固定宿主窗口，不声称 8 最优、不声称模型学会主动退出。

## 冻结样本

|序号|层|游戏身份|原始公开目标|分支顺序|
|---|---|---|---|---|
|0|put_two|alf-9759a1bf434bc8a273af|put two alarmclock in desk.|H → F_full → F8|
|1|other|alf-c76a401607c375011a2e|find two keychain and put them in coffeetable.|H → F8 → F_full|
|2|put_two|alf-83cdd08e3ba61ca202f5|put two box in coffeetable.|F_full → H → F8|
|3|other|alf-489f31d4d2e37eb716de|find two cup and put them in countertop.|F_full → F8 → H|
|4|put_two|alf-a421d22ca32165451146|put two lettuce in fridge.|F8 → H → F_full|
|5|other|alf-eb3daaa09b937481ef97|find two candle and put them in shelf.|F8 → F_full → H|
|6|put_two|alf-99e7830d2b716090fb37|put two newspaper in garbagecan.|H → F_full → F8|
|7|other|alf-9447c85c4213eba99f7d|find two cd and put them in garbagecan.|H → F8 → F_full|
|8|put_two|alf-3c45b22e5cfc3e1958a0|put two watch in dresser.|F_full → H → F8|
|9|other|alf-d0bcb0fb8a51c17441b3|find two handtowel and put them in toilet.|F_full → F8 → H|
|10|put_two|alf-033d7639d13307be1a0a|put two book in desk.|F8 → H → F_full|
|11|other|alf-9c5a1c70ab503fa1e9ba|find two creditcard and put them in armchair.|F8 → F_full → H|
|12|put_two|alf-5c2ceda68a5e812240bf|put two potato in fridge.|H → F_full → F8|
|13|other|alf-edb5f2d63526a46b357c|find two spraybottle and put them in countertop.|H → F8 → F_full|
|14|put_two|alf-cc01dd9e9912e28b75fb|put two peppershaker in cabinet.|F_full → H → F8|
|15|other|alf-232eaa3997ed5d7e5dcc|find two tissuebox and put them in drawer.|F_full → F8 → H|
|16|put_two|alf-35ef30eb13490cb7807a|put two saltshaker in cabinet.|F8 → H → F_full|
|17|other|alf-eb9c2e580d559e9d884f|find two soapbottle and put them in toilet.|F8 → F_full → H|
|18|put_two|alf-97cc7f7880ec5728080b|put two bowl in coffeetable.|H → F_full → F8|
|19|other|alf-b2baba8d453a5cbb7985|find two winebottle and put them in cabinet.|H → F8 → F_full|
|20|put_two|alf-8e168fa632507abc2b2b|put two remotecontrol in armchair.|F_full → H → F8|
|21|other|alf-7a557585aea43150518e|find two spatula and put them in drawer.|F_full → F8 → H|
|22|put_two|alf-9015e721fecb1dce5bf0|put two cellphone in shelf.|F8 → H → F_full|
|23|other|alf-e38cdf92ca7a67d0e1d6|find two cloth and put them in shelf.|F8 → F_full → H|
