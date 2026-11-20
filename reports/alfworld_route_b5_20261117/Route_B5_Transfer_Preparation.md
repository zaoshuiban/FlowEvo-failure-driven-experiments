# Route B5：P1 检查点准备

状态：P1 完成；覆盖不足，仅允许 P2 探索性局部迁移，不满足完整确认性比较或 P3 条件。

协议：`8c36667f426e4f740c99833c931567984cd5ed7be09fc85ae0b903a4faa05840`。检查点：`c7b14abdb24260be7f70113d24b1d178135b30050b6ab97f96247525fefcc8ec`。

## 冻结候选

- FR11：`3c63f420b178b8f40846dc03396f3519ebf940db12a7eec0076da01de0169b97`。
- Route_A：`5d92dd91b7bec7d514112f6bfef5814f381a4f8670f72a3807e7200b18de22fd`。
- S0：`233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37`。
- S11：`da2d550f990194ad14f0ea61a57281931a6c57a14cdbebb2bb5cf6fd05598f7b`。

S11/FR11 为原模型 Python；Route A 使用原 candidate_0 gate，仅添加现有返回信封适配，MATCH 后调用原 S0。门控仅入口一次；三组独立重置、同公开上下文、空技能状态、min(18,50-prefix) 恢复窗口。未新增 Rule。

## 来源与曝光

沿用 B3 的 12 局预约清单和顺序：清洗6、简单3、冷却2、加热1；Cabinet5、Microwave3、Fridge2、Drawer2；10个场景。0个严格未见场景，无 Safe。

已扫描仓库 runs 与本机受控存储中的全部 JSONL 身份以及冻结分配文件；游戏内容、轨迹哈希及任务组均无历史实质曝光命中，只命中原预约清单。数据集行/游戏路径/内容/场景来自实际文件。此结论不涵盖没有留下记录的外部使用。原34+46池与A/B已曝光集仍隔离。

## 采集与标签

复用未改动 A1d 公开状态采集器，依次尝试 READY、TARGET_CONFLICT、UNPROCESSED、OTHER_INSTANCE；真实失败投递、独立reset逐步重放、独立参考探测后才审标签。没有使用候选表现选题或标注。所有游戏不替换。

每局最多3条：优先READY的等长MATCH/UNKNOWN真实子序列对，或完整MATCH；再取第一条可信DECLINE；剩余名额按冻结顺序取其他物理状态。所有未选中记录与原因保留。

DECLINE只表示不适合恢复所声称的最终投递；不是断言任何打开动作都会破坏任务。未加工/未获胜/不同实例本身不足以标负。UNKNOWN明确记录省略的处理证据；不由短历史长度自动赋值。参考探针与评分标签不进入候选上下文。

| 标签 | 记录 | 游戏 | 物理组 | 场景 |
|---|---:|---:|---:|---:|
| MATCH | 9 | 6 | 9 | 5 |
| DECLINE | 3 | 3 | 3 | 2 |
| UNKNOWN | 3 | 3 | 3 | 3 |

总计15条、6游戏、12物理组；不能把裁剪视图或三候选重复执行当成独立游戏。

## 排除明细

- alf-dcbaf4efc3840568e447：入选 0 条；搜索结果 PUBLIC_SEARCH_BUDGET。
- alf-8326657193823dc7a5fd：入选 0 条；搜索结果 PUBLIC_SEARCH_BUDGET。
- alf-132796d472d5c752b18c：入选 2 条；搜索结果 完成。
- alf-140f8b06a403dd062d0d：入选 2 条；搜索结果 完成。
- alf-372e4de43d6ba9151de8：入选 0 条；搜索结果 PUBLIC_SEARCH_BUDGET。
- alf-943d120cbb0023c9dd09：入选 3 条；搜索结果 完成。
- alf-e42737643587fd4a7019：入选 3 条；搜索结果 完成。
- alf-04c6c94a29905032ae5b：入选 0 条；搜索结果 PUBLIC_SEARCH_BUDGET。
- alf-4e6a2dc865c2ca3dc6af：入选 0 条；搜索结果 PUBLIC_SEARCH_BUDGET。
- alf-c84d3d53a9c05cda73b6：入选 2 条；搜索结果 完成。
- alf-26670fb0478fa935f958：入选 0 条；搜索结果 PUBLIC_SEARCH_BUDGET。
- alf-7219a87c54721de51e5e：入选 3 条；搜索结果 完成。

完整逐分支排除原因保存在私有 checkpoints.private.json；未验证状态不进入可靠标签分母。

## 资源与验收

模型请求/Token/费用上限为0。采集预算6000环境步，候选评价10000（包括恢复余量），总16000；最多36检查点×3候选，1980 Worker 主执行+20冒烟余量。已实际采集1011环境步、52次reset。后续不会调用原生解题模型。

14项B5专项测试与24项历史回归通过，后者包含真实Docker Linux Worker、旧TextWorld检查点、中断重放、无重复结算、Shadow与UNKNOWN阻断。三份冻结恢复程序及Route A门控Worker冒烟通过。

首次采集缺少共享采集器要求的协议镜像，在0环境步时停止；补齐相同哈希协议副本，保留启动异常。没有改变冻结源码、候选或实验规则。

P2入口只消费本次冻结数据；保持私有完整回执、逐动作评分、源码及结果哈希。P3不自动执行。
