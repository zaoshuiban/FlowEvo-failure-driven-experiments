# Postlock Opportunity Audit

基于已结案的 runs/failure_acquisition_pilot_20261120/real_01。审计日期：2026-11-20。以下均为新增事后观察，不回填旧 Pilot。

## 先回答研究问题

1. **原“零失败”是否主要由公开验证覆盖不足造成？本次没有这样的证据。** 24 个当时实际执行的最终程序，在同版本可用完整评分中全部通过。公开通过／完整失败为 0；评分异常及源码／依赖不可恢复也为 0。有限完整检查不等于全域正确证明。
2. **当前接口兼容、可信的未解决训练失败：0 个。** 旧 Pilot 的题末公开失败 0、学习项 0 保持原样。
3. **真实失败后恢复经验：1 份，HumanEval/59。缺少可调用正确实现的有 0 份；普通 active 路径尚未接入的有 1 份。** 修复已保存为 shadow 任务技能，现有原生执行接口可以显式调用，但不属于原 11 个准入程序，也不是普通 Actor 已经可以自动选用的 active 操作。
4. **下一轮优先复用已有修复，不需要强教师重解。** 如继续处理 HumanEval/59，新增工作是契约、绑定及独立训练准入证据；不能计为教师救回原 Agent 最终失败。
5. **这 24 题没有新增实现获取来源。** Next_Learning_Items.json 的 learning_items=[]，记录 **NO_ADDITIONAL_ACQUISITION_OPPORTUNITY_IN_CURRENT_POOL**。这个状态仅指额外获取正确实现；不抹掉 shadow 接入缺口。停止对本池追加求解／教师学习请求。已有 taco_0875 是更可信的历史开发候选，但尚未适配当前接口，不能现在计入准入训练项。

## 实际范围、成本和封存

|项目|实测|
|---|---:|
|锁定的训练最终程序|24|
|完整评分执行|24|
|HumanEval/59 原生新参数调用执行|1（内含 4 次函数调用）|
|新增模型请求／Token／模型费用|0 / 0 / $0|
|隔离执行总数|25|
|累计 Worker 墙钟耗时|7.037 秒|
|账本向上取整计时|7049 毫秒|
|账本未结算／未知请求|0|
|12 个迁移任务执行|0|
|旧 Run／协议／报告／冻结源码核对文件数|567，全部一致|

独立新账本上限为 0 模型请求、32 次执行、900 秒墙钟，没有消费旧 Pilot 的剩余额度。未计价本地计算费用；零模型费不等于零执行成本。无新增 TACO 执行。

审计协议 SHA：ed11ef309a6fdc1ffba31e8aebd0c5fdd506cfc4ade0398fc53d258005415722。冻结审计脚本 SHA：8c3c723852710b08d55490437232379e401ec3261d5413a4ed0256253a2804e9。旧文件集合前后摘要均为 015fbf312e77360a203064a44201853ed01bd89167920ebe6ce44458ebea3530。

迁移任务仅核对封存 ID，未选择其评分对象、执行程序或产生学习材料。没有新求解 Agent、没有教师实例，没有发布／推送；只新增审计脚本和独立产物。

## 源码与执行条件如何绑定

逐题从 collect_progress.json 定位原 trace，核对最后 attempt、code_history[-1]、公开 VerifierFeedback 的执行代码与旧 Docker 输入／回执。任务 prompt、入口、公开版本摘要、完整数据文件摘要与冻结配置一致。**24/24 成功恢复。**

使用当时实际提交的完整源码字节和 trace 内嵌依赖 bundle，不取后来库中更新的程序。本池没有原生直接复用完成的题：结果为 pure_dynamic 或 skill_seeded_dynamic；后者是提示辅助的实际新程序，不是执行后来库版本。所有 bundle 均为空，依赖为原镜像中的 Python／标准库，无额外第三方模块。逐题保留请求、响应、请求回执、公开执行回执和关联技能 ID。

final_source_sha256 是源码 UTF-8 字节的 SHA-256。历史回执的 code_sha256 实际为 canonical JSON 字符串指纹；审计按旧格式核验，并另记真实源码 SHA，未混用。依赖包摘要采用原有 canonical JSON 指纹。

原公共 harness 捕获断言后可能以进程码 0 退出，故**旧 raw Worker 的 passed/returncode 不是公开题目成败**。审计解析 harness 通过数／总数，与原 VerifierFeedback 核对；HumanEval/59 首次确为公开失败。

本次调用未改动的 eval.verifier.verify_humaneval，加载同一数据版本的完整 test，运行原 check(entry_point)。评分前检查 check 与断言存在。未使用 canonical_solution；没有根据测试生成、修订或修补程序。私有 stderr、断言和 executed_code 只存 private_scoring，不进入逐题摘要和训练投影。

## 逐题公开检查与完整评分

表内源码 SHA 显示前 12 位；完整 SHA、任务版本、入口、依赖镜像、逐题 scorer test 摘要、请求和执行回执引用均见 Postlock_Opportunity_Audit.json。

- S1：同一冻结 HumanEval 数据 + 原 Verifier，逐题 test 摘要分别列于 JSON。
- Verifier SHA：77b4ff39afde45ed3f6854cf778eaef10e2f7b47ba6ef81d195c96ca5255f024。
- 数据 SHA：b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef。
- 原始镜像：sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8。
- D0（每题相同的空 bundle）完整 SHA：80392c22197a063f482b45cbc08c567c08c3248d71083073ac6f5388eddedc2b。

|task_id|final_source_sha256（前12）|public_verdict|full_check_verdict|scorer_version|dependency_bundle_sha256|execution_receipt|
|---|---|---|---|---|---|---|
|HumanEval/0|6dbbff3b9d38|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_0/1/result.json)|
|HumanEval/20|d6d1562b15e1|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_20/1/result.json)|
|HumanEval/1|3de684b63f01|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_1/1/result.json)|
|HumanEval/6|88e795dd3489|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_6/1/result.json)|
|HumanEval/56|b5db9bb86dac|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_56/1/result.json)|
|HumanEval/61|1762c78c8d8d|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_61/1/result.json)|
|HumanEval/13|3a0782ea9a1a|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_13/1/result.json)|
|HumanEval/24|55ed8c36a46a|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_24/1/result.json)|
|HumanEval/25|dbfbd33b0ac5|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_25/1/result.json)|
|HumanEval/31|cd3b2c411435|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_31/1/result.json)|
|HumanEval/39|e6db5b426a71|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_39/1/result.json)|
|HumanEval/59|a1b45f115ec2|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_59/1/result.json)|
|HumanEval/8|f6fe9a3e7d67|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_8/1/result.json)|
|HumanEval/9|35e3fc471eb1|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_9/1/result.json)|
|HumanEval/21|655c0b65e0c7|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_21/1/result.json)|
|HumanEval/46|fdf86e8265ff|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_46/1/result.json)|
|HumanEval/55|2020175cd108|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_55/1/result.json)|
|HumanEval/63|8855c6fc2eb9|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_63/1/result.json)|
|HumanEval/10|fa0ddd4cf2d4|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_10/1/result.json)|
|HumanEval/48|8e6b362f06ab|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_48/1/result.json)|
|HumanEval/18|06697d5b9e86|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_18/1/result.json)|
|HumanEval/17|8d1c7d14ebcf|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_17/1/result.json)|
|HumanEval/33|1bceddee7295|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_33/1/result.json)|
|HumanEval/37|173e77314ea9|PUBLIC_CHECK_PASS|FULL_CHECK_PASS|S1|D0|[回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_37/1/result.json)|

汇总：公开通过且完整通过 **24**；公开通过但完整失败 **0**；评分异常 **0**；源码／依赖无法恢复 **0**。11 个原准入程序的完整评分均通过，需标记的失败关联产物为空。未来如发现准入产物完整失败，应在各比较组的新基础库副本中按同一来源 SHA／依赖规则隔离，保留旧 Run 的历史准入事实。

## HumanEval/59：失败、修复、产物与调用

原始证据：[trace_8c0627be](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_pilot_20261120/real_01/base/traces/trace_8c0627be.json)；[真实失败与公开回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/public_probe/original_failure.json)；[完整评分回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/private_scoring/executions/full_check/HumanEval_59/1/result.json)。

首次程序不断约去因子后直接返回剩余 n，在原公开例子 largest_prime_factor(2048) == 2 上返回 1，公开检查为 1/2 通过。这是实际反馈，不是注入故障。原生第二次尝试保留已除去的最大因子，并处理剩余大于 1 的因子；两个公开例子和本次完整评分均通过。最终成功不改写成原系统题末失败。

原成功编译产生了 skill_humaneval_HumanEval_59_trace_8c0627be，保存的是**完整任务程序及顶层参数化函数**，并非只有文字策略。状态 shadow、direct_eligible=false、compiled_skill_admitted=false；原因为 seeded_shadow_compile。因此它**不属于 11 个 active 准入程序**，但这不等于没有保存实现。

- 原最终提交 SHA：a1b45f115ec230fdf42be65e811c482ebd11de8e7575045815e54e38f8d66915。
- 原编译产物 SHA：ae18e0d8aa0310008febd94f43014345bc379febb8257b4c056d8454a853d87d。
- 两者 SHA 不同是原 Compiler 增加公开题目函数桩／文档造成；最后定义、实际生效的函数 AST 完全一致。本轮没有重新编译、改写或替换原文件。
- 输入：整数 n，遵循原题 n > 1 且非素数；输出：最大素因子整数。职责单一，仅内建依赖，无外部副作用。
- 顶层函数本身就是有明确输入输出的参数化操作。helper_function_count=0 不是不可复用证据。PrimitiveCompiler 偏向 helper 提取只是接口限制。

通过**现有 CodeTaskExecutor 的 call_skill 路径**，显式指定原文件、SHA、入口和空依赖，在原 Docker 中执行参数 [81, 77, 121, 360]，期望 [3, 11, 11, 5]，4/4 通过。参数在评分前声明并符合公开前提。这是新参数调用诊断，不是第二独立任务，也不声称与隐藏测试去重。生成器禁用，没有改卡片为 active 或放宽普通路由。[调用 trace](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/public_probe/trace.json)；[调用回执](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/public_probe/executions/native_call_probe/HumanEval_59/1/result.json)。

|核查状态|结论与边界|
|---|---|
|NATIVE_ARTIFACT_EXISTS|是：源码、技能卡、依赖和编译记录存在，shadow 保存|
|CALLABLE_CAPABILITY_VERIFIED|是：原生执行接口显式加载同 SHA，在新参数下实际调用成功|
|ADDITIONAL_ACQUISITION_NEEDED|否：正确实现已有，无需教师重解或人为制造嵌套 helper|
|COVERAGE_UNCERTAIN|普通 Actor 自主复用和第二独立任务支持未验证；默认检索不含该 shadow 卡片已确定|

若下一轮让它进入常规操作库，应复用已有实现，补契约／绑定，再在第二独立训练任务调用冻结 SHA，完成准入和原 Actor 复用诊断。当前探针不替代这些步骤。新增内容是接入与证据，不是新的算法能力；该项单列 existing_repair_followups，不充入 learning_items。

## 新训练资格与教师规则

仅适用于下一份明确冻结的新协议，不追溯修改旧 Pilot。

|类型|可用来源|边界|
|---|---|---|
|A 未解决训练失败|正常预算后公开失败；或答案锁定后经允许的独立训练评分 FULL_CHECK_FAIL|评分异常和无法恢复不是程序失败；最多 3 项，先谱系去重、再能力差异，按冻结顺序，不按教师容易程度挑选|
|B recovered_failure|真实中途失败、后来修复成功；先查现有库和实际调用|保留最终成功；已有可调用实现无需额外获取，接入／准入缺口另记|
|C 工程问题|网络、交付、评分器、依赖恢复|独立记录，不直接当算法学习项|

分开保存 final_public_verdict、independent_full_check_verdict、中途失败／公开恢复标签、原生产物、可调用状态和准入状态。若公开错误已修复但完整评分仍失败，两种事实同时保留。HumanEval/59 是“中途真实失败→原生修复→公开通过→完整通过”。

教师规则：已有验证通过的真实修复先复用；确实缺少正确实现才考虑强教师；实现仅参数化不足时，必要且有独立预算才请求整理；原生已有可调用能力记为无需获取。发生失败不自动触发教师。这里没有申请付费比较额度。

## 私有评分与学习／编译输入分离

这 24 题明确是 train，新用户指令允许二元训练反馈用于后续新协议；旧 Pilot 按原公开学习规则结案。未来各组权限和预算一致。

完整私有 VerifierFeedback（executed_code、stdout/stderr、测试／断言）仅在独立 private_scoring，目录 0700、评分文件按 0077 umask 写入。不交给模型、Compiler 或检索。

model_projection 只接受一个 bool 训练结论，以及公开 manifest、实际 Actor 源码和公开反馈。输出只有公开题面／源码／公开断言与成败、二元训练结论、评分回执引用；它不是可送成功编译器的 ExecutionTrace。嵌套 executed_code／failed_tests／hidden_inputs／canonical_solution 污染标记检查通过，将整个私有对象当二元值会被拒绝。没有向任何模型发送投影。

现有 Compiler 某些路径会从成功 VerifierFeedback.executed_code 提取重放测试，**自身没有完整私有信息隔离标记保护**。未来不得把私有完整评分的成功反馈构造成教师成功 trace 再给 Compiler。只用允许公开的验证形成编译轨迹，带显式公开 assertions；私有评分仅给二元信号和回执。不得重命名隐藏测试为公开材料。

本次通过隔离和白名单避免该泄漏路径，没有改旧编译源码，也不声称已对全框架完成信息流安全证明。旧数据约定禁止学习的私有评分仍仅限诊断，不通过改角色绕过。

## 明确的数据升级路线

**排除 taco_0003 输入消费假说作为当前可信来源。** 其历史初审记过 110 个通过后 StopIteration，但后续 E1 最终卡为 VERIFIED_EVALUATION_PROBLEM / invalid_input。对应旧失败为声明长度大于实际 token 数；269 个测试中 7 个违反输入契约，原首稿和最终程序在剩余 262 个合法测试的复审均 PASS。不能据此证明全域正确，但不能继续把该 StopIteration 直接当能力缺口。证据引用在 JSON，私有具体输入／期望／断言未写入学习投影。旧准备报告不改，本报告追加纠正。

**优先审查 taco_0875 深链递归开发案例。** 历史报告有合法无环父节点链 n=1100，期望由题意可得为 1100；原程序实际 RecursionError，已有局部修复通过冻结的 89 个合法输入。契约检查、原源码、修复和回执俱全。本轮未重跑，也不是当前模型新学习成果；已有修复仍优先复用。旧私有最终评分输入和 oracle 继续限于诊断，不能改角色送教师。

最小适配仅限父节点森林契约 parent_forest_depth(parents: list[int]) -> int：1..2000 个节点，父索引 1-based 或 -1，无自环和有向环。保留原历史失败／修复 SHA，明确 stdin 到参数的等价映射，以合法公开输入核查。提取／整理不冒充原程序原样执行，人工整理不声称为模型学会。

必要代码改动（本轮不实施扩展）：

1. acquisition_adapters.py 加明确标记 taco 的函数子集入口，保留原任务 ID、版本、谱系和角色，不伪装成 HumanEval。
2. 薄的专用 loader 加载公开题面和类型／契约；eval.verifier 为该子集复用函数验证，私有评分单独分派。不先支持全部 stdin/stdout、多签名、数学或交互。
3. 必要时 PrimitiveCompiler 增加“显式声明的顶层参数化操作”选项，保留完整依赖／SHA 检查，不凭非嵌套判定无能力。
4. 新协议、独立账本和 manifest；核对历史请求／源码谱系、排除故意错误夹具、解决重复组。旧 E1/RGF 隐藏评分和参考材料权限不扩张；未来独立评价另取未曝光来源。

通过来源和最小适配检查后，再走“取得候选→冻结 SHA→第二独立训练任务实际调用→准入→原 Actor 复用诊断”。第二来源是训练／准入，不是独立评价。无需继续随机抽相似 HumanEval，也不立即启动无新学习项的付费比较。

## 产物与复核

- [Postlock_Opportunity_Audit.json](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/failure_acquisition_postlock_audit_20261120/Postlock_Opportunity_Audit.json)：逐题状态、完整摘要、原请求／本次回执、能力层次、成本、完整性。
- [Next_Learning_Items.json](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/failure_acquisition_postlock_audit_20261120/Next_Learning_Items.json)：学习项为空，另列修复接入与数据升级门槛。
- [冻结协议](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/protocol.json)、[锁定提交](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/locked_submissions.json)、[独立账本](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/failure_acquisition_postlock_audit_20261120/budget.jsonl)。
- [零模型审计脚本](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/audit_failure_acquisition_opportunities.py)：prepare 锁源，execute 复用 Verifier／Docker／账本与原生 call_skill。报告解释和下一步资格在评分后单独整理，不改已经执行的评分源码。
