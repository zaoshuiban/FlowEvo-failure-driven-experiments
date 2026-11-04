"""Post-lock host-only report; no API dispatch."""
import json,datetime,collections,subprocess
from pathlib import Path
import run_hard_math_property_probe as r
O=r.OUT

def text(name,s):(O/name).write_text(s.strip()+'\n')
def table(h,rr):return '| '+' | '.join(h)+' |\n| '+' | '.join(['---']*len(h))+' |\n'+'\n'.join('| '+' | '.join(map(str,x))+' |' for x in rr)
def main():
 p=r.verify();assert (O/'COMPLETE.json').exists();costs=[];pending=[];reserved=0;wireaudit=[]
 for d in sorted((O/'jobs').iterdir()):
  events=r.core.EvidenceStore(d/'provider.jsonl').records();responses=[e for e in events if e['kind']=='RAW_RESPONSE'];starts=[e for e in events if e['kind']=='SEND_STARTED'];assert len(responses)==len(starts)==1
  e=responses[0];raw=e['payload']['response'];u=raw['usage'];dt=datetime.datetime.fromtimestamp(e['at'],datetime.timezone.utc);peak=dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10);hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit);fee=(hit*.006+miss*.3+u['completion_tokens']*1.2)/1e6*(1 if peak else .5)
  costs.append(dict(job=d.name,response_id=raw['id'],model=raw['model'],usage=u,estimated_usd=fee,finish_reason=raw['choices'][0]['finish_reason']))
  inp=json.loads(starts[0]['payload']['wire']['messages'][1]['content']);r.core.assert_no_gold(inp);wireaudit.append(dict(job=d.name,wire_sha256=r.fingerprint(starts[0]['payload']['wire']),input_sha256=r.fingerprint(inp),gold_fields_absent=True))
  b=r.core.PersistentBudget.__new__(r.core.PersistentBudget);b.path=d/'budget.jsonl'
  with b._locked() as rr:
   ss,_=b._state(rr);reserved+=sum(v['cost_upper_microusd'] for v in ss.values());pending.extend(v['status'] for v in ss.values() if v['status']!='settled')
 assert not pending and len(set(c['response_id'] for c in costs))==len(costs)
 ds=r.load(O/'discovery.json');discovery=[]
 for k,v in ds.items():
  rec=v['receipt']['records'] if v['receipt'] else [];obs=[o for x in rec for o in x.get('observations',[])];discovery.append(dict(key=k,proposal_count=len(rec),statuses=dict(collections.Counter(x['status'] for x in rec)),execution_outcomes=dict(collections.Counter(x['status'] for x in obs)),unique_input_count=len({r.fingerprint(x['parameters']) for x in obs}),algorithm_counterexamples=sum(x['status']=='ALGORITHM_COUNTEREXAMPLE' for x in rec)))
 ev=r.load(O/'evaluation.json');scores={k:{role:dict(collections.Counter(x['status'] for x in ev if x['kind']==k and x['role']==role)) for role in ['development_regression','new_parameter_confirmation','exposed_overlap']} for k in r.SPECS}
 # Audit all newly revealed wrong score instances, never feeding these to the learner.
 cases={x['id']:x for x in r.load(O/'private/cases.json')['score']};audit=[]
 for e in ev:
  if e['kind']!='score' or e['status']!='WRONG':continue
  c=cases[e['id']];q=c['parameters'];actual=int(e['raw']['raw']['value']);N=q['total_problems'];B=q['base_score'];A=q['correct_coefficient'];W=q['wrong_coefficient'];exact=[];interval=[]
  for correct in range(N+1):
   if B+A*correct-W*(N-correct)<=actual<=B+A*correct:interval.append(correct)
   if any(B+A*correct-W*w==actual for w in range(N-correct+1)):exact.append(correct)
  audit.append(dict(case_id=e['id'],parameters=q,returned=actual,reference=c['reference'],interval_consistent_c=interval,exact_consistent_c=exact,root='discrete scoring progression treated as contiguous integer interval',role='POST_CONFIRMATION_HOST_ONLY_NOT_AUTONOMOUS_DISCOVERY'))
 r.save(O/'private/missed_defect_audit.json',audit)
 wr=r.core.EvidenceStore(O/'worker.jsonl').records();hist=r.load(O/'history_hashes.json');changed=[f for f,h in hist.items() if r.sha(r.ROOT/f)!=h];assert not changed
 metrics=dict(status='COMPLETE_NO_AUTONOMOUS_COUNTEREXAMPLE',model_calls=len(costs),tokens=sum(c['usage']['total_tokens'] for c in costs),estimated_usd=sum(c['estimated_usd'] for c in costs),reserved_upper_usd=reserved/1e6,hard_ceiling_usd=7.2,actual_invoice=None,unknown=0,source_tasks=3,official_difficulty='Level 5',source_exposure='previously exposed development',initial_algorithms_generated=0,revision_calls=0,autonomous_confirmed_defects=0,post_confirmation_wrong_score_inputs=len(audit),post_confirmation_reviewed_root_clusters=1 if audit else 0,worker_executions=len(wr),worker_host_wall_seconds=sum(e['payload']['result'].get('host_wall_seconds',0) for e in wr),history_files=len(hist),history_changed=changed,scores=scores)
 for name,x in [('metrics',metrics),('costs',costs),('wire_audit',wireaudit),('discovery_metrics',discovery),('score_matrix',scores)]:r.save(O/(name+'.json'),x)
 rows=[]
 for d in discovery:
  s=d['statuses'];rows.append([d['key'],d['proposal_count'],d['unique_input_count'],d['algorithm_counterexamples'],s.get('UNVERIFIED_REFERENCE_OR_DOMAIN',0),s.get('UNVERIFIED_SPEC',0)+s.get('UNVERIFIED_RELATION_NO_VALUE',0)])
 text('Discovery_Report.md','# 困难MATH缺陷发现\n\n'+table(['来源/组','提案','去重已执行输入','可信算法反例','范围或参考未验证','关系/格式未验证'],rows)+'''

D普通诊断与C性质驱动共六次真实生成，均使用冻结接收层、同一工具权限和测试配额。未向模型提供研究者已知错误、标准答案、Oracle实现或确认输入。模型生成的claim中的数值和数学断言不作可信答案。

计分题的两组全部可评价提案都通过，但没有证明程序全域正确。D覆盖过W=2，C覆盖过W=2/3，仍没有选择出暴露错误的参数组合。因此不是简单地“没有尝试W>1”，而是所选例子的分数与唯一性条件没有区分错误区间模型和正确离散模型。

传输费用题两组没有发现缺陷，新参数上也全部正确。根式题部分提案因范围、关系或格式无法评价；正确拒绝无解案例没有被算成缺陷。没有可信反例时，按预注册门控不进入修订，不能将未执行修订报作修订失败。

自然语言解释仍含未经验证的假设，特别是计分题C把固定c的所有分数当作连续整数区间；后续确认反驳了这个推广。这个事后归因不是模型自主发现，不能加到C的发现成绩中。
''')
 rows=[]
 for k,s in scores.items():
  c=s['new_parameter_confirmation'];rows.append([k,c.get('CORRECT',0),c.get('CORRECT_REJECTION',0),c.get('WRONG',0)+c.get('WRONG_ACCEPT',0),sum(v for a,v in c.items() if a not in ['CORRECT','CORRECT_REJECTION','WRONG','WRONG_ACCEPT']),sum(c.values())])
 text('Confirmation_and_Attribution.md','# 冻结后确认与漏检归因\n\n'+table(['程序','正确数值','正确无解拒绝','错误数值/接受','其他','总输入'],rows)+'''

计分题6个确认数值错误归入同一离散性缺陷。算法用[最低分,最高分]的连续整数区间判断可达性；当扣分步长W>1时，固定正确题数产生的是间隔为W的离散分数，区间内并非每个整数都可达。遗漏这项条件会改变最小分数或唯一正确题数的判定。private/missed_defect_audit.json逐例列出候选的区间判断与真实(c,w)枚举。没有修改源码，也没有把这些结果回传模型启动修订。

根式18条新确认全部在冻结有限搜索范围内没有满足容差的三元组，候选均正确拒绝。这不是18道数学题解对，更不能证明数值算法在有解时可靠。这个随机参数集缺少合法有解正例，限制必须保留，不事后替换输入补齐好看的成绩。

来源题另行评分：计分、传输费用均交付来源正确答案；根式程序在原source_parameters上ValueError，未解决来源题。来源数值评分与参数化接口评分是两种证据，不能用有限域正确拒绝掩盖来源能力不足。

54个新确认输入是三道原题各18个参数变体，不是54道独立MATH题；它们在模型调用前生成并冻结。角色重合检查见evaluation.json的exposed_overlap（本轮为空）。这些数据现已曝光，后续仅限开发。
''')
 text('Protocol_and_Engineering.md',f'''# 协议与工程
最终协议SHA `{r.fingerprint(p)}`。三道官方Level5来源选自既有hard140训练开发材料：number_theory-550 FC、number_theory-420 FC、intermediate_algebra-426 F。根式原FC未静态通过，因此选已有F；几何因缺少本轮可审计有界参考未纳入。本轮不称新独立原题，不声称三类都仍具有相同求解难度。

共用deepseek-flash（官方当前服务版本DeepSeek-V4.1-Flash-1017），temperature0.2、非thinking、8192输出、65536保守wire上界。最多36物理请求/$7.20硬上限；实际{len(costs)}次、{metrics['tokens']:,} tokens、估算${metrics['estimated_usd']:.8f}。保守预留${metrics['reserved_upper_usd']:.6f}，不是账单。报价页面已冻结，费用使用实际usage和峰谷缓存价格；没有沿用旧预算。

七项新增零API测试通过。一次单元测试期望值写错在首个API之前修正：upper_bound=3的参考输出为1而非2；Oracle实现未改。原协议、测试修正原因和最终源码哈希均保留于pre_api_test_correction.json；任务、提示、候选、参考算法未改，禁止掩盖该准备问题。

真实Worker预检6次，包含正确值与正确拒绝；总执行{len(wr)}次，主机调用墙钟{metrics['worker_host_wall_seconds']:.3f}秒。根式独立Oracle使用10^60尺度的整数根界形成严格区间，只有容差内外可证明分离时才给确定结论；临界不确定返回UNVERIFIED。宿主Oracle不作为模型算子、不发送给生成模型。

模型请求无Gold字段，真实请求全部已响应结算，未知0、重复响应ID0。旧Run的{len(hist)}份文件哈希未变。沿用现有预算、编译、接收和Linux Worker；无新研究模块、无初始算法生成、无Experimental和在线复用。
''')
 text('Final_Report.md',f'''# 困难MATH性质探索总结
**完成3道官方MATH Level5来源上的有限探索。最明确的结果是：自主测试漏掉了一个随后被独立确认暴露的真实缺陷。**

{table(['观察','结果'],[['模型自主发现','D/C均0个可信反例'],['是否修订','未触发；没有人工补反例或强行改代码'],['计分唯一性新参数','5正确值＋7正确拒绝＋6错误值'],['传输费用新参数','18/18正确值'],['嵌套根式新参数','18/18正确拒绝；没有有解正例'],['原来源题','计分与传输正确；根式未交付答案'],['模型调用与费用',f"{len(costs)}次，{metrics['tokens']:,}tokens，约${metrics['estimated_usd']:.6f}"]])}

计分算法将离散可达分数误作连续整数区间，D/C的自选测试都没有暴露该问题；确认集6个错误由宿主事后审查归为同一缺陷，不能登记为自主发现。说明当前瓶颈至少包含测试反例的区分能力，不能仅凭模型能写出性质说明就认定测试有效。

本轮没有修订比较数据，因此无法评价C是否更会修复。也没有证据证明C比D更会发现问题。正确程序和无解输入没有被强制修改，停止门控正常工作。

限制：来源已曝光，54个确认只是参数变体；根式正例覆盖不足；单次模型采样、有限参考域。更换为Level5来源不自动保证生成程序困难或仍有缺陷。本轮保留负结果，不追加模型调用、不按结果换样本、不用确认反例继续修订。全部源码和输入保持冻结。
''')
 text('README.md','''# 交付索引
- Final_Report.md：总结。
- Discovery_Report.md：六次自主测试与未验证提案。
- Confirmation_and_Attribution.md：独立确认及事后漏检归因。
- Protocol_and_Engineering.md：预算、隔离、测试与准备期修正。
- protocol.json / freeze.json / frozen_source：冻结源码和协议。
- jobs / discovery.json：真实请求、响应、接收和执行。
- shared_counterexamples.json / candidate_freeze.json：0反例，未启动修订。
- evaluation.json / source_results.json：参数评分和原题评分分别记录。
- private/missed_defect_audit.json：宿主事后审查，不进入模型。
- metrics.json / costs.json / wire_audit.json：完整成本与审计。
''')
 r.save(O/'exposure_registry.json',dict(status='CLOSED_NO_OUTCOME_DRIVEN_RERUN',cases=[dict(kind=k,id=x['id'],parameters_sha256=r.fingerprint(x['parameters']),future_role='EXPOSED_DEVELOPMENT_ONLY') for k,cs in r.load(O/'private/cases.json').items() for x in cs]))
 r.save(O/'final_audit.json',dict(history_changed=changed,pending=pending,unique_response_ids=len(costs),source_hashes_verified=True,remaining_worker_containers=subprocess.check_output(['docker','ps','-a','--filter','name=flowevo-','--format','{{.Names}}'],text=True).splitlines()))
 print(json.dumps(metrics,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
