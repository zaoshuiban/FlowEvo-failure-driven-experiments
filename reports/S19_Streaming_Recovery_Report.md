# S19 连续任务与学习作业恢复

## 恢复原则

仍使用原 PersistentBudget、SharedTransport、EvidenceStore 与注册表；没有新增恢复框架或重写 Controller。新入口必须指定相同 Run ID、计划哈希、任务清单哈希、arm、批次大小与源码依赖；不同配置不能接续旧 Run。

请求在最终预检通过后预留。COMPLETED 响应和 UNKNOWN 审计在 transport 返回调用方前持久化。状态 JSON 使用原子替换，追加日志和账本沿用原校验；损坏或不完整文件停止，不静默修复为新的独立样本。

## 学习作业状态

| 持久状态 | 重启行为 |
| --- | --- |
| JOB_SCHEDULED，未开始 | 可重新得到同一确定性 job ID；不应产生模型费用 |
| JOB_STARTED，无完成凭据 | 检查账本；无发送可继续；存在 pending/unknown 则停止 |
| RESPONSE_PERSISTED | 对照相同消息哈希和 COMPLETED 记录恢复响应，不再次生成 |
| CANDIDATE_REGISTERED | 规则登记去重；继续来源评估，不重发生成请求 |
| SOURCE_ASSESSED | 复用原报告；补齐未完成的登记/功能反馈，不重发验证请求 |
| JOB_FINISHED | 跳过；已消耗诊断不会自行启动下一轮 |
| ABORTED | 预检或预算阻断归档；不自动扩大预算 |
| JOB_UNKNOWN | 保留账本占用，停止整个运行，等待可信结算与人工核对 |

状态事件分布在 `hypotheses.jsonl`、`stream.jsonl`；作业文件保存 messages、response、state，实际请求审计和持久预算单独保留。不存在仅因有一个 response.json 就允许继续的捷径：它必须与已结算审计一致。

已注入三个真实中断位置：RESPONSE_PERSISTED、CANDIDATE_REGISTERED、SOURCE_ASSESSED。每种情况下重启后的学习和来源模型模拟调用总数均保持预期的 2/2，没有重复发送。恢复到合法响应后只进行尚未完成的本地处理或 Worker 评分。另有篡改保存响应测试：立即停止，发送次数不增加。

如果响应已经从网络返回，但进程在完整可信结算前退出，不能确定费用；本轮仍 fail-closed。没有实现自动向供应商核账或未知请求退款。若本地 Worker 评分完成但报告未落盘，恢复可能重做本地评分，这部分真实工具开销继续入账，不假装免费。

## 任务与三臂状态

已完成任务恢复成功 Skill 库、文本经验、失败事件、假设、规则版本/权限及三个预算通道。任务成功库先保存，再写 TASK_FINALIZED；中途留有 TASK_STARTED 而没有完成标记时，**不重跑该题**。

G/M/F 使用独立目录和 Manifest；跨 arm 复用同一 stream 会被拒绝。没有把 F 的未来结果传给 M 或 G。每题规则可见集合是开始时快照，试用预留时重新检查暂停；题间新版本不能回到来源题使用。

M 更新另记录 MEMORY_STARTED/MEMORY_FINISHED、更新前文本、新增证据和重复证据。更新响应已结算、但记忆快照尚未保存时，使用相同消息与缓存响应继续验证，不重发。该恢复也有模拟故障测试。

## 预算与费用

solve、learning、validation 三本账各自恢复。每个来源评估还恢复原检查点的逻辑任务预算；它约束动作合法性，但不把离线来源验证费用算回已结束任务的在线费用。实际验证费用独立累计。

未知请求的保守预留不能称为实付，未收到可信用量不能记零。模型 API 当前实际调用为0；工程账本的合成 Token/费用只验证扣费行为。Docker 本地耗时记录，货币成本未知。

本轮没有提供逐 Token、逐 Controller stage 的题中恢复。这个限制是显式停止边界，不是将中断后重跑的两条轨迹混成一次样本。
