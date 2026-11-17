"""Read-only scoring audit of the frozen B2 run; writes new derived artifacts."""
from collections import Counter,defaultdict
from pathlib import Path
import argparse,json
import run_alfworld_route_b_b2 as B
P=B.P

def analyze(out):
    p=P.read(out/'protocol.json');r=P.read(out/'result.json');P.verify_history(p['historical_sha256'])
    cases={c['id']:c for c in p['cases']};candidates={c['candidate_id']:c for c in p['candidates']}
    assert len(r['rows'])==len(cases)*len(candidates)
    workers={x['payload']['execution_id']:x['payload'] for x in P.EvidenceStore(out/'worker.jsonl').records() if x['kind']=='ENVIRONMENT_POLICY_EXECUTED'}
    summaries={};steps=[];branches=[]
    for name,candidate in candidates.items():
        selected=[x for x in r['rows'] if x['candidate']==name];m=Counter();mechanisms=defaultdict(Counter);stops=Counter();actions=Counter();execution_ids=set()
        for row in selected:
            case=cases[row['checkpoint']];path=out/'executions'/name/(row['checkpoint']+'.json')
            assert P.sha(path)==row['source_receipt_sha256']
            result=P.read(path);assert B.score(case,result)==row['score']
            s=row['score'];m['branches']+=1;stops[s['stop']]+=1
            m['intervened']+=bool(result['actions']);m['declined_without_action']+=s['declined'];m['candidate_error_branches']+=s['candidate_error']
            m['scoped_false_applicability']+=bool(s['scoped_false_applicability']);m['scoped_unsupported_action']+=bool(s['scoped_unsupported_action'])
            m['unverified_other_intervention']+=s['unrelated_action_intervention_unverified']
            if case['label']=='MATCH':
                m['native_cases']+=1;m['local_repair']+=bool(s['local_repair']);m['won']+=s['won']
                mechanisms[case['mechanism']]['cases']+=1;mechanisms[case['mechanism']]['repair']+=bool(s['local_repair']);mechanisms[case['mechanism']]['won']+=s['won']
            origin=case['origin'];anchor=origin['projected']['anchor'];current=origin['steps'][anchor-1];prefix=[]
            for i,d in enumerate(result['decisions'],1):
                execution_ids.add(d['execution_id']);w=workers[d['execution_id']]
                assert w['artifact_sha256']==candidate['file_sha256']
                chosen=d['selected_action'];legal=chosen in current['commands'] if chosen is not None else None
                m['decisions']+=1;m['worker_ok']+=d['worker_status']=='OK';m['selected_actions']+=chosen is not None;m['selected_legal']+=legal is True;m['selected_illegal']+=legal is False
                receipt=d['receipt'];m['executed_actions']+=receipt is not None
                if receipt is not None:
                    assert legal and receipt['action']==chosen
                    prefix.append(receipt);actions[chosen.split(' ')[0]]+=1;current=receipt
                partial=B.score(case,dict(actions=prefix,stop=result['stop']))
                steps.append(dict(candidate=name,checkpoint=case['id'],decision_index=i,source_step=anchor+len(prefix),
                    worker_status=d['worker_status'],worker_result=d['operator'],worker_error=d.get('candidate_error'),
                    selected_action=chosen,legal_at_selection=legal,executed=receipt is not None,not_executed_reason=d.get('not_executed_reason'),
                    environment_receipt=receipt,environment_effect=d.get('effect'),
                    verified_goal_progress=partial['goal_relevance'],local_repair_by_this_step=partial['local_repair'],won=partial['won'],
                    execution_id=d['execution_id'],context_sha256=d['context_sha256'],artifact_sha256=d['artifact_sha256'],
                    worker_cache_hit=d.get('worker_cache_hit','NOT_RECORDED_IN_SOURCE_RECEIPT'),worker_seconds=w['seconds']))
            branches.append(dict(row,first_action=result['actions'][0]['action'] if result['actions'] else None,
                actions=[a['action'] for a in result['actions']],reasons=[d['operator'].get('reason') for d in result['decisions']]))
        summaries[name]=dict(m,mechanisms=dict(mechanisms),stops=dict(stops),action_verbs=dict(actions),
            unique_worker_executions=len(execution_ids),worker_seconds=sum(workers[i]['seconds'] for i in execution_ids),
            full_common_source_pass=m['local_repair']==16 and not(m['scoped_false_applicability'] or m['scoped_unsupported_action'] or m['candidate_error_branches']))
    manifest=[]
    for c in p['cases']:
        o=c['origin'];a=o['projected']['anchor'];prefix,_,h=P.start_state(o,p)
        manifest.append(dict(checkpoint=c['id'],label=c['label'],mechanism=c['mechanism'],provenance=c['provenance'],
            game_sha256=o['row']['game_sha256'],physical_group=c['physical_group'],sequence=o['sequence'],
            goal=o['projected']['goal'],anchor_step=a,failed_action=prefix[-1]['action'],feedback=prefix[-1]['observation'],
            post_failure_public_state_sha256=h,visible_history_indices=c['ids'],remaining_budget=min(18,50-a),score_basis=c['score_basis']))
    summary=dict(status=r['status'],protocol_sha256=P.fingerprint(p),protocol_file_sha256=P.sha(out/'protocol.json'),
        candidates=summaries,denominators=dict(generation=dict(T=4,S=4,F=4),generated=dict(T=0,S=4,F=1),
        native_games=16,control_games=2,unique_games=len({c['origin']['row']['game_sha256'] for c in p['cases']}),
        branches=len(r['rows']),native_candidate_executions=80,independent_games=0),
        model_calls=0,model_tokens=0,model_cost_usd=0,budget=r['budget'],environment_steps=r['environment_steps'],
        unchanged_historical_files=len(p['historical_sha256']),permissions=r['permissions'],
        source_qualified_candidates=sum(x['full_common_source_pass'] for x in summaries.values()),
        independent_transfer_qualification='NONE_DEVELOPMENT_ONLY',excluded=Counter(x['reason'] for x in p['excluded']))
    dest=out/'analysis';P.commit(dest/'summary.json',summary);P.commit(dest/'checkpoint_manifest.private.json',manifest);P.commit(dest/'branches.private.json',branches)
    data=''.join(P.canonical(s)+'\n' for s in steps)
    path=dest/'steps.private.jsonl'
    if path.exists():assert path.read_text()==data
    else:path.write_text(data)
    return summary

def report(out,summary):
    p=P.read(out/'protocol.json');s=summary['candidates'];table=[];mechanisms=[];hashes=[];checkpoints=[]
    for name,x in s.items():
        table.append(f"| {name} | {x['local_repair']}/16 | {x['won']}/16 | {x['scoped_false_applicability']}/1 | {x['scoped_unsupported_action']}/1 | {x['declined_without_action']}/18 | {x['candidate_error_branches']}/18 | {x['executed_actions']} |")
        for family,v in x['mechanisms'].items():mechanisms.append(f"| {name} | {family} | {v['repair']}/{v['cases']} | {v['won']}/{v['cases']} |")
        c=next(c for c in p['candidates'] if c['candidate_id']==name)
        hashes.append(f"| {name} | `{c['file_sha256']}` |")
    for c in p['cases']:
        o=c['origin'];a=o['projected']['anchor']
        checkpoints.append(f"| {c['id']} | {c['label']} | {c['mechanism']} | {a} | `{o['steps'][a-1]['action']}` | {min(18,50-a)} |")
    raw=P.read(out/'result.json');env=summary['environment_steps'];total_actions=sum(x['executed_actions'] for x in s.values())
    worker=sum(x['unique_worker_executions'] for x in s.values());secs=sum(x['worker_seconds'] for x in s.values())
    winners=[(n,[r['checkpoint'] for r in raw['rows'] if r['candidate']==n and r['score']['won']]) for n in s]
    selected_legal=sum(x['selected_legal'] for x in s.values());selected=sum(x['selected_actions'] for x in s.values())
    txt=f'''# Route B B2：冻结候选统一开发评价

2026-11-16。状态：**COMPLETED_DEVELOPMENT_ONLY**。正式开发 Run：`{out.name}`。

本轮五份 B1 真实模型源码保持原样，在相同的 18 个已曝光检查点完成 90 个执行分支；新增模型请求、Token、API 费用及独立 Gate 游戏均为 0。完整共同来源验收通过候选 **{summary['source_qualified_candidates']}/5**，独立迁移资格 **0**。部分检查点成功不等于完整来源验收通过，也不等于独立迁移或在线收益。

## 1. 冻结与审计

- 协议 canonical SHA-256：`{summary['protocol_sha256']}`；文件字节 SHA-256：`{summary['protocol_file_sha256']}`。
- 每份 candidate.py 与原始供应商响应中的 code 逐字一致，绑定原版本、响应哈希、真实文件 SHA；没有格式修订、源码插桩、重采样或宿主补写算法。旧 B1 的 canonical 字符串指纹与 UTF-8 文件哈希分别保留，Worker 使用文件哈希。
- 开始和结束均验证 {summary['unchanged_historical_files']} 项冻结历史/输入/代码绑定。注册项显式标记 B2 的来源是评价证据，不冒充 B1 生成时的学习来源；原 B1 请求和响应仍是学习谱系。
- 复用 EnvironmentPolicyRunner、FrozenLinuxBackend、FailureOperatorRegistry、PersistentBudget 和来源重放接口；所有注册候选保持 Shadow，不调用发布 Gate、不运行完整在线 Agent、不改变 L1/L2/L3。
- Worker 继续使用原静态检查与 Linux 隔离：禁网、只读文件系统、禁止提权、资源与超时限制。实际执行读取冻结文件，逐步回执绑定该文件 SHA、上下文和 Worker 版本。

| 候选 | 原始文件 SHA-256 |
|---|---|
{chr(10).join(hashes)}

## 2. 共同检查点与分母

16 个自然发生的 L1 局部失败—恢复来源游戏：11 个容器、5 个台灯。所有调用均在真实 `Nothing happens.` 回执之后，历史前缀经 TextWorld 原样重放，公开目标、观察、合法动作和可见历史均来自原回执。

另从已曝光 A1d TRAIN 中按预定 sample_id 指纹顺序、标签及构造模式去重选择控制。上限为每标签 3 条，实际仅覆盖 1 个目标冲突 DECLINE 和 1 个 UNKNOWN。它们来自真实受控干预，不能称为 Agent 自发失败。UNKNOWN 的可见历史按旧冻结投影裁切，完整重放信息只供宿主核验。这两个控制均属容器机制，台灯不适用状态覆盖为0；台灯拒绝边界因此 NOT_EVALUABLE，不能用容器控制替代。

18 个检查点来自 18 个不同游戏/物理状态组，但均是开发曝光资料。五份候选在相同状态上执行形成 90 次观测，其中正例 80 次、控制 10 次；**不是 90 个独立游戏**。B1 的 T 四次弃权保留为零源码，不伪造 T 的执行失败率：执行分母为 0，NOT_EVALUABLE。

| 组 | B1 生成尝试 | 弃权 | 实际源码/静态通过 | B2 分支 |
|---|---:|---:|---:|---:|
| T | 4 | 4 | 0 | 0（不可评价） |
| S | 4 | 0 | 4 | 72 |
| F | 4 | 3 | 1 | 18 |

排除清单完整保存在 protocol.json：7 条整局失败缺少事前冻结的非终止局部失败锚点；18 条控制记录因已达到其标签/模式去重额度未选中。这些排除均先于候选执行，不能解释成被排除记录不是真实失败或没有价值。本轮无导航独立机制测试，不能外推到所有恢复类型。

| 检查点 | 标签 | 机制分层 | 失败步骤 | 原失败动作 | 候选最大步数 |
|---|---|---|---:|---|---:|
{chr(10).join(checkpoints)}

每个分支从全新环境重放相同前缀、候选 state={{}} 开始，窗口为 min(18, 50−前缀步数)，并保留原无进展停止规则。没有将前一候选状态留给后一候选。历史成功后缀仅用于私有评分，不进入候选上下文。

## 3. 分层评分与结果

静态通过只表示代码交付和权限合规。Worker 返回 OK、动作在当前合法列表、动作真正执行、目标相关、局部修复、官方 won 分别记录。一般观察变化、合法探索或模型自述均不能单独获得局部修复分数。

局部修复采用严格已有证据：达到历史获胜/得分动作之前的同一公开状态并使该动作可用，或环境实际 won。保留旧来源评分器的原始回执，但汇总采用 protocol 中事先冻结的严格评分，不采用较宽松的“某决定动作新变合法”推断。

控制标签原始作用域是 FAILED_FINAL_DELIVERY_ONLY_NOT_ALL_USEFUL_OPENING_ACTIONS。表中错误介入仅指执行原失败投递或打开其目标容器的**限定作用域介入**；其他动作不能依此标签一概判断错误，标记 NOT_EVALUABLE。UNKNOWN 标签只适用于初始公开证据，若后来出现新证据，作用域动作标记需另行审核，不能自动视为已确认错误。这里的控制计数不是一般恢复策略的完整误触发率，更不是负迁移率。

| 候选 | 局部修复 | 来源获胜 | DECLINE 作用域介入 | UNKNOWN 作用域介入 | 无动作拒绝 | 执行错误分支 | 实际动作 |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(table)}

| 候选 | 来源机制 | 局部修复 | 环境 won |
|---|---|---:|---:|
{chr(10).join(mechanisms)}

实际获胜检查点（未列出任何独立游戏）：`{json.dumps(winners,ensure_ascii=False)}`。

全体已选择动作中合法 {selected_legal}/{selected}；实际环境动作 {total_actions}。被停止规则拦截的动作选择不计作已执行。逐步文件记录 selected_action、legal_at_selection、executed、not_executed_reason、Worker 结果、环境反馈、目标证据、局部修复及 won，不把一次回执的多字段当作多个成功样本。

## 4. S/F 行为与错误归因边界

S 的源码主要是目标驱动的重新求解启发式，并不等同于专门的失败恢复技能。来源 trace 可见重新搜索、导航往返或持有物/阶段状态未正确衔接；例如 native_33 已持有 vase 3，部分候选仍进入找物品阶段，另一些在 safe 与其他地点间往返。这是实际行为证据；对内部原因的归因需结合源码，不能把推测当成已验证共同根因。

F2 的冻结代码不读取 goal，在无效/关闭反馈后优先 look，否则回到合法列表首项。native_33 中出现 look 与 examine drawer 4 交替。它展示了从失败现象生成可执行反应，但不足以证明学到了目标相关的恢复操作。

本轮实际正向证据集中于 S2：5/5 台灯来源完成导航并 use 获胜，11 个容器来源则全部失败。五份候选的全部实际动作中没有 open 或 move；S3 的294步全是 go，F2 的136步为55次 look、72次 examine、9次 cool。这些是执行记录中的动作分布，不是根据模型解释推断的修复。

两个控制上，五份候选均介入而未获胜，也没有任何无动作拒绝。虽然限定的失败投递/开目标容器计数为0，仍不能评价为安全拒绝成功：它们执行的是其他尚未证明相关或有益的动作。28个 ENVIRONMENT_TERMINAL 分支中仅5个 won，其余23个终止未获胜；34个达到恢复窗口上限，28个被无进展循环规则停止。没有候选 Python/接口错误。

源码中的固定实例假设、公开状态与内部阶段不同步、目标解析失败后的任意合法动作回退均保留为风险。本轮没有将这些语义问题改写为格式错误来修订模型。最终行为统计、停止原因和逐步回执见机器可读结果；不能仅因没有 Python 异常认定学习成功，也不能仅因局部失败否定所有失败学习方法。

S/F 只有 4 对 1 个已生成候选，生成信息量不同且同一来源集合高度曝光。本轮不做显著性或 F 优于 S 的主张；T 全弃权也不能证明失败信息独有价值。没有原生 G 同检查点的新配对执行，因此没有在线正确率提升、动作节省或负迁移的因果估计。原历史恢复后缀不是本轮同步 G 对照。

## 5. 预检、恢复与资源

先完成 18/18 检查点真实重放、实际 Linux Worker 冒烟与缓存验收，再执行候选。本轮 11 项专项/接口测试通过：原始哈希、无成功后缀评分、标签作用域、零模型与 Worker 预算、真实 TextWorld/Worker 中断后恢复、已提交分支重复进入不新增计量、Shadow 权限与未决 Worker 阻断等。

旧完整回归 25 项中 8 项通过、17 项在旧冻结身份检查时报错，完整日志保留，**不能宣称全部历史回归通过**。进一步只读定位发现：检查点、边界及 Worker 身份均一致；差异仅在旧协议的 code_sha256，涉及既有 success_baseline.py、autonomous_generation.py、recovery_acquisition.py 变更。诊断保存于 acceptance/historical_identity_diagnosis.json。本轮没有修改旧冻结期望；另用当前实际执行路径完成上述 11 项验收。

初次预检 Run `_01` 在候选执行前暴露 score_source 对没有成功后缀的控制状态抛出 StopIteration，候选执行为 0。最小修复仅将“无历史成功动作”保留为缺乏该项修复证据；随后新建 `_02`、重新冻结并预检。原 `_01` 未改成绩，B1 五份源码也未改。

冻结硬上限：模型请求/Token/API费用均为0；Worker调用 {p['worker_calls']}；环境步 {p['environment_steps']}（含重放及恢复余量）；总时限86400秒。实际候选独立 Worker 执行 {worker}，累计宿主测得 Worker 用时 {secs:.3f} 秒；另有预检工程夹具。完整账本：`{json.dumps(summary['budget'],ensure_ascii=False)}`。

环境步分项：`{json.dumps(env,ensure_ascii=False)}`，合计2938步。前缀重放、预检、候选动作和中断恢复分别计量，不能把重放步算作策略动作。账本约302.359秒使用后端计时；上述314.195秒为候选 Worker 宿主包装层计时，计时边界不同，不能相加。预检/单测日志另存。机器计算没有供应商费用账单，CPU/本机成本为 NOT_MONETIZED，而非声称计算免费。

既有 B1 学习成本不计为零：12 请求、383245 Token；按其冻结计价及缓存字段估算 $0.042818856，不计缓存保守估算 $0.1245144，均非供应商账单。本轮新增 API 费用为 $0，没有沿用授权补生成。

## 6. 资格与下一轮最小对照

本次完整共同来源通过规则是在执行前冻结的“16 个正例全部修复且没有限定控制违规或执行错误”；它比单个检查点成功严格，结果不能以挑选最好来源重新定义。通过数量为 {summary['source_qualified_candidates']}，所有候选仍为 Shadow。局部有效候选可以保留为后续研究对象，但控制覆盖仅2条、没有独立评价、没有完整在线比较，**本轮不授予任何独立迁移资格**。

下一轮先保留当前源码和逐机制正反证据；若要比较信息价值，应给 S/F 相同的明确恢复介入接口、模型资源与已曝光开发反馈机会，固定相同的状态恢复窗口，记录所有弃权和失败候选。避免将重新求解初始化失败与恢复知识缺失混为一谈。只有在开发适用范围与拒绝行为有足够证据后，另冻结未见检查点及原生 G 同状态对照；不得用本轮控制反复修到通过后再称独立证据。本轮不执行该下一阶段。

## 7. 文件与可重放材料

新增 `scripts/run_alfworld_route_b_b2.py`、`scripts/test_alfworld_route_b_b2.py`、`scripts/report_alfworld_route_b_b2.py`；共用来源评分器只增加无成功后缀的保守处理。未重写 Worker、注册表、预算系统或成功学习代码。本工作树其他既有改动不计作 B2 修改。

Run 目录含 protocol.json（包括全部排除原因、精确来源与版本绑定）、preflight/、regression_pass.json、executions/、scores/、Worker/环境/预算/Shadow日志和 result.json。派生 analysis/ 包含 summary.json、checkpoint_manifest.private.json、branches.private.json、steps.private.jsonl。完整轨迹与私有控制标签保留在受控本地 Run，公开报告只给摘要和哈希；未推送私有材料。

分析可重复执行：`PYTHONPATH=FlowEvo/src:scripts <冻结Python> scripts/report_alfworld_route_b_b2.py --output {out.relative_to(B.ROOT)}`。只读取冻结结果，不重跑环境或模型。恢复入口相同 run 命令会核验哈希、检查健康并跳过已提交分支；未决 Worker/环境状态仍阻断，不自动重发。
'''
    report_path=B.ROOT/'reports/alfworld_failure_skill_acquisition_20261109/Route_B_B2_Frozen_Candidate_Evaluation.md'
    report_path.write_text(txt)
    return report_path

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();summary=analyze(out)
    print(json.dumps(summary,ensure_ascii=False,indent=2));print(report(out,summary))
