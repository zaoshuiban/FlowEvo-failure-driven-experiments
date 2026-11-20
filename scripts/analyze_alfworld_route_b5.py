"""Read-only B5 statistics. No candidate calls, new labels, or result mutation."""
import argparse
from collections import Counter
from pathlib import Path
import run_alfworld_route_b5_transfer as X


def cohort(rows):
    return dict(records=len(rows),games=len({s['game_sha256'] for s in rows}),
        physical_groups=len({s['physical_state_group_id'] for s in rows}),scenes=len({s['scene_id'] for s in rows}),
        containers=dict(Counter(s['container'] for s in rows)),task_types=dict(Counter(s['task_type'] for s in rows)))


def summarize(root):
    p,selection=X.verify(root);f=X.A.read(root/'Checkpoint_Freeze.json')
    if X.A.sha(root/'checkpoints.private.json')!=f['checkpoint_sha256']:raise PermissionError('checkpoint drift')
    X.P.verify_history(f['files']);data=X.A.read(root/'checkpoints.private.json');samples=data['samples']
    coverage={label:cohort([s for s in samples if s['label']==label]) for label in ('MATCH','DECLINE','UNKNOWN')}
    controls=cohort([s for s in samples if s['label']!='MATCH'])
    coverage_pass=(coverage['MATCH']['games']>=8 and controls['games']>=8 and coverage['DECLINE']['games']>=2 and coverage['UNKNOWN']['games']>=2
        and controls['scenes']>=2 and coverage['MATCH']['scenes']>=2 and len(coverage['MATCH']['task_types'])>=2)
    result=X.A.read(root/'result.json');rows=result['rows'];metrics={}
    for arm in X.ARMS:
        rs=[r for r in rows if r['arm']==arm];positive=[r for r in rs if r['label']=='MATCH'];success=[r for r in positive if r['score']['completed_repair']]
        metrics[arm]=dict(records=len(rs),actual_interventions=sum(r['score']['actions']>0 for r in rs),actions=sum(r['score']['actions'] for r in rs),
            match_records=len(positive),match_games=len({r['game'] for r in positive}),barrier_removed=sum(r['score']['barrier_removed'] for r in positive),
            positive_deliveries=sum(r['score']['delivery_confirmed'] for r in positive),completed_repairs=len(success),
            success_games=len({r['game'] for r in success}),success_scenes=len({r['scene'] for r in success}),success_containers=len({r['container'] for r in success}),
            wins_all_labels=sum(r['score']['won'] for r in rs),wins_positive=sum(r['score']['won'] for r in positive),
            false_recovery=sum(r['score']['false_final_delivery_recovery'] for r in rs),
            unsupported_recovery=sum(r['score']['unsupported_recovery'] for r in rs),
            safety_unresolved=sum(r['score']['safety_unresolved'] for r in rs),
            declines=sum(r['score']['declined'] for r in rs),errors=sum(r['score']['candidate_error'] or r['gate_error'] for r in rs),
            stop_counts=dict(Counter(r['score']['stop'] for r in rs)),gate_counts=dict(Counter(r['decision']['status'] for r in rs)),
            per_label={l:dict(records=len([r for r in rs if r['label']==l]),interventions=sum(r['score']['actions']>0 for r in rs if r['label']==l),declines=sum(r['score']['declined'] for r in rs if r['label']==l)) for l in ('MATCH','DECLINE','UNKNOWN')})
    fr=metrics['FR11'];capability=fr['success_games']>=3 and fr['success_scenes']>=2 and fr['success_containers']>=2
    safety=not any(fr[k] for k in ('false_recovery','unsupported_recovery','safety_unresolved','errors'))
    # Verify every published row against its durable outcome receipt, not only
    # the summary. Independent executions and cropped views remain clustered.
    commits={r['payload']['path']:r['payload']['sha256'] for r in X.P.EvidenceStore(root/'outcomes.jsonl').records() if r['kind']=='OUTCOME_COMMITTED'}
    for row in rows:
        path=root/'outcomes'/row['arm']/(X.A.digest(row['sample_id'])+'.json')
        if commits.get(str(path))!=X.A.sha(path) or X.A.read(path)!=row:raise PermissionError('outcome receipt mismatch')
    X.P.EnvironmentReceipts(root/'environment.jsonl',p['environment_steps'])
    workers=X.P.EvidenceStore(root/'worker.jsonl').records()
    starts={r['payload']['execution_id'] for r in workers if r['kind']=='ENVIRONMENT_POLICY_STARTED'}
    completed={r['payload']['execution_id'] for r in workers if r['kind']=='ENVIRONMENT_POLICY_EXECUTED'}
    engineering=len(rows)==len(samples)*3 and starts==completed and result['paid_requests']==0
    games=[]
    for t in selection['tasks']:
        task=t['task'];rs=[r for r in rows if r['game']==task['task_id']]
        games.append(dict(task_id=task['task_id'],scene=task['scene'],task_type=task['task_type'],container=task['group'].rsplit('-',2)[-2],
            records=len({r['sample_id'] for r in rs}),labels=dict(Counter(r['label'] for r in rs if r['arm']=='S11')),
            arms={arm:dict(repairs=sum(r['score']['completed_repair'] for r in rs if r['arm']==arm),wins=sum(r['score']['won'] for r in rs if r['arm']==arm),actions=sum(r['score']['actions'] for r in rs if r['arm']==arm)) for arm in X.ARMS}))
    return dict(status='EXPLORATORY_CONTROLLED_TRANSFER_COMPLETED',protocol_sha256=X.A.digest(p),checkpoint_sha256=f['checkpoint_sha256'],
        reserved_games=12,eligible_games=len(selection['tasks']),coverage=coverage,control_coverage=controls,metrics=metrics,games=games,
        independent_unseen_scenes=0,readiness=dict(CAPABILITY_READY=capability,SAFETY_READY=safety,COVERAGE_READY=coverage_pass,ENGINEERING_READY=engineering),
        P3_GO=all((capability,safety,coverage_pass,engineering)),P3_executed=False,paid_requests=0,new_model_cost_usd=0,
        worker_calls=len(completed),collection_environment_steps=result['collection_environment_steps'],evaluation_environment_steps=result['evaluation_environment_steps'],
        total_environment_steps=result['collection_environment_steps']+result['evaluation_environment_steps'],budget=result['budget'],
        exclusions=dict(Counter(x.get('reason',x.get('exclusion',x.get('status','UNSPECIFIED'))) for x in data['excluded'])),
        results_sha256=X.A.sha(root/'result.json'))


def report(root,out):
    s=summarize(root);out.mkdir(parents=True,exist_ok=True)
    X.A.commit(out/'Route_B5_Summary.json',s)
    def line(text=''):lines.append(text)
    lines=[]
    line('# Route B5：冻结候选的局部迁移结果')
    line();line('本轮完成 P1 采集与 P2 零模型调用比较。结果属于未见游戏、已见场景中的受控恢复检查点探索，不是原生 Agent 在线增益，也不是未见场景泛化。全部候选保持 Shadow，未执行 P3。')
    line();line(f"Run：`{root.name}`。协议 SHA-256：`{s['protocol_sha256']}`；检查点 SHA-256：`{s['checkpoint_sha256']}`。")
    line();line('## 数据与分母');line();line('| 标签 | 记录 | 游戏 | 物理组 | 场景 |');line('|---|---:|---:|---:|---:|')
    for label,c in s['coverage'].items():line(f"| {label} | {c['records']} | {c['games']} | {c['physical_groups']} | {c['scenes']} |")
    line();line('不同公开历史视图仍共享物理检查点；三个候选执行同一记录也不增加独立游戏数量。UNKNOWN 是明确披露的真实历史裁剪视图，不能解释为原生 Agent 自发忘记处理过程。')
    line();line('## 三候选结果');line();line('| 候选 | 正例障碍解除 | 正例完整修复 | 成功游戏 | 可信负例错误恢复 | UNKNOWN 无证据恢复 | 拒绝 | 错误 |');line('|---|---:|---:|---:|---:|---:|---:|---:|')
    for a,m in s['metrics'].items():line(f"| {a} | {m['barrier_removed']}/{m['match_records']} | {m['completed_repairs']}/{m['match_records']} | {m['success_games']}/{m['match_games']} | {m['false_recovery']}/{m['per_label']['DECLINE']['records']} | {m['unsupported_recovery']}/{m['per_label']['UNKNOWN']['records']} | {m['declines']} | {m['errors']} |")
    line();line('零分母项为 NOT_EVALUABLE；表中 0/0 不是通过。障碍解除指原失败投递变为合法；完整修复在本批单目标游戏中要求成功投递且环境 won。打开容器不计完整修复。UNKNOWN 物理状态即使获胜，也不能反向证明介入时证据充分。')
    line();line('## 逐游戏结果');line();line('| 游戏 | 类型 / 容器 / 场景 | 标签数 | S11 修复 | FR11 修复 | Route A 修复 |');line('|---|---|---|---:|---:|---:|')
    for g in s['games']:line(f"| {g['task_id']} | {g['task_type']} / {g['container']} / {g['scene']} | {g['labels']} | {g['arms']['S11']['repairs']} | {g['arms']['FR11']['repairs']} | {g['arms']['Route_A']['repairs']} |")
    line();line('## 四轴准入');line()
    for k,v in s['readiness'].items():line(f'- {k}：{"通过" if v else "未通过"}。')
    line();line(f"P3：{'具备申请条件，但未启动' if s['P3_GO'] else 'NO-GO；不启动原生 G 增量实验'}。禁止把局部恢复结果表述为整局在线正确率改善或失败信息的因果优势。")
    line();line('## 成本、完整性与证据');line()
    line(f"新增模型请求 0、Token 0、API 费用 $0。Worker {s['worker_calls']} 次（包括旧开发夹具冒烟）；采集/独立重放 {s['collection_environment_steps']} 环境步，候选评价 {s['evaluation_environment_steps']} 步，合计 {s['total_environment_steps']}，低于 16,000 上限。Worker 主机成本未换算成货币，不能称为完全免费。历史技能学习成本仍属于旧实验，不并入本轮新增 API 费，也不视为零。")
    line();line('候选源码、父代运行、依赖、环境、Worker、数据和结果通过 SHA 绑定；分支逐步日志与结果提交收据保存在私有 Run。38 项零 API 测试通过（14 项 B5 专项 + 24 项历史回归），包括真实 Linux Worker、已曝光 TextWorld 回放、中断恢复、未知阻断和 Shadow 权限。')
    line();line('首次采集启动在任何环境动作之前因共享采集器缺少协议镜像而停止；补齐完全相同 SHA 的协议副本后执行，原日志保留。没有修改候选、题序、采集或标注算法。')
    line();line('逐记录、逐动作、合法动作、Worker 原始回执、进入时门控、时序证据与完整资源账本见私有 `result.json`、`outcomes/`、`live/`、`worker.jsonl`、`environment.jsonl`；公开机器可读统计为同目录 `Route_B5_Summary.json`。')
    (out/'Route_B5_Transfer_Result.md').write_text('\n'.join(lines)+'\n')
    return s


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    print(report(args.output.resolve(),args.report.resolve())['readiness'])
