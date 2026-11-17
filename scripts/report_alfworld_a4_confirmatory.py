"""Read-only C1 closeout. Does not execute policies or environments."""
from pathlib import Path
import argparse
from collections import Counter, defaultdict
import run_alfworld_a4_confirmatory as A


def finish(root):
    start=A.read(root/'start_snapshot.private.json')
    changed=[p for p,h in start['historical_sha256'].items() if A.sha(p)!=h]
    if changed:raise PermissionError('historical artifacts changed')
    plan=A.read(root/'collection/protocol.json');ready=A.read(root/'C1_Readiness.json')
    labels=A.read(root/'collection/review.private.json');metadata=A.read(root/'metadata_audit.json')
    inv=A.read(root/'exposure.private.json');summary=A.read(root/'collection/collection_summary.json')
    physical=defaultdict(set);physical_files={}
    def walk(x,path):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ('physical_state_group_id','physical_checkpoint_identity') and isinstance(v,str):physical[v].add(str(path))
                else:walk(v,path)
        elif isinstance(x,list):
            for v in x:walk(v,path)
    # Additional explicit physical identities: game/trajectory exclusion already
    # protected all descendants before collection. Old snapshots remain intact.
    for p in start['historical_sha256']:
        if p.endswith('.json'):
            before=sum(len(v) for v in physical.values());walk(A.read(p),p)
            if sum(len(v) for v in physical.values())>before:physical_files[p]=A.sha(p)
    new={s['physical_state_group_id'] for s in labels['samples']}
    overlap=sorted(new&set(physical))
    if overlap:raise PermissionError('physical state overlap')
    A.commit(root/'physical_identity_audit.private.json',dict(historical_ids={k:sorted(v) for k,v in physical.items()},files=physical_files,new_ids=sorted(new),overlap=overlap,
        timing='explicit physical-ID audit after collection; pre-collection game/trajectory exclusion already excluded every old-game physical state'))
    events=[A.json.loads(s) for s in (root/'collection/environment.jsonl').read_text().splitlines()]
    kinds=Counter(e['kind'] for e in events)
    audit=dict(historical_files_checked=len(start['historical_sha256']),historical_files_changed=[],
        historical_physical_ids=len(physical),new_physical_ids=len(new),physical_overlap=overlap,
        environment_event_counts=dict(kinds),environment_receipts_sha256=A.sha(root/'collection/environment.jsonl'),
        frozen_source_and_data_hashes_pass=all(A.sha(f)==h for f,h in plan['files'].items()),
        paid_requests=0,candidate_executions=0,C2_executed=False,publication=False)
    A.commit(root/'Completion_Audit.json',audit)
    scorer=A.read(root/'scoring_regression.json');arms=A.read(root/'Candidate_Freeze.json')['arms']
    report=A.ROOT/'reports/alfworld_failure_skill_acquisition_20261109/A4_Confirmatory';report.mkdir(exist_ok=True)
    rows='\n'.join(f"| {l} | {v['records']} | {v['games']} | {v['physical_groups']} | {v['scenes']} |" for l,v in ready['coverage']['strict_scene'].items())
    sources='\n'.join(f"- {name}: `{r['sha256']}`" for name,r in arms.items())
    reasons='\n'.join(f'- {reason}: {n}' for reason,n in Counter(s['reason'] for s in labels['unresolved']).items())
    p=f'''# Route A A4 Confirmatory：C1准备与阻断报告

日期：2026-11-15。最终状态：**C1_BLOCKED_DATA_COVERAGE；C2_NOT_RUN**。

本轮完成真实独立游戏身份审计、评分器只读兼容验收、规则/资源冻结及6个新游戏的宿主检查点采集。没有执行S0/S1/Rule/A3b新评价，没有模型请求，没有修改任何候选或历史成绩。数据准备失败不能解释为候选泛化失败。

## 1. 起始工作树与四组身份

基线commit：`{start['commit']}`。工作树含此前修改和未跟踪文件；完整git status和tracked diff保存在start_snapshot.private.json，没有切换或清理。{len(start['historical_sha256'])}份相关历史工件逐文件SHA已在采集前冻结，收尾全部一致。S0动作程序与三份门控原版本不变，均保持Shadow；A3b为初稿candidate_0，不是R0/R1。

{sources}

未执行新的候选发布、模型学习、选择或修订。

## 2. 全部曝光与预留保护

审查明确数据目录的train/valid_seen/valid_unseen共{metadata['dataset_games']}个游戏，不把本地valid_train等附加目录混入。递归扫描仓库runs和本机flowevo存储的JSONL身份；合并protocol的tasks/future_tasks/gate_shards、selection、roles和封存池。命中及分配文件共{len(inv['files'])}份，逐文件哈希与逐游戏排除依据保存在exposure.private.json。

保护{metadata['protected_games']}个游戏、{metadata['protected_scenes']}个场景，包含实际日志命中与未执行但仍预留的分配；这个数量**不是已执行游戏数**。元数据inventory里的eligible/excluded行不直接当作曝光。保护依据包含game SHA、trajectory SHA、task group、scene；同游戏全部物理状态随之排除。补充逐字段审计得到{len(physical)}个旧物理组ID，新{len(new)}个物理组与其交集为0。该显式物理ID清单在采集后补充，采集前已完成更保守的整游戏/轨迹排除。

原34＋46池不是剩余63局未曝光：80局均有GAME_STARTED和GAME_COMPLETED、实际宿主交互。只有17局/52条产生了A4候选评价，但其余局也不满足本次“未执行、未标注”的新游戏要求。旧80局全部排除，没有拿旧A4补数据。

审计覆盖本机可访问受控记录，不能证明没有外部、丢失或未记录的活动。冻结分配也被保守保护，因此未将未知是否曝光的材料当作新材料。

## 3. 新游戏规则与真实采集

在已有容器采集器支持范围内，仅从train挑选未保护游戏/轨迹/任务组，使用原4类放置任务及5类目标容器的元数据范围。该范围是宿主数据构造范围，不是修改候选规则。严格场景候选只有6局、3任务组、3场景（402、405、408），全部清洗后放入Cabinet。所有6局按路径顺序冻结并执行，不抽取容易成功的局、不补位。

跨split审计另发现2个valid_seen元数据候选，分别与所选游戏共享402/405场景及相同任务组。它们未执行：本轮冻结train-only范围以兼容现有候选来源执行器，不在看到标签后跨split追加。它们不是不存在，也不构成两个新的场景或任务组；本轮不能据此声称所有可能数据已经耗尽。

补充层有341个符合相同元数据范围的未见游戏、32场景，但仅保存元数据，没有采集、标注或运行候选。事前冻结先采集严格层；严格层不足即停止，不用扩充层代替主要结论。当前不足只针对本地隔离约束和冻结构造协议，**不证明ALFWorld不存在其他可用机制或任何方法都无法构造负例**。

使用既有A1d公开搜索、受控失败投递、宿主参考探针、独立reset回放及确定性标签审核，没有学习模型或四组候选参与标签。每个分支原目标不变，不能读取隐藏任务状态/专家计划来规划。环境初始化枚举数据文件不等于在其余游戏执行交互，实际reset均绑定冻结游戏SHA。参考探针只留在HOST_ONLY工件，不提供给未来候选。

## 4. 实际标签与停止原因

| 标签 | 记录 | 游戏 | 物理组 | 场景 |
|---|---:|---:|---:|---:|
{rows}

合计14条记录、6游戏、12个物理组、3任务组；同物理状态多视图不独立。12条完整正例来自READY与OTHER_INSTANCE：类别型目标不能武断认定另一个合法同类实例为冲突。另有一对12步等长公开历史：一条MATCH，一条UNKNOWN。UNKNOWN不能仅根据短窗口赋值。

未构造/未决12条：
{reasons}

6条TARGET_CONFLICT在冻结公开访问范围内未发现可打开的异类目标，不能伪造错误投递。6条UNPROCESSED中，缺乏加工完成证据但开门仍可能是准备动作，不足以标记DECLINE；保持未决，未强改成UNKNOWN。

预先冻结每类至少4游戏/2严格场景作为诊断准入目标。MATCH达到游戏/场景目标，但集中在3任务组、单一任务/容器，不等于统计充分。DECLINE为0，UNKNOWN仅1游戏/1场景，且没有简单放置覆盖。**严格跨场景安全性无法评价，停止C2。** 不运行部分正例候选来绕过门槛，也不扩大池或降低标签要求。

## 5. 评分器冻结与只读历史回归

评分器直接复用resume_alfworld_a4_scoring.py，SHA：`{scorer['scorer_sha256']}`。未重新实现评分，未修改旧入口。无历史决定性动作时不给予对应见证，不因缺失直接判环境失败；一般状态变化仍为PROGRESS_UNVERIFIED；真实得分/获胜及有历史依据的任务相关动作可形成见证。UNKNOWN物理获胜不会改变标签，S0无门控不是UNKNOWN率0。

旧208份组别结果中，174份真实执行回执逐字段重算全部一致；34份门控拒绝没有环境分支，按原值保留。没有重跑旧候选或旧游戏。评分器及所有实际导入的项目依赖在采集前绑定代码SHA。旧11来源/21边界归档仍为11/11修复、边界无介入，候选身份相同；本轮没有再做实时Worker回归。由于C1不通过，实时保留否决、Worker镜像验证和四组执行预算不进入C2，不声称这些已重新完成。

## 6. 零API测试、资源和恢复

23项测试通过：本次16项、旧A4入口4项、旧采集器3项。包括旧回执重评分、缺失见证、合法变化不等于修复、UNKNOWN获胜不改标签、旧池曝光/预留排除、不同层不替代、重复窗口不增加游戏分母、未决不伪装UNKNOWN、未完成游戏阻断、不可变写入及四源码身份。测试输出在zero_api_tests.txt；手写夹具只作工程测试。

C1预算冻结：6游戏、54 reset、2700环境步、3600秒，公开搜索28步、最多4个目标实例、每分支50步；模型请求0、候选Worker调用0。实际{summary['resets']} reset、{summary['environment_steps']}环境步、{summary['elapsed_seconds']:.2f}秒；包括原始前缀和独立验证重放，API费用$0，本地硬件未定价。过去A3b学习费用约$0.121397另属历史支出。

完成后安全重入实际执行过，environment日志SHA未变、增加动作0。事件账本无未完成游戏，未完成步骤会阻断恢复。新采集没有运行时补丁；全部结果在同一预先冻结协议下产生。旧2412份工件没有变化。

C1采集协议文件SHA：`{A.sha(root/'collection/protocol.json')}`。这是**采集协议**，不是已获准的C2确认性执行协议。C2若准备完成才需另冻结18步剩余额度窗口、Worker镜像、逐臂成本和分层聚类分析版本；当前未生成可执行C2授权，未宣称READY。

## 7. 文件及结案

新增：scripts/run_alfworld_a4_confirmatory.py、collect_alfworld_a4_confirmatory.py、test_alfworld_a4_confirmatory.py、report_alfworld_a4_confirmatory.py。复用原环境、账本、参考采集、标签审核和评分器；没有新建Worker、Registry或技能系统。

私有工件：`{root}`。包含start_snapshot、exposure、candidate_metadata、四组SHA、scoring_regression、collection/protocol与selection、原始games及环境日志、review、C1_Readiness和Completion_Audit。完整标签/探针不放公开报告、不进入模型。

本轮按任务书结束在C1；C2不执行，无新的四组分数。以后不能把这6局继续称为“从未执行的新游戏”，也不能把宿主探针成功计为模型策略成功。没有自动启动A3c/A4b或路线B。
'''
    (report/'Route_A_A4_Confirmatory_Preparation.md').write_text(p)
    (report/'Route_A_A4_Confirmatory_Result.md').write_text('''# A4确认性评价执行状态

**C2_NOT_RUN / C1_BLOCKED_DATA_COVERAGE**。

6个新游戏的C1宿主采集得到13条MATCH、0条DECLINE、1条UNKNOWN；严格层缺乏可信负例和足够UNKNOWN，未满足冻结准入目标。没有运行任何四组新候选比较。候选正确率、误介入率、配对差异及置信区间均为NOT_EVALUABLE，不能填0或沿用旧A4成绩。

详见同目录准备报告。数据阻断不等于算法负结果。
''')
    (report/'Route_A_Final_Assessment.md').write_text('''# 路线A阶段结案判断

截至2026-11-15。本轮C1结束，C2未运行，没有独立确认性新成绩。

| 层次 | 已有证据 | 不能推出的结论 |
|---|---|---|
| 工程可执行性 | 真实模型门控通过Worker，既有A4完成208条组别记录 | 不等于适用性可靠 |
| 来源开发修复 | 冻结候选保留11/11曝光来源；A3b TRAIN47/47、开发38/38 | 不是独立泛化 |
| 多候选学习 | 4初稿及同父修订实际产生，冻结选择初稿candidate_0 | 未隔离额外采样/数据的因果收益 |
| 增强反馈 | R1部分增加修复机会，同时增加UNKNOWN介入 | 没有稳定优于R0的独立因果证据 |
| 跨游戏适用性 | 旧A4探索候选保留34/34正例，明确负例0/7，UNKNOWN介入2/11 | 不是本次确认性结果；样本非独立窗口 |
| 严格跨场景安全 | 旧严格层无可信负例；本轮新严格层仍无可信负例 | 不可评价，不能宣称0错误或泛化失败 |
| 人工Rule | 旧A4正例相同，Rule UNKNOWN介入0/11，候选2/11 | 未观察学习门控超越Rule |
| 完整在线收益 | 尚未完成新的原生FlowEvo配对整局评价 | 局部恢复不能推导整体成功率、费用收益 |

本轮独立采集的参考探针证明数据构造与标签可以运行，不是候选动作证据。全部候选继续Shadow，未发布。

进入路线B可沿用的能力基线：冻结S0恢复程序、S1/Rule/candidate_0门控、原生FlowEvo成功经验G、可靠Worker与恢复/费用账本、公开四字段输入和三值拒绝语义。路线B若启动，应是独立协议和新的数据分配；不能把本轮采集或旧A4再包装成未见确认集。

仍需回答：加工要求及公开完成证据是否被稳定保留；任务目标/实例语义能否在新任务中匹配；失败信息是否比任务信息或成功经验带来独立增量；收益发生在识别机会、执行修复还是额外计算；可靠局部行为能否提高强原生基线整体结果。当前不得声称失败数据优于Task-only、增强反馈有效、LearnAct-inspired优于官方LearnAct，或恢复了原系统无法解决的新任务。

按本轮边界结束，不为获得正向结果自动扩集、重新生成候选或启动路线B。
''')
    return dict(status=ready['status'],report=str(report/'Route_A_A4_Confirmatory_Preparation.md'),audit=audit)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();print(A.json.dumps(finish(a.output.resolve()),ensure_ascii=False))
