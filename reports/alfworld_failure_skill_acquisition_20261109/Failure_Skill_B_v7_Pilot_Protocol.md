# B v7 真实 Pilot 冻结协议

输入为固定 v4 机制及其 11 条公开分析。只发 1 次源码生成请求，不归并、不自动修订、不续跑原生模型。供应商模型别名为 deepseek-flash，核对时官方映射为 DeepSeek-V4.1-Flash-1017。非思考、temperature 0、JSON，输入预留最多 65,536，输出最多 4,096。供应商实际响应版本、usage 和费用另行记录。 [DeepSeek 官方模型与计价](https://api-docs.deepseek.com/quick_start/pricing/)

以峰时未缓存输入 $0.30、输出 $1.20 每百万 Token 估算，请求上限为 $0.024576。按全部 69,632 Token 使用最高费率的保守预留为 $0.083559，硬上限 $0.09。Worker 至多 68 次，由四局各 12 步及 20 个负例组成。实际运行受任务剩余步数及同配置持久预算约束。 [DeepSeek 官方模型与计价](https://api-docs.deepseek.com/quick_start/pricing/)

冻结四个失败后检查点和原 20 个负例。只有局部修复 4/4、负例误触发 0/20、接口错误为 0 才达到开发标准。整局获胜单列。供应商响应截断、格式错误或静态拒绝时留原件并停止该候选。UNKNOWN、预算、环境重放和沙箱异常均按已有安全规则停止；已结算请求恢复时复用。无独立 Gate 运行及权限发布。真实启动要求同一冻结配置的零 API 证据及新授权文件。

实际冻结 Run ID 为 `real:B:alfworld_recovery_v7_pilot_20261110_01`，协议 SHA-256 为 `c0e90648989b9b4280141543bbebf78e98601d56cb5e6cd8f0c70a8a9be24b5a`。保守的实际预检输入计量为 16,430，低于输入硬上限。配置和未授权模板保存在 `~/.local/share/flowevo/alfworld_recovery_v7_pilot_20261110_01/`，当前 READY_PENDING_EXPLICIT_AUTHORIZATION。使用 `scripts/run_alfworld_recovery_v7.py run` 及匹配授权文件启动或恢复。本次尚未发送真实请求。
