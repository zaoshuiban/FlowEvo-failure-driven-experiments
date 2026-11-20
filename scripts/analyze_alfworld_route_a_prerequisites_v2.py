"""Read-only result audit. No policy execution, environment or model requests."""
import argparse
import ast
from collections import Counter
from pathlib import Path
import run_alfworld_route_a_prerequisites_v2 as R


def metrics(rows):
    out={}
    for label in ('MATCH','DECLINE','UNKNOWN'):
        xs=[r for r in rows if r['label']==label]
        out[label]=dict(records=len(xs),games=len({r['game'] for r in xs}),
            decisions=dict(Counter(r['decision']['status'] for r in xs)),
            full_repairs=sum(r['score']['completed_repair'] for r in xs),
            false_interventions=sum(r['score']['false_final_delivery_recovery'] for r in xs),
            unsupported_interventions=sum(r['score']['unsupported_recovery'] for r in xs),
            won=sum(r['score']['won'] for r in xs),
            errors=sum(r['gate_error'] or r['score']['candidate_error'] for r in xs))
    return out


def analyze(root,out):
    plan,_=R.verify(root/'development')
    generation=R.A.read(root/'generation/result.json')
    result=R.A.read(root/'development/result.json')
    readiness=R.A.read(root/'development/Readiness.json')
    forms=R.A.read(root/'engineering_forms/result.json')
    cost=R.A.read(root/'generation/Cost_Audit.json')
    old=R.A.read(R.N.OLD/'result.json')['rows'];rows=result['rows']
    if {r['sample_id'] for r in old}!={r['sample_id'] for r in rows}:
        raise PermissionError('different development denominators')
    for s in rows:
        before=next(x for x in old if x['sample_id']==s['sample_id'])
        if s['sample_sha256']!=before['sample_sha256']:raise PermissionError('changed old checkpoint')
    events=R.P.EvidenceStore(root/'generation/provider.jsonl').records()
    if sum(e['kind']=='SEND_STARTED' for e in events)!=1:raise PermissionError('request count')
    unsafe=[r for r in rows if r['score']['unsupported_recovery'] or r['score']['false_final_delivery_recovery']]
    summary=dict(status='DEVELOPMENT_NO_GO' if not readiness['passed'] or not forms['passed'] else 'DEVELOPMENT_PASSED_PENDING_INDEPENDENT',
        candidate_version=generation['candidate_version'],gate_sha256=generation['code_sha256'],
        parent_gate_sha256=generation['parent_sha256'],recovery_sha256=generation['recovery_sha256'],
        origin='REAL_MODEL_REVISION_NO_HOST_SOURCE_REPAIR',before=metrics(old),after=metrics(rows),
        development_readiness=readiness,engineering_cases=dict(total=forms['total'],passed=forms['pass_count'],
            failures=[r['case_id'] for r in forms['rows'] if not r['passed']],scope=forms['role']),
        paired=dict(same_gate_decisions=sum(a['decision']['status']==next(b['decision']['status'] for b in rows if b['sample_id']==a['sample_id']) for a in old),
                    corrected_unsafe=len([r for r in old if r['score']['unsupported_recovery'] and not next(b['score']['unsupported_recovery'] for b in rows if b['sample_id']==r['sample_id'])]),
                    lost_repairs=len(readiness['lost'])),cost=cost,
        independent_games_executed=0,online_games_executed=0,published=False,
        warning='Controlled, exposed development checkpoints and synthetic engineering cases are separate; not online benefit or independent transfer.')
    if not readiness['passed'] or not forms['passed']:
        if (root/'confirmation/collection/collection.jsonl').exists():raise PermissionError('independent games despite veto')
        R.A.commit(root/'Independent_And_Online_NO_GO.json',dict(status='STOP_AFTER_ONE_REVISION_DEVELOPMENT_VETO',
            candidate_version=generation['candidate_version'],development_passed=readiness['passed'],
            engineering_passed=forms['passed'],confirmation_games_reserved=48,online_games_reserved=60,
            new_game_executions=0,online_executed=False,remaining_model_calls=0,automatic_revision=False,
            reason='Frozen development safety condition not met; keep source and all receipts, no independent exposure.'))
    R.A.commit(out/'public_audit_summary.json',summary)
    new=summary['after'];prev=summary['before']
    source=Path(plan['candidates']['Route_A']['path']).read_text()
    funcs={n.name:ast.unparse(n) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
    body=f'''# Route A V2：一次真实门控修订与开发验证

**结果：{summary['status']}。** 真实模型交付完整源码并通过静态检查，但未修复已知的形容词处理前提遗漏。完成全部61条曝光开发回归及30条工程词形/实例检查；按预定否决条件停止，新的48局和在线60局均未执行。

## 一次请求及产物来源

- 用户授权：最多1次门控修订，上限$1，不包含在线实验。
- 冻结协议：`{R.A.digest(R.N.verify_preparation(root))}`；实际wire与冻结一致。
- 模型：DeepSeek Flash，thinking disabled，temperature0，输出上限4096；供应商 finish_reason=`stop`。完整JSON及源码均由模型返回，无宿主策略补写、无第二次请求。
- 父门控SHA：`{generation['parent_sha256']}`。
- 新门控SHA：`{generation['code_sha256']}`。
- 新候选版本：`{generation['candidate_version']}`。
- 恢复源码保持：`{generation['recovery_sha256']}`。
- 新门控及恢复程序仅以Shadow执行；未发布或授予在线权限。

## 相同61条开发记录的配对结果

| 项目 | 旧门控 | 新门控 |
|---|---:|---:|
| 支持状态完整修复 | {prev['MATCH']['full_repairs']}/{prev['MATCH']['records']} | {new['MATCH']['full_repairs']}/{new['MATCH']['records']} |
| 明确不适用状态错误介入 | {prev['DECLINE']['false_interventions']}/{prev['DECLINE']['records']} | {new['DECLINE']['false_interventions']}/{new['DECLINE']['records']} |
| 证据不足状态无证据介入 | {prev['UNKNOWN']['unsupported_interventions']}/{prev['UNKNOWN']['records']} | {new['UNKNOWN']['unsupported_interventions']}/{new['UNKNOWN']['records']} |
| 接口/执行错误 | {sum(r['errors'] for r in prev.values())} | {sum(r['errors'] for r in new.values())} |

61条记录并非61个独立游戏；本轮完全继承旧检查点、标签、物理状态和评分依据。新旧门控判断相同的记录为{summary['paired']['same_gate_decisions']}/61；已知无证据介入修复{summary['paired']['corrected_unsafe']}条，旧正确修复退化{summary['paired']['lost_repairs']}条。正例游戏级指标仍需与记录级分开读取。

## 工程词形与实例检查

在读取新源码之前，另行冻结30条工程检查，覆盖简单放置、hot/heated、cold/cool/cooled、clean/cleaned、处理证据缺失、不同物体处理及显式目标实例冲突。它们来自曝光公开上下文的显式工程改写；没有冒充真实新游戏、独立负例或原生Agent自发失败。其数据未进入本轮模型请求。

通过{forms['pass_count']}/{forms['total']}。失败项：{', '.join(summary['engineering_cases']['failures'])}。

这些检查只使用Linux Worker读取上下文，没有环境动作。缺失证据或冲突允许DECLINE/UNKNOWN，但ERROR一律不通过。未修改模型源码使测试通过。

## 为什么没修好

模型在交付说明中声称包括形容词处理要求；实际源码仍先移除物体短语修饰，再用完整动词检查处理要求：

```python
{funcs['_processing_required']}
```

这会使 `hot`、`cold` 等描述不能产生对应的处理前提。`clean`、`cool` 因恰好与动作动词相同而表现不同。问题属于**模型修订未落实到可执行逻辑**，不是JSON截断、Worker拒绝或网络错误。不能把“描述说已修复”视为功能修复。

旧的三条无证据介入在新版本中仍出现；相关分支后来实际获胜。这证明的是公开前提门控未满足，而不是已经观察到整局损害。真实在线发生率、与原生FlowEvo相比的胜负和负迁移仍未测量。

## 成本与资源

- 真实模型调用1次；输入{cost['usage']['prompt_tokens']:,}、输出{cost['usage']['completion_tokens']:,}、总计{cost['usage']['total_tokens']:,} Token。
- 其中cache hit {cost['usage']['prompt_cache_hit_tokens']}、cache miss {cost['usage']['prompt_cache_miss_tokens']}。
- 按调用时段和供应商公开单价估算API费用 **${cost['usage_based_estimate_usd']:.8f}**，未核对账单；与预算账本中的保守扣占 **${cost['ledger_charge_or_reserve_usd']:.6f}** 分开报告，不能把预留当作实际消费。[DeepSeek计价依据](https://api-docs.deepseek.com/quick_start/pricing/)
- 开发环境步数：{result['environment_steps']}（包括前缀重放和候选动作）。工程词形测试环境步数0。完整Worker与预算记录保存在受控Run目录。
- 旧算法获取费用不抹除，本段只统计本轮增量开销。

## 停止与下一阶段边界

本轮已用完1次请求机会，虽然远未用完$1金额，也不会补采样或增加修订。候选源码、原始响应、反馈和所有失败结果保留。

新的48局只完成元数据冻结，没有构造或执行检查点，仍保持本轮未曝光。原封存60局清单保持原哈希，没有运行G或G＋Route A。由于开发安全失败，不进入独立确认，也不存在在线实验GO。

后续若另行研究修订方法，应首先检查模型是否真的改变了目标前提谓词，再进行有界开发验证；不得人工补好门控后继续把它记为本次模型学习成果。阶段与实例冲突的可信独立标签覆盖仍是后续确认阶段的单独问题。
'''
    report=out/'Route_A_V2_Revision_Result.md'
    if report.exists() and report.read_text()!=body:raise PermissionError('immutable report differs')
    report.write_text(body)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--report-dir',type=Path,required=True)
    args=parser.parse_args();args.report_dir.mkdir(parents=True,exist_ok=True)
    print(analyze(args.output.resolve(),args.report_dir.resolve())['status'])
