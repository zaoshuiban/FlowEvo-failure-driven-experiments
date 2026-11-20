# Route A：修订门控的48局独立检查点确认

**状态：CONFIRMATION_NO_GO。** 候选在新游戏执行前冻结，未根据结果修改、重采样或重新生成。本轮没有付费API，也没有G在线比较。

门控SHA：`32feddc3d43c357bf0e84235d3b9d89e2822ca7b5efe06c66b0c74c20f816553`；恢复SHA：`233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37`。协议：`df74aca16893b79ad7463b56fb7a82f064f78505a0709dd588ff56259695aff5`；检查点：`c00bea55b462b3fa9ca2a70b029c02ec9082af97ab9bfa29dcbad920e52abb22`。

## 样本与来源

原封存48个独立任务组全部按原序采集，20个游戏形成86条可信记录、46个物理状态组。其他游戏没有可评分检查点，保留排除原因，不算候选失败。

简单放置1局、清洗16局、加热16局、冷却15局，22场景。样本依据元数据平衡与SHA顺序冻结，不依据候选表现。与已知来源、B5、旧48局和在线60局按游戏/轨迹/任务组隔离；场景可已见，不能声称未见场景泛化。

这是受控构造的真实失败检查点，非原生Agent自发失败。可信标签和参考回放在候选执行前冻结；参考探针、评分和未来轨迹不进入候选。UNKNOWN包含明示裁剪的真实历史，同状态的视图共享物理组。

## 实际结果

| 标签 | 记录/游戏 | 门控输出 | 实际介入 | 完整正例修复 | 错误/无证据介入 |
|---|---|---|---:|---:|---:|
| MATCH | 52/20 | {'MATCH': 52} | 52 | 52 | 0 |
| DECLINE | 14/14 | {'DECLINE': 14} | 0 | 0 | 0 |
| UNKNOWN | 20/20 | {'UNKNOWN': 20} | 0 | 0 | 0 |

全部入选正例均完整修复的游戏：20/20。存在错误/无证据恢复的控制游戏：0/20。接口/计算错误0；未解决安全事件0。

| 正例任务类型 | 完整修复/记录 | 游戏数 |
|---|---:|---:|
| pick_clean_then_place_in_recep | 20/20 | 7 |
| pick_cool_then_place_in_recep | 13/13 | 5 |
| pick_heat_then_place_in_recep | 19/19 | 8 |

| 正例容器 | 完整修复/记录 | 游戏数 |
|---|---:|---:|
| Cabinet | 20/20 | 7 |
| Drawer | 18/18 | 6 |
| Fridge | 10/10 | 5 |
| Microwave | 4/4 | 2 |

## 冻结门槛与覆盖缺口

- CAPABILITY_READY：True。
- SAFETY_READY：True。
- COVERAGE_READY：True。
- additional_coverage_ready：False。

阶段冲突可信负例游戏：0/至少3；实例冲突可信负例游戏：0/至少3。

原门槛保留：至少12正例游戏、12控制游戏，DECLINE/UNKNOWN各6游戏，正例覆盖6场景/3容器/3任务类型；至少80%正例游戏的全部检查点完整修复；零确认安全错误和运行错误。额外阶段/实例覆盖不能由旧工程夹具替代。

未处理状态下打开可能只是准备动作；类别目标不能自动确定某一个实例。没有可审查证据的阶段/实例标签保持UNVERIFIED，不以不获胜、动作合法或采集mode名称强行标负。

未决记录mode统计：`{'TARGET_CONFLICT': 3, 'UNPROCESSED': 18}`。全部排除原因：`{'NO_OPENABLE_PUBLIC_INSTANCE_WITHIN_BUDGET': 13, 'A different destination may allow useful intermediate placement; positive witness and failed retry required, no-win alone insufficient.': 3, 'Processing absent: opening may be preparation; phase preference is not a proven negative.': 18, 'PUBLIC_SEARCH_BUDGET': 28}`。

在已观察到零控制错误时，按控制游戏计算的单侧95%二项上界为0.13910834066826516；共享场景、多个视图和受控状态限制独立性，该数不是全面安全保证。

## 异常与不可评价项

本批可评价记录未观察到已定义的错误/无证据介入。不代表未覆盖的阶段、实例和任意表述均安全。

## 资源与结论边界

新增模型调用、Token及API费均0。Worker执行192次；采集/参考重放4464步，候选评价1232步。历史模型学习成本保留，不能将整个技能获取成本记为零。

本批未满足完整在线准入条件，维持NO-GO和Shadow；不能以局部成功绕过覆盖或安全缺口。

原封存60局保持未执行。本批48局现在全部属于曝光材料，不可修改候选后再次当作未见确认。不能以本轮局部恢复成绩证明整体FlowEvo在线正确率或成本增益。

## 48局逐游戏清单摘要

| 游戏ID | 类型 | 场景 | 标签记录 | 完整修复 | 错误介入 |
|---|---|---:|---|---:|---:|
| alf-69e7f4823f17b964e2d9 | pick_heat_then_place_in_recep | 7 | {'MATCH': 2, 'UNKNOWN': 1} | 2 | 0 |
| alf-a312869118e02bcf7fb7 | pick_clean_then_place_in_recep | 8 | NOT_EVALUABLE | 0 | 0 |
| alf-dbe1ed4b3fd1393489ef | pick_cool_then_place_in_recep | 24 | NOT_EVALUABLE | 0 | 0 |
| alf-a28dff9470e6194d4d90 | pick_and_place_simple | 30 | NOT_EVALUABLE | 0 | 0 |
| alf-d93f8510be9a26fef24f | pick_heat_then_place_in_recep | 12 | NOT_EVALUABLE | 0 | 0 |
| alf-e155a8d036b7b02d0169 | pick_clean_then_place_in_recep | 4 | {'MATCH': 2, 'UNKNOWN': 1} | 2 | 0 |
| alf-07f14ec51cc61581ba6f | pick_cool_then_place_in_recep | 19 | NOT_EVALUABLE | 0 | 0 |
| alf-a1fedd5bd8fc0c8fe22e | pick_clean_then_place_in_recep | 2 | {'MATCH': 3, 'UNKNOWN': 1, 'DECLINE': 1} | 3 | 0 |
| alf-7905d89478ceb0a95170 | pick_heat_then_place_in_recep | 18 | NOT_EVALUABLE | 0 | 0 |
| alf-639501dabfc91d16fc86 | pick_cool_then_place_in_recep | 1 | {'MATCH': 3, 'UNKNOWN': 1, 'DECLINE': 1} | 3 | 0 |
| alf-8ed8b72b1abcbb8c7e52 | pick_clean_then_place_in_recep | 426 | {'MATCH': 3, 'UNKNOWN': 1} | 3 | 0 |
| alf-02fe9d87426438548189 | pick_cool_then_place_in_recep | 25 | {'MATCH': 2, 'UNKNOWN': 1} | 2 | 0 |
| alf-8d5050bf64510f4d6232 | pick_heat_then_place_in_recep | 20 | {'MATCH': 2, 'UNKNOWN': 1, 'DECLINE': 1} | 2 | 0 |
| alf-051b05953324762fc9ed | pick_heat_then_place_in_recep | 13 | NOT_EVALUABLE | 0 | 0 |
| alf-ea04108aa48e78f3b495 | pick_cool_then_place_in_recep | 17 | NOT_EVALUABLE | 0 | 0 |
| alf-0e1ef051888f2013f4e1 | pick_clean_then_place_in_recep | 409 | {'MATCH': 3, 'UNKNOWN': 1} | 3 | 0 |
| alf-87a352b4f7af376f291e | pick_clean_then_place_in_recep | 16 | NOT_EVALUABLE | 0 | 0 |
| alf-7bdf5228b46d1399233e | pick_heat_then_place_in_recep | 15 | {'MATCH': 2, 'UNKNOWN': 1, 'DECLINE': 1} | 2 | 0 |
| alf-0fcd371840032d8b76da | pick_cool_then_place_in_recep | 18 | NOT_EVALUABLE | 0 | 0 |
| alf-3cd003222e7b02c12101 | pick_clean_then_place_in_recep | 5 | NOT_EVALUABLE | 0 | 0 |
| alf-68d5fafcfc3c35c1f96b | pick_cool_then_place_in_recep | 27 | {'MATCH': 3, 'UNKNOWN': 1, 'DECLINE': 1} | 3 | 0 |
| alf-55683c743578b6d05701 | pick_heat_then_place_in_recep | 23 | {'MATCH': 2, 'UNKNOWN': 1, 'DECLINE': 1} | 2 | 0 |
| alf-6edbe20e51023401e055 | pick_clean_then_place_in_recep | 6 | NOT_EVALUABLE | 0 | 0 |
| alf-bed7af62d19527269278 | pick_heat_then_place_in_recep | 7 | {'MATCH': 3, 'UNKNOWN': 1, 'DECLINE': 1} | 3 | 0 |
| alf-cb7b7caf0e822c360cbf | pick_cool_then_place_in_recep | 19 | NOT_EVALUABLE | 0 | 0 |
| alf-0cba4b2b74e1fe756786 | pick_clean_then_place_in_recep | 8 | NOT_EVALUABLE | 0 | 0 |
| alf-b5890d5b6c6231fc8e7f | pick_heat_then_place_in_recep | 13 | NOT_EVALUABLE | 0 | 0 |
| alf-bf97c15477b80b4aa3d3 | pick_cool_then_place_in_recep | 17 | NOT_EVALUABLE | 0 | 0 |
| alf-1dc0071981496d91403f | pick_clean_then_place_in_recep | 2 | {'MATCH': 3, 'UNKNOWN': 1, 'DECLINE': 1} | 3 | 0 |
| alf-54e7c12b59ed51533f5e | pick_heat_then_place_in_recep | 16 | NOT_EVALUABLE | 0 | 0 |
| alf-fa781f1ec32d9ea90304 | pick_cool_then_place_in_recep | 20 | {'MATCH': 2, 'UNKNOWN': 1, 'DECLINE': 1} | 2 | 0 |
| alf-1e6492a06425f37ad8dd | pick_clean_then_place_in_recep | 25 | {'MATCH': 3, 'UNKNOWN': 1, 'DECLINE': 1} | 3 | 0 |
| alf-9b4a791110f1400e543d | pick_heat_then_place_in_recep | 1 | {'MATCH': 3, 'UNKNOWN': 1, 'DECLINE': 1} | 3 | 0 |
| alf-cc5a048ba91a20add97d | pick_cool_then_place_in_recep | 30 | NOT_EVALUABLE | 0 | 0 |
| alf-57f99adb784e722500d5 | pick_clean_then_place_in_recep | 24 | NOT_EVALUABLE | 0 | 0 |
| alf-d2b6cefe484c610faf5d | pick_heat_then_place_in_recep | 15 | {'MATCH': 3, 'UNKNOWN': 1, 'DECLINE': 1} | 3 | 0 |
| alf-d088a347642ebba2f97d | pick_cool_then_place_in_recep | 18 | NOT_EVALUABLE | 0 | 0 |
| alf-2ddd5a140619d374feb5 | pick_clean_then_place_in_recep | 426 | {'MATCH': 3, 'UNKNOWN': 1} | 3 | 0 |
| alf-eb0a4110343ad8dbe8e1 | pick_heat_then_place_in_recep | 12 | NOT_EVALUABLE | 0 | 0 |
| alf-c63ec38fafff59eda389 | pick_cool_then_place_in_recep | 7 | {'MATCH': 3, 'UNKNOWN': 1, 'DECLINE': 1} | 3 | 0 |
| alf-4fff2daa6ecdc1c1ad5b | pick_clean_then_place_in_recep | 8 | NOT_EVALUABLE | 0 | 0 |
| alf-0abec8d0a8a6e09808ee | pick_heat_then_place_in_recep | 30 | NOT_EVALUABLE | 0 | 0 |
| alf-89eac982eb2b987efb70 | pick_cool_then_place_in_recep | 24 | NOT_EVALUABLE | 0 | 0 |
| alf-3f57a44502ad0d0c47a3 | pick_clean_then_place_in_recep | 16 | NOT_EVALUABLE | 0 | 0 |
| alf-69974cce8a8a4763e8ac | pick_heat_then_place_in_recep | 25 | {'MATCH': 2, 'UNKNOWN': 1, 'DECLINE': 1} | 2 | 0 |
| alf-4ebd19eaae2867caf999 | pick_cool_then_place_in_recep | 16 | NOT_EVALUABLE | 0 | 0 |
| alf-dcb9294314a5b0bc71d8 | pick_clean_then_place_in_recep | 27 | NOT_EVALUABLE | 0 | 0 |
| alf-20b4a28405f5f02a78ca | pick_heat_then_place_in_recep | 19 | NOT_EVALUABLE | 0 | 0 |
