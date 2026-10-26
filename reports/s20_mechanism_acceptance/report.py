import pathlib,sys,json,datetime,hashlib
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from failure_evo.repair_choice_memory import RuleMemory
P=R/'runs/s20_mechanism_acceptance_20261025_01';d=e.read(P/'result.json');m=e.read(P/'memory_use.json');plan=e.read(P/'plan.json');registry=RuleMemory(P/'rule_registry.jsonl','repair-choice-json-v2')
for f in d['F']:
 if 'rule' not in f:continue
 key=registry.add(f['rule'],[x['event_id'] for x in f['observations']],metadata=dict(source_run='s20_taco80_f_20261025_01',real_generation_path=str((P/'F'/f['job_id']/'0.json').relative_to(R)),no_distinct_action=True,source_validation_not_run=True))
 assert registry.state(key)['permission']=='shadow'
 f['registered_shadow_id']=key
costs=[]
for ch in ('learning','solve','validation'):
 for file in sorted(P.glob('wire/'+ch+'/*/response.json')):
  r=e.read(file);u=r['usage'];hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit);peak=(hit*.006+miss*.3+u['completion_tokens']*1.2)/1e6;date=datetime.datetime.fromtimestamp(r['created'],datetime.timezone.utc);value=peak if date.weekday()<5 and (1<=date.hour<4 or 6<=date.hour<10) else peak/2
  costs.append(dict(channel=ch,tokens=u['total_tokens'],estimated_usd=value,peak_upper_usd=peak,file=str(file.relative_to(R))))
state=e.read(P/'state.json');used=[i for row in (P/'stream.jsonl').read_text().splitlines() for r in [json.loads(row)] if r['kind']=='MEMORY_DELTA_COMMITTED' for i in r['payload']['included_ids']]
summary=dict(status='M_LOOP_PASS_F_NO_DISTINCT_ACTION_VALUE',M_real_updates=2,M_unique_events=len(set(used)),tail_events_committed=set(plan['tail_memory_ids'])<=set(used),M_injected=m['memory_in_actual_wire'],M_public_result={k:m['evaluation'][k] for k in ['status','tests_passed','tests_run']},F_format_pass=2,F_candidates=2,F_distinct_rules=len({e.fingerprint(f['rule']) for f in d['F']}),F_changed_generic=0,F_experimental=0,stage3_started=False,requests=len(costs),tokens=sum(x['tokens'] for x in costs),estimated_usd=sum(x['estimated_usd'] for x in costs),peak_upper_usd=sum(x['peak_upper_usd'] for x in costs),hard_cap_usd=.9,costs=costs,budgets=state['budgets'])
e.write(P/'acceptance_summary.json',summary);e.write(P/'shadow_registration.json',d['F'])
text=f'''# S20 小规模真实机制验收

结论：M_LOOP_PASS / F_NO_DISTINCT_ACTION_VALUE。20–30题与419题均未启动，119道确认题未读取。

## 第一关：真实M闭环
两次真实模型更新均成功：第一批9条历史事件，第二批加入原离线回放遗漏的4条，共13条事件真实处理。不能把离线57条覆盖说成57条真实学习。4条被省略的原因是16KB视图预算，在事前确定的任务轮转次序中未能进入末批；不被标记已消费，下一次增量已全部进入并成功提交。

记忆及消费标记持久化；实际重新构造runner并重放boundary，学习调用不增加。另有两个故障注入测试覆盖“响应落盘后”及“记忆保存后、事件标记前”中断，不重发。使用独立版本MechanismStream修复这一事务窗口，没有改旧Run。

原生M首轮l1不注入失败记忆，修复阶段才注入。本轮首次使用联调错误地在prepare上追加提示，SharedTransport重新核验时检测到wire不同，调用尚未预留、发送。该失败记录保留。恢复诊断将公共交付要求放在构造messages阶段，不再修改prepare；事前按task/stage/event顺序选取未参与这13条记忆输入的历史公开修复检查点。不是新的未见任务。

实际M修复任务{s['packet']['task_id'] if False else m['packet']['task_id']}：保存的最终请求明确包含真实生成记忆，公开14/14通过，1次请求、1722 Token。仅证明记忆被注入和该次修复成功，没有无记忆配对，不能证明模型因记忆改善。已保存两次记忆全文、哈希、输入视图和完整wire。

## 第二关：F真实生成
按旧学习请求顺序事前冻结最早两个初始作业，未按旧效果换样本。2次初始生成均通过严格契约，0次修订，2条不同规则；小样本不能证明长期稳定合规。

1. NO_COMPLETE_CODE → REGENERATE_FRESH，4个匹配事件上的选择均与Generic相同。
2. STRUCTURAL_PASS / RUNTIME_ERROR → REPAIR_EXISTING，3个匹配事件上的选择均与Generic相同。

共7条匹配记录，无一次动作不同。两个候选实际登记Shadow，无来源验证，无Experimental授权，无未来使用。当前阶段不为等价动作重复花钱修来源。动作等价不代表所有原生请求字节相同；未运行的请求级配对不虚构结果。规则没有形成新的独立决策能力证据。

## 成本和停止
实际{summary['requests']}次模型响应、{summary['tokens']} Token。按响应时段与冻结价格估算${summary['estimated_usd']:.7f}，峰值价格上界${summary['peak_upper_usd']:.7f}，都不是账单。硬预算$0.90；各通道完整预算与工具记录见acceptance_summary.json。没有未知请求或自动重发。工具费用未货币化，不能称免费。

第一关通过的是工程与实际使用闭环；第二关格式通过但独立价值门槛未通过，因此不进入第三关，不启动配对20–30题或外部419题，也不追加生成直到成功。结果支持修复有效，但不支持失败学习具有增量性能收益。先前S20-A数据、评分和账本保持不变。
'''
(P/'S20_真实机制验收报告.md').write_text(text)
e.write(P/'artifact_hashes.json',{str(f.relative_to(R)):e.sha(f) for f in [P/'plan.json',P/'acceptance_summary.json',P/'result.json',P/'memory_use.json',R/'scripts/s20_mechanism_stream.py',R/'scripts/test_s20_mechanism_stream.py',pathlib.Path(__file__)]})
print(json.dumps({k:v for k,v in summary.items() if k not in ['budgets','costs']},ensure_ascii=False))
