"""Opt-in versioned controller for final-wire, single-owner model accounting.

Uses WorkflowClient (or an equivalent budget-owning callable). S15 remains
frozen. Selecting this class is a protocol change, not a rerun of S15.
"""
from .runtime import (ast, hashlib, time, PublicTaskView, PublicFeedback, Router)
from .workflow_protocol_v2 import PreflightRejected

class PreparedController:
    stages=(('l1',0.0),('l2a',.5),('l2b',.5),('l3',.7),('l4',.2))
    def __init__(self,generator,public_evaluator,context,router=None,operator_runner=None,clock=time.time,max_output=8192,plugin=None,request_adapter=None,allow_task_start=False):
        self.allow_task_start=allow_task_start
        self.generator=generator;self.evaluate=public_evaluator;self.context=context;self.router=router or Router();self.operator_runner=operator_runner;self.clock=clock;self.max_output=max_output;self.plugin=plugin;self.request_adapter=request_adapter
    def solve(self,raw_task,budget):
        task=PublicTaskView.project(raw_task);events=[];previous='';feedback=PublicFeedback('UNKNOWN');best=None
        plugin=self.plugin if self.plugin is not None and self.plugin.enabled else None
        if plugin:
            if plugin.context!=self.context:raise ValueError('plugin baseline fingerprint differs')
            plugin.begin(task,self.clock())
        return self._solve(task,budget,events,previous,feedback,best,plugin)

    def _solve(self,task,budget,events,previous,feedback,best,plugin):
        try:
            return self._run(task,budget,events,previous,feedback,best,plugin)
        finally:
            if plugin:plugin.finish(self.clock())

    def _run(self,task,budget,events,previous,feedback,best,plugin):
        if plugin and self.allow_task_start:
            applied=plugin.invoke('before_native_start','task_start','l1','',PublicFeedback('NO_COMPLETE_CODE'),budget,self.evaluate,self.clock())
            if applied:
                return dict(problem_id=task.problem_id,status='PUBLIC_ACCEPTED',
                    selected={k:applied[k] for k in ('stage','code','code_sha256')},
                    retained_candidates=[applied['code_sha256']],last_candidate=applied['code'],events=[],
                    budget=budget.snapshot(),hidden_correctness='NOT_QUERIED',
                    candidate_ledger=plugin.current['ledger'],hook_events=plugin.current['hooks'],
                    registry_snapshot_id=plugin.current['snapshot'].snapshot_id)
        for stage,temp in self.stages:
            if plugin and stage!='l1':
                applied=plugin.invoke('before_native_retry',stage,stage,previous,feedback,budget,self.evaluate,self.clock())
                if applied:
                    best={k:applied[k] for k in ['stage','code','code_sha256']};previous=applied['code'];feedback=applied['public_feedback'];break
            payload={'task':task.to_dict(),'stage':stage,'temperature':temp,'max_tokens':self.max_output}
            operator=None;blocked=[];proposal=None
            if stage != 'l1':payload.update(previous_candidate=previous,feedback=feedback.to_dict())
            if stage in ['l3','l4']:
                operator,blocked=(None,[]) if plugin else self.router.choose(task,previous,feedback,stage,self.context,self.clock(),budget)
                if operator and self.operator_runner is None:
                    blocked.append({'operator_id':operator.operator_id,'reason':'runner_unavailable'});operator=None
                if operator and self.operator_runner:
                    try:
                        budget.tool();proposal=self.operator_runner.run(operator,{'task':task.to_dict(),'candidate':previous,'feedback':feedback.to_dict(),'remaining_budget':budget.snapshot()},min(operator.max_seconds,budget.remaining_seconds))
                    except Exception as exc:proposal={'status':'error','reason':type(exc).__name__}
                    if proposal.get('status')=='proposed':payload['operator_proposal']={k:proposal[k] for k in ['diagnostic','proposed_code'] if k in proposal}
            if self.request_adapter is not None:payload=self.request_adapter(payload)
            try:
                payload['timeout_seconds']=budget.remaining_seconds
                response=self.generator(payload,budget)
                observed_candidate=None
                if plugin:
                    raw_code=response.get('code','')
                    observed_candidate=plugin.observe(raw_code if isinstance(raw_code,str) else '',stage,PublicFeedback('UNKNOWN'),response,self.clock(),hashlib.sha256(previous.encode()).hexdigest() if previous else '',learnable=False)
                if budget.remaining_seconds<=0:raise TimeoutError('provider exceeded whole-workflow deadline')
                if response.get('model')!=self.context.model:raise ValueError('execution model differs from frozen evidence')
                if plugin:observed_candidate['learnable']=True
                code=response.get('code','')
                if not isinstance(code,str):code=''
                if not code.strip():feedback=PublicFeedback.project({'visibility':'public','status':'NO_COMPLETE_CODE'})
                else:
                    try:ast.parse(code)
                    except SyntaxError:feedback=PublicFeedback.project({'visibility':'public','status':'COMPILE_ERROR'})
                    else:
                        budget.tool()
                        if plugin:
                            observed_candidate['validation_cost']['tool_calls']=1
                            from .failure_events import checked_public_feedback
                            raw_checked=self.evaluate(task,code)
                            feedback=checked_public_feedback(raw_checked)
                            from .contracts import fingerprint
                            observed_candidate['audited_case_outcomes']={fingerprint([c['input'],c['expected']]):c['correct'] for c in raw_checked.get('cases',[]) if type(c.get('correct')) is bool}
                            if budget.remaining_seconds<=0:raise TimeoutError('public evaluator exceeded deadline')
                        else:feedback=PublicFeedback.project(self.evaluate(task,code))
                if plugin:
                    observed_candidate['public_feedback']=feedback.to_dict()
                previous=code
                event={'stage':stage,'request':payload,'operator_id':operator.operator_id if operator else None,'blocked':blocked,'operator_status':proposal.get('status') if proposal else None,
                       'code':code,'code_sha256':hashlib.sha256(code.encode()).hexdigest(),'public_feedback':feedback.to_dict(),'budget':budget.snapshot(),
                       'checkpoint_budget':dict(max_calls=budget.max_calls,max_tokens=budget.max_tokens,max_tools=budget.max_tools,
                           calls=budget.calls,used_tokens=budget.used_tokens,tool_calls=budget.tool_calls,remaining_seconds=budget.remaining_seconds)}
                events.append(event)
                if feedback.status=='PUBLIC_PASS':best={'stage':stage,'code':code,'code_sha256':event['code_sha256']};break
            except Exception as exc:
                events.append({'stage':stage,'request':payload,'error':type(exc).__name__,'request_state':'NOT_SENT' if isinstance(exc,PreflightRejected) else 'SEE_TRANSPORT_AUDIT','diagnosis':getattr(exc,'details',{}),'budget':budget.snapshot()})
                # Unknown model or evaluator state cannot authorize more adaptive calls.
                break
        if plugin and not any('error' in e for e in events):
            applied=plugin.invoke('before_final_return','final','final',previous,feedback,budget,self.evaluate,self.clock())
            if applied:
                best={k:applied[k] for k in ['stage','code','code_sha256']};previous=applied['code']
        result={'problem_id':task.problem_id,'status':'PUBLIC_ACCEPTED' if best else 'UNRESOLVED','selected':best,'retained_candidates':[e['code_sha256'] for e in events if 'code_sha256' in e],
                'last_candidate':previous,'events':events,'budget':budget.snapshot(),'hidden_correctness':'NOT_QUERIED'}
        if plugin:
            result.update(candidate_ledger=plugin.current['ledger'],hook_events=plugin.current['hooks'],registry_snapshot_id=plugin.current['snapshot'].snapshot_id)
        if plugin and 'routing' in plugin.current:result['routing_events']=plugin.current['routing']
        return result
