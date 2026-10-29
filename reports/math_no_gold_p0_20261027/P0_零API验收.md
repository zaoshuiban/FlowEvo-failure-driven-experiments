# P0：Mock模型与真实Worker验收

最终验收：`acceptance04/summary.json`；21/21通过，0次真实模型请求。实际调用本机Linux Docker隔离Worker，Mock只替换模型发送器，未替换算子执行和私有评分路径。

测试启动器禁用Python HTTP发送；Mock要求engineering命名空间。实际wire、响应、预算、算子源码、开发/Gate结果、发布和暂停日志保留在 `acceptance04/fixtures/`。

| 验收内容 | 实际结果 |
|---|---|
| 改变私有gold | 两次求解wire及固定调用次数不变 |
| 错误APPLIED答案 | 锁定后私有判错，模型调用仍0，无补救 |
| DECLINED / 执行ERROR | 前者真实Controller回退；后者Worker如实输出ERROR |
| GPT来源至独立任务 | Mock完整源码经真实Worker完成来源/Design/Gate和后续不同题面计算 |
| 非适用输入 | 拒绝并回退固定两调用 |
| 静态安全 | 网络、文件、反射被拒；源码哈希变化阻断 |
| 资源限制 | 无限循环由真实Worker超时终止 |
| 模块关闭 | 不调用算子库，原生no_gold两调用 |
| 旧入口 | cfg.no_gold真实进入新通道；旧verify仍保留历史行为 |
| 来源失败 | 保存Shadow，诊断修订最多一次，记录父哈希 |
| Gate失败 | 不准入，不再生成或换候选重测Gate |
| 无机制/仅假设 | 正常停止，无源码请求 |
| 自题及同序号 | 不能使用刚发布版本或自身来源版本 |
| 暂停 | 后续不再返回版本 |
| 未授权 | 两个真实通道均在发送前拒绝 |
| UNKNOWN | GPT与DeepSeek模拟异常后不重复发送 |
| 私有字段/未来反馈 | 公共投影拒绝额外字段，Gate和gold诊断不能进入修订 |
| 符号非匹配 | 不进入可信失败池 |
| 数据角色及哈希 | 672题跨角色无ID重叠，所有存档文件哈希吻合 |

旧autonomous_mvp回归另运行17项：12通过，5项因未启用旧隔离配置跳过。不能将其写成17项全部通过；新数学真实Worker测试已单独执行。

复验命令（必须使用新的输出目录，不覆盖历史验收）：

```sh
/Users/majiatong/lab/AFlow/.venv/bin/python scripts/accept_math_no_gold.py --output reports/math_no_gold_p0_20261027/new_acceptance
```

Mock源码是显式工程夹具，既未进入真实Discovery，也不是GPT实际学习结果。实际学习机制数、真实生成数、来源效果、正式复用次数均为0/尚未测量。
