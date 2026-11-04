"""Synthetic-specific report, preserving the actual information contrast."""
import json,collections
import report_math_auto100 as generic
from run_math_synthetic100 import OUT

def main():
 generic.OUT=OUT;generic.main()
 summary=json.loads((OUT/'summary.json').read_text());roles=json.loads((OUT/'roles.json').read_text());labels={x['task_id']:x for x in json.loads((OUT/'private.json').read_text())};rows=json.loads((OUT/'results.json').read_text());byfamily={}
 for arm in ['Discovery','G','T','F']:
  byfamily[arm]={}
  for family in ['expression','digits','walk']:
   selected=[r for r in rows if r['arm']==arm and labels[r['task_id']]['family']==family]
   byfamily[arm][family]=dict(completed=len(selected),correct=sum(r['grade']['correct'] is True for r in selected),statuses=dict(collections.Counter(r['grade']['status'] for r in selected)),applied=sum(r['locked']['selection']=='first_applied_operator' for r in selected))
 summary['family_results']=byfamily;
 summary['learning_funnel']={'frozen_instances':100,'confirmed_failure_instances':summary['confirmed_final_failure_tasks'],'selected_failure_instances':len(json.loads((OUT/'selected_bundle.json').read_text())['events']),'actual_hypotheses':sum(len(x['hypotheses']) for x in summary['mechanisms'].values()),'generated_code_versions':sum(len(x['reviews']) for x in summary['mechanisms'].values()),'actual_operator_applications':summary['outcomes']['T']['operator_applied']+summary['outcomes']['F']['operator_applied']}
 summary['scope']='manual synthetic3families; parameter generalization only, NOT new original MATH problems';summary['baseline_information_caveat']='Existing discovery_view exposes selection metadata mentioning failures to both arms. T lacks wrong answers/trajectories but is not fully blind to source failure membership. F/T estimates trajectory/binary-detail increment conditional on that metadata, not strict all-failure-information vs none.'
 (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 s=summary;table='\n'.join(f"|{arm}|{v['correct']}/{v['completed']}|{v['model_calls']}|{v['input_tokens']+v['output_tokens']}|{v['operator_applied']}|${v['peak_cost']:.6f}|" for arm,v in s['outcomes'].items())
 text=f'''# 人工设计数据上的真实失败驱动自动学习实验

状态：**{s['status']}**。研究状态：**{s['research_status']}**。

## 设计与证据边界

人工编写任务分布和私有参考评分器，不人工编写待学习算子、不伪造失败。100个冻结参数实例：20发现、10开发、10Gate、60最终配对；三类为有序表达式括号化结果计数、受约束数字素数计数、随机游走首次到达概率。这是受控合成机制实验，**不是100道独立原题，不是MATH独立泛化**。人为限定了机制空间，不能声称开放世界机制发现。

固定随机种子73120261031。公开输入仅题面与参数，不含内部类别标签、Oracle代码或答案。所有100题两种宿主参考计算一致，另对首次到达的30个小问题用全部路径穷举核对。参考可信度来自明确题目定义与独立实现的有限交叉验证，不来自模型或候选算子自报。

协议SHA：`{json.loads((OUT/'freeze.json').read_text())['sha256']}`。复用已有无Gold Controller、BoundedCompiler、数学算子Worker和MathLearningPipeline；没有导入手工求和算子或历史源码。

## 对照及实际信息可见性

G为原生两次无反馈求解；T使用相同选中来源题；F额外看到真实错误输出、轨迹和失败状态。生成模型均DeepSeek Flash，各最多1次归纳+1次源码生成，无修订。真正的错误只在答案锁定后判定，截断/UNVERIFIED不作为数学错误。

**需保留的实现限制：** 复用的`discovery_view`给两组的selection元数据都包含“earliest distinct Discovery failures”。所以T没有错误答案及轨迹，却能知道来源属于失败池；它不是对失败成员身份完全盲的严格Task-Only。不得把F/T结果包装为“全部失败信息对零失败信息”的纯净因果效应。当前更准确的对比是：共享来源失败筛选说明，额外提供错误轨迹及详细二值事件是否有增量。本轮未在运行中修改冻结接口来掩盖这一限制。

相同接口、静态限制、Worker与准入规则。源/Design至少一个正确应用、无错误应用/ERROR且拒绝控制通过，才能一次Gate；Gate不能回流修订。最终测试前冻结学习和注册表。

## 归纳内容与证据边界

T从题面提出“有限候选生成、去重、判定/求值”的共同结构，但认为两个问题族不一定共享机制。F从错误轨迹提出“尚未完成穷举/动态规划便提前给出计数”的原因假设。二者返回的decision仍须按原值执行；不能把可执行建议文字直接当成已生成源码。

长输出输入视图按既有协议截取前2400字符，并标记is_fragment及完整SHA；原文保留。F据此作出的根因判断不自动可信，尤其不能从片段缺失推断完整轨迹中从未执行某步。

## 结果

可信最终失败来源：{s['confirmed_final_failure_tasks']}题。

|组别|正确/完成|模型请求|输入+输出Tokens|算子应用|峰价API估算|
|---|---:|---:|---:|---:|---:|
{table}

生成与准入状态：`{[(x['arm'],x['status']) for x in s['learning']]}`。

逐类结果、原始机制假设、静态验收、来源/开发效果见`summary.json`；所有候选源码与模型原始响应保留在T/F目录。正常拒绝、生成失败和无后续机会均不补写为成功。

配对：
```json
{json.dumps(s['pairwise'],ensure_ascii=False,indent=2)}
```

精确McNemar仅为这一有限参数样本的描述；同一模型每组只生成一个候选，且只有3个机制族，不能将60题视为60个独立机制学习重复。F/G即使改善，也可能来自程序工具能力；F/T及生成成本才涉及失败轨迹增量。

## 成本与完整性

全部真实响应{s['total_calls']}次，{s['total_tokens']}tokens。含发现、两组归纳/代码生成、来源/开发/准入验证和后续三组求解的模型费用；执行工具耗时另记。峰价估算${s['estimated_peak_cost']:.9f}，非峰价${s['estimated_offpeak_cost']:.9f}，非账单。20美元硬上限，UNKNOWN={s['unknown']}，无自动重发。生成失败也计入成本。人工数据与Oracle设计、本地计算成本未货币化。

100为冻结角色总数，实际求解不同任务{s['actually_solved_unique_tasks']}；没有被触发的开发/Gate不记为通过。最终统计不利用测试错误更新源码或追加候选。

## 判断原则

如果F没有准入或介入，不能从F/G分数波动推断学习收益；若T/F都获得相近收益，只能说明题面生成程序也有效；只有额外错误轨迹带来可复核的独立改善，才出现有限增量信号。即使出现正结果，仍受上述源失败元数据、单候选及人工分布限制，不能据此宣称广义失败驱动学习已被证明。
'''
 (OUT/'Final_Report.md').write_text(text)
if __name__=='__main__':main()
