"""Read-only V3.2 report; no generation, no modification of candidate/gate results."""
import json,sys,datetime,collections
from pathlib import Path
from run_math_v3_development import ROOT,save,sha
RUN=ROOT/'runs/math_v32_semantic_20261028_01';OUT=ROOT/'reports/math_v32_semantic_20261028'
def load(p):return json.loads(p.read_text())
def write(name,text):(OUT/name).write_text(text+'\n')
def report():
 OUT.mkdir(parents=True,exist_ok=True);plan=load(RUN/'protocol.json');dev=load(RUN/'development/summary.json');gate=load(RUN/'gate/summary.json');ds=load(RUN/'development/scores.json');gs=load(RUN/'gate/scores.json');costs=[]
 for key in plan['order']:
  starts={}
  for l in (RUN/key/'provider.jsonl').read_text().splitlines():
   r=json.loads(l)
   if r['kind']=='SEND_STARTED':starts[r['payload']['key']]=r['at']
   if r['kind']=='RAW_RESPONSE':
    v=r['payload']['response'];u=v['usage'];dt=datetime.datetime.fromtimestamp(r['at'],datetime.timezone.utc);factor=1 if dt.weekday()<5 and (1<=dt.hour<4 or 6<=dt.hour<10) else .5
    costs.append(dict(candidate=key,response_id=v.get('id'),model=v['model'],utc=dt.isoformat(),usage=u,finish_reason=v['choices'][0]['finish_reason'],elapsed_seconds=r['at']-starts[r['payload']['key']],estimated_usd=(u.get('prompt_cache_hit_tokens',0)*.006+u.get('prompt_cache_miss_tokens',u['prompt_tokens'])*.3+u['completion_tokens']*1.2)/1e6*factor,invoice=False))
 save(OUT/'costs.json',costs)
 metric={}
 for role,s in [('Development',dev),('Gate',gate)]:
  metric[role]={k:dict(v,correct_accept_rate=v['correct_accept']/v['supported'],false_accept_rate=v['false_accept']/v['unsupported'],unknown_rate=v['unknown']/(v['supported']+v['unsupported']),interface_error_rate=v['interface_error']/v['total']) for k,v in s.items()}
 save(OUT/'metrics.json',metric)
 pairs=[]
 for role,rows in [('Development',ds),('Gate',gs)]:
  for rep in range(1,4):
   f={x['task_id']:x for x in rows if x['candidate']=='F'+str(rep)};t={x['task_id']:x for x in rows if x['candidate']=='T'+str(rep)}
   pairs.append(dict(role=role,replica=rep,f_only=sum(f[k]['correct_accept'] and not t[k]['correct_accept'] for k in f),t_only=sum(t[k]['correct_accept'] and not f[k]['correct_accept'] for k in f),both=sum(f[k]['correct_accept'] and t[k]['correct_accept'] for k in f),f_false=sum(x['false_accept'] for x in f.values()),t_false=sum(x['false_accept'] for x in t.values())))
 save(OUT/'paired_results.json',pairs)
 worker=[]
 for role in ['development','gate']:
  worker += [json.loads(l)['payload'] for l in (RUN/role/'worker.jsonl').read_text().splitlines() if json.loads(l)['kind']=='V3_COMPONENT_EXECUTED']
 save(OUT/'worker_usage.json',dict(calls=len(worker),wall_seconds=sum(x['seconds'] for x in worker),monetized=False))
 baseline=load(RUN/'data_v2/manifest.json')['old_artifact'];artifacts=load(RUN/'candidate_freeze.json')['artifacts'];assert all(a['solver_sha256']==baseline['solver_sha256'] and sha(a['solver_path'])==baseline['solver_sha256'] for a in artifacts.values())
 historical={p:sha(p)==h for p,h in plan['history_files'].items()};assert all(historical.values());save(OUT/'historical_integrity.json',historical)
 save(OUT/'component_versions.json',{k:{field:a[field] for field in ['solver_sha256','matcher_sha256','contract_sha256','code_sha256']} for k,a in artifacts.items()})
 def table(s):
  text='|版本|正确接受|错误接受|UNKNOWN（可判定题）|接口ERROR|歧义接受|\n|---|---:|---:|---:|---:|---:|\n'
  for k in ['V31_F3_F','T1','F1','T2','F2','T3','F3']:
   v=s[k];text+='|'+ '|'.join([k,f"{v['correct_accept']}/12",f"{v['false_accept']}/8",f"{v['unknown']}/20",f"{v['interface_error']}/24",f"{v['ambiguous_accept']}/4"])+ '|\n'
  return text
 write('V3_2_Frozen_Contract_Audit.md',f'''# 冻结F3契约究竟学到了什么

算法SHA `{baseline['solver_sha256']}`；V3.1 F3_F匹配器SHA `{baseline['matcher_sha256']}`。全部保持不变。

旧自动合法正例只有2/5通过：其余3条都写了“rearranging is not allowed”，旧代码只接受三个固定更长短语，因此提前UNKNOWN；不是这些题在数学上无法判断。单操作数正例还潜藏第二道限制：解析器必须看到运算符、至少3个交替token，虽然冻结solve支持单操作数。

契约将目标量识别实现为固定短语列表；参数提取选择最长数字/运算符片段，无法保证覆盖整个表达式。它排除÷、指数等部分写法，却未完整排除普通斜杠、目标否定等。以上是只读代码审查，并未把这些人工补丁写进新匹配器。

V3.2新开发支持题上旧契约0/12，新封存支持题也0/12。Gate的UNKNOWN为0不意味着优秀：它主要直接DECLINE。V3.1的8/8应限于此前题面表达分布，不能说明一般语义适用性已学会。

代表案例继续保留：原F2联合SHA未变却全拒绝，代表未发生有效修订；原T3覆盖提高但目标量误触发，代表覆盖与安全冲突。本轮只围绕冻结F3算法做配对，没有重写这两份历史案例。''')
 write('V3_2_Data_and_Protocol.md',f'''# 数据独立性与预注册协议

协议SHA `{load(RUN/'freeze.json')['sha256']}`。

新建Development24和Gate24，各12支持、8不支持、4歧义。正例包括自然措辞、列表描述、树与集合描述、单操作数；负例只改变目标量、重排许可或算术域；歧义题含矛盾要求或缺失关键字段。支持/不支持标签由宿主在生成前按完整语义审查，歧义不强制标MATCH/DECLINE。

数值参考由P0封存的既有独立参考函数计算，不使用待测solve作为Oracle，不将标准答案、参考源码或新题面发给生成模型。题面作者与语义审查均为本次宿主流程，不是第三方盲法双审，应保留此限制。

隔离层级：新题面不在历史模型请求中；新正例参数与历史及另一角色不重叠；Development/Gate使用不同措辞模板。历史8条失败在V3.1锁定，新题池随后建立。F只获得公开题面、旧match状态/参数/原因及既有语义审查标签，不获得旧matcher代码、数学Gold或新评价题。

**来源限制：这些是新编写的合成语义题，同属一个数学机制族。它们具有不同题面/参数/编写来源，但不能声称不同自然原题或跨数据集泛化。** 原P0 Gate/Legacy/Fresh未读取。首次准备目录data的负例谱系哈希预检发现引用了未使用参数占位，执行前更正为题面实际数值/符号指纹并重新冻结为data_v2；原目录保留且不参与模型请求或评分。

三对F/T契约生成，使用相同冻结算法、schema和原来源题面；F额外获得8条历史真实失败。DeepSeek Flash，温度0.2，非思考，每份1次请求、12288输出上限、无后续修订。固定顺序T1,F1,F2,T2,T3,F3。此处数字是生成重复编号，不是旧F1/F2/F3算法编号。没有按新题结果挑选候选。

未加入等Token非失败P，因为本地未找到兼容离线分词器；不将字符数当Token匹配。F/T输入长度仍不同，故仍不能隔离失败语义知识与额外上下文的贡献。

全部静态合法候选及原冻结基线在任何开发评分前一起冻结，随后同一Gate各评价一次。这里是隔离研究确认，不是生产准入：不因开发表现筛选Gate候选、不授予Experimental、不利用Gate修订。如此避免只汇报最佳版本；所有候选仍Shadow。''')
 write('V3_2_Paired_Results.md',f'''# 配对开发与新封存结果

## 新开发集

{table(dev)}

## 一次性新封存集

{table(gate)}

Gate三对的逐题差异：

{json.dumps([p for p in pairs if p['role']=='Gate'],ensure_ascii=False,indent=2)}

F1错误接受指数链 `3 ** 2 - 5`；F2错误接受“所有不同结果的和”，而冻结算法只计算集合大小。两者都是适用性错误，不能以算法源代码本身未改变为由忽略。

开发上F2曾正确接受7/12，但新措辞Gate降为1/12且有1次错误接受。旧V3.1正例基线新Gate为0/12。这说明当前代码仍高度依赖局部措辞，现有失败信息没有稳定转化为宽覆盖且安全的契约。

F累计2/36、T累计1/36只是同12道支持题上的三次生成观察，不是36道独立题。三个F候选总计2次错误接受，T为0。没有可靠的安全增量，不进行总体优势宣称。各候选所有接口ERROR均为0，本轮主要问题已经是语义边界而非交付。

没有候选满足全部支持题正确接受、零错误接受及零歧义接受的开发/确认条件。没有增加算子权限或开始FlowEvo大规模试用。''')
 tokens=sum(c['usage']['total_tokens'] for c in costs);usd=sum(c['estimated_usd'] for c in costs)
 write('V3_2_Final_Report.md',f'''# V3.2 实验总结

**结论：有限独立题面验证完成，未获得失败驱动契约优于Task-Only的稳定、安全收益；当前正向研究主张仍未成立。**

冻结同一F3计算算法，仅生成6份新契约，3对F/T。6次真实DeepSeek响应均交付且静态合格，无人工修改、无重复生成。新增开发和封存各24题，在生成前固定；模型未见其中任一题面。所有候选先冻结，再同集一次性确认，结果不回流模型。

{table(gate)}

最重要的新证据：旧V3.1 F3在此前Design上的8/8没有迁移到新措辞，Gate支持题为0/12。新F候选分别1/12、1/12、0/12，T分别0/12、1/12、0/12；F有2次明确错误接受，不能把多一次成功说成可靠增益。没有接口ERROR，主要瓶颈是用短语/正则表达语义前提与数学目标量。

## 边界

这批题是新编写的合成语义测试，同数学机制族，**不是不同自然原题的独立泛化**。F/T只控制了算法、来源题面、模型、工具与调用上限；未设置等Token P，生成样本也只有3对。因此完成的是V3.2小规模合成题机制诊断，不是完整因果证明或统计否定。

Gate在本轮新协议中是全部冻结候选的隔离审查，不等于获得Experimental权限；原先V3.1未准入的决定不变。旧P0 Gate/Test没有使用。新Gate已曝光，此后不能再充当未见测试。

## 成本及完整性

6次真实请求、{tokens:,} Token，新增费用估算 **${usd:.8f}**（当前官方峰谷/缓存报价，非账单）。无新UNKNOWN、无截断。Linux Worker实际函数执行{len(worker)}次，宿主等待合计{sum(x['seconds'] for x in worker):.3f}秒，工具成本未货币化。6份算法源码与原SHA全部相同，旧历史文件核验不变。所有响应、冻结输入、源码、联合哈希、完整逐题输出与评分已保存。

## 后续判断

停止本轮生成，不根据Gate再改Prompt或补规则。保留F3接口修订正例、F2学习停滞和T3误触发反例，避免只讲成功案例。当前证据不支持启动大规模FlowEvo实验，也不支持继续用同类生成请求期待偶然胜出。若后续改造语义表示，需要新开发协议与新确认数据，明确承认旧Gate已曝光。

文件：V3_2_Frozen_Contract_Audit.md、V3_2_Data_and_Protocol.md、V3_2_Paired_Results.md，以及costs.json、metrics.json、paired_results.json、component_versions.json。''')
 save(OUT/'manifest.json',dict(run=str(RUN),protocol_sha256=load(RUN/'freeze.json')['sha256'],files={str(p.relative_to(ROOT)):sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'},scripts={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'scripts/prepare_math_v32.py',ROOT/'scripts/run_math_v32.py',ROOT/'scripts/evaluate_math_v32.py']}))
 print('REPORT',OUT,'TOKENS',tokens,'USD',usd,'WORKER',len(worker))
if __name__=='__main__':report()
