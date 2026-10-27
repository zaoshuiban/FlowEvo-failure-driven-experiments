# P0–P2 零 API 验收

本轮新 GPT/DeepSeek 请求：**0**；未推送。基线及源码 hash 见 source_manifest.json。历史实验没有追溯改写。

## 结果

| 测试 | 数量 | 结果/日志 |
|---|---:|---|
| FlowEvo/tests 全量 | 212 | core_all_final.log，全部通过 |
| 原自主 MVP（实际 Docker） | 17 | mvp_final.log，全部通过 |
| DeepSeek 生成适配器 | 3 | provider_final.log，全部通过 |
| 最终 wire 计量 | 5 | accounting_final.log，全部通过 |
| 本轮学习链路 | 16 | attempt02.log，全部通过，包含实际 Docker |
| 合计 | 253 | 无跳过；Mock 模型，不是 Mock 评分器 |

源码 git diff --check 通过。core_final.log 的198项为 test_failure_evo*.py 子集，不另加到总数。

## 安全与功能覆盖

1. 空真实证据、未审查语法、未来证据、代码 hash 不一致拒绝。
2. 即使 legal_verified=True，非法 SAMPLE 输入也无法准入；新增勘误日志，旧证据不改。
3. 未知/private任务与反馈字段拒绝；design/gate/regression/test不进入归纳 wire。
4. 非法 Python 或禁止 os 导入不得进入 Worker。
5. 真实 Docker 执行既有隔离限制；源码不能获得密钥/网络或模型客户端。
6. 五角色及谱系重叠、用例所属任务不符均拒绝。
7. NO_MECHANISM / HYPOTHESIS_ONLY 正常停止；来源失效保留 Shadow；独立失效无授权。
8. 原题/开发题不在未来允许清单；任务快照和发布屏障复用原注册表。
9. 持久预算、拒绝回退、不覆盖已有有效候选由原核心/MVP回归覆盖。
10. 未授权不得真实发送；UNKNOWN再次调用不重复发送。
11. 实际 Worker 执行拒绝路径，Controller继续原生返回正确程序。
12. code_repair 使用已有重试 Hook；task_solver使用新显式 Hook。
13. 关闭新能力时，两条Controller路径输出和调用记录一致。
14. 模型身份、原始源码、hash、原始响应及父链在工程记录中留存。

## 历史输入与正向工程夹具

来源：S20-A M组 s19g_taco-train-s00-r0298 真实公开失败，事件 dff2f1324f4cf13e96730309d5de2c7309b7e96de25d0b00e50f60c16f9d991c。读取冻结01.json及原证据；宿主执行题面语法验证。原任务完成收据只投影到本轮新日志，用于原LearningLoop题间门控。

完整链路 engineering_attempt02 保留：真实历史来源、症状队列、LearningLoop.run_pipeline、富结构Mock假设、Mock源码、真实来源与工程独立正反评分、授权收据、未来题Hook和暂停检查。未来工程题在算子成功后不调用求解模型。

独立样例是求和/最大值/回显/排序等明确工程夹具，**不是自然失败、不是模型自动发现的同机制独立任务**。Mock生成器有固定答案是测试框架的特性，不是生产学习能力。非法SAMPLE回归是定向注入测试，未重新执行S23旧实验。

## 证据等级与结论

| 等级 | 本轮状态 |
|---|---|
| IMPLEMENTED | 是，显式接入现有学习与运行模块 |
| MOCK_VERIFIED | 是，完整闭环 |
| REAL_WORKER_VERIFIED | 是，实际隔离执行Mock返回源码 |
| REAL_MODEL_GENERATED | 本轮否 |
| SOURCE_VALIDATED | 仅Mock源码的宿主功能验收，非真实学习 |
| INDEPENDENTLY_VALIDATED | 仅工程角色隔离验收，非自然独立机制验证 |
| CROSS_TASK_REUSED | 仅工程未来任务Hook验收 |
| CAUSAL_BENEFIT_OBSERVED | 否 |

P0–P2工程路径通过，H1仍待真实模型和自然独立数据检验。旧DeepSeek试运行只得到假设，不能与本轮Mock源码拼接成真实生成成功。
