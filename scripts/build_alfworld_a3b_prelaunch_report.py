"""Read-only summarization of completed zero-API A3b checks; no model calls."""
from pathlib import Path
from collections import Counter
from shutil import copyfile
import json
import run_alfworld_applicability_a3b as S
from alfworld_.applicability_semantic_feedback import paired_feedback
from failure_evo.contracts import fingerprint,canonical
from failure_evo.math_stream import read,sha
from audit_alfworld_a3b import archived_hashes

ROOT=S.B.ROOT
R=ROOT/'runs/alfworld_route_a_a3b_semantic_feedback_20261114_01'
OUT=ROOT/'reports/alfworld_failure_skill_acquisition_20261109/A3b'
OUT.mkdir(exist_ok=True)
def write(name,text):(OUT/name).write_text(text)
def save(name,obj):write(name,canonical(obj)+'\n')

plan,roles=S.preflight(R/'pilot_frozen');old=read(S.OLD/'result.json')
replay=read(R/'audit/replay_summary.json');traces=[json.loads(s) for s in (R/'audit/A3b_Decision_Trace.jsonl').read_text().splitlines()]
assert archived_hashes()==read(R/'audit/historical_sha256.json')
actual=read(R/'final_acceptance_v2/result.json');synthetic=read(R/'semantic_tests_v2/semantic_results.json')
cf=read(R/'counterfactual_v2/A3b_Counterfactual_Diagnostics.json')['rows']+read(R/'counterfactual_binding_only/A3b_Counterfactual_Diagnostics.json')['rows']
measurements=[]
for a in old['attempts'][:4]:
    diag={r['sample_id']:dict(candidate_version=a['version'],sample_id=r['sample_id'],split='TRAIN',trace=r['trace'],category=r['category'])
          for r in traces if r['candidate_version']==a['version'] and r['split']=='TRAIN'}
    r0,r1,binding=paired_feedback(a,roles['TRAIN'],plan['revision_policy'],diag)
    for branch,payload in [('R0',r0),('R1',r1)]:
        S.B.wire(R/'pilot_frozen',payload,S.prompts()[1],.6,plan['revision_policy'])
        measurements.append(dict(parent=a['candidate_id'],branch=branch,**S.I.measure(payload,S.prompts()[1]),selected=len(binding['sample_ids']),sample_ids_sha256=binding['sample_ids_sha256']))
initial=S.I.measure({'candidate_id':'candidate_0','training_input':read(R/'pilot_frozen/learning.private.json')},S.prompts()[0])
proxy_estimate=4*initial['estimated_peak_cost_usd']+sum(m['estimated_peak_cost_usd'] for m in measurements)
proxy_upper=4*initial['conservative_peak_cost_usd']+sum(m['conservative_peak_cost_usd'] for m in measurements)
input_upper=4*262400+8*393472;output_upper=12*4096
budget=dict(initial=initial,archived_parent_feedback_proxies=measurements,proxy_peak_estimate_usd=proxy_estimate,
 proxy_measured_bytes_peak_upper_usd=proxy_upper,full_protocol_peak_provider_upper_usd=(input_upper*.3+output_upper*1.2)/1e6,
 ledger_worst_usd=plan['max_tokens']*1.2/1e6,requested_not_authorized_usd=5.5,max_calls=12,max_tokens=plan['max_tokens'],
 worker_upper=plan['worker_calls'],environment_step_upper=plan['environment_steps'],actual_paid_calls=0,actual_paid_cost_usd=0,
 uncertainty='New drafts/feedback do not exist. Archive-based lengths are proxies, not guarantees or supplier usage; enforce hard wire bounds on both branches before either is sent.')
save('A3b_Budget_Estimate.json',budget)
# Keep detailed private trace and counterfactual artifacts in ignored local run storage; public reports carry hashes/aggregates.
save('A3b_Artifact_Manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in [R/'audit/A3b_Decision_Trace.jsonl',R/'counterfactual_v2/A3b_Counterfactual_Diagnostics.json',R/'counterfactual_binding_only/A3b_Counterfactual_Diagnostics.json',R/'semantic_tests_v2/semantic_results.json',R/'final_acceptance_v2/result.json',R/'pilot_frozen/protocol.json']})
copyfile(R/'semantic_tests_v2/A3b_Semantic_Unit_Tests.json',OUT/'A3b_Semantic_Unit_Tests.json')
for name in ('A3b_Semantic_Contract.md','A3b_Generation_Prompt.md'):copyfile(ROOT/'experiments/route_a3b'/name,OUT/name)
rows=[]
labels={'punctuation':'仅去目标句末标点','binding_raw':'仅类别—实例比较（不清理标点）','binding':'标点/冠词归一化＋类别实例比较','grammar':'仅扩展加工任务语法','grammar_plus_punctuation':'语法扩展＋去标点','instance':'仅取消未指定编号时强制编号相等'}
for key in sorted({(r['candidate'],r['intervention']) for r in cf}):
    rs=[r for r in cf if (r['candidate'],r['intervention'])==key]
    m=sum(r['expected']==r['after']=='MATCH' for r in rs);d=sum(r['expected']=='DECLINE' and r['after']=='MATCH' for r in rs);u=sum(r['expected']=='UNKNOWN' and r['after']=='MATCH' for r in rs)
    games=len({r['game_sha256'] for r in rs if r['expected']==r['after']=='MATCH'})
    rows.append(f"| {key[0]} | {labels[key[1]]} | {m}/47 | {d}/7 | {u}/13 | {games} |")
bycategory={k:dict(records=sum(r['category']==k for r in traces),games=len({r['game_sha256'] for r in traces if r['category']==k})) for k in sorted({r['category'] for r in traces})}
save('A3b_Diagnostic_Summary.json',dict(replay=replay,observational_categories=bycategory,
    not_confirmed_categories=['B_NORMALIZATION_ALONE','C_BINDING_ALONE','D_ROLE_CONFUSION','E_HISTORY_INTERPRETATION','F_UNJUSTIFIED_REJECTION','H_RUNTIME_ERROR'],
    note='Zero standalone causal counts mean not established, not absent. Counterfactual joint interventions reported separately.'))
write('A3b_Root_Cause_Audit.md',f'''# A3b 只读根因诊断

状态：DIAGNOSTIC_ONLY。没有新增模型请求，也没有修改 A3 成绩。原协议 `{fingerprint(read(S.OLD/'protocol.json'))}` 保持不变。

8 份源码 × 119 条记录 = **952 条决策**，原始状态及理由全部与归档一致；原始源码回放＋返回位置插桩共 **1,904 次真实 Linux Worker**。0 次环境动作。四组修订仍各自与初稿119/119判断相同。119条来自41个游戏，952不是独立样本数。

真实返回位置与包含它的 if 条件保存在 `audit/A3b_Decision_Trace.jsonl`。插桩只存在诊断副本，逐条核对三值判断不变；返回位置不是完整路径证明，更不是最深层根因。

## 原始拒绝落点

- 候选0/2：每个版本119/119落在目的地直接字符串比较；每版本85条正例被拒。四版本合计476次落点，不能当476个独立失败。
- 候选1：每版本59条目标解析未成功（其中39条正例）；另60条落在目标比较（其中46条正例）。
- 候选3：每版本8条正例目标解析未成功；111条落在目的地匹配（其中77条正例）。源码中要求动作里的编号也出现在目标描述。
- 两个版本合计94次正例直接停在目标解析；涉及游戏数量可从逐条记录按候选/版本去重。解析返回UNKNOWN有时符合监督标签，不能把所有解析失败都算分类错误。
- 观测分类：{canonical(bycategory)}。H没有观察到Worker/接口异常；B/C/D/E/F不能仅凭自述理由独立定因，未确证部分保留I，不填造根因。

## TRAIN 单因素及组合干预

事前固定：只用四份初稿、全部67条TRAIN、同一冻结Worker。共670次Worker，没有环境动作。旧验证集未用于选择干预样本。所有人工副本均标为DIAGNOSTIC_ONLY，不能注册为学习成功或晋级。

| 初稿 | 诊断干预 | 正例MATCH | DECLINE误MATCH | UNKNOWN误MATCH | 正例成功游戏数 |
|---|---|---:|---:|---:|---:|
{chr(10).join(rows)}

仅去标点或仅改变类别编号比较，对0/2都不足以恢复MATCH；组合条件才改变判断。因此不能把联合修补的结果全部归因于“实例绑定”。候选0组合干预恢复47条正例，同时引入5条UNKNOWN误接受。候选2组合干预仅恢复14条正例；后续还有33条正例停在处理对象比较。候选3放开未指定实例编号后仅恢复7条正例，36条正例仍被物体目标比较拒绝，4条仍解析失败。候选1仅去标点恢复22条正例；加工语法加标点修复才达到47条，未见TRAIN错误MATCH。

这些是开发者诊断副本的功能结果，**不是模型自主学到的能力，也不是独立泛化结果**。尤其候选1的人工诊断程序不得进入生成Prompt。

原始A3文件、源码、账本和NO_ELIGIBLE_CANDIDATE均逐文件SHA核对不变。第一次反事实诊断在发现插入位置错误后中止并保留；最终使用counterfactual_v2及binding_only，未覆盖旧目录。
''')
write('A3b_Input_Interface_Audit.md','''# 真实接口审计

`recovery_applicability.worker_artifact` 仅将 `goal`、`observation`、`admissible_commands`、`history` 四个键交给 `applicability_gate(context)`。外层Worker的state并未透传；public_history_scope也未透传。

返回必须恰为status/reason；status为MATCH、DECLINE、UNKNOWN，reason字符串不超过400字符。模型不能用state保存门控状态；仅MATCH允许冻结S0开始恢复。后续恢复状态由原S0控制。

新Prompt明确真实四键、类别与实例、显式编号、最终目标与中间位置、操作阶段、不完整历史及三值语义。没有新增运行时字段，没有把宿主目标解析器注入候选。合成测试中的参考解析器仅做独立诊断。

旧候选访问缺失字段的默认值可能造成保守拒绝；本次不通过补字段让它们获得额外证据。目标解析错误与真实冲突必须分别报告。
''')
write('A3b_Experiment_Protocol.md',f'''# A3b 配对开发实验（尚未付费运行）

运行身份：`{plan['run_id']}`。协议SHA：`{fingerprint(plan)}`。

保持：67 TRAIN/24游戏；52 TRAIN_VALIDATION/17游戏；原标签、物理检查点分组、S0 SHA `{plan['recovery_sha256']}`、Worker、18步来源恢复上限、50步整局上限、原A3准入和排序。TRAIN_VALIDATION已曝光，标为Previously inspected validation / development evidence，禁止进入模型输入。

新变化：固定语义契约生成4份初稿；每份从同一父版本分叉R0/R1，各最多1次修订。最多12次请求。初稿弃权则没有分支；重复源码不补采样，执行缓存保留原请求及共享回执身份；交付错误保留并最多按既定分支修订，不额外抽样。

R0复用原TRAIN反馈选择。R1使用完全相同选中ID和完整父源码，增加TRAIN真实返回分支、实际判断与可信标签，并引用同包公开证据的SHA。不会重复粘贴轨迹造成输入倍增。未定位原因写UNDETERMINED；候选自述不是环境事实。R1是“结构化执行诊断反馈策略”，不是单纯排版对照。两包先共同检查大小，一包超限即整对不发，不允许只运行容易放入上下文的一支。

固定顺序：4初稿；每父R0、R1；任何分支不会读另一分支反馈。模型deepseek-flash，temperature=0.6，thinking disabled，4096输出，供应商json_object。实际响应model字段原样保留，不虚构供应商隐藏版本。价格核验2026-11-14。

所有版本复用现有静态校验、Linux Worker、TRAIN/开发验证评分。可信正例MATCH时继续执行原有来源修复检查，不能只凭门控判断通过资格。全部保持Shadow。沿用原资格和排序；旧11来源/21边界本轮禁止使用，故即使选中也只冻结为PENDING_REGRESSION，不发布、不进入A4。

预算：最多{plan['max_tokens']:,}保守Token、{plan['worker_calls']:,}Worker调用、{plan['environment_steps']:,}环境步；12模型请求；拟授权$5.50，当前false。UNKNOWN/未决账本/未决环境操作停止，原请求不自动重发。完整已结算记录可恢复。反馈超限、弃权、静态失败或零合格候选均正常记录。

主要描述性指标：47/38正例覆盖，7/4可信负例误MATCH，13/10 UNKNOWN误MATCH；三值准确率、接口错误；每父R0/R1逐条改判、纠错、退化、新误触发及涉及游戏数。按游戏和检查点分组，不把多轨迹视为独立样本。四对模型生成也不是大量独立重复。不会用新Prompt与旧A3的差异宣称因果效果。

本次已经完成工程准备；真实结果仍NOT_RUN。未来执行命令仅在新授权后：

```sh
export PYTHONPATH="FlowEvo/src:scripts"
py="$HOME/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python"
run_dir="runs/alfworld_route_a_a3b_semantic_feedback_20261114_01/pilot_frozen"
"$py" scripts/run_alfworld_applicability_a3b.py preflight --output "$run_dir"
# authorization.json 必须对应本协议与新一轮明确授权；模板当前 paid_api_authorized=false。
caffeinate -i "$py" -u scripts/run_alfworld_applicability_a3b.py run --output "$run_dir" --authorization "$run_dir/authorization.json"
```
''')
write('A3b_Budget_Estimate.md',f'''# A3b 费用与资源（待批准）

已核验[DeepSeek官方价格](https://api-docs.deepseek.com/quick_start/pricing/)：Flash当前文档版本DeepSeek-V4.1-Flash-1017，峰时未缓存输入$0.30/M、输出$1.20/M，缓存输入$0.006/M；低谷半价。使用峰时未缓存作为保守估算，不依赖优惠。

初稿实际wire：{initial['wire_bytes']:,}字节，字符启发式约{initial['local_input_tokens_estimate']:,}输入Token。使用原A3四份初稿与真实TRAIN回执构造两类反馈的长度代理，最大{max(m['wire_bytes'] for m in measurements):,}字节；全部通过393216字节修订限制。这不是未来新稿的长度保证。

- 12请求字符启发式费用约 **${proxy_estimate:.3f}**（假定每次输出用满4096）。
- 现有代理wire按UTF8字节上界估算 **${proxy_upper:.3f}**。
- 全协议输入/输出硬上限按供应商峰时价格 **${budget['full_protocol_peak_provider_upper_usd']:.3f}**。
- 既有统一账本用$1.20/M覆盖全部Token的更保守预留上界 **${budget['ledger_worst_usd']:.3f}**。
- 因此建议新授权硬上限 **$5.50**；原A3的$3.50不继承。预留不是实际消费，真实成本按响应usage/缓存/时段另行计算。

最多1,428次常规门控执行、268次初稿TRAIN诊断、18,360次来源恢复Worker，合计20,056。来源环境两分支×12版本×85正例×50步=102,000步保守上限，受真实剩余步数再次限制。未运行旧曝光回归/A4。重复源码缓存或拒绝会降低实际资源。

当前新增付费调用 **0**、新增API费 **$0**。本地Worker/CPU实际耗时见各run账本，未给定硬件单价，不能伪装成零基础设施成本。
''')
# Full private diagnostics remain local run artifacts.
save('A3b_Results.json',dict(status='NOT_RUN',paid_requests=0,candidates=[],selection=None,reason='NEW_A3B_AUTHORIZATION_REQUIRED',mock_result=str(R/'final_acceptance_v2/result.json')))
write('A3b_Revision_Comparison.md','''# A3b 配对修订比较

状态：NOT_RUN。新真实初稿、R0、R1均未生成。不能用Mock判断数填入真实成绩。

运行后由applicability_paired_metrics.py输出每版本TRAIN/开发验证指标、逐样本变化、涉及游戏数、R1相对R0纠错/退化及完整账本。缺失执行覆盖记NOT_EVALUABLE，不以零替代。
''')
# Keep actual acceptance log with hashes, avoid unverifiable PASS text.
copyfile('/private/tmp/a3b_final_acceptance_v2.log',R/'A3b_Zero_API_Test_Log.txt')
freeze=dict(status='ENGINEERING_READY_PENDING_NEW_AUTHORIZATION',protocol_sha256=fingerprint(plan),run_id=plan['run_id'],
    paid_api_authorized=False,new_paid_requests=0,S0_sha256=sha(S.B.CODE),historical_a3_unchanged=True,
    A4='NOT_RUN',validation_role=plan['validation_role'],authorization_template=str(R/'pilot_frozen/authorization.template.json'),
    evidence={str(p.relative_to(ROOT)):sha(p) for p in [R/'audit/replay_summary.json',R/'final_acceptance_v2/result.json',R/'A3b_Zero_API_Test_Log.txt',R/'semantic_tests_v2/semantic_results.json']})
save('A3b_Prelaunch_Freeze.json',freeze)
write('A3b_Zero_API_Test_Report.md',f'''# A3b 零API验收

最终命令：
```sh
A3B_REAL_WORKER=1 A3B_TEST_OUTPUT=<新的工程目录> PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=FlowEvo/src:scripts "$HOME/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python" -m unittest scripts.test_alfworld_applicability_a3b scripts.test_alfworld_applicability_multicandidate.CoreTests scripts.test_alfworld_applicability_multicandidate.ArchivedReceiptsTests -v
```

**22项通过**，实际日志A3b_Zero_API_Test_Log.txt（含32.710秒测试时间）。覆盖同父双分支/同TRAIN ID/异候选反馈拒绝/无验证泄漏/完整源码/温度wire/全拒绝不可晋级/旧授权拒绝/数据漂移/UNKNOWN不重发/预算中止/统计零分母/历史回归。

完整Mock链：12个独立已结算响应、{actual['budget']['tool_calls']}次真实Linux Worker；有真实TextWorld来源前缀和S0恢复动作。初稿后故意中断并恢复，总请求仍12；完成后再次进入不会重发或增加费用。全部Shadow，未执行旧11/21或A4。Mock策略含常量返回，只用于测试执行/选择，不是自主学习成果。

合成24条分层：现有宿主参考解析器8/8；归档候选1语义判断5/8；严格四字段Worker接口8/8。后三个旧门控语义失败被正确观测，不能把“测试架构通过”写成新模型语义能力通过。编号在既有解析器中是字符串；首次工程预期写整数导致1例类型不符，已独立记录并修正夹具，未修改解析器或模型源码。

历史回放：952/952状态和理由复现，插桩诊断952/952状态保持，共1,904Worker。人工反事实670Worker。最终证据路径及SHA见Artifact_Manifest；旧A3文件全量SHA未变。

工程过程中曾发现：诊断证据迁移缺少配套源码工件、诊断副本语法插入顺序、候选冻结目录未创建。修复仅涉及新工具；所有未完成目录保留，不删改历史或伪造成功。旧的mock_acceptance/final_mock_acceptance/pilot目录不是最终新授权目标；最终为final_acceptance_v2和pilot_frozen。
''')
write('A3b_Final_Report.md',f'''# Route A3b 工程准备与只读诊断报告

**ENGINEERING_READY / PAID_NOT_RUN**。原A3仍为NO_ELIGIBLE_CANDIDATE；没有新的付费请求，没有运行A4。

1. 原8版本952条判断与理由完整复现，四组修订均未改变旧行为。S0与旧Run逐文件SHA不变。
2. 目标语义确实阻断覆盖，但存在叠加问题：单修标点或类别比较对0/2无效；组合归一化/绑定后0达到47/47 TRAIN正例，同时误MATCH 5/13 UNKNOWN。1需要语法和标点联合改善；2/3还有物体目标解析阻断。所有这些都是人工诊断副本，不计自主学习成绩。
3. 新语义契约严格对应四字段真实接口；没有添加state/public_history_scope，没有隐式注入人工解析器。
4. 已实现4初稿→同父R0/R1各一次修订；同TRAIN ID、独立请求、完整源码与反馈hash、现有安全Worker/来源恢复/资格逻辑复用。R1新增真实返回分支，不把自述理由当事实。
5. 最终22项工程测试通过；24条合成诊断分层8/8、5/8、8/8。真实Worker和TextWorld已执行，Mock不算学习成果。零分母/缺失配对保留不可评价。
6. 现有验证集已曝光，只能做开发资格和描述性比较；正例门控通过还必须保留来源修复检查。旧曝光回归本轮禁止，最终选中也保持待回归Shadow，不能发布或自动A4。
7. 新协议SHA：`{fingerprint(plan)}`。预计供应商费用约${proxy_estimate:.2f}（仅旧稿长度代理）；保守账本上界${budget['ledger_worst_usd']:.2f}，建议独立授权 **$5.50**。尚无授权文件，paid_api_authorized=false，旧$3.50不可复用。

## 实际新增文件

- applicability_semantic_feedback.py：分支诊断、同样本双反馈。
- applicability_paired_metrics.py：只读逐版本与配对指标。
- run_alfworld_applicability_a3b.py：复用旧引擎的双分支入口、冻结、预算、恢复。
- audit_alfworld_a3b.py、diagnose_alfworld_a3b_counterfactual.py：只读回放/DIAGNOSTIC_ONLY副本。
- test_alfworld_applicability_a3b.py、test_alfworld_a3b_semantics.py：工程与分层语义测试。
- experiments/route_a3b两份语义契约与Prompt；本报告目录；新run独立归档。

本轮没有修改旧A3/S0/Worker/Registry/准入排序实现。工作树已有其他历史未提交改动，不属于本次新增修复，不进行整体提交或推送。

仍待真实实验回答：新语义契约能否生成有正例覆盖的门控；R1是否比同父R0更好；是否会增加困难负例或UNKNOWN误触发。当前工程结果不能回答这些学习效果问题。获得新的明确授权后才能运行pilot_frozen；本次在此停止。
''')
print(canonical(dict(report=str(OUT/'A3b_Final_Report.md'),freeze=freeze['status'],protocol=fingerprint(plan),budget=budget['requested_not_authorized_usd'],estimated=proxy_estimate)))
