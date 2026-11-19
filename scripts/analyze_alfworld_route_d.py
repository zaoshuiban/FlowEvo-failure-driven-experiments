"""Read-only execution analysis; writes only Route D report artifacts."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'runs/alfworld_route_d_20261118_01';REPORT=ROOT/'reports/alfworld_route_d_20261118_01'
def read(p):return json.loads(p.read_text())
def link(label,p):return f'[{label}]({p})'
models=['deepseek-flash','deepseek-v4-pro'];rows=[];requests=[]
for p in sorted((RUN/'requests').rglob('request.private.json')):
 folder=p.parent;ident=str(folder.relative_to(RUN/'requests'));response=read(folder/'response.json') if (folder/'response.json').exists() else None
 requests.append(dict(ident=ident,model=read(p)['model'],response_received=response is not None,usage=response.get('usage') if response else None))
budget=[]
for model in models:
 p=RUN/f'budget_{model}.jsonl'
 if not p.exists():continue
 events=[json.loads(l) for l in p.read_text().splitlines()];states={}
 for e in events:
  x=e['payload'];k=x.get('request_id')
  if e['kind']=='RESERVED':states[k]=dict(x,status='reserved')
  elif e['kind']=='SETTLED':states[k].update(status='settled',settlement=x)
  elif e['kind']=='UNKNOWN':states[k]['status']='unknown'
  elif e['kind']=='NOT_SENT':states[k]['status']='not_sent'
  elif e['kind']=='NETWORK_SEND_STARTED' and k in states:states[k]['sent']=True
 # Send identity is verified separately by durable transport events below.
 budget.append(dict(model=model,reserved_usd=sum(x['cost_upper_microusd'] for x in states.values() if x['kind']=='model' and x['status']!='not_sent')/1e6,tokens=sum(x.get('settlement',{}).get('tokens',0) for x in states.values()),worker_calls=sum(x['kind']=='tool' for x in states.values()),unsettled=[k for k,x in states.items() if x['status'] not in ('settled','not_sent')],states=states))
for model in models:
 for n in (1,2):
  folder=RUN/f'P1/{model}/attempt_{n}';p=folder/'result.json';result=read(p) if p.exists() else None
  decisions=[read(x) for x in sorted(folder.glob('request_*_decision.json'))]
  actions=[read(x) for x in sorted(folder.glob('action_*_returned.json'))]
  req=[x for x in requests if x['ident'].startswith(f'P1/{model}/attempt_{n}/')]
  row=dict(model=model,attempt=n,executed=result is not None or bool(req),completed=result is not None,won=result['won'] if result else None,model_requests=len(req),environment_actions=len(actions),invalid_action_requests=sum(d['decision']['status']=='DELIVERY_ERROR' for d in decisions),stop_reason=result['stop_reason'] if result else ('INFRASTRUCTURE_STOP' if req else 'NOT_RUN'),actions=actions,usage_tokens=sum((x['usage'] or {}).get('total_tokens',0) for x in req),unknown_usage_requests=sum(x['usage'] is None for x in req))
  row['conservative_reserved_usd']=sum(v['cost_upper_microusd'] for b in budget for k,v in b['states'].items() if k.startswith(f'P1/{model}/attempt_{n}/'))/1e6
  rows.append(row)
envfile=RUN/'environment_actions.jsonl';env=[json.loads(l) for l in envfile.read_text().splitlines()] if envfile.exists() else []
starts=[x for x in env if x['kind']=='STARTED'];returned=[x for x in env if x['kind']=='RETURNED']
sendfile=RUN/'events.jsonl';events=[json.loads(l) for l in sendfile.read_text().splitlines()] if sendfile.exists() else []
p1=read(RUN/'P1_Result.json') if (RUN/'P1_Result.json').exists() else None
p2=read(RUN/'P2_Result.json') if (RUN/'P2_Result.json').exists() else None
summary=dict(run_id=RUN.name,P1_status=p1['status'] if p1 else 'STOPPED_INCOMPLETE',attempts=rows,selected_recovery=p1.get('selected') if p1 else None,P2=p2,P4='NOT_AUTHORIZED_NOT_RUN',model_requests_prepared=len(requests),model_POST_started=sum(x['kind']=='SEND_STARTED' for x in events),known_tokens=sum(x['tokens'] for x in budget),conservative_reserved_usd=sum(x['reserved_usd'] for x in budget),actual_billed_usd=None,model_budget=budget,environment_attempts=len(starts),environment_returned=len(returned),P0_prefix_actions=16,total_environment_including_P0=len(starts)+16,worker_calls=sum(x['worker_calls'] for x in budget),stops=[read(x) for x in RUN.glob('Stopped_*.json')])
(REPORT/'Results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
lines=['模型自己找到恢复路线了吗？'+('是，实际环境确认的成功见下表。' if any(x['won'] for x in rows) else '本轮现有记录没有建立成功恢复；未执行或基础设施中断不能算任务失败。'),'模型能把恢复路线写成程序吗？'+('编译结果单独报告。' if p2 and p2.get('chains') else '尚无可报告的程序复现结果。'),'程序能复用吗？P4 未授权、未执行，未知。','',f'Run ID：`{RUN.name}`。P1 状态：`{summary["P1_status"]}`。','', '| 模型 | 尝试 | 请求 | 实际恢复动作 | 非法/交付错误请求 | won | 终止原因 | 已知 tokens | 保守预留 USD |','| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |']
for x in rows:lines.append(f"| {x['model']} | {x['attempt']} | {x['model_requests']} | {x['environment_actions']} | {x['invalid_action_requests']} | {x['won'] if x['won'] is not None else '未确认'} | {x['stop_reason']} | {x['usage_tokens']} | ${x['conservative_reserved_usd']:.6f} |")
for x in rows:
 lines.extend(['',f"**{x['model']} 尝试 {x['attempt']} 的实际动作**",''])
 if x['actions']:
  for i,a in enumerate(x['actions'],17):lines.append(f"{i-16}. 第 {i} 步：`{a['action']}` → {a['observation']}（won={a['won']}）")
 else:lines.append('没有实际恢复动作。')
lines.extend(['',f"实际 POST 开始 {summary['model_POST_started']} 次；已知用量 {summary['known_tokens']:,} tokens；保守费用预留 ${summary['conservative_reserved_usd']:.6f}，实际供应商账单未知。新增环境动作含前缀 {len(starts)} 次，另 P0 的 16 次；Worker {summary['worker_calls']} 次。未知请求保留完整预留，不补发。",'', '所有尝试从同一真实检查点开始，原剩余动作上限 34。非法输出没有替代为合法动作；完整响应、合法列表与诊断保存于运行目录。仅两种模型各至多两次诊断，不构成统计上独立重复；配置和思考预算差异不能归因于单一因素。', '',link('协议',REPORT/'Route_D_Protocol.md')+' · '+link('原始执行记录',RUN/'P1')+' · '+link('机器结果',REPORT/'Results.json')])
(REPORT/'Route_D_Recovery_Discovery_Result.md').write_text('\n'.join(lines)+'\n')
if not p2 or not p2.get('chains'):
 (REPORT/'Route_D_Skill_Compilation_Result.md').write_text('模型能把恢复路线写成程序吗？本轮未进入正式技能编译，无法判断。\n\n没有取得已选定的真实成功恢复轨迹，或 P1 因基础设施问题未完成；不把这一结果归为程序归纳失败。P2/P3 未执行，P4 未授权。下一步应先解决已记录的恢复探索或基础设施障碍，不能据此宣称程序编译能力不足。\n')
else:
 lines=['模型自己找到恢复路线了吗？是，来自 '+str(summary['selected_recovery'])+'。','模型能把恢复路线写成程序吗？结果见下表，合法执行不等于恢复成功。','程序能复用吗？P4 未执行，未知。','','| 版本 | 静态通过 | 41 won | 12 won | 107 won | 23 零动作拒绝 | 开发通过 |','| --- | --- | --- | --- | --- | --- | --- |']
 for chain in p2['chains']:
  for v in chain['versions']:
   b=[x['summary'] for x in v['branches']];vals=[str(x['environment_won']) for x in b[:3]] if b else ['未执行']*3
   lines.append('| '+' | '.join([v['version'],str(v['static']['passed'])]+vals+[str(b[3]['declined_without_action']) if b else '未执行',str(v['passed'])])+' |')
 lines.extend(['',f"选定版本：{p2['selected']}。恢复来源固定为第一条实际成功轨迹，不根据代码表现重选。",'',link('完整源码与原始响应',RUN/'candidates')+' · '+link('真实分支反馈',RUN/'P3')])
 (REPORT/'Route_D_Skill_Compilation_Result.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:summary[k] for k in ['P1_status','selected_recovery','model_POST_started','known_tokens','conservative_reserved_usd','total_environment_including_P0','worker_calls']},ensure_ascii=False))
