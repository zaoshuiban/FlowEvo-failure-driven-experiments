# ALFWorld full_library 零 API 验收报告

状态为 PASS。24 项单元和回归测试通过，其中 9 项针对本次成功学习接入，另完成真实 ALFWorld 历史轨迹回放。付费调用为 0。

| 检查 | 实际证据 |
| --- | --- |
| 成功编译、入库及跨局持久化 | 7 个已曝光双物体游戏，6 在线加 1 锁库。第 1 局原生动态，赢后提交 L1/L2。第 2 局检索此前库并实际发送含 L2 的请求。第 3 局后 L3 出现，第 4 局 L2/L3 同时注入。 |
| 实际使用而非仅检索 | 132 次动作 Mock 请求中，93 次送达 L2，60 次送达 L3。共有 5 局 exemplar_guided、2 局 pure_dynamic。双物体 L1 动作为 0，符合原版。另在普通放置的单元夹具中验证了 L1 动作直接执行时模型零调用，以及直接执行失败后将最新观察交给原生回退。 |
| 20% holdout、治理与统计 | 真实回放第 6 局触发 holdout，L2/L3 注入均为零。单元夹具让原生 ContrastiveEval 达到其负迁移条件，观察到注入压制；L1 效用不足后周期审计压制。正常失败保留在 L3 轨迹统计。 |
| 同题隔离与冻结评价 | 首局动作不含自身编译内容。评价局仍有 L2/L3，评价前后库 SHA 相同，评价编译 0 次。冻结库包含治理及 RNG 状态。新增回归断言评价不抽取 holdout、不消耗 RNG、不更新库；真实环境回放评价局关闭 holdout 且有 L2/L3 注入。 |
| 中断恢复 | 第 1 局动作及编译已结算但题间尚未提交时注入中断，恢复沿用原响应并提交一次；随后重跑已完成入口也没有新增请求。另测试了只有已结算原始响应、缺少解析回执时的安全恢复。 |
| 异常和计分 | Mock UNKNOWN、截断、环境异常及预算耗尽均未提交为成功或有效技能。done=true、won=false 的轨迹无成功编译。真实回放的 won 与宿主动作回执一致。 |
| 数据预检 | 保留原序的 16 局校准及六类混合随机、全部在线的 120 局正式候选均通过重算抽样、源码、依赖、路径和曝光校验。计划、实际运行和已有回放账本相互隔离。 |

## 120 局全在线和中断恢复的专项证据

同一个运行入口在 120 局 Mock 环境中从空库启动。第 1 局完成并提交后，第 2 局检索到 L2。第 91 局的动作和 L2 编译已结算，但尚未写题间提交时注入中断，此时账本为 182 次。恢复沿用原响应，完成第 91—120 局并继续注入、编译、统计和审计。

- 120 条题间记录全部为在线提交，没有 `BANK_FROZEN` 事件或冻结库文件。刻意安排第 95 局 `done=true, won=false`，该局写入原生失败统计，未执行成功编译。
- 整个夹具 120 次动作请求、119 次编译，账本与发送计数均为 239，合计 11,950 Mock Token。最后 20 局产生 20 次 L2 指南，第 120 局完成 L2 编译并提交最终库。
- 全部 holdout 决策和最终 RNG 与不间断的种子 1337 序列一致。物化 6 个 20 局快照，最终库 SHA 与第 120 局提交一致。删除派生的最终库文件后恢复可重建它，发送数仍为 239。
- Mock 动作请求验证未出现未来题面标记或专家字段。实际运行加载单个当前游戏，历史回放另核查真实 ALFWorld 状态与回执。

这些数字来自工程夹具，不代表正式 120 局成绩、技能效果或真实消费。

真实环境回放完成 7/7，动作 132 次、编译 6 次，Mock 总 Token 6,900，恢复新增重复请求 0。动作来源是历史成功轨迹，成功率只验证复现回执，不能用作真实新模型或技能收益估计。

完整零 API 账本在 `~/.local/share/flowevo/alfworld_success_acceptance_20261109_03/`。其中 `budget.jsonl`、`episodes.jsonl`、`frozen_bank.json` 和 `ACCEPTANCE.json` 的摘要见本目录 `public_audit_summary.json`。历史专家计划未进入测试轨迹或 Mock 请求，回放沿用已归档公开动作。两份真实模型方案没有预算账本或授权收据。

复验命令在仓库根目录执行，回放指定新的输出目录。

```bash
export PYTHONPATH="FlowEvo/src:scripts"
py="$HOME/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python"
"$py" -m unittest scripts/test_alfworld_success_baseline.py \
  scripts/test_alfworld_audited_baseline.py scripts/test_alfworld_failure_learning.py -v
"$py" scripts/accept_alfworld_success_baseline.py \
  --data "$HOME/.local/share/flowevo/alfworld_baseline_20261107/data" \
  --output "$HOME/.local/share/flowevo/alfworld_success_acceptance_recheck_01"
```

真实校准报告和正式复现报告尚未产生。工程通过说明成功经验的确进入后续求解路径，真实模型下的采用、成功率和相对收益仍待授权后的结果。
