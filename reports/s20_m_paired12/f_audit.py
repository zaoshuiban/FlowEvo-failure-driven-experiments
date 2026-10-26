import pathlib,sys,json,collections
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import restore_budget
from failure_evo.contracts import strict_feedback
from failure_evo.repair_choice_v2 import eligible_actions,generic_choice,observation
P=R/'reports/s20_m_paired12';old=R/'runs/s20_taco80_f_20261025_01';rows=[]
for file in sorted((old/'public_packets').glob('*.json')):
 p=e.read(file);b=restore_budget(p['checkpoint_budget']);f=strict_feedback(p['feedback']);actions=eligible_actions(p['code'],f,b);g=generic_choice(p['code'],f,b);o=observation(p['code'],f,b)
 rows.append(dict(event_id=p['event_id'],task_id=p['task_id'],stage=p['stage'],state=o['candidate_state'],public_result=o['public_result'],remaining_calls=o['remaining_calls'],legal_actions=list(actions),generic_action=g,alternatives=[x for x in actions if x!=g],meaning='legal difference is not measured benefit'))
summary=dict(events=len(rows),tasks=len({x['task_id'] for x in rows}),with_alternative=sum(bool(x['alternatives']) for x in rows),alternative_tasks=len({x['task_id'] for x in rows if x['alternatives']}),signatures=dict(collections.Counter(x['state']+'/'+x['public_result']+'/'+str(x['legal_actions']) for x in rows)),new_model_requests=0)
e.write(P/'f_decision_space.json',dict(summary=summary,events=rows))
(P/'F_零API决策空间审计.md').write_text(f'''# F零API决策空间审计

当前S20-A公开证据：{summary['events']}事件、{summary['tasks']}个原题；其中{summary['with_alternative']}事件、{summary['alternative_tasks']}个原题在原权限下存在不同于Generic的合法动作。详表见f_decision_space.json。存在合法替代不等于替代有收益。

S17-B已有3题真实A/B开发对照：重新生成B全部通过复核，修复A仅1题全通过。这支持Generic固定修复并非总合适，但固定B已覆盖全部赢家，尚不足以证明需要学习条件选择。A/B请求还同时改变源码及错误反馈，不是纯粹删除源码的单因素因果试验。

S17-B2筛查20条仅1条合格，没有真实A/B调用，不能引用为动作效果接近。S18-P2的425/463四分支均未同时通过公开与外部复核：425的B公开通过但最终11/12；463两动作均失败。因此未补充可靠的相反偏好。

当前字段仅candidate_state、public_result、remaining_calls阈值。相同字段下算法错误根因可能不同；没有证据说明这些字段能预先区分最优动作。完整代码、公开用例可能蕴含信息，但现有规则不能表达其语义判断。不能将事后赢家或封存失败作为在线可见特征。

近期2个真实规则（空程序重生成、完整程序运行错误修复）7次匹配均与Generic相同。它们重述底座能力，没有获得独立动作收益。也不能因已有19份契约失败就断言其他动作必然有效。

结论：NO_GO_CURRENT_CONDITIONAL_SELECTOR / LEGAL_HEADROOM_NOT_YET_IDENTIFIABLE。不再追加F生成。保留既有A/B证据作为未来机制开发材料；若重新设计，应先提出当时公开可见、可证伪的状态区分假设，并将固定A、固定B列为共同基线。此轮不新增动作或特征、不恢复权限、不改路由、不声称失败驱动学习总体无效。
''')
print(summary)
