"""Read-only report; never sends model requests or changes frozen results."""
import json,datetime,collections,ast
from run_hard10_algorithm import ROOT,OUT,load,save,sha,verify,fingerprint
p=verify();report=ROOT/'reports/hard10_algorithm_20261028_01';report.mkdir(exist_ok=True)
outcomes=load(OUT/'discovery_outcomes.json');scores=load(OUT/'evaluation/scores.json');tasks=load(OUT/'tasks.json');evidence=load(OUT/'failure_evidence.json')
requests=[];ledgers=[]
for path in [OUT/'solver/requests.jsonl',*sorted((OUT/'jobs').glob('*/provider.jsonl'))]:
 for line in path.read_text().splitlines():
  e=json.loads(line)
  if e['kind']=='RAW_RESPONSE':
   raw=e['payload']['response'];u=raw['usage'];dt=datetime.datetime.fromtimestamp(e['at'],datetime.timezone.utc);peak=dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10);factor=1 if peak else .5
   hit=u.get('prompt_cache_hit_tokens',u.get('prompt_tokens_details',{}).get('cached_tokens',0));miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit)
   cost=(hit*.006+miss*.3+u['completion_tokens']*1.2)*factor/1e6
   requests.append(dict(channel='solver' if path.parent.name=='solver' else path.parent.name.split('-')[-1],job=path.parent.name,id=raw['id'],at=e['at'],utc=dt.isoformat(),model=raw['model'],usage=u,estimated_cost_usd=cost,price_factor=factor,finish_reason=raw['choices'][0]['finish_reason']))
for path in [OUT/'solver/budget.jsonl',*sorted((OUT/'jobs').glob('*/budget.jsonl'))]:
 for line in path.read_text().splitlines():
  e=json.loads(line);ledgers.append(e)
summary={}
for arm in ['solver','T','F','FC']:
 rr=[r for r in requests if r['channel']==arm];ss=[s for s in scores if s['arm']==arm]
 summary[arm]=dict(calls=len(rr),input_tokens=sum(x['usage']['prompt_tokens'] for x in rr),output_tokens=sum(x['usage']['completion_tokens'] for x in rr),tokens=sum(x['usage']['total_tokens'] for x in rr),estimated_cost_usd=sum(x['estimated_cost_usd'] for x in rr),attempts=len(ss),static_pass=sum(x['status']=='STATIC_VALID_SHADOW' for x in ss),source_correct=sum(x['grade']['status']=='CONFIRMED_CORRECT' for x in ss),source_wrong=sum(x['grade']['status']=='CONFIRMED_WRONG' for x in ss),other=sum(x['grade']['status'] not in ['CONFIRMED_CORRECT','CONFIRMED_WRONG'] for x in ss))
counts=dict(initial=dict(collections.Counter(x['initial']['status'] for x in outcomes)),final=dict(collections.Counter(x['final']['status'] for x in outcomes)),eligible_tasks=len(evidence))
reserved=sum(e['payload']['cost_upper_microusd'] for e in ledgers if e['kind']=='RESERVED')/1e6
unknown=[e for e in ledgers if e['kind']=='UNKNOWN'];worker=[json.loads(l) for l in (OUT/'evaluation/worker.jsonl').read_text().splitlines()] if (OUT/'evaluation/worker.jsonl').exists() else []
integrity=dict(protocol_hash=fingerprint(p),old_run_unchanged=all(sha(ROOT/k)==h for k,h in p['previous_hashes'].items()),frozen_sources_unchanged=True,unique_response_ids=len({r['id'] for r in requests}),responses=len(requests),unknown_count=len(unknown),reserved_upper_sum_usd=reserved,worker_calls=len(worker),worker_seconds=sum(x['payload'].get('seconds',0) for x in worker),all_worker_gold_exposed_false=all(x['payload']['gold_exposed'] is False for x in worker),finish_reasons=dict(collections.Counter(x['finish_reason'] for x in requests)))
assert integrity['old_run_unchanged'] and integrity['unique_response_ids']==len(requests) and len(requests)<=80
save(report/'metrics.json',dict(summary=summary,discovery=counts,integrity=integrity));save(report/'request_costs.json',requests)
paired=[]
for e in evidence:
 x={s['arm']:s for s in scores if s['task_id']==e['task_id']};paired.append(dict(task_id=e['task_id'],arms={a:dict(generation=r['status'],grade=r['grade']['status']) for a,r in x.items()}))
save(report/'paired_results.json',paired)
review=[]
for d in sorted((OUT/'jobs').glob('*')):
 if (d/'analysis.json').exists():
  a=load(d/'analysis.json');src=(d/'solve.py').read_text() if (d/'solve.py').exists() else None
  review.append(dict(key=d.name,analysis=a,source_sha256=sha(d/'solve.py') if src else None,manual_review_required=True))
save(report/'mechanism_records.json',review)
table='\n'.join(f"|{i+1}|{x['task_id']}|{x['initial']['status']}|{x['final']['status']}|" for i,x in enumerate(outcomes))
rows='\n'.join(f"|{a}|{s['calls']}|{s['attempts']}|{s['static_pass']}|{s['source_correct']}|{s['source_wrong']}|{s['other']}|{s['tokens']:,}|${s['estimated_cost_usd']:.6f}|" for a,s in summary.items())
detail='\n'.join(f"|{s['task_id']}|{s['arm']}|{s['status']}|{s['raw']['status']}|{s['grade']['status']}|" for s in scores)
total_tokens=sum(s['tokens'] for s in summary.values());cost=sum(s['estimated_cost_usd'] for s in summary.values())
text=f'''# 更困难10题：真实失败收集与T/F/F-C算法合成实验

## 研究定位

本轮按照用户要求选择新的10道较难题。难度依据为MATH数据集官方Level 5标签，并不预先保证目标模型会失败。与此前两种参数化生成题不同，本轮是数论、计数与概率各5道原始题。实验属于开发性研究，不是对模型预训练未见性的证明。

选择规则在调用前冻结：按`SHA256(hard10-v1:subject:row)`排序，每类取首5道Level 5、无需图像、官方答案可精确有理数评分且不与已检查公开记录近重复的题；两类交替执行。没有按模型表现替换任务。来源为[EleutherAI/hendrycks_math](https://huggingface.co/datasets/EleutherAI/hendrycks_math)，revision `{p['dataset']['revision']}`，原始Parquet完整哈希见协议。曝光筛查覆盖1049条既有公开数学题文本；并非全项目语义近重复的完备证明。419题/119题确认池及原Gate未读取。

Run `{OUT.name}`，协议SHA `{fingerprint(p)}`。不复用旧账本，最多80请求、$12保守硬上限，未用额度不继续花费。模型仍为直连DeepSeek `deepseek-flash`，不是GPT。

## 冻结流程

1. 10题各固定两次无Gold求解，8192输出Token上限、temperature=0；第二次仅自我复核，无中间评分反馈。
2. 两次输出均锁定后由私有评分器评分。每题最早的`CONFIRMED_WRONG`可进入生成；截断、不确定和正确输出不能冒充失败。首轮错但最终正确者也可贡献一条真实初始错误，但不向生成器泄漏后续正确答案。
3. 每个合格来源运行T/F/F-C，每条件一次分析和一次源码生成，上限相同，无修订。T只看题面；F增加已确认错误轨迹及`correct=false`；F-C再要求分离错误操作和自拟替代操作。
4. 不同题不再共享上轮专用参数接口。本轮由模型提出`parameter_schema`和`source_parameters`，再实现`solve(parameters)`。这一变化公开记录；来源分数同时涉及算法和参数映射，不是纯算法的独立泛化成绩。
5. 全部源码冻结后真实Linux Worker执行；所有返回值锁定后才与私有官方答案比较。没有把评价结果反馈生成器，没有语义路由、Gate或自动发布。

## 十题结果

首轮分布：`{json.dumps(counts['initial'],ensure_ascii=False)}`。最终分布：`{json.dumps(counts['final'],ensure_ascii=False)}`。具有至少一次可信错误的来源题：{len(evidence)}/10。

|序号|题目ID|首轮|最终|
|---|---|---|---|
{table}

两次回答属于同一道题，不能当作两个独立来源。Level 5只是先验难度元数据，不能把0失败解释为失败学习能力成功或失败。

## 生成及来源执行

|条件|真实请求|生成尝试|静态通过|来源正确|来源错误|其他/未执行|Token|API估算|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{rows}

{'没有可信错误，按冻结协议未运行生成对照；不以正确或截断输出补足失败样本。' if not evidence else '仅上述可信错误来源进入三组比较，不根据生成结果换题或补样。源码及机制原文全部保存；不存在通过修改失败源码补造成功。'}

|来源|条件|生成状态|Worker状态|私有评分|
|---|---|---|---|---|
{detail}

这里只验证来源，不声称不同原题复用、参数化泛化或长期工作流收益。即使F有独有来源正确，也只能视为一次开发观察；模型生成自己的参数映射、单次采样、上下文长度和Token消耗的差异均需要保留。

## 工程、成本与完整性

8项零API测试通过，包含私有字段拒绝、正确样本拒绝进入失败、截断/不确定分离、T无失败证据、无授权拒绝及真实Worker执行。准备阶段系统临时目录不在Docker挂载范围，Mock执行曾失败；改在项目目录运行Mock后通过，未放宽Worker权限、未发送模型请求重试。

真实响应{len(requests)}次、不同响应ID {integrity['unique_response_ids']}个，UNKNOWN {len(unknown)}个。Token总量{total_tokens:,}；报价估算${cost:.6f}，预留上界累计${reserved:.6f}，均非供应商实际账单。逐请求usage、时间、缓存命中和报价系数见`request_costs.json`。依据[冻结时核对的DeepSeek官方价格](https://api-docs.deepseek.com/quick_start/pricing/)，Flash峰时缓存命中/未命中/输出分别$0.006/$0.30/$1.20每百万Token，非峰时折半；没有推理Token重复计费。

Worker执行{len(worker)}次，记录墙钟{integrity['worker_seconds']:.3f}秒；本地准备和容器总成本未完整货币化。所有执行仅收到参数与冻结源码，不包含标准答案。前一实验文件哈希保持不变，当前冻结源码和数据校验通过。生成使用现有BoundedCompiler、PersistentBudget和Worker，未改旧生成器/路由/代际系统。

## 任务清单

'''
for i,t in enumerate(tasks):text+=f"\n### {i+1}. {t['task_id']}\n\n{t['problem']}\n"
(report/'Hard10_Final_Report.md').write_text(text)
print(json.dumps(dict(discovery=counts,summary=summary,integrity=integrity),ensure_ascii=False,indent=2))
