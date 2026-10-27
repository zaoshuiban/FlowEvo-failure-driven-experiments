"""Post-lock descriptive report; no model calls or changes to frozen execution."""
import collections,datetime,json,pathlib,sys
import s22_executor as e
r=pathlib.Path(sys.argv[1]).resolve();s=e.read(r/'state.json');f=e.read(r/'final_review.json')
assert s['status']=='ONLINE_LOCKED'
manual=e.read(r/'manual_action_review_before_scoring.json');keys=e.read(r/'review_key.json')
summary={};rows=[]
for arm in 'AB':
 br=[v for v in s['branches'].values() if v['arm']==arm];usage=[v['response']['usage'] for v in br]
 summary[arm]=dict(calls=len(br),public_success=sum(v['public_pass'] for v in br),strict_success=sum(s['branches'][f'{i:02}-{arm}']['public_pass'] and e.read(r/f'{i:02}-{arm}.sealed.json')['result']['passed'] for i in range(1,11)),input_tokens=sum(u['prompt_tokens'] for u in usage),output_tokens=sum(u['completion_tokens'] for u in usage),tokens=sum(u['total_tokens'] for u in usage),peak_no_cache_estimated_usd=sum(v['estimated_usd'] for v in br),peak_cache_aware_estimated_usd=sum((u['prompt_cache_hit_tokens']*.006+u['prompt_cache_miss_tokens']*.3+u['completion_tokens']*1.2)/1e6 for u in usage),length_stops=sum(v['response']['finish_reason']=='length' for v in br),request_seconds=sum(v['request_seconds'] for v in br))
for i,p in enumerate(f['pairs'],1):
 row=dict(index=i,task_id=p['task_id'],public=p['public'],strict=p['strict'],arms={},source_review=manual['notes'][i-1]['note'],review_labels={x['label']:x['arm'] for x in keys if x['index']==i})
 source=e.read(e.BASE/f'frozen/{i:02}.json')['public_checkpoint']
 for arm in 'AB':
  k=f'{i:02}-{arm}';b=s['branches'][k];q=e.read(r/f'{k}.sealed.json')['result'];artifact=e.read(r/f'{k}.artifact.json')
  row['arms'][arm]=dict(public_passed=b['public_result']['tests_passed'],public_total=len(source['public_cases']),sealed_passed=q['tests_passed'],sealed_total=24 if i==7 else 12,sealed_executed=q['tests_run'],sealed_status=q['status'],tokens=b['response']['usage']['total_tokens'],finish_reason=b['response']['finish_reason'],syntax_ok=artifact['syntax_ok'],artifact_sha256=artifact['artifact_sha256'],estimated_usd=b['estimated_usd'],source_character_similarity=b['action_audit']['character_similarity'],source_ast_similarity=b['action_audit']['ast_node_type_similarity'])
  (r/f'{k}.py').write_text(artifact['code'])
  (r/f'{k}.diff').write_text(b['action_audit']['diff'])
 rows.append(row)
ledger=[json.loads(x) for x in (r/'budget.jsonl').read_text().splitlines()]
req=[x['payload']['request_id'] for x in ledger if x['kind']=='RESERVED' and x['payload']['kind']=='model']
audit=dict(request_ids=len(req),unique_request_ids=len(set(req)),unknown=f['budget']['unknown_or_pending_requests'],wire_hashes_all_match=all(e.sha(r/f'{i:02}-{a}.wire.json') is not None and e.fingerprint(e.read(r/f'{i:02}-{a}.wire.json'))==e.read(e.BASE/f'frozen/{i:02}.json')['request_freeze']['arms'][a]['wire_sha256'] for i in range(1,11) for a in 'AB'),original_freeze_unchanged=bool(e.verify()),hard_budget_microusd=1000000,charged_or_reserved_microusd=f['budget']['charged_or_reserved_cost_microusd'])
e.save(r/'summary.json',dict(status='COMPLETE',arms=summary,pairs=rows,classes=dict(collections.Counter(x['strict'] for x in rows)),integrity=audit,budget=f['budget'],preflight_budget=e.read(r/'worker_preflight.json')['budget'],actual_invoice=None))
lines=['# S22-RQ1真实10题A/B实验报告','',f'Run：`{r.name}`。按本轮明确授权完成20次请求，未追加调用、改题、改Prompt或改预算。在线状态ONLINE_LOCKED，之后完成独立封存复核。','', '结论：`RQ1_COMPLETE / CONDITIONAL_LEARNING_NOT_JUSTIFIED`。观察到一次B独有成功，但没有A独有成功；没有建立双向动作偏好、可预测边界或历史学习必要性。','', '| 指标 | A：修复提示 | B：重生成提示 |','|---|---:|---:|']
for label,key in [('公开全部通过','public_success'),('公开与封存均通过','strict_success'),('模型响应','calls'),('输入Token','input_tokens'),('输出Token','output_tokens'),('总Token','tokens'),('length截断','length_stops')]:lines.append(f"| {label} | {summary['A'][key]} | {summary['B'][key]} |")
for label,key in [('峰值未命中口径费用估算','peak_no_cache_estimated_usd'),('峰值缓存感知费用估算','peak_cache_aware_estimated_usd')]:lines.append(f"| {label} | ${summary['A'][key]:.7f} | ${summary['B'][key]:.7f} |")
lines+=['','A-only=0，B-only=1，Both-success=1，Both-fail=8，UNKNOWN=0。公开与严格分类一致。唯一不一致配对的双侧精确McNemar p=1.0，仅作描述，不构成稳定优势。','', '|顺序/任务|A公开|A封存|B公开|B封存|严格分类|','|---|---:|---:|---:|---:|---|']
for x in rows:
 a,b=x['arms']['A'],x['arms']['B'];lines.append(f"|{x['index']} {x['task_id']}|{a['public_passed']}/{a['public_total']}|{a['sealed_passed']}/{a['sealed_total']}|{b['public_passed']}/{b['public_total']}|{b['sealed_passed']}/{b['sealed_total']}|{x['strict']}|")
lines+=['','第4题B在结构检查被拒绝，封存0/12代表制品失败，实际运行0个封存输入，并非12次程序执行。第3题A/B均封存12/12但公开14/15，因此严格判为共同失败，不能用封存PASS替代公开修复。','', '## 动作实际遵循与来源局限','', '在读取评分之前，先生成隐去组别及分数的源码视图，进行助手静态审查并保存时间和哈希；不是独立人工双盲审查。语法通过、AST相似度、代码变短均不直接证明算法完整或策略转换。较长无效代码的显示存在截取，结论限于可确认结构。','']
for x in rows:lines.append(f"- 第{x['index']}题（映射{x['review_labels']}）：{x['source_review']}")
lines+=['','最关键的B独有成功为r0298：旧来源只有一行递推式。A达到8192输出上限，未交付有正常入口及输出的程序；B交付完整程序，公开15/15、封存12/12。这是交付和提示处理的单次差异，不能称为对完整失败算法的优越重建。','', 'r0236、r0712、0313、909等任务的两个分支仍沿用相同核心框架；r0712去注释AST相同。B被允许查看旧代码并重新设计，并不被强制采用不同算法。保留按分配提示的主分析，不事后删除不遵循预期的分支。','', '## 成本、完整性和停止审计','',f"20个唯一模型请求，20份响应；UNKNOWN为0；逐分支wire与冻结文件一致。峰值未命中估算合计${sum(v['peak_no_cache_estimated_usd'] for v in summary.values()):.7f}，峰值缓存感知估算合计${sum(v['peak_cache_aware_estimated_usd'] for v in summary.values()):.7f}。账本保守占用${f['budget']['charged_or_reserved_cost_microusd']/1e6:.6f}，低于$1硬上限，不是账单。缓存感知估算仍统一使用峰值，不主张等于实际时段扣费。",'', f"正式Run（在线+封存）工具{f['budget']['tool_calls']}次，工具计时{f['budget']['charged_or_reserved_tool_milliseconds']/1000:.3f}秒；另有预检{e.read(r/'worker_preflight.json')['budget']['tool_calls']}工具单元。工具时间不等于完整容器墙钟/CPU成本，未货币化；各分支请求耗时保存在state和summary中。reasoning用量未返回时保持NOT_REPORTED。",'', '报价依据：[DeepSeek官方价格页](https://api-docs.deepseek.com/quick_start/pricing)，本轮下载快照及哈希见pricing_recheck.json。model按冻结deepseek-flash发送，官方当前映射Flash-1017；返回model字段一致不构成后端权重身份的独立证明。温度0按冻结值发送，但单次调用不保证确定性。','', '## 研究边界与下一步','', '10题是已曝光开发材料，没有读取119道确认题、没有启动419题长流，没有生成或恢复Operator。来源包含代码片段、未完成程序和编译错误，不能整体描述为10份完整算法；遵守预先筛选，不因事后结果更换样本。','', '本次没有支持继续生成条件选择规则所需的双向可信偏好。B在共同成功的r1248成本也较低，但只是一道来源补全案例。A在若干共同失败题上公开通过用例较多，属于局部改善，不是可靠效率成功。无需根据此批结果扩大规则生成或宣称固定B总体更好。RQ2仅允许描述，RQ3未启动。','', '逐题源码、diff、原始响应、请求wire、公开反馈、离线封存评分均保存在本Run。summary.json提供可复算统计；manual_action_review_before_scoring.json保留评分前审查。历史Run、冻结协议和执行器源码均未修改。']
(r/'S22_真实10题AB实验报告.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(arms=summary,integrity=audit),indent=2))
