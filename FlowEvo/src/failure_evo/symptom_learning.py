"""Public symptom index and append-only, non-causal hypothesis scheduling.

No model client, authorization, or private evaluator is owned by this index.
"""
from .contracts import fingerprint
from .evidence import EvidenceStore
from .workflow_protocol_v2 import program_observation


class SymptomLearning:
    def __init__(self, path, store, stream_id, representation="repair-choice-json-v1", scheduler_protocol="legacy-id-order"):
        self.representation=representation
        self.scheduler_protocol=scheduler_protocol
        self.events = EvidenceStore(path)
        self.store, self.stream_id = store, stream_id

    def states(self):
        states = {}
        for row in self.events.records():
            if row['kind'] == 'HYPOTHESIS_VERSION':
                states[row['payload']['hypothesis_id']] = row['payload']
        return states

    def ingest(self, fact, feedback, code, *, remaining_calls, at, budget=None):
        visible = {x['event_id']: x for x in self.store.visible(at, self.stream_id)}
        if fact['event_id'] not in visible:
            raise ValueError('unavailable evidence')
        obs = program_observation(code)
        exceptions = sorted({c.get('exception_class') for c in feedback.to_dict()['public_cases'] if c.get('exception_class')})
        # An exception string alone is never certified as a shared cause.
        complete = obs['structural_status'] == 'STRUCTURAL_PASS' and not obs['definitions_and_imports_only']
        actions = ['REPAIR_EXISTING', 'REGENERATE_FRESH'] if complete and remaining_calls >= 2 else []
        if self.representation=='repair-choice-json-v2':
            from .repair_choice_v2 import eligible_actions,observation
            from .runtime import Budget
            budget=budget or Budget(max_calls=remaining_calls)
            actions=list(eligible_actions(code,feedback,budget))
            obs['structural_status']=observation(code,feedback,budget)['candidate_state']
        symptom = dict(stage='before_native_retry', artifact=obs['structural_status'],
            complete_candidate=complete, public_result=feedback.status, exceptions=exceptions,
            finish_reason=fact['finish_reason'], actions=actions)
        group = fingerprint(symptom);key = fingerprint([self.stream_id, group])
        old = self.states().get(key)
        if old and fact['event_id'] in old['source_evidence_ids']:
            return old
        state = dict(old) if old else dict(hypothesis_id=key,group_id=group,version=0,
            symptom=symptom,claim='Recovery preference unverified; no learned hypothesis content yet',content=None,content_version=0,evidence_version=0,effects=[],
            source_evidence_ids=[],supporting_evidence_ids=[],contradicting_evidence_ids=[],
            applicable_actions=actions,known_limitations=['Symptom similarity is not shared root cause or benefit'],
            linked_operator_versions=[],status='UNTESTED')
        state['source_evidence_ids'] = state['source_evidence_ids'] + [fact['event_id']]
        state['independent_task_count'] = len({visible[x]['task_id'] for x in state['source_evidence_ids'] if x in visible})
        state['provenance_groups'] = sorted({visible[x]['provenance_group_id'] for x in state['source_evidence_ids'] if x in visible})
        state['evidence_version']=state.get('evidence_version',0)+1
        state['change_kind']='EVIDENCE_SET_CHANGED'
        self._version(state, at)
        return state

    def _version(self, state, at):
        state['version'] += 1; state['last_updated_at'] = at
        self.events.append('HYPOTHESIS_VERSION',state,at)

    def feedback(self, hypothesis_id, evidence_id, *, supports, claim, at):
        if self.representation=='repair-choice-json-v2':raise ValueError('v2 requires a host functional effect, not a symptom-level support assertion')
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
            s['linked_operator_versions']=list(dict.fromkeys(s['linked_operator_versions']+[candidate_id]))
            self._version(s,at)
        self.events.append('JOB_FINISHED',dict(job_id=job['job_id'],hypothesis_id=job['hypothesis_id'],candidate_id=candidate_id,consumed_diagnostics=[x['effect_id'] for x in self.states()[job['hypothesis_id']].get('effects',[])]),at)

    def learn_content(self,hypothesis_id,content,response_id,at):
        required={'conditions','action','expected_improvement','refusal_conditions','stop_conditions','unknowns'}
        if set(content)!=required or any(not isinstance(x,str) or not x.strip() for x in content.values()):raise ValueError('hypothesis content contract')
        s=self.states()[hypothesis_id];old=s.get('content')
        if old==content:return
        s['content']=content;s['claim']=content['expected_improvement'];s['content_version']=s.get('content_version',0)+1
        s['change_kind']='HYPOTHESIS_CONTENT_CHANGED';s['content_delta']={'before':old,'after':content,'response_id':response_id}
        self._version(s,at)

    def effect(self,hypothesis_id,*,candidate_id,source_event_id,task_id,checkpoint_hash,report,at):
        # report is a HOST-created public assessment, never model self-evaluation.
        if report.get('visibility')!='public':raise ValueError('external assessment cannot update online hypothesis')
        allowed={'visibility','kind','level','source_success','operator_public_pass','regressed','improved','diagnosis','cost','actual_intervention','changed_generic_action','fallback','model_calls','tokens','seconds','paired_cost_benefit','continuation_cost'}
        if set(report)-allowed:raise ValueError('unknown/private functional evidence field')
        if report.get('cost') is not None and set(report['cost'])-{'model_calls','tokens','tool_seconds','actual_currency'}:raise ValueError('unknown functional cost field')
        if report.get('continuation_cost') is not None and (set(report['continuation_cost'])!={'calls','charged_or_reserved_tokens','tool_calls'} or any(type(v) is not int or v<0 for v in report['continuation_cost'].values())):raise ValueError('invalid continuation cost')
        s=self.states()[hypothesis_id]
        fact=next((x for x in self.store.visible(at,self.stream_id) if x['event_id']==source_event_id),None)
        if not fact or fact['task_id']!=task_id or fact['candidate_sha256']!=checkpoint_hash:raise ValueError('effect source/checkpoint mismatch')
        effect=dict(candidate_id=candidate_id,source_event_id=source_event_id,task_id=task_id,
                    checkpoint_hash=checkpoint_hash,report=report,visibility='public')
        effect['effect_id']=fingerprint(effect)
        if any(x['effect_id']==effect['effect_id'] for x in s.get('effects',[])):return effect['effect_id']
        s['effects']=s.get('effects',[])+[effect];s['change_kind']='FUNCTIONAL_EVIDENCE_CHANGED'
        # Public success supports only observed source/usage behavior. No causal
        # or efficiency certification without an actual paired baseline.
        if report.get('regressed'):
            s['contradicting_evidence_ids']=list(dict.fromkeys(s['contradicting_evidence_ids']+[source_event_id]))
            s['status']='COUNTEREVIDENCE';s['known_limitations']=list(dict.fromkeys(s['known_limitations']+['Observed public regression; suspended version must not be reused']))
        elif report.get('source_success') or report.get('operator_public_pass'):
            s['supporting_evidence_ids']=list(dict.fromkeys(s['supporting_evidence_ids']+[source_event_id]))
            s['status']='OBSERVED_PUBLIC_EFFECT_NOT_COMPARATIVE'
        self._version(s,at);return effect['effect_id']
