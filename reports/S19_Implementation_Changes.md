# S19最小闭环改造

## 已实现

- `failure_evo/symptom_learning.py`：在FailureEvidenceStore之上按公开症状分组；单独保存未认证的恢复假设、版本、来源、支持/反例、不同任务数、谱系组、动作和关联制品。追加更新不覆盖历史；撤销事实从后续调度资格移除。
- `compile_queue.py::schedule_hypotheses`：复用队列日志，输出SKIP/GENERATE/REVISE；单见证可调度；没有新证据不重编译；最多两族同时进入作业；启动标记先于模型调用，未知状态不自动重试。这里数量是资源限制，不是晋级标准。
- `scripts/run_learning_stream.py`：薄编排调用现有ExperimentRunner。题末记录可信事实/公开源包，批边界自动生成JSON规则（不另作规格API，0次规格符合最多1次上限）、最多一次格式修订、保存Shadow、调用现有独立验证预算及Judge做来源评估。只有来源收益、安全声明、未来任务范围和明确试用授权齐全才调用RuleMemory.authorize。M独立使用已有memory_update；G不学习。
- `run_workflow_v2.py`：显式resume校验同一计划、恢复持久预算、请求审计和成功CodeSkillLibrary；新增validation账本通道，未改变求解预算定义。原入口默认仍拒绝覆盖既有目录。
- `repair_choice_hook.py`、`RuleMemory.finish`：保存执行前后公开反馈、实际模型次数/Token、经过时间和回退标志；相同公开用例集合出现原先通过用例退化时自动暂停；新公开事实回流到关联假设反例。模型算法错误不自动等于算子因果伤害；这里仅实施保守治理阻断。
- `failure_events.py`：未知运行时异常名称不能仅凭字符串形成可信异常事实。

## 权限与表示边界

仅repair-choice-json-v1两个动作。生成代码不会自行授权。Shadow不是experimental；来源失败/局部改善不放行。无成熟晋级阈值，未改变旧Python注册表。连续入口只收公开任务清单，拒绝额外字段；外部最终评分没有学习入口。

源验证只尝试规则提议一次动作，不花剩余额度凑成功；无法适用或验证失败保留Shadow。功能失败的新证据会形成新作业，不在当前作业无限重试。当前一次修订针对输出协议错误，尚未实现来源功能诊断在同一作业内自动修订；明确保留此限制。

## 可运行入口

`python scripts/run_learning_stream.py --plan PLAN --authorization AUTH --tasks PUBLIC_TASKS [--resume]`

须冻结tasks_sha256、arm、batch_size、start_mode=cold、预算及protocol_hash；每臂使用独立run_id与目录。计划中求解、学习、来源验证分别持久化。此命令未在本轮以真实API执行。warm-start显式拒绝，不能静默借用历史状态。

## 恢复与安全限制

正常题末恢复通过Mock验收；题中断安全阻断，尚无自动逐阶段续跑。学习请求发出后的中断不自动重做；不把未知费用计零。当前成功库保存是普通JSON文件写入，不是事务快照；极端断电的部分写入将失败关闭。CLI已绑定安全声明与独立报告哈希；真实Worker新增路径联调仍阻断正式S19。详见Gap Audit。

历史S1–S18结果、预算、原始响应和其保存哈希未编辑。修改当前源码会使旧依赖校验不再匹配；旧实验应从cc965f83及其历史提交重现，不应重写旧哈希来“通过”。本轮未提交或推送GitHub。
