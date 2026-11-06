# 冻结记录的只读收益审计

工具：`scripts/analyze_math_reuse_outcomes.py`。仅使用标准库，不导入运行器、Registry、评分器或模型客户端；不执行候选源码，不写Run、权限、评分或预算。输出在仓库外并限制为0600。

## 事前方法

固定方法文件：`math_outcome_protocol_v1.json`。主指标为F相对G在四组共同可信评分任务上的原题等权正确率差；F/T、F/R固定为次要比较，不能看结果后只选择有利组。

同原题参数变体先归为一个原题；统计检验进一步按已核验谱系聚类，使用双侧精确符号检验。逐题净正确数与描述性精确McNemar同时报告，但不能将同原题重复观测当作独立样本；单条自适应任务流的检验只作探索性证据。

CONFIRMED_CORRECT/WRONG进入可信数学配对；TRUNCATED、UNVERIFIED和基础设施缺失分别列出，并给完整计划集的成功率上下界。缺失不是数学错误。缺少已核验原题/谱系时主原题指标不可评价，但仍提供同题描述结果。

正式Run应在STREAM_FROZEN计划中同时记录：

- `analysis_protocol_sha256`：方法JSON按仓库canonical规范序列化后的SHA。
- `analysis_implementation_sha256`：分析器Python文件字节SHA。

两者未绑定或工程Mock时，一律标EXPLORATORY_POSTHOC_OR_ENGINEERING。绑定只证明宿主计划包含这些哈希，不是第三方时间戳或数学正确性认证。方法变更必须新版本、新协议；不能修改旧Run后回称事前注册。

## 配对与归因

- 全程比较：G/T/F/R相同任务、相同问题哈希和可信锁定结果；报告共同集合及各组缺失情况。
- 介入子集：确认实际APPLIED结果出现在最终答案锁中，再与G同题结果配对。这是条件性的工作流比较，不是同检查点单次算子的因果效应。
- 同检查点反事实：现有记录缺乏冻结且可核验的反事实对照，因此明确NOT_EVALUABLE，不把先错后对冒充算子因果增益。
- 不同原题复用：核对精确候选版本、原有准入、发布、任务授权、试用额度及时间顺序；复核冻结源码SHA，排除来源/生成曝光、验证题、同谱系参数变体、未知谱系、已暂停和非复用型制品。成功使用次数与不同原题数量分开。
- 谱系里的`source_identity_verified`和`prior_exposure=false`是受信宿主冻结元数据输入；分析器不为它们认证来源。独立计数仅为CONDITIONAL_ON_FROZEN_LINEAGE，不能代替真正独立评审。

## 适用性与转换率

只有冻结reviewed_cases与V3_VALIDATION的候选、数据哈希、问题哈希匹配时统计标签条件下的误接受/误拒绝。Development与Gate分开；未知标签不强标。另报UNKNOWN、ERROR、支持题覆盖损失、参数映射错误与联合正确接受，避免“全部UNKNOWN却误拒绝率0”的误导。

评审者可信身份仍是外部依赖。统计标为CONDITIONAL_ON_FROZEN_HOST_LABELS；不能因为文件中有reviewer名字就视为独立数学Oracle。

失败到Gate分别报告：可信失败证据中实际贡献给Gate候选的覆盖率、候选到Gate的版本转换率。它们不是同一分母，更不是失败因果或长期收益证明。

## 成本

直接读取原预算事件和原始响应，按物理请求身份去重，包含失败/截断响应、归纳、生成、修订、Gate验证与R额外计算。`channels`分solve_base、solve_extra、learning、validation；推理Token已在输出中，不再重复收费。

方法文件的各通道报价为每百万Token美元，字段为input_uncached、input_cached、output；Worker单价另用worker_usd_per_second。真实实验必须在运行前填写并冻结合法报价，不使用预算预留单价冒充实际报价。

报价、usage、响应或祖先账本缺失时，总费用不可评价，保留可知小计、Worker实耗时间、缺口和UNKNOWN预留。预留不是消费，供应商实际账单没有独立凭据时不可得。Mock usage只作模拟计算，真实API实付为0。0成功时每成功成本不可评价。

本版面向同一完整Run，不自动合并多个续跑祖先。不能仅凭最新续跑目录声称已包含祖先学习成本；检测到继承标记时费用保持不可评价，直到准备完整祖先审计输入。

## 命令

先停止输入写入，准备与Run冻结任务哈希一致的tasks.json/JSONL、完整lineage.json以及方法文件。冻结清单与结果均在仓库外：

```sh
python3 scripts/analyze_math_reuse_outcomes.py freeze \
  --run /controlled/RUN \
  --tasks /controlled/tasks.json \
  --lineage /controlled/lineage.json \
  --protocol docs/research_evaluation/math_outcome_protocol_v1.json \
  --output /controlled/audit/snapshot.json

python3 scripts/analyze_math_reuse_outcomes.py analyze \
  --manifest /controlled/audit/snapshot.json \
  --output /controlled/audit/analysis.json
```

现有输出不覆盖。任何日志哈希、链、锁定、评分、任务顺序、问题或参考文件漂移均拒绝。分析前后重新核对，不能在活动Run上边运行边冻结。该工具不接受隐藏答案作为新的评分Oracle，也不重新判数学对错；它审计宿主已锁定的评分事实。

完整分析与快照可能包含私有路径，应使用现有受控归档器保存。公开只放经审查的汇总、源码SHA与归档完整性凭据。

逐题输出包含四组确认状态。Shadow 原生配对要求注册表执行事件、Shadow 锁定、私有评分及原生锁定引用一致。配对效应同时给出按谱系加权的 95% Hoeffding 区间，依赖谱系独立假设。缺少实际介入前的同检查点原生对照时，该指标仍为不可评价。
