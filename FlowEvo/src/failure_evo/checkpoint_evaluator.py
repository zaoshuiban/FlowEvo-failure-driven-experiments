"""Host-scored conditional checkpoint evaluator, gated by real Worker acceptance.

Expected outputs and independent cases are never mounted into the worker. This
measures checkpoint behavior, not the cost of a full native model continuation.
"""
import hashlib
import json
import math
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
from .container_worker import DockerWorker
from .contracts import canonical
from .failure_events import structural_status
from .persistent_budget import PersistentBudget
from .runtime import SandboxOperatorRunner


def resolve_action(result, ledger):
    if not isinstance(result,dict) or result.get('status') not in ('applied','declined','error'):
        raise ValueError('invalid operator contract')
    allowed={'status','candidate_code','selected_candidate_id','validation_status','actual_cost','evidence_ids','reason'}
    if set(result)-allowed or len(canonical(result).encode())>16384:
        raise ValueError('unauthorized action or oversized output')
    if result['status']!='applied':
        if 'candidate_code' in result or 'selected_candidate_id' in result:
            raise ValueError('declined/error result must not carry an action')
        return None
    if ('candidate_code' in result)==('selected_candidate_id' in result):
        raise ValueError('exactly one action required')
    if 'candidate_code' in result:
        code=result['candidate_code']
    else:
        selected=[r for r in ledger if r['candidate_id']==result['selected_candidate_id']]
        if len(selected)!=1:raise ValueError('candidate outside public ledger')
        code=selected[0]['code']
    if not isinstance(code,str) or structural_status(code)!='STRUCTURAL_PASS':
        raise ValueError('invalid candidate code')
    # Never trust result.validation_status or result.actual_cost.
    return code


def compare_output(actual, expected, rule):
    if rule!='whitespace_token_exact':
        raise ValueError('unsupported scorer; multi-answer/float tasks require a reviewed checker')
    return isinstance(actual,str) and actual.split()==expected.split()


class CheckpointEvaluator:
    def __init__(self, root, budget, *, image, worker_script, acceptance_path):
        if not isinstance(budget,PersistentBudget):raise TypeError('PersistentBudget required')
        proof=json.loads(Path(acceptance_path).read_text())
        script=Path(worker_script).resolve()
        adapter=Path(__file__).with_name('container_worker.py')
        if (proof.get('status')!='PASS' or not proof.get('checks') or
            not all(c.get('passed') is True for c in proof['checks']) or
            proof.get('image')!=image or
            proof.get('worker_script_sha256')!=hashlib.sha256(script.read_bytes()).hexdigest() or
            proof.get('adapter_sha256')!=hashlib.sha256(adapter.read_bytes()).hexdigest()):
            raise RuntimeError('real matching local Worker acceptance required')
        self.root=Path(root).resolve();self.budget=budget
        self.deadline=time.monotonic()+budget.remaining_seconds
        self.factory=lambda candidate:DockerWorker(candidate,image=image,worker_script=script)
        self.runner=SandboxOperatorRunner(self.factory,protocol='v2')

    def _source(self, descriptor):
        path=(self.root/descriptor['source_path']).resolve()
        if self.root not in path.parents:raise ValueError('source outside study repository')
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=descriptor['sha256']:raise ValueError('source changed')
        return data.decode()

    def _remaining(self):
        remaining=min(self.deadline-time.monotonic(),self.budget.remaining_seconds)
        if remaining<=0:raise TimeoutError('checkpoint evaluator deadline exceeded')
        return remaining

    def _charged(self, capability, callback):
        self._remaining()
        key=self.budget.tool(job_id='checkpoint-evaluation',capability=capability)
        start=time.monotonic()
        try:
            value=callback()
            self.budget.settle(key,tool_milliseconds=math.ceil((time.monotonic()-start)*1000))
            self._remaining()
            return value
        except BaseException:
            self.budget.settle(key)
            raise

    def judge(self, code, cases, timeout):
        if not cases:return dict(outcome='unavailable',tests_run=0,tests_passed=0)
        if structural_status(code)!='STRUCTURAL_PASS':
            return dict(outcome='unavailable',tests_run=0,tests_passed=0,reason='invalid_artifact',artifact_failed=True)
        passed=0;observed=[]
        with tempfile.TemporaryDirectory(prefix='flowevo-judge-') as tmp:
            source=Path(tmp)/'candidate.py';source.write_text(code)
            for case in cases:
                def execute():
                    with self.factory(source) as worker:
                        compiled=worker.call(dict(mode='compile_stdio',timeout=min(timeout,5,self._remaining())))
                        if compiled.get('status')!='OK':return compiled
                        return worker.call(dict(mode='stdio',input=case['input'],timeout=min(timeout,5,self._remaining())))
                raw=self._charged('program-test',execute)
                if raw.get('status') in ('EVALUATOR_ERROR','WORKER_ERROR'):
                    return dict(outcome='unavailable',tests_run=len(observed),tests_passed=passed,reason='worker_failure')
                correct=raw.get('status')=='OK' and compare_output(raw.get('output'),case['expected'],case['comparison'])
                observed.append(dict(case_id=case['case_id'],status=raw.get('status'),correct=correct))
                passed+=correct
        return dict(outcome='passed' if passed==len(cases) else 'failed',tests_run=len(cases),tests_passed=passed,cases=observed)

    def __call__(self, code, dataset, timeout):
        if timeout<=0:raise TimeoutError('no evaluation budget')
        self.deadline=time.monotonic()+timeout
        rows=[];contract=True
        for checkpoint in dataset['checkpoints']:
            # Public evidence is recomputed now, never relabelled from old hidden verdicts.
            public_cases=checkpoint['public_cases'];ledger=[]
            for i,descriptor in enumerate(checkpoint['candidate_ledger']):
                candidate=self._source(descriptor);verdict=self.judge(candidate,public_cases,timeout)
                ledger.append(dict(candidate_id='c'+str(i+1),code=candidate,stage=descriptor['stage'],
                    structural_status=structural_status(candidate),public_check_outcome=verdict['outcome'],
                    public_feedback=dict(status='PUBLIC_PASS' if verdict['outcome']=='passed' else 'UNKNOWN',
                        tests_run=verdict['tests_run'],tests_passed=verdict['tests_passed'])))
            current=self._source(checkpoint['current'])
            payload=dict(task_public=checkpoint['task_public'],candidate_code=current,
                candidate_ledger=ledger,public_feedback={'status':structural_status(current)},
                generation_metadata={},remaining_budget=self.budget.snapshot(),hook='before_native_retry')
            with tempfile.TemporaryDirectory(prefix='flowevo-evaluate-') as tmp:
                artifact=Path(tmp)/'operator.py';artifact.write_text(code)
                card=SimpleNamespace(artifact_path=str(artifact),artifact_sha256=hashlib.sha256(code.encode()).hexdigest())
                result=self._charged('operator',lambda:self.runner.run(card,payload,min(timeout,1,self._remaining())))
            try:proposed=resolve_action(result,ledger)
            except ValueError:
                contract=False;proposed=None
            public=self.judge(proposed,public_cases,timeout) if proposed is not None else {'outcome':'unavailable'}
            independent=self.judge(proposed,checkpoint.get('independent_cases',[]),timeout) if proposed is not None else {'outcome':'unavailable'}
            decline=result.get('status')=='declined' if isinstance(result,dict) else False
            expectation=checkpoint['expected_behavior']
            success=decline if expectation=='decline' else public['outcome']=='passed'
            if dataset.get('role') in ('gate','regression') and expectation!='decline':
                success=success and independent['outcome']=='passed'
            rows.append(dict(checkpoint_id=checkpoint['checkpoint_id'],public=public,independent=independent,
                declined=decline,success=success,worker_result_status=result.get('status') if isinstance(result,dict) else 'invalid'))
        eligible=bool(rows) and contract and all(r['success'] for r in rows)
        return dict(eligible=eligible,score=sum(r['success'] for r in rows)/len(rows) if rows else 0,
            contract_checks_passed=contract,scope_checks_passed=eligible,checkpoint_results=rows,
            paired_results=[],benefit_route=None,
            limitation='No full native continuation comparison: cannot authorize Experimental from these results alone',
            costs=self.budget.snapshot())
