# 测试报告

命令：

```sh
PYTHONPATH='/private/tmp/flowevo-goal-test-deps:FlowEvo/src:scripts' /opt/homebrew/bin/python3.11 -m unittest scripts.test_operator_contract scripts.test_association_lifecycle scripts.test_evidence_retrieval scripts.test_cluster_contract scripts.test_evidence_links scripts.test_delivery_observation -q
```

150项通过，失败0、跳过0，包含继承重复执行，并非150个独立研究样本。新增split绑定测试验证真实文件SHA变更、生成协议变更和伪造证据集合拒绝。

未运行全仓库回归；未完成BundleCompilerAdapter真实执行到release的模拟端到端测试；未做真实Worker专项安全测试和可信验证器全链测试。Docker只读info确认linux，仅为环境可用性。付费API调用0、费用0。

## 续实施验收

相关六模块组合151项通过，0失败0跳过。新增record_stage无真实执行收据拒绝测试；旧UNKNOWN测试改为断言RunUnhealthy（仍断言仅发送一次），未改变运行安全逻辑。

真实执行命令：

```sh
PYTHONPATH='/private/tmp/flowevo-goal-test-deps:FlowEvo/src:scripts' /opt/homebrew/bin/python3.11 scripts/accept_post_pilot50_worker.py
PYTHONPATH='/private/tmp/flowevo-goal-test-deps:FlowEvo/src:scripts' /opt/homebrew/bin/python3.11 scripts/accept_post_pilot50_validator.py
PYTHONPATH='/private/tmp/flowevo-goal-test-deps:FlowEvo/src:scripts' /opt/homebrew/bin/python3.11 scripts/test_math_continuous_stream.py reports/post_pilot50_end_to_end/stream_acceptance01
```

Worker9个探针结果见worker_acceptance.json；工程SOURCE/Gate及缓存恢复见validator_acceptance.json；旧协议四组流38项通过，162次真实Worker，140次Mock模型调用。

扩大回归：从scripts收集45个直接继承unittest.TestCase的文件，清除环境API_KEY，使用python -m unittest运行，清单regression_inventory.json。第一轮265项：5失败、29错误、10跳过。加入现有repair-test-deps后385项：5失败、17错误、10跳过（353项通过），详见regression_with_dependencies.log。此清单不包含所有继承式或脚本式测试，不能称全仓库测试全绿。

已观察失败包括历史hard10/hard140/pilot/algorithm-evidence源码冻结检查和旧性质测试预期；错误的逐项堆栈完整保留，尚未全部完成基线对照归因，不将其全部称为既有缺陷。未修改历史冻结哈希或实验结果以通过测试。

无付费模型调用。Worker探针及验证器均为工程夹具，不是自动学习或泛化证据。

## 最后一次验收（以本节为当前结果）

- 相关10模块组合191项通过，0失败0跳过，含继承重复。
- 完整test_math_cumulative_learning.py，工程Run contract_stream_acceptance05：44/44检查通过；涵盖四种场景、四组连续调度、拒绝/诊断/配对信息与新契约发布。实际模型响应均Mock，Worker真实。
- 最终新发布路径重测contract_stream_acceptance07，结果及测量见该目录；不会与旧50题混记。
- accept_post_pilot50_validator.py：实际安全、来源、计算Gate、后续Shadow、独立私有评分、布尔伪造拒绝、缓存恢复；registry_events和component_events保留原始执行事实与fixture源码。
- 安全收据中14项Docker探针全部通过，含真正OOM与进程上限。初次系统临时目录无法挂载并非安全通过。
- 45个直接TestCase文件+新runtime测试的扩大组合：411项，383通过、5失败、13错误、10跳过，日志regression_final02.log。不是全仓库全部脚本清单，不宣称全绿。

扩大回归分组：历史冻结哈希相关失败/错误入口覆盖hard10、hard140、S22/S24、旧pilot/algorithm；外部AFlow缺tree_sitter及旧Worker验收绑定缺失；4项S16c2有限试用续期预期与现有状态约束不符；1项旧性质测试期待PROPERTY_COUNTEREXAMPLE而实际UNVERIFIED_REFERENCE_OR_DOMAIN。逐项名和原始堆栈以日志为准，不将全部失败直接归因于新模块或全部判为旧缺陷。补装sympy及openai到独立/tmp依赖目录后，原5项sympy缺失错误消失；没有修改项目依赖锁定或历史实验源码以消除失败。

历史50题953个文件哈希核对无变化。所有本轮模型请求0、费用0。报告中的Mock tokens不是真实账单。

## 收尾补充

当前权威结果见closeout_report.md和isolated_regression_verified.json。新相关快速回归195项通过（含继承重复）。实际Worker故障注入13/13；候选生成后登记前中断恢复证明T/F各仅1次候选生成请求。完整四组新契约路径最新Run09为44/44。

测试运行器run_post_pilot50_regression.py按文件启动独立进程，禁止API_KEY环境传递。最终保留5失败11错误；它们与未修改dc98cb74源码快照上的失败集合完全相同，见regression_attribution.json。旧性质测试单独运行通过，不再混合进程运行；旧S19白名单测试改用现有FakeJudge后12项通过。

未删除失败测试、未改历史冻结Hash、未恢复S16暂停算子。实际S16状态为permission=suspended、valid=False、used=2、remaining=1，符合拒绝续期条件。

执行命令：

```sh
PYTHONPATH='/private/tmp/flowevo-goal-test-deps:FlowEvo/src:scripts' /opt/homebrew/bin/python3.11 scripts/accept_post_pilot50_recovery.py
PYTHONPATH='/private/tmp/flowevo-goal-test-deps:/private/tmp/flowevo-repair-test-deps:/private/tmp/flowevo-post-pilot-test-deps:FlowEvo/src:scripts' /opt/homebrew/bin/python3.11 scripts/run_post_pilot50_regression.py isolated_regression_verified
```

每次隔离回归独立JSON与日志保留，计数不跨批相加。所有结果均为零付费模型验收。

### 最终冻结执行结果

isolated_regression_frozen.json：46文件、418项，392通过、5失败、11错误、10跳过；源码前后SHA无漂移。全部16个未通过项与基线dc98cb74复现集合相同，无新增失败集合。不同文件间继承测试仍可能重复，此计数不是独立用例或研究样本数。

该最终执行在每文件独立进程进行，期间未修改源码；源码清单随结果保存。相关快速回归195项、真实Worker故障13项、四组累积流44项分别报告，不跨批相加。
