# ALFWorld B v2 真实来源技能获取 Pilot

真实范围只含 B 的 16 个来源事件。A 仍保留旧协议。无原生模型续跑、Gate 执行或有限授权。先生成冻结配置并关联同配置的零 API 验收，再使用本轮明确授权文件。历史 120 局授权和旧 A/B 预算均不可复用。

| 通道 | 上界 |
| --- | ---: |
| 逐条分析 | 2 次，各 8 条 |
| 机制归并 | 1 次 |
| 代码生成 | 4 次，每机制至多 1 次 |
| 自动修订、来源验证模型请求 | 0 |
| 短窗口 Worker | 最多 48 次，4 候选 × 3 检查点 × 4 步 |
| 扩展窗口 Worker | 最多再 96 次，总计 144 次；账本时长上界 2,160 秒 |
| 模型 | DeepSeek Flash，JSON 模式，非思考，温度 0 |
| 模型 Token | 7 ×（65,536 输入上界＋4,096 输出）＝487,424 |

输入预留使用最终序列化 UTF-8 字节数加 256 的保守计量。沿用此前核对的峰时未缓存输入 $0.30、输出 $1.20／百万 Token 报价，七次均打满的估算上界为 **$0.172032**。持久账本把全部 Token 按 $1.20 保守预留，逐次向上取整总上界 **$0.584913**，冻结硬上限 **$0.60**。供应商 usage、估算费用及预留分列。启动前核对实际报价及别名版本。 [DeepSeek 官方计价](https://api-docs.deepseek.com/quick_start/pricing/)

严格复用确定未发送的恢复与 UNKNOWN 阻断。交付拒绝不追加生成，已有结算复用确切请求回执。来源不一致、Worker 基础设施异常、未确认请求或预算耗尽时停止并保留阶段账本。零机制、全弃权、零源码与零可信修复都是可解释结果。

## 独立池覆盖

已重新做元数据核查。已知曝光按游戏 SHA、轨迹 SHA、任务组及场景隔离。现有 34 个未运行候选覆盖 3 个场景，简单放置 19、双物体放置 14、清洗后放置 1。池中缺少台灯及加热任务。按类型只能预判机会，无法确认某个尚未生成的策略有足够适用、近似不适用或跨场景状态。相关条件保持待核实；缺失任务类型保持覆盖不足。

真实候选及版本先冻结，再由独立评估者在未见游戏按事前规则确定正负检查点，保留原生能成功的场景，不按候选结果挑游戏。未来 G/F/Rule 使用同一公开检查点和原生 FlowEvo 设置，Rule 仅作独立对照。Gate 反馈不返回本候选版本的生成或修订流程。

## 当前冻结状态

本地 Pilot 已生成，协议 SHA-256 为 3cf6d64f4505ed63280b61f2399294019c3d6a9bd23444ed3e6b20a399143725。当前为 READY_PENDING_EXPLICIT_AUTHORIZATION。DeepSeek 凭据已做存在性检查，未发送网络验证。授权模板仍为 false，启动负向测试已确认拒绝且未创建供应商日志。只在获得本轮明确授权后，才使用同协议匹配的正式授权文件。恢复使用同一入口、Run 目录和授权文件。

```zsh
export PYTHONPATH=FlowEvo/src:scripts
flowevo_data="$HOME/.local/share/flowevo"
flowevo_py="$flowevo_data/alfworld_baseline_20261107/venv/bin/python"
flowevo_pilot="$flowevo_data/alfworld_recovery_v2_pilot_20261110_01"
# 此入口需要匹配的正式授权文件。当前只有未授权模板。
"$flowevo_py" scripts/run_alfworld_skill_acquisition.py run-recovery \
  --source "$flowevo_data/alfworld_full_library_online120_20261109_01" \
  --output "$flowevo_pilot" --authorization "$flowevo_pilot/authorization.json"
```
