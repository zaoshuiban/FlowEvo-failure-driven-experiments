"""Read-only accounting and Chinese reports for component delivery and development audits."""
import json,sys,collections,datetime,urllib.request,re
from pathlib import Path
from run_math_v3_development import ROOT,save,sha
from failure_evo.contracts import fingerprint
REPORT=ROOT/'reports/math_v3_continuation_20261027';REPORT.mkdir(exist_ok=True,parents=True)
def load(p):return json.loads(p.read_text())
def write(name,text):(REPORT/name).write_text(text+'\n')
runs=['math_v3_components_20261027_01','math_v3_components_deepseek_20261027_01','math_v3_components_deepseek_repair_20261027_01']
prices=urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing',timeout=30).read();(REPORT/'deepseek_pricing_snapshot.html').write_bytes(prices)
assert b'$0.3' in prices and b'$1.2' in prices
costs=[];unknowns=[]
for name in runs:
 run=ROOT/'runs'/name;records=[];starts=0;started={}
 for p in sorted(run.glob('*/provider.jsonl')):
  for line in p.read_text().splitlines():
   r=json.loads(line)
   if r['kind']=='SEND_STARTED':
    starts+=1;started[r['payload']['key']]=r['at']
   if r['kind']=='SEND_UNKNOWN':unknowns.append(dict(run=name,branch=p.parent.name,record=r))
   if r['kind']=='RAW_RESPONSE':
    raw=r['payload']['response'];u=raw['usage'];dt=datetime.datetime.fromtimestamp(r['at'],datetime.timezone.utc);peak=dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10)
    estimated=u.get('cost') if raw['model'].startswith('openai/') else (u.get('prompt_cache_hit_tokens',0)*.006+u.get('prompt_cache_miss_tokens',u['prompt_tokens'])*.3+u['completion_tokens']*1.2)/1e6*(1 if peak else .5)
    records.append(dict(provider_wall_seconds=r['at']-started[r['payload']['key']],branch=p.parent.name,response_id=raw.get('id'),model=raw['model'],at_utc=dt.isoformat(),prompt_tokens=u['prompt_tokens'],completion_tokens=u['completion_tokens'],total_tokens=u['total_tokens'],reasoning_tokens=u.get('completion_tokens_details',{}).get('reasoning_tokens',0),finish_reason=raw['choices'][0]['finish_reason'],estimated_usd=estimated,basis='provider usage.cost' if raw['model'].startswith('openai/') else 'current official peak/off-peak quote; not invoice',raw_sha256=fingerprint(raw)))
 cost=dict(run=name,send_attempts=starts,responses=len(records),total_tokens=sum(x['total_tokens'] for x in records),estimated_usd=sum(x['estimated_usd'] for x in records),requests=records);costs.append(cost)
save(REPORT/'costs.json',costs);save(REPORT/'unknown_requests.json',unknowns)
# Reconcile semantically equivalent parameter representations, no output or score changed.
summaries={};corrections=[]
for arm,name in [('GPT','math_v3_components_audit_gpt_20261027_01'),('DS','math_v3_components_audit_deepseek_20261027_01')]:
 rows=load(ROOT/'runs'/name/'scores.json')
 for r in rows:
  m=r['observed']['match'].get('parameters');p=r['parameters'];eq=False
  if r['applicability']=='PARAMETER_MISMATCH' and p and m:
   if set(p)==set(m)=={'expression'}:eq=p['expression'].split()==m['expression'].split()
   elif 'digit_set' in p: eq=0 not in p['digit_set'] and set(p['digit_set'])==set(m.get('digit_set',[])) and p['max_length']==m.get('max_length')
  if eq:
   corrections.append(dict(run=name,name=r['name'],task_id=r['task_id'],old='PARAMETER_MISMATCH',new='CORRECT_MATCH',basis='whitespace-only arithmetic token equality, or irrelevant leading-zero flag when zero absent; no algorithm/output change'))
   r['applicability']='CORRECT_MATCH'
 save(REPORT/(arm+'_reviewed_scores.json'),rows)
 summaries[arm]={n:{role:{k:dict(collections.Counter(r[k] for r in rows if r['name']==n and r['role']==role)) for k in ('computation','applicability','combined')} for role in ('Source','Design')} for n in sorted({r['name'] for r in rows})}
save(REPORT/'parameter_equivalence_review.json',corrections);save(REPORT/'summary.json',summaries)
proposal=load(ROOT/'runs/math_v3_generated_tests_review_20261027_01/summary.json')
save(REPORT/'generated_test_summary.json',proposal)
rows=[]
for arm,groups in summaries.items():
 for name,s in groups.items():
  source=s['Source'];design=s['Design'];rows.append('|'+ '|'.join([arm+' '+name,str(source['computation'].get('CORRECT',0)),str(source['combined'].get('CORRECT',0)),str(design['computation'].get('CORRECT',0)),str(design['combined'].get('CORRECT',0)),str(design['applicability'])])+'|')
table='|候选|来源独立计算正确|来源联合正确|Design独立计算正确|Design联合正确|Design适用性计数|\n|---|---:|---:|---:|---:|---|\n'+'\n'.join(rows)
common='本轮为已曝光来源与 Design48 的开发验证；未读取 Gate/Legacy/Fresh，没有性能对照，没有新增 Experimental 权限。用户中途明确切换 DeepSeek，因此原 GPT 机制归纳与 DeepSeek 组件生成分开归因。原 P0–P3、旧 V3 结果不修改。'
write('V3_Component_Generation_Report.md',f'''# V3 分组件生成交付报告

{common}

旧 V3：6 份真实归纳中 5 份 PROPOSE_CORRECTION、T1 为 HYPOTHESIS_ONLY。5 份原文及 normalized 来源绑定直接导入，0 次新机制归纳。每个新 Run 的 protocol/frozen_source 保存真实工程版本，Git HEAD 不能代替未提交源码的内容哈希。

旧 GPT 四次 12288 输出均为 reasoning，content 为空。新 GPT 采用 low reasoning、每请求单组件、8192 上限；F1 三次完整交付算法、契约、8 测试提案。F2 下一次请求 HTTP402，停止，不重发。此前进度消息把402说成F1测试请求，原始账本证实是F2算法请求，本报告予以更正。

用户改用 DeepSeek 后另建 Run，deepseek-flash / thinking disabled / temperature 0 / JSON object，沿用原安全与接口检查。5/5 算法源码完整交付并静态通过。首轮 matcher 三份 parameter_schema 为对象而非字符串，一份多出顶层 type，一份8192截断。每份仅一次工程重交付：4份算法/契约联合制品，T2仍改变参数 schema，拒绝组装。F3源码静态可执行但返回字符串，实际接口失败。没有手工修改任何生成代码。

初轮10响应，工程修订及测试9响应；没有数学正确性反馈进入任何修订。F2/F3/T3各提9条测试，超过提示建议8但未超过现有20条解析硬界限，全部保存，不假装遵守8条建议。

真实源码、响应、联合SHA见各 Run 的 artifact.json、solver_response.json、matcher_response.json；生成请求不包含私有评分答案。协议没有替旧UNKNOWN解账。

费用、完整响应ID与usage见 costs.json。''')
write('V3_Algorithm_Validation.md',f'''# 数学计算开发验证

{common}

使用独立于 matcher 的已冻结题目参数映射，Worker只接收 parameters；输出锁定后私有评分器比较答案。没有从候选输出推导 Gold。

{table}

DeepSeek 5个算法共17次来源计算全部正确，涉及12道唯一来源题（F/T共享来源不能当17道）；40次Design计算全部正确，涉及16道唯一目标题。其余题不调用不适用的独立计算，不计数学错误。GPT F1额外7次来源和8次Design计算正确。

特别是F2替代算法在2个原错误来源计算2/2，原V0为0/2；这是已曝光开发来源上的纠错证据，不是迁移。匹配器拒绝这两题，因此端到端来源修复仍0/2。代码审查见完整区间集合运算，没有旧提前化简步骤。

评分依据沿用P0私有参考，非定理证明。参数表达的空白和无零时leading-zero布尔差异经单独语义核对，修正适用性统计见parameter_equivalence_review.json；原Worker输出、原始scores均保留。''')
write('V3_Semantic_Contract_Validation.md',f'''# 语义契约开发验证

{table}

计算正确不意味着可用。F1 DeepSeek来源放行5/7、Design放行1/8目标；GPT F1来源3/7、Design2/8。未放行情况以UNKNOWN和DECLINE分别报告。

F2把含rearrang/reorder的所有题面拒绝，包括“rearranging ... is not allowed”；还把句号当小数信号。这是生成匹配器的语义错误，不能归为数学算法失败。F3的match返回json.dumps字符串而不是dict，所有运行均由宿主拒绝为ERROR。T2参数schema改变，没有完整联合版本。T3来源1/3、Design4/8目标正确匹配，但自动提案中的歧义/矛盾问题被接受3次。

Design已知数字可重复题、最小/最大值、括号形式数量等没有观察到错误接受；其中UNKNOWN不算明确正确拒绝，也不能用全拒绝申报通过。自动测试发现T3歧义接受，尚不计数学错误，但不满足“前提不确定时拒绝”的安全语义要求。

本轮4个DeepSeek联合制品均保留Shadow，0个进入Gate。''')
write('V3_Test_Generation_Validation.md',f'''# 自动测试提案与可信审查

共43条提案：GPT F1 8条；DeepSeek F1/F2/F3/T3分别8/9/9/9条。全部原提案保留，标签并非真值：有些NEAR_MISS仍是合法正例，有些AMBIGUOUS实际由“distinct digits”充分限定，有些题面互相矛盾或复用来源。

独立宿主逐题审查语义，23条明确正例由既有P0私有冻结参考函数计算，23/23独立算法计算正确；12条明确负例只验证拒绝，不凭生成器自报答案判分；8条歧义提案保持数学UNVERIFIED。没有用待测算子自身作Oracle，没有把参考实现传给生成模型。参考源码SHA及私有审查逐题参数见runs/math_v3_generated_tests_review_20261027_01/freeze.json和private/reviews.json。

发现的真实缺陷：F2拒绝所有5条合法正例；F3所有9条返回接口错误；T3接受3条歧义或互相矛盾的提案。没有发现可核验的数学错误，不能将拒绝或接口失败伪报数学错误。

{json.dumps(proposal,ensure_ascii=False,indent=2)}

这些提案是生成后人工语义复核的开发材料，不是独立封存测试。与来源题面重复的提案也不提供新的跨题证据。''')
write('V3_Variant_Comparison.md',f'''# 版本比较与归因边界

V0直接引用冻结P3的156次真实Worker结果：算子1来源7/7、Design正确5/错1；算子2来源0/2、Design错4/异常2；算子3来源3/3、Design正确8/错4。其余为拒绝。旧源码未改。

V1旧算法+新契约、V2新算法+旧契约：NOT_GENERATED。V0是单个math_operator，内部识别、参数提取、计算纠缠；没有由原模型生成的独立solve/match及参数契约。人工拆分或写等价包装会引入不受控算法/解析改变，故不伪造纯消融版本。

V3新算法+新契约：GPT F1完整；DeepSeek F1/F2/F3/T3有联合哈希，T2因schema不兼容NOT_GENERATED。完整源码不等于功能通过，F3实际接口失败。按全部版本而非最好版本报告如下：

{table}

独立参数执行提供算法纠错证据，语义匹配提供覆盖/误触发证据；缺少V1/V2意味着不能声称已完成完整2×2因果消融。T与F使用同源题面，但本轮混合历史归纳及一次工程修订，不将少量成绩作失败信息优于Task-Only的统计结论。''')
total_tokens=sum(c['total_tokens'] for c in costs);total_cost=sum(c['estimated_usd'] for c in costs)
write('V3_Continuation_Final_Report.md',f'''# V3 续跑最终报告

结论：**交付修复成功，算法纠错有开发证据；语义适用性仍不足，0个候选获准进入独立Gate。**

{common}

## 五个问题的回答

1. 5份PROPOSE全部转为DeepSeek完整算法源码；另有1份GPT F1算法。按原机制计5/5，不把重复模型版本算新增机制。HYPOTHESIS_ONLY保持不生成。
2. 独立参数下5/5算法在各自来源全部计算正确，合计17/17调用、12道唯一来源。F组联合来源修复只有F1的5/7，F2为0/2，F3为0/3（接口错误）；T3为1/3，T2无合法联合制品。
3. Design已知近似负例没有观察到错误接受，但契约常过度拒绝/UNKNOWN，F3接口失败；不能因此认定4份契约均有效。T3自动提案暴露3次不确定前提接受。
4. 自动测试识别了过度拒绝、接口类型错误和歧义接受；23次可信正例算法计算全对，未识别数学计算反例。8条歧义保持UNVERIFIED。
5. **0个**满足本轮进入Gate条件。全部继续Shadow，没有恢复任何旧Suspended版本。

## 成本与完整性

本轮真实响应22次（GPT3、DeepSeek19），总Token {total_tokens:,}，响应费用估算合计约 **${total_cost:.8f}**。GPT使用供应商usage.cost，DeepSeek按官方当前Flash峰谷报价和UTC请求时间估算，不是实际账单。DeepSeek价格快照在执行后核实，发送前沿用更高的$15/百万Token保守预留；这不是精准事前价格冻结，应作为过程限制披露。

另有1次本轮GPT HTTP402 UNKNOWN，旧V3另1次402 UNKNOWN；二者不重发、不清零、不冒充收费或成功。当前客户端能确认HTTP402但旧响应正文/供应商request id未保存，无法确认结算。未知费用与保守预留另列，不加进已知响应费用。每分支$4为PersistentBudget工程预留，不是实际支出。

旧V3历史生成成本约$1.3296475另列，不消失；本轮后续所有生成、无效输出、工程修订均入costs.json。无DeepSeek求解器新调用、无P1再收集、无Gate或大规模性能实验。

{table}

## 可复核文件

- costs.json：每次响应、Token、报价依据、费用。
- summary.json、GPT_reviewed_scores.json、DS_reviewed_scores.json：完整开发评分。
- generated_test_summary.json及对应Run：自动提案、私有审查和真实Worker。
- unknown_requests.json：本轮未知请求记录；原V3 STOP和账本保持不变。
- completion_manifest.json：交付源码、报告及数据哈希。

## 下一步边界

不再重发相同生成请求。本轮已做一次有界工程修订；剩余问题是契约语义、接口遵循与资源边界，不能通过宿主偷偷解析字符串或补人工规则放行。若继续，应单独设计契约更新实验，保持算法冻结，之后再申请独立Gate；当前结果不证明泛化或相对Generic收益。
''')
save(REPORT/'completion_manifest.json',dict(files={str(p.relative_to(ROOT)):sha(p) for p in list(REPORT.iterdir()) if p.is_file()},code={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'scripts/run_math_v3_components.py',ROOT/'scripts/repair_math_v3_delivery.py',ROOT/'scripts/audit_math_v3_components.py',ROOT/'scripts/review_math_v3_test_proposals.py',Path(__file__),ROOT/'FlowEvo/src/failure_evo/math_v3_component_generation.py']},paid_runs=runs))
print(REPORT)
