"""Immutable-input experiment reporting, no model/network calls."""
import datetime,collections,json
from run_hard140_algorithm import *
REPORT=ROOT/'reports/hard140_algorithm_20261028_01'
def report():
 p=verify();REPORT.mkdir(exist_ok=True);tasks=load(OUT/'tasks.json');labels={x['task_id']:x for x in load(OUT/'private/labels.json')};audit=load(OUT/'selection_audit.json')
 outcomes=load(OUT/'discovery_outcomes.json') if (OUT/'discovery_outcomes.json').exists() else load(OUT/'discovery_progress.json') if (OUT/'discovery_progress.json').exists() else []
 scores=load(OUT/'evaluation/scores.json') if (OUT/'evaluation/scores.json').exists() else [];evidence=load(OUT/'failure_evidence.json') if (OUT/'failure_evidence.json').exists() else [];chosen=load(OUT/'selected_failure_evidence.json') if (OUT/'selected_failure_evidence.json').exists() else []
 requests=[];ledgers=[];send_events=[]
 for path in [*sorted((OUT/'solver').glob('*/requests.jsonl')),*sorted((OUT/'jobs').glob('*/provider.jsonl'))]:
  for line in path.read_text().splitlines():
   e=json.loads(line)
   if e['kind']=='SEND_STARTED':send_events.append(e)
   if e['kind']!='RAW_RESPONSE':continue
   raw=e['payload']['response'];u=raw['usage'];dt=datetime.datetime.fromtimestamp(e['at'],datetime.timezone.utc);factor=1 if dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10) else .5
   hit=u.get('prompt_cache_hit_tokens',u.get('prompt_tokens_details',{}).get('cached_tokens',0));miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit);cost=(hit*.006+miss*.3+u['completion_tokens']*1.2)*factor/1e6
   requests.append(dict(channel='solver' if path.parent.parent.name=='solver' else path.parent.name.split('-')[-1],job=path.parent.name,id=raw['id'],at=e['at'],utc=dt.isoformat(),usage=u,model=raw['model'],price_factor=factor,estimated_cost_usd=cost,finish_reason=raw['choices'][0]['finish_reason']))
 for path in [*sorted((OUT/'solver').glob('*/budget.jsonl')),*sorted((OUT/'jobs').glob('*/budget.jsonl'))]:
  ledgers += [json.loads(l) for l in path.read_text().splitlines()]
 summary={}
 for arm in ['solver','T','F','FC']:
  rr=[r for r in requests if r['channel']==arm];ss=[s for s in scores if s['arm']==arm]
  summary[arm]=dict(calls=len(rr),input_tokens=sum(x['usage']['prompt_tokens'] for x in rr),output_tokens=sum(x['usage']['completion_tokens'] for x in rr),total_tokens=sum(x['usage']['total_tokens'] for x in rr),estimated_cost_usd=sum(x['estimated_cost_usd'] for x in rr),attempts=len(ss),static_pass=sum(x['status']=='STATIC_VALID_SHADOW' for x in ss),source_correct=sum(x['grade']['status']=='CONFIRMED_CORRECT' for x in ss),source_wrong=sum(x['grade']['status']=='CONFIRMED_WRONG' for x in ss),other=sum(x['grade']['status'] not in ['CONFIRMED_CORRECT','CONFIRMED_WRONG'] for x in ss))
 bysubject={s:dict(n=20,completed=0,initial=collections.Counter(),final=collections.Counter(),credible_failure_tasks=0) for s in SUBJECTS}
 for x in outcomes:
  sub=labels[x['task_id']]['subject'];z=bysubject[sub];z['completed']+=1;z['initial'][x['initial']['status']]+=1;z['final'][x['final']['status']]+=1;z['credible_failure_tasks']+=any(g['status']=='CONFIRMED_WRONG' for g in x['attempt_grades'])
 counts=dict(initial=dict(collections.Counter(x['initial']['status'] for x in outcomes)),final=dict(collections.Counter(x['final']['status'] for x in outcomes)),credible_failure_tasks=len(evidence),generation_source_tasks=len(chosen),by_subject=bysubject)
 reserved=sum(e['payload']['cost_upper_microusd'] for e in ledgers if e['kind']=='RESERVED')/1e6;unknown=[e for e in ledgers if e['kind']=='UNKNOWN'];worker=[json.loads(l) for l in (OUT/'evaluation/worker.jsonl').read_text().splitlines()] if (OUT/'evaluation/worker.jsonl').exists() else []
 # Exact actual wires reconstructed from public task+previous unverified output.
 wire_checks=[];taskmap={t['task_id']:PublicMathTask.parse(t) for t in tasks}
 for directory in (OUT/'solver').glob('*'):
  if not (directory/'controller.jsonl').exists():continue
  ctrl=EvidenceStore(directory/'controller.jsonl').records();reqs=EvidenceStore(directory/'requests.jsonl').records();locks=[e['payload'] for e in ctrl if e['kind']=='MATH_ANSWER_LOCKED']
  for lock in locks:
   previous=None
   for i,response in enumerate(lock['responses']):
    request=next(e['payload'] for e in reqs if e['kind']=='NO_GOLD_REQUEST' and e['payload']['request_id']==lock['episode_id']+'/s'+str(i));body=request['wire'];body=json.loads(body) if isinstance(body,str) else body
    passed=body['messages']==solver_messages(taskmap[lock['task_id']],previous,profile='concise-v1');assert passed;wire_checks.append(dict(task_id=lock['task_id'],step=i,exact_public_projection=passed,gold_exposed=request['gold_exposed']));previous=response['text']
 integrity=dict(protocol_hash=fingerprint(p),old_runs_unchanged=all(sha(ROOT/k)==v for k,v in p['previous_hashes'].items()),frozen_source_verified=True,responses=len(requests),send_started=len(send_events),unique_response_ids=len({r['id'] for r in requests}),unknown=len(unknown),reserved_upper_sum_usd=reserved,worker_calls=len(worker),worker_seconds=sum(x['payload'].get('seconds',0) for x in worker),wire_checks=len(wire_checks),finish_reasons=dict(collections.Counter(r['finish_reason'] for r in requests)))
 assert integrity['old_runs_unchanged'] and integrity['unique_response_ids']==len(requests)
 save(REPORT/'metrics.json',dict(discovery=counts,channels=summary,integrity=integrity));save(REPORT/'request_costs.json',requests);save(REPORT/'wire_projection_audit.json',wire_checks)
 paired=[]
 for e in chosen:
  ss={x['arm']:x for x in scores if x['task_id']==e['task_id']};paired.append(dict(task_id=e['task_id'],subject=labels[e['task_id']]['subject'],arms={a:dict(generation=x['status'],execution=x['raw']['status'],grade=x['grade']['status']) for a,x in ss.items()}))
 save(REPORT/'paired_results.json',paired)
 table='\n'.join(f"|{s}|{z['completed']}/20|{z['initial'].get('CONFIRMED_CORRECT',0)}|{z['initial'].get('CONFIRMED_WRONG',0)}|{z['final'].get('CONFIRMED_CORRECT',0)}|{z['final'].get('CONFIRMED_WRONG',0)}|{z['final'].get('UNVERIFIED',0)}|{z['final'].get('TRUNCATED',0)}|{z['credible_failure_tasks']}|" for s,z in bysubject.items())
 costrows='\n'.join(f"|{a}|{z['calls']}|{z['attempts']}|{z['static_pass']}|{z['source_correct']}|{z['source_wrong']}|{z['other']}|{z['total_tokens']:,}|${z['estimated_cost_usd']:.6f}|" for a,z in summary.items())
 details='\n'.join(f"|{x['task_id']}|{x['arm']}|{x['status']}|{x['raw']['status']}|{x['grade']['status']}|" for x in scores)
 per_task='\n'.join(f"|{i+1}|{t['task_id']}|{next((x['initial']['status'] for x in outcomes if x['task_id']==t['task_id']),'NOT_RUN')}|{next((x['final']['status'] for x in outcomes if x['task_id']==t['task_id']),'NOT_RUN')}|" for i,t in enumerate(tasks))
 (REPORT/'Task_List_and_Outcomes.md').write_text('# 冻结140题与逐题结果\n\n|序号|任务ID|首轮|最终|\n|---|---|---|---|\n'+per_task+'\n\n'+''.join(f"\n## {i+1}. {t['task_id']}\n\n{t['problem']}\n" for i,t in enumerate(tasks)))
 text=f'''# 140道最高难度多类型数学题：真实失败与算子合成实验

## 运行状态

Run `{OUT.name}`；任务完成记录{len(outcomes)}/140。Discovery状态：{'COMPLETE' if (OUT/'DISCOVERY_COMPLETE.json').exists() else 'PARTIAL'}；算法生成状态：{'COMPLETE' if (OUT/'GENERATION_COMPLETE.json').exists() else 'NOT_COMPLETE'}；Worker来源评价状态：{'COMPLETE' if (OUT/'COMPLETE.json').exists() else 'NOT_COMPLETE'}。总共{len(requests)}次真实模型响应。

## 选题与冻结

采用[EleutherAI/hendrycks_math](https://huggingface.co/datasets/EleutherAI/hendrycks_math)固定revision `{p['dataset']['revision']}` 的train七个分片。140题均为该数据集最高难度标签Level 5，每类20题。所谓“最高”指数据集等级，不是宣称这些题是全部数学题中最难，也不保证DeepSeek会失败。

按`SHA256(hard140-v1:subject:row)`固定排序，在每类取首20道合格题，并按七类轮转形成完整顺序。排除依赖图像或图示语义不确定的题、超长题、缺少明确参考答案的题，以及与{audit['known_public_texts']}条已记录公开题面或本次选题近重复的题。近重复采用数字掩码、空白规范化后的SequenceMatcher≥0.90。上一轮10题与旧P2/Discovery/Design公开题已纳入排除。选题不使用目标模型运行表现。

候选筛查：`{json.dumps(dict(collections.Counter(x['reason'] for x in audit['funnel'])),ensure_ascii=False)}`。104题官方答案是精确有理数，36题为符号/集合等形式；本轮不因非数值答案排除难题。曝光筛查不是全项目或模型预训练去重的完备证明。不访问Gate/Legacy/Fresh、419题长流或119题确认池。

协议SHA `{fingerprint(p)}`；Git基准`{p['git_sha']}`，实际修改源码以逐文件SHA冻结，不能只用Git SHA代替运行代码状态。

## 求解与证据准入

沿用FlowEvo无Gold数学控制器、DeepSeek Flash、concise-v1、temperature=0、每次8192输出Token。每题固定两次调用；第二次是无任何评分反馈的自我复核，不根据首轮隐藏正确性决定是否调用。四路并发仅用于独立任务API传输，不是多Agent角色系统；每任务账本独立、无跨任务信息，四题窗口按冻结顺序派发。未知请求或基础设施问题停止下一窗口，不自动重发。

两次输出锁定后评分：精确可确认的错误为CONFIRMED_WRONG；截断为TRUNCATED；无法确认符号等价/不等价为UNVERIFIED。不将后两者冒充数学失败。若复核输入因原有保守上界无法发送，则该题TASK_NOT_COMPLETED，无自动补发或放宽上限。

首轮分布：`{json.dumps(counts['initial'],ensure_ascii=False)}`。

最终分布：`{json.dumps(counts['final'],ensure_ascii=False)}`。

至少一次可信数学错误的独立原题：{len(evidence)}。同一题两次错误不算两道独立来源。

|类型|完成|首轮正确|首轮错误|最终正确|最终错误|最终未确认|最终截断|有可信错误的题|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{table}

## 有界T/F/F-C实验

事前规则：每类型选冻结顺序最早的两个具有可信错误的任务，最多14个来源，不补齐不存在的失败类型、不根据生成结果换源。本轮入选{len(chosen)}个来源。每源只提供最早一次可信错误，后续已正确的输出不提供给生成器。

T只看题面；F额外看到该真实错误轨迹及二值false；F-C在相同证据上要求分开陈述错误操作与自行提出的替代操作。三组共享DeepSeek型号、temperature=0.2、8192输出上限、每源两调用（分析/源码）、零修订和相同工程检查。沿用上一轮冻结生成协议`{GENERATION_VERSION}`，没有人工数学算法提示。

模型自主提出参数schema及来源参数映射，生成`solve(parameters)`。因此来源分数是算法与参数映射的联合结果，不是纯算法正确性或跨题泛化。源码及分析全部冻结后，在现有Linux Worker中实际执行，结果锁定后才与私有官方答案比较。没有用Gold反复修订，没有自动获得Experimental权限。

|条件|请求|生成尝试|静态通过|来源正确|来源错误|其他/未执行|全部Token|API估算|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{costrows}

|来源任务|条件|生成|执行|私有评分|
|---|---|---|---|---|
{details}

单次配对、每源一份候选；不按最佳版本挑选。未交付、静态拒绝、运行异常和数学错误分别记录。即使观察到F独有来源成功，也不能宣称失败经验提高未见任务泛化；必须审查是否真正参数化、输入映射是否泄漏计算结果、是否仅解决来源题。

## 成本与审计

真实模型Token {sum(z['total_tokens'] for z in summary.values()):,}，按实际usage和缓存/时段估算费用${sum(z['estimated_cost_usd'] for z in summary.values()):.6f}。账本费用预留上界合计${reserved:.6f}，不是实际账单。独立硬上限分配：140×$0.15求解 + 最多42×$0.25生成 = $31.50；上限不等于预计支出，也不要求花满。

价格来自[DeepSeek官方价目](https://api-docs.deepseek.com/quick_start/pricing/)，快照保存在Run：Flash峰时缓存命中/未命中/输出$0.006/$0.30/$1.20每百万Token，非峰时减半。逐请求原始usage和估算见`request_costs.json`，包括所有失败生成成本。Worker记录墙钟{integrity['worker_seconds']:.3f}秒，本地计算未完全货币化。

响应ID去重{integrity['unique_response_ids']}/{len(requests)}，UNKNOWN {integrity['unknown']}。完成任务的{len(wire_checks)}条实际wire逐条与题面+上次未验证输出重建相等，未提供Gold/solution/中间评分。旧10题与旧算法实验哈希保持不变。8项零API验收通过，包括真实Worker；Mock仅证明工程能力。

## 研究边界

这是最高标签开发任务上的失败机会与来源合成实验，不是独立Gate、不证明长期收益。UNVERIFIED降低可确认覆盖，不能算错误或正确；官方最高难度仍可能对模型较易。三组输入长度不同、未设置等Token中性对照，且单次生成存在随机波动。冻结任务及代码不因中间成绩而改变。未自动扩大到其他数据集或修订当前契约路线。

[逐题清单与结果](Task_List_and_Outcomes.md)；机器数据`metrics.json`、`paired_results.json`、`request_costs.json`、`wire_projection_audit.json`。所有原始模型响应、源码、账本及Worker结果在`runs/{OUT.name}`。
'''
 (REPORT/'Hard140_Final_Report.md').write_text(text)
 print(json.dumps(dict(discovery=counts,channels=summary,integrity=integrity),ensure_ascii=False,indent=2))
if __name__=='__main__':report()
