# 首次真实 Operator 生成：Shadow-only 结果

日期：2026-10-21。Run ID：s12b_shadow_20261021_01。

**结论：已完成一次真实规格归纳和三次真实候选生成请求；归纳成功，三个候选请求均因输出契约不合格失败。实际生成的 Python Operator 源码为 0。三个返回均作为 Shadow 失败草稿保留，没有执行、门控或权限晋级。**

## 范围与授权

本轮依据用户最新指令运行：不要求先搭建 Linux，只进行可信失败证据驱动的真实 DeepSeek 生成、静态和接口检查。使用已有 $0.60 生成硬上限，进一步将本轮限制为 4 个请求（归纳 1 + 候选 3），无修订、无自动重试。没有开展评价器执行、Experimental、Active、第二机制族或 S2/S3。

protocol.json 在调用前记录输入、预算、授权范围、基础提交 e70e8da3 及实际源码哈希。API 密钥来自 Git 忽略的本地配置，没有写入实验记录。生成脚本在执行结束后增加了“已有 result.json 时拒绝再次启动”的保护；它不改变已执行请求。

## 可信输入

采用 A2 固定的 lcb_atcoder_abc371_f:l2b 真实空代码事件，以及此前 l2a 的完整程序。请求前校验输入哈希、FailureEvidenceStore 中真实且可见的事实、所有候选源码哈希。只使用截至 l2b 的历史开发材料和公开题面样例，不使用隐藏判题结果或未来程序。

该见证只证明存在产物退化，不证明先前程序正确。没有可靠公开执行结果，因此模型不能假定旧候选已通过测试。历史开发材料不构成独立门控数据。

## 实际请求结果

| 请求 | 返回 | 判定 |
|---|---|---|
| 规格归纳 | specification 字符串 | 已保存 specification.txt |
| 候选 1 | status=declined 的动作 JSON | FAIL：缺少 code 字段和 Python 源码 |
| 候选 2 | status=declined 的动作 JSON | FAIL：缺少 code 字段和 Python 源码 |
| 候选 3 | status=declined 的动作 JSON | FAIL：缺少 code 字段和 Python 源码 |

实际返回模型均为 deepseek-flash，system_fingerprint 均为 e72d3c7f663d3e1383b00b3884cb4501。四次 finish_reason 均为 stop，不是输出 Token 截断。

三个返回都指出当前代码为空、公开验证不可用，应保守拒绝。这种判断属于 Operator **运行时动作**，不是所请求的 Operator **源码制品**。不能人工将动作 JSON 包装成函数，再声称代码由模型生成。

## 静态与接口检查

- 三个响应的生成接口检查均失败：期待包含 code 字符串的 JSON，实际仅有 status/reason。
- 没有源码，因此 Python 语法、源码权限策略与函数签名检查均不可执行；不把它们记为通过。
- 本轮未运行任何生成源码，工具执行次数 0。
- 三个原始响应保存为 candidate_1.response.json、candidate_2.response.json、candidate_3.response.json；shadow_drafts.json 记录 Shadow 草稿身份和失败原因。
- 无有效代码制品，因此没有注册 FailureOperator 卡片；没有 Experimental 授权。Shadow 草稿保留不等于可执行算子已入库。

## 成本与完整记录

PersistentBudget 在每个请求之前持久化预留，返回后结算 Token；请求、原始响应、规格和预算均保留在 compiler.jsonl、generated_artifacts、budget.jsonl。

| 项目 | 数值 |
|---|---:|
| 实际模型请求 | 4 |
| 输入 Token | 17326 |
| 输出 Token | 419 |
| 总 Token | 17745 |
| 已报告缓存命中输入 Token | 7040 |
| 推理 Token | 响应未单独报告；请求已关闭 thinking |
| 工具/Operator 执行 | 0 |
| 重试/修订 | 0 |
| 生成费用硬上限 | $0.60 |
| 当前保留的货币预留 | $0.101183 |
| 按高峰价且忽略缓存优惠估算的用量费用 | $0.0057006 |
| 实际账单金额 | 未知，未查询账单 |

用量估算采用输入 $0.30/百万 Token、输出 $1.20/百万 Token，来源为本日已核对的 [DeepSeek 官方价格](https://api-docs.deepseek.com/quick_start/pricing/)。这不是实际账单金额。账本继续保留未知货币成本对应的请求上界，没有自动退款。

## 研究判断与下一步

本轮证明可信失败能够触发真实模型调用并形成有界、可追溯的生成记录，但**没有证明模型已生成可执行 Operator，更没有证明算子有效**。本次失败属于输出契约层级错误，不是独立门控失败。

生成提示同时描述了顶层源码 JSON 与函数运行时动作 JSON，模型实际返回了后者，提示层级区分不足是需要修正的因素。下一轮应把候选阶段的顶层输出严格限定为 code，明确“不执行当前检查点决策；即使该检查点应拒绝，也必须生成实现拒绝逻辑的函数”。这不要求扩大 Operator 权限。

本轮已停止，没有用额外付费请求掩盖失败，也没有手工替代模型代码。若后续再生成，需采用新的明确协议和运行记录；已有三次失败及其费用必须保留。
