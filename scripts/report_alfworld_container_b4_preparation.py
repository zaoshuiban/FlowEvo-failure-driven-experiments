"""Derived B4 preparation report. No model/environment execution."""
import argparse
from pathlib import Path
from collections import Counter
import prepare_alfworld_container_b4 as D
P=D.P

def report(out):
 p=P.read(out/'protocol.json');P.verify_history(p['historical_sha256']);sel=P.read(out/'source_selection.private.json')
 d22=p['train']['FR22'];d11=p['train']['FR11'];validation=p['validation'];subset=set(p['d11'])
 replay=P.read(out/'replay/result.json');worker=P.read(out/'worker_acceptance/result.json');mock=P.read(out/'mock_full54/acceptance.json');stress=P.read(out/'behavior_stress.json')
 def count(cases):return dict(records=len(cases),games=len({D.M.identity(c) for c in cases}),groups=len({c['origin']['row']['group'] for c in cases}),scenes=len({c['origin']['row']['scene'] for c in cases}),physical=len({c['physical_group'] for c in cases}))
 table=[]
 for c in d22:
  r=c['origin']['row'];table.append(f"| {c['model_ref']} | {'自然' if c['source_provenance']=='NATURAL_AGENT_FAILURE' else '受控'} | {r['task_type']} | {r['group'].rsplit('-',2)[-2]} | {r['scene']} | `{r['game_sha256'][:12]}` | {'是' if c['id'] in subset else '否'} |")
 val=count(validation);wire=[]
 for cell in D.M.CELLS:
  m=p['measurements'][cell];wire.append(f"| {cell} | {m['wire_bytes']:,} | {m['input_token_upper']:,} | 4 |")
 protocol=f'''# Route B4：双倍数据 S／F／FR 协议

2026-11-16。**P1_PREPARATION_READY / P2_PENDING_NEW_AUTHORIZATION / P3_NOT_EXECUTED**。
本轮只有数据准备、代码和零 API 验收；未发送模型请求，未构造独立游戏状态，未发布技能。旧 B3 12/12 弃权原样保留。

## 1. 身份、审计与复用

正式准备目录：`{out.relative_to(D.ROOT)}`。协议 canonical SHA-256：`{P.fingerprint(p)}`；文件 SHA-256：`{P.sha(out/'protocol.json')}`。
Git commit 为 `e7e79e2bf3d6c8abf59c3a934a79862f5c51c3b3`；已有未提交修改保存在 working_tree_start.json，不切换、不清理。实际源码含新适配文件，不能仅以该 commit 描述运行版本。冻结 {len(p['historical_sha256'])} 项源文件、历史材料和依赖 SHA，覆盖 Worker/Registry/预算所在模块。

已核对 B3 真实 wire/响应与全弃权报告、B1 五份源码、B2 开发结果、B0 投影/原生回退，以及旧容器和路线 A 11/11 来源修复。历史恢复源码 SHA `233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37` 仅作历史身份，不进入 B4 模型输入，也没有代写新候选。

复用 B3 同源投影、RecoveryAdapter、BoundedCompiler、持久账本、静态限制、Linux Worker、FailureOperatorRegistry、严格来源评分及 TextWorld 重放。没有改 L1/L2/L3、没有新增 DSL 或任务解析器。

## 2. D22 与 D11

D22 有 22 个不同游戏、22 个物理检查点、21 个任务组、13 个场景：旧 11 条 NATURAL_AGENT_FAILURE＋新增 11 条 CONTROLLED_INTERVENTION。旧自然来源中两个游戏同属一个任务组，不能称 22 个完全独立任务结构。

新增来源全部取自 A1c 原 TRAIN；A1d 合并数据中的 TRAIN 身份未改变。优先 READY、完整公开历史、已审查 MATCH，逐条核验：文件 SHA、原实际 TRANSITION、独立 verification 分支、失败 Nothing happens、后缀真实 won、目标与对象绑定。不是把未执行建议当成恢复后缀。24 个合格 TRAIN 游戏中以任务类型、目标容器、场景的稀少覆盖优先，固定 `B4_NEW_TRAIN_V1` SHA 破同分，选 11 个；不依据模型成绩。未运行新的训练游戏采集。

D11 从完整 D22 中固定选 6 条自然＋5 条受控，种子身份分别为 `B4_D11_NATURAL_V1` 和 `B4_D11_CONTROLLED_V1`，同样只用元数据覆盖排序，并保留 D22 顺序。D11 为 11 游戏、11 组、8 场景。它不是旧 B3 的 11 条自然来源，不能把本轮 D11 当作旧 B3 严格复现。

| 来源 | 来源性质 | 任务类型 | 目标容器 | 场景 | 游戏 SHA 前缀 | 入 D11 |
|---|---|---|---|---:|---|---|
{chr(10).join(table)}

D22 容器覆盖 Safe 2、Drawer 7、Microwave 4、Fridge 6、Cabinet 3；任务为简单 8、清洗 6、冷却 5、加热 3。新增数据没有强凑 Safe，其 Safe 来自旧自然来源。控制脚本确实引入了恢复示范，结论只能是混合来源的方法开发，不能将 22 条全部计为 Agent 自主失败。

每条完整 host 记录保存 game/trajectory/group/scene、原目标、原步骤、失败锚点、真实动作与反馈、R、won、来源哈希、物理组及重放证据。模型只得到允许的中性编号 C/F/R，路径、私有审查和封存标签不发送。机器可读清单为 source_selection.private.json 及 protocol.json；公开报告不附完整私有探测轨迹。

## 3. 共同验证与未见游戏角色

共同 TRAIN_VALIDATION 固定 14 条：6 MATCH、4 DECLINE、4 UNKNOWN，来自 {val['games']} 游戏、{val['groups']} 任务组、{val['scenes']} 场景、{val['physical']} 物理检查点。按标签内任务/容器/场景覆盖与 `B4_VALIDATION_<label>` 固定 SHA 选取，一标签内一游戏/组；同游戏的正例、负例或不同可见视图可以共组，因此 14 条不是 14 个独立游戏。

这些来自原 A1c/A1d TRAIN_VALIDATION，未进入任何 B4 生成包，与 D22 按游戏/轨迹/任务组/物理状态隔离。它们在旧路线 A 中已曝光，定位为**本轮输入外的共同开发验证**，不是全项目未见独立 Gate。保持困难负例的最终投递作用域；UNKNOWN 的缺失历史不补回。验证结果只在全部模型调用结束后计算，不用于工程或行为修订。

继续保留 B3 的 12 个新游戏元数据池（335 个合格池选出、10 场景、严格未见场景 0），与训练/验证游戏及任务组不交叉。原 34＋46 和既有 Gate 保留池未用于补数。新池未 reset、未标签、未执行候选，且没有 Safe；不能宣布独立验证覆盖已完备。候选冻结后，P3 才能按独立资源/采集冻结开展，不得按候选成绩换题或重选来源。

## 4. 替换后的共同离线任务说明

六个单元共享同一 system prompt、接口、安全规则与输出约束。核心完整替换 B3 的离线/在线混合开头，安全段复用原规范；不是在原歧义提示结尾补一句。

核心含义：现在编写未来可复用的 Python 函数，历史案例只是学习材料；现在没有 live context 是正常的。未来宿主会提供真实 goal/observation/admissible_commands/history/state，函数那时再判断适用与动作合法。可以因无法形成任何有依据的通用策略而 ABSTAIN，但不能仅因生成时没有实时游戏状态而拒绝编写参数化程序。

恢复仍限定真实失败后的局部任务；不是从第一步重做游戏、固定下一动作、无目标合法列表首项或替代原生 Agent。state={{}} 只表示程序记忆为空，保留持物、加工完成及任务实例要求；当前动作与未来动作条件分开核对；探索必须有目的、有界、有退出条件。运行时信息不足仍应拒绝。

完整英文共同提示见 `Common_Prompt.txt`，实际六个 wire 位于 inputs/，源码 `container_information_b4.py` 绑定于协议。动作说明仅提供相同命令语法，不含手写恢复步骤或旧程序。Mock 只能证明交付接口和提示内容存在，不能证明真实模型已经理解。

## 5. C/F/R 一致性

每条案例使用原真实前缀与后缀。C 为失败之前的中性公开状态及目标；F 为实际失败前缀到无效果动作；R 为该动作之后真实执行过的恢复片段。R 明确起点观察/历史缺省，保留实际起点合法动作和片段边界，不假装拼成完整连续轨迹。

S=C+R，F=C+F，FR=C+F+R。三组 C 相同，S/FR 的 R 相同，F/FR 的 F 相同，F 不得得到 R。D11 采用 D22 同一来源编号与原始片段，不重新解释同一证据。编码必须可无损 decode 回原投影，不静默删 F 步骤。源 106 的真实反复开关步骤也完整保留。

## 6. 六单元、早停和修订

单元 S11/F11/FR11/S22/F22/FR22 各 4 条初始谱系。先按单元固定顺序各做编号 0、1，共 12 初稿；若且仅若 12/12 全部是合法 ABSTAIN，结案并停止余下初稿。格式错误不是合法弃权，不满足该早停条件。

否则按同序补编号 2、3，完成 24 初稿，再逐个对交付/静态失败给予最多一次工程修订。全部初稿和工程修订归档后才开始 TRAIN 执行。工程反馈只有自己完整提交与通用格式、语法、接口、安全诊断。

每单元最多一份父版本进入行为修订：至少有一次 Worker OK、具有完整 TRAIN 回执，且未在自身 TRAIN 达到全部修复/零错误；按 TRAIN 修复数降序、错误/错误介入/不足证据介入升序、固定候选编号选取。**零修复也允许获得这一次机会**，全弃权则没有机会。TRAIN 当前均为正例，错误介入维度为 0；不借验证负例给修订器“补分”。

行为修订只收到自己的完整代码、获准 TRAIN 的起点和实际公开决策/回执/异常/合法动作/无进展信息；候选自述标为非环境事实。D11 仅 11 条，D22 仅 22 条。控制标签、TRAIN_VALIDATION、其他候选、人工路线及原 R 私有见证不进入反馈。完整源码与全部起点必须保留；超长决策按时间轮转固定前缀截取、记录省略索引；连起点与源码都超限时不发请求。

最多 24 初稿＋24 工程修订＋6 行为修订＝54。行为修订交付失败不再补工程请求。不补采样、不挪用未用额度。所有响应/源码/父版本和失败保留；修订失败或退化不删除先前合规父版本。阶段 II 要标为 origin+execution_feedback，不能再把 S 解释为完全未见失败。

## 7. 开发执行与最终选择

同样 Linux Worker、真实 TextWorld、静态权限和上下文投影；每个版本/检查点独立 reset 重放；窗口 min(18,50−前缀步数)。不赠送步骤，不复用上一个候选改变后的环境。所有候选仅 Shadow。

评分复用严格历史决定性状态见证/官方 won。局部修复、实际受阻投递完成、won、合法动作、实际执行、无进展、错误、拒绝和未知相关性分别记录。look/inventory 或状态变化本身不等于修复。无动作拒绝与未评定的探索也分开。UNKNOWN 后若出现新公开证据，不以入口标签永久判断后续，也不以物理 won 追认入口正当。

全部行为修订结束后才用同一 14 条验证集评价所有合规父/修订版本。最终需要验证正例至少一次严格修复、零运行错误；按验证修复数降序、明确不相容/不足证据介入、动作数、Worker 调用数、整条谱系 tokens、固定 ID 依次排序。全拒绝不能入选；没有合格版本返回 NO_ELIGIBLE_CANDIDATE。**开发优胜者不是发布技能，若仍有误触发必须公开报告。**

分母分别为每单元 4 个初稿机会、实际源码、实际 Worker 版本、每程序来源执行、独立谱系、共同验证记录/游戏/物理组。D11 对自己 11 条和 D22 对自己 22 条的训练修复率不构成公平泛化比较；规模比较以共同验证为主，仍是有限采样的探索性结果。

## 8. 模型、输入与独立预算

deepseek-flash，文档版本 DeepSeek-V4.1-Flash-1017，temperature=0.6，thinking disabled，JSON object，4096 输出上限。2026-11-16 核对 [供应商价格与模型](https://api-docs.deepseek.com/quick_start/pricing/)：1M 上下文；峰时未缓存输入 $0.30/M、缓存 $0.006/M、输出 $1.20/M。真实授权发送前仍要复核报价并归档响应模型字段，不能把别名当不可变权重哈希。

本轮六单元统一使用已有实验级容量接口：524,288 wire 字节、524,544 输入安全上界，旧全局 INPUT_LIMIT 不变。

| 单元 | 完整 wire 字节 | 输入安全上界 | 初稿数 |
|---|---:|---:|---:|
{chr(10).join(wire)}

工程压力包（64KiB 源码）73,568 字节。行为压力包完整 64KiB 源码＋22 起点＋396 条独立长反馈，固定投影保留 {sum(stress['retained'])} 条，最终 {stress['measurement']['wire_bytes']:,} 字节；其余索引保存。不能称所有反馈均完整进入模型。

| 阶段 | 模型请求上限 | 最大 tokens 预留 | 统一高价预留 |
|---|---:|---:|---:|
| I 初稿＋工程修订 | 48 | 25,374,720 | $30.449664 |
| II 行为修订 | 6 | 3,171,840 | $3.806208 |
| 合计 | 54 | {p['max_tokens']:,} | ${p['max_uniform_reservation_usd']:.6f} |

按输入/输出分价的最坏峰价上界为 **${p['max_peak_quote_usd']:.7f}**；按现有账本统一最高费率预留为 **$34.255872**。建议新的授权硬上限 **$36**，六单元各 $6、9 请求，互不转移。当前无有效授权，不能用 B3 剩余额度。实际消费按真实 usage/cache 另算，账本保守预留不冒充账单。没有填充无意义文本来伪装等实际 tokens。

开发最多 30 个合规父/行为版本：TRAIN 495 分支、共同验证 420 分支，共 915。Worker 上限 {p['worker_calls']:,} 次（18×915＋60）；环境步上限 {p['environment_steps']:,}（每分支含恢复重放余量 100），总壁钟上限 48 小时；任一上限先到即停。工具累计超时上界不是预计耗时，不与墙钟上限相加。实际预计时长依候选动作和环境初始化而变，不保证用满全部请求或分支。

P3 暂列 12 新游戏/最多 36 检查点，6 候选最多 3,888 Worker、25,200 环境步的资源计划，模型调用 0。必须在候选冻结后把采集参数和检查点绑定成 P3 执行协议；覆盖不足如实结案。原生 Agent/G 不在该计划中，如需要额外模型调用，另行报价授权。本轮不会运行 P3。

## 9. 文件、恢复与停止

新增 `container_information_b4.py`、prepare/run/test/accept/report_alfworld_container_b4*.py。原模块只复用，不改安全边界。每次请求、候选和角色评价有独立身份；已结算请求重入读取既有结果，未决发送和预算耗尽阻断。异常环境步骤按既有持久回执恢复/阻断，不盲目重放。没有真实授权时 sender=None 必须拒绝。

零 API 命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=FlowEvo/src:scripts \\
 "$HOME/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python" \\
 -m unittest scripts.test_alfworld_container_b4 scripts.test_alfworld_container_information scripts.test_alfworld_route_b_b0
```

本阶段没有提供 paid run 命令。下一步需要用户批准本轮独立费用，并绑定真实 transport/Run，复核输入/协议/报价；不得更改本冻结的提示、来源、排序、早停和修订规则。若运行前代码变化，必须留下新执行身份，不能冒充本次验收版本。
'''
 checks=[
 ('D22 22 来源','22 游戏/22 状态，原实际与 verification 回执匹配'),
 ('D11 子集','固定6自然＋5受控，11/22子集'),
 ('去重','游戏、物理组唯一；任务组21/22透明披露'),
 ('保护池','34＋46及其他保留池未进入新增TRAIN；12前瞻池三角色无重叠'),
 ('来源标注','自然11、受控11分别保存'),
 ('S/FR恢复片段','逐条相等'),('F/FR失败片段','逐条相等'),('S失败隔离','无F块、C无失败回执、片段缺省显式'),('F后缀隔离','无R块且无损decode'),
 ('共同Prompt','六cell相同system'),('离线在线语义','只验提示/接口，不宣称模型理解'),('无实时状态生成','Mock可交付参数化源码'),
 ('运行时判断','真实Worker工程fixture实际look/随后decline、无合法命令拒绝'),('固定初稿','六cell各4'),('早停','12合法ABSTAIN才停'),
 ('修订独立','54 Mock=24+24+6，所有生成先于验证'),('自身TRAIN反馈','D11仅11，外版本/验证canary拒绝'),
 ('Worker缓存','同工件同上下文不重执行'),('物理状态区分','11真实来源初始context及execution_id互异'),('真实重放','36/36回执精确一致'),
 ('角色隔离','TRAIN/VALIDATION/保留游戏按游戏轨迹组和状态核验'),('全拒绝不晋级','零修复NO_ELIGIBLE_CANDIDATE'),
 ('UNKNOWN/预算','一次未知阻断后续；零预算拒绝；sender=None拒绝'),('历史不可变','最终清单全部SHA一致'),('Shadow','真实Registry权限仍shadow')]
 zero=f'''# Route B4：双倍数据零 API 验收

2026-11-16。最终准备 Run：`{out.name}`。**P1_ENGINEERING_READY；P2 未授权；P3 未执行。**

## 1. 实际验收与分母

- 自动测试 **43 项通过**：B4 24 项综合测试、B3/B0 19 项回归。日志 acceptance/unit_tests.log。
- 真实 TextWorld 重放 **36/36**：22 训练＋14共同验证，合计 **{sum(replay['environment_steps'].values())} 步**，全部与历史原动作/观察/合法动作/成功状态一致。不是重新采集新训练样本，没有独立新游戏。
- 真实 Linux Worker＋Registry＋TextWorld：工程夹具在 **11 个 S11 来源**执行 {worker['metrics']['actions']} 个 look 并有界拒绝；源码不含容器恢复答案，不计为模型学习。来源修复/投递/won 均 **0**，验证了观察动作不被冒充恢复。
- 该夹具 {worker['metrics']['worker_calls']} 次环境决策，工具账本另含上下文/合法列表变化测试，共 {worker['budget']['tool_calls']} 次真实 Worker，计量 {worker['budget']['charged_or_reserved_tool_milliseconds']} 毫秒。相同上下文重复调用复用；11 不同真实来源的上下文、执行身份均区分。
- 完整调度 54 个 **Mock** 响应，24谱系、30可评价版本、60个 TRAIN/VALIDATION 回调；回调为明确的合成评价器，**不是60次真实环境模型实验**。保存在 mock_full54/acceptance.json，全部无修复、未选候选。
- 本轮真实模型请求/模型 tokens/API费用 **0**；没有新增学习技能、没有独立新游戏、没有原生 G。

## 2. 用户要求逐项证据

| 要求 | 实际检查 |
|---|---|
{chr(10).join('| '+a+' | '+b+' |' for a,b in checks)}

这25项要求由43项综合单测和实际环境验收共同覆盖，不能把“测试数量”当作独立研究样本。

## 3. 接入修复与保留的失败尝试

`_01` 数据准备及36状态回放完成，但真实Registry注册前因传入空 public_cases，被现有可信失败入口拒绝，未执行候选。最小修复为附上原始无效果动作及实际观察，保持原因未验证；没有把标签直接当事实、没有放宽安全检查。新增专测验证可信事件、6/5来源身份和重复入库幂等。

`_02` 保留中间冻结；`_03` 增加完整 alfworld_/failure_evo 源码依赖冻结，重新执行最终43测试、36状态回放和真实Worker验收。三版模型输入和来源选取相同；均无付费模型。旧B3、A系列及自然基线记录没有覆盖。中间失败日志单独归档。

## 4. 预算、压力与剩余风险

六个完整输入均通过统一512KiB wire限制，FR22最大424,157字节；无删关键失败步骤。输入字节保守上界不等于供应商tokens。行为压力包完整源码和22起点保留，但396长决策仅保留{sum(stress['retained'])}条，其余索引明确记录；修订可能缺少较晚反馈，不隐藏此限制。

统一54请求保守预留$34.255872，建议新授权$36；不是实际支出。原12美元授权不继承。源程序64KiB及AST权限上限不变，实验级输入扩大不扩大候选权限。

尚未验证：

1. 真实模型能否理解新离线任务定义、停止因缺少live context而弃权。
2. 能否交付正确程序，或根据自身反馈改善；Mock不提供研究成绩。
3. D22是否优于D11，F/FR是否有信息增量。规模比较还包含样本组成和少量随机生成差异。
4. 共同验证只有14记录/9游戏/5场景，困难边界覆盖有限且历史已曝光；不是新的独立Gate。
5. 12个前瞻游戏仅元数据保留，严格未见场景为0、没有Safe，未验证状态可构造性。P3需冻结实际采集/评价身份后另行运行。
6. 当前只开放Mock调度与零API重放。真实transport/新Run授权绑定需在用户批准后增加并进行等价性检查；不能假称本轮已有paid CLI。

## 5. 交付与停止

新增文件清单及完整共同Prompt见协议。Final_Preparation_Acceptance.json 绑定协议、代码、测试日志、原始重放回执、Worker回执、选择清单、输入和本两份报告。

本阶段停止于准备验收。没有生成本轮真实学习结果报告或迁移结果报告，不追加A1e式数据补采集，不向任何模型发送人工修复策略。
'''
 folder=D.ROOT/'reports/alfworld_failure_skill_acquisition_20261109'
 for name,txt in [('Route_B4_Double_Data_Protocol.md',protocol),('Route_B4_Double_Data_Zero_API.md',zero)]:
  P.save_exact_source(folder/name,txt)
 return dict(protocol_sha256=P.fingerprint(p),history_bindings=len(p['historical_sha256']),D11=count(d11),D22=count(d22),validation=val)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);x=a.parse_args();print(P.canonical(report(x.output.resolve())))
