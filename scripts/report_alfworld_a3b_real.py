"""Read-only real A3b outcome analysis. Never sends calls or changes frozen artifacts."""
import argparse,json
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from failure_evo.contracts import canonical,fingerprint
from failure_evo.math_stream import read,sha
from alfworld_.applicability_paired_metrics import analyze
import run_alfworld_applicability_a3b as S
from audit_alfworld_a3b import archived_hashes


def events(path):return [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.exists() else []

def analyze_real(root,out):
    result=read(root/'result.json')
    if result['paid_requests']==0:raise ValueError('real responses required')
    plan,roles=S.preflight(root);assert result['protocol_sha256']==fingerprint(plan)
    assert archived_hashes()==plan['historical_sha256']
    rows=events(root/'provider.jsonl');responses=[r for r in rows if r['kind']=='RAW_RESPONSE']
    fee=[]
    for e in responses:
        raw=e['payload']['response'];u=raw.get('usage',{});i=u.get('prompt_tokens');o=u.get('completion_tokens')
        cached=u.get('prompt_cache_hit_tokens',u.get('prompt_tokens_details',{}).get('cached_tokens',0));miss=u.get('prompt_cache_miss_tokens',i-cached if i is not None else None)
        dt=datetime.fromtimestamp(e['at'],timezone.utc)
        # Exact weekend rule; otherwise show peak/no-holiday uncertainty rather than guessing holidays.
        weekend=dt.weekday()>=5
        peak=(cached*.006+miss*.3+o*1.2)/1e6 if None not in (cached,miss,o) else None
        fee.append(dict(request_key=e['payload']['key'],model=raw.get('model'),id=raw.get('id'),at=dt.isoformat(),usage=u,
            finish_reasons=[c.get('finish_reason') for c in raw.get('choices',[])],peak_estimate_usd=peak,
            applicable_estimate_usd=peak*.5 if weekend and peak is not None else None,
            basis='published weekend off-peak rate, not supplier invoice' if weekend else 'exact tariff unconfirmed; report peak bound'))
    usage=dict(input_tokens=sum(r['usage'].get('prompt_tokens',0) for r in fee),output_tokens=sum(r['usage'].get('completion_tokens',0) for r in fee),
        total_tokens=sum(r['usage'].get('total_tokens',0) for r in fee),cache_hit_tokens=sum(r['usage'].get('prompt_cache_hit_tokens',0) for r in fee))
    metric=analyze(result);byv={a['version']:a for a in result['attempts']};paired=[];wire_audit=[]
    for parent in result['attempts'][:4]:
        pair={a['branch']:a for a in result['attempts'] if a.get('parent_version')==parent['version']}
        if set(pair)!={'R0','R1'}:paired.append(dict(candidate=parent['candidate_id'],status='NOT_EVALUABLE'));continue
        feedback=read(root/parent['candidate_id']/'paired_feedback.private.json');r0,r1=feedback['R0'],feedback['R1']
        assert {k:r1[k] for k in r0}==r0
        wires={b:read(root/parent['candidate_id']/b/'request.private.json')['wire'] for b in ('R0','R1')}
        settings={b:{k:v for k,v in w.items() if k!='messages'} for b,w in wires.items()}
        assert settings['R0']==settings['R1']
        assert wires['R0']['messages'][0]==wires['R1']['messages'][0]
        wire_audit.append(dict(candidate=parent['candidate_id'],same_parent=True,same_train_feedback=True,selected_ids_sha256=feedback['sample_ids_sha256'],
            actual_request_settings=settings['R0'],same_system_prompt=True,
            feedback_bytes={b:len(canonical(feedback[b]).encode()) for b in ('R0','R1')}))
        for role in ('train','validation'):
            rr={b:{r['sample_id']:r for r in a.get(role,[])} for b,a in pair.items()}
            if not rr['R0'] or set(rr['R0'])!=set(rr['R1']):paired.append(dict(candidate=parent['candidate_id'],role=role,status='NOT_EVALUABLE'));continue
            changes=[]
            for sid,x in rr['R0'].items():
                y=rr['R1'][sid];assert x['expected']==y['expected']
                changes.append(dict(sample_id=sid,game_sha256=x['game_sha256'],expected=x['expected'],R0=x['actual'],R1=y['actual'],
                    R0_recovery_verified=x.get('recovery_verified'),R1_recovery_verified=y.get('recovery_verified')))
            positives=[x for x in changes if x['expected']=='MATCH']
            paired.append(dict(candidate=parent['candidate_id'],role=role,status='PAIRED',records=len(changes),games=len({r['game_sha256'] for r in changes}),
                R0_only_repair=sum(x['R0_recovery_verified'] is True and x['R1_recovery_verified'] is not True for x in positives),
                R1_only_repair=sum(x['R1_recovery_verified'] is True and x['R0_recovery_verified'] is not True for x in positives),
                both_repair=sum(x['R1_recovery_verified'] is True and x['R0_recovery_verified'] is True for x in positives),rows=changes))
    outcomes=[]
    for a in result['attempts']:
        wrong=[r for r in a.get('train',[])+a.get('validation',[]) if r['actual']!=r['expected']]
        outcomes.append(dict(candidate=a['candidate_id'],branch=a['branch'],version=a['version'],status=a['status'],
            error_reasons=dict(Counter(r['reason'] for r in wrong)),source_sha256=a.get('code_sha256'),
            source_changed_vs_parent=bool(a.get('parent_version') and a.get('code_sha256')!=byv[a['parent_version']].get('code_sha256'))))
    worker=events(root/'worker.jsonl');env=events(root/'environment.jsonl');registry=events(root/'registry.jsonl')
    resource=dict(worker_started=sum(e['kind']=='ENVIRONMENT_POLICY_STARTED' for e in worker),worker_executed=sum(e['kind']=='ENVIRONMENT_POLICY_EXECUTED' for e in worker),
        worker_seconds=sum(e['payload'].get('seconds',0) for e in worker if e['kind']=='ENVIRONMENT_POLICY_EXECUTED'),
        environment_steps=sum(e['kind']=='STEP_OBSERVED' for e in env),source_commits=sum(e['kind']=='SOURCE_COMMITTED' for e in env))
    data=dict(status=result['status'],protocol_sha256=fingerprint(plan),metrics=metric,paired_verified_recovery=paired,wire_audit=wire_audit,
        outcomes=outcomes,usage=usage,fees=fee,fee_estimate_usd=sum(e['applicable_estimate_usd'] for e in fee) if all(e['applicable_estimate_usd'] is not None for e in fee) else None,
        peak_fee_estimate_usd=sum(e['peak_estimate_usd'] for e in fee) if all(e['peak_estimate_usd'] is not None for e in fee) else None,
        resources=resource,selection=result['selection'],historical_unchanged=True,S0_sha256=sha(S.B.CODE),A4='NOT_RUN',
        source_result_sha256=sha(root/'result.json'),registry_event_types=dict(Counter(e['kind'] for e in registry)))
    out.mkdir(parents=True,exist_ok=True);S.B.pilot.commit(out/'A3b_Real_Results.private.json',data)
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    d=analyze_real(a.run.resolve(),a.output.resolve());print(canonical({k:d[k] for k in ('status','usage','fee_estimate_usd','resources','selection')}))


def public_report(data,root,path):
    """Descriptive report; no change to selection or paid-run artifacts."""
    versions=data['metrics']['versions'];table=[]
    for a in versions:
        t,v=a['train'],a['validation']
        table.append('| '+a['candidate']+' | '+a['status']+' | '+f"{t['source_repairs_verified']}/47"+' | '+f"{v['source_repairs_verified']}/38"+' | '+f"{t['false_match']['numerator']}/7 · {v['false_match']['numerator']}/4"+' | '+f"{t['unsupported_match']['numerator']}/13 · {v['unsupported_match']['numerator']}/10"+' |')
    pairlines=[]
    for p in data['paired_verified_recovery']:
        if p['status']!='PAIRED':pairlines.append(f"| {p['candidate']} | {p.get('role','—')} | 不可评价 | — | — |");continue
        pairlines.append(f"| {p['candidate']} | {p['role']} | {p['R1_only_repair']} | {p['R0_only_repair']} | {p['both_repair']} |")
    selected=data['selection'].get('selected');ledger=data['metrics']['ledger'];fee=data['fee_estimate_usd'];res=data['resources']
    text=f'''# A3b 真实配对反馈学习 Pilot 报告

状态：{data['status']}。真实模型请求{data['metrics']['paid_requests']}次，协议 `{data['protocol_sha256']}`。只执行这一轮，未运行A4，未改变原A3/S0/标签/规则。

## 数据与解释边界

TRAIN 67条/24游戏，开发验证52条/17游戏。正例分别47/38；可信DECLINE分别7/4，UNKNOWN分别13/10。原验证集已经曝光，只能用于开发资格检查和描述性比较，不是独立泛化证据。来源数据包含受控环境干预，不能将它们伪装为新发生的Agent自发失败。

四份初稿；每份同父R0/R1各最多一次修订。两支使用相同TRAIN样本、完整父源码、系统提示和资源上限；R1增加结构化执行诊断，实际输入更长，不是等Token或纯排版对照。R0固定先运行，样本仅四对，不能据一次生成宣布稳定因果优势。

## 全部版本

表内修复数量为门控MATCH且真实来源环境确认local_repair_verified。错误MATCH只指门控误准入：负例及UNKNOWN未执行S0，不代表观察到了环境损害。静态通过不等于满足完整资格。

| 版本 | 工程状态 | TRAIN修复 | 开发验证修复 | DECLINE误MATCH（TRAIN · 开发） | UNKNOWN误MATCH（TRAIN · 开发） |
|---|---|---:|---:|---:|---:|
{chr(10).join(table)}

## R1对同父R0：真实恢复机会

| 父候选 | 数据角色 | R1独有修复 | R0独有修复 | 两支都修复 |
|---|---|---:|---:|---:|
{chr(10).join(pairlines)}

上述各行是相同检查点配对，不能把跨候选重复执行合并为新增独立游戏。逐条改判/纠错/退化、新误MATCH和按游戏分组统计保存在私有A3b_Real_Results.private.json。

## 资格和权限

冻结选择状态：`{data['selection']['status']}`。选中身份：`{selected}`。

原选择逻辑要求可信正例全保留并通过来源检查，再对负例错误、UNKNOWN错误等排序；这些错误不是零容忍硬门槛。即便选中也只为待回归Shadow，本次禁止执行旧11来源/21边界及A4，无正式发布权限。

## 请求、成本与资源

真实输入{data['usage']['input_tokens']:,}、输出{data['usage']['output_tokens']:,}，合计{data['usage']['total_tokens']:,} tokens。实际返回model字段单列于请求回执，不推断隐藏底层版本。

按实际usage及[DeepSeek公开价格](https://api-docs.deepseek.com/quick_start/pricing/)估算本次API费用约${fee:.6f}；这是时段/缓存计价估算，不是供应商发票。统一账本已结算/预留金额${ledger['charged_or_reserved_cost_microusd']/1e6:.6f}，授权上限$5.50；账本保守计量不能冒充实际API支出。

真实Worker完成{res['worker_executed']:,}次，合计执行计时{res['worker_seconds']:.2f}秒；环境观察步{res['environment_steps']:,}，来源验证回执{res['source_commits']:,}。环境步包含历史前缀重放，不都是新增恢复动作；本地硬件没有核定单价，不能声称基础设施成本为零。未决请求：{ledger['unknown_or_pending_requests']}。

## 完整性

完整请求响应、初稿和分支源码、反馈差异、来源执行及选择均在 `{root}`。S0 SHA `{data['S0_sha256']}`；历史A3逐文件SHA未变。预检报告仍作为运行前记录保留，本报告记录真实运行结果。候选原始失败/拒绝均保留，无额外采样、无后验改规则。
'''
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
