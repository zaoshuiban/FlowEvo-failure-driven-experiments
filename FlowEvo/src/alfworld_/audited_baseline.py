"""Audited DeepSeek bridge for the existing ALFWorld action generator."""
import json
import time
from pathlib import Path
from types import SimpleNamespace

from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.model_api import configured_api_key
from failure_evo.network_transport import post_deepseek
from failure_evo.run_health import RunUnhealthy, assert_run_healthy
from failure_evo.workflow_protocol_v2 import Limits, SharedTransport, prepare


class AuditedActionClient:
    def __init__(self, root, budget, config, *, sender=None, request_prefix=""):
        self.root, self.budget, self.config = Path(root), budget, config
        self.events = EvidenceStore(self.root/'requests.jsonl')
        self.sender = sender
        self.request_prefix = request_prefix
        self.episode = None
        self.step = 0

    def begin(self, task_id):
        self.episode = task_id
        self.step = 0

    def health(self):
        assert_run_healthy(budgets=[self.budget],
                          network_policy=self.config['network_policy'] if self.sender is None else None)
        if any(r['kind']=='SEND_UNKNOWN' for r in self.events.records()):
            raise RunUnhealthy('unknown ALFWorld request')

    def generate(self, *, instructions, input_text, settings):
        self.health()
        if self.episode is None or settings.temperature!=0 or settings.max_output_tokens!=self.config['output_tokens']:
            raise PermissionError('unfrozen ALFWorld generation settings')
        request_id = self.request_prefix+self.episode+'/'+str(self.step)
        self.step += 1
        prepared = prepare([dict(role='system',content=instructions),dict(role='user',content=input_text)],
                           limits=Limits(input_token_upper=self.config['input_upper'],output_tokens=self.config['output_tokens']),
                           temperature=0)
        records = [r for r in self.events.records() if r['payload'].get('request_id')==request_id]
        previous = [r['payload'] for r in records if r['kind']=='ACTION_RESPONSE']
        if previous:
            if len(previous)!=1 or previous[0]['wire_sha256']!=prepared.sha256:
                raise PermissionError('replay state or prompt changed')
            result = previous[0]['result']
        else:
            requests = [r['payload'] for r in records if r['kind']=='ACTION_REQUEST']
            frozen = dict(request_id=request_id,wire=prepared.body,wire_sha256=prepared.sha256)
            if requests and requests!=[frozen]:
                raise PermissionError('request identity changed')
            if not requests:
                self.events.append('ACTION_REQUEST',frozen,time.time())

            def send(wire):
                body = json.loads(wire)
                if self.sender is not None:
                    self.events.append('SEND_STARTED',dict(request_id=request_id),time.time())
                    try:
                        raw = self.sender(body)
                    except BaseException:
                        self.events.append('SEND_UNKNOWN',dict(request_id=request_id),time.time())
                        raise
                else:
                    def emit(kind,payload):
                        self.events.append(kind,dict(payload,request_id=request_id),time.time())
                    raw = post_deepseek(body,configured_api_key(),budget=self.budget,request_id=request_id,
                                        policy=self.config['network_policy'],emit=emit)
                self.events.append('RAW_RESPONSE',dict(request_id=request_id,response=raw),time.time())
                return raw

            cfg = self.budget.config
            transport = SharedTransport(self.budget,send,authorized=dict(
                run_id=cfg['run_id'],protocol_hash=cfg['protocol_hash']),
                network_policy=self.config['network_policy'] if self.sender is None else None)
            result = transport.send(prepared,request_id=request_id,capability='alfworld-action')
            if result['finish_reason']!='stop':
                # Usage is already settled. This is delivery failure, not task failure.
                raise RunUnhealthy('action delivery incomplete')
            self.events.append('ACTION_RESPONSE',dict(request_id=request_id,wire_sha256=prepared.sha256,
                                                      result=result),time.time())
        usage = result['usage']
        return SimpleNamespace(text=result['text'],prompt_tokens=usage['prompt_tokens'],
                               completion_tokens=usage['completion_tokens'],
                               total_tokens=usage['total_tokens'])


def classify_trace(trace):
    if trace.success:
        return 'SUCCESS'
    if trace.failure_type.startswith('llm_error'):
        return 'INFRASTRUCTURE_OR_DELIVERY_ERROR'
    if trace.total_steps>=trace.max_steps:
        return 'STEP_LIMIT'
    if trace.failure_type=='action_cycle_detected':
        return 'ACTION_CYCLE'
    return 'NO_PROGRESS'


def summarize(episodes, budget):
    completed = [e for e in episodes if e['status']!='INFRASTRUCTURE_OR_DELIVERY_ERROR']
    correct = sum(e['status']=='SUCCESS' for e in completed)
    state = budget.snapshot()
    return dict(episodes_recorded=len(episodes),evaluable=len(completed),successes=correct,
                success_rate=correct/len(completed) if completed else None,
                infrastructure_missing=len(episodes)-len(completed),budget=state,
                cost_basis='CONSERVATIVE_RESERVED_RATE_NOT_PROVIDER_INVOICE')
