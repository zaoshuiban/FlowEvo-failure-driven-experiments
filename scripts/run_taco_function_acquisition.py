"""Bounded real TACO acquisition using the existing native Pilot components.

One protocol-bound authorization covers collect -> acquire -> support -> freeze
-> autonomous paired transfer -> report. No authorization means no model client
requests. Completed jobs resume; ambiguous partial jobs stop without reissuing.
"""
import argparse
import ast
import copy
from dataclasses import asdict
from datetime import datetime,timezone,timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

REPO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(REPO/'FlowEvo/src'),str(REPO/'scripts')]
from core.schemas import ExecutionTrace
from core.generator_state import GeneratorState,SkillActionEntry,WorkflowMotif,RoutingBiases
from env.taco_function_loader import public_task,scoring_task
from eval.verifier import verify_task
from failure_evo.contracts import fingerprint
from failure_evo.pilot_runtime import PilotStop,PilotTransport,PilotTeacher,IsolatedCodeSandbox,write_json
from failure_evo.teacher_acquisition import AcquisitionScheduler
from failure_evo.skill_runtime import bundle_from_cards,sha
from memory.primitive_store import PrimitiveStore
from run_failure_acquisition_pilot import runner,snapshot,tree_hash,budget,trace_of,paths

OUT=REPO/'reports/taco_function_acquisition_20261120'
PREP=REPO/'runs/taco_function_acquisition_20261120/preparation'
ROOT=REPO/'runs/taco_function_acquisition_20261120/real_01'
STAGES=('collect','acquire','support','freeze','transfer','report')


def read(p):return json.loads(Path(p).read_text())


def code_hashes():
    files=list((REPO/'FlowEvo/src').rglob('*.py'))+[Path(__file__),REPO/'scripts/run_failure_acquisition_pilot.py',
          REPO/'scripts/check_taco_function_acquisition.py',REPO/'scripts/prepare_taco_function_acquisition.py']
    return {str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def freeze_protocol():
    data=read(OUT/'Data_Manifest.json');train=data['train_count']
    cfg=copy.deepcopy(read(REPO/'configs/failure_acquisition_pilot.json'))
    actor=4*train+3*2*data['transfer_count'];teacher=12
    peak=(actor*(32768*.30+16384*1.20)+teacher*(32768*1.32+16384*3.96))/1000000
    cfg.update(status='AWAITING_THIS_PROTOCOL_BUDGET_AUTHORIZATION',reports=str(OUT.relative_to(REPO)),
        run_root=str(ROOT.relative_to(REPO)),initial_library='runs/failure_acquisition_pilot_20261120/real_01/G',
        initial_library_sha256=tree_hash(REPO/'runs/failure_acquisition_pilot_20261120/real_01/G'),
        absolute_deadline_utc=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat(),
        dataset_path=str(PREP/'taco_train_shard00.parquet'),manifest_sha256=fingerprint(data),
        source_hashes=code_hashes(),request_price_upper_usd=peak,
        price_source='https://api-docs.deepseek.com/quick_start/pricing/?model_version=DeepSeek-V4-Pro-0813')
    cfg['budget'].update(actor_solve_calls=3*(train+24),actor_strategy_calls=train,actor_calls=actor,teacher_calls=teacher,
        max_tokens=(actor+teacher)*49152,max_usd=int(peak)+1,executions=768,wall_seconds=14400)
    cfg['protocol']=dict(train_tasks=train,batch_size=16,opportunity_target=6,candidate_strata_target=3,
        max_families=3,max_candidate_lineages_per_family=1,source_attempts=2,support_attempts=2,
        transfer_tasks=12,reserved_tasks=12,actor_attempts=3,
        stop='after each fixed batch: >=6 credible opportunities across >=3 sampling strata, else next fixed batch within budget; no expansion',
        sampling_strata_are_not_confirmed_mechanisms=True,
        selection='lineage dedup, first eligible source per stratum in frozen training order, max 3; no replacement after acquisition failure',
        initial_library='exact copy of the closed Pilot G; retain all original artifacts and normal native learning',
        score_gate='same post-lock training score before any success admission for common G; does not count as failure-learning gain',
        teacher_policy='A missing implementation: at most 2 source attempts; B recovery: reuse exact module; C callable: skip; D invalid/engineering: exclude',
        second_source='one deterministic distinct training lineage; real frozen-SHA call, public+full validation, return-value dependence; no evaluation support',
        full_feedback='train binary only; private code/assertions/inputs/expected/reference never enter model or compiler',
        transfer='G vs G_plus independent frozen libraries; original Actor selects calls; no candidate revisions',
        formal_comparison=False)
    cfg.pop('dry_root',None)
    cfg['protocol_sha256']=fingerprint(cfg)
    write_json(OUT/'Frozen_Config.json',cfg)
    print(json.dumps(dict(protocol_sha256=cfg['protocol_sha256'],actor_calls=actor,teacher_calls=teacher,
                         total_calls=actor+teacher,peak_bound_usd=peak,max_usd=cfg['budget']['max_usd'])))


def load_config():
    cfg=read(OUT/'Frozen_Config.json');data=read(OUT/'Data_Manifest.json')
    assert fingerprint({k:v for k,v in cfg.items() if k!='protocol_sha256'})==cfg['protocol_sha256']
    if cfg['source_hashes']!=code_hashes() or fingerprint(data)!=cfg['manifest_sha256']:raise PilotStop('FROZEN_CODE_OR_DATA_DRIFT')
    for row in data['tasks']:
        if sha((REPO/row['private_scoring_ref']).read_text())!=row['private_scoring_sha256']:raise PilotStop('SCORER_DRIFT')
    if tree_hash(REPO/cfg['initial_library'])!=cfg['initial_library_sha256']:raise PilotStop('INITIAL_LIBRARY_DRIFT')
    return cfg,data


def restore_generator_state(value):
    return GeneratorState(skill_action_space={k:SkillActionEntry(**v) for k,v in value['skill_action_space'].items()},
        active_motifs=[WorkflowMotif(**v) for v in value['active_motifs']],routing_biases=RoutingBiases(**value['routing_biases']),
        prompt_directives=value['prompt_directives'],version=value['version'],episode_count=value['episode_count'])


def opportunity_target_reached(completed):
    items=[x for x in completed if x['source_kind'] in {'unresolved_failure','recovered_failure'}]
    return len(items)>=6 and len({x['row']['capability_family_id'] for x in items})>=3


class Experiment:
    def __init__(self,cfg,data,authorization):
        proof=read(authorization);checks=read(OUT/'Acceptance.json')
        if proof.get('authorized') is not True or proof.get('protocol_sha256')!=cfg['protocol_sha256'] or proof.get('max_usd')!=cfg['budget']['max_usd']:
            raise PilotStop('THIS_PROTOCOL_AUTHORIZATION_REQUIRED')
        if checks.get('protocol_sha256')!=cfg['protocol_sha256'] or not all(checks['checks'].values()):raise PilotStop('ACCEPTANCE_REQUIRED')
        if datetime.now(timezone.utc)>=datetime.fromisoformat(cfg['absolute_deadline_utc']):raise PilotStop('ABSOLUTE_DEADLINE')
        self.cfg=cfg;self.data=data;ROOT.mkdir(parents=True,exist_ok=True)
        self.budget=budget(cfg,ROOT)
        self.client=PilotTransport(cfg,ROOT,self.budget,authorized=True)
        self.box=IsolatedCodeSandbox(image=cfg['image'],budget=self.budget,root=ROOT,absolute_deadline=cfg['absolute_deadline_utc'])
        private=ROOT/'private_scoring';private.mkdir(exist_ok=True,mode=0o700);os.chmod(private,0o700)
        self.private_box=IsolatedCodeSandbox(image=cfg['image'],budget=self.budget,root=private,absolute_deadline=cfg['absolute_deadline_utc'])
        self.rows={r['problem_id']:r for r in data['tasks']}

    def context(self,phase,job,role='actor'):
        self.client.context(phase,job,role);self.box.context(phase,job)

    def score(self,task,source,bundle,phase):
        row=self.rows[task.task_id]
        if row['data_role']=='reserved_eval':raise PilotStop('RESERVED_EVALUATION_FORBIDDEN')
        label=task.task_id.replace('/','_')+'_'+fingerprint([sha(source),bundle])[:16]
        target=ROOT/'locked_submissions'/phase/label
        target.mkdir(parents=True,exist_ok=True)
        source_file=target/'source.py'
        if source_file.exists() and source_file.read_text()!=source:raise PilotStop('LOCKED_SOURCE_DRIFT')
        source_file.write_text(source);write_json(target/'dependencies.json',bundle)
        private_task=scoring_task(row,REPO)
        self.private_box.context(phase+'_full',label)
        with self.private_box.bind_dependencies(bundle):
            feedback=verify_task(private_task,source,self.private_box)
        folder=self.private_box.root/'executions'/(phase+'_full')/label/'1'
        write_json(folder/'feedback.json',feedback.model_dump(mode='json'))
        receipt=read(folder/'result.json')
        verdict='FULL_CHECK_PASS' if feedback.passed else 'FULL_CHECK_FAIL'
        if receipt['status'] in {'EVALUATOR_ERROR','OUTPUT_LIMIT','MEMORY_LIMIT'}:verdict='SCORING_ERROR'
        result=dict(verdict=verdict,receipt_ref=str((folder/'result.json').relative_to(REPO)),
                    source_sha256=sha(source),dependency_bundle_sha256=fingerprint(bundle))
        write_json(target/'binary_score.json',result)
        return result

    def native_runner(self,path,*,frozen=False):
        return runner(path,self.cfg,self.client,self.box,frozen=frozen)

    def phase(self,name):return read(ROOT/'phases'/(name+'.json'))['result']

    def existing_callable(self,actor,task,trace):
        """Probe a native saved artifact through the existing call boundary.

        Explicit invocation establishes availability only, never autonomous reuse.
        It neither promotes shadow cards nor creates a new operation.
        """
        from agent.executor import CodeTaskExecutor
        for sid in trace.compiled_skill_ids:
            card=actor.skill_registry.get(sid)
            if card is None or not card.source_sha256:continue
            source=Path(card.code_path).read_text()
            if sha(source)!=card.source_sha256:continue
            final=trace.code_history[-1]
            if ast.dump(ast.parse(source))!=ast.dump(ast.parse(final)):continue
            executor=CodeTaskExecutor(self.box,max_repairs=0)
            executor.executable_skills_enabled=True;executor._task_code_sha=card.source_sha256
            self.box.context('existing_native_call',task.task_id.replace('/','_'))
            actions=[];attempts=[];history=[];feedbacks=[];outputs=[]
            with self.box.bind_dependencies(card.executable_dependencies):
                feedback,_,_,_=executor._run_skill_step(task,dict(skill_id=sid,code_path=card.code_path,entry_point=task.entry_point),
                    actions,attempts,history,feedbacks,outputs)
            write_json(ROOT/'native_coverage'/(task.task_id.replace('/','_')+'.json'),dict(
                artifact_id=sid,source_sha256=card.source_sha256,status=card.status,
                direct_eligible=card.direct_eligible,explicit_callable=feedback.passed,
                scope='existing native call_skill boundary; public parameters; not autonomous Actor use',
                feedback=feedback.model_dump(mode='json')))
            if feedback.passed:return True
        return False

    def collect(self):
        base=ROOT/'base'
        if not base.exists():snapshot(REPO/self.cfg['initial_library'],base)
        actor=self.native_runner(base)
        actor.postlock_training_validator=lambda task,trace:self.score(task,trace.code_history[-1] if trace.code_history else '',trace.executable_dependencies,'collect')
        completed=read(ROOT/'collect_progress.json') if (ROOT/'collect_progress.json').exists() else []
        if completed:actor._generator_state=restore_generator_state(completed[-1]['generator_state'])
        rows=[r for r in self.data['tasks'] if r['data_role']=='train']
        for offset in range(0,len(rows),16):
            for row in rows[offset:offset+16]:
                if any(x['row']['problem_id']==row['problem_id'] for x in completed):continue
                task=public_task(row);task.metadata['binary_training_feedback_allowed']=True
                label=task.task_id.replace('/','_');marker=ROOT/'jobs'/('collect_'+label+'.json')
                if marker.exists():raise PilotStop('PARTIAL_EPISODE_REQUIRES_AUDIT_NO_REISSUE')
                write_json(marker,dict(status='started',initial_library_sha256=tree_hash(base)))
                self.context('collect',label)
                result=actor.run_episode(task);trace=trace_of(result)
                score=trace.final_result['independent_training_score']
                midway=any(a.verifier_feedback and not a.verifier_feedback.passed for a in trace.attempts[:-1])
                if score['verdict']=='FULL_CHECK_FAIL' and trace.code_history and trace.failure_type!='generation_error':kind='unresolved_failure'
                elif score['verdict']=='FULL_CHECK_PASS' and midway:kind='recovered_failure'
                else:kind='no_opportunity' if score['verdict']=='FULL_CHECK_PASS' else 'engineering_error'
                # Correct executable task artifacts already present are not new acquisition.
                native_callable=trace.planning_mode=='direct_skill' and trace.success
                if kind=='recovered_failure':native_callable=self.existing_callable(actor,task,trace) or native_callable
                if native_callable and kind=='recovered_failure':kind='already_callable'
                record=dict(row=row,result=result,final_public_passed=trace.success,independent_training_score=score,
                    intermediate_public_failure=midway,source_kind=kind,ordinary_native_callable=native_callable,
                    generator_state=asdict(actor._generator_state))
                completed.append(record);write_json(ROOT/'collect_progress.json',completed)
                write_json(marker,dict(status='complete',task_id=task.task_id))
                print('collect',task.task_id,kind,score['verdict'],flush=True)
            opportunities=[x for x in completed if x['source_kind'] in {'unresolved_failure','recovered_failure'}]
            strata={x['row']['capability_family_id'] for x in opportunities}
            batch=dict(through=min(offset+16,len(rows)),opportunities=len(opportunities),candidate_strata=len(strata))
            write_json(ROOT/'batches'/f'{offset//16+1}.json',batch)
            if opportunity_target_reached(completed):return dict(tasks=completed,stop='OPPORTUNITY_TARGET_REACHED',base_hash=tree_hash(base))
        return dict(tasks=completed,stop='FIXED_TRAINING_LIMIT',base_hash=tree_hash(base))

    def scheduler(self):
        host=self.native_runner(ROOT/'acquired')
        return AcquisitionScheduler(root=ROOT/'acquisition',teacher=PilotTeacher(self.client),registry=host.skill_registry,
            primitive_store=host.primitive_store,sandbox=self.box,phase='train',max_items=3,max_attempts=2,max_operations=1,
            training_validator=lambda task,code,bundle:self.score(task,code,bundle,self.client.phase))

    def acquire(self):
        items=self.phase('collect')['tasks'];selected=[];families=set();lineages=set()
        for item in items:
            row=item['row'];family=row['capability_family_id']
            if item['source_kind'] not in {'unresolved_failure','recovered_failure'} or family in families or row['source_lineage_id'] in lineages:continue
            selected.append(item);families.add(family);lineages.add(row['source_lineage_id'])
            if len(selected)==3:break
        write_json(ROOT/'selection.json',dict(selected=[x['row']['problem_id'] for x in selected],
            rule=self.cfg['protocol']['selection'],not_confirmed_mechanism_classes=True))
        scheduler=self.scheduler();out=[]
        for item in selected:
            row=item['row'];task=public_task(row);task.metadata['binary_training_feedback_allowed']=True
            target=ROOT/'source_results'/(task.task_id.replace('/','_')+'.json')
            marker=target.with_suffix('.started')
            if target.exists():out.append(read(target));continue
            if marker.exists():raise PilotStop('PARTIAL_ACQUISITION_REQUIRES_AUDIT_NO_REISSUE')
            write_json(marker,dict(task_id=task.task_id))
            self.context('acquire',task.task_id.replace('/','_'),'teacher')
            outcome=scheduler.on_task_end(task,trace_of(item['result']),opportunity=dict(kind=item['source_kind'],
                independent_training_verdict=item['independent_training_score']['verdict'],receipt_ref=item['independent_training_score']['receipt_ref']))
            record=dict(source=row,outcome=outcome);write_json(target,record)
            out.append(record);write_json(ROOT/'acquire_progress.json',out)
        return out

    def support(self):
        scheduler=self.scheduler();out=[]
        for item in self.phase('acquire'):
            for packed in item['outcome'].get('compiled_operations',[]):
                card=scheduler.primitive_store.get(packed['primitive_id']);source=item['source']
                choices=[r for r in self.data['tasks'] if r['data_role']=='train' and r['source_lineage_id']!=source['source_lineage_id'] and r['duplicate_group_id']!=source['duplicate_group_id'] and r['capability_family_id']==source['capability_family_id']]
                words=set(re.findall('[a-z]{3,}',json.dumps(card.operation_contracts).lower()))
                def key(r):
                    arity=abs(len(r['call_protocol']['parameters'])-len(card.signature.get('args',[])))
                    overlap=len(words & set(re.findall('[a-z]{3,}',r['public_problem'].lower())))
                    return arity,-overlap,fingerprint(r['problem_id'])
                if not choices:out.append(dict(candidate_id=card.primitive_id,status='NO_SECOND_SOURCE'));continue
                chosen=min(choices,key=key)
                write_json(ROOT/'support_selections'/(card.primitive_id+'.json'),dict(source=source['problem_id'],chosen=chosen['problem_id'],rule='same sampling stratum; independent source and duplicate group; arity distance, public contract overlap, SHA; one frozen choice'))
                self.context('support',card.primitive_id,'teacher')
                out.append(scheduler.support_frozen(card.primitive_id,public_task(chosen)))
        return out

    def freeze(self):
        from run_failure_acquisition_pilot import freeze as original_freeze
        return original_freeze(self.cfg,self.data,ROOT,self.client,self.box)

    def transfer(self):
        frozen=self.phase('freeze')
        if not frozen['admitted']:return dict(status='SKIPPED_NO_ADMITTED_OPERATION',tasks=[])
        for arm in ('G','G_plus'):
            if tree_hash(ROOT/arm)!=frozen[arm+'_hash']:raise PilotStop('FROZEN_LIBRARY_DRIFT')
            if not (ROOT/(arm+'_runtime')).exists():snapshot(ROOT/arm,ROOT/(arm+'_runtime'))
        actors={arm:self.native_runner(ROOT/(arm+'_runtime'),frozen=True) for arm in ('G','G_plus')}
        results=read(ROOT/'transfer_progress.json') if (ROOT/'transfer_progress.json').exists() else []
        for i,row in enumerate(r for r in self.data['tasks'] if r['data_role']=='transfer_dev'):
            for arm in (('G','G_plus') if i%2==0 else ('G_plus','G')):
                if any(x['task_id']==row['problem_id'] and x['arm']==arm for x in results):continue
                task=public_task(row);job=arm+'_'+task.task_id.replace('/','_')
                marker=ROOT/'jobs'/('transfer_'+job+'.json')
                if marker.exists():raise PilotStop('PARTIAL_TRANSFER_REQUIRES_AUDIT_NO_REISSUE')
                write_json(marker,dict(status='started'));self.context('transfer',job)
                result=actors[arm].run_episode(task);trace=trace_of(result)
                results.append(dict(task_id=task.task_id,arm=arm,result=result,calls=trace.actual_skill_calls,
                    presented=[a.tool_input_summary for a in trace.actions if a.tool_name=='skill_presented']))
                write_json(ROOT/'transfer_progress.json',results);write_json(marker,dict(status='complete'))
                print('transfer',task.task_id,arm,'public',trace.success,flush=True)
        # All Actor programs are fixed before these diagnostic ablations. No
        # result is fed back to an Actor or used to revise a candidate.
        for item in results:
            trace=trace_of(item['result']);task=public_task(self.rows[item['task_id']])
            called={e['skill_id'] for e in item['calls'] if e['event']=='returned'} & set(frozen['admitted'])
            item['return_use_checks']=[]
            if item['arm']=='G_plus':
                for skill_id in sorted(called):
                    pack=copy.deepcopy(trace.executable_dependencies)
                    if not any(e['skill_id']==skill_id for e in pack.get('entries',{}).values()):continue
                    for entry in pack['entries'].values():
                        if entry['skill_id']==skill_id:entry['ablate_return']=True
                    self.box.context('return_use',task.task_id.replace('/','_')+'_'+skill_id)
                    with self.box.bind_dependencies(pack):fb=verify_task(task,trace.code_history[-1],self.box)
                    item['return_use_checks'].append(dict(skill_id=skill_id,ablation_passed=fb.passed,
                        return_use_established=trace.success and not fb.passed,
                        method='fixed final caller; substitute None for operation return; public validation only'))
            item['call_assessment']=dict(started=sum(e['event']=='started' for e in item['calls']),
                returned=sum(e['event']=='returned' for e in item['calls']),runtime_errors=sum(e['event']=='error' for e in item['calls']),
                semantic_preconditions='requires source and argument review; completed call does not establish semantic compliance',
                scope='public execution calls across normal attempts; final return use assessed separately')
        # All transfer programs locked before any private transfer scoring.
        for item in results:
            trace=trace_of(item['result']);task=public_task(self.rows[item['task_id']])
            item['full_score']=self.score(task,trace.code_history[-1] if trace.code_history else '',trace.executable_dependencies,'transfer_'+item['arm'])
        return dict(status='COMPLETED',tasks=results)

    def report(self):
        collected=self.phase('collect');acquired=self.phase('acquire');supported=self.phase('support');frozen=self.phase('freeze');transfer=self.phase('transfer')
        paired={}
        for row in transfer['tasks']:paired.setdefault(row['task_id'],{})[row['arm']]=row
        counts=dict(only_G_plus=0,only_G=0,both_pass=0,both_fail=0,scoring_exception=0)
        for tid,pair in paired.items():
            g,h=pair['G']['full_score']['verdict'],pair['G_plus']['full_score']['verdict']
            if g not in {'FULL_CHECK_PASS','FULL_CHECK_FAIL'} or h not in {'FULL_CHECK_PASS','FULL_CHECK_FAIL'}:counts['scoring_exception']+=1;continue
            key='both_pass' if g==h=='FULL_CHECK_PASS' else 'both_fail' if g==h else 'only_G_plus' if h=='FULL_CHECK_PASS' else 'only_G'
            counts[key]+=1
        costs={}
        for path in (ROOT/'requests').rglob('receipt.json'):
            value=read(path);stage=value['phase'];v=costs.setdefault(stage,dict(model_requests=0,tokens=0,price_upper_microusd=0,executions=0,worker_seconds=0.0))
            v['model_requests']+=1;v['tokens']+=value['usage']['total_tokens'];v['price_upper_microusd']+=value['price_bound_microusd']
        for path in ROOT.glob('**/executions/**/result.json'):
            value=read(path);stage=path.parts[path.parts.index('executions')+1]
            v=costs.setdefault(stage,dict(model_requests=0,tokens=0,price_upper_microusd=0,executions=0,worker_seconds=0.0));v['executions']+=1;v['worker_seconds']+=value['seconds']
        funnel=dict(training_tasks=len(collected['tasks']),training_stop=collected['stop'],
            credible_unresolved=sum(x['source_kind']=='unresolved_failure' for x in collected['tasks']),
            recovered_sources=sum(x['intermediate_public_failure'] and x['independent_training_score']['verdict']=='FULL_CHECK_PASS' for x in collected['tasks']),
            recovered_already_callable=sum(x['source_kind']=='already_callable' for x in collected['tasks']),
            selected_sources=len(acquired),source_teacher_attempts=sum(x['outcome'].get('teacher_attempts',0) for x in acquired),
            new_teacher_implementations=sum(x['outcome'].get('teacher_success',False) for x in acquired),
            reused_recovery_implementations=sum(x['outcome'].get('source_kind')=='native_recovery_reuse' and x['outcome'].get('source_implementation_verified',False) for x in acquired),
            executable_candidates=sum(len(x['outcome'].get('compiled_operations',[])) for x in acquired),
            independent_support_pass=sum(x.get('status')=='SUPPORT_ADMITTED' for x in supported),admitted=len(frozen['admitted']),
            actual_actor_call_starts=sum(e['event']=='started' for x in transfer['tasks'] for e in x['calls']),
            actual_actor_call_returns=sum(e['event']=='returned' for x in transfer['tasks'] for e in x['calls']),
            actual_actor_call_errors=sum(e['event']=='error' for x in transfer['tasks'] for e in x['calls']),
            tasks_with_call_but_full_failure=sum(any(e['event']=='returned' for e in x['calls']) and x['full_score']['verdict']=='FULL_CHECK_FAIL' for x in transfer['tasks']),
            final_program_return_use_established=sum(any(c['return_use_established'] for c in x['return_use_checks']) for x in transfer['tasks']))
        for item in transfer['tasks']:
            job=item['arm']+'_'+item['task_id'].replace('/','_')
            receipts=[read(p) for p in (ROOT/'requests'/'transfer'/job).rglob('receipt.json')]
            executions=[read(p) for p in (ROOT/'executions'/'transfer'/job).glob('*/result.json')]
            item['deployment_cost']=dict(model_requests=len(receipts),tokens=sum(r['usage']['total_tokens'] for r in receipts),
                price_upper_microusd=sum(r['price_bound_microusd'] for r in receipts),public_executions=len(executions),
                worker_seconds=sum(r['seconds'] for r in executions))
        result=dict(protocol_sha256=self.cfg['protocol_sha256'],funnel=funnel,paired_complete_task_results=counts,
            effect_evaluated=bool(paired),net_additional_success=counts['only_G_plus']-counts['only_G'] if paired else None,
            transfer=transfer,acquisition=acquired,support=supported,
            budget=self.budget.snapshot(),stage_costs=costs,reserved_executions=0,
            mechanism_claim='sampling strata are candidate coverage, not a count of verified distinct mechanisms',
            engineering_artifacts_not_model_learning=['method bridge','top-level operation admission','HumanEval/59 regression','taco_0875 historical manual repair regression'])
        write_json(OUT/'Experiment_Result.json',result)
        lines=['# TACO 函数技能获取：实际结果','','有限开发实验；不宣称正式评价或多机制已证实。','','|漏斗|实测|','|---|---:|']
        lines += [f'|{k}|{v}|' for k,v in funnel.items()]
        lines += ['','|完整任务配对|数量|','|---|---:|']+[f'|{k}|{v}|' for k,v in counts.items()]
        lines += ['',f"净增加成功：{result['net_additional_success']}。迁移状态：{transfer['status']}。",'',
            '来源、候选 SHA、第二来源实际调用与逐题回执见 Experiment_Result.json。未取得技能时保留具体失败层，不扩大来源池。',
            '本轮新教师实现、原生恢复复用、历史人工修复和纯工程接入分别计数；第二来源属于训练。',
            '', '|阶段|模型请求|Token|隔离执行|Worker 秒|费用上界 USD|','|---|---:|---:|---:|---:|---:|']
        lines += [f"|{k}|{v['model_requests']}|{v['tokens']}|{v['executions']}|{v['worker_seconds']:.3f}|{v['price_upper_microusd']/1e6:.6f}|" for k,v in costs.items()]
        (OUT/'Experiment_Result.md').write_text('\n'.join(lines)+'\n')
        return result

    def run(self):
        from failure_evo.pilot_runtime import save_stop_snapshot
        name='not_started';status='STOPPED';error=None
        try:
            for name in STAGES:
                target=ROOT/'phases'/(name+'.json')
                if target.exists():continue
                value=getattr(self,name)();write_json(target,dict(status='complete',result=value))
            status='COMPLETED'
            return self.phase('report')
        except BaseException as exc:
            from failure_evo.runtime import BudgetExhausted
            error=type(exc).__name__
            status='INTERRUPTED' if isinstance(exc,KeyboardInterrupt) or str(exc)=='KeyboardInterrupt' else 'BUDGET_STOP' if isinstance(exc,BudgetExhausted) or 'BUDGET' in str(exc).upper() or 'DEADLINE' in str(exc).upper() else 'EXCEPTION_STOP'
            raise
        finally:
            if hasattr(self,'budget'):
                save_stop_snapshot(ROOT,self.budget,status=status,stage=name,error_type=error)


def main():
    os.chdir(REPO)
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--authorization');args=parser.parse_args()
    if args.freeze:freeze_protocol();return
    if not args.authorization:raise SystemExit('Explicit authorization for the concrete frozen budget is required; model requests=0.')
    cfg,data=load_config()
    if os.environ.get('PYTHONHASHSEED')!='0':raise SystemExit('Run with PYTHONHASHSEED=0 for deterministic native routing.')
    result=Experiment(cfg,data,args.authorization).run()
    print(json.dumps(dict(funnel=result['funnel'],budget=result['budget']),ensure_ascii=False))


if __name__=='__main__':main()
