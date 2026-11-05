# 50题后工程接入：最终阶段报告

## 结论

核心新契约链路已在零付费模型、实际Linux Worker、宿主独立夹具Oracle条件下走通。完整累积学习脚本44/44工程检查通过；专项相关191项测试通过（含继承重复执行）。这证明工程可运行，不证明真实自主学习、官方独立原题泛化或相对G/T/R收益。

本轮工程收尾已完成，当前判定与证据以closeout_report.md为准。仓库历史回归仍有5失败11错误，均在未修改dc98cb74上逐项复现，不放宽冻结或暂停权限以消除。没有真实模型学习或研究收益结论。

## 基线与修改前调用链

HEAD基线dc98cb74bf07e673d44ff50f25533530328b9a03。工作树保留用户历史未跟踪数据，无强制重置。本轮未提交或推送。修改前审计见prechange_audit.md。

原链：ingest→持久证据→检索/关联→机制簇→Queue→BundleCompilerAdapter→receive_source→diagnosis→split artifact→registry.shadow→来源诊断→release。正式契约未进入Prompt，split联合SHA与单源码binding不兼容，record_stage只接受布尔声明，缺Shadow与发布续接。

## 修改后真实调用链

CumulativeStream.run → ingest/旧证据检索/关联 → 合法机制与双判断 → 稳定Queue作业 → BundleCompilerAdapter要求正式契约 → receive_source/diagnosis → 原split artifact → attach_contract/证据和版本绑定 → 原registry.shadow → validate_safety → 原SplitRunner来源诊断 → ReviewedRelease/独立审查包 → validate_computation_stage(SOURCE、INDEPENDENT_GATE) → 等待未来题 → ContractShadow.observe（正式评分前）→ 原生G/T/F/R求解和答案锁定 → ContractShadow.finalize（独立私有评分、不改正式答案）→ poll_contract → 原配对发布Gate → 原VersionGate.admit/authorize_trial → 后续原UnifiedMathRouter实际介入。

这一路径沿用现有注册表、EvidenceStore、Worker、预算账本、评分器和发布Gate。新增math_contract_runtime.py只是职责明确的验证/Shadow适配，不维护第二套权限库。

## 逐文件修改

- math_cumulative_learning.py：生成Prompt要求applicability携带正式契约JSON；严格接收、缺失拒绝而不补数学字段；保留source_evidence_ids、关联尝试ID、cluster/version、双判断及生成作业ID；修复事实原题身份字段层级错误；接入真实安全检查。
- operator_contract.py：支持split文件SHA和联合绑定；契约Schema检查及外部引用禁止；源码、契约、生成协议、证据与原题身份绑定；两已知来源才允许复用；record_stage必须引用执行收据；SOURCE/Gate使用真实SplitRunner与既有独立评价；Gate版本锁定；恢复不重复Worker、工程收据不授权真实制品。
- semantic_contract.py：实际求解时检查新契约输入/输出Schema与工件绑定。
- math_contract_runtime.py：实际Docker安全探针、候选静态权限检查、题间Shadow两阶段执行/评分、无分母测量、读取原预算与使用账本。
- math_stream.py、math_cumulative_stream.py：显式冻结operator_contract_shadow=pre-score-one-candidate-v1后接入Shadow；默认关闭；每题最多一个候选；全部答案锁定后评分与发布续接。
- math_stream_learning.py：新契约分支使用可信计算验证器；SOURCE审查须覆盖实际声明来源；缺阶段保持Shadow；原配对Gate和有限授权不变；补充RunUnhealthy导入；发布续接中断阻断。
- math_gate_pool.py：区分等待阶段与最终发布结果，不把等待Shadow永久缓存为终态。
- math_operators.py、operator_version_gate.py：新契约运行资格重新检查；Gate和试用记录绑定candidate_version；只改契约不得继承旧版本权限。
- container_worker.py：清理前保留并查询容器OOM事实；确认OOM返回MEMORY_LIMIT，无法确认的退出仍为基础设施错误；退出仍强制清理且无法确认清理时停止。
- 测试脚本见source_manifest.json。原UNKNOWN测试更新为RunUnhealthy预期，仍断言没有重发；没有改成成功。

## 验证状态与权限

模型提出的REUSABLE_CANDIDATE不是验证结论。正式契约不能写权限字段。新版本需STATIC_SAFETY、SOURCE、INDEPENDENT_GATE和SHADOW_OBSERVATION执行收据，并继续满足旧配对Gate、注册、任务排除、有限任务清单和次数限制。

SOURCE需要受信宿主审查的参数与独立答案；Worker只收到公开问题/参数。Gate先冻结，不能对同版本换池试探。未知来源、同原题或生成曝光保持拒绝。只有来源及计算Gate通过的候选才可在后续不同来源题执行Shadow。Shadow评分使用独立日志，必须引用真实持久答案锁，结果不作为当前正式答案或补救反馈。

恢复使用原追加日志：已完成执行收据可补回阶段记录，不再执行；有STARTED无收据则阻断。Shadow已执行时可恢复后续锁定/评分；发布STARTED未结束阻断。工程Mock身份不能进入真实制品授权。旧制品无新契约时维持显式旧协议兼容，不宣称已通过新标准。

## 安全验收

14项真实Docker检查通过：正常程序、外部网络阻断、根文件系统写入阻断、256MiB配置和OOM实际限制、单CPU配额、进程数量实际限制及配置、文件描述符上限、临时文件上限、输出上限、墙钟超时、递归失败、已存在宿主canary文件不可见。canary是临时无私密内容文件，不读取真实用户秘密。候选禁止模块/动态执行由现有静态检查处理，容器限制为纵深防护，不能声称禁止了Python一切潜在逃逸方式。

首次系统临时目录挂载失败记录保留，不算安全通过；项目目录正常样例成功后才进行限制判断。初次新契约联调失败01/02/03保留；修复了累积调度漏Shadow、原题字段位置、审查身份漂移及发布续接后，新Run04/05/06通过。最终核验Run07及完整事件见对应目录。

## 未完成与研究边界

- 扩大回归旧失败未全部修复或基线复现；未删除失败测试、未改历史冻结哈希。
- 中断和负向组合不是穷尽测试；更严格的并发验证、容器宿主失联及全部故障矩阵仍需补齐。
- 尚无新真实模型候选通过本协议，没有真实官方独立原题Gate或在线学习收益结论。
- Token估算只使用明确冻结报价；无报价时NOT_EVALUABLE，未知预留与实际费用分开，实际账单不可得时明确记录。

历史50题清单953个文件SHA全部未变，见historical_integrity.json。未运行200题、未修改旧实验成绩、未重发UNKNOWN、未继承旧预算。

## 收尾状态更新

本报告前文PARTIAL是阶段状态；当前收尾判定与证据以closeout_report.md为准。核心新链路、真实Worker安全、故障注入和旧回归归因已完成。未决验证/发布现在阻断全局新请求，较早通过记录不能掩盖未决执行。相关195项快速回归通过；完整工程流44/44，真实Worker故障注入13/13。

剩余5失败11错误逐项在dc98cb74源码快照复现，属于历史冻结拒绝及已暂停旧算子的续期拒绝。没有降低门槛或恢复权限。独立进程回归消除了旧性质测试的混合进程污染；S19白名单测试使用原FakeJudge隔离了不相关的旧Worker环境依赖。

工程收尾COMPLETE不等于真实数学泛化或研究收益成立；不自动启动付费实验。
