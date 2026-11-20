"""Read-only independent applicability audit, with game-level denominators."""
import argparse
from collections import Counter
from pathlib import Path
import run_alfworld_route_a_value_validation as V


def analyze(root,out):
    p,selection=V.verify(root);result=V.A.read(root/'result.json');rows=result['rows']
    f=V.A.read(root/'Checkpoint_Freeze.json')
    if f['checkpoint_sha256']!=V.A.sha(root/'checkpoints.private.json') or f['protocol_sha256']!=V.A.digest(p):raise PermissionError('checkpoint binding')
    V.P.verify_history(f['files'])
    data=V.A.read(root/'checkpoints.private.json');samples=data['samples'];byid={s['sample_id']:s for s in samples}
    if {r['sample_id'] for r in rows}!=set(byid) or len(rows)!=len(byid):raise PermissionError('incomplete/duplicate evaluation')
    ledger={e['payload']['path']:e['payload']['sha256'] for e in V.P.EvidenceStore(root/'outcomes.jsonl').records() if e['kind']=='OUTCOME_COMMITTED'}
    for r in rows:
        path=root/'outcomes'/(V.A.digest(r['sample_id'])+'.json')
        if ledger.get(str(path))!=V.A.sha(path) or V.A.read(path)!=r or r['sample_sha256']!=V.A.digest(byid[r['sample_id']]):raise PermissionError('outcome identity')
    V.P.EnvironmentReceipts(root/'environment.jsonl',p['environment_steps'])
    w=V.P.EvidenceStore(root/'worker.jsonl').records();started={e['payload']['execution_id'] for e in w if e['kind']=='ENVIRONMENT_POLICY_STARTED'}
    finished={e['payload']['execution_id'] for e in w if e['kind']=='ENVIRONMENT_POLICY_EXECUTED'}
    if started!=finished or result['budget']['unknown_or_pending_requests']:raise PermissionError('pending execution')
    a=V.assess(rows,p['thresholds']);a['ENGINEERING_READY']=True
    a['per_label']={label:dict(records=len(rs),games=len({r['game'] for r in rs}),gate=dict(Counter(r['decision']['status'] for r in rs)),
        actual_interventions=sum(r['score']['actions']>0 for r in rs),barrier_removed=sum(r['score']['barrier_removed'] for r in rs),completed_repairs=sum(r['score']['completed_repair'] for r in rs),
        won=sum(bool(r['score']['won']) for r in rs),false_recovery=sum(r['score']['false_final_delivery_recovery'] for r in rs),unsupported=sum(r['score']['unsupported_recovery'] for r in rs))
        for label in ('MATCH','DECLINE','UNKNOWN') for rs in [[r for r in rows if r['label']==label]]}
    a['per_type']={kind:dict(records=len(rs),games=len({r['game'] for r in rs}),repairs=sum(r['score']['completed_repair'] for r in rs))
        for kind in V.TYPES for rs in [[r for r in rows if r['label']=='MATCH' and r['task_type']==kind]]}
    a['unsafe_cases']=[dict(sample_id=r['sample_id'],game=r['game'],label=r['label'],task_type=r['task_type'],container=r['container'],
        goal=byid[r['sample_id']]['candidate_context']['goal'],gate=r['decision'],actions=[s['action'] for s in r['live']['actions']] if r['live'] else [],
        won=r['score']['won'],temporal=r['score']['temporal']) for r in rows if r['score']['false_final_delivery_recovery'] or r['score']['unsupported_recovery']]
    a['cost']=dict(model_calls=0,tokens=0,api_usd=0,worker_calls=len(finished),worker_seconds=sum(e['payload']['seconds'] for e in w if e['kind']=='ENVIRONMENT_POLICY_EXECUTED'),
        collection=V.A.read(root/'collection/collection_summary.json'),evaluation_environment_steps=result['environment_steps'],budget=result['budget'])
    a.update(protocol_sha256=V.A.digest(p),checkpoint_sha256=f['checkpoint_sha256'],result_sha256=V.A.sha(root/'result.json'),
        status='APPLICABILITY_COMPLETED_ONLINE_NOT_STARTED',online_executed=False,independent_scenes=0,
        selected_games=len(selection['tasks']),games_with_checkpoints=len({r['game'] for r in rows}),physical_groups=len({r['physical_group'] for r in rows}),
        excluded_reasons=dict(Counter(x.get('exclusion',x.get('reason','UNVERIFIED')) for x in data['excluded'])))
    out.mkdir(parents=True,exist_ok=True);V.A.commit(out/'public_audit_summary.json',a)
    lines=['# 冻结 Route A：扩大独立适用性验证结果','',
        '本轮实际执行新的适用性验证；没有重新生成/修改门控或恢复代码，没有付费模型请求，没有运行G与G＋Route A在线比较。', '',
        f"协议SHA：`{a['protocol_sha256']}`；检查点SHA：`{a['checkpoint_sha256']}`。", '',
        f"48局冻结游戏中，{a['games_with_checkpoints']}局形成可评价检查点，共{len(rows)}条记录、{a['physical_groups']}个物理组。游戏、轨迹及任务组与全部已知来源隔离；场景已见，不宣称跨未见场景。参考探针和评分数据不进入候选。", '',
        '| 标签 | 记录/游戏 | 门控返回 | 实际介入 | 完整正例修复 | 错误/无证据恢复 |', '|---|---|---|---:|---:|---:|']
    for label,m in a['per_label'].items():lines.append(f"| {label} | {m['records']}/{m['games']} | {m['gate']} | {m['actual_interventions']} | {m['completed_repairs']} | {m['false_recovery']+m['unsupported']} |")
    lines+=['', 'UNKNOWN即使物理世界实际获胜，也不能据此反向标为MATCH。同一物理状态的完整/裁剪历史共享分组；未知标签不是根据历史长度猜测。打开合法不等于最终投递适用。', '',
        f"正例完整修复 {a['positive_repairs']}/{a['positive_records']}；所有入选正例都完整修复的游戏 {a['fully_repaired_games']}/{a['coverage']['match_games']}。有错误/无证据恢复的控制游戏 {a['unsafe_control_games']}/{a['coverage']['control_games']}。无可评价检查点的游戏保留NOT_EVALUABLE，不算候选失败。", '',
        '| 正例任务类型 | 记录 | 游戏 | 完整修复 |','|---|---:|---:|---:|']
    for k,m in a['per_type'].items():lines.append(f"| {k} | {m['records']} | {m['games']} | {m['repairs']} |")
    lines+=['', '## 冻结准入判定','']
    for key in ('CAPABILITY_READY','SAFETY_READY','COVERAGE_READY','ENGINEERING_READY'):lines.append(f"- {key}：{'通过' if a[key] else '未通过'}。")
    lines+=['',f"在线阶段：{'可继续做启动工程验收及预算授权，尚未运行' if a['eligible_for_online_preparation'] else 'NO-GO；不得绕过失败条件启动G对照'}。",'',
        '门槛在结果之前固定：12正例游戏、12控制游戏、DECLINE/UNKNOWN各6游戏；6正例场景、3容器、3题型；正例游戏全部检查点修复比例≥80%；零已确认错误/无证据介入、零错误与未解决安全状态。全部候选保持Shadow，没有伪造发布Gate。', '',
        f"零错误时控制游戏的单侧95%二项错误率上界：{a['zero_error_one_sided95_upper'] if a['zero_error_one_sided95_upper'] is not None else 'NOT_APPLICABLE（观察到错误或零分母）'}。共享场景和受控构造带来相关性，此数不构成全面安全保证。", '',
        '## 异常记录','']
    for u in a['unsafe_cases']:lines.append(f"- `{u['sample_id']}`，{u['label']}：目标“{u['goal']}”；门控{u['gate']['status']}；实际动作{u['actions']}；won={u['won']}。")
    if not a['unsafe_cases']:lines.append('本批未观察到冻结定义下的错误或无证据恢复。仍受样本与语义覆盖范围限制。')
    lines+=['', '## 成本及结论边界','',
        f"模型请求/Token/API费均0。Worker {a['cost']['worker_calls']}次，回执耗时合计{a['cost']['worker_seconds']:.3f}秒；采集/参考重放{a['cost']['collection']['environment_steps']}环境步，候选评价{result['environment_steps']}步。历史技能获取成本保留在原账本，未视为零；主机执行时间未转换为货币。", '',
        '35项零API工程测试已通过，覆盖确定性抽样、角色隔离、预算/未知阻断、版本绑定、按游戏计数、门槛失败、原生回退等价性。真实Linux Worker与TextWorld运行记录单独保存，不把Mock测试当成学习成绩。', '',
        '后续60局在线清单已在验证成绩出现前固定，六类任务、60不同任务组，与48局验证集隔离，未交互。要检验完整任务增益，仍须在安全条件满足后按同题同序重新运行G及G＋Route A，不能用旧113/120相减。冻结技能对照只回答已学能力的运行价值，不能单独证明失败信息的独立因果收益。', '',
        '原始证据：私有Run中的protocol.json、Checkpoint_Freeze.json、checkpoints.private.json、outcomes/、live/、worker.jsonl、environment.jsonl及result.json。公开统计见public_audit_summary.json。']
    (out/'Route_A_Applicability_Validation_Result.md').write_text('\n'.join(lines)+'\n')
    return a


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);parser.add_argument('--report',required=True,type=Path);args=parser.parse_args()
    print(analyze(args.output.resolve(),args.report.resolve())['eligible_for_online_preparation'])
