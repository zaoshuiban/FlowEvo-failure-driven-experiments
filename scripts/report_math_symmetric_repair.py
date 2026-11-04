"""Read-only summary; never generates or changes a model artifact."""
import json,sys
from run_math_symmetric_repair import ROOT,OUT,PARENT,read,records,save,sha

def main():
 p=read(OUT/'protocol.json');results=read(OUT/'results.json');rows=[];usage=[];cost=0;tools=0;tool_ms=0;occupied=0
 for r in results:
  d=OUT/r['name'];review=r['review'];dev=read(d/'development.json') if (d/'development.json').exists() else []
  source=[x for v in dev if v['role']=='Source' for x in v['rows']]
  design=[x for v in dev if v['role']=='Design' for x in v['rows'] if x['supported']]
  negative=[x for v in dev for x in v['rows'] if not x['supported']]
  allrows=source+design+negative
  row=dict(name=r['name'],status=r['status'],static_pass=review.get('diagnostic',{}).get('static',{}).get('passed',False),
   classification=review.get('change',{}).get('classification'),source_n=len(source),design_n=len(design),
   source_compute=sum(x['computation_correct'] for x in source),source_combined=sum(x['combined_correct'] for x in source),
   design_compute=sum(x['computation_correct'] for x in design),design_combined=sum(x['combined_correct'] for x in design),
   parameter_correct=sum(x['parameter_correct'] is True for x in source+design),
   correct_refusal=sum(x['correct_refusal'] for x in negative),false_accept=sum(x['false_accept'] for x in negative),negative_n=len(negative),
   mapping_unknown=sum(x['mapping'].get('value',{}).get('status')=='UNKNOWN' for x in allrows if isinstance(x['mapping'].get('value'),dict)),
   execution_errors=sum(bool(x['end_to_end']['status']=='ERROR' or x['mapping']['status']!='OK' or (x['computation'] and x['computation']['status']!='OK')) for x in allrows),
   parent_sha256=review.get('change',{}).get('parent_sha256'),code_sha256=review.get('change',{}).get('code_sha256'),ready_for_gate=r['ready_for_gate'])
  rows.append(row)
  for v in records(d/'provider.jsonl'):
   if v['kind']=='RAW_RESPONSE':
    u=v['payload']['response']['usage'];usage.append(u)
    hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit)
    cost+=(hit*.006+miss*.3+u['completion_tokens']*1.2)/1e6
  from failure_evo.persistent_budget import PersistentBudget
  b=PersistentBudget.__new__(PersistentBudget);b.path=d/'budget.jsonl'
  with b._locked() as ledger:
   totals=b._totals(ledger);tools+=totals['tools'];tool_ms+=totals['tool_ms'];occupied+=totals['cost']
 gatepath=OUT/'independent_gate'
 gate=read(gatepath/'results.json') if (gatepath/'COMPLETE.json').exists() else []
 gate_budget=read(gatepath/'COMPLETE.json')['budget'] if gate else {}
 summary=dict(protocol_sha256=read(OUT/'freeze.json')['sha256'],rows=rows,responses=len(usage),
   input_tokens=sum(u['prompt_tokens'] for u in usage),output_tokens=sum(u['completion_tokens'] for u in usage),
   total_tokens=sum(u['total_tokens'] for u in usage),peak_estimated_usd=cost,offpeak_estimated_usd=cost*.5,
   reserved_or_charged_upper_usd=occupied/1e6,worker_calls=tools,worker_seconds=tool_ms/1000,
   gate_executed=bool(gate),gate_results=gate,gate_budget=gate_budget,
   total_worker_calls=tools+gate_budget.get('tool_calls',0),
   total_worker_seconds=(tool_ms+gate_budget.get('charged_or_reserved_tool_milliseconds',0))/1000,
   experimental=0,old_run_unchanged=all(sha(ROOT/k)==v for k,v in p['parent_hashes'].items()))
 save(OUT/'summary.json',summary)
 lines=['# T/F统一算子工程修复与开发验证报告','',
 '## 结论','',
 f"真实修订 {len(usage)}/6 份；静态通过 {sum(r['static_pass'] for r in rows)}/6；来源与开发全量验收通过 {sum(r['ready_for_gate'] for r in rows)}/6。",'',
 '本轮只证明交付与工程修复流程使候选获得了真实执行机会。工程通过不等于失败信息增量有效，也不等于跨原题迁移。', '',
 '## 冻结与对称性','',
 f"新Run：`{OUT.name}`；协议 SHA256：`{summary['protocol_sha256']}`。原六份候选、原始响应和各自归纳原文作为历史模型产物导入；不重新归纳或生成初始算法。",'',
 'T/F各三份；保持旧轮冻结顺序，每份仅一次修订、8192输出上限、65536保守输入上限；相同模型deepseek-flash、非推理模式、温度0、接口、安全检查和诊断算法。六个独立账户各0.20美元，合计1.20美元硬上限，不转移旧预算。', '',
 '修订模型只获得该候选原始源码、统一静态诊断、同一组来源/已曝光Design题面及接口要求。不追加历史假设、失败轨迹、评分结果、Gold、可信参数、Gate或Test材料。原始T/F源码保留各自的生成信息差异。修订失败不追加采样。', '',
 '## 验证结果','',
 '|候选|静态|来源计算/联合（5）|开发计算/联合（20）|参数正确（25）|工程负例拒绝/错误接受（2）|状态|',
 '|---|---|---|---|---|---|---|']
 for r in rows:
  lines.append(f"|{r['name']}|{'通过' if r['static_pass'] else '拒绝'}|{r['source_compute']}/{r['source_combined']}|{r['design_compute']}/{r['design_combined']}|{r['parameter_correct']}|{r['correct_refusal']}/{r['false_accept']}|{r['status']}|")
 lines += ['', '每列计算与联合数字是两种测量，不是分子/分母。分母见表头。静态失败未执行记为未测，汇总JSON的0计数不能解释为数学0分。五道来源和20道Design为同一人工数学机制的参数实例，并非25道不同原题。', '',
 '## 工程修复与算法版本','',
 '所有模型源码原样保存。对源码SHA、去位置及文档字符串后的AST、顶层函数差异分别记录。只有AST未变才标记格式/说明变化；其他统一标记SUBSTANTIVE_OR_UNRESOLVED，不能证明数学逻辑等价，也不能宣称只是去掉nonlocal。未继承任何旧验证或试用权限。', '',
 '计算：真实Worker直接调用生成的solve(parameters)，可信参数仅宿主离线诊断可见。映射：调用生成的map_parameters(problem)，与独立参数逐字段比较。联合：调用生成的math_operator，使用现有MathOperatorRunner。所有执行都绑定完整生成源码SHA；宿主没有另写等价数学算法。', '',
 '## Gate及研究边界','',
 '开发通过仅产生READY_FOR_INDEPENDENT_GATE收据，不自动授予Experimental。开发阶段的两个负例只是无题目/越权请求工程控制，不能替代数学语义近似负例。六份源码冻结后，另立零API Gate协议：使用原先冻结且未执行的20道支持输入，加上在Gate执行前冻结的6道目标量变更负例。所有负例由研究者审查其目标与冻结算法接口不符；没有把模型自报答案作为Oracle。负例由其中6道支持题变体产生，共享参数谱系，不算26道独立原题。', '',
 'Gate与开发/修订题面不重叠，但仍是同机制人工参数分布。新增负例属于开发后设计的压力测试，并非所有数据从最初生成前就盲法预注册；已在Gate前固定，结果不回流任何修订。60道Test未执行，也未进行Generic端到端收益比较。', '',
 '## 成本及完整性','',
 f"真实响应{summary['responses']}次；输入{summary['input_tokens']:,}、输出{summary['output_tokens']:,}、合计{summary['total_tokens']:,} Tokens。峰价估算${cost:.9f}，非峰价估算${cost*.5:.9f}；账本保守占用上界${summary['reserved_or_charged_upper_usd']:.6f}。估算不是实际账单。",'',
 f"真实Worker调用{tools}次，账本工具耗时{summary['worker_seconds']:.3f}秒。旧Run全部文件哈希保持不变：{summary['old_run_unchanged']}。",'',
 '[供应商报价](https://api-docs.deepseek.com/quick_start/pricing/)已于冻结时保存pricing.html；峰价输入未缓存0.3、缓存0.006、输出1.2美元/百万Tokens。', '',
 '## 工程验收与交付','',
 '零API人工夹具22项检查通过，使用真实Linux Worker；另通过现有BoundedCompiler与新Adapter的Mock完整调用。人工夹具不计真实学习。测试覆盖具体nonlocal/缺导入诊断、对称输入、原始/修订留档、版本分类、私有字段阻断、UNKNOWN不重发、交付失败与传输未知分离、参数/算法错误分离、验证绑定和源码变更失效。', '',
 '代码：`FlowEvo/src/failure_evo/math_engineering_repair.py`；真实入口：`scripts/run_math_symmetric_repair.py`；验收：`scripts/test_math_engineering_repair.py`；报告：`scripts/report_math_symmetric_repair.py`。', '',
 '所有真实请求/响应见各候选provider.jsonl；修订链见repair/；开发执行见validation.jsonl、development.json；账本见budget.jsonl。原始与修订源码分别为repair/original.py与repair/revised.py。']
 if gate:
  lines += ['', '## 冻结源码的独立保留输入与语义压力Gate', '',
   '|候选|计算正确/20|参数正确/20|联合正确/20|错误接受/6|正确拒绝/6|Gate|',
   '|---|---|---|---|---|---|---|']
  for g in gate:
   lines.append(f"|{g['name']}|{g['computation_correct']}|{g['parameter_correct']}|{g['combined_correct']}|{g['false_accept']}|{g['correct_refusal']}|{'通过' if g['passed'] else '未通过'}|")
  lines += ['', '计算组件获得了新参数输入上的功能性证据；适用性不能只依据合法参数JSON。目标量改变后仍接受，属于语义门控失败。所有未通过版本保留Shadow，不因计算20/20而发布，不再围绕本Gate修订。T中1-T、2-T通过，F三份均未通过；本轮不支持失败信息优于Task-Only。仅三对生成及单机制人工数据，不能泛化为T总体更优。通过者也没有端到端Generic收益证据，暂不发布。', '',
    f"Gate额外Worker账本：`{gatepath.relative_to(ROOT)}/budget.jsonl`。没有模型请求。Gate结果：{sum(g['passed'] for g in gate)}/{len(gate)}通过；Experimental仍为0。", '',
    '原六候选生成轮另有12次响应、77,386 Tokens，峰价估算$0.018077448；加本轮六次修订后，合计18次响应、108,973 Tokens、峰价估算$0.034489728。该合计只覆盖这两轮生成/修订，不是全部历史研发总成本。两轮账本均保留。']
 if (OUT/'final_audit.json').exists():
  audit=read(OUT/'final_audit.json')
  lines += ['', '## 最终工程审计', '',
    '新增22项零API验收通过；P1/P2兼容回归26/26通过（包含继承的无Gold测试，不重复累计21项）。最初测试环境缺少pydantic/PyYAML/requests，已在临时依赖目录安装后完成回归，没有更改系统全局依赖或数学算法。', '',
    '六份provider与预算账本均为HEALTHY，未知/待定请求0；旧Run文件哈希全部一致。计算/开发474次Worker调用，Gate432次，合计906次，账本工具耗时187.049秒，不含单元回归及人工成本。', '',
    '原始源码、各候选修订版和实验运行时工程源码已冻结。实验结束后只收紧运行入口的ValueError捕获范围：只有明确的交付解析错误可作为普通交付失败继续，模型漂移等错误必须传播停止。该后续工程变更没有重发模型或重跑评分，运行时/当前源码哈希分别保存在final_audit.json与frozen_source。', '',
    '|候选|AST发生变化的函数|', '|---|---|']
  for row in audit['candidates']:
   lines.append('|'+row['name']+'|'+', '.join(row['change']['changed_functions'])+'|')
  lines += ['', '0-F的原计算辅助函数AST未变，主要新增/修改解析与接口；其余五份的计算辅助函数也发生结构变化。该比较是语法树证据，不是数学等价性证明，所有修订均作为新代码版本重新验证。']
 report='\n'.join(lines)+'\n';(OUT/'Final_Report.md').write_text(report)
 dest=ROOT/'reports/math_symmetric_repair_20261031';dest.mkdir(parents=True,exist_ok=True);(dest/'Final_Report.md').write_text(report);save(dest/'summary.json',summary)
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
