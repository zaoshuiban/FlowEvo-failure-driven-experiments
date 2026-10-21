import ast,collections,csv,hashlib,json,math,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1];P=ROOT/'audit';D=P/'audit_20261020'
contracts=json.loads((ROOT/'runtime_contract_review.json').read_text());findings=json.loads((ROOT/'contract_findings.json').read_text())
extra={
 'taco_0491':'首个失败输入声明n=10，但两数组各仅5项。',
 'taco_0431':'首个失败输入同一玩家词表含重复hello，违反单方词表唯一约束。',
 'taco_0563':'首个失败文件含右下角不是C的网格。',
 'taco_0471':'5个相同的4共有C(5,2)=10对，参考输出6；程序输出10。',
 'taco_0234':'独立数组剪切模拟得到7 4 5 1 3 2 6，与程序一致，与参考输出不一致。',
 'taco_0602':'首个地图S到E曼哈顿下界14，但参考距离11；独立BFS得到28。',
 'taco_0594':'倒序排列相邻整数乘积不可能为完全平方；合法多解被单一参考文本拒绝。',
 'taco_0694':'唯一错误用例n=1，违反题面n>=3；其余153个通过。',
 'taco_0947':'失败用例包含数字0，题面明确排除0；当前模型将其按偶数处理。',
 'taco_0857':'测试含c_max>1000，且若干参考输出截在1000；独立数论计数核查见taco_0857_oracle_check.json。另本次重放初始化触及4秒限制，错误类别发生变化。',
 'taco_0191':'292测试中16个浮点精确比较失败；例如9.04433524367601与9.044335243676011，题面允许1e-7。',
 'taco_0137':'循环分配颜色满足每色各堆数量差<=1；首个失败示例只因合法着色方案不同。',
 'taco_0510':'7 24 25满足勾股关系，题面允许任意顺序；参考为24 25 7。',
}
lcb={
 'lcb_atcoder_abc375_c':('评测I/O兼容问题','MockBuffer.readline不推进位置，每次返回第一行；真实标准输入运行原程序通过36/36。'),
 'lcb_atcoder_abc314_d':('评测I/O兼容问题','stdout捕获器是StringIO，无buffer；真实标准I/O运行原程序通过14/14。'),
 'lcb_atcoder_abc392_d':('浮点比较问题','官方Decimal列表精确相等拒绝容差内数值；1e-9诊断容差下42/42。'),
 'lcb_atcoder_abc385_f':('浮点比较问题','官方Decimal列表精确相等拒绝容差内数值；1e-9诊断容差下44/44。'),
 'lcb_atcoder_abc314_e':('浮点比较问题','官方Decimal列表精确相等拒绝容差内数值；1e-9诊断容差下15/15。'),
 'lcb_atcoder_abc350_c':('多解比较问题','以实际交换后是否有序及操作次数范围验证，原程序通过3/3。'),
 'lcb_atcoder_abc311_c':('多解比较问题','以输出是否构成图中合法有向环验证，原程序通过15/15。'),
 'lcb_atcoder_abc315_e':('多解比较问题','以先修依赖集合及拓扑次序验证，原程序通过15/15。'),
 'lcb_atcoder_abc366_g':('多解比较问题','以各点邻居XOR及数字范围验证，原程序通过29/29；示例1 1 1与4 4 4均合法。'),
 'lcb_atcoder_arc181_c':('多解比较问题','以题面行列字典序约束验证，原程序通过27/27。'),
 'lcb_leetcode_3344':('测试参数契约问题','测试19传入[0,0]而非点数组，且不满足至少3点；TypeError发生在解包(x,y)，不能当作算法反例；仅剔除该非法用例后原程序通过其余26/26。'),
}
rows=[];stats=collections.Counter();hashes=[];attempt_count=0;feedback=collections.Counter();changed=[]
for f in sorted(P.glob('runs/*/*/result.json')):
 r=json.loads(f.read_text());tid=r['task_id'];ds=r['dataset'];task=json.loads((P/'task_summaries'/(tid+'.json')).read_text());trace=json.loads((D/('trace_'+tid+'.json')).read_text());last=r['attempts'][-1];code=(f.parent/(r['final_stage']+'.py')).read_text();flags=[];notes=[];classification='算法根因未确定';certainty='未确定';stage_valid=[]
 for a in r['attempts']:
  path=f.parent/(a['stage']+'.py');s=path.read_text();valid=bool(s.strip())
  try:ast.parse(s)
  except SyntaxError:valid=False
  stage_valid.append(valid)
  resp=f.parent/(a['stage']+'.response.json');d=json.loads(resp.read_text());attempt_count+=1
  assert d['finish_reason']==a['finish_reason'];assert hashlib.sha256(s.encode()).hexdigest()==a['code_sha256']
  if ds=='lcb' and a['stage'] in ('l3','l4'):
   msg=d['request']['messages'][-1]['content']
   for k in ['Runtime or compilation error.','Compilation or testing error.']:
    if 'Verifier feedback: '+k+'\n' in msg:feedback[k]+=1
  hashes.append({'path':str(resp.relative_to(ROOT)),'sha256':hashlib.sha256(resp.read_bytes()).hexdigest()})
 assert not any(a['passed'] for a in r['attempts'])
 if not stage_valid[-1] and any(stage_valid[:-1]):flags.append('较早有语法完整代码但最终丢失');stats['earlier_valid_final_invalid']+=1
 if last['finish_reason']=='length':
  classification='输出预算耗尽/产物不完整';certainty='直接日志';flags.append('最终响应截断');notes.append('最终文本为空。' if not code.strip() else '文本截断且保留未闭合Markdown代码围栏，导致语法错误。');stats['generation']+=1
 if tid in contracts:
  classification='输入数据违反题面契约';certainty='题面与原始失败输入直接比对';notes.append(contracts[tid]['explanation']);flags.append('已证实评测/数据异常')
 if tid in extra:
  classification='评测或测试数据异常';certainty='直接反例/数学条件核查';notes.append(extra[tid]);flags.append('已证实评测/数据异常')
 if tid in lcb:
  classification,detail=lcb[tid];certainty='异常元数据/独立契约验证';notes.append(detail);flags.append('已证实评测/数据异常')
 mismatch=trace.get('official_metadata',{}).get('mismatch',{});a=mismatch.get('actual','').split();b=mismatch.get('expected','').split()
 if a and len(a)==len(b):
  kind=None
  if a==b:kind='首个失败输出仅空白不同'
  elif any('.' in x or 'e' in x.lower() for x in a+b):
   try:
    if all(math.isclose(float(x),float(y),rel_tol=1e-9,abs_tol=1e-9) for x,y in zip(a,b)):kind='首个失败输出浮点数值一致或在1e-9内'
   except ValueError:pass
  if kind:
   flags.append(kind);flags.append('已证实评测/数据异常');notes.append(kind+'；仅定位当前拒绝用例，未据此证明整个程序全部测试正确。');classification='输出比较器异常';certainty='原始输出与参考输出对照'
 if tid=='taco_0382':classification='交互协议与离线评测不匹配';certainty='题面与协议直接核对';notes.append('题面要求交互询问，而本次只提供六个隐藏数字并使用普通stdin执行，无交互器。');stats['interactive']+=1
 if last['feedback']=='Time limit exceeded.' or tid=='lcb_atcoder_abc371_f':flags.append('观察到超时');stats['timeout']+=1;notes.append('超时是现象，不能据此区分算法复杂度、Python常数及执行资源限制。')
 if ds=='lcb' and tid in lcb and tid!='lcb_leetcode_3344':flags.append('修正契约后原程序全部用例通过');stats['counterfactual_lcb_allpass']+=1
 if trace.get('feedback') and trace['feedback']!=last['feedback']:changed.append(tid)
 if '已证实评测/数据异常' in flags:stats['evaluation']+=1
 if classification=='算法根因未确定':stats['unresolved_primary']+=1
 if ds=='lcb' and any('Verifier feedback: '+k+'\n' in json.loads((f.parent/(s+'.response.json')).read_text())['request']['messages'][-1]['content'] for s in ['l3','l4'] for k in ['Runtime or compilation error.','Compilation or testing error.']):flags.append('修复实际收到误译或不准确错误类别');stats['feedback_tasks']+=1
 rows.append({'task_id':tid,'dataset':ds,'difficulty':r['difficulty'],'original_final_feedback':last['feedback'],'primary_observed_mechanism':classification,'evidence_level':certainty,'flags':';'.join(dict.fromkeys(flags)),'explanation':' '.join(notes) or '现有运行错误类别不能区分算法选择、状态转移或边界缺陷；需在可靠评测契约下构造反例后归因。','final_code':str((f.parent/(r['final_stage']+'.py')).relative_to(ROOT)),'trace':str((D/('trace_'+tid+'.json')).relative_to(ROOT)),'final_response':str((f.parent/(r['final_stage']+'.response.json')).relative_to(ROOT)),'first_failed_test_index':trace.get('tests_reported',0)-1 if not trace.get('skipped') else '', 'finish_reason':last['finish_reason'],'attempts':len(r['attempts'])})
assert len(rows)==312 and attempt_count==1560
with (ROOT/'逐题机制审计.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(ROOT/'逐题机制审计.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));(ROOT/'audit_response_hashes.json').write_text(json.dumps(hashes,indent=2));summary={'tasks':len(rows),'attempts':attempt_count,'stats':dict(stats),'primary_counts':dict(collections.Counter(x['primary_observed_mechanism'] for x in rows)),'repair_feedback_occurrences':dict(feedback),'replay_category_changed':changed}
(ROOT/'mechanism_audit_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
