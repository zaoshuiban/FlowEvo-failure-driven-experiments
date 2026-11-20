"""Freeze -> A/B twice -> at most one profile; zero model requests."""
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO/'FlowEvo/src'))
from failure_evo.container_worker import DockerWorker
from failure_evo.contracts import fingerprint
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.pilot_runtime import write_json
from failure_evo.skill_runtime import validate_bundle, materialize, check_source

OLD = REPO/'runs/humaneval_plus_locked_20261120'
ROOT = REPO/'runs/existing_capability_performance_20261120'
OUT = REPO/'reports/existing_capability_performance_20261120'
WORKER = REPO/'scripts/existing_capability_performance_worker.py'
SCORER = REPO/'scripts/locked_evalplus_worker.py'

def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rel(path): return str(Path(path).relative_to(REPO))

def last_fn(source, name):
    return [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == name][-1]

def check_prior():
    before = read(ROOT/'prior_files.json')
    assert all(sha(REPO/p) == h for p,h in before.items()), 'HISTORICAL_FILE_CHANGED'
    return len(before)

def prepare():
    assert not (ROOT/'protocol.json').exists(), 'ALREADY_FROZEN'
    ROOT.mkdir(parents=True, exist_ok=True)
    private = ROOT/'private'; private.mkdir(exist_ok=True); private.chmod(0o700)
    before = read(OLD/'prior_runs_immutable.json')
    for directory in [OLD, REPO/'reports/humaneval_plus_locked_20261120']:
        before.update({rel(p):sha(p) for p in directory.rglob('*') if p.is_file()})
    write_json(ROOT/'prior_files.json', before); check_prior()
    old = read(OLD/'protocol.json')
    assert all(sha(REPO/p) == h for p,h in old['source_hashes'].items()), 'ENVIRONMENT_NOT_COMPARABLE'
    info = json.loads(subprocess.check_output(['docker','image','inspect',old['image']], timeout=10))[0]
    assert info['Id'] == old['image'] and info['Architecture'] == 'arm64' and info['Os'] == 'linux'
    write_json(ROOT/'image_identity.json', {k:info[k] for k in ('Id','Architecture','Os','Created')})
    locks = {x['task_id']:x for x in read(OLD/'locked_submissions.json')}
    a = (REPO/locks['HumanEval/39']['locked_source_ref']).read_text()
    assert hashlib.sha256(a.encode()).hexdigest() == 'e6db5b426a719c3d35d681793ccc16609bf5e9742bed2ee562da72efe562d7f5'
    row31 = locks['HumanEval/31']; original31 = (REPO/row31['locked_source_ref']).read_text()
    assert hashlib.sha256(original31.encode()).hexdigest() == row31['final_source_sha256']
    card = next(c for c in read(REPO/'runs/failure_acquisition_pilot_20261120/real_01/G/skills/registry.json') if c['validated_entry_point']=='is_prime')
    module_source = (REPO/card['code_path']).read_text()
    assert sha(REPO/card['code_path']) == card['source_sha256']
    assert ast.dump(last_fn(module_source,'is_prime'),include_attributes=False)==ast.dump(last_fn(original31,'is_prime'),include_attributes=False)
    deps39=read(REPO/locks['HumanEval/39']['dependencies_ref']); deps31=read(REPO/row31['dependencies_ref'])
    for deps, lock in [(deps39,locks['HumanEval/39']),(deps31,row31)]:
        validate_bundle(deps); assert fingerprint(deps)==lock['dependency_bundle_sha256']
        assert not deps['modules'] and not deps['entries']
    assert card['executable_dependencies']==deps31
    check_source(module_source)
    fn=last_fn(a,'prime_fib'); inner=fn.body[0]
    assert isinstance(inner,ast.FunctionDef) and inner.name=='is_prime'
    lines=a.splitlines(keepends=True)
    binding='    from flowevo_skills import archived_is_prime as is_prime\n'
    b=''.join(lines[:inner.lineno-1])+binding+''.join(lines[inner.end_lineno:])
    assert ast.dump(ast.Module(body=fn.body[1:],type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=last_fn(b,'prime_fib').body[1:],type_ignores=[]),include_attributes=False)
    module='_frozen_'+card['source_sha256']
    bundle=dict(modules={module:dict(source=module_source,sha256=card['source_sha256'])},
        entries={'archived_is_prime':dict(module=module,entry='is_prime',skill_id=card['skill_id'],
            version=card['source_sha256'],sha256=card['source_sha256'],contract={'scope':'archived integer primality predicate; diagnostic binding only'})},
        card_names={card['skill_id']:'archived_is_prime'})
    validate_bundle(bundle)
    for arm,source,deps in [('A',a,deps39),('B',b,bundle)]:
        folder=ROOT/'locked'/arm; folder.mkdir(parents=True,exist_ok=True)
        (folder/'source.py').write_text(source); write_json(folder/'dependencies.json',deps)
    (ROOT/'locked/original31.py').write_text(original31)
    (ROOT/'locked/compiled31.py').write_text(module_source)
    problems=[p for p in map(json.loads,(OLD/'private/approved_24.jsonl').read_text().splitlines()) if p['task_id']=='HumanEval/39']
    assert len(problems)==1
    (private/'problem.jsonl').write_text(json.dumps(problems[0],ensure_ascii=False)+'\n')
    old_replay=read(OLD/'private/executions/replay/HumanEval_39/receipt.json')
    write_json(private/'diagnostic_case.json',{k:old_replay['request'][k] for k in ['subset','index']})
    public=next(x for x in read(REPO/'reports/failure_acquisition_pilot_20261120/Pilot_Data_Manifest.json')['tasks'] if x['problem_id']=='HumanEval/39')
    assert problems[0]['prompt']==public['prompt']
    write_json(ROOT/'public_task.json',public)
    protocol=dict(name='HumanEval39-existing-capability-performance-v1',created_utc=datetime.now(timezone.utc).isoformat(),
        image=old['image'],prior_protocol=old['protocol_sha256'],
        task='HumanEval/39',problem_sha256=sha(private/'problem.jsonl'),
        cases={k:len(problems[0][k+'_input']) for k in ['base','plus']},
        original39=locks['HumanEval/39'],original31=row31,native31_card=card,
        versions={arm:dict(source_sha256=sha(ROOT/'locked'/arm/'source.py'),dependencies_sha256=fingerprint(read(ROOT/'locked'/arm/'dependencies.json'))) for arm in ['A','B']},
        host_composition_only=True,new_algorithm_or_actor_source_generated=False,
        composition='Replace only local is_prime definition by a frozen module import. Remaining prime_fib AST and bytes unchanged.',
        score_order=['A1','B1','B2','A2'],scorer_options=old['options'],
        profile_rule='At most once, B same prior failed input for five seconds, only if both B runs fail with real bound calls; never a scoring substitute.',
        limits=dict(model_calls=0,new_inputs=0,per_version_repeats=2,worker_jobs=12,profile_jobs=1,wall_seconds=900,
            cpus=1,memory_mib=256,pids=32,case_seconds=5,worker_supervisor_seconds=180),
        source_hashes={rel(p):sha(p) for p in [Path(__file__),WORKER,SCORER,REPO/'FlowEvo/src/failure_evo/container_worker.py',REPO/'FlowEvo/src/failure_evo/persistent_budget.py',REPO/'FlowEvo/src/failure_evo/skill_runtime.py']})
    protocol['protocol_sha256']=fingerprint(protocol)
    write_json(ROOT/'protocol.json',protocol); write_json(OUT/'Existing_Capability_Performance_Protocol.json',protocol)
    (OUT/'Existing_Capability_Performance_Protocol.md').write_text(f'''# 既有能力性能诊断冻结协议

协议 SHA256：`{protocol['protocol_sha256']}`。

只比较 HumanEval/39：A 为原始 UTF-8 源码；B 只把局部素性判断绑定到 HumanEval/31 真实编译模块。B 是宿主辅助的组合上界诊断，不是 Actor 自主复用，也不准入任何技能。

实际执行顺序 A1、B1、B2、A2；各运行原 HumanEval/39 的全部 10 个基础、2 个增强案例，不新增输入。原单案例 5 秒规则、官方比较器、随机种子 0、原镜像、1 CPU / 256 MiB / 32 PID 保持一致。B 两次仍失败且存在真实模块调用时，最多增加一次在原失败输入上的 5 秒 cProfile 诊断；其计时不替代正式评分。

硬上限：0 模型请求、0 新算法源码、0 新独立任务；每版最多 2 次，隔离作业最多 12 个、诊断最多 1 个，实际执行窗口 900 秒。新增的 B 文本仅为明确授权的模块接线。所有执行均在无网络、只读 Docker 中；记录原始调用回执，私有参数和期望值不进入模型或编译输入。

身份、归档回执、依赖及脚本哈希见同名 JSON。缺失原环境即停止，结论 ENVIRONMENT_NOT_COMPARABLE；组合不成立则不推断算法性能。完成后结案，不修订候选或扩展测试。
''')
    print(json.dumps(dict(status='FROZEN',protocol_sha256=protocol['protocol_sha256'],versions=protocol['versions']),ensure_ascii=False))

def run(resume=False):
    p=read(ROOT/'protocol.json'); assert fingerprint({k:v for k,v in p.items() if k!='protocol_sha256'})==p['protocol_sha256']
    hashes=read(ROOT/'logging_addendum.json')['source_hashes'] if resume else p['source_hashes']
    assert all(sha(REPO/k)==v for k,v in hashes.items())
    check_prior()
    budget=PersistentBudget(ROOT/'budget.jsonl',run_id='existing-capability39',protocol_hash=p['protocol_sha256'],
        max_calls=0,max_tokens=0,max_tools=12,max_cost_microusd=0,token_rate_microusd_per_million=0,
        tool_cost_upper_microusd=0,max_tool_milliseconds=900000,tool_milliseconds_upper=185000,wall_seconds=900)
    progress=read(ROOT/'progress.json') if resume else []; status='STOPPED'; error=None
    if resume:
        invalid=ROOT/'private/executions/B1/receipt.json'
        saved=read(invalid)
        assert not saved['result']['skill_events'] and budget.request_state('B1')['status']=='settled'
        progress.append(dict(job='B1',arm='B',receipt_ref=rel(invalid),receipt_sha256=sha(invalid),
            formal_score_valid=False,classification='BINDING_LOG_ERROR_BEFORE_OPERATION',
            worker_seconds=saved['seconds'],result={k:v for k,v in saved['result'].items() if k!='skill_events'},
            call_counts=dict(started=0,returned=0,error=0),call_errors=[]))
    def execute(job,arm,mode):
        if budget.request_state(job):raise RuntimeError('NO_AUTOMATIC_REISSUE')
        source=ROOT/'locked'/arm/'source.py'; bundle=read(ROOT/'locked'/arm/'dependencies.json')
        assert sha(source)==p['versions'][arm]['source_sha256'] and fingerprint(bundle)==p['versions'][arm]['dependencies_sha256']
        folder=ROOT/'private/executions'/job; modules=folder/'modules'; modules.mkdir(parents=True)
        materialize(bundle,modules,event_path='/tmp/skill_events.jsonl')
        shutil.copyfile(ROOT/'private/problem.jsonl',modules/'problems.jsonl');shutil.copyfile(SCORER,modules/'locked_evalplus_worker.py')
        (modules/'samples.jsonl').write_text(json.dumps(dict(task_id='HumanEval/39',solution=source.read_text()))+'\n')
        request=dict(mode=mode,timeout=180)
        if mode=='profile':request.update(read(ROOT/'private/diagnostic_case.json'))
        identity=fingerprint(dict(source_sha256=sha(source),bundle=bundle,request=request,problem_sha256=p['problem_sha256'],image=p['image']))
        budget.tool(job_id=job,capability='existing_capability_diagnostic',request_id=job,request_hash=identity)
        start=time.monotonic()
        with DockerWorker(source,image=p['image'],worker_script=WORKER,module_dir=modules,timeout_limit=180) as worker:
            result=worker.call(request)
        elapsed=time.monotonic()-start
        write_json(folder/'receipt.json',dict(job=job,arm=arm,request=request,identity=identity,seconds=elapsed,result=result))
        budget.settle(job,tool_milliseconds=math.ceil(elapsed*1000),cost_microusd=0)
        if result['status'] not in {'COMPLETED','PROFILE_COMPLETED'}:raise RuntimeError('EVIDENCE_INSUFFICIENT:'+result['status'])
        events=result['skill_events']
        if arm=='B' and not any(e['event']=='started' and e['sha256']==p['native31_card']['source_sha256'] for e in events):
            raise RuntimeError('COMPOSITION_NOT_ESTABLISHED')
        safe={k:v for k,v in result.items() if k!='skill_events'}
        record=dict(job=job,arm=arm,formal_score_valid=True,receipt_ref=rel(folder/'receipt.json'),receipt_sha256=sha(folder/'receipt.json'),
            worker_seconds=elapsed,result=safe,call_counts={k:sum(e['event']==k for e in events) for k in ['started','returned','error']},
            call_errors=sorted({e.get('error_type','') for e in events if e['event']=='error'}))
        progress.append(record);write_json(ROOT/'progress.json',progress)
        print(json.dumps(dict(job=job,subsets={k:v['status'] for k,v in result.get('subsets',{}).items()},calls=record['call_counts'],errors=record['call_errors']),ensure_ascii=False),flush=True)
        return record
    try:
        for job in p['score_order']:
            if any(x['job']==job for x in progress):continue
            execute(job,job[0],'score')
        b=[x for x in progress if x['arm']=='B' and x.get('formal_score_valid',True)]
        if b and all(any(s['status']!='pass' for s in x['result']['subsets'].values()) for x in b):execute('B_profile','B','profile')
        status='COMPLETED'
    except BaseException as exc:
        error=type(exc).__name__+': '+str(exc)
        raise
    finally:
        value=dict(status=status,error=error,protocol_sha256=p['protocol_sha256'],jobs=progress,budget=budget.snapshot(),
            old_files_unchanged=check_prior(),new_model_requests=0)
        write_json(ROOT/'stop_snapshot.json',value);write_json(OUT/'Existing_Capability_Performance.json',value)

if __name__=='__main__':
    os.chdir(REPO)
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','run','resume_logging']);a=parser.parse_args()
    {'prepare':prepare,'run':run,'resume_logging':lambda:run(resume=True)}[a.stage]()
