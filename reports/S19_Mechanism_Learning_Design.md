# S19 机制学习与实际数据流

## 本轮最小变化

系统仍只有 REPAIR_EXISTING 与 REGENERATE_FRESH 两种受控恢复动作，NATIVE 表示不干预。模型不能选择隐藏测试、增加预算、修改权限或直接执行 Python。新表示为 `repair-choice-json-v2`，不和旧自由 Python 策略的成功率混算。

真实调用路径：

```text
LearningStream.run
  → ExperimentRunner.solve → PreparedController → SharedTransport
  → trusted public Judge → finalize → FailureEvidenceStore
  → SymptomLearning.ingest → CompileQueue.schedule_hypotheses
  → job → learning_messages → final-wire request
  → learn_content + RuleMemory.add
  → assess(original checkpoint budget, same public tests, Linux Worker)
  → bounded authorization (future tasks only)
  → next task RepairChoiceHook → host model action → public Judge
  → RuleMemory.finish → exact-checkpoint effect → hypothesis update
```

`run` 在题间执行 boundary；不会在当前题生成后立即发布。每题 begin 固定可见规则集，reserve 时再检查暂停和额度。暂停立即有效。

## 症状不是机制

SymptomGroup 的 key 使用产物状态、公开结果、异常类别、生成结束原因及动作资格；重复异常只能提示共同表征，不能确认共同根因。

MechanismHypothesis 初始没有内容且为 UNTESTED。模型输出的六项内容是：conditions、action、expected_improvement、refusal_conditions、stop_conditions、unknowns。它们必须是非空字符串，并与受约束 rule 同时生成；宿主不预写哪种动作正确。

| 记录 | 含义 |
| --- | --- |
| evidence_version | 新的可信事件进入集合；不是策略有效性提升 |
| content_version / content_delta | 模型实际改变假设内容，并绑定响应指纹 |
| operator_version / rule_diff | 规则真正变化；相同规则只增加证据及对应生成成本记录 |
| assessment_diff / validation_cost | 来源验证效果变化，不自动表示机制改进 |
| supporting_evidence_ids | 宿主观察到来源或未来公开成功；不等于相对 Generic 的因果收益 |
| contradicting_evidence_ids | 真实同组反馈中的公开用例退化，绑定实际前置候选和 task/stage |

`independent_task_count` 是不同 task_id 的计数，不自动等于独立原题、代码谱系或自然失败数量。Pilot 用来源文件、行号、题面去重与曝光标记补充谱系；工程夹具的多个任务不能按此计数宣称泛化。

## 有界修订与旧版本

单条合法失败可以启动 Shadow 学习；不要求三题。后续相似事件进入原症状组。调度要求新增证据或未消耗的功能诊断，并受并发机制数及持久预算限制。

每个作业最多两个生成请求：初始一个，失败后有诊断才修订一次。来源评估失败、范围不适用及编译错误均可形成该作业内诊断。后续新证据可以启动新的有界作业，但不能仅因上一作业失败就无条件循环。

修订输入包含当前假设、新失败/公开反例、旧规则、来源评估和功能诊断；不包含最终复核、参考程序或未来轨迹。内容变化、规则变化和作用变化分别记录。相同规则不会重设试用额度，已暂停版本也不会借重新生成同文规则恢复权限。

版本保留 parent_operator_id、operator_version、evidence_delta、rule_diff、generation_cost，以及 assessment_diff、validation_cost。相同文本的额外生成尝试存为 equivalent_generation_records，其费用不因去重消失。实际请求和工具账本始终是完整成本依据。

## 来源评估和反馈级别

来源包保留真实 stage、候选 SHA、公开反馈与已耗预算。取按 observed_at 排序的最早合法来源，不按修复结果挑源。before/after 使用相同公开输入的稳定 case ID；缺失/编译失败按这些相同 case ID 的 false 结果比较，而非空测试集合。

- 合法行为：协议、拒绝和动作符合契约，但未见改进。
- 局部改善：部分用例改善且未退化，任务仍未完全正确；保留 Shadow。
- 来源公开修复：全部来源公开用例恢复，可在通过宿主安全探针且预授权的情况下获得有限试用。
- 最终复核：本轮连续工程路径不查询；未来单独锁定后评价，不能回流在线假设。
- 相对 Generic 增量：必须有真正配对证据；本轮 `paired_cost_benefit=None`，不能从失败但便宜推断效率收益。

宿主产生安全探针结果：适用状态、PASS/UNKNOWN 拒绝、零/不足调用预算、工具预算、缺失源码不能 repair、未知请求停止、正常原生回退。注册依据由这些实际布尔结果映射，不接受模型自报 `passed=true`。

未来反馈通过干预前 `candidate_sha256 + stage + observed_at` 匹配事件；不是选本题第一条失败。记录实际干预、原生动作差异、公开效果和回退需求；公开退化暂停并增加假设限制。没有命中只保留 routing 记录，不记为失败。

## 路由与长期边界

路由仍是持久顺序中的第一个有权限、适用且有额度的版本。记录所有匹配、冲突、选择原因、模型调用/Token/工具耗时。更便宜的原生动作是否存在目前未知，不能称为成本学习路由器。`changed_generic_action` 比较现有原生重试的上下文动作，不把不同措辞自动算作新的规划能力。

G/M/F 运行目录、成功库、失败池、文本记忆与账本独立；M 与 F 经过同样严格的公开任务投影。M 记录新增/重复输入，不因重复知识不收费。S20 需要进一步做公平配对和总学习费用比较；S21 消融与老年代晋级未在本轮实施。

`continuation_cost` 另记录干预失败后直到题结束的调用、Token及工具消耗；这包括整个后续流程，可能包含其他算子，不伪称为单独的原生增量成本。异常未知时不产生虚构的零费用结论。
