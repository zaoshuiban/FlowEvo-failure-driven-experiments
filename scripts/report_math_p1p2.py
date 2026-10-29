"""Read-only post-run reporting, without private reference answers or solutions."""
import argparse,collections,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.evidence import EvidenceStore
from failure_evo.contracts import fingerprint

def events(p):return EvidenceStore(p).records() if p.exists() else []
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def generate(run,out):
 out.mkdir(parents=True,exist_ok=True)
 scores=[r['payload'] for r in events(run/'discovery_scores.jsonl') if r['kind']=='DISCOVERY_SCORED']
 original_score_labels=[dict(task_id=r['task_id'],initial=r['initial']['status'],final=r['final']['status']) for r in scores]
 if (out/'posthoc_replay.json').exists():scores=json.loads((out/'posthoc_replay.json').read_text())
 locked=[r['payload'] for r in events(run/'controller.jsonl') if r['kind']=='MATH_ANSWER_LOCKED']
 requests=events(run/'solver_requests.jsonl');raw=[r['payload']['response'] for r in requests if r['kind']=='RAW_RESPONSE']
 initial=collections.Counter(r['initial']['status'] for r in scores);final=collections.Counter(r['final']['status'] for r in scores)
 transitions=collections.Counter(r['initial']['status']+' → '+r['final']['status'] for r in scores)
 failure_rows=[r for r in scores if r['final']['status']=='CONFIRMED_WRONG']
 costs={};arms={}
 def usage_cost(raw,gpt=False):
  u=raw.get('usage',{});i=u.get('prompt_tokens',0);o=u.get('completion_tokens',0)
  cache=u.get('prompt_cache_hit_tokens',0) if not gpt else u.get('prompt_tokens_details',{}).get('cached_tokens',0)
  return dict(input_tokens=i,output_tokens=o,total_tokens=u.get('total_tokens',i+o),reasoning_tokens=u.get('completion_tokens_details',{}).get('reasoning_tokens',0),
   quote_estimate_usd=((i-cache)*(2.5 if gpt else .3)+cache*(.25 if gpt else .006)+o*(15 if gpt else 1.2))/1e6,provider_reported_cost_usd=u.get('cost'))
 def total(rows,gpt=False):
  vals=[usage_cost(r,gpt) for r in rows]
  return dict(responses=len(rows),**{k:sum(v[k] for v in vals) for k in ('input_tokens','output_tokens','total_tokens','reasoning_tokens','quote_estimate_usd')},provider_reported_cost_usd=sum(v['provider_reported_cost_usd'] or 0 for v in vals) if any(v['provider_reported_cost_usd'] is not None for v in vals) else None)
 costs['DeepSeek']=total(raw)
 for arm in ('F','T'):
  er=events(run/arm/'candidate/engineering.jsonl');pr=events(run/arm/'provider.jsonl')
  hypothesis=[r['payload'] for r in er if r['kind']=='HYPOTHESIS'];candidates=[r['payload'] for r in er if r['kind']=='CANDIDATE_ENGINEERING']
  provider_raw=[r['payload']['response'] for r in pr if r['kind']=='RAW_RESPONSE']
  costs[arm]=total(provider_raw,True)
  arms[arm]=dict(hypothesis=hypothesis[-1]['content'] if hypothesis else None,candidates=[dict(code_sha256=c['artifact']['code_sha256'],version=c['artifact']['version'],parent_sha256=c['artifact']['parent_sha256'],source_event_ids=c['artifact']['source_event_ids'],static=c['static'],calls=c['calls'],engineering_passed=c['engineering_passed'],source_path=c['artifact']['source_path']) for c in candidates],engineering_passed=sum(c['engineering_passed'] for c in candidates),paid_model_responses=len(provider_raw),registry_publications=0)
  write(out/(arm+'_operator_provenance.json'),arms[arm])
 status=json.loads((run/'COMPLETE.json').read_text()) if (run/'COMPLETE.json').exists() else (json.loads((run/'STOP.json').read_text()) if (run/'STOP.json').exists() else {'status':'RUNNING'})
 integrity=[]
 for r in failure_rows:
  l=next(x for x in locked if x['task_id']==r['task_id'])
  good=(r['locked_sha256']==l['locked_sha256'] and r['trajectory_sha256']==fingerprint(l['responses']) and r['final']['correct'] is False and all(a.get('gold_exposed') is False for a in r['responses']))
  integrity.append(dict(task_id=r['task_id'],evidence_id=r['evidence_id'],problem_sha256=r['problem_sha256'],trajectory_sha256=r['trajectory_sha256'],locked_sha256=r['locked_sha256'],complete=good,legal_feedback={'correct':False},scorer_version=r['scorer_version'],solver_models=sorted(set(a['model'] for a in r['responses'])),raw_response_journal=str(run/'solver_requests.jsonl')))
 unknown=[];reserved={}
 for label,p in [('DeepSeek',run/'solver_budget.jsonl'),('F',run/'F/budget.jsonl'),('T',run/'T/budget.jsonl')]:
  rows=events(p);reserve={r['payload']['request_id']:r['payload'] for r in rows if r['kind']=='RESERVED'}
  # Preserve raw ledger summary without treating reservation as invoice.
  unknown += [dict(channel=label,**r['payload']) for r in rows if r['kind']=='UNKNOWN']
  reserved[label]=sum(r.get('cost_upper_microusd',0) for r in reserve.values())/1e6
 summary=dict(original_score_labels=original_score_labels,label_basis='POSTHOC_V2_DIAGNOSIS_ONLY' if (out/'posthoc_replay.json').exists() else 'ORIGINAL_FROZEN',status=status,completed_tasks=len(scores),planned_tasks=96,initial_statuses=dict(initial),final_statuses=dict(final),transitions=dict(transitions),
  initial_confirmed_failures=initial['CONFIRMED_WRONG'],final_confirmed_failures=final['CONFIRMED_WRONG'],reliably_scored_final=final['CONFIRMED_CORRECT']+final['CONFIRMED_WRONG'],
  failures_integrity=integrity,costs=costs,quote_estimate_total_usd=sum(v['quote_estimate_usd'] for v in costs.values()),reserved_upper_usd=reserved,unknown_requests=unknown,arms=arms,
  no_gate=True,no_cross_task_reuse=True,no_operator_correctness_scored=True,no_paid_mock_results_claimed=True)
 write(out/'summary.json',summary);write(out/'failure_manifest.json',integrity)
 write(out/'task_outcomes.json',[{k:r[k] for k in ('task_id','initial','final','attempt_grades','locked_sha256','trajectory_sha256','evidence_id')} for r in scores])
 def md(name,text):(out/name).write_text(text+'\n')
 table='\n'.join('| '+k+' | '+str(initial[k])+' | '+str(final[k])+' |' for k in ('CONFIRMED_CORRECT','CONFIRMED_WRONG','UNVERIFIED','EXECUTION_ERROR'))
 md('P1_真实失败收集报告.md',f'''# P1 真实失败收集报告

Run：`{run.name}`。P0冻结Discovery96题、固定两次DeepSeek Flash调用、全部调用完成后锁定再评分。未读取Design/Gate/Legacy/Fresh题目。

完成 **{len(scores)}/96**。首次明确失败 **{initial['CONFIRMED_WRONG']}** 道；最终明确失败 **{final['CONFIRMED_WRONG']}** 道。最终可靠评分 **{summary['reliably_scored_final']}** 道。两次输出始终按同一道题统计，不算两个独立样本。

| 状态 | 首次 | 最终 |
|---|---:|---:|
{table}

变化分布：

```json
{json.dumps(dict(transitions),ensure_ascii=False,indent=2)}
```

失败证据完整性：{sum(x['complete'] for x in integrity)}/{len(integrity)}。每条包含题面/完整输出、解析答案、锁定与轨迹哈希、模型及usage、评分版本和二值反馈。实际响应ID与原始供应商输出保存在solver_requests.jsonl。非思考模式不提供隐藏推理轨迹；保存的是完整可见解答和供应商返回字段，不虚构隐藏思维链。

最终CONFIRMED_WRONG进入学习池；首次错误而最终正确保留恢复记录，但不进入此次归纳输入。UNVERIFIED不作为失败；请求/解析/执行异常单独记录，未知请求触发停止。

DeepSeek实际响应{costs['DeepSeek']['responses']}次，{costs['DeepSeek']['total_tokens']} tokens，按冻结峰值报价含缓存字段估算${costs['DeepSeek']['quote_estimate_usd']:.6f}。非供应商账单，实际非高峰计价可能更低。原始计量和保守预留分别保留。

当前终态：`{status['status']}`。详情见task_outcomes.json与failure_manifest.json。
''')
 htext='\n\n'.join('## '+a+'\n\n```json\n'+json.dumps(arms[a]['hypothesis'],ensure_ascii=False,indent=2)+'\n```' for a in ('F','T'))
 md('P2_自主机制发现报告.md',f'''# P2 自主机制发现报告

事前规则：从最早两道不同题面的最终CONFIRMED_WRONG记录取证；不足两道则停止P2。不按机制名称或模型生成结果选题。

F见题面、完整两次公开输出、错误解析答案与correct=false；T只见相同题面。二者均为GPT-5.4，通过OpenRouter固定OpenAI供应商、关闭fallback；单组最多归纳1次、候选1次、契约修复1次。

未提供标准答案、官方solution、评分差异、历史算子或Gate材料。错误根因仍由GPT推测，不是评分器确认。模型原始wire与输出见各组provider.jsonl；生成内容未人工改写。

{htext}

模型假设不是验证事实。本轮未开展来源答案正确性或跨题实验；F/T只可比较假设和代码行为，不可凭代码数量判断失败学习优越性。
''')
 ct=[]
 for a in ('F','T'):
  for c in arms[a]['candidates']:
   ct.append(f"| {a} v{c['version']} | {c['code_sha256'][:16]} | {c['static']['passed']} | {c['engineering_passed']} | "+', '.join(x['result']['status'] for x in c['calls'])+' |')
 md('P2_生成算子工程验收报告.md','''# P2 生成算子工程验收报告

| 组/版本 | 源码SHA前缀 | 静态通过 | 工程通过 | Worker实际状态 |
|---|---|---|---|---|
'''+ '\n'.join(ct)+'''

Worker运行精确GPT响应源码，哈希绑定，不由宿主提供等价算法。只执行两道来源题面和一条无数学问题的拒绝工程输入，不做其他任务验证。APPLIED表示输出可执行计算结果，不代表数学正确。

检查语法、math_operator接口、允许依赖、禁止权限、返回协议、2秒超时与异常。源码不做人工修复；只有静态/返回契约问题可向GPT提出一次定向修复。算子答案错误不得触发本轮追加模型修复。

全部候选仅Shadow记录，没有Experimental权限、Hook发布或跨题复用。完整调用、源码、版本父链和来源见F_operator_provenance.json、T_operator_provenance.json及Run制品。
''')
 md('P1P2_实验总结.md',f'''# P1–P2 实验总结

Run：`{run.name}`。状态：`{status['status']}`。

- 真实完成：{len(scores)}/96题；首次明确失败{initial['CONFIRMED_WRONG']}，最终明确失败{final['CONFIRMED_WRONG']}。
- GPT实际响应：F {costs['F']['responses']}次，T {costs['T']['responses']}次。
- 工程验收通过的版本：F {arms['F']['engineering_passed']}，T {arms['T']['engineering_passed']}。
- 总实际返回tokens：{sum(v['total_tokens'] for v in costs.values())}；按冻结报价估算${summary['quote_estimate_total_usd']:.6f}。
- 未开展Gate、跨题复用、正确率对比；不能宣称失败驱动算子已获得泛化或收益。

## 证据解释

真实数学失败、二值评分、模型假设、模型源码和真实Worker运行是不同证据层级。源码工程合格不等于算法正确。Task-only与F的行为差异需结合原始输出审查；单次差异不能给出因果性能结论。源码是否来源特定、是否只是提示策略，须在完成后另附代码审查，不通过人工补写算法制造成功。

## 运行和费用边界

25项零API测试先于真实请求通过。独立授权总硬上限17美元（P1 9、F 4、T 4），不是旧预算续用；真实请求次数、usage、提供商返回cost（若有）、报价估算与保守预留分开保存。所有UNKNOWN保持未知，不自动重发。

[失败收集](P1_真实失败收集报告.md) · [机制发现](P2_自主机制发现报告.md) · [工程验收](P2_生成算子工程验收报告.md) · [机器结果](summary.json)
''')
 print(json.dumps({k:summary[k] for k in ('status','completed_tasks','initial_confirmed_failures','final_confirmed_failures','quote_estimate_total_usd')},ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True);a=p.parse_args();generate(Path(a.run).resolve(),Path(a.output).resolve())
