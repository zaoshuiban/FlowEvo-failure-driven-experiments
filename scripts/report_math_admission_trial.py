"""Read-only report of the bounded admission attempt; never promotes candidates."""
import json
from run_math_admission_trial import ROOT,load,save
r=ROOT/'runs/math_admission_trial_20261031_01'
def events(p):return [json.loads(x) for x in p.read_text().splitlines()]
rows=load(r/'development.json');raw=[x['payload']['response'] for x in events(r/'provider.jsonl') if x['kind']=='RAW_RESPONSE'];u=raw[0]['usage'];w=events(r/'worker.jsonl');reg=events(r/'registry.jsonl');a=load(r/'artifact.json')
peak=(u['prompt_cache_hit_tokens']*.006+u['prompt_cache_miss_tokens']*.3+u['completion_tokens']*1.2)/1e6
summary=dict(status='SHADOW_DEVELOPMENT_FAILED',real_requests=len(raw),tokens=u,estimated_cost_usd_peak=peak,estimated_cost_usd_offpeak=peak/2,invoice_cost=None,worker_calls=len(w),worker_seconds=sum(x['payload']['seconds'] for x in w),computational_correct=3,supported_total=3,correct_accept=2,negative_total=2,explicit_decline=1,negative_unknown=1,false_accept=0,interface_error=0,registered_shadow=1,experimental=0,gate_executed=False,online_trial_executed=False,algorithm_sha256=a['solver_sha256'],joint_sha256=a['code_sha256'],scope='parameterized MATH source-derived development only; no independent-original reuse evidence')
save(r/'summary.json',summary)
report=f'''# 数学算子准入与后续复用：真实候选验收

结论：**PARTIAL / SHADOW_DEVELOPMENT_FAILED**。完成真实模型契约生成和真实 Linux Worker 验收；未达到准入条件，未执行 Gate 或后续在线试用。不能宣称已完成数学数据集在线复用收益验证。

## 候选选择与冻结

使用历史真实生成的 `hard140-math-train-number_theory-420-FC` 算法。选择依据为已曝光来源和18个参数测试的正确计算证据，不依据本次Gate结果选优。算法原文与历史 `code_response.json` 完全一致。

- 算法 SHA256：`{a['solver_sha256']}`。
- 算法/契约联合 SHA256：`{a['code_sha256']}`。
- 协议：`{load(r/'freeze.json')['sha256']}`。
- 新模型仅接收算法、参数接口和原来源题面；不接收开发/Gate/未来题、标准答案或旧失败轨迹。因此这是**历史失败驱动算法＋Task-Only契约**，不构成新的失败驱动契约学习证据。
- 仅1次契约生成、不修订、不替换候选。源码、Worker版本、数据及预算均事前冻结。
- 开发、Gate、Future各5条：3个支持参数/题面变体，2个目标量或进制改变的负控制。均为受控派生任务，**不是15道不同原始MATH题**，也不是新数据集泛化。
- 新协议独立上限2美元（生成0.20、条件求解1.80），最多21次请求；实际仅1次。

## 开发结果

| 指标 | 结果 |
|---|---:|
| 可信参数计算正确 | 3/3 |
| 从题面正确接受并计算 | 2/3 |
| 支持题过度拒绝 | 1/3 |
| 不支持题明确拒绝 | 1/2 |
| 不支持题UNKNOWN并安全回退 | 1/2 |
| 错误接受 | 0/2 |
| 接口/执行错误 | 0 |
| 注册Shadow | 1 |
| 获得Experimental | 0 |
| Gate实际执行 | 0 |
| 未来在线试用 | 0 |

第三个支持题用 `base ten / base two` 表述相同数学要求；模型契约只检测 `binary / base 2`，因而拒绝。计数目标负例被返回UNKNOWN，而不是现有准入要求的明确DECLINE。未放宽标准，也未人工改写匹配器。

独立评分使用宿主枚举参考，而非待测算法作为Oracle；另用十进制数字元组构造进行了9个支持参数的交叉核对。参考答案仅供私有评价。算子执行输入只有公开题面或参数，模型请求不含答案。参考核对只能确认这一有限任务分布，不能证明算法全域正确。

## 成本与状态

真实请求1次，输入{u['prompt_tokens']}、输出{u['completion_tokens']}，合计{u['total_tokens']}tokens；缓存命中{u['prompt_cache_hit_tokens']}。
按保存的官方报价，峰时估算${peak:.9f}，非峰时${peak/2:.9f}；当前日期为周末，非峰口径供参考，**不是供应商账单**。保守账本预留与实际用量分列在原始账本中，未将预留视为实付。
Worker实际执行{len(w)}次，累计{summary['worker_seconds']:.3f}秒；本地成本未货币化。无UNKNOWN请求，无重发，无追加模型生成。

## 权限与证据边界

现有VersionGate已写入Shadow与失败的Development收据；没有Experimental授权，也没有未来试用额度。算法/契约源码与验证记录以联合哈希绑定。Gate/Future题在调用前已冻结、没有进入生成请求，也没有执行；宿主准备数据不等于模型曝光。

本轮没有找到达到完整准入条件的版本。继续更换措辞、删除失败题或放宽UNKNOWN标准，会改变冻结研究问题；本轮未这样做。用户要求的“准入后在线复用收益”仍未完成，当前阻断依然是自然语言适用契约，而非计算源码交付或计算执行。

旧报告、旧Run、旧权限未覆盖。历史模型成本未重复算入本轮费用；由于没有在线收益，不能声称学习成本已经回本。
'''
(r/'Final_Report.md').write_text(report)
print(json.dumps(summary,ensure_ascii=False,indent=2))
