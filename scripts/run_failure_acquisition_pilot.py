"""Staged, bounded real acquisition pilot. Real calls require protocol-bound authorization."""
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

from agent.generator import LLMGenerator
from core.schemas import ExecutionTrace
from eval.runner import BenchmarkRunner, RunnerConfig
from eval.verifier import verify_task
from failure_evo.contracts import fingerprint
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.pilot_data import manifest, task_from_manifest, final_score_task
from failure_evo.pilot_runtime import PilotStop, PilotTransport, PilotTeacher, IsolatedCodeSandbox, write_json
from failure_evo.teacher_acquisition import AcquisitionScheduler
from failure_evo.skill_runtime import bundle_from_cards, sha
from memory.primitive_store import PrimitiveStore
from runtime.config import RuntimeLLMConfig, GenerationSettings, SkillContextBudgets

STAGES=('preflight','collect','acquire','support','freeze','transfer','report')

def source_hashes():
    files=sorted(Path('FlowEvo/src').rglob('*.py'))+[Path(__file__),Path('scripts/check_failure_acquisition_pilot.py')]
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

def paths(root):
    root=Path(root)
    return dict(registry_path=str(root/'skills/registry.json'),primitive_path=str(root/'primitives/registry.json'),
        policy_path=str(root/'policy.json'),template_path=str(root/'templates.json'),negative_memory_path=str(root/'negative.json'),
        workflow_memory_path=str(root/'workflow.json'),strategy_path=str(root/'strategies.json'),trace_root=str(root/'traces'))

def runner(root,cfg,client,sandbox,*,frozen=False):
    settings=GenerationSettings(0,cfg['actor']['output_tokens'])
    runtime=RuntimeLLMConfig('deepseek','','https://api.deepseek.com',cfg['actor']['model'],'FlowEvo-pilot',3,
        SkillContextBudgets(4096,4096,1536,1536),settings,settings,'frozen_pilot','')
    value=BenchmarkRunner(RunnerConfig(**paths(root),executable_skills_enabled=True,frozen_eval=frozen),
        dynamic_generator=LLMGenerator(runtime,client),sandbox=sandbox)
    assert value.executor.max_repairs==2
    return value

def snapshot(src,dst):
    src,dst=Path(src),Path(dst)
    if dst.exists():raise PilotStop('SNAPSHOT_ALREADY_EXISTS')
    shutil.copytree(src,dst)
    for p in dst.rglob('*.json'):
        p.write_text(p.read_text().replace(str(src.resolve()),str(dst.resolve())).replace(str(src)+'/',str(dst)+'/'))

def tree_hash(root):
    return fingerprint({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(root).rglob('*')) if p.is_file()})

def budget(cfg,root):
    b=cfg['budget']
    return PersistentBudget(Path(root)/'budget.jsonl',run_id=Path(root).name,protocol_hash=cfg['protocol_sha256'],
        max_calls=b['actor_calls']+b['teacher_calls'],max_tokens=b['max_tokens'],max_tools=b['executions'],
        max_cost_microusd=b['max_usd']*1000000,token_rate_microusd_per_million=3960000,tool_cost_upper_microusd=0,
        max_tool_milliseconds=b['executions']*20000,tool_milliseconds_upper=20000,wall_seconds=b['wall_seconds'],model_rates=b['model_rates'])

def freeze_preflight(config_path):
    cfg=json.loads(Path(config_path).read_text());out=Path(cfg['reports']);out.mkdir(parents=True,exist_ok=True)
    data=manifest(cfg['dataset_path'])
    write_json(out/'Pilot_Data_Manifest.json',data)
    cfg['manifest_sha256']=fingerprint(data);cfg['source_hashes']=source_hashes()
    cfg['protocol_sha256']=fingerprint(cfg)
    write_json(out/'Pilot_Frozen_Config.json',cfg)
    return cfg,data

def load_frozen(config_path):
    raw=json.loads(Path(config_path).read_text());out=Path(raw['reports'])
    cfg=json.loads((out/'Pilot_Frozen_Config.json').read_text());data=json.loads((out/'Pilot_Data_Manifest.json').read_text())
    unhashed={k:v for k,v in cfg.items() if k!='protocol_sha256'}
    if fingerprint(unhashed)!=cfg['protocol_sha256']:raise PilotStop('FROZEN_PROTOCOL_DRIFT')
    if cfg['source_hashes']!=source_hashes() or cfg['manifest_sha256']!=fingerprint(data):raise PilotStop('FROZEN_CODE_OR_DATA_DRIFT')
    if hashlib.sha256(Path(cfg['dataset_path']).read_bytes()).hexdigest()!=data['dataset_sha256']:raise PilotStop('DATASET_DRIFT')
    return cfg,data

def authorize(cfg,path):
    if not path:raise PilotStop('EXPLICIT_PILOT_BUDGET_AUTHORIZATION_REQUIRED')
    checks=json.loads((Path(cfg['reports'])/'Pilot_Preflight_Receipts.json').read_text())
    if checks.get('protocol_sha256')!=cfg['protocol_sha256'] or not all(checks['checks'].values()):raise PilotStop('PREFLIGHT_NOT_VALID_FOR_PROTOCOL')
    a=json.loads(Path(path).read_text())
    if a.get('protocol_sha256')!=cfg['protocol_sha256'] or a.get('authorized') is not True or a.get('max_usd')!=cfg['budget']['max_usd']:
        raise PilotStop('AUTHORIZATION_SCOPE_MISMATCH')
    if datetime.now(timezone.utc)>=datetime.fromisoformat(cfg['absolute_deadline_utc']):raise PilotStop('ABSOLUTE_DEADLINE')
    return True

def set_context(client,box,phase,job,role='actor'):
    client.context(phase,job,role);box.context(phase,job)

def label(task):return task.task_id.replace('/','_')

def trace_of(result):return ExecutionTrace.model_validate_json(Path(result['trace_file']).read_text())

def save_phase(root,name,value):write_json(Path(root)/'phases'/f'{name}.json',dict(status='complete',result=value))

def prior(root,name):return json.loads((Path(root)/'phases'/f'{name}.json').read_text())['result']

def support_choice(card,source,rows):
    candidates=[r for r in rows if r['data_role']=='train' and r['source_lineage_id']!=source['source_lineage_id'] and r['capability_family_id']==source['capability_family_id']]
    words=set(re.findall('[a-z]{3,}',json.dumps(card.operation_contracts).lower()))
    def key(r):
        entry=next(n for n in ast.parse(r['prompt']).body if isinstance(n,ast.FunctionDef) and n.name==r['entry_point'])
        arity=abs(len(entry.args.args)-len(card.signature.get('args',[])))
        overlap=len(words & set(re.findall('[a-z]{3,}',r['prompt'].lower())))
        return arity,-overlap,fingerprint(r['problem_id'])
    return min(candidates,key=key) if candidates else None

def collect(cfg,data,root,client,box):
    base=root/'base';r=runner(base,cfg,client,box)
    outputs=[]
    for row in data['tasks']:
        if row['data_role']!='train':continue
        initial_library=tree_hash(base)
        task=task_from_manifest(row);task.metadata.update(actor_model=cfg['actor']['model'],actor_config=cfg['actor'],initial_library=initial_library)
        set_context(client,box,'collect',label(task))
        result=r.run_episode(task);trace=trace_of(result)
        feedback=trace.verifier_feedback[-1] if trace.verifier_feedback else None
        credible=bool(not trace.success and feedback and feedback.executed_code and trace.failure_type!='generation_error')
        outputs.append(dict(row=row,result=result,credible_failure=credible,initial_library_sha256=initial_library))
        write_json(root/'collect_progress.json',outputs)
    return dict(tasks=outputs,base_hash=tree_hash(base))

def acquire(cfg,data,root,client,box):
    collected=prior(root,'collect');selected=[];seen=set()
    for item in sorted(collected['tasks'],key=lambda x:fingerprint(x['row']['problem_id'])):
        family=item['row']['capability_family_id']
        if item['credible_failure'] and family not in seen and len(selected)<3:
            selected.append(item);seen.add(family)
    write_json(root/'selection.json',dict(rule='public confirmed failure; one task per frozen public capability stratum, SHA order, max 3; no transfer feedback',selected=[x['row']['problem_id'] for x in selected],all_items=[dict(task=x['row']['problem_id'],selected=x in selected,credible_failure=x['credible_failure']) for x in collected['tasks']]))
    r=runner(root/'acquired',cfg,client,box)
    scheduler=AcquisitionScheduler(root=root/'acquisition',teacher=PilotTeacher(client),registry=r.skill_registry,
        primitive_store=r.primitive_store,sandbox=box,phase='train',max_items=3,max_attempts=2,max_operations=1)
    results=[]
    for item in selected:
        task=task_from_manifest(item['row'])
        task.metadata.update(actor_model=cfg['actor']['model'],actor_config=cfg['actor'],initial_library=item['initial_library_sha256'])
        set_context(client,box,'acquire',label(task),'teacher')
        result=scheduler.on_task_end(task,trace_of(item['result']))
        results.append(dict(source=item['row'],outcome=result))
    return results

def support(cfg,data,root,client,box):
    acquired=prior(root,'acquire');r=runner(root/'acquired',cfg,client,box)
    scheduler=AcquisitionScheduler(root=root/'acquisition',teacher=PilotTeacher(client),registry=r.skill_registry,
        primitive_store=r.primitive_store,sandbox=box,phase='train',max_items=3,max_attempts=2,max_operations=1)
    outcomes=[]
    for item in acquired:
        for packed in item['outcome'].get('compiled_operations',[]):
            card=r.primitive_store.get(packed['primitive_id']);chosen=support_choice(card,item['source'],data['tasks'])
            if chosen is None:
                outcomes.append(dict(candidate_id=card.primitive_id,status='NO_INDEPENDENT_COMPATIBLE_TRAIN_SOURCE'));continue
            write_json(root/'support_selections'/f'{card.primitive_id}.json',dict(source=item['source']['problem_id'],chosen=chosen['problem_id'],rule='same public capability stratum; distinct lineage; arity distance, contract/prompt token overlap, SHA tie break; one task only'))
            task=task_from_manifest(chosen);set_context(client,box,'support',card.primitive_id,'teacher')
            outcomes.append(scheduler.support_frozen(card.primitive_id,task))
    return outcomes

def freeze(cfg,data,root,client,box):
    prior(root,'support')
    snapshot(root/'base',root/'G');snapshot(root/'base',root/'G_plus')
    store=PrimitiveStore(root/'acquired/primitives/registry.json')
    target=PrimitiveStore(root/'G_plus/primitives/registry.json')
    admitted=[]
    for outcome in prior(root,'support'):
        if outcome['status']!='SUPPORT_ADMITTED':continue
        card=store.get(outcome['candidate_id'])
        if card.status!='active':raise PilotStop('SUPPORT_NOT_ACTIVE')
        bundle_from_cards([card.model_dump(mode='json')])
        card.code_path=str(target.save_code(card.primitive_id,Path(card.code_path).read_text()))
        target.upsert(card);admitted.append(card.primitive_id)
    return dict(admitted=admitted,G_hash=tree_hash(root/'G'),G_plus_hash=tree_hash(root/'G_plus'),base_hash=tree_hash(root/'base'))

def transfer(cfg,data,root,client,box):
    frozen=prior(root,'freeze')
    if not frozen['admitted']:return dict(status='SKIPPED_NO_ADMITTED_OPERATION',tasks=[])
    for arm in ('G','G_plus'):
        if tree_hash(root/arm)!=frozen[arm+'_hash']:raise PilotStop('FROZEN_LIBRARY_DRIFT')
    outputs=[]
    # Identical frozen library per arm, independent mutable diagnostic state and trace directories.
    for arm in ('G','G_plus'):
        snapshot(root/arm,root/(arm+'_runtime'))
    runners={a:runner(root/(a+'_runtime'),cfg,client,box,frozen=True) for a in ('G','G_plus')}
    for row in data['tasks']:
        if row['data_role']!='transfer_dev':continue
        task=task_from_manifest(row)
        for arm in ('G','G_plus'):
            set_context(client,box,'transfer',arm+'_'+label(task))
            r=runners[arm];retrievable=[c['primitive_id'] for c in r._match_primitives(task)]
            result=r.run_episode(task);trace=trace_of(result)
            outputs.append(dict(task_id=task.task_id,arm=arm,retrievable=retrievable,result=result,
                presented=[a.tool_input_summary for a in trace.actions if a.tool_name=='skill_presented'],calls=trace.actual_skill_calls,
                parameter_contract_assessment='inspect recorded argument types and caller source; not inferred from whole-task pass',
                return_use_assessment='caller source retained; autonomous return dependence not automatically established'))
            write_json(root/'transfer_progress.json',outputs)
    # Diagnostic ablations run after autonomous programs are fixed; no feedback to Actor.
    for item in outputs:
        if item['arm']!='G_plus':continue
        trace=trace_of(item['result'])
        source_row=next(r for r in data['tasks'] if r['problem_id']==item['task_id'])
        task=task_from_manifest(source_row)
        called={e['skill_id'] for e in item['calls'] if e['event']=='returned'} & set(frozen['admitted'])
        use_checks=[]
        for skill_id in sorted(called):
            pack=copy.deepcopy(trace.executable_dependencies)
            for entry in pack['entries'].values():
                if entry['skill_id']==skill_id:entry['ablate_return']=True
            box.context('return_use',label(task)+'_'+skill_id)
            with box.bind_dependencies(pack):
                fb=verify_task(task,trace.code_history[-1],box)
            use_checks.append(dict(skill_id=skill_id,ablation_passed=fb.passed,
                return_use_established=bool(item['result']['passed'] and not fb.passed),
                method='replace helper return by None; conservative public-test dependence check'))
        item['return_use_checks']=use_checks
        item['parameter_contract_assessment']=[dict(skill_id=e['skill_id'],argument_types=e.get('argument_types'),keyword_types=e.get('keyword_types'),
            contract=e.get('contract'),status='runtime_call_completed' if any(x['event']=='returned' and x['skill_id']==e['skill_id'] for x in item['calls']) else 'runtime_error_or_incomplete',
            precondition_compliance='requires source/argument review; runtime success alone does not prove all preconditions') for e in item['calls'] if e['event']=='started']
    # Only after every generated program is frozen may final scoring read private tests.
    if not client.dry:
        for item in outputs:
            trace=trace_of(item['result']);task=final_score_task(cfg['dataset_path'],item['task_id'])
            box.context('final_score',item['arm']+'_'+label(task))
            with box.bind_dependencies(trace.executable_dependencies):fb=verify_task(task,trace.code_history[-1] if trace.code_history else '',box)
            item['final_passed']=fb.passed
            write_json(root/'private_scores'/f"{item['arm']}_{label(task)}.json",fb.model_dump(mode='json'))
    else:
        for item in outputs:item['final_passed']=item['result']['passed']
    return dict(status='COMPLETE',tasks=outputs)

def report(cfg,data,root,client,box):
    c=prior(root,'collect');a=prior(root,'acquire');s=prior(root,'support');f=prior(root,'freeze');t=prior(root,'transfer')
    paired={}
    for item in t['tasks']:paired.setdefault(item['task_id'],{})[item['arm']]=item
    rescue=sum(not x['G']['final_passed'] and x['G_plus']['final_passed'] for x in paired.values())
    harm=sum(x['G']['final_passed'] and not x['G_plus']['final_passed'] for x in paired.values())
    funnel=dict(training_tasks=len(c['tasks']),credible_failures=sum(x['credible_failure'] for x in c['tasks']),
        capability_hypotheses=len(a),learning_items=len(a),source_teacher_attempts=sum(x['outcome'].get('teacher_attempts',0) for x in a),
        source_verified=sum(x['outcome']['teacher_success'] for x in a),operations=sum(len(x['outcome'].get('compiled_operations',[])) for x in a),
        support_teacher_attempts=sum(len(x.get('attempts',[])) for x in s),support_passed=sum(x['status']=='SUPPORT_ADMITTED' for x in s),
        admitted=len(f['admitted']),transfer_calls=sum(sum(e['event']=='started' for e in x['calls']) for x in t['tasks']),new_success=rescue,new_failure=harm)
    result=dict(dry_run=client.dry,funnel=funnel,budget=client.budget.snapshot(),transfer=t,protocol_sha256=cfg['protocol_sha256'])
    stage_costs={}
    for p in (root/'requests').rglob('receipt.json'):
        r=json.loads(p.read_text());acc=stage_costs.setdefault(r['phase'],dict(requests=0,tokens=0,peak_price_bound_microusd=0,executions=0,execution_seconds=0))
        acc['requests']+=1;acc['tokens']+=r['usage']['total_tokens'];acc['peak_price_bound_microusd']+=0 if client.dry else r['price_bound_microusd']
    for p in (root/'executions').rglob('result.json'):
        phase=p.relative_to(root/'executions').parts[0];acc=stage_costs.setdefault(phase,dict(requests=0,tokens=0,peak_price_bound_microusd=0,executions=0,execution_seconds=0))
        r=json.loads(p.read_text());acc['executions']+=1;acc['execution_seconds']+=r['seconds']
    result['stage_costs']=stage_costs
    for item in t['tasks']:
        job=item['arm']+'_'+item['task_id'].replace('/','_')
        rows=[json.loads(p.read_text()) for p in (root/'requests'/'transfer'/job).rglob('receipt.json')]
        workers=[json.loads(p.read_text()) for p in (root/'executions'/'transfer'/job).rglob('result.json')]
        item['deployment_cost']=dict(model_requests=len(rows),tokens=sum(r['usage']['total_tokens'] for r in rows),
            peak_price_bound_microusd=sum(0 if client.dry else r['price_bound_microusd'] for r in rows),
            isolated_executions=len(workers),execution_seconds=sum(r['seconds'] for r in workers))
    write_json(root/'Pilot_Result.json',result)
    lines=['# Pilot '+('Dry Run' if client.dry else 'Result'),'','Dry-run fixtures are not real learning results.' if client.dry else 'Real model development diagnosis; no claim of stable success-rate improvement.','','|Funnel|Count|','|---|---:|']
    lines += [f'|{k}|{v}|' for k,v in funnel.items()]
    lines += ['','|Task|G complete|G + skills complete|G + skills actual calls|','|---|---|---|---:|']
    for tid,x in paired.items():lines.append(f"|{tid}|{x['G']['final_passed']}|{x['G_plus']['final_passed']}|{sum(e['event']=='started' for e in x['G_plus']['calls'])}|")
    lines += ['', '|Stage|Model requests|Tokens|Isolated executions|Peak price bound USD|','|---|---:|---:|---:|---:|']
    lines += [f"|{name}|{v['requests']}|{v['tokens']}|{v['executions']}|{v['peak_price_bound_microusd']/1e6:.6f}|" for name,v in stage_costs.items()]
    lines += ['','Per-task deployment costs and exact usage: `Pilot_Result.json`. Private scoring is never fed back to any actor, teacher or compiler.', '', 'Next: '+('No public learning opportunity: reconsider distribution in a new protocol; do not expand this run.' if not funnel['credible_failures'] else 'Inspect the first drop in this funnel. Retain unsuccessful acquisition, absent calls, wrong composition and negative transfer.')]
    (root/'Pilot_Result.md').write_text('\n'.join(lines)+'\n')
    if not client.dry:shutil.copy2(root/'Pilot_Result.md',Path(cfg['reports'])/'Pilot_Result.md')
    return result

FUNCTIONS=dict(collect=collect,acquire=acquire,support=support,freeze=freeze,transfer=transfer,report=report)

def execute(cfg,data,root,stages,*,authorized=False,dry=False):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    b=budget(cfg,root);client=PilotTransport(cfg,root,b,authorized=authorized,dry=dry)
    box=IsolatedCodeSandbox(image=cfg['image'],budget=b,root=root,absolute_deadline=None if dry else cfg['absolute_deadline_utc'])
    if dry:install_mock(client)
    for stage in stages:
        marker=root/'phases'/f'{stage}.json'
        if marker.exists():
            state=json.loads(marker.read_text())
            if state['status']=='complete':continue
            raise PilotStop('INCOMPLETE_STAGE_STOP_NO_REISSUE:'+stage)
        if stage!='collect':prior(root,STAGES[STAGES.index(stage)-1])
        write_json(marker,dict(status='running',protocol_sha256=cfg['protocol_sha256']))
        try:
            result=FUNCTIONS[stage](cfg,data,root,client,box)
        except BaseException as exc:
            write_json(root/'Pilot_Stop.json',dict(stage=stage,reason=str(exc),error_type=type(exc).__name__,budget=b.snapshot(),dry_run=dry))
            if not dry:
                partial=['# Pilot Result — stopped', '', 'Status: STOPPED; no incomplete stage is silently repeated.', '', 'Stage: '+stage, 'Reason: '+str(exc), '', 'Completed phases and task receipts remain in the run directory; no final success-rate claim is available.', '', 'Budget: '+json.dumps(b.snapshot(),ensure_ascii=False)]
                (Path(cfg['reports'])/'Pilot_Result.md').write_text('\n'.join(partial)+'\n')
            raise
        save_phase(root,stage,result)
        print(json.dumps(dict(stage=stage,status='complete',budget=b.snapshot()),ensure_ascii=False),flush=True)
    return b.snapshot()

def dry_data():
    rows=[]
    for tid,role,entry,prompt in [('fixture_order','train','order_values','Order the input values by absolute magnitude.\n>>> order_values([3,-1,2])\n[-1,2,3]'),('fixture_max','train','maximum_value','Return greatest magnitude element.\n>>> maximum_value([-8,2,3])\n-8'),('fixture_transfer','transfer_dev','transfer_values','Order by magnitude then append 999.\n>>> transfer_values([-5,2,0])\n[0,2,-5,999]')]:
        from failure_evo.pilot_data import public_examples
        source=f'def {entry}(xs):\n    """{prompt}"""\n'
        rows.append(dict(problem_id=tid,data_role=role,source_lineage_id=tid,duplicate_group_id=tid,capability_family_id='fixture_only',prompt=source,entry_point=entry,examples=public_examples(source,entry)))
    return dict(tasks=rows)

def install_mock(client):
    def actor(messages):
        if client.phase=='collect':
            entry='order_values' if client.job=='fixture_order' else 'maximum_value'
            return f'def {entry}(xs):\n    return []\n'
        names=re.findall(r'from flowevo_skills import (op_[a-f0-9]+)',messages[-1]['content'])
        if names:return f'from flowevo_skills import {names[0]}\ndef transfer_values(xs):\n    return {names[0]}(xs)+[999]\n'
        return 'def transfer_values(xs):\n    return sorted(xs,key=abs)+[999]\n'
    def teacher(messages):
        payload=json.loads(messages[-1]['content']);entry=payload['task']['entry_point']
        if client.phase=='acquire':
            # One deliberately invalid delivery exercises feedback revision.
            if client.ordinal==1:return dict(code='',operations={})
            contract=dict(purpose='Order values by absolute magnitude',parameters={'xs':'list[number]'},preconditions='finite real values',output='list[number]',side_effects='none',failure='TypeError for unsupported values')
            suffix='[-1]' if entry=='maximum_value' else ''
            return dict(code=f'def ordered(xs):\n    return sorted(xs,key=abs)\ndef {entry}(xs):\n    return ordered(xs){suffix}\n',operations={'ordered':contract})
        op=payload['frozen_operation']['import_statement'].split()[-1]
        if client.ordinal==1:return dict(code=f'def {entry}(xs):\n    return []\n')
        suffix='[-1]' if entry=='maximum_value' else ''
        return dict(code=f'from flowevo_skills import {op}\ndef {entry}(xs):\n    return {op}(xs){suffix}\n')
    client.dry_actor=actor;client.dry_teacher=teacher

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--stage',choices=STAGES+('all',),default='preflight');p.add_argument('--dry-run',action='store_true');p.add_argument('--authorization-file');args=p.parse_args()
    if args.stage=='preflight':
        cfg,data=freeze_preflight(args.config)
        print(json.dumps(dict(status='DATA_AND_CONFIG_FROZEN',usable=data['usable_public_example_tasks'],tasks=len(data['tasks']),protocol_sha256=cfg['protocol_sha256']),ensure_ascii=False))
        if not args.dry_run:return
    else:cfg,data=load_frozen(args.config)
    if args.dry_run:
        root=Path(tempfile.mkdtemp(prefix='dry_',dir=cfg['dry_root']))
        execute(cfg,dry_data(),root,STAGES[1:],dry=True)
        write_json(Path(cfg['reports'])/'Pilot_Dry_Run.json',dict(run_root=str(root),result=json.loads((root/'Pilot_Result.json').read_text())))
        from check_failure_acquisition_pilot import run_checks
        checked=run_checks(cfg,data,root)
        print(json.dumps(checked,ensure_ascii=False),flush=True)
    else:
        allowed=authorize(cfg,args.authorization_file)
        execute(cfg,data,Path(cfg['run_root']),STAGES[1:] if args.stage=='all' else [args.stage],authorized=allowed)

if __name__=='__main__':
    try:main()
    except PilotStop as exc:
        print('PILOT_STOP: '+str(exc),file=sys.stderr);raise SystemExit(2)
