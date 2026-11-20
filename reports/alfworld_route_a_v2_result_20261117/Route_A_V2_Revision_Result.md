# Route A V2：一次真实门控修订与开发验证

**结果：DEVELOPMENT_NO_GO。** 真实模型交付完整源码并通过静态检查，但未修复已知的形容词处理前提遗漏。完成全部61条曝光开发回归及30条工程词形/实例检查；按预定否决条件停止，新的48局和在线60局均未执行。

## 一次请求及产物来源

- 用户授权：最多1次门控修订，上限$1，不包含在线实验。
- 冻结协议：`6016191eb157d1cbfbdf02c252689d268b7b60eaebb532009a170b87137947f3`；实际wire与冻结一致。
- 模型：DeepSeek Flash，thinking disabled，temperature0，输出上限4096；供应商 finish_reason=`stop`。完整JSON及源码均由模型返回，无宿主策略补写、无第二次请求。
- 父门控SHA：`5d92dd91b7bec7d514112f6bfef5814f381a4f8670f72a3807e7200b18de22fd`。
- 新门控SHA：`59e5747a1fcb6455119eff961cdd4ed8e0613a667189334ce836d38bc44783c6`。
- 新候选版本：`398a6d5d7fbb90766d19b713622fd86510e51b8ffe025f6c1fa35fbcba5fb97e`。
- 恢复源码保持：`233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37`。
- 新门控及恢复程序仅以Shadow执行；未发布或授予在线权限。

## 相同61条开发记录的配对结果

| 项目 | 旧门控 | 新门控 |
|---|---:|---:|
| 支持状态完整修复 | 34/34 | 34/34 |
| 明确不适用状态错误介入 | 0/9 | 0/9 |
| 证据不足状态无证据介入 | 3/18 | 3/18 |
| 接口/执行错误 | 0 | 0 |

61条记录并非61个独立游戏；本轮完全继承旧检查点、标签、物理状态和评分依据。新旧门控判断相同的记录为61/61；已知无证据介入修复0条，旧正确修复退化0条。正例游戏级指标仍需与记录级分开读取。

## 工程词形与实例检查

在读取新源码之前，另行冻结30条工程检查，覆盖简单放置、hot/heated、cold/cool/cooled、clean/cleaned、处理证据缺失、不同物体处理及显式目标实例冲突。它们来自曝光公开上下文的显式工程改写；没有冒充真实新游戏、独立负例或原生Agent自发失败。其数据未进入本轮模型请求。

通过20/30。失败项：hot_processing_not_disclosed, hot_other_object_processed, heated_processing_not_disclosed, heated_other_object_processed, cold_processing_not_disclosed, cold_other_object_processed, cooled_processing_not_disclosed, cooled_other_object_processed, cleaned_processing_not_disclosed, cleaned_other_object_processed。

这些检查只使用Linux Worker读取上下文，没有环境动作。缺失证据或冲突允许DECLINE/UNKNOWN，但ERROR一律不通过。未修改模型源码使测试通过。

## 为什么没修好

模型在交付说明中声称包括形容词处理要求；实际源码仍先移除物体短语修饰，再用完整动词检查处理要求：

```python
def _processing_required(goal):
    g = _low(goal)
    for verb in _PROC:
        if re.search('\\b' + verb + '\\b', g):
            return verb
    return None
```

这会使 `hot`、`cold` 等描述不能产生对应的处理前提。`clean`、`cool` 因恰好与动作动词相同而表现不同。问题属于**模型修订未落实到可执行逻辑**，不是JSON截断、Worker拒绝或网络错误。不能把“描述说已修复”视为功能修复。

旧的三条无证据介入在新版本中仍出现；相关分支后来实际获胜。这证明的是公开前提门控未满足，而不是已经观察到整局损害。真实在线发生率、与原生FlowEvo相比的胜负和负迁移仍未测量。

## 成本与资源

- 真实模型调用1次；输入24,688、输出2,543、总计27,231 Token。
- 其中cache hit 256、cache miss 24432。
- 按调用时段和供应商公开单价估算API费用 **$0.01038274**，未核对账单；与预算账本中的保守扣占 **$0.114690** 分开报告，不能把预留当作实际消费。[DeepSeek计价依据](https://api-docs.deepseek.com/quick_start/pricing/)
- 开发环境步数：816（包括前缀重放和候选动作）。工程词形测试环境步数0。完整Worker与预算记录保存在受控Run目录。
- 旧算法获取费用不抹除，本段只统计本轮增量开销。

## 停止与下一阶段边界

本轮已用完1次请求机会，虽然远未用完$1金额，也不会补采样或增加修订。候选源码、原始响应、反馈和所有失败结果保留。

新的48局只完成元数据冻结，没有构造或执行检查点，仍保持本轮未曝光。原封存60局清单保持原哈希，没有运行G或G＋Route A。由于开发安全失败，不进入独立确认，也不存在在线实验GO。

后续若另行研究修订方法，应首先检查模型是否真的改变了目标前提谓词，再进行有界开发验证；不得人工补好门控后继续把它记为本次模型学习成果。阶段与实例冲突的可信独立标签覆盖仍是后续确认阶段的单独问题。
