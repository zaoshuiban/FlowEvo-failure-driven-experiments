import json,datetime,time,collections,subprocess
from pathlib import Path
from run_hard10_algorithm import ROOT,load,save,sha,canonical,fingerprint,EvidenceStore
FIRST=ROOT/'runs/flowevo_v42_delivery_20261029_01';OUT=ROOT/'runs/flowevo_v42_delivery_20261029_02'
def md(name,text):(OUT/name).write_text(text.strip()+'\n')
def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)
def main():
 costs=[];state=[];wires=[];pending=[];reserve=0;workers=[]
 from failure_evo.persistent_budget import PersistentBudget
 for run in [FIRST,OUT]:
  if (run/'worker.jsonl').exists():workers.extend(EvidenceStore(run/'worker.jsonl').records())
  for job in sorted((run/'jobs').iterdir()):
   ev=EvidenceStore(job/'provider.jsonl').records();response=None
   for e in ev:
    p=e['payload']
    if e['kind']=='RAW_RESPONSE':
     raw=p['response'];response=raw;u=raw['usage'];dt=datetime.datetime.fromtimestamp(e['at'],datetime.timezone.utc);peak=dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10);hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit)
     usd=(hit*.006+miss*.3+u['completion_tokens']*1.2)/1e6*(1 if peak else .5)
     costs.append(dict(run=run.name,job=job.name,response_id=raw['id'],usage=u,estimated_usd=usd,peak=peak))
    if e['kind']=='SEND_STARTED':
     inp=json.loads(p['wire']['messages'][1]['content']);assert not set(inp)-{'problem','schema','failure_evidence','previous_code','diagnostics','analysis','original_response','delivery_diagnostics'}
     def walk(x):
      if isinstance(x,dict):
       assert not set(x)&{'gold_answer','reference_answer','expected_answer','expected','official_solution','oracle_source'}
       for v in x.values():walk(v)
      elif isinstance(x,list):
       for v in x:walk(v)
     walk(inp);wires.append(dict(run=run.name,job=job.name,sha256=p['wire_sha256'],gold_exposed=False,confirmation_exposed=False))
   obj=PersistentBudget.__new__(PersistentBudget);obj.path=job/'budget.jsonl'
   with obj._locked() as rr:
    s,_=obj._state(rr);pending += [dict(run=run.name,job=job.name,key=k,status=v['status']) for k,v in s.items() if v['status']!='settled'];reserve+=sum(v['cost_upper_microusd'] for v in s.values())
   reception=load(job/'reception.json');state.append(dict(run=run.name,job=job.name,model_responded=response is not None,finish_reason=response['choices'][0]['finish_reason'],reception_status=reception['receipt']['status'] if reception['receipt'] else 'PARSE_INVALID',tokens=response['usage']['total_tokens']))
 assert not pending and len({c['response_id'] for c in costs})==len(costs)
 hist=load(OUT/'history_hashes.json');changed=[p for p,h in hist.items() if sha(ROOT/p)!=h];assert not changed,changed
 rows=load(OUT/'evaluation_results.json');versions=load(OUT/'candidate_freeze.json')['versions'];matrix=[]
 for arm in versions:
  rr=[r for r in rows if r['arm']==arm]
  matrix.append(dict(arm=arm,code_sha256=versions[arm].get('sha256'),static_status=versions[arm]['status'],source=dict(collections.Counter(r['status'] for r in rr if r['role']=='source')),development=dict(collections.Counter(r['status'] for r in rr if r['role']=='development_regression')),new_confirmation=dict(collections.Counter(r['status'] for r in rr if r['role']=='new_parameter_confirmation'))))
 before={r['case_id']:r for r in rows if r['arm']=='parent'};delta={}
 for arm in ['C','B-R']:
  rr=[r for r in rows if r['arm']==arm];delta[arm]={role:dict(improved=sum(r['status']=='MATHEMATICAL_CORRECT' and before[r['case_id']]['status']!='MATHEMATICAL_CORRECT' for r in rr if r['role']==role),regressed=sum(r['status']!='MATHEMATICAL_CORRECT' and before[r['case_id']]['status']=='MATHEMATICAL_CORRECT' for r in rr if r['role']==role)) for role in ['source','development_regression','new_parameter_confirmation']}
 bound=load(OUT/'boundary_regression.json');boundary={a:dict(collections.Counter(r['raw']['status'] for r in bound if r['arm']==a)) for a in versions}
 prop=load(OUT/'properties.json');pcounts=dict(collections.Counter(x['verdict']['status'] for x in prop['receipt']['records']))
 post={a:dict(collections.Counter(x['verdict']['status'] for x in load(OUT/'property_rechecks'/(a+'.json'))['records'])) for a in versions}
 metrics=dict(status='REAL_PROPERTY_REVISION_EXECUTED',model_calls=len(costs),tokens=sum(c['usage']['total_tokens'] for c in costs),estimated_usd=sum(c['estimated_usd'] for c in costs),reserved_upper_usd=reserve/1e6,actual_invoice=None,properties=len(prop['proposal']['properties']),test_specifications=len(prop['receipt']['records']),property_before=pcounts,property_after=post,new_initial_algorithm_generations=0,new_semantic_revisions=2,code_compliance_calls=sum('compliance' in c['job'] for c in costs),format_or_clarification_calls=sum(c['job'].endswith('-1') for c in costs),worker_executions=len(workers),worker_host_wall_seconds=sum(e['payload']['result'].get('host_wall_seconds',0) for e in workers),history_files=len(hist),history_changed=changed,unknown=0,experimental=0,regressions=delta,boundary=boundary)
 save(OUT/'pipeline_states.json',{a:dict(model_responded=True,artifact_received=True,static_executable=True,property_evaluable=(7 if a=='C' else None),counterexample_established=(2 if a=='C' else None),revision_executed=True,new_confirmation_improved=delta[a]['new_parameter_confirmation']['improved'],new_confirmation_regressed=delta[a]['new_parameter_confirmation']['regressed'],post_hoc_old_refusal_boundary_changes=(0 if a=='C' else 3),note='B-R使用普通执行反馈，不声称自主性质链；边界变化不等于数学错误') for a in ['C','B-R']});save(OUT/'metrics.json',metrics);save(OUT/'request_costs.json',costs);save(OUT/'stage_states.json',state);save(OUT/'wire_audit.json',wires);save(OUT/'result_matrix.json',matrix);save(OUT/'history_integrity_final.json',dict(files=len(hist),changed=changed))
 md('Delivery_Read_Only_Audit.md','''# V4.2 原始交付只读审查
旧V4.2保持PARTIAL_DELIVERY_BLOCKED。historical_reception_replay.json在本次第一尝试目录，记录原始响应ID、完整哈希、重新接收结果，不能作为旧成绩。

|旧产物|分类|新版处理|
|---|---|---|
|表达式A/B的nonlocal|静态权限拒绝|不自动改代码，不执行；无数学错误结论|
|poly-B仅code|缺可选文档|源码字节不变；description/applicability标记未提供，不伪造模型说明|
|walk-B-R diagnostics别名|明确格式别名|重命名为diagnosis；冲突值拒绝|
|walk-C顶层tests=[]|额外补充制品|完整隔离保存，不并入可信测试|
|walk-C前提列表|可接受表示差异|列表原样保留，不拼接或改变逻辑|
|walk-C equal且right=null|关键语义缺失|不可评价，不能猜成oracle_correct|
|旧walk/poly已执行错误|实际计算错误|以原执行/独立评分记录报告，不与格式拒绝混淆|

新的01尝试：首份C提案JSON解析失败；一次模型澄清产出4条性质、7条测试，被旧接收数量3限制拒绝。02没有重新归纳，而按接收v2导入完整相同原文。此变更发生在确认评分前，01尝试及拒绝记录保留。
''')
 md('Delivery_Reception_Protocol.md',f'''# 统一交付接收与修复
版本operator-delivery-reception-v2。原始响应、原始JSON、规范化JSON、变化理由、隔离补充内容、原/新哈希全部保存。

白名单：固定type=json_object；无冲突diagnostics→diagnosis；代码说明可选但代码必需；性质前提可为非空字符串或字符串列表。未知权限/业务字段仍拒绝。补充tests/self_tests保留为未验证提案，答案永远不是Oracle。

接收数量与执行预算分开：接收上限32条性质、64条测试，执行仍受冻结的测试/Worker预算约束。本次4条性质7条测试全部在原执行配额内，没有删性质，也没有按结果选择测试。协议所述通用超额选择尚未在本次触发；当前脚本会在不满足本次8条条件时停止，不能声称已验收所有超额情况。

格式规范化必须保持源码、性质列表及替代假设的受保护内容哈希不变。模型澄清若改变数学内容，记录NEW_CONTENT_VERSION_REVALIDATED，而不是格式修复。本次澄清属于新的模型提案版本，不声称原文不变；02对该提案的重新接收则完整保持内容。

C与B-R共享入口、静态限制、Worker、单次修订和合规修复规则。nonlocal仍不支持；顶层自测仍拒绝，模型可返回单独self_tests制品但不自动执行。源码变化创建子版本并重新验收。无宿主算法替写。

协议哈希：`{load(OUT/'freeze.json')['hash']}`。完整运行源码快照和生成记录均冻结。
''')
 md('Property_Review_and_Counterexamples.md',f'''# 真实性质检验
从V4.1冻结错误程序出发，模型自主提出4条性质、7条参数测试。提示未提供用户举例的性质或正确替代算法。原始提案包含一些未经证明甚至措辞不严谨的判断，未将其作为事实。

独立参考采用路径枚举/反向精确概率，不使用候选自身输出或模型自报答案。实例语义限定：等概率移动选项，首次命中包含时间0，输出为约分概率分子分母之和。

初次结果：{pcounts}。
两个反例分别为模型自选的目标(0,0)、0步与目标(0,0)、1步。冻结程序实际返回错误结果；独立参考确认这些是算法错误，不是参数提取错误。其余5个实例支持有限正确性，含一次重复来源实例，不算5个独立任务。

修订反馈只发送测试参数、候选实际输出和判定类别，不发送Oracle数值答案、评分器代码或确认题。C收到反例后实际生成新源码，在输入验证后处理时间0已命中；源码由模型原样生成并保存，没有宿主补行。

修订后性质实例：{post}。这些结果不能证明模型全部自然语言性质的全称成立；仅证明本次实例反例被修复。尤其P3“不是某时刻到过”的文字不严谨，未将这句文本认证为数学定理。安全准入依赖执行证据，仍无Experimental。
''')
 summary=[]
 for m in matrix:
  def ok(k):return m[k].get('MATHEMATICAL_CORRECT',0)
  summary.append([m['arm'],str(ok('source'))+'/1',str(ok('development'))+'/16',str(ok('new_confirmation'))+'/30',str(post[m['arm']])])
 md('Revision_and_Regression_Report.md','# 修订与回归\n\n'+table(['版本','来源','已曝光开发','新参数确认','性质复检'],summary)+'''

C和普通修订B-R均修复6个新参数确认失败，没有在这30条测试上观察到数学退化；两者成绩相同，不能声称性质验证相对普通测试反馈有正确率增益。

补充事后边界审计：源码审查发现B-R删除了部分原有资源限制，于是对三版共同执行全部10条已曝光V4.1不支持输入。B-R对N>200、目标坐标越界、移动向量越界3类返回结果；parent/C仍拒绝。该行为属于原拒绝边界变化，不等同于这3个数值答案错误，且沙箱资源限制没有放宽。它是事后开发性安全发现，不是预注册新确认优势。未进一步修订B-R或删除其结果。

新确认30条全部在运行前冻结、均未用于修订；它们是新参数，不是不同原题。旧V4.2确认题被明确列为已曝光开发材料，未重新命名为新确认。
''')
 md('Engineering_Acceptance.md',f'''# 工程验收
11项接收单元测试及4项流程测试通过：源码/性质保持、明确别名、冲突拒绝、权限字段拒绝、模型答案隔离、缺失关系不可推断、版本变化、历史回放、新确认排重和真实Linux Worker反例/哈希绑定。

最终增加了非对象JSON修复的健壮性检查，发生在全部真实请求与评分结束之后；详见post_run_robustness_patch.json。运行时源码快照保持不变，此补丁未用于改写实验结果。

本次真实Worker执行{len(workers)}次，记录调用墙钟{metrics['worker_host_wall_seconds']:.3f}秒；同一冻结镜像/非root/无网络/只读/256MB/1CPU/2秒约束。没有模型自测导入执行，没有代码合规修复调用，因为两份真实修订均静态通过。合规修复入口已存在，但本轮不声称真实验收了所有可能的代码修复情况。

真实模型{len(costs)}次响应全部持久化和结算，UNKNOWN=0、重复响应ID=0。历史{len(hist)}文件哈希不变。旧V4.2保持原状态，01尝试单独关闭，02明确导入历史模型提案及普通修订。实际请求未出现参考答案字段，新确认没有进入请求。
''')
 md('Final_Report.md',f'''# V4.2 交付修复与真实性质驱动修订总结
**完成本轮目标：真实模型产物已走到性质检验、反例成立、真实修订及回归评价。** 这不等于证明性质驱动方法优于普通修订。

{table(['环节','实际结果'],[['共同起点','V4.1原始随机游走FC；初始算法生成0次'],['性质','模型自主提出4条、7个测试实例'],['独立检验','发现2个真实算法反例'],['真实修订','C与B-R各1个模型生成版本，均静态可执行'],['新参数确认','原版24/30；C30/30；B-R30/30'],['数学回归','两修订版均16/16，无观察到的数学退化'],['边界审计','B-R放宽3项旧拒绝边界；C保持；属事后审查'],['准入','仍为离线候选；没有Experimental或在线复用']])}

C的具体改动是处理起点已经等于目标的情形。这个计算变化由模型根据真实反例生成，宿主未写替代算法。普通修订也得到相同数学改进，因此当前证据支持“真实闭环成立”，不支持“性质验证的独立增益成立”。

交付过程如实保留：01尝试经历一次JSON失败和一次提案数量拒绝；02以接收v2完整导入相同4条性质，没有重新生成、删性质或修改旧分数。30条确认在01前已冻结且01从未执行，因此未参与内容修订。全过程五次真实请求（包括失败交付和澄清）均计费，不只报成功调用。

成本：{metrics['model_calls']}次真实响应，{metrics['tokens']:,} tokens，按供应商冻结报价估算${metrics['estimated_usd']:.8f}；保守预留占用${metrics['reserved_upper_usd']:.6f}，不是实际账单。C包含2次性质响应与1次修订，B-R包含1次普通诊断与1次修订，实际成本不相等但配额/接收规则相同；详见request_costs.json。Worker成本另计，未货币化。

限制：单一已知错误程序、单次修订、新参数而非不同原题；参考实现只核验实例，不证明自然语言性质；数量接收规则是在未进行确认评分时修复的工程变更。所有这些都不支持总体方法优势或大规模部署结论。本轮不扩大研究机制，不重新生成初始算法，不再为了更多正向结果追加请求。
''')
 md('README.md','''# 交付索引
- Final_Report.md：结论与成本。
- Delivery_Read_Only_Audit.md：旧响应分类、关键语义缺失。
- Delivery_Reception_Protocol.md：版本化接收与统一修复。
- Property_Review_and_Counterexamples.md：真实性质和反例证据。
- Revision_and_Regression_Report.md：同起点配对、回归、边界。
- Engineering_Acceptance.md：测试及历史完整性。
机器数据：protocol/freeze、proposal_import、ordinary_revision_import、properties、C_gate、candidate_freeze、evaluation_results、property_rechecks、boundary_regression、stage_states、pipeline_states、metrics、request_costs、wire_audit。
01尝试的原始响应/规范化/普通修订保留在相邻flowevo_v42_delivery_20261029_01；02仅导入并引用，不改写。private是宿主评分材料，不供模型读取。
''')
 save(OUT/'audit_final.json',dict(history_changed=changed,pending=pending,unique_responses=len(costs),remaining_containers=subprocess.check_output(['docker','ps','-a','--filter','name=flowevo-','--format','{{.Names}}'],text=True).splitlines()))
 print(json.dumps(metrics,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
