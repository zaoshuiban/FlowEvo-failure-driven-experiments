"""Regrade all saved candidates. No API/client/key imports, immutable originals."""
import argparse
import ast
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import threading
import time
from comparison import solver_feedback, stdio_equal, structured_equal
from contracts import VALIDATED
from preflight import preflight
from sandbox import Worker
from semantic import accepts

LOCK=threading.Lock()


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2));tmp.replace(path)


def evaluate(task,policy,pre,cases,code_path):
    text=code_path.read_text();base={'task_id':task['task_id'],'valid_tests':len(cases),
        'total_tests':pre.get('total_cases',0),'invalid_tests':len(pre.get('invalid_cases',[])),
        'reference_corrections':len(pre.get('reference_corrections',[])),
        'input_coverage':pre.get('input_coverage'),'code_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'tests_passed':0,'executed':False}
    if pre['status']!='READY':return dict(base,status=pre['status'])
    if not text.strip():return dict(base,status='NO_COMPLETE_CODE')
    try:ast.parse(text)
    except SyntaxError as exc:return dict(base,status='COMPILE_ERROR',error=str(exc))
    seconds=4 if task['dataset']=='taco' else 6
    start=time.monotonic()
    with Worker(code_path) as worker:
        if not task.get('function_name'):
            response=worker.call({'mode':'compile_stdio','timeout':seconds})
            if response['status']!='OK':return dict(base,status=response['status'],diagnostic=response)
        base['executed']=True
        for case in cases:
            request={'mode':'function' if task.get('function_name') else 'stdio','timeout':seconds}
            if task.get('function_name'):request.update(function=task['function_name'],args=case['input'])
            else:request['input']=case['input']
            response=worker.call(request)
            if response['status']!='OK':
                return dict(base,status=response['status'],failed_test_index=case['index'],diagnostic=response,seconds=time.monotonic()-start)
            actual=response['value'] if task.get('function_name') else response['output']
            if policy['comparison']=='semantic':ok=accepts(task['task_id'],case['semantic_data'],actual)
            elif task.get('function_name'):ok=structured_equal(actual,case['expected'],policy)
            else:ok=stdio_equal(actual,case['expected'],policy)
            if not ok:
                return dict(base,status='WRONG_ANSWER',failed_test_index=case['index'],
                            actual_preview=str(actual)[:2000],expected_preview=str(case['expected'])[:2000],seconds=time.monotonic()-start)
            base['tests_passed']+=1
    return dict(base,status='PASS',seconds=time.monotonic()-start)


def process(args,old_path,policies,frozen):
    old=json.loads(old_path.read_text());tid=old['task_id'];policy=policies[tid]
    task_path=args.source/'data/tasks'/(tid+'.json');raw=task_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=policy['task_sha256']:raise RuntimeError('task changed: '+tid)
    task=json.loads(raw);pre,cases=preflight(task,policy);write(args.output/'preflight'/(tid+'.json'),pre)
    results=[]
    for attempt in old['attempts']:
        stage=attempt['stage'];dest=args.output/'verdicts'/tid/(stage+'.json');code_path=old_path.parent/(stage+'.py')
        frozen_attempt=frozen[(tid,stage)]
        if hashlib.sha256(code_path.read_bytes()).hexdigest()!=frozen_attempt['code_sha256']:raise RuntimeError('code changed: '+tid+stage)
        if dest.exists():verdict=json.loads(dest.read_text())
        else:
            verdict=evaluate(task,policy,pre,cases,code_path);verdict.update(stage=stage,old_passed=attempt['passed'],old_feedback=attempt['feedback'])
            verdict['solver_feedback']=solver_feedback(verdict);write(dest,verdict)
        results.append(verdict)
    summary={'task_id':tid,'dataset':old['dataset'],'difficulty':old['difficulty'],
             'old_first_pass':old['first_pass'],'old_final_pass':old['passed'],
             'new_first_status':results[0]['status'],'new_original_final_status':results[-1]['status'],
             'any_saved_candidate_pass':any(v['status']=='PASS' for v in results),
             'first_passing_saved_stage':next((v['stage'] for v in results if v['status']=='PASS'),None),
             'attempts':len(results),'invalid_cases':len(pre.get('invalid_cases',[])),
             'reference_corrections':len(pre.get('reference_corrections',[])),
             'input_coverage':pre.get('input_coverage'),'preflight_status':pre['status']}
    write(args.output/'tasks'/(tid+'.json'),summary)
    with LOCK:print(tid,pre['status'],summary['new_original_final_status'],'attempts',len(results),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);parser.add_argument('--workers',type=int,default=2);parser.add_argument('--only',nargs='*');args=parser.parse_args()
    policies=json.loads((args.output/'policies.json').read_text());inventory=json.loads((args.output/'frozen_inventory.json').read_text());frozen={(r['task_id'],r['stage']):r for r in inventory}
    files=sorted(args.source.glob('runs/*/*/result.json'))
    if args.only:files=[f for f in files if f.parent.name in args.only]
    code_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path(__file__).resolve().parent.glob('*.py')}
    manifest={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'code_hashes':code_hashes,'policies_sha256':hashlib.sha256((args.output/'policies.json').read_bytes()).hexdigest(),'tasks':len(files),'expected_candidates':sum(len(json.loads(f.read_text())['attempts']) for f in files),'new_model_calls':0,'workers':args.workers}
    write(args.output/'run_manifest.json',manifest)
    errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(process,args,f,policies,frozen):f for f in files}
        for future in concurrent.futures.as_completed(futures):
            try:future.result()
            except BaseException as exc:errors.append({'file':str(futures[future]),'error':repr(exc)});print('ERROR',errors[-1],flush=True)
    write(args.output/'run_errors.json',errors)
    print('COMPLETE' if not errors else 'COMPLETED_WITH_ERRORS',len(files),len(errors),flush=True)


if __name__=='__main__':main()
