> 运行状态更新（2026-11-20）：用户已授权并完成实跑，见 Pilot_Result.md。下文保留预检时点的零付费结果；授权文件现已创建，真实请求36。

# Pilot Preflight

实际状态：**7/7 类必要验收通过；新增真实模型 HTTP 请求0，付费请求0**。原有41项结果保留在 failure_acquisition_prepare_20261119，未覆盖其 Zero_API_Result 或回执。预算模块改动后另运行原有11项持久预算回归，全部通过；git diff --check 通过。

协议 SHA：`7921ed7ab5fe7b66d420ee7b766673db7e459f486b5ea4060d8e108fd16121da`。测试回执、源码哈希、数据哈希均绑定此版本。

## 实际接入

- 原生 HumanEval loader 支持本地原版 gzip 和公开投影，未安装 datasets 时本地路径仍可用；只在原远程路径需要该依赖。
- 原生 Generator 的公开 import 保留；实际 HumanEval/0 类型签名走过隔离验证，预期错误实现得到真实断言失败，没有缺失类型注解依赖。
- 原生 LLMGenerator 注入 PilotTransport，Actor 与 Teacher 都复用 PersistentBudget 和既有官方请求发送边界；未知请求不重发。原生策略提炼的24次潜在调用已计入总额。
- AcquisitionScheduler 支持一次来源修订、固定候选和一次独立第二来源支持。PrimitiveStore 保存支持证据；不同 SHA 拒绝合并。
- 旧 helper 仍展示源码；达到新条件的 helper 使用只读模块接口。准入函数接受共享 Sandbox，所有重放统一经 DockerWorker。
- 分阶段驱动已经实现 collect/acquire/support/freeze/transfer/report。G_plus 只增加准入操作，Teacher 来源完整题解不进入迁移库。

## 验收

|检查组|结果|
|---|---|
|real_loader_and_public_validation_boundary|PASS|
|both_model_roles_budgeted_and_live_default_blocked|PASS|
|same_sha_independent_support_and_dedup|PASS|
|draft_requires_explicit_training_support_binding|PASS|
|legacy_and_native_success_prompt_reuse_preserved|PASS|
|isolated_modules_readonly_network_timeout_receipts|PASS|
|staged_entry_dry_run_and_cost_consistency|PASS|

最终 dry-run 目录：`runs/failure_acquisition_pilot_20261120/dry/dry_f97lcdpf`。完整分阶段链使用2个合成训练夹具、1个迁移夹具；模型响应全部明确为 Mock。来源初稿为空、修订成功；第二来源初稿失败、修订后真实调用同 SHA 并通过返回值依赖检查。漏斗：2个学生失败 → 1个来源成功 → 1个操作 → 1个第二来源支持 → 1个准入操作 → 1次自主接口路径调用；两组完整夹具均成功。此处的调用选择由 Mock文本模拟，不能当作真实 Actor 自主工具能力或学习收益。

最终 dry-run 运行15次真正隔离执行；七类检查另运行4次，包括只读模块写入被拒绝、无宿主 API key、网络不可用、真实超时。没有拿宿主 subprocess 运行新生成代码。中间失败预检目录保留，不计为真实实验成绩。

数据最终可用68题，冻结24 train＋12 transfer_dev；未选择TACO，不重标MBPP。已完成原始任务身份和公开近重复分组审查；人工分层／启发式支持选择与尚未穷尽的语义去重限制见协议。现有18个历史失败和封存集不混入。

凭证存在性、到 api.deepseek.com 的 DNS/TCP/TLS 连接已检查，通过；**该检查未发送 HTTP 请求**。未做付费接口探测。

## 命令

仓库目录：`/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments`。
本次实际 Python：`/Users/majiatong/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python`。

零付费准备与必要检查：

```bash
PYTHONPATH=FlowEvo/src python scripts/run_failure_acquisition_pilot.py \
  --config configs/failure_acquisition_pilot.json --stage preflight --dry-run
```

本轮明确授权后执行真实阶段：

```bash
PYTHONPATH=FlowEvo/src python scripts/run_failure_acquisition_pilot.py \
  --config configs/failure_acquisition_pilot.json --stage all \
  --authorization-file reports/failure_acquisition_pilot_20261120/Pilot_Authorization.json
```

授权文件目前**不存在**，不能由预检自动生成。它至少需 authorized=true、上述 protocol_sha256、max_usd=8，并记录本次用户明确确认。也可逐次指定 collect/acquire/support/freeze/transfer/report，复用同一授权与账本；正常阶段不重新审批。

真实结果将写入 `reports/failure_acquisition_pilot_20261120/Pilot_Result.md`，包含漏斗、完整任务配对结果及阶段成本。逐题调用、参数与返回值依赖、两组请求／token／执行成本在真实 run 的 Pilot_Result.json。当前未生成真实结果报告。无准入操作时迁移阶段自动跳过；停机则输出停止原因和已用预算。

## 当前界限

具备启动这一次真实代码域开发试验的入口和预检证据。尚未验证真实 Teacher 能产出可复用操作，也尚未验证 Actor 自主使用质量。数学和 ALFWorld 完整新适配仍为 ADAPTER_NOT_READY。当前只等待本轮明确预算授权，不继续优化 Mock 成绩。
