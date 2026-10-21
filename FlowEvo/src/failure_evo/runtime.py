"""Budgeted, public-only FlowEvo stage controller with optional l3 repair operator."""
import ast,hashlib,json,pathlib,time,tempfile,math
from dataclasses import dataclass,field
from .contracts import PublicTaskView,PublicFeedback,OperatorCard,Fingerprint,canonical,fingerprint

class BudgetExhausted(RuntimeError):pass
@dataclass
class Budget:
    max_calls:int=5
    max_tokens:int=250000
    max_tools:int=100
    wall_seconds:float=300
    clock:object=time.monotonic
    calls:int=0
    used_tokens:int=0
    tool_calls:int=0
    reservations:dict=field(default_factory=dict)
    def __post_init__(self):
        if any(type(x) is not int or x<0 for x in [self.max_calls,self.max_tokens,self.max_tools]) or isinstance(self.wall_seconds,bool) or not math.isfinite(self.wall_seconds) or self.wall_seconds<=0:raise ValueError('invalid budget')
        self.started=self.clock()
    @property
    def remaining_seconds(self):return max(0,self.wall_seconds-(self.clock()-self.started))
    def reserve(self,input_upper,output_upper):
        if any(type(x) is not int or x<0 for x in [input_upper,output_upper]):raise ValueError("nonnegative integer token bounds required")
        bound=input_upper+output_upper
        if self.calls>=self.max_calls or self.used_tokens+sum(self.reservations.values())+bound>self.max_tokens or self.remaining_seconds<=0:raise BudgetExhausted('model budget exhausted')
        self.calls+=1;key=self.calls;self.reservations[key]=bound;return key
    def settle(self,key,tokens=None):
        bound=self.reservations.pop(key)
        if tokens is None:self.used_tokens+=bound;return
        if type(tokens) is not int or tokens<0 or tokens>bound:
            self.used_tokens+=bound;raise BudgetExhausted('invalid or unbounded provider usage')
        self.used_tokens+=tokens
    def tool(self):
        if self.tool_calls>=self.max_tools or self.remaining_seconds<=0:raise BudgetExhausted('tool/time budget exhausted')
        self.tool_calls+=1
    def snapshot(self):return {'calls':self.calls,'charged_or_reserved_tokens':self.used_tokens+sum(self.reservations.values()),'tool_calls':self.tool_calls}

class Router:
    def __init__(self,cards=(),evidence_validator=None):self.cards=tuple(cards);self.evidence_validator=evidence_validator
    def choose(self,task,code,feedback,stage,context,at,budget,fallback_seconds=1):
        blocked=[];eligible=[]
        try:names={n.id for n in ast.walk(ast.parse(code)) if isinstance(n,ast.Name)}
        except SyntaxError:names=set()
        for c in self.cards:
            reason=''
            admission_valid=False;admission_error=False
            if c.status=='active' and c.published_at<=at and c.evidence_fingerprint==context and self.evidence_validator is not None:
                try:admission_valid=self.evidence_validator(c,context,at)
                except Exception:admission_error=True
            if c.status!='active':reason='not_active'
            elif not c.evidence_id or not c.evidence_scope:reason='missing_evidence_scope'
            elif c.published_at>at:reason='not_published_yet'
            elif c.evidence_fingerprint!=context:reason='evidence_fingerprint_mismatch'
            elif admission_error:reason='evidence_lookup_failed'
            elif not admission_valid:reason='no_valid_admission_record'
            elif stage not in c.stages:reason='unsupported_stage'
            elif feedback.status not in c.allowed_feedback:reason='unsupported_feedback'
            elif not pathlib.Path(c.artifact_path).is_file() or hashlib.sha256(pathlib.Path(c.artifact_path).read_bytes()).hexdigest()!=c.artifact_sha256:reason='artifact_changed'
            elif any(not pathlib.Path(p).is_file() or hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()!=h for p,h in c.dependency_files):reason='dependency_changed'
            elif not c.required_ast_names and not c.prompt_terms:reason='applicability_unknown'
            elif not set(c.required_ast_names)<=names or not all(term.lower() in task.prompt.lower() for term in c.prompt_terms):reason='precondition_not_met'
            elif budget.remaining_seconds<c.max_seconds+fallback_seconds or budget.tool_calls>=budget.max_tools:reason='no_operator_and_fallback_budget'
            if reason:blocked.append({'operator_id':c.operator_id,'reason':reason})
            else:eligible.append(c)
        if len(eligible)>1:
            blocked +=[{'operator_id':c.operator_id,'reason':'ambiguous_multiple_applicable'} for c in eligible];eligible=[]
        return (eligible[0] if eligible else None),blocked

class SandboxOperatorRunner:
    """worker_factory must be a process-isolated host adapter, e.g. sandbox.Worker."""
    def __init__(self,worker_factory,protocol="v1"):self.worker_factory=worker_factory;self.protocol=protocol
    def run(self,card,payload,timeout):
        allowed={'ast','json','math','collections','itertools','functools','re','heapq','bisect','fractions','statistics'}
        try:
            source=pathlib.Path(card.artifact_path).read_text()
            if hashlib.sha256(source.encode()).hexdigest()!=card.artifact_sha256:return {'status':'error','reason':'artifact_changed_before_execution'}
            tree=ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node,ast.Import) and any(x.name.split('.')[0] not in allowed for x in node.names):raise ValueError()
                if isinstance(node,ast.ImportFrom) and (node.level or (node.module or '').split('.')[0] not in allowed):raise ValueError()
                if isinstance(node,ast.Name) and (node.id.startswith('__') or node.id in {'open','eval','exec','compile','getattr','setattr','globals','locals','vars','input','breakpoint','help'}):raise ValueError()
                if isinstance(node,ast.Attribute) and node.attr.startswith('__'):raise ValueError()
        except (ValueError,SyntaxError,OSError):return {'status':'error','reason':'static_operator_policy_rejected'}
        # Bind the verified byte snapshot, not a mutable pathname checked earlier.
        with tempfile.TemporaryDirectory(prefix='flowevo_operator_') as directory:
            snapshot=pathlib.Path(directory)/'operator.py';snapshot.write_text(source);snapshot.chmod(0o444)
            with self.worker_factory(snapshot) as worker:
                r=worker.call({'mode':'function','function':'repair_operator','args':[payload],'timeout':timeout})
        if r.get('status')!='OK':return {'status':'error','reason':r.get('status','WORKER_ERROR')}
        value=r.get('value')
        if self.protocol=='v2':
            if not isinstance(value,dict):return {'status':'error','reason':'invalid_operator_contract'}
            return value
        if not isinstance(value,dict) or value.get('status') not in ['declined','proposed','error']:return {'status':'error','reason':'invalid_operator_contract'}
        if any(k in value and not isinstance(value[k],str) for k in ['diagnostic','proposed_code','reason']):return {'status':'error','reason':'non_string_operator_field'}
        if len(canonical(value).encode())>16384:return {'status':'error','reason':'operator_output_too_large'}
        return {k:value[k] for k in ['status','diagnostic','proposed_code','reason'] if k in value}

class Controller:
    stages=(('l1',0.0),('l2a',.5),('l2b',.5),('l3',.7),('l4',.2))
    def __init__(self,generator,public_evaluator,context,router=None,operator_runner=None,clock=time.time,max_output=32768,plugin=None,request_adapter=None):
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
        for stage,temp in self.stages:
            if plugin and stage!='l1':
                applied=plugin.invoke('before_native_retry',stage,stage,previous,feedback,budget,self.evaluate,self.clock())
                if applied:
                    best={k:applied[k] for k in ['stage','code','code_sha256']};previous=applied['code'];feedback=applied['public_feedback'];break
            payload={'task':task.to_dict(),'stage':stage,'temperature':temp,'max_tokens':self.max_output}
            operator=None;blocked=[];proposal=None
            if stage in ['l3','l4']:
                payload.update(previous_candidate=previous,feedback=feedback.to_dict())
                operator,blocked=(None,[]) if plugin else self.router.choose(task,previous,feedback,stage,self.context,self.clock(),budget)
                if operator and self.operator_runner is None:
                    blocked.append({'operator_id':operator.operator_id,'reason':'runner_unavailable'});operator=None
                if operator and self.operator_runner:
                    try:
                        budget.tool();proposal=self.operator_runner.run(operator,{'task':task.to_dict(),'candidate':previous,'feedback':feedback.to_dict(),'remaining_budget':budget.snapshot()},min(operator.max_seconds,budget.remaining_seconds))
                    except Exception as exc:proposal={'status':'error','reason':type(exc).__name__}
                    if proposal.get('status')=='proposed':payload['operator_proposal']={k:proposal[k] for k in ['diagnostic','proposed_code'] if k in proposal}
            if self.request_adapter is not None:payload=self.request_adapter(payload)
            try:reservation=budget.reserve(len(canonical(payload).encode())+4096,self.max_output)
            except BudgetExhausted:break
            charged=False
            try:
                payload['timeout_seconds']=budget.remaining_seconds
                response=self.generator(payload)
                observed_candidate=None
                if plugin:
                    raw_code=response.get('code','')
                    observed_candidate=plugin.observe(raw_code if isinstance(raw_code,str) else '',stage,PublicFeedback('UNKNOWN'),response,self.clock(),hashlib.sha256(previous.encode()).hexdigest() if previous else '',learnable=False)
                budget.settle(reservation,response.get('usage',{}).get('total_tokens'));charged=True
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
                            feedback=checked_public_feedback(self.evaluate(task,code))
                            if budget.remaining_seconds<=0:raise TimeoutError('public evaluator exceeded deadline')
                        else:feedback=PublicFeedback.project(self.evaluate(task,code))
                if plugin:
                    observed_candidate['public_feedback']=feedback.to_dict()
                previous=code
                event={'stage':stage,'request':payload,'operator_id':operator.operator_id if operator else None,'blocked':blocked,'operator_status':proposal.get('status') if proposal else None,
                       'code':code,'code_sha256':hashlib.sha256(code.encode()).hexdigest(),'public_feedback':feedback.to_dict(),'budget':budget.snapshot()}
                events.append(event)
                if feedback.status=='PUBLIC_PASS':best={'stage':stage,'code':code,'code_sha256':event['code_sha256']};break
            except Exception as exc:
                if reservation in budget.reservations:budget.settle(reservation,None)
                events.append({'stage':stage,'request':payload,'error':type(exc).__name__,'budget':budget.snapshot()})
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
        return result
