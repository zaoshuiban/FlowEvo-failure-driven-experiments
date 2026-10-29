"""Read-only report. All raw scores remain immutable; annotation qualifications explicit."""
import json,datetime,collections,time
from run_math_v34 import OUT,OLD,ROOT,load,save,sha,fingerprint,verify
REP=ROOT/'reports/math_v34_evidence_20261028'
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def report():
 REP.mkdir(parents=True,exist_ok=True);plan=verify();costs=[];unknown=[];reserved=0
 for p in sorted((OUT/'calls').glob('*/provider.jsonl')):
  starts={}
  for r in rows(p):
   if r['kind']=='SEND_STARTED':starts[r['payload']['key']]=r
   if r['kind']=='SEND_UNKNOWN':unknown.append(r)
   if r['kind']=='RAW_RESPONSE':
    v=r['payload']['response'];u=v['usage'];d=datetime.datetime.fromtimestamp(r['at'],datetime.timezone.utc);factor=1 if d.weekday()<5 and (1<=d.hour<4 or 6<=d.hour<10) else .5
    costs.append(dict(key=p.parent.name,id=v['id'],model=v['model'],usage=u,utc=d.isoformat(),finish_reason=v['choices'][0]['finish_reason'],seconds=r['at']-starts[r['payload']['key']]['at'],estimated_usd=(u.get('prompt_cache_hit_tokens',0)*.006+u.get('prompt_cache_miss_tokens',u['prompt_tokens'])*.3+u['completion_tokens']*1.2)/1e6*factor,invoice=False,wire_sha256=starts[r['payload']['key']]['payload']['wire_sha256'],response_sha256=fingerprint(v)))
  for r in rows(p.parent/'budget.jsonl'):
   if r['kind']=='RESERVED':reserved+=r['payload']['cost_upper_microusd']/1e6
 usd=sum(c['estimated_usd'] for c in costs);tokens=sum(c['usage']['total_tokens'] for c in costs)
 save(REP/'costs.json',dict(calls=costs,total_tokens=tokens,estimated_usd=usd,cumulative_reserved_upper_usd=reserved,unknown_requests=unknown,actual_invoice=None,pricing_sha256=sha(OUT/'pricing.html')))
 breakdown={}
 for group,keys in [('schema',['schema-0','schema-1']),('S',['S-0','S-1']),('FS',['FS-0','FS-1']),('shared_parser',[c['key'] for c in costs if c['key'].startswith('parse-')])]:
  cc=[c for c in costs if c['key'] in keys];breakdown[group]=dict(calls=len(cc),tokens=sum(c['usage']['total_tokens'] for c in cc),estimated_usd=sum(c['estimated_usd'] for c in cc))
 save(REP/'cost_breakdown.json',breakdown)
 worker={}
 for scope in ['evaluation','historical_replay','interface_probe']:
  rr=[r['payload'] for p in (OUT/scope).rglob('worker.jsonl') for r in rows(p) if r['kind']=='V3_COMPONENT_EXECUTED'];worker[scope]=dict(calls=len(rr),wall_seconds=sum(r['seconds'] for r in rr),monetized=False)
 save(REP/'worker_cost.json',worker)
 summary={r:load(OUT/f'evaluation/{r}/summary.json') for r in ['development','confirmation']};scores={r:load(OUT/f'evaluation/{r}/scores.json') for r in summary};pa={r:load(OUT/f'evaluation/{r}/parser_audit.json') for r in summary}
 paired={}
 for role,rr in scores.items():
  by={k:{r['task_id']:r for r in rr if r['candidate']==k and r['path']=='runtime'} for k in ['S','FS']}
  paired[role]=dict(fs_only=sum(by['FS'][k]['correct_accept'] and not by['S'][k]['correct_accept'] for k in by['S']),s_only=sum(by['S'][k]['correct_accept'] and not by['FS'][k]['correct_accept'] for k in by['S']),both=sum(by['S'][k]['correct_accept'] and by['FS'][k]['correct_accept'] for k in by['S']),s_false=sum(x['false_accept'] for x in by['S'].values()),fs_false=sum(x['false_accept'] for x in by['FS'].values()))
 save(REP/'paired_results.json',paired)
 parsemetric={role:dict(n=len(rr),schema_valid=sum(x['schema_valid'] for x in rr),evidence_valid=sum(x['evidence_valid'] for x in rr),numeric_and_operator_exact=sum(x['parameter_values_exact'] for x in rr),zero_issue_review_false_premise_fill=False) for role,rr in pa.items()}
 save(REP/'metrics.json',dict(raw=summary,parser=parsemetric))
 # Audit an independently found annotation overreach; do not alter original locked rows.
 qualification=dict(task_id='v34-confirmation-06',path='trusted_offline',issue='Host annotation filled counting_rule=count distinct values for a minimum query which does not state a counting rule. This is an offline annotation overreach. Main runtime and task support labels unaffected.',decision='Exclude this row from reviewed trusted-negative rates; preserve raw result as an artificial goal probe, not trustworthy task-grounded confirmation.',no_rerun=True)
 save(REP/'annotation_qualification.json',qualification)
 filtered={}
 for role,rr in scores.items():
  filtered[role]={}
  for arm in ['S','FS']:
   rs=[r for r in rr if r['candidate']==arm and r['path']=='trusted_offline' and not (role=='confirmation' and r['task_id']==qualification['task_id'])]
   filtered[role][arm]=dict(supported=sum(x['supported'] is True for x in rs),correct_accept=sum(x['correct_accept'] for x in rs),unsupported=sum(x['supported'] is False for x in rs),false_accept=sum(x['false_accept'] for x in rs),excluded_unverified=1 if role=='confirmation' else 0)
 save(REP/'reviewed_trusted_metrics.json',filtered)
 history={p:sha(p)==h for p,h in plan['history_hashes'].items()};assert all(history.values());save(REP/'history_integrity.json',history)
 # Generated S repair is a binding-only AST change; all semantics outside that value preserved.
 from repair_math_v34_interface import normalized_tree
 f=load(OUT/'candidate_freeze.json');s0=load(OUT/'S/version0/artifact.json');s1=f['artifacts']['S']
 assert normalized_tree(__import__('pathlib').Path(s0['matcher_path']).read_text())==normalized_tree(__import__('pathlib').Path(s1['matcher_path']).read_text())
 save(REP/'source_versions.json',dict(protocol_sha256=load(OUT/'freeze.json')['sha256'],semantics_sha256=fingerprint(load(OUT/'semantics.json')),solver_sha256=plan['solver_sha256'],final_artifacts=f['artifacts'],S_initial=s0,solver_unchanged=load(OUT/'COMPLETE.json')['solver_unchanged'],S_repair_AST_binding_only=True))
 eval_at=load(OUT/'evaluation_started.json')['at'];assert all(datetime.datetime.fromisoformat(c['utc']).timestamp()<eval_at for c in costs)
 allnew=[t for role in summary for t in load(OUT/f'data/public/{role}.json')]
 for p in (OUT/'calls').glob('*/input.json'):
  v=load(p)
  if p.parent.name.startswith('parse-'):assert set(v)=={'semantics','tasks'} and all(set(t)=={'task_id','problem'} for t in v['tasks'])
  else:assert not any(t['problem'] in json.dumps(v,ensure_ascii=False) for t in allnew)
 save(REP/'integrity.json',dict(old_history_unchanged=True,all_paid_calls_before_scoring=True,no_new_task_in_contract_or_repair=True,parser_has_no_answers_or_annotations=True,shared_parser_identical_for_S_FS=True,unknown_requests=len(unknown),experimental=0,tests_new=14,tests_regression=16,engineering_timing_deviation=load(OUT/'engineering_timing_amendment.json')))
 # Per-case source-grounded interpretation audit, separate from exact string comparisons.
 notes={
 'development':['Allowed-transformations value has wrong scalar type; semantic content otherwise present.','Allowed-transformations scalar instead of array; meanings present.','Scalar type; order null on one-leaf case, implicit-order interpretation uncertain.','Scalar type; operands/operators preserve negative first literal.','Counting rule null despite cardinality of a value set.','Counting rule null despite explicit unique results.','Distinct-result summation correctly identified; deduplication not retained in counting field.','Division symbol preserved; distinct-result convention left null.','Explicit operand permutation retained; no missing prerequisite fabricated.','Decimal 1.25 preserved without rounding.','Unstated reordering stays null; correct conservative handling.','Unstated operations stay null; correct conservative handling.'],
 'confirmation':['Allowed transformations null despite arbitrary full binary execution trees.','Transformation and counting fields null despite all full binary shapes and distinct evaluations.','Single-leaf transformation/order/deduplication under-specified in parser; annotation implicitness caveat.','Relevant mathematical meanings retained in noncanonical phrases.','Relevant mathematical meanings retained in noncanonical phrases.','Relevant mathematical meanings retained in noncanonical phrases.','Minimum quantity correctly retained; counting rule null is appropriate, original offline annotation overreached.','Exponentiation preserved; requested-quantity string omits explicit count verb.','Tree-counting rather than value-counting explicitly retained.','Mandatory unchanged parentheses represented as null transformations rather than explicit no-change; leads conservative unknown.','Unstated order remains null and review unresolved; distinct count also omitted.','Contradiction quoted and review CONFLICT; incompatible counting descriptions retained verbatim, host blocks execution.']}
 audit=[]
 for role in summary:
  for i,r in enumerate(pa[role]):audit.append(dict(role=role,task_id=r['task_id'],schema_valid=r['schema_valid'],evidence_valid=r['evidence_valid'],parameters_exact=r['parameter_values_exact'],finding=notes[role][i],reviewer='host single semantic review; not blinded second reviewer',used_for_model_revision=False))
 save(REP/'per_task_semantic_review.json',audit)
 def write(n,s):(REP/n).write_text(s+'\n')
 def table(role):
  txt='|版本/路径|正确接受|错误接受|UNKNOWN（全部12题）|接口/计算ERROR|\n|---|---:|---:|---:|---:|\n'
  for name in ['R/runtime','S/runtime','FS/runtime']:
   x=summary[role][name];txt+=f"|{name}|{x['correct_accept']}/6|{x['false_accept']}/4|{x['unknown']}/12|{x['interface_error']}/{x['execution_error']}|\n"
  return txt
 write('V3_4_Evidence_Protocol.md',f'''# 统一语义事实与证据协议

新增默认关闭模块 semantic_evidence_v2.py，复用编译预算、SplitRunner和Linux Worker。未修改F3算法，SHA `{plan['solver_sha256']}`；旧V3.3模块和历史Run保持原样。

事实值与证据分离：每个字段附kind、quotes、scope、rule、from_field。明确肯定/否定要求真实原文引用；NOT_STATED和UNRESOLVED必须value=null，不能以缺失推出禁止或允许。DERIVED仅支持宿主可机械核验的EXACT_COPY和LIST_LENGTH，不接受模型自创推理规则，拒绝循环依赖。

全文review独立于facts。NO_ISSUE_OBSERVED允许空引文，但不是任何数学前提的证据；不能补全缺失事实。CONFLICT需要对应原文，UNRESOLVED保留不确定。进入运行前，模型契约声明的必要字段为空时返回UNKNOWN。实际值不受solver支持域限制：除法、乘方、非整数可进入事实表示，再由契约拒绝。

引用验证只证明来源绑定，不能机械证明语义蕴含；必要字段列表也由模型声明，可能遗漏数学前提。因此不能把协议通过等同数学正确或自动准入。

语义schema仍由DeepSeek生成。初稿只复制operands/operators，保留integer限制，未描述目标和变换；经预定一次表示修订，增加目标、允许变换、顺序约束及计数方式，number和开放operator string保留不支持的实际值。模型自己选择字段及含义，没有人工写数学规则。修订没有看到新任务或其结果。

表示的新局限：目标和约束仍是自由文本字段，并非稳定的机器语义标识。共同解析器与契约对这些字符串没有可靠共同约定；这不能称为已解决数学语义表示。

14项零API检查和16项原V3回归通过。首次测试有一项Mock夹具缺少显式sender，后修正夹具；schema首请求已在该次shell序列中启动，应记录这一执行顺序偏差。该错误未涉及生产证据校验，后续真实契约生成前14项全通过。''')
 replay=load(OUT/'historical_replay/summary.json')
 write('V3_4_Historical_Replay.md',f'''# V3.3 已曝光材料只读回放

0次新模型调用。固定旧FS契约、旧算法与原解析事实；仅将旧模型的explicit_contradiction/missing_premises元审查状态迁移到全文review，将UNKNOWN用于验证时映射为空，执行旧契约时仍传原事实。不给其他约束免除引用检查。

{json.dumps(replay,ensure_ascii=False,indent=2)}

开发5/6、原确认5/6，错误接受均0/4。24题证据格式均可通过；单叶题等缺失前提仍不能自动变为允许。旧V3.3确认0/6不改写，以上是曝光材料的兼容性回放，不是新泛化结果或新模型学习。

这说明旧宿主引用政策确实造成了可移除阻断；不能说明新解析器一定准确，也不能证明失败经验优于Task-Only。''')
 write('V3_4_Paired_Validation.md',f'''# S/FS配对与分层验证

两组相同F3、相同模型生成schema、共同解析器及输出、同一Worker与执行接口、同一模型/温度/调用上限。S只看算法和旧来源题面；FS另看8条时间更早的真实历史契约观察。没有新题、答案或Gold反馈进入契约生成。

两组首轮都生成真实Python，均未由宿主补写。S存在MATCH目标回传字段与自身声明不一致的接口问题；用非评价数据的工程探针发现后，使用预定一次修订，AST检查确认只改MATCH返回目标绑定，所有条件分支不变。FS工程探针通过，不使用修订。两组修订上限相同，但实际S2次、FS1次，费用分别记录。

**时序偏差**：初版候选冻结与共同解析启动后，才完成S工程探针及绑定修订。最终候选在任何新题评分之前重新冻结，旧冻结单保存；修订输入没有新题、解析结果或评分，解析未重发。此偏差与原计划“解析前冻结最终版本”不符，不能隐藏。仍可作有限开发诊断，不宣称严格无偏确认。

## 新开发12题

{table('development')}

## 新确认12题

{table('confirmation')}

两组各6支持、4不支持、2歧义。新题为事前编写的同数学族合成题，不是不同自然原题。确认结果只评价一次，不回流模型。FS没有独有正确接受；确认中S独有正确接受3题。FS少一次错误接受伴随零有效覆盖，不能称为增益。

## 分层归因

开发4/12解析出现allowed_transformations从array变成string，按冻结类型规则拒绝，没有事后将字符串包装为列表来改善成绩；确认12/12通过schema和证据检查。两组所有24题的数值及operator提取与预先审查相同，除法、乘方、小数真实值都保留了。后续错误主要在语义字段遗漏和契约逻辑，不再是全文否定审查缺引文。

开发剩余两道支持题把“value set/unique”所表达的计数规则置空。确认前三道支持题遗漏允许变换或计数条件；后三道支持题含充分语义，但FS只检查字段内是否有parenthes片段，将association等同义描述拒绝。S只检查字段非空和类型，没有真正验证目标/权限，因此确认正确接受3题的同时错误接受树计数题。

## 离线可信语义与注释质量

两组在规范化离线支持语义下均6/6，但S在开发两个负例（求和、允许重排）错误接受，FS在求和负例错误接受。它的目标检查只是包含distinct/value/result，并未验证所求量必须是数量。

原始离线确认统计S错误接受3/4、FS1/4。审计发现确认06最小值题的人工离线注释把未声明的counting_rule填成count distinct values；该行不是可靠题面事实，现标为UNVERIFIED、只保留为人工目标探针，不改写原输出，不重跑。排除这行后的已审查离线负例为S2/3、FS0/3；两个版本均不能因此忽略开发中的真实错误接受。主runtime成绩不受此注释问题影响。

“全部字段精确相等”不适合本轮自由文本schema；报告分别给出数值/符号一致性、类型与证据通过率，以及逐题语义审查，不把同义措辞差异误算为语义错误。注释由同一宿主审查，非第三方盲法，应保留单审局限。

S/FS各一份生成、未做等Token非失败P、输入长度不同，本轮不能估计失败经验的稳定因果效应。没有任何候选获得Experimental或大规模试用资格。''')
 write('V3_4_Cost_and_Integrity.md',f'''# 调用、成本与完整性

真实DeepSeek响应{len(costs)}次：schema2次、S生成及接口修订2次、FS生成1次、共同解析6次。无UNKNOWN、无自动重发、无评分后新请求。

总tokens {tokens:,}；按冻结官方报价及缓存/时段估算 **${usd:.8f}**。累计请求预留上界 **${reserved:.6f}**；不是实付账单。报价原页已保存，来源为 https://api-docs.deepseek.com/quick_start/pricing 。

{json.dumps(breakdown,ensure_ascii=False,indent=2)}

{json.dumps(worker,ensure_ascii=False,indent=2)}

共同解析仅真实调用一次并为两组共享，不能把实际付费总额重复加两遍。若估计分别部署S、FS的在线开销，每组均应计入该解析成本；本轮没有证明在线省钱。历史回放、工程探针和新实验Worker成本单列，本地计算尚未货币化。

协议SHA `{load(OUT/'freeze.json')['sha256']}`；语义SHA `{fingerprint(load(OUT/'semantics.json'))}`。每次调用原始wire/response、精确代码、两份候选冻结单、接口修订AST约束、题目角色与输出锁、历史SHA对照均保存。旧V3.2/V3.3全部文件保持原哈希。无数学算法变更，无旧Suspended恢复，无Gate反馈修订。

新增/修改本轮文件：semantic_evidence_v2.py；scripts/run_math_v34.py、math_v34_data.py、test_math_v34.py、replay_math_v34.py、annotate_math_v34.py、repair_math_v34_interface.py、evaluate_math_v34.py、report_math_v34.py。均为新文件，旧实验实现未静默切换。''')
 write('V3_4_Final_Report.md',f'''# V3.4 证据协议修复与S/FS配对实验

**判断：工程阻断已得到明确修复，并形成可执行S/FS配对；当前FS实现没有显示值得扩大试用的独立收益。保持Shadow，不开展大规模性能实验。**

旧V3.3的24道已曝光题零API回放：冻结旧算法和旧FS，仅迁移元审查证据，两组支持题均5/6，错误接受均0/4。旧0/6历史成绩不修改。这是协议兼容性证据，不是新独立确认。

新算法没有生成，F3源码保持原SHA。新schema、S/FS Python契约均为DeepSeek真实生成；数值/符号域不再拒绝已知但不支持的事实。主比较使用共同解析输出，只有FS额外获得历史观察。

新确认12题结果：

{table('confirmation')}

新开发中S/FS正确接受均0/6，错误接受分别1/4和0/4。四题有类型错误，另两道支持题的计数语义被遗漏；没有用事后格式修补抬高成绩。

本轮已经可以区分三类原因：

- **协议**：确认12/12通过证据格式校验，全文未发现矛盾不再要求伪造引句；必要前提未知仍阻断。
- **解析**：数学参数/运算符24/24与预先审查一致，但若干明确语义仍被置空；自由文本字段没有形成稳定机器语义。
- **契约**：S检查过宽，未验证目标与权限，错误接受树计数；FS仍用parenthes等关键词，拒绝有效的association描述，且离线求和反例显示目标判断不充分。

所以，FS的零错误接受不能当作优于S：它在确认支持题也为零。S的3/6也不能当作可靠方案：伴有1次明确误触发。两组离线支持6/6只说明参数化计算可执行，不能掩盖负例错误，更不能代替端到端成绩。

S一次接口修订仅改变MATCH目标回传绑定，AST校验其余逻辑不变；该修订发生在共同解析启动后、所有评分前，作为时序偏差明确记录，未见新题内容/输出。另一个人工离线最小值注释过度填值，已在审查报告标UNVERIFIED并排除可信负例统计，原始执行和主runtime结果不改。

{len(costs)}次真实响应、{tokens:,} tokens，估算 **${usd:.8f}**；预留上界${reserved:.6f}，非账单。14项新检查、16项原回归通过；无UNKNOWN，无Gold进入模型，无评分后修订。模型没有被人工提供新数学算法或专项匹配源码。

本轮不支持失败经验带来独立语义判断增益。这个判断限于一对生成、当前表示/契约、24道同族合成题，且没有等Token控制；不是对失败驱动学习总体的否定。当前最具体的反证是：即使采用结构化容器，模型仍可能只检查字段非空，或在自由文本字段里继续写关键词规则。不能把“换成JSON”当作学会了数学语义。

建议暂停当前FS契约路线的重复生成和扩大量级；保留自主算法生成的已有成果。只有在提出能区分真正语义判断与字段内关键词匹配的新假设时，再考虑下一轮有限实验。此次新确认集现已曝光，不可继续修订后作为未见证据。''')
 print(json.dumps(dict(calls=len(costs),tokens=tokens,cost=usd,reserved=reserved,worker=worker,report=str(REP)),ensure_ascii=False))
if __name__=='__main__':report()
