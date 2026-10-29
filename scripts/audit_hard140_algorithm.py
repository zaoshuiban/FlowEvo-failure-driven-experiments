"""Post-run attribution and ledger audit only. No API, no candidate edits."""
import json,collections
from run_hard140_algorithm import *
R=ROOT/'reports/hard140_algorithm_20261028_01';verify();scores=load(OUT/'evaluation/scores.json');unknown=[]
for directory in sorted((OUT/'jobs').glob('*')):
 budgetrows=EvidenceStore(directory/'budget.jsonl').records();providers=EvidenceStore(directory/'provider.jsonl').records();compiler=EvidenceStore(directory/'compiler.jsonl').records()
 for u in [x for x in budgetrows if x['kind']=='UNKNOWN']:
  q=next(x['payload'] for x in compiler if x['kind']=='GENERATION_REQUESTED' and fingerprint(['generation',(x['payload']['stream_id'],x['payload']['family_id']),x['payload']['phase'],x['payload']['slot']])==u['payload']['request_id'])
  key=fingerprint([q['stream_id'],q['family_id'],q['phase'],q['slot']]);raw=next(x for x in providers if x['kind']=='RAW_RESPONSE' and x['payload']['key']==key)
  reservation=next(x['payload'] for x in budgetrows if x['kind']=='RESERVED' and x['payload']['request_id']==u['payload']['request_id'])
  unknown.append(dict(job=directory.name,stage=q['stage'],ledger_request_id=u['payload']['request_id'],ledger_reason=u['payload']['reason'],raw_response_id=raw['payload']['response']['id'],raw_response_sha256=raw['payload']['sha256'],finish_reason=raw['payload']['response']['choices'][0]['finish_reason'],usage=raw['payload']['response']['usage'],raw_saved_at=raw['at'],ledger_unknown_at=u['at'],reserved_upper_usd=reservation['cost_upper_microusd']/1e6,classification='RAW_RECEIVED_BUT_NORMALIZATION_FAILED_BEFORE_USAGE_SETTLEMENT',ledger_rewritten=False,resend=False))
transportunknown=[]
for p in list((OUT/'jobs').glob('*/provider.jsonl'))+list((OUT/'solver').glob('*/requests.jsonl')):
 for x in EvidenceStore(p).records():
  if x['kind']=='SEND_UNKNOWN':transportunknown.append(dict(path=str(p),record=x))
pairs={}
for left,right in [('F','T'),('FC','T'),('FC','F')]:
 key=left+'_vs_'+right;result={}
 for mode in ['all_attempts','both_static_valid']:
  wins=losses=both=neither=0;n=0;ids=[]
  for tid in sorted({s['task_id'] for s in scores}):
   a=next(s for s in scores if s['task_id']==tid and s['arm']==left);b=next(s for s in scores if s['task_id']==tid and s['arm']==right)
   if mode=='both_static_valid' and any(x['status']!='STATIC_VALID_SHADOW' for x in [a,b]):continue
   n+=1;aa=a['grade']['status']=='CONFIRMED_CORRECT';bb=b['grade']['status']=='CONFIRMED_CORRECT';wins+=aa and not bb;losses+=bb and not aa;both+=aa and bb;neither+=not aa and not bb
   if aa!=bb:ids.append(dict(task_id=tid,winner=left if aa else right,left_execution=a['raw']['status'],right_execution=b['raw']['status']))
  result[mode]=dict(n=n,wins=wins,losses=losses,both_correct=both,neither_correct=neither,discordances=ids)
 pairs[key]=result
save(R/'ledger_normalization_audit.json',dict(ledger_unknowns=unknown,transport_unknowns=transportunknown,protocol_deviation='Frozen stop list included UNKNOWN; executor checked SEND_UNKNOWN only, so normalization-induced ledger UNKNOWN did not stop further generation. Raw responses and usage exist. No ledger mutation/retry; exploratory only.'))
save(R/'pairwise_attribution.json',pairs)
case_table='\n'.join(f"|{key}|{p['all_attempts']['wins']} / {p['all_attempts']['losses']}|{p['both_static_valid']['wins']} / {p['both_static_valid']['losses']}（{p['both_static_valid']['n']}对）|" for key,p in pairs.items())
text=f'''# 机制归因与账本停止门控审计

## 必须保留的执行偏差

发现2条PersistentBudget的UNKNOWN，分别位于几何551的T分析和中级代数426的T源码请求。两者均已保存完整RAW_RESPONSE、响应ID及usage，并非网络状态无法确认；前者JSON解析失败，后者字段契约失败。归一化函数在返回usage前抛出异常，BoundedCompiler以`usage_not_known`保守记UNKNOWN。

冻结协议的停止列表包含UNKNOWN，但执行器只检查供应商`SEND_UNKNOWN`。因而没有将这两条账本UNKNOWN提升为全局停止，随后继续生成。**这是停止门控执行偏差，不能用“最终拿到了响应”掩盖。** 本轮应标记`COMPLETE_WITH_LEDGER_GATE_DEVIATION`，只作为开发探索证据，不能称为完整符合预注册的确认实验。

321次请求均有321个不同响应ID；实际传输SEND_UNKNOWN为{len(transportunknown)}。两条账本UNKNOWN费用预留合计${sum(x['reserved_upper_usd'] for x in unknown):.6f}保留，原账本没有改成SETTLED，没有重发。报告费用已经从真实响应usage计入这两次，不遗漏生成成本。后续付费实验应先单独修复“归一化拒绝的usage结算与全局UNKNOWN门控”，本轮不追溯改写运行代码、账本或结果。

## 配对结果应怎样解释

|对比|全部尝试：左方独有正确 / 右方独有正确|双方静态有效：左方独有正确 / 右方独有正确|
|---|---:|---:|
{case_table}

静态有效不保证运行成功，配对详情保留具体执行状态。F相对T没有新增来源成功；FC全部尝试净多1题，但其中随机游走的T未执行是工程拒绝。只看T和FC均可执行的4对，FC一胜一负，不能宣称有稳定数学收益。

## 1. 嵌套表达式：F复现错误，FC改变了处理方式

来源`algebra-330`。F生成递推程序，但手工映射深度仍有问题，输出与原错误答案相同；T也采用递推/深度映射，来源错误。FC把原表达式作为输入，生成支持整数、加法、乘法、括号和隐式乘法的递归下降解析器，来源评分正确。

这是本轮最直接的“纠错协议改变可执行过程”的正例：减少人工层数映射，改为解析原始表达式结构。源码实际计算，不是固定答案表。但结果同时包含输入表示/参数提取改进，不能只归因于底层数学算法更强；只有一次生成和一个来源，尚未验证跨题复用。

## 2. 随机游走：FC处理首次命中，F仍统计了不同事件

来源`counting_and_probability-351`。F累加不同长度下终点位于目标的路径数，并除以所有长度路径数之和；这不等同于六步内首次到达目标的概率，来源评分错误。

FC显式指出重复命中/重复计数风险，生成吸收态动态规划：命中路径不再传播，按命中步数累计概率，来源正确。两者都执行真实代码，存在实际算法差异。

不过T的算法主体也包含首次命中计数，因顶层`_self_test()`执行被安全规则拒绝。该自测答案由模型自报，不是可信Oracle；本轮没有删除自测后补跑，不能用T的未执行证明FC数学能力优于T。

FC也没有获得独立参数正确性证明；例如起点即目标等边界未专门验收。不要把来源成功当作通用随机游走算子已经验证。

## 3. 多项式：纠错协议也可能引入错误约束

来源`intermediate_algebra-289`。T和F来源正确，FC错误。F采用精确有理数插值并消去系数分母。FC在失败诊断中新增外部点的同余条件，再构造更复杂的搜索。

代码审查发现FC只采用一个CRT代表`c_r`作为外部点值进行插值，没有覆盖该同余类全部可选值。这可能额外收窄可行解；这里只是有代码依据的失效解释，不宣称已经证明唯一根因。已确定的事实是：新增纠错推理和更多代码没有保证正确性，反而该来源变差。

## 4. 其他来源

两个数论来源（420、550）三组均正确，没有失败信息独有成功。几何551的F/FC分别返回“no solution found”和“failed to converge”；这不是Worker故障，也不能算数学正确答案。根式426的F在给定搜索范围未找到解；FC因不允许的import被拒绝，T源码输出契约不合格。未通过候选全部保留，未手工修补。

## 研究判断

本轮解决了“没有真实失败可学”的问题：140题产生8道可信数学错误，7道进入对照。取得2个值得保留的纠错过程改变案例，同时有1个明确反例。普通F并未表现出优于T的来源结果；FC也没有稳定净优势，更未证明独立复用或成本收益。

下一步若继续，优先冻结本轮源码，独立验证表达式解析与首次命中两类候选，并保留多项式负例；不要基于这7道题再次修改生成Prompt后把结果称为独立验证。首先修复账本停止门控，再决定新的实验。
'''
(R/'Mechanism_and_Ledger_Audit.md').write_text(text)
main=R/'Hard140_Final_Report.md';s=main.read_text();intro='''## 结论摘要

**140题真实求解完成，但存在账本停止门控执行偏差，标记`COMPLETE_WITH_LEDGER_GATE_DEVIATION`。** 最终118题确认正确、8题确认错误、13题UNVERIFIED、1题截断。7道可信错误来源进入T/F/F-C对照，来源正确分别3/7、3/7、4/7。

FC有表达式解析和首次命中的正例，也有多项式来源退化。排除T的工程拒绝后，T与FC共同可执行的4对中一胜一负；尚无稳定失败学习收益。两条已有完整响应的格式错误被账本保守标为UNKNOWN，未触发全局停止；原始记录、费用预留均保留，无重发。本轮只作为开发探索证据。

详见[机制归因及停止门控审计](Mechanism_and_Ledger_Audit.md)。

'''
if '## 结论摘要' not in s:s=s.replace('## 运行状态',intro+'## 运行状态',1)
main.write_text(s)
save(OUT/'decision.json',dict(status='COMPLETE_WITH_LEDGER_GATE_DEVIATION',discovery_tasks=140,confirmed_wrong_tasks=8,source_pairs=7,source_success={'T':3,'F':3,'FC':4},ledger_unknown_count=2,transport_unknown_count=0,ledger_modified=False,claims='Exploratory source effects only; no stable independent learning benefit or transfer established',further_api_calls=False))
print(json.dumps(dict(pairs=pairs,ledger_unknowns=len(unknown),transport_unknowns=len(transportunknown)),ensure_ascii=False,indent=2))
if (R/'README.md').exists():raise RuntimeError('audit already finalized')
(R/'README.md').write_text('# 140题最高难度数学实验\n\n[完整报告](Hard140_Final_Report.md) · [机制与账本审计](Mechanism_and_Ledger_Audit.md) · [140题清单](Task_List_and_Outcomes.md)\n\n最终118正确、8错误、13未确认、1截断。7个来源的T/F/FC正确数为3/3/4。本轮存在账本UNKNOWN门控偏差，保留为开发探索，不作为严格确认。\n')
