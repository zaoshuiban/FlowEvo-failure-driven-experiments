"""Small audited I/O boundary for the bounded ScienceWorld experiment.

Importing this module neither contacts a model nor starts the run clock. The
caller owns the frozen protocol, candidate static admission, and experiment.
"""
import hashlib
import json
import os
from pathlib import Path
import time

from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import canonical
from failure_evo.evidence import EvidenceStore
from failure_evo.model_api import configured_api_key
from failure_evo.network_transport import post_deepseek
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.run_health import trusted_usage


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def write_immutable(path, text):
    """Never overwrite an existing artifact, including a partial crash write."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x') as out:
            out.write(text)
            out.flush()
            os.fsync(out.fileno())
        fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except FileExistsError:
        if path.read_text() != text:
            raise PermissionError('immutable output differs: ' + str(path))
    return text


def commit(path, value):
    write_immutable(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    return value


def parse_candidate(raw):
    """Project required compile fields without throwing away rejected source.

    Additional top-level fields are retained as ignored metadata. They never
    become runtime context, permissions, or execution instructions.
    """
    parsed = raw
    errors = []
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError) as exc:
            errors.append('INVALID_JSON: ' + str(exc))
    fields = ('code', 'description', 'applicability')
    if not isinstance(parsed, dict):
        errors.append('TOP_LEVEL_OBJECT_REQUIRED')
        candidate = {key: '' for key in fields}
        ignored = {}
    else:
        candidate = {key: parsed.get(key, '') for key in fields}
        ignored = {key: value for key, value in parsed.items() if key not in fields}
        for key in fields:
            if key not in parsed:
                errors.append('MISSING_FIELD: ' + key)
            elif not isinstance(parsed[key], str):
                errors.append('FIELD_NOT_STRING: ' + key)
            elif not parsed[key].strip():
                errors.append('EMPTY_FIELD: ' + key)
    return dict(candidate, passed=not errors, errors=errors, raw=parsed,
                raw_text=raw if isinstance(raw, str) else None, ignored_metadata=ignored)


class ModelDeliveryError(ValueError):
    def __init__(self, result):
        self.result = result
        super().__init__('incomplete model delivery: ' + str(result.get('finish_reason')))


class StudyIO:
    def __init__(self, root, protocol):
        self.root = Path(root).resolve()
        self.p = json.loads(canonical(protocol))
        ceilings = dict(max_calls=1600, max_tokens=8_000_000, max_tools=1200,
                        max_cost_microusd=10_000_000, wall_seconds=4*3600)
        for key, ceiling in ceilings.items():
            value = self.p[key]
            if type(value) is not int or not 0 < value <= ceiling:
                raise ValueError('authorized experiment bound: ' + key)
        self.budget = PersistentBudget(self.root/'budget.jsonl',
            run_id=self.p['run_id'], protocol_hash=digest(self.p),
            max_calls=self.p['max_calls'], max_tokens=self.p['max_tokens'],
            max_tools=self.p['max_tools'], max_cost_microusd=self.p['max_cost_microusd'],
            token_rate_microusd_per_million=self.p['token_rate_microusd_per_million'],
            tool_cost_upper_microusd=0,
            max_tool_milliseconds=self.p.get('max_tool_milliseconds', self.p['max_tools']*10000),
            tool_milliseconds_upper=10000, wall_seconds=self.p['wall_seconds'])
        self.events = EvidenceStore(self.root/'events.jsonl')
        self.backend = FrozenLinuxBackend(image=self.p['worker']['image'],
                                         worker_script=self.p['worker']['worker_script'])
        if self.backend.manifest() != self.p['worker']:
            raise ValueError('Worker changed')

    def _request_folder(self, ident):
        value = Path(ident)
        if not isinstance(ident, str) or not ident or value.is_absolute() or '..' in value.parts:
            raise ValueError('relative request identity required')
        return self.root/'requests'/value

    def logical_usage(self):
        """Unique logical decisions count even when an exact response is cached."""
        rows = [read(path) for path in (self.root/'requests').rglob('logical_call.json')]
        return dict(logical_calls=len(rows),
                    learning_calls=sum(row['request_id'].startswith('learning/') for row in rows),
                    cache_hits=sum((self._request_folder(row['request_id'])/'cache.json').exists()
                                   for row in rows))

    def model(self, ident, messages, max_tokens=1024, json_output=False, cache=True):
        wire = dict(model=self.p['model'], messages=messages, max_tokens=max_tokens,
                    temperature=0, thinking={'type':'disabled'}, reasoning_effort='none', stream=False)
        if json_output:
            wire['response_format'] = {'type':'json_object'}
        wire_hash = digest(wire)
        folder = self._request_folder(ident)
        upper = len(canonical(wire).encode()) + 256
        if upper > self.p['max_wire_bytes'] + 256:
            raise ValueError('input limit')
        native_limit = self.p.get('native_max_wire_bytes')
        if (native_limit is not None and ident.startswith(('native/', 'pairs/'))
                and not ident.endswith('/plan') and upper > native_limit + 256):
            raise ValueError('native prompt limit')
        logical_path = folder/'logical_call.json'
        if (not logical_path.exists() and ident.startswith('learning/')
                and self.logical_usage()['learning_calls'] >= 3):
            raise ValueError('three logical learning requests exhausted')
        commit(folder/'request.private.json', wire)
        commit(logical_path, dict(request_id=ident, wire_sha256=wire_hash))
        cachefile = self.root/'response_cache'/f'{wire_hash}.json'
        if (folder/'response.json').exists():
            raw = read(folder/'response.json')
        elif cache and cachefile.exists():
            record = read(cachefile)
            # A cache is reusable only while bound to its persisted exact wire.
            source = self._request_folder(record['request_id'])
            if digest(read(source/'request.private.json')) != wire_hash:
                raise ValueError('cache source wire differs')
            raw = record['response']
            if read(source/'response.json') != raw:
                raise ValueError('cache source response differs')
            commit(folder/'cache.json', dict(source=record['request_id'], wire_sha256=wire_hash))
            commit(folder/'response.json', raw)
        else:
            if self.budget.blocking_requests(self.p['network_policy']):
                raise RuntimeError('unsettled request; never resend')
            self.budget.reserve_network(upper, max_tokens, job_id=ident, capability='model',
                request_id=ident, request_hash=wire_hash, policy=self.p['network_policy'], wire_hash=wire_hash)
            raw = post_deepseek(wire, configured_api_key(), budget=self.budget, request_id=ident,
                policy=self.p['network_policy'],
                emit=lambda kind, payload: self.events.append(kind, payload, time.time()))
            commit(folder/'response.json', raw)
            usage = trusted_usage(raw)
            if not usage:
                self.budget.settle(ident)
                raise RuntimeError('unknown provider usage')
            # Supplier tokens are actual; money retains its conservative reservation.
            self.budget.settle(ident, tokens=usage['total_tokens'])
            if cache:
                commit(cachefile, dict(request_id=ident, response=raw))
        if raw.get('model') != self.p['model'] or not trusted_usage(raw):
            raise ValueError('provider identity/usage')
        state = self.budget.request_state(ident)
        if state and state['status'] != 'settled':
            self.budget.settle(ident, tokens=trusted_usage(raw)['total_tokens'])
        choice = raw['choices'][0]
        result = dict(text=choice['message']['content'], usage=trusted_usage(raw),
                      request_id=ident, cache=(folder/'cache.json').exists(), wire_sha256=wire_hash,
                      finish_reason=choice['finish_reason'])
        if result['finish_reason'] != 'stop':
            raise ModelDeliveryError(result)
        return result

    def worker(self, code, context, path):
        code, path = Path(code).resolve(), Path(path).resolve()
        relative = path.relative_to(self.root)
        code_hash, context_hash = sha(code), digest(context)
        if len(canonical(context).encode()) > 65536:
            raise ValueError('Worker context bound')
        if path.exists():
            receipt = read(path)
            if receipt['context_sha256'] != context_hash or receipt['code_sha256'] != code_hash:
                raise ValueError('Worker replay mismatch')
            if receipt['raw'].get('status') in ('EVALUATOR_ERROR', 'WORKER_ERROR'):
                raise RuntimeError('Worker infrastructure failure; stop study: ' + receipt['raw']['status'])
            return receipt['result']
        if self.budget.blocking_requests(self.p['network_policy']):
            raise RuntimeError('unsettled request; stop before Worker execution')
        key = self.budget.tool(job_id=str(relative), capability='environment-policy',
                               request_id='worker/'+str(relative), request_hash=digest([code_hash, context]))
        started = time.monotonic()
        try:
            with self.backend(code) as worker:
                raw = worker.call(dict(mode='function', function='environment_operator', args=[context], timeout=2))
        except BaseException:
            # Do not turn an infrastructure interruption into a candidate failure.
            self.budget.settle(key)
            raise
        elapsed = int((time.monotonic()-started)*1000)
        self.budget.settle(key, tool_milliseconds=elapsed)
        if raw.get('status') in ('EVALUATOR_ERROR', 'WORKER_ERROR'):
            commit(path, dict(context_sha256=context_hash, code_sha256=code_hash, raw=raw,
                result=dict(status='error', state={}, reason='WORKER_INFRASTRUCTURE_ERROR'),
                milliseconds=elapsed, budget_request_id=key))
            raise RuntimeError('Worker infrastructure failure; stop study: ' + raw['status'])
        value = raw.get('value')
        valid = isinstance(value, dict)
        if valid:
            valid = (value.get('status') in ('applied', 'declined') and isinstance(value.get('state'), dict)
                and isinstance(value.get('reason'), str) and len(canonical(value).encode()) <= 8192
                and len(canonical(value['state']).encode()) <= 4096
                and set(value) == ({'status','action','state','reason'} if value.get('status') == 'applied'
                                   else {'status','state','reason'}))
        if not valid or raw.get('status') != 'OK':
            value = dict(status='error', state={}, reason='OUTPUT_CONTRACT_OR_EXECUTION', raw_status=raw.get('status'))
        elif value['status'] == 'applied':
            action = value['action']
            if self.p.get('action_mode') == 'free_text':
                legal = (isinstance(action, str) and bool(action.strip()) and len(action) <= 256
                         and '\n' not in action and '\r' not in action
                         and not action.strip().lower().startswith('reset'))
            else:
                legal = isinstance(action, str) and action in context['admissible_commands']
            if not legal:
                value = dict(status='error', state={}, reason='ACTION_CONTRACT_ERROR')
        commit(path, dict(context_sha256=context_hash, code_sha256=code_hash, raw=raw,
                          result=value, milliseconds=elapsed, budget_request_id=key))
        return value
