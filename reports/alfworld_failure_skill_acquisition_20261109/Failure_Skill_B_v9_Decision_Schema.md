# B v9 输出 Schema 与一致性检查

协议内冻结 JSON Schema 与宿主检查版本 `v9-decision-schema-1` 和 `v9-self-consistency-1`。两组 JSON 根对象仅含 `rows`。每条记录有唯一输入 ID，未知和重复记录单独拒收，字段缺失、类型、枚举和引用错误带字段路径及错误代码。结构检查按行进行。

| 字段 | 含义 |
|---|---|
| `failure_relevant` | 选定历史失败是否仍与当前目标有关 |
| `obstacle_present` | 同一历史障碍是否仍存在。无选定失败或无法确认是哪一个障碍时为 UNKNOWN |
| `recovery_needed` | 公开证据支持恢复为 YES，明确不适用或无选定失败为 NO，证据不足为 UNKNOWN |
| `evidence_steps` | 唯一证据字符串的 JSON 数组，最多 8 项。当前观察有单独 ID |
| `uncertainty` | 简短说明，最多 180 字符 |

历史步骤保留原 `step_id` 并提供按记录限定的 `evidence_id`。例如 `["case_022:step_002", "case_022:current"]`。当前公开快照 ID 由输入的 `current_evidence_id` 给出。单字符串、逗号拼接、裸步骤 ID、不存在的 ID、跨样本引用均拒收，即便两条记录恰好有同名局部步骤。引用验证只确定来源和时间合法，证据是否支持陈述仍由事实与决策评分检验。

S 增加 `facts`。实体字段分别描述目标和失败动作的物体与容器类别、实例。类别去掉实例编号。目标实例仅指目标明确命名的实例，缺失或不能确认用 `null`。

| S 字段 | 含义 |
|---|---|
| `object_category_match`、`container_category_match` | 对比目标与失败动作各自的类别 |
| `object_instance_match`、`container_instance_match` | 对比目标显式命名实例和失败实例。任一未指定时为 UNKNOWN |
| `held_object_matches_goal` | 当前持有物是否满足目标类别和显式实例要求 |
| `held_failed_object_match` | 当前持有物是否就是失败动作中的物体 |
| `local_target_binding` | 公开证据是否足以支持失败目的地为当前局部目的地。类别目标可以允许多个容器 |
| `phase_match` | 当前阶段是否仍是该次投递所需阶段，考虑处理前提与子目标完成。单凭持有物无法定位阶段 |
| `binding_consistent` | 综合当前持有、目标、局部绑定及阶段是否一致 |
| `obstacle_resolved` | 同一障碍是否已解除 |
| `held_object_changed` | 自失败后，失败物体是否已失去持有或被替换 |
| `subgoal_completed` | 原投递子目标是否已完成 |
| `failure_step_id`、`post_failure_evidence_steps` | 失败锚点及其后的公开历史证据。后续列表仅接受严格晚于所报锚点的历史引用 |

MATCH 表示公开证据支持相符。CONFLICT 表示公开证据明确不相容。UNKNOWN 表示缺少足够证据或比较不适用。持有失败物体可以为 MATCH，而该物体与当前目标类别不符。目标为容器类别时，显式实例比较可以是 UNKNOWN，同时具体失败实例仍可在公开状态下建立局部绑定。

一致性检查只比较模型自己的字段。共同规则检查无关、障碍不在或条件仍未知却报告恢复 YES。S 另查明确目标冲突、已解除障碍、持有物已替换、子目标已完成、局部实例未定却恢复 YES，以及所报实体、比较、综合绑定之间的矛盾。公开输入仅用于校验引用和参考评分，不用于替模型计算决定。结构合格的矛盾输出标记 `INCONSISTENT_OUTPUT`，原始值保持可追溯并进入配对统计。未启用额外宿主决策 Gate。
