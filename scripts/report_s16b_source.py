"""Read-only diagnosis of S16-B model responses; writes only derived report files."""
import json,hashlib
from pathlib import Path
import run_workflow_v2 as entry
ROOT=entry.ROOT;R=ROOT/'runs/s16b_source_20261022_01'
read=entry.read;write=entry.write;sha=entry.sha
s=read(R/'summary.json');p=read(R/'plan.json');raw=read(R/'wire/learning/1/response.json')
c=raw['choices'][0];value=json.loads(c['message']['content'])
diagnosis=dict(stage='fresh_specification',error='SPECIFICATION_OUTPUT_CONTRACT_ERROR',json_parse_passed=True,finish_reason=c['finish_reason'],expected_fields=sorted(entry.SPEC_FIELDS),actual_fields=sorted(value),missing_fields=sorted(entry.SPEC_FIELDS-set(value)),unexpected_fields=sorted(set(value)-entry.SPEC_FIELDS),nonempty_string_fields={k:isinstance(value.get(k),str) and bool(value[k].strip()) for k in entry.SPEC_FIELDS},unexpected_values={k:value[k] for k in set(value)-entry.SPEC_FIELDS},raw_response_sha256=sha(R/'wire/learning/1/response.json'),request_sha256=sha(R/'wire/learning/1/request.json'),old_interpretation_reused=False,manual_normalization_applied=False,new_request_sent=False)
assert diagnosis['unexpected_fields']==['type'] and not diagnosis['missing_fields'] and all(diagnosis['nonempty_string_fields'].values())
write(R/'specification_contract_diagnosis.json',diagnosis)
# Exercise the actual entry induction method with an in-memory sender only. No
# network, key, PersistentBudget mutations or changes to the real run records.
class MockTransport:
 def __init__(self,text):self.text=text;self.calls=0
 def send(self,*a,**k):self.calls+=1;return dict(text=self.text,finish_reason='stop',model='deepseek-flash')
def check(text,want_error):
 obj=entry.ExperimentRunner.__new__(entry.ExperimentRunner);tr=MockTransport(text)
 obj.transports={'learning':tr};obj.outputs={};obj.save=lambda:None
 try:obj.induction('fixture',read(R/'source_packet.json'));error=False
 except ValueError:error=True
 assert error==want_error and tr.calls==1
 assert bool(obj.outputs)==(not want_error)
 return dict(passed=True,mock_only=True,real_api_requests=0,rejected=error)
tests=dict(saved_real_extra_field=check(c['message']['content'],True),valid_engineering_fixture=check(json.dumps({k:'ENGINEERING TEST ONLY' for k in entry.SPEC_FIELDS}),False))
write(R/'schema_regression.json',tests)
for path,h in p['frozen_files'].items():assert sha(ROOT/path)==h,path
hist=read(R/'historical_before.json');assert all(sha(f)==h for f,h in hist.items())
write(R/'final_integrity.json',dict(plan_hash_valid=p['protocol_hash']==entry.fingerprint({k:v for k,v in p.items() if k!='protocol_hash'}),frozen_dependencies_checked=len(p['frozen_files']),historical_files_checked=len(hist),all_unchanged=True))
learn=s['budgets']['learning'];solve=s['budgets']['solve'];accept=read(R/'scorer_acceptance.json')
text=f'''# S16-B：真实生成与来源验收实验报告

运行：`{R.name}`。日期：2026-10-22。

**结果：在真实规格归纳的输出契约检查处停止。没有生成 Operator，没有进行 Operator 来源修复，不能据此判断修复机制是否有效。**

本轮实际发出 1 次 DeepSeek 请求，收到正常 stop 响应。模型正确将来源理解为“未交付程序”，但额外输出了 `"type": "json_object"`，违反冻结的六字段规格契约。实验按规则停止，没有删除额外字段、手工补规格、再次归纳或转用旧机制继续生成。

## 冻结范围与授权

- 从两个已重投影的来源中，固定使用第一个 `taco_0313` 的 l1 缺失程序检查点；第二个 `taco_0511` 不参与本轮归纳和选优。
- 只做一个 `missing_program_delivery_policy` 方向，不强凑第二机制族。
- 最多 1 次规格归纳、1 个初始候选、1 次候选修订：生成请求上限 3。
- 每个候选版本最多 2 次来源宿主修复，共不超过 4 次；同一原始检查点的重复尝试不算独立任务。第一次真正通过即停止后续来源尝试。
- 全程使用新 Run、PersistentBudget、此前验收的 ExperimentRunner / v2 共同协议。没有继承旧账本余额。
- 新生代规则预先冻结：来源确实由生成策略请求宿主修好，基本正反检查及零预算回退通过，才允许对预注册的 `taco_0511` 最多 1 次未来受限试用；本轮不执行该试用。
- 该限定来自本次“进行实验 S16-B”的明确请求；没有扩大为 30 题重跑、第二机制族或无界修订。

## 请求配置与预算

模型请求名及实际返回标识均为 `deepseek-flash`；官方当日列示版本为 `DeepSeek-V4.1-Flash-1017`，但响应未单独返回版本字符串，不能据此另造实测版本。`thinking=disabled`、`reasoning_effort=none`、`temperature=0`、输出上限 8,192。规格和候选采用 JSON 输出；JSON 模式不保证业务对象只有所需字段。

学习输入保守上界为 65,536，来源求解为 32,768。它们使用最终序列化 UTF-8 字节数加 2,048 的本地估计，不等于实际 tokenizer 计数。没有放宽 S16-A/S16-B 前置验收中的上限。

按 [DeepSeek 官方价格页](https://api-docs.deepseek.com/quick_start/pricing/) 当日峰时、缓存未命中价格：输入 $0.30 / 百万 Token，输出 $1.20 / 百万 Token。

|预算|生成|来源宿主求解|合计|
|---|---:|---:|---:|
|最大请求数|3|4|7|
|最大输入＋输出 Token|221,184|163,840|385,024|
|按输入/输出分别计算的报价上界|$0.0884736|$0.0786432|$0.1671168|
|账本采用更保守预留率的货币硬限|$0.27|$0.20|$0.47|

持久账本用最高输出单价保守预留所有 Token，费用未知时不当作零。实际响应费用另外按冻结价格估算；不是账单结算。工具货币成本未知，另记工具次数和时间。

## 零 API 准备与评分器验收

原始来源响应哈希、重新投影的空程序状态、公开题面和原三个公开检查已冻结；旧 `taco_0055` 的表达式补全解释、旧规格、旧策略和未来正确解答均没有进入归纳输入。

在任何 API 请求之前，原受限 Linux Worker 实际运行了已冻结参考程序和错误控制程序：

|检查|结果|
|---|---|
|参考程序的原三个公开检查|{accept['positive']['tests_passed']}/{accept['positive']['tests_run']} 通过|
|错误控制程序的公开检查|{accept['negative']['tests_passed']}/{accept['negative']['tests_run']} 通过，正确被拒绝|
|本轮工具调用|{solve['tool_calls']}，包括两次编译与六次程序测试|

参考程序只用于宿主评分器验收，没有提供给模型。复用已有隔离验收与不可变镜像，没有在宿主 Python 执行生成程序。以上是评分器准备，不是 Operator 的功能成功。

## 真实规格响应与阻断

唯一请求已完成，JSON 可解析、finish_reason 为 stop，要求的六个字段均存在且为非空字符串：

`mechanism / conditions / repair_strategy / refusal_conditions / stop_rule / limitations`

但实际对象还有第七个字段：

```json
{{"type": "json_object"}}
```

严格检查 `set(value) == SPEC_FIELDS` 失败，记录为 `SPECIFICATION_OUTPUT_CONTRACT_ERROR`。这不是请求预检错误、预算耗尽、网络失败、输出截断、Python 静态错误或来源修复失败。

新增的 type 字段与请求 response_format 的类型标识相同；一次响应不足以判断其因果来源，不能断言是供应商缺陷或模型必然持续犯错。本轮没有更改验证标准。

真实规格内容将来源描述为 delivery failure / NO_COMPLETE_CODE，并明确“不依赖旧说明作为算法”，所以此前错误机制解释没有被复用。但是，内容方向合理不等于契约合格；该响应作为失败制品保存，不进入候选生成。

## 实际执行量与成本

|环节|实际结果|
|---|---|
|真实规格归纳|1 次响应，契约未通过|
|初始候选生成|0|
|候选诊断修订|0|
|实际 Operator 源码|0|
|Operator 隔离执行|0|
|来源宿主修复请求|0|
|Operator 来源成功 / Generic 回退成功|均未发生|
|新生代准入 / 后续试用|0 / 0|

实际用量：输入 {raw['usage']['prompt_tokens']:,} Token，输出 {raw['usage']['completion_tokens']:,} Token，总计 **{raw['usage']['total_tokens']:,} Token**。缓存命中 0；响应未另列推理 Token，本报告不虚构推理用量分项。

按冻结峰值报价估算 **${s['peak_quote_estimated_usd']:.7f}**，实际账单未知。学习账本保留的货币额度为 **${learn['charged_or_reserved_cost_microusd']/1e6:.6f}**，这是保守预留，不是已付款金额。当前无未知或待结算的模型请求；只结算了真实 Token，未以报价估算冒充实付。

## 停止原因与结论

本轮已预先冻结“每族只归纳一次规格”。唯一规格响应不合格，因此没有合法规格可供生成候选。候选修订额度不能自动改成第二次规格归纳，未用完的预算也不能成为放宽规则、删除字段或增加机制族的理由。

合理结论为 **SPEC_CONTRACT_BLOCKED / 本轮未形成合格制品**。不是“容量修复无效”，也不是“工作流 Operator 无法修复该来源”；本轮根本尚未进入该验证阶段。不能把评分器参考程序通过当作策略成功，也没有将 Generic 自行修好计作 Operator 收益。

已补做两项零 API 回归，直接调用真实入口的 induction 方法：保存的七字段响应应被拒绝；六字段工程样例应被接受。均通过，工程样例不进入本轮真实规格或研究证据。

后续若处理规格输出问题，需要作为新版本/新运行明确冻结如何诊断与有限修订规格，而不是在本轮历史结果上静默规范化。当前实验已停止，不自动发起下一次调用。

## 证据入口

- `plan.json`、`authorization.json`：冻结规模、费用、代码哈希和本次授权依据。
- `source_packet.json`、`source_event.json`、`task_public_frozen.json`：来源及公开数据。
- `scorer_acceptance.json`：真实隔离程序验证。
- `wire/learning/1/request.json`、`response.json`：唯一真实请求和完整原始响应。
- `specification_contract_diagnosis.json`：逐字段诊断；没有手工规范化。
- `learning_requests.json`、`learning_budget.jsonl`、`solve_budget.jsonl`：实际调用和持久预算。
- `schema_regression.json`：两项工程回归，0 次 API。
- `summary.json`、`final_integrity.json`：停止状态及完整性。

S15、S16-A 和 S16-B 前置验收的历史文件均未改写；本轮冻结依赖也全部通过最终哈希核对。当前运行统计与原始失败响应保持原样。
'''
(R/'S16-B真实生成与来源验收实验报告.md').write_text(text)
print('REPORTED',s['status'],s['actual_response_count'],diagnosis['unexpected_fields'])
