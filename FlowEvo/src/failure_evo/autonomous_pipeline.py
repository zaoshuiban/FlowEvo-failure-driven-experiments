"""Executable checkers around existing LearningPipeline; no host repair algorithms."""
from dataclasses import asdict,replace
import ast,hashlib,json,time
from pathlib import Path
from .contracts import fingerprint,canonical,PublicTaskView,PublicFeedback
from .pipeline import LearningPipeline
from .data_roles import validate_data_roles
from .autonomous_mechanism import VERSION,parse_mechanism
from .autonomous_generation import MechanismHypothesis,GeneratedOperator,OperatorValidation
from .autonomous_mvp import AutonomousMVP,DeterministicRunner,LinuxPublicEvaluator,FrozenLinuxBackend
from .model_api import validate_compile_output
from .failure_registry import FailureOperator
from .plugin import FailureLearningPlugin
from .evidence import EvidenceStore

class ExecutableLearningPipeline(LearningPipeline):
    def __init__(self,root,compiler,evaluation_budget,registry,context,backend,*,input_validators,candidate_limit=1):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        if not isinstance(backend,FrozenLinuxBackend):raise ValueError('actual frozen Linux backend required')
        self.registry=registry;self.context=context;self.backend=backend
        self.input_validators=dict(input_validators)
        self.runner=DeterministicRunner(backend);self.evaluator=LinuxPublicEvaluator(backend)
        self._engine=AutonomousMVP(self.root/'execution',compiler,self.runner,self.evaluator,registry,context,evaluation_budget)
        super().__init__(self.root/'pipeline.jsonl',compiler,evaluation_budget,self._design,self._gate,
                         candidate_limit=candidate_limit,hypothesis_validator=self._hypothesis,revise_failed_only=True,delegate_static_validation=True)

    def _save(self,name,value):
        p=self.root/name;data=canonical(value)+'\n'
        if p.exists() and p.read_text()!=data:raise ValueError('immutable artifact changed')
        p.write_text(data);return p

    def run(self,public_job,*,design,gate,regression,at,revise=False,data_manifest=None):
        if data_manifest is None:raise ValueError('all five data roles required')
        validate_data_roles(data_manifest)
        if not public_job.get('discovery',{}).get('evidence'):raise ValueError('admitted public evidence required')
        if set(public_job['evidence_ids'])!={x['event_id'] for x in public_job['discovery']['evidence']}:
            raise ValueError('discovery binding mismatch')
        self.job=public_job;self.at=at;self.manifest=data_manifest
        # Frozen role membership includes exact task/code/test content, not just labels.
        for role in ('design','gate','regression','test'):
            data=data_manifest[role]
            if not data.get('cases'):raise ValueError('nonempty executable cases required: '+role)
            expected={i['problem_id']:i['source_lineage'] for i in data['items']}
            if {c['task']['problem_id']:c['lineage_id'] for c in data['cases']}!=expected:
                raise ValueError('case membership differs from role manifest')
            for c in data['cases']:
                validator=self.input_validators.get(c['task']['problem_id'])
                if not validator or not c['task'].get('public_examples'):
                    raise ValueError('reviewed validation input grammar required')
                if any(not validator.verify(c['task'],v['input'])['valid'] for v in c['task']['public_examples']):
                    raise ValueError('illegal validation input')
            if any(c.get('expectation') not in ('repair','decline') for c in data['cases']):raise ValueError('explicit case expectation required')
        source=[]
        for e in public_job['discovery']['evidence']:
            task=dict(e['task']);task['public_examples']=[dict(c,visibility='public',legal_verified=True) for c in e['task']['public_examples']]
            source.append(dict(case_id=e['event_id'],task=task,code=e['code'],lineage_id=e['lineage_id'],expectation='repair'))
        self.sources=source
        self._save('roles.json',data_manifest)
        result=super().run(public_job,design=design,gate=gate,regression=regression,at=at,revise=revise,data_manifest=data_manifest)
        if result.get('winner'):
            winner=result['winner'];v=winner['evaluation'];ind=result.get('validation',[])
            validation=OperatorValidation(hashlib.sha256(winner['code'].encode()).hexdigest(),v['static'],tuple(v['source']),
                tuple(ind[0]['rows'] if ind else []),tuple(ind[1]['rows'] if len(ind)>1 else []),
                dict(evaluation_budget=self.budget.snapshot(),compiler_budget=self.compiler.budget.snapshot(),worker=self.backend.manifest()),
                result['status'],'MOCK_ONLY' if self.compiler.provider.mock else 'HOST_PUBLIC_VALIDATION_NOT_CAUSAL')
            self._save('operator_validation.json',asdict(validation))
        self._save('result.json',result)
        return result

    def _hypothesis(self,spec,job):
        h=parse_mechanism(json.loads(spec))
        if set(h['source_evidence_ids'])!=set(job['evidence_ids']):raise ValueError('invented or omitted source event')
        self.h=h
        responses=[r['payload']['response'] for r in self.compiler.events.records() if r['kind']=='GENERATION_RESPONSE']
        response=responses[-1]
        obj=MechanismHypothesis(fingerprint([job['job_id'],h]),tuple(job['evidence_ids']),
            tuple(sorted({x['task']['problem_id'] for x in job['discovery']['evidence']})),
            tuple(sorted({x['lineage_id'] for x in job['discovery']['evidence']})),h,
            response['wire_sha256'],response['response_sha256'],response['origin'])
        self.hid=obj.hypothesis_id;self._save('hypothesis.json',asdict(obj))
        return h

    def _card(self,code):
        digest=hashlib.sha256(code.encode()).hexdigest();path=self.root/(digest+'.py')
        if path.exists() and path.read_text()!=code:raise ValueError('source changed')
        path.write_text(code)
        kind=self.h['suggested_operator_kind']
        return FailureOperator('auto-'+self.hid[:16],digest[:16],str(path.resolve()),digest,self.context,VERSION,
            tuple(self.job['evidence_ids']),tuple(sorted(set(self.manifest['discovery']['source_groups'])|set(self.manifest['design']['source_groups']))),
            hooks=('before_native_start',) if kind=='task_solver' else ('before_native_retry',),
            stages=('l1',) if kind=='task_solver' else ('l2a','l2b','l3','l4'),
            allowed_feedback=('NO_COMPLETE_CODE',) if kind=='task_solver' else ('WRONG_ANSWER','RUNTIME_ERROR','COMPILE_ERROR','NO_COMPLETE_CODE'),
            structural_statuses=('NO_COMPLETE_CODE',) if kind=='task_solver' else ('STRUCTURAL_PASS','COMPILE_ERROR','NO_COMPLETE_CODE'),
            allowed_actions=('candidate_code',),max_seconds=5,operator_kind=kind)

    def _cases(self,card,cases):
        rows=[]
        for case in cases:
            row=self._engine._case(card,case,at_start=card.operator_kind=='task_solver')
            row['expectation']=case['expectation']
            row['eligible']=(row['action']=='declined' if case['expectation']=='decline' else row['source_effective']) and not row['regressed']
            rows.append(row)
        return rows

    def _design(self,code,data,timeout):
        static=validate_compile_output(dict(code=code,description='host static review',applicability='unverified'))
        # Narrow identity/answer-table lint is not a semantic anti-hardcoding proof.
        findings=[]
        try:
            tree=ast.parse(code)
            for n in ast.walk(tree):
                if isinstance(n,ast.Subscript) and isinstance(n.slice,ast.Constant) and n.slice.value=='problem_id':findings.append('TASK_ID_LOOKUP')
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='get' and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=='problem_id':findings.append('TASK_ID_LOOKUP')
            if any(e['task']['problem_id'] in code for e in self.job['discovery']['evidence']):findings.append('SOURCE_ID_LITERAL')
        except SyntaxError:pass
        if findings:
            static['errors']+=sorted(set(findings));static['static_pass']=False
        static['specialization_check']='limited task-ID lint; behavior gates still required'
        card=self._card(code)
        # Keep every model candidate/version even if functionally unsuccessful.
        response=next(r['payload']['response'] for r in reversed(self.compiler.events.records()) if r['kind']=='GENERATION_RESPONSE' and r['payload']['response'].get('code')==code)
        prior=[r['payload'] for r in self.events.records() if r['kind']=='GENERATED_OPERATOR']
        same=[r for r in prior if r['code_sha256']==card.artifact_sha256]
        phase_rows=[r['payload'] for r in self.compiler.events.records() if r['kind']=='GENERATION_REQUESTED']
        request=phase_rows[-1]
        parent=hashlib.sha256(request['code'].encode()).hexdigest() if request['phase']=='revision' else ''
        op=GeneratedOperator(self.hid,card.operator_id,card.version,parent,card.operator_kind,code,card.artifact_sha256,
            card.artifact_path,VERSION,'runtime_projection; task_solver receives empty candidate','applied candidate_code / declined / error',
            response['applicability'],response['model'],response['id'],response['response_sha256'],response['wire_sha256'],response['usage'],
            response.get('quoted_cost_estimate_microusd',response.get('reserved_rate_estimate_microusd',0)),response['origin'])
        self.events.append('GENERATED_OPERATOR',dict(asdict(op),duplicate_capability=bool(same)),self.at)
        if static['static_pass'] and not self.registry._rows(card):self.registry.register(card,self.at)
        source=self._cases(card,self.sources) if static['static_pass'] else []
        design=self._cases(card,data['cases']) if source and all(r['eligible'] for r in source) else []
        eligible=bool(source) and all(r['eligible'] for r in source) and bool(design) and all(r['eligible'] for r in design)
        return dict(eligible=eligible,score=sum(r['eligible'] for r in source+design),static=static,
                    source=source,design=design,card=card.to_dict(),source_effective=bool(source) and all(r['eligible'] for r in source))

    def _gate(self,code,data,timeout):
        card=self._card(code);rows=self._cases(card,data['cases'])
        result=dict(eligible=all(r['eligible'] for r in rows),score=sum(r['eligible'] for r in rows),rows=rows,
                    contract_checks_passed=True,scope_checks_passed=all(r['eligible'] for r in rows))
        self._save('validation-'+data['shard_id']+'.json',result)
        return result

    def authorize(self,result,*,experiment_id,stream_id,after_task,effective_from,at,engineering=False):
        # Existing registry remains permission owner; no model-provided booleans.
        saved=json.loads((self.root/'result.json').read_text())
        if saved!=json.loads(canonical(result)) or result['status']!='ready_for_experimental_review':raise ValueError('independent host validation not passed')
        winner=result['winner'];card=FailureOperator.from_dict(winner['evaluation']['card'])
        origin=next(r['payload']['origin'] for r in reversed(self.events.records()) if r['kind']=='GENERATED_OPERATOR' and r['payload']['code_sha256']==card.artifact_sha256)
        engineering_data=any(i.get('engineering_only') for role in self.manifest.values() for i in role['items'])
        if (origin=='MOCK' or engineering_data) and not (engineering and experiment_id.startswith('engineering:') and stream_id.startswith('engineering:')):raise PermissionError('Mock cannot authorize research use')
        source=winner['evaluation']['source'][0];path=self.root/'result.json';digest=hashlib.sha256(path.read_bytes()).hexdigest()
        future={i['problem_id']:i['source_lineage'] for i in self.manifest['test']['items']}
        excluded=[i['problem_id'] for role in ('discovery','design','gate','regression') for i in self.manifest[role]['items']]
        checks={k:dict(passed=True,evidence_sha256=digest,artifact_sha256=card.artifact_sha256,execution='isolated_actual_source') for k in ('static_contract','isolated_worker','source_repair','boundary','inapplicable','host_fallback')}
        # Fallback must be a separate bound engineering receipt, not a fabricated success.
        fallback=self.root/'fallback_acceptance.json'
        if not fallback.exists():raise ValueError('actual Controller fallback acceptance required')
        f=json.loads(fallback.read_text())
        if f.get('artifact_sha256')!=card.artifact_sha256 or f.get('passed') is not True:raise ValueError('fallback receipt mismatch')
        checks['host_fallback']['evidence_sha256']=hashlib.sha256(fallback.read_bytes()).hexdigest()
        checks['source_repair'].update(event_id=self.sources[0]['case_id'],original_sha256=source['original_sha256'],host_public_outcome='passed',action='applied',tests_run=source['after']['tests_run'],tests_passed=source['after']['tests_passed'])
        if not any(r['expectation']=='decline' and r['eligible'] for v in result['validation'] for r in v['rows']):raise ValueError('independent refusal gate required')
        report=dict(role='NURSERY_ADMISSION',operator_id=card.operator_id,version=card.version,artifact_sha256=card.artifact_sha256,
            fingerprint=card.evidence_fingerprint.to_dict(),scope=card.evidence_scope,evidence_ids=list(card.evidence_ids),experiment_id=experiment_id,
            evaluated_at=at,files=[dict(path=str(path.resolve()),sha256=digest),dict(path=str(fallback.resolve()),sha256=checks['host_fallback']['evidence_sha256'])],
            checks=checks,future_tasks=future,excluded_task_ids=excluded,engineering_only=origin=='MOCK' or engineering_data,independent_validation=True,
            data_manifest_sha256=fingerprint(self.manifest),worker=self.backend.manifest())
        gate=self._save('admission.json',report)
        self.registry.admit_nursery(card,gate,experiment_id=experiment_id,stream_id=stream_id,after_task=after_task,effective_from=effective_from,at=at,opportunity_limit=min(5,len(future)))
        return card

class ExecutableOperatorHook(FailureLearningPlugin):
    def begin(self,task,at):
        super().begin(task,at)
        snapshot=self.current['snapshot'];cards=[]
        for card in snapshot.cards:
            auth=self.registry.state(card,at)['authorization']
            report=json.loads(Path(auth['gate_path']).read_text())
            if card.evidence_scope!=VERSION or report.get('role')!='NURSERY_ADMISSION':continue
            if report.get('engineering_only') and not self.stream_id.startswith('engineering:'):continue
            if task.problem_id in report.get('excluded_task_ids',[]) or task.problem_id not in report.get('future_tasks',{}):continue
            cards.append(card)
        self.current['snapshot']=replace(snapshot,cards=tuple(cards),snapshot_id=fingerprint([snapshot.snapshot_id,[c.to_dict() for c in cards]]))

    # (Methods below are deliberately not attached to the runtime Hook.)

def verify_controller_fallback(pipeline,result):
    """Engineering-only native fallback probe using the exact winning artifact.

    The temporary registry double exposes no mutation or production authorization.
    Solver responses are fixed fixtures; actual operator/program execution uses
    Linux. This is safety plumbing evidence, never model or causal benefit evidence.
    """
    from .failure_registry import OperatorSnapshot
    from .failure_events import FailureEvidenceStore
    from .runtime import Budget
    from .workflow_runtime_v2 import PreparedController
    if result.get('status')!='ready_for_experimental_review':raise ValueError('no gate winner')
    card=FailureOperator.from_dict(result['winner']['evaluation']['card'])
    case=next(c for role in ('regression','gate') for c in pipeline.manifest[role]['cases'] if c['expectation']=='decline')
    class ProbeRegistry:
        def snapshot(self,**kw):return OperatorSnapshot('engineering-probe',kw['stream_id'],kw['task_index'],(card,),kw['experiment_id'],kw['at'])
        def valid(self,c,at):return c.intact()
    ev=FailureEvidenceStore(pipeline.root/'fallback_probe_evidence.jsonl')
    hook=FailureLearningPlugin(ProbeRegistry(),ev,pipeline.context,stream_id='engineering:fallback',runner=pipeline.runner,synthetic=True)
    calls=[]
    def generator(payload,budget):
        calls.append(payload)
        return dict(model=pipeline.context.model,code=case['code'] if card.operator_kind=='task_solver' or len(calls)>1 else 'pass',usage={'total_tokens':0})
    out=PreparedController(generator,pipeline.evaluator,pipeline.context,plugin=hook,allow_task_start=True).solve(case['task'],Budget(max_tools=30,wall_seconds=120))
    passed=out['status']=='PUBLIC_ACCEPTED' and out['selected']['code']==case['code'] and any(h['status']=='declined' for h in out['hook_events'])
    receipt=dict(passed=passed,artifact_sha256=card.artifact_sha256,engineering_mock_solver=True,new_model_requests=0,
                 exact_operator_executed=any(h.get('operator_id')==card.operator_id for h in out['hook_events']),result=out)
    pipeline._save('fallback_acceptance.json',receipt)
    return receipt
