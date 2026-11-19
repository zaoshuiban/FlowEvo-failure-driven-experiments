import argparse,csv,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def link(n,p):return f'[{n}]({p.resolve()})'
p=argparse.ArgumentParser();p.add_argument('run',type=Path);args=p.parse_args();run=args.run.resolve();report=ROOT/'reports'/run.name
proto=read(run/'protocol.json');events=[json.loads(l) for l in (run/'budget.jsonl').read_text().splitlines()];states={}
for e in events:
 x=e['payload'];k=x.get('request_id')
 if e['kind']=='RESERVED':states[k]=dict(x,status='reserved')
 elif e['kind']=='SETTLED':states[k].update(status='settled',settlement=x)
 elif e['kind']=='UNKNOWN':states[k]['status']='unknown'
 elif e['kind']=='NOT_SENT':states[k]['status']='not_sent'
rows=[]
for sp in sorted((run/'candidates').glob('*/submission.json')):
 s=read(sp);v=s['version'];q=run/'requests'/v;w=read(q/'request.private.json');metrics=read(q/'Delivery_Metrics.json');ep=run/'evaluations'/v/'source.json';ev=read(ep) if ep.exists() else None;rp=sp.parent/'parameterization.json';review=read(rp) if rp.exists() else None
 cat='CODE_NOT_DELIVERED' if not s['extraction']['passed'] else ('STATIC_REJECTED' if not s['static']['passed'] else ('SOURCE_REPRODUCED' if ev and ev['summary']['environment_won'] and review['passed'] else ('EXECUTION_FAILED' if ev else 'NOT_EXECUTED')))
 rows.append(dict(version=v,kind=read(run/'slots'/f'{v}.json')['kind'],configuration=w['thinking']['type']+'/'+w['reasoning_effort'],output_cap=w['max_tokens'],complete_source=s['extraction']['passed'],source_chars=metrics['source_chars'],source_sha256=s['code_sha256'],static_pass=s['static']['passed'],parameterization_pass=review['passed'] if review else None,used_actions=ev['summary']['used_actions'] if ev else None,won=ev['summary']['environment_won'] if ev else None,stop_reason=ev['summary']['stop_reason'] if ev else cat,category=cat,reused_from=ev.get('reused_from') if ev else None,finish_reason=metrics['finish_reason'],content_chars=metrics['content_chars'],input_tokens=metrics['usage']['prompt_tokens'],output_tokens=metrics['usage']['completion_tokens'],reasoning_tokens=metrics['usage'].get('completion_tokens_details',{}).get('reasoning_tokens'),total_tokens=metrics['usage']['total_tokens'],reserved_usd=states[v]['cost_upper_microusd']/1e6,usage_peak_no_cache_estimate_usd=(metrics['usage']['prompt_tokens']*1.32+metrics['usage']['completion_tokens']*3.96)/1e6,actual_billed_usd=None,elapsed_seconds=read(q/'end.json')['elapsed_seconds'],input_measurement=read(q/'input_measurement.json')))
selected=read(run/'Selected.json') if (run/'Selected.json').exists() else None;diagnostics=[]
if selected:
 for x in sorted((run/'evaluations'/selected['version']).glob('diagnostic_*.json')):diagnostics.append(read(x))
envp=run/'environment_actions.jsonl';env=[json.loads(x) for x in envp.read_text().splitlines()] if envp.exists() else [];starts=[x for x in env if x['kind']=='STARTED'];returned=[x for x in env if x['kind']=='RETURNED'];pending=[k for k,x in states.items() if x['status'] not in ('settled','not_sent')]
limited=selected and len(diagnostics)==3 and not (all(x['summary']['environment_won'] for x in diagnostics[:2]) and diagnostics[2]['summary']['declined_without_action'] and not any(x['summary']['runtime_errors'] or x['summary']['false_completion_claim'] for x in diagnostics))
status='REQUEST_STATUS_UNKNOWN' if pending else ('EXPOSED_DIAGNOSTIC_LIMITED' if limited else ('EXPOSED_DIAGNOSTIC_PASSED' if selected and len(diagnostics)==3 else ('SOURCE_REPRODUCED' if selected else rows[-1]['category'] if rows else 'NOT_RUN')))
result=dict(run_id=run.name,status=status,versions=rows,selected=selected,diagnostics=diagnostics,requests=len([x for x in states.values() if x['kind']=='model']),logical_slots=len(list((run/'slots').glob('*.json'))),tokens=sum(x.get('settlement',{}).get('tokens',0) for x in states.values()),reserved_usd=sum(x['cost_upper_microusd'] for x in states.values() if x['kind']=='model' and x['status']!='not_sent')/1e6,actual_billed_usd=None,environment_actions=len(starts),environment_returned=len(returned),prefix_actions=sum(x['payload']['phase']=='prefix' for x in starts),suffix_actions=sum(x['payload']['phase']=='suffix' for x in starts),workers=sum(x['kind']=='tool' for x in states.values()),pending_requests=pending,request_deadlines_satisfied=all(x['elapsed_seconds']<600 for x in rows),stops=[read(x) for x in run.glob('Stopped_*.json')],new_games=0,new_recovery_discovery=0,new_transfer=0)
(report/'Results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if rows:
 with (report/'Results.csv').open('w',newline='') as f:
  fields=[k for k in rows[0] if k!='input_measurement'];writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
sourcewon=selected is not None
lines=[f"这次 Pro {'已' if any(x['complete_source'] for x in rows) else '未'}真正交付完整 Python；交付和执行结果逐版本列于下表。",f"程序{'已' if sourcewon else '未'}从同一第 16 步失败检查点、在原剩余 34 步内复现环境确认的恢复。",'已执行候选的只读核对未发现明显来源固定路线或实例答案；这不等于证明泛化。',('其他已曝光案例结果见独立诊断表，不回流修订或候选选择。' if diagnostics else '第 12、107、23 局诊断未执行，不能填写零成功率。'),('来源编译已可行，下一步是否开展独立复用评价须结合以下诊断限制；本轮没有迁移结果。' if sourcewon else '下一步仍应研究程序归纳；当前没有依据开展新的独立复用评价。'),'',f"Run ID：`{run.name}`；结案分类：`{status}`。",'', '| 版本 | 思考／输出上限 | 完整源码 | 静态通过 | 41 动作 | 41 won | 参数化核对 | 停止原因 | tokens／保守预留 USD |','| --- | --- | --- | --- | ---: | --- | --- | --- | --- |']
for x in rows:lines.append('| '+' | '.join([x['version'],f"{x['configuration']} / {x['output_cap']}",str(x['complete_source']),str(x['static_pass']),str(x['used_actions']) if x['used_actions'] is not None else '未执行',str(x['won']) if x['won'] is not None else '未执行',str(x['parameterization_pass']) if x['parameterization_pass'] is not None else '未检查',x['stop_reason'],f"{x['total_tokens']:,} / ${x['reserved_usd']:.6f}"])+' |')
lines.extend(['','| 旧开发诊断 | 动作 | 环境 won | 无动作拒绝 | 实际退出原因 |','| --- | ---: | --- | --- | --- |'])
for seq in [12,107,23]:
 found=next((x['summary'] for x in diagnostics if x['summary']['source_sequence']==seq),None)
 lines.append('| '+' | '.join([str(seq),str(found['used_actions']),str(found['environment_won']),str(found['declined_without_action']),found['exit_reason']])+' |' if found else f'| {seq} | 未执行 | 未执行 | 未执行 | 来源通过后才执行 |')
lines.extend(['',f"实际请求 {result['requests']} 次，实际 tokens {result['tokens']:,}，保守预留 ${result['reserved_usd']:.6f}；实际供应商扣费未知。环境 {result['environment_actions']} 步＝{result['prefix_actions']} 前缀＋{result['suffix_actions']} 技能，Worker {result['workers']} 次；未决请求 {len(pending)}。",'', '每份请求均保存 HTTP 字段、实际 usage、reasoning tokens、最终 content 和源码长度、起止时间及输入计量。输入采用本地 token 计数＋25%＋1024 的冻结估计；不以字节冒充 token，不截断材料。费用按完整输入上限及输出上限预留，采用峰时统一最高单价，比供应商分开计输入输出更保守。每次绝对截止为600秒，总阶段上限90分钟。', '', '| 请求 | finish_reason | content 字符 | 源码字符 | 输入／输出／reasoning tokens | 实际秒数 |','| --- | --- | ---: | ---: | --- | ---: |'])
for x in rows:lines.append(f"| {x['version']} | {x['finish_reason']} | {x['content_chars']} | {x['source_chars']} | {x['input_tokens']} / {x['output_tokens']} / {x['reasoning_tokens']} | {x['elapsed_seconds']:.2f} |")
lines.extend(['','材料来自一个游戏：完整失败50步＋真实成功恢复后缀11步，前16步共享。选择始终为Pro第一次11步恢复，没有引入第二次8步、Flash源码、旧思考伪代码或人工策略。全部动作由候选根据原公开接口产生，宿主没有补算持物、位置或任务进度；没有原生兜底、额外直接恢复、新游戏或 G/R/F。','','本轮不是低思考与高思考的严格优劣比较，不证明Pro普遍优于Flash；来源成功不等于独立迁移成功，已曝光诊断不等于系统增量。材料含失败及真实恢复，不能推出纯失败信息优势。旧实验结果保持原样。','',link('协议',report/'Protocol.md')+' · '+link('机器结果',report/'Results.json')+' · '+link('原始响应与实际参数',run/'requests')+' · '+link('原样源码与参数化核对',run/'candidates')+' · '+link('逐步执行证据',run/'evaluations')+' · '+link('账本',run/'budget.jsonl')])
(report/'Final_Result.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:result[k] for k in ['status','requests','tokens','reserved_usd','environment_actions','workers','pending_requests']},ensure_ascii=False))
