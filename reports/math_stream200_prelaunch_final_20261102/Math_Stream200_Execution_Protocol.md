# Math Stream200 执行协议

本次只完成启动准备及旧题真实 smoke。正式200题未启动；不得用旧题 smoke 代替正式实验。数据不重选、不改序。最终资格以本目录 Prelaunch_Final 为准。

## 工作树核对与复用

基准 Git HEAD 为 `10e85deeb98eb00e08c354c71376be475e28f5ed`，工作树存在大量本轮之前的未提交文件。执行冻结采用实际文件 SHA256，而非假定 HEAD 等于运行源码。新快照在 `runs/math_stream200_preparation_20261102_02/frozen_source`，清单在同目录 `formal_plan.json`。旧付费源码另留于 preparation_01；没有覆盖旧实验。

|组件|决定|本轮连接|
|---|---|---|
|code_math.no_gold.NoGoldMathController|复用|增加显式 durable resume，默认旧入口行为不变|
|PrivateMathScorer / grade_continuation|复用与显式严格模式|统一 finish_reason 与可信状态；历史评分不重算|
|run_math_auto100.py|保留|一次发现、一次生成、冻结测试，不能直接当持续流|
|run_learning_stream.py / S19 LearningStream|审查保留|面向 repair-choice-json-v2 编程工作流，不强行套用数学接口|
|SharedTransport / PersistentBudget / EvidenceStore|直接复用|每 arm / 窗口独立账户及不可重复消费标识|
|SplitRunner / FrozenLinuxBackend|直接复用|生成源码实际交给既有 Linux Worker|
|VersionGate / UnifiedMathRouter / MathPublicationGate|直接复用|已有资格、质量、冲突、三 Gate 与未来授权|
|math_stream.py|新增薄调度层|四组顺序、锁定/评分屏障、窗口、恢复和 R 额度|
|math_stream_learning.py|新增连接层|已有 BoundedCompiler 生成、工程修订、来源诊断及发布协调|
|run_math_stream200.py|新增准备入口|prepare / smoke / summary；没有自动正式200启动动作|

## 固定运行规则

三类200题依旧为代数67、数论66、组合概率67；10个窗口，每窗口20题。第20至180题结束时最多9次学习机会；第200题后不再为已结束的流生成工具。各组从独立空库开始，连续保留状态，不逐批冷启动。

G/T/F/R 均按同一 task_id 顺序；每题组执行顺序循环轮换以缓解供应商时间效应。每题先完成四组全部 `ANSWER_LOCKED`，再允许任一组 `PRIVATE_SCORED`。`WINDOW_COMPLETED` 提交该窗口所覆盖任务，任务不能提前参与学习。求解统一 deepseek-flash、temperature=0、固定两次调用（初解+无条件自审）、单次4096输出/32768保守输入上界。没有隐藏评分决定重试或选答案。

所有完整请求、原始响应、finish_reason、usage、锁定 SHA、Worker记录均持久保存。模型通常只返回模型别名，文档快照记载 DeepSeek-V4.1-Flash-1017；不能将文档版本当作供应商签名的内部部署证明。

## 评分与可见性

只有完整、明确、可比较的标量答案可判 CONFIRMED_CORRECT / CONFIRMED_WRONG；length→TRUNCATED，表达式等无法可靠比较→UNVERIFIED。请求故障单独记基础设施状态并停止，不伪造成数学错误。学习器只获得锁定后允许公开的错误轨迹及 correct=false；无 gold、官方 solution、答案差异或私有评分器推理。

隔离属于宿主信任边界：私有评分与公开投影由同一可信宿主控制，并非不同硬件进程。Worker不挂载评分数据，模型请求采用字段白名单。模型自产测试或答案不作为独立Oracle。

## 恢复与停止

已锁定任务、完整窗口及收到响应且结清usage的请求可回放，不再次发送。并发进程受文件锁排斥。任何未决请求/账本、SEND_UNKNOWN、Worker故障、冻结哈希漂移、权限或泄漏异常、硬上限耗尽均停止。验证中断不得自动重复消耗Gate。无失败、无候选、格式拒绝但已结算、Shadow无资格和零收益均是正常研究结果。

第一次 smoke 的HTTP400保留原账本；第二次是显式的新工程复验，非旧请求恢复。详见 HTTP400_Audit.json。
