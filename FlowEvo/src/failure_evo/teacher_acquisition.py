"""Thin, phase-gated teacher acquisition using native compilation and stores.

No live client is constructed here. Replay responses are explicitly labeled and
never constitute evidence of model learning. Unknown delivery is never retried.
"""
import ast
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from compiler.admission import admit_compiled_trace, existing_dedup_keys
from compiler.primitive_compiler import PrimitiveCompiler
from core.schemas import ExecutionTrace, AttemptRecord
from failure_evo.acquisition_adapters import CodeAdapter
from failure_evo.acquisition_selectors import eligible_failure
from failure_evo.skill_runtime import check_source, sha

class ReplayTeacher:
    model = 'MOCK_INTERFACE_ONLY'
    def __init__(self, responses):self.responses=iter(responses);self.calls=0
    def request(self, payload, *, phase):
        if phase not in {'train', 'development'}:raise RuntimeError('TEACHER_UNAVAILABLE_IN_EVALUATION')
        self.calls += 1
        return next(self.responses)

class AcquisitionScheduler:
    def __init__(self, *, root, teacher, registry, primitive_store, sandbox, phase='train', mode='G+F', max_items=6, selected_problem_ids=None, max_attempts=1, max_operations=None, training_validator=None):
        from failure_evo.pilot_runtime import PilotTeacher
        if not isinstance(teacher, (ReplayTeacher, BudgetedTeacher, PilotTeacher)):
            raise PermissionError("REPLAY_OR_BUDGETED_TEACHER_REQUIRED")
        if max_attempts not in (1,2):raise ValueError("ACQUISITION_ATTEMPT_BOUND")
        self.max_attempts=max_attempts;self.max_operations=max_operations
        self.selected_problem_ids = None if selected_problem_ids is None else frozenset(selected_problem_ids)
        self.root=Path(root);self.root.mkdir(parents=True, exist_ok=True)
        self.is_mock=isinstance(teacher,ReplayTeacher) or bool(getattr(getattr(teacher,'transport',None),'dry',False))
        self.teacher=teacher;self.registry=registry;self.primitive_store=primitive_store
        self.sandbox=sandbox;self.phase=phase;self.mode=mode;self.max_items=max_items
        self.count=sum(bool(json.loads(p.read_text()).get('teacher_attempts',0)) for p in self.root.glob('*/result.json'))
        self.adapter=CodeAdapter()
        self.training_validator=training_validator

    def _independent_check(self,task,code,bundle):
        if self.training_validator is None:return None
        result=self.training_validator(task,code,bundle)
        if set(result)-{'verdict','receipt_ref','source_sha256','dependency_bundle_sha256'}:
            raise ValueError('PRIVATE_TRAINING_PROJECTION_VIOLATION')
        return result

    def on_task_end(self, task, student, *, opportunity=None):
        if self.phase not in {'train','development'}:raise RuntimeError('TEACHER_UNAVAILABLE_IN_EVALUATION')
        if self.selected_problem_ids is not None and task.task_id not in self.selected_problem_ids:
            return dict(status='NOT_SELECTED',reason='not_in_frozen_selection',problem_id=task.task_id)
        record=dict(problem_id=task.task_id, domain='code', data_role=task.metadata.get('data_role'), success=student.success,
                    failure_type=student.failure_type, execution_confirmed=bool(student.attempts and student.verifier_feedback and student.verifier_feedback[-1].executed_code),
                    capability_family_id=task.metadata.get('capability_family_id','unclassified'),
                    source_lineage_id=task.metadata.get('source_lineage_id',task.task_id),
                    duplicate_group_id=task.metadata.get('duplicate_group_id',task.task_id), exposure_status='exposed',
                    actor=task.metadata.get('actor_model','unspecified'), actor_config=task.metadata.get('actor_config',{}),
                    initial_library=task.metadata.get('initial_library','unspecified'), observed_at=datetime.now(timezone.utc).isoformat(),
                    evidence_trace_id=student.trace_id, evidence_sha256=sha(student.model_dump_json()))
        recovered=False
        if opportunity is not None:
            if task.metadata.get('data_role')!='train' or not task.metadata.get('binary_training_feedback_allowed'):
                raise ValueError('NEW_TRAINING_FEEDBACK_PERMISSION_REQUIRED')
            if set(opportunity)-{'kind','independent_training_verdict','receipt_ref'}:
                raise ValueError('OPPORTUNITY_PROJECTION_VIOLATION')
            recovered=opportunity['kind']=='recovered_failure'
            eligible=(opportunity['kind']=='unresolved_failure' and opportunity['independent_training_verdict']=='FULL_CHECK_FAIL'
                      or recovered and opportunity['independent_training_verdict']=='FULL_CHECK_PASS')
        else:eligible=eligible_failure(record)
        if self.mode=='G' or self.mode=='G+F' and not eligible:return dict(status='NOT_SELECTED', record=record)
        if self.mode not in {'G+F','G+U'}:raise ValueError('UNKNOWN_SELECTOR')
        # Selection of a bounded batch is done by acquisition_selectors.select.
        key=sha(task.task_id)[:20];folder=self.root/key;folder.mkdir(exist_ok=True)
        if (folder/'result.json').exists():return json.loads((folder/'result.json').read_text())
        result=dict(observed_failure=record if not student.success else None, source_record=record,
                    capability=dict(capability_family_id=record['capability_family_id'], judgment='candidate_hypothesis', failure_trace=student.trace_id if not student.success else None),
                    start_mode='fresh_task', teacher_model=self.teacher.model, response_kind='mock' if self.is_mock else 'live',
                    student_success=student.success, teacher_success=False, status='PREPARED', paid_model_requests=0)
        result['source_kind']='native_recovery_reuse' if recovered else 'teacher_new_implementation'
        if recovered:result['response_kind']='native_existing_recovery'
        result['opportunity']=opportunity
        def save():
            (folder/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
            return result
        if self.count>=self.max_items:result['status']='ACQUISITION_BUDGET_EXHAUSTED';return save()
        try:
            public=self.adapter.public_view(task)
        except ValueError as exc:
            result.update(status='ADAPTER_NOT_READY' if str(exc)=='ADAPTER_NOT_READY' else 'VALIDATION_NOT_READY',reason=str(exc))
            return save()
        # Use only public-verifier receipt, never student hidden scoring feedback.
        attempt=student.code_history[-1] if student.code_history else ''
        source_bundle=student.executable_dependencies if recovered else {}
        with self.sandbox.bind_dependencies(student.executable_dependencies):
            public_feedback=self.adapter.verify(task,attempt,self.sandbox,public)
        payload=dict(task=public, original_attempt=attempt, feedback=dict(passed=public_feedback.passed,summary=public_feedback.summary,stderr=public_feedback.stderr),
                     interface='Complete Python implementation. Parameterized reusable functions where natural; describe purpose, arguments/types, preconditions, output, side effects, failure behavior. Do not use private tests.', start_mode='fresh_task')
        if opportunity is not None:payload['independent_training_feedback']=opportunity['independent_training_verdict']
        wire=json.dumps(payload,ensure_ascii=False)
        result['request']=payload;result['input_measurement']=dict(serialized_bytes=len(wire.encode()),input_token_estimate=None,provider_input_tokens=None,output_token_limit=None,reasoning_limit=None,source_bytes_limit=64000,worker_state_limit=None,worker_return_limit=None)
        (folder/'student_trace.json').write_text(student.model_dump_json(indent=2))
        self.count+=1
        result['teacher_attempts']=0
        result['attempt_records']=[]
        feedback=None
        code=''
        contracts={}
        for attempt_index in range(1 if recovered else self.max_attempts):
            if recovered:
                # Interface description only: preserve the actual recovery module.
                entry=public['entry_point'];spec=task.metadata.get('call_protocol',{})
                response=dict(code=attempt,operations={entry:dict(
                    purpose='Parameterized implementation of the public task: '+task.prompt,
                    parameters={name:'as specified in the public task' for name in spec.get('parameters',[])},
                    preconditions='The public task input contract applies.',output=spec.get('returns') or 'public task return value',
                    side_effects='as in the preserved source; isolated execution',failure='unsupported outside the stated input contract')})
            else:
                result['teacher_attempts']+=1
                try:
                    response=self.teacher.request(payload,phase=self.phase)
                except BaseException as exc:
                    result.update(status='TEACHER_DELIVERY_STOP',reason=type(exc).__name__)
                    save()
                    raise
            result['paid_model_requests']=0 if self.is_mock else result['teacher_attempts']
            result['source_output' if recovered else 'teacher_output']=response
            if isinstance(response,dict) and isinstance(response.get('receipt'),dict):
                result['input_measurement'].update(response['receipt'])
            code=response.get('code','') if isinstance(response,dict) else ''
            contracts=response.get('operations',{}) if isinstance(response,dict) else {}
            if not isinstance(contracts,dict):contracts={}
            feedback=None
            reason=''
            try:
                if not isinstance(code,str) or not code or len(code.encode())>64000:raise ValueError('EMPTY_OR_OVERSIZE_SOURCE')
                if task.benchmark=='taco' and not recovered:
                    from env.taco_function_loader import adapt_candidate
                    code=adapt_candidate(code,public['entry_point'])
                check_source(code)
                tree=ast.parse(code)
                if not any(isinstance(n,ast.FunctionDef) and n.name==public['entry_point'] for n in tree.body):raise ValueError('MISSING_ENTRY')
            except (ValueError,SyntaxError) as exc:
                result['status']='TEACHER_INCOMPLETE';reason=str(exc)
            else:
                with self.sandbox.bind_dependencies(source_bundle):
                    feedback=self.adapter.verify(task,code,self.sandbox,public)
                result['verification']=feedback.model_dump(mode='json')
                result['status']='SOURCE_VERIFIED' if feedback.passed else 'TEACHER_VERIFICATION_FAILED'
            independent=self._independent_check(task,code,source_bundle) if feedback and feedback.passed else None
            full_pass=independent is None or independent['verdict']=='FULL_CHECK_PASS'
            result['attempt_records'].append(dict(index=attempt_index,response=response,feedback=feedback.model_dump(mode='json') if feedback else None,reason=reason,independent_training_score=independent))
            save()
            if feedback is not None and feedback.passed and full_pass:break
            payload={**result['request'],'revision':dict(previous_response=response,feedback=feedback.model_dump(mode='json') if feedback else dict(delivery_error=reason),independent_training_score=independent)}
        if feedback is None or not feedback.passed or not full_pass:
            if feedback and feedback.passed:result['status']='INDEPENDENT_TRAINING_VERIFICATION_FAILED'
            return save()
        result['teacher_success']=not recovered
        result['source_implementation_verified']=True
        trace=ExecutionTrace(trace_id=('recovery_' if recovered else 'teacher_')+uuid.uuid4().hex,task_id=task.task_id,family=task.benchmark,benchmark=task.benchmark,query=task.prompt,
             success=True,code_history=[code],attempts=[AttemptRecord(attempt_index=0,stage='teacher_acquisition',candidate_code=code,verifier_feedback=feedback)],verifier_feedback=[feedback],
             executable_dependencies=source_bundle,
             validated_entry_point=public['entry_point'], independent_source_ids=[record['source_lineage_id']],operation_contracts=contracts,episode_provenance='recovery_reuse_success' if recovered else 'teacher_acquisition_success',task_pattern=student.task_pattern)
        (folder/('recovery_success_trace.json' if recovered else 'teacher_success_trace.json')).write_text(trace.model_dump_json(indent=2))
        result['source_trace_id']=trace.trace_id
        if not recovered:result['teacher_trace_id']=trace.trace_id
        admitted=admit_compiled_trace(trace,provenance=trace.episode_provenance,registry=self.registry,timeout_seconds=self.sandbox.timeout_seconds,sandbox=self.sandbox,dedup_keys=existing_dedup_keys(self.registry))
        result['native_admission']=admitted.__dict__
        candidates=PrimitiveCompiler().compile_success_primitives(trace)
        # The teacher must actually supply an operation contract; no human splitting.
        candidates=[c for c in candidates if isinstance(contracts.get(c.card.helper_name),dict) and all(k in contracts[c.card.helper_name] for k in ['purpose','parameters','preconditions','output','side_effects','failure'])]
        if self.max_operations is not None:candidates=candidates[:self.max_operations]
        result['compiled_operations']=[]
        for c in candidates:
            # Native gatekeeper success is necessary; drafts do not get forced active.
            if not admitted.admitted:continue
            card=self.primitive_store.observe_candidate(c.card,c.code)
            result['compiled_operations'].append(card.model_dump(mode='json'))
        result['status']=('SUCCESS_WITHOUT_REUSABLE_OPERATION' if not candidates else 'ADMITTED_EXECUTABLE_SKILL' if any(c['status']=='active' for c in result['compiled_operations']) else 'COMPILED_NOT_ADMITTED')
        return save()

    def support_frozen(self, candidate_id, task):
        """One preselected independent training task; only the calling program may change."""
        from failure_evo.skill_runtime import bundle_from_cards
        from failure_evo.pilot_runtime import write_json
        if self.phase!='train' or task.metadata.get('data_role')!='train':
            raise RuntimeError('DRAFT_ONLY_IN_TRAINING_SUPPORT')
        card=self.primitive_store.get(candidate_id)
        if card is None:raise ValueError('MISSING_CANDIDATE')
        lineage=task.metadata['source_lineage_id']
        frozen=card.source_sha256
        folder=self.root/'supports'/candidate_id
        result_path=folder/'result.json'
        if result_path.exists():
            cached=json.loads(result_path.read_text())
            if (cached.get('sha256'),cached.get('support_problem_id'),cached.get('source_lineage_id'))!=(frozen,task.task_id,lineage):
                raise ValueError('SUPPORT_REPLAY_IDENTITY_DRIFT')
            return cached
        if (folder/'started.json').exists():
            from failure_evo.pilot_runtime import PilotStop
            raise PilotStop('PARTIAL_SUPPORT_REQUIRES_AUDIT_NO_REISSUE')
        if lineage in card.independent_source_ids:raise ValueError('SUPPORT_SOURCE_NOT_INDEPENDENT')
        pack=bundle_from_cards([card.model_dump(mode='json')],training_support=(candidate_id,frozen))
        call=pack['card_names'][candidate_id]
        public=self.adapter.public_view(task)
        payload=dict(task=public,frozen_operation=dict(skill_id=candidate_id,sha256=frozen,
            import_statement='from flowevo_skills import '+call,contract=card.operation_contracts.get(card.helper_name,{})),
            requirement='Solve this complete training task by using the frozen operation return value. Do not redefine, modify, or replace that operation.')
        outcome=dict(candidate_id=candidate_id,sha256=frozen,support_problem_id=task.task_id,
            source_lineage_id=lineage,attempts=[],status='SUPPORT_FAILED')
        write_json(folder/'started.json',dict(candidate_id=candidate_id,sha256=frozen,support_problem_id=task.task_id))
        for i in range(self.max_attempts):
            response=self.teacher.request(payload,phase='train')
            code=response.get('code','') if isinstance(response,dict) else ''
            feedback=None;events=[];ablation=None;reason='';independent=None
            try:
                if not isinstance(code,str) or not code or len(code.encode())>64000:raise ValueError('EMPTY_OR_OVERSIZE')
                if task.benchmark=='taco':
                    from env.taco_function_loader import adapt_candidate
                    code=adapt_candidate(code,public['entry_point'])
                check_source(code)
                tree=ast.parse(code)
                if any(isinstance(n,(ast.FunctionDef,ast.Assign)) and getattr(n,'name','')==call for n in ast.walk(tree)):
                    raise ValueError('FROZEN_BINDING_REDEFINED')
                with self.sandbox.bind_dependencies(pack):
                    feedback=self.adapter.verify(task,code,self.sandbox,public)
                    events=list(self.sandbox.skill_events)
                returned=any(e['event']=='returned' and e['sha256']==frozen for e in events)
                independent=self._independent_check(task,code,pack) if feedback.passed and returned else None
                full_pass=independent is None or independent['verdict']=='FULL_CHECK_PASS'
                if feedback.passed and returned and full_pass:
                    # Return-value dependence: same helper, same arguments, substitute None.
                    # Conservative: legitimate uses insensitive to this ablation remain unqualified.
                    poison=json.loads(json.dumps(pack));poison['entries'][call]['ablate_return']=True
                    with self.sandbox.bind_dependencies(poison):
                        ablation=self.adapter.verify(task,code,self.sandbox,public)
                    if not ablation.passed:
                        evidence=dict(task_id=task.task_id,source_lineage_id=lineage,sha256=frozen,passed=True,
                            actual_calls=events,return_use_verified=True,program_sha256=sha(code),
                            ablation_passed=False,evidence_path=str(result_path))
                        accepted=self.primitive_store.observe_support(candidate_id,evidence)
                        outcome.update(status='SUPPORT_ADMITTED',card=accepted.model_dump(mode='json'))
                    else:reason='RETURN_USE_NOT_ESTABLISHED'
                elif not returned:reason='FROZEN_OPERATION_NOT_CALLED'
                elif not full_pass:reason='INDEPENDENT_TRAINING_VERIFICATION_FAILED'
            except (ValueError,SyntaxError,TypeError) as exc:reason=str(exc)
            receipt=dict(index=i,response=response,feedback=feedback.model_dump(mode='json') if feedback else None,
                actual_calls=events,ablation=ablation.model_dump(mode='json') if ablation else None,reason=reason,
                independent_training_score=independent)
            outcome['attempts'].append(receipt)
            if self.primitive_store.get(candidate_id).source_sha256!=frozen:raise RuntimeError('FROZEN_CANDIDATE_DRIFT')
            if outcome['status']=='SUPPORT_ADMITTED':break
            payload={**payload,'revision':receipt}
        write_json(result_path,outcome)
        return outcome

class BudgetedTeacher:
    """Explicit future transport; disabled unless independently authorized/configured.

    Uses the existing durable budget and network send boundary. The preparation
    command never constructs an enabled instance. No hidden automatic revision.
    """
    def __init__(self, *, model, budget, network_policy, root, allow_real_requests=False,
                 input_token_upper=32768, output_tokens=8192, max_request_bytes=131072):
        if not allow_real_requests:raise PermissionError('REAL_REQUESTS_DISABLED')
        from failure_evo.persistent_budget import PersistentBudget
        if not isinstance(budget,PersistentBudget):raise TypeError('DURABLE_BUDGET_REQUIRED')
        self.model=model;self.budget=budget;self.network_policy=network_policy;self.root=Path(root)
        self.input_token_upper=input_token_upper;self.output_tokens=output_tokens;self.max_request_bytes=max_request_bytes
        self.calls=0;self.last_receipt={}

    def request(self, payload, *, phase):
        if phase not in {'train','development'}:raise RuntimeError('TEACHER_UNAVAILABLE_IN_EVALUATION')
        from failure_evo.contracts import canonical, fingerprint
        from failure_evo.model_api import configured_api_key
        from failure_evo.network_transport import post_deepseek
        from failure_evo.run_health import trusted_usage
        wire=dict(model=self.model,messages=[dict(role='system',content='Return JSON with complete Python code and operations (contracts keyed by helper name). Solve the public training task; parameterize repeated operations where natural. No private tests or external access.'),dict(role='user',content=canonical(payload))],max_tokens=self.output_tokens,thinking={'type':'disabled'},stream=False,response_format={'type':'json_object'})
        serialized=len(canonical(wire).encode());upper=serialized+256
        if serialized>self.max_request_bytes or upper>self.input_token_upper:raise ValueError('INPUT_LIMIT_NO_TRUNCATION')
        rid='teacher/'+fingerprint(wire);folder=self.root/rid;folder.mkdir(parents=True,exist_ok=True)
        if (folder/'request.json').exists():raise RuntimeError('CONSUMED_REQUEST_NO_REISSUE')
        self.budget.reserve_network(upper,self.output_tokens,job_id=rid,capability='teacher',request_id=rid,request_hash=fingerprint(wire),policy=self.network_policy,wire_hash=fingerprint(wire))
        (folder/'request.json').write_text(canonical(wire));self.calls+=1
        raw=post_deepseek(wire,configured_api_key(),budget=self.budget,request_id=rid,policy=self.network_policy)
        (folder/'response.json').write_text(canonical(raw));usage=trusted_usage(raw)
        if not usage:self.budget.settle(rid);raise RuntimeError('UNKNOWN_USAGE_STOP')
        self.budget.settle(rid,tokens=usage['total_tokens'])
        self.last_receipt=dict(request_id=rid,model=self.model,serialized_bytes=serialized,input_token_upper=upper,usage=usage,output_limit=self.output_tokens,reasoning_limit=0)
        if raw['choices'][0]['finish_reason']!='stop':return dict(code='',delivery='INCOMPLETE',receipt=self.last_receipt)
        try:response=json.loads(raw['choices'][0]['message']['content'])
        except (ValueError,TypeError):return dict(code='',delivery='MALFORMED',receipt=self.last_receipt)
        if not isinstance(response,dict):return dict(code='',delivery='MALFORMED',receipt=self.last_receipt)
        response['receipt']=self.last_receipt
        return response
