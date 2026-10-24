# S19学习调度修订

## 范围与结论

新增显式`evidence-diversity-v1`，复用SymptomLearning与CompileQueue；旧ID排序仍是旧计划默认路径。没有增加动作或代际机制，没有使用隐藏答案、最终复核或事后A/B胜负。

零API重放旧第一批边界：新排序第一名为425/741跨任务未交付程序组，第二名为909的IndexError证据族，包含length/stop两个原症状组的3条证据。旧排序选择了909的两个组。本结果仅证明调度决策改变，不证明它们能够生成更好的规则。

## 冻结排序

只使用截止调度时可见且未撤销的证据和假设事件。粗证据族为原symptom去掉finish_reason后的哈希；保留artifact、public_result、异常及动作资格，不合并不兼容的动作状态。各子组ID和length/stop继续记录，不删除、改写原假设，不声明共同根因。

按以下元组降序，再按family SHA稳定排序：

1. 不同原题数量。
2. 记录的provenance_group覆盖数。
3. 相对已尝试材料新增的不同原题数量。
4. 是否存在两种合法可比较动作。
5. 较少的既往尝试次数。

事件数仅记录，不作为主排序。现有provenance_group默认可能等于task_id，因此明确标记为谱系代理而非独立谱系证明，不虚增独立性主张。

每个边界最多两个族。同一来源题不能同时占两个族的名额；同族仅一个代表作业，输入为合并后的当时可见证据。优先沿用已有规则关联的代表以便修订，否则用稳定ID。子组证据与功能反例仍留在原始日志，模型收到子类型清单。

不把原生后续成功/成本纳入本版排序：当前调度记录没有完整、可比的前缀绑定恢复成本；`priority_basis`明确标记NOT_RANKED，避免将未来结果或未知成本当成0。若规则已出现，同文聚合由既有RuleMemory负责；没有新增证据/诊断不得重新学习，不事先假装知道尚未生成的规则是否重复。

## 审计与停止

每族记录排名、原题ID、谱系代理、动作、子类型、先前尝试数、选择及跳过原因。原因包括NO_BUDGET、NO_ACTION、NO_NEW_EVIDENCE、IN_FLIGHT、SOURCE_DIVERSITY_LIMIT、FAMILY_LIMIT。

未知在途请求仍停止，旧预算不回填；无新证据不无限编译。第二批旧预算耗尽的零API重放仍为NO_BUDGET，不假设新排序会改变过去真实花费。

## 能力与文字更新分开

既有RuleMemory对相同规范化rule聚合为同一能力版本，同时保留每次生成请求、用量、证据增量；本轮未再造库。新增capability审计逐个可见任务记录match、action、Generic action、是否改变动作、不同动作数及同文次数。命中但均等同Generic明确为NO_DISTINCT_ACTION_VALUE；不命中为NO_MATCHING_OPPORTUNITY。

相同动作下，fixed action与learned rule调用同一action_messages，区别在条件选择。原生Generic使用repair_messages及成功经验，等同动作不保证完整Prompt字节相同。实际发送内容继续由SharedTransport完整保存；不将文案差异或假设版本号当能力收益。

工程验证：确定性排序、同源限制、预算阻断、在途阻断和去重通过。研究效果：未进行真实新生成或成本对照。
