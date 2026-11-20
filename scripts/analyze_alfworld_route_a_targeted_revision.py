"""Read-only summary for the bounded targeted revision; no policy calls."""
import argparse
from collections import Counter
from pathlib import Path
import run_alfworld_route_a_targeted_revision as V


def analyze(root,out):
    plan=V.verify(root)
    with V.adapter():V.R.verify(root/'development')
    accepted=V.A.read(root/'Semantic_Acceptance.json')
    V.P.verify_history(accepted['receipts'])
    gen=V.A.read(root/'generation/result.json');dev=V.A.read(root/'development/result.json')
    ready=V.A.read(root/'development/Readiness.json');forms=V.A.read(root/'engineering_forms/result.json')
    old=V.A.read(V.PARENT/'development/result.json');cost=V.A.read(root/'generation/Cost_Audit.json')
    parent={r['sample_id']:r for r in old['rows']};new={r['sample_id']:r for r in dev['rows']}
    if parent.keys()!=new.keys():raise PermissionError('different development inputs')
    for key,r in new.items():
        if r['sample_sha256']!=parent[key]['sample_sha256']:raise PermissionError('checkpoint changed')
    def count(rows):
        result={}
        for label in ('MATCH','DECLINE','UNKNOWN'):
            xs=[r for r in rows if r['label']==label]
            result[label]=dict(records=len(xs),games=len({r['game'] for r in xs}),
                decisions=dict(Counter(r['decision']['status'] for r in xs)),
                repairs=sum(r['score']['completed_repair'] for r in xs),
                unsafe=sum(r['score']['unsupported_recovery'] or r['score']['false_final_delivery_recovery'] for r in xs),
                errors=sum(r['gate_error'] or r['score']['candidate_error'] for r in xs))
        return result
    by_type={}
    for typ in V.N.V.TYPES:
        xs=[r for r in new.values() if r['task_type']==typ and r['label']=='MATCH']
        by_type[typ]=dict(records=len(xs),repairs=sum(r['score']['completed_repair'] for r in xs),games=len({r['game'] for r in xs}))
    summary=dict(status=accepted['status'],candidate_version=gen['candidate_version'],gate_sha256=gen['code_sha256'],
        parent_sha256=gen['parent_sha256'],recovery_sha256=gen['recovery_sha256'],before=count(parent.values()),after=count(new.values()),
        positive_types=by_type,engineering=dict(total=forms['total'],passed=forms['pass_count'],failures=[r['case_id'] for r in forms['rows'] if not r['passed']]),
        changed_functions=V.A.read(root/'Function_Diff_Audit.json')['changed_functions'],
        corrected_unsafe=sum(r['score']['unsupported_recovery'] and not new[key]['score']['unsupported_recovery'] for key,r in parent.items()),
        lost_repairs=ready['lost'],cost=cost,environment_steps=dev['environment_steps'],
        paid_requests=1,new_independent_games_executed=0,online_games_executed=0,published=False,
        interpretation='Targeted supervised functional repair on exposed data; not independent transfer or proof of native FlowEvo benefit.')
    V.A.commit(out/'public_audit_summary.json',summary)
    yes=accepted['passed'];pos=summary['after']['MATCH'];neg=summary['after']['DECLINE'];unk=summary['after']['UNKNOWN']
    table='\n'.join('| '+typ+' | '+str(v['repairs'])+'/'+str(v['records'])+' | '+str(v['games'])+' |' for typ,v in by_type.items())
    body=f'''# Route A：针对性前提修订与开发验收

**状态：{accepted['status']}。** {'本次已修复曝光开发数据中的处理前提遗漏，保留原正确恢复能力。' if yes else '本次仍有执行验收未通过，不能宣称修复。'} 新48局与在线60局未启动。

## 实际改动

新门控由一次真实DeepSeek请求完整生成。宿主只提供上一版本源码、函数级问题诊断和7条曝光真实公开状态（3条已确认缺陷＋四种类型各1条正例），未代写策略或替模型补丁。30条工程检查、独立游戏、Rule及私有参考路线均未进入请求。

AST只读比较显示修改的函数为 `{', '.join(summary['changed_functions'])}`。模型增加处理形容词到动作前提的映射：hot/heated→heat，cold/cool/cooled→cool，clean/cleaned→clean。门控随后沿用同实例处理回执检查。原容器恢复源码完全不变。

门控SHA：`{gen['code_sha256']}`；父SHA：`{gen['parent_sha256']}`；恢复SHA：`{gen['recovery_sha256']}`。新候选版本：`{gen['candidate_version']}`。完整原始回复、源码与diff保存在受控运行目录，原实验不覆盖。

## 真实开发回归

采用原冻结的61条检查点，逐条在相同公开视图、前缀状态、窗口、Worker和评分规则下执行。

| 指标 | 上一修订 | 本次修订 |
|---|---:|---:|
| 正例完整修复 | {summary['before']['MATCH']['repairs']}/34 | {pos['repairs']}/{pos['records']} |
| 明确负例错误介入 | {summary['before']['DECLINE']['unsafe']}/9 | {neg['unsafe']}/{neg['records']} |
| 证据不足状态错误介入 | {summary['before']['UNKNOWN']['unsafe']}/18 | {unk['unsafe']}/{unk['records']} |
| 旧正确修复退化 | — | {len(ready['lost'])} |

正例来自{pos['games']}个游戏；61条记录不是61个独立游戏。三条已知问题修复{summary['corrected_unsafe']}/3。UNKNOWN判断分布为 `{unk['decisions']}`；这些是拒绝无证据介入，不是将所有任务拒绝。

| 正例类型 | 完整修复/检查点 | 游戏数 |
|---|---:|---:|
{table}

任务整体胜负只在完整实际分支中记录；本报告不是原生FlowEvo完整在线对照，也不把处理后的局部状态获胜等同于在线增益。

## 工程语义检查

{forms['pass_count']}/{forms['total']}通过。检查包括简单放置、7种处理词形、有同实例处理证据、无处理证据、仅其他物体处理证据和明确目标实例冲突。正例要求MATCH；其他情况要求DECLINE或UNKNOWN；ERROR失败。

这些是显式工程变体，来自曝光上下文，**不是30个未见游戏**。没有新环境动作，没有将合成标签冒充可信自然负例。验收现在要求真实开发回归与工程检查同时通过，并绑定同一个候选版本；其中任一失败都会阻断。

## 调用与成本

真实请求1次，模型deepseek-flash，thinking disabled，temperature0，完整响应finish_reason=stop。输入{cost['usage']['prompt_tokens']:,}、输出{cost['usage']['completion_tokens']:,}、总{cost['usage']['total_tokens']:,} Token；预算上限$1。

按原始usage与调用时段估算 **${cost['usage_based_estimate_usd']:.8f}**；账本保守扣占 **${cost['ledger_charge_or_reserve_usd']:.6f}**，两者不得混淆，实际供应商账单未核验。[供应商价格](https://api-docs.deepseek.com/quick_start/pricing/)

开发环境步数{dev['environment_steps']}，包含前缀重放及恢复动作；工程词形检查环境步数0。历史技能获取与之前失败修订的费用仍保留，本段只计本轮增量。

零API回归共58项：57项通过，1项独立旧Worker测试未启用；本轮真实候选随后已通过实际Linux Worker、TextWorld开发执行及工程语义检查。没有用Mock作为真实候选成绩。

## 结论与保留边界

{'已观察到要求的开发修复：安全拒绝缺失处理证据，同时保留简单放置与已处理正例。' if yes else '仍不能确认要求的开发修复。'} 本次输入含明确函数级诊断，因此属于有监督的针对性反馈修订；不能用单次成功宣称失败学习方法普遍有效，或优于Task-only/Success-only。

该门控仍使用有限语法和字符串解析，未证明任意任务表述、所有阶段与实例冲突都能可靠判断。新48局尚未交互，原60局在线清单保持不变，候选仍为Shadow。独立验证覆盖、尤其阶段/实例冲突的可信标签仍需单独验收；本结果不授予发布、在线权限或新的付费预算。
'''
    f=out/'Route_A_Targeted_Repair_Result.md'
    if f.exists() and f.read_text()!=body:raise PermissionError('immutable report')
    f.write_text(body)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--report-dir',type=Path,required=True)
    args=parser.parse_args();args.report_dir.mkdir(parents=True,exist_ok=True)
    print(analyze(args.output.resolve(),args.report_dir.resolve())['status'])
