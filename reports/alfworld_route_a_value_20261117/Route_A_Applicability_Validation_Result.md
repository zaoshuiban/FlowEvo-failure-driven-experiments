# 冻结 Route A：扩大独立适用性验证结果

本轮实际执行新的适用性验证；没有重新生成/修改门控或恢复代码，没有付费模型请求，没有运行G与G＋Route A在线比较。

协议SHA：`99ea2464eaa97d5d6273b5d2b2758867ef246bb0d3de613d15e13941a80ef370`；检查点SHA：`f9915852bd1686ab73ceb15b8509119756296352ba82db8652c420195255ff4a`。

48局冻结游戏中，25局形成可评价检查点，共61条记录、43个物理组。游戏、轨迹及任务组与全部已知来源隔离；场景已见，不宣称跨未见场景。参考探针和评分数据不进入候选。

| 标签 | 记录/游戏 | 门控返回 | 实际介入 | 完整正例修复 | 错误/无证据恢复 |
|---|---|---|---:|---:|---:|
| MATCH | 34/25 | {'MATCH': 34} | 34 | 34 | 0 |
| DECLINE | 9/9 | {'DECLINE': 9} | 0 | 0 | 0 |
| UNKNOWN | 18/18 | {'UNKNOWN': 15, 'MATCH': 3} | 3 | 0 | 3 |

UNKNOWN即使物理世界实际获胜，也不能据此反向标为MATCH。同一物理状态的完整/裁剪历史共享分组；未知标签不是根据历史长度猜测。打开合法不等于最终投递适用。

正例完整修复 34/34；所有入选正例都完整修复的游戏 25/25。有错误/无证据恢复的控制游戏 3/18。无可评价检查点的游戏保留NOT_EVALUABLE，不算候选失败。

| 正例任务类型 | 记录 | 游戏 | 完整修复 |
|---|---:|---:|---:|
| pick_and_place_simple | 8 | 5 | 8 |
| pick_clean_then_place_in_recep | 12 | 8 | 12 |
| pick_heat_then_place_in_recep | 6 | 5 | 6 |
| pick_cool_then_place_in_recep | 8 | 7 | 8 |

## 冻结准入判定

- CAPABILITY_READY：通过。
- SAFETY_READY：未通过。
- COVERAGE_READY：通过。
- ENGINEERING_READY：通过。

在线阶段：NO-GO；不得绕过失败条件启动G对照。

门槛在结果之前固定：12正例游戏、12控制游戏、DECLINE/UNKNOWN各6游戏；6正例场景、3容器、3题型；正例游戏全部检查点修复比例≥80%；零已确认错误/无证据介入、零错误与未解决安全状态。全部候选保持Shadow，没有伪造发布Gate。

零错误时控制游戏的单侧95%二项错误率上界：NOT_APPLICABLE（观察到错误或零分母）。共享场景和受控构造带来相关性，此数不构成全面安全保证。

## 异常记录

- `b5/alf-5ebf0966c19b66f207e8/READY/view1`，UNKNOWN：目标“put a hot cup in cabinet.”；门控MATCH；实际动作['open cabinet 1', 'move cup 1 to cabinet 1']；won=True。
- `b5/alf-c9760a0fc2d029544048/READY/view1`，UNKNOWN：目标“put a hot apple in fridge.”；门控MATCH；实际动作['open fridge 1', 'move apple 2 to fridge 1']；won=True。
- `b5/alf-c0a53ee3f9bd14db124c/READY/view1`，UNKNOWN：目标“put a hot mug in cabinet.”；门控MATCH；实际动作['open cabinet 1', 'move mug 1 to cabinet 1']；won=True。

## 成本及结论边界

模型请求/Token/API费均0。Worker 137次，回执耗时合计41.601秒；采集/参考重放4852环境步，候选评价816步。历史技能获取成本保留在原账本，未视为零；主机执行时间未转换为货币。

35项零API工程测试已通过，覆盖确定性抽样、角色隔离、预算/未知阻断、版本绑定、按游戏计数、门槛失败、原生回退等价性。真实Linux Worker与TextWorld运行记录单独保存，不把Mock测试当成学习成绩。

后续60局在线清单已在验证成绩出现前固定，六类任务、60不同任务组，与48局验证集隔离，未交互。要检验完整任务增益，仍须在安全条件满足后按同题同序重新运行G及G＋Route A，不能用旧113/120相减。冻结技能对照只回答已学能力的运行价值，不能单独证明失败信息的独立因果收益。

原始证据：私有Run中的protocol.json、Checkpoint_Freeze.json、checkpoints.private.json、outcomes/、live/、worker.jsonl、environment.jsonl及result.json。公开统计见public_audit_summary.json。

## 只读根因审查：目标属性未转成执行前提

三个异常目标分别是hot cup、hot apple、hot mug。冻结门控的`_strip_adj()`会剥离hot等对象修饰词，从而成功绑定物体；但是`_processing_required()`只检索heat/cool/clean三个动词，没有把hot转成“需要加热”的前提。于是热处理要求在对象归一化后丢失，门控跳过可见加热回执检查。这个解释来自冻结源码和真实回执，不是再次调用模型的推测。

三条UNKNOWN与各自MATCH具有相同物理状态，但公开历史经过事前冻结的等长子序列投影，缺少加热完成证据。三条分支都实际won；不能把它们说成已经观察到的环境任务失败或已造成负迁移。观察到的是确定的适用性协议违反：在证据不足时承诺最终投递恢复。原生完整历史中的发生频率尚未测量，也不能据这三条直接估计线上损害率。

这也解释了为什么B5的9/9不足以宣布成熟：B5没有可评价的加热正例，本轮有6条加热正例及5条加热UNKNOWN，新增覆盖暴露了此前未触达的分支。恢复程序本身在本轮全部34条可信正例成功，不需要据此重新生成恢复动作算法。

本次不改代码补hot规则，不删热处理记录、不放宽UNKNOWN要求，也不把同批已曝光题再当作新的确认集。若下一步修订，应建立新的门控版本和新的独立验证；S0继续冻结。只有随后真正满足准入条件，才能启动已经保留的60局在线比较。

## 完成态与未启动阶段

已实际验证完成态重入：9个关键账本/结果文件哈希完全不变，零新增请求、Worker或环境动作，零重复计费。原生120局最终技能库及治理快照哈希未变化。所有48局均已成为曝光资料，包括未形成有效检查点的23局；不得再称为未见验证游戏。

60局在线池只有冻结元数据，没有环境reset或模型求解；没有生成付费授权。当前无法报告G对G＋Route A的正确率或成本改善，不能声称已证明整个失败学习系统对原生FlowEvo有增益。当前实证是：冻结恢复能力能迁移，但门控存在一个具体且可复查的安全阻断。

## 逐游戏概要

无检查点为NOT_EVALUABLE；游戏内多个视图不增加独立游戏数。

| 游戏 | 题型/容器/场景 | MATCH完整修复 | DECLINE错误 | UNKNOWN无证据介入 |
|---|---|---:|---:|---:|
| alf-78942a0e6581efed8f6e | pick_cool_then_place_in_recep/Microwave/15 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-58f20609efa2e2019bef | pick_clean_then_place_in_recep/Cabinet/13 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-e9b00c7b588d003d573e | pick_heat_then_place_in_recep/Fridge/24 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-d6c20051fc85e9bcc964 | pick_and_place_simple/Drawer/409 | 2/2 | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-c960b67604cd4345c9f1 | pick_and_place_simple/Safe/323 | 1/1 | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-1bcfccd955e18c463e47 | pick_clean_then_place_in_recep/Fridge/18 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-6d77274cdb9070b4f7e2 | pick_cool_then_place_in_recep/Cabinet/19 | 2/2 | NOT_EVALUABLE | 0/1 |
| alf-93029a5940f33367a8cc | pick_clean_then_place_in_recep/Drawer/30 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-3a5a2b3822da40a84cfc | pick_cool_then_place_in_recep/Microwave/12 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-5ebf0966c19b66f207e8 | pick_heat_then_place_in_recep/Cabinet/25 | 1/1 | 0/1 | 1/1 |
| alf-443582b5b1a78271082e | pick_and_place_simple/Drawer/302 | 2/2 | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-b5adbc2858d16603c1cb | pick_heat_then_place_in_recep/Fridge/16 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-00882c8d1706f3122184 | pick_cool_then_place_in_recep/Microwave/2 | 1/1 | 0/1 | 0/1 |
| alf-378c76b13a41d6aadff3 | pick_clean_then_place_in_recep/Cabinet/1 | 1/1 | 0/1 | 0/1 |
| alf-e298f18aeef0d500bf94 | pick_heat_then_place_in_recep/Fridge/17 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-a0c2d30e908ba33eb912 | pick_and_place_simple/Drawer/8 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-ee3973a466d4d5a8c3cf | pick_cool_then_place_in_recep/Microwave/20 | 1/1 | 0/1 | 0/1 |
| alf-790b6f6fefeac9d1c49a | pick_heat_then_place_in_recep/Cabinet/26 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-31672c43e920ef4a7e55 | pick_clean_then_place_in_recep/Drawer/27 | 2/2 | NOT_EVALUABLE | 0/1 |
| alf-04f6c88d74036da65fac | pick_and_place_simple/Fridge/7 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-dc0d6fb2f484be3c47ea | pick_clean_then_place_in_recep/Microwave/6 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-1feb176b270b99fbf25b | pick_cool_then_place_in_recep/Cabinet/5 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-228b377ea782b33efaa9 | pick_heat_then_place_in_recep/Fridge/22 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-1086f8b6c5294719aa98 | pick_and_place_simple/Drawer/409 | 2/2 | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-fc6cac9aa33ec81226b5 | pick_clean_then_place_in_recep/Microwave/23 | 1/1 | NOT_EVALUABLE | 0/1 |
| alf-ea917be742c4ab4087f3 | pick_heat_then_place_in_recep/Fridge/14 | 1/1 | 0/1 | 0/1 |
| alf-e4bbf903ac2edf4a2755 | pick_cool_then_place_in_recep/Microwave/30 | 1/1 | NOT_EVALUABLE | 0/1 |
| alf-e57150e3ae526335f252 | pick_and_place_simple/Cabinet/17 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-9e9f8e8cc589b60b15e5 | pick_clean_then_place_in_recep/Drawer/4 | 2/2 | NOT_EVALUABLE | 0/1 |
| alf-9733458f0cdb10342e39 | pick_heat_then_place_in_recep/Cabinet/6 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-b9017eebf2fc78d83a7a | pick_and_place_simple/Fridge/16 | 1/1 | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-c3e32de307294d55b658 | pick_cool_then_place_in_recep/Microwave/5 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-01de45479f9a18439ccf | pick_clean_then_place_in_recep/Drawer/415 | 2/2 | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-9c240ec70c15b83ee9c1 | pick_heat_then_place_in_recep/Fridge/18 | 1/1 | NOT_EVALUABLE | 0/1 |
| alf-0599e1c41d6f2dc870ab | pick_cool_then_place_in_recep/Cabinet/26 | 1/1 | 0/1 | 0/1 |
| alf-967de26e54522ddc0397 | pick_and_place_simple/Microwave/13 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-99301122c6409ba69fb2 | pick_clean_then_place_in_recep/Drawer/410 | 2/2 | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-c9760a0fc2d029544048 | pick_heat_then_place_in_recep/Fridge/25 | 1/1 | 0/1 | 1/1 |
| alf-5e0e0fb0086c241b3533 | pick_cool_then_place_in_recep/Microwave/12 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-68fce58679eb60fe7a78 | pick_and_place_simple/Cabinet/5 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-7e2d685a68c6b32e8277 | pick_clean_then_place_in_recep/Drawer/11 | 1/1 | 0/1 | 0/1 |
| alf-c0a53ee3f9bd14db124c | pick_heat_then_place_in_recep/Cabinet/20 | 2/2 | NOT_EVALUABLE | 1/1 |
| alf-13a7899168fd4ad1a4ce | pick_cool_then_place_in_recep/Microwave/7 | 1/1 | NOT_EVALUABLE | 0/1 |
| alf-bd5e5b8a58b8f45a84cc | pick_and_place_simple/Drawer/12 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-793c1a6ed9977cbac72e | pick_clean_then_place_in_recep/Fridge/1 | 1/1 | NOT_EVALUABLE | 0/1 |
| alf-81b18fcafbe24da65a48 | pick_cool_then_place_in_recep/Cabinet/22 | 1/1 | 0/1 | 0/1 |
| alf-6a502ffeedf9bdcd2027 | pick_heat_then_place_in_recep/Fridge/19 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
| alf-a6639c6ce503c58a7955 | pick_and_place_simple/Microwave/8 | NOT_EVALUABLE | NOT_EVALUABLE | NOT_EVALUABLE |
