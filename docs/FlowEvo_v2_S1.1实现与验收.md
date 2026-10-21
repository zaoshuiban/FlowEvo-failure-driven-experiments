# FlowEvo v2 S1.1 本地实现与验收

日期：2026-10-21。基于远程提交 `c7839276dfdcf21358d47d7d09834a7a70fe1a72`，本地分支 `feat/failure-learning-v2`。本轮新增可执行模块和回归测试，新增外部模型 API 调用为 0；没有推送 GitHub。

## 已实现

| 模块 | 行为 |
|---|---|
| `failure_events.py` | 宿主记录公开失败事实；原代码按哈希保存；区分产物/运行/功能证据；时间可见性、依赖、去重和撤销；不要求三题才能进入发现通道 |
| `compile_queue.py` | 首见证/每20题调度，去重、最多两族；学习预算独立；归纳/三候选/各一次修订最多14请求；失败不退款、不自动重试；请求、生成内容、来源和制品哈希保存 |
| `learning.py` | 题末查询待编译队列，只解析当时可见公开证据及固定源码；默认不调用模型；显式注入有预算编译器才能归纳 |
| `failure_registry.py` | 不可变规格、Shadow 注册、独立 experimental 授权、题序发布屏障、固定快照；失败门控分片同样消耗；支持可靠性或效率 Pilot；撤销/漂移阻断 |
| `plugin.py` | 两 Hook、冻结优先级/冲突拒绝、每 Hook 实例最多一次；宿主验证和公开候选账本；拒绝回到原生检查点，费用不退款；候选和权限隔离 |
| `runtime.py` | 可选插件接入原五阶段控制器；关闭插件保留旧接口；保存验证失败/预算耗尽时的原产物；默认仍支持旧 v1 路由与返回协议 |
| `native_adapter.py` | 保留历史 benchmark 的基础 Prompt 和成功库调用接口；成功经验按可信公开通过更新；真实模型/提取器/CodeSkillLibrary由宿主注入；完整 Prompt 和成功参考上下文进入预留预算 |
| `benchmark_failure_evo.py` | 增加 `--v2 --state-dir`；夹具强制 synthetic，不能进入自然失败学习或实验授权 |

旧 `MechanismStore` 的 3题/2组严格认证保留；新失败事实及编译资格不依赖它。旧冻结 `experiments/.../implementation` 未修改。

## 运行方式

仓库根目录执行：

```sh
python3 -m unittest discover -s FlowEvo/tests -p 'test_failure_evo*.py' -v
python3 scripts/smoke_failure_evo_v2.py
python3 FlowEvo/benchmark_failure_evo.py \
  --fixture FlowEvo/examples/v2_incomplete_fixture.json \
  --v2 --state-dir smoke-results/example-state \
  --output smoke-results/example-result.json
```

全新克隆运行48题归档回放前，先执行 `python3 scripts/restore_datasets.py`。单位测试不需要数据恢复、第三方模型 SDK 或密钥。夹具状态目录每次使用新的路径；同一流不允许重复完成同一 task_id，防止恢复时重复计数。

验收输出默认写入 `smoke-results/v2/`，不改冻结证据；该目录、构建目录和 egg-info 已加入忽略规则。输出包含 `unittest.log`、`summary.json`、`baseline_manifest.json`。

## 本轮验证

- Python 3.9 与 Python 3.11：原55项及新增38项，共93项单元测试全部通过。
- 48题固定历史响应：关闭插件与空Shadow库的请求、预算、停止及返回策略一致。每模式复用55份保存响应；224份历史程序是输入清单规模，不等于全部都被两模式执行。
- 1,112个冻结制品哈希校验通过，`experiments/` 下没有代码或证据差异。
- 基础 Prompt 通过 AST 独立提取历史 `prompt_for` 后逐字比较；五阶段成功参考使用与公开成功入库有配对回归。
- 覆盖单见证、合成夹具排除、未来证据不可见、门控分片消耗、效率晋级、当前题不可用、Shadow不改请求、撤销、隐藏隔离、空测试拒绝、length完整代码保留、原候选保留、超限与费用预留。

这些是工程测试结果，不能作为失败算子自然生成、迁移或降低成本的研究结果。

## 边界与后续

1. **实际服务器接入未完成验证。** 已实现保留历史提示与成功库接口的适配层，但实际服务器 CodeSkillLibrary 实例、配置、模型、提取器、平台仍须由宿主提供并核实。基线清单的本地源码哈希不等于服务器身份认证。
2. **真实生成 API 未配置/调用。** BoundedCompiler 是有预算、有持久化的宿主回调接口；LearningLoop 自动调度仅到规格归纳。候选/修订、设计集选优及独立门控仍需显式执行，不能自动晋级。参数化真实生成输入和价格上限须先冻结。
3. **新注册表只提供 Pilot experimental。** 两个独立原题的配对节省及无观测回归只可支持效率 Pilot，不是总体非劣证明。S1.1 不开放新 active 晋级；旧正式准入路径保持原样。
4. **算子第一版无模型调用能力。** 只允许提出代码或选公开账本中的候选，由宿主验证；未知/空公开测试不接受。以后增加恢复动作或算子内部模型调用，需要独立能力代理与预算测试，不能通过放宽返回字典实现。
5. **Linux真实沙箱未在macOS执行。** SandboxOperatorRunner 的 v2 协议复用现有静态检查及不可变源码快照，真实进程隔离/超时依赖注入的 Linux Worker；测试 Worker 是工程夹具。未重新运行历史候选或评分器。
6. **公开候选策略采取保守子集。** 新算子提出的候选需有非空可信公开测试通过才改变当前选择；结构通过但缺少公开测试时仍保留原生流程。当前不实现“仅结构通过就改选”的新策略。
7. **状态存储面向串行单宿主。** 每流依次处理任务；不是跨进程并发数据库。部署并行服务前须增加进程级锁/事务和流隔离检查。
8. 原历史 benchmark 使用完整测试反馈；这里显式建立共同公开反馈适配基线，不能把两种协议差异归因于失败算子。

下一步是冻结实际服务器入口、完整生成与验证预算和数据角色，并完成Linux Worker验收；之后才进入S1.2真实候选生成。B/G/M/F干预和60题顺序流本轮均未运行。
