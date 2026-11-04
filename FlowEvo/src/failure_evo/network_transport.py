"""Explicit, frozen connection policy. Retries CONNECT, never a model POST.

The budget journal is the durable send boundary. HTTP proxy CONNECT contains no
model prompt or API key. Environment/system proxies and redirects are not used.
"""
import copy
import http.client
import json
import socket
import ssl
import time
from .contracts import canonical, fingerprint
from .run_health import RunUnhealthy

VERSION = 'pre-send-connect-v1'
DEFAULT_POLICY = dict(version=VERSION, route=dict(mode='direct'),
    max_connect_attempts=3, backoff_seconds=[2, 5],
    connect_timeout_seconds=15, response_timeout_seconds=120)

class DefinitelyNotSent(RuntimeError):
    """Durably proved: no model HTTP request was started. Not a math failure."""

class SendUnknown(RuntimeError):
    """POST might have reached the provider. No retry, full reservation retained."""

def validate_policy(policy):
    p=copy.deepcopy(policy)
    if not isinstance(p,dict) or set(p)!=set(DEFAULT_POLICY) or p['version']!=VERSION:
        raise ValueError('network policy schema/version')
    n=p['max_connect_attempts']
    if type(n) is not int or not 1<=n<=5:raise ValueError('connection attempt bound')
    waits=p['backoff_seconds']
    if not isinstance(waits,list) or len(waits)!=n-1 or any(type(x) is not int or not 0<=x<=30 for x in waits) or sum(waits)>90:
        raise ValueError('bounded pre-send backoff required')
    for k,hi in [('connect_timeout_seconds',30),('response_timeout_seconds',300)]:
        if type(p[k]) is not int or not 1<=p[k]<=hi:raise ValueError(k)
    route=p['route']
    if route=={'mode':'direct'}:return p
    if not isinstance(route,dict) or set(route)!={'mode','host','port'} or route['mode']!='http_connect':raise ValueError('explicit direct or HTTP CONNECT route required')
    host=route['host']
    if not isinstance(host,str) or not host or len(host)>253 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-:' for c in host):raise ValueError('proxy host only; no credentials or URL')
    if type(route['port']) is not int or not 1<=route['port']<=65535:raise ValueError('proxy port')
    return p

def _connection(policy,timeout):
    route=policy['route'];proxy=route['mode']=='http_connect'
    c=http.client.HTTPSConnection(route['host'] if proxy else 'api.deepseek.com',
        route['port'] if proxy else 443,timeout=timeout,context=ssl.create_default_context())
    if proxy:c.set_tunnel('api.deepseek.com',443)
    # Once connect() succeeds, request() must not silently create a new connection.
    c.auto_open=0
    return c

def _retryable(exc):
    # Certificate/policy errors are not transient network failures.
    return isinstance(exc,OSError) and not isinstance(exc,(ssl.SSLCertVerificationError,PermissionError))

def post_deepseek(body,key,*,budget,request_id,policy,emit=lambda *a:None,
                  connection_factory=None,sleep=time.sleep):
    policy=validate_policy(policy);wire=canonical(body).encode();wire_hash=fingerprint(body)
    factory=connection_factory or _connection
    budget.bind_network(request_id,policy,wire_hash)
    state=budget.request_state(request_id)
    if state['status'] in ('settled','unknown') or state.get('network_send_started'):
        raise RunUnhealthy('possibly sent request is never retried: '+request_id)
    if state['status']=='not_sent':budget.reopen_not_sent(request_id)
    emit('NETWORK_POLICY',dict(request_id=request_id,policy=policy,policy_sha256=fingerprint(policy)))
    connection=None;retry_allowed=True
    try:
        if not key:
            retry_allowed=False
            raise PermissionError('DEEPSEEK_API_KEY unavailable')
        while True:
            state=budget.request_state(request_id);used=state.get('connection_attempts',0)
            if used>=policy['max_connect_attempts'] or budget.remaining_seconds<=0:
                raise DefinitelyNotSent('pre-send connection budget exhausted: '+request_id)
            if used:
                delay=policy['backoff_seconds'][used-1]
                if budget.remaining_seconds<=delay:raise DefinitelyNotSent('pre-send wall budget exhausted: '+request_id)
                emit('CONNECT_WAIT',dict(request_id=request_id,seconds=delay,next_attempt=used+1))
                sleep(delay)
            budget.start_connection_attempt(request_id)
            emit('CONNECT_ATTEMPT',dict(request_id=request_id,attempt=used+1))
            try:
                connection=factory(policy,min(policy['connect_timeout_seconds'],budget.remaining_seconds))
                connection.connect()  # DNS, TCP, proxy CONNECT, TLS; no model HTTP yet.
                break
            except Exception as exc:
                emit('CONNECT_FAILED',dict(request_id=request_id,attempt=used+1,error_type=type(exc).__name__,errno=getattr(exc,'errno',None),model_http_started=False))
                if connection is not None:
                    connection.close();connection=None
                if not _retryable(exc):
                    retry_allowed=False
                    raise DefinitelyNotSent('non-transient pre-send failure: '+type(exc).__name__) from exc
        # Write-ahead marker: a crash from here on is conservatively UNKNOWN.
        budget.mark_network_send(request_id)
        emit('SEND_STARTED',dict(request_id=request_id,wire_sha256=wire_hash))
        remaining=budget.remaining_seconds
        if remaining<=0:raise TimeoutError('deadline reached at send boundary')
        connection.sock.settimeout(min(policy['response_timeout_seconds'],remaining))
        connection.request('POST','/chat/completions',body=wire,
            headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
        response=connection.getresponse()
        raw=response.read(4*1024*1024+1)
        emit('HTTP_RESPONSE_RECEIVED',dict(request_id=request_id,http_status=response.status,response_bytes=len(raw)))
        if len(raw)>4*1024*1024:raise ValueError('response size limit; incomplete receipt')
        text=raw.decode(errors='replace').replace(key,'[REDACTED]')
        if response.status!=200:return dict(http_status=response.status,error_body=text)
        try:value=json.loads(text)
        except ValueError:return dict(http_status=response.status,transport_status='HTTP_RESPONSE_RECEIVED',parse_error='INVALID_HTTP_JSON',error_body=text)
        if not isinstance(value,dict):return dict(http_status=response.status,transport_status='HTTP_RESPONSE_RECEIVED',parse_error='INVALID_HTTP_OBJECT',raw_response=value)
        return value
    except BaseException as exc:
        state=budget.request_state(request_id)
        if state.get('network_send_started'):
            budget.settle(request_id)
            emit('SEND_UNKNOWN',dict(request_id=request_id,error_type=type(exc).__name__,no_retry=True))
            if isinstance(exc,(KeyboardInterrupt,SystemExit)):raise
            raise SendUnknown('model request may have been sent; no retry: '+type(exc).__name__) from exc
        budget.mark_not_sent(request_id,type(exc).__name__,retry_allowed=retry_allowed)
        emit('NOT_SENT',dict(request_id=request_id,error_type=type(exc).__name__,model_http_started=False,
            connection_attempts=state.get('connection_attempts',0),retry_remaining=max(0,policy['max_connect_attempts']-state.get('connection_attempts',0))))
        if isinstance(exc,(KeyboardInterrupt,SystemExit,DefinitelyNotSent)):raise
        raise DefinitelyNotSent('model request not sent: '+type(exc).__name__) from exc
    finally:
        if connection is not None:connection.close()
