"""Persistent S1.2 orchestration. Providers/checkers are trusted host capabilities."""
import ast
import hashlib
import math
import time
import fcntl
from .contracts import fingerprint
from .evidence import EvidenceStore
from .data_roles import validate_data_roles


class LearningPipeline:
    """One frozen winner; a failed or interrupted gate is never tried again.

    evaluation_budget is separate from compiler.budget. Checkers must enforce the
    supplied timeout in an isolated worker. This class never executes model code.
    """
    def __init__(self, path, compiler, evaluation_budget, design_checker, gate_checker):
        self.events = EvidenceStore(path)
        self.compiler = compiler
        self.budget = evaluation_budget
        self.design_checker = design_checker
        self.gate_checker = gate_checker

    def _step(self, key, request, callback, at):
        digest = fingerprint(request)
        records = [r for r in self.events.records() if r['payload'].get('key') == key]
        if records:
            if records[0]['payload']['request_hash'] != digest:
                raise ValueError('frozen step inputs changed')
            if records[-1]['kind'] == 'STEP_DONE':
                return records[-1]['payload']['result']
            raise RuntimeError('interrupted/failed step consumed; host review required')
        self.events.append('STEP_STARTED', dict(key=key, request_hash=digest), at)
        self._step_key=key
        try:
            result = callback()
        except Exception as exc:
            self.events.append('STEP_FAILED', dict(key=key, error=type(exc).__name__), at)
            raise
        self.events.append('STEP_DONE', dict(key=key, result=result), at)
        return result

    def _evaluate(self, checker, code, dataset):
        durable = hasattr(self.budget, 'consume_shard')
        if durable:
            key=self.budget.tool(job_id=self._job_id,capability='evaluation:'+dataset['shard_id'],
                request_id=self._step_key,request_hash=fingerprint([code,dataset]))
        else:
            key=self.budget.tool()
        started=time.monotonic()
        timeout=self.budget.remaining_seconds
        if durable:timeout=min(timeout,self.budget.config['tool_milliseconds_upper']/1000)
        try:
            result = checker(code, dataset, timeout)
            if durable:
                self.budget.settle(key,tool_milliseconds=math.ceil((time.monotonic()-started)*1000))
        except BaseException:
            if durable:self.budget.settle(key)
            raise
        if self.budget.remaining_seconds <= 0:
            raise TimeoutError('evaluation deadline exceeded')
        if not isinstance(result, dict) or type(result.get('eligible')) is not bool:
            raise ValueError('host checker must return explicit eligibility')
        score = result.get('score')
        if type(score) not in (int, float) or not math.isfinite(score):
            raise ValueError('finite preregistered design score required')
        return result

    def run(self, public_job, *, design, gate, regression, at, revise=False, data_manifest=None):
        # Serialize all jobs in this pipeline; the budget separately locks across processes.
        with self.events.path.with_suffix('.pipeline.lock').open('a+b') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            try:
                return self._run(public_job,design=design,gate=gate,regression=regression,at=at,revise=revise,data_manifest=data_manifest)
            finally:fcntl.flock(lock,fcntl.LOCK_UN)

    def _run(self, public_job, *, design, gate, regression, at, revise=False, data_manifest=None):
        if data_manifest is not None:
            validate_data_roles(data_manifest)
            if any(data_manifest[role] != value for role, value in
                   [('design', design), ('gate', gate), ('regression', regression)]):
                raise ValueError('evaluation data differs from frozen manifest')
            discovery = set(data_manifest['discovery']['source_groups'])
            if discovery != {e['provenance_group_id'] for e in public_job['public_evidence']}:
                raise ValueError('discovery provenance differs from public evidence')
        # Data roles are host manifests, never accepted from generated source.
        sets = [set(d['source_groups']) for d in (design, gate, regression)]
        sources = {e['provenance_group_id'] for e in public_job['public_evidence']}
        if any(not groups or groups & sources for groups in sets):
            raise ValueError('development/validation provenance overlaps discovery')
        if any(sets[i] & sets[j] for i in range(3) for j in range(i)):
            raise ValueError('data roles must have disjoint provenance')
        shard_ids = [d['shard_id'] for d in (design, gate, regression)]
        if len(set(shard_ids)) != 3:
            raise ValueError('data roles require distinct shard identities')
        job_id = public_job['job_id']
        self._job_id=job_id
        protocol = dict(public_job=public_job, design=design,
            gate=gate, regression=regression, revise=revise)
        if data_manifest is not None:
            protocol['data_manifest'] = data_manifest
        self._step(job_id+':protocol', protocol, lambda: {'frozen':True}, at)
        def generate(phase, slot, payload):
            return self._step(job_id+':'+phase+':'+str(slot), payload,
                lambda:self.compiler.request(payload, phase, slot, at), at)
        spec = generate('induction', 0, public_job)['specification']
        candidates = []
        for slot in range(3):
            payload = dict(public_job, specification=spec)
            response = generate('candidate', slot, payload)
            code = response['code']
            for revision in range(2 if revise else 1):
                try:
                    tree = ast.parse(code)
                    valid = any(isinstance(n, ast.FunctionDef) and n.name=='repair_operator' for n in tree.body)
                except (SyntaxError, ValueError):
                    valid = False
                result = self._step(job_id+':design:'+str(slot)+':'+str(revision),
                    dict(code=code, data=design),
                    lambda:self._evaluate(self.design_checker, code, design) if valid
                    else {'eligible':False, 'score':0, 'reason':'invalid_operator_structure'}, at)
                candidates.append(dict(slot=slot, revision=revision, code=code, evaluation=result))
                if revise and revision==0:
                    code = generate('revision', slot, dict(payload, code=code, design_feedback=result))['code']
        eligible = [c for c in candidates if c['evaluation']['eligible']]
        if not eligible:
            return {'status':'shadow_retained', 'reason':'no_design_winner', 'candidates':candidates}
        winner = sorted(eligible, key=lambda c:(-c['evaluation']['score'],c['slot'],c['revision']))[0]
        self._step(job_id+':winner', winner, lambda:winner, at)
        outcomes = []
        for role, data in [('gate',gate),('regression',regression)]:
            # Global shard identity prevents another job/candidate fishing on it.
            result = self._step('shard:'+data['shard_id'],
                dict(job_id=job_id, role=role, code=winner['code'], data=data),
                lambda:self._gate_evaluate(job_id,winner['code'],data), at)
            outcomes.append(result)
        return dict(status='ready_for_experimental_review' if all(r['eligible'] for r in outcomes)
                    else 'shadow_retained', winner=winner, validation=outcomes,
                    artifact_sha256=hashlib.sha256(winner['code'].encode()).hexdigest())

    def _gate_evaluate(self,job_id,code,data):
        if hasattr(self.budget,'consume_shard'):
            self.budget.consume_shard(data['shard_id'],job_id=job_id,request_hash=fingerprint([code,data]))
        return self._evaluate(self.gate_checker,code,data)
