# FlowEvo failure-driven experiments

## 自主算子 v2：DeepSeek 替换试验（2026-10-27）

[真实对照报告](runs/autonomous_v2_deepseek_source_20261027_01/DeepSeek_真实机制归纳对照报告.md)：相同原始失败证据，DeepSeek真实归纳1次、8,253 tokens，峰值报价估算$0.002964。返回HYPOTHESIS_ONLY，按规则不生成源码；不是源码生成失败。GPT/DeepSeek均尚无自然跨题复用证据。

## 自主算子 v2：真实 GPT 来源验证（2026-10-27）

[真实实验报告](runs/autonomous_v2_gpt_source_20261027_04/Autonomous_GPT_真实生成与来源验证报告.md)：GPT-5.4真实归纳＋源码生成共2次，23,153 tokens，用量费用约$0.14781。来源公开0/3→3/3，但生成的是来源题专用解法；4个开发控制均拒绝，保持Shadow。未完成自然独立验证、无未来Hook或因果收益；没有启动长流。

## 自主可执行算子学习 v2：P0–P2（2026-10-27）

[架构与接口](reports/autonomous_learning_v2/Architecture_and_Interfaces.md) · [代码差距审计](reports/autonomous_learning_v2/Code_Gap_Audit.md) · [零 API 验收](reports/autonomous_learning_v2/Zero_API_Acceptance.md) · [P3 协议及预算草案](reports/autonomous_learning_v2/P3_Protocol_and_Budget_Draft.md)。253项测试通过，包含真实Linux Worker；模型响应均为Mock。本轮未发送API，未证明自然跨题学习或因果收益。

## 编译器计量修复（2026-10-27）

[零 API 修复报告](reports/autonomous_wire_accounting_fix_20261027/计量口径修复报告.md)：最终wire计量、预检及预留统一；历史候选请求31847可通过32768上限。237项测试通过，原Run不变，未发送新模型请求。

## Autonomous MVP：DeepSeek真实试运行（2026-10-27）

[真实试运行报告](runs/autonomous_mvp_pilot_20261027_01/Autonomous_DeepSeek_真实试运行报告.md)：经用户明确变更生成模型，1次DeepSeek响应、7,377 tokens、估算$0.0027522；机制假设通过契约。候选最终wire估计31,847，但编译器内部请求估计33,151超过32,768，源码生成在发送前停止。0个算子、0次算子执行，H1未完成检验；不归因于模型修复能力失败。新3项适配测试和17项含真实Worker的MVP测试通过。

## Autonomous Operator Learning MVP（P0/P1，2026-10-27）

[实现与零 API 验收](reports/autonomous_mvp_v1/MVP_Implementation_and_Zero_API_Acceptance.md)：新增自主机制假设、GPT 完整 Python 源码生成适配、实际 Linux 验证与题间受限 Hook。17 项新增测试、198 项核心回归及 12 项隔离探针通过。所有生成响应均为 Mock，真实模型调用 0；**工程闭环通过，H1 尚未检验**。未修改旧实验记录或默认求解器。

[后续真实小实验预算提案](reports/autonomous_mvp_v1/API_Experiment_Proposal.md)：尚未执行；需先冻结真实独立验证数据。

## S22–S24（2026-10-27归档）

- [S22真实10题A/B实验](runs/s22_rq1_real_20261026_01/S22_真实10题AB实验报告.md)：20次响应；严格成功A 1/10、B 2/10，无UNKNOWN。尚未支持条件学习的独立价值。
- [S23上下文干预探索](runs/s23_context_probe_20261026_01/探索性实验报告.md)：两题四组，人工上下文整理与交付提醒组合出现一个正例；不是自动学习成功。
- [S24自动条件归纳与跨程序探索](runs/s24_learning_probe_20261026_01/S24_自动条件归纳与跨程序探索报告.md)：真实归纳1条条件，2个目标均未命中；固定P/CP均未完成严格修复，未注册新算子。
- [S22执行器验收](reports/s22_executor_v1/README.md)：冻结wire、独立账本、UNKNOWN停止及独立封存入口。

本次提交保留相关源码、协议、真实响应、账本和复核记录。历史运行不改写；新发现的非法测试输入单独记录。模型请求需遵守各Run授权边界，不应直接重跑已完成Run。文中“成功”均限于对应冻结测试，开发题不称为独立泛化。下文保留各历史阶段记录，时间与结论应按对应报告理解。

冻结的 TACO / LiveCodeBench 实验数据、历史候选、评测审查和 E3-S0/S1 原型。

## 范围与当前结论

- 800 题：TACO 五个难度各 100 题；LiveCodeBench release_v6 三个难度各 100 题。
- 2,132 份历史候选；E3-S0 重建历史事件流。
- E3-S1 冻结 48 题、224 份历史程序；新增模型调用为 0。
- 当前只有一个新确证的功能缺陷，未达到跨题机制发布门槛，未启动 S2。
- `FlowEvo/` 包含原源码快照和新增 failure_evo 模块；真实生成 API 后端未配置。

## 数据集与复现

`datasets/` 保存完整 800 题快照的压缩分卷、逐文件 SHA-256 索引和分卷索引。隐藏测试是实验归档的一部分，必须与生成/修复模型隔离；不能用于生成 R2 公开反例或修复提示。数据仍受各原始来源许可证约束，本仓库不授予额外再分发权。

```sh
python3 scripts/restore_datasets.py
python3 -m unittest discover -s FlowEvo/tests -p test_failure_evo.py
python3 experiments/flowevo_taco_lcb_20261019/e3_s1_20261020/code/verify_delivery.py
```

恢复脚本校验分卷与 800 个源文件，并重建历史证据使用的相对路径。Linux 沙箱测试需要对应的 bubblewrap 环境。策略回放基于保存的响应，不能解释为新生成性能或因果效果。

## 阅读入口

- `docs/FlowEvo失败驱动系统设计v1.md`
- `docs/FlowEvo_E3下一步实验计划.md`
- `experiments/flowevo_taco_lcb_20261019/e3_s1_20261020/E3-S1报告.md`
- 同目录 `逐题审查表.csv`、`review_cards/`、`counterfactuals/`、`mechanisms_verified.json`
- `experiments/flowevo_taco_lcb_20261019/e3_s0_20261020/`：历史候选和时间回放证据

原始历史失败标签、修正评分、公开有限测试结果是不同证据层级。有限 PASS 不等于全域正确；被废弃的 stress_v1 已在 exclusions.json 标记，不能用于结论。工程错误夹具不计入机制支持。

来源：TACO https://huggingface.co/datasets/BAAI/TACO；LiveCodeBench https://huggingface.co/datasets/livecodebench/code_generation_lite 。本仓库收录的是原实验使用的冻结文件，具体来源字段以任务 JSON 和原始实验配置为准。


## v2 本地开发：S1.1 零 API 插件

当前可编辑实现增加证据触发、题间发布、双 Hook、实验授权及独立学习预算。历史归档保持不变；尚未运行真实生成或 B/G/M/F 实验。

```sh
python3 -m unittest discover -s FlowEvo/tests -p 'test_failure_evo*.py' -v
python3 scripts/smoke_failure_evo_v2.py
```

48题回放需要先按上文恢复数据；输出写入忽略的 `smoke-results/`。

- [机制设计 v2](docs/FlowEvo失败驱动系统设计v2.md)
- [实施、验收与限制](docs/FlowEvo_v2_S1.1实现与验收.md)
- [当前实验协议](docs/FlowEvo_E3下一步实验计划.md)


## 跨不同原题的自主算子发现（2026-10-27）

按跨不同原题要求重新冻结2道来源、2道验证目标，使用 DeepSeek 真实归纳；旧苹果树专用源码未输入。结果 `HYPOTHESIS_ONLY`：1次请求、14,272 tokens，保守报价估算约 $0.00510；未产生源码，未启动 G/F 配对，不能声称跨题复用或优于对照。历史实验与确认集保持不变。

[真实实验报告](runs/autonomous_cross_original_20261027_01/跨原题自主算子发现与复用实验报告.md) · [机器可读结果](runs/autonomous_cross_original_20261027_01/summary.json) · [冻结协议](runs/autonomous_cross_original_20261027_01/protocol.json)
