# P0：代码差距审计（修改前）

基准HEAD为8ff0e7ac34a87ce9ccda6dafdf0da32b1cc35832；在此前未提交MVP及计量修复上增量开发。旧实验制品与账本不改写。本轮不付费、不推送。

|组件|当前事实|复用/缺口|
|---|---|---|
|failure_events|持久公开事实、时间边界、撤销、源码hash已实现|旧legal判据依赖public_cases；新学习入口必须另做可信宿主合法性验收，保留旧记录|
|symptom_learning|症状索引、版本及公开效果记录已实现|症状不是根因；新机制内容需要独立结构化验证|
|compile_queue / PersistentBudget|有限编译、重复槽位阻断、最终wire预检、持久预留、UNKNOWN已实现|复用，不另建账本；上一轮计量修复已保留|
|LearningLoop.run_pipeline|已调度单家族并调用LearningPipeline|扩展公开输入构建钩子，使用可信证据准入|
|LearningPipeline|已有3候选、修订、winner冻结、独立gate/regression与防重放|静态只有函数存在性；接入真实静态/Worker checker；新增可配置候选数与无机制停止，不更改旧默认|
|model_api|DeepSeek生成、静态权限与返回契约已实现|复用检查器；不能把提示request_repair当算法|
|autonomous_generation / autonomous_mvp|此前GPT接口Mock、DeepSeek1次真实归纳；真实Worker Mock闭环|只有code_repair路径；GPT实际源码生成仍未检验；旧MVP合法性侧车不等于可信验证器执行|
|data_roles|五角色和四类谱系隔离已有|新流水线强制使用；工程构造样例不称自然独立任务|
|pipeline_admission|绑定winner、gate、regression、paired证据已有|复用证明构造；有限准入仍由宿主和原注册表决定|
|failure_registry / generations|Shadow、有限权限、暂停、额度、题间快照已有|task_solver只是kind；before_task调用能力缺失，不修改旧卡默认hooks|
|plugin|Worker调用、结果复验、回退、暂停已有|增加独立显式启用的任务开始能力；必须禁止在来源/设计题复用|
|workflow_policy|Python输出request_repair后由宿主再调用模型|提示策略，不是确定性算法算子，本轮不复用其动作|
|workflow_runtime_v2|真实五阶段求解、公共预算及插件路径已有|加入默认关闭的task_solver调用点；关闭时行为不变|
|run_learning_stream|S19持续JSON动作学习真实路径|不静默切换为新Python生成协议|
|learn_reuse30|S15人为指定两类机制、宿主模型修复、历史真实运行|不算自主发现，保持历史代码|
|s24_learning_probe|模型学习人工STRIP_COMMENTS/KEEP的条件|不是自动生成算法；不输入旧双算子代码|
|runtime/llm_client|OpenRouter兼容客户端有4次自动重试|不复用重试行为；保持GPT无重试独立发送器及授权/预算绑定|
|code_math/runner|数学gold反馈存在泄漏风险|本轮不接入数学；仅stdio代码任务|

实现次序：可信准入 → 三态机制schema → 复用LearningLoop/LearningPipeline的真实Worker验证 → 默认关闭task_solver候选程序接口 → 门控及后续题调用 → 零API验收与P3草案。

证据等级：现有代码执行能力属于REAL_WORKER_VERIFIED（Mock源码）；历史DeepSeek假设属于REAL_MODEL_GENERATED，但没有真实生成源码。不得将二者合并为真实学习成功。
