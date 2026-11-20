# MATH 括号化已有程序覆盖核查

结论：冻结旧程序 `43cda71416fe598643a93400f493c22ad510b0e5232a44d5927cbe2d9ebe43f8` 已能解决本轮的全部 5 个真实来源错误和 8 个已曝光计数正例。它的计算目标是“不同可达结果的数量”；不是返回结果集合、目标值可达性、最小/最大值，也不是括号形式总数。文本入口未做可靠目标量判断，4 个其他目标任务全部错误接受。只将计数域标为 `EXISTING_CAPABILITY_SUFFICIENT`，不激活整个程序。

新增模型 0；新增 Docker 作业 **17**，账本 **4.626 秒**。没有生成新问题、替换候选、修订源码、扩展参数或在结果出来后追加检查。检查清单与脚本已先冻结，SHA 为 `6ef16ac7fa3c9f407ea115a3fd40131baa8904db2c9d189e1ac61d033df8bc98`。旧坏程序 904210… 的结果直接核对历史 P3 回执，没有再执行一次来凑证据。

| 固定材料 | 旧 43cda… 实际结果 | 解释 |
|---|---:|---|
| 5 个 P1 真实最终错误 | 5/5 PASS | 都可由现有计数程序处理 |
| 8 个已曝光 P3 计数开发题 | 8/8 PASS | 不同参数成功，不等于独立原题泛化 |
| 1 个最小值题、1 个最大值题、2 个括号形式数题 | 4/4 WRONG_TARGET_ACCEPTED | 合法任务，但不属于计数操作；程序没有拒绝 |
| 原 904210… 引用的 2 个错误来源 | 历史 P3 0/2 | 错误前缀折叠保留，不手修后冒充模型恢复 |

**五份失败的谱系和实际答案**

下表“原答案”是 Actor 当时的错误输出，不是私有参考答案。逐份完整题面、源码/回执引用和哈希保存在 Parenthesization_Sources.json；原最终文本保持原样。

| 任务 ID | 原 Actor 最终答案 | 原评分 | 对应 P2 候选来源 | 本次旧 43cda… |
|---|---:|---|---|---|
| math-4220e51a86ed1e06842cd093 | 26 | CONFIRMED_WRONG | 区间集合候选 3 | PASS |
| math-3ea8382e636948f1ab643366 | 116 | CONFIRMED_WRONG | 区间集合候选 3 | PASS |
| math-89dd90943b2f5cb78d64a3e8 | 114 | CONFIRMED_WRONG | 区间集合候选 3 | PASS |
| math-7ab26853dc601349835bf1c2 | 9 | CONFIRMED_WRONG | 前缀折叠候选 2 | PASS |
| math-71853e3dff2f1732bc5b1669 | 4 | CONFIRMED_WRONG | 前缀折叠候选 2 | PASS |

这五题的原始 metadata 均为 `origin=generated_exact_oracle`、`generator_version=baseline_headroom_mechanisms_v2_2`、`source_failure_indices=[7]`。它们是同一历史机制/来源索引的参数化变体；参数哈希不同不意味着五个独立原题。原竞赛来源尚未解析，不把旧标签 Level 5 误称为本轮五个自然竞赛题。

五题都进入过 P2 的全 12 条失败归纳；候选 3 的生成引用子集为前三题，候选 2 引用后两题。P3 对各候选原来源做了事后私有评分；本次让候选 3 覆盖后两题，也不能称为未见测试，因为上游归纳已看过。原 P0 Gate/Legacy/Fresh 未用于这条生成链的本次验证；后续已曝光 V3 语义试验另行记录，不能把其确认材料再次当未见。

**实际源码与职责**

候选 3 的原始响应 code 字符串、归档源码、Worker 执行 SHA 完全一致，来自历史 GPT-5.4（GPT_VIA_OPENROUTER）响应。当前入口为 `math_operator(context)`：读取公开 problem，提取最长符合简单正整数 `+ - *` 语法的表达式，调用顶层 `_count_distinct_values(nums, ops)`，返回 `{'status':'APPLIED','answer':字符串}`。原始源码只读保存，没有提取并重写核心函数。

计数函数维护每个区间的精确整数结果集合，遍历合法分割点和左右结果的笛卡尔积，再将全区间结果去重计数。工作量取决于所有区间结果集的乘积和，不能只声称 O(n³)；空间也随区间结果集增长。它没有依赖某一个 task_id 或固定答案表。

顶层 helper 职责明确且有参数，具备复用结构；当前验证实际经过的是完整冻结模块的 math_operator 入口。它还不是两来源准入的 active primitive，未证明 Actor 已能自主选择它。模块不对任意空输入、负数文本、除法、固定括号约束或长表达式提供已验证承诺。本次检查使用已有合法正整数题面，支持域外风险仅作源码观察，不伪称执行反例。

候选 2 SHA 为 `90421062837425d60693ba5c8325c1ff5dec35ca13a63805366a24e97dbd9098`，在计算前压缩开头乘法或抵消项，删除跨边界括号结构。其历史来源与开发错误都真实保留；相邻已有候选 3 可以解决两份来源，所以没有必要再向 Teacher 请求同一个计数算法。

**评分与拒绝边界**

复用 MathOperatorRunner、FrozenLinuxBackend 和既有 candidate_worker。Worker 只得到冻结源码与公开 problem，保持无网络、只读、非 root、1 CPU、256 MiB、32 PID、每次 2 秒。全部 17 个输出先锁定，再在宿主独立阶段调用归档参考 `_parenthesized_values`（精确 Fraction），按题目目标分别算数量、极值或形式数，并与当年参考核对；17 份均一致。

参考实现独立于模型生成候选，来源和 SHA 单独封存；这不等于全域形式化证明。参考结果集合、期望值、参数化评分记录保存于本轮 private/reference_receipts.json；公开投影只保留合法性、二元结论和回执引用。未进入教师、编译、技能卡或检索材料。原 P2 的 `source_gold_scoring=false` 保持原样，P3 与本轮诊断不被回填成当年已观察到的训练反馈。

历史 P3 曾检查该程序全部 48 个 Design：8 正确、4 错误接受、36 拒绝；本轮没有重跑那 36 个其他域题。当前 4 个复现反例都是明确的目标量错误，足以否定“看到括号相关词就可直接应用”的宽入口。没有继续调整规则或开展语义契约生成。

核对了 **2,885 个历史文件/当前核心源码文件哈希不变**。两份数学候选、旧 P2/P3、Hard140、HumanEval/39 自主复用封存材料与核心代码均保持原样。既有程序足够处理该批计数错误，但没有独立原题支持，因此结束本机制的新算法获取准备，转向其他真实候选的来源审查。

复核文件：

- [17 项逐题结果](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/historical_capability_gap_review_20261120/Math_Operator_Coverage_Result.json)
- [五份来源审计](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/historical_capability_gap_review_20261120/Parenthesization_Sources.json)
- [原始模型响应与源码绑定](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/historical_capability_gap_review_20261120/Parenthesization_Candidate_Provenance.json)
- [预先冻结清单](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/historical_capability_gap_review_20261120/freeze.json)
- [执行账本](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/historical_capability_gap_review_20261120/budget.jsonl)

已执行的离线阶段命令（留档；原目录已经消费，不重复执行）：

```sh
/Users/majiatong/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python scripts/review_historical_capability_gaps.py prepare
PYTHONHASHSEED=0 /Users/majiatong/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python scripts/review_historical_capability_gaps.py execute
/Users/majiatong/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python scripts/review_historical_capability_gaps.py score
```
