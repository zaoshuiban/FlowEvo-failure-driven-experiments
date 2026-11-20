"""Native G/R development diagnostic; preparation sends zero model requests."""
import argparse
import ast
import copy
from datetime import datetime,timezone,timedelta
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time

REPO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(REPO/'FlowEvo/src'),str(REPO/'scripts')]
from agent.generator import LLMGenerator
from core.schemas import PrimitiveCard
from eval.runner import BenchmarkRunner,RunnerConfig
from eval.verifier import verify_task
from failure_evo.contracts import fingerprint
from failure_evo.container_worker import DockerWorker
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.pilot_data import public_examples,task_from_manifest
from failure_evo.pilot_runtime import PilotTransport,PilotStop,IsolatedCodeSandbox,write_json,save_stop_snapshot
from failure_evo.skill_runtime import sha,check_source,materialize,bundle_from_cards,logger_identity
from runtime.config import RuntimeLLMConfig,GenerationSettings,SkillContextBudgets
from run_failure_acquisition_pilot import paths,snapshot,tree_hash,trace_of

ROOT=REPO/'runs/autonomous_reuse_20261120';OUT=REPO/'reports/autonomous_reuse_20261120'
BASE=REPO/'runs/failure_acquisition_pilot_20261120/real_01/G'
OLD=REPO/'runs/humaneval_plus_locked_20261120'
WORKER=REPO/'scripts/autonomous_reuse_scoring_worker.py'
SCORER=REPO/'scripts/locked_evalplus_worker.py'
IDS=[39,75,96,72]
EXAMPLES={75:[('is_multiply_prime(30)','True')],
 96:[('count_up_to(5)','[2,3]'),('count_up_to(11)','[2,3,5,7]'),('count_up_to(0)','[]'),('count_up_to(20)','[2,3,5,7,11,13,17,19]'),('count_up_to(1)','[]'),('count_up_to(18)','[2,3,5,7,11,13,17]')],
 72:[('will_it_fly([1, 2], 5)','False'),('will_it_fly([3, 2, 3], 1)','False'),('will_it_fly([3, 2, 3], 9)','True'),('will_it_fly([3], 5)','True')],
 92:[('any_int(5, 2, 7)','True'),('any_int(3, 2, 2)','False'),('any_int(3, -2, 1)','True'),('any_int(3.6, -2.2, 2)','False')]}
def read(p):return json.loads(Path(p).read_text())
def fsha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(REPO))
def integrity():
    before=read(ROOT/'prior_files.json');assert all(fsha(REPO/p)==h for p,h in before.items()),'HISTORY_CHANGED'
    return len(before)
def code_hashes():
    files=list((REPO/'FlowEvo/src').rglob('*.py'))+[Path(__file__),WORKER,SCORER,REPO/'scripts/run_failure_acquisition_pilot.py']
    return {rel(p):fsha(p) for p in sorted(files)}
def task_of(row):
    task=task_from_manifest(row)
    if row['problem_id']=='HumanEval/39':
        source=(OLD/'locked/HumanEval_39/solution.py').read_text()
        task.metadata['resume_public_failure']=dict(source=source,source_sha256=sha(source),
            summary='The archived program failed independent training validation by exceeding a five-second case limit. Specific private inputs and expected values are unavailable.',
            evidence_id='humaneval39-locked-enhanced-repeated-timeout')
    return task
def native(root,cfg,client,box,arm):
    s=GenerationSettings(0,cfg['actor']['output_tokens'])
    rt=RuntimeLLMConfig('deepseek','','https://api.deepseek.com',cfg['actor']['model'],'FlowEvo-reuse',3,
        SkillContextBudgets(4096,4096,1536,1536),s,s,'development_reuse','')
    r=BenchmarkRunner(RunnerConfig(**paths(root),executable_skills_enabled=True,
        development_callable_catalog_path=str(ROOT/'Callable_Catalog.json') if arm=='R' else ''),
        dynamic_generator=LLMGenerator(rt,client),sandbox=box)
    assert r.executor.max_repairs==2
    return r

def prepare():
    assert not (OUT/'Frozen_Config.json').exists(),'ALREADY_FROZEN'
    ROOT.mkdir(exist_ok=True);OUT.mkdir(parents=True,exist_ok=True);integrity()
    private=ROOT/'private';private.mkdir(exist_ok=True);private.chmod(0o700)
    cfg=read(REPO/'configs/failure_acquisition_pilot.json')
    all_rows={r['task_id']:r for r in map(json.loads,gzip.open(cfg['dataset_path'],'rt'))}
    plus={r['task_id']:r for r in map(json.loads,(OLD/'private/HumanEvalPlus-v0.1.10.jsonl').read_text().splitlines())}
    old_manifest=read(REPO/'reports/failure_acquisition_pilot_20261120/Pilot_Data_Manifest.json')
    sealed={r['problem_id'] for r in old_manifest['tasks'] if r['data_role']=='transfer_dev'}
    tasks=[]
    for n in IDS:
        tid='HumanEval/'+str(n);row=all_rows[tid];assert tid not in sealed and plus[tid]['prompt']==row['prompt']
        examples=public_examples(row['prompt'],row['entry_point']) if n==39 else [dict(source=a,expected_literal=b,assertion=f'assert ({a}) == {b}') for a,b in EXAMPLES[n]]
        for e in examples:
            ast.literal_eval(e['expected_literal']);ast.parse(e['assertion'])
            # The equation/arrow spelling alone differs from the public docstring.
            assert ''.join(e['source'].split()) in ''.join(row['prompt'].split())
        tasks.append(dict(problem_id=tid,data_role='train' if n==39 else 'transfer_dev',source_lineage_id=tid,duplicate_group_id=tid,
            capability_family_id='number_theory' if n in (39,75,96) else 'ordinary_control',
            exposure_status='previously_discussed_development',source='original HumanEval task; no generated variant',
            prompt=row['prompt'],entry_point=row['entry_point'],examples=examples,
            public_example_origin='original docstring literal examples only; arrow/equality converted to assert',
            compatibility='SCOPED_COMPATIBLE' if n==92 else 'COMPATIBLE',
            contract_review={39:'Same previously audited shared domain; exact integer comparison.',75:'a<100; multiplication of exactly three primes, with repetition allowed.',96:'Public examples fix primes strictly below n; n is nonnegative.',72:'Numeric list palindrome and total weight <= w.',92:'Type-int convention; bool cases are recorded separately because original prose does not define bool-as-int semantics.'}[n]))
    write_json(ROOT/'Data_Manifest.json',dict(tasks=tasks,roles='exposed development only',independence_review='Distinct authored responsibilities; 39 sequence selection, 75 prime product, 96 prime enumeration; 72 ordinary control. No claim of pretraining exclusion.',
        excluded=[dict(task_id='HumanEval/92',reason='Original prose does not settle whether bool counts as an integer, while the enhanced contract allows bool. Excluded before any Actor run rather than using ambiguous outcomes for paired success.')]))
    for row in tasks:
        (private/(row['problem_id'].replace('/','_')+'.jsonl')).write_text(json.dumps(plus[row['problem_id']],ensure_ascii=False)+'\n')
    cards=[];catalog_dir=ROOT/'development_candidates';catalog_dir.mkdir(exist_ok=True)
    for c in read(BASE/'skills/registry.json'):
        if c['status']!='active' or not c.get('validated_entry_point'):continue
        source=(REPO/c['code_path']).read_text();assert sha(source)==c['source_sha256'];check_source(source)
        entry=c['validated_entry_point'];fn=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==entry][-1]
        pid='development_'+c['skill_id'];path=catalog_dir/(pid+'.py');path.write_text(source)
        contract=dict(purpose=ast.get_docstring(fn) or c['description'],parameters=c['signature']['args'],
            preconditions='The original public function contract applies; no claimed performance outside verified domains.',output=c['signature'].get('returns','as documented'),side_effects='as in the frozen archived program',failure='ordinary Python error or caller timeout; no fallback algorithm')
        card=PrimitiveCard(primitive_id=pid,name=entry+'_archived_operation',description=contract['purpose'],
            benchmark=c['family'],task_pattern=c['preconditions']['task_pattern'],helper_name=entry,target_entry_point=entry,
            signature={'args':c['signature']['args'],'returns':c['signature'].get('returns')},code_path=str(path),
            source_trace_ids=c.get('source_trace_ids',[]),source_skill_ids=[c['skill_id']],support_count=1,utility=1,status='draft',
            independent_source_ids=c['independent_source_ids'],source_sha256=c['source_sha256'],executable_dependencies=c['executable_dependencies'],
            operation_contracts={entry:contract},validation_status='source_verified_dependency_checked')
        cards.append(card.model_dump(mode='json'))
    write_json(ROOT/'Callable_Catalog.json',dict(scope='development_diagnostic',selection='all active native Python function cards; no target-specific choice; retrieve with unchanged Retriever',cards=cards))
    cfg.update(run_root=rel(ROOT/'real_01'),reports=rel(OUT),initial_library=rel(BASE),initial_library_sha256=tree_hash(BASE),
        image=read(OLD/'protocol.json')['image'],status='PREPARATION_ZERO_MODELS',
        absolute_deadline_utc=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat())
    cfg['budget'].update(actor_solve_calls=24,actor_strategy_calls=8,actor_calls=32,teacher_calls=0,
        max_tokens=32*49152,max_usd=2,executions=128,wall_seconds=3600,
        model_rates={'actor':[300000,1200000],'teacher':[1320000,3960000]},
        price_source='https://api-docs.deepseek.com/quick_start/pricing/',price_checked=datetime.now(timezone.utc).isoformat())
    cfg['protocol']=dict(task_ids=[x['problem_id'] for x in tasks],groups=['G','R'],attempts_per_task_arm=3,
        source_kind='ACTOR_SELECTED_REUSE diagnostic, never NEW_SKILL_ACQUIRED',
        resume_task='HumanEval/39',teacher_calls=0,oracle_candidate_presented=False,
        snapshots='identical complete G base per task/arm; native success learning retained within task, never fed into later tasks',
        retrieval='unchanged whole-program Retriever and thresholds; all retrieved eligible active functions exposed as development-only draft callables in R; no manual insert',
        scoring='All final programs locked before independent EvalPlus base+plus scoring; only public verification informs normal repairs; no private input/result given to Actor',
        ablation='After all programs frozen, at most one public validation per returned operation in each R final program; replace only that operation return by None. At most 25 jobs overall.',
        no_task_replacement=True,unknown_delivery_stop=True)
    cfg['request_price_upper_usd']=32*(32768*.30+16384*1.20)/1000000
    write_json(ROOT/'Prepared_Config.json',cfg)
    print(json.dumps(dict(tasks=len(tasks),development_cards=len(cards),model_requests=0),ensure_ascii=False))

def budget(cfg,root,preflight=False):
    b=cfg['budget'];return PersistentBudget(root/'budget.jsonl',run_id=root.name,
        protocol_hash=cfg.get('protocol_sha256','zero-model-preflight-v1'),max_calls=0 if preflight else b['actor_calls'],
        max_tokens=0 if preflight else b['max_tokens'],max_tools=8 if preflight else b['executions'],
        max_cost_microusd=0 if preflight else b['max_usd']*1000000,token_rate_microusd_per_million=1200000,
        tool_cost_upper_microusd=0,max_tool_milliseconds=1800000,tool_milliseconds_upper=185000,
        wall_seconds=1800 if preflight else b['wall_seconds'],model_rates=b['model_rates'])

def isolated(root,b,job,source,bundle,problems,mode='score'):
    key='private/'+job;folder=root/'private/executions'/job
    identity=fingerprint(dict(source=source,bundle=bundle,problems=problems,mode=mode,logger=logger_identity(),worker_sha256=fsha(WORKER)))
    receipt=folder/'receipt.json'
    if receipt.exists():
        saved=read(receipt);assert saved['identity']==identity;return saved
    if b.request_state(key):raise PilotStop('PARTIAL_WORKER_NO_REISSUE')
    modules=folder/'modules';modules.mkdir(parents=True,exist_ok=True)
    materialize(bundle,modules,event_path='/tmp/skill_events.jsonl');shutil.copyfile(SCORER,modules/SCORER.name)
    (modules/'problems.jsonl').write_text(''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in problems))
    candidate=folder/'source.py';candidate.write_text(source)
    b.tool(job_id=job,capability='private_verification',request_id=key,request_hash=identity)
    started=time.monotonic()
    image=read(ROOT/'Prepared_Config.json')['image']
    with DockerWorker(candidate,image=image,worker_script=WORKER,module_dir=modules,timeout_limit=180) as w:
        raw=w.call(dict(mode=mode,timeout=180))
    elapsed=time.monotonic()-started
    value=dict(identity=identity,logger_identity=logger_identity(),worker_sha256=fsha(WORKER),image=image,
        source_sha256=sha(source),dependency_bundle_sha256=fingerprint(bundle),seconds=elapsed,result=raw)
    write_json(receipt,value);b.settle(key,tool_milliseconds=math.ceil(elapsed*1000),cost_microusd=0)
    return value

class CaptureStop(BaseException):pass
class CaptureClient:
    def __init__(self):self.wire=None
    def generate(self,*,instructions,input_text,settings):
        self.wire=dict(instructions=instructions,input_text=input_text,settings=vars(settings))
        raise CaptureStop()

def preflight():
    cfg=read(ROOT/'Prepared_Config.json');manifest=read(ROOT/'Data_Manifest.json');root=ROOT/'preflight';root.mkdir(exist_ok=True)
    b=budget(cfg,root,True);cards=read(ROOT/'Callable_Catalog.json')['cards']
    permission=dict(scope='development_diagnostic',allowed={c['primitive_id']:c['source_sha256'] for c in cards})
    prime=next(c for c in cards if c['helper_name']=='is_prime')
    try:bundle_from_cards([prime])
    except ValueError:pass
    else:raise AssertionError('DRAFT_ACTIVATED_WITHOUT_PERMISSION')
    bundle=bundle_from_cards([prime],development_permission=permission);call=bundle['card_names'][prime['primitive_id']]
    source=f'from flowevo_skills import {call}\ndef logger_regression(n):\n    import builtins\n    assert builtins.open is None\n    return {call}(n)\n'
    logger=isolated(root,b,'logger_regression',source,bundle,[],mode='logger_regression')
    assert logger['result']['status']=='REGRESSION_PASS'
    problems=[json.loads((ROOT/'private'/(r['problem_id'].replace('/','_')+'.jsonl')).read_text()) for r in manifest['tasks']]
    old_contracts=root/'private/executions/contracts/receipt.json'
    if old_contracts.exists():
        earlier={p['task_id']:p for p in map(json.loads,(old_contracts.parent/'modules/problems.jsonl').read_text().splitlines())}
        assert all(earlier[p['task_id']]==p for p in problems),'CONTRACT_INPUT_DRIFT'
        contracts=read(old_contracts)['result']
    else:contracts=isolated(root,b,'contracts','pass\n',{},problems,mode='contracts')['result']
    assert contracts['status']=='CONTRACTS_CHECKED'
    assert all(not v['official_contract_invalid'] for t in contracts['tasks'] for v in t['subsets'].values())
    previews=[]
    for row in manifest['tasks']:
        for arm in ('G','R'):
            dest=root/(arm+'_'+row['problem_id'].replace('/','_'))
            if not dest.exists():snapshot(BASE,dest)
            capture=CaptureClient();box=IsolatedCodeSandbox(image=cfg['image'],budget=b,root=root)
            r=native(dest,cfg,capture,box,arm);task=task_of(row)
            recall,_=r._retrieve(task);matched=r._match_primitives(task)
            try:r.run_episode(task)
            except CaptureStop:pass
            assert capture.wire is not None,'NO_ACTOR_REQUEST_AT_FIRST_ATTEMPT'
            text=capture.wire['input_text']
            if row['problem_id']=='HumanEval/39':
                assert (OLD/'locked/HumanEval_39/solution.py').read_text().strip() in text
                assert 'five-second case limit' in text
                assert 'archived_is_prime' not in text # prior host-bound B is forbidden
            path=root/'request_previews'/(arm+'_'+row['problem_id'].replace('/','_')+'.json');write_json(path,capture.wire)
            previews.append(dict(task_id=row['problem_id'],arm=arm,retrieved=[x['skill_id'] for x in recall],
                candidate_callables=[x['primitive_id'] for x in matched],request_preview=rel(path),
                first_request_captured_no_send=True,bytes=len(text.encode())))
    write_json(OUT/'Preflight.json',dict(status='PASS',logger_regression=logger['result'],contracts=contracts,
        previews=previews,budget=b.snapshot(),old_files_unchanged=integrity(),model_requests=0))
    print(json.dumps(dict(status='PASS',budget=b.snapshot(),core_retrieval=[x for x in previews if x['task_id']=='HumanEval/39']),ensure_ascii=False))

def freeze():
    checks=read(OUT/'Preflight.json');assert checks['status']=='PASS'
    cfg=read(ROOT/'Prepared_Config.json');cfg['status']='AWAITING_NEW_EXPLICIT_AUTHORIZATION'
    cfg['source_hashes']=code_hashes();cfg['manifest_sha256']=fsha(ROOT/'Data_Manifest.json');cfg['catalog_sha256']=fsha(ROOT/'Callable_Catalog.json')
    cfg['private_suite_hashes']={r['problem_id'].replace('/','_')+'.jsonl':fsha(ROOT/'private'/(r['problem_id'].replace('/','_')+'.jsonl')) for r in read(ROOT/'Data_Manifest.json')['tasks']}
    cfg['candidate_file_hashes']={rel(p):fsha(p) for p in (ROOT/'development_candidates').glob('*.py')}
    cfg['preflight_sha256']=fsha(OUT/'Preflight.json');cfg['protocol_sha256']=fingerprint(cfg)
    write_json(OUT/'Frozen_Config.json',cfg)
    print(json.dumps(dict(protocol_sha256=cfg['protocol_sha256'],actor_calls=32,teacher_calls=0,max_usd=2),ensure_ascii=False))

def run(authorization):
    cfg=read(OUT/'Frozen_Config.json');assert fingerprint({k:v for k,v in cfg.items() if k!='protocol_sha256'})==cfg['protocol_sha256']
    assert code_hashes()==cfg['source_hashes'] and fsha(ROOT/'Data_Manifest.json')==cfg['manifest_sha256'] and fsha(ROOT/'Callable_Catalog.json')==cfg['catalog_sha256']
    assert tree_hash(BASE)==cfg['initial_library_sha256']
    assert all(fsha(ROOT/'private'/p)==h for p,h in cfg['private_suite_hashes'].items())
    assert all(fsha(REPO/p)==h for p,h in cfg['candidate_file_hashes'].items())
    if not authorization:raise PilotStop('NEW_EXPLICIT_AUTHORIZATION_REQUIRED')
    a=read(authorization)
    if a.get('authorized') is not True or a.get('protocol_sha256')!=cfg['protocol_sha256'] or a.get('max_usd')!=2:raise PilotStop('AUTHORIZATION_MISMATCH')
    if os.environ.get('PYTHONHASHSEED')!='0':raise PilotStop('PYTHONHASHSEED_MUST_BE_ZERO')
    root=ROOT/'real_01';root.mkdir(exist_ok=True);(root/'private').mkdir(exist_ok=True);(root/'private').chmod(0o700)
    b=budget(cfg,root);client=PilotTransport(cfg,root,b,authorized=True)
    box=IsolatedCodeSandbox(image=cfg['image'],budget=b,root=root,absolute_deadline=cfg['absolute_deadline_utc'])
    rows=read(ROOT/'Data_Manifest.json')['tasks'];outputs=read(root/'transfer_progress.json') if (root/'transfer_progress.json').exists() else []
    status='STOPPED';stage='actors';error=None
    try:
        for i,row in enumerate(rows):
            for arm in (('G','R') if i%2==0 else ('R','G')):
                job=arm+'_'+row['problem_id'].replace('/','_')
                if any(x['job']==job for x in outputs):continue
                marker=root/'jobs'/(job+'.json')
                if marker.exists():raise PilotStop('PARTIAL_TASK_NO_REISSUE')
                write_json(marker,dict(status='started',task_id=row['problem_id'],arm=arm))
                dest=root/'libraries'/job;snapshot(BASE,dest)
                client.context('reuse',job);box.context('reuse',job)
                r=native(dest,cfg,client,box,arm);task=task_of(row)
                result=r.run_episode(task);trace=trace_of(result)
                outputs.append(dict(job=job,task_id=row['problem_id'],arm=arm,result=result,
                    actual_calls=trace.actual_skill_calls,retrieved=trace.retrieved_skills,
                    presented=[x.tool_input_summary for x in trace.actions if x.tool_name=='skill_presented'],
                    callable_retrieved=[x.tool_input_summary for x in trace.actions if x.tool_name=='skill_retrieved'],
                    final_source_sha256=sha(trace.code_history[-1]) if trace.code_history else None,
                    final_dependencies_sha256=fingerprint(trace.executable_dependencies)))
                write_json(root/'transfer_progress.json',outputs);write_json(marker,dict(status='complete'))
                print(job,'public',trace.success,flush=True)
        stage='locked_scoring'
        for item in outputs:
            if 'full_score' in item:continue
            trace=trace_of(item['result']);source=trace.code_history[-1] if trace.code_history else ''
            problem=json.loads((ROOT/'private'/(item['task_id'].replace('/','_')+'.jsonl')).read_text())
            receipt=isolated(root,b,item['job'],source,trace.executable_dependencies,[problem])
            raw=receipt['result'];verdict='SCORING_ERROR' if raw['status']!='COMPLETED' else 'PASS' if all(x['status']=='pass' for x in raw['subsets'].values()) else 'FAIL'
            item['full_score']=dict(verdict=verdict,receipt_ref=rel(root/'private/executions'/item['job']/'receipt.json'),
                source_sha256=receipt['source_sha256'],subset_summary={s:{k:v[k] for k in ['status','planned_count','executed_count','passed_count']} for s,v in raw.get('subsets',{}).items()})
            item['final_operation_calls']=[{k:e.get(k) for k in ('skill_id','sha256','event','argument_types','keyword_types','error_type')} for e in raw.get('skill_events',[]) if e['event'] in {'started','returned','error','logging_truncated'}]
            write_json(root/'transfer_progress.json',outputs)
        stage='fixed_return_use'
        for item in outputs:
            if item['arm']!='R' or 'return_use' in item:continue
            trace=trace_of(item['result']);used={x['skill_id'] for x in trace.actual_skill_calls if x['event']=='returned'}
            used &= {e['skill_id'] for e in item.get('final_operation_calls',[]) if e['event']=='returned'}
            checks=[]
            for sid in sorted(used):
                if not trace.code_history:continue
                pack=copy.deepcopy(trace.executable_dependencies)
                targets=[e for e in pack.get('entries',{}).values() if e['skill_id']==sid]
                if not targets:continue
                for e in targets:e['ablate_return']=True
                box.context('ablation',item['job']+'_'+sha(sid)[:8]);task=task_of(next(r for r in rows if r['problem_id']==item['task_id']))
                with box.bind_dependencies(pack):fb=verify_task(task,trace.code_history[-1],box)
                checks.append(dict(skill_id=sid,established=trace.success and not fb.passed,ablation_public_passed=fb.passed,
                    scope='one frozen operation at a time; fixed final caller and public checks'))
            item['return_use']=checks
            target='development_skill_humaneval_HumanEval_31_trace_7a579aec'
            final=[e for e in item.get('final_operation_calls',[]) if e['skill_id']==target]
            item['target_reuse_status']=('RETRIEVAL_MISS' if target not in item['callable_retrieved'] else
                'RETRIEVED_NOT_PRESENTED' if target not in item['presented'] else
                'ACTOR_SELECTED_REUSE' if any(c['skill_id']==target and c['established'] for c in checks) else
                'CALL_ERROR' if any(e['event']=='error' for e in final) else
                'RETURN_USE_UNCONFIRMED' if any(e['event']=='returned' for e in final) else 'PRESENTED_NOT_USED')
            write_json(root/'transfer_progress.json',outputs)
        status='COMPLETED'
    except BaseException as exc:error=type(exc).__name__+': '+str(exc);raise
    finally:
        save_stop_snapshot(root,b,status=status,stage=stage,error_type=error)
        pairs={tid:{x['arm']:x['full_score']['verdict'] for x in outputs if x['task_id']==tid and 'full_score' in x} for tid in {x['task_id'] for x in outputs}}
        counts={'both_pass':0,'only_R':0,'only_G':0,'both_fail':0,'incomplete_or_scoring_error':0}
        for pair in pairs.values():
            if set(pair)!={'G','R'} or 'SCORING_ERROR' in pair.values():counts['incomplete_or_scoring_error']+=1;continue
            counts['both_pass' if pair['G']==pair['R']=='PASS' else 'only_R' if pair['R']=='PASS' else 'only_G' if pair['G']=='PASS' else 'both_fail']+=1
        write_json(OUT/'Autonomous_Reuse_Result.json',dict(status=status,error=error,tasks=outputs,paired=counts,budget=b.snapshot(),
            old_files_unchanged=integrity(),new_skill_acquired=False,protocol_sha256=cfg['protocol_sha256']))

if __name__=='__main__':
    os.chdir(REPO);p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','preflight','freeze','run']);p.add_argument('--authorization');args=p.parse_args()
    {'prepare':prepare,'preflight':preflight,'freeze':freeze,'run':lambda:run(args.authorization)}[args.stage]()
