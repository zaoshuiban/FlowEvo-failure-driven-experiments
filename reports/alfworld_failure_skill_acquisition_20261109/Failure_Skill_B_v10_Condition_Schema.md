# B v10 条件 Schema 与检查语义

`public-condition-1` 和 `public-receipts-1` 是本轮冻结的交付与检查版本。模型只交付一个 JSON 对象，可用 `decision=ABSTAIN` 与 `reason` 弃权，或用 `decision=PROPOSE` 交付下列字段。

| 字段 | 用途 |
|---|---|
| `roles` | 模型自定别名，绑定到目标物体、目标容器、失败动作主体、失败动作客体或当前持有物 |
| `conditions` | 1–16 个原子，每项包含 `id`、`op`、`args`、`sources`、`claim`、`supports`、`contradicts` |
| `require`、`abstain` | 分别组合适用与拒绝条件，可用 `condition`、`all`、`any`、`not`。显式拒绝表达式可为空 |
| `recovery`、`refusal`、`uncertainty`、`scope` | 修复、拒绝、不确定性、适用范围的简短描述。文本仅归档 |

角色最多 8 个，条件组合深度最多 4 层，总节点最多 48。原子必须被表达式引用，每个原子必须有 1–6 个真实学习步骤引用。引用按轨迹作用域检查。学习引用的存在性可验证，文字解释是否足以支撑归纳仍需审查。校验可执行参数时只接受别名、固定操作名和有限参数。任意实体实例、状态 ID、Python 或自然语言比较均不能进入执行参数。

| 通用运算 | 可判定的公开事实 |
|---|---|
| `selected_failure` | 当前公开快照是否选定失败锚点 |
| `same_category`、`same_instance` | 比较已解析的类别或已知编号的实体。任一缺少编号时，实例比较为 UNKNOWN |
| `state_is` | 对某个具体实体比较明示 open/closed。只在明确无效果回执连续时沿用紧邻的显式状态 |
| `command_available` | 检查公开合法命令列表中是否存在指定动词和确切绑定 |
| `unique_command_binding` | 检查公开合法命令中某一参数位置的同类别选项是否唯一并符合给定绑定。唯一性限于可见命令 |
| `goal_requires` | 从已支持的公开目标句式读取放置、清洁、加热、冷却要求 |
| `observed_event` | 在锚点前、锚点后或整个已见前缀中匹配同一动作及实际回执。处理动作可仅指定主体。它可表达阶段证据，未观察到动作时为 UNKNOWN |

状态和事件解析仅覆盖冻结的小型语法。没有观察到打开不证明仍然关闭。未见到期望事件也不证明其没有发生。类别兼容不能推出实例相同。比较当前持有物时用明示字段或已见拾取、投递回执，遇到无法解释的状态变化时退回 UNKNOWN。没有状态检查会根据案例号或参考答案补全事实。

三值组合采用强 Kleene 逻辑。all 遇 FALSE 为 FALSE，其余有 UNKNOWN 为 UNKNOWN。any 遇 TRUE 为 TRUE，其余有 UNKNOWN 为 UNKNOWN。not 反转 TRUE/FALSE，保持 UNKNOWN。只有适用式 TRUE 且拒绝式 FALSE 才记为可介入。未知扩展运算有独立 `UNSUPPORTED_CONDITION` 状态，整套候选不能通过。运行记录分别保存角色绑定、条件真假、学习来源引用、当前证据引用、适用式和拒绝式结果。相互矛盾的同一状态证据，以及适用式和拒绝式同时为 TRUE，均记录为冲突。
