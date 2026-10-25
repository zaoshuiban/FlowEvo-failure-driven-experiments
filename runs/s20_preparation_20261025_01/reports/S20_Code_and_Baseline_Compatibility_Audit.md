# S20 源码与基线兼容性审查

日期：2026-10-25。基线提交：`2614b9274efcc8c4b0ff482dcdeba9bb9d5c245a`。本轮真实模型请求为0，所有发送器联调均为模拟响应；公开数据HTTP下载不计作模型请求。

## 最小改动及其原因

1. `scripts/run_learning_stream.py` 新增绝对批次号 `--stop-after-batch N`。每个批次完成题间学习、保存Runner后写入持久 `BATCH_FINALIZED`；恢复时跳过已完成批次。旧入口对已完成任务会再次调用boundary，因此仅增加一个循环break不足以保证恢复不重复调度。中间暂停不写ONLINE_LOCKED，最后一批完成才锁定。
2. `repair_choice_hook.py` 仅追加实际介入前的公开任务投影与预算快照。动作、准入、额度、暂停和Controller逻辑没有改变。
3. `scripts/s20_action_pair_preflight.py` 根据实际Hook前缀重建固定Generic与学习动作的最终wire，使用同一 `action_messages`、temperature=0和Limits。它没有模型发送入口，拒绝非法动作、变更源码哈希及不匹配Generic。显式只读before字段，忽略future/proposed/final字段。

`production.patch`保存两处生产改动；新文件另由`source_dependencies.json`冻结。原S19-G2计划没有被覆盖，因依赖变化其旧哈希不能用于新工作区开跑。新计划如下：

- G: `s20_taco80_g_20261025_01`，协议 `a54e002cc73d0ba51e360c2b6d7f580128199f9204f327fcd7b298f5f449d8f9`。
- M: `s20_taco80_m_20261025_01`，协议 `f7a8c5504cfcc9c1ca3a1c9d15d5101dbd2545d778e715658d3977c5acb7d830`。
- F: `s20_taco80_f_20261025_01`，协议 `137dfde0cb68c6186553d0dd20f324e78685f43e66162ee10110c83ed2ea4523`。

## 已完成验收

- 原冻结清单在修改前复核：80题、1137在线、960封存；参考源码哈希、三臂预算、旧20题159文件保持一致。
- FlowEvo核心测试212项通过；S19脚本回归28项通过；S20新增3项通过，覆盖G/M/F批次恢复、已完成请求不重发、manifest不匹配拒绝、非法暂停参数以及配对请求隔离。
- 真实Linux Worker安全资源探针12/12通过；模拟模型＋真实Worker完成生成、来源修复、跨题试用、公开退化暂停、缺失程序、编译错误、正常和错误程序检查。原有Shadow/Experimental与未知请求保护未放松。
- `worker_batch_acceptance.json`：真实Controller在第2批暂停并恢复，已完成发送计数不变；2条实际Hook前缀重建的学习wire与当时发送wire哈希一致。此处“真实”指Controller/Worker执行，**不指真实模型效果**。
- 新增快照首次复核暴露了PublicTaskView已投影样例不含visibility标签的问题；配对工具现直接校验投影格式并重建对象，不再次投影丢样例。早期失败日志保留，最终验收单独记录。

## 仍然存在的比较边界

G/M使用原生五阶段恢复及各自成功Skill库；F另有受限Hook。系统级分数差异包含调用时机、请求内容和学习成本，不能直接归因于规则表示。动作级配对工具只证明相同状态可构建请求，尚未进行付费干预比较。

Generic对NO_ENTRY等状态可能选择当前A/B权限不允许的动作；工具将明确拒绝这类配对，不能把不合法分支强行执行。未来配对必须冻结合法适用范围、独立预算和相同回退续跑协议。

本轮未重写Controller、EvidenceBundle、调度、代际管理，未恢复任何历史Suspended版本。
