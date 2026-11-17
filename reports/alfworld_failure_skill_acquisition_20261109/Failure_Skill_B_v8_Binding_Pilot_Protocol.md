# B v8 真实诊断 Pilot 冻结协议

当前仅准备，不发付费请求。使用新的独立 Run ID alfworld_binding_v8_pilot_20261111_01。授权模板 paid_api_authorized=false，不能沿用 v7 授权。

36个冻结诊断记录，A与B分别每6条一批，各6请求，共12请求。顺序固定，A完成后运行B，但B不获得A输出。每批结构错误逐条拒绝，整体JSON不可解析则记录交付拒绝，继续未执行的冻结批次，不增加格式修复或重采样。本轮单次抽样，没有统计效力宣称。

配置为 deepseek-flash，temperature=0，thinking disabled，reasoning_effort none，JSON object，每请求最多4096输出Token，保守输入上界65536。模型别名当前文档对应 DeepSeek-V4.1-Flash-1017，真实供应商响应中的model原文另行保存，别名不能保证未来永不变更。

总Token上限835584。按峰时无缓存输入$0.30/百万、输出$1.20/百万，上界报价估算$0.294912。继承现有预算器按全部Token采用高费率保守预留，12次最高预留约$1.002708，待批准上限$1.01。预留、报价估算与实际账单分开，缓存/非峰时折扣未计入上界。定价核对于2026-11-11，正式授权前如报价变化应重新冻结。[DeepSeek官方定价](https://api-docs.deepseek.com/quick_start/pricing/)

复用原请求日志、BoundedCompiler、PersistentBudget和网络恢复。完整响应但解析拒绝不算传输UNKNOWN。SEND_UNKNOWN保持预留并全局停止，不自动重发。预算超限、协议/源码/数据哈希变化、历史工件变化同样停止。已结算请求按冻结身份重放。真实结果逐字段评分，记录原始响应、usage、finish_reason和报价估算，不产生策略或授权。

授权后使用如下入口，当前请勿运行。

```sh
cd "/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments"
export PYTHONPATH="FlowEvo/src:scripts"
base="$HOME/.local/share/flowevo"
py="$base/alfworld_baseline_20261107/venv/bin/python"
caffeinate -i "$py" -u scripts/run_alfworld_binding_v8.py run \
  --source "$base/alfworld_full_library_online120_20261109_01" \
  --v7 "$base/alfworld_recovery_v7_pilot_20261110_01" \
  --output "$base/alfworld_binding_v8_pilot_20261111_01" \
  --authorization "$base/alfworld_binding_v8_pilot_20261111_01/authorization.json"
```

authorization.json 只能在用户明确批准新诊断预算后，从冻结模板形成，必须匹配Run、模型、协议和金额。恢复使用相同命令，不改协议、不删除旧回执。不存在执行代码、开启Gate或正式发布的入口。

冻结协议 SHA-256 `2752020e1068eddc9066df33de4b55fd084a71b3302baca988bb62db25ea7ee8`。诊断数据 SHA-256 `927220f6ca23e887cca114078f992cadc1c0b21fa706d41a65e2144ae176b6e8`。
