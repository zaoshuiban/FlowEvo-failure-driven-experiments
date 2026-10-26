"""Produce reports only from completed offline artifacts; never sends requests."""
import pathlib,json,hashlib,collections,time,subprocess
P=pathlib.Path(__file__).resolve().parent;R=P.parents[1]
def read(n):return json.loads((P/n).read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
while not (P/'acceptance_summary.json').exists() or not (P/'downloads_complete.json').exists():time.sleep(20)
s=read('inventory_summary.json');a=read('acceptance_summary.json');sel=read('selected_metadata.json');inv=read('inventory.json');w=read('worker_results.json')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
files=list(P.glob('*.py'))+[P/n for n in ['protocol.json','inventory.json','selected_metadata.json','worker_protocol.json','scorer_worker_acceptance.json','learning_public_tasks.json','learning_sealed_tasks.json','confirmation_public_tasks.json','confirmation_sealed_tasks.json','learning_lineage.json','confirmation_lineage.json']]
protected=[R/'runs/s20_preparation_20261025_01'/n for n in ['external_public_tasks.json','external_sealed_tasks.json','external_lineage.json','external_worker_results.json']]
manifest={'git_commit':head,'new_model_requests':0,'files':{str(f.relative_to(R)):sha(f) for f in files},'preserved_strict_A_files':{str(f.relative_to(R)):sha(f) for f in protected},'source_receipts':[read(f.name) for f in sorted(P.glob('*.receipt.json'))], 'scorer_sources':read('scorer_receipts.json'),'worker_config':json.loads((R/'reports/s19_v2_acceptance/worker_environment.json').read_text()),'paid_experiment_authorized':False}
(P/'freeze_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
table='\n'.join('| '+k+' | '+str(v)+' |' for k,v in s['source_split_counts'].items())
tiers='\n'.join('| '+k+' | '+str(v)+' |' for k,v in s['tiers'].items())
quota='\n'.join('| '+role+' | '+k+' | '+str(v)+' |' for role,counts in s['quota_counts'].items() for k,v in counts.items())
(P/'S20_External_v2_Data_Inventory.md').write_text(f'''# S20-External-v2 全量数据与分层准入报告

状态：完成离线数据准备；本数据准备新增模型请求为0。已有S20-A是独立授权运行，未改变其任务、预算或历史结果。

## 实际候选池

共读取{s['total']}条官方记录，不是{s['total']}道独立原题。跨源、跨划分去重后按组件隔离。

| 官方来源与划分 | 记录数 |
| --- | ---: |
{table}

| 全量元数据层级 | 数量 |
| --- | ---: |
{tiers}

A层是原有60题，原文件另存于旧Run，保持不变；不会把新B层直接升级为A。上述B为元数据准入，只有选定池完成逐题Worker验收。C层原因及B薄覆盖任务保留在inventory.json，不进入主实验。

本轮学习池{len(sel['learning'])}题、确认池{len(sel['confirmation'])}题。目标分别450和150；缺额不会靠降低判分正确性补齐。

| 角色 | 配额层 | 实际数量 |
| --- | --- | ---: |
{quota}

完整源缓存位于 /Users/majiatong/lab/AFlow/data/sources/s20_external_v2；旧APPS test及CC test复用原始缓存。release_v6读取test至test6，不是仅test6。revision、SHA256、文件大小和官方LFS哈希见freeze_manifest.json及receipt文件。

## 曝光和重复

规范化题面、原题URL、参考源码哈希、五词shingle近重复组件共同用于排查。{s['exposed_components_tasks']}条记录属于保守历史曝光组件。历史TACO、已用于研发的材料、旧严格60题和已有LCB test6记录不重新称作新确认题。

元数据读取不等于Operator调参曝光；因此没有因为曾读取APPS test元数据就整体剔除5000题。CC train用于学习、valid/test用于确认。APPS train优先学习，APPS test按事前哈希划为研究开发与确认两部分，保留官方test标签，不将研究开发题称作未见确认；LCB同样保留官方test标签再分研究角色。学习和确认池组件不重叠。近重复使用bottom32候选检索后完整Jaccard≥0.85确认，可能遗漏改写和跨语言近重复，不能声称绝无泄漏。基础模型预训练曝光未知。

不按目标模型结果选题；没有目标模型预跑。完整分难度统计及重叠排除原因见inventory_summary.json，各排除原因不能相加。
''')
(P/'S20_External_v2_Scoring_Acceptance.md').write_text(f'''# S20-External-v2 评分与隔离验收

实际Linux Worker完成{a['tasks']}道选定任务，验收通过{a['passed']}道；有可执行人类参考在所验测试上通过的任务{a['human_reference_agreement']}道，其余{a['official_oracle_only']}道依赖官方输入输出依据。新增模型API为0。

每题在线集与至少6个封存输入接受正反检查。每题最多24个最终封存输入另存，初始Worker验收覆盖前6个；其余官方测试仅保留于固定原始源及可重建引用，不假称已经全部执行。在线输入来自题面样例或协议事先开放的官方测试；后者不称为题面公开样例。APPS中疑似在题面直接出现的官方输入保守归在线，不进入封存。

正向输入输出回放只证明Worker传输及比较器可用，不证明程序算法正确，不称为独立参考程序。错误常量程序须在全部已检输入被拒绝。人类参考独立运行结果和错误日志保存在worker_results.json；缺参考不再是一票否决。

## 比较语义

- LCB：固定官方grade_stdio比较逻辑，逐行strip、字符串或Decimal向量精确比较；27项适配器测试和其中6项LCB官方代码差异测试均在Worker通过。执行传输使用现有Worker，不称为完整官方排行榜runner的逐位复现。
- CodeContests：采用官方token及大小写逻辑，对整数预期增加精确比较，避免浮点将大整数错误接受；该安全修正会拒绝官方通用容差可能接受的123与123.000001。不是无差别官方metric复现。官方通用比较器不能替代多解题特殊判分器。
- APPS：使用官方标准输入输出及有序token比较，保留重复元素，禁用旧实现的集合/四舍五入宽松分支。属于事前定义的研究比较器，不与官方排行榜分数混算。

特殊判分、交互、未支持函数式入口和不明输出契约进入C。输出契约机器筛查不是语义证明；出现评分争议必须隔离该任务并记录，不可将其失败用于算子晋级。

Worker沿用原镜像与权限，单线程离线验收，与独立S20-A并行时的本地耗时不能直接作为模型实验效率比较。实测本地累计运行时间{a['local_seconds']:.2f}秒；工具账本逐题保留，未货币化。
''')
(P/'S20_External_v2_Stream_Protocol.md').write_text(f'''# S20-External-v2 任务池与使用协议

学习池{len(sel['learning'])}题，确认池{len(sel['confirmation'])}题。完整ID顺序见selected_metadata.json；按冻结种子在难度层内排序，再独立冻结全流顺序，不以原始文件前缀或模型表现选择。

学习运行只冷启动一次，建议每20题一批，批间保留失败证据、机制假设及Operator。确认池在学习完成并锁定制品后使用；不得根据确认结果继续选择同一版本并仍声称独立确认。

三组使用同题同顺序、同模型、同在线评价、同基础动作及正常求解额度。F学习/验证/失败回退成本和M文本经验生成/注入成本必须全部累计。封存测试在在线状态锁定后执行；最终结果不进入在线学习请求。C及薄覆盖不混入主结果，A严格60单列且属于已验收历史材料。

本轮只冻结数据与评分适配器，未改Operator生成、路由、代际管理或五阶段Controller。正式运行入口需明确采用external-scorer-v2适配器，不能将任务直接交给旧tokens入口并声称已使用LCB逐行语义。

未授权新的外部付费实验。原S20-A协议与$66授权不转移。按旧80题$66硬额度仅做线性容量参考，{len(sel['learning'])+len(sel['confirmation'])}题三组约${(len(sel['learning'])+len(sel['confirmation']))*66/80:.2f}，不是预计实付、当前报价或已冻结预算。正式费用还需按模型价格、学习次数、输入上界和验证额度另行核对；没有新授权不启动。
''')
(P/'README.md').write_text(f'''# S20-External-v2 数据包

全量元数据{s['total']}条；学习池{len(sel['learning'])}题；确认池{len(sel['confirmation'])}题；选定池Worker验收{a['passed']}/{a['tasks']}；本数据准备0次模型API。

- [全量准入与曝光审计](S20_External_v2_Data_Inventory.md)
- [评分器与Worker验收](S20_External_v2_Scoring_Acceptance.md)
- [冻结任务流与使用协议](S20_External_v2_Stream_Protocol.md)
- freeze_manifest.json：源码、协议、任务、测试、官方来源与SHA256。
- learning_public_tasks.json / confirmation_public_tasks.json：在线入口材料。
- learning_sealed_tasks.json / confirmation_sealed_tasks.json：仅外部最终复核，禁止混入在线入口。
- candidates/：离线审计材料，包含参考和封存内容，禁止整体发送给模型。

这些是评分可信度分层的数据准备结果，不是模型泛化或失败学习收益结果。旧严格60及TACO80未改写。
''')
print('REPORTS FROZEN',len(sel['learning']),len(sel['confirmation']),flush=True)
