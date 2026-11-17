# B v11 真实跨机制 Pilot 冻结协议

状态为 `PREPARED_NOT_AUTHORIZED`。真实 Run ID 为 `real:alfworld_cross_mechanism_v11_pilot_20261111_01`，模型 `deepseek-flash`，温度 0，关闭 thinking，JSON object。供应商当前公开映射为 DeepSeek-V4.1-Flash-1017。[DeepSeek 模型与定价](https://api-docs.deepseek.com/quick_start/pricing/)

两次逐条分析、最多一次归并、最多两次 Structured 候选生成。候选排序和上限先于验证，不重新生成、修补或重采样。前两批输入预留由实际序列化字节加 256 计算，后续尚未知响应的三批各按 65,536 上界。每请求输出上限 4,096 Token。V 的来源与边界阶段只使用本地检查和 Worker。来源每个分支最多 18 个动作，且受原局剩余步数限制。

| 项目 | 上限 |
|---|---:|
| 模型请求 | 5 |
| 输入预留 | 259,727 |
| 输出 Token | 20,480 |
| 合计 Token | 280,207 |
| 峰时无缓存报价估算 | $0.1024941 |
| 账本及授权费用上限 | $0.336251 |
| Worker | 316 次，每次候选执行超时 2 秒 |

Worker 上限为 16 个不同来源各 18 次，另加两候选各 14 个边界检查。分支重复、无动作及已缓存结果不增加环境动作预算。Worker 启动与清理由已有账本另计，至多预留每次 15 秒。模型费用上界按峰时输入 $0.30/百万及输出 $1.20/百万估算，账本统一使用较高费率预留。[DeepSeek 模型与定价](https://api-docs.deepseek.com/quick_start/pricing/)

- 协议 SHA-256 `42abbe8aef052b6b1160f898c7e5e8c7f93dd01b908a68012247e8c6ec02be4d`
- 学习投影 SHA-256 `8c360533378a18070028d3faf5eb7fc1fbba7a1818b85d43dfcbbf39492d2448`
- 来源检查点 SHA-256 `bd03e85cc3320fd5c7e4751f960b00c40e0e1eb077de5022a72d5f86ccbcb636`
- 边界控制 SHA-256 `d3cfe97140fa75b11f75039aabffe20df00475207bc893fa6f09b6c0e6ae7752`
- Mock 结果 SHA-256 `06ef65d0b184b5a771907a56ed406b7a171c19caa3bc6f220683e5651d50f4cd`

冻结目录为 `~/.local/share/flowevo/alfworld_cross_mechanism_v11_pilot_20261111_01`。授权模板保持禁用。运行时需要与 Run ID、协议 SHA、模型及费用上限一致的独立授权。Free-Code 对照、原生模型后续求解及独立 Gate 需要另行冻结和授权。

```sh
cd "/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments"
export PYTHONPATH="FlowEvo/src:scripts"
base="$HOME/.local/share/flowevo"
run_root="$base/alfworld_cross_mechanism_v11_pilot_20261111_01"
"$base/alfworld_baseline_20261107/venv/bin/python" scripts/run_alfworld_cross_mechanism_v11.py run \
  --base "$base" \
  --output "$run_root" \
  --authorization "$run_root/authorization.json"
```

已结算模型回执与已完成 Worker 结果可在相同 Run 复用。模型发送后 UNKNOWN、Worker 中断待核、协议和账本漂移均阻断继续。候选拒绝、表示不支持和某一分层缺失保留在结果中。开发验证即使通过，产物权限仍为 Shadow。
