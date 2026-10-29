"""V3.1 immutable-result reporting; no API, no Gate, no candidate edits."""
import json,sys,datetime,collections
from pathlib import Path
from run_math_v3_development import ROOT,save,sha
from failure_evo.contracts import fingerprint
RUN=ROOT/'runs/math_v31_semantic_20261027_01';OUT=ROOT/'reports/math_v31_semantic_20261027'
def load(p):return json.loads(p.read_text())
def write(name,text):(OUT/name).write_text(text+'\n')
def report():
 OUT.mkdir(parents=True,exist_ok=True);s=load(RUN/'development/summary.json');scores=load(RUN/'development/scores.json');plan=load(RUN/'protocol.json');inputs=load(RUN/'inputs.json');cost=[];unknown=[]
 for key in plan['order']:
  starts={}
  for line in (RUN/key/'provider.jsonl').read_text().splitlines():
   r=json.loads(line)
   if r['kind']=='SEND_STARTED':starts[r['payload']['key']]=r['at']
   if r['kind']=='SEND_UNKNOWN':unknown.append(dict(key=key,record=r))
   if r['kind']=='RAW_RESPONSE':
    v=r['payload']['response'];u=v['usage'];dt=datetime.datetime.fromtimestamp(r['at'],datetime.timezone.utc);peak=dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10);factor=1 if peak else .5
    usd=(u.get('prompt_cache_hit_tokens',0)*.006+u.get('prompt_cache_miss_tokens',u['prompt_tokens'])*.3+u['completion_tokens']*1.2)/1e6*factor
    cost.append(dict(key=key,response_id=v.get('id'),model=v.get('model'),utc=dt.isoformat(),usage=u,finish_reason=v['choices'][0]['finish_reason'],seconds=r['at']-starts[r['payload']['key']],estimated_usd=usd,price_period='peak' if peak else 'off_peak',cost_is_invoice=False))
 save(OUT/'costs.json',cost);save(OUT/'unknown_requests.json',unknown)
 worker=[json.loads(x) for x in (RUN/'development/worker.jsonl').read_text().splitlines()];worker=[r['payload'] for r in worker if r['kind']=='V3_COMPONENT_EXECUTED']
 save(OUT/'worker_usage.json',dict(calls=len(worker),wall_seconds=sum(x['seconds'] for x in worker),monetized=False,old_baseline='reused hash-bound identical public cases from prior actual Worker outputs; not new calls'))
 # Keep raw summaries; semantic rates are undefined when no candidate can execute.
 metrics={}
 for name,conds in s.items():
  metrics[name]={}
  for cond,roles in conds.items():
   metrics[name][cond]={}
   for role,v in roles.items():
    v=dict(v);v['not_generated']=v['status_counts'].get('NOT_GENERATED',0)
    if v['n'] and v['not_generated']==v['n']:
     for field in ['correct_accept_rate','false_accept_rate','unknown_rate','interface_error_rate']:v[field]=None
     v['semantic_status']='NOT_EVALUATED_DELIVERY_MISSING'
    else:v['semantic_status']='EVALUATED'
    metrics[name][cond][role]=v
 save(OUT/'semantic_metrics.json',metrics)
 bindings=[]
 for key in plan['order']:
  p=RUN/key;v=inputs[key];valid=(p/'artifact.json').exists();entry=dict(key=key,algorithm_sha256=v['solver_sha256'],algorithm_unchanged=sha(p/'solver.py')==v['solver_sha256'],origin='DEEPSEEK',delivery=load(p/'result.json'))
  if valid:
   a=load(p/'artifact.json');old=ROOT/'runs/math_v3_components_deepseek_repair_20261027_01'/key.rsplit('_',1)[0]/'artifact.json';o=load(old) if old.exists() else None
   entry.update(matcher_sha256=a['matcher_sha256'],joint_sha256=a['code_sha256'],identical_old_matcher=o and o['matcher_sha256']==a['matcher_sha256'],identical_old_joint=o and o['code_sha256']==a['code_sha256'])
  bindings.append(entry)
 save(OUT/'component_bindings.json',bindings)
 def show(v,k,den):
  if v['semantic_status'].startswith('NOT_EVALUATED'):return '—'
  return str(v[k])+'/'+str(v[den])
 table='|冻结算法|条件|正确接受 / 支持题|错误接受 / 不支持题|UNKNOWN / 可判定题|接口或执行ERROR|\n|---|---|---:|---:|---:|---:|\n'
 for name in s:
  for cond in ['OLD','F','T']:
   v=metrics[name][cond]['Design'];table+='|'+ '|'.join([name,cond,show(v,'correct_accept','supported'),show(v,'false_accept','unsupported'),show(v,'unknown','n'),show(v,'interface_error','n')])+'|\n'
 paired=[]
 for name in s:
  a={r['task_id']:r for r in scores if r['algorithm']==name and r['condition']=='F' and r['role']=='Design'};b={r['task_id']:r for r in scores if r['algorithm']==name and r['condition']=='T' and r['role']=='Design'}
  paired.append(dict(algorithm=name,both_contracts_delivered=(RUN/(name+'_F')/'artifact.json').exists() and (RUN/(name+'_T')/'artifact.json').exists(),f_only=sum(a[k]['correct_accept'] and not b[k]['correct_accept'] for k in a),t_only=sum(b[k]['correct_accept'] and not a[k]['correct_accept'] for k in a),both=sum(a[k]['correct_accept'] and b[k]['correct_accept'] for k in a)))
 save(OUT/'paired_differences.json',paired)
 hashes={r:sha(r)==h for r,h in plan['history_hashes'].items()};save(OUT/'history_integrity.json',hashes);assert all(hashes.values()) and all(x['algorithm_unchanged'] for x in bindings)
 tokens=sum(x['usage']['total_tokens'] for x in cost);usd=sum(x['estimated_usd'] for x in cost)
 write('V3_1_Protocol.md',f'''# V3.1 冻结算法的语义契约学习协议

Run `{RUN.name}`；协议SHA `{load(RUN/'freeze.json')['sha256']}`。启动时冻结，日期名称不因跨午夜执行重命名。

保留全部5份既有DeepSeek算法：F1、F2、T2、F3、T3；这些是旧候选标识，不是本轮条件。本轮每个算法分别配F/T两条件，共10次上限、每条件1次、0次追加修订。DeepSeek Flash、非思考、温度0、输出12288、wire上界65536；复用BoundedCompiler/PersistentBudget/Worker/注册表，新增模块默认关闭。原始Python算法SHA完全不变。

共同输入仅算法、既有参数schema、相同来源公开题面和接口要求。T不接收旧契约、失败状态或轨迹。F增加旧matcher/contract与至多12条既有开发诊断；按不确定案例、支持题失败、不支持题失败的固定顺序选择。没有Gold、标准解、评分器内部信息，也没有由宿主提供具体修订规则。两组算力上限相同，实际输入长度不同。

评价：每算法自己的来源 + 同48道已曝光Design + 同算法既有自动提案。仅独立语义审查确定支持/不支持的题进入三项主要比率；不确定题另外报告，不强制标签。所有输出锁定后评分，评分结果不回流本轮模型。

开发冻结条件事前要求支持正例全部正确接受、无错误接受/参数误提取/接口异常、歧义案例不MATCH；全拒绝不能通过。通过仅表示可冻结为后续Gate候选，绝不自动执行Gate或授予Experimental。

本轮采用先前明确指定的DeepSeek渠道；没有GPT调用，也未继承旧UNKNOWN请求。源码快照、原始输入、每次response和预算账本均在Run目录。''')
 write('V3_1_Evidence_Audit.md',f'''# 证据与隔离审计

- 10份wire零API预检通过；每对移除F证据与条件标签后共同输入完全一致。
- 结构化投影不含gold_answer、solution、reference_answer、correct_answer、answer等私有字段；旧matcher的MATCH参数只是公开题面参数，不是数学答案。
- F使用历史开发反馈，不使用未来Gate或本轮新评分。
- 计算代码10份拷贝对应5份唯一算法，SHA逐项未变；生成模型没有solve修改权限。
- {len(hashes)}份旧Run/开发审查文件哈希保持不变；旧402 UNKNOWN未重发。
- 9份新契约静态合格；F1_F源码含JSON风格`false`和禁止的定义/顶层执行，保留原文拒绝，没有人工修补。
- 旧基线复用相同题面/同哈希源码的既有真实Worker输出；F/T均重新执行真实Worker。独立数学正确性沿用私有冻结参考，未让候选互证。

限制：开发语义标签来自此前宿主对固定题面与目标量的审查；不是模型自报标签，也不是新的盲法专家标注。本次部分评价题的契约失败记录已提供F，结果只用于开发，不是跨题独立增量证据。''')
 write('V3_1_Paired_Development_Report.md',f'''# 同算法旧契约 / F / T 配对开发结果

{table}

`—`表示没有可运行契约，语义率未定义，不能把其UNKNOWN=0解释为改善。可判定Design每算法48题，其中8道目标、40道不支持；5算法重复使用同48题，不能把240个算子×题观察说成240道独立题。4份表达式算法的目标还是同8道题。Source和GeneratedDevelopment单独见semantic_metrics.json。

## 来源与对照

F3_F：来源3/3、Design目标8/8；旧接口全部ERROR，T同算法来源1/3、Design4/8。F独有Design正确接受4题，T独有0题。这是最清晰的局部开发改善，既包含字符串→dict接口修复，也包含保留已有解析覆盖；不能全归为学到了新的数学语义边界。

F2_F联合SHA与旧版本完全相同，仍拒绝所有正例；F2_T有2/8目标正确接受。T2_F全部UNKNOWN，T2_T 2/8。T3_F与旧契约的已测行为相同，Design4/8；T3_T 8/8但错误接受2/40，不能用覆盖提升掩盖副作用。F1_T只有1/8目标正确接受，并新增1/40错误接受；F1_F静态失败，不能用于纯语义比较。

双方均形成合法契约的4对，Design目标累计F为12/32、T为16/32；这只是同一批8道表达式题在4个算法上的重复观察，不能作独立样本统计优势判断。F不能据此被认定总体优于T。

## 误触发的具体内容

F1_T把明确“digit repetition is allowed”的题交给不重复枚举算法，实际答案错误。T3_T把两道明确要求括号形式数量（即使数值相同也分别计数）的题交给不同数值计数算法，两题实际答案均错误。固定solve未改变，错误来自契约接受了不同数学目标或约束；这是覆盖提高不能替代语义正确性的直接例子。

## 自动开发控制与停止

F3_F的5条明确支持提案只正确接受2条，仍有过度拒绝；T3_F仍接受3条歧义提案。T3_T还错误接受1条明确不支持提案并接受2条歧义提案。歧义不进入错误接受率的分母/分子，但单列为不安全推断风险。所有原提案与未验证标签保留。

0个版本满足全部冻结开发准入要求。没有因F3的8/8而删除自动控制、收窄统计口径或提前打开Gate。''')
 write('V3_1_Final_Report.md',f'''# V3.1 实验总结

**结论：发现一个冻结算法下的真实契约修订正例，但未证明失败经验总体优于Task-Only；0个版本满足完整开发准入，Gate未启动。**

本轮只修改语义契约。5份算法原样冻结，10次真实DeepSeek请求均正常结束，共生成10份响应；9份契约通过静态检查，1份被拒绝，没有人工补写规则或重复改Prompt。

最有价值的结果是F3：相同solve下，失败证据条件F达到来源3/3、Design正确接受8/8；Task-Only为1/3、4/8。旧契约则接口错误。F减少了当前已见开发题的接口错误与误拒绝，但自动合法正例仍仅2/5，未通过完整准入。

其他算法不支持总体成功：F2原样重复；T2_F全部UNKNOWN；T3_F未消除歧义接受；F1_F静态交付失败。Task-Only有的覆盖更高，同时出现错误接受。结果表明应该同时考察覆盖、误触发、UNKNOWN与ERROR，而不能只统计匹配数。

{table}

## 成本与真实性

真实请求/响应10/10，无新UNKNOWN、无截断，Token **{tokens:,}**，新增API费用估算 **${usd:.8f}**。报价快照在Run启动前保存，按真实cache usage及UTC峰谷费率估算，不是供应商账单。保守预算预留不是实付。继承算法的历史构建费用没有在本轮重复支付，也不能在未来总体收益中删除；本轮不声称摊销回本。

本轮新增Linux Worker函数调用 **{len(worker)}** 次，累计宿主等待 **{sum(x['seconds'] for x in worker):.3f}秒**，本地工具未货币化。算法SHA检查全部通过，历史文件哈希未变。

## 研究边界和下一步

这是已曝光开发材料上的一次配对机制探索。F额外看到部分评价题的旧失败记录；每条件仅一次生成，输入长度也不同。因此F3正例不能替代独立Gate，也不能证明失败经验相对T具有可重复增量。

所有候选保留Shadow。本轮0个满足“全部开发支持正例正确接受、无已知误触发/接口错误/歧义接受”的冻结要求；不为了推进阶段放宽标准。没有读取Gate/Legacy/Fresh，没有FlowEvo规模性能实验，也没有重新生成数学算法。

建议保留F3作为局部修订成功案例，保留F2/T3未改进和T组误触发作为反例。若开展下一轮，需单独冻结合同修订范围及未见验证协议；不能把本轮开发成绩写成独立泛化或失败学习的总体胜利。

完整逐题记录见Run的development/scores.json；语义率、生成失败、成本、哈希与配对差异分别见本报告目录JSON文件。
''')
 save(OUT/'gate_readiness.json',load(RUN/'gate_readiness.json'))
 save(OUT/'manifest.json',dict(run=str(RUN),protocol_sha256=load(RUN/'freeze.json')['sha256'],files={str(p.relative_to(ROOT)):sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'},code={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'scripts/run_math_v31.py',ROOT/'scripts/validate_math_v31.py',ROOT/'FlowEvo/src/failure_evo/math_v31_semantic.py']}))
 print('REPORT',OUT,'TOKENS',tokens,'USD',usd,'WORKER',len(worker))
if __name__=='__main__':report()
