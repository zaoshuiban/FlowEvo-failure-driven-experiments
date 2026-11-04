"""Post-lock descriptive/paired analysis. No model requests or registry mutations."""
import json,math,collections
from run_math_auto100 import OUT,read,save

def events(p):return [json.loads(x) for x in p.read_text().splitlines()]
def cost(u):
 hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit)
 return (hit*.006+miss*.3+u['completion_tokens']*1.2)/1e6

def main():
 complete=(OUT/'COMPLETE.json').exists();stop=read(OUT/'STOP.json') if (OUT/'STOP.json').exists() else None
 rows=read(OUT/'results.json');roles=read(OUT/'roles.json');testids={x['task_id'] for x in roles['Test']};outcomes={};allraw=[];models=collections.Counter()
 for path in list(OUT.rglob('requests.jsonl'))+list(OUT.rglob('provider.jsonl')):
  for e in events(path):
   if e['kind']!='RAW_RESPONSE':continue
   raw=e['payload']['response'];u=raw['usage'];allraw.append(dict(path=str(path.relative_to(OUT)),usage=u,peak_cost=cost(u),model=raw['model'],response_id=raw.get('id')));models[raw['model']]+=1
 for arm in ['Discovery','G','T','F']:
  rr=[x for x in rows if x['arm']==arm];raw=[x for x in allraw if x['path'].startswith('episodes/') and x['path'].split('/')[-2]==arm]
  outcomes[arm]=dict(completed=len(rr),correct=sum(x['grade']['correct'] is True for x in rr),statuses=dict(collections.Counter(x['grade']['status'] for x in rr)),model_calls=sum(x['locked']['model_calls'] for x in rr),input_tokens=sum(x['locked']['input_tokens'] for x in rr),output_tokens=sum(x['locked']['output_tokens'] for x in rr),operator_attempts=sum(len(x['locked']['operator_events']) for x in rr),operator_applied=sum(x['locked']['selection']=='first_applied_operator' for x in rr),fallback=sum(x['locked']['fallback'] for x in rr),peak_cost=sum(x['peak_cost'] for x in raw),seconds=sum(x['locked']['seconds'] for x in rr))
 pairwise={}
 for arm,base in [('F','G'),('F','T'),('T','G')]:
  a={x['task_id']:x for x in rows if x['arm']==arm};b={x['task_id']:x for x in rows if x['arm']==base};ids=sorted(set(a)&set(b));wins=sum(a[i]['grade']['correct'] is True and b[i]['grade']['correct'] is not True for i in ids);loss=sum(b[i]['grade']['correct'] is True and a[i]['grade']['correct'] is not True for i in ids);discord=wins+loss
  # Non-pass outcomes include delivery/unverified; mathematical-error categories retained above.
  pairwise[arm+'-'+base]=dict(pairs=len(ids),arm_only_pass=wins,base_only_pass=loss,both_pass=sum(a[i]['grade']['correct'] is True and b[i]['grade']['correct'] is True for i in ids),neither_pass=sum(a[i]['grade']['correct'] is not True and b[i]['grade']['correct'] is not True for i in ids),exact_mcnemar_p=min(1.,2*sum(math.comb(discord,k) for k in range(min(wins,loss)+1))/2**discord) if discord else 1.)
 learning=read(OUT/'learning_results.json') if (OUT/'learning_results.json').exists() else [];failures=read(OUT/'failures.json') if (OUT/'failures.json').exists() else [];mechanisms={}
 for arm in ['T','F']:
  path=OUT/arm/'pipeline/learning.jsonl';ev=events(path) if path.exists() else [];review=[x['payload'] for x in ev if x['kind']=='DEVELOPMENT_REVIEW'];mechanisms[arm]=dict(hypotheses=[x['payload'] for x in ev if x['kind']=='MECHANISM_HYPOTHESIS'],reviews=[dict(static=x['static'],development_passed=x['development_passed'],code_sha256=x['artifact']['code_sha256'],source_correct=sum(d.get('role')=='Source' and d.get('status')=='APPLIED' and d.get('correct') for d in x['diagnostics']),design_correct=sum(d.get('role')=='Design' and d.get('status')=='APPLIED' and d.get('correct') for d in x['diagnostics'])) for x in review],generation_calls=sum(x['path'].startswith(arm+'/') for x in allraw),generation_peak_cost=sum(x['peak_cost'] for x in allraw if x['path'].startswith(arm+'/')))
 budgetevents=[e for p in OUT.rglob('budget.jsonl') for e in events(p)];unknown=sum(x['kind']=='UNKNOWN' for x in budgetevents);tools=[e for e in budgetevents if e['kind']=='SETTLED' and 'tool_milliseconds' in e['payload']]
 summary=dict(status='COMPLETE' if complete else 'STOPPED' if stop else 'RUNNING',stop=stop,planned_unique=100,roles={k:len(v) for k,v in roles.items()},outcomes=outcomes,pairwise=pairwise,confirmed_final_failure_tasks=len(failures),learning=learning,mechanisms=mechanisms,total_calls=len(allraw),total_tokens=sum(x['usage']['total_tokens'] for x in allraw),estimated_peak_cost=sum(x['peak_cost'] for x in allraw),estimated_offpeak_cost=sum(x['peak_cost']/2 for x in allraw),invoice_cost=None,actual_models=dict(models),unknown=unknown,tool_settlements=len(tools))
 summary['research_status']='NO_DISCOVERY_FAILURE_LEARNING_NOT_ACTIVATED' if not failures else ('NO_OPERATOR_INTERVENTION' if outcomes['F']['operator_applied']==0 else 'INTERVENTION_OBSERVED_REQUIRES_PAIRED_REVIEW')
 summary['actually_solved_unique_tasks']=len({x['task_id'] for x in rows})
 save(OUT/'summary.json',summary);save(OUT/'request_costs.json',allraw)
 table='\n'.join(f"|{arm}|{v['correct']}/{v['completed']}|{v['model_calls']}|{v['input_tokens']+v['output_tokens']}|{v['operator_applied']}|${v['peak_cost']:.6f}|" for arm,v in outcomes.items())
 conclusion='F没有实际算子介入，因此任何F/G/T正确率差异都不能归因于已学算子；学习支出保留。' if outcomes['F']['operator_applied']==0 else '观察到F介入；需结合逐题配对、T对照、来源与全部成本判断增量，不能只看总正确率。'
 text=f'''# 100题失败驱动自动学习实验报告

状态：**{summary['status']}**；研究状态：**{summary['research_status']}**。{conclusion}

实际完成模型求解的不同任务：{summary['actually_solved_unique_tasks']}；100是角色冻结总数，未触发的Design/Gate不得宣称已完成算子验证。

## 实验定义与冻结

100个不同MATH记录：20 Discovery、10 Design、10 Gate、60 Test。最终配对样本量是60，不是100。Level5、7数学类别、只保留能精确比较的有理数官方答案；按哈希固定顺序选择，排除清单中已曝光文本及90%数字掩码近重复，不按目标模型表现选题。不访问旧独立确认池。记录级去重不等于完整竞赛谱系审计；模型预训练曝光不可排除。

协议SHA：`{read(OUT/'freeze.json')['sha256']}`。全程不用手工算子，不导入历史Experimental。DeepSeek同时用于基础求解和两组生成，与此前用户指定DeepSeek通道一致；不是GPT实验。

G原生FlowEvo；T只看相同来源题面；F额外看真实错误输出/轨迹及失败状态。两组最多各一次归纳、一次源码生成，无修订；来源为最早6个终局可信错误的不同Discovery任务。相同接口、模型、输出上限和安全Worker。F上下文更长，没有等token负控制，且每组仅一个生成样本，不能声称一般性的失败知识因果规律。

来源和Design通过，才允许一次Gate；Gate不回流学习。60题比较前锁定学习与注册表。不匹配或无准入算子则原生两次求解；G/T/F均真实独立请求，不复用G输出冒充其他组。

## 实际结果

|组别|正确/已完成|模型请求|输入+输出Tokens|算子实际应用|峰价API估算|
|---|---:|---:|---:|---:|---:|
{table}

最终可信数学失败来源：{len(failures)}题。截断、无法判断与错误分开记录，UNVERIFIED不进入失败池。实际模型：`{dict(models)}`。

学习状态：`{[(x['arm'],x['status']) for x in learning]}`。

配对结果：
```json
{json.dumps(pairwise,ensure_ascii=False,indent=2)}
```

指标“非通过”含截断与未验证；不将这些一律称为数学推理错误，细分见summary.json。若学习阶段未通过，Design/Gate保留未执行状态；不能把100个冻结题目写成100个都进行了有效算子评价。

## 完整成本

全部真实响应{len(allraw)}次，{summary['total_tokens']}tokens；包含Discovery、T/F归纳/生成和三组最终求解。按保存官方峰价估算${summary['estimated_peak_cost']:.9f}，非峰价${summary['estimated_offpeak_cost']:.9f}；实际账单不可得。硬上限20美元、404请求。UNKNOWN={unknown}。保守账本占用不是实付。

生成费用按T/F分别保存，不因拒绝或失败而删除。总成本不可直接当作任一单组部署成本：Discovery是共享准备，G/T/F是实验对照开销；分析F单组时须另加其学习成本和共享准备分摊。Worker及人工研究准备成本未货币化，不能只凭API差额宣称完整回本。

## 研究判断

{conclusion} 数量增加本身不能证明收益。只有来源、独立准入、真实匹配、实际介入、同题成功/退化、T对照及全成本形成一致证据，才支持当前实现的正向结论。

全部原始请求、响应、账本、源码、假设、失败证据、角色清单与回答锁定记录保存在本Run。旧实验与手工夹具权限不变。没有根据Test结果追加候选、改提示或替换题目。
'''
 (OUT/'Final_Report.md').write_text(text)
 print(json.dumps({k:summary[k] for k in ['status','total_calls','total_tokens','estimated_peak_cost','unknown','outcomes','learning','pairwise']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
