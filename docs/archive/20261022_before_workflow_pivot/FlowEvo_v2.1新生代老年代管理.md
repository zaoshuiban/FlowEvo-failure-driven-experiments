# FlowEvo v2.1 新生代—老年代管理

实施日期：2026-10-21。本修订替代“必须先证明跨题收益才能有限试用”的前置条件；不改变冻结实验的历史结果，也不扩大 Operator 动作权限。

## 两个独立维度

| generation | 含义 | permission |
|---|---|---|
| nursery | 来源有效，未来复用仍待观察；Shadow 制品也以此作为初始管理代际 | shadow 或 experimental |
| mature | 已有跨任务实际复用及独立配对门控支持 | 本实现仍为 experimental；不自动 Active |
| cold | 暂无机会或暂不值得调度，保留制品和全部历史 | 保留原权限，但禁止路由 |

`state(card)` 从现有注册表追加事件投影代际和权限，不向不可变制品卡添加字段，不改变历史卡及其哈希。暂停为 `permission=suspended`；淘汰为 `generation=cold, permission=suspended, retired=true`。无机会不等于无效。

## 新生代准入

宿主调用 `FailureOperatorRegistry.admit_nursery`，绑定 experiment、stream、未来任务序号、不可变源码、公开失败证据和最多 5 次机会。默认 5 次，允许冻结更小额度。不能重复准入重置额度。

准入不要求 Generic 失败，也不要求已经出现跨题收益。要求来源真实、非 synthetic，并有实际源码在隔离执行器中的来源修复、边界、不适用和宿主回退验收；同时有静态契约及执行隔离验收。`source_repair` 必须绑定来源事件和原程序哈希，返回 applied，且宿主非空公开测试全部通过。仅静态通过或 Mock 执行不能准入。

验收 JSON 是**可信宿主评价器的证明文件**，不能由 Operator 或生成模型自行提交并赋权。哈希检查用于发现后续改动，不是对文件陈述真实性的独立证明。文件至少包含：

- `role=NURSERY_ADMISSION`；`operator_id/version/artifact_sha256/fingerprint/scope/evidence_ids/experiment_id/evaluated_at`。
- `files=[{path, sha256}, ...]`：保留的原始执行证据。
- `checks` 中 `isolated_worker/static_contract/source_repair/boundary/inapplicable/host_fallback`：每项 `passed=true`，绑定 `artifact_sha256` 和 `evidence_sha256`。
- 四项功能检查 `execution=isolated_actual_source`。来源修复另有 `event_id/original_sha256/action/host_public_outcome/tests_run/tests_passed`。

这里没有自动信任新模型生成的“验收声明”。生产宿主负责用真实受控执行结果构造并审查证明；本轮没有为任何研究制品构造新的准入证明。

## 5 次机会如何使用

路由先检查冻结范围、任务边界、实际剩余预算与执行器，再在执行前持久化预留。一个 operator/version/stream/task/checkpoint/hook 只预留一次。使用跨进程文件锁、追加哈希链和 fsync；旧快照、重启、未完成运行及冷藏恢复都不能绕过额度。

“机会”是宿主范围匹配且准备执行的一次尝试，并不预先断言 Operator 最终适用。主动拒绝、异常、公开验证失败及中途崩溃都消耗机会；没有匹配任务或执行前预算不足不消耗。额度用尽后退出新快照；第 5 次已预留调用仍可正常完成。未结算记录保留为 pending，不自动退款。

宿主记录任务、检查点、原程序哈希、是否提议、实际 applied/declined/error、公开复验、工具数、模型调用数、模型 Token 和耗时。容器货币成本未知记 `null`；没有配对对照的 `paired_savings=null`。一次 applied 不自动成为“比 Generic 省钱”的证据。工程 synthetic 结果不能支持成熟晋级。

越权结果，包括藏在 declined 里的权限修改，会被拒绝并暂停。宿主观测到原公开通过程序被提议改坏时暂停；原先就失败的程序再次验证失败只记失败试用，不冒充负迁移。源码、准入文件、原始验收文件或来源证据失效时，下一次调用前暂停；正在进行的公开验证后也重新检查授权。暂停不退款；写审计失败返回原生流程。

## 长期管理

`review` 返回实际修复、拒绝、不同任务数、额度和是否需要复核；没有机会的建议为 `no_opportunities_not_ineffective`。`set_generation(..., 'cold')` 暂停调度但不认定无效；回到 nursery 不补额度。`retire` 用于宿主已有证据支持“不划算/不再使用”的决定。范围收窄或源码修订必须使用新的冻结版本，不在原版本上暗改。

`authorize_experiment(..., promote_mature=True)` 才能晋入 mature：先要求两个其他任务、不同原程序上的真实 applied 记录，再复用原独立门控（来源隔离、回归、配对正确性和可比成本、一次性分片），配对任务须覆盖实际复用任务。可靠性或效率路线沿用原门控；这只是当前小规模管理配置，不是总体统计保证。失败门控仍消耗分片，不会刷新机会额度。成熟仍绑定实验和未来任务边界，仍会复验和暂停，不获得 Active。

已有独立门控授权继续有效，但尚未成熟的版本也按新规则最多 5 次新预留机会；不虚构旧调用记录。自动选择对照、随机分派、长期全成本统计以及 Active 正式授权不在本修订中新增。

## 容量修复的下一步

`abc301_f` 的公开失败及 `before_native_retry` 可达性是已保存证据。新的生成判断为 `READY_FOR_BOUNDED_GENERATION`，Generic 可以修好不再阻止生成。这表示可准备单族的独立预算和生成配置，不表示已经生成、准入或证明收益。

研究问题改为：将 Generic 需要模型分析的修复编译为可复用程序后，能否在后续合法任务上保持可靠性，并降低包括构建、验证和路由在内的成本。新生代先获得有限收集证据的机会；缺少后续增量则不晋级，必要时冷藏或淘汰。
