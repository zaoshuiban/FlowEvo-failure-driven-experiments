# E3-S0

800题、2,132份历史候选的失败事件流重建与离线时间顺序回放。入口：`E3-S0报告.md`。

本轮不调用生成模型、不运行候选、不修改原评测判定。旧判定、修订判定、独立有限测试与根因证据分别保留。

在资料包根目录复核：

```sh
python3 experiments/flowevo_taco_lcb_20261019/e3_s0_20261020/code/rebuild.py
python3 experiments/flowevo_taco_lcb_20261019/e3_s0_20261020/code/verify_replay.py
```

需要Python及matplotlib，以及同级既有repair_v2、e1_e2与trusted_rgf证据目录。原始历史数据完整保存在raw/runs；原服务器纳秒mtime保存在raw/e3_s0_20261020/source/file_metadata.json，解压后的本地mtime不用于回放。

输出：

- `events.jsonl`：全部候选事件。
- `dependency_edges.jsonl`：640条修复反馈边、624条旧PASS解答引用边。
- `online_accumulation.csv`：逐事件失败/产物/候选积累与严格历史认证数。
- `online_failure_accumulation.png/.svg`：总览；`per_stream_accumulation.png`：8流分图。
- `mechanism_candidates.json`：12类候选，只有2类达到真实实现失败证据门槛，各仅1道来源题。
- `integrity_checks.json`、`replay_verification.json`：结构、哈希、因果偏序和前缀信息隔离检查。
- `source_hashes.json`、`supporting_evidence_hashes.json`：原始及外部支持证据摘要。
- `artifact_integrity.json`：本轮全部输出文件SHA256；重新生成输出后需刷新该清单。

图中事后认证缺陷曲线仅为回看投影；原历史运行没有失败机制库，不能把这两条机制写入当时的在线可用知识。
