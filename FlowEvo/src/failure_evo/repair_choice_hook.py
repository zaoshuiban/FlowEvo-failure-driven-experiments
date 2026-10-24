"""Opt-in adapter for the existing PreparedController and JSON RuleMemory."""
import hashlib
import time
from types import SimpleNamespace
from .contracts import fingerprint
from .failure_events import checked_public_feedback
from .workflow_protocol_v2 import PreflightRejected

class RepairChoiceHook:
    def __init__(self,memory,client,context,*,enabled=True,audit_requests=False):
        self.memory=memory;self.client=client;self.context=context;self.enabled=enabled;self.audit_requests=audit_requests
    def begin(self,task,at):
        # Only versions already experimental at task start may run. Recheck live
        # permission on reservation so suspension takes effect immediately.
        with self.memory._transaction() as (rows,_):
            keys=list(dict.fromkeys(r['candidate_id'] for r in rows))
            eligible=[k for k in keys if self.memory._state(rows,k)['permission']=='experimental']
        self.current={'task':task,'ledger':[],'hooks':[],'keys':eligible,
                      'routing':[], 'snapshot':SimpleNamespace(snapshot_id=fingerprint(eligible))}
    def observe(self,code,stage,feedback,response,at,*args,**kwargs):
        row={'code_sha256':hashlib.sha256(code.encode()).hexdigest(),'stage':stage,
             'public_feedback':feedback.to_dict(),'generation_metadata':{'finish_reason':response.get('finish_reason')},
             'at':at,'learnable':kwargs.get('learnable',True),'validation_cost':{}}
        self.current['ledger'].append(row);return row
    def invoke(self,hook,checkpoint,stage,code,feedback,budget,evaluator,at):
        if hook!='before_native_retry' or budget.max_calls-budget.calls<2:return None
        matches=[]
        for key in self.current['keys']:
            state=self.memory.state(key)
            if state['permission']=='experimental' and state['remaining']>0 and self.current['task'].problem_id in state.get('tasks',[]) and self.current['task'].problem_id not in state['used_tasks']:
                a=self.memory.choose(state['rule'],code,feedback,budget)
                if a!='NATIVE':matches.append({'candidate_id':key,'action':a})
        from .repair_choice import generic_choice
        if self.memory.representation=='repair-choice-json-v2':
            from .repair_choice_v2 import generic_choice
        native=generic_choice(code,feedback,budget)
        self.current['routing'].append(dict(at=at,stage=stage,matching=matches,conflict=len({m['action'] for m in matches})>1,
            selection_reason='first authorized matching version in persisted order',generic_action=native,
            cheaper_native_known=False,estimated_cost_difference=None))
        for key in self.current['keys']:
            action=self.memory.reserve_action(key,self.current['task'].problem_id,code,feedback,budget)
            if action=='NATIVE':continue
            started=time.monotonic();before_budget=budget.snapshot()
            audit={'before_outcomes':self.current['ledger'][-1].get('audited_case_outcomes',{}) if self.current['ledger'] else {},'before_stage':self.current['ledger'][-1]['stage'] if self.current['ledger'] else None,'before_code':code,'before_sha256':hashlib.sha256(code.encode()).hexdigest(),'before_feedback':feedback.to_dict(),'generic_action':native,'changed_generic_action':action!=native,'candidate_id':key,'action':action,'at':at,'stage':stage,'status':'error'}
            self.current['hooks'].append(audit)
            try:
                if self.audit_requests:
                    from .repair_choice import action_messages
                    from .workflow_runtime_v2 import PreparedController
                    from .learning_distinctness import request_view,compare
                    native_messages=self.client.native_messages(dict(stage=stage,task=self.current['task'].to_dict(),previous_candidate=code,feedback=feedback.to_dict()))
                    audit['request_distinctness']=compare(
                        request_view(action_messages(action,self.current['task'],code,feedback),limits=self.client.limits,temperature=0),
                        request_view(native_messages,limits=self.client.limits,temperature=dict(PreparedController.stages)[stage]))
                    audit['request_distinctness']['generic_evidence']='counterfactual exact native builder at same checkpoint; not sent'
                response=self.client.execute_action(action,self.current['task'],code,feedback,budget)
                if self.audit_requests:
                    receipts=[r for r in self.client.transport.audit if r['request_id']==f'{self.client.request_prefix}/{self.client.sequence}']
                    audit['request_distinctness']['actual_sent_wire_sha256']=receipts[-1]['request_sha256'] if receipts else None
                    if not receipts or receipts[-1]['request_sha256']!=audit['request_distinctness']['learned'].get('wire_sha256'):raise ValueError('audited/sent request mismatch')
                proposed=response['code']
                budget.tool()
                raw_checked=evaluator(self.current['task'],proposed)
                checked=checked_public_feedback(raw_checked)
                audit['after_outcomes']={fingerprint([c['input'],c['expected']]):c['correct'] for c in raw_checked.get('cases',[]) if type(c.get('correct')) is bool}
                if self.memory.representation=='repair-choice-json-v2' and not audit['after_outcomes'] and checked.status in ('NO_COMPLETE_CODE','COMPILE_ERROR'):
                    audit['after_outcomes']=dict.fromkeys(audit['before_outcomes'],False)
                if budget.remaining_seconds<=0:raise TimeoutError('task deadline')
                self.observe(proposed,stage+':rule',checked,response,at)
                audit.update(status='applied' if checked.status=='PUBLIC_PASS' else 'declined',public_feedback=checked.to_dict(),response=response,proposed_code=proposed,proposed_sha256=hashlib.sha256(proposed.encode()).hexdigest())
                audit.update(budget_after=budget.snapshot(),elapsed_seconds=time.monotonic()-started,model_calls=budget.calls-before_budget['calls'],tokens=budget.snapshot()['charged_or_reserved_tokens']-before_budget['charged_or_reserved_tokens'],fallback_required=audit['status']!='applied',visibility='public')
                self.memory.finish(key,self.current['task'].problem_id,audit)
                if audit['status']=='applied':return {'stage':stage+':rule','code':proposed,'code_sha256':hashlib.sha256(proposed.encode()).hexdigest(),'public_feedback':checked}
                return None
            except PreflightRejected as exc:
                audit.update(status='declined',reason=str(exc),budget_after=budget.snapshot(),fallback_required=True,elapsed_seconds=time.monotonic()-started);self.memory.finish(key,self.current['task'].problem_id,audit);return None
            except Exception as exc:
                audit['error']=type(exc).__name__;self.memory.finish(key,self.current['task'].problem_id,audit)
                raise  # Unknown transport/evaluator state must never initiate retry.
        return None
    def finish(self,at):self.current['finished_at']=at
