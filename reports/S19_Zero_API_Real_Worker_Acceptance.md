# S19 零 API、真实 Worker 验收

本轮未使用供应商模型 API、未读取密钥、未运行真实学习 Pilot。模拟的是模型响应；被评分的 Python 程序实际进入既有 Linux 隔离 Worker，不在宿主 Python 主进程执行。

## 可复核证据

最终工程运行：`runs/s19_v2_worker_acceptance_20261024_07/`。

提交的精简证据位于 `reports/s19_v2_acceptance/`：

- `real_worker_acceptance.json`、`real_worker.log`。
- `engineering_stream.jsonl`、`engineering_hypotheses.jsonl`、`engineering_rule_registry.jsonl`。
- `runtime_probes.json`、`worker_environment.json`。
- `first_worker_failure.json`：首轮失败保留，未覆盖。
- `pilot_public_acceptance.json`：40题公开评分复验摘要。

本机连接由显式配置文件冻结；运行入口读取配置中的 unix socket、Docker config、既有验收报告及 SHA。没有在新连续入口硬编码个人 socket。复用已有 Worker 安全约束与验收，不声称本轮重新证明了全部 12 项隔离探针。

## 连续工程路径结果

| 检查 | 结果 |
| --- | --- |
| 同组失败触发生成、失败后诊断修订 | 通过 |
| 形成两份不同规则，旧版本保留 | 通过 |
| 相同规则修订只增加记录、不虚增版本 | 通过 |
| 机制内容发生实际变化 | 通过 |
| 来源通过的候选在后续任务介入 | 通过 |
| 新干预造成公开 case 退化后暂停 | 通过 |
| 反例绑定实际干预前检查点 | 通过 |
| 正确程序通过、错误程序被拒绝 | 通过 |
| 无代码/语法错误被识别，不能冒充完整解法 | 通过 |
| 缺失程序的 fresh-only 规则完成真实来源评分 | 通过 |

验收文件包含 10 项自动断言，全部为 true。主夹具四个顺序任务产生 11 个 solve、3 个 learning、3 个 validation **模拟响应**；另一个缺失程序夹具有 3/1/1 个模拟响应。工程 usage 是固定小数值，仅用于核对账本与控制流，不能拿它估算实际模型价格或节省。

具体闭环：首次规则选择 A，初版和一次同文修订均来源失败，保持 Shadow；下一任务产生相关证据后，模型夹具返回 B 及更新的假设内容，来源验证通过，发布到未来任务；之后一次未来使用公开通过，另一次公开退化，版本立即暂停。来源评估依次为失败、失败、成功；不得把该序列描述成真实模型自然学会了 B。

未知请求与原生回退使用隔离的工程账本另测：一个模拟请求产生未知状态后，后续调用被阻断；两次模拟原生调用完成错误到正确的回退。源码指纹绑定这些宿主探针。它们不是收费模型记录。

## 失败如何暴露、如何修复

首轮真实 Worker 联调未通过公开退化断言。原因是旧逻辑把 `actual == expected` 当作结果：换行差异导致 token 比较器已经判对的用例被错误当作错，随后退化无法识别。现在 Controller/Hook 携带宿主评分布尔值，RuleMemory 和机制反馈使用相同稳定 case ID 比较；没有放宽程序正确性标准。

40题公开评分的首次适配也在继承比较器 `prior_case` 缺失处停止。修正为调用同一历史比较函数的等价解包，增加新旧评分对照，未替换任务、未将失败题剔除。最新重跑 40/40 正例通过，40/40 反例未通过全部公开用例。此处只验收公开评分，不意味着40题最终独立复核已经通过，更不意味着模型解出了40题。

## 场景覆盖

A：同组证据聚合、独立事件与 task ID、未把计数当支持；工程题同模板，不宣称自然独立谱系。

B：有界初版/一次修订、新证据再调度、同文规则去重、parent 与成本元数据；无预算则不生成。

C：真实 Worker 评分正确/错误/缺失/语法程序；原预算应用与宿主拒绝检查。

D：下一题发布、公开通过与退化、暂停后权限阻断；路由中无适用机会不计失败。

E：嵌套私有字段在 G/M/F 中拒绝且未发送；任务中断 fail-closed；三个学习中断点恢复不重复发送；响应篡改拒绝；M 已结算响应恢复；未知费用保留额度；三臂状态隔离。

## 测试命令和完整性

```sh
python -m unittest discover -s FlowEvo/tests
python -m unittest discover -s scripts -p 'test_s19*.py'
python -m unittest discover -s scripts -p 'test*protocol*.py'
python scripts/accept_s19_real_worker.py --output <NEW_RUN_DIR> --worker-config reports/s19_v2_acceptance/worker_environment.json
python scripts/prepare_s19_pilot.py --output <NEW_PREPARATION_DIR>
python scripts/accept_s19_pilot_public.py --bundle <PREPARATION_DIR> --output <NEW_ACCEPTANCE_DIR>
```

本机使用 AFlow `.venv` 中的 Python 运行，未引入新依赖。前述数据文件是本地已有材料；克隆源码后若没有这些历史数据，需恢复原始资料，不能以同名人工题替代。

测试统计：核心212通过，S19专项15通过，协议专项32通过。全量 scripts 84项仍有6项历史上下文失败（细节见 Code Fix Report）；未宣称全部测试通过。

**ENGINEERING_READY：本轮声明范围内成立。LEARNING_LOOP_READY：工程联调成立，真实模型连续学习待验。RESEARCH_EFFECT_UNVERIFIED：保持。**
