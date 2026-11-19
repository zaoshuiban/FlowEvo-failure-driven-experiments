模型自己找到恢复路线了：Pro 两次尝试均获得环境 won=true，分别用 11 步和 8 步；Flash 两次未完成。
模型尚未把这条恢复经验转化为有效程序：Flash 的可执行版本未复现第 41 局恢复，Pro 三次编译均在思考输出上限处截断，没有完整源码。
没有合格候选，P4 未执行；当前最值得改进的是经验到程序的编译环节，尚不能评价新游戏复用或系统增量。

Run ID：`alfworld_route_d_20261118_01`。本轮已按范围结案，没有未决模型请求。

**Recovery Discovery：直接恢复已经建立，但只在本来源、配置和小样本范围内。**

| 模型 | 尝试 | 实际模型请求 | 实际恢复动作 | 交付错误请求 | 环境 won | 停止原因 |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Flash | 1 | 7 | 2 | 5 | false | 纠正机会用尽 |
| Flash | 2 | 8 | 3 | 5 | false | 纠正机会用尽 |
| Pro | 1 | 11 | 11 | 0 | true | EPISODE_WON |
| Pro | 2 | 9 | 8 | 1 | true | EPISODE_WON |

Flash 两次都先放回第一件物品，但随后反复提出当前合法列表之外的 `go to tvstand 1`；第二次也出现了这一非法命令。宿主没有执行、替换或修正这些动作。这里的 5 次错误为第一次错误加 4 次纠正请求，纠正请求没有获得额外环境步数。Pro 第二次的一个错误是输出截断，此后在原请求额度内纠正成功。逐次成本、原始输出和全部实际动作见 [恢复发现报告](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d_20261118_01/Route_D_Recovery_Discovery_Result.md)。

Pro 首次成功不是宿主重放正确路线：它逐步探索 shelf 6/7/8、armchair 1/2，从真实观察发现第二个不同实例，再返回 shelf 1 放回手中的 keychain 2，取出 keychain 3 并送到同一容器。第 27 个总环境动作（第 11 个恢复动作）返回 won=true。第二次在第 24 个总动作完成。两次起点均为真实第 16 步后的状态，最多允许 34 步；没有泄漏原失败第 17—50 步、私有目标或未来位置。

按预注册顺序，P2 使用 Pro 第一次的 11 步成功轨迹，没有选择更短的第二次。两组 P1 初始公开上下文哈希相同；P2 初稿的系统提示与用户材料逐字相同。材料由第 41 局完整历史失败、选定的真实成功恢复及统一接口组成，不包含宿主写的正确程序。Pro 成功不能计作 Flash 自己发现恢复路线。

**Skill Compilation：源码交付和执行失败分开记录。**

| 版本 | 分类 | 第 41 局技能动作 | 第 41 局 won | 第 23 局零动作拒绝 |
| --- | --- | ---: | --- | --- |
| deepseek-flash_v1 | STATIC_REJECTED | 未执行 | 未执行 | 未执行 |
| deepseek-flash_v2 | ACTION_LIMIT | 34 | False | True |
| deepseek-flash_v3 | ACTION_LIMIT | 34 | False | True |
| deepseek-v4-pro_v1 | CODE_NOT_DELIVERED | 未执行 | 未执行 | 未执行 |
| deepseek-v4-pro_v2 | CODE_NOT_DELIVERED | 未执行 | 未执行 | 未执行 |
| deepseek-v4-pro_v3 | CODE_NOT_DELIVERED | 未执行 | 未执行 | 未执行 |

Flash v1 已给出源码，但使用了禁止的 `nonlocal`，被既有静态权限检查拒绝，没有环境执行。v2 删除了该声明，通过静态检查，但第 41 局的 34 个动作全部为导航，没有拾取或投递；v3 与 v2 源码逐字相同，行为未改善。两份可执行版本对 12/107/23 均零动作拒绝（理由为目标不含 keychain）；这说明其作用范围被缩窄，不应把这些拒绝写成整局恢复成功。两版没有实际触发错误完成声明，也没有执行异常。

Flash 源码检查可解释其行为：内部 ingest 函数中的 current_loc 赋值只改变局部变量，外层位置保持为空；持物解析只识别 `You are carrying ...`，未从真实 `You pick up ...` 回执重建当前持物。历史放置记录只增加、不在取回时撤销，仍跨容器累计物件；该计数缺陷本轮未触发完成声明，不能冒充实测误完成。模型增加了位置/物件记忆和探索规则，但没有把关键状态更新落实成可工作的程序。该分析在执行后形成，没有反馈给 Pro 或人工修改源码。

Pro 三次响应的 `finish_reason` 都是 length，`content` 长度为 0；每次 completion_tokens=16,384，且全部记为 reasoning_tokens。因此没有可提取的 Python，更没有程序环境失败。不是因额外 JSON 元数据拒绝源码，也不是输入被截断；是冻结的思考与最终输出合用额度被耗尽。详见 [Pro 交付证据](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d_20261118_01/Pro_Compilation_Delivery.json)。三次都计费、占名额，不追加免费格式修复。不能据此断言 Pro 无法归纳程序，只能说本配置和预算没有交付可执行程序。

所有修订保留当前完整源码、具体诊断及最后执行版本。Flash v3 收到的是 v2 完整源码与真实逐步行为；Pro 没有完整源码时明确保留“无可执行提交”的状态。编译输入每轮只含共同材料和最新反馈，没有不断叠加旧日志。完整请求均通过新的容量检查，没有复现上一轮本地 100,000 字节限制导致的未发送，也没有静默截断。

**Skill Transfer：未执行。** 两个可执行候选在第 41 局都未通过，未选定迁移候选。没有读取新测试游戏，没有运行 P4 或新的 G/R/F，也没有使用失败候选硬做迁移。不能报告新增获胜游戏、节省原生调用或正常任务无退化；第 23 局无动作拒绝只支持该边界检查点未改变。

| 实际资源 | 数量 |
| --- | ---: |
| P1 模型请求 | 35 |
| P2 生成/修订请求 | 6 |
| 总逻辑请求／实际 POST／完整响应 | 41 / 41 / 41 |
| 实际 tokens | 196,105 |
| 保守费用预留 | $1.792350 |
| 供应商实际账单 | 未知 |
| P1 环境动作 | 88＝64 前缀＋24 恢复 |
| P3 环境动作 | 226＝158 前缀＋68 技能 |
| P0 前缀动作 | 16 |
| 全部环境动作 | 330 |
| Worker 调用 | 74 |
| 新采集游戏 | 0 |

Flash 共 18 次模型请求、74,201 tokens，保守预留 $0.323009；Pro 共 23 次、121,904 tokens，保守预留 $1.469341。没有 UNKNOWN、未决调用、自动重发或未记账推理。预留不是实际供应商扣费，额外思考也不是免费收益。4 次 P1 尝试来自同一游戏；P3 只执行 4 个既有开发游戏上的 8 个分支（两版各四个），不把重复执行或请求数算作新数据来源。P0 加 P1/P3 合计 13 次 reset。新编译提交 6 版，但只有 3 份完整源码、2 份不同源码；真正执行 2 个版本，其源码相同。

本轮还有一项需要保留的计时限制：沿用的网络传输把 120 秒设为 socket 等待超时，并非整个 POST 的绝对墙钟截止；Pro 三次编译实际分别耗时约 250、239、268 秒。协议中“单次响应 120 秒”的文字比实现更严格，不能宣称严格满足该逐请求墙钟上限。总执行仍在 6 小时上限内，模型请求、费用、环境和 Worker 均在冻结上限内。本轮没有事后改配置或重跑消除这一差异。

结论范围：在这组公开信息和原剩余额度内，Pro 已展示直接恢复能力；Flash 的失败包含动作合法性问题。使用同一条真实成功恢复经验后，当前编译流程仍未产出有效来源技能，表现为 Flash 的程序状态维护错误以及 Pro 的思考额度耗尽导致无源码交付。下一步应针对经验到程序的编译与完整源码交付研究，避免继续增加直接探索次数。这不是纯失败信息优势、整个 FlowEvo 成功率提升、跨场景迁移或某模型能力上限的证据。

[协议](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d_20261118_01/Route_D_Protocol.md) · [恢复发现报告](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d_20261118_01/Route_D_Recovery_Discovery_Result.md) · [技能编译报告](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d_20261118_01/Route_D_Skill_Compilation_Result.md) · [机器结果](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d_20261118_01/Results.json) · [逐版本 CSV](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d_20261118_01/Compilation_Results.csv) · [只读核对](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d_20261118_01/Validation.json) · [原始响应、源码、执行与账本](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_d_20261118_01)。
