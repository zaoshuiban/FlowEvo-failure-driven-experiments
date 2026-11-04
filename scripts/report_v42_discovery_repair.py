"""Read-only experiment accounting and reporting; never sends model requests."""
import ast,json,datetime,collections,difflib,subprocess
from pathlib import Path
import run_v42_discovery_repair as r
OUT=r.OUT

def write(name,s):(OUT/name).write_text(s.strip()+'\n')
def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)
def main():
 protocol=r.verify();assert (OUT/'COMPLETE.json').exists();assert not (OUT/'STOP.json').exists()
 costs=[];states=[];wire_audit=[];reserved=0;pending=[]
 for d in sorted((OUT/'jobs').iterdir()):
  events=r.EvidenceStore(d/'provider.jsonl').records();starts=[e for e in events if e['kind']=='SEND_STARTED'];responses=[e for e in events if e['kind']=='RAW_RESPONSE'];assert len(starts)==len(responses)==1
  e=responses[0];raw=e['payload']['response'];u=raw['usage'];dt=datetime.datetime.fromtimestamp(e['at'],datetime.timezone.utc);peak=dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10);mult=1 if peak else .5
  hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit);fee=(hit*.006+miss*.3+u['completion_tokens']*1.2)*mult/1e6
  costs.append(dict(job=d.name,response_id=raw['id'],model=raw['model'],at=e['at'],finish_reason=raw['choices'][0]['finish_reason'],usage=u,estimated_usd=fee,pricing='frozen official peak/offpeak; receipt usage; invoice unavailable'))
  wire=starts[0]['payload']['wire'];inp=json.loads(wire['messages'][1]['content']);r.assert_no_gold(inp)
  wire_audit.append(dict(job=d.name,sha256=r.fingerprint(wire),gold_field_scan_pass=True,confirmation_included=False,known_bug_label_included=False,public_input_sha256=r.fingerprint(inp)))
  receipt=r.load(d/'reception.json');states.append(dict(job=d.name,model_responded=True,reception=receipt['receipt']['status'] if receipt['receipt'] else 'PARSE_FAILED'))
  b=r.PersistentBudget.__new__(r.PersistentBudget);b.path=d/'budget.jsonl'
  with b._locked() as rr:
   ss,_=b._state(rr);reserved+=sum(v['cost_upper_microusd'] for v in ss.values());pending += [dict(job=d.name,request=k,status=v['status']) for k,v in ss.items() if v['status']!='settled']
 assert not pending;assert len({x['response_id'] for x in costs})==len(costs)
 discovery=r.load(OUT/'discovery.json');disc=[]
 for key,v in discovery.items():
  rec=v['receipt']['records'] if v['receipt'] else [];obs=[o for x in rec for o in x.get('observations',[])];validkeys={r.fingerprint(o['parameters']) for o in obs};wrong={r.fingerprint(o['parameters']) for o in obs if o['status']=='CONFIRMED_WRONG'}
  disc.append(dict(program=key[0],arm=key[-1],test_specs=len(rec),statuses=dict(collections.Counter(x['status'] for x in rec)),actual_input_executions=len(obs),unique_valid_inputs=len(validkeys),duplicate_valid_inputs=len(obs)-len(validkeys),wrong_inputs=len(wrong),confirmed_defect_clusters=1 if wrong else 0,root_review='private/root_cause_witnesses.json; two Q witnesses share same canonical CRT restriction, no model access',prose_false_alarm_count=1 if key=='Z-D' else None,prose_false_alarm_basis='Confuses integer-valued with integer-coefficient polynomial; qualitative post-run review, not in-domain executed false-positive rate' if key=='Z-D' else None))
 # Compare unchanged executable syntax and retain diffs rather than equating code hash changes with capability.
 vs=r.load(OUT/'candidate_freeze.json')['versions'];parent=Path(vs['Q']['parent']['path']).read_text();baseast=ast.dump(ast.parse(parent),include_attributes=False);edits={}
 for arm in ['C','D']:
  s=Path(vs['Q'][arm]['path']).read_text();edits[arm]=dict(source_sha256=vs['Q'][arm]['sha256'],parent_sha256=vs['Q']['parent']['sha256'],ast_identical=ast.dump(ast.parse(s),include_attributes=False)==baseast,semantic_improvement_proven=False,review='Comment-only edit; AST identical' if arm=='C' else 'Deletes unused temporary congs construction and no-op loop; core CRT/interpolation search and refusal bounds unchanged')
  write('Q_'+arm+'_source.diff',''.join(difflib.unified_diff(parent.splitlines(True),s.splitlines(True),fromfile='frozen-parent',tofile=arm)))
 ev=r.load(OUT/'evaluation.json');score=[];deltas={}
 for kind,arms in vs.items():
  for arm,a in arms.items():
   rr=[x for x in ev if x['program']==kind and x['arm']==arm]
   score.append(dict(program=kind,arm=arm,status=a['status'],source_sha256=a.get('sha256'),results={role:dict(collections.Counter(x['status'] for x in rr if x['role']==role)) for role in ['development_regression','new_parameter_confirmation','exposed_overlap']}))
 for arm in ['C','D']:
  base={x['case_id']:x for x in ev if x['program']=='Q' and x['arm']=='parent'};rr=[x for x in ev if x['program']=='Q' and x['arm']==arm]
  deltas[arm]=dict(improved=sum(x['status']=='CORRECT' and base[x['case_id']]['status']!='CORRECT' for x in rr),regressed=sum(x['status']!='CORRECT' and base[x['case_id']]['status']=='CORRECT' for x in rr),same_output_or_error=sum(x['raw'].get('raw',{}).get('value')==base[x['case_id']]['raw'].get('raw',{}).get('value') and x['status']==base[x['case_id']]['status'] for x in rr))
 shared=r.load(OUT/'shared_counterexamples.json');plans={}
 for arm in ['C','D']:
  p=r.load(OUT/'repair_plans'/('Q-'+arm+'.json'));assert p['common_feedback_sha256']==r.fingerprint(shared['Q']);plans[arm]=dict(test_statuses=dict(collections.Counter(x['status'] for x in p['receipt']['records'])),same_common_feedback_sha256=p['common_feedback_sha256'])
 workers=r.EvidenceStore(OUT/'worker.jsonl').records();history=r.load(OUT/'history_hashes.json');changed=[p for p,h in history.items() if r.sha(r.ROOT/p)!=h];assert not changed
 metrics=dict(status='COMPLETE_DISCOVERY_CONFIRMED_REPAIR_NO_GAIN',requests=len(costs),tokens=sum(x['usage']['total_tokens'] for x in costs),estimated_usd=sum(x['estimated_usd'] for x in costs),reserved_upper_usd=reserved/1e6,hard_ceiling_usd=protocol['hard_budget_usd'],invoice=None,unknown=len(pending),initial_generations=0,model_revision_deliveries=2,ast_changed_revisions=1,confirmed_repair_improvements=0,worker_executions=len(workers),worker_host_wall_seconds=sum(x['payload']['result'].get('host_wall_seconds',0) for x in workers),historical_files=len(history),historical_changes=changed,independent_originals=1,program_versions=2,confirmation_parameter_cases=30,confirmation_overlap=r.load(OUT/'confirmation_exposure_audit.json')['overlap'],deltas=deltas)
 for name,data in [('metrics',metrics),('costs',costs),('delivery_states',states),('wire_audit',wire_audit),('discovery_metrics',disc),('score_matrix',score),('revision_diff_audit',edits),('repair_plan_metrics',plans)]:r.save(OUT/(name+'.json'),data)
 r.save(OUT/'pipeline_states.json',dict(discovery_complete=True,confirmed_counterexamples=2,distinct_root_clusters=1,shared_counterexample_package=True,model_revision_delivered=2,static_executable=2,counterexamples_fixed=0,independent_confirmation_improvement=0,regression_observed=0,control_revised=False,experimental=False))
 rows=[]
 for x in disc:
  c=x['statuses'];rows.append([x['program'],x['arm'],x['test_specs'],x['unique_valid_inputs'],x['wrong_inputs'],x['confirmed_defect_clusters'],c.get('OUTSIDE_CERTIFIED_DOMAIN',0),c.get('PROPERTY_COUNTEREXAMPLE',0)])
 write('Discovery_Report.md','# 缺陷发现阶段\n\n'+table(['程序','组','测试提案','去重有效输入','可信错误输入','缺陷簇','范围外提案','执行核验假性质'],rows)+'''

Q是已有错误程序，Z是已有参考一致实现；二者同一道原题的不同生成版本，不是两个独立数学任务。模型只看原始公开问题、冻结程序、Schema和评分支持范围，不看研究者错误标签或旧失败解释。D直接诊断并提出具体测试；C提出性质再构造测试。两者复用同一存储外壳，不将D的测试说明冒称形式化不变量。诊断可以无缺陷，不强迫修订。

Q-D与Q-C分别找到一个不同参数反例。事后独立符号参考构造了更小可行值的整数系数多项式，并检查父程序只取CRT规范余数的限制：两例归为同一个缺陷簇。不能说发现2个独立算法缺陷，也没有C独有缺陷簇。完整见private/root_cause_witnesses.json（未向模型发送）。归并是非盲法、事后代码审查。

正反证据：两组大量测试超出冻结评分范围，未临时放宽。D在Q有2/8范围外，C有6/8；Z-D全部8条范围外，Z-C6/8范围外。范围外包括原8节点来源输入、零符号、全部同号和无效输入等；原问题仍显示，但评分域预先限制2–7节点且两种非零符号均存在。模型未遵守这个范围属于提案质量问题；不是已证数学失败，也不是已证安全拒绝。该较窄范围限制负控制结论。

误报不能用“测试通过”替代。Z-D文字诊断混淆了整数值多项式和整数系数多项式，构成一类可明确反驳的文字误诊；其试图支持该指控的具体零符号测试均在冻结范围外，所以不捏造其执行误报率。Z-C两条可评价测试通过，另有一次重复输入；没有可信缺陷触发，宿主门控阻止了对Z的修改。这证明本次门控工作，不证明模型永不有害纠错。

模型在claim中夹带的数值推算和答案全部视为未验证文本，评分只调用独立参考。本轮没有把这些数字变成Oracle。自然语言claim即使某个oracle_correct测试通过，也没有被全称认证。
''')
 sr=[]
 for s in score:
  def cell(role):
   d=s['results'][role];return f"{d.get('CORRECT',0)}/{sum(d.values())}" if d else '未修订'
  sr.append([s['program'],s['arm'],cell('development_regression'),cell('new_parameter_confirmation'),s['results']['new_parameter_confirmation'].get('RESOURCE_EXCEEDED',0)])
 write('Repair_Report.md','# 相同反例下的修订评价\n\n'+table(['程序','版本','开发回归','新参数确认','确认资源超限'],sr)+'''

两组从同一个Q源码SHA和完全相同的两个已确认反例包开始。包中只有参数、候选返回值、二值错误类别，没有参考答案。随后各获一次计划/测试调用与一次源码修订调用，测试和接收限制相同。C计划显式提出性质，D普通计划提测试；各自测试反馈可以不同，这是被研究的处理差异，不是隐藏额外预算。

C实际交付源码的AST与父版本完全一致，仅注释改变。D删除未使用的临时列表和无作用循环，核心算法没有纠正。两组修订在相同两个反例上仍各0/2；新确认均14/30正确、14/30数值错误、2/30资源超限，和父程序一致；5个开发回归均4/5，与父程序一致。未观察到新增数学退化，但也没有修复收益。不能将源码SHA变更或计划文字变化算作算法能力改善。

C的修订计划中有2条关系被独立参考直接否定，另有4条实例仍揭示算法错误，2条范围外；这些假性质被如实保留，反馈只给类别及候选结果。普通计划同样有4个算法反例。所有记录可回溯到真实响应。

30条新输入在API前冻结、与旧V4/V4.2公开过的相同符号节点集排重；生成提案与修订材料的重合检查为0。它们现在已曝光，后续只能当作开发材料。这里是参数化能力评价，不是30道新原题，不是跨数学类型验证。
''')
 write('Protocol_and_Audit.md',f'''# 协议、工程和成本核查
冻结协议SHA：`{r.fingerprint(protocol)}`。
模型deepseek-flash，官方服务版本DeepSeek-V4.1-Flash-1017；thinking disabled，temperature0.2，8192输出，65536保守wire输入。当前官方报价HTML与哈希已冻结，估算按receipt时间峰谷和缓存usage计算；真实账单未取得。

最多24请求、硬上限4.80美元；实际{len(costs)}响应，{metrics['tokens']} tokens，估算${metrics['estimated_usd']:.8f}，保守预留占用${metrics['reserved_upper_usd']:.6f}。预留不是实付。所有交付失败/澄清都计入。分组/阶段费用见costs.json，不只统计修订成功调用。

Z-C第一次性质输出契约拒绝，按冻结统一规则执行一次澄清；原文、规范化与内容变化记录均保留。未改接收层、算子初始源码、模型提示或范围。没有新增初始算法，没有重跑关闭的随机游走案例，没有人工改模型源码。

新增6项零API测试及冻结接收层11项测试通过。负控制真实Worker预检5/5。全程Worker{len(workers)}次，记录主机调用墙钟{metrics['worker_host_wall_seconds']:.3f}秒；无网络、非root、只读、256MB、1CPU、2秒限制不变。未知/未决请求0，无重发；Worker实际算法资源超限按执行失败记录，不混同基础设施故障。

历史{len(history)}份文件哈希未变，旧V4.2及两次交付修复Run原成绩保持。模型请求键白名单和完整wire保留；Gold/Oracle答案字段检查通过。模型自己写在诊断中的数值不能宣称Gold泄漏，也不能当可信标准。

来源选择是已知开发程序，研究者不是盲法；只对模型隐藏错误标签。负控制仅在认证范围讨论。未进行Experimental授权或任何在线复用。报告只支持本次有限机制诊断。
''')
 write('Final_Report.md',f'''# 缺陷发现与修复分离实验总结
**实验完成：找到了真实问题，但没有修复收益；未观察到性质驱动C相对普通诊断D的优势。**

{table(['问题','D普通诊断','C性质驱动'],[['错误程序上的可信反例输入','1','1'],['去重后缺陷簇','同一缺陷簇1个','同一缺陷簇1个'],['共同反例包','相同2例','相同2例'],['修订后修复反例','0/2','0/2'],['新参数确认（父版14/30）','14/30','14/30'],['新增正确／退化','0 / 0','0 / 0'],['真实代码变化','删除无效代码，核心算法未修','仅注释变化，AST完全相同']])}

这次区分了两个环节：模型确实能提出暴露错误的测试，但从“知道程序有错”到“写出纠正错误的算法”没有成功。两组提出的反例参数不同，独立数学见证与源码审查显示它们暴露相同的CRT取值限制；不能将两个反例报为两个独立缺陷。

正确实现负控制保留：Z在新确认上30/30，未被修订。普通诊断对Z提出整数值/整数系数混淆的错误解释，但其测试全部超出冻结可信域；性质驱动也有大量范围外提案。因此本轮既暴露了文字误诊，也暴露测试提案遵守范围不足，不能声称已经可靠估计误报率。没有反例时不改代码的门控实际阻止了无依据修改。

交付链路可靠运行，所有原始响应、一次澄清、静态验收、独立评分及源码版本完整保留。总计{len(costs)}次真实响应、{metrics['tokens']:,} tokens，估算${metrics['estimated_usd']:.6f}；无UNKNOWN。细分参见costs.json。

停止于预注册有限尝试，不再追加修订来得到正向结果。结论是本轮修复NO-GAIN，而不是证明性质机制总体无效。只有一个原题的两个既有程序版本、单次采样、有限评分域和30条新参数，不能推出稳定跨题收益。本轮新确认现已曝光；后续不得改代码后再称未见确认。
''')
 write('README.md','''# 交付索引
- Final_Report.md：研究结论。
- Discovery_Report.md：发现、重复缺陷、误报与范围外提案。
- Repair_Report.md：共同反例、修订、确认及回归。
- Protocol_and_Audit.md：冻结、成本、零API与真实Worker验收。
- protocol.json / freeze.json / frozen_source：运行前冻结。
- discovery.json / shared_counterexamples.json / repair_plans：实际发现和相同反馈。
- jobs：原始请求、响应、规范化、拒绝及账本。
- parents / artifacts / candidate_freeze.json：真实源码及版本。
- evaluation.json / shared_counterexample_recheck.json / score_matrix.json：完整成绩。
- revision_diff_audit.json / Q_C_source.diff / Q_D_source.diff：源码与行为区别。
- private/root_cause_witnesses.json：仅宿主使用的事后数学归因。
- costs.json / metrics.json / wire_audit.json / pipeline_states.json：机器记录。
不包含新模型调用入口以外的第二套执行系统；沿用现有BoundedCompiler、PersistentBudget、接收层与Linux Worker。
''')
 r.save(OUT/'exposure_registry.json',dict(status='CLOSED_NO_RESULT_DRIVEN_RERUN',cases=[dict(id=x['id'],parameters_sha256=r.fingerprint(x['parameters']),future_role='EXPOSED_DEVELOPMENT_ONLY') for x in r.load(OUT/'private/confirmation.json')]))
 r.save(OUT/'final_audit.json',dict(history_unchanged=True,files=len(history),pending=pending,unique_response_ids=len(costs),source_freeze_verified=True,common_counterexamples_identical=True,remaining_worker_containers=subprocess.check_output(['docker','ps','-a','--filter','name=flowevo-','--format','{{.Names}}'],text=True).splitlines()))
 print(json.dumps(metrics,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
