# 失败定向技能获取：实现映射

基准 d845600594ee4d0d32c60b17b3cc7a12cd3f73e1；独立分支 feat/failure-acquisition-prepare。开始时 HEAD 与基准一致、无已跟踪文件差异，已有未跟踪历史材料未覆盖。D1–D5 脚本、候选与 runs 归档未修改。

本轮已接回原生代码链：BenchmarkRunner.run_episode → CodeTaskPlanner → CodeTaskExecutor → 原生 Generator 接口 → verify_task/Sandbox。新增默认关闭的 executable_skills_enabled。关闭时直接调用原执行体；原生 LLM 提示路径在开启时展示用途、签名、前提、正常返回／错误约定和稳定 import 名，不再展示 helper 源码片段。离线来源任务使用仓库自身 HeuristicGenerator 产生并真实执行失败，教师以及未来任务程序文本使用明确标注的 Mock；没有验证 LLM 自主选工具的质量。

题末 AcquisitionScheduler 使用公开投影重新验证原尝试，独立保留原失败、能力候选假设和取得结果。教师只见 prompt、实际源码和允许的公开验证反馈，不接收 canonical_solution、hidden tests 或未来任务。验证非空且实际执行后产生 teacher_* 独立 ExecutionTrace，记录真实 AttemptRecord/VerifierFeedback 和 teacher_acquisition_success 来源，再经 Compiler.compile → admit_compiled_trace/GateKeeper → PrimitiveCompiler → PrimitiveStore。成功教师不修改学生 trace.success，不走学生使用统计。

|修改位置|目的和实际接入|
|---|---|
|failure_evo/teacher_acquisition.py|题末调度、独立教师成功轨迹、结果状态与成本来源；ReplayTeacher；未来显式启用的 BudgetedTeacher 复用 PersistentBudget 和 post_deepseek，默认拒绝真实请求，未知或已消费请求不重发|
|failure_evo/acquisition_selectors.py|失败选择与不依赖成败的普通哈希抽样；输出全部选择／未选择记录；问题、来源谱系、近重复跨角色隔离，能力 family 可跨角色|
|failure_evo/acquisition_adapters.py|代码公开投影与有效 assert 验证；数学 PublicMathTask、交互公开状态接口，两个完整获取适配器明确未就绪|
|failure_evo/skill_runtime.py|从准入卡构建冻结模块包；校验源码哈希、模块名和依赖完整性；稳定 flowevo_skills.op_* 入口；真实运行选择、开始、返回／异常事件|
|agent/generator.py、executor.py|原生提示提供调用接口；原生执行器绑定同一模块包到全部尝试，记录检索／展示与实际调用，返回后继续原任务程序|
|env/sandbox.py、eval/verifier.py（复用未改）|原有 verifier 使用同一个已绑定 Sandbox；可选模块文件包放入临时目录，运行后收取调用回执；关闭新功能维持原路径|
|core/schemas.py|带默认值的入口、依赖、独立来源、操作约定、实际调用和验证状态字段；旧 JSON 仍可读取|
|compiler/compiler.py、gatekeeper.py|显式被验证入口优先；公开验证断言转成真正会失败的准入重放；所有 GateKeeper 重放绑定冻结依赖|
|compiler/primitive_compiler.py|传递辅助函数、常量与 import 的闭包；函数作为 key 参数传递也保留；提取后再次检查自由名称；不支持结构保守拒绝|
|memory/primitive_store.py|按独立来源而非导入次数增加支持；一次来源仍是 draft；两来源才沿用原生阈值激活；禁止同 ID 源码漂移|
|alfworld_/success_baseline.py|抽取 compile_success_into_library；原 update_library 继续相同编译与统计，教师可只调用编译部分，不污染 guided/unguided 或效用统计|

新 helper 不包含任务答案常量生成器；本轮 Mock 函数专为接口验收，不能视为模型学得算法。每个操作的 purpose/parameters/preconditions/output/side_effects/failure 来自教师响应，缺少约定时保留 SUCCESS_WITHOUT_REUSABLE_OPERATION。只支持可解析的普通函数、字面量常量、允许的标准库和冻结模块；不是任意 Python 依赖打包器。新模式的独立来源去重属于三组共同基础设施，后续不能归因于失败学习；关闭新模式时仍沿用旧记录的计数语义，不将历史产物静默升级为已验证 helper。

执行日志的 retrieved/presented 来自原 runner 检索与接口传递；selected/started/returned/error 来自运行时 wrapper。仅 import 名或提示 ID 不计运行。returned 保存有界结果预览及截断标记。局部返回成功与 trace.success 独立，已验收“helper 返回、任务随后抛错”，也覆盖依赖任务再次直接复用；此时没有 Generator 展示事件，依赖仅在子进程加载，任务源码哈希与冻结包一致。这里是原生 subprocess 的执行观察，不是抵抗恶意 Python 篡改日志的可信安全隔离；新增路径未宣称获得 Docker Worker 的安全保证。

## 三领域就绪状态

|领域|当前可运行|未接通／限制|
|---|---|---|
|代码 HumanEval/MBPP 公共 assert 接口|原生 runner 学习、验证、编译、准入、实际参数化调用闭环；本轮完整夹具使用 HumanEval 接口|正式训练／评价清单未冻结；Mock 不是教师能力或泛化证据；现有旧 helper 未重新验证时新执行模式拒绝加载|
|TACO / LiveCodeBench|存在历史数据和其他 runner，不传入本轮函数任务适配器|ADAPTER_NOT_READY：stdin/stdout 或多签名加载、公开验证集合、最终评分的 native BenchmarkRunner 适配缺失；历史 TACO StopIteration 不能用 HumanEval 夹具冒充适配成功|
|数学|PublicMathTask 严格公开投影、真实本地参数／结果往返；code_math/no_gold.py、runner.py、failure_evo/math_operators.py 已映射|ADAPTER_NOT_READY：no_gold 验证成功的可用证据、强教师成功判定和原求解器显式调用后继续推理未接好；现有 NoGoldMathController 的 first_applied_operator 可直接锁定答案，不等同于此新模式；本轮没有运行 MathOperatorRunner/Linux Worker|
|ALFWorld|历史真实回执进入 AlfWorldExecutor；旧 L1/L2 成功编译入库独立于学生计分|ADAPTER_NOT_READY：原 Agent 显式选择 Python 操作并传参、教师真实前缀／后缀预算接线尚未实现；不是新环境试验。旧 L1 blueprint/L2 继续保留，不称为新算法；PolicyGenerator 自动遍历不是显式调用；未扩展 D5 窗口|

数学公开输入仅 task_id/problem；真实错误需答案锁定后的独立评分或允许的公开精确验证，不能仅以模型自检确认。可复用函数应接收明确参数、返回计算结果，文字解答不得伪装 Python 成功轨迹。未来数学 no_gold 路径继续隔离私有最终答案。

本轮只实现准备命令和接入点，不引入未来求解 Agent，不套用旧 BoundedCompiler 的家族／槽位限制，也不修改旧 data_roles.py。diff 见 Implementation.patch；新模块与准备命令在仓库中保留。

## 2026-11-20 Pilot 接入更新

上一节描述的是2026-11-19零 API 准备版本；本次已新增可直接启动真实代码开发试验的分阶段入口，当前等待本轮明确预算授权。详情集中于 ../failure_acquisition_pilot_20261120/Pilot_Protocol.md、Pilot_Data_Manifest.json、Pilot_Preflight.md。

|位置|当前实现|
|---|---|
|scripts/run_failure_acquisition_pilot.py|preflight/collect/acquire/support/freeze/transfer/report；协议／源码／数据哈希、独立库快照、授权与停止记录|
|env/humaneval_loader.py、failure_evo/pilot_data.py|真实本地 HumanEval loader、公开例子确定性断言转换、24训练／12迁移清单；原始私有评分延后独立执行|
|failure_evo/pilot_runtime.py、persistent_budget.py|原生 LLMGenerator 客户端预算适配；保留额外策略提炼；按冻结角色费率预留；独立回执、未知停止|
|teacher_acquisition.py、primitive_store.py|最多一次来源反馈修订；同 SHA 候选在一个独立训练任务中真实调用、整题公开验证、返回值依赖检查；证据去重后激活|
|skill_runtime.py、container_worker.py、code_worker.py|只读冻结模块挂载；draft 训练期限定；真实返回及异常、资源与网络隔离；复用现有 DockerWorker|
|agent/executor.py、eval/verifier.py、compiler/admission.py、eval/runner.py|公开 import 兼容，旧 helper 提示复用保留；共享隔离后端贯穿执行与准入，公开验证与最终评分分离|

七类必要预检通过，真实付费请求仍为0。原先“没有可执行付费CLI”的状态已由此次入口补齐；正式 G/G+F/G+U 比较依然未启动。HumanEval真实数据准备完成不等于模型学会；数学、ALFWorld、TACO/LCB 的未就绪范围保持原结论。原41项零 API 结果及 D1—D5档案未改写。


### Pilot 实跑状态（2026-11-20）

冻结24题训练已通过真实 Flash 和原生链执行；25次解题请求、11次原生策略提炼，共36次。23题首次公开通过，HumanEval/59原生修复一次后通过，题末失败0。按协议未调用Teacher、未进行第二支持或迁移比较。因此真实 Actor 接入已实跑，真实 Teacher 学习与新操作自主复用仍未检验；本轮不扩池。结果见 ../failure_acquisition_pilot_20261120/Pilot_Result.md。
