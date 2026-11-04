import sys,json,time,collections,datetime,subprocess
from pathlib import Path
from run_hard10_algorithm import ROOT,load,save,sha,EvidenceStore,fingerprint
OUT=ROOT/'runs/flowevo_v42_20261028'
def table(head,rows):return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)
def write(name,text):(OUT/name).write_text(text.strip()+'\n')
def main():
 costs=[];delivery=[];wires=[];pending=[];reserved=0
 for d in sorted((OUT/'jobs').iterdir()):
  events=EvidenceStore(d/'provider.jsonl').records()
  for e in events:
   p=e['payload']
   if e['kind']=='RAW_RESPONSE':
    raw=p['response'];u=raw['usage'];dt=datetime.datetime.fromtimestamp(e['at'],datetime.timezone.utc);peak=dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10)
    hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit)
    cost=(hit*.006+miss*.3+u['completion_tokens']*1.2)/1e6*(1 if peak else .5)
    costs.append(dict(job=d.name,response_id=raw['id'],usage=u,estimated_usd=cost,peak=peak))
   elif e['kind']=='DELIVERY_STATUS':delivery.append(dict(job=d.name,**p))
   elif e['kind']=='SEND_STARTED':
    payload=json.loads(p['wire']['messages'][1]['content']);assert not set(payload)-{'problem','schema','failure_evidence','previous_code','diagnostics','analysis'}
    wires.append(dict(job=d.name,wire_sha256=p['wire_sha256'],fields=list(payload),gold_exposed=False,confirmation_exposed=False))
  # Audit append-only budget, including hash chain validation.
  from failure_evo.persistent_budget import PersistentBudget
  obj=PersistentBudget.__new__(PersistentBudget);obj.path=d/'budget.jsonl'
  with obj._locked() as rows:
   state,_=obj._state(rows)
   pending += [dict(job=d.name,key=k,status=v['status']) for k,v in state.items() if v['status']!='settled']
   reserved+=sum(v['cost_upper_microusd'] for v in state.values())
 assert not pending;assert len({c['response_id'] for c in costs})==len(costs)
 history=load(OUT/'history_hashes.json');changed=[p for p,h in history.items() if sha(ROOT/p)!=h];assert not changed
 conf=load(OUT/'confirmation_results.json');reg=load(OUT/'regression_results.json');arts=load(OUT/'candidate_freeze.json')['artifacts']
 metrics=dict(status='PARTIAL_DELIVERY_BLOCKED',real_calls=len(costs),tokens=sum(c['usage']['total_tokens'] for c in costs),estimated_usd=sum(c['estimated_usd'] for c in costs),reserved_upper_usd=reserved/1e6,actual_invoice=None,raw_code_responses=6,contract_valid_code=5,static_valid_code=3,accepted_property_proposals=0,real_revisions=0,experimental=0,pending=pending,history_files=len(history),history_changed=changed,confirmation_cases=67,confirmation_model_feedback=0)
 save(OUT/'metrics.json',metrics);save(OUT/'request_costs.json',costs);save(OUT/'wire_audit.json',wires);save(OUT/'delivery_audit.json',delivery)
 matrix=[]
 for fam,aa in arts.items():
  for arm,a in aa.items():
   rr=[r for r in conf if r['family']==fam and r['arm']==arm];sr=next(r for r in reg if r['family']==fam and r['arm']==arm and r['role']=='source')
   matrix.append(dict(family=fam,arm=arm,artifact_status=a['status'],source_status=sr['status'],confirmation=dict(collections.Counter(r['status'] for r in rr)),denominator=len(rr),source_sha256=a.get('sha256')))
 save(OUT/'result_matrix.json',matrix)
 write('V4_2_Protocol.md',f'''# V4.2 性质验证与有界修订协议
协议哈希：`{load(OUT/'freeze.json')['hash']}`。使用3类已曝光开发案例，未重新收集失败。

A仅获得题面和共同接口；B额外获得同源真实错误轨迹与二值false。C和B-R复用同一份B初始源码，分别增加一次性质提案/普通诊断和至多一次修订。两者相同模型deepseek-flash、temperature0.2、8192输出上限、同一安全Worker、最多16个开发参数执行。C由模型自选最多8条单/双输入测试；B-R使用事前固定普通测试。执行数量和实际Token不必相等，全部计费。

共享Schema来自历史FC模型声明，因此这里比较的是给定接口下的算法构建，不是无接口的自主发现。三类来源是已知案例，不提供总体平均效应或独立原题迁移证据。

确认数据在所有生成前冻结，去除旧参数及内部重复后为表达式24、随机游走22、多项式21，共67条；属于新参数，不是67道不同原题。所有版本冻结后统一评价，没有确认反馈回流。

模型提示没有包含用户举例的三条数学性质。性质必须由模型输出；宿主只提供通用关系oracle_correct/equal/different及大小边界。模型不能自报verified，也不能提供标准答案字段。没有独立参考的实例保持UNVERIFIED；有限通过只标记FINITE_SAMPLE_SUPPORTED。

失败处理事前冻结：不补字段、不自动修代码、不重复同一请求。初始B无法执行则C/B-R不启动；性质或普通诊断交付失败则该路径不进入修订。该规则使本轮受到交付阻断，不能据此否定性质验证机制。
''')
 write('V4_2_Property_Validation_Design.md','''# 自主性质与独立证据
新增property_validation.py，默认不接在线路由。

模型分开提交diagnosis、replacement_hypothesis和properties。每条性质包含claim、preconditions及具体参数测试。字段明确区分错误诊断、替代假设、待检验的性质，但文本本身始终未被认证。

宿主独立参考：表达式用标准Python AST的受限节点解释，验证前替换进制数字和显式化乘号；随机游走采用前期独立路径穷举/反向精确概率；多项式采用有理插值分母LCM。参考源码与结果不进入模型请求。

判定区分：PROPERTY_COUNTEREXAMPLE（参考结果已反驳关系）；ALGORITHM_COUNTEREXAMPLE（性质实例可审查，但候选结果不正确）；EXECUTION_FAILURE；UNVERIFIED；FINITE_SAMPLE_SUPPORTED。即使两个错误输出满足等式，也不能通过独立正确性检查。

注意：本版只能够独立审查具体参数实例及关系，不能自动证明任意自然语言前提或全域不变量。提出的性质不等于数学定理，测试通过不能获得Experimental。自由文本前提未形式化的部分仍是UNVERIFIED假设。

验证收据绑定source_sha256、proposal_sha256、evidence_sha256和角色。新版源码需要重新执行，不能继承旧版权限。原版及所有失败保留。给修订模型的反馈只有参数、候选实际输出、错误类别/二值判断，不含参考数值答案或评分器实现。
''')
 write('V4_2_Engineering_Acceptance.md',f'''# 工程验收
11项零API测试通过，另1项完整Mock链路通过：固定Mock模型提出性质→真实Linux Worker产生反例→Mock生成子版本→重新执行旧反例→确认参数验证。Mock输出只证明工程闭环，不能冒充真实模型学习成果。

覆盖模型自报verified拒绝、模型expected答案字段拒绝、错误输出满足关系仍判反例、无法评分UNVERIFIED、有限证据非全称证明、源码版本绑定、三类Oracle、A输入隔离和真实Worker执行。

真实阶段8次响应全部已结算，没有UNKNOWN或重复发送；历史{len(history)}文件哈希保持。各组同一权限；两份nonlocal源码没有人工改写。原V4.0–V4.1产物保持只读。

证据文件：zero_api_tests.log、mock_closed_loop.log、mock_closed_loop_receipt.json、wire_audit.json、delivery_audit.json、request_costs.json。本轮性质真实交付未通过，因此真实闭环仍为PARTIAL。
''')
 write('V4_2_Real_Experiment_Report.md','# V4.2 真实实验结果\n\n'+table(['案例','组','制品','来源','确认结果'],[[m['family'],m['arm'],m['artifact_status'],m['source_status'],str(m['confirmation'])] for m in matrix])+'''

实际8次响应：6次算法生成、1次性质提案、1次普通诊断；没有执行修订。6次算法响应中5次交付契约通过，3份静态可执行。

交付阻断：
- 表达式A/B均含nonlocal，按共同静态协议拒绝，C/B-R不启动。
- 随机游走C返回3条性质、5条嵌套测试，但附加顶层tests字段，未通过冻结精确契约；这些原文保存，未擅自丢弃额外字段后登记为合格。
- 随机游走B-R返回diagnostics而不是diagnosis，未进入修订。
- 多项式B仅返回code，缺description/applicability，交付失败，C/B-R不启动。

随机游走A/B在新参数上分别15/22与16/22，但两者来源仍错。多项式A确认0/21。静态/交付失败以状态报告，不混成数学错误分母。C没有合格可执行版本，不能以“0次成功”认定性质机制无效，也不能做C优于B-R的比较。

原始性质文本还含有未经验证的诊断陈述。本轮没有把模型对错误根因的解释当成事实，也没有让生成模型为自己的性质背书。
''')
 write('V4_2_Final_Report.md',f'''# V4.2 总报告
结论：**PARTIAL_DELIVERY_BLOCKED**。工程已实现性质提案、独立反例判定、版本绑定和有界修订入口，但真实模型阶段没有完成性质驱动修订，尚不能评价其收益。

|项目|结果|
|---|---|
|零API验收|11项单元＋1项完整Mock/真实Worker链路通过|
|真实模型响应|8次，无UNKNOWN、无重发|
|算法源码交付|5/6契约通过，3/6静态通过|
|真实性质提案|1份原始响应；契约未通过|
|真实自主修订|0次|
|C与同预算B-R比较|未形成有效比较|
|新参数确认|67条，四组全部状态保留；不是67道独立原题|
|Experimental/在线复用|0；未启动|

花费：{metrics['tokens']:,} tokens，估算API ${metrics['estimated_usd']:.8f}；保守预留占用 ${metrics['reserved_upper_usd']:.6f}，不是账单。历史接口及证据属于复用资产，本轮不将其既往学习成本伪记为0；当前新调用成本单独列示。Mock不计作真实学习。

主要阻断是源码权限和输出契约，不能写成“性质验证无效”。尤其本轮重新生成初始A/B使表达式路径在性质实验前即被拦住，这限制了实验的信息量。原始V4已有算法没有修改，所有新版本均另存。

当前实现只检验有限具体实例；自然语言不变量及前提并未得到通用形式化证明。下一步若继续，应先只读诊断交付契约，另行冻结能可靠接收结构化提案的版本，再考察性质验证本身。不能在本Run里事后补字段、替换初始算法、重发请求或混入新成绩。

本轮不会继续扩大请求次数来凑成功，也没有修改确认题、评分Oracle或安全规则。现有结果支持工程可运行（Mock），不支持真实模型已经形成经过性质验证的可复用知识。
''')
 write('README.md','''# V4.2 交付
- V4_2_Final_Report.md：结论与限制。
- V4_2_Protocol.md：A/B/C及同预算B-R设计。
- V4_2_Property_Validation_Design.md：性质/反例/版本接口。
- V4_2_Engineering_Acceptance.md：零API验收，明确Mock边界。
- V4_2_Real_Experiment_Report.md：所有真实候选及确认结果。
- protocol.json/freeze.json、jobs/、artifacts/、ordinary_feedback/、confirmation_results.json、regression_results.json：完整审计。
- private/：宿主独立评分材料，不供模型读取。
没有启动大规模在线复用或自动晋级。
''')
 save(OUT/'audit_final.json',dict(history_changed=changed,pending=pending,unique_responses=len(costs),container_names=subprocess.check_output(['docker','ps','-a','--filter','name=flowevo-','--format','{{.Names}}'],text=True).splitlines()))
 print(json.dumps(metrics,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
