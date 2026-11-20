# 累积式数学失败学习：六项实现与零API验收

日期：2026-11-03。状态：工程实现及Mock验收；真实累积机制学习效果未验证。未调用付费模型，未修改200题旧Run或原窗口式入口。

## 六项实现

|设计|实现|边界|
|---|---|---|
|事实与推测分离|原始题面/完整输出/轨迹/明确错误答案/二值反馈/谱系/哈希存raw；模型描述存views；假设和关联另存clusters|所有推测均UNVERIFIED，模型无权自证或授权|
|候选机制簇|词汇检索仅作候选召回并保留旧簇探索位；模型基于题面、过程、现象和纠错方向决定多重关联或未知；支持SUPPORT/POSSIBLE/COUNTEREXAMPLE/UNRELATED|不是按学科自动判定共同根因；语义关联能力尚无真实实验|
|新信息触发|簇版本、证据ID、接口版本组成作业键；新原题、反例、模型声明并引用的新信息参与确定性优先级；记录未选原因|模型判断“新信息”仍是待验证推测；不设三题硬门槛；仅改文字、重复旧证据不能再生成|
|有界证据包|优先反例、原题多样性、早期代表；全轨迹可追溯；前后片段保留最终答案；记录省略哈希；来源诊断单独保存|反例放不下则EVIDENCE_REPRESENTATION_LIMIT；最终wire仍由BoundedCompiler检查，不能扩大预算绕过|
|题间调度|四组答案锁定并评分后入库/关联/调度；20题窗口仅核算与报告；原始证据无窗口失效；预算不足保留积压|最后一题不触发无后续用途的新学习；未知请求全局停止，不自动重发|
|T/F对照|workflow：T由全部历史题面、F由可信失败分别选择；paired_information：运行前冻结相同题包/时间点，同算法接口和预算上限|前者比较整体策略，后者比较失败信息；成对模式不给T错误标记、轨迹或失败驱动选题身份|

## 复用与新增

新增math_cumulative.py、math_cumulative_learning.py、math_cumulative_stream.py。复用EvidenceStore、CompileQueue日志、BoundedCompiler、SharedTransport对应已有生成通道、PersistentBudget、SplitRunner/Linux Worker、VersionGate与MathPublicationGate。候选静态检查、一次工程修订、来源执行和现有准入规则沿用旧WindowLearner流程；没有预置数学算法，也没有放宽Gate。

运行路径：CumulativeStream → 原生四组solve/锁定/评分 → CumulativeMemory.ingest → 关联模型适配器 → 不确定机制簇 → CumulativeQueue → 有界bundle → 原有归纳/源码生成/工程修订 → 来源执行 → ReviewedRelease → Shadow或有限授权 → 后续统一路由。公共源码修改后必须重新验证，沿用已有版本Gate绑定。

旧math_stream.py/math_stream_learning.py不改。新入口scripts/run_math_cumulative.py只接受新Run目录；prepare不发API，run必须提供绑定Run ID与协议哈希的新授权文件。不会将新机制嫁接到已经结束的200题账本。未知请求保持全局停止，此入口不自动继承旧探索实验的网络隔离例外。

## 数据与证据

raw.jsonl：完整源证据；public.jsonl：按题后时间可见的公开题面；views.jsonl：模型可追溯描述及关联作业结果；clusters.jsonl：机制版本、关系、来源执行诊断。queue.jsonl：优先级/跳过理由/消费记录。已有provider/compiler/budget/registry日志保留原始请求响应、用量与版本。

HOST_MIDDLE_OMISSION表示宿主裁剪，delivery_status/finish_reason表示真实交付；两者分开。parsed_wrong_answer从公开模型输出解析，不来自Gold。关系引用须匹配实际提供的公开题面或片段；引用一致不等于机制真实成立。

来源检查的诊断只投影执行状态和二值结果，并绑定工件SHA；不投影预期答案、Gate结果或未来任务。功能验证失败不会自动无限修算法，保留结果，后续有新证据才考虑新生成作业。

## 对照与预算

默认配置：每组最多20个关联作业、6个生成作业，每个关联1次调用；每个生成最多1次归纳、1次候选、1次工程修订。因此不含独立Gate的辅助调用上限为每学习组38次。真实计划须按任务流长度另行冻结，默认值不是付费授权。模型/Token/工具费用全部沿用已有账本，R在下一报告窗口按过去F的全部关联/生成/修订/验证请求数获取调用额度；实际Token和美元仍不必相同。

配置独立Gate时，额外验证调用上限还需加入现有4×Gate案例数×生成作业上限；准入资源不足应停止或保持Shadow，不能把这些费用排除。每个报告窗口新增关联/生成额度亦受r_max_extra_calls约束。源码和测试集哈希、Worker版本、数据顺序及配对题包都需在新Run冻结。

paired_information模式只允许每个冻结题包提出一个候选簇；T/F生成时使用全部同包题面，F额外具有其真实错误证据。没有失败记录不意味着给T提示“这些题都做对了”。支持两种实验模式不意味着本轮已运行两个真实模型实验。

## 验收与研究边界

工程验收使用已曝光的人工夹具、Mock响应和真实Docker Worker；无新200题求解或付费模型。覆盖持久化、无重复请求、T字段隔离、预冻结题包、未知来源不计独立原题、反例优先、多簇/无簇、新信息去重、未授权拒绝、Shadow与真实Gate路径。

历史只读回放：F的55条CONFIRMED_WRONG全部持久保存；94正确、13截断、32UNVERIFIED、6基础设施缺失不进入数学失败。20题边界累计失败数为5、11、17、19、29、34、42、46、50、55。这里只做真实记录入库与时间边界核查，没有调用模型聚类，也没有声称55条构成某几个共同机制。

真实模型是否能形成有意义的簇、独立反例是否改变机制、是否因此产生可执行算法及收益，仍需新协议的真实试验。本轮不新增付费授权，不推送Git，不改写历史结果。

## 使用

零API测试：
```bash
PYTHONPATH="/private/tmp/flowevo-goal-test-deps:FlowEvo/src:scripts" /opt/homebrew/bin/python3.11 scripts/test_math_cumulative_boundaries.py
PYTHONPATH="/private/tmp/flowevo-goal-test-deps:FlowEvo/src:scripts" /opt/homebrew/bin/python3.11 scripts/test_math_cumulative_learning.py /tmp/flowevo-cumulative-new-acceptance
```

新协议准备入口（必须提供新的plan及已冻结的数据路径）：
```bash
PYTHONPATH="/private/tmp/flowevo-goal-test-deps:FlowEvo/src:scripts" /opt/homebrew/bin/python3.11 scripts/run_math_cumulative.py prepare --output runs/NEW_RUN --plan PLAN.json --tasks PUBLIC_TASKS.jsonl --private-scoring PRIVATE_SCORING.jsonl --lineage LINEAGE.json
```

plan在原StreamRuntime参数基础上增加cumulative配置（见同目录config_example.json）。不要将旧运行目录作为output。prepare仅生成冻结协议和未授权模板。

最终验收：端到端 33/33 项通过，边界单元测试12/12通过，真实Linux Worker组件执行 78 次，付费模型调用0。旧200题冻结源码逐文件SHA核验一致。机器可读结果见acceptance.json。
