# Route B5：冻结候选的局部迁移结果

本轮完成 P1 采集与 P2 零模型调用比较。结果属于未见游戏、已见场景中的受控恢复检查点探索，不是原生 Agent 在线增益，也不是未见场景泛化。全部候选保持 Shadow，未执行 P3。

Run：`alfworld_route_b5_transfer_20261117_01`。协议 SHA-256：`8c36667f426e4f740c99833c931567984cd5ed7be09fc85ae0b903a4faa05840`；检查点 SHA-256：`c7b14abdb24260be7f70113d24b1d178135b30050b6ab97f96247525fefcc8ec`。

## 数据与分母

| 标签 | 记录 | 游戏 | 物理组 | 场景 |
|---|---:|---:|---:|---:|
| MATCH | 9 | 6 | 9 | 5 |
| DECLINE | 3 | 3 | 3 | 2 |
| UNKNOWN | 3 | 3 | 3 | 3 |

不同公开历史视图仍共享物理检查点；三个候选执行同一记录也不增加独立游戏数量。UNKNOWN 是明确披露的真实历史裁剪视图，不能解释为原生 Agent 自发忘记处理过程。

## 三候选结果

| 候选 | 正例障碍解除 | 正例完整修复 | 成功游戏 | 可信负例错误恢复 | UNKNOWN 无证据恢复 | 拒绝 | 错误 |
|---|---:|---:|---:|---:|---:|---:|---:|
| S11 | 9/9 | 0/9 | 0/6 | 3/3 | 3/3 | 0 | 0 |
| FR11 | 5/9 | 5/9 | 4/6 | 0/3 | 2/3 | 8 | 0 |
| Route_A | 9/9 | 9/9 | 6/6 | 0/3 | 0/3 | 6 | 0 |

零分母项为 NOT_EVALUABLE；表中 0/0 不是通过。障碍解除指原失败投递变为合法；完整修复在本批单目标游戏中要求成功投递且环境 won。打开容器不计完整修复。UNKNOWN 物理状态即使获胜，也不能反向证明介入时证据充分。

## 逐游戏结果

| 游戏 | 类型 / 容器 / 场景 | 标签数 | S11 修复 | FR11 修复 | Route A 修复 |
|---|---|---|---:|---:|---:|
| alf-dcbaf4efc3840568e447 | pick_cool_then_place_in_recep / Cabinet / 1 | {} | 0 | 0 | 0 |
| alf-8326657193823dc7a5fd | pick_clean_then_place_in_recep / Fridge / 17 | {} | 0 | 0 | 0 |
| alf-132796d472d5c752b18c | pick_and_place_simple / Drawer / 410 | {'MATCH': 2} | 0 | 2 | 2 |
| alf-140f8b06a403dd062d0d | pick_clean_then_place_in_recep / Cabinet / 413 | {'MATCH': 2} | 0 | 0 | 2 |
| alf-372e4de43d6ba9151de8 | pick_and_place_simple / Cabinet / 18 | {} | 0 | 0 | 0 |
| alf-943d120cbb0023c9dd09 | pick_clean_then_place_in_recep / Cabinet / 428 | {'MATCH': 2, 'UNKNOWN': 1} | 0 | 0 | 2 |
| alf-e42737643587fd4a7019 | pick_clean_then_place_in_recep / Microwave / 2 | {'MATCH': 1, 'UNKNOWN': 1, 'DECLINE': 1} | 0 | 1 | 1 |
| alf-04c6c94a29905032ae5b | pick_clean_then_place_in_recep / Drawer / 30 | {} | 0 | 0 | 0 |
| alf-4e6a2dc865c2ca3dc6af | pick_clean_then_place_in_recep / Cabinet / 2 | {} | 0 | 0 | 0 |
| alf-c84d3d53a9c05cda73b6 | pick_and_place_simple / Microwave / 15 | {'MATCH': 1, 'DECLINE': 1} | 0 | 1 | 1 |
| alf-26670fb0478fa935f958 | pick_heat_then_place_in_recep / Fridge / 12 | {} | 0 | 0 | 0 |
| alf-7219a87c54721de51e5e | pick_cool_then_place_in_recep / Microwave / 15 | {'MATCH': 1, 'UNKNOWN': 1, 'DECLINE': 1} | 0 | 1 | 1 |

## 四轴准入

- CAPABILITY_READY：通过。
- SAFETY_READY：未通过。
- COVERAGE_READY：未通过。
- ENGINEERING_READY：通过。

P3：NO-GO；不启动原生 G 增量实验。禁止把局部恢复结果表述为整局在线正确率改善或失败信息的因果优势。

## 成本、完整性与证据

新增模型请求 0、Token 0、API 费用 $0。Worker 89 次（包括旧开发夹具冒烟）；采集/独立重放 1011 环境步，候选评价 771 步，合计 1782，低于 16,000 上限。Worker 主机成本未换算成货币，不能称为完全免费。历史技能学习成本仍属于旧实验，不并入本轮新增 API 费，也不视为零。

候选源码、父代运行、依赖、环境、Worker、数据和结果通过 SHA 绑定；分支逐步日志与结果提交收据保存在私有 Run。38 项零 API 测试通过（14 项 B5 专项 + 24 项历史回归），包括真实 Linux Worker、已曝光 TextWorld 回放、中断恢复、未知阻断和 Shadow 权限。

首次采集启动在任何环境动作之前因共享采集器缺少协议镜像而停止；补齐完全相同 SHA 的协议副本后执行，原日志保留。没有修改候选、题序、采集或标注算法。

逐记录、逐动作、合法动作、Worker 原始回执、进入时门控、时序证据与完整资源账本见私有 `result.json`、`outcomes/`、`live/`、`worker.jsonl`、`environment.jsonl`；公开机器可读统计为同目录 `Route_B5_Summary.json`。

## 行为差异与错误归因

S11 在15个检查点都只执行一次 open，随后拒绝继续。源码在开门后没有保留具体物体/容器绑定：最新动作已经是 open，随后从目标文本重新抽取的类别缺少实例编号；同时检查 “is open” 与真实 “You open …” 回执不一致。真实回执最终理由均为 `no supported legal recovery action matches evidence`。这是多步延续/状态解释问题，不能把9/9开门视为9/9恢复。

FR11 在四个新游戏完成了5次正例恢复，涉及Drawer、Microwave两个容器类别和3个场景；正例每次实际执行open→move。两个Cabinet清洗游戏的4个正例全部拒绝。其目标是 `put a clean soapbar in cabinet.`，冻结正则未识别带clean形容词的目标；但 `clean some potato and put it in microwave.` 能匹配。这是目标表达覆盖缺陷，尚不能把失败归因于Cabinet计算能力本身。没有修改正则或重跑。

FR11 在两条裁剪后的UNKNOWN中没有先取得缺失处理证据，就立即open→move，并实际won。物理世界中物体确实已处理，但当时模型可见上下文没有这个证据，因此这2次仍为无证据恢复，不因获胜而改标。另一条UNKNOWN随目标解析失败而拒绝，不能解释为主动识别了证据不足。3条目标冲突负例均拒绝，但这不能证明阶段/实例冲突也安全。

Route A 的门控为9 MATCH、3 DECLINE、3 UNKNOWN；9次MATCH都由原S0执行open→move并won。它在本批检查点保留恢复机会且拒绝6个控制，但训练历史、监督方式和候选选择与B4不同，属于成熟策略参照，不能据此计算路线A或失败信息的公平因果优势。

表中“拒绝”仅指没有任何环境动作的入口拒绝；S11的15次开门后拒绝另见stop_counts。成功游戏按“该游戏至少一条正例完整修复”计数，并非整局从初始状态在线成功率。无检查点的6个游戏为NOT_EVALUABLE，不是三个候选各失败6次。

## 覆盖边界与最小后续建议

6局因PUBLIC_SEARCH_BUDGET未形成可用检查点；共有6个目标分支因预算内没有可打开实例而未构造、4个未加工分支保留未验证、2个简单任务没有加工分支。3条可信DECLINE全部是TARGET_CONFLICT，未获得可信阶段冲突/实例冲突负例。没有Fridge、Safe或加热任务上的可评价正例；正例实际覆盖Drawer、Cabinet、Microwave。未见场景仍为0。

本轮已封存，不补题、不修订候选以改变成绩。FR11能力轴通过（4游戏、3场景、2容器），安全轴因2次UNKNOWN无证据恢复失败；覆盖轴正例6游戏、控制3游戏，低于各8游戏门槛。因此即使Route A本批全通过，也不能替代FR11安全条件而启动P3。下一轮若获授权，应独立冻结新的覆盖材料与边界机制对照；若修改候选，必须建立新版本，不能把本轮已看过的15条记录再次当作独立确认。

## 逐检查点审计摘要

以下为同状态三组的真实行为；完整动作与回执在私有记录。`完整修复`只用于MATCH；`无证据介入`可能在物理世界获胜，但不获得适用性信用。

| 检查点（游戏后缀/分支/视图） | 标签 | S11 | FR11 | Route A |
|---|---|---|---|---|
| 132796d472d5c752b18c/READY/full | MATCH | 仅解除障碍（1步，won=0） | 完整修复（2步，won=1） | 完整修复（2步，won=1） |
| 132796d472d5c752b18c/OTHER_INSTANCE/full | MATCH | 仅解除障碍（1步，won=0） | 完整修复（2步，won=1） | 完整修复（2步，won=1） |
| 140f8b06a403dd062d0d/READY/full | MATCH | 仅解除障碍（1步，won=0） | 拒绝（0步，won=0） | 完整修复（2步，won=1） |
| 140f8b06a403dd062d0d/OTHER_INSTANCE/full | MATCH | 仅解除障碍（1步，won=0） | 拒绝（0步，won=0） | 完整修复（2步，won=1） |
| 943d120cbb0023c9dd09/READY/view0 | MATCH | 仅解除障碍（1步，won=0） | 拒绝（0步，won=0） | 完整修复（2步，won=1） |
| 943d120cbb0023c9dd09/READY/view1 | UNKNOWN | 无证据介入（1步，won=0） | 拒绝（0步，won=0） | 拒绝（0步，won=0） |
| 943d120cbb0023c9dd09/OTHER_INSTANCE/full | MATCH | 仅解除障碍（1步，won=0） | 拒绝（0步，won=0） | 完整修复（2步，won=1） |
| e42737643587fd4a7019/READY/view0 | MATCH | 仅解除障碍（1步，won=0） | 完整修复（2步，won=1） | 完整修复（2步，won=1） |
| e42737643587fd4a7019/READY/view1 | UNKNOWN | 无证据介入（1步，won=0） | 无证据介入（2步，won=1） | 拒绝（0步，won=0） |
| e42737643587fd4a7019/TARGET_CONFLICT/full | DECLINE | 错误最终投递恢复（1步，won=0） | 拒绝（0步，won=0） | 拒绝（0步，won=0） |
| c84d3d53a9c05cda73b6/READY/full | MATCH | 仅解除障碍（1步，won=0） | 完整修复（2步，won=1） | 完整修复（2步，won=1） |
| c84d3d53a9c05cda73b6/TARGET_CONFLICT/full | DECLINE | 错误最终投递恢复（1步，won=0） | 拒绝（0步，won=0） | 拒绝（0步，won=0） |
| 7219a87c54721de51e5e/READY/view0 | MATCH | 仅解除障碍（1步，won=0） | 完整修复（2步，won=1） | 完整修复（2步，won=1） |
| 7219a87c54721de51e5e/READY/view1 | UNKNOWN | 无证据介入（1步，won=0） | 无证据介入（2步，won=1） | 拒绝（0步，won=0） |
| 7219a87c54721de51e5e/TARGET_CONFLICT/full | DECLINE | 错误最终投递恢复（1步，won=0） | 拒绝（0步，won=0） | 拒绝（0步，won=0） |

## 完成态恢复与冻结存档

再次进入已完成执行入口后，9个关键账本/结果文件SHA完全不变，没有新增Worker或环境动作，也没有新增请求与费用。详细证据：`Resume_Acceptance.json`。所有12局现在均视为本研究已曝光游戏，包括未形成标签的6局。

## 分组执行资源

| 候选 | Worker调用 | Worker回执耗时（秒） | 环境步（含前缀） | 恢复动作 |
|---|---:|---:|---:|---:|
| S11 | 30 | 9.551 | 309 | 15 |
| FR11 | 22 | 7.860 | 308 | 14 |
| Route A | 33 | 9.025 | 154 | 18 |

P2合计85次Worker；另4次旧开发状态冒烟，共89。771环境步中724为前缀重放、47为恢复动作。Route A拒绝入口时不启动恢复环境分支；使用经独立真实重放确认的公开状态执行门控，成本差异如实保留。
