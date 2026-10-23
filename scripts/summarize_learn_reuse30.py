"""Add evidence-specific conclusions to S15 report without changing frozen results."""
import json
from collections import Counter
from pathlib import Path
import learn_reuse30 as s

def main():
 s.report();r=s.RUN;m=s.read(r/'metrics.json');ls=s.read(r/'learning_state.json');quality=[];native_blocks=[]
 for f in sorted((r/'operators').glob('*/*/functional.json')):
  x=s.read(f);result=x.get('source_result');quality.append(dict(family=f.parent.parent.name,version=f.parent.name,static=s.read(f.parent/'static.json')['passed'],source_called=bool(result),source_tests_passed=result['tests_passed'] if result else 0,source_tests_run=result['tests_run'] if result else 0,controls_passed=sum(c['passed'] for c in x['checks'][1:]),controls_count=len(x['checks'])-1,passed=x['passed']))
 for f in sorted((r/'branches').glob('*/*/workflow.json')):
  w=s.read(f)
  for e in w['events']:
   if e.get('error'):native_blocks.append(dict(task_id=f.parent.parent.name,arm=f.parent.name,stage=e['stage'],error=e['error']))
 rejected=[x for x in ls['log'] if x['kind'] in ('WARM_BLOCKED','UPDATE_BLOCKED','TEXT_MEMORY_REJECTED')]
 missing=[dict(family=x['family'],version=x['version'],reason='prepared but not sent; see block record') for x in ls['log'] if x['kind'] in ('CANDIDATE','REVISION') and not x.get('result')]
 synopsis=dict(artifacts=quality,host_blocks=native_blocks,learning_blocks=rejected,unsent_preparations=missing,source_task_count=len({x['source_task'] for x in ls['log'] if x['kind']=='CANDIDATE'}),f_new_failure_facts=m['failure_facts']['F'],new_trials=sum(x['operator_calls'] for x in s.read(r/'results.json')['rows']))
 s.write(r/'learning_outcome_breakdown.json',synopsis)
 text=['','## 本轮实际结论与阻断分解','', '|机制/版本|静态合格|来源公开通过|拒绝控制通过|准入|','|---|---|---:|---:|---|']
 for x in quality:text.append(f"|{x['family']}/{x['version']}|{x['static']}|{x['source_tests_passed']}/{x['source_tests_run']}|{x['controls_passed']}/{x['controls_count']}|{x['passed']}|")
 text+=['',f"实际生成并执行策略源码 {len(quality)} 份；来源验证成功 {sum(x['passed'] for x in quality)} 份。在线F新失败事实 {m['failure_facts']['F']} 条，实际算子试用 {synopsis['new_trials']} 次。没有源码准入时，F仍走共同底座，不能把其分数或Token差异解释为算子复用收益。",'', '模型失败、真实功能失败和本地阻断分别保留：', '', '```json',json.dumps(dict(learning_blocks=rejected,unsent_preparations=missing,native_host_errors=native_blocks),ensure_ascii=False,indent=2),'```','', '本地输入上界使用最终请求序列化字节数加保守余量作为Token上界，不是供应商实际Tokenizer计数，也不是供应商上下文窗口。触发该上界只能说明本轮请求组织/预算预检阻断；不能解释为模型已修订失败或题目不可解。M的文字更新若违反冻结长度契约，会保留旧版本；该次请求和费用仍计入学习。','']
 if not synopsis['new_trials']:
  text+=['本轮结论：**真实学习尝试已经发生，但未形成学习—准入—未来复用的完整成功实例，不能宣称闭环有效。** 与S13“生成预算为0”不同，本轮确实调用了规格归纳、候选生成、诊断修订和来源执行验证。没有进入新生代的直接原因应按上表归因，不能归为“要求跨题收益太高”。','', '若F没有新的可信失败，批间不生成是触发条件未满足，不能伪造失败或消费预算凑算子。下一次应先零API压缩重复诊断上下文、校准真实请求尺寸，并明确来源选择规则；本轮不更换来源反复补跑，也不追加预算强求成功。','']
 else:
  text+=['出现实际试用仅证明工作流经历了学习、准入和调用；须结合每次宿主公开验证、独立复核及完整成本判断价值。模型随机性和三组不同历史仍限制总体效果归因。','']
 text+=['本轮所有组均采用一次随机生成轨迹，没有统计显著性或长期净收益主张。来源公开验证及本轮最终复核也不等同于完整隐藏正确性。','']
 with (r/'30题真正学习—复用试运行报告.md').open('a') as out:out.write('\n'.join(text))
 print(json.dumps({k:v for k,v in synopsis.items() if k not in ('artifacts','host_blocks')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
