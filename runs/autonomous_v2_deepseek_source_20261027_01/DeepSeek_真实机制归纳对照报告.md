# DeepSeek 替换生成模型：真实机制归纳对照

2026-10-27。用户明确要求“换成DeepSeek试一下”，沿用本轮授权，另建Run：`autonomous_v2_deepseek_source_20261027_01`。结论：**HYPOTHESIS_ONLY，未进入源码生成，正常停止。**

## 本轮做了什么

使用DeepSeek官方API的 `deepseek-flash`，官方当前版本标识DeepSeek-V4.1-Flash-1017，temperature=0、thinking=disabled、reasoning_effort=none。从原始失败重新归纳，不复用GPT归纳结果、不提供GPT代码、不提供人工目标算法。

输入是此前同一真实来源 `s18_taco-test-91` 的最早合法公开检查点。来源题面、错误源码、公开反馈、宿主合法性审计及4个冻结开发控制与GPT运行的JSON逐对象相等，见input_parity.json。生成仅看到来源证据；开发控制不进入请求，119确认池和419学习流均未使用。

先用真实Linux Worker再次确认来源程序公开0/3，再发送1次机制归纳请求。宿主契约解析通过；模型返回HYPOTHESIS_ONLY。模型响应、机制原文、时间边界、hash、预算与历史完整性检查均已保存。

## DeepSeek的判断

模型观察到：源码大量重复讨论small-to-large集合合并及偏移问题，没有提交完成的合并逻辑和最终输出。它提出“检测并打断未完成实现的反复讨论”这一假设，但保留了三点不确定性：预期的奇偶聚合算法是否正确、空输出的具体原因、是否属于长度截断造成的现象。

这些均属于模型提出的假设，不是宿主验证的根因。模型在transferable_operation中提到一种具体合并方向，但最终decision仍为HYPOTHESIS_ONLY，系统不得自行把它升级为PROPOSE。部分疑问（如被宿主吞掉异常）尚无证据支持；本轮没有据此重写失败标签。

因此不调用源码生成器、不强制修订、不将结果算作来源修复失败。机制以UNVERIFIED记录保留，没有生成可执行候选，也没有注册Experimental。

## 与GPT上轮比较

| 指标 | GPT-5.4 | DeepSeek Flash |
|---|---|---|
| 来源材料 | 相同真实失败 | 相同真实失败 |
| 归纳决策 | PROPOSE | HYPOTHESIS_ONLY |
| 实际请求 | 2：归纳＋生成 | 1：归纳 |
| 完整算子源码 | 1份 | 0份 |
| 来源验证 | 0/3→3/3 | 未运行生成候选验证 |
| 非来源题介入 | 4个开发控制均拒绝 | 无候选，未执行 |
| 独立确认 | 无 | 无 |
| 后续Hook | 0 | 0 |
| 状态 | 来源题专用源码，Shadow | 未验证假设，无算子 |
| 总Token | 23,153 | 8,253 |
| 费用估算USD | 0.1478075 | 0.0029637（保守峰值报价） |

这不是严格的模型能力排行榜。GPT使用medium推理和服务端JSON Schema；DeepSeek沿用既有非思考模式、json_object及宿主严格schema。源码生成阶段是否发生本身由模型归纳决策决定，所以总费用与成功数不能脱离阶段差异直接比较。只观察了一次同来源尝试，不能据此推断稳定优劣。

## 调用与费用

- 返回模型：deepseek-flash。
- 输入：7,711 tokens；缓存命中0，未命中7,711。
- 输出：542 tokens；total=8,253。
- finish_reason：stop；无UNKNOWN，无自动重发。
- 峰值输入$0.30/M、输出$1.20/M，估算$0.0029637；实际账单未取得。非峰值报价为其一半，报告不把保守报价视为实付。
- charged_or_reserved=$0.046551，为保守请求预留占用，不能当实际费用。
- 来源本地检查1次工具调用、约0.427秒，不含工程回归和准备时间。

原计划最多归纳1次、候选1次、修订1次，输入保守上界65,536、输出8,192，与GPT后续协议的资源范围一致。请求实际wire上界30,600。因HYPOTHESIS_ONLY提前正常结束；不是费用不足或基础设施中断。

## 工程改动和复现

- 新增 `autonomous_deepseek_v2.py`：显式DeepSeek生成配置；复用v2机制字段、原始源码契约、持久预算和单发送记录；不修改默认GPT生成器。
- 新增 `run_autonomous_v2_deepseek.py`：同来源冻结、原始证据一致性检查、来源重验及正常三态停止。
- 新增 `test_autonomous_deepseek_v2.py`：3项通过，覆盖GPT/DeepSeek公共输入与提示前缀一致、模型来源、最终wire上界、未授权拒绝、截断不成功及UNKNOWN不重发。
- 212项核心回归通过；git diff --check通过。

本轮工程结果与真实模型结果分别记录。旧GPT报告、历史账本及算子权限均未修改，没有推送远端。

## 研究结论

已验证DeepSeek能够接收相同真实失败并返回符合新协议的机制假设，也验证系统能够尊重“目前只保留假设”的决定。**尚未检验DeepSeek在这一新v2协议下的算子源码生成能力**，因为它本轮未选择PROPOSE。不能写成“DeepSeek生成算子失败”，也不能把保守拒绝本身计为学习收益。

GPT目前提供了来源专用可执行解法，DeepSeek此次提供了更保留的机制判断；两者都没有证明自然跨题可复用能力。本轮不为取得成功而修改Prompt、强迫生成或重复抽样。

依据：[DeepSeek官方型号及价格](https://api-docs.deepseek.com/quick_start/pricing/)、[JSON输出接口](https://api-docs.deepseek.com/guides/json_mode/)。冻结网页副本及hash见pricing_official.html、model_metadata.json。
