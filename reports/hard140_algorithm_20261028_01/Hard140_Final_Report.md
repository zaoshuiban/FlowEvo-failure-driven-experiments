# 140道最高难度多类型数学题：真实失败与算子合成实验

## 结论摘要

**140题真实求解完成，但存在账本停止门控执行偏差，标记`COMPLETE_WITH_LEDGER_GATE_DEVIATION`。** 最终118题确认正确、8题确认错误、13题UNVERIFIED、1题截断。7道可信错误来源进入T/F/F-C对照，来源正确分别3/7、3/7、4/7。

FC有表达式解析和首次命中的正例，也有多项式来源退化。排除T的工程拒绝后，T与FC共同可执行的4对中一胜一负；尚无稳定失败学习收益。两条已有完整响应的格式错误被账本保守标为UNKNOWN，未触发全局停止；原始记录、费用预留均保留，无重发。本轮只作为开发探索证据。

详见[机制归因及停止门控审计](Mechanism_and_Ledger_Audit.md)。

## 运行状态

Run `hard140_algorithm_20261028_01`；任务完成记录140/140。Discovery状态：COMPLETE；算法生成状态：COMPLETE；Worker来源评价状态：COMPLETE。总共321次真实模型响应。

## 选题与冻结

采用[EleutherAI/hendrycks_math](https://huggingface.co/datasets/EleutherAI/hendrycks_math)固定revision `21a5633873b6a120296cce3e2df9d5550074f4a3` 的train七个分片。140题均为该数据集最高难度标签Level 5，每类20题。所谓“最高”指数据集等级，不是宣称这些题是全部数学题中最难，也不保证DeepSeek会失败。

按`SHA256(hard140-v1:subject:row)`固定排序，在每类取首20道合格题，并按七类轮转形成完整顺序。排除依赖图像或图示语义不确定的题、超长题、缺少明确参考答案的题，以及与1119条已记录公开题面或本次选题近重复的题。近重复采用数字掩码、空白规范化后的SequenceMatcher≥0.90。上一轮10题与旧P2/Discovery/Design公开题已纳入排除。选题不使用目标模型运行表现。

候选筛查：`{"SELECTED": 140, "VISUAL_REQUIRED_OR_UNCERTAIN": 21, "RECORDED_TEXT_NEAR_DUPLICATE": 7}`。104题官方答案是精确有理数，36题为符号/集合等形式；本轮不因非数值答案排除难题。曝光筛查不是全项目或模型预训练去重的完备证明。不访问Gate/Legacy/Fresh、419题长流或119题确认池。

协议SHA `30eef0837f32e5fb7d41511db38a46734563b05f290b17bebce4896e9b70003e`；Git基准`abf86c669ab5d5a2f8419085b43db6f813c74741`，实际修改源码以逐文件SHA冻结，不能只用Git SHA代替运行代码状态。

## 求解与证据准入

沿用FlowEvo无Gold数学控制器、DeepSeek Flash、concise-v1、temperature=0、每次8192输出Token。每题固定两次调用；第二次是无任何评分反馈的自我复核，不根据首轮隐藏正确性决定是否调用。四路并发仅用于独立任务API传输，不是多Agent角色系统；每任务账本独立、无跨任务信息，四题窗口按冻结顺序派发。未知请求或基础设施问题停止下一窗口，不自动重发。

两次输出锁定后评分：精确可确认的错误为CONFIRMED_WRONG；截断为TRUNCATED；无法确认符号等价/不等价为UNVERIFIED。不将后两者冒充数学失败。若复核输入因原有保守上界无法发送，则该题TASK_NOT_COMPLETED，无自动补发或放宽上限。

首轮分布：`{"CONFIRMED_CORRECT": 119, "UNVERIFIED": 12, "CONFIRMED_WRONG": 8, "TRUNCATED": 1}`。

最终分布：`{"CONFIRMED_CORRECT": 118, "UNVERIFIED": 13, "CONFIRMED_WRONG": 8, "TRUNCATED": 1}`。

至少一次可信数学错误的独立原题：8。同一题两次错误不算两道独立来源。

|类型|完成|首轮正确|首轮错误|最终正确|最终错误|最终未确认|最终截断|有可信错误的题|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|algebra|20/20|17|1|17|1|2|0|1|
|counting_and_probability|20/20|18|1|19|1|0|0|1|
|geometry|20/20|18|1|17|1|2|0|1|
|intermediate_algebra|20/20|16|2|16|2|2|0|2|
|number_theory|20/20|16|3|16|3|0|1|3|
|prealgebra|20/20|18|0|18|0|2|0|0|
|precalculus|20/20|16|0|15|0|5|0|0|

## 有界T/F/F-C实验

事前规则：每类型选冻结顺序最早的两个具有可信错误的任务，最多14个来源，不补齐不存在的失败类型、不根据生成结果换源。本轮入选7个来源。每源只提供最早一次可信错误，后续已正确的输出不提供给生成器。

T只看题面；F额外看到该真实错误轨迹及二值false；F-C在相同证据上要求分开陈述错误操作与自行提出的替代操作。三组共享DeepSeek型号、temperature=0.2、8192输出上限、每源两调用（分析/源码）、零修订和相同工程检查。沿用上一轮冻结生成协议`hard10-source-synthesis-v1`，没有人工数学算法提示。

模型自主提出参数schema及来源参数映射，生成`solve(parameters)`。因此来源分数是算法与参数映射的联合结果，不是纯算法正确性或跨题泛化。源码及分析全部冻结后，在现有Linux Worker中实际执行，结果锁定后才与私有官方答案比较。没有用Gold反复修订，没有自动获得Experimental权限。

|条件|请求|生成尝试|静态通过|来源正确|来源错误|其他/未执行|全部Token|API估算|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|solver|280|0|0|0|0|0|406,054|$0.154069|
|T|13|7|4|3|1|3|23,818|$0.008874|
|F|14|7|7|3|2|2|54,890|$0.013868|
|FC|14|7|6|4|1|2|61,573|$0.017965|

|来源任务|条件|生成|执行|私有评分|
|---|---|---|---|---|
|hard140-math-train-geometry-551|T|DELIVERY_REJECTED|NOT_EXECUTED|EXECUTION_ERROR|
|hard140-math-train-geometry-551|F|STATIC_VALID_SHADOW|RUNTIME_ERROR|EXECUTION_ERROR|
|hard140-math-train-geometry-551|FC|STATIC_VALID_SHADOW|RUNTIME_ERROR|EXECUTION_ERROR|
|hard140-math-train-algebra-330|F|STATIC_VALID_SHADOW|OK|CONFIRMED_WRONG|
|hard140-math-train-algebra-330|FC|STATIC_VALID_SHADOW|OK|CONFIRMED_CORRECT|
|hard140-math-train-algebra-330|T|STATIC_VALID_SHADOW|OK|CONFIRMED_WRONG|
|hard140-math-train-intermediate_algebra-426|FC|STATIC_REJECTED|NOT_EXECUTED|EXECUTION_ERROR|
|hard140-math-train-intermediate_algebra-426|T|DELIVERY_REJECTED|NOT_EXECUTED|EXECUTION_ERROR|
|hard140-math-train-intermediate_algebra-426|F|STATIC_VALID_SHADOW|RUNTIME_ERROR|EXECUTION_ERROR|
|hard140-math-train-number_theory-420|T|STATIC_VALID_SHADOW|OK|CONFIRMED_CORRECT|
|hard140-math-train-number_theory-420|F|STATIC_VALID_SHADOW|OK|CONFIRMED_CORRECT|
|hard140-math-train-number_theory-420|FC|STATIC_VALID_SHADOW|OK|CONFIRMED_CORRECT|
|hard140-math-train-number_theory-550|F|STATIC_VALID_SHADOW|OK|CONFIRMED_CORRECT|
|hard140-math-train-number_theory-550|FC|STATIC_VALID_SHADOW|OK|CONFIRMED_CORRECT|
|hard140-math-train-number_theory-550|T|STATIC_VALID_SHADOW|OK|CONFIRMED_CORRECT|
|hard140-math-train-counting_and_probability-351|FC|STATIC_VALID_SHADOW|OK|CONFIRMED_CORRECT|
|hard140-math-train-counting_and_probability-351|T|STATIC_REJECTED|NOT_EXECUTED|EXECUTION_ERROR|
|hard140-math-train-counting_and_probability-351|F|STATIC_VALID_SHADOW|OK|CONFIRMED_WRONG|
|hard140-math-train-intermediate_algebra-289|T|STATIC_VALID_SHADOW|OK|CONFIRMED_CORRECT|
|hard140-math-train-intermediate_algebra-289|F|STATIC_VALID_SHADOW|OK|CONFIRMED_CORRECT|
|hard140-math-train-intermediate_algebra-289|FC|STATIC_VALID_SHADOW|OK|CONFIRMED_WRONG|

单次配对、每源一份候选；不按最佳版本挑选。未交付、静态拒绝、运行异常和数学错误分别记录。即使观察到F独有来源成功，也不能宣称失败经验提高未见任务泛化；必须审查是否真正参数化、输入映射是否泄漏计算结果、是否仅解决来源题。

## 成本与审计

真实模型Token 546,335，按实际usage和缓存/时段估算费用$0.194775。账本费用预留上界合计$5.005267，不是实际账单。独立硬上限分配：140×$0.15求解 + 最多42×$0.25生成 = $31.50；上限不等于预计支出，也不要求花满。

价格来自[DeepSeek官方价目](https://api-docs.deepseek.com/quick_start/pricing/)，快照保存在Run：Flash峰时缓存命中/未命中/输出$0.006/$0.30/$1.20每百万Token，非峰时减半。逐请求原始usage和估算见`request_costs.json`，包括所有失败生成成本。Worker记录墙钟2.458秒，本地计算未完全货币化。

响应ID去重321/321，UNKNOWN 2。完成任务的280条实际wire逐条与题面+上次未验证输出重建相等，未提供Gold/solution/中间评分。旧10题与旧算法实验哈希保持不变。8项零API验收通过，包括真实Worker；Mock仅证明工程能力。

## 研究边界

这是最高标签开发任务上的失败机会与来源合成实验，不是独立Gate、不证明长期收益。UNVERIFIED降低可确认覆盖，不能算错误或正确；官方最高难度仍可能对模型较易。三组输入长度不同、未设置等Token中性对照，且单次生成存在随机波动。冻结任务及代码不因中间成绩而改变。未自动扩大到其他数据集或修订当前契约路线。

[逐题清单与结果](Task_List_and_Outcomes.md)；机器数据`metrics.json`、`paired_results.json`、`request_costs.json`、`wire_projection_audit.json`。所有原始模型响应、源码、账本及Worker结果在`runs/hard140_algorithm_20261028_01`。
