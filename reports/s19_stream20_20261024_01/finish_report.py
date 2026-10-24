"""Post-run report and audit package; read-only toward the locked run."""
import json,hashlib,shutil,collections,datetime,copy,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PRE=Path(__file__).parent;RUN=ROOT/'runs/s19_stream20_20261024_01';OUT=ROOT/'reports/s19_stream20_20261024_01'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
s=read(RUN/'stream20_analysis.json');p=read(PRE/'plan.json');audit=read(RUN/'final_audit.json')
assert s['online_locked'] and s['funnel']['tasks_completed']==20 and not s['total']['unknown_requests']
assert not subprocess.check_output(['git','diff','HEAD','--','FlowEvo','scripts'],cwd=ROOT)
old=read(ROOT/'reports/s19_contract_revision_20261024_03/old_run_integrity.json')
old_root=ROOT/'runs/s19_real_pilot_20261024_01'
assert all(sha(old_root/f)==h for f,h in old['files_sha256'].items())
OUT.mkdir(parents=True,exist_ok=False)
for name in ('plan.json','authorization.json','authorization_record.json','tasks.json','task_manifest.json','price_quote.json','preflight.json','worker_probe.json','worker_image.json','python_requirements.txt','execution.log','freeze.py','analyze.py','final_audit.py','finish_report.py'):
 shutil.copyfile(PRE/name,OUT/name)
for name in ('stream.jsonl','hypotheses.jsonl','rule_registry.jsonl','evidence_F.jsonl','solve_budget.jsonl','learning_budget.jsonl','validation_budget.jsonl','learning_requests.json','validation_requests.json','final_audit.json'):
 if (RUN/name).exists():shutil.copyfile(RUN/name,OUT/name)
for dirname in ('jobs','assessments'):
 if (RUN/dirname).exists():shutil.copytree(RUN/dirname,OUT/dirname)
compact=copy.deepcopy(s)
for t in compact['per_task']:
 if t['selected']:t['selected']={k:v for k,v in t['selected'].items() if k!='code'}
write(OUT/'stream20_analysis.json',compact)
index={str(f.relative_to(ROOT)):dict(sha256=sha(f),bytes=f.stat().st_size) for f in RUN.rglob('*') if f.is_file()}
write(OUT/'artifact_index.json',index)
write(OUT/'final_integrity.json',dict(frozen_189_files_unchanged=True,old_pilot_files_unchanged=len(old['files_sha256']),tracked_source_unchanged=True,online_locked=True,unknown_requests=0,additional_paid_requests=0))
rows=[]
for t in s['per_task']:
 trajectory=' → '.join(e.get('stage','?')+':'+e.get('public_result',e.get('error','?')) for e in t['trajectory'])
 rows.append(f"| {t['index']} | {t['task_id']} | {trajectory} | {t['model_calls']} | {t['tokens']:,} | ${t['estimated_usd']:.9f} |")
task_table='\n'.join(rows)
channel_table='\n'.join(f"| {ch} | {v['completed']} | {v['input_tokens']:,} | {v['output_tokens']:,} | {v['total_tokens']:,} | ${v['offpeak_estimate_usd']:.9f} | {v['persistent_budget']['remaining_calls']} |" for ch,v in s['channels'].items())
hyp_table='\n'.join(f"| {h['hypothesis_id'][:12]} | {h['symptom']['artifact']} / {h['symptom']['public_result']} / {h['symptom']['finish_reason']} | {len(h['source_evidence_ids'])} / {h['independent_task_count']} | {h['evidence_version']} | {h['content_version']} | {len(h['effects'])} |" for h in s['hypotheses'].values())
start=s['stream_log'][0]['at'];end=s['stream_log'][-1]['at'];elapsed=end-start
batch_data=[]
for b in range(1,5):
 ts=[t for t in s['per_task'] if t['batch']==b]
 boundary=next(x['at'] for x in s['stream_log'] if x['kind']=='TASK_FINALIZED' and x['payload']['task_id']==ts[-1]['task_id'])
 nextstart=next((x['at'] for x in s['stream_log'] if x['kind']=='TASK_STARTED' and x['payload']['task_id']==s['per_task'][b*5]['task_id']),end+1) if b<4 else end+1
 decisions=[x['payload'] for x in [json.loads(l) for l in (RUN/'hypotheses.jsonl').read_text().splitlines()] if x['kind']=='SCHEDULE_DECISION' and boundary<=x['at']<nextstart]
 batch_data.append(dict(batch=b,public_accepted=sum(t['status']=='PUBLIC_ACCEPTED' for t in ts),native_calls=sum(t['model_calls'] for t in ts),tokens=sum(t['tokens'] for t in ts),decisions=decisions))
write(OUT/'batch_summary.json',batch_data)
key=next(iter(s['operators']));rule=s['operators'][key]['rule']
report=f'''# S19真实模型20题连续学习实验报告

## 1. 总结

**STREAM_COMPLETE / CONTRACT_ACCEPTED / SOURCE_INEFFECTIVE / REUSE_NOT_REACHED**。

20题、4批、冷启动F组按冻结协议完成，未因前5/10题没有成功Operator停止；08:13:49.731–08:21:45.590 UTC，2026-10-24，实际流墙钟{elapsed:.3f}秒。最终ONLINE_LOCKED。

| 指标 | 实测 |
|---|---:|
| 完成任务 / 全部公开检查通过 | 20 / 18 |
| 可信失败任务 / 事件 | 3 / 12 |
| 有合法动作的任务 / 事件 | 3 / 8 |
| 症状组 / 跨题症状组 | 6 / 1 |
| 已调度学习作业 / 发送过模型的作业 | 4 / 1 |
| 本地输入预检阻断作业 | 3 |
| 真实生成响应 / 完整契约通过 | 2 / 2 |
| 正式机制内容版本 / 不同规则 | 1 / 1 |
| 来源验证 / 来源成功 / 局部改善 | 2 / 0 / 0 |
| Shadow能力版本 / Experimental授权 / 后续执行 | 1 / 0 / 0 |
| 真正改变Generic动作的实际执行 | 0 |
| 真实响应 / Token | 34 / 167,646 |
| API费用估算，非账单 | **$0.067543956** |
| 未知/待结算请求 | 0 |

18/20是已曝光开发题上的有限公开通过，全部由原生流程完成；没有Operator在线介入，不能归因于失败学习，不能称独立泛化或最终正确率。没有G/M配对，没有查询私有最终复核。

## 2. 冻结、授权与完整性

- Run：`{p['run_id']}`。
- 源码：`{p['git_commit']}`。
- 计划SHA：`{p['protocol_hash']}`。
- 20题SHA：`{p['tasks_sha256']}`。
- 编译`s19-compile-envelope-v2`；调度`evidence-diversity-v1`；动作`repair-choice-json-v2`。
- 用户针对已提交计划及$8硬上限明确回复“授权,不再问我”；对应授权文件在第一次真实请求前写入。
- 189项冻结依赖在开始前、结束后均核对一致，Worker镜像与预检验收一致；旧10题Pilot的{len(old['files_sha256'])}份文件SHA未变。

未修改Prompt、选择顺序、任务、契约或策略；没有回填旧Pilot规则、预算或授权，没有恢复旧Suspended版本。本轮没有S20/S21或额外任务。

## 3. 逐题结果

仅列真实求解通道，来源验证和生成费用另计。PUBLIC_PASS只对应该题冻结公开集合。

| 顺序 | 任务 | 原生轨迹 | 请求 | Token | API估算 |
|---|---|---|---:|---:|---:|
{task_table}

456最终0/2公开通过；0313最终1/3。91在l1的0/3、l2a的1/3之后由原生l2b达到3/3，是本轮唯一有失败后原生公开恢复的任务。其余17道公开通过题均在l1通过。不要将这个恢复归到规则库。

## 4. 跨批证据累积和调度

| 批次 | 公开通过 | 求解请求 | 学习边界实际情况 |
|---|---:|---:|---|
| 1，题1–5 | 4/5 | 9 | 456的NO_ENTRY组入选；缺程序组因同来源限制跳过。入选作业输入过大，0发送 |
| 2，题6–10 | 5/5 | 7 | 91的完整程序WA证据族与456缺程序组入选。前者输入过大；后者生成、修订各1次并来源验证各1次 |
| 3，题11–15 | 4/5 | 9 | 0313新失败加入91的完整程序WA证据族，触发REVISE；输入过大，0发送 |
| 4，题16–20 | 5/5 | 5 | 没有新增失败；有动作的族按NO_NEW_EVIDENCE跳过，不人为追加学习 |

调度排除了不具备调用/回退余额的组；同来源不能同时占两席。细症状保留length/stop，粗族合并了完整程序WA的两个子类型，最后共有5条合法事件、2道原题（91与0313）。这是症状与动作相近，不是共同根因证明；谱系字段仍只是记录的代理。

这一跨题族确实获得了排序优先和REVISE调度，说明本轮不再是旧Pilot那种跨题组没有名额。但它没有通过本地请求预检，模型实际没有看到这批新增跨题材料，不能声称已经验证了“模型利用新增多任务证据修订”。

全部12条失败中，456有5条（缺程序1、NO_ENTRY 4），91有2条完整程序WA，0313有5条完整程序WA。8条有动作资格，另外4条因剩余预算不足无法保留干预和原生回退。机会覆盖仅描述本样本。

## 5. 新的直接阻断：学习输入上限

| 作业 | 来源及公开材料 | 实际wire字节 | 保守输入Token上界 | 结果 |
|---|---|---:|---:|---|
| b9cd77979639，批1 GENERATE | 456，2份NO_ENTRY失败包 | 64,049 | 66,097 | NOT_SENT |
| d21bf51ae5b4，批2 GENERATE | 91，2份完整程序WA失败包 | 37,446 | 39,494 | NOT_SENT |
| eee6dc54c208，批3 REVISE | 91+0313，5份完整程序WA失败包 | 59,953 | 62,001 | NOT_SENT |

冻结上限32,768，算法为最终wire UTF8字节+2,048余量；**这不是供应商实测输入Token，也不是模型上下文长度耗尽**。三次均在本地prepare阶段阻断，无供应商请求、无请求预算预留。仍有学习14次和来源验证14次余额，不能称为费用耗尽。

跨题累积后的输入由两份包扩展为五份包，增加了要传输的完整代码、题面与公开反馈。调度改进使该族得到机会，但现有整包输入表达不能容纳于冻结上限。执行时没有压缩材料或加大上限，完整失败输入及事后只读预检诊断均保存。

调度将已开始但本地预检失败的作业归档，其证据已被记为尝试过；没有新增证据时不重新投递。报告中的批3 REVISE是调度重试新增证据的提案，不是模型已经修订过一个跨题规则。

## 6. 机制假设版本史

| 假设ID | 症状 | 事件/原题 | evidence_version | content_version | 功能反馈条数 |
|---|---|---:|---:|---:|---:|
{hyp_table}

只有40e58d8d5633形成内容，第一次真实生成把content从空变为1。修订后的hypothesis与rule在规范化后**与初版完全相同**，没有内容更新、没有实际规则变化。总状态版本升到5包含证据、功能反馈和关联登记，不能解释成五次学习；实际有两条来源功能反馈。

原始hypothesis主要讨论456的具体LCM/集合算法，并包含未经证实的隐藏正确性预期及对相等集合的犹疑。这些是模型提出的假设，不是可信结论。宿主仅执行受约束rule，hypothesis正文不会自动成为修复提示或获得额外权限。本轮不能从这段文字认定已获得可靠机制知识。

## 7. Operator版本树、来源效果与动作差异

```text
456:l1 可信NO_COMPLETE_CODE
  → 真实生成 slot0：合法规则，Shadow v1
      → 来源验证1：IndexError，公开0/2
  → 诊断修订 slot1：hypothesis和rule均同文
      → 聚合到同一Shadow v1，保留全部费用
      → 来源验证2：length，未交付程序，公开仍无成功
  → 留在Shadow，0授权，0未来执行
```

能力ID：`{key}`。

```json
{json.dumps(rule,ensure_ascii=False,indent=2)}
```

初版响应本身符合两字段契约；修订响应多出白名单`type=json_object`，规范化后通过。两份均合法，但不自动获得Experimental。安全边界检查通过，不替代来源有效要求。

第一次来源输出前半段已经用input消费公开输入，后半段又用sys.stdin.read重新解析，导致公开两例均IndexError；这是实际输出与隔离执行轨迹确认的交付/实现错误，不是对未知测试的推断。第二次响应耗尽8,192输出Token，没有完整源码。两次均LEGAL_BEHAVIOR，无局部改善，无来源收益。

两次验证执行的是同一固定REGENERATE_FRESH动作，最终wire SHA均为`147b458e6c9569c010ca43a04e92395ec8faf449224d7fe3644677babfb1b9e5`。文字修订没有改变规则，也没有改变宿主发送内容；不能把两次不同输出算作两个不同工作流能力。

规则只在源缺程序状态匹配，并与Generic该状态的REGENERATE_FRESH动作相同，标记**NO_DISTINCT_ACTION_VALUE**。同一个action下固定动作和learned rule调用同一action_messages。原生Generic的repair_messages仍可能有不同上下文，等同动作不等于字节相同或因果效果相同。

未来第11–20题没有合法授权版本：真实匹配/试用/回退均0，不能称迁移失败、低触发负迁移或节约调用。后续0313是完整程序WA，也不是这个缺程序条件的自然匹配状态。

## 8. 完整成本

[DeepSeek官方报价](https://api-docs.deepseek.com/quick_start/pricing/)已在执行前复核并冻结：实际响应模型标识deepseek-flash；公布版本V4.1-Flash-1017不当成响应单独证明。全部请求处于UTC周六，缓存命中输入$0.003、未命中$0.15、输出$0.60，每百万Token。预留仍用峰时最高$1.20，不以折扣扩预算。

| 通道 | 响应数 | 输入Token | 输出Token | 总Token | 估算美元 | 剩余请求额度 |
|---|---:|---:|---:|---:|---:|---:|
{channel_table}
| 合计 | 34 | 66,782 | 100,864 | 167,646 | **$0.067543956** | 98 |

生成+来源验证合计17,599 Token、$0.007589454，没有删去同文生成或失败验证。实际调用预算剩余70/14/14，不顺延到新Run。没有在未来执行规则，因此solve通道全部为原生求解，规则试用及回退增量0；无G/M对照，不能声称净节省。

供应商缓存命中输入20,352、未命中46,430；thinking disabled，未提供单独reasoning_tokens细分，不能称实测0。solve有6次length，validation有1次length，learning两次均stop。

账本货币预留$0.704617，不是实付；峰时保守用量估算$0.135087912，实际周末估算如上，供应商账单未取得。34个请求全部COMPLETED，无未知/未决请求，无自动重发。

Worker预算记录107个工具操作、3.908秒计费执行时间；不含全部容器启动和宿主工作，也不等于475.859秒流墙钟。启动前Worker探针单独记录。未将本地时间货币化，不记为零。

历史10题Pilot已报告$0.060589308（其中生成$0.002301168）另列，不从历史抹去；本次冷启动未继承任何旧制品或余额。若合并这两次S19探索的API支出，估算$0.128133264，这不是有配对基线支持的摊销收益。

## 9. 研究判断

1. **真实闭环能否自主运行？** 本轮真实走到失败采集、证据族调度、模型归纳、规范化、Shadow登记、来源验证和一次有界修订。没有来源有效版本，因此没有进入后续试用环节，不能声称完整长期学习已验证。
2. **新增失败是否改变假设和能力？** 跨题新证据改变了调度决定，但请求被输入上限阻断；唯一真正收到诊断的模型修订返回同文假设和规则。本轮未证明新增证据产生能力更新。
3. **新规范化是否有效？** 有真实正例：修订响应的无语义元数据被安全剥离，协议2/2通过。它修复的是接口可靠性，不是来源修复能力。
4. **调度是否改进？** 有真实跨题组获优先且尝试修订，来源多样性限制生效；但排序还未转化为可发送输入和有效生成，不能宣称可靠性/成本收益。
5. **主要限制在哪里？** 直接瓶颈是完整证据包增长与本地输入上限不匹配；其后是唯一可发送规则与Generic动作相同、修订同文且来源无效。不是硬预算不够，也不能笼统否定所有失败学习机制。
6. **是否扩大规模？** 当前不支持原样追加长流。若继续，应另行冻结一个最小的证据表达/输入可发送性复核，先证明跨题证据能够送达模型，并明确规则变化是否改变实际请求。本轮不做这些修改，不追加预算，不启动S20/S21。

本轮完整执行20题才做以上判断，没有在前5/10题缺少成功时提前停止，也不为了产生成功强行授权Shadow。

## 10. 审计交付

审计包`reports/s19_stream20_20261024_01/`含冻结计划/授权、任务与报价、逐题结构化结果、批次调度、假设/规则历史、全部学习请求和响应、来源评估、预算账本与完整性检查。`artifact_index.json`记录整个原始Run文件的SHA与路径，完整solve请求/响应仍在原始`runs/s19_stream20_20261024_01/wire/`。

所有分析脚本均为运行锁定后的只读分析，不用于改变真实任务执行。旧结果不变、当前源码不变、189项冻结文件不变。
'''
(ROOT/'reports/S19真实模型20题连续学习实验报告.md').write_text(report)
print(json.dumps(dict(report='reports/S19真实模型20题连续学习实验报告.md',artifact_files=len(index),batch_summary=[{k:v for k,v in b.items() if k!='decisions'} for b in batch_data]),ensure_ascii=False,indent=2))
