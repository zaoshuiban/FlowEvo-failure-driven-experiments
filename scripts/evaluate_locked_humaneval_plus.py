"""Score exactly 24 archived training solutions; never generate or sanitize.

prepare: bind source and run official input contracts without running solutions.
freeze: seal per-case common scopes before looking at any new solution results.
run: one official base/plus flow, at most one fixed diagnostic replay per failure.
"""
import argparse
import ast
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'FlowEvo/src'))
from failure_evo.container_worker import DockerWorker
from failure_evo.contracts import fingerprint
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.pilot_runtime import write_json,save_stop_snapshot
from failure_evo.skill_runtime import validate_bundle

ROOT=REPO/'runs/humaneval_plus_locked_20261120'
OUT=REPO/'reports/humaneval_plus_locked_20261120'
PRIVATE=ROOT/'private'
WORKER=REPO/'scripts/locked_evalplus_worker.py'
OLD_LOCK=REPO/'runs/failure_acquisition_postlock_audit_20261120/locked_submissions.json'
OLD_REPORT=REPO/'reports/failure_acquisition_postlock_audit_20261120/Postlock_Opportunity_Audit.json'
OLD_MANIFEST=REPO/'reports/failure_acquisition_pilot_20261120/Pilot_Data_Manifest.json'

REVIEWS={
0:('SCOPED_COMPATIBLE','正阈值、有限数值列表；排序相邻距离与原任意两元素距离定义一致。'),
20:('SCOPED_COMPATIBLE','原题未规定并列最小距离的择对规则；仅唯一最小值对属于共同可解释范围。所有案例仍原样评分。'),
1:('COMPATIBLE','平衡括号组，忽略空格；新版扫描在组结束处输出，与原题一致。'),
6:('SCOPED_COMPATIBLE','空格分组后每组须各自平衡；仅全串平衡不足以证明符合原分组题意。'),
56:('COMPATIBLE','仅尖括号，前缀不负且最终为零，空串按空配对解释。'),
61:('COMPATIBLE','仅圆括号，前缀不负且最终为零；与 56 是近重复机制，不当独立机制证据。'),
13:('SCOPED_COMPATIBLE','只解释正整数共同域；递归 Euclid 与原最大公约数定义一致。'),
24:('SCOPED_COMPATIBLE','只解释整数 n>1；最小非平凡因子对应最大真因子，素数返回 1。'),
25:('SCOPED_COMPATIBLE','只解释整数 n>=2，输出递增质因子及重数；新版参考与原参考 AST 一致。'),
31:('COMPATIBLE','整数素性，n<2 为假；只到平方根的试除不改变定义。'),
39:('SCOPED_COMPATIBLE','共同域为 1<=n<=12；新版参考改用概率素性检测，固定随机种子；超时单列，不能当错误答案。'),
59:('COMPATIBLE','n>1 的合数；筛法求最大质因子与原定义一致；旧修复不是新教师成果。'),
8:('COMPATIBLE','整数列表的和与积，空列表为 (0,1)；保留 tuple 返回约定。'),
9:('COMPATIBLE','整数列表每个前缀最大值；空列表返回空列表。'),
21:('SCOPED_COMPATIBLE','至少两个有限数且极差>0；相同线性变换，官方浮点容差保持不变。'),
46:('COMPATIBLE','非负整数四项递推，固定初值；不要求借由改写历史程序消除递归。'),
55:('SCOPED_COMPATIBLE','非负整数 Fibonacci，共同域含 n=0；迭代参考替代递归不改变数列。'),
63:('COMPATIBLE','非负整数三项递推与原初值一致；效率问题单列。'),
10:('COMPATIBLE','字符串最短回文后缀补全，包含空串；不拼接新版 helper 到提交源码。'),
48:('COMPATIBLE','字符串与反转相同的回文谓词，包含空串。'),
18:('SCOPED_COMPATIBLE','只解释非空子串的重叠计数；空子串语义不用于归责。'),
17:('SCOPED_COMPATIBLE','只解释空串或三个合法音符 token 的单空格分隔串；保留原空格宽松域未被覆盖的限制。'),
33:('COMPATIBLE','按零起始每三位排序，其余位置不变；只评分官方给定的可排序列表。'),
37:('COMPATIBLE','零起始偶数位置排序、奇数位置不变；数字列表共同域。'),
}


def read(p):return json.loads(Path(p).read_text())
def fsha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def relative(p):return str(Path(p).resolve().relative_to(REPO))


def source_hashes():
    return {relative(p):fsha(p) for p in [Path(__file__),WORKER,
        REPO/'FlowEvo/src/failure_evo/container_worker.py',REPO/'FlowEvo/src/failure_evo/persistent_budget.py',
        REPO/'FlowEvo/src/failure_evo/pilot_runtime.py']}


def check_prior():
    before=read(ROOT/'prior_runs_immutable.json')
    assert all(fsha(REPO/p)==h for p,h in before.items()),'PRIOR_RUN_CHANGED'
    return len(before)


def budget(stage,protocol_hash,tools,wall):
    return PersistentBudget(ROOT/(stage+'_budget.jsonl'),run_id='humaneval_plus_'+stage,protocol_hash=protocol_hash,
        max_calls=0,max_tokens=0,max_tools=tools,max_cost_microusd=0,token_rate_microusd_per_million=0,
        tool_cost_upper_microusd=0,max_tool_milliseconds=tools*185000,
        tool_milliseconds_upper=185000,wall_seconds=wall)


def run_worker(stage,job,request,b,source,problems,image):
    folder=PRIVATE/'executions'/stage/job;folder.mkdir(parents=True,exist_ok=True)
    identity=fingerprint(dict(source_sha256=hashlib.sha256(source).hexdigest(),problems=problems,request=request,image=image))
    receipt=folder/'receipt.json'
    if receipt.exists():
        saved=read(receipt);assert saved['identity']==identity
        return saved['result']
    key=stage+'/'+job
    if b.request_state(key):raise RuntimeError('PARTIAL_EXECUTION_NO_AUTOMATIC_REISSUE')
    candidate=folder/'solution.py';candidate.write_bytes(source)
    modules=folder/'inputs';modules.mkdir(exist_ok=True)
    (modules/'problems.jsonl').write_text(''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in problems))
    if request['mode']!='contracts':
        (modules/'samples.jsonl').write_text(json.dumps(dict(task_id=problems[0]['task_id'],solution=source.decode('utf-8')),ensure_ascii=False)+'\n')
    b.tool(job_id=key,capability='locked_evalplus',request_id=key,request_hash=identity)
    started=time.monotonic()
    with DockerWorker(candidate,image=image,worker_script=WORKER,module_dir=modules,timeout_limit=180) as worker:
        result=worker.call(dict(request,timeout=180))
    elapsed=time.monotonic()-started
    write_json(receipt,dict(identity=identity,source_sha256=hashlib.sha256(source).hexdigest(),
        image=image,request=request,seconds=elapsed,result=result))
    b.settle(key,tool_milliseconds=math.ceil(elapsed*1000),cost_microusd=0)
    return result


def prepare():
    OUT.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True);PRIVATE.chmod(0o700)
    check_prior()
    image=(ROOT/'image_id.txt').read_text().strip()
    all_data={r['task_id']:r for r in map(json.loads,(PRIVATE/'HumanEvalPlus-v0.1.10.jsonl').read_text().splitlines())}
    old=read(OLD_LOCK);public={r['problem_id']:r for r in read(OLD_MANIFEST)['tasks'] if r['data_role']=='train'}
    prior_scores={r['task_id']:r for r in read(OLD_REPORT)['tasks']}
    assert len(old)==len(public)==24 and set(public)=={r['task_id'] for r in old}
    locked=[];problems=[]
    for row in old:
        tid=row['task_id'];p=all_data[tid];original=public[tid]
        source=(REPO/row['source_ref']).read_bytes();trace=read(REPO/row['trace_ref'])
        assert source.decode('utf-8')==trace['attempts'][-1]['candidate_code']==trace['code_history'][-1]
        assert hashlib.sha256(source).hexdigest()==row['final_source_sha256']
        assert trace['validated_entry_point']==original['entry_point']==p['entry_point']
        assert original['prompt']==trace['query']==p['prompt'],'TASK_PROMPT_DIFF_REQUIRES_REVIEW'
        deps=read(REPO/row['dependencies_ref']);validate_bundle(deps)
        assert not deps.get('modules') and not deps.get('entries'),'NONEMPTY_DEPENDENCY_NEEDS_RESTORATION'
        dest=ROOT/'locked'/tid.replace('/','_');dest.mkdir(parents=True,exist_ok=True)
        (dest/'solution.py').write_bytes(source)
        shutil.copyfile(REPO/row['dependencies_ref'],dest/'dependencies.json')
        status,note=REVIEWS[int(tid.split('/')[1])]
        locked.append(dict(**row,locked_source_ref=relative(dest/'solution.py'),
            old_full_verdict=prior_scores[tid]['full_check_verdict'],
            old_full_receipt_ref=prior_scores[tid]['execution_receipt'],
            dependency_manifest_file_sha256=fsha(dest/'dependencies.json'),
            enhanced_task_sha256=fingerprint(p),compatibility=status,compatibility_review=note,
            enhanced_base_count=len(p['base_input']),enhanced_plus_count=len(p['plus_input']),atol=p['atol']))
        problems.append(p)
    subset=PRIVATE/'approved_24.jsonl';subset.write_text(''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in problems))
    contract_protocol=dict(stage='input_contracts_only_before_locked_program_evaluation',image=image,
        script_hashes=source_hashes(),dataset_sha256=fsha(subset),model_calls=0,max_executions=1,worker_seconds=180,wall_seconds=300)
    write_json(ROOT/'Contract_Check_Protocol.json',contract_protocol)
    b=budget('contracts',fingerprint(contract_protocol),1,300)
    result=run_worker('contracts','approved24',dict(mode='contracts'),b,b'pass\n',problems,image)
    if result.get('status')!='CONTRACTS_CHECKED':raise RuntimeError('CONTRACT_CHECK_FAILED:'+str(result.get('status')))
    for task in result['tasks']:
        for subset,compact in list(task['subsets'].items()):
            invalid=set(compact['official_contract_invalid'])
            excluded={i:reason for reason,indices in compact['common_scope_exclusions'].items() for i in indices}
            task['subsets'][subset]=[dict(index=i,official_contract=i not in invalid,common_scope=i not in excluded,
                reason=excluded.get(i,'within_reviewed_common_scope')) for i in range(compact['count'])]
    write_json(PRIVATE/'contract_details.json',result)
    for row in locked:
        d=next(x for x in result['tasks'] if x['task_id']==row['task_id'])
        row['case_qualification']={s:dict(planned=len(v),official_contract_pass=sum(x['official_contract'] for x in v),
            common_scope_count=sum(x['common_scope'] for x in v),exclusions=dict(Counter(x['reason'] for x in v if not x['common_scope']))) for s,v in d['subsets'].items()}
        if any(not x['official_contract'] for v in d['subsets'].values() for x in v):
            row['compatibility']='SCOPED_COMPATIBLE'
        row['input_contract_dimension']='case-level official predicates plus predeclared common-scope checks'
        row['expected_result_dimension']='official pinned reference and unchanged comparator; task-specific semantic review recorded; failed evidence needs separate confirmation'
        row['coverage_dimension']='available base and enhanced case counts, not independent source counts or universal correctness'
    write_json(ROOT/'locked_submissions.json',locked)
    write_json(OUT/'Compatibility_Manifest.json',dict(tasks=locked,contract_details_ref=relative(PRIVATE/'contract_details.json'),
        source_evaluation_started=False,selection='first qualified reusable source in original locked order, max two candidates; no requirement for multiple strata'))
    print(json.dumps(dict(prepared=len(locked),compatibility=dict(Counter(x['compatibility'] for x in locked)),contract_budget=b.snapshot()),ensure_ascii=False))


def freeze():
    check_prior()
    locked=read(ROOT/'locked_submissions.json')
    protocol=dict(name='locked-training-humaneval-plus-v1',created_utc=datetime.now(timezone.utc).isoformat(),
        image=(ROOT/'image_id.txt').read_text().strip(),scorer_version='EvalPlus v0.3.1',
        scorer_commit='e5d0ed0bab96280b60b637ec7f15b5e4841b0cb2',data_version='HumanEvalPlus v0.1.10',
        full_data_sha256=fsha(PRIVATE/'HumanEvalPlus-v0.1.10.jsonl'),subset_sha256=fsha(PRIVATE/'approved_24.jsonl'),
        compatibility_manifest_sha256=fsha(OUT/'Compatibility_Manifest.json'),contract_details_sha256=fsha(PRIVATE/'contract_details.json'),
        locked_submissions_sha256=fingerprint(locked),source_hashes=source_hashes(),
        task_ids=[r['task_id'] for r in locked],data_role='train',new_independent_evaluation_set=False,
        resources=dict(model_requests=0,model_usd=0,max_primary=24,max_failure_replays=24,max_worker_calls=48,
            wall_seconds=1800,worker_timeout_seconds=180,cpus=1,memory_mib=256,pids=32),
        options=dict(base_only=False,fast_check=False,min_time_limit=5.0,gt_time_limit_factor=4.0,
            official_per_subset_cap_seconds=62,random_seed=0,numpy_seed=0,python_hash_seed=0,
            comparator='unmodified EvalPlus: exact equality; float atol default 1e-6 when atol=0, rtol=1e-7'),
        replay_rule='At most one: first failed common-scope input in base then plus order; if none, no replay. Same source bytes/input/image, diagnostic not replacement score.',
        no_sanitize=True,solution_field=True,no_prompt_concatenation_to_submission=True,
        main_interfaces=['official stream_jsonl/load_solutions','official trusted_exec reference','official untrusted_check'],
        learning_projection=['original public prompt','actual source','allowed public feedback','binary training verdict','evidence ID'],
        forbidden_projection=['private inputs','expected outputs','reference implementation','private executed_code','private feedback object'],
        selection='original locked order; first audited reusable source with independent support and future task feasibility; at most 2',
        reserved_runs_unchanged=True)
    protocol['protocol_sha256']=fingerprint(protocol)
    write_json(ROOT/'protocol.json',protocol)
    write_json(OUT/'Scoring_Protocol.json',protocol)
    print(json.dumps(dict(protocol_sha256=protocol['protocol_sha256'],primary=24,replay_max=24,wall_seconds=1800,model_calls=0)))


def run():
    p=read(ROOT/'protocol.json');assert fingerprint({k:v for k,v in p.items() if k!='protocol_sha256'})==p['protocol_sha256']
    assert source_hashes()==p['source_hashes']
    for file,key in [(PRIVATE/'approved_24.jsonl','subset_sha256'),(PRIVATE/'contract_details.json','contract_details_sha256'),(OUT/'Compatibility_Manifest.json','compatibility_manifest_sha256')]:assert fsha(file)==p[key]
    locked=read(ROOT/'locked_submissions.json');assert fingerprint(locked)==p['locked_submissions_sha256']
    problems={x['task_id']:x for x in map(json.loads,(PRIVATE/'approved_24.jsonl').read_text().splitlines())}
    scopes={x['task_id']:x for x in read(PRIVATE/'contract_details.json')['tasks']}
    assert set(problems)==set(p['task_ids'])
    b=budget('evaluation',p['protocol_sha256'],48,1800)
    progress=read(ROOT/'enhanced_progress.json') if (ROOT/'enhanced_progress.json').exists() else []
    status='EXCEPTION_STOP';stage='not_started';error=None
    try:
        for row in locked:
            tid=row['task_id'];stage=tid
            if any(x['task_id']==tid for x in progress):continue
            source=(REPO/row['locked_source_ref']).read_bytes();assert hashlib.sha256(source).hexdigest()==row['final_source_sha256']
            result=run_worker('primary',tid.replace('/','_'),dict(mode='score'),b,source,[problems[tid]],p['image'])
            item=dict(task_id=tid,final_source_sha256=row['final_source_sha256'],dependency_bundle_sha256=row['dependency_bundle_sha256'],
                scoring_suite_sha256=p['subset_sha256'],public_verdict=row['public_verdict'],old_full_verdict=row['old_full_verdict'],
                compatibility=row['compatibility'],case_qualification=row['case_qualification'],
                raw_status=result['status'],new_base=result.get('subsets',{}).get('base'),new_plus=result.get('subsets',{}).get('plus'),
                private_receipt_ref=relative(PRIVATE/'executions/primary'/tid.replace('/','_')/'receipt.json'))
            failures=[]
            for subset in ('base','plus'):
                raw=result.get('subsets',{}).get(subset,{})
                eligible={x['index'] for x in scopes[tid]['subsets'][subset] if x['common_scope']}
                failures += [(subset,i) for i in raw.get('failed_indices',[]) if i in eligible]
            item['common_scope_failed_count']=len(failures)
            if failures:
                subset,index=failures[0]
                replay=run_worker('replay',tid.replace('/','_'),dict(mode='replay',subset=subset,index=index),b,source,[problems[tid]],p['image'])
                item['replay_ref']=relative(PRIVATE/'executions/replay'/tid.replace('/','_')/'receipt.json')
                item['replay_outcome']=replay.get('outcome',replay['status'])
                item['replay_seconds']=replay.get('seconds')
                item['replay_exact_equal']=replay.get('exact_equal')
            item['evidence_qualification']=dict(evidence_valid=False,acquisition_eligible=False,
                compatibility=row['compatibility'],input_contract_valid=bool(failures),expected_result_trusted=False,
                reproduced=bool(failures and item.get('replay_outcome') in {'TIMEOUT','RUNTIME_ERROR'} or failures and item.get('replay_exact_equal') is False),
                reason='requires post-score oracle/error/reuse review' if failures else 'no_common_scope_failure')
            progress.append(item);write_json(ROOT/'enhanced_progress.json',progress)
            write_json(OUT/'Enhanced_Scores.json',dict(protocol_sha256=p['protocol_sha256'],status='RUNNING',tasks=progress))
            print(tid,result['status'],result.get('subsets',{}).get('base',{}).get('status'),result.get('subsets',{}).get('plus',{}).get('status'),'common failures',len(failures),flush=True)
        status='COMPLETED'
    except BaseException as exc:
        error=type(exc).__name__
        status='INTERRUPTED' if isinstance(exc,KeyboardInterrupt) else 'BUDGET_STOP' if 'budget' in str(exc).lower() or 'deadline' in str(exc).lower() else 'EXCEPTION_STOP'
        raise
    finally:
        value=dict(protocol_sha256=p['protocol_sha256'],status=status,tasks=progress,budget=b.snapshot(),
            source_count=len(progress),model_requests=0,prior_run_files_unchanged=check_prior(),current_task=stage,error_type=error)
        write_json(OUT/'Enhanced_Scores.json',value)
        write_json(ROOT/'stop_snapshot.json',value)
    return value


if __name__=='__main__':
    os.chdir(REPO)
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','freeze','run']);args=parser.parse_args()
    {'prepare':prepare,'freeze':freeze,'run':run}[args.stage]()
