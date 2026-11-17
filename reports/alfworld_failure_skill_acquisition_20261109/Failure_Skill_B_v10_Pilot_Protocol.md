# B v10 真实条件学习 Pilot 冻结协议

状态为 `PREPARED_NOT_AUTHORIZED`。Run ID 为 `real:alfworld_precondition_v10_pilot_20261111_01`。模型使用 `deepseek-flash`，温度 0，关闭 thinking，JSON object，最多 4,096 输出 Token。供应商当前公开映射为 DeepSeek-V4.1-Flash-1017。[DeepSeek 模型与定价](https://api-docs.deepseek.com/quick_start/pricing/)

唯一付费请求为 P，使用一个冻结机制及其 11 条公开来源轨迹。V 对 36 条开发记录进行本地计算，模型请求数为 0。无修复、续写或重采样额度。

| 项目 | 上限 |
|---|---:|
| P 请求 | 1 |
| 输入预留，序列化字节加 256 的保守上界 | 52,046 |
| 输出 Token | 4,096 |
| Token 预算 | 56,142 |
| 峰时无缓存分项报价估算 | $0.020529 |
| 账本及独立授权上限 | $0.067371 |

报价按输入未命中缓存 $0.30/百万、输出 $1.20/百万。账本按较高费率预留全部 Token，实际账单由供应商结算。[DeepSeek 模型与定价](https://api-docs.deepseek.com/quick_start/pricing/)

- 协议 SHA-256 `45c62eeda5f0f231a5d31de6bb2e9d9be02c962fed243d7d1f416b650e92f57d`
- 学习输入 SHA-256 `b19d25e4da71fbe48283ce1634e14bd817418e427d0d2b589f67c43ac8693ef9`
- 验证公开输入 SHA-256 `070125b016118389bc0a0df5f129f4e0acef77333b133d4f1e7ba0b89b63684d`
- 参考标签 SHA-256 `4f0cc4e949a87dfd03e8cff823835c4155b79096eeecd7d30cb28be1c62217ac`
- Mock 结果 SHA-256 `093531a4868448a6ddf2e4030c4a6938367e23df1d179d2b0c0da45beb39bc3c`

本机冻结目录为 `~/.local/share/flowevo/alfworld_precondition_v10_pilot_20261111_01`。协议同时绑定代码、请求哈希、机制来源、模型参数、历史快照和 Mock 回执。授权模板保持关闭，需针对本轮 Run、协议、模型和额度的独立授权。

```sh
cd "/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments"
export PYTHONPATH="FlowEvo/src:scripts"
base="$HOME/.local/share/flowevo"
run_root="$base/alfworld_precondition_v10_pilot_20261111_01"
"$base/alfworld_baseline_20261107/venv/bin/python" scripts/run_alfworld_precondition_v10.py run \
  --base "$base" \
  --output "$run_root" \
  --authorization "$run_root/authorization.json"
```

同一 Run 的已结算请求可复用回执。发送后 UNKNOWN 阻断续跑和自动重发。协议、数据、预算和授权漂移也会阻断。返回格式错误、模型弃权或能力不支持时保留原响应和结算事实，结果按对应阶段状态报告。

工程已具备真实条件学习 Pilot 的运行条件。实际有效条件产出、公开证据在新场景中的覆盖和完整恢复策略的执行效果仍待验证。
