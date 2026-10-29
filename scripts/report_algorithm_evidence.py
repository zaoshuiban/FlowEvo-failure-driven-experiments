import json,pathlib,hashlib,datetime,collections,ast
root=pathlib.Path.cwd();r=root/'runs/algorithm_evidence_20261028_01';out=root/'reports/algorithm_evidence_20261028_01';out.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
summary=load(r/'evaluation/summary.json');protocol=load(r/'protocol.json');tot={a:collections.defaultdict(float) for a in ['T','F','FC']};requests=[];mechanisms=[]
for key,s in summary.items():
 a=s['arm'];d=r/'jobs'/key;z=tot[a];z['attempts']+=1;z['executable']+=s['status']=='STATIC_VALID_SHADOW';z['qualified']+=s['fully_qualified']
 for part in ['source','new_parameters','invalid']:
  for metric in ['n','correct','safe_reject']:z[part+'_'+metric]+=s[part][metric]
 analysis=load(d/'analysis.json');code=(d/'solve.py').read_text();tree=ast.parse(code)
 mechanisms.append(dict(key=key,analysis=analysis,source_sha256=sha(d/'solve.py'),ast_sha256=hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest(),uses_nonlocal=any(isinstance(n,ast.Nonlocal) for n in ast.walk(tree))))
 for line in (d/'provider.jsonl').read_text().splitlines():
  e=json.loads(line)
  if e['kind']!='RAW_RESPONSE':continue
  raw=e['payload']['response'];u=raw['usage'];dt=datetime.datetime.fromtimestamp(e['at'],datetime.timezone.utc);peak=dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10);factor=1 if peak else .5
  cost=(u['prompt_cache_hit_tokens']*.006+u['prompt_cache_miss_tokens']*.3+u['completion_tokens']*1.2)*factor/1e6
  z['calls']+=1;z['estimated_cost_usd']+=cost
  for k in ['prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens']:z[k]+=u[k]
  requests.append(dict(key=key,id=raw['id'],at=e['at'],utc=dt.isoformat(),model=raw['model'],usage=u,price_factor=factor,estimated_cost_usd=cost,finish_reason=raw['choices'][0]['finish_reason']))
 for line in (d/'budget.jsonl').read_text().splitlines():
  e=json.loads(line)
  if e['kind']=='RESERVED':z['sum_reserved_upper_usd']+=e['payload']['cost_upper_microusd']/1e6
workers=[json.loads(l) for l in (r/'evaluation/worker.jsonl').read_text().splitlines()];worker_sec=sum(x['payload']['seconds'] for x in workers)
history=all(sha(pathlib.Path(k))==v for k,v in protocol['history_hashes'].items());source=all(sha(root/k)==v for k,v in protocol['source_hashes'].items());data=all(sha(r/k)==v for k,v in protocol['data_hashes'].items())
audit=dict(history_unchanged=history,frozen_source_unchanged=source,frozen_data_unchanged=data,requests=len(requests),unique_response_ids=len({x['id'] for x in requests}),finish_reasons=dict(collections.Counter(x['finish_reason'] for x in requests)),worker_calls=len(workers),worker_request_wall_seconds=worker_sec,all_worker_gold_exposed_false=all(x['payload']['gold_exposed'] is False for x in workers),all_generation_before_evaluation=max(x['at'] for x in requests)<min(x['at'] for x in workers),unique_source_hashes=len({x['source_sha256'] for x in mechanisms}))
assert history and source and data and len(requests)==36 and audit['unique_response_ids']==36 and len(workers)==507
for name,value in [('aggregate.json',tot),('request_costs.json',requests),('mechanism_audit.json',mechanisms),('integrity.json',audit)]: (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2))
rows='\n'.join(f"| {a} | {int(z['qualified'])}/6 | {int(z['source_correct'])}/{int(z['source_n'])} | {int(z['new_parameters_correct'])}/{int(z['new_parameters_n'])} | {int(z['invalid_safe_reject'])}/{int(z['invalid_n'])} | {int(z['total_tokens']):,} | ${z['estimated_cost_usd']:.6f} |" for a,z in tot.items())
detail='\n'.join(f"| {k} | {s['status']} | {s['source']['correct']}/{s['source']['n']} | {s['new_parameters']['correct']}/{s['new_parameters']['n']} | {s['invalid']['safe_reject']}/{s['invalid']['n']} |" for k,s in summary.items())
text=f'''# T/F/F-C 参数化数学算法生成实验报告

## 结论

实验已完成。三组都能生成正确的参数化计算算法；本轮没有观察到失败信息或纠错分离协议带来数学正确性增量。17份可执行候选全部通过来源、新参数和非法输入检查。T的另一份因`nonlocal`被现有静态权限规则拒绝，未执行，不能标记数学错误。

判定：`ALGORITHM_SYNTHESIS_FEASIBLE / FAILURE_EVIDENCE_INCREMENT_NOT_DEMONSTRATED`。这不证明失败经验普遍无用，只说明在本轮两类计算问题、固定接口、同一模型和两次生成重复下，Task-Only已经足够。未启动语义路由、独立Gate或大规模FlowEvo性能实验。

## 冻结设计

Run：`algorithm_evidence_20261028_01`。协议SHA：`b45313bb39e5c5f58874a49845b4223b187385d5c135ca4f4622343b172d0efb`。

复用12条历史真实数学错误，按已有事件分组形成7/2/3个来源的三组开发材料。后两组属于同一种表达式计算家族，因此不是三个独立机制族。只导入分组ID，不给模型旧机制文本、旧算法或标准答案。固定输入接口由宿主提供；这是给定接口的条件算法合成，不是全自主发现新任务类别。

T只看到来源题面与输入接口；F额外看到真实错误输出及二值反馈；F-C与F使用相同证据，再要求模型区分可能导致失败的操作和自行提出的替代操作。三组共享代码生成提示、模型设置和调用额度。每组每条件生成2次，共18次尝试；每次先分析、再源码生成，最多2请求，无修订、无择优。模型实际使用现有直连DeepSeek `deepseek-flash`，不是GPT；temperature=0.2，thinking disabled，每次输出上限8192。

所有候选生成并冻结后才执行评分。原始长轨迹确定性保留头1400/尾1800字符，附省略长度及完整哈希；全部最终错误输出完整保留。初始截断记录保留TRUNCATED标记，不作为独立数学错误。

## 完整结果

下表保留全部生成尝试，T的未执行项仍在分母中；这些分母是候选×输入观测数，不能当作独立题数。

| 条件 | 全部检查通过候选 | 来源正确 | 新参数正确 | 非法输入安全拒绝 | 全部Token | API估算 |
|---|---:|---:|---:|---:|---:|---:|
{rows}

仅对可执行候选计：T为5/5、F为6/6、F-C为6/6全部正确。新参数分别为100/100、120/120、120/120。不存在某个两边均可运行的配对中，F或F-C正确而T数学错误的情况。

唯一交付分歧`g0-r0-T`使用递归计数及`nonlocal count`，触发现有`UNSUPPORTED_CAPABILITY`。没有人工改写、放宽权限或重试。另一份T数字算法成功，因此不能把该静态拒绝包装成失败证据提高数学算法正确率的证据。

| 候选 | 生成状态 | 来源 | 新参数 | 非法安全拒绝 |
|---|---|---:|---:|---:|
{detail}

## 独立评分与统计单位

共有12个来源参数、40个新参数（数字类20、表达式类20）和12个非法输入。表达式两个来源组共用同20个新参数，不能重复计数。17份候选实际执行507次Worker调用：405次合法输入计算全部正确、102次非法输入均明确抛出ValueError/TypeError或拒绝。非法输入的预期异常是安全拒绝，不是基础设施故障。

新参数和边界分布在模型输出前固定，排除已读取Discovery/Design参数；不读取封存Gate/Legacy/Fresh。新参数不是新原题、自然语言泛化或新的数学家族。52个合法来源/新参数均由两条独立计算路径核对：数字类枚举试除与SymPy素数集合筛选；表达式区间值集合与相邻归约穷举。参考实现只在宿主私有评分，不发送模型/候选。待测算子没有作为自己的Oracle。

执行记录锁定后评分。冻结源码在Linux Worker内真实运行，仅接收参数，无标准答案。没有运行时LLM或按隐藏评分回退，也没有自动授予Experimental权限。

## 失败经验究竟改变了什么

F/F-C的分析确实提及人工枚举中断、猜测小计、提前折叠表达式和集合遗漏。F-C明确填写了错误操作与替代操作；T没有历史轨迹，主要依据题意推导算法。这是分析内容差异。

但是生成的计算核心趋同：数字类遍历合法数字排列并精确检验素数；表达式类对所有切分传播结果集合并去重。Task-Only同样自行提出了这些方法。18份源码哈希各不相同，但不同代码文本不是18种新能力。F-C更清楚地描述了不能提前化简，并没有在本轮带来额外通过案例。

尤其应保留`g1-r0-F`的诊断局限：它描述某次乘法前缀化简为“correctly reduced”，但最终仍生成完整区间算法并通过测试。模型对失败原因的文字解释不是已验证的因果结论，不能用源码正确反向证明所有诊断都正确。

## 成本及完整性

36次真实请求、36个不同响应ID，全部finish_reason=stop；无截断或UNKNOWN。总Token {int(sum(z['total_tokens'] for z in tot.values())):,}；按请求时段和缓存命中拆分估算API费用${sum(z['estimated_cost_usd'] for z in tot.values()):.6f}，不是供应商账单。所有分析、生成及静态拒绝费用均计入。预留上界合计${sum(z['sum_reserved_upper_usd'] for z in tot.values()):.6f}，与估算消费分列，不称为实付。

使用冻结官方报价快照`pricing.html`：峰时输入缓存命中$0.006/百万、未命中$0.30/百万、输出$1.20/百万，非峰时折半；逐请求时间、usage和费用见`request_costs.json`。Worker调用墙钟累计{worker_sec:.3f}秒，不包含全部准备/容器启动和人工时间，未货币化；不据此宣称长期净收益。

10项零API测试通过。复核当前源码、数据与历史产物冻结哈希全部一致。所有模型响应早于首次评分执行，所有Worker记录gold_exposed=false。旧P2/V3.4记录未改写。

## 限制与下一步

只有12道曝光来源、两个计算家族、每组两次生成；本轮没有等Token中性对照，F/F-C输入更长。结果支持参数化源码生成可行，不支持失败经验的独立收益，也不证明语义路由或跨原题泛化。

建议停止围绕这两个已出现天花板的计算家族继续重复生成。若继续研究，先预注册其他真实失败机制和Task-Only基线，检验失败轨迹是否提供题面本身缺少的可执行信息；不得根据生成成绩挑选F获胜样本。当前不自动扩大实验。

## 可追溯交付

原始请求/响应、18份源码、分析及账本位于`runs/algorithm_evidence_20261028_01/jobs/`。冻结协议、来源投影、候选冻结及Worker锁定输出均在同Run；报告目录含逐请求费用、聚合成绩、机制原文与完整性检查。新增实验及报告代码仅为五个脚本，复用既有Compiler、预算与Worker，没有新增路由或代际机制。
'''
(out/'Algorithm_Evidence_Final_Report.md').write_text(text)
(out/'README.md').write_text('# 算法生成信息增量实验\n\n详见 [完整中文报告](Algorithm_Evidence_Final_Report.md)。\n\n结论：三组均能生成正确算法，失败经验的数学正确性增量未得到证明。T的一次静态权限拒绝单列，不能当作数学错误。\n')
print(json.dumps(dict(totals=tot,audit=audit),ensure_ascii=False,indent=2))
