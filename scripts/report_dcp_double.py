import json,datetime,collections
import run_dcp_discovery_double as m
h=m.h;c=m.c;o=h.OUT
h.verify();assert (o/'COMPLETE.json').exists();data=h.load(o/'discovery.json');stats=[]
for k,v in data.items():
 rec=v['receipt']['records'] if v['receipt'] else [];obs=[a for r in rec for a in r.get('observations',[])];bad={h.fingerprint(x['parameters']) for x in obs if x['status'] in ('WRONG','WRONG_ACCEPT','RUNTIME_ERROR','RESOURCE_EXCEEDED','INTERFACE_ERROR')};diff=v.get('differential') or {};comp=diff.get('comparisons',[])
 stats.append(dict(group=k,proposal_status='ACCEPTED' if v['proposal'] else 'DELIVERY_FAILURE',wrong_inputs=len(bad),statuses=dict(collections.Counter(x['status'] for x in rec)),worker_inputs=diff.get('total_worker_inputs',v['receipt']['worker_input_count'] if v['receipt'] else 0),comparisons=len(comp),disagreements=sum(x['disagreement'] is True for x in comp),alternative_wrong=sum(x.get('alternative_status') in ('WRONG','WRONG_ACCEPT') for x in comp),same_outputs=sum(x['disagreement'] is False for x in comp)))
cost=[];pending=[]
for d in sorted((o/'jobs').iterdir()):
 ev=c.EvidenceStore(d/'provider.jsonl').records();rr=[e for e in ev if e['kind']=='RAW_RESPONSE'];assert len(rr)==1;raw=rr[0]['payload']['response'];u=raw['usage'];dt=datetime.datetime.fromtimestamp(rr[0]['at'],datetime.timezone.utc);mult=1 if dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10) else .5;hit=u.get('prompt_cache_hit_tokens',0);miss=u.get('prompt_cache_miss_tokens',u['prompt_tokens']-hit);cost.append(dict(job=d.name,id=raw['id'],usage=u,estimated_usd=(hit*.006+miss*.3+u['completion_tokens']*1.2)*mult/1e6))
 b=c.PersistentBudget.__new__(c.PersistentBudget);b.path=d/'budget.jsonl'
 with b._locked() as rs:
  state,_=b._state(rs);pending.extend(x['status'] for x in state.values() if x['status']!='settled')
assert not pending
hist=h.load(o/'history_hashes.json');changed=[f for f,v in hist.items() if h.sha(h.ROOT/f)!=v];assert not changed
summary=dict(calls=len(cost),tokens=sum(x['usage']['total_tokens'] for x in cost),estimated_usd=sum(x['estimated_usd'] for x in cost),worker_calls=len(c.EvidenceStore(o/'worker.jsonl').records()),unknown=0,repairs=0,history_changed=changed)
h.save(o/'discovery_metrics.json',stats);h.save(o/'costs.json',cost);h.save(o/'summary.json',summary)
rows=['|组|可信错误输入|Worker输入|双程序比较|输出分歧|替代程序错误|','|---|---|---|---|---|---|']
for x in stats:rows.append('|'+ '|'.join(str(x[k]) for k in ['group','wrong_inputs','worker_inputs','comparisons','disagreements','alternative_wrong'])+'|')
(o/'Final_Report.md').write_text('# D/C/P双倍额度探索\n\n来源程序从2个增加为3个：计分、数字费用、根式；均为已曝光MATH Level5来源。每组测试上限8→16、Worker输入16→32，总费用硬上限2.40→4.80美元。模型与8192输出上限保持一致，不把工具预算加倍伪称所有模型参数加倍。\n\n'+'\n'.join(rows)+'\n\n错误输入不等于不同缺陷。计分错误属于既有离散分数区间化缺陷；其他错误若未完成根因归并，保留未归并状态。P输出差异必须独立核验原程序，不能把错误的替代假设当Oracle。相同输出只是本输入没有区分力，不是两个程序等价的证明。D/C没有可执行竞争假设，不将它们所有通过测试武断算作无区分力。\n\n每组单次生成，可能含一次合规交付澄清。已知开发材料、不同实际生成数和有限样本，不能据错误输入数量直接宣称方法优势。超额测试保存但不执行；没有按结果换题或追加修订。只有发现阶段，修复实验未启动。\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n完整提案、拒绝、原始响应、账本、替代源码及逐输入执行记录均在本目录。')
print(json.dumps(summary));print('\n'.join(rows))
