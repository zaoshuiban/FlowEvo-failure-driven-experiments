# v2.1 闭环实现进度

本轮代码增量在 `feat/failure-learning-v2` 工作区，尚未提交或推送。新增外部模型调用为0。

## 已接入

- `LearningLoop.run_pipeline` 从单个已完成任务流的待编译作业读取公开证据，进入 `LearningPipeline`。
- 自动规格、三个候选、可选各一次修订、D_des评分、确定性平局处理、冻结一个赢家、独立D_gate/D_reg；生成请求不含门控和回归材料。
- 每个步骤先记STARTED再调用能力，成功记DONE；恢复时只复用输入哈希一致的完成记录。失败或中断需宿主处理，不自动重试。协议、赢家和门控分片绑定持久记录。
- 发现、设计、门控、回归来源组隔离，分片ID须不同。门控失败保持Shadow；通过仅返回ready_for_experimental_review，不能直接执行或自动Active。
- Operator公开验证增加passed/failed/unavailable；无可靠测试时保留候选、结构状态和不可用原因，恢复原生流程。

## 使用接口

宿主构造LearningPipeline(path, compiler, evaluation_budget, design_checker, gate_checker)，再调用LearningLoop.run_pipeline。传入design/gate/regression冻结清单，各含shard_id和source_groups；每次只分配一个族，避免多族共享一次性门控分片。

检查器是可信宿主接口 `(code, dataset_manifest, timeout_seconds)`，返回eligible布尔值和预注册的有限score，可附开发反馈。检查器必须在隔离Worker中验证实际源码、动作/资源契约和任务表现；静态存在repair_operator函数只是预筛，不能代表源码已通过执行验证。编译预算与评价工具预算分开。含模型调用的评价器仍须自行经过宿主模型预算代理，当前测试评价器没有模型调用。

## 验证

Python 3.9和3.11均99项测试通过（此前93项＋6项流程测试）。新增测试覆盖完整流程/恢复不重复调用、失败不自动重试、协议漂移、来源污染、门控拒绝及三类公开验证。48题固定响应兼容性与1,112个冻结制品校验通过。

工程测试用注入的确定性生成器和检查器，不是真实API生成或收益验证。

## 尚待完成

- 目标服务器入口/模型/成功库/提取器身份与Linux真实Worker验收。
- 实际模型后端、任务数据清单、具有语义依据的设计评分与独立门控检查器，以及完整费用上限。
- 将独立评价输出形成既有注册表要求的配对证据并授权experimental；当前pipeline结果不替代该证据文件。
- 自动生成之后在独立检查点受控使用及B/G/M/F比较，均未运行。
- 持久化日志保证同一已记录步骤不重试，但Budget对象仍为内存状态；进程重启后新步骤的剩余总额度须由宿主从账本恢复。不能使用新建满额Budget继续正式实验。这是进入真实预算运行前的阻断项。

当前改动使组件可以自动完成生成与验证编排，但不能据此宣称真实Operator学习或在线收益已验证。
