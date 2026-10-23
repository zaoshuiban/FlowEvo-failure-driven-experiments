"""Explicit experiment-only renewal; older runners remain quota-exhausted.
Host-written grants bind a new stream, exact task allowlist and reviewed evidence.
No source admission, artifact, old event, or completed opportunity is rewritten.
"""
from failure_evo.workflow_policy import WorkflowRegistry
from failure_evo.generations import serialized,bound_file
from failure_evo.contracts import fingerprint
from failure_evo.failure_events import finite_time
import json
from pathlib import Path

class RenewedRegistry(WorkflowRegistry):
    def state(self,card,at=None):
        state=super().state(card,at)
        for row in self._rows(card,at):
            if row['kind']=='NURSERY_PROBATION_EXTENDED':
                state['authorization']=row['payload']['authorization']
                state['opportunity_limit']+=row['payload']['additional_opportunities']
        state['opportunities_remaining']=max(0,state['opportunity_limit']-state['opportunities_used'])
        return state

    @serialized
    def extend(self,card,grant_path,at):
        finite_time(at);state=self.state(card);g=json.loads(Path(grant_path).read_text())
        if not self.valid(card,None) or state['generation']!='nursery' or state['permission']!='experimental' or state['retired'] or state['opportunities_remaining'] or state['completed']!=state['opportunities_used']:
            raise ValueError('only valid exhausted and completed nursery probation can renew')
        if g['artifact_sha256']!=card.artifact_sha256 or g['previous_authorization_sha256']!=fingerprint(state['authorization']) or g['prior_opportunities_used']!=state['opportunities_used']:
            raise ValueError('grant does not bind current immutable state')
        tasks=g['task_ids'];count=g['additional_opportunities']
        if type(count)!=int or not 1<=count<=4 or len(tasks)!=count or len(set(tasks))!=len(tasks) or any(not isinstance(t,str) or not t for t in tasks):raise ValueError('bounded distinct tasks required')
        if not g['user_authorization'] or g['experiment_id']==state['authorization']['experiment_id'] or not g['experiment_id'] or not g['stream_id'] or g['stream_id']==state['authorization']['stream_id']:raise ValueError('fresh explicit grant required')
        if g['effective_from']!=1:raise ValueError('new stream begins at task one')
        files=[bound_file(f) for f in g['review_evidence']];grant=bound_file(dict(path=str(Path(grant_path).resolve()),sha256=__import__('hashlib').sha256(Path(grant_path).read_bytes()).hexdigest()))
        if not files:raise ValueError('review evidence required')
        auth=dict(state['authorization'],experiment_id=g['experiment_id'],stream_id=g['stream_id'],after_task=0,effective_from=1,task_ids=tasks,evidence_files=state['authorization']['evidence_files']+files+[grant],renewal_grant=grant,opportunity_limit=state['opportunity_limit']+count)
        self.events.append('NURSERY_PROBATION_EXTENDED',dict(key=self.key(card),additional_opportunities=count,authorization=auth),at)

    def reserve_opportunity(self,card,**kw):
        tasks=self.state(card)['authorization'].get('task_ids',[])
        if kw['task_id'] not in tasks:return False
        return super().reserve_opportunity(card,**kw)
