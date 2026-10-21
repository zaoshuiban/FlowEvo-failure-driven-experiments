# FlowEvo failure-driven experiments

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
