# B v9 真实 Pilot 冻结协议

状态为 `PREPARED_NOT_AUTHORIZED`。Run ID 为 `real:alfworld_decision_v9_pilot_20261111_01`。模型为 `deepseek-flash`，温度 0，关闭 thinking，使用 JSON object，D/S 每请求均允许 4,096 输出 Token。供应商定价页当前将该别名映射为 DeepSeek-V4.1-Flash-1017。真实模型版本以后续返回为准。[DeepSeek 模型与定价](https://api-docs.deepseek.com/quick_start/pricing/)

D/S 各 6 批，每批 6 条，最多 12 次请求。每批计算实际序列化请求字节加 256 的保守输入上界。S Prompt 较长，因此两组在相同的单请求输入允许上限及输出上限下，冻结的实际输入预留不同。资源计量按组保存。

| 项目 | 上限 |
|---|---:|
| D 输入预留 | 49,136 |
| S 输入预留 | 75,614 |
| 两组输出预留 | 49,152 |
| 合计 Token 预算 | 173,902 |
| 按峰时无缓存分项报价估算 | $0.0964074 |
| 账本和独立授权上限 | $0.208687 |

峰时输入未命中缓存 $0.30/百万，输出 $1.20/百万。报价上界按输入输出分别估算。账本按较高输出单价预留所有 Token，每请求向上取整，实际账单由供应商结算。[DeepSeek 模型与定价](https://api-docs.deepseek.com/quick_start/pricing/)

- 协议 SHA-256 `11742ac1cb37418163ce9db40c22085fb6423432d970c592da34901edc299fae`
- 公开投影 SHA-256 `070125b016118389bc0a0df5f129f4e0acef77333b133d4f1e7ba0b89b63684d`
- 参考标签 SHA-256 `b88c0c5695059f141dc63784da8342044d723b3f2ecca869d6899658f9ec20ef`
- Mock 协议 SHA-256 `0193256505c6c9663dc7848ffa0c806cd75f04f3cfc34903c8382213e87c6c47`
- Mock 结果文件 SHA-256 `f4e32b612a62f2fb03dbd85d34aa39b987dc50a554fd1bb1ce349744198443c5`
- v8 只读回放文件 SHA-256 `937d4bc23290cc9fdf8d85142469a2c6daac0a422b206ab7f5e14aefce5ab044`

本机冻结目录为 `~/.local/share/flowevo/alfworld_decision_v9_pilot_20261111_01`。协议记录逐批请求哈希、代码和历史文件哈希以及计量配置。授权模板处于禁用状态。用户明确批准后，才可使用与本轮 Run、协议 SHA、模型及费用上限完全一致的独立授权文件。

```sh
cd "/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments"
export PYTHONPATH="FlowEvo/src:scripts"
base="$HOME/.local/share/flowevo"
run_root="$base/alfworld_decision_v9_pilot_20261111_01"
"$base/alfworld_baseline_20261107/venv/bin/python" scripts/run_alfworld_decision_v9.py run \
  --v8 "$base/alfworld_binding_v8_pilot_20261111_01" \
  --output "$run_root" \
  --authorization "$run_root/authorization.json"
```

可计量的格式错误记录为交付失败，继续其余冻结批次。授权、预算、协议或数据不符，以及发送后状态 UNKNOWN 会阻断后续请求。确认未发送的网络中断按既有冻结策略处理，已结算请求复用原回执。中断后使用同一命令及相同 Run 目录恢复。结果文件分别保存 D/S 的原始决定、字段拒收、一致性检查、参考评分和成本。
