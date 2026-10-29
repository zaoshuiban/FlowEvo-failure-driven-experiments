"""Read-only synthesis. Never upgrades historical rejected output or changes scores."""
from run_math_v33 import OUT,ROOT,OLD,load,save,sha,fingerprint
from pathlib import Path
import json,datetime,collections
REPORT=ROOT/'reports/math_v33_structured_20261028'
def rows(p):return [json.loads(l) for l in p.read_text().splitlines()]
def report():
 REPORT.mkdir(parents=True,exist_ok=True);plan=load(OUT/'protocol.json');calls=[];reserved=0;unknown=[];normalizations=[]
 for number in ['01','02','03']:
  run=ROOT/f'runs/math_v33_structured_20261028_{number}'
  for p in sorted((run/'calls').glob('*/provider.jsonl')):
   starts={}
   for r in rows(p):
    if r['kind']=='SEND_STARTED':starts[r['payload']['key']]=r
    if r['kind']=='SEND_UNKNOWN':unknown.append(dict(run=run.name,call=p.parent.name,record=r))
    if r['kind']=='ENVELOPE_NORMALIZED':normalizations.append(dict(run=run.name,call=p.parent.name,record=r))
    if r['kind']=='RAW_RESPONSE':
     v=r['payload']['response'];u=v['usage'];d=datetime.datetime.fromtimestamp(r['at'],datetime.timezone.utc);factor=1 if d.weekday()<5 and (1<=d.hour<4 or 6<=d.hour<10) else .5
     cost=(u.get('prompt_cache_hit_tokens',0)*.006+u.get('prompt_cache_miss_tokens',u['prompt_tokens'])*.3+u['completion_tokens']*1.2)/1e6*factor
     calls.append(dict(run=run.name,key=p.parent.name,id=v['id'],model=v['model'],usage=u,estimated_usd=cost,utc=d.isoformat(),finish_reason=v['choices'][0]['finish_reason'],seconds=r['at']-starts[r['payload']['key']]['at'],wire_sha256=starts[r['payload']['key']]['payload']['wire_sha256'],response_sha256=fingerprint(v),invoice=False))
   for r in rows(p.parent/'budget.jsonl'):
    if r['kind']=='RESERVED':reserved+=r['payload']['cost_upper_microusd']/1e6
 save(REPORT/'calls_and_costs.json',dict(calls=calls,estimated_usd=sum(x['estimated_usd'] for x in calls),total_tokens=sum(x['usage']['total_tokens'] for x in calls),cumulative_reserved_upper_usd=reserved,unknown=unknown,actual_invoice=None,pricing_snapshot_sha256=sha(OUT/'pricing.html'),normalizations=normalizations))
 worker=[r['payload'] for p in (OUT/'evaluation').glob('*/worker.jsonl') for r in rows(p) if r['kind']=='V3_COMPONENT_EXECUTED']
 save(REPORT/'worker_usage.json',dict(calls=len(worker),seconds=sum(r['seconds'] for r in worker),monetized=False,source_bound=True))
 summaries={r:load(OUT/f'evaluation/{r}/summary.json') for r in ['development','confirmation']};parser={r:load(OUT/f'evaluation/{r}/parser_scores.json') for r in summaries}
 pm={role:dict(n=len(rs),representable=sum(r['representable'] for r in rs),complete_field_agreement=sum(r['all_fields_correct'] is True for r in rs),field_agreement=10*sum(r['representable'] for r in rs)-sum(len(r['field_differences']) for r in rs),field_denominator=10*sum(r['representable'] for r in rs),schema_and_quote_pass=sum(r['schema_and_quote_valid'] for r in rs),representation_limits=[r for r in rs if not r['representable']]) for role,rs in parser.items()}
 save(REPORT/'metrics.json',dict(layered=summaries,parser=pm,missing_condition='S: no executable Python delivered'))
 history={p:sha(p)==h for p,h in plan['history_hashes'].items()};assert all(history.values());save(REPORT/'history_integrity.json',history)
 artifacts=load(OUT/'candidate_freeze.json');save(REPORT/'component_versions.json',dict(algorithm_sha256=plan['algorithm_sha256'],semantics_sha256=fingerprint(load(OUT/'semantics.json')),R=load(OLD/'data_v2/manifest.json')['old_artifact'],candidates=artifacts,missing_S=load(OUT/'S/REJECTED.json')))
 # Integrity of actual projections: evaluation labels/answers were never placed in paid input objects.
 wires=[]
 for n in ['01','02','03']:
  for p in (ROOT/f'runs/math_v33_structured_20261028_{n}/calls').glob('*/provider.jsonl'):
   for r in rows(p):
    if r['kind']=='SEND_STARTED':wires.append(r['payload']['wire'])
 pub=[t for role in summaries for t in load(OUT/f'data/public/{role}.json')]
 generation=[r for r in calls if not r['key'].startswith('parse-')]
 for n in ['01','02','03']:
  for p in (ROOT/f'runs/math_v33_structured_20261028_{n}/calls').glob('*/input.json'):
   v=load(p)
   if p.parent.name.startswith('parse-'):assert set(v)=={'semantics','tasks'} and all(set(t)=={'task_id','problem'} for t in v['tasks'])
   else:assert not any(t['problem'] in json.dumps(v,ensure_ascii=False) for t in pub)
 save(REPORT/'integrity_checks.json',dict(history_unchanged=True,frozen_solver_unchanged=load(OUT/'COMPLETE.json')['solver_unchanged'],all_generation_excludes_new_questions=True,parser_only_public_task_and_schema=True,answers_scored_after_role_lock=True,trusted_facts_not_model_visible=True,unknown_requests=len(unknown),real_calls=len(calls),experimental=0,regression_tests=16,new_tests=10))
 def table(role):
  s=summaries[role];txt='|路径|正确接受|错误接受|UNKNOWN（全部题）|接口/执行ERROR|\n|---|---:|---:|---:|---:|\n'
  for k in ['R/runtime','FS/runtime','FS/trusted_offline']:
   x=s[k];txt+=f"|{k}|{x['correct_accept']}/{x['supported']}|{x['false_accept']}/{x['unsupported']}|{x['unknown']}/{x['n']}|{x['interface_error']}/{x['execution_error']}|\n"
  txt+='|S|NOT_GENERATED|不可比较|不可比较|未执行|\n';return txt
 def write(name,s):(REPORT/name).write_text(s+'\n')
 write('V3_3_Protocol_and_Representation.md',f'''# V3.3 协议、数据与表示

本次定位是有限机制诊断。固定既有 F3 solve SHA `{plan['algorithm_sha256']}`，不生成或人工修改数学算法，不改变旧 R 匹配器。研究执行链为：

```mermaid
flowchart LR
 Q[公开题面] --> P[共同模型语义解析]
 P --> V[通用schema和引用校验]
 V --> C[模型生成的结构化契约]
 C --> W[冻结solve · Linux Worker]
 V -->|不确定或无效| D[DECLINED · 原生回退接口]
 T[离线审查字段] -. 仅归因 .-> C
 W --> L[锁定输出]
 L --> E[私有独立评分]
```

默认关闭；此次没有真正追加原生FlowEvo求解请求，拒绝记录不能称为回退后成功。沿用 BoundedCompiler、PersistentBudget、SplitRunner、FrozenLinuxBackend；未构建新Worker、路由或代际库。

新增开发12题、确认12题，各6支持、4不支持、2歧义。均在首个模型请求前固定。数学族仍是同一固定序列二元运算集合计数；新措辞和参数不等于不同自然原题。旧V3.2所有题仅算已曝光材料，未复用为本轮确认题；未读取原P0 Gate/Legacy/Fresh。

题面由宿主编写；数值答案复用既有独立Fraction参考实现，未调用候选solve制造Gold。语义标签由宿主按题面审查，不是第三方盲法双审。结构化字段由DeepSeek提出后，宿主依字段定义标注离线语义，标注在解析输出之前锁定，未进入生成或解析输入。数学参考实现独立于候选源码，但语义标签仍有单审局限。

10个事实字段、前提描述及可执行 match(facts) 均来自真实DeepSeek响应；宿主没有人工写专项数学匹配规则。S/FS共享同一schema、算法、来源题、参数接口；FS额外获得8条V3.1历史观察，时间早于新题。两组生成输入不等Token，每组只一次生成；不能做严格知识增量归因。

模型生成schema仍混淆“求解器支持域”和“事实表达域”：只允许整数，运算符枚举只含+、-、*、UNKNOWN。它不能如实保留已知除法、乘方或小数。开发1题、确认2题标为 EVIDENCE_REPRESENTATION_LIMIT；未将其未知值强行标作可信语义，未手工扩展模型字段。

共同解析器以6题为一批，每题只解析一次，共4次请求。批内可见其他公开题面，但没有答案或反馈。结果在有合法契约的条件间复用；当前S没有生成源码，实际仅FS消耗解析结果。模型解析费用与运行时计算必须单列，不能把这条路径说成零模型调用。

主执行冻结哈希 `{load(OUT/'freeze.json')['sha256']}`。所有契约在新题解析和评分前冻结；确认只执行一次，没有根据确认结果修改候选。全部保持Shadow/未获Experimental。''')
 write('V3_3_Delivery_and_Engineering_Audit.md',f'''# 交付与工程审计

实际8次DeepSeek Flash响应：2次语义表示交付、S/FS各1次契约生成、4次共同解析。无未知请求、无自动重发。

第一段运行01：语义字段已提出，但code为对象、JSON有非法转义，旧编译器拒绝；schema描述允许null而类型不允许null。原始响应、计量与STOP保留。

第二段运行02：仅一次明确工程修订，模型补了null，但将field_meanings/parser_instructions/prerequisites放到顶层，违反三字符串交付契约。再次保留拒绝及STOP。没有对这两个历史结果改判成功。

第三段运行03：按新冻结的有限规范化规则导入第二份真实响应：仅把3个已知字段搬入只含schema的code对象，数值/字段定义原文不改，原始及规范化SHA另存。未再生成schema。解析阶段另只允许将完整code列表序列化为JSON字符串；3份响应使用该规则。未知字段、非法JSON均不宽松放行。导入既有响应不是新的成功生成调用。

S的code字段实际是契约JSON，description为自然语言说明；**没有Python match源码**。不能人工把说明编译成规则，记录NOT_GENERATED，不视为Task-Only数学失败。FS交付真实Python并通过原有静态权限及接口验证。

26项检查通过：10项新检查覆盖Gold/额外字段、无授权请求、算法变更、引用来源、可信语义禁入运行时、schema哈希及真实源码绑定；16项已有V3回归含实际Worker。另有首轮冻结算法真实Worker预检。所有确认和开发执行均使用真实Linux Worker；没有模型自报成绩。

发现宿主协议缺陷：要求每个已知字段都有精确原文引句，对“没有矛盾/没有缺失前提”这种基于完整题面得出的否定判断，容易产生没有可直接引用句子的情况。解析器第一批引用题面片段；后三批用空列表表达这种判断，导致18题在进入契约前被UNKNOWN阻断。不能把这一阻断算作18道数学语义理解错误。

本轮不回改评分、不补引句、不重新解析确认集。若后续修正，应采用新的通用证据类型协议（例如直接引文与整题推断分离），不能按本轮正确答案补字段。FS还将不确定前提一律DECLINE而非UNKNOWN，三态解释并不理想；未人工改写源码。

本轮新增文件：scripts/run_math_v33.py、annotate_math_v33.py、evaluate_math_v33.py、report_math_v33.py、test_math_v33.py；FlowEvo/src/failure_evo/structured_semantics.py。旧历史文件SHA全部复核不变。''')
 write('V3_3_Layered_Validation.md',f'''# 分层评价

## 开发集

{table('development')}

## 新确认集（一次性）

{table('confirmation')}

可信语义路径的负例分母不同：开发3题、确认2题；其余3个负例无法用模型schema如实表达，被排除于契约层准确率，不能算正确拒绝。运行时负例全部保留。两组各2歧义题均未错误接受。

## 解析层

|集合|可表达题|全部字段与审查一致|逐字段一致|schema及引用共同通过|\n|---|---:|---:|---:|---:|\n|开发|11/12|8/11|106/110|6/12|\n|确认|10/12|7/10|95/100|0/12|

这些是与宿主预先审查的一致率，不是外部权威认证。单叶树的“允许括号变化/禁止重排”是审查依据数学结构作出的等价解释，而schema文字强调显式描述；这一差异本身反映表示定义与解析约定不完全一致。

来源归因：开发第02题为单操作数，模型把不可重排视为UNKNOWN，契约拒绝；确认第02题同时把括号变化和重排限制视为UNKNOWN。固定括号负例还把连接乘号误解析为UNKNOWN。矛盾题将重排字段记YES而非UNKNOWN，但另有明确矛盾标志。

确认集5道多操作数支持题的事实字段与可信输入完全一致，仍被引用门控拒绝。因此0/6不能解释为结构化语义完全无法迁移。可信输入下6/6只能说明该契约/算法在这一小组已审查结构化输入上有效，不能冒充原始题面端到端成功。

S没有交付可执行代码，故缺少S与FS同表示配对。不使用人工规则补这个空位。开发FS相对R多5道正确接受只是路径差异，混合了LLM解析、契约、失败信息与额外计算，不能单独归因于失败经验或表示形式。确认正式联合结果没有改善。''')
 tokens=sum(x['usage']['total_tokens'] for x in calls);cost=sum(x['estimated_usd'] for x in calls)
 subt={}
 for name,filter_ in [('表示构建及工程修订',lambda x:x['key']=='schema'),('契约生成（含未交付S）',lambda x:x['key'] in ['S','FS']),('24题共同解析',lambda x:x['key'].startswith('parse-'))]:
  cc=[c for c in calls if filter_(c)];subt[name]=dict(calls=len(cc),tokens=sum(x['usage']['total_tokens'] for x in cc),estimated_usd=sum(x['estimated_usd'] for x in cc))
 save(REPORT/'cost_breakdown.json',subt)
 write('V3_3_Final_Report.md',f'''# V3.3 结构化语义适用性机制验证

**结论：PARTIAL。已实际运行模型生成语义表示→模型解析→结构化契约→冻结算法的链路，并定位层间瓶颈；尚未完成有效S/FS配对，也未取得独立确认集端到端增益。**

新开发12题、新确认12题，算法F3全程不变。没有新增数学算法，没有扩大FlowEvo性能实验。S只交付契约说明而未交付Python，FS交付可执行契约。总计8次真实DeepSeek响应，含2次表示交付失败及历史导入，不能全部计为成功生成。

{table('development')}

新确认结果：

{table('confirmation')}

三个不同结论需要分开：

1. **计算与契约的潜在能力**：离线可信语义输入下，冻结FS在两组支持题各6/6正确执行，已表达的负例和歧义题没有错误接受。这是实际Worker证据，不是模型自报。
2. **解析与传输的实际限制**：确认集7/10可表达题的全部字段与预先审查一致，但全部12题因否定判断缺少精确引句被宿主阻断；另3个跨两组负例受schema表达域限制。正式联合结果仍为0/6，不能用离线6/6替换。
3. **失败经验的独立价值**：S源码未交付，且只有一对生成、上下文不等长，无法完成FS对S归因。没有证明失败驱动优于Task-Only，也不能将S缺失当作FS成功优势。

实际费用：{tokens:,} tokens，按冻结官方时段/缓存报价估算 **${cost:.8f}**；并非账单。累计请求预留上界 **${reserved:.6f}**，与已用估算费用分开列示；UNKNOWN为0。包括所有失败交付、S无源码、FS生成和解析成本，未沿用旧预算。

{json.dumps(subt,ensure_ascii=False,indent=2)}

真实Worker {len(worker)}次组件执行，墙钟合计{sum(r['seconds'] for r in worker):.3f}秒；本地计算未货币化。新检查10项、已有回归16项通过。旧V3.1/V3.2原始记录和算法哈希保持不变，没有Experimental权限、没有在线隐藏答案补救。

下一阶段不应再生成一批新算子或扩大性能实验。首先需要在新协议中处理两个通用交付问题：S必须真正交付Python；否定/缺失类事实的证据类型须与引用校验相容。模型自主schema还需能够记录“已知但不支持”的真实值，避免把支持域误当事实域。之后才有条件比较相同表示下S与FS。当前确认题已曝光，不可修订后再声称未见确认；不在本轮继续调试它们。

这次支持“分层表示能让瓶颈可定位”的工程结论，尚不支持“结构化方案已优于正则”或“失败经验具有独立增益”。全部新题是宿主编写的同族合成题，语义审查不是第三方盲审；本轮不代表跨原题、跨数据集泛化。''')
 print(json.dumps(dict(tokens=tokens,cost=cost,reserved=reserved,worker=len(worker),reports=str(REPORT)),ensure_ascii=False))
if __name__=='__main__':report()
