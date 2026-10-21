# -*- coding: utf-8 -*-
"""Summarize frozen evidence without model calls or executing candidates."""
import collections, hashlib, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
def read(path): return json.loads((ROOT/path).read_text())
def write(path, value): (ROOT/path).write_text(json.dumps(value, ensure_ascii=False, indent=2))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    tasks=read('trusted_tasks.json'); calls=read('rgf_frozen/calls.json'); ledger=read('rgf_results/ledger.json')['calls']
    grades=read('rgf_results/grades_all.json'); by_id={x['call_id']:x for x in grades}; logs={x['call_id']:x for x in ledger}
    assert len(calls)==len(ledger)==len(grades)==12
    for c in calls:
        cid=c['call_id']; g=by_id[cid]; l=logs[cid]
        assert l['state']=='RESPONSE' and l['request_sha256']==hashlib.sha256(json.dumps(c['request'],sort_keys=True).encode()).hexdigest()
        assert g['code_sha256']==sha(ROOT/'rgf_results/programs'/(cid+'.py'))
        raw=read('rgf_results/responses/'+cid+'.json')
        assert raw['usage']==l['usage']==g['usage'] and raw['model']==l['model']==g['model']=='deepseek-flash'
    manifest=read('rgf_frozen/manifest.json'); checked=0
    for rel,h in manifest['hashes'].items():
        p=ROOT/rel
        if not p.exists() and rel.startswith('../repair_v2d_20261020/'):
            p=ROOT.parent/'repair_v2/epochs'/rel[3:]
        assert sha(p)==h, str(p)
        checked+=1
    counts=collections.Counter(json.loads(p.read_text())['status'] for p in (ROOT/'verdicts').glob('*/*.json'))
    assert sum(counts.values())==155 and len(tasks)==35 and sum(t['cases'] for t in tasks)==3089
    arms={}
    for arm in 'RGF':
        gs=[g for g in grades if g['condition']==arm]; ls=[l for l in ledger if l['condition']==arm]
        passed=sum(g['audited_hidden']['passed'] for g in gs)
        arms[arm]={'calls':len(gs),'passed':passed,'rate':passed/len(gs),
          'prompt_tokens':sum(l['usage']['prompt_tokens'] for l in ls),
          'completion_tokens':sum(l['usage']['completion_tokens'] for l in ls),
          'total_tokens':sum(l['usage']['total_tokens'] for l in ls),
          'latency_s':round(sum(l['latency_s'] for l in ls),3)}
        arms[arm]['tokens_per_success']=round(arms[arm]['total_tokens']/passed,2)
    total=sum(l['usage']['total_tokens'] for l in ledger)
    assert total==135279 and total<=3000000 and len(ledger)<=72
    result={'trusted_tasks':35,'legal_cases':3089,'inventory':2132,'regraded':155,'outside_coverage':1977,
      'offline_statuses':dict(counts),'verified_functional_failures':2,'arms':arms,'new_calls':12,'new_tokens':total,
      'frozen_hashes_verified':checked,'actual_model':'deepseek-flash','independent_tasks':2,
      'paired_task_mean_differences':{'G_minus_R':.25,'F_minus_R':.25,'F_minus_G':0}}
    write('summary.json',result)
    lines=['# 可信任务集与 R/G/F 实验报告','',
      '已完成 35 题可信有限测试集、历史候选离线重评、两道真实实现失败的反事实验证，以及 12 次 R/G/F 修复试验。没有发现可确证的算法选择或 DP 状态/转移错误；不能据此证明这类错误不存在。','',
      '## 可信任务集与离线重评','',
      '31 道 TACO、4 道 LCB，共 3,089 个预先冻结的合法输入。逐题检查输入契约、参考计算与比较方式；35 个正确参考程序全部通过，35 个有意错误的评分探针全部被拒绝，专项比较器另做 1,369 次独立交叉核验。探针仅用于检验评分器，不属于历史失败，也不进入 F 的经验库。','',
      '对 2,132 份历史候选完成清单与哈希登记；其中属于这 35 题的 155 份实际离线评分，其余 1,977 份未在本轮覆盖。离线阶段没有调用生成模型。','',
      '|结果|程序数|占155份|','|---|---:|---:|']
    for status,n in sorted(counts.items()): lines.append(f'|{status}|{n}|{n/155:.2%}|')
    lines += ['', '没有把空代码、语法错误归为算法失败。两个运行异常均有合法输入、异常栈、独立正确结果与最小修复，确认为实现缺陷。', '',
      '参考程序中，abc399_e 使用此前 E2 已保存的 R2 修复，明确不属于原 2,132 份历史候选；其余参考来源见 trusted_tasks.json。通过仅表示通过本轮有限输入，不能保证题目全部输入域正确，也不是原800题的新成功率。','',
      '## 确证根因','',
      '|任务 / 历史阶段|合法反例与实际错误|根因与最小反事实修复|独立留出验证|','|---|---|---|---:|',
      '|abc301_f / l1|AaAA 应输出1，实际 IndexError|阶乘表只按输入长度分配，却用到26字母范围；将容量下限提高到26|45/45|',
      '|taco_0875 / l1|1100人无环反向管理链应输出1100，实际 RecursionError|记忆化不降低递归深度；提高递归上限到10000|90/90|','',
      '两者分别属于下标/容量缺陷与运行时递归资源缺陷，各占本轮2个确证功能失败的50%。它们均不是算法选错的证据。每题目录保存原始程序、错误输出、异常栈、反例、最小差异和修复验证；见“逐题根因证据.md”。','',
      '## R/G/F 试验','',
      '仅2个检查点合格，按实际数量执行：每题三条件、各重复两次、每次只修复一次，共12次。R为普通Reflection，G为通用修复检查，F为其他任务的历史失败机制引导。同题共享原始程序、题面与相同公开诊断；F严格排除本题及同家族经验。公开反例独立生成，未取自原隐藏测试；最终留出输入采用另一随机种子，事先冻结且不发送给模型。','',
      '请求相同模型与参数、相同32768输出Token上限和统一最终评分。实际服务端模型均报告 deepseek-flash；不能将结果写成 deepseek-reasoner。思考Token已经包含在completion/total中，不重复计费。','',
      '|条件|通过/调用|通过率|输入Token|输出Token（含思考）|总Token|每次成功Token|累计响应秒|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for a,v in arms.items(): lines.append(f"|{a}|{v['passed']}/{v['calls']}|{v['rate']:.0%}|{v['prompt_tokens']:,}|{v['completion_tokens']:,}|{v['total_tokens']:,}|{v['tokens_per_success']:,.2f}|{v['latency_s']}|")
    lines += ['', '|任务|R|G|F|','|---|---:|---:|---:|']
    for tid in sorted({g['task_id'] for g in grades}):
        values=[str(sum(g['audited_hidden']['passed'] for g in grades if g['task_id']==tid and g['condition']==a))+'/2' for a in 'RGF']
        lines.append('|'+tid+'|'+'|'.join(values)+'|')
    lines += ['', f'新增合计 {total:,} Token、12次调用，均低于72次/300万Token上限。R唯一失败为abc301_f第1次重复：finish_reason=length，未产出完整可执行代码；不应解释成修复后算法仍然错误。其余11份修复通过各自全部45或90个留出输入。','',
      '按题配对平均：G−R与F−R均为+25个百分点，F−G为0。只有2道独立任务，重复调用不等于独立任务；不做显著性或总体提升推断。本轮没有观察到F超过G。F增加了其他任务历史知识，提示长度与内容也不同，因此本试验不能单独识别“机制算子创新”的因果贡献。成本为Token与耗时，未估算货币费用。','',
      '## 评分修订与边界','',
      '比较器保留有序输出和重复元素；浮点按题面容差；函数返回允许数值等价但排除bool冒充数值；分组、二进制串构造、奇偶约束等使用独立语义检查与小规模穷举交叉核验。输入契约检查同时覆盖多测换行、合法值域与管理图无环条件。早期草稿中非法输入/展开行布局已在预检中否决，draft_verdicts_invalid_layout及suite_*_draft不参与统计。','',
      '可信范围是冻结输入及所审查比较器。大部分生成输入为可独立穷举的小规模域，管理链包含最大深度2000；仍需更广泛的合法压力测试才能讨论完整复杂度正确性。本次未完成原800题所有评测器的整体认证，也未证明所有新旧评分翻转均合理。','',
      f'最终检查：12次请求哈希、响应usage、程序哈希相符；{checked}个冻结文件哈希复核通过。协议、调用顺序、原始响应、留出评分与成本台账均保留。','',
      '## 文件入口','',
      '- trusted_tasks.json：35题及参考程序来源、比较规则、覆盖数量。',
      '- input_contract_review.json / validation.json：契约与独立检查证据。',
      '- inventory_2132.json / verdicts：全量清单与155份实际重评。',
      '- 逐题根因证据.md / counterfactuals：2题根因与最小修复。',
      '- rgf_frozen：模型调用前冻结的协议、提示与独立留出输入。',
      '- rgf_results：12份原始响应、程序、评分与成本台账。',
      '- summary.json：机器可读汇总。', '']
    (ROOT/'实验报告.md').write_text('\n'.join(lines))
    cards=['# 逐题根因证据','', '这两项是原始历史程序在合法输入上的真实运行失败；不是人为变异程序。公开反例与原隐藏测试无关。','']
    for f in read('failure_mechanism_bank.json'):
        tid=f['task_id']; d=ROOT/'counterfactuals'/tid; v=read('verdicts/'+tid+'/l1.json'); evidence=f['public_evidence']
        (d/'public_input.txt').write_text(evidence['input']); (d/'expected.txt').write_text(evidence['expected']+'\n')
        write('counterfactuals/'+tid+'/original_failure.json',v)
        cards += ['## '+tid,'', '分类：VERIFIED_ALGORITHM_FAILURE（实现缺陷；不代表算法选择错误）。', '',
          ('输入为长度4的字母串 AaAA；不存在符合DDoS条件的四位置子序列，唯一填充方案合法，结果1。' if tid.endswith('abc301_f') else 'n=1100，父节点依次为2至1100、末节点为-1，所有父节点合法且无环。整条链任意两人有祖先关系，至少1100组；每人单独成组可行，故答案1100。'), '',
          '根因：'+f['root_cause']['mechanism'], '', '最小修复：', '```diff', (d/'minimal.diff').read_text().rstrip(),'```','',
          '实际异常：','```',v.get('actual',{}).get('stderr','').rstrip(),'```','',
          f"修复通过冻结任务集 {read('counterfactuals/'+tid+'/verification.json')['tested']} 个输入，以及另行冻结的留出输入 {read('rgf_frozen/baselines/'+tid+'.json')['counterfactual']['tested']} 个。局部修复支持上述机制解释，不构成全输入域证明。", '',
          f'证据目录：counterfactuals/{tid}/，含 original.py、fixed.py、minimal.diff、public_input.txt、expected.txt、original_failure.json、verification.json。','']
    (ROOT/'逐题根因证据.md').write_text('\n'.join(cards))
    write('artifact_integrity.json',{str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='artifact_integrity.json' and '__pycache__' not in p.parts})
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
