"""Read-only ALFWorld baseline report; raw responses stay in controlled storage."""
import argparse
from collections import Counter,defaultdict
from decimal import Decimal
import json
from pathlib import Path

from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read,save


def analyze(root,output):
    cfg=read(root/'protocol.json')
    episodes=[r['payload'] for r in EvidenceStore(root/'episodes.jsonl').records() if r['kind']=='EPISODE_LOCKED']
    transport=EvidenceStore(root/'requests.jsonl').records()
    raw=[r['payload']['response'] for r in transport if r['kind']=='RAW_RESPONSE']
    inputs=sum(r.get('usage',{}).get('prompt_tokens',0) for r in raw)
    outputs=sum(r.get('usage',{}).get('completion_tokens',0) for r in raw)
    groups=defaultdict(list)
    for e in episodes:
        groups[e['task_type']].append(e)
    tokens=dict(input=inputs,output=outputs,total=inputs+outputs)
    peak=(Decimal(inputs)*Decimal('0.30')+Decimal(outputs)*Decimal('1.20'))/1000000
    offpeak=peak/2
    rows=[]
    for e in episodes:
        # Only classify publicly delivered action lines; never infer failure root cause.
        rows.append(dict(task_id=e['task_id'],task_type=e['task_type'],status=e['status'],
                         steps=e['trace']['total_steps'],model_calls=e['trace']['llm_call_count']))
    metrics=dict(scope='REAL_ALFWORLD_PURE_DYNAMIC_PILOT',protocol_sha256=fingerprint(cfg),
                 scheduled=len(cfg['tasks']),completed=len(episodes),success=sum(e['status']=='SUCCESS' for e in episodes),
                 statuses=dict(Counter(e['status'] for e in episodes)),model_responses=len(raw),tokens=tokens,
                 peak_uncached_estimate_usd=str(peak),offpeak_uncached_estimate_usd=str(offpeak),
                 unknown_events=sum(r['kind']=='SEND_UNKNOWN' for r in transport),
                 per_type={k:dict(completed=len(v),successes=sum(e['status']=='SUCCESS' for e in v))
                           for k,v in groups.items()},rows=rows)
    output.mkdir(parents=True,exist_ok=True)
    save(output/'public_audit_summary.json',metrics)
    table='\n'.join('| {task_id} | {task_type} | {status} | {steps} | {model_calls} |'.format(**r) for r in rows)
    report=f"""# ALFWorld 首轮真实基线报告

状态 {'COMPLETED' if len(episodes)==len(cfg['tasks']) else 'PARTIAL'}。已完成 {len(episodes)}/{len(cfg['tasks'])}，成功 {metrics['success']} 题。成功率以官方 won 信号计算。未完成任务保留缺失状态。

本轮采用 FlowEvo 现有 ALFWorld pure_dynamic 动作生成与执行链，官方文本环境 0.4.2、TextWorld 1.7.0，valid_unseen，冻结 {len(cfg['tasks'])} 题，种子 {cfg['seed']}，每题单次尝试、最多 50 步。冻结协议摘要为 `{fingerprint(cfg)}`。

真实响应 {len(raw)} 次，输入 {inputs:,}、输出 {outputs:,}、合计 {inputs+outputs:,} Token。按官方未缓存价格计算，峰时估算上界 {peak} 美元、非峰时估算上界 {offpeak} 美元；缓存折扣和供应商账单以实际账户记录为准。未知发送事件 {metrics['unknown_events']} 次。 [DeepSeek 官方价格](https://api-docs.deepseek.com/quick_start/pricing/)

| 任务 | 类型 | 结果 | 步数 | 模型调用 |
| --- | --- | --- | --- | --- |
{table}

本轮使用环境的合法动作提示，保留仓库原有人工通用任务说明和动作解析回退。环境步数耗尽、动作循环及无进展与请求异常分开记录。每个模型请求只包含公开观察和动作历史，参考轨迹与 expert plan 不进入提示。

本轮没有学习、编译或复用算子。现有 ALFWorld 编译器含人工任务蓝图，并从成功轨迹生成模板；因此本轮成绩只用于描述原生工作流表现。后续失败驱动比较需接入真实失败证据、自动能力来源与独立验证，再冻结新的对照协议。本轮任务均属于已曝光的开发评测材料。
"""
    (output/'ALFWorld_Baseline_Report.md').write_text(report)
    print(json.dumps({k:v for k,v in metrics.items() if k not in ('rows',)},ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    analyze(args.run,args.output)
