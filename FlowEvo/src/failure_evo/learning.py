"""Task-end learning seam. The default is observation/queueing, never a model call."""
from .contracts import fingerprint
from .evidence import EvidenceStore


class LearningLoop:
    def __init__(self, queue, evidence, stream_id, path):
        self.queue, self.evidence, self.stream_id = queue, evidence, stream_id
        self.events = EvidenceStore(path)

    def pending(self, at):
        completed = [r for r in self.evidence.events.visible(at)
                     if r['kind'] == 'TASK_COMPLETED' and r['payload']['stream_id'] == self.stream_id]
        return self.queue.due(self.evidence, self.stream_id, len(completed), at)

    def public_input(self, job, at):
        """Resolve only already available public facts and their pinned source code."""
        known = {e['event_id']: e for e in self.evidence.visible(at, self.stream_id)}
        if job['stream_id'] != self.stream_id or not set(job['evidence_ids']) <= set(known):
            raise ValueError('learning source unavailable in this stream')
        facts = [known[e] for e in job['evidence_ids']]
        if any(e['synthetic'] for e in facts):
            raise ValueError('engineering fixtures cannot enter learning input')
        programs = {e['candidate_sha256']: (self.evidence.artifacts / (e['candidate_sha256']+'.py')).read_text() for e in facts}
        return dict(job, public_evidence=facts, source_programs=programs)

    def run_pending(self, compiler, *, at):
        """Explicit host action after completion, using a caller-funded BoundedCompiler.

        Only the induction phase is scheduled here. Candidate/revision calls require
        explicit design input; no automatic selection or gate bypass is performed.
        """
        results = []
        for job in self.pending(at):
            public = self.public_input(job, at)
            try:
                response = compiler.request(public, 'induction', 0, at)
            finally:
                # A reserved/attempted request consumes the queue job, even on failure.
                if any(r['payload'].get('job_id') == job['job_id'] for r in compiler.events.records()):
                    self.queue.events.append('COMPILE_ATTEMPTED', dict(job), at)
            self.events.append('LEARNING_INDUCTION_FINISHED', dict(job_id=job['job_id'], stream_id=self.stream_id,
                response_sha256=fingerprint(response), status='shadow'), at)
            results.append(response)
        return tuple(results)

    def run_pipeline(self, pipeline, *, design, gate, regression, at, revise=False,
                     data_manifest=None, environment=None):
        """Complete one pending family's generation/validation with frozen role manifests.

        A caller must explicitly assign independent shards per family. No automatic
        registration/experimental authorization follows a checker result.
        """
        jobs = self.pending(at)
        if len(jobs) != 1:
            raise ValueError('assign exactly one pending family to these data shards')
        job = jobs[0]
        public = self.public_input(job, at)
        if environment is not None:
            public['environment'] = environment
        result = pipeline.run(public, design=design, gate=gate,
                              regression=regression, at=at, revise=revise,
                              data_manifest=data_manifest)
        self.queue.events.append('COMPILE_ATTEMPTED', dict(job), at)
        self.events.append('PIPELINE_FINISHED', dict(job_id=job['job_id'],
            stream_id=self.stream_id, status=result['status']), at)
        return result
