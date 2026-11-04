import json
from run_math_real_cross_record import OUT,load,save
from code_math.no_gold import solver_messages,PublicMathTask

def records(p):return [json.loads(x) for x in p.read_text().splitlines()]
def cost(raw):
 u=raw['usage'];hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit)
 return (hit*.006+miss*.3+u['completion_tokens']*1.2)/1e6
assert (OUT/'COMPLETE.json').exists()
r=load('results.json');ev=records(OUT/'requests.jsonl');raw=[x['payload'] for x in ev if x['kind']=='RAW_RESPONSE'];w=records(OUT/'worker.jsonl');registry=records(OUT/'registry.jsonl')
def totals(arm):
 rows=[x for x in r if x['arm']==arm];req=[x for x in raw if '/'+arm+'/' in x['request_id']]
 return dict(tasks=len(rows),correct=sum(x['grade']['correct'] is True for x in rows),model_calls=sum(x['locked']['model_calls'] for x in rows),input_tokens=sum(x['locked']['input_tokens'] for x in rows),output_tokens=sum(x['locked']['output_tokens'] for x in rows),cost_upper_peak_usd=sum(cost(x['response']) for x in req),seconds=sum(x['locked']['seconds'] for x in rows),applied=sum(x['locked']['selection']=='first_applied_operator' for x in rows),fallback=sum(x['locked']['fallback'] for x in rows))
g,o,gate=totals('G'),totals('O'),totals('Gate-G')
pairs=[]
for t in load('tasks.json'):
 a=next(x for x in r if x['arm']=='G' and x['task_id']==t['task_id']);b=next(x for x in r if x['arm']=='O' and x['task_id']==t['task_id']);pairs.append(dict(task_id=t['task_id'],g_correct=a['grade']['correct'],o_correct=b['grade']['correct'],applied=b['locked']['selection']=='first_applied_operator',g_calls=a['locked']['model_calls'],o_calls=b['locked']['model_calls']))
# Verify actual wire is exactly the public no-gold controller projection, including only own prior response.
wires={x['payload']['request_id']:x['payload']['wire'] for x in ev if x['kind']=='NO_GOLD_REQUEST'}
public={t['task_id']:t['problem'] for t in load('tasks.json')};public.update({'gate-'+str(i):c['proposal']['problem'] for i,c in enumerate(load('gate_cases.json')[:3])})
for row in r:
 l=row['locked'];previous=None
 for i,response in enumerate(l['responses']):
  wire=wires[l['episode_id']+'/s'+str(i)];assert wire['messages']==solver_messages(PublicMathTask(row['task_id'],public[row['task_id']]),previous,profile='concise-v1');previous=response['text']
summary=dict(status='REAL_PAIRED_ENGINEERING_PASS',autonomously_learned=False,operator_origin='HUMAN_ENGINEERING',future_G=g,future_O=o,gate_generic=gate,pairs=pairs,total_real_calls=len(raw),total_tokens=sum(x['response']['usage']['total_tokens'] for x in raw),total_peak_cost=sum(cost(x['response']) for x in raw),worker_calls=len(w),worker_seconds=sum(x['payload']['seconds'] for x in w),wire_public_projection_verified=True,unknown=sum(x['kind']=='UNKNOWN' for x in records(OUT/'solver_budget.jsonl')),trial_reserved=sum(x['kind']=='V3_TRIAL_RESERVED' for x in registry))
save(OUT/'summary.json',summary)
lines='\n'.join('| '+x['task_id']+' | '+str(x['g_correct'])+' | '+str(x['o_correct'])+' | '+str(x['applied'])+' | '+str(x['g_calls'])+' / '+str(x['o_calls'])+' |' for x in pairs)
(OUT/'Final_Report.md').write_text(f'''# 手工算子的真实跨MATH记录自动复用验收

**REAL_PAIRED_ENGINEERING_PASS**。手工算法与匹配器，真实DeepSeek求解，真实Linux Worker，现有Controller/注册表自动调用。不是自动学习成功，不是失败驱动学习增量的证明。

## 协议与来源

协议SHA：`{load('freeze.json')['sha256']}`。算法/契约SHA：`{load('artifact.json')['code_sha256']}`。

本地官方MATH train/algebra固定Parquet，revision `{load('protocol.json')['source_revision']}`，行226、539、690、39分别为奇数区间求和、三位整数求和、倍数求和及二次关系求根后求和。保留原始题面与官方解答的私有评分，不是自行改参数后当作新原题。它们是不同数据记录；未获取完整竞赛来源URL，不能进一步保证竞赛谱系独立。

题目由公开题面人工选择，适用契约也根据这些题面人工编写。它们是**已见工程开发题**，不是独立未见泛化确认。手工接口覆盖三个明确题面模板，其余拒绝；没有按题ID或标准答案返回常量。主计算是通用等差数列求和。此项验证的是自动执行，不是自主生成。

先冻结源码、题目、预算，再读取官方solution用于私有评分；任何模型或Worker输入均无官方答案。真实模型请求逐条与原生无Gold消息构造器比对通过。G与O回退使用相同模型、4096输出上限、两次固定求解/自查、温度和提示。

## 注册与验收

开发3个支持题计算正确、1个负例拒绝。不同参数Gate同样3/3及1/1，并真实运行Generic配对。随后通过现有VersionGate登记Experimental，授权4个未来任务ID与4次调用，先保留额度再执行；没有直接写入伪造准入事件。四次后额度耗尽，实际检查不再可调用。全部权限仅存在本Run隔离注册表。

Gate是人工构造工程数据，不是独立数学研究证据。此处达标不代表旧真实模型候选已获得权限。

## 后续真实配对结果

| 原始记录 | G正确 | O正确 | 算子实际应用 | G/O模型请求 |
|---|---|---|---|---|
{lines}

| 指标 | G | O |
|---|---:|---:|
| 正确 | {g['correct']}/{g['tasks']} | {o['correct']}/{o['tasks']} |
| 模型请求 | {g['model_calls']} | {o['model_calls']} |
| 输入tokens | {g['input_tokens']} | {o['input_tokens']} |
| 输出tokens | {g['output_tokens']} | {o['output_tokens']} |
| 峰价API估算美元 | {g['cost_upper_peak_usd']:.9f} | {o['cost_upper_peak_usd']:.9f} |

收益只解释为这批已选工程任务上观察到的调用与API消耗差异；没有自动学习收益或总体性能结论。最后一题由算子拒绝，原生流程真实回退。G/O回退独立采样，输出与tokens差异可能来自模型波动。

## 完整本轮成本与限制

共{len(raw)}次真实响应、{summary['total_tokens']}tokens；保存官方报价，按峰价估算${summary['total_peak_cost']:.9f}，若适用非峰报价为一半；不是实际账单。未知请求{summary['unknown']}次，不重发。硬预算2美元，上限16请求。

上述总额包括Gate的{gate['model_calls']}次Generic请求（${gate['cost_upper_peak_usd']:.9f}峰价），并非只报告未来O。Worker{len(w)}次、累计{summary['worker_seconds']:.3f}秒。本地执行与人工设计时间未货币化；没有生成API，但不能把手工设计成本当作零成本学习。因此不能给出完整经济回本结论。

本轮没有自主归纳、没有真实学习源码、没有T/F生成对照，不能宣称“经过验证的自动失败学习跨原题收益”。它确认了：在人工提供一个有效算子后，现有注册、准入、白名单、自动跨记录执行、真实回退、成本与私有评分链路能够工作。下一步研究缺口仍是让学习器产出同样可用的能力与契约，而不是再次证明这条工程链路。
''')
print(json.dumps(summary,ensure_ascii=False,indent=2))
