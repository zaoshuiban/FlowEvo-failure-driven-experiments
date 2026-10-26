import pathlib,json,sys,collections,datetime
P=pathlib.Path(__file__).resolve().parent;R=P.parents[1];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from failure_evo.evidence import EvidenceStore
B=R/'runs/s20_preparation_20261025_01';out={}
for arm in 'GMF':
 plan=e.read(B/f'plan_{arm}.json');f=R/'runs'/plan['run_id'];ev=EvidenceStore(f/'stream.jsonl').records();done=[x['payload']['task_id'] for x in ev if x['kind']=='TASK_FINALIZED'];skips=[x['payload']['task_id'] for x in ev if x['kind']=='INFRASTRUCTURE_TASK_SKIPPED'];w=[e.read(f/'branches'/t/arm/'workflow.json') for t in done];audits=[];budgets={};dup_res=[];wire_dups=[]
 for ch,cfg in plan['budgets'].items():
  budget=e.PersistentBudget(f/(ch+'_budget.jsonl'),run_id=plan['run_id']+'-'+ch,protocol_hash=plan['protocol_hash'],**cfg);budgets[ch]=budget.snapshot()
  rows=[json.loads(l) for l in (f/(ch+'_budget.jsonl')).read_text().splitlines()];ids=[x['payload']['request_id'] for x in rows if x['kind']=='RESERVED'];dup_res += [ch+':'+k for k,v in collections.Counter(ids).items() if v>1]
  audits+=e.read(f/(ch+'_requests.json'))
  hashes=collections.defaultdict(list)
  for p in f.glob('wire/'+ch+'/*/request.json'):hashes[e.sha(p)].append(str(p.relative_to(R)))
  wire_dups += [paths for paths in hashes.values() if len(paths)>1]
 raw=[e.read(p) for p in f.glob('wire/*/*/response.json')];cost=0
 for r in raw:
  u=r.get('usage',{});hit=u.get('prompt_cache_hit_tokens',u.get('prompt_tokens_details',{}).get('cached_tokens',0));miss=u.get('prompt_cache_miss_tokens',max(0,u.get('prompt_tokens',0)-hit));v=(hit*.006+miss*.3+u.get('completion_tokens',0)*1.2)/1e6
  if r.get('created'):
   d=datetime.datetime.fromtimestamp(r['created'],datetime.timezone.utc)
   if not(d.weekday()<5 and (1<=d.hour<4 or 6<=d.hour<10)):v/=2
  cost+=v
 reg=[json.loads(l) for l in (f/'rule_registry.jsonl').read_text().splitlines()] if (f/'rule_registry.jsonl').exists() else [];latest={x['candidate_id']:x['state'] for x in reg};ass=[e.read(p) for p in f.glob('assessments/*.json')]
 out[arm]=dict(completed=len(done),unique_completed=len(set(done)),skipped=skips,online_locked=any(x['kind']=='ONLINE_LOCKED' for x in ev),public_pass=sum(x['status']=='PUBLIC_ACCEPTED' for x in w),responses=len(raw),tokens=sum(x.get('usage',{}).get('total_tokens',0) for x in raw),estimated_api_usd=cost,duplicate_request_ids=[k for k,v in collections.Counter(x['request_id'] for x in audits).items() if v>1],duplicate_reservation_ids=dup_res,identical_wire_groups=wire_dups,unknown=[dict(request_id=x['request_id'],status=x['status']) for x in audits if x['status']!='COMPLETED'],budget_overrun=any(v<0 for b in budgets.values() for k,v in b.items() if k.startswith('remaining_') and isinstance(v,(int,float))),budgets=budgets,learning_responses=len(list(f.glob('wire/learning/*/response.json'))),operators=[dict(candidate_id=k,permission=v['permission'],rule=v['rule'],used_tasks=v['used_tasks']) for k,v in latest.items()],source_success=sum(bool(x.get('source_success')) for x in ass),source_levels=[x.get('level') for x in ass],hooks=sum(len(x.get('hook_events',[])) for x in w))
e.write(P/'verified_results.json',dict(arms=out,sealed_executed=(P/'sealed_results.json').exists(),scope='read-only records audit; zero API; no sealed evaluation'))
lines=['# S20-A 实际结果核查','', '数据来自逐题 workflow、stream 事件、原始供应商响应及经过完整性验证的持久化预算账本；不是续跑调度日志。','', '|组|完成评价|公开通过|公开通过率（已评价）|响应|Token|估算USD|','|---|---:|---:|---:|---:|---:|---:|']
for a,s in out.items():lines.append(f"|{a}|{s['completed']}|{s['public_pass']}|{s['public_pass']/s['completed']:.2%}|{s['responses']}|{s['tokens']}|{s['estimated_api_usd']:.7f}|")
lines+=['','三组均ONLINE_LOCKED。G/M各80题；F为79题及1题基础设施缺失评价，并非三组都完成80题。F缺失题r1204不计程序失败或可信学习证据。','', '费用是按冻结报价和响应usage估算，并非账单；未知请求继续完整预留，未假定零费用。']
for a,s in out.items():lines.append(f"\n{a}：重复请求ID {len(s['duplicate_request_ids'])}；重复预留ID {len(s['duplicate_reservation_ids'])}；同文wire组 {len(s['identical_wire_groups'])}（同文不自动代表重复发送）；未知请求 {len(s['unknown'])}；预算超限 {s['budget_overrun']}；学习响应 {s['learning_responses']}；候选 {len(s['operators'])}；来源成功 {s['source_success']}；实际Hook {s['hooks']}。")
lines+=['','F两份候选保持Shadow，来源评价均LEGAL_BEHAVIOR、无来源修复成功；没有真实跨任务介入。M学习响应0，不能当作充分运行的自动文本经验对照。','', '封存测试尚未执行：恢复状态为ONLINE_COMPLETE_WITH_INFRASTRUCTURE_SKIP，原离线入口要求三组各80个TASK_FINALIZED，因此不能直接运行。需要按已批准的缺失评价口径适配离线入口；不能将缺失题作为错误代码评分，也不能虚构TASK_FINALIZED。','', '当前数据仅支持公开检查描述，不支持最终正确率或F学习收益结论。G/M/F任务不完全配对，F实际介入0；应在封存复核后另列共同79题配对统计。']
(P/'S20A_实际结果核查.md').write_text('\n'.join(lines))
for a,s in out.items():print(a,{k:s[k] for k in ('completed','online_locked','duplicate_request_ids','duplicate_reservation_ids','budget_overrun','source_success','hooks')},'wire_duplicate_groups',len(s['identical_wire_groups']),'permissions',[x['permission'] for x in s['operators']],'reserved_usd',sum(b['charged_or_reserved_cost_microusd'] for b in s['budgets'].values())/1e6)
