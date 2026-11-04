"""Crash-safe, process-serialized run budget. POSIX host only; no network access.

The append-only journal is fsynced *before* a capability can be invoked. A partial
or corrupt record fails closed. Unknown requests keep their full reservation.
One ledger owns all generation, validation and tool accounts for a run.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import time
import uuid
from .contracts import canonical, fingerprint
from .runtime import BudgetExhausted


def integer(value, name):
    if type(value) is not int or value < 0:
        raise ValueError('nonnegative integer required: ' + name)
    return value


class PersistentBudget:
    def __init__(self, path, *, run_id, protocol_hash, max_calls, max_tokens,
                 max_tools, max_cost_microusd, token_rate_microusd_per_million,
                 tool_cost_upper_microusd, max_tool_milliseconds,
                 tool_milliseconds_upper, wall_seconds, clock=time.time):
        if not run_id or not protocol_hash:
            raise ValueError('run and protocol identity required')
        values = dict(max_calls=max_calls,max_tokens=max_tokens,max_tools=max_tools,
            max_cost_microusd=max_cost_microusd,token_rate_microusd_per_million=token_rate_microusd_per_million,
            tool_cost_upper_microusd=tool_cost_upper_microusd,max_tool_milliseconds=max_tool_milliseconds,
            tool_milliseconds_upper=tool_milliseconds_upper,wall_seconds=wall_seconds)
        for name,value in values.items():integer(value,name)
        if wall_seconds == 0 or tool_milliseconds_upper == 0:
            raise ValueError('positive wall/tool time bounds required')
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.clock=clock
        self.config=dict(values,run_id=run_id,protocol_hash=protocol_hash,currency='USD',cost_unit='microusd')
        with self._locked() as rows:
            if not rows:
                self._append(rows,'RUN_OPENED',dict(config=self.config,deadline=self.clock()+wall_seconds))
            elif rows[0]['payload']['config'] != self.config:
                raise ValueError('run identity, protocol or frozen limits changed')
        self.max_calls=max_calls;self.max_tokens=max_tokens;self.max_tools=max_tools

    @contextmanager
    def _locked(self):
        with self.path.with_suffix(self.path.suffix+'.lock').open('a+b') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            try:
                rows=[];previous='0'*64
                if self.path.exists():
                    raw=self.path.read_bytes()
                    if raw and not raw.endswith(b'\n'):raise ValueError('partial budget record; fail closed')
                    for line in raw.splitlines():
                        row=json.loads(line);digest=row.pop('record_hash')
                        if row['previous_hash']!=previous or fingerprint(row)!=digest:
                            raise ValueError('budget journal integrity failure')
                        row['record_hash']=digest;rows.append(row);previous=digest
                yield rows
            finally:fcntl.flock(lock,fcntl.LOCK_UN)

    def _append(self,rows,kind,payload):
        now=self.clock()
        if not math.isfinite(now):raise ValueError('invalid host clock')
        row=dict(kind=kind,payload=payload,at=now,previous_hash=rows[-1]['record_hash'] if rows else '0'*64)
        row['record_hash']=fingerprint(row)
        with self.path.open('ab') as out:
            out.write((canonical(row)+'\n').encode());out.flush();os.fsync(out.fileno())
        fd=os.open(str(self.path.parent),os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
        rows.append(row)

    @staticmethod
    def _state(rows):
        requests={};shards={}
        for row in rows:
            p=row['payload']
            if row['kind']=='RESERVED':requests[p['request_id']]=dict(p,status='reserved')
            elif row['kind']=='SETTLED':requests[p['request_id']].update(status='settled',settlement=p)
            elif row['kind']=='UNKNOWN':requests[p['request_id']]['status']='unknown'
            elif row['kind']=='NETWORK_BOUND':requests[p['request_id']]['network']=p
            elif row['kind']=='CONNECT_ATTEMPT':requests[p['request_id']]['connection_attempts']=p['attempt']
            elif row['kind']=='NETWORK_SEND_STARTED':requests[p['request_id']]['network_send_started']=True
            elif row['kind']=='NOT_SENT':requests[p['request_id']].update(status='not_sent',not_sent=p)
            elif row['kind']=='NOT_SENT_REOPENED':requests[p['request_id']]['status']='reserved'
            elif row['kind']=='SHARD_CONSUMED':shards[p['shard_id']]=p
        return requests,shards

    def _totals(self,rows):
        requests,_=self._state(rows)
        totals=dict(calls=0,tokens=0,tools=0,cost=0,tool_ms=0)
        for r in requests.values():
            if r['status']=='not_sent':continue
            totals['calls']+=r['kind']=='model';totals['tools']+=r['kind']=='tool'
            settled=r.get('settlement',{})
            totals['tokens']+=settled.get('tokens',r['token_upper'])
            totals['cost']+=settled.get('cost_microusd',r['cost_upper_microusd'])
            totals['tool_ms']+=settled.get('tool_milliseconds',r['tool_milliseconds_upper'])
        return totals

    def _reserve(self,kind,input_upper,output_upper,*,job_id,capability,request_id,request_hash,network_binding=None):
        integer(input_upper,'input');integer(output_upper,'output')
        if not all(isinstance(x,str) and x for x in (job_id,capability,request_id,request_hash)):
            raise ValueError('request provenance required')
        tokens=input_upper+output_upper
        cost=(tokens*self.config['token_rate_microusd_per_million']+999999)//1000000 if kind=='model' else self.config['tool_cost_upper_microusd']
        ms=0 if kind=='model' else self.config['tool_milliseconds_upper']
        with self._locked() as rows:
            requests,_=self._state(rows)
            if request_id in requests:raise ValueError('request already consumed; do not retry')
            total=self._totals(rows)
            if (self.clock()>=rows[0]['payload']['deadline'] or
                total['calls']+(kind=='model')>self.max_calls or total['tools']+(kind=='tool')>self.max_tools or
                total['tokens']+tokens>self.max_tokens or total['cost']+cost>self.config['max_cost_microusd'] or
                total['tool_ms']+ms>self.config['max_tool_milliseconds']):
                raise BudgetExhausted('persistent run budget exhausted')
            payload=dict(run_id=self.config['run_id'],job_id=job_id,
                capability=capability,request_id=request_id,request_hash=request_hash,kind=kind,
                input_upper=input_upper,output_upper=output_upper,token_upper=tokens,
                cost_upper_microusd=cost,tool_milliseconds_upper=ms)
            if network_binding is not None:payload['network']=network_binding
            self._append(rows,'RESERVED',payload)
        return request_id

    def reserve(self,input_upper,output_upper,*,job_id='runtime',capability='model',request_id=None,request_hash=None):
        request_id=request_id or str(uuid.uuid4())
        return self._reserve('model',input_upper,output_upper,job_id=job_id,capability=capability,
            request_id=request_id,request_hash=request_hash or fingerprint([input_upper,output_upper,request_id]))

    def tool(self,*,job_id='runtime',capability='tool',request_id=None,request_hash=None):
        request_id=request_id or str(uuid.uuid4())
        return self._reserve('tool',0,0,job_id=job_id,capability=capability,request_id=request_id,
            request_hash=request_hash or fingerprint([capability,request_id]))

    def settle(self,key,tokens=None,*,cost_microusd=None,tool_milliseconds=None):
        with self._locked() as rows:
            requests,_=self._state(rows)
            if key not in requests:raise ValueError('unknown request id')
            r=requests[key]
            if r['status']=='not_sent':
                if tokens is None and cost_microusd is None and tool_milliseconds is None:return
                raise ValueError('no usage may be assigned to a proven NOT_SENT request')
            if tokens is None and cost_microusd is None and tool_milliseconds is None:
                if r['status']=='settled':return
                if r['status']!='unknown':self._append(rows,'UNKNOWN',dict(request_id=key,reason='usage_not_known'))
                return
            actual=dict(request_id=key)
            for name,value,bound in [('tokens',tokens,r['token_upper']),('cost_microusd',cost_microusd,r['cost_upper_microusd']),('tool_milliseconds',tool_milliseconds,r['tool_milliseconds_upper'])]:
                if value is None:continue
                if type(value) is not int or not 0<=value<=bound:
                    raise BudgetExhausted('usage outside reservation; full reservation retained')
                actual[name]=value
            # No quote-derived number is labeled actual money. Unknown actual cost stays reserved.
            if r['status']=='settled':
                if r['settlement']!=actual:raise ValueError('conflicting duplicate settlement')
                return
            self._append(rows,'SETTLED',actual)

    def request_state(self,key):
        with self._locked() as rows:return self._state(rows)[0].get(key)

    def bind_network(self,key,policy,wire_hash):
        from .network_transport import validate_policy
        policy=validate_policy(policy)
        binding=dict(request_id=key,policy=policy,policy_sha256=fingerprint(policy),wire_sha256=wire_hash)
        with self._locked() as rows:
            r=self._state(rows)[0].get(key)
            if not r or r['kind']!='model':raise ValueError('reserved model request required')
            if r.get('network'):
                if r['network']!=binding:raise ValueError('network policy/wire drift')
            else:raise ValueError('legacy/unbound reservation cannot acquire NOT_SENT proof')

    def start_connection_attempt(self,key):
        with self._locked() as rows:
            r=self._state(rows)[0][key];n=r.get('connection_attempts',0)+1
            if r['status']!='reserved' or r.get('network_send_started') or n>r['network']['policy']['max_connect_attempts']:
                raise ValueError('connection attempt consumed or possibly sent')
            self._append(rows,'CONNECT_ATTEMPT',dict(request_id=key,attempt=n))

    def mark_network_send(self,key):
        with self._locked() as rows:
            r=self._state(rows)[0][key]
            if r['status']!='reserved' or not r.get('network') or not r.get('connection_attempts') or r.get('network_send_started'):
                raise ValueError('send boundary already consumed or not prepared')
            self._append(rows,'NETWORK_SEND_STARTED',dict(request_id=key))

    def mark_not_sent(self,key,reason,*,retry_allowed=True):
        with self._locked() as rows:
            r=self._state(rows)[0][key]
            if r['status']=='not_sent':return
            if r['status']!='reserved' or not r.get('network') or r.get('network_send_started'):
                raise ValueError('cannot release possible/legacy send as NOT_SENT')
            self._append(rows,'NOT_SENT',dict(request_id=key,reason=reason,model_http_started=False,
                retry_allowed=retry_allowed,connection_attempts=r.get('connection_attempts',0),wire_sha256=r['network']['wire_sha256']))

    def reopen_not_sent(self,key):
        from .network_transport import DefinitelyNotSent
        with self._locked() as rows:
            r=self._state(rows)[0][key];p=r.get('network',{}).get('policy',{})
            if r['status']!='not_sent' or r.get('network_send_started'):raise ValueError('only proven NOT_SENT can resume')
            if not r['not_sent'].get('retry_allowed') or r.get('connection_attempts',0)>=p.get('max_connect_attempts',0):
                raise DefinitelyNotSent('connection attempts exhausted or recovery prohibited; new protocol required')
            t=self._totals(rows)
            if (self.clock()>=rows[0]['payload']['deadline'] or t['calls']+1>self.max_calls or
                t['tokens']+r['token_upper']>self.max_tokens or t['cost']+r['cost_upper_microusd']>self.config['max_cost_microusd']):
                raise BudgetExhausted('NOT_SENT recovery exceeds unchanged run budget')
            self._append(rows,'NOT_SENT_REOPENED',dict(request_id=key))

    def reserve_network(self,input_upper,output_upper,*,job_id,capability,request_id,request_hash,policy,wire_hash):
        """Same logical reservation across safe pre-send restarts; never a new POST ID."""
        from .network_transport import validate_policy
        policy=validate_policy(policy)
        old=self.request_state(request_id)
        if old:
            expected=dict(job_id=job_id,capability=capability,request_hash=request_hash,input_upper=input_upper,output_upper=output_upper)
            if any(old[k]!=v for k,v in expected.items()) or not self.safe_pre_send(old,policy):raise ValueError('consumed request or recovery identity drift')
            self.bind_network(request_id,policy,wire_hash)
            if old['status']=='not_sent':self.reopen_not_sent(request_id)
        else:
            binding=dict(request_id=request_id,policy=policy,policy_sha256=fingerprint(policy),wire_sha256=wire_hash)
            # Atomic proof at reservation creation; an old pending account cannot
            # later be relabelled as a request created under the new send boundary.
            self._reserve('model',input_upper,output_upper,job_id=job_id,capability=capability,
                request_id=request_id,request_hash=request_hash,network_binding=binding)
        return request_id

    @staticmethod
    def safe_pre_send(r,policy):
        return bool(policy and r and r['status'] in ('reserved','not_sent') and not r.get('network_send_started')
                    and r.get('network',{}).get('policy')==policy)

    def blocking_requests(self,policy=None):
        with self._locked() as rows:
            return [k for k,r in self._state(rows)[0].items() if r['status'] not in ('settled','not_sent') and not self.safe_pre_send(r,policy)]

    def consume_shard(self,shard_id,*,job_id,request_hash):
        with self._locked() as rows:
            _,shards=self._state(rows)
            if shard_id in shards:raise ValueError('gate shard already consumed')
            self._append(rows,'SHARD_CONSUMED',dict(shard_id=shard_id,job_id=job_id,request_hash=request_hash))

    @property
    def reservations(self):
        with self._locked() as rows:
            requests,_=self._state(rows)
            return {k:r['token_upper'] for k,r in requests.items() if r['status'] not in ('settled','not_sent')}
    @property
    def remaining_seconds(self):
        with self._locked() as rows:return max(0,rows[0]['payload']['deadline']-self.clock())
    @property
    def calls(self):return self.snapshot()['calls']
    @property
    def tool_calls(self):return self.snapshot()['tool_calls']
    @property
    def used_tokens(self):return self.snapshot()['charged_or_reserved_tokens']

    def snapshot(self):
        with self._locked() as rows:
            t=self._totals(rows);requests,shards=self._state(rows)
            return dict(run_id=self.config['run_id'],calls=t['calls'],tool_calls=t['tools'],
                charged_or_reserved_tokens=t['tokens'],charged_or_reserved_cost_microusd=t['cost'],
                charged_or_reserved_tool_milliseconds=t['tool_ms'],
                remaining_calls=self.max_calls-t['calls'],remaining_tokens=self.max_tokens-t['tokens'],
                remaining_tools=self.max_tools-t['tools'],remaining_cost_microusd=self.config['max_cost_microusd']-t['cost'],
                remaining_tool_milliseconds=self.config['max_tool_milliseconds']-t['tool_ms'],
                unknown_or_pending_requests=[k for k,r in requests.items() if r['status'] not in ('settled','not_sent')],
                not_sent_requests=[k for k,r in requests.items() if r['status']=='not_sent'],
                connection_attempts=sum(r.get('connection_attempts',0) for r in requests.values()),
                consumed_gate_shards=sorted(shards))
