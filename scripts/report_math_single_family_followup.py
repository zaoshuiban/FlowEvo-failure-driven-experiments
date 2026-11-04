"""Report all attempts, including mixed-family failure, without outcome selection."""
import json,collections,math
from run_math_single_family_followup import OUT,PARENT,load,save
from failure_evo.evidence import EvidenceStore

def ev(p):return EvidenceStore(p).records()
def price(u):return (u.get('prompt_cache_hit_tokens',0)*.006+u.get('prompt_cache_miss_tokens',u['prompt_tokens']-u.get('prompt_cache_hit_tokens',0))*.3+u['completion_tokens']*1.2)/1e6
def main():
 rows=load('results.json') if (OUT/'results.json').exists() else [];learning=load('learning_results.json') if (OUT/'learning_results.json').exists() else [];raw=[]
 for path in list(OUT.rglob('requests.jsonl'))+list(OUT.rglob('provider.jsonl')):
  for e in ev(path):
   if e['kind']=='RAW_RESPONSE':
    response=e['payload']['response'];raw.append(dict(path=str(path.relative_to(OUT)),model=response['model'],id=response.get('id'),usage=response['usage'],peak_cost=price(response['usage'])))
 outcomes={};mechanisms={};labels={x['task_id']:x for x in load('private.json')};primary=load('protocol.json')['selected_family']
 for arm in ['G','T','F']:
  rr=[x for x in rows if x['arm']==arm];rrraw=[x for x in raw if x['path'].startswith('episodes/') and x['path'].split('/')[-2]==arm]
  outcomes[arm]=dict(completed=len(rr),correct=sum(x['grade']['correct'] is True for x in rr),statuses=dict(collections.Counter(x['grade']['status'] for x in rr)),primary_correct=sum(x['grade']['correct'] is True and labels[x['task_id']]['family']==primary for x in rr),primary_completed=sum(labels[x['task_id']]['family']==primary for x in rr),applied=sum(x['locked']['selection']=='first_applied_operator' for x in rr),applied_correct=sum(x['locked']['selection']=='first_applied_operator' and x['grade']['correct'] is True for x in rr),fallback=sum(x['locked']['fallback'] for x in rr),model_calls=sum(x['locked']['model_calls'] for x in rr),tokens=sum(x['locked']['input_tokens']+x['locked']['output_tokens'] for x in rr),peak_cost=sum(x['peak_cost'] for x in rrraw))
 for arm in ['T','F']:
  pe=ev(OUT/arm/'pipeline/learning.jsonl');reviews=[x['payload'] for x in pe if x['kind']=='DEVELOPMENT_REVIEW'];gate=[x['payload'] for x in pe if x['kind']=='GATE_DECISION'];hyp=[x['payload'] for x in pe if x['kind']=='MECHANISM_HYPOTHESIS']
  mechanisms[arm]=dict(hypotheses=hyp,review_summary=[dict(static=r['static'],passed=r['development_passed'],code_sha256=r['artifact']['code_sha256'],source_correct=sum(x.get('role')=='Source' and x.get('status')=='APPLIED' and x.get('correct') is True for x in r['diagnostics']),design_correct=sum(x.get('role')=='Design' and x.get('status')=='APPLIED' and x.get('correct') is True for x in r['diagnostics'])) for r in reviews],gate_passed=bool(gate and gate[-1]['gate_passed']),generation_calls=sum(x['path'].startswith(arm+'/') for x in raw),generation_peak_cost=sum(x['peak_cost'] for x in raw if x['path'].startswith(arm+'/')))
 pairwise={}
 for arm,base in [('F','G'),('F','T'),('T','G')]:
  aa={x['task_id']:x for x in rows if x['arm']==arm};bb={x['task_id']:x for x in rows if x['arm']==base};ids=set(aa)&set(bb);win=sum(aa[i]['grade']['correct'] is True and bb[i]['grade']['correct'] is not True for i in ids);loss=sum(bb[i]['grade']['correct'] is True and aa[i]['grade']['correct'] is not True for i in ids);n=win+loss
  pairwise[arm+'-'+base]=dict(pairs=len(ids),arm_only=win,base_only=loss,both=sum(aa[i]['grade']['correct'] is True and bb[i]['grade']['correct'] is True for i in ids),exact_mcnemar_p=min(1,2*sum(math.comb(n,k) for k in range(min(win,loss)+1))/2**n) if n else 1.)
 ledger=[x for p in OUT.rglob('budget.jsonl') for x in ev(p)];tool=[x for x in ledger if x['kind']=='SETTLED' and 'tool_milliseconds' in x['payload']];summary=dict(status=load('COMPLETE.json')['status'] if (OUT/'COMPLETE.json').exists() else 'STOPPED' if (OUT/'STOP.json').exists() else 'RUNNING',source_failures_imported=load('protocol.json')['source_count'],learning=learning,mechanisms=mechanisms,outcomes=outcomes,pairwise=pairwise,new_real_calls=len(raw),new_tokens=sum(x['usage']['total_tokens'] for x in raw),new_peak_cost=sum(x['peak_cost'] for x in raw),new_offpeak_cost=sum(x['peak_cost']/2 for x in raw),unknown=sum(x['kind']=='UNKNOWN' for x in ledger),worker_tool_calls=len(tool),worker_tool_ms=sum(x['payload']['tool_milliseconds'] for x in tool))
 if (PARENT/'summary.json').exists():
  parent=json.loads((PARENT/'summary.json').read_text());summary['combined_all_attempts']=dict(calls=parent['total_calls']+len(raw),tokens=parent['total_tokens']+summary['new_tokens'],peak_cost=parent['estimated_peak_cost']+summary['new_peak_cost'])
 save(OUT/'summary.json',summary);save(OUT/'request_costs.json',raw)
 table='\n'.join(f"|{a}|{x['correct']}/{x['completed']}|{x['applied']}|{x['applied_correct']}|{x['fallback']}|{x['model_calls']}|{x['tokens']}|" for a,x in outcomes.items())
 if not outcomes['F']['applied']:conclusion='未观察到F实际算子介入，不能证明失败驱动自动学习收益。'
 elif outcomes['F']['correct']<=outcomes['T']['correct'] or (outcomes['F']['primary_correct']<=outcomes['T']['primary_correct'] and outcomes['F']['applied_correct']<=outcomes['T']['applied_correct']):conclusion='F出现真实自动生成与复用，但没有观察到相对T的正确数增量；不能将可执行工具的收益等同于失败证据的独立价值。'
 else:conclusion='观察到F相对T的有限正确数增量；仅为单候选、人工单族数据上的探索信号，必须结合配对和成本，不能宣布一般性证明。'
 text=f'''# 单族失败驱动自动学习：有界跟进实验

状态：**{summary['status']}**。{conclusion}

## 为什么另开一轮

第一轮人工100题发现10个可信错误，但混合题族的T/F均选择HYPOTHESIS_ONLY。此负结果及全部费用保留在父Run。现在仅做一次公开记录的开发性跟进：取最早可信失败所属题族（digits），按时间取同族5条真实终局错误。人工提供的是题族分组与Oracle，**没有编写或注入候选算法**。

改变了两项设计：单族分组；消除题面控制组的失败池选样提示。因此这不是“仅改变分组”的因果消融，也不能将两个Run的好坏直接归因于分组。没有继续按生成结果换族。

## 冻结与隔离

协议SHA：`{load('freeze.json')['sha256']}`。T/F相同DeepSeek模型、接口与最多两次请求（归纳+源码），不修订。T只有相同公开题面；F额外看到合法错误轨迹和二值失败反馈。原始错误记录从父Run逐字导入，不再次求解或改写。

开发/Gate使用父Run已经冻结但从未用于模型生成或候选验证的各10题。30个新确认实例在调用前用新种子冻结，24个同族、6个其他族控制；与父100题参数哈希不重叠。所有答案由独立宿主参考交叉检查，不传给模型或Worker。

这仍是人工合成分布的**同机制参数迁移**，不是不同原始数学题的泛化。公开参数已结构化，降低了自然语言解析难度；不能声称已解决此前任意题面的语义路由问题。

## 自动生成、验证与准入

状态：`{[(x['arm'],x['status']) for x in learning]}`。

实际模型假设、源码、静态诊断、来源和开发验证、一次Gate决定分别保存在T/F/pipeline。只在源码通过既有来源/Design/拒绝检查和独立Gate后才注册Experimental；否则保持Shadow。若两组都不合格，预冻结代码规定不运行30题无干预比较。

## 新确认结果

|组别|正确/完成|实际应用|应用后正确|回退|模型请求|Tokens|
|---|---:|---:|---:|---:|---:|---:|
{table}

配对：
```json
{json.dumps(pairwise,ensure_ascii=False,indent=2)}
```

只比较锁定答案；不能在算子输出错误后利用Gold追加救援。算子拒绝/异常按相同无Gold原生流程回退。最终确认不用于重新生成或修订。正确数包含原生回退成功，实际算子应用成功另列。

## 全成本与证据强度

本跟进新增{len(raw)}次真实请求、{summary['new_tokens']}tokens，峰价估算${summary['new_peak_cost']:.9f}，非峰价${summary['new_offpeak_cost']:.9f}，不是账单。Worker工具调用{len(tool)}次、计量耗时{summary['worker_tool_ms']/1000:.3f}秒。未知请求{summary['unknown']}。人工数据与参考实现成本未货币化。

父Run失败发现与无增量尝试的成本不能删除，联合计量见summary.json的combined_all_attempts；不能只报最后一轮费用。后续G/T/F真实请求独立执行，因而回退部分仍有模型随机性。每组仅一个生成样本，同族参数并非独立机制重复；即使p较小，也不构成广泛机制有效性的充分证据。

{conclusion}
'''
 (OUT/'Final_Report.md').write_text(text)
 print(json.dumps({k:summary[k] for k in ['status','new_real_calls','new_tokens','new_peak_cost','unknown','outcomes','pairwise']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
