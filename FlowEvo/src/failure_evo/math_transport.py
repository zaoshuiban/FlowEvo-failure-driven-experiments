"""Independent DeepSeek solver channel; explicit authorization and no auto-retry."""
import json,time
from .evidence import EvidenceStore
from .contracts import fingerprint
from .workflow_protocol_v2 import SharedTransport,prepare,Limits
from .model_api import DeepSeekGenerator,configured_api_key

class NoGoldSolverChannel:
    def __init__(self,budget,path,*,authorization=None,mock=False,sender=None):
        self.budget=budget;self.events=EvidenceStore(path);self.authorization=authorization;self.mock=mock;self.sender=sender
        if mock and (sender is None or not budget.config['run_id'].startswith('engineering:')):
            raise PermissionError('mock sender and engineering namespace required')

    def generate_no_gold(self,*,messages,policy,request_id):
        cfg=self.budget.config
        expected=dict(run_id=cfg['run_id'],protocol_hash=cfg['protocol_hash'],model='deepseek-flash',max_cost_microusd=cfg['max_cost_microusd'],paid_api_authorized=True,channel='math-solver-no-gold-v1')
        if not self.mock and self.authorization!=expected:raise PermissionError('new math Run/channel budget authorization required')
        if len(messages)!=2 or any(set(m)!={'role','content'} or not isinstance(m['content'],str) for m in messages):raise ValueError('strict solver messages required')
        if messages[0]['role']!='system' or messages[1]['role']!='user':raise ValueError('solver message roles')
        from code_math.no_gold import SOLVER_SYSTEM,REVIEW_SYSTEM,CONCISE_SOLVER_SYSTEM,CONCISE_REVIEW_SYSTEM
        allowed=(SOLVER_SYSTEM,REVIEW_SYSTEM) if policy.delivery_profile=='legacy' else (CONCISE_SOLVER_SYSTEM,CONCISE_REVIEW_SYSTEM)
        if messages[0]['content'] not in allowed:raise ValueError('unfrozen solver system prompt')
        if any(r['payload'].get('request_id')==request_id for r in self.events.records()):raise RuntimeError('request consumed; unknown never resent')
        prepared=prepare(messages,limits=Limits(input_token_upper=policy.input_upper,output_tokens=policy.output_tokens),temperature=policy.temperature)
        self.events.append('NO_GOLD_REQUEST',dict(request_id=request_id,wire=prepared.body,wire_sha256=prepared.sha256,
            gold_exposed=False,origin='MOCK' if self.mock else 'DEEPSEEK',channel='solver',preflight=prepared.measures),time.time())
        audit=[]
        def send(wire):
            self.events.append('SEND_STARTED',dict(request_id=request_id,wire_sha256=fingerprint(wire.decode()),gold_exposed=False),time.time())
            raw=self.sender(json.loads(wire)) if self.mock else DeepSeekGenerator._post(json.loads(wire),configured_api_key(),min(120,self.budget.remaining_seconds))
            self.events.append('RAW_RESPONSE',dict(request_id=request_id,response=raw,gold_exposed=False),time.time());return raw
        transport=SharedTransport(self.budget,send,authorized=dict(run_id=cfg['run_id'],protocol_hash=cfg['protocol_hash']),audit=audit)
        try:
            result=transport.send(prepared,request_id=request_id,capability='math-solver')
            raw=next(r['payload']['response'] for r in reversed(self.events.records()) if r['kind']=='RAW_RESPONSE' and r['payload']['request_id']==request_id)
            result['reasoning_tokens']=raw.get('usage',{}).get('completion_tokens_details',{}).get('reasoning_tokens',0)
            result['gold_exposed']=False;result['origin']='MOCK' if self.mock else 'DEEPSEEK'
            result['request_sha256']=prepared.sha256
            return result
        finally:
            self.events.append('REQUEST_FINISHED',dict(request_id=request_id,gold_exposed=False,audit=audit),time.time())
