# 路线 A · A2：多候选反馈学习实现与零 API 验收

2026-11-13。

**工程状态：`A2_ENGINEERING_READY`。真实学习状态：`A3_DATA_NOT_READY`。**

已实现四候选独立初稿、TRAIN 执行反馈、每候选最多一次修订、固定排序、最终冻结及曝光回归。完成真实 Linux Worker 和 TextWorld 验收。所有模型响应均为明确标记的手写 Mock，不能计作自主学习成果。

本轮没有发送付费模型请求，没有执行独立 Gate，没有发布技能，没有重新采集 A1b 数据。新增模型费用为 **$0**。A1b 仍只有 8 条 TRAIN、2 条 TRAIN_VALIDATION；后者来自一个有效游戏且缺 UNKNOWN。

## 1. 复用边界与文件变化

已阅读 A1 方法与选择规则、A1b 数据报告、标签模块、S1 门控与 Rule、Python 交付反馈、S1 实际入口和测试。

| 文件 | 实际变化 |
|---|---|
| `FlowEvo/src/alfworld_/recovery_applicability_learning.py` | 新增：数据身份与白名单、分组隔离、反馈分类、单候选修订投影、冻结选择规则 |
| `scripts/run_alfworld_applicability_multicandidate.py` | 新增：Mock-only 四候选入口，接入原账本、Worker、Registry、环境重放及曝光回归 |
| `scripts/test_alfworld_applicability_multicandidate.py` | 新增：纯逻辑、真实 Worker/TextWorld、恢复和旧 wire 兼容验收 |
| `FlowEvo/src/alfworld_/recovery_acquisition.py` | 最小修改：可选 temperature，默认仍为 0；非零值绑定作业身份和实际 wire |

没有复制 Worker、Registry、模型预算或环境账本。使用原 `RecoveryAdapter → BoundedCompiler → replay_train_generation`，以及 `PersistentBudget`、`FailureOperatorRegistry`、`EnvironmentPolicyRunner`、`validate_source` 和 `EnvironmentReceipts`。

冻结恢复源码实测 SHA-256 始终为：

`233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37`

只生成 `applicability_gate(context)`。门控通过既有 `worker_artifact()` 封装执行，原门控源码与封装工件分别记录 SHA；只有 MATCH 才进入恢复程序。进入后不再重复调用门控，后续动作及回退由原冻结恢复程序和现有执行器控制。

## 2. 数据角色、身份与隔离

从 A1b 的 `dataset.json` 核对 TRAIN/VALIDATION 文件 SHA、审查文件 SHA、审查后的逐条记录和公开模型视图。模型输入使用已审核的公共投影，不包含私有恢复探测后缀、游戏路径、Rule、隐藏状态或验证集标签。

同一游戏或物理检查点组不得跨 TRAIN / TRAIN_VALIDATION。UNKNOWN 的不完整历史标志保留在监督包中；运行时门控仍使用既有四字段公开上下文，不额外添加私有状态。

候选工件绑定：候选 ID、初稿/修订号、父版本、父源码 SHA、请求 payload/wire SHA、响应 SHA、原始源码 SHA、数据版本、Worker 身份。恢复执行分支还绑定门控版本，防止新修订错误接续旧候选的环境状态。

A1b 的真实数据用于工程诊断，但 `DATA_COVERAGE_BLOCKED` 阻止正式选择和付费运行。为了单独检验完整选择流程，另建 **ENGINEERING_FIXTURE** 数据视图，附加一条显式工程 UNKNOWN；它没有写回 A1b，也没有被统计为新的可信环境样本。

## 3. 四候选与修订流程

```text
冻结协议、TRAIN 公开投影、恢复源码和 Worker
→ candidate_0..3 各自独立初稿请求
→ 严格交付、源码保存、门控接口及静态安全检查
→ 真实 Worker 分别判断 TRAIN / TRAIN_VALIDATION
→ 可信 MATCH 正例上，允许执行冻结恢复程序
→ 初稿各自按冻结条件决定是否修订，最多一次
→ 完整新源码重新检查、执行与评价
→ Best Initial 和全部版本按 A1 规则选择
→ 保存 selected.json，之后才执行曝光回归
```

初稿共 4 次；最多再发 4 次修订，总上限 8。ABSTAIN、重复源码和输入超限不补采样。交付或静态拒绝可消耗一次既定修订机会；合法候选存在自身 TRAIN 分类错误或来源修复失败时才触发修订。第二轮拒绝或失败即保留结果，不追加请求。

重复源码保留独立请求和原始响应，记录 `DUPLICATE_SOURCE` 与前一版本引用，不当作新的有效候选执行。输入包超出冻结上限时记录 `INPUT_LIMIT`，不发送模型请求。

修订模型得到完整上一源码；宿主不修改门控算法。Mock 源码是测试夹具，不是模型学习的程序。

## 4. 反馈与错误分类

每个候选只能收到自己版本的 TRAIN 记录。反馈校验候选 ID、父版本、样本身份和数据角色。

| 来源 | 修订包中的表示 |
|---|---|
| 候选判断与理由 | `candidate_self_report`，明确不是环境真值 |
| Worker 执行 | execution ID、状态、上下文 SHA |
| 可信监督 | 冻结标签、分类错误、允许公开的标签依据 |
| 恢复执行 | 实际执行动作与回执、是否验证修复；注明来自冻结恢复程序 |
| 交付/静态问题 | 单独保存 delivery 与 static 诊断 |

分类包括 `FALSE_REJECTION`、`FALSE_APPLICABILITY`、`UNSUPPORTED_MATCH`、`UNNECESSARY_UNKNOWN`、`WORKER_ERROR`。UNKNOWN 被判为确定拒绝的情况另记 `UNCERTAINTY_MISCLASSIFIED`，不能和直接 MATCH 的风险混为一项。

TRAIN_VALIDATION 可以供宿主评价和排序，但不进入修订包或决定是否再给某候选追加机会。Rule、其他候选反馈和曝光回归结果也不进入修订。

本阶段负例与 UNKNOWN 执行真实门控 Worker，错误 MATCH 按冻结标签计数；不利用它们的私有完整状态继续跑恢复环境。真实恢复重放限定在有可靠映射的 MATCH 正例。曝光边界另执行冻结恢复程序的 Worker 动作选择检查，**不把“选出动作”说成环境已经执行该动作**。

## 5. 选择、冻结和权限

沿用 A1 已冻结规则，不新增结果导向权重：

1. 工程有效，且在 TRAIN 和 TRAIN_VALIDATION 可信正例上全部 MATCH；有真实恢复映射时，来源恢复也必须通过。
2. 排序依次比较验证集负例误 MATCH、UNKNOWN 误 MATCH、运行错误；再比较 TRAIN 同项、不必要 UNKNOWN、模型调用占用和固定候选编号/版本。
3. 全拒绝门控不能进入排序。记录 Best Initial 与最终选择，不删除较差版本。
4. 先冻结所选版本，再跑 11 个来源与 21 个曝光边界。来源保留失败标为 `SELECTED_BUT_RETENTION_FAILED`，不换候选、不追加修订。

| 状态 | 含义 |
|---|---|
| `DATA_COVERAGE_BLOCKED` | 数据不足，不能产生正式胜者 |
| `NO_ELIGIBLE_CANDIDATE` | 数据具备基本覆盖，但无候选满足条件 |
| `SELECTED_PENDING_REGRESSION` | 已冻结候选，等待曝光回归；选择记录不被回归重写 |
| `ENGINEERING_SELECTION_VALID` | Mock 选择流程正确运行，不是科研有效优胜者 |
| `ENGINEERING_REGRESSION_PASSED` | 已冻结工程夹具通过所执行的保留检查 |

所有注册事件都是 `SHADOW_REGISTERED`。没有生成试用授权，也没有把工程选择转换为正式发布。A2 入口不提供有效付费授权；即使工程夹具覆盖完整，真实请求仍被 `A2_ENGINEERING_ONLY_NO_PAID_AUTHORIZATION` 阻断。

## 6. 实际零 API 结果

最终验收目录：`runs/alfworld_route_a_a2_20261113_01/final_acceptance/`。

| 验收场景 | Mock 响应 | 真实 Worker 调用 | TextWorld 步数 | 结果 |
|---|---:|---:|---:|---|
| `actual_a1b` | 8 | 64 | 282 | 四初稿＋四修订；`DATA_COVERAGE_BLOCKED`，未运行选择后回归 |
| `engineering_selection` | 5 | 88 | 341 | 工程选择冻结；11 个来源修复，21 个边界完整记录 |
| `resume` | 4 | 0 | 0 | 第一次结算后中断，恢复总计仍为 4 次请求 |
| `worker_errors` | 8 | 40 | 0 | DECLINE、UNKNOWN、Python 异常及错误输出契约均独立记录 |
| **合计** | **25** | **192** | **623** | 全部为工程验收 |

这些环境步数是对冻结状态的重新验证，**不是重新采集 A1b 数据**。192 次 Worker 调用累计记录约 65.57 秒本地执行时间。Mock usage 回执总计 5,000 Token，仅用于计量测试；实际付费模型 Token 为 0。

`actual_a1b` 中的初稿分别覆盖：合法 UNKNOWN、合法 MATCH、禁止导入、外层必需字段缺失。修订覆盖新版本、重复源码与弃权。三份允许恢复的版本分别从原检查点重放了 4 个正例，12 次来源执行均完成冻结恢复；没有接着父版本的环境状态执行。

`engineering_selection` 故意使用“全部 MATCH”工程夹具：来源修复 11/11，但 21 个边界全被门控接受，冻结恢复程序在其中 3 个边界选出了动作。这是测试选择与记录链路的夹具，**不是安全门控、有效学习结果或可发布候选**。A1 的排序不等于零风险准入，Shadow 权限仍必须保留。

### 测试证据

共 **54 个不同测试通过**：A2 11 个纯逻辑测试＋4 个真实执行测试＋2 个归档回执审计测试；原生成功基线 9 项；A1b 21 项；A1 7 项。

- 四初稿身份、实际 temperature=0.6、父版本和完整父源码绑定。
- 重复源码不补采样；交付、静态、Worker 错误分离；三个门控状态实际在 Linux Worker 执行。
- 三类主要适用性错误、自己的 TRAIN 反馈、验证集隔离。
- 同长度但不同可信标签的工程夹具：宿主按标签评分，不按窗口长度赋值。此测试不证明未来模型不会学到捷径。
- 正例覆盖准入、全拒绝不能晋级、数据不足与无候选的不同状态、固定排序可重放。
- 真实 TextWorld 原检查点重置、冻结恢复程序执行、最终选择后曝光回归。
- `SEND_UNKNOWN` 保留费用预留并阻断后续请求；预算不足时 sender 未被调用。
- 中断后已结算响应重入、完整 Run 重入均不重复请求或费用；原生治理、holdout、120 局续跑和 `done/won` 区分的旧测试通过。
- 旧 S1 默认温度 0 的实际 wire 与归档 wire 逐字节相同。

日志：`acceptance_final.log` 14 项通过（当次加载 10 个纯逻辑＋4 个真实执行）；`regression.log` 48 项通过（含后来补入的旧 wire 测试），另有 `receipt_audit_tests.log` 2 项归档回执审计通过；扣除重复项后共 54 项。两项审计确认修订从完整原前缀开始，以及四初稿先于修订且模型输入不含验证样本身份。

首次工程验收在曝光回归入口发现历史源码身份比较阻断，日志与目录均保留。原因是旧入口用当前源码重建旧付费实验身份；新增温度配置使其代码哈希改变。A2 新读取路径复用历史数据加载器，直接核对归档协议 SHA、检查点 SHA、边界 SHA、S0 结果 SHA 和 Worker 身份，未放宽旧实验入口。修正后在独立验收目录重新通过完整链路。

## 7. 请求与资源预算准备

以下为 **待 A1c 补数后重新冻结的估算，不是授权**。

模型配置：`deepseek-flash`，thinking disabled，temperature 0.6，单次输出上限 4,096 Token。此次只通过 Mock sender 检查真实 wire，没有验证真实模型的采样多样性或源码交付率。

| 项目 | 当前 10 条数据上的数值 |
|---|---:|
| 初稿数 | 4 |
| 修订数 | 至多 4 |
| 每次初稿实际 wire 保守输入上界 | 29,155 |
| 本轮 Mock 修订实际包上界 | 30,383–40,759 |
| 每次未来修订允许输入上界 | 65,536 |
| 每次输出上界 | 4,096 |
| 当前输入大小下 4＋4 Token 上界 | **411,532** |
| 通用账本 Token 硬上限 | 557,056 |

输入上界采用实际 wire 的 UTF-8 字节数＋256，是保守预留，不是供应商实际 Token。真实输出可能使反馈包变大；超过 65,536 时停止该提交，不能假定所有未来源码都装得下。

2026-11-13 核查的 DeepSeek Flash 峰时未缓存输入价为 $0.30/百万 Token，输出 $1.20/百万 Token。按当前输入包与上述修订上限，模型报价上界约 **$0.152951**；沿用账本将全部 Token 按 $1.20/百万保守预留，逐请求向上取整约 **$0.493844**。Mock 协议设置的通用费用硬上限为 **$0.70**，没有生成有效付费授权。[供应商计价](https://api-docs.deepseek.com/quick_start/pricing/)

| 阶段 | 门控 Worker 上界 | 恢复 Worker 上界 | 环境前缀上界 | 恢复动作上界 |
|---|---:|---:|---:|---:|
| TRAIN，最多8版本 | 64 | 432 | 440 | 432 |
| TRAIN_VALIDATION，最多8版本 | 16 | 144 | 248 | 144 |
| 最终曝光回归，唯一所选版本 | 32 | 190 | 225 | 169 |

回归的 190 次恢复 Worker 上界包含 169 个来源动作槽和 21 个边界动作选择检查；后者不执行环境动作。精确结构估算共 878 次 Worker 上界，运行协议保守上限 **907**。正常环境步骤细算上界 1,658，运行协议保守上限 **4,300**，包含受控恢复重放余量；单分支依旧不能超过 50 步。

未知请求自动重发额度始终为 0。额外环境重放也消耗同一有界账本；存在未决环境步骤或 Worker 步骤时先阻断，余量不构成自动重试权限。Worker 按真实调用数和耗时记录，未指定本机算力货币单价，不能把未计价 CPU 成本写成免费的研究成本。

详细包大小、阶段预算及价格来源保存在 `runs/alfworld_route_a_a2_20261113_01/budget_estimate.json`。A1c 改变样本数或前缀后必须重算。

## 8. 完整性、运行方式和剩余阻断

开始时冻结的 100 个文件中，99 个历史运行工件未变，唯一修改是本轮明确允许的 `recovery_acquisition.py`。S0 恢复源码、A1b 数据、旧 S1 结果均保持原始 SHA。新原始响应、源码、训练反馈、环境和 Worker 日志均在 Git 排除的私有 runs 目录中；公开报告只保留摘要与哈希。

主要入口：

```bash
cd "/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments"
export PYTHONPATH="FlowEvo/src:scripts"
py="$HOME/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python"

# 纯逻辑验收：无付费、无环境执行
PYTHONDONTWRITEBYTECODE=1 "$py" -m unittest -v \
  test_alfworld_applicability_multicandidate.CoreTests

# 再次执行完整工程验收须指定一个尚不存在的新私有目录，保留旧记录
ALFWORLD_A2_REAL_ACCEPTANCE=1 \
ALFWORLD_A2_OUTPUT="$PWD/runs/alfworld_route_a_a2_new_acceptance" \
PYTHONDONTWRITEBYTECODE=1 "$py" -m unittest -v \
  test_alfworld_applicability_multicandidate
```

数据入口支持 `prepare`、`preflight`、`mock_run --mock-responses <固定JSON文件>`；同一 `mock_run` 是幂等恢复入口，不提供真实 API 的 run/authorize 子命令。

当前阻断仍是：TRAIN_VALIDATION 缺 UNKNOWN 且有效游戏仅 1 个；难的目标/阶段/实例冲突负例仍不足。补数必须进入独立 A1c 冻结流程。A3 还需要新协议、重算预算及明确授权，不能用本轮附加的工程夹具补齐研究证据。

因此可以确认多候选反馈学习的工程路径已贯通；尚不能确认失败经验提高门控质量，更不能报告独立迁移收益。本轮在 A2 验收完成后停止。
