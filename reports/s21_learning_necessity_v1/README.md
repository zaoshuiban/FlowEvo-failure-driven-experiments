# S21 学习必要性审计：任务1、2、3

基于57e6b865，零新API。R触发3次，S Shadow触发2次；174/175动作相同，唯一差异是r0236同来源隔离，S独有触发0。原三题草案R/S全部相同。当前候选未证明历史知识的独立决策价值。

- [任务1：R/S及消融](任务1_R与S学习必要性检验.md)
- [任务2：条件与公开反例](任务2_历史依赖条件与反例审查.md)
- [任务3：证据链与决策](任务3_跨任务经验独立价值证据链.md)

复现（仓库根目录）：

```sh
/Users/majiatong/lab/AFlow/.venv/bin/python scripts/s21_learning_necessity.py
PYTHONPATH=scripts /Users/majiatong/lab/AFlow/.venv/bin/python -m unittest test_s21_learning_necessity test_s21_selective_experience test_s20_repair_stream test_s20_mechanism_stream -v
```

需要原本地历史公开run文件。输出仅写本目录；不重跑旧S21生成脚本，不修改旧结果。31项测试及哈希复核见tests.txt、verification.json；完整输入列表见input_hashes.json。原15请求方案暂停，不自动执行新的付费诊断。
