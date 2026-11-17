# ALFWorld 单机制 Python 恢复技能 Pilot 协议

运行身份为 `real:python_recovery_container_pilot_20261112_01`，协议版本为 `alfworld-python-recovery-container-pilot-v1`。规范化协议 SHA-256 为 `2be1114573c96f296cf46776c4c658c4cc9ef69aab3b13290abfc113921d314e`。冻结配置和待授权模板已生成，真实模型请求为 0。 [冻结配置](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/protocol.json>)、[预检回执](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/preflight.json>)、[授权模板](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/python_recovery_container_pilot_20261112_01/authorization.template.json>)

## 1. 研究问题与来源

1. Q1 检验初稿或最多两次修订能否通过现有 Python 安全检查。
2. Q2 检验通过检查的源码能否由 Linux Worker 执行，并在真实 TextWorld 来源状态产生合法且与原局部失败相关的动作。
3. Q3 在候选执行后仍未完成恢复时，检验它自身的公开执行反馈能否带来同一来源状态上的修复改善。

Q1 未通过时，Q2 和 Q3 记为未触达。初稿已满足来源恢复标准时，按实际表现结案。归纳机制来自历史模型，所有来源属于已曝光开发数据，本轮衡量的是固定机制下的代码交付与修订可行性。

基线提交为 `1e276ed0103af24fd874625559b2450135d2a9de`，冻结文件记录当前工作树的 123 份源码与 1,004 份历史文件哈希。系统完整核对 B v14 和扩展 Pilot 的三机制、合并响应、证据 ID、锚点和来源回执，逐一检查所用游戏及轨迹文件 SHA-256，再按 `container_precondition` 和检查点清单哈希选取一个机制。台灯和导航只参与这一步历史完整性检查。 [选择与绑定代码](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:103>)

| 来源顺序 | 失败后锚点步数 | 候选动作上限 |
| --- | ---: | ---: |
| 33、40、47、54、66、70 | 5、6、8、5、7、5 | 各 18 |
| 72、86、88、94、106 | 38、38、39、37、37 | 12、12、11、13、13 |

- 检查点规范化 SHA-256 为 `1a606e4ad09804f09843a316262c84ac0fd195ad8a39073fb23841ac01081fcd`。
- 容器初稿 wire SHA-256 为 `4b636bb7cfeb79511009d4b213e416701b5a8caf9dfcdc3302417dc55a067574`，与结案的旧 Pilot 容器初稿一致。
- 新账本只导入这 11 条证据。初稿接收已归纳机制、公开动作与观察、锚点合法动作，以及原协议允许的真实恢复后缀。私有评分见证、人工路线、探针位置、开发边界和独立 Gate 结果均在模型输入之外。

## 2. 初稿、修订与反馈

冻结请求依次为 `initial`、`revision_01`、`revision_02`。每个槽位最多消费一次。供应商、消息封套、参数和输出接口沿用现有实现。请求模型为 `deepseek-flash`，非思考模式、temperature 0、非流式、JSON 对象，Pydantic 严格验收。DeepSeek 官方标注该别名对应 DeepSeek-V4.1-Flash-1017，返回模型字段、响应 ID 和供应商指纹随真实回执记录。 [DeepSeek 模型与计价](https://api-docs.deepseek.com/quick_start/pricing/)

- 初稿需完整交付 `environment_operator(context)` Python 源码，允许返回 `ABSTAIN`。归档原始响应、完整解码源码、SHA-256、交付与静态检查结果。宿主按字节保存模型提交。
- 静态拒绝时，修订接收最近正式解码的完整源码、逐处违规位置、AST 节点类型及允许结构。记录违规节点的结构哈希、移除和新增数量，以及剩余修订槽位。两处减为一处时可继续修订。单纯位移、注释与格式变化不产生新诊断。
- 完整供应商响应违反单 JSON 对象交付时，保留拒收响应并传递诊断及其归档引用。后续请求保留最近正式解码的完整源码和其静态诊断。供应商标注为截断或未完成时记录 `DELIVERY_INCOMPLETE`，结束候选生成。
- 静态通过后若来源仍有未完成恢复，修订可接收本候选的合法动作、观察、进展、可公开的异常类别及终止状态。参考动作、未执行替代路线和环境评分见证留在宿主。超长反馈按冻结规则投影，保留所有来源的首尾步骤、遗漏区间和完整反馈哈希。正式源码与诊断保持完整。仍超限则按 `INPUT_LIMIT` 结案。 [反馈投影代码](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/FlowEvo/src/alfworld_/python_recovery_feedback.py:247>)

## 3. 来源执行与开发边界

静态通过的精确源码进入既有 Shadow Registry。宿主核对解码源码、注册工件与 Worker 回执中的 SHA-256。Worker 从当前公开 `goal`、观察、合法命令、已发生的动作与观察以及自己的有界 JSON 状态选择一个动作或拒绝。每次重新评估从同一个原始失败后状态重放，实际执行动作由宿主按合法动作表核准。每个来源的动作窗口为 `min(18, 50 - 前缀步数)`。

来源回执分别保存静态通过、Worker 执行、首动作执行、首动作反馈或状态变化、局部修复、恢复完成、环境 `won` 以及拒绝和异常。一般观察变化只计为状态变化。局部修复由冻结评分器检查来源的关键动作在目标实例上恢复可用，或环境分数与胜利见证。恢复完成使用实际分数进展或获胜。整局胜利读取 `won`，局部修复可以先于胜利。 [来源执行与计分](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:557>)

所有学习请求结案后，逐版本运行原有 21 条开发边界，其中 18 条明确不适用、3 条信息不足。独立记录错误接受、信息不足时的触发和执行异常。同源码且同上下文引用原评估。报告保留全部提交及最后提交，边界结果不会进入修订或改变来源检查点。候选只留在 Shadow，独立 Gate 执行次数固定为 0。

最终汇总记录首次静态通过、首次来源 Worker 执行、首次 TextWorld 动作。获得实际来源反馈后若提交新版，以同一检查点配对列出局部修复、恢复完成和获胜的改善与退化。任一阶段未执行时保留未触达状态。 [结果汇总代码](</Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/scripts/run_alfworld_python_recovery_feedback.py:918>)

## 4. 冻结预算

| 槽位 | 输入保守代理上限 | 最大输出 Token | 峰时无缓存报价上界 | 账本预留上界 |
| --- | ---: | ---: | ---: | ---: |
| `initial` | 22,240 | 4,096 | $0.0115872 | $0.031604 |
| `revision_01` | 65,536 | 4,096 | $0.0245760 | $0.083559 |
| `revision_02` | 65,536 | 4,096 | $0.0245760 | $0.083559 |
| 合计 | 153,312 | 12,288 | $0.0607392 | $0.198722 |

账本总 Token 预留上限为 **165,600**，费用硬上限为 **$0.20**。初稿规范化 wire 为 **21,984 UTF-8 字节**，其中系统消息 3,311 字节、证据消息 16,540 字节。保守代理为 wire 字节数加 256。同哈希历史请求实测输入 5,708 Token，本轮实际 Token 以供应商回执为准。修订压力测试按 169 个来源决策槽位构造，用冻结投影将输入代理压到 53,207，保留完整夹具源码。

峰时无缓存输入按 $0.30/百万 Token、输出按 $1.20/百万 Token 估算，账本对输入和输出统一按 $1.20/百万 Token 向上取整预留。真实计量、保守预算占用和实际账单分开存储。没有附加评审、格式修复或原生求解模型请求。 [DeepSeek 模型与计价](https://api-docs.deepseek.com/quick_start/pricing/)

- 环境每版最多重放 225 步原始前缀并执行 169 步候选动作。三个版本最多 1,182 步，另留 468 步给已确认中断后的确定性重放，账本硬上限 1,650 步。
- Worker 上限为 `3 × (169 + 21) = 570` 次，按每次 15 秒预留累计 8,550 秒。候选函数调用沿用 2 秒参数。Linux 镜像、Worker 脚本、运行包版本、游戏逻辑哈希以及全程 86,400 秒账本时间窗均已冻结。安全隔离沿用已有无网络、只读容器及资源限额。
- 只在能确认未发送时使用冻结的连接恢复规则。原始传输状态未知、已收到响应但本地回执未闭合、预算不足、环境前缀不一致、Worker 基础设施异常或源码配置漂移均保全现场。已结算且回执完整的请求按原版本复用，已确认环境状态可按预算重放。

## 5. 终端命令和授权

当前目录已经执行 `prepare`。下面的命令仅复核预检。

```zsh
repo="/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments"
pilot_dir="$repo/runs/python_recovery_container_pilot_20261112_01"
py="$HOME/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python"
entry="$repo/scripts/run_alfworld_python_recovery_container_pilot.py"
cd "$repo"
export PYTHONPATH="$repo/FlowEvo/src:$repo/scripts" PYTHONDONTWRITEBYTECODE=1
"$py" "$entry" preflight --output "$pilot_dir"
```

当前只存在 `authorization.template.json`，其内容为

```json
{
  "run_id": "real:python_recovery_container_pilot_20261112_01",
  "protocol_hash": "2be1114573c96f296cf46776c4c658c4cc9ef69aab3b13290abfc113921d314e",
  "model": "deepseek-flash",
  "protocol": "alfworld-python-recovery-container-pilot-v1",
  "max_cost_microusd": 200000,
  "paid_api_authorized": false
}
```

取得本轮明确授权后，另建匹配的 `authorization.json`，保留模板的身份和额度字段，将授权标志设为 `true`。首次运行用 `run`，可恢复的中断用同一个 Run 的 `resume`。以下是授权后的命令。

```zsh
caffeinate -i "$py" -u "$entry" run --output "$pilot_dir" \
  --authorization "$pilot_dir/authorization.json"
```

```zsh
caffeinate -i "$py" -u "$entry" resume --output "$pilot_dir" \
  --authorization "$pilot_dir/authorization.json"
```
