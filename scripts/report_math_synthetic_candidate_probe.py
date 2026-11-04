"""Read-only audit/report; never supplies scoring evidence to a model."""
import json,hashlib,collections,math
from pathlib import Path
import run_math_synthetic_candidate_probe as m
from failure_evo.evidence import EvidenceStore
from failure_evo.persistent_budget import PersistentBudget
from code_math.no_gold import PublicMathTask,solver_messages

def events(p):return EvidenceStore(p).records()
def price(u):return (u.get('prompt_cache_hit_tokens',0)*.006+u.get('prompt_cache_miss_tokens',u['prompt_tokens']-u.get('prompt_cache_hit_tokens',0))*.3+u['completion_tokens']*1.2)/1e6

def main():
 p=m.load('protocol.json');roles=m.load('roles.json');bundle=m.load('bundle.json');checks=[]
 def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
 check('protocol hash',m.fingerprint(p)==m.load('freeze.json')['sha256'])
 check('runtime sources unchanged',all(m.sha(m.ROOT/f)==h for f,h in p['source_hashes'].items()))
 check('source events unchanged',m.sha(m.PARENT/'selected_bundle.json')==p['parent_bundle_hash'] and bundle==json.load(open(m.PARENT/'selected_bundle.json')))
 check('100 private references agree',len(m.load('oracle_acceptance.json'))==100 and all(r['agreement'] for r in m.load('oracle_acceptance.json')))
 check('no role intersection',len({x['task_id'] for k in ['Source','Design','Gate','Test'] for x in roles[k]})==105)
 raw=[];mechanisms=[]
 for path in list(m.OUT.rglob('provider.jsonl'))+list(m.OUT.rglob('requests.jsonl')):
  for e in events(path):
   if e['kind']=='RAW_RESPONSE':
    r=e['payload']['response'];raw.append(dict(path=str(path.relative_to(m.OUT)),id=r.get('id'),model=r.get('model'),usage=r['usage'],peak_cost=price(r['usage']),at=e['at']))
 seenids=[r['id'] for r in raw if r['id']];check('unique provider response ids',len(seenids)==len(set(seenids)))
 for spec in p['order']:
  name=f"{spec['pair']}-{spec['arm']}";rows=events(m.OUT/name/'pipeline/learning.jsonl');pr=events(m.OUT/name/'provider.jsonl')
  wires=[x['payload']['wire'] for x in pr if x['kind']=='SEND_STARTED']
  for i,w in enumerate(wires):
   v=json.loads(w['messages'][1]['content']);view=v['evidence']
   check(name+' only F sees failures '+str(i),('observations' in view)==(spec['arm']=='F'))
   check(name+' identical public questions '+str(i),view['questions']==[dict(problem=x['task']['problem']) for x in bundle['events']])
   check(name+' no target/gold keys '+str(i),not any(k in json.dumps(v) for k in ['gold_answer','candidate-probe-','source_diagnostics']))
  hyp=[r['payload']['content'] for r in rows if r['kind']=='MECHANISM_HYPOTHESIS'];rev=[r['payload'] for r in rows if r['kind']=='DEVELOPMENT_REVIEW']
  record=dict(name=name,hypothesis=hyp[-1] if hyp else None,generated=bool(rev),static=None,source_correct=0,design_correct=0,source_statuses={},design_statuses={})
  if rev:
   v=rev[0];a=v['artifact'];code=Path(a['source_path']).read_text();record.update(static=v['static'],code_sha256=a['code_sha256'],source_path=a['source_path'])
   rr=[r['payload']['response'] for r in pr if r['kind']=='RAW_RESPONSE' and m.fingerprint(r['payload']['response'])==a['response_sha256']]
   check(name+' exact model source',len(rr)==1 and json.loads(rr[0]['choices'][0]['message']['content'])['code']==code and hashlib.sha256(code.encode()).hexdigest()==a['code_sha256'])
   for role in ['Source','Design']:
    ds=[d for d in v['diagnostics'] if d['role']==role and d.get('reason')!='ENGINEERING_REFUSAL_CONTROL']
    record[role.lower()+'_correct']=sum(x['correct'] for x in ds);record[role.lower()+'_statuses']=dict(collections.Counter(x['status'] for x in ds))
   if (m.OUT/name/'gate.json').exists():
    gs=json.load(open(m.OUT/name/'gate.json'));record['gate_correct']=sum(x['correct'] for x in gs);record['gate_statuses']=dict(collections.Counter(x['status'] for x in gs))
  check(name+' no online admission',not any(r['kind']=='MATH_EXPERIMENTAL' for r in events(m.OUT/name/'registry.jsonl')))
  mechanisms.append(record)
 states=[];cap=0;charged=0;worker_calls=0;worker_ms=0
 for path in m.OUT.rglob('budget.jsonl'):
  b=PersistentBudget.__new__(PersistentBudget);b.path=path
  with b._locked() as rr:
   ss,_=b._state(rr);states+=list(ss.values());t=b._totals(rr);cfg=rr[0]['payload']['config'];check('ledger bound '+str(path),t['cost']<=cfg['max_cost_microusd']);cap+=cfg['max_cost_microusd'];charged+=t['cost']
   tools=[x for x in rr if x['kind']=='SETTLED' and 'tool_milliseconds' in x['payload']];worker_calls+=len(tools);worker_ms+=sum(x['payload']['tool_milliseconds'] for x in tools)
 check('no unresolved requests',all(s['status']=='settled' for s in states));check('real response bound',len(raw)<=p['max_requests'])
 results=m.load('results.json') if (m.OUT/'results.json').exists() else [];qualification=m.load('qualification.json') if (m.OUT/'qualification.json').exists() else []
 outcomes={};pairwise={}
 for spec in p['order']:
  name=f"{spec['pair']}-{spec['arm']}";rs=[next(x for x in r['candidates'] if x['name']==name) for r in results]
  outcomes[name]=dict(completed=len(rs),correct=sum(x['primary_correct'] for x in rs),applied=sum(x['used'] for x in rs),fallback=sum(x['fallback'] for x in rs),qualified=next((x['qualified'] for x in qualification if x['name']==name),False))
 for i in range(3):
  wins=loss=0
  for r in results:
   f=next(x for x in r['candidates'] if x['name']==str(i)+'-F');t=next(x for x in r['candidates'] if x['name']==str(i)+'-T')
   wins+=f['primary_correct'] and not t['primary_correct'];loss+=t['primary_correct'] and not f['primary_correct']
  n=wins+loss;pv=min(1,2*sum(math.comb(n,k) for k in range(min(wins,loss)+1))/2**n) if n else 1
  pairwise[str(i)]=dict(pairs=len(results),F_only=wins,T_only=loss,exact_mcnemar_p=pv)
 for r in results:
  g=r['generic'];l=g['locked'];check('G lock '+r['task_id'],m.fingerprint({k:v for k,v in l.items() if k!='locked_sha256'})==l['locked_sha256'])
  t=next(t for t in roles['Test'] if t['task_id']==r['task_id']);ev=events(m.OUT/'G'/r['task_id']/'requests.jsonl');wire={x['payload']['request_id']:x['payload']['wire'] for x in ev if x['kind']=='NO_GOLD_REQUEST'};prev=None
  for j,response in enumerate(l['responses']):check('public G request '+r['task_id']+'/'+str(j),wire[l['episode_id']+'/s'+str(j)]['messages']==solver_messages(PublicMathTask.parse(t),prev,profile='concise-v1'));prev=response['text']
 status=m.load('COMPLETE.json')['status'] if (m.OUT/'COMPLETE.json').exists() else 'STOPPED' if (m.OUT/'STOP.json').exists() else 'RUNNING'
 check('source code lock unchanged',not (m.OUT/'CODE_LOCK.json').exists() or m.load('CODE_LOCK.json')['learning_sha256']==m.sha(m.OUT/'learning.json'))
 check('qualification locked',not (m.OUT/'PRE_TEST_LOCK.json').exists() or m.load('PRE_TEST_LOCK.json')['qualification_sha256']==m.sha(m.OUT/'qualification.json'))
 summary=dict(status=status,historical_real_failures=5,designed_new_instances=100,test_completed=len(results),real_requests=len(raw),tokens=sum(r['usage']['total_tokens'] for r in raw),peak_estimated_usd=sum(r['peak_cost'] for r in raw),offpeak_estimated_usd=sum(r['peak_cost']*.5 for r in raw),charged_or_reserved_usd=charged/1e6,monetary_hard_cap_usd=12,worker_calls=worker_calls,worker_seconds=worker_ms/1000,unknown=sum(s['status']=='unknown' for s in states),mechanisms=mechanisms,outcomes=outcomes,pairwise=pairwise,G_correct=sum(r['generic']['grade']['status']=='CONFIRMED_CORRECT' for r in results),online_operator_uses=0,checks=len(checks),audit_passed=all(x['passed'] for x in checks))
 m.save(m.OUT/'summary.json',summary);m.save(m.OUT/'request_costs.json',raw);m.save(m.OUT/'integrity_audit.json',dict(passed=summary['audit_passed'],checks=checks))
 table='\n'.join(f"|{r['name']}|{(r['hypothesis'] or {}).get('decision','未交付')}|{r['static']['passed'] if r['static'] else '未生成'}|{r['source_correct']}/5|{r['design_correct']}/20|{r.get('gate_correct','未启动')}|{outcomes[r['name']]['qualified']}|" for r in mechanisms)
 verdict='未建立失败经验的独立收益。' if not results or all(v['F_only']<=v['T_only'] for v in pairwise.values()) else '观察到部分配对中的探索性增量，须与其他生成重复、成本和选择限制共同解释，不能称为普遍证明。'
 diagnosis=m.load('posthoc_diagnosis/results.json') if (m.OUT/'posthoc_diagnosis/results.json').exists() else []
 details='\n'.join(f"- {x['name']}：静态拒绝节点 {[(n['type'],n['line']) for n in x['static_rejection_nodes']]}；组件诊断正确 {sum(y['correct'] for y in x.get('component_only',[]))}/{len(x.get('component_only',[]))}。" for x in diagnosis)
 text=f'''# 人工数据上的失败驱动自动学习：计算候选实验

**{status}。{verdict}**

## 冻结与对照

新协议SHA：`{m.load('freeze.json')['sha256']}`。新手工合成100个参数实例：Design20、Gate20、Test60。两个独立参考（数字元组+试除、整数域扫描+筛法）全部一致。参考实现与答案只在宿主使用，不给生成模型或Worker。100个实例不是100道不同原题。

来源为历史最早可信失败所属题族的5条真实错误，逐字导入，未制造失败。本次没有新的失败采集费用。改变的是公开的归纳决策语义：根因不确定不自动禁止提出可测试候选，但仍允许NO_MECHANISM/HYPOTHESIS_ONLY。T/F完全相同规则；T只看相同题面，F额外看真实错误。3对生成，模型均DeepSeek Flash，不修订、不按结果换题或追加抽样。没有主张消除了上下文长度差异。

## 全部候选

|候选|真实决策|静态通过|来源正确|开发正确|Gate正确|合格|
|---|---|---|---|---|---|---|
{table}

源码及假设见各`pair-arm/pipeline`。静态拒绝不是数学错误；未匹配/拒绝也不是正确计算。模型源码原样保存，有逐字原响应与SHA核验。不得从生成数量推导正确性收益。

## 事后只读归因（不是新成绩）

{details}

五份静态拒绝全部来自 `nonlocal`，没有放宽沙箱或重发生成请求。唯一静态合格的0-F，题面正则对全部25个来源/开发输入均未匹配，同时缺少json导入；宽泛异常捕获会把解析异常伪装为不适用。

保持该源码逐字不变，仅使用独立审查的参数在Linux Worker直接调用原 `_count`：来源5/5、开发20/20正确。这是25个已曝光输入的计算组件诊断，不是正常入口、路由、独立Gate或在线复用成绩；未修代码、未改准入。没有执行被静态拒绝的其他源码，因此不能据此比较F/T的数学正确率。

## 独立能力评价

实际完成Test：{len(results)}/60。原生G正确：{summary['G_correct']}/{len(results)}。三对F/T结果：

```json
{json.dumps(pairwise,ensure_ascii=False,indent=2)}
```

若六个候选均未通过开发/Gate，按事前停止条件不发送后续120次原生请求。这不是根据Test效果提前停止；Test成绩不得填写为0/60。

本轮是离线冻结源码能力及共同回退回放。G每题真实运行一次固定两调用；同一G结果用于所有拒绝分支，避免把随机回退差异当作学习收益。候选APPLIED后即使错误也不使用Gold救援。所有候选均保留，未合格候选不能进入主效果比较。**没有启用在线算子库，0次真实在线发布/调用；不能把这里的能力结果称为完成统一路由器的在线收益验证。**

## 成本与完整性

新增真实模型请求{len(raw)}次，{summary['tokens']:,}tokens；峰价估算${summary['peak_estimated_usd']:.9f}，非峰价估算${summary['offpeak_estimated_usd']:.9f}，均非供应商账单。charged_or_reserved为${summary['charged_or_reserved_usd']:.6f}，不能与实付混用；预算硬上限$12。实际报价存档pricing.html，公开来源https://api-docs.deepseek.com/quick_start/pricing/。

Worker计量{worker_calls}次、{worker_ms/1000:.3f}秒；未知请求{summary['unknown']}。新增审计{len(checks)}项，全部通过={summary['audit_passed']}。历史失败获取、之前无效尝试和人工数据开发成本不能从生命周期收益中删除；旧两轮已报告404次请求、1,554,686tokens、峰价约$1.206610。本轮费用只是新增费用。

## 研究边界

这是人工选定的单一机制族、已有开发观察推动的实验，不是盲选自然任务分布。来源题与新题共享生成机制，只能称参数迁移，不能称自动跨原题泛化。人工编写的Oracle没有传给生成器；算子源码仍须模型自主交付。只有F相对同资源Task-Only稳定改善，才支持失败信息增量；只优于无工具G不够。

{verdict}
'''
 (m.OUT/'Final_Report.md').write_text(text)
 print(json.dumps({k:summary[k] for k in ['status','real_requests','tokens','peak_estimated_usd','test_completed','audit_passed']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
