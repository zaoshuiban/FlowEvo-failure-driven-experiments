"""Budgeted native LLM client and thin DockerWorker-to-Sandbox adapter."""
import copy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import tempfile
import time
from env.sandbox import Sandbox
from runtime.llm_client import LLMResponse
from failure_evo.contracts import canonical, fingerprint
from failure_evo.container_worker import DockerWorker
from failure_evo.skill_runtime import materialize, validate_bundle, logger_identity
from failure_evo.network_transport import post_deepseek
from failure_evo.run_health import trusted_usage

class PilotStop(BaseException):
    """Must cross native best-effort Exception handlers without another model call."""

def write_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2));temp.replace(path)

def save_stop_snapshot(root, budget, *, status, stage, error_type=None):
    """Persist observed state on every exit without settling pending requests."""
    root=Path(root)
    def read_if(path, default):
        return json.loads(path.read_text()) if path.exists() else default
    progress=read_if(root/'collect_progress.json', [])
    value=dict(status=status, stage=stage, error_type=error_type,
        recorded_utc=datetime.now(timezone.utc).isoformat(), budget=budget.snapshot(),
        completed_phases=sorted(p.stem for p in (root/'phases').glob('*.json')),
        training_tasks=[dict(task_id=x.get('row',{}).get('problem_id'),
            public_passed=x.get('final_public_passed',x.get('result',{}).get('passed')),
            score=x.get('independent_training_score'),source_kind=x.get('source_kind'),
            trace_ref=x.get('result',{}).get('trace_file')) for x in progress],
        task_jobs={p.stem:read_if(p,{}) for p in (root/'jobs').glob('*.json')},
        transfer_progress=read_if(root/'transfer_progress.json',[]),
        pending_policy='retain original ledger reservation; never infer no charge or retry')
    write_json(root/'stop_snapshot.json',value)
    return value

class PilotTransport:
    def __init__(self,cfg,root,budget,*,authorized=False,dry=False):
        self.cfg=cfg;self.root=Path(root);self.budget=budget;self.authorized=authorized;self.dry=dry
        self.job='unset';self.role='actor';self.phase='unset';self.ordinal=0
    def context(self,phase,job,role='actor'):
        self.phase=phase;self.job=job;self.role=role;self.ordinal=0
    def request(self,messages,*,json_output=False):
        if self.role=='teacher' and self.phase not in {'acquire','support'}:raise PilotStop('TEACHER_PHASE_FORBIDDEN')
        if not self.dry and not self.authorized:raise PilotStop('PILOT_AUTHORIZATION_REQUIRED')
        if self.budget.blocking_requests():raise PilotStop('UNRESOLVED_REQUEST_STOP')
        if not self.dry and datetime.now(timezone.utc)>=datetime.fromisoformat(self.cfg['absolute_deadline_utc']):raise PilotStop('ABSOLUTE_DEADLINE')
        role=self.cfg[self.role];self.ordinal+=1
        key=f'{self.phase}/{self.job}/{self.role}/{self.ordinal}'
        folder=self.root/'requests'/key
        wire=dict(model=role['model'],messages=messages,max_tokens=role['output_tokens'],thinking={'type':'disabled'},temperature=0,stream=False)
        if json_output:wire['response_format']={'type':'json_object'}
        serialized=len(canonical(wire).encode());upper=serialized+256
        if serialized>role['request_bytes'] or upper>role['input_token_upper']:raise PilotStop('INPUT_BOUND_NO_TRUNCATION')
        if (folder/'response.json').exists():
            saved=json.loads((folder/'request.json').read_text())
            if saved!=wire:raise PilotStop('REPLAY_REQUEST_DRIFT')
            return json.loads((folder/'response.json').read_text())
        if (folder/'request.json').exists() or self.budget.request_state(key):raise PilotStop('CONSUMED_OR_UNKNOWN_REQUEST_NO_REISSUE')
        limit=self.cfg['budget']['teacher_calls' if self.role=='teacher' else 'actor_calls']
        prior=list((self.root/'requests').glob(f'*/*/{self.role}/*/request.json'))
        if len(prior)>=limit:raise PilotStop('ROLE_REQUEST_LIMIT')
        try:
            self.budget.reserve_network(upper,role['output_tokens'],job_id=self.phase+'/'+self.job,capability=self.role,
                request_id=key,request_hash=fingerprint(wire),wire_hash=fingerprint(wire),policy=self.cfg['network'])
        except Exception as exc:raise PilotStop('BUDGET_RESERVATION_STOP:'+str(exc)) from exc
        write_json(folder/'request.json',wire)
        started=time.monotonic()
        if self.dry:
            if json_output:
                content=json.dumps(self.dry_teacher(messages))
            elif 'strategy analyst' in messages[0]['content']:
                content='APPROACH: offline fixture\nSTRATEGY: interface test only\nAPPLICABILITY: development fixture'
            else:
                content=self.dry_actor(messages)
            raw=dict(model='OFFLINE_MOCK',choices=[dict(finish_reason='stop',message=dict(content=content))],usage=dict(prompt_tokens=1,completion_tokens=1,total_tokens=2))
        else:
            from failure_evo.model_api import configured_api_key
            try:raw=post_deepseek(wire,configured_api_key(),budget=self.budget,request_id=key,policy=self.cfg['network'])
            except BaseException as exc:raise PilotStop(type(exc).__name__) from exc
        write_json(folder/'response.json',raw)
        usage=trusted_usage(raw)
        if not usage:self.budget.settle(key);raise PilotStop('UNKNOWN_USAGE_STOP')
        rates=self.cfg['budget']['model_rates'][self.role]
        upper_price=math.ceil((usage['input_tokens']*rates[0]+usage['output_tokens']*rates[1])/1e6)
        try:self.budget.settle(key,tokens=usage['total_tokens'],cost_microusd=0 if self.dry else upper_price)
        except Exception as exc:raise PilotStop('USAGE_BOUND_STOP:'+str(exc)) from exc
        write_json(folder/'receipt.json',dict(role=self.role,phase=self.phase,job=self.job,request_id=key,
            wire_sha256=fingerprint(wire),serialized_bytes=serialized,input_token_upper=upper,usage=usage,
            price_bound_microusd=upper_price,price_kind='peak_uncached_bound_not_invoice',model_response=raw.get('model'),
            system_fingerprint=raw.get('system_fingerprint'),seconds=time.monotonic()-started,dry=self.dry))
        return raw
    def generate(self,*,instructions,input_text,settings):
        raw=self.request([dict(role='system',content=instructions),dict(role='user',content=input_text)])
        u=trusted_usage(raw)
        return LLMResponse(raw['choices'][0]['message']['content'],'offline_mock' if self.dry else 'deepseek',raw.get('model',self.cfg['actor']['model']),u['input_tokens'],u['output_tokens'],u['total_tokens'],0)

class PilotTeacher:
    def __init__(self,transport):self.transport=transport;self.model='MOCK_OFFLINE_INTERFACE' if transport.dry else transport.cfg['teacher']['model']
    def request(self,payload,*,phase):
        if phase not in {'train','development'}:raise PilotStop('TEACHER_PHASE_FORBIDDEN')
        raw=self.transport.request([dict(role='system',content='Return JSON with complete Python code and operations contracts keyed by helper name. Solve only the public training task. For natural reusable operations provide purpose, parameters/types, preconditions, output, side_effects, failure. No external access. When a frozen operation is supplied, import its stable name, use its returned result, and never redefine or modify it.'),dict(role='user',content=canonical(payload))],json_output=True)
        if raw['choices'][0]['finish_reason']!='stop':return dict(code='',delivery='INCOMPLETE',partial_response=raw['choices'][0]['message']['content'])
        try:r=json.loads(raw['choices'][0]['message']['content'])
        except ValueError:return dict(code='',delivery='MALFORMED')
        if isinstance(r,dict):
            r.pop('receipt',None)  # Usage only comes from the provider's separate receipt.
            return r
        return dict(code='',delivery='MALFORMED')

class IsolatedCodeSandbox(Sandbox):
    def __init__(self,*,image,budget,root,timeout_seconds=5, absolute_deadline=None):
        super().__init__(timeout_seconds=timeout_seconds)
        self.absolute_deadline=absolute_deadline
        self.image=image;self.budget=budget;self.root=Path(root);self.phase='preflight';self.job='check';self.ordinal=0
    def context(self,phase,job):self.phase=phase;self.job=job;self.ordinal=0
    def run(self,code,module_bundle=None):
        if self.absolute_deadline and datetime.now(timezone.utc)>=datetime.fromisoformat(self.absolute_deadline):raise PilotStop('ABSOLUTE_DEADLINE')
        bundle=self.dependencies if module_bundle is None else module_bundle
        validate_bundle(bundle)
        self.ordinal+=1;key=f'worker/{self.phase}/{self.job}/{self.ordinal}'
        folder=self.root/'executions'/self.phase/self.job/str(self.ordinal)
        identity=fingerprint(dict(code=code,bundle=bundle,image=self.image,logger_identity=logger_identity()))
        if (folder/'result.json').exists():
            value=json.loads((folder/'result.json').read_text())
            if value['identity']!=identity:raise PilotStop('EXECUTION_REPLAY_DRIFT')
            self.skill_events.extend(value['skill_events']);return value
        if self.budget.request_state(key):raise PilotStop('UNFINISHED_EXECUTION_STOP')
        self.budget.tool(job_id=self.phase+'/'+self.job,capability='isolated_code',request_id=key,request_hash=identity)
        started=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='flowevo_pilot_',dir=self.root) as tmp:
            root=Path(tmp);candidate=root/'candidate.py';candidate.write_text(code);modules=root/'modules';modules.mkdir()
            materialize(bundle,modules,event_path='/tmp/skill_events.jsonl')
            with DockerWorker(candidate,image=self.image,worker_script=Path(__file__).with_name('code_worker.py'),module_dir=modules) as worker:
                raw=worker.call(dict(timeout=self.timeout_seconds))
        elapsed=time.monotonic()-started
        value=dict(returncode=raw.get('returncode',-1),stdout=raw.get('stdout',''),stderr=raw.get('stderr',raw.get('status','')),
            passed=bool(raw.get('passed')),timeout=raw.get('status')=='TIME_LIMIT',skill_events=raw.get('skill_events',[]),
            status=raw.get('status'),seconds=elapsed,identity=identity,code_sha256=fingerprint(code),logger_identity=logger_identity())
        if raw.get('status') in {'EVALUATOR_ERROR','MEMORY_LIMIT','OUTPUT_LIMIT'}:value['passed']=False
        write_json(folder/'input.json',dict(code=code,bundle=bundle))
        write_json(folder/'result.json',value)
        self.budget.settle(key,tool_milliseconds=math.ceil(elapsed*1000),cost_microusd=0)
        self.skill_events.extend(value['skill_events'])
        if raw.get('status') in {'EVALUATOR_ERROR','CALL_LOG_ERROR'}:raise PilotStop('ISOLATED_BACKEND_FAILURE:'+raw['status'])
        return value
