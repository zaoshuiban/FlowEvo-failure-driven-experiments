"""Read-only aggregate of online records; sealed data only if completed evaluator output exists."""
import pathlib,sys,json,collections,datetime,hashlib
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1];B=R/'runs/s20_preparation_20261025_01';sys.path.insert(0,str(R/'scripts'));import run_workflow_v2 as e

def events(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
def price(raw):
 u=raw.get('usage',{});hit=u.get('prompt_cache_hit_tokens',u.get('prompt_tokens_details',{}).get('cached_tokens',0));miss=u.get('prompt_cache_miss_tokens',max(0,u.get('prompt_tokens',0)-hit));out=u.get('completion_tokens',0)
 peak=(hit*.006+miss*.3+out*1.2)/1e6;stamp=raw.get('created');known=stamp is not None
 if known:
  d=datetime.datetime.fromtimestamp(stamp,datetime.timezone.utc);peak_time=d.weekday()<5 and (1<=d.hour<4 or 6<=d.hour<10)
  # Weekends are unambiguously off-peak. Weekday holidays cannot increase cost.
  estimate=peak if peak_time else peak/2
 else:estimate=peak
 return estimate,peak,known
state=e.read(P/'execution_status.json');tasks=e.read(B/'stream_tasks.json');sealed=e.read(P/'sealed_results.json') if (P/'sealed_results.json').exists() else [];summaries={};traces=[];batch=[];capabilities=[];versions=[];rules=[]
for arm in 'GMF':
 folder=R/'runs'/e.read(B/f'plan_{arm}.json')['run_id'];work={};requests=[]
 for f in folder.glob('branches/*/*/workflow.json'):
  w=e.read(f);work[w['problem_id']]=w
 for ch in ('solve','learning','validation'):
  for f in folder.glob(f'wire/{ch}/*/response.json'):
   raw=e.read(f);est,upper,known=price(raw);requests.append(dict(channel=ch,file=str(f.relative_to(R)),usage=raw.get('usage',{}),model=raw.get('model'),estimated_usd=est,peak_upper_usd=upper,created_known=known))
 failure=events(folder/f'evidence_{arm}.jsonl');hyp=events(folder/'hypotheses.jsonl');registry=events(folder/'rule_registry.jsonl');stream=events(folder/'stream.jsonl')
 for x in hyp:
  if x.get('kind')=='HYPOTHESIS_VERSION':versions.append(dict(arm=arm,**x))
 for x in registry:rules.append(dict(arm=arm,**x))
 assessments=[e.read(f) for f in folder.glob('assessments/*.json')]
 for f in folder.glob('jobs/*/*-capability.json'):capabilities.append(dict(arm=arm,path=str(f.relative_to(R)),**e.read(f)))
 packets=[e.read(f) for f in folder.glob('public_packets/*.json')]
 for i,t in enumerate(tasks):
  if t['task_id'] not in work:continue
  w=work[t['task_id']];audit=next((s for s in sealed if s['arm']==arm and s['task_id']==t['task_id'] and s['kind']=='TASK_FINAL'),None)
  traces.append(dict(arm=arm,index=i+1,batch=i//10+1,task_id=t['task_id'],public_status=w['status'],stage=(w.get('selected') or {}).get('stage'),calls=w['budget']['calls'],tokens=w['budget']['charged_or_reserved_tokens'],hook_count=len(w.get('hook_events',[])),changed_generic=sum(bool(h.get('changed_generic_action')) for h in w.get('hook_events',[])),not_sent=[x for x in w['events'] if x.get('request_state')=='NOT_SENT'],sealed_pass=audit['result']['passed'] if audit else None,sealed_tests_passed=audit['result']['tests_passed'] if audit else None))
 for n in range(1,9):
  tr=[x for x in traces if x['arm']==arm and x['batch']==n]
  if tr:batch.append(dict(arm=arm,batch=n,tasks=len(tr),public_pass=sum(x['public_status']=='PUBLIC_ACCEPTED' for x in tr),hooks=sum(x['hook_count'] for x in tr),calls=sum(x['calls'] for x in tr),tokens=sum(x['tokens'] for x in tr)))
 normalized=[e.read(f) for f in folder.glob('jobs/*/*-normalization.json')]
 budgets=e.read(folder/'state.json')['budgets'] if (folder/'state.json').exists() else {}
 audits=[x for ch in ('solve','learning','validation') if (folder/f'{ch}_requests.json').exists() for x in e.read(folder/f'{ch}_requests.json')]
 own=[x for x in traces if x['arm']==arm];sc=[x for x in sealed if x['arm']==arm and x['kind']=='TASK_FINAL'];unknown=[x for x in audits if x['status']!='COMPLETED']
 summaries[arm]=dict(tasks_completed=len(own),public_pass=sum(x['public_status']=='PUBLIC_ACCEPTED' for x in own),sealed_tasks_scored=len(sc),sealed_pass=sum(x['result']['passed'] for x in sc),public_pass_sealed_fail=sum(x['public_pass'] and not x['result']['passed'] for x in sc),failure_events=len(packets),failure_tasks=len({x['task_id'] for x in packets}),hypothesis_ids=len({x['payload']['hypothesis_id'] for x in hyp if x.get('kind')=='HYPOTHESIS_VERSION'}),hypothesis_versions=sum(x.get('kind')=='HYPOTHESIS_VERSION' for x in hyp),content_versions=[x['payload'].get('content_version') for x in hyp if x.get('kind')=='HYPOTHESIS_VERSION'],learning_responses=sum(x['channel']=='learning' for x in requests),validation_responses=sum(x['channel']=='validation' for x in requests),compile_accepted=sum(bool(x.get('accepted')) for x in normalized),source_effects=dict(collections.Counter(x.get('level','UNKNOWN') for x in assessments)),source_public_success=sum(bool(x.get('source_success')) for x in assessments),hooks=sum(x['hook_count'] for x in own),changed_generic_actions=sum(x['changed_generic'] for x in own),request_count=len(requests),tokens=sum(x['usage'].get('total_tokens',0) for x in requests),estimated_api_usd=sum(x['estimated_usd'] for x in requests),all_peak_upper_usd=sum(x['peak_upper_usd'] for x in requests),unknown_requests=len(unknown),preflight_blocked_events=sum(len(x['not_sent']) for x in own),budgets=budgets,channels={ch:dict(calls=sum(x['channel']==ch for x in requests),tokens=sum(x['usage'].get('total_tokens',0) for x in requests if x['channel']==ch),estimated_usd=sum(x['estimated_usd'] for x in requests if x['channel']==ch)) for ch in ('solve','learning','validation')},online_locked=any(x['kind']=='ONLINE_LOCKED' for x in stream))
 e.write(P/f'{arm}_physical_costs.json',requests)
e.write(P/'summary.json',dict(execution=state,arms=summaries,batches=batch,capabilities=capabilities,real_experiment=True,independent_generalization=False))
e.write(P/'task_traces.json',traces);e.write(P/'hypothesis_version_history.json',versions);e.write(P/'operator_version_history.json',rules)
table='\n'.join('|'+a+'|'+str(s['tasks_completed'])+'|'+str(s['public_pass'])+'|'+(str(s['sealed_pass'])+'/'+str(s['sealed_tasks_scored']) if s['sealed_tasks_scored'] else '未运行')+'|'+str(s['request_count'])+'|'+str(s['tokens'])+'|'+f"${s['estimated_api_usd']:.6f}"+'|'+str(s['hooks'])+'|' for a,s in summaries.items())
learning='\n'.join(f"|{a}|{s['failure_events']}|{s['failure_tasks']}|{s['hypothesis_ids']}|{s['learning_responses']}|{s['compile_accepted']}|{s['source_public_success']}|{s['changed_generic_actions']}|" for a,s in summaries.items())
bt='\n'.join(f"|{x['batch']}|{x['arm']}|{x['tasks']}|{x['public_pass']}|{x['calls']}|{x['hooks']}|" for x in batch)
total=sum(x['estimated_api_usd'] for x in summaries.values());pending=sum(x['unknown_requests'] for x in summaries.values());F=summaries['F']
status='ONLINE_COMPLETE' if all(s['online_locked'] for s in summaries.values()) else state['status']
text=f'''# S20-A TACO80长期G/M/F真实实验报告

执行状态：**{status}**。原因：{state.get('reason','按冻结顺序完成或仍在运行；详见状态账本')}。

授权范围为S20-A三臂80题、8批、总硬预算$66；不含外部迁移、额外付费动作配对及S21。基线提交7229373535abc42794c9dd993d7f9f98308f8eda，任务及协议沿用S20准备冻结文件。历史实验未修改。

## 实际结果

|臂|已完成任务|公开通过|封存全通过/已评分|真实响应|Token|API估算|实际Hook|
|---|---:|---:|---|---:|---:|---:|---:|
{table}

费用合计估算${total:.6f}，不是账单。按响应usage、缓存用量和响应时间对应冻结报价估算；无时间时按峰值上界。预算账本的charged_or_reserved金额为保守预留，不是已付费用。未知请求{pending}个，其预留不得当作0实付，也不能重发。

## 失败—学习—使用漏斗

|臂|可信事件|失败原题|假设ID|学习响应|编译通过|来源公开成功|改变Generic动作|
|---|---:|---:|---:|---:|---:|---:|---:|
{learning}

G/M中的假设索引仅为公开事件整理，不代表G训练Operator。M的学习响应是文本记忆；F才是受约束规则学习。F来源效果分布：{json.dumps(F['source_effects'],ensure_ascii=False)}。

假设完整版本史见hypothesis_version_history.json，规则/准入/试用/暂停事件见operator_version_history.json，各作业动作差异见summary.json.capabilities。版本号、文字变化、同文重复不计作性能改善；全部生成成本仍累计。

## 批次与逐题

|批次|臂|完成任务|公开通过|正常求解调用|Hook|
|---|---|---:|---:|---:|---:|
{bt}

逐题的阶段、调用、Token、NOT_SENT、Hook及封存结果见task_traces.json。原始响应、wire、公开轨迹与预算位于三个s20_taco80_* Run。批次间不中途冷启动，不按失败结果改顺序、Prompt、规则或调度。

## 归因边界与下一阶段

本轮主比较为系统级G/M/F，不是单一表示的因果消融。没有额外付费配对，不能把组间差异当作Operator独立因果收益。F实际介入为{F['hooks']}次，改变Generic动作为{F['changed_generic_actions']}次；若为0，不能归因失败学习。相同动作但不同wire应分别看作请求差异，不能声称工作流选择创新。

仅在三臂全ONLINE_LOCKED后读取封存材料。本报告若显示封存未运行，则没有最终可靠性结论；来源公开PASS不是泛化。80题属于已冻结开发分布，不能称独立跨数据集验证。来源失败、没有匹配与可信负迁移分别记录，不能把两个失败分支的较低费用奖励为效率收益。

S20-B/B2/S21没有启动。是否值得迁移或消融需要结合来源有效规则、未来实际复用与全部成本审查；没有充分证据时不自动扩大范围或预算。
'''
(P/'S20A_真实80题长期GMF实验报告.md').write_text(text)
print(json.dumps({'status':status,'tasks':{a:s['tasks_completed'] for a,s in summaries.items()},'estimated_usd':total,'unknown':pending},ensure_ascii=False))
