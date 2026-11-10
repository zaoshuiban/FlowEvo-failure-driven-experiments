# ALFWorld B v2 零 API 验收

## 实际结果

| 验收 | 结果 |
| --- | --- |
| 16 条独立分析 | 16 条均定位到原始无效动作并通过反馈引句检查，其中 2 条 Mock 弃权。 |
| 机制归并 | 3 个 Mock 提案，覆盖分别为 2、1、1 条，其他证据仍有独立记录。 |
| 策略生成 | 3 份不同的 Mock 源码通过静态检查与真实 Linux Worker 接口。均只注册为 Shadow。 |
| 同状态来源分叉 | 4 个来源检查点。2 个在一次动作后恢复此前不可用的决定性动作，标记 LOCAL_REPAIR_VERIFIED；1 个拒绝；1 个变化无足够推进证据。整局获胜为 0。 |
| 扩展与边界 | 无充分证据的分支实际执行 5 步，跨过短窗口。所有分支按剩余 50 步和冻结扩展上限裁剪。状态分类覆盖无效反馈、环境获胜、拒绝、异常。 |
| 隔离 | 负向测试拒绝非原始引句和弃权证据进入归并。模型输入与独立游戏清单、人工探针分离。 |
| 请求与预算 | 主流程 Mock 请求 6 次，分为分析 2、归并 1、生成 3。Worker 执行 11 次。恢复后账本逐字节不变；故障注入验证 UNKNOWN 不重发；未授权启动被拒绝。 |
| 独立池 | 只核查元数据，0 局执行，无独立通过、有限授权或真实能力收益。 |

Mock 源码仅用于工程测试。当前真实模型新生成、来源有效和跨游戏成功均无观测。

## 复现命令

在仓库根目录运行，Docker 需能挂载本机用户目录。用新的私有目录保存 Mock 回执。

```zsh
export PYTHONPATH=FlowEvo/src:scripts
flowevo_data="$HOME/.local/share/flowevo"
flowevo_py="$flowevo_data/alfworld_baseline_20261107/venv/bin/python"
"$flowevo_py" scripts/test_alfworld_recovery_acquisition.py -v
"$flowevo_py" -m unittest scripts.test_alfworld_skill_acquisition \
  scripts.test_alfworld_failure_learning scripts.test_alfworld_success_baseline -q
"$flowevo_py" scripts/run_alfworld_skill_acquisition.py mock-recovery \
  --source "$flowevo_data/alfworld_full_library_online120_20261109_01" \
  --output "$flowevo_data/alfworld_recovery_v2_mock_new"
```

专项 4 项与原 A/B、ALFWorld 失败学习和成功基线回归 22 项均通过。冻结后的真实入口使用未授权模板再次运行拒绝检查，未创建供应商请求日志。验收运行保留在本地私有目录。
