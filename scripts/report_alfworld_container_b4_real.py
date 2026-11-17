"""Read-only B4 actual response/execution audit. Never dispatches requests."""
import argparse,json
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
import run_alfworld_container_b4_real as R
P=R.P

def analyze(out):
 p=P.read(out/'protocol.json');r=P.read(out/'result.json');P.verify_history(p['historical_sha256'])
 if P.sha(Path(R.__file__))!=p['transport_binding_sha256']:raise PermissionError('binding drift')
 P.verify_history(P.read(R.PRE/'Final_Preparation_Acceptance.json')['artifact_sha256'])
 requests=[];cells={};versions=[];timestamps=[]
 for cell in R.M.CELLS:
  journal=P.EvidenceStore(out/cell/'provider.jsonl').records();sent={};raw={}
  for e in journal:
   timestamps.append(e['at']);d=e['payload']
   if e['kind']=='SEND_STARTED':sent[d['key']]=d
   elif e['kind']=='RAW_RESPONSE':raw[d['key']]=d
  if set(sent)!=set(raw):raise PermissionError('unresolved request; use partial audit instead')
  usage=Counter();phases=Counter();finishes=Counter();models=Counter();cost=0.;nocache=0.
  for key,rec in raw.items():
   wire=sent[key]['wire'];v=rec['response'];u=v['usage'];ch=v['choices'][0]
   if P.fingerprint(v)!=rec['sha256'] or P.fingerprint(wire)!=sent[key]['wire_sha256']:raise PermissionError('request hash changed')
   phase=next(k for k,value in R.M.PROMPTS.items() if wire['messages'][0]['content']==value)
   if phase=='initial' and wire!=P.read(R.PRE/'inputs'/f'{cell}.wire.private.json'):raise PermissionError('initial wire drift')
   inp=u['prompt_tokens'];op=u['completion_tokens'];hit=u.get('prompt_cache_hit_tokens');miss=u.get('prompt_cache_miss_tokens')
   if inp+op!=u['total_tokens'] or hit is None or miss is None or hit+miss!=inp:raise ValueError('usage missing or inconsistent')
   usage.update(input_tokens=inp,output_tokens=op,total_tokens=inp+op,cached_input_tokens=hit,uncached_input_tokens=miss)
   estimate=(hit*.006+miss*.30+op*1.20)/1e6;cost+=estimate;nocache+=(inp*.30+op*1.20)/1e6
   phases[phase]+=1;finishes[ch['finish_reason']]+=1;models[v['model']]+=1
   requests.append(dict(cell=cell,phase=phase,response_id=v['id'],provider_model=v['model'],finish_reason=ch['finish_reason'],usage=u,wire_sha256=sent[key]['wire_sha256'],response_sha256=rec['sha256'],peak_cached_estimate_usd=estimate))
  lineages=[x for x in r['lineages'] if x['cell']==cell];attempts=[a for x in lineages for a in x['attempts']]
  vs=[]
  for x in lineages:
   for a in x['attempts']:
    if a['path'] and P.sha(Path(a['path']))!=a['code_sha256']:raise PermissionError('candidate source changed')
    row=dict(cell=cell,lineage=x['id'],id=a['id'],status=a['status'],version=a['version'],parent=a['parent_version'],code_sha256=a['code_sha256'],diagnostics=a['diagnostics'],provider_finish_reason=a['provider_finish_reason'])
    try:row['model_reason']=json.loads(a['raw_content']).get('reason')
    except (TypeError,ValueError):row['model_reason']=None
    for role in ('train','validation'):
     ev=a.get(role+'_evaluation')
     if ev:
      if ev['candidate_version']!=a['version'] or ev['code_sha256']!=a['code_sha256']:raise PermissionError('execution version mismatch')
      row[role]=dict(metrics=ev['metrics'],cases=len(ev['case_ids']),permission=ev['permission'])
      cases=p['train'][cell] if role=='train' else p['validation'];index={c['id']:c for c in cases};branches=[]
      for result in ev['sources']+[c['result'] for c in ev['controls']]:
       c=index[result['source_ref']];score=R.E.B.score(c,result)
       branches.append(dict(case_id=c['id'],game_sha256=R.M.identity(c),task_group=c['origin']['row']['group'],scene=c['origin']['row']['scene'],task_type=c['origin']['row']['task_type'],target=c['origin']['row']['group'].rsplit('-',2)[-2],provenance=c['source_provenance'],label=c['label'],score=score,stop=result['stop'],actions=[a['action'] for a in result['actions']],decisions=len(result['decisions'])))
      row[role]['branches']=branches
      row[role]['provenance_breakdown']={kind:dict(branches=sum(b['provenance']==kind for b in branches),repairs=sum(bool(b['score']['local_repair']) for b in branches if b['provenance']==kind),won=sum(bool(b['score']['won']) for b in branches if b['provenance']==kind)) for kind in sorted({b['provenance'] for b in branches})}
    versions.append(row);vs.append(row)
  cells[cell]=dict(initials=len(lineages),initial_status=dict(Counter(x['attempts'][0]['status'] for x in lineages)),attempt_status=dict(Counter(a['status'] for a in attempts)),source_versions=sum(bool(a['code_sha256']) for a in attempts),static_pass=sum(a['status']=='STATIC_PASS' for a in attempts),train_versions=sum('train' in v for v in vs),
   repaired_lineages=sum(any(a.get('train_evaluation',{}).get('metrics',{}).get('repairs',0)>0 for a in x['attempts']) for x in lineages),selection=r['selection'][cell],usage=dict(usage),phases=dict(phases),finish_reasons=dict(finishes),provider_models=dict(models),peak_cached_estimate_usd=cost,peak_nocache_estimate_usd=nocache,ledger=r['budget']['models'][cell])
 usage=Counter()
 for c in cells.values():usage.update(c['usage'])
 worker=r['budget']['worker'];env=P.EvidenceStore(out/'environment.jsonl').records()
 summary=dict(status=r['status'],run_id=p['run_id'],protocol_sha256=P.fingerprint(p),preparation_sha256=p['preparation_protocol_sha256'],paid_requests=len(requests),cells=cells,versions=versions,requests=requests,usage=dict(usage),peak_cached_estimate_usd=sum(c['peak_cached_estimate_usd'] for c in cells.values()),peak_nocache_estimate_usd=sum(c['peak_nocache_estimate_usd'] for c in cells.values()),
  ledger_charged_or_reserved_usd=sum(c['ledger']['charged_or_reserved_cost_microusd'] for c in cells.values())/1e6,unknown_pending=sum(len(c['ledger']['unknown_or_pending_requests']) for c in cells.values()),worker=worker,environment_events=dict(Counter(e['kind'] for e in env)),new_games=0,native_G_calls=0,authorization_usd=36,history_files_verified=len(p['historical_sha256']),provider_seconds=max(timestamps)-min(timestamps),started_utc=datetime.fromtimestamp(min(timestamps),timezone.utc).isoformat(),ended_utc=datetime.fromtimestamp(max(timestamps),timezone.utc).isoformat())
 if len(requests)!=r['paid_requests']:raise PermissionError('response count mismatch')
 P.commit(out/'analysis/summary.json',summary);return summary

def report(out,s):
 rows=[];best=[]
 for c,a in s['cells'].items():
  rows.append(f"| {c} | {a['initials']} | {a['initial_status'].get('ABSTAIN',0)} | {a['source_versions']} | {a['static_pass']} | {a['train_versions']} | {a['repaired_lineages']}/{a['initials']} | {a['selection']['selected'] or '无'} |")
 vr=[];pr=[]
 for v in s['versions']:
  t=v.get('train');val=v.get('validation');tm=t['metrics'] if t else {};vm=val['metrics'] if val else {}
  if t:
   pr.append(f"| {v['id']} | "+' | '.join(str(t['provenance_breakdown'].get(k,{}).get('repairs',0))+'/'+str(t['provenance_breakdown'].get(k,{}).get('branches',0)) for k in ('NATURAL_AGENT_FAILURE','CONTROLLED_INTERVENTION'))+' |')
  vr.append(f"| {v['id']} | {v['status']} | {str(tm.get('repairs','未触达'))+'/'+str(t['cases']) if t else '未触达'} | {tm.get('won','未触达')} | {str(vm.get('repairs','未触达'))+'/6' if val else '未触达'} | {vm.get('won','未触达')} | {vm.get('incompatible','—')}/4 | {vm.get('unsupported','—')}/4 | {vm.get('control_relevance_unverified','—')} | {tm.get('errors',0)+vm.get('errors',0) if t or val else '未触达'} |")
 for cell,a in s['cells'].items():
  choice=a['selection']['selected'];v=next((x for x in s['versions'] if x['id']==choice),None)
  if v:
   t=v['train']['metrics'];q=v['validation']['metrics'];best.append(f"| {cell} | {choice} | {t['repairs']}/{v['train']['cases']} | {t['won']}/{v['train']['cases']} | {q['repairs']}/6 | {q['won']}/6 | {q['incompatible']}/4 | {q['unsupported']}/4 |")
  else:best.append(f"| {cell} | 无合格开发候选 | — | — | — | — | — | — |")
 phases=Counter()
 for a in s['cells'].values():phases.update(a['phases'])
 text=f'''# Route B4：双倍数据 S／F／FR 真实生成与开发评价

Run：`{s['run_id']}`。状态：**{s['status']}**。仅已曝光开发数据；没有新游戏、独立 Gate 或原生 G 对照。全部候选保持 Shadow。

## 冻结与授权

本轮授权上限 $36；六个独立模型账本各 $6/9 次请求，共最多54次。准备协议 `{s['preparation_sha256']}`；实际授权运行协议 `{s['protocol_sha256']}`。真实入口的4项零API测试验证与旧冻结调度器54请求wire、执行/选择、已结算恢复、UNKNOWN阻断一致；准备期43项测试保留。供应商、源码、Worker和环境通过预检。结束复核{s['history_files_verified']}项历史/输入绑定，旧B3和准备记录未改写。

D22为22游戏：11自然失败＋11受控失败、21任务组/13场景；D11固定6自然＋5受控，不是旧B3的11自然来源。共同验证14条（6MATCH/4DECLINE/4UNKNOWN），9游戏/5场景，与本轮训练分离但曾在路线A曝光。因此只能解释开发阶段能力，不能当成独立泛化。

六单元相同离线生成说明、模型deepseek-flash、temperature=0.6、thinking disabled、4096输出上限。输入容量512KiB，C/F/R投影不变，所有初稿实际wire逐字核验。模型文档版本DeepSeek-V4.1-Flash-1017，实际响应型号见summary；文档版本不等于不可变权重身份。

## 生成与候选谱系

| 单元 | 实际初稿 | 初稿弃权 | 含源码尝试 | 静态通过版本 | TRAIN评价版本 | 有来源修复的谱系 | 开发选择 |
|---|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(rows)}

真实请求{s['paid_requests']}次：初稿{phases['initial']}、工程修订{phases['engineering']}、行为修订{phases['behavior']}。未使用的机会不能转为补采样。源码版本数包含修订，不等于独立学习谱系数；静态通过不等于Worker成功或局部修复。零执行分母记为NOT_EVALUABLE，不记作环境修复失败。

## 冻结规则选择结果

| 单元 | 开发候选 | TRAIN局部修复 | TRAIN获胜 | 验证局部修复 | 验证获胜 | DECLINE错误介入 | UNKNOWN未经支持介入 |
|---|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(best)}

本轮选择规则按正例修复、边界行为与成本排序，并未要求所有边界错误清零；“合格开发候选”不是安全发布资格。所有选择都保持Shadow。无候选单元的详细执行成绩仍完整列于下表，不能只报赢家。

## 每版本实测

| 版本 | 交付/静态 | TRAIN局部修复/来源 | TRAIN获胜 | 共同验证局部修复/正例 | 共同验证获胜 | DECLINE错误作用域介入 | UNKNOWN起点未经支持介入 | 后续/无关行为待审 | 累计候选错误 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(vr)}

负例指标针对已冻结动作作用域；UNKNOWN主动观察后状态可能变化，后续行动保留待审，不能把起点标签永久套用。一般合法动作或look不算修复。整局won、投递、动作、拒绝和Worker指标在每版本原始回执及analysis/summary.json中分别保留。

选择只按冻结规则在共同验证后完成，没有把验证结果回传模型。被选者只是DEVELOPMENT_SELECTION_ONLY；不代表其所有负例安全、取得Gate或发布资格。行为修订只接收自己的TRAIN代码和公开回执，父版本也保留。

## 自然与受控来源分开统计

| 版本 | 自然来源修复/分支 | 受控来源修复/分支 |
|---|---:|---:|
{chr(10).join(pr)}

逐游戏、场景、任务类型、目标容器、动作和停止原因见summary各版本branches。相同游戏在多个版本执行不增加独立游戏数。

## 成本与运行

- 供应商真实tokens：{s['usage'].get('input_tokens',0):,}输入＋{s['usage'].get('output_tokens',0):,}输出＝{s['usage'].get('total_tokens',0):,}。
- 按真实缓存字段与冻结峰价估算：**${s['peak_cached_estimate_usd']:.6f}**；完全不计缓存峰价${s['peak_nocache_estimate_usd']:.6f}。是API费用估算，不是供应商账单。
- 持久账本charged_or_reserved：${s['ledger_charged_or_reserved_usd']:.6f}，保守预留口径，不与实际估算相加。UNKNOWN/PENDING：{s['unknown_pending']}。
- Worker调用{s['worker']['tool_calls']}。环境journal事件计数：`{json.dumps(s['environment_events'],ensure_ascii=False)}`。模型费用不包含未计价的本机CPU；Worker实际耗时和token账本见summary。
- 请求事件范围{s['started_utc']}—{s['ended_utc']}，{s['provider_seconds']:.1f}秒；环境执行耗时与总运行时间不同。
- 价格依据：[DeepSeek官方价格](https://api-docs.deepseek.com/quick_start/pricing/)，峰价输入未缓存$0.30、缓存$0.006、输出$1.20/百万tokens。

## 只读错误归因（不回流模型）

- S22_0、FR22_2：目标解析正则以容器名称/空白加`$`结尾，不接受实际目标的句末句号（如`put some vase on safe.`）；执行回执分别为goal not a bounded delivery/container-delivery task。静态可执行不等于能理解实际接口字符串。
- S22_1：直接重试无效果投递，TRAIN 22个分支全部触发NO_PROGRESS_CYCLE；动作在合法列表中不能证明物理前置条件满足。
- F22_0：源码将带正则转义的字符串当普通子串查找，移动/物体匹配又未正确处理实例编号；回执可见在两个位置之间重复导航。TRAIN 364个动作、零局部修复，15分支ACTION_LIMIT、7分支环境终止但won=false。
- S11_3：所有11来源先打开目标容器、随后拒绝继续。局部错误修复与整局成功分别为11/11、0/11，不能从最终DECLINED状态推断从未介入。其目标一致性仍须由共同负例检查。
- FR11工程版本与行为版本：实际来源和共同验证指标相同，不能把“再次交付代码”称为行为改善。
- 交付/安全：原始24初稿含5次JSON接收失败、6次静态拒绝，完整provider响应与本地错误分开保留。11次工程修订只新增1份静态通过，其余7次合法弃权、3次静态拒绝；没有手工抽取部分源码或放宽安全规则。
- 信息理解：部分F弃权理由自述看到恢复后缀，但逐字wire核验及C/F/R投影仍证明F未得到R。这是模型自述与实际输入不符，不能将其当成宿主泄漏的事实。

以上仅为真实轨迹和源码的事后开发诊断；未修改候选、未新增请求、未另测修复版。不能证明某个单独缺陷被修复后必然整体有效。

## 六项研究问题的本轮回答

1. **澄清之后是否仍大量弃权？** 初稿弃权8/24，已经突破B3的12/12弃权；但直接静态通过仅5/24，包含工程修订后6/24谱系进入Worker，仍不能称为稳定获取。
2. **D22是否更容易得到有效程序？** 本次未观察到：D11有S/FR两个来源有效谱系，D22三个单元均未产生来源有效谱系。不能由一次小样本得出更多数据必然有害。
3. **哪种信息产生真实修复？** S11生成了能局部开门但未完成投递的程序；FR11生成了能在部分来源及共同开发正例获胜的程序；F11无可执行父版本，F22执行后无修复。两份开发优胜者都存在边界问题，不能据此宣布FR整体优于S或失败信息具有独立收益。
4. **行为反馈是否改善？** 四次行为修订中三次弃权、一次静态通过；唯一可执行修订与其父版本的来源和共同验证指标一致，没有观察到改善。
5. **未见新游戏是否成功？** 未运行，NOT_EVALUABLE。
6. **主要阻断在哪里？** 生成可靠性、目标解析/实例绑定、多步状态延续，以及适用边界同时存在；有程序实际恢复，不能再概括为全部停在交付，也不能把来源有效直接当成可迁移技能。

## 解释边界与下一步

按各单元初稿弃权、真实源码及逐版本修复分别判断是否突破B3生成阻断。D22与D11差异还包含组成与模型采样差异；不单凭胜负声称数据量因果收益。S/F/FR实际输入token不等，预算上限相同不等于实际等费用。FR及行为修订结果不能归因于纯失败前缀。

本轮未运行新游戏，不能回答独立迁移成功或原生FlowEvo净收益。12游戏元数据池仍缺Safe和严格未见场景；没有按候选成绩更换池。后续先冻结独立检查点与评分，再另行授权验证，不能用新游戏调参。

完整原始响应、Python、SHA、父版本、TRAIN及共同验证回执位于`{out}`；analysis/summary.json为只读派生统计。本报告不改写原始实验结果。
'''
 target=R.D.ROOT/'reports/alfworld_failure_skill_acquisition_20261109/Route_B4_Double_Data_Result.md';P.save_exact_source(target,text);return target

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);x=a.parse_args();out=x.output.resolve();s=analyze(out);print(report(out,s));print(P.canonical({k:s[k] for k in ('status','paid_requests','usage','peak_cached_estimate_usd','ledger_charged_or_reserved_usd')}))
