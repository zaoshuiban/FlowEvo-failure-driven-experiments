# Route B4：双倍数据 S／F／FR 协议

2026-11-16。**P1_PREPARATION_READY / P2_PENDING_NEW_AUTHORIZATION / P3_NOT_EXECUTED**。
本轮只有数据准备、代码和零 API 验收；未发送模型请求，未构造独立游戏状态，未发布技能。旧 B3 12/12 弃权原样保留。

## 1. 身份、审计与复用

正式准备目录：`runs/alfworld_route_b4_preparation_20261116_03`。协议 canonical SHA-256：`5dc67b21ce2e16be9fb2b6d8f7a0493fd4e25875645412322af76729b68686f0`；文件 SHA-256：`86da809ca6e27ac8ef943eff17a794e3ea13d91e526a2a712f76844d88c389ff`。
Git commit 为 `e7e79e2bf3d6c8abf59c3a934a79862f5c51c3b3`；已有未提交修改保存在 working_tree_start.json，不切换、不清理。实际源码含新适配文件，不能仅以该 commit 描述运行版本。冻结 991 项源文件、历史材料和依赖 SHA，覆盖 Worker/Registry/预算所在模块。

已核对 B3 真实 wire/响应与全弃权报告、B1 五份源码、B2 开发结果、B0 投影/原生回退，以及旧容器和路线 A 11/11 来源修复。历史恢复源码 SHA `233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37` 仅作历史身份，不进入 B4 模型输入，也没有代写新候选。

复用 B3 同源投影、RecoveryAdapter、BoundedCompiler、持久账本、静态限制、Linux Worker、FailureOperatorRegistry、严格来源评分及 TextWorld 重放。没有改 L1/L2/L3、没有新增 DSL 或任务解析器。

## 2. D22 与 D11

D22 有 22 个不同游戏、22 个物理检查点、21 个任务组、13 个场景：旧 11 条 NATURAL_AGENT_FAILURE＋新增 11 条 CONTROLLED_INTERVENTION。旧自然来源中两个游戏同属一个任务组，不能称 22 个完全独立任务结构。

新增来源全部取自 A1c 原 TRAIN；A1d 合并数据中的 TRAIN 身份未改变。优先 READY、完整公开历史、已审查 MATCH，逐条核验：文件 SHA、原实际 TRANSITION、独立 verification 分支、失败 Nothing happens、后缀真实 won、目标与对象绑定。不是把未执行建议当成恢复后缀。24 个合格 TRAIN 游戏中以任务类型、目标容器、场景的稀少覆盖优先，固定 `B4_NEW_TRAIN_V1` SHA 破同分，选 11 个；不依据模型成绩。未运行新的训练游戏采集。

D11 从完整 D22 中固定选 6 条自然＋5 条受控，种子身份分别为 `B4_D11_NATURAL_V1` 和 `B4_D11_CONTROLLED_V1`，同样只用元数据覆盖排序，并保留 D22 顺序。D11 为 11 游戏、11 组、8 场景。它不是旧 B3 的 11 条自然来源，不能把本轮 D11 当作旧 B3 严格复现。

| 来源 | 来源性质 | 任务类型 | 目标容器 | 场景 | 游戏 SHA 前缀 | 入 D11 |
|---|---|---|---|---:|---|---|
| source_01 | 自然 | pick_and_place_simple | Safe | 204 | `e257456feffa` | 是 |
| source_02 | 自然 | pick_and_place_simple | Drawer | 423 | `db912a3f8b63` | 否 |
| source_03 | 自然 | pick_clean_then_place_in_recep | Drawer | 423 | `b9ca750a5ee7` | 是 |
| source_04 | 自然 | pick_and_place_simple | Safe | 204 | `3e07afa5d73e` | 否 |
| source_05 | 自然 | pick_clean_then_place_in_recep | Drawer | 411 | `621ad5ae0410` | 否 |
| source_06 | 自然 | pick_and_place_simple | Drawer | 411 | `dd62c1c2a8e9` | 是 |
| source_07 | 自然 | pick_cool_then_place_in_recep | Microwave | 6 | `e3680d6eb5d5` | 是 |
| source_08 | 自然 | pick_cool_then_place_in_recep | Microwave | 6 | `6e01515e7efc` | 否 |
| source_09 | 自然 | pick_clean_then_place_in_recep | Fridge | 6 | `e749212e8a88` | 是 |
| source_10 | 自然 | pick_heat_then_place_in_recep | Fridge | 6 | `63fbdae21215` | 是 |
| source_11 | 自然 | pick_and_place_simple | Fridge | 6 | `89c2656a348e` | 否 |
| source_12 | 受控 | pick_clean_then_place_in_recep | Fridge | 21 | `ef3181cf112d` | 否 |
| source_13 | 受控 | pick_and_place_simple | Drawer | 423 | `2c8afbc95c72` | 否 |
| source_14 | 受控 | pick_cool_then_place_in_recep | Cabinet | 4 | `c97428094306` | 否 |
| source_15 | 受控 | pick_heat_then_place_in_recep | Fridge | 13 | `e55e00b531d7` | 是 |
| source_16 | 受控 | pick_cool_then_place_in_recep | Microwave | 11 | `e15c9d850e4a` | 是 |
| source_17 | 受控 | pick_clean_then_place_in_recep | Drawer | 416 | `4b7ca4f869f7` | 是 |
| source_18 | 受控 | pick_and_place_simple | Cabinet | 413 | `5b2d43c7f69e` | 是 |
| source_19 | 受控 | pick_heat_then_place_in_recep | Fridge | 27 | `0c46bafbb89b` | 否 |
| source_20 | 受控 | pick_cool_then_place_in_recep | Microwave | 6 | `c39675c58e30` | 是 |
| source_21 | 受控 | pick_clean_then_place_in_recep | Drawer | 430 | `437f1fbfdbf9` | 否 |
| source_22 | 受控 | pick_and_place_simple | Cabinet | 428 | `dbe64da25068` | 否 |

D22 容器覆盖 Safe 2、Drawer 7、Microwave 4、Fridge 6、Cabinet 3；任务为简单 8、清洗 6、冷却 5、加热 3。新增数据没有强凑 Safe，其 Safe 来自旧自然来源。控制脚本确实引入了恢复示范，结论只能是混合来源的方法开发，不能将 22 条全部计为 Agent 自主失败。

每条完整 host 记录保存 game/trajectory/group/scene、原目标、原步骤、失败锚点、真实动作与反馈、R、won、来源哈希、物理组及重放证据。模型只得到允许的中性编号 C/F/R，路径、私有审查和封存标签不发送。机器可读清单为 source_selection.private.json 及 protocol.json；公开报告不附完整私有探测轨迹。

## 3. 共同验证与未见游戏角色

共同 TRAIN_VALIDATION 固定 14 条：6 MATCH、4 DECLINE、4 UNKNOWN，来自 9 游戏、9 任务组、5 场景、12 物理检查点。按标签内任务/容器/场景覆盖与 `B4_VALIDATION_<label>` 固定 SHA 选取，一标签内一游戏/组；同游戏的正例、负例或不同可见视图可以共组，因此 14 条不是 14 个独立游戏。

这些来自原 A1c/A1d TRAIN_VALIDATION，未进入任何 B4 生成包，与 D22 按游戏/轨迹/任务组/物理状态隔离。它们在旧路线 A 中已曝光，定位为**本轮输入外的共同开发验证**，不是全项目未见独立 Gate。保持困难负例的最终投递作用域；UNKNOWN 的缺失历史不补回。验证结果只在全部模型调用结束后计算，不用于工程或行为修订。

继续保留 B3 的 12 个新游戏元数据池（335 个合格池选出、10 场景、严格未见场景 0），与训练/验证游戏及任务组不交叉。原 34＋46 和既有 Gate 保留池未用于补数。新池未 reset、未标签、未执行候选，且没有 Safe；不能宣布独立验证覆盖已完备。候选冻结后，P3 才能按独立资源/采集冻结开展，不得按候选成绩换题或重选来源。

## 4. 替换后的共同离线任务说明

六个单元共享同一 system prompt、接口、安全规则与输出约束。核心完整替换 B3 的离线/在线混合开头，安全段复用原规范；不是在原歧义提示结尾补一句。

核心含义：现在编写未来可复用的 Python 函数，历史案例只是学习材料；现在没有 live context 是正常的。未来宿主会提供真实 goal/observation/admissible_commands/history/state，函数那时再判断适用与动作合法。可以因无法形成任何有依据的通用策略而 ABSTAIN，但不能仅因生成时没有实时游戏状态而拒绝编写参数化程序。

恢复仍限定真实失败后的局部任务；不是从第一步重做游戏、固定下一动作、无目标合法列表首项或替代原生 Agent。state={} 只表示程序记忆为空，保留持物、加工完成及任务实例要求；当前动作与未来动作条件分开核对；探索必须有目的、有界、有退出条件。运行时信息不足仍应拒绝。

完整英文共同提示见 `Common_Prompt.txt`，实际六个 wire 位于 inputs/，源码 `container_information_b4.py` 绑定于协议。动作说明仅提供相同命令语法，不含手写恢复步骤或旧程序。Mock 只能证明交付接口和提示内容存在，不能证明真实模型已经理解。

## 5. C/F/R 一致性

每条案例使用原真实前缀与后缀。C 为失败之前的中性公开状态及目标；F 为实际失败前缀到无效果动作；R 为该动作之后真实执行过的恢复片段。R 明确起点观察/历史缺省，保留实际起点合法动作和片段边界，不假装拼成完整连续轨迹。

S=C+R，F=C+F，FR=C+F+R。三组 C 相同，S/FR 的 R 相同，F/FR 的 F 相同，F 不得得到 R。D11 采用 D22 同一来源编号与原始片段，不重新解释同一证据。编码必须可无损 decode 回原投影，不静默删 F 步骤。源 106 的真实反复开关步骤也完整保留。

## 6. 六单元、早停和修订

单元 S11/F11/FR11/S22/F22/FR22 各 4 条初始谱系。先按单元固定顺序各做编号 0、1，共 12 初稿；若且仅若 12/12 全部是合法 ABSTAIN，结案并停止余下初稿。格式错误不是合法弃权，不满足该早停条件。

否则按同序补编号 2、3，完成 24 初稿，再逐个对交付/静态失败给予最多一次工程修订。全部初稿和工程修订归档后才开始 TRAIN 执行。工程反馈只有自己完整提交与通用格式、语法、接口、安全诊断。

每单元最多一份父版本进入行为修订：至少有一次 Worker OK、具有完整 TRAIN 回执，且未在自身 TRAIN 达到全部修复/零错误；按 TRAIN 修复数降序、错误/错误介入/不足证据介入升序、固定候选编号选取。**零修复也允许获得这一次机会**，全弃权则没有机会。TRAIN 当前均为正例，错误介入维度为 0；不借验证负例给修订器“补分”。

行为修订只收到自己的完整代码、获准 TRAIN 的起点和实际公开决策/回执/异常/合法动作/无进展信息；候选自述标为非环境事实。D11 仅 11 条，D22 仅 22 条。控制标签、TRAIN_VALIDATION、其他候选、人工路线及原 R 私有见证不进入反馈。完整源码与全部起点必须保留；超长决策按时间轮转固定前缀截取、记录省略索引；连起点与源码都超限时不发请求。

最多 24 初稿＋24 工程修订＋6 行为修订＝54。行为修订交付失败不再补工程请求。不补采样、不挪用未用额度。所有响应/源码/父版本和失败保留；修订失败或退化不删除先前合规父版本。阶段 II 要标为 origin+execution_feedback，不能再把 S 解释为完全未见失败。

## 7. 开发执行与最终选择

同样 Linux Worker、真实 TextWorld、静态权限和上下文投影；每个版本/检查点独立 reset 重放；窗口 min(18,50−前缀步数)。不赠送步骤，不复用上一个候选改变后的环境。所有候选仅 Shadow。

评分复用严格历史决定性状态见证/官方 won。局部修复、实际受阻投递完成、won、合法动作、实际执行、无进展、错误、拒绝和未知相关性分别记录。look/inventory 或状态变化本身不等于修复。无动作拒绝与未评定的探索也分开。UNKNOWN 后若出现新公开证据，不以入口标签永久判断后续，也不以物理 won 追认入口正当。

全部行为修订结束后才用同一 14 条验证集评价所有合规父/修订版本。最终需要验证正例至少一次严格修复、零运行错误；按验证修复数降序、明确不相容/不足证据介入、动作数、Worker 调用数、整条谱系 tokens、固定 ID 依次排序。全拒绝不能入选；没有合格版本返回 NO_ELIGIBLE_CANDIDATE。**开发优胜者不是发布技能，若仍有误触发必须公开报告。**

分母分别为每单元 4 个初稿机会、实际源码、实际 Worker 版本、每程序来源执行、独立谱系、共同验证记录/游戏/物理组。D11 对自己 11 条和 D22 对自己 22 条的训练修复率不构成公平泛化比较；规模比较以共同验证为主，仍是有限采样的探索性结果。

## 8. 模型、输入与独立预算

deepseek-flash，文档版本 DeepSeek-V4.1-Flash-1017，temperature=0.6，thinking disabled，JSON object，4096 输出上限。2026-11-16 核对 [供应商价格与模型](https://api-docs.deepseek.com/quick_start/pricing/)：1M 上下文；峰时未缓存输入 $0.30/M、缓存 $0.006/M、输出 $1.20/M。真实授权发送前仍要复核报价并归档响应模型字段，不能把别名当不可变权重哈希。

本轮六单元统一使用已有实验级容量接口：524,288 wire 字节、524,544 输入安全上界，旧全局 INPUT_LIMIT 不变。

| 单元 | 完整 wire 字节 | 输入安全上界 | 初稿数 |
|---|---:|---:|---:|
| S11 | 36,897 | 37,153 | 4 |
| F11 | 219,501 | 219,757 | 4 |
| FR11 | 242,743 | 242,999 | 4 |
| S22 | 69,061 | 69,317 | 4 |
| F22 | 375,857 | 376,113 | 4 |
| FR22 | 424,157 | 424,413 | 4 |

工程压力包（64KiB 源码）73,568 字节。行为压力包完整 64KiB 源码＋22 起点＋396 条独立长反馈，固定投影保留 85 条，最终 523,239 字节；其余索引保存。不能称所有反馈均完整进入模型。

| 阶段 | 模型请求上限 | 最大 tokens 预留 | 统一高价预留 |
|---|---:|---:|---:|
| I 初稿＋工程修订 | 48 | 25,374,720 | $30.449664 |
| II 行为修订 | 6 | 3,171,840 | $3.806208 |
| 合计 | 54 | 28,546,560 | $34.255872 |

按输入/输出分价的最坏峰价上界为 **$8.7630336**；按现有账本统一最高费率预留为 **$34.255872**。建议新的授权硬上限 **$36**，六单元各 $6、9 请求，互不转移。当前无有效授权，不能用 B3 剩余额度。实际消费按真实 usage/cache 另算，账本保守预留不冒充账单。没有填充无意义文本来伪装等实际 tokens。

开发最多 30 个合规父/行为版本：TRAIN 495 分支、共同验证 420 分支，共 915。Worker 上限 16,530 次（18×915＋60）；环境步上限 91,500（每分支含恢复重放余量 100），总壁钟上限 48 小时；任一上限先到即停。工具累计超时上界不是预计耗时，不与墙钟上限相加。实际预计时长依候选动作和环境初始化而变，不保证用满全部请求或分支。

P3 暂列 12 新游戏/最多 36 检查点，6 候选最多 3,888 Worker、25,200 环境步的资源计划，模型调用 0。必须在候选冻结后把采集参数和检查点绑定成 P3 执行协议；覆盖不足如实结案。原生 Agent/G 不在该计划中，如需要额外模型调用，另行报价授权。本轮不会运行 P3。

## 9. 文件、恢复与停止

新增 `container_information_b4.py`、prepare/run/test/accept/report_alfworld_container_b4*.py。原模块只复用，不改安全边界。每次请求、候选和角色评价有独立身份；已结算请求重入读取既有结果，未决发送和预算耗尽阻断。异常环境步骤按既有持久回执恢复/阻断，不盲目重放。没有真实授权时 sender=None 必须拒绝。

零 API 命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=FlowEvo/src:scripts \
 "$HOME/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python" \
 -m unittest scripts.test_alfworld_container_b4 scripts.test_alfworld_container_information scripts.test_alfworld_route_b_b0
```

本阶段没有提供 paid run 命令。下一步需要用户批准本轮独立费用，并绑定真实 transport/Run，复核输入/协议/报价；不得更改本冻结的提示、来源、排序、早停和修订规则。若运行前代码变化，必须留下新执行身份，不能冒充本次验收版本。
