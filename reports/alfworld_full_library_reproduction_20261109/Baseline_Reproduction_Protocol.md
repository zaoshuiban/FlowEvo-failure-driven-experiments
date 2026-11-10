# ALFWorld 成功经验基线冻结协议 v3

状态为工程验收通过、真实校准待授权、正式 G 待校准和独立授权。真实请求及费用均为 0。

## 实验及数据

| 用途 | 冻结设置 | 种子 | 模型请求上限 | 待批账本上限 |
| --- | --- | ---: | ---: | ---: |
| 独立校准 | 原 16 局双物体清单，12 局在线、4 局锁库，题目与顺序未变 | 20261109 | 812 | $11 |
| 正式 G | 120 局全部在线，六类混合，空库启动 | 20261111 | 6,120 | $85 |

正式流没有内部评价集或题间锁库。每局先锁定公开轨迹和环境 won，然后按原版 full_library 更新成功编译、原生失败统计与治理。更新在提交后才对下一局可见。在线 holdout 为原版的 20% 条件抽签，仅遮蔽 L2/L3 引导，保持 L1 行为。每 20 局审计并从已提交账本物化快照，第 120 局的最终库包含本局更新。校准的四局锁库只用于工程与模型通道校准，不构成正式 120 局的一部分。将来独立泛化评价另冻结新的未曝光游戏及场景，排除本次所有学习和校准来源。

新正式清单从严格 `json_2.1.1/train/` 的 3,553 局可解游戏开始，合并冻结的历史实验、工程回放、Gate 和校准曝光清单。按游戏 SHA、轨迹 SHA、任务组和场景排除已知重叠，并在候选池内排除重复内容。2,905 局被排除，剩 648 局。按固定种子从排序后的**单一合格池**无放回抽取 120 局，抽取顺序即运行顺序。规则只检查六类是否齐全，没有题型配额、内部场景切分、按难度排序或依结果重抽。候选池内采用均匀抽样，合格池本身受历史场景隔离约束，因此不能把结果视为全 train 的无约束简单随机样本。无法排除未归档曝光和预训练曝光。

| 类型 | 120 局 |
| --- | ---: |
| 普通拾取放置 | 50 |
| 灯下观察 | 6 |
| 清洗放置 | 15 |
| 加热放置 | 9 |
| 冷却放置 | 7 |
| 双物体放置 | 33 |

覆盖 26 个场景、106 个任务组，单场景最多 12 局。局间会因场景、谱系及前序技能状态产生相关性。每 20 局与各题型的差异只作描述，不能将早晚期的差异直接解释为学习效果。未来 G/F/R 配对使用同一清单、顺序、在线治理、模型、基础动作和裁决口径。各自技能库独立演化，F/R 的额外模型与工具预算另行冻结。

| 私有 Run | 协议 SHA-256 |
| --- | --- |
| `alfworld_full_library_calibration_20261109_04` | `2ea254f72270c05a5be79330828a88e672a194a7293cf8b0fb717f0ca188535e` |
| `alfworld_full_library_online120_20261109_01` | `8f1861756351c3e56028144e19acf84357959dfe60ec1222db891c9a3256c562` |

完整路径、内容与轨迹哈希、场景、任务类型、任务组、试次、候选池和排除理由在私有 Run 的 `protocol.json` 和 `selection.json`。v2 未执行的校准和 90＋30 清单保存在 `superseded_unexecuted_alfworld_full_library_calibration_20261109_03` 与 `superseded_unexecuted_alfworld_full_library_formal_20261109_02`，文件字节保留。旧代码与报告见提交 `52ba9da9`，旧 Run 及账本未改写。

## 请求与预算

动作与编译均使用 `deepseek-flash`，thinking disabled，temperature 0，保守输入上界 10,000 Token。每局至多 50 环境步、每步至多一次动作请求（输出 1,024）。直接模板消耗同一环境步数，回退只用剩余步。每个已锁定的在线成功至多一次 L2 请求（输出 500），L1、L3、检索和治理是本地操作。正常恢复只复用回执。两通道请求身份分离，共享同一账本。

- 正式上界为 6,000 次动作与 120 次 L2，共 6,120 次。逐请求 Token 合计上界 67,404,000；共享账本按较大单请求边界设置总量 67,466,880。实际派发仍分别执行 1,024/500 输出边界。
- 现有账本按 $1.20/百万 Token 逐请求向上取整预留。动作每请求最多 13,229 微美元，L2 为 12,600 微美元，全流合计 $80.886。新待批硬上限 $85，余量 $4.114，旧 $82 不继承。按已查表列峰价、无缓存且用满输入输出计算的理论费用上界为 $25.8048，账本规则更保守。 [DeepSeek 官方计价](https://api-docs.deepseek.com/quick_start/pricing/)
- 校准 800 动作＋12 L2，最坏预留 $10.7344，待批 $11。金额是本地派发边界，实际账单单列。供应商型号别名或价格变化需重新确认，不能悄悄更改冻结设置。截断和计量异常保留账本，UNKNOWN 阻断，未提交局不填成环境失败。

## 运行与恢复

在仓库根目录设置环境和校验冻结协议。预检不发 API。

```bash
export PYTHONPATH="FlowEvo/src:scripts"
py="$HOME/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python"
calibration="$HOME/.local/share/flowevo/alfworld_full_library_calibration_20261109_04"
formal="$HOME/.local/share/flowevo/alfworld_full_library_online120_20261109_01"
"$py" scripts/run_alfworld_success_baseline.py preflight --output "$calibration"
"$py" scripts/run_alfworld_success_baseline.py preflight --output "$formal"
```

校准独立授权后才写入校准授权文件。字段为 `run_id`、`purpose=calibration`、`protocol_sha256`、`max_cost_microusd=11000000`、`paid_api_authorized=true`。校准第 6 局主动暂停，复核后恢复。对真实指南分开核对生成有效性、跨局送达、行为采用、矛盾或伤害及无法判断。真实费用和暂停恢复须一致。没有可复核的实际使用时暂缓正式申请。CLI 只机械检查完成、L2 送达及暂停收据，采用和伤害由校准报告审查。

```bash
"$py" -u scripts/run_alfworld_success_baseline.py run --output "$calibration" \
  --authorization "$calibration/authorization.json" --pause-after 6
"$py" -u scripts/run_alfworld_success_baseline.py run --output "$calibration" \
  --authorization "$calibration/authorization.json"
```

正式校准通过并另获明确授权后才执行。正式授权字段同上，`purpose=formal`、`max_cost_microusd=85000000`，身份和哈希使用本协议正式 Run。正常题间暂停后可用原命令恢复，遇 UNKNOWN 或环境漂移先审计。

```bash
"$py" -u scripts/run_alfworld_success_baseline.py run --output "$formal" \
  --authorization "$formal/authorization.json"
```

## 输出

- `episodes.jsonl` 为题间提交链，保存每局结果、轨迹绑定、编译、治理、库及 RNG。每局另有 `environment.jsonl`、`locked.json` 和两通道 `requests.jsonl`。
- `checkpoints/{020,040,060,080,100,120}.json` 与 `final_bank.json` 从已提交链生成，含快照、协议哈希及绑定回执。正式流没有 `BANK_FROZEN` 事件。
- `summary.json` 包含全程、每 20 局、题型和逐局指标，逐局累计成功率、动作步数/调用、L2 编译调用、生成/入库/检索/实际介入、回退和治理。L2/L3 实际送达以请求为准，不能据此判定因果收益。账本与 Provider usage 分动作及编译两通道报告，另列估算、预留、实际账单（若有）及未提交局。运行故障由 `STOP.json` 和已提交链解释。
