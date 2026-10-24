"""Opt-in adapter for the existing PreparedController and JSON RuleMemory."""
import hashlib
import time
from types import SimpleNamespace
from .contracts import fingerprint
from .failure_events import checked_public_feedback
from .workflow_protocol_v2 import PreflightRejected

class RepairChoiceHook:
    def __init__(self,memory,client,context,*,enabled=True):
        self.memory=memory;self.client=client;self.context=context;self.enabled=enabled
    def begin(self,task,at):
        # Only versions already experimental at task start may run. Recheck live
        # permission on reservation so suspension takes effect immediately.
        with self.memory._transaction() as (rows,_):
            keys=list(dict.fromkeys(r['candidate_id'] for r in rows))
            eligible=[k for k in keys if self.memory._state(rows,k)['permission']=='experimental']
        self.current={'task':task,'ledger':[],'hooks':[],'keys':eligible,
                      'snapshot':SimpleNamespace(snapshot_id=fingerprint(eligible))}
    def observe(self,code,stage,feedback,response,at,*args,**kwargs):
        row={'code_sha256':hashlib.sha256(code.encode()).hexdigest(),'stage':stage,
             'public_feedback':feedback.to_dict(),'generation_metadata':{'finish_reason':response.get('finish_reason')},
             'at':at,'learnable':kwargs.get('learnable',True),'validation_cost':{}}
        self.current['ledger'].append(row);return row
    def invoke(self,hook,checkpoint,stage,code,feedback,budget,evaluator,at):
        if hook!='before_native_retry' or budget.max_calls-budget.calls<2:return None
        for key in self.current['keys']:
            action=self.memory.reserve_action(key,self.current['task'].problem_id,code,feedback,budget)
            if action=='NATIVE':continue
            started=time.monotonic();before_budget=budget.snapshot()
            audit={'before_feedback':feedback.to_dict(),'candidate_id':key,'action':action,'at':at,'stage':stage,'status':'error'}
            self.current['hooks'].append(audit)
            try:
                response=self.client.execute_action(action,self.current['task'],code,feedback,budget)
                proposed=response['code']
                budget.tool()
                checked=checked_public_feedback(evaluator(self.current['task'],proposed))
                if budget.remaining_seconds<=0:raise TimeoutError('task deadline')
                self.observe(proposed,stage+':rule',checked,response,at)
                audit.update(status='applied' if checked.status=='PUBLIC_PASS' else 'declined',public_feedback=checked.to_dict(),response=response)
                audit.update(elapsed_seconds=time.monotonic()-started,model_calls=budget.calls-before_budget['calls'],tokens=budget.snapshot()['charged_or_reserved_tokens']-before_budget['charged_or_reserved_tokens'],fallback_required=audit['status']!='applied',visibility='public')
                self.memory.finish(key,self.current['task'].problem_id,audit)
                if audit['status']=='applied':return {'stage':stage+':rule','code':proposed,'code_sha256':hashlib.sha256(proposed.encode()).hexdigest(),'public_feedback':checked}
                return None
            except PreflightRejected as exc:
                audit.update(status='declined',reason=str(exc));self.memory.finish(key,self.current['task'].problem_id,audit);return None
            except Exception as exc:
                audit['error']=type(exc).__name__;self.memory.finish(key,self.current['task'].problem_id,audit)
                raise  # Unknown transport/evaluator state must never initiate retry.
        return None
    def finish(self,at):self.current['finished_at']=at
