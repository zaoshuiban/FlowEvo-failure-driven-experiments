"""Public symptom index and append-only, non-causal hypothesis scheduling.

No model client, authorization, or private evaluator is owned by this index.
"""
from .contracts import fingerprint
from .evidence import EvidenceStore
from .workflow_protocol_v2 import program_observation


class SymptomLearning:
    def __init__(self, path, store, stream_id):
        self.events = EvidenceStore(path)
        self.store, self.stream_id = store, stream_id

    def states(self):
        states = {}
        for row in self.events.records():
            if row['kind'] == 'HYPOTHESIS_VERSION':
                states[row['payload']['hypothesis_id']] = row['payload']
        return states

    def ingest(self, fact, feedback, code, *, remaining_calls, at):
        visible = {x['event_id']: x for x in self.store.visible(at, self.stream_id)}
        if fact['event_id'] not in visible:
            raise ValueError('unavailable evidence')
        obs = program_observation(code)
        exceptions = sorted({c.get('exception_class') for c in feedback.to_dict()['public_cases'] if c.get('exception_class')})
        # An exception string alone is never certified as a shared cause.
        complete = obs['structural_status'] == 'STRUCTURAL_PASS' and not obs['definitions_and_imports_only']
        actions = ['REPAIR_EXISTING', 'REGENERATE_FRESH'] if complete and remaining_calls >= 2 else []
        symptom = dict(stage='before_native_retry', artifact=obs['structural_status'],
            complete_candidate=complete, public_result=feedback.status, exceptions=exceptions,
            finish_reason=fact['finish_reason'], actions=actions)
        group = fingerprint(symptom);key = fingerprint([self.stream_id, group])
        old = self.states().get(key)
        if old and fact['event_id'] in old['source_evidence_ids']:
            return old
        state = dict(old) if old else dict(hypothesis_id=key,group_id=group,version=0,
            symptom=symptom,claim='Compare existing-code repair with fresh generation; preference unknown',
            source_evidence_ids=[],supporting_evidence_ids=[],contradicting_evidence_ids=[],
            applicable_actions=actions,known_limitations=['Symptom similarity is not shared root cause or benefit'],
            linked_operator_versions=[],status='UNTESTED')
        state['source_evidence_ids'] = state['source_evidence_ids'] + [fact['event_id']]
        state['independent_task_count'] = len({visible[x]['task_id'] for x in state['source_evidence_ids'] if x in visible})
        state['provenance_groups'] = sorted({visible[x]['provenance_group_id'] for x in state['source_evidence_ids'] if x in visible})
        self._version(state, at)
        return state

    def _version(self, state, at):
        state['version'] += 1; state['last_updated_at'] = at
        self.events.append('HYPOTHESIS_VERSION',state,at)

    def feedback(self, hypothesis_id, evidence_id, *, supports, claim, at):
        if type(supports) is not bool or not claim.strip():raise ValueError('explicit hypothesis review required')
        known = {x['event_id'] for x in self.store.visible(at,self.stream_id)}
        if evidence_id not in known:raise ValueError('online public evidence required')
        s = self.states()[hypothesis_id]
        field = 'supporting_evidence_ids' if supports else 'contradicting_evidence_ids'
        if evidence_id in s[field]:return
        s[field] = s[field] + [evidence_id];s['claim']=claim;s['status']='SUPPORTED_LOCALLY' if supports else 'COUNTEREVIDENCE'
        self._version(s,at)

    def schedule(self, *, at, budget_available, max_families=2):
        from .compile_queue import CompileQueue
        queue=CompileQueue(self.events.path,max_families=max_families)
        return queue.schedule_hypotheses(self,at=at,budget_available=budget_available)

    def start(self, job, at):
        if any(r['kind']=='JOB_STARTED' and r['payload']['job_id']==job['job_id'] for r in self.events.records()):
            raise ValueError('job already consumed; interrupted job requires reconciliation')
        if not set(job['evidence_ids']) <= {x['event_id'] for x in self.store.visible(at,self.stream_id)}:raise ValueError('revoked learning evidence')
        self.events.append('JOB_STARTED',job,at)

    def finish(self,job,candidate_id,at):
        if candidate_id:
            s=self.states()[job['hypothesis_id']]
            s['linked_operator_versions']=s['linked_operator_versions']+[candidate_id]
            self._version(s,at)
        self.events.append('JOB_FINISHED',dict(job_id=job['job_id'],candidate_id=candidate_id),at)
