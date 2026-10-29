# 更困难10题：真实失败收集与T/F/F-C算法合成实验

## 本轮结论

`DISCOVERY_COMPLETE / NO_CONFIRMED_MATH_FAILURE / SYNTHESIS_NOT_TRIGGERED`。10题最终全部正确，首轮9题正确、1题截断，无可信数学错误。完成了20次真实求解，但没有运行T/F/F-C生成比较。结果不支持也不反对失败信息的独立价值，只表明本批官方Level 5题没有提供可用失败。没有为了继续实验而换题、降低求解预算或将截断算作数学错误。

## 研究定位

本轮按照用户要求选择新的10道较难题。难度依据为MATH数据集官方Level 5标签，并不预先保证目标模型会失败。与此前两种参数化生成题不同，本轮是数论、计数与概率各5道原始题。实验属于开发性研究，不是对模型预训练未见性的证明。

选择规则在调用前冻结：按`SHA256(hard10-v1:subject:row)`排序，每类取首5道Level 5、无需图像、官方答案可精确有理数评分且不与已检查公开记录近重复的题；两类交替执行。没有按模型表现替换任务。来源为[EleutherAI/hendrycks_math](https://huggingface.co/datasets/EleutherAI/hendrycks_math)，revision `21a5633873b6a120296cce3e2df9d5550074f4a3`，原始Parquet完整哈希见协议。曝光筛查覆盖1049条既有公开数学题文本；并非全项目语义近重复的完备证明。419题/119题确认池及原Gate未读取。

Run `hard10_algorithm_20261028_01`，协议SHA `e510bf13d9847b7d106ddefdbff800b65a16c887b60d04da561c14f714107c90`。不复用旧账本，最多80请求、$12保守硬上限，未用额度不继续花费。模型仍为直连DeepSeek `deepseek-flash`，不是GPT。

## 冻结流程

1. 10题各固定两次无Gold求解，8192输出Token上限、temperature=0；第二次仅自我复核，无中间评分反馈。
2. 两次输出均锁定后由私有评分器评分。每题最早的`CONFIRMED_WRONG`可进入生成；截断、不确定和正确输出不能冒充失败。首轮错但最终正确者也可贡献一条真实初始错误，但不向生成器泄漏后续正确答案。
3. 每个合格来源运行T/F/F-C，每条件一次分析和一次源码生成，上限相同，无修订。T只看题面；F增加已确认错误轨迹及`correct=false`；F-C再要求分离错误操作和自拟替代操作。
4. 不同题不再共享上轮专用参数接口。本轮由模型提出`parameter_schema`和`source_parameters`，再实现`solve(parameters)`。这一变化公开记录；来源分数同时涉及算法和参数映射，不是纯算法的独立泛化成绩。
5. 全部源码冻结后真实Linux Worker执行；所有返回值锁定后才与私有官方答案比较。没有把评价结果反馈生成器，没有语义路由、Gate或自动发布。

## 十题结果

首轮分布：`{"CONFIRMED_CORRECT": 9, "TRUNCATED": 1}`。最终分布：`{"CONFIRMED_CORRECT": 10}`。具有至少一次可信错误的来源题：0/10。

|序号|题目ID|首轮|最终|
|---|---|---|---|
|1|hard10-math-train-number_theory-669|CONFIRMED_CORRECT|CONFIRMED_CORRECT|
|2|hard10-math-train-counting_and_probability-767|CONFIRMED_CORRECT|CONFIRMED_CORRECT|
|3|hard10-math-train-number_theory-282|CONFIRMED_CORRECT|CONFIRMED_CORRECT|
|4|hard10-math-train-counting_and_probability-693|CONFIRMED_CORRECT|CONFIRMED_CORRECT|
|5|hard10-math-train-number_theory-579|CONFIRMED_CORRECT|CONFIRMED_CORRECT|
|6|hard10-math-train-counting_and_probability-433|TRUNCATED|CONFIRMED_CORRECT|
|7|hard10-math-train-number_theory-791|CONFIRMED_CORRECT|CONFIRMED_CORRECT|
|8|hard10-math-train-counting_and_probability-439|CONFIRMED_CORRECT|CONFIRMED_CORRECT|
|9|hard10-math-train-number_theory-665|CONFIRMED_CORRECT|CONFIRMED_CORRECT|
|10|hard10-math-train-counting_and_probability-360|CONFIRMED_CORRECT|CONFIRMED_CORRECT|

两次回答属于同一道题，不能当作两个独立来源。Level 5只是先验难度元数据，不能把0失败解释为失败学习能力成功或失败。

## 生成及来源执行

|条件|真实请求|生成尝试|静态通过|来源正确|来源错误|其他/未执行|Token|API估算|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|solver|20|0|0|0|0|0|44,755|$0.016696|
|T|0|0|0|0|0|0|0|$0.000000|
|F|0|0|0|0|0|0|0|$0.000000|
|FC|0|0|0|0|0|0|0|$0.000000|

没有可信错误，按冻结协议未运行生成对照；不以正确或截断输出补足失败样本。

|来源|条件|生成状态|Worker状态|私有评分|
|---|---|---|---|---|


这里只验证来源，不声称不同原题复用、参数化泛化或长期工作流收益。即使F有独有来源正确，也只能视为一次开发观察；模型生成自己的参数映射、单次采样、上下文长度和Token消耗的差异均需要保留。

## 工程、成本与完整性

8项零API测试通过，包含私有字段拒绝、正确样本拒绝进入失败、截断/不确定分离、T无失败证据、无授权拒绝及真实Worker执行。准备阶段系统临时目录不在Docker挂载范围，Mock执行曾失败；改在项目目录运行Mock后通过，未放宽Worker权限、未发送模型请求重试。

真实响应20次、不同响应ID 20个，UNKNOWN 0个。Token总量44,755；报价估算$0.016696，预留上界累计$0.330338，均非供应商实际账单。逐请求usage、时间、缓存命中和报价系数见`request_costs.json`。依据[冻结时核对的DeepSeek官方价格](https://api-docs.deepseek.com/quick_start/pricing/)，Flash峰时缓存命中/未命中/输出分别$0.006/$0.30/$1.20每百万Token，非峰时折半；没有推理Token重复计费。

Worker执行0次，记录墙钟0.000秒；本地准备和容器总成本未完整货币化。所有执行仅收到参数与冻结源码，不包含标准答案。前一实验文件哈希保持不变，当前冻结源码和数据校验通过。20条真实发送wire逐一与“题面＋可选前次未验证输出”的固定消息构造完全一致；没有二值评分或私有评分字段进入当前题的自我复核。生成使用现有BoundedCompiler、PersistentBudget和Worker，未改旧生成器/路由/代际系统。

## 任务清单


### 1. hard10-math-train-number_theory-669

Let $S$ denote the sum of all of the three digit positive integers with three distinct digits. Compute the remainder when $S$ is divided by $1000$.


### 2. hard10-math-train-counting_and_probability-767

The integers $r$ and $k$ are randomly selected, where $-3 < r < 6$ and $1 < k < 8$. What is the probability that the division $r \div k$ is an integer value? Express your answer as a common fraction.

### 3. hard10-math-train-number_theory-282

What is the least positive integer which when divided by 5 gives a remainder of 4, when divided by 6 gives a remainder of 5, when divided by 7 gives a remainder of 6, when divided by 8 gives a remainder of 7, when divided by 9 gives a remainder of 8, and when divided by 10 gives a remainder of 9?

### 4. hard10-math-train-counting_and_probability-693

The Lakers are playing the Celtics in the NBA finals. To win the NBA finals, a team must win 4 games before the other team does. If the Celtics win each game with probability $\dfrac{2}{3}$ and there are no ties, what is the probability that the Lakers will win the NBA finals but that the contest will need all seven games to be decided? Express your answer as a fraction.

### 5. hard10-math-train-number_theory-579

The harmonic mean of two positive integers is the reciprocal of the arithmetic mean of their reciprocals. For how many ordered pairs of positive integers $(x,y)$ with $x<y$ is the harmonic mean of $x$ and $y$ equal to $6^{20}$?


### 6. hard10-math-train-counting_and_probability-433

How many triangles with positive area are there whose vertices are points in the $xy$-plane whose coordinates are integers $(x,y)$ satisfying $1\le x\le 4$ and $1\le y\le 4$?
$\text{(A) } 496\quad \text{(B) } 500\quad \text{(C) } 512\quad \text{(D) } 516\quad \text{(E) } 560$


### 7. hard10-math-train-number_theory-791

A group of 25 friends were discussing a large positive integer. ``It can be divided by 1,'' said the first friend. ``It can be divided by 2,'' said the second friend. ``And by 3,'' said the third friend. ``And by 4,'' added the fourth friend. This continued until everyone had made such a comment. If exactly two friends were incorrect, and those two friends said consecutive numbers, what was the least possible integer they were discussing?

### 8. hard10-math-train-counting_and_probability-439

At the end of a professional bowling tournament, the top 5 bowlers have a playoff. First #5 bowls #4. The loser receives $5$th prize and the winner bowls #3 in another game. The loser of this game receives $4$th prize and the winner bowls #2. The loser of this game receives $3$rd prize and the winner bowls #1. The winner of this game gets 1st prize and the loser gets 2nd prize. In how many orders can bowlers #1 through #5 receive the prizes?
$\textbf{(A)}\ 10\qquad \textbf{(B)}\ 16\qquad \textbf{(C)}\ 24\qquad \textbf{(D)}\ 120\qquad \textbf{(E)}\ \text{none of these}$


### 9. hard10-math-train-number_theory-665

Let $d_1 = a^2 + 2^a + a \cdot 2^{(a+1)/2}$ and $d_2 = a^2 + 2^a - a \cdot 2^{(a+1)/2}$. If $1 \le a \le 251$, how many integral values of $a$ are there such that $d_1 \cdot d_2$ is a multiple of $5$?


### 10. hard10-math-train-counting_and_probability-360

Forty teams play a tournament in which every team plays every other team exactly once. No ties occur, and each team has a $50 \%$ chance of winning any game it plays. The probability that no two teams win the same number of games is $\frac mn,$ where $m$ and $n$ are relatively prime positive integers. Find $\log_2 n.$

