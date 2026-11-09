"""Read-only audit of a frozen ALFWorld learning Run, including every model phase."""
import argparse
from collections import Counter,defaultdict
from decimal import Decimal
import json
import math
from pathlib import Path

from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read,save
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.run_health import trusted_usage


def analyze(prepared,output,*,allow_partial=False):
    plan=read(prepared/'learning_protocol.json')
    root=prepared/'run'
    events=EvidenceStore(root/'stream.jsonl').records()
    pairs=[r['payload'] for r in events if r['kind']=='FUTURE_PAIRED_DONE']
    expected=[r['task_id'] for r in plan['future_tasks']]
    if [p['task_id'] for p in pairs]!=expected[:len(pairs)]:
        raise PermissionError('paired outcomes differ from frozen sequence')
    if not allow_partial and len(pairs)!=len(expected):
        raise PermissionError('Run incomplete; explicitly request a partial audit')
    registry=EvidenceStore(root/'registry.jsonl').records()
    source=EvidenceStore(root/'failures.jsonl').records()
    budgets=[]
    budget_paths=[root/'action_budget.jsonl',root/'worker_budget.jsonl',*root.glob('jobs/*/budget.jsonl')]
    for path in budget_paths:
        rows=EvidenceStore(path).records()
        state,_=PersistentBudget._state(rows)
        b=PersistentBudget.__new__(PersistentBudget)
        total=b._totals(rows)
        budgets.append(dict(path=str(path.relative_to(root)),totals=total,
                            unresolved=[k for k,r in state.items() if r['status'] not in ('settled','not_sent')]))
    model_phases=defaultdict(lambda:dict(responses=0,input_tokens=0,output_tokens=0,cache_hit=0,cache_miss=0))
    raw_ids=[]
    missing_usage=0
    unknown=0
    paths=[*root.glob('clients/*/requests.jsonl'),*root.glob('jobs/*/provider.jsonl')]
    for path in paths:
        phase=path.parent.name if path.parent.parent.name=='clients' else 'learning-'+path.parent.name
        for record in EvidenceStore(path).records():
            unknown+=record['kind']=='SEND_UNKNOWN'
            if record['kind']!='RAW_RESPONSE':
                continue
            raw=record['payload']['response']
            raw_ids.append(raw.get('id'))
            usage=trusted_usage(raw)
            if not usage:
                missing_usage+=1
                continue
            row=model_phases[phase]
            row['responses']+=1
            row['input_tokens']+=usage['input_tokens']
            row['output_tokens']+=usage['output_tokens']
            row['cache_hit']+=raw['usage'].get('prompt_cache_hit_tokens',0)
            row['cache_miss']+=raw['usage'].get('prompt_cache_miss_tokens',usage['input_tokens'])
    duplicate_ids=len(raw_ids)-len(set(raw_ids))
    if duplicate_ids:
        raise PermissionError('duplicate provider response IDs')
    for row in model_phases.values():
        row['offpeak_cache_aware_estimate_usd']=str((Decimal(row['cache_hit'])*Decimal('.003')
            +Decimal(row['cache_miss'])*Decimal('.15')+Decimal(row['output_tokens'])*Decimal('.6'))/1000000)
    successes={arm:sum(p[arm]['trace']['success'] for p in pairs) for arm in ('G','F')}
    f_only=sum(p['gain'] for p in pairs)
    g_only=sum(p['regression'] for p in pairs)
    discordant=f_only+g_only
    mcnemar=min(1.0,2*sum(math.comb(discordant,k) for k in range(min(f_only,g_only)+1))/2**discordant) if discordant else 1.0
    learning=[]
    for start_event in (r for r in events if r['kind']=='LEARNING_STARTED'):
        start=start_event['payload']
        slot=start['slot']
        path=root/'jobs'/str(slot)/'hypothesis.json'
        hypothesis=read(path) if path.exists() else {}
        end=next((r['payload'] for r in events if r['kind']=='LEARNING_DONE' and r['payload']['slot']==slot),None)
        result=end['result'] if end else {'status':'INCOMPLETE'}
        validation=result.get('validation',{})
        card=result.get('card',{})
        learning.append(dict(slot=slot,after_sequence=start['after_sequence'],
            evidence_ids=start['evidence_ids'],decision=hypothesis.get('decision','NOT_ACCEPTED'),
            category=hypothesis.get('operator_category','UNKNOWN'),
            result=dict(status=result['status'],artifact_sha256=card.get('artifact_sha256'),
                        candidate_version=card.get('version'),
                        validation_status=validation.get('status'),
                        source_won=validation.get('source_won'),
                        source_generic_won=validation.get('source_generic_won'))))
    total=dict(input_tokens=sum(x['input_tokens'] for x in model_phases.values()),
               output_tokens=sum(x['output_tokens'] for x in model_phases.values()),
               cache_hit=sum(x['cache_hit'] for x in model_phases.values()),
               cache_miss=sum(x['cache_miss'] for x in model_phases.values()))
    source_validations=[]
    for path in sorted(root.glob('jobs/*/environment_validation/source_traces.private.json')):
        traces=read(path)
        source_validations.append(dict(slot=int(path.parents[1].name),
            **{arm: {k:traces[arm][k] for k in ('success','llm_call_count','direct_use_count','direct_failure_count')}
               for arm in ('G','F')}))
    worker_total=next(b['totals'] for b in budgets if b['path']=='worker_budget.jsonl')
    off=(Decimal(total['cache_hit'])*Decimal('.003')+Decimal(total['cache_miss'])*Decimal('.15')
         +Decimal(total['output_tokens'])*Decimal('.6'))/1000000
    by_type={}
    types={r['task_id']:r['task_type'] for r in plan['future_tasks']}
    for kind in sorted(set(types.values())):
        selected=[p for p in pairs if types[p['task_id']]==kind]
        by_type[kind]=dict(tasks=len(selected),G_success=sum(p['G']['trace']['success'] for p in selected),
                          F_success=sum(p['F']['trace']['success'] for p in selected),
                          F_only=sum(p['gain'] for p in selected),G_only=sum(p['regression'] for p in selected))
    metrics=dict(scope='REAL_ALFWORLD_LEARNING_DEVELOPMENT_PILOT',scheduled=len(expected),paired_completed=len(pairs),
        G_success=successes['G'],F_success=successes['F'],F_only=f_only,G_only=g_only,mcnemar_exact_p=mcnemar,
        registered=sum(r['kind']=='SHADOW_REGISTERED' for r in registry),
        authorized=sum(r['kind']=='EXPERIMENT_AUTHORIZED' for r in registry),
        suspended=sum(r['kind']=='OPERATOR_SUSPENDED' for r in registry),
        actual_future_operator_actions=sum(p['F']['trace']['direct_use_count'] for p in pairs),
        actual_future_intervened_tasks=sum(bool(p['F']['trace']['direct_use_count']) for p in pairs),
        learning_jobs=learning,model_phases=dict(model_phases),tokens=total,model_responses=len(raw_ids),
        source_validations=source_validations,worker_calls=worker_total['tools'],worker_elapsed_ms=worker_total['tool_ms'],
        offpeak_cache_aware_estimate_usd=str(off),peak_cache_aware_estimate_usd=str(off*2),
        conservative_budget_occupied_usd=str(Decimal(sum(b['totals']['cost'] for b in budgets))/1000000),
        unknown_events=unknown,unmetered_responses=missing_usage,duplicate_provider_ids=duplicate_ids,
        unresolved_requests=sum(len(b['unresolved']) for b in budgets),
        trusted_failure_facts=sum(r['kind']=='FAILURE_FACT' for r in source),
        per_type=by_type,protocol_sha256=fingerprint(plan),
        results=[dict(task_id=p['task_id'],task_type=types[p['task_id']],G=p['G']['status'],F=p['F']['status'],
                      G_calls=p['G']['trace']['llm_call_count'],F_calls=p['F']['trace']['llm_call_count'],
                      operator_actions=p['F']['trace']['direct_use_count']) for p in pairs])
    output.mkdir(parents=True,exist_ok=True)
    save(output/'public_audit_summary.json',metrics)
    table='\n'.join(f"| {kind} | {r['tasks']} | {r['G_success']} | {r['F_success']} | {r['F_only']} | {r['G_only']} |"
                    for kind,r in by_type.items())
    status='COMPLETED' if len(pairs)==len(expected) else 'PARTIAL'
    report=f"""# ALFWorld 真实失败学习 {len(expected)} 题 Pilot 报告

状态 {status}。已完成 {len(pairs)}/{len(expected)} 对，G 成功 {successes['G']}，F 成功 {successes['F']}。F 独有成功 {f_only}，G 独有成功 {g_only}。精确配对检验 p={mcnemar}，小规模开发实验仅作描述性解读。

本轮读取历史 20 条完整失败，并执行真实模型归纳。学习作业 {len(learning)} 个，注册 {metrics['registered']} 个候选，通过 Gate 授权 {metrics['authorized']} 个，后续实际策略动作 {metrics['actual_future_operator_actions']} 次。F/G 差异只有在确有介入并有配对证据时才可能支持工具收益，零介入的差异不能归因为学习。

| 类型 | 配对题数 | G 成功 | F 成功 | F 独有 | G 独有 |
| --- | --- | --- | --- | --- | --- |
{table}

真实模型响应 {len(raw_ids)} 次，输入 {total['input_tokens']:,}、输出 {total['output_tokens']:,} Token，包含归纳、生成、来源与 Gate 验证及后续任务。按本轮冻结报价和缓存用量计算，非峰时估算 {off} 美元，峰时估算 {off*2} 美元。供应商实际账单尚未取得。预算占用 {metrics['conservative_budget_occupied_usd']} 美元，含保守预留；总硬上限 {plan["max_cost_microusd"]/1000000:g} 美元。 [官方计价](https://api-docs.deepseek.com/quick_start/pricing/)

UNKNOWN {unknown}，无法计量响应 {missing_usage}，未决请求 {metrics['unresolved_requests']}，重复供应商响应 ID {duplicate_ids}。全部原始请求、响应、代码及 Worker 记录保存在受控本地目录。

这 {len(expected)} 题来自官方 train，按六类均衡分层冻结，排除历史和工程演练中的相同内容游戏。G/F 同题、单次尝试、最多 50 步、输出上限同为 1024 Token。历史来源 256 Token 失败与本轮配置不同，来源阶段另有同为 1024 的原生对照。Gate 来自 valid_seen，本轮属于开发性跨游戏实验，尚不能声称严格新场景泛化或失败信息相对 Task-Only 的独立贡献。
"""
    (output/'ALFWorld_Learning_Final_Report.md').write_text(report)
    print(json.dumps({k:metrics[k] for k in ('scheduled','paired_completed','G_success','F_success','registered',
          'authorized','actual_future_operator_actions','model_responses','offpeak_cache_aware_estimate_usd')},indent=2))
    return metrics


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--allow-partial',action='store_true')
    args=parser.parse_args()
    analyze(args.run,args.output,allow_partial=args.allow_partial)
