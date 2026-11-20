"""Read-only, version-bound independent-checkpoint audit; no execution."""
import argparse
from collections import Counter
from pathlib import Path
import run_alfworld_route_a_independent_confirmation as C

A=C.A; V=C.V


def analyze(root,out):
    C.verify(root);phase=root/'confirmation';p=A.read(phase/'protocol.json')
    result=A.read(phase/'result.json');ready=A.read(phase/'Readiness.json')
    data=A.read(phase/'checkpoints.private.json');freeze=A.read(phase/'Checkpoint_Freeze.json')
    if freeze['checkpoint_sha256']!=A.sha(phase/'checkpoints.private.json') or freeze['protocol_sha256']!=A.digest(p):
        raise PermissionError('checkpoint identity')
    V.P.verify_history(freeze['files'])
    samples={s['sample_id']:s for s in data['samples']};rows=result['rows']
    if {r['sample_id'] for r in rows}!=samples.keys() or len(rows)!=len(samples):raise PermissionError('incomplete or duplicate outcomes')
    commits={e['payload']['path']:e['payload']['sha256'] for e in V.P.EvidenceStore(phase/'outcomes.jsonl').records() if e['kind']=='OUTCOME_COMMITTED'}
    for r in rows:
        f=phase/'outcomes'/(A.digest(r['sample_id'])+'.json')
        if r['sample_sha256']!=A.digest(samples[r['sample_id']]) or A.sha(f)!=commits.get(str(f)) or A.read(f)!=r:
            raise PermissionError('outcome lineage')
    w=V.P.EvidenceStore(phase/'worker.jsonl').records()
    starts=[e['payload']['execution_id'] for e in w if e['kind']=='ENVIRONMENT_POLICY_STARTED']
    dones=[e['payload']['execution_id'] for e in w if e['kind']=='ENVIRONMENT_POLICY_EXECUTED']
    if sorted(starts)!=sorted(dones) or len(dones)!=len(set(dones)) or result['budget']['unknown_or_pending_requests']:
        raise PermissionError('pending or duplicate execution')
    V.P.EnvironmentReceipts(phase/'environment.jsonl',p['environment_steps'])
    selection=A.read(phase/'collection/selection.private.json')['tasks']
    collection=A.read(phase/'collection/collection_summary.json')
    stats={}
    for label in ('MATCH','DECLINE','UNKNOWN'):
        rs=[r for r in rows if r['label']==label]
        stats[label]=dict(records=len(rs),games=len({r['game'] for r in rs}),physical_groups=len({r['physical_group'] for r in rs}),
            gate=dict(Counter(r['decision']['status'] for r in rs)),interventions=sum(r['score']['actions']>0 for r in rs),
            completed_repairs=sum(r['score']['completed_repair'] for r in rs),won=sum(r['score']['won'] for r in rs),
            false_interventions=sum(r['score']['false_final_delivery_recovery'] for r in rs),
            unsupported_interventions=sum(r['score']['unsupported_recovery'] for r in rs),errors=sum(r['gate_error'] or r['score']['candidate_error'] for r in rs))
    types={};containers={}
    for name,field in ((types,'task_type'),(containers,'container')):
        for value in sorted({s[field] for s in data['samples']}):
            rs=[r for r in rows if r['label']=='MATCH' and r[field]==value]
            name[value]=dict(positive_records=len(rs),games=len({r['game'] for r in rs}),repairs=sum(r['score']['completed_repair'] for r in rs))
    unsafe=[dict(sample_id=r['sample_id'],game=r['game'],goal=samples[r['sample_id']]['candidate_context']['goal'],label=r['label'],
        decision=r['decision'],actions=[a['action'] for a in r['live']['actions']] if r['live'] else [],won=r['score']['won'])
        for r in rows if r['score']['false_final_delivery_recovery'] or r['score']['unsupported_recovery'] or r['score']['safety_unresolved']]
    games=[]
    for item in selection:
        t=item['task'];rs=[r for r in rows if r['game']==t['task_id']]
        games.append(dict(game=t['task_id'],task_type=t['task_type'],scene=t['scene'],container=t['group'].rsplit('-',2)[-2],
            records=len(rs),labels=dict(Counter(r['label'] for r in rs)),repairs=sum(r['score']['completed_repair'] for r in rs),
            unsafe=sum(r['score']['false_final_delivery_recovery'] or r['score']['unsupported_recovery'] for r in rs),
            status='EVALUATED' if rs else 'NO_TRUSTED_CHECKPOINT_NOT_CANDIDATE_FAILURE'))
    summary=dict(status='CONFIRMATION_PASSED_PENDING_ONLINE_ENGINEERING_AND_AUTHORIZATION' if ready['passed'] else 'CONFIRMATION_NO_GO',
        candidate_version=p['candidate_version'],candidate_sha256=p['candidates']['Route_A']['sha256'],recovery_sha256=p['candidates']['S0']['sha256'],
        protocol_sha256=A.digest(p),checkpoint_sha256=freeze['checkpoint_sha256'],selected_games=48,
        evaluated_games=len({r['game'] for r in rows}),physical_groups=len({r['physical_group'] for r in rows}),records=len(rows),
        per_label=stats,per_type=types,per_container=containers,readiness=ready,unsafe_cases=unsafe,games=games,
        exclusions=dict(Counter(x.get('exclusion',x.get('reason','UNVERIFIED')) for x in data['excluded'])),
        unresolved_modes=dict(Counter(x.get('mode','UNSPECIFIED') for x in data['excluded'] if x.get('status')=='UNVERIFIED')),
        cost=dict(new_model_calls=0,new_tokens=0,new_api_usd=0,worker_calls=len(dones),
            worker_seconds=sum(e['payload']['seconds'] for e in w if e['kind']=='ENVIRONMENT_POLICY_EXECUTED'),
            collection_environment_steps=collection['environment_steps'],evaluation_environment_steps=result['environment_steps'],collection_resets=collection['resets']),
        permission='SHADOW',published=False,online_executed=False,strict_unseen_scene_claim=False,
        feedback_to_model=False,all_selected_games_now_exposed=True)
    out.mkdir(parents=True,exist_ok=True);A.commit(out/'public_audit_summary.json',summary)
    lines=['# Route A：修订门控的48局独立检查点确认','',f"**状态：{summary['status']}。** 候选在新游戏执行前冻结，未根据结果修改、重采样或重新生成。本轮没有付费API，也没有G在线比较。",'',
        f"门控SHA：`{summary['candidate_sha256']}`；恢复SHA：`{summary['recovery_sha256']}`。协议：`{summary['protocol_sha256']}`；检查点：`{summary['checkpoint_sha256']}`。",'',
        '## 样本与来源','',f"原封存48个独立任务组全部按原序采集，{summary['evaluated_games']}个游戏形成{len(rows)}条可信记录、{summary['physical_groups']}个物理状态组。其他游戏没有可评分检查点，保留排除原因，不算候选失败。",'',
        '简单放置1局、清洗16局、加热16局、冷却15局，22场景。样本依据元数据平衡与SHA顺序冻结，不依据候选表现。与已知来源、B5、旧48局和在线60局按游戏/轨迹/任务组隔离；场景可已见，不能声称未见场景泛化。', '',
        '这是受控构造的真实失败检查点，非原生Agent自发失败。可信标签和参考回放在候选执行前冻结；参考探针、评分和未来轨迹不进入候选。UNKNOWN包含明示裁剪的真实历史，同状态的视图共享物理组。', '',
        '## 实际结果','', '| 标签 | 记录/游戏 | 门控输出 | 实际介入 | 完整正例修复 | 错误/无证据介入 |','|---|---|---|---:|---:|---:|']
    for label,s in stats.items():lines.append(f"| {label} | {s['records']}/{s['games']} | {s['gate']} | {s['interventions']} | {s['completed_repairs']} | {s['false_interventions']+s['unsupported_interventions']} |")
    lines+=['',f"全部入选正例均完整修复的游戏：{ready['fully_repaired_games']}/{ready['coverage']['match_games']}。存在错误/无证据恢复的控制游戏：{ready['unsafe_control_games']}/{ready['coverage']['control_games']}。接口/计算错误{ready['errors']}；未解决安全事件{ready['safety_unresolved']}。",'',
        '| 正例任务类型 | 完整修复/记录 | 游戏数 |','|---|---:|---:|']
    for t,s in types.items():lines.append(f"| {t} | {s['repairs']}/{s['positive_records']} | {s['games']} |")
    lines+=['','| 正例容器 | 完整修复/记录 | 游戏数 |','|---|---:|---:|']
    for t,s in containers.items():lines.append(f"| {t} | {s['repairs']}/{s['positive_records']} | {s['games']} |")
    lines+=['','## 冻结门槛与覆盖缺口','']
    for k in ('CAPABILITY_READY','SAFETY_READY','COVERAGE_READY','additional_coverage_ready'):lines.append(f"- {k}：{ready[k]}。")
    lines+=['',f"阶段冲突可信负例游戏：{ready['additional_coverage']['phase_conflict_games']}/至少3；实例冲突可信负例游戏：{ready['additional_coverage']['instance_conflict_games']}/至少3。",'',
        '原门槛保留：至少12正例游戏、12控制游戏，DECLINE/UNKNOWN各6游戏，正例覆盖6场景/3容器/3任务类型；至少80%正例游戏的全部检查点完整修复；零确认安全错误和运行错误。额外阶段/实例覆盖不能由旧工程夹具替代。', '',
        '未处理状态下打开可能只是准备动作；类别目标不能自动确定某一个实例。没有可审查证据的阶段/实例标签保持UNVERIFIED，不以不获胜、动作合法或采集mode名称强行标负。', '',
        f"未决记录mode统计：`{summary['unresolved_modes']}`。全部排除原因：`{summary['exclusions']}`。", '',
        f"在已观察到零控制错误时，按控制游戏计算的单侧95%二项上界为{ready['zero_error_one_sided95_upper']}；共享场景、多个视图和受控状态限制独立性，该数不是全面安全保证。",'',
        '## 异常与不可评价项','']
    if not unsafe:lines.append('本批可评价记录未观察到已定义的错误/无证据介入。不代表未覆盖的阶段、实例和任意表述均安全。')
    for u in unsafe:lines.append(f"- {u['sample_id']}：{u['label']}，{u['decision']['status']}，动作{u['actions']}，won={u['won']}。")
    lines+=['','## 资源与结论边界','',f"新增模型调用、Token及API费均0。Worker执行{len(dones)}次；采集/参考重放{collection['environment_steps']}步，候选评价{result['environment_steps']}步。历史模型学习成本保留，不能将整个技能获取成本记为零。",'',
        ('本批通过预定确认条件；仍需在线桥接验收、有限权限和独立付费授权，未自动运行60局。' if ready['passed'] else '本批未满足完整在线准入条件，维持NO-GO和Shadow；不能以局部成功绕过覆盖或安全缺口。'),'',
        '原封存60局保持未执行。本批48局现在全部属于曝光材料，不可修改候选后再次当作未见确认。不能以本轮局部恢复成绩证明整体FlowEvo在线正确率或成本增益。', '',
        '## 48局逐游戏清单摘要','', '| 游戏ID | 类型 | 场景 | 标签记录 | 完整修复 | 错误介入 |','|---|---|---:|---|---:|---:|']
    for g in games:lines.append(f"| {g['game']} | {g['task_type']} | {g['scene']} | {g['labels'] if g['records'] else 'NOT_EVALUABLE'} | {g['repairs']} | {g['unsafe']} |")
    report=out/'Route_A_Independent_Confirmation_Result.md';body='\n'.join(lines)+'\n'
    if report.exists() and report.read_text()!=body:raise PermissionError('immutable report changed')
    report.write_text(body)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--report-dir',type=Path,required=True)
    a=p.parse_args();print(analyze(a.output.resolve(),a.report_dir.resolve())['status'])
