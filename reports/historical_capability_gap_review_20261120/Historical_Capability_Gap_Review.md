# 历史真实能力缺口审查

**1. 哪些是已有技能没用好，哪些可能需要新增能力？** HumanEval/39、括号化不同值计数、无重复数字的素数枚举，以及真实 MATH Level 5 中的表达式求值、数字和枚举、考试得分可辨识性、有限步首次命中、多项式整数系数比例，均已有至少来源范围内验证通过的实现。不能再把这些来源错误当成“没有算法”。几何约束分支与根式表示仍有真实未解决来源，列为 `NEW_CAPABILITY_CANDIDATE`；这是值得审查的候选，不是已证明的共同根因或已具备跨任务学习资格。

**2. MATH 括号化已有程序能否解决相应任务？** 可以解决本轮固定的 5 个真实错误及 8 个已曝光计数开发题；对另外 4 个要求极值或括号形式数的任务仍错误接受。核心计数能力足够，宽泛文本入口不可靠。5 条错误均来自同一生成机制并追溯到同一个历史来源索引，不能当作 5 个独立原题。

**3. 是否已有一个可以启动强教师跨任务获取的新操作？** 还没有完整合格项。本次找到 2 个可信、尚无成功恢复的来源级候选，但没有为其中任一个确认第二独立原题和参数化正确性验证。`Next_Qualified_Learning_Items.json` 的 `items` 为空，另外保留这两个候选与具体缺项；不把“待核实”隐藏成没有发现真实失败，也不把它们提前当作可运行实验。

**4. 哪个领域最快，还缺什么？** 数学的现成函数 Worker、参数化生成、编译和支持接口最接近可用。若优先探索仍未解决的新操作，先限定根式表示候选的精确输出与恒等式证据，再取得第二原题；目前不能冻结付费实验。若允许先做真实恢复的能力沉淀，有限步首次命中概率已有正确 FC 源码，是更短的路线，但它不是新算法补课。两条路线都必须把中间计算结果返回原 Actor 继续求解，不能直接锁为整题答案。

本轮完成阶段 A，新增模型请求 **0**、Teacher **0**。只增加一个薄审查脚本；未修改核心算法、求解器、编译器或历史库。新增 17 次无网络 Docker 检查，Worker 账本合计 **4.626 秒**，另有 17 次宿主独立参考重算；未将本地计算当作零成本，也未虚报其精确 CPU 费用。固定检查完成后即收住。

**证据范围与资格口径**

本次以已有 6 类缺口清单和上一轮覆盖清单为起点，核对 P1/P2/P3 括号化材料、后续 V3.1–V3.4 已曝光报告、已结案 Hard140 的 8 个最终错误及 21 份历史候选结果，以及已曝光 ALFWorld 与代码撤销材料。未新增随机抽样，未读取或运行原 P0 Gate/Legacy/Fresh、未曝光正式评价题、旧 HumanEval 保留题或 ALFWorld 封存 60 局。后续语义试验只读已结案报告，没有重跑其旧确认题。

清单有 16 行机制/失败类别，状态为：已有实现足够 8、能力状态未知 5、新能力候选 2、无效或非算法 1。这里的“足够”严格限定于已验证来源和输入条件；不等于已 active 准入、任意参数正确或 Actor 已会自主使用。同源参数、重复试验和 T/F/FC 三份程序均不增加独立来源数。机制名称是对证据的组织假设，不是因果证明。

| 能力机制 | 真实证据与已有覆盖 | 本次判断 | 后续动作 |
|---|---|---|---|
| 括号化不同结果计数 | 5 份真实错误；旧 43cda… 本次 5/5＋开发正例 8/8 | EXISTING_CAPABILITY_SUFFICIENT（计数域） | 复用旧核心，不再生成同类算法 |
| 括号化目标量与适用前提 | 4 个真实误接受；旧语义修订有局部正例但不稳定 | CAPABILITY_STATUS_UNKNOWN | 保留已知缺陷；不继续同族关键词/提示调参 |
| 无重复数字素数枚举 | 旧 P3 来源 7/7，允许重复时误触发 | EXISTING_CAPABILITY_SUFFICIENT（来源域） | 先限定已有实现适用范围 |
| 固定括号表达式求值 | Hard140 algebra-330；FC 正确，T/F 错 | EXISTING_CAPABILITY_SUFFICIENT（来源） | 复用已有解析程序 |
| 十进制数字和与二进制位数计数 | number_theory-420；T/F/FC 均正确 | EXISTING_CAPABILITY_SUFFICIENT（来源） | 不再请求教师求同题 |
| 得分可辨识性枚举 | number_theory-550；T/F/FC 均正确 | EXISTING_CAPABILITY_SUFFICIENT（来源） | 核查独立支持后复用 |
| 有限步首次命中 | counting_and_probability-351；FC 正确，F 错 | EXISTING_CAPABILITY_SUFFICIENT（来源） | 先复用恢复，整理返回量和边界 |
| 整数系数多项式比例 | intermediate_algebra-289；T/F 正确、FC 错 | EXISTING_CAPABILITY_SUFFICIENT（来源） | 保留既有正确实现和 FC 反例 |
| 受约束圆交点分支 | geometry-551 原生最终错；F/FC 未找到解/不收敛 | NEW_CAPABILITY_CANDIDATE | 明确分支契约、独立验证和第二来源 |
| 三次根式表示与精确恒等式 | intermediate_algebra-426 原生最终错；F 有界搜索未找到，FC/T 工程拒绝 | NEW_CAPABILITY_CANDIDATE | 优先限定精确表示/证据接口；第二来源缺失 |
| 台阶安全距离下的吞吐极值 | number_theory-618 最终数字不匹配，未进入旧生成清单 | CAPABILITY_STATUS_UNKNOWN | 先核验取整、可达性和计数建模，不泛化成优化器缺口 |
| HumanEval/39 | 宿主复用曾成功，G/R 普通 repair 成功，未自主调用 | EXISTING_CAPABILITY_SUFFICIENT | 分支已关闭，不追加实验 |
| TACO/LCB 输入消费 | 指定 TACO 非法输入回执已撤销；0875 只有人工修补 | INVALID_OR_NON_ALGORITHMIC | 不复活旧证据，不重发旧请求 |
| ALFWorld 搜索覆盖 | 3 个真实超时游戏；存在后验研究者分支，D4 搜索有残余成本 | CAPABILITY_STATUS_UNKNOWN | 原始公开状态与旧程序覆盖需绑定；后验路线不得当模型恢复 |
| ALFWorld 持物前提 | 1 个真实失败；旧程序含 inventory 行为，未做同状态验证 | CAPABILITY_STATUS_UNKNOWN | 优先复用覆盖核查 |
| ALFWorld 已完成实例账本 | 原失败真实；D4 有 placed 账本、D5 有整局复用 | CAPABILITY_STATUS_UNKNOWN（确切旧状态） | 不据此声称缺少账本算法 |

**Hard140 真实错误与旧恢复**

8 个来源来自固定版本 `21a5633873b6a120296cce3e2df9d5550074f4a3` 的 hendrycks_math train、Level 5，均已在 2026-10-28 完成两次原生响应和答案锁定。本次逐题核对锁定哈希、实际末次响应、题面哈希、原始评分回执和精确数值不匹配。未将输出截断、符号未确认或源码交付异常当作数学错误。

5 个来源已有至少一份成功程序；2 个来源曾生成但没有验证成功的程序；另 1 个因旧的每类型最多两个来源规则未被选择生成。数据集 train 行号是稳定记录身份，原竞赛谱系仍未全部确认，不能把行号直接当作独立性证明。对已曝光 140 题只做有限题面关联核查：圆/交点相关 8 题，三次根相关 2 题，概率/随机相关 12 题，台阶距离相关 1 题。这些词汇命中没有自动成为支持题；没有一个被核定为当前候选的第二独立来源。

旧 Hard140 存在 `COMPLETE_WITH_LEDGER_GATE_DEVIATION`：两条完整响应的格式错误曾被账本保守记为 UNKNOWN，未按原门控停止。该偏差保留，使旧结果只用于开发探索；本轮不修旧账、不重发请求。源码静态拒绝与候选实际数学搜索失败分别保存，不能把 FC 不允许导入 decimal 或 T 交付错误冒充数学反例。

几何候选的输入可以明确到边长、距离及点次序，但旧程序输出仍是整题的 `a+b+c+d`；“完整实分支与约束证据”尚未得到验证。根式候选输入含 p、q、multiplier、bound、tolerance，旧 F 在所给边界找不到结果。提高搜索上限或放宽容差并不自动产生正确算法，本轮未这样修补。第二个命中 cube-root 词汇的题是反比例关系，不能充当根式分解的独立支持。

**交互与代码材料的限制**

ALFWorld 原公开动作与回执是有效失败记录；`Supporting_Evidence_v2.private.json` 明确将研究者探路标为 `HOST_RETROSPECTIVE_REPAIR_ONLY`，`model_training_allowed_paths=[]`。有些快捷恢复使用此前探路才发现的位置，不能投影为原分叉状态已知信息或 Teacher 成功轨迹。D1–D5 冻结程序与真实模型恢复仍单独保存；D4 Kettle 的退化及 D5 固定接管窗口的代价都没有消失，但尚不能由此直接得到一个新的、已限定输入输出且有独立支持的局部操作。

TACO 0003、144、1454 只保留原指定证据的撤销；不推断这些题永远没有任何算法错误。当前完成可信性审查的代码材料没有留下可用的未解决项。未读取新的 LCB 题来补足清单。

**最小接线结论**

已核对 `NoGoldMathController.solve`：`library.run` 最后返回 APPLIED 时，直接将 answer 作为 output，跳过后续模型求解，最终记录 `selection=first_applied_operator`。因此现有这条路径确实不能直接拿来声称“Actor 调用中间工具后继续完成任务”。

在来源资格满足后，只需增加明确的可调用操作路径：沿用当前 Actor 的求解请求和预算，给出正常可见接口，由 Actor 选择函数与参数；通过既有冻结 Worker 执行并记录 SHA、参数和返回；将公开返回值交回同一个 Actor，再锁定完整答案。G 保留原有正确技能、普通推理和修订预算，不能人为削弱。已有 `SplitRunner` 的 match/solve、`PrimitiveCompiler`、`PrimitiveStore.observe_support` 与 `AcquisitionScheduler.support_frozen` 可复用，不另造数学编译器。顶层 solve 或计数函数同样可以是可复用操作，不以是否存在嵌套 helper 决定资格。

本轮没有合格的来源—独立支持组合，因此没有提前实现这段付费执行适配，也没有生成貌似可运行的 `Next_Experiment_Protocol.md`。`Next_Experiment_Readiness.json` 保存具体缺项，Actor/Teacher 预算为 null，API 开关关闭；旧余额不继承。需要来源级精确验证与第二独立题身份通过后，才能冻结开发清单、真实模型配置及费用。

未来保留 G、G＋F、G＋U 对照约束：F/U 相同教师、编译、验证与预算；U 从同一训练池按冻结普通抽样规则选题，允许选到失败题。本轮未运行三组比较，也没有将机制排序声称为创新算法。

审查入口与证据：

- [机器可读机制清单](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/historical_capability_gap_review_20261120/Historical_Capability_Gap_Review.json)
- [8 个真实 MATH 来源与全部旧候选回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/historical_capability_gap_review_20261120/Math_Level5_Source_Review.json)
- [括号化验证报告](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/historical_capability_gap_review_20261120/Math_Operator_Coverage_Result.md)
- [合格学习项与未合格候选](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/historical_capability_gap_review_20261120/Next_Qualified_Learning_Items.json)
- [后续运行缺项](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/historical_capability_gap_review_20261120/Next_Experiment_Readiness.json)
- [本轮薄审查脚本](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/review_historical_capability_gaps.py)
