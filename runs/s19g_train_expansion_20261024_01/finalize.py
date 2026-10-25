import pathlib,sys,json,hashlib,collections,math,subprocess,time
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1];O=R/'runs/s19g_preparation_20261024_01';sys.path.insert(0,str(R/'scripts'));import run_workflow_v2 as e
from failure_evo.contracts import strict_stream_task,fingerprint
from failure_evo.workflow_protocol_v2 import prepare,memory_messages,Limits,PreflightRejected

def wr(n,x):e.write(P/n,x)
def read(p):return e.read(p)
old=read(O/'tasks.json');new=read(P/'tasks.json');alltasks=old+new
assert len({t['original_url'] for t in alltasks})==len(alltasks)
# Future sequence fixed from metadata only after reference admission, never target-model correctness.
seed='S19G-GMF-stream80-order-v1';groups=[]
for d in ('MEDIUM','MEDIUM_HARD','HARD','VERY_HARD'):
 groups.append(iter(sorted([x for x in alltasks if x['difficulty']==d],key=lambda x:hashlib.sha256((seed+'|'+x['original_url']).encode()).hexdigest())))
import itertools
ordered=[x for row in itertools.zip_longest(*groups) for x in row if x is not None]
public=[];sealed=[];lineage=[];refs={};n=len(ordered);batch=10;b=math.ceil(n/batch)
for pos,t in enumerate(ordered):
 cases=[]
 for c in t['public_cases']:
  is_sample=c.get('provenance')=='verbatim statement sample';a={k:c[k] for k in ('input','expected','comparison','scorer')}
  a.update(visibility='public',legal_verified=True,source={'kind':'public_statement' if is_sample else 'public_dataset','id':t['original_id']+('::statement' if is_sample else '::predesignated-online-development'),'case_sha256':fingerprint([c['input'],c['expected']])});cases.append(a)
 tp=dict(t['task_public']);tp['public_examples']=[dict(c) for c in cases if c['source']['kind']=='public_statement']
 pub=strict_stream_task({'task_id':t['task_id'],'dataset':'taco','difficulty':t['difficulty'],'role':'prospective_online','task_public':tp,'public_cases':cases});public.append(pub)
 hid={'task_id':t['task_id'],'role':'sealed_final_evaluator_only','cases':t['audit_cases']};sealed.append(hid)
 onlinekeys={ ' '.join(x['input'].split()) for x in cases};finalkeys={' '.join(x['input'].split()) for x in hid['cases']};assert len(finalkeys)==12 and not onlinekeys&finalkeys
 assert sum(c['source']['kind']=='public_dataset' for c in cases)==12
 src=P if t in new else O;rh=[]
 for f in sorted((src/'tasks'/t['original_id']).glob('reference_*.py')):
  import ast
  h=e.sha(f);ah=hashlib.sha256(ast.dump(ast.parse(f.read_text()),include_attributes=False).encode()).hexdigest();rh.append({'path':str(f.relative_to(R)),'sha256':h,'ast_sha256':ah})
  if ah in refs and refs[ah]!=t['task_id']:raise ValueError('cross-task reference lineage overlap')
  refs[ah]=t['task_id']
 assert len(rh)==2 and rh[0]['ast_sha256']!=rh[1]['ast_sha256']
 lineage.append({'position':pos+1,'task_id':t['task_id'],'original_id':t['original_id'],'original_url':t['original_url'],'difficulty':t['difficulty'],'question_sha256':hashlib.sha256(' '.join(tp['prompt'].split()).encode()).hexdigest(),'source_split':'train' if t in new else 'test','reference_implementations':rh,'statement_samples':sum(c['source']['kind']=='public_statement' for c in cases),'online_development_tests':12,'sealed_final_tests':12,'prior_operator_development':False,'prior_scoring_admission':True,'source_qualification_directory':str(src.relative_to(R))})
wr('stream_tasks.json',public);wr('sealed_final_tasks.json',sealed);wr('task_lineage_manifest.json',lineage)
raw=read(P/'metadata_funnel.json');acc=read(P/'acceptance_summary.json');review=read(P/'output_contract_review.json');res=read(P/'scoring_acceptance.json')
failures=[]
for x in res:
 if not x['passed']:failures.append({'id':x['id'],'reference_results':[{'status':v['result']['status'],'passed':v['result']['tests_passed'],'total':v['result']['tests_run']} for v in x['references']],'reason':'fewer than two fully passing references or negative rejection failed'})
wr('admission_funnel.json',{'official_shard_rows':raw['raw'],'metadata_eligible':raw['eligible_before_train_dedup'],'after_near_lineage_dedup':raw['frozen_candidates'],'after_output_contract_review':sum(x['accepted'] for x in review['rows']),'worker_examined':acc['examined'],'worker_passed':acc['passed'],'selected_train':len(new),'extra_reference_verified_reserve':acc['reference_verified_reserve'],'existing_test':len(old),'total_frozen':n,'unexecuted_candidates':sum(x['accepted'] for x in review['rows'])-acc['examined'],'worker_failures':failures,'metadata_rejection_counts_nonexclusive':raw['rejection_reasons_nonexclusive']})
# Task-level exposure registry for subsequent pool construction; no prior files changed.
examined={x['id'] for x in res};chosen={x['original_id'] for x in new}
wr('new_task_exposure_registry.json',[{'original_id':x['id'],'original_url':x['url'],'question_hash':x['question_hash'],'source_split':'train','metadata_reviewed':True,'reference_executed':x['id'] in examined,'selected_for_future_stream':x['id'] in chosen,'target_model_executed':False,'operator_induction_or_tuning':False,'future_reuse_requires_role_disclosure':True} for x in read(P/'candidate_order.json')])
# Freeze only existing implementation; no production source edits.
deps={str(p.relative_to(R)):e.sha(p) for d in ('FlowEvo/src','scripts') for p in (R/d).rglob('*.py')};wr('source_dependencies.json',deps)
olddeps=read(O/'source_dependencies.json');assert all(e.sha(R/k)==v for k,v in olddeps.items())
checked=read(R/'reports/s19e_zero_api_replay_20261024_03/original_files_after.json');assert all(e.sha(R/'runs/s19_stream20_20261024_01'/k)==v for k,v in checked.items())
wr('integrity.json',{'old_source_dependencies_unchanged':True,'historical_run_files_unchanged':len(checked),'initial_probe_wire_unchanged':True,'production_source_edits':0,'real_model_calls':0})
# Budget: native five calls common; M's existing memory builder has a 65536 input cap, honestly budgeted separately.
solve_calls=5*n;f_calls=4*b;m_calls=2*b;tools_per_task=max(128,5*(max(len(x['public_cases']) for x in public)+1)+20)
def cfg(calls,tools,usd,inputmax=32768):
 c=e.prior.config(calls,tools,int(usd*1_000_000),input_max=inputmax);c['wall_seconds']=86400;return c
solve_cash=math.ceil(solve_calls*40960*1.2/1e6);m_cash=math.ceil(m_calls*73728*1.2/1e6);f_cash=math.ceil(f_calls*40960*1.2/1e6)
plans=[]
base=read(R/'reports/s19f_preparation_20261024_01/plan_proposal.json')
for arm in ('G','M','F'):
 budgets={'solve':cfg(solve_calls,n*tools_per_task,solve_cash),'learning':cfg(m_calls if arm=='M' else f_calls if arm=='F' else 0,0,m_cash if arm=='M' else f_cash if arm=='F' else 0,inputmax=65536 if arm=='M' else 32768),'validation':cfg(f_calls if arm=='F' else 0,f_calls*128 if arm=='F' else 0,f_cash if arm=='F' else 0)}
 plan={k:base[k] for k in ('shared_protocol','operator_representation','model','worker_environment','compile_protocol','scheduler_protocol','allow_bounded_trials','trial_opportunities')}
 plan.update(run_id=f's19g_long{n}_{arm.lower()}_proposal_01',arm=arm,start_mode='cold',batch_size=10,evidence_kind='real_experiment',learning_evidence_protocol='learning-evidence-bundle-v1',rule_hook_enabled=arm=='F',per_task={'max_calls':5,'max_tokens':204800,'max_tools':tools_per_task,'wall_seconds':600},tasks_sha256=e.sha(P/'stream_tasks.json'),budgets=budgets,frozen_files=deps,preparation_status='PROPOSAL_NOT_AUTHORIZED',source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip())
 plan['protocol_hash']=fingerprint(plan);wr(f'plan_{arm}.json',plan);plans.append(plan)
maxcalls=3*solve_calls+m_calls+2*f_calls;reserved=(3*solve_calls*40960+m_calls*73728+2*f_calls*40960)*1.2/1e6;price_bound=(3*solve_calls+2*f_calls)*(32768*.3+8192*1.2)/1e6+m_calls*(65536*.3+8192*1.2)/1e6;hard=3*solve_cash+m_cash+2*f_cash
proposal={'status':'DATA_FROZEN_GMF_NOT_AUTHORIZED','tasks':n,'train':len(new),'previously_admitted_test':len(old),'batches':[[t['task_id'] for t in public[i:i+10]] for i in range(0,n,10)],'ordering_seed':seed,'arms':['G','M','F'],'arm_execution_order':['G','M','F'],'cold_start':'one per isolated arm; continuous within arm; never reinitialize batch state','normal_solve_calls_per_task':5,'normal_input_upper':32768,'normal_output_upper':8192,'memory_generation_input_upper':65536,'memory_generation_output_upper':8192,'max_requests':maxcalls,'conservative_token_reservation_usd':reserved,'peak_no_cache_price_upper_usd':price_bound,'hard_budget_proposal_usd':hard,'authorized_usd':0,'probe_budget_separate_usd':.25,'probe_authorized_usd':0,'offline_final_tools_cap':3*n*13+3*f_calls*13,'offline_final_wall_seconds':21600,'tool_time_not_monetized':True,'failure_evidence_and_library_arm_isolation':True,'plan_hashes':{x['arm']:x['protocol_hash'] for x in plans},'tasks_sha256':e.sha(P/'stream_tasks.json'),'sealed_sha256':e.sha(P/'sealed_final_tasks.json'),'lineage_sha256':e.sha(P/'task_lineage_manifest.json'),'price_review_sha256':e.sha(P/'pricing_review.json')};wr('long_stream_proposal.json',proposal)
# Zero-API M diagnostic using the exact historical public packet references, not final tests.
S=O/'cross_task_probe';packets=[read(R/x['path']) for x in read(S/'host_reference_manifest.json')]
try:
 prepared=prepare(memory_messages('',{'packets':packets}),limits=Limits(input_token_upper=65536),json_output=True);memory_check={'status':'SENDABLE','input_upper':prepared.input_upper,'wire_sha256':prepared.sha256}
except PreflightRejected as exc:memory_check={'status':'NOT_SENT','reason':exc.reason,'details':exc.details}
wr('memory_protocol_preflight.json',dict(memory_check,real_calls=0,scope='five historical public events; not future long-run guarantee',existing_input_limit=65536,existing_behavior='preflight failure preserves prior text memory, no silent truncation or budget increase'))
# Preserve explicit task-level historic train search evidence, ignoring current preparation itself.
paths=[x for x in (P/'train_reference_paths.txt').read_text().splitlines() if P.name not in x];wr('train_history_search.json',{'prior_matching_paths':paths,'patterns':['taco-train','taco_train'],'available_roots':['AFlow/results','FlowEvo/datasets','FlowEvo/reports','FlowEvo/runs'],'metadata_identity_exclusion':'all1000 TACO test plus available extracted tasks and LCB metadata; canonical URL / normalized question / 5gram / program hash proxies','limitation':'not a proof against missing or externally held exposure records; not pretraining cleanliness'})
# Reports have separate new names, old S19G records remain immutable.
D=R/'reports';rel='../runs/'+P.name+'/'
def report(name,s):(D/name).write_text(s)
probe=read(P/'probe_preflight.json');funnel=read(P/'admission_funnel.json');difficulty=dict(collections.Counter(x['difficulty'] for x in ordered))
report('S19G2_Cross_Task_Probe_Status.md',f'''# S19-G后续：历史跨任务诊断状态

**未授权，0次真实模型请求。** 未继承S19-F预算，也没有创建授权文件或模型发送器。

复核2道原题、5个失败事件，observed_at≤available_from≤原cutoff `{probe['source_cutoff']}`；所有原始packet及冻结wire哈希一致。wire SHA `{probe['frozen_wire_sha256']}`，保守输入17,878，输出上限8,192。协议及deepseek-flash模型未变。

原最早合法来源已按时间、event_id固定：`{probe['fixed_source']['task_id']}:{probe['fixed_source']['stage']}`，event `{probe['fixed_source']['event_id']}`。不能按模型结果换来源。

独立申请预算**$0.25**：生成2次、来源验证2次，每通道$0.125；最大token保守预留$0.196608。只允许初版+一次诊断修订，每版本一次原来源公开验证。不因为无效追加请求。协议、事件及价格复核见[preflight]({rel}probe_preflight.json)。

待授权后记录单/多见证假设内容差异、条件和动作变化、Generic动作与wire差异、来源完整修复/局部改善/无效、所有成本。当前这些研究结果均为**未测量**，不能把零API可发送当作模型已形成新能力。旧诊断不进入新任务流的冷启动记忆，不称独立泛化。
''')
report('S19G2_Task_Source_and_Exposure_Audit.md',f'''# S19-G后续：任务来源和曝光审计

已冻结**{n}题：新train {len(new)}题＋前轮已验收test {len(old)}题**。与此前Operator归纳/调参/选优材料分开；本轮参考评分和元数据筛查是数据准备曝光，不是目标模型求解或Operator开发。TACO train为官方训练划分，绝不声称模型预训练未见。

新源固定官方版本`d593ed0a2becbbc952230bb89be09189bf1056dc`的`ALL/train-00000-of-00009.parquet`，2,827行；SHA `{read(P/'download_ledger.json')['sha256']}`，大小及SHA与HuggingFace官方LFS记录一致。下载不执行任何远程代码，模型调用0。见[来源凭据]({rel}download_ledger.json)。

对train保守排除全部1,000个TACO test原题身份，再匹配项目任务元数据及已有LCB题面；规范化原题URL、题面SHA、词5-gram Jaccard≥0.85、原参考源码及AST哈希作为近重复和程序谱系代理。候选间同样去重。原19题按用户要求保留，但新train不重复它们。现有路径中未找到此前taco-train任务研究记录，见[曝光基线]({rel}exposure_baseline.json)、[搜索审计]({rel}train_history_search.json)。代理方法不能证明不存在语义改写或缺失的外部曝光记录。

固定难度分层和SHA顺序，不用目标模型试跑。难度分布：{difficulty}。研究分布偏向中高难Codeforces、stdin、可精确判分任务，不能外推到所有TACO/编程题。新增候选同时受公开输入输出总字节≤16000的事前通信约束，因而偏向可紧凑表示的验证材料；这不是任务难度或自然失败率的保证。所有原题URL、题面哈希、参考源码/AST谱系、分片行号及测试角色见[清单]({rel}task_lineage_manifest.json)。

train没有经过证实的官方SPJ索引可直接复用，未错误套用test的1000行索引。另在参考执行前逐一审查188个输出规范，排除非唯一构造答案、大小写宽松规则及其他现有精确比较器无法可靠覆盖的题，原文与原因保留。
''')
report('S19G2_Admission_Funnel_and_Worker_Acceptance.md',f'''# S19-G后续：完整准入漏斗及Worker验收

|环节|数量|
|---|---:|
|官方train首分片|{raw['raw']}|
|元数据/样例/24个输入/曝光/引用筛查|{raw['eligible_before_train_dedup']}|
|候选间近重复与谱系去重后|{raw['frozen_candidates']}|
|输出契约人工审查后|{funnel['after_output_contract_review']}|
|真实Worker评估|{acc['examined']}|
|Worker通过|{acc['passed']}|
|按原序选入train|{len(new)}|
|额外已验收预留|{len(acc['reference_verified_reserve'])}|
|合并旧19题的最终流|{n}|

前置筛查各拒绝原因可重叠，不能把原因计数相加当作独立题数。完整逐题原因见[漏斗]({rel}admission_funnel.json)、[元数据审计]({rel}task_exposure_and_admission_audit.json)、[评分原始记录]({rel}scoring_acceptance.json)。在每批4题隔离验收后按预冻结次序选前61个通过者，额外已验收题仅列预留，未按模型结果替换任务。

两份AST不同的原始参考实现通过全部题面样例+12在线开发+12封存输入；常量无效输出在所有同样输入上通过0例。它证明参考一致性、判分接线和负例拒绝，不是两算法独立正确性的数学证明，也不能证明所有未来错误必被检测。新参考验收累计工具{acc['budget']['tool_calls']}单元，账本记录工具时间{acc['budget']['charged_or_reserved_tool_milliseconds']/1000:.3f}秒，验收墙钟{acc['elapsed_seconds']:.3f}秒；容器启动等墙钟需另计，本地工具不作零成本宣称。

现有Linux DockerWorker、镜像及权限未改，12安全探针结果另存worker_probes.json。源码只在Worker执行，宿主只做AST/编译静态检查。旧19题沿用冻结验收并核对参考及测试文件哈希，不声称本轮重新求解。

冻结在线{sum(len(t['public_cases']) for t in public)}例，其中新增开发角色{12*n}例；封存{12*n}例。输入来自固定官方benchmark，题面样例保持原文；其余不是官方题面公开样例，而是事前指定的在线开发输入。合法性以官方来源、接口检查和参考一致性支撑；不声称每条约束均形式化证明。按规范化输入排除样例和两组之间重复，案例及参考不进入学习器的文件单独保存。

最终反馈只能在G/M/F三组全部ONLINE_LOCKED后用于报告/外部治理，禁止回填失败经验库、假设或路由。验收日志内遗留visibility=public是评分器局部字段，最终角色由sealed_final_tasks.json独立清单约束。
''')
report('S19G2_Long_Stream_Freeze_Proposal.md',f'''# S19-G后续：完整连续任务流冻结提案

**{n}题任务池达标；付费运行尚未授权。** 完整顺序、难度和原题谱系已固定，不再根据前批失败率换题。

任务SHA `{proposal['tasks_sha256']}`；封存SHA `{proposal['sealed_sha256']}`；代码提交 `{plans[0]['source_base_commit']}`，全部依赖另有文件SHA绑定。见[长期提案]({rel}long_stream_proposal.json)、[在线任务]({rel}stream_tasks.json)、[谱系与顺序]({rel}task_lineage_manifest.json)。

G、M、F为同一研究实验下三个独立持久Run，每组只冷启动一次，{b}批、每批10题，同题同序。各自成功经验库、失败库、文本记忆、假设、Operator隔离；不共享别组未来解答。批次间保留所有允许状态。历史跨任务probe的规则不偷偷注入冷启动F。固定组顺序G→M→F，记录供应商版本、时段和延迟；这是每题每组一次观测，仍有模型随机性和时间漂移限制，不宣称统计优势。

维持learning-evidence-bundle-v1、s19-compile-envelope-v2、evidence-diversity-v1、repair-choice-json-v2及五阶段Controller。不改动作、优先级或修订次数。现有普通求解温度0、thinking disabled、输出8192、输入32768，每题5次调用/204800Token；工具每题{tools_per_task}，墙钟600秒，三组一致。工具额度按更大公开集提高，避免40旧额度使后续验证被人为截断；不是减少模型预算制造失败。

G使用现有原生通用决策；M自动更新文本经验并计费；F自主聚合失败、生成规则、来源评价及受限试用。三组共有底层repair/fresh执行能力，但Generic原生策略与学到的条件选择可能不同；必须同时报告固定动作与实际wire，不把任何Prompt差别都称为规划创新。

公开失败批次为0仍继续；没有Operator不虚构收益；无未来匹配不视为负迁移。停止仅按冻结安全/污染/未知请求/无法恢复/Worker异常/硬预算条件。三组在线状态全部锁定后，最终程序、来源验证产物和实际Operator介入候选使用相应任务的封存集复核。研究问题为前瞻性连续学习信号，不以必须产生成功算子为目标。无充分复用，不开展复杂老年代或S20/S21。

执行前仍需新预算授权、Worker即时确认和plan依赖一致检查；配置是提案，绝不等同allow_real_api。M现有全文证据更新的输入上界65536，与F压缩学习的32768不同，保留并明确报告，未偷偷改造记忆系统。历史5事件零API检查见memory_protocol_preflight.json；未来更长证据仍可能预检拒绝，必须按现有规则保留旧记忆并计入失败机会，不能静默扩大输入或宣称理想化M比较。必须单独报告M的证据送达率和记忆更新成功率；M的输入预检失败不等于文本经验机制无效。这是现有完整系统的比较，不是排除所有实现因素后的纯表示形式对照。
''')
report('S19G2_GMF_Budget_and_Protocol.md',f'''# S19-G后续：G/M/F完整预算与公平比较

当前授权**$0**，无真实模型请求，不继承任何S19-F余额。正式三组提案API总硬预算 **${hard}**，独立历史probe另提$0.25。

|组|普通求解最多请求|学习最多请求|来源验证最多请求|货币硬上限|
|---|---:|---:|---:|---:|
|G|{solve_calls}|0|0|${solve_cash}|
|M|{solve_calls}|{m_calls}|0|${solve_cash+m_cash}|
|F|{solve_calls}|{f_calls}|{f_calls}|${solve_cash+2*f_cash}|

总请求上限{maxcalls}。F每批最多2作业、每作业初版及最多一次修订；来源每版本最多1调用。试用和失败回退都占本题普通5次额度，不能给F额外求解请求。M每批最多一次记忆更新及一次格式修订；没有新证据不强行花满。文本生成、注入导致的输入Token全部计费。所有费用保留通道、任务、请求及来源映射，未知费用不记0。

价格按[官方DeepSeek页面](https://api-docs.deepseek.com/quick_start/pricing/)复核：deepseek-flash / DeepSeek-V4.1-Flash-1017；峰值输入miss $0.30、hit $0.006、输出$1.20/百万Token。纯峰值且全miss、所有输入输出满额的价目上界约 **${price_bound:.6f}**；PersistentBudget沿用全部Token按$1.20/百万的更保守预留，总 **${reserved:.6f}**。两者都不是预计实付账单，${hard}为各通道向上取整后的硬限。M学习上界65536+8192，F学习/验证及三组普通求解32768+8192，已分别计入，没有漏算长记忆。

正常求解工具总上限每组{n*tools_per_task}，F独立来源验证{f_calls*128}；离线最终复核上限{proposal['offline_final_tools_cap']}单元，独立0模型调用账本，每工具保守20秒、程序每例5秒。实际工具耗时、容器启动/路由墙钟、失败回退都记录，本地时间尚未货币化，不与API美元随意相加。

三组共用任务、公开测试、参考隔离规则、模型、求解限制和基础动作，成功经验机制全部保留。M/F各自只使用当时本组公开失败；不共享最终答案，不把F更大总支出当作免费学习。既报告总成本，也报告可信正确性相当条件下的配对成本；双方均失败时花钱少不计可靠效率收益。

主要记录：公开失败机会率→独立原题证据族→单/多见证作业→送达→假设实质差异→规则差异/重复→来源效果→有限权限→未来命中/改变Generic动作→请求差异→可靠性/回退→全成本。最终复核用于评价而非在线学习。单次80题也不能消除预训练曝光或统计随机性，必须报告不确定性。

机器可读、带协议哈希的[plan_G]({rel}plan_G.json)、[plan_M]({rel}plan_M.json)、[plan_F]({rel}plan_F.json)均无授权文件。独立账本禁止通道/组间自动挪用。开始前必须重新核对价格和Worker；任何提案改动须重新冻结，不能边运行边调整。
''')
report('S19G2_Preparation_Summary.md',f'''# S19-G后续准备结论

- 新任务是否够：**是，{n}题**（train {len(new)}＋前轮test {len(old)}），完整顺序冻结。
- 评价能否暴露失败：**可验证地拒绝已验收负例并检出部分参考不一致**；不保证所有算法错误都能被12+12样例发现，不把工程验收等同模型可靠性。
- 跨任务证据是否产生有意义规则：**尚未测量**。历史probe预检通过，但未获得新的$0.25授权，0次真实学习/验证。
- 是否可开展正式长流比较：**数据、评分、预算及三组配置已准备；尚未授权启动**。M全文证据增长与模型随机性等限制已明确保留，启动前仍需Worker及依赖即时核验，不宣称长期稳定性已实测。

新增候选不曾用于目标模型选优；参考验收不是独立泛化结果。核心源码及旧S19结果未改，Suspended权限未恢复，没有启动S20/S21。

详细交付：S19G2_Cross_Task_Probe_Status.md、S19G2_Task_Source_and_Exposure_Audit.md、S19G2_Admission_Funnel_and_Worker_Acceptance.md、S19G2_Long_Stream_Freeze_Proposal.md、S19G2_GMF_Budget_and_Protocol.md。
''')
with (D/'S19G2_Long_Stream_Freeze_Proposal.md').open('a') as f:
 f.write('\n## 固定任务顺序\n\n|序号|任务|难度|原题|\n|---|---|---|---|\n')
 for t in lineage:f.write(f"|{t['position']}|{t['original_id']}|{t['difficulty']}|[原题]({t['original_url']})|\n")
with (D/'S19G2_Preparation_Summary.md').open('a') as f:
 f.write('\n## 交付文件\n\n')
 for name in ['S19G2_Cross_Task_Probe_Status.md','S19G2_Task_Source_and_Exposure_Audit.md','S19G2_Admission_Funnel_and_Worker_Acceptance.md','S19G2_Long_Stream_Freeze_Proposal.md','S19G2_GMF_Budget_and_Protocol.md']:f.write(f'- [{name}]({name})\n')
wr('artifact_manifest.json',{str(p.relative_to(R)):e.sha(p) for p in P.rglob('*') if p.is_file() and 'tmp' not in p.parts and p.name!='artifact_manifest.json'})
print(json.dumps({'tasks':n,'requests':maxcalls,'hard_usd':hard,'reserved_usd':reserved,'price_upper_usd':price_bound,'public_cases':sum(len(x['public_cases']) for x in public),'sealed_cases':12*n,'memory_check':memory_check},ensure_ascii=False))
