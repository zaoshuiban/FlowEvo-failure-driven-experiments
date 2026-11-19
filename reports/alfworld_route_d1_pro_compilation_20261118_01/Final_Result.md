这次 Pro 已真正交付完整 Python；交付和执行结果逐版本列于下表。
程序已从同一第 16 步失败检查点、在原剩余 34 步内复现环境确认的恢复。
已执行候选的只读核对未发现明显来源固定路线或实例答案；这不等于证明泛化。
其他已曝光案例结果见独立诊断表，不回流修订或候选选择。
已经值得针对明确支持的目标句式预注册小规模独立复用评价；第 107 局暴露的句式限制须保留，本轮没有启动新评价。

Run ID：`alfworld_route_d1_pro_compilation_20261118_01`；结案分类：`EXPOSED_DIAGNOSTIC_LIMITED`。

| 版本 | 思考／输出上限 | 完整源码 | 静态通过 | 41 动作 | 41 won | 参数化核对 | 停止原因 | tokens／保守预留 USD |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| v1 | enabled/low / 32768 | True | True | 15 | False | True | ACTION_CYCLE | 21,167 / $0.389284 |
| v2 | enabled/low / 32768 | True | True | 6 | True | True | SUCCESS | 33,116 / $0.389284 |

| 旧开发诊断 | 动作 | 环境 won | 无动作拒绝 | 实际退出原因 |
| --- | ---: | --- | --- | --- |
| 12 | 6 | True | False | deterministic search and placement with capacity handling |
| 107 | 0 | False | True | cannot parse goal |
| 23 | 0 | False | True | cannot parse goal |

实际请求 2 次，实际 tokens 54,283，保守预留 $0.778568；实际供应商扣费未知。环境 122 步＝95 前缀＋27 技能，Worker 29 次；未决请求 0。实际执行阶段约 9.18 分钟，低于 90 分钟。

实际学到了什么：v1 能从公开历史重建位置、持物与放置记录，但在第 41 局仍持物探索，执行六次导航后连续九次 look，触发现有循环停止；没有拾取或投递。模型收到这一完整真实反馈后，v2 增加了持物时先处理投递、更新当前可见对象，以及从已见物品中选择未放置实例的逻辑。这个变化由模型生成，宿主没有补写恢复算法。

v2 的第 41 局实际后缀为：放回 keychain 2 → 导航 armchair 1 → 导航 armchair 2 → 拾取 keychain 3 → 返回 shelf 1 → 投递 keychain 3。第 22 个总环境动作返回 won=true（恢复后缀 6 步），余 28 步。程序每次根据公开历史和当前合法命令选择动作；没有保存该六步序列或原十一节点路径。它选中 shelf 1 来自对目标类型和运行时位置列表的解析，不是源码中的固定答案。

第 12 局目标类别是 creditcard，v2 同样用 6 步完成：放回 creditcard 4，再取得不同实例 creditcard 3 并送到 coffeetable 1。该结果说明它并非仅接受 keychain，但只是已曝光开发诊断。第 107 局的目标为 `put two soapbar in toilet`，当前解析器只接受 find 开头的句式，因 cannot parse goal 零动作退出；环境未完成。第 23 局同样不能解析而无动作拒绝，符合该检查点的边界标签。这支持“来源成功、其他已曝光双物体案例通用化仍不足”，不能将来源成功归零，也不能把边界拒绝写成整体安全。

最小参数化核对只排除了明显来源答案/固定路线：v2 第18–53行从目标和公开位置提取类别及实例，第55–110行处理真实观察，第112–175行据运行时变量构造合法命令。不存在字面 `keychain 2`、`keychain 3` 或固定来源搜索清单。保留的局限包括窄目标句式、找不到目的地类型时回退到首个已知位置，以及末端通用合法首项回退。这些没有在本轮来源/诊断中表现为非法动作，但不能据此承诺其他状态中的适用性。没有人工修补这些逻辑后重测。

配置回退未使用，第二次修订也未使用。v2 第一次满足来源通过条件后立即按 SHA `59ff438fafdb2675fc33d4a1543bce38088b59703cd9a85840cdd26407f67e04` 冻结；三个诊断没有进入任何模型请求，没有根据诊断换版本。两份程序源码不同，未复用同源码行为；每次评价均从原状态独立重放，内部 state 为空。没有运行异常或实际错误完成声明。

本轮实测恢复程序是 [v2/code.py](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_d1_pro_compilation_20261118_01/candidates/v2/code.py)。源码原样提取，原始模型响应及逐步执行均保留；[只读核对](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d1_pro_compilation_20261118_01/Validation.json) 全部通过。来源材料仍为一个游戏；实际环境评价覆盖原四个已曝光游戏，共五个分支（两次来源＋三次诊断）。请求、版本和重复重放不是新增独立样本。

每份请求均保存 HTTP 字段、实际 usage、reasoning tokens、最终 content 和源码长度、起止时间及输入计量。输入采用本地 token 计数＋25%＋1024 的冻结估计；不以字节冒充 token，不截断材料。费用按完整输入上限及输出上限预留，采用峰时统一最高单价，比供应商分开计输入输出更保守。每次绝对截止为600秒，总阶段上限90分钟。

| 请求 | finish_reason | content 字符 | 源码字符 | 输入／输出／reasoning tokens | 实际秒数 |
| --- | --- | ---: | ---: | --- | ---: |
| v1 | stop | 8216 | 7506 | 5439 / 15728 / 13453 | 236.12 |
| v2 | stop | 9253 | 8593 | 21032 / 12084 / 9562 | 167.91 |

材料来自一个游戏：完整失败50步＋真实成功恢复后缀11步，前16步共享。选择始终为Pro第一次11步恢复，没有引入第二次8步、Flash源码、旧思考伪代码或人工策略。全部动作由候选根据原公开接口产生，宿主没有补算持物、位置或任务进度；没有原生兜底、额外直接恢复、新游戏或 G/R/F。

本轮不是低思考与高思考的严格优劣比较，不证明Pro普遍优于Flash；来源成功不等于独立迁移成功，已曝光诊断不等于系统增量。材料含失败及真实恢复，不能推出纯失败信息优势。旧实验结果保持原样。

[协议](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d1_pro_compilation_20261118_01/Protocol.md) · [机器结果](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d1_pro_compilation_20261118_01/Results.json) · [原始响应与实际参数](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_d1_pro_compilation_20261118_01/requests) · [原样源码与参数化核对](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_d1_pro_compilation_20261118_01/candidates) · [逐步执行证据](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_d1_pro_compilation_20261118_01/evaluations) · [账本](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_d1_pro_compilation_20261118_01/budget.jsonl)
