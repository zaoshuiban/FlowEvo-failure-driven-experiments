import json,datetime,collections
from pathlib import Path
import run_dcp_discovery_verified as m
h=m.h;c=m.c;o=h.OUT
h.verify();assert (o/'COMPLETE.json').exists();data=h.load(o/'discovery.json');rows=[];stats=[]
for k,v in data.items():
 rec=v['receipt']['records'];obs=[z for x in rec for z in x.get('observations',[])];bad={h.fingerprint(x['parameters']) for x in obs if x['status'] in ('WRONG','WRONG_ACCEPT')};counts=dict(collections.Counter(x['status'] for x in rec));diff=v.get('differential') or {};comp=diff.get('comparisons',[])
 s=dict(group=k,test_specs=len(rec),confirmed_wrong_inputs=len(bad),distinct_defect_clusters=1 if bad else 0,non_error_observations=sum(x['status'] in ('CORRECT','CORRECT_REJECTION') for x in obs),statuses=counts,actual_differential_checks=len(comp),different_outputs=sum(x['disagreement'] is True for x in comp),same_outputs=sum(x['disagreement'] is False for x in comp),logical_worker_inputs=diff.get('total_worker_inputs',v['receipt']['worker_input_count']))
 stats.append(s);rows.append(f"| {k} | {len(bad)} | {s['logical_worker_inputs']} | {s['actual_differential_checks']} | {s['different_outputs']} |")
cost=[]
for d in sorted((o/'jobs').iterdir()):
 ev=c.EvidenceStore(d/'provider.jsonl').records();r=[e for e in ev if e['kind']=='RAW_RESPONSE'];assert len(r)==1;raw=r[0]['payload']['response'];u=raw['usage'];dt=datetime.datetime.fromtimestamp(r[0]['at'],datetime.timezone.utc);mult=1 if dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10) else .5;hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit);cost.append(dict(job=d.name,id=raw['id'],usage=u,estimated_usd=(hit*.006+miss*.3+u['completion_tokens']*1.2)*mult/1e6))
h.save(o/'discovery_metrics.json',stats);h.save(o/'costs.json',cost)
workers=c.EvidenceStore(o/'worker.jsonl').records();old=h.load(o/'history_hashes.json');changed=[p for p,d in old.items() if h.sha(h.ROOT/p)!=d];assert not changed
summary=dict(status='PARTIAL_DIFFERENTIAL_EVIDENCE',calls=len(cost),tokens=sum(x['usage']['total_tokens'] for x in cost),estimated_usd=sum(x['estimated_usd'] for x in cost),worker_calls=len(workers),history_changed=changed,revision_calls=0)
h.save(o/'summary.json',summary)
(o/'Final_Report.md').write_text('''# D/C/P差异驱动发现实验
Docker已恢复，既有镜像与隔离执行可用。原准备Run保留，真实调用在新Run02进行。

| 程序/组 | 独立确认错误输入 | 逻辑Worker输入次数 | 实际双程序比较 | 实际分歧 |
|---|---|---|---|---|
'''+ '\n'.join(rows)+'''

P在计分程序上找到了一个原程序错误，并且在同一输入上实际执行了不同计算假设，独立参考确认原程序错误、替代输出正确。D/C本次没有找到错误。该反例对应离散分数被当成连续区间的同一缺陷，只算一个缺陷，不是多个独立机制。未把研究者已知错误写进提示，也未使用上一轮确认输入来引导模型。

但是本轮必须判PARTIAL：P未按提示只返回单输入oracle_correct测试，而采用了多个双输入关系，消耗了预算；计分P只剩3次替代执行，数字负控制P用完16次原程序输入执行额度，没有剩余额度执行替代程序。不能说完整通过了双程序负控制，更不能用未执行分歧宣称无误报。关系被独立参考否定的提案作为错误关系保留，和原程序错误分开统计。普通测试通过不等于“无区分力”；D/C未声明竞争假设，不能据此计算其双假设区分率。

还有一次宿主缺失json导入错误，发生在P响应保存后。恢复使用原始响应，没有重发请求；原停止记录及续跑说明保留。重复Worker执行计入实际成本，但不重复计算反例。逻辑配额与实际工程开销分别保存，避免将恢复开销当作发现优势。

这是一道已曝光错误程序和一道已有正确性证据程序、每组一次采样的探索。P仅获得单例正向发现证据，尚不足以证明优于D/C。没有进行修订，没有额外调用补出正向结论。下一步若继续，应先固定单输入双程序执行的配额分配，再用新冻结样本确认；不要重跑本例争取胜出。

'''+f"真实调用{summary['calls']}次，{summary['tokens']}tokens，估算费用${summary['estimated_usd']:.8f}；实际Worker{len(workers)}次。历史文件未变。完整请求在jobs，执行在worker.jsonl，分组指标在discovery_metrics.json，费用在costs.json。\n")
print(json.dumps(summary,ensure_ascii=False));print('\n'.join(rows))
