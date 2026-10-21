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
            elif row['kind']=='SHARD_CONSUMED':shards[p['shard_id']]=p
        return requests,shards

    def _totals(self,rows):
        requests,_=self._state(rows)
        totals=dict(calls=0,tokens=0,tools=0,cost=0,tool_ms=0)
        for r in requests.values():
            totals['calls']+=r['kind']=='model';totals['tools']+=r['kind']=='tool'
            settled=r.get('settlement',{})
            totals['tokens']+=settled.get('tokens',r['token_upper'])
            totals['cost']+=settled.get('cost_microusd',r['cost_upper_microusd'])
            totals['tool_ms']+=settled.get('tool_milliseconds',r['tool_milliseconds_upper'])
        return totals

    def _reserve(self,kind,input_upper,output_upper,*,job_id,capability,request_id,request_hash):
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
            self._append(rows,'RESERVED',dict(run_id=self.config['run_id'],job_id=job_id,
                capability=capability,request_id=request_id,request_hash=request_hash,kind=kind,
                input_upper=input_upper,output_upper=output_upper,token_upper=tokens,
                cost_upper_microusd=cost,tool_milliseconds_upper=ms))
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

    def consume_shard(self,shard_id,*,job_id,request_hash):
        with self._locked() as rows:
            _,shards=self._state(rows)
            if shard_id in shards:raise ValueError('gate shard already consumed')
            self._append(rows,'SHARD_CONSUMED',dict(shard_id=shard_id,job_id=job_id,request_hash=request_hash))

    @property
    def reservations(self):
        with self._locked() as rows:
            requests,_=self._state(rows)
            return {k:r['token_upper'] for k,r in requests.items() if r['status']!='settled'}
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
                unknown_or_pending_requests=[k for k,r in requests.items() if r['status']!='settled'],
                consumed_gate_shards=sorted(shards))
