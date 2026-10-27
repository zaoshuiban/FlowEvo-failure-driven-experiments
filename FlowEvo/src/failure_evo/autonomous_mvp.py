"""Minimal autonomous Python-operator discovery, evaluation and task-boundary release.

No algorithm is provided by this host. Existing compiler, static policy, sandbox,
registry, quota and Controller hooks remain the execution/permission authorities.
"""
from dataclasses import asdict, dataclass
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import fcntl
from .contracts import canonical, fingerprint, PublicFeedback, PublicTaskView
from .autonomous_generation import (PROTOCOL, MechanismHypothesis, GeneratedOperator,
                                    OperatorValidation, parse_hypothesis)
from .evidence import EvidenceStore
from .model_api import validate_compile_output
from .runtime import SandboxOperatorRunner
from .failure_registry import FailureOperator
from .plugin import FailureLearningPlugin


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def public_checkpoint(store, event_id, checkpoint, *, at, allow_synthetic=False):
    """A frozen host sidecar supplies public checks absent from FailureEvidenceStore.

    Hash/time/source binding is checked, but legality still needs a trusted task
    grammar audit. The caller must retain that audit; model assertions never count.
    """
    fact = next((e for e in store.visible(at) if e['event_id']==event_id), None)
    if fact is None or (fact['synthetic'] and not allow_synthetic):
        raise ValueError('unavailable or synthetic failure source')
    expected = {'event_id','task','code','feedback','observed_at','lineage_id','legality_audit'}
    if set(checkpoint)!=expected or checkpoint['event_id']!=event_id:
        raise ValueError('checkpoint fields/binding')
    if (checkpoint['observed_at']!=fact['observed_at'] or checkpoint['observed_at']>at
            or checkpoint['task']['problem_id']!=fact['task_id']
            or checkpoint['lineage_id']!=fact['provenance_group_id']
            or sha(checkpoint['code'])!=fact['candidate_sha256']):
        raise ValueError('checkpoint provenance/time/source mismatch')
    audit = checkpoint['legality_audit']
    if set(audit)!={'path','sha256','passed','checkpoint_sha256'} or audit['passed'] is not True:
        raise ValueError('trusted legality audit required')
    p = Path(audit['path'])
    if hashlib.sha256(p.read_bytes()).hexdigest()!=audit['sha256']:
        raise ValueError('legality artifact changed')
    material = {k:v for k,v in checkpoint.items() if k!='legality_audit'}
    if audit['checkpoint_sha256']!=fingerprint(material):
        raise ValueError('legality audit not bound to checkpoint')
    report=json.loads(p.read_text())
    if report.get('passed') is not True or report.get('checkpoint_sha256')!=fingerprint(material):
        raise ValueError('legality report binding differs')
    feedback=PublicFeedback.project(checkpoint['feedback'])
    if feedback.status!=fact['verifier_status'] and fact['observation_type']!='artifact':
        raise ValueError('feedback status differs from fact')
    if fact['observation_type']!='artifact' and not feedback.public_cases:
        raise ValueError('no legal visible public failure checks')
    return dict(event_id=event_id, task=PublicTaskView.project(checkpoint['task']).to_dict(),
        code=checkpoint['code'], feedback=feedback.to_dict(), observed_at=fact['observed_at'],
        available_from=fact['available_from'], lineage_id=fact['provenance_group_id'],
        code_sha256=fact['candidate_sha256'], legality_audit_sha256=audit['sha256'])


def discover_jobs(store, index, queue, checkpoints, *, at, completed_tasks, allow_synthetic=False):
    """Index symptoms, then use the existing task-end queue without assuming causality.

    Unlike A/B scheduling this uses CompileQueue.due: no solver action is imposed on
    code-generating discovery. Existing scheduler/Controller behavior is unmodified.
    """
    selected={}
    for event_id, checkpoint in checkpoints.items():
        p=public_checkpoint(store,event_id,checkpoint,at=at,allow_synthetic=allow_synthetic)
        fact=next(e for e in store.visible(at,index.stream_id) if e['event_id']==event_id)
        feedback=PublicFeedback(p['feedback']['status'],p['feedback']['summary'],
                                tuple(canonical(c) for c in p['feedback']['public_cases']))
        index.ingest(fact,feedback,p['code'],remaining_calls=0,at=at)
        selected[event_id]=p
    jobs=[]
    class SelectedEvidence:
        def visible(self,when,stream_id):
            return tuple(e for e in store.visible(when,stream_id) if e['event_id'] in selected)
    # The supplied checkpoint manifest freezes the discovery selection before outputs.
    # This is not a rescan of the entire historical pool.
    for job in queue.due(SelectedEvidence(),index.stream_id,completed_tasks,at):
        # Never silently accept a missing selected sidecar.
        if not set(job['evidence_ids'])<=set(selected):
            continue
        discovery=dict(version=PROTOCOL, shared_cause='UNVERIFIED',
            evidence=[selected[i] for i in job['evidence_ids']],
            symptom_groups=[s['group_id'] for s in index.states().values()
                            if set(s['source_evidence_ids']) & set(job['evidence_ids'])])
        jobs.append(dict(job, discovery=discovery))
    return jobs


def runtime_projection(payload):
    """Never mount/evaluate scoring answers in the operator process."""
    task=payload['task_public']
    feedback=payload['public_feedback']
    return dict(task_public={k:task.get(k,'') for k in ('problem_id','prompt','starter_code','function_name')},
        candidate_code=payload['candidate_code'],
        public_feedback=dict(status=feedback['status'],summary=feedback.get('summary',''),visibility='public',
            public_cases=[{'exception_class':c['exception_class']} for c in feedback.get('public_cases',[]) if c.get('exception_class')]),
        generation_metadata=payload.get('generation_metadata',{}),candidate_ledger=[],
        remaining_budget=payload.get('remaining_budget',{}),hook=payload.get('hook','before_native_retry'),
        checkpoint_id=payload.get('checkpoint_id',''), registry_snapshot_id=payload.get('registry_snapshot_id',''))


class FrozenLinuxBackend:
    """Pin the existing DockerWorker script and immutable local image for each call."""
    def __init__(self, *, image, worker_script):
        self.image=image
        self.worker_script=Path(worker_script).resolve()
        self.worker_sha256=hashlib.sha256(self.worker_script.read_bytes()).hexdigest()

    def __call__(self, path):
        from .container_worker import DockerWorker
        if hashlib.sha256(self.worker_script.read_bytes()).hexdigest()!=self.worker_sha256:
            raise ValueError('frozen Worker script changed')
        return DockerWorker(path,image=self.image,worker_script=self.worker_script)

    def manifest(self):
        return dict(image=self.image,worker_script=str(self.worker_script),worker_sha256=self.worker_sha256,
                    network='none',memory='256m',pids=32,cpus=1,read_only=True,user='65534:65534')


class DeterministicRunner:
    def __init__(self, worker_factory):
        self.inner=SandboxOperatorRunner(worker_factory,protocol='v2')

    def run(self,card,payload,timeout):
        value=self.inner.run(card,runtime_projection(payload),timeout)
        if not isinstance(value,dict) or set(value)-{'status','candidate_code','reason'}:
            return {'status':'error','reason':'unauthorized_result_fields'}
        if value.get('status') not in ('applied','declined','error'):
            return {'status':'error','reason':'invalid_status'}
        if value['status']=='applied':
            if not isinstance(value.get('candidate_code'),str) or not value['candidate_code'].strip():
                return {'status':'error','reason':'missing_candidate_code'}
        elif 'candidate_code' in value:
            return {'status':'error','reason':'action_on_decline'}
        if len(canonical(value).encode())>16384:
            return {'status':'error','reason':'result_size'}
        return value


class LinuxPublicEvaluator:
    """Minimal stdio/token comparator for pre-frozen public MVP fixtures.

    No answer is passed to Docker. Use an existing official scorer for tasks whose
    semantics require it. Unsupported function tasks fail closed rather than adapt.
    """
    def __init__(self,worker_factory):
        self.worker_factory=worker_factory

    def __call__(self,task,code):
        if task.function_name or not task.public_examples:
            raise ValueError('stdio with audited nonempty public checks required')
        cases=[]
        with tempfile.TemporaryDirectory(prefix='autonomous-evaluate-') as d:
            path=Path(d)/'program.py';path.write_text(code)
            with self.worker_factory(path) as worker:
                compiled=worker.call(dict(mode='compile_stdio',timeout=2))
                if compiled.get('status') in ('EVALUATOR_ERROR','WORKER_ERROR'):
                    raise RuntimeError('Worker compile infrastructure failure')
                if compiled.get('status')!='OK':
                    return dict(visibility='public',status='COMPILE_ERROR',tests_run=0,tests_passed=0,cases=[])
                for encoded in task.public_examples:
                    case=json.loads(encoded)
                    run=worker.call(dict(mode='stdio',input=case['input'],timeout=2))
                    if run['status'] in ('EVALUATOR_ERROR','WORKER_ERROR'):
                        raise RuntimeError('Worker infrastructure failure')
                    passed=run['status']=='OK' and run.get('output','').split()==case['expected'].split()
                    cases.append(dict(visibility='public',legal_verified=True,input=case['input'],
                        expected=case['expected'],actual=run.get('output',''),passed=passed,worker=run))
        count=sum(c['passed'] for c in cases)
        return dict(visibility='public',status='PUBLIC_PASS' if count==len(cases) else 'WRONG_ANSWER',
                    tests_run=len(cases),tests_passed=count,cases=cases)


def case_task(case):
    return PublicTaskView.project(case['task'])


class AutonomousMVP:
    def __init__(self,root,compiler,runner,evaluator,registry,context,tool_budget):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.events=EvidenceStore(self.root/'mvp.jsonl')
        self.compiler,self.runner,self.evaluate=compiler,runner,evaluator
        self.registry,self.context,self.tool_budget=registry,context,tool_budget

    def _step(self,key,payload,fn,at):
        rows=[r for r in self.events.records() if r['payload'].get('key')==key]
        if rows:
            if rows[0]['payload']['hash']!=fingerprint(payload):raise ValueError('frozen inputs changed')
            if rows[-1]['kind']=='DONE':return rows[-1]['payload']['result']
            raise RuntimeError('interrupted step; no automatic resend')
        self.events.append('START',dict(key=key,hash=fingerprint(payload)),at)
        value=fn()
        self.events.append('DONE',dict(key=key,result=value),at)
        return value

    def _tool(self,kind,fn):
        started=time.monotonic()
        budget=self.tool_budget
        if hasattr(budget,'consume_shard'):
            key=budget.tool(capability=kind)
            try:
                value=fn()
                budget.settle(key,tool_milliseconds=int((time.monotonic()-started)*1000)+1)
            except BaseException:
                budget.settle(key);raise
        else:
            budget.tool();value=fn()
        return value

    def _case(self,card,case,*,at_start=False):
        started=time.monotonic()
        task=case_task(case)
        original=self._tool('baseline_public',lambda:self.evaluate(task,case['code']))
        payload=dict(task_public=task.to_dict(),candidate_code=case['code'],public_feedback=PublicFeedback.project(original).to_dict())
        if at_start:
            payload.update(candidate_code='',public_feedback=PublicFeedback('NO_COMPLETE_CODE').to_dict(),hook='before_native_start')
        result=self._tool('operator',lambda:self.runner.run(card,payload,card.max_seconds))
        if result.get('reason') in ('EVALUATOR_ERROR','WORKER_ERROR'):
            raise RuntimeError('operator Worker infrastructure failure')
        proposed=result.get('candidate_code') if result.get('status')=='applied' else None
        after=original
        if proposed is not None:
            try:ast.parse(proposed)
            except SyntaxError:after=dict(status='COMPILE_ERROR',tests_run=0,tests_passed=0,cases=[])
            else:after=self._tool('proposal_public',lambda:self.evaluate(task,proposed))
        passed=lambda r: r.get('status')=='PUBLIC_PASS' and r.get('tests_run',0)>0 and r.get('tests_run')==r.get('tests_passed')
        before_cases=original.get('cases',[]);after_cases=after.get('cases',[])
        regression=(passed(original) and not passed(after)) or any(
            c.get('passed') and (i>=len(after_cases) or not after_cases[i].get('passed')) for i,c in enumerate(before_cases))
        return dict(case_id=case['case_id'],task_id=task.problem_id,lineage_id=case['lineage_id'],
            before=original,after=after,operator_result=result,original_sha256=sha(case['code']),
            proposed_sha256=sha(proposed) if proposed is not None else None,
            executed_artifact_sha256=card.artifact_sha256,action=result.get('status'),
            source_effective=bool(proposed is not None and proposed!=case['code'] and not passed(original) and passed(after)),
            regressed=bool(regression),passed=passed(after),
            partial_improvement=after.get('tests_passed',0)>original.get('tests_passed',0) and not passed(after),
            seconds=time.monotonic()-started,model_calls=0)

    def run(self,job,*,source,independent,negative,at,revise=False):
        with (self.root/'run.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            return self._run(job,source=source,independent=independent,negative=negative,at=at,revise=revise)

    def _run(self,job,*,source,independent,negative,at,revise):
        facts=job['discovery']['evidence']
        sources={x['task']['problem_id'] for x in facts};lineages={x['lineage_id'] for x in facts}
        if not source or not independent or not negative:
            raise ValueError('source, independent positive and negative controls required')
        if any(c['task']['problem_id'] not in sources or c['lineage_id'] not in lineages or
               not any(c['code']==f['code'] and c['task']['problem_id']==f['task']['problem_id'] for f in facts) for c in source):
            raise ValueError('source not bound to discovery')
        for c in independent+negative:
            if c['task']['problem_id'] in sources or c['lineage_id'] in lineages or sha(c['code']) in {f['code_sha256'] for f in facts}:
                raise ValueError('independent task/lineage overlaps discovery')
        if len({c['case_id'] for c in source+independent+negative})!=len(source+independent+negative):
            raise ValueError('duplicate case IDs')
        if {c['task']['problem_id'] for c in independent}&{c['task']['problem_id'] for c in negative}:
            raise ValueError('positive/negative task overlap')
        # Freeze tests before any generation; never send them to compiler.
        jid=job['job_id']
        plan=dict(job=job,source=source,independent=independent,negative=negative,revise=revise)
        self._step(jid+':freeze',plan,lambda:{'hash':fingerprint(plan)},at)
        self._save('frozen_plan.json',plan)
        spec=self._step(jid+':induction',job,lambda:self.compiler.request(job,'induction',0,at),at)
        content=parse_hypothesis(json.loads(spec['specification']))
        hypothesis=MechanismHypothesis(fingerprint([jid,content]),tuple(job['evidence_ids']),tuple(sorted(sources)),
            tuple(sorted(lineages)),content,spec['wire_sha256'],spec['response_sha256'],spec['origin'])
        self._save('hypothesis.json',asdict(hypothesis))
        if content['decision']=='NO_MECHANISM':return dict(status='NO_MECHANISM',hypothesis=asdict(hypothesis))
        payload=dict(job,specification=spec['specification'])
        versions=[];parent=''
        for version in range(2 if revise else 1):
            phase='candidate' if version==0 else 'revision'
            response=self._step(jid+':'+phase,payload,lambda:self.compiler.request(payload,phase,0,at),at)
            code=response['code'];digest=sha(code)
            path=self.root/('operator-v'+str(version)+'.py');path.write_text(code)
            op=GeneratedOperator(hypothesis.hypothesis_id,'auto-'+hypothesis.hypothesis_id[:16],str(version),parent,
                content['operator_category'],code,digest,str(path.resolve()),PROTOCOL,
                'runtime_projection payload; no grader answers, no model tools','applied candidate_code OR declined/error reason',
                response['applicability'],response['model'],response['id'],response['response_sha256'],response['wire_sha256'],
                response['usage'],response.get('reserved_rate_estimate_microusd',0),response['origin'])
            self._save('generated-v'+str(version)+'.json',asdict(op))
            card=FailureOperator(op.operator_id,op.version,op.artifact_path,op.code_sha256,self.context,
                PROTOCOL,tuple(job['evidence_ids']),tuple(sorted(lineages)),hooks=('before_native_retry',),allowed_feedback=('WRONG_ANSWER','RUNTIME_ERROR','COMPILE_ERROR','NO_COMPLETE_CODE','PUBLIC_PASS'),
                structural_statuses=('STRUCTURAL_PASS','COMPILE_ERROR','NO_COMPLETE_CODE'),
                allowed_actions=('candidate_code',),operator_kind='code_repair',max_seconds=5)
            static=validate_compile_output({k:response[k] for k in ('code','description','applicability')})
            outcomes=[]
            if static['static_pass']:
                outcomes=self._step(jid+':source:'+str(version),[digest,source],
                    lambda:[self._case(card,c) for c in source],at)
            effective=bool(outcomes) and all(r['source_effective'] and not r['regressed'] for r in outcomes)
            versions.append(dict(operator=asdict(op),static=static,source=outcomes))
            if effective:break
            parent=digest
            payload=dict(payload,code=code,source_diagnostics=dict(static=static,public_source=outcomes))
        self._save('versions.json',versions)
        checks=[];neg=[]
        if effective:
            if not self.registry._rows(card):self.registry.register(card,at)
            # One winner, one independent gate. No revisions based on its result.
            checks=self._step(jid+':independent',[digest,independent],lambda:[self._case(card,c) for c in independent],at)
            neg=self._step(jid+':negative',[digest,negative],lambda:[self._case(card,c) for c in negative],at)
        isolated=(isinstance(self.runner,DeterministicRunner) and isinstance(self.evaluate,LinuxPublicEvaluator)
                  and isinstance(self.runner.inner.worker_factory,FrozenLinuxBackend)
                  and self.runner.inner.worker_factory is self.evaluate.worker_factory)
        eligible=(isolated and effective and all(r['source_effective'] and not r['regressed'] for r in checks)
                  and bool(checks) and bool(neg) and all(r['action']=='declined' and not r['regressed'] for r in neg))
        validation=OperatorValidation(digest,static,tuple(outcomes),tuple(checks),tuple(neg),
            dict(isolated_actual_source=isolated,worker=self.evaluate.worker_factory.manifest() if isolated else None,induction_usage=spec['usage'],model_usage=[v['operator']['usage'] for v in versions],tool_budget=self.tool_budget.snapshot()),
            'READY_FOR_HOST_LIMITED_REVIEW' if eligible else 'SHADOW_NO_ADMISSION',
            'ENGINEERING_MOCK_NOT_LEARNING' if op.origin=='MOCK' else 'SOURCE_AND_INDEPENDENT_DEVELOPMENT_ONLY')
        result=dict(status=validation.decision,operator=asdict(op),card=card.to_dict(),validation=asdict(validation),
            excluded_task_ids=sorted(sources|{c['task']['problem_id'] for c in independent+negative}),
            excluded_lineages=sorted(lineages|{c['lineage_id'] for c in independent+negative}),
            origin=op.origin,synthetic=op.origin=='MOCK')
        self._save('validation.json',result)
        return result

    def _save(self,name,value):
        path=self.root/name
        text=canonical(value)+'\n'
        if path.exists() and path.read_text()!=text:raise ValueError('immutable result already exists: '+name)
        path.write_text(text)
        return path

    def authorize(self,result,*,experiment_id,stream_id,after_task,effective_from,at,future_tasks,engineering=False):
        # Always reload the host result; caller/model cannot replace acceptance booleans.
        saved=json.loads((self.root/'validation.json').read_text())
        if saved!=json.loads(canonical(result)) or saved['status']!='READY_FOR_HOST_LIMITED_REVIEW':
            raise ValueError('host validation did not pass')
        if saved['origin']=='MOCK' and not (engineering and experiment_id.startswith('engineering:') and stream_id.startswith('engineering:')):
            raise PermissionError('mock results cannot authorize research use')
        if not isinstance(future_tasks,dict) or not future_tasks or any(
                not isinstance(k,str) or not k or not isinstance(v,str) or not v or
                k in saved['excluded_task_ids'] or v in saved['excluded_lineages'] for k,v in future_tasks.items()):
            raise ValueError('explicit disjoint future task/lineage scope required')
        card=FailureOperator.from_dict(saved['card']);v=saved['validation']
        raw=self.root/'validation.json';digest=hashlib.sha256(raw.read_bytes()).hexdigest()
        checks={name:dict(passed=True,evidence_sha256=digest,artifact_sha256=card.artifact_sha256,
                    execution='isolated_actual_source') for name in
                ('isolated_worker','static_contract','source_repair','boundary','inapplicable','host_fallback')}
        s=v['source'][0]
        source_event=next(e['event_id'] for e in self.registry.evidence.visible(at)
            if e['event_id'] in card.evidence_ids and e['task_id']==s['task_id'] and e['candidate_sha256']==s['original_sha256'])
        checks['source_repair'].update(event_id=source_event,original_sha256=s['original_sha256'],
            host_public_outcome='passed',action='applied',tests_run=s['after']['tests_run'],tests_passed=s['after']['tests_passed'])
        report=dict(role='NURSERY_ADMISSION',operator_id=card.operator_id,version=card.version,
            artifact_sha256=card.artifact_sha256,fingerprint=card.evidence_fingerprint.to_dict(),scope=card.evidence_scope,
            evidence_ids=list(card.evidence_ids),experiment_id=experiment_id,evaluated_at=at,
            files=[dict(path=str(raw.resolve()),sha256=digest)],checks=checks,
            future_tasks=future_tasks,independent_mvp_gate=v['independent'],excluded_task_ids=saved['excluded_task_ids'],engineering_only=engineering)
        path=self._save('admission.json',report)
        self.registry.admit_nursery(card,path,experiment_id=experiment_id,stream_id=stream_id,
            after_task=after_task,effective_from=effective_from,at=at,opportunity_limit=2)
        return card


class AutonomousHook(FailureLearningPlugin):
    """Opt-in plugin. Existing Controller is unchanged when absent/disabled."""
    def begin(self,task,at):
        super().begin(task,at)
        from dataclasses import replace
        snapshot=self.current['snapshot'];cards=[]
        for card in snapshot.cards:
            auth=self.registry.state(card,at)['authorization']
            report=json.loads(Path(auth['gate_path']).read_text())
            if report.get('engineering_only') and not self.stream_id.startswith('engineering:'):
                continue
            if task.problem_id in report.get('excluded_task_ids',[]) or task.problem_id not in report.get('future_tasks',{}):continue
            if report.get('role')!='NURSERY_ADMISSION' or card.evidence_scope!=PROTOCOL:continue
            cards.append(card)
        self.current['snapshot']=replace(snapshot,cards=tuple(cards),
            snapshot_id=fingerprint([snapshot.snapshot_id,[c.to_dict() for c in cards]]))
