"""Bounded, persistent learning scheduler. No model or network client is imported."""
import hashlib
from pathlib import Path
from .contracts import fingerprint
from .evidence import EvidenceStore
from .runtime import BudgetExhausted


class CompileQueue:
    def __init__(self, path, interval=20, max_families=2):
        if type(interval) is not int or interval < 1 or type(max_families) is not int or not 1 <= max_families <= 2:
            raise ValueError('invalid learning schedule')
        self.events = EvidenceStore(path)
        self.interval = interval
        self.max_families = max_families

    def due(self, store, stream_id, completed_tasks, at):
        """First credible fact at task end, then fixed checkpoints; no repeated evidence."""
        if type(completed_tasks) is not int or completed_tasks < 1:
            return ()
        prior = [r['payload'] for r in self.events.visible(at) if r['payload']['stream_id'] == stream_id]
        if prior and completed_tasks % self.interval:
            return ()
        used = {e for row in prior for e in row['evidence_ids']}
        families = {row['family_id'] for row in prior}
        grouped = {}
        for event in store.visible(at, stream_id):
            if event['synthetic'] or event['event_id'] in used:
                continue
            grouped.setdefault(event['family_id'], []).append(event['event_id'])
        jobs = []
        for family, ids in sorted(grouped.items()):
            if family not in families and len(families) >= self.max_families:
                continue
            families.add(family)
            jobs.append(dict(stream_id=stream_id, family_id=family, evidence_ids=ids,
                             job_id=fingerprint([stream_id, family, ids]), completed_tasks=completed_tasks))
        return tuple(jobs)

    def compile(self, job, compiler, budget, *, at, output_upper=4096):
        """Host-injected compiler adapter; first request creates only a Shadow artifact.

        Failed requests are consumed. This is specification induction, not an implicit
        deployment permission. Candidate/revision calls use BoundedCompiler below.
        """
        if any(r['payload']['job_id'] == job['job_id'] for r in self.events.records()):
            raise ValueError('job already attempted')
        # Reserve before recording an attempt, so no budget means no lost queue work.
        key = budget.reserve(len(str(job).encode()) + 4096, output_upper)
        self.events.append('COMPILE_ATTEMPTED', dict(job), at)
        try:
            response = compiler(dict(job))
            budget.settle(key, response.get('usage', {}).get('total_tokens'))
            if budget.remaining_seconds <= 0:
                raise BudgetExhausted('learning deadline exceeded')
            return response
        except BaseException:
            if key in budget.reservations:
                budget.settle(key)
            raise


class BoundedCompiler:
    """Per-study 2 families × (1 induction + 3 candidates + 3 revisions) ceiling."""
    def __init__(self, provider, budget, path, model):
        if budget.max_calls > 14:
            raise ValueError('generation budget exceeds 14 requests')
        self.provider, self.budget, self.model = provider, budget, model
        self.events = EvidenceStore(path)
        self.artifacts = Path(path).parent / 'generated_artifacts'

    def request(self, job, phase, slot, at, output_upper=4096):
        rows = [r['payload'] for r in self.events.records() if r['kind']=='GENERATION_REQUESTED']
        family = (job['stream_id'], job['family_id'])
        keys = {(r['stream_id'], r['family_id']) for r in rows}
        if family not in keys and len(keys) >= 2:
            raise ValueError('family limit reached')
        if phase not in ('induction', 'candidate', 'revision') or type(slot) is not int:
            raise ValueError('unknown generation phase')
        if (phase == 'induction' and slot != 0) or (phase != 'induction' and slot not in (0, 1, 2)):
            raise ValueError('candidate slot limit reached')
        completed = [r['payload'] for r in self.events.records() if r['kind']=='GENERATION_COMPLETED']
        own_completed = [r for r in completed if (r['stream_id'],r['family_id'])==family]
        own = [r for r in rows if (r['stream_id'], r['family_id']) == family]
        if any(r['phase'] == phase and r['slot'] == slot for r in own):
            raise ValueError('generation request already consumed')
        if phase != 'induction' and not any(r['phase'] == 'induction' for r in own_completed):
            raise ValueError('induction must precede candidates')
        if phase == 'revision' and not any(r['phase'] == 'candidate' and r['slot'] == slot for r in own_completed):
            raise ValueError('candidate must precede revision')
        request = dict(job, phase=phase, slot=slot, max_tokens=output_upper)
        key = self.budget.reserve(len(str(request).encode()) + 4096, output_upper)
        self.events.append('GENERATION_REQUESTED', request, at)
        try:
            response = self.provider(request)
            self.budget.settle(key, response.get('usage', {}).get('total_tokens'))
            if response.get('model') != self.model:
                raise ValueError('compiler model drift')
            if self.budget.remaining_seconds <= 0:
                raise BudgetExhausted('compiler exceeded deadline')
            content = response.get('specification') if phase=='induction' else response.get('code')
            if not isinstance(content,str) or not content.strip():
                raise ValueError('compiler returned no specification/artifact')
            self.artifacts.mkdir(parents=True,exist_ok=True)
            artifact = self.artifacts / (fingerprint(request) + ('.txt' if phase=='induction' else '.py'))
            artifact.write_text(content)
            # Persist successful model provenance and content, without granting execution.
            self.events.append('GENERATION_COMPLETED', dict(stream_id=job['stream_id'],
                family_id=job['family_id'], phase=phase, slot=slot, request_sha256=fingerprint(request),
                model=response.get('model'), response_id=response.get('id'),
                content=content, artifact_path=str(artifact.resolve()),
                content_sha256=hashlib.sha256(content.encode()).hexdigest(),
                usage=response.get('usage', {}), status='draft'), at)
            return response
        finally:
            if key in self.budget.reservations:
                self.budget.settle(key)
