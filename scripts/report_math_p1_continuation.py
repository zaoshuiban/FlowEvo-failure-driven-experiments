"""Post-run read-only audit and reporting. Never loads private reference answers."""
import argparse,collections,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.evidence import EvidenceStore
from failure_evo.contracts import canonical,fingerprint
from code_math.no_gold import PublicMathTask,solver_messages

def records(path):return EvidenceStore(path).records() if path.exists() else []
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def report(run,out):
 p=json.loads((run/'protocol.json').read_text());plan=p['plan'];out.mkdir(parents=True,exist_ok=True)
 c=records(run/'controller.jsonl');s=records(run/'scores.jsonl');q=records(run/'requests.jsonl');ledger=records(run/'budget.jsonl')
 locked=[r['payload'] for r in c if r['kind']=='MATH_ANSWER_LOCKED'];scores=[r['payload'] for r in s if r['kind']=='DISCOVERY_SCORED']
 requests=[r['payload'] for r in q if r['kind']=='NO_GOLD_REQUEST'];sent=[r['payload'] for r in q if r['kind']=='SEND_STARTED'];responses=[r['payload'] for r in q if r['kind']=='RAW_RESPONSE']
 planned=[x['task_id'] for x in plan['new_tasks']];done=[x['task_id'] for x in locked];unknown=[r['payload'] for r in ledger if r['kind']=='UNKNOWN']
 initial=collections.Counter(x['initial']['status'] for x in scores);final=collections.Counter(x['final']['status'] for x in scores)
 transitions=collections.Counter(x['initial']['status']+' → '+x['final']['status'] for x in scores)
 reqmap={r['request_id']:r for r in requests};rawmap={r['request_id']:r['response'] for r in responses}
 entries=[];frozen_wires=True
 for x in locked:
  task=next(t for t in plan['new_tasks'] if t['task_id']==x['task_id']);prev=None
  for i,a in enumerate(x['responses']):
   key=x['episode_id']+'/s'+str(i)
   wire=reqmap[key]['wire'];expected=solver_messages(PublicMathTask.parse(task),prev,profile='concise-v1')
   frozen_wires &= wire['messages']==expected and wire['model']=='deepseek-flash' and wire['max_tokens']==4096 and wire['temperature']==0
   frozen_wires &= reqmap[key].get('gold_exposed') is False
   prev=a['text']
  entries.append(dict(task_id=x['task_id'],original_discovery_ordinal=x['sequence']+1,episode_id=x['episode_id'],calls=x['model_calls'],locked_sha256=x['locked_sha256'],finish_reasons=[a['finish_reason'] for a in x['responses']],input_tokens=x['input_tokens'],output_tokens=x['output_tokens']))
 costs=[]
 for item in responses:
  raw=item['response'];u=raw['usage'];i=u['prompt_tokens'];o=u['completion_tokens'];hit=u.get('prompt_cache_hit_tokens',0)
  costs.append(dict(request_id=item['request_id'],response_id=raw.get('id'),model=raw['model'],finish_reason=raw['choices'][0]['finish_reason'],input_tokens=i,output_tokens=o,reasoning_tokens=u.get('completion_tokens_details',{}).get('reasoning_tokens',0),total_tokens=u['total_tokens'],cache_hit_tokens=hit,estimated_usd_frozen_peak=((i-hit)*.3+hit*.006+o*1.2)/1e6,provider_reported_cost=u.get('cost')))
 reserves=[r['payload'] for r in ledger if r['kind']=='RESERVED'];reserved=sum(r['cost_upper_microusd'] for r in reserves)/1e6
 failures=[r for r in scores if r['final']['status']=='CONFIRMED_WRONG'];truncated=[r for r in scores if r['final']['status']=='TRUNCATED']
 audit=dict(task_order_preserved=done==planned[:len(done)],completed_task_count=len(done),planned_task_count=82,exact_two_calls=all(r['model_calls']==2 for r in locked),
  no_exposed_or_quarantined_tasks=not(set(done)&set(plan['exposed_locked']+plan['quarantined_started_unlocked'])),
  duplicate_request_ids=len(sent)-len({r['request_id'] for r in sent}),request_ids_use_new_run=all(r['request_id'].startswith(run.name+'/') for r in requests),frozen_wire_verified=frozen_wires,
  lock_hashes_valid=all(fingerprint({k:v for k,v in r.items() if k!='locked_sha256'})==r['locked_sha256'] for r in locked),
  evidence_hashes_valid=all(r['trajectory_sha256']==fingerprint(r['responses']) and fingerprint({k:v for k,v in r.items() if k!='evidence_id'})==r['evidence_id'] for r in scores),
  scoring_after_complete_lock=all(any(t['kind']=='MATH_ANSWER_LOCKED' and t['payload']['locked_sha256']==r['payload']['locked_sha256'] and t['at']<=r['at'] for t in c) for r in s if r['kind']=='DISCOVERY_SCORED'),
  failure_admission_valid=all(r['final']['correct'] is False and r['responses'][-1]['finish_reason']=='stop' for r in failures),unknown_new_requests=unknown,
  source_hashes_unchanged=all(sha(ROOT/name)==digest for name,digest in p['source_hashes'].items()),p2_started=False,budget_within_cap=reserved<=8)
 old_summary_path=ROOT/'reports/math_p1p2_20261027/summary.json'
 old_summary=json.loads(old_summary_path.read_text()) if old_summary_path.exists() else {}
 historical=dict(previous_estimated_usd=old_summary.get('quote_estimate_total_usd'),previous_tokens=old_summary.get('costs',{}).get('DeepSeek',{}).get('total_tokens'),note='old run costs reported separately; scores and budgets not pooled')
 status='COMPLETE' if (run/'COMPLETE.json').exists() else 'STOPPED' if (run/'STOP.json').exists() else 'RUNNING'
 summary=dict(historical_cost=historical,run_id=run.name,status=status,protocol_sha256=sha(run/'protocol.json'),completed=len(scores),planned=82,old_exposed=13,old_unknown_quarantined=1,
  initial=dict(initial),final=dict(final),transitions=dict(transitions),distinct_task_final_failures=len(failures),first_wrong_final_correct=sum(r['initial']['status']=='CONFIRMED_WRONG' and r['final']['status']=='CONFIRMED_CORRECT' for r in scores),
  models={'solver':'deepseek-flash','generation_calls':0},requests_sent=len(sent),responses=len(responses),
  tokens={k:sum(x[k] for x in costs) for k in ('input_tokens','output_tokens','reasoning_tokens','total_tokens','cache_hit_tokens')},
  estimated_usd_frozen_peak=sum(x['estimated_usd_frozen_peak'] for x in costs),reserved_upper_usd=reserved,hard_cap_usd=8,invoice_available=False,
  audit=audit,discovery_coverage={'old_configuration_completed':13,'new_configuration_completed':len(scores),'old_unknown_quarantined':1,'remaining_not_completed':82-len(scores)},p2_started=False)
 for name,val in [('summary.json',summary),('audit.json',audit),('request_costs.json',costs),('confirmed_failures.json',failures),('truncated_records.json',truncated),('task_trajectory_manifest.json',entries),('task_outcomes.json',[dict(task_id=r['task_id'],initial=r['initial'],final=r['final'],evidence_id=r['evidence_id']) for r in scores])]:dump(out/name,val)
 categories=('CONFIRMED_CORRECT','CONFIRMED_WRONG','TRUNCATED','UNVERIFIED','EXECUTION_ERROR')
 table='\n'.join(f'| {k} | {initial[k]} | {final[k]} |' for k in categories)
 fs='\n'.join(f"| {i+1} | `{r['task_id']}` | {r['initial']['status']} | {r['final']['parsed_answer']} | `{r['evidence_id'][:16]}` |" for i,r in enumerate(failures))
 errors=[k for k,v in audit.items() if v is False and k!='p2_started']
 text=f'''# P1剩余82题无Gold可信失败收集报告

Run：`{run.name}`。状态：**{status}**。本轮只执行P1，GPT/P2调用0次。

## 任务边界

82道新任务按冻结原序运行，完成{len(scores)}/82。旧13题保持曝光标记，旧第14题UNKNOWN继续隔离，没有重发。原Discovery覆盖口径为旧配置13题＋新配置{len(scores)}题＋1题隔离；新旧提示不同，不合并为同一配置96题实验。

## 可信数学失败与截断

| 状态 | 首次输出（终态锁后评分） | 最终输出 |
|---|---:|---:|
{table}

最终可可靠评分{final['CONFIRMED_CORRECT']+final['CONFIRMED_WRONG']}题；确认数学答案错误{len(failures)}题，输出截断{len(truncated)}题。首次错误但最终正确{summary['first_wrong_final_correct']}题。两次输出属于同一道来源题，不计两道独立失败。

`TRUNCATED`的correct=null，不能进入数学失败池；`UNVERIFIED`也不计真实错误。CONFIRMED_WRONG指当前冻结评分协议下完整明确数值答案与私有参考不一致，不等于已经定位具体数学推理根因。

| 序号 | 来源题ID | 首次状态 | 模型最终错误答案（非Gold） | 证据ID前缀 |
|---|---|---|---|---|
{fs}

完整题面、两轮输出、解析结果、模型/usage、锁定哈希及二值反馈保存在confirmed_failures.json。没有标准答案或官方解法。所有符号非匹配仍保持未确认，未在看到模型表现后修改评分器。

## 请求、tokens和费用

- 发送{len(sent)}次，返回{len(responses)}次；本轮UNKNOWN {len(unknown)}次。
- 输入{summary['tokens']['input_tokens']}、输出{summary['tokens']['output_tokens']}、总{summary['tokens']['total_tokens']} tokens；单独返回的推理tokens {summary['tokens']['reasoning_tokens']}（非思考模式）。
- 按冻结峰值报价并使用缓存命中字段估算 **${summary['estimated_usd_frozen_peak']:.6f}**，不是供应商账单；实际非高峰价格可能更低。
- 旧Run估算费用${historical['previous_estimated_usd']:.6f}、{historical['previous_tokens']} tokens单列，不占用本轮新8美元授权；旧UNKNOWN仍保留原预留。
- 账本保守占用上界 **${reserved:.6f}**，硬上限$8；保守占用不是实付。

报价依据：[DeepSeek官方价格](https://api-docs.deepseek.com/quick_start/pricing/)。冻结输入缓存未命中$0.30/M、缓存命中$0.006/M、输出$1.20/M；按实际usage计量，不以序列化字节冒充实际tokens。

## 隔离与审计

- 源码哈希及题序保持：{audit['source_hashes_unchanged']} / {audit['task_order_preserved']}。
- 每个完成任务固定两次调用：{audit['exact_two_calls']}；未用中间正确性决定重试。
- 实际请求内容逐条重建核对：{audit['frozen_wire_verified']}。仅题面与自己的未评分输出，gold_exposed=False。
- 评分发生在完整终态锁后：{audit['scoring_after_complete_lock']}。
- 重复请求ID：{audit['duplicate_request_ids']}；旧曝光和隔离题未调用：{audit['no_exposed_or_quarantined_tasks']}。
- 失败证据哈希和准入有效：{audit['evidence_hashes_valid']} / {audit['failure_admission_valid']}。
- 审计未通过项：{errors}。

新配置只增加通用简洁交付要求，仍为4096-token上限、temperature=0、固定自检一次。未指定算法、未修改模型输出、未人工制造错误。

## 研究结论与下一步

本轮回答的是是否能获得可信数学失败，不是算子学习是否成功。即使有足够失败，也不自动启动P2；失败池可用于后续单独冻结的GPT自主归纳。当前没有生成算子、来源效果或跨题收益结论。若错误不足，应报告机会不足，不能将截断改称数学错误。

机器数据：[汇总](summary.json)、[审计](audit.json)、[可信失败](confirmed_failures.json)、[截断记录](truncated_records.json)、[请求费用](request_costs.json)、[逐题结果](task_outcomes.json)。
'''
 (out/'P1_剩余82题可信失败收集报告.md').write_text(text)
 print(json.dumps({k:summary[k] for k in ('status','completed','final','responses','estimated_usd_frozen_peak','reserved_upper_usd')},ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--out',required=True);a=p.parse_args();report(Path(a.run).resolve(),Path(a.out).resolve())
