# 评测修复与800题全量离线复核

已处理全部800题、2132个保存候选；28项自动测试通过；原题目、代码、响应与旧判分哈希未改变；新增模型调用0。

[完整结果报告](epochs/repaired_reports_20261020/修复与全量重评报告.md) · [800题结果](epochs/repaired_reports_20261020/task_results.csv) · [新旧变化](epochs/repaired_reports_20261020/transitions.csv) · [未定项目](epochs/repaired_reports_20261020/unresolved.csv)

| 数据集 | 总题数 | 旧最终程序通过 | 新规则下原最终程序通过 | 无法可靠判分 |
|---|---:|---:|---:|---:|
| TACO | 500 | 210 | 243 | 23 |
| LiveCodeBench | 300 | 278 | 286 | 4 |
| 合计 | 800 | 488 | 529 | 27 |

529是既有最终程序的离线诊断通过数，不是修复反馈后重新生成的FlowEvo成绩。“任一保存候选通过”为539题，不能与原流程最终程序混用。47道通过题剔除了非法测试，结果表已标记。

共隔离2612条非法测试，涉及78题；依据独立BFS、数组直接模拟和位运算计数规则修正244条参考输出。原失败转新通过64题；原通过变为非通过23题：18题新规则为WA、2题缺checker、3题计时不稳定。后两类不是算法失败；18题仍受下面的输入/参考覆盖边界限制。

## 实现与覆盖边界

- 整数精确比较、有序token空白规范化；25题采用题面浮点误差标准；另3题按固定小数或科学计数格式。
- 62道构造/多解题中，42道已实现任务级约束与必要的最优性验证；另20道标记CHECKER_UNSUPPORTED，不再用固定参考文本冒充可靠判分。
- 真实stdin/stdout、文件描述符、buffer、连续readline与EOF；函数指定入口及返回类型验证；候选看不到标准答案JSON。
- 分离各数据集错误码、语法/运行/超时/框架异常；保留诊断元数据；求解器反馈仅发送白名单类别。
- 3道交互题标记PROTOCOL_UNSUPPORTED；3道计时变化题标记TIMING_UNSTABLE；1道科学计数参考缺少指数的题标记REFERENCE_DISPUTE。
- 90题有专项输入契约检查；其余710题仅有通用结构/签名检查，不能据此宣称全部测试语义合法，或所有评测问题已消除。

## 版本和使用

服务器新入口由 `/opt/flowevo-benchmark-20261019/EVALUATOR_CURRENT.json` 指向 `repair_v2d_20261020/code/adapter.py`。历史benchmark.py保留旧行为用于复现，不静默覆盖历史运行。

接口为 `evaluate_v2(task_path, candidate_path, policies_path)`。不可判分时passed为null；调用者必须暂停该题，不得当作模型失败继续修复。solver_feedback只包含白名单类别，完整判分证据保留在评测端。

服务器工作目录中的调用示例：

```bash
venv/bin/python repair_v2d_20261020/code/adapter.py --task data/tasks/lcb_atcoder_abc392_d.json --candidate runs/lcb_medium/lcb_atcoder_abc392_d/l4.py --policies repair_v2d_20261020/policies.json --out /tmp/verification_v2.json
```

A版本全量重评；B版本补齐18道多解题、检查特定方法题并串行复核5道超时，共24题；C版本补齐3道定点格式；D版本隔离参考科学计数缺字段。每题实际epoch在task_results.csv中，冻结源码、规则、日志和运行清单保留在epochs/。

最新独立源码在code/，policies.json覆盖800题。可复现重评需要服务器保存的原始data/tasks与runs；应使用新的输出目录及对应冻结清单，不混用不同版本缓存。完整性证据见epochs/repaired_reports_20261020/integrity.json；最终测试日志见epochs/repair_v2d_20261020/all_tests.log。
