import pathlib,sys,json,time,tempfile,datetime,math
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import configure_worker
from failure_evo.contracts import fingerprint
P=R/'runs/s20_m_paired12_20261025_01';B=R/'runs/s20_preparation_20261025_01';assert e.read(P/'online_lock.json')['locked'];branches=e.read(P/'branches.json');assert e.sha(P/'branches.json')==e.read(P/'online_lock.json')['branches_sha256'];assert len(branches)==24
configure_worker(e.read(B/'plan_G.json')['worker_environment']);tempfile.tempdir=str(P/'tmp');plan=e.read(P/'plan.json');budget=e.PersistentBudget(P/'solve_budget.jsonl',run_id=plan['run_id']+'-solve',protocol_hash=plan['protocol_hash'],**plan['budgets']['solve']);judge=e.prior.Judge(budget)
sealed={x['task_id']:x['cases'] for x in e.read(B/'sealed_final_tasks.json')};rows=[];start=time.time();assert not (P/'sealed_results.json').exists(),'no silent scoring rerun'
for x in branches:
 result=judge.run(x['task_id'],x['code'],sealed[x['task_id']]);rows.append(dict(task_id=x['task_id'],arm=x['arm'],result=result));e.write(P/'sealed_results.json',rows)
# Response-based cost; identical formula for branches and memory construction.
def cost(raw):
 u=raw['usage'];hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit);v=(hit*.006+miss*.3+u['completion_tokens']*1.2)/1e6;date=datetime.datetime.fromtimestamp(raw['created'],datetime.timezone.utc)
 return v if date.weekday()<5 and (1<=date.hour<4 or 6<=date.hour<10) else v/2
requests={x['request_id']:x for x in e.read(P/'solve_requests.json')};stats={};details=[]
for arm in 'GM':
 br=[x for x in branches if x['arm']==arm];sc=[x for x in rows if x['arm']==arm];stats[arm]=dict(public_success=sum(x['public_result']['passed'] for x in br),sealed_success=sum(x['result']['passed'] for x in sc),joint_success=sum(x['public_result']['passed'] and next(y['result']['passed'] for y in sc if y['task_id']==x['task_id']) for x in br),calls=len(br),tokens=sum(x['response']['usage']['total_tokens'] for x in br),input_tokens=sum(x['response']['usage']['prompt_tokens'] for x in br),output_tokens=sum(x['response']['usage']['completion_tokens'] for x in br),estimated_usd=sum(cost(requests[f"{arm}/{x['task_id']}/repair1"]['raw_response']) for x in br))
for tid in dict.fromkeys(x['task_id'] for x in branches):
 pair={x['arm']:x for x in branches if x['task_id']==tid};sc={x['arm']:x['result'] for x in rows if x['task_id']==tid};details.append(dict(task_id=tid,G_public=pair['G']['public_result']['tests_passed'],M_public=pair['M']['public_result']['tests_passed'],public_total=pair['G']['public_result']['tests_run'],G_sealed=sc['G']['tests_passed'],M_sealed=sc['M']['tests_passed'],G_joint=pair['G']['public_result']['passed'] and sc['G']['passed'],M_joint=pair['M']['public_result']['passed'] and sc['M']['passed'],code_changed=pair['G']['code_sha256']!=pair['M']['code_sha256'],input_token_delta=pair['M']['response']['usage']['prompt_tokens']-pair['G']['response']['usage']['prompt_tokens']))
mwin=sum(x['M_joint'] and not x['G_joint'] for x in details);gwin=sum(x['G_joint'] and not x['M_joint'] for x in details);n=mwin+gwin;pv=min(1,2*sum(math.comb(n,i) for i in range(min(mwin,gwin)+1))/2**n) if n else 1
src=R/'runs/s20_mechanism_acceptance_20261025_01';learn=[e.read(f) for f in src.glob('wire/learning/*/response.json') if int(f.parent.name)<=2];learning_cost=sum(cost(x) for x in learn);learning_tokens=sum(x['usage']['total_tokens'] for x in learn)
summary=dict(stats=stats,M_only_success=mwin,G_only_success=gwin,exact_mcnemar_p=pv,code_changed=sum(x['code_changed'] for x in details),memory_learning_tokens=learning_tokens,memory_learning_estimated_usd=learning_cost,M_with_learning_estimated_usd=stats['M']['estimated_usd']+learning_cost,details=details,budget=budget.snapshot(),evaluation_seconds=time.time()-start,extra_evaluation_model_calls=0,development_only=True)
e.write(P/'paired_summary.json',summary)
lines=['# M同检查点12题配对与F决策空间审计','', '结论基于12个不同原题、24个真实分支，每分支仅一次修复；相同模型、相同8192输出上限、相同交付要求与公开检查。请求内容差异仅固定记忆输入。原成功经验库上下文两组均为空，以隔离失败记忆；不是原生五阶段完整成绩。','', '从原M失败公开记录按原S20任务顺序、每题最早有调用额度的检查点选取前12题。排除记忆13事件涉及的6题及先前使用验收612题。任务、顺序、wire、预算在首次请求前冻结。119确认题和419题未使用。所有题为曝光开发材料，不是独立泛化。','', '|组|公开全通过|封存全通过|两者都通过|请求|Token|费用估算USD|','|---|---:|---:|---:|---:|---:|---:|']
for arm,s in stats.items():lines.append(f"|{arm}|{s['public_success']}/12|{s['sealed_success']}/12|{s['joint_success']}/12|{s['calls']}|{s['tokens']}|{s['estimated_usd']:.7f}|")
lines += ['',f'以公开及封存均通过为成功：M独有{mwin}题，G独有{gwin}题。探索性未校正精确McNemar p={pv:.6f}；单次生成及小样本不足强因果/统计结论。',f"12对中{summary['code_changed']}对代码哈希不同。这说明输出有差异，不足证明修复思路发生特定改变；不将代码变化直接计作有效记忆。输入Token增加逐对列于paired_summary.json，反映记忆注入开销。",f'真实记忆构建2次，{learning_tokens} Token，估算${learning_cost:.7f}；M合计含构建${summary["M_with_learning_estimated_usd"]:.7f}。费用按原始usage与缓存/响应时段估算，不是账单；未货币化本地计算，不能声称完整回本。此前记忆使用验收及F生成成本另留原Run，不悄悄删除，也不混算为本轮M构建成本。','', '|任务|G公开通过数|M公开通过数|G封存通过数|M封存通过数|G共同成功|M共同成功|','|---|---:|---:|---:|---:|---|---|']
for x in details:lines.append(f"|{x['task_id']}|{x['G_public']}|{x['M_public']}|{x['G_sealed']}|{x['M_sealed']}|{x['G_joint']}|{x['M_joint']}|")
lines+=['', 'F零API审计见reports/s20_m_paired12/F_零API决策空间审计.md。当前51事件24题中26事件14题存在合法替代，但历史配对未形成可由当前字段辨识的相反可靠偏好。固定B必须保留为强基线，暂不生成新规则，不改权限。','', '本轮结束即停止，不自动启动419题。出现M独有成功只能视为开发性潜在信号，应同时报告G独有成功及构建成本，再决定是否预注册重复配对或正式流；不能根据本轮结果调整记忆后仍称同一确认实验。']
(P/'M_12题配对实验报告.md').write_text('\n'.join(lines));print(json.dumps({k:v for k,v in summary.items() if k not in ['details','budget']},ensure_ascii=False))
