"""Read-only final stream audit; writes only a new report directory."""
import json,csv,math,collections,hashlib
from pathlib import Path
import run_math_stream200_finish196 as r
ROOT=r.ROOT; out=ROOT/'reports/math_stream200_final_20261103';out.mkdir(exist_ok=True)
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
summary=r.report_chain(r.PARENTS+[r.OUT],out/'accounting')
plan=r.read(r.OUT/'execution_plan.json');lineage=r.read(r.OUT/'lineage.json')
meta=rows(r.DATA/'host/task_metadata.jsonl'); byid={x['task_id']:x for x in meta}
states={};scores={};locks={};mechanism={};windows=[]
for arm in r.ms.ARMS:
 states[arm]=rows(r.OUT/arm/'task_state.jsonl')
 scores[arm]={x['payload']['sequence']:x['payload']['verdict']['status'] for x in states[arm] if x['kind']=='PRIVATE_SCORED'}
 locks[arm]={x['payload']['sequence']:x['payload']['lock'] for x in states[arm] if x['kind']=='ANSWER_LOCKED'}
 assert set(scores[arm])==set(range(1,201))
 reg=rows(r.OUT/arm/'registry.jsonl');mechanism[arm]=dict(collections.Counter(x['kind'] for x in reg))
 for f in sorted((r.OUT/arm/'learning').glob('*/result.json'),key=lambda x:int(x.parent.name)):
  res=r.read(f);p=r.read(f.parent/'public_input.json');refs=r.read(f.parent/'input_refs.json');obs=p.get('observations',[])
  for o in obs:
   tid=next(t['task_id'] for t in r.lines(r.DATA/'public/tasks.jsonl') if t['problem']==o['problem']);seq=byid[tid]['sequence']
   assert scores[arm][seq]=='CONFIRMED_WRONG' and locks[arm][seq]['responses'][-1]['finish_reason']=='stop'
  windows.append(dict(arm=arm,cutoff=res['cutoff'],status=res['status'],calls=res['learning_calls'],questions=len(p['questions']),observations=len(obs),fragment_outputs=sum(o['final_output']['is_fragment'] for o in obs),task_ids=refs['task_ids'],hypothesis=r.read(f.parent/'hypothesis.json') if (f.parent/'hypothesis.json').exists() else None))
# Unique model receipts across all parents, including inherited learner directories.
cost={a:collections.defaultdict(float) for a in r.ms.ARMS};seen={};models=collections.Counter();sendkeys=collections.Counter()
for root in r.PARENTS+[r.OUT]:
 for arm in r.ms.ARMS:
  for p in list((root/arm).rglob('requests.jsonl'))+list((root/arm).rglob('provider.jsonl')):
   for e in rows(p):
    if e['kind']!='RAW_RESPONSE':continue
    raw=e['payload']['response'];rid=raw.get('id');digest=r.fingerprint(raw)
    if rid in seen:assert seen[rid]==digest;continue
    seen[rid]=digest;u=raw['usage'];stage='learning' if 'learning' in p.parts else 'solve';c=cost[arm]
    c[stage+'_calls']+=1;c[stage+'_tokens']+=u['total_tokens'];c['input_tokens']+=u['prompt_tokens'];c['output_tokens']+=u['completion_tokens'];c['reasoning_tokens']+=u.get('completion_tokens_details',{}).get('reasoning_tokens',0)
    hit=u.get('prompt_cache_hit_tokens',0);c[stage+'_usd']+=((u['prompt_tokens']-hit)*.3+hit*.006+u['completion_tokens']*1.2)/1e6;models[raw.get('model','UNKNOWN')]+=1
  # Unique owning account ID prevents copied learning logs from appearing as re-sends.
  for b in (root/arm).rglob('*budget.jsonl'):
   opened,_,_=r.account(b)
   if b.name!='solve_budget.jsonl':continue
   for e in rows(b.parent/'requests.jsonl'):
    if e['kind']=='SEND_STARTED':sendkeys[(opened['config']['run_id'],e['payload']['request_id'])]+=1
assert len(seen)==1602 and sum(c['solve_tokens']+c['learning_tokens'] for c in cost.values())==5887969
assert max(sendkeys.values())==1
pairs=[]
for name,v in summary['paired_results'].items():
 b,c=v['trusted_x_wins'],v['trusted_y_wins'];n=b+c;p=min(1,2*sum(math.comb(n,k) for k in range(min(b,c)+1))/2**n) if n else 1
 pairs.append(dict(comparison=name,**v,exact_mcnemar_p_reliable_subset=p))
traces=[]
for m in meta:
 q=dict(sequence=m['sequence'],task_id=m['task_id'],subject=m['subject'],difficulty=m['difficulty'],source_original_id=lineage[m['task_id']]['source_original_id'])
 for arm in r.ms.ARMS:q[arm]=scores[arm][m['sequence']]
 traces.append(q)
with (out/'task_results.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(traces[0]));w.writeheader();w.writerows(traces)
batches=[]
for end in range(20,201,20):
 b={'end':end}
 for a in r.ms.ARMS:b[a]=dict(collections.Counter(scores[a][i] for i in range(end-19,end+1)))
 batches.append(b)
subjects={s:{a:dict(collections.Counter(scores[a][m['sequence']] for m in meta if m['subject']==s)) for a in r.ms.ARMS} for s in sorted({m['subject'] for m in meta})}
checks=dict(all_200_have_terminal_records=True,stream_completed=any(x['kind']=='STREAM_COMPLETED' for x in rows(r.OUT/'stream.jsonl')),no_duplicate_solver_send_ids=True,source_hashes_match=all(r.sha(ROOT/k)==h for k,h in plan['sources'].items()),parent_files_unchanged=all(r.sha(Path(p['root'])/k)==h for p in r.read(r.OUT/'continuation.json')['parents'] for k,h in p['files'].items()),F_observations_are_confirmed_wrong_with_stop=True)
assert all(checks.values())
result=dict(summary=summary,costs=cost,models=dict(models),mechanism=mechanism,windows=windows,batches=batches,subjects=subjects,paired=pairs,checks=checks,source_originals_known_records=sum(x['source_original_id']!='UNKNOWN' for x in lineage.values()),distinct_known_originals=len({x['source_original_id'] for x in lineage.values()}-{'UNKNOWN'}))
save(out/'results.json',result)
def table(head,rr):return '| '+' | '.join(head)+' |\n|'+'|'.join(['---']*len(head))+'|\n'+'\n'.join('| '+' | '.join(map(str,x))+' |' for x in rr)+'\n'
t=['# FlowEvo 200题长期数学任务流实验结果报告','报告日期：2026-11-03（America/New_York）。只读核查，新增模型请求0，未修改历史Run、评分或账本。',
'## 1. 核心结论','**任务流完成：COMPLETE_WITH_MISSING；失败驱动可执行能力收益：未得到验证。** 200条固定任务记录已遍历，194题形成四组完整配对，6题基础设施缺失。F确认正确94题，G为82题，但T/F都没有提出PROPOSE，没有生成Python算子，也没有真实算子介入。分数差异不能归因于算子学习。',
'## 2. 实验与证据边界','G/T/F/R共享固定任务顺序和deepseek-flash原生无Gold求解配置；通常每题固定两次调用，4096输出Token上限。T/F每20题学习一次，最后200题处不再学习，实际各9个窗口。T只读历史题面；F另读所选题中可信错误及裁剪轨迹。最多选择窗口末尾6道、16,000 UTF-8字节题面，并不是对所有历史失败进行全量归纳。保留最近2条未验证假设。',
'本次为多次明确续跑修订组成的探索性连续任务流；基础求解/学习协议保持，网络隔离规则有版本化修订，不能称为从头到尾完全不变的单一冻结运行。没有安装独立Gate provider，因此即使生成候选也只能Shadow。不是官方Omni-MATH排行榜评测，也不是独立跨原题泛化确认。',
'## 3. 结果及分母','下表“确认正确/194”是已完成任务中确认成功比例。TRUNCATED和UNVERIFIED不是确认数学错误；不能把它们合并成CONFIRMED_WRONG。',
table(['组','确认正确','确认错误','截断','无法确认','确认正确/194','可信可评分子集正确率'],[[a,*[summary['arms'][a]['statuses'][k] for k in ['CONFIRMED_CORRECT','CONFIRMED_WRONG','TRUNCATED','UNVERIFIED']],f"{summary['arms'][a]['statuses']['CONFIRMED_CORRECT']/194:.2%}",f"{summary['arms'][a]['statuses']['CONFIRMED_CORRECT']/(summary['arms'][a]['statuses']['CONFIRMED_CORRECT']+summary['arms'][a]['statuses']['CONFIRMED_WRONG']):.2%}"] for a in r.ms.ARMS]),
'各组可信可评分子集不同，最后一列不宜直接作因果比较。完整200记录口径的确认成功率分别为G 41%、T 45%、F 47%、R 44%，其中6个基础设施缺失仍是缺失，不是错误。若仅改变这6题的成功假设，对应范围为G 41–44%、T 45–48%、F 47–50%、R 44–47%；该范围不处理UNVERIFIED与截断的不确定性。',
'## 4. 同题配对',table(['比较','共同完成','仅X确认成功','仅Y确认成功','双方可信评分','X胜/Y胜（可信）','精确McNemar p（可信）'],[[x['comparison'],194,x['x_only_confirmed_correct'],x['y_only_confirmed_correct'],x['both_reliably_scored_pairs'],f"{x['trusted_x_wins']}/{x['trusted_y_wins']}",f"{x['exact_mcnemar_p_reliable_subset']:.4f}"] for x in pairs]),
'“仅确认成功”包含另一组UNVERIFIED或截断，故不同于已确认正确/错误之间的胜负。F比G多12个确认成功（+6.19个百分点）；F比R多6个确认成功，但双方可信评分子集中F胜9、R胜11。结果受评分覆盖差异影响。检验仅作描述，未做多重比较校正，且题目谱系相关性使独立配对假设受限。不能宣称显著因果收益。',
'## 5. 学习与算子漏斗',table(['窗口结束','T结果','T调用','F结果','F调用','F错误观察数','其中最终输出被裁剪'],[[n,next(x['status'] for x in windows if x['arm']=='T' and x['cutoff']==n),1,next(x['status'] for x in windows if x['arm']=='F' and x['cutoff']==n),next(x['calls'] for x in windows if x['arm']=='F' and x['cutoff']==n),next(x['observations'] for x in windows if x['arm']=='F' and x['cutoff']==n),next(x['fragment_outputs'] for x in windows if x['arm']=='F' and x['cutoff']==n)] for n in range(20,200,20)]),
'T：9次归纳全部NO_MECHANISM。F：8次归纳全部HYPOTHESIS_ONLY，100题窗口因所选题无可信失败跳过。两组PROPOSE、源码生成、工程修订、Shadow候选、Gate通过、Experimental、真实执行和跨原题复用均为0。路由记录存在，但都是无合格候选后的原生回退；不是算子触发成功，也不是算子误触发。计算/路由验证正确率均不适用，不能写成100%。',
'F全流55道确认错误，只向归纳模型暴露16条所选错误记录（不同窗口不重叠）；7条最终输出在学习视图中被裁为前1500字符。原始最终响应均finish_reason=stop且评分为CONFIRMED_WRONG，不能把学习视图片段当作真实模型输出被Token截断。窗口80、180的假设明确描述了片段不完整，说明信息裁剪可能干扰失败原因诊断；是否造成拒绝生成，需要新对照，不能由本次直接断言。',
'F早期反复提出“极值结论需要可达构造和最优性双向检查”的未验证假设；180题窗口转向约数概率的指数分解枚举建议，并指出旧极值假设不适用。这说明假设内容有变化，但没有变为可执行版本。完整原文保存在results.json的windows字段。',
'## 6. 模型与成本',table(['组','原生/额外求解响应','学习响应','输入tokens','输出tokens','求解tokens','学习tokens','求解估算USD','学习估算USD','合计USD'],[[a,int(c['solve_calls']),int(c['learning_calls']),int(c['input_tokens']),int(c['output_tokens']),int(c['solve_tokens']),int(c['learning_tokens']),f"{c['solve_usd']:.6f}",f"{c['learning_usd']:.6f}",f"{c['solve_usd']+c['learning_usd']:.6f}"] for a,c in cost.items()]),
'总计1,602份唯一响应、5,887,969 tokens、按冻结报价估算$4.556122734。计价：未命中输入$0.30/百万、命中输入$0.006/百万、输出$1.20/百万；这是实验冻结报价估算，没有重新套用今日价格。实际供应商账单不可得。模型响应标识统计：'+str(dict(models))+'.',
'已结算账户中的计费/保守额度占用$22.228706，另有6次UNKNOWN保留$0.098524，总账本占用$22.327230。这不是实付$22.33。历史复制的学习响应和账户仅计一次；缺失题的部分求解调用也计入成本。Worker账本用时0，因为没有生成候选进入执行验证，不代表已完成Worker功能验收。',
'R采用上一窗口F实际学习调用数作为额外重启额度，在下一窗口末题执行，按预定最后响应选择答案，不看当前私有评分。F真实学习8次，R额外调用8次；这是调用次数匹配，不是严格Token/费用匹配，也不是每题资源匹配。',
'## 7. 数据谱系、完整性和异常',f"200记录中来源可确认的记录{result['source_originals_known_records']}条，对应{result['distinct_known_originals']}个已确认原题；其他仍UNKNOWN，不把不同题面哈希当独立原题。23个预先标记评分风险的任务继续UNVERIFIED隔离（其中151题因网络缺失）。",
table(['请求','UNKNOWN预留USD'],[[x['request_id'],x['reserved_usd']] for x in summary['unresolved_requests']]),
'89、112、115、151、194、195六题未进入数学错误统计；未重发UNKNOWN。最终状态COMPLETE_WITH_MISSING，最后五题完成。源码与父Run文件哈希核验通过；各组200条终结状态，包含194正常评分和6缺失标记，10个窗口完成。没有新增未分类pending。已核验solver SEND_STARTED在所属账本内无重复；未进行供应商账单层面的重复收费审计。此报告不声称进行了新的全链路Gold泄漏安全审计，沿用既有字段白名单与评分隔离协议。',
'## 8. 分批及数学类型',table(['批次截止','G正确','T正确','F正确','R正确','共同完成'],[[b['end'],*[b[a].get('CONFIRMED_CORRECT',0) for a in r.ms.ARMS],20-b['G'].get('INFRASTRUCTURE_MISSING',0)] for b in batches]),
table(['类型','记录数','G正确','T正确','F正确','R正确'],[[sub,sum(m['subject']==sub for m in meta),*[v[a].get('CONFIRMED_CORRECT',0) for a in r.ms.ARMS]] for sub,v in subjects.items()]),
'批次/类型难度不同，不把随时间的分数波动解释为学习曲线。',
'## 9. 最终研究判断','本轮真正验证了：困难数学题流可连续运行、评分后可信错误可进入学习窗口、模型能接收并产生未验证机制假设、异常和费用可追溯。没有验证：从失败自动生成可执行算子、功能准入、后续跨原题复用、可靠性或成本增益。',
'直接观察到的瓶颈是“可信失败→可程序化PROPOSE”：T/F均未进入代码生成。另有独立Gate缺失这个预先已知阻断。建议先只读审查16条学习证据的裁剪完整性及任务共同机制，不因F分数较高就扩大在线流，不把泛化、路由或准入问题误当成此次已经测到的失败。任何修复后的真实对照另建协议，不能改写本轮结果。',
'## 10. 复核文件','- results.json：逐窗口假设、统计、计量及检查结果。\n- task_results.csv：200条逐题四组状态与真实来源标记，不含Gold。\n- accounting/summary.json：全续跑链去重账本。\n- scripts/report_math_stream200_final.py：只读报告生成脚本。']
(out/'Final_Report.md').write_text('\n\n'.join(t)+'\n')
print(json.dumps(dict(cost=cost,checks=checks,output=str(out)),ensure_ascii=False))
