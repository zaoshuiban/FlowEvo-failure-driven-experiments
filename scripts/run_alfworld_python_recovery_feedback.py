"""ALFWorld Python recovery Pilot on frozen, exposed source states."""

import argparse
from collections import Counter, defaultdict
import fcntl
import hashlib
from importlib.metadata import version as package_version
import json
import os
from pathlib import Path
import platform
import re
import subprocess
from tempfile import TemporaryDirectory
from time import time
from types import SimpleNamespace

from alfworld_.failure_learning import (
    EnvironmentPolicyRunner, context_view, register_environment_candidate, static_check_detailed,
)
from alfworld_.generic_recovery_skill import parse_command, receipt_truth
from alfworld_.python_recovery_feedback import (
    INITIAL_PROMPT, PROJECTION_RULES, REVISION_PROMPT, bounded_revision, compare_static, delivery,
    execution_feedback_sha256, initial_payload, parse_delivery, revision_payload, revision_signature,
    revision_stress_packet,
)
from alfworld_.recovery_acquisition import RecoveryAdapter, parse_mechanisms, stage_request
from alfworld_.skill_acquisition import (
    INPUT_LIMIT, StrictTrainEnv, _reset, _step, import_source_events, local_repair_witness, verify_source_game,
)
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.math_stream import read, save, sha
from failure_evo.model_api import configured_api_key
from failure_evo.network_transport import DefinitelyNotSent, SendUnknown, validate_policy
from failure_evo.run_health import RunUnhealthy, assert_run_healthy, trusted_usage
from failure_evo.runtime import BudgetExhausted
import run_alfworld_cross_mechanism_expanded as frozen


VERSION = 'alfworld-python-recovery-feedback-pilot-v2'
PARENT = 'alfworld_recovery_plan_v14_pilot_20261112_01'
PARENT_SHA = 'dd049687410f4df774f0541fd5caace1bf9a70e9f764a0b26fb5217be1a4b629'
UPDATED_DIAGNOSTIC_FILES = (
    'FlowEvo/src/alfworld_/failure_learning.py',
    'FlowEvo/src/failure_evo/math_operators.py',
)
PREVIOUS = frozen.previous
ROOT = PREVIOUS.ROOT
OUTPUT_UPPER = 4096  # The existing replay_train_generation slot size.
REVISION_LIMIT = 2
SOURCE_WINDOW = 18
EPISODE_LIMIT = 50
ENVIRONMENT_LIMIT = 3450  # Includes all extra deterministic replay after interruption.
MAX_STAGNANT_REPEATS = 2
PRICE = dict(verified_date='2026-11-12', currency='USD',
    source='https://api-docs.deepseek.com/quick_start/pricing/',
    model_release_reference='DeepSeek-V4.1-Flash-1017',
    peak_cache_miss_microusd_per_million=300_000,
    peak_cache_hit_microusd_per_million=6_000,
    peak_output_microusd_per_million=1_200_000)
RESERVATION_RATE = 1_200_000
HARD_CAP_INCREMENT = 50_000
VERSION_PACKAGES = ('alfworld', 'textworld', 'numpy', 'PyYAML', 'pydantic', 'pydantic_core')


def ceiling_microusd(tokens, rate):
    return (tokens*rate+999_999)//1_000_000


def estimate_peak(input_tokens, output_tokens):
    return (input_tokens*PRICE['peak_cache_miss_microusd_per_million']
            +output_tokens*PRICE['peak_output_microusd_per_million'])/1_000_000_000_000


def environment_manifest(data):
    return dict(python=platform.python_version(), architecture=platform.machine(),
        packages={name:package_version(name) for name in VERSION_PACKAGES},
        logic_sha256={name:sha(Path(data)/'logic'/name) for name in ('alfred.pddl', 'alfred.twl2')})


def wire(path, packet, prompt):
    adapter = RecoveryAdapter(path, None, model=PREVIOUS.MODEL, mock=True, sender=lambda _: None,
        stage='analyze', payload=packet, parser=parse_delivery, protocol=VERSION,
        analysis_prompt=prompt, max_wire_input_upper=INPUT_LIMIT)
    return adapter.preflight(dict(phase='induction', max_tokens=OUTPUT_UPPER,
        discovery=dict(stage='analyze', payload_sha256=fingerprint(packet))))


def revision_measure(path):
    """Measure oversize packets using the unchanged adapter wire format."""
    body = wire(path, {}, REVISION_PROMPT)

    def measure(packet):
        body['messages'][1]['content'] = canonical(packet)
        return len(canonical(body).encode())+256

    return measure


def frozen_sources(base, output):
    parent = base/PARENT
    protocol, result = read(parent/'protocol.json'), read(parent/'result.json')
    protected = [base/PARENT, base/frozen.EXPANDED, base/PREVIOUS.SOURCE,
                 *(Path(name) for name in protocol['historical_sha256'])]
    if any(output.is_relative_to(p.resolve()) or p.resolve().is_relative_to(output) for p in protected):
        raise PermissionError('use a separate private output directory')
    if (fingerprint(protocol)!=PARENT_SHA or result['protocol_sha256']!=PARENT_SHA
            or result['scope']!='REAL_COMPACT_PLAN_SOURCE_ONLY'):
        raise PermissionError('B v14 frozen source protocol differs')
    old, source, events, host, views, checkpoints, boundaries, backend = frozen.configuration(base, output, False)
    expanded_dir = base/frozen.EXPANDED
    expanded = read(expanded_dir/'result.json')
    expanded_protocol = read(expanded_dir/'protocol.json')
    old['run_id'] = 'real:'+expanded_dir.name
    # These lint modules now emit optional diagnostics. Verify the historical
    # identity against its archived hashes; configuration() freezes live code.
    for name in UPDATED_DIAGNOSTIC_FILES:
        if expanded_protocol['code_sha256'][name]!=protocol['code_sha256'][name]:
            raise PermissionError('historical lint source binding differs')
        old['code_sha256'][name] = expanded_protocol['code_sha256'][name]
    if (old!=expanded_protocol or expanded['protocol_sha256']!=fingerprint(expanded_protocol)
            or protocol['checkpoints_sha256']!=fingerprint(checkpoints)
            or protocol['boundaries_sha256']!=fingerprint(boundaries) or protocol['worker']!=backend.manifest()):
        raise PermissionError('source checkpoints, boundary or Worker identity differs')
    merge_sha, = [row['response_sha256'] for row in expanded['model_receipts'] if row['stage']=='merge']
    raw, = [row['payload']['response'] for row in EvidenceStore(expanded_dir/'provider.jsonl').records()
            if row['kind']=='RAW_RESPONSE' and row['payload']['sha256']==merge_sha]
    if fingerprint(raw)!=merge_sha or raw['choices'][0]['finish_reason']!='stop':
        raise PermissionError('historical mechanism response differs')
    analyses = [row for row in expanded['analyses'] if row['decision']=='HYPOTHESIS']
    merged = parse_mechanisms(json.loads(raw['choices'][0]['message']['content']), analyses)
    if merged!=expanded['merge'] or len(merged['mechanisms'])!=3:
        raise PermissionError('three frozen model mechanisms required')
    by_id = {row['evidence_id']:row for row in checkpoints}
    schedule = []
    for mechanism, entry in zip(merged['mechanisms'], protocol['schedule'], strict=True):
        selected = [by_id[key] for key in mechanism['evidence_ids']]
        if ({row['group'] for row in selected}!={entry['group']}
                or [row['sequence'] for row in selected]!=entry['sequences']):
            raise PermissionError('candidate sources differ from B v14')
        packet = initial_payload(PREVIOUS.generation_payload(mechanism, analyses, views))
        schedule.append((entry['group'], selected, packet))
    history = {**protocol['historical_sha256'], **{str(p):sha(p) for p in parent.rglob('*') if p.is_file()}}
    if len(boundaries)!=21 or sum(len(selected) for _,selected,_ in schedule)!=23:
        raise PermissionError('development case count drift')
    return source, events, host, schedule, boundaries, backend, history


def configuration(base, output, *, env_factory=StrictTrainEnv, real=False):
    base, output = Path(base).resolve(), Path(output).resolve()
    if real and env_factory is not StrictTrainEnv:
        raise PermissionError('real Pilot requires the frozen TextWorld environment')
    source, events, host, schedule, boundaries, backend, history = frozen_sources(base, output)
    verify_history(history)
    files = [Path(__file__).resolve(), ROOT/'FlowEvo/src/alfworld_/python_recovery_feedback.py']
    # Read frozen manifests rather than rescanning historical source trees for code identities.
    files += [ROOT/name for name in read(base/PARENT/'protocol.json')['code_sha256']]
    entries = []
    with TemporaryDirectory() as temp:
        provider = Path(temp)/'provider.jsonl'
        measure = revision_measure(provider)
        for group, selected, packet in schedule:
            body = wire(provider, packet, INITIAL_PROMPT)
            for row in selected:
                verify_source_game(source['data_root'], host[row['evidence_id']])
            entry = dict(group=group, sources=selected, wire_sha256=fingerprint(body),
                         input_upper=len(canonical(body).encode())+256)
            if real:
                slots = [min(SOURCE_WINDOW, EPISODE_LIMIT-row['anchor']) for row in selected]
                stress = revision_stress_packet(packet, slots)
                fitted, audit = bounded_revision(stress, measure, limit=INPUT_LIMIT)
                if (fitted is None or fitted['previous_code']!=stress['previous_code']
                        or audit['input_upper']!=len(canonical(wire(provider,fitted,REVISION_PROMPT)).encode())+256):
                    raise PermissionError('revision stress envelope does not fit the frozen adapter')
                entry['stress_probe'] = dict(source_slots=sum(slots), status=audit['status'], tier=audit['tier'],
                    full_input_upper=measure(stress), fitted_input_upper=audit['input_upper'],
                    previous_code_bytes=len(stress['previous_code'].encode()))
            entries.append(entry)
    calls = len(entries)*(REVISION_LIMIT+1)
    action_slots = sum(min(SOURCE_WINDOW, EPISODE_LIMIT-row['anchor']) for entry in entries for row in entry['sources'])
    original_prefix_steps = sum(row['anchor'] for entry in entries for row in entry['sources'])
    # The compiler reserves the actual wire byte bound for each request.
    # Initial requests have exact sizes; revisions can use the entire bound.
    input_bounds = [entry['input_upper'] for entry in entries]+[INPUT_LIMIT]*(len(entries)*REVISION_LIMIT)
    conservative_cost = sum(ceiling_microusd(size+OUTPUT_UPPER, RESERVATION_RATE) for size in input_bounds)
    hard_cap = ((conservative_cost+HARD_CAP_INCREMENT-1)//HARD_CAP_INCREMENT)*HARD_CAP_INCREMENT
    scope = 'REAL_SOURCE_ONLY' if real else ('MOCK_SOURCE_ONLY' if env_factory is StrictTrainEnv else 'MOCK_ENV_FIXTURE_ONLY')
    plan = dict(version=VERSION, scope=scope,
        run_id=('real:' if real else 'mock:')+output.name, model=PREVIOUS.MODEL, paid_api_authorized=False,
        disposition='SHADOW_SOURCE_ONLY',
        source_protocol_sha256=fingerprint(source), parent_protocol_sha256=PARENT_SHA,
        environment_type=env_factory.__module__+'.'+env_factory.__qualname__,
        code_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))}, historical_sha256=history,
        schedule=entries, boundaries_sha256=fingerprint(boundaries), worker=backend.manifest(),
        pydantic_version=package_version('pydantic'), pydantic_core_version=package_version('pydantic_core'),
        prompt_sha256=fingerprint(INITIAL_PROMPT), revision_prompt_sha256=fingerprint(REVISION_PROMPT),
        revision_limit=REVISION_LIMIT, source_window=SOURCE_WINDOW, episode_limit=EPISODE_LIMIT,
        max_stagnant_repeats=MAX_STAGNANT_REPEATS, initial_prefix_steps=original_prefix_steps,
        environment_steps=ENVIRONMENT_LIMIT, source_action_slots=action_slots*(REVISION_LIMIT+1),
        worker_calls=(action_slots+len(entries)*len(boundaries))*(REVISION_LIMIT+1),
        max_calls=calls, max_tokens=sum(input_bounds)+calls*OUTPUT_UPPER, input_upper=INPUT_LIMIT, output_upper=OUTPUT_UPPER,
        max_cost_microusd=hard_cap)
    plan.update(input_bounds=input_bounds, pricing=PRICE, feedback_projection=PROJECTION_RULES,
        peak_no_cache_quote_upper_usd=estimate_peak(sum(input_bounds), calls*OUTPUT_UPPER),
        conservative_cost_upper_microusd=conservative_cost,
        worker_milliseconds_per_call=15_000, worker_milliseconds_total=plan['worker_calls']*15_000,
        run_wall_seconds=86_400,
        final_version_rule='LAST_SUBMISSION_IN_FROZEN_SCHEDULE',
        revision_rules=['SOURCE_ONLY_NEW_EVIDENCE', 'STATIC_VIOLATION_STRUCTURE', 'LAST_VALID_DECODED_SOURCE',
                        'ABSTAIN_STOPS', 'ALL_SOURCES_RECOVERED_STOPS', 'UNCHANGED_EXECUTION_REUSED',
                        'INPUT_LIMIT_STOPS_STAGE', 'UNKNOWN_BLOCKS_RUN'])
    if real:
        plan.update(environment=environment_manifest(source['data_root']),
                    network_policy=validate_policy(read(base/PARENT/'protocol.json')['network_policy']))
    return plan, source, events, host, schedule, boundaries, backend


def verify_history(history):
    if any(sha(path)!=digest for path,digest in history.items()):
        raise PermissionError('historical artifact changed')


def authorization_for(plan):
    if plan['scope']!='REAL_SOURCE_ONLY':
        raise PermissionError('real protocol required for authorization')
    return dict(run_id=plan['run_id'], protocol_hash=fingerprint(plan), model=plan['model'],
        protocol=plan['version'], max_cost_microusd=plan['max_cost_microusd'], paid_api_authorized=True)


def authorization_template(plan):
    return dict(authorization_for(plan), paid_api_authorized=False)


def frozen_real_inputs(base, output):
    values = configuration(base, output, real=True)
    plan = values[0]
    if (not output.is_dir() or output.stat().st_mode & 0o077
            or not (output/'protocol.json').is_file() or canonical(read(output/'protocol.json'))!=canonical(plan)
            or not (output/'authorization.template.json').is_file()
            or canonical(read(output/'authorization.template.json'))!=canonical(authorization_template(plan))):
        raise PermissionError('private real Pilot and matching frozen protocol required')
    return values


def prepare(base, output):
    output = Path(output).resolve()
    plan, *_ = configuration(base, output, real=True)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    save(output/'protocol.json', plan)
    save(output/'authorization.template.json', authorization_template(plan))
    return plan


def check_local_runtime(plan):
    """Read-only check of the same local Docker and immutable image used by Worker."""
    context = json.loads(subprocess.check_output(['docker','context','inspect'], timeout=5))
    endpoint = context[0]['Endpoints']['docker']['Host']
    if not endpoint.startswith('unix://') or os.environ.get('DOCKER_HOST','').startswith(('tcp:','ssh:')):
        raise RunUnhealthy('local Unix-socket Docker daemon required')
    if subprocess.check_output(['docker','info','--format','{{.OSType}}'], timeout=5, text=True).strip()!='linux':
        raise RunUnhealthy('Linux Docker daemon required')
    image = plan['worker']['image']
    local = subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',image],
                                    timeout=5,text=True).strip()
    if local!=image:
        raise RunUnhealthy('frozen local Docker image differs')


def preflight(base, output):
    output = Path(output).resolve()
    plan, *_ = frozen_real_inputs(base, output)
    check_local_runtime(plan)
    credential = bool(configured_api_key())
    started = (output/'budget.jsonl').exists()
    return dict(status=('RUN_EXISTS_USE_RESUME' if started else
                        'READY_PENDING_AUTHORIZATION' if credential else 'CREDENTIAL_REQUIRED'),
        run_id=plan['run_id'], protocol_sha256=fingerprint(plan), credential_configured=credential,
        worker_ready=True, max_calls=plan['max_calls'], max_tokens=plan['max_tokens'],
        max_cost_microusd=plan['max_cost_microusd'], quote_upper_usd=plan['peak_no_cache_quote_upper_usd'],
        stress_probes=[row['stress_probe'] for row in plan['schedule']], model_requests=0)


def commit(path, value):
    """Idempotent, exact result at a frozen identity."""
    if path.exists():
        if read(path)!=value:
            raise PermissionError('committed receipt differs: '+path.name)
    else:
        save(path, value)
    return value


def start_state(origin, plan):
    anchor = origin['projected']['anchor']
    prefix = origin['steps'][:anchor]
    if not prefix or prefix[-1]['done'] or prefix[-1]['won'] or prefix[-1]['observation']!='Nothing happens.':
        raise PermissionError('verified nonterminal failed prefix required')
    start = context_view(origin['projected']['goal'], prefix[-1]['observation'], prefix[-1]['commands'], prefix, {})
    return prefix, start, fingerprint([origin['row']['game_sha256'], origin['receipt_sha256'], anchor,
                                      start, plan['environment_type'], plan['source_window'], plan['episode_limit']])


class EnvironmentReceipts:
    """Account for host steps using the existing append-only evidence format."""

    def __init__(self, path, cap):
        self.events = EvidenceStore(path)
        self.cap = cap
        self.started = Counter()
        self.branch_steps = defaultdict(Counter)
        self.started_branches = set()
        self.cache_hits = 0
        self.committed = {}
        self.actions = {}
        pending = None
        for row in self.events.records():
            kind, payload = row['kind'], row['payload']
            if kind=='STEP_STARTED':
                if pending or payload['index']!=sum(self.started.values())+1:
                    raise RunUnhealthy('invalid environment step ordering')
                pending = payload
                self.started[payload['scope']]+=1
                self.branch_steps[payload['branch']][payload['scope']]+=1
                self.started_branches.add(payload['branch'])
            elif kind=='STEP_OBSERVED':
                if not pending or payload['index']!=pending['index'] or payload['branch']!=pending['branch']:
                    raise RunUnhealthy('unbound environment step')
                if pending['scope']=='candidate':
                    self.actions.setdefault(payload['branch'], []).append(payload['decision'])
                pending = None
            elif kind=='SOURCE_COMMITTED':
                if pending or payload['branch'] in self.committed:
                    raise RunUnhealthy('invalid environment checkpoint ordering')
                self.committed[payload['branch']] = payload['receipt_sha256']
            elif kind=='WORKER_CACHE_HIT':
                self.cache_hits+=1
            else:
                raise RunUnhealthy('environment requires infrastructure review')
        if pending:
            raise RunUnhealthy('environment step is unresolved')
        if sum(self.started.values())>self.cap:
            raise BudgetExhausted('stored environment budget exhausted')

    def step(self, env, action, *, branch, scope, expected=None, decision=None):
        index = sum(self.started.values())+1
        if index>self.cap:
            raise BudgetExhausted('environment step budget exhausted')
        self.events.append('STEP_STARTED', dict(index=index, branch=branch, scope=scope,
                                               action_sha256=fingerprint(action)), time())
        self.started[scope]+=1
        self.branch_steps[branch][scope]+=1
        self.started_branches.add(branch)
        receipt = _step(env, action)
        if expected is not None and receipt!=expected:
            raise RunUnhealthy('source transition differs')
        payload = dict(index=index, branch=branch, receipt_sha256=fingerprint(receipt))
        if decision is not None:
            payload['decision'] = dict(decision, receipt=receipt)
            self.actions.setdefault(branch, []).append(payload['decision'])
        self.events.append('STEP_OBSERVED', payload, time())
        return receipt

    def finish(self, branch, path, result):
        commit(path, result)
        self.events.append('SOURCE_COMMITTED', dict(branch=branch, receipt_sha256=sha(path)), time())
        self.committed[branch] = sha(path)

    def count_cache_hit(self, decision):
        if decision.pop('worker_cache_hit'):
            self.events.append('WORKER_CACHE_HIT', dict(execution_id=decision['execution_id']), time())
            self.cache_hits+=1


def check_response_commit(budget, provider):
    """Identify a known response that cannot be resumed by the shared compiler."""
    root = provider.events.path.parent
    raw_rows = defaultdict(list)
    http_receipts = {}
    unknown = set()
    for row in provider.events.records():
        payload = row['payload']
        if row['kind']=='RAW_RESPONSE':
            raw_rows[payload['key']].append(payload)
        elif row['kind']=='HTTP_RESPONSE_RECEIVED':
            http_receipts[payload['key']] = payload['http_status']
        elif row['kind']=='SEND_UNKNOWN':
            unknown.add(payload['key'])
    for path in sorted(root.glob('candidate_*/*/compiler.jsonl')):
        rows = EvidenceStore(path).records()
        requests = [row['payload'] for row in rows if row['kind']=='GENERATION_REQUESTED']
        if not requests:
            continue
        request, = requests
        request_sha = fingerprint(request)
        if any(row['kind']=='GENERATION_COMPLETED' and row['payload']['request_sha256']==request_sha for row in rows):
            continue
        family = (request['stream_id'], request['family_id'])
        phase, slot = request['phase'], request['slot']
        key = fingerprint([*family, phase, slot])
        if key in unknown:
            continue
        request_id = fingerprint(['generation', family, phase, slot])
        state = budget.request_state(request_id)
        if key not in raw_rows:
            if key in http_receipts:
                commit(path.parent/'response_review.private.json', dict(status='HTTP_RECEIVED_RAW_REVIEW_REQUIRED',
                    request_id=request_id, request_sha256=request_sha, http_status=http_receipts[key],
                    transport_status='HTTP_RECEIVED_RAW_NOT_ARCHIVED', no_retry=True))
                raise RunUnhealthy('HTTP_RECEIVED_RAW_REVIEW_REQUIRED: '+request_id)
            if state and state.get('network_send_started'):
                raise RunUnhealthy('SEND_UNKNOWN: durable send without a raw receipt: '+request_id)
            continue
        stored, = raw_rows[key]
        raw = stored['response']
        if fingerprint(raw)!=stored['sha256']:
            raise RunUnhealthy('response archive hash differs')
        usage = trusted_usage(raw)
        if (not state or state['request_hash']!=request_sha
                or state.get('network', {}).get('wire_sha256')!=read(path.parent/'request_binding.json')['wire_sha256']):
            raise RunUnhealthy('received response reservation binding differs')
        parsed = [row['payload']['response'] for row in rows if row['kind']=='GENERATION_RESPONSE'
                  and row['payload']['request_sha256']==request_sha]
        settled = state['status']=='settled' and usage and state['settlement'].get('tokens')==usage['total_tokens']
        if (settled and len(parsed)==1 and parsed[0].get('parse_status')=='COMPILE_OUTPUT_CONTRACT_ERROR'
                and parsed[0].get('model')==PREVIOUS.MODEL and parsed[0].get('response_sha256')==stored['sha256']
                and parsed[0].get('raw_response')==raw):
            continue  # The shared compiler can replay this exact rejection.
        http_status = raw.get('http_status',http_receipts.get(key))
        if type(http_status) is int and http_status!=200:
            status = 'PROVIDER_HTTP_REVIEW_REQUIRED'
        elif not settled:
            status = 'RECEIVED_USAGE_REVIEW_REQUIRED'
        elif raw.get('model')!=PREVIOUS.MODEL:
            status = 'PROVIDER_MODEL_REVIEW_REQUIRED'
        else:
            status = 'LOCAL_COMMIT_REVIEW_REQUIRED'
        commit(path.parent/'response_review.private.json', dict(status=status, request_id=request_id,
            request_sha256=request_sha, response_sha256=stored['sha256'], transport_status='RESPONDED',
            http_status=http_status, ledger_status=state['status'], no_retry=True))
        raise RunUnhealthy(status+': '+request_id)


def check_run(budget, provider, worker, network_policy=None):
    if network_policy:
        check_response_commit(budget, provider)
    assert_run_healthy(budgets=[budget], providers=[provider], network_policy=network_policy)
    rows = worker.events.records()
    started = Counter(r['payload']['execution_id'] for r in rows if r['kind']=='ENVIRONMENT_POLICY_STARTED')
    finished = Counter(r['payload']['execution_id'] for r in rows if r['kind']=='ENVIRONMENT_POLICY_EXECUTED')
    if started!=finished or any(count!=1 for count in started.values()):
        raise RunUnhealthy('Worker execution unresolved or duplicated')
    if any(r['kind']=='ENVIRONMENT_POLICY_EXECUTED'
           and r['payload']['raw'].get('origin')=='host_deadline' for r in rows):
        raise RunUnhealthy('host did not receive a confirmed Worker reply')


EXCEPTION_TYPES = frozenset({
    'ArithmeticError','AssertionError','AttributeError','IndexError','KeyError','MemoryError',
    'NameError','OverflowError','RecursionError','RuntimeError','TypeError','ValueError','ZeroDivisionError',
})


def invoke(runner, card, context):
    execution = fingerprint([card.version, context, runner.backend.manifest()])
    cached = any(r['kind']=='ENVIRONMENT_POLICY_EXECUTED' and r['payload']['execution_id']==execution
                 for r in runner.events.records())
    result = runner.run(card, context)
    receipt, = [r['payload'] for r in runner.events.records()
                if r['kind']=='ENVIRONMENT_POLICY_EXECUTED' and r['payload']['execution_id']==execution]
    if (receipt['artifact_sha256']!=card.artifact_sha256 or receipt['context_sha256']!=fingerprint(context)
            or receipt['worker_sha256']!=fingerprint(runner.backend.manifest()) or receipt['result']!=result):
        raise PermissionError('Worker receipt differs')
    raw = receipt['raw']
    if raw.get('origin')=='host_deadline':
        raise RunUnhealthy('host did not receive a confirmed Worker reply')
    selected = raw.get('value')
    action = selected.get('action') if isinstance(selected,dict) and isinstance(selected.get('action'),str) else None
    diagnostic = None
    if result['status']=='error':
        status = raw['status']
        category = result['reason'] if status=='OK' else ('EXCEPTION' if status=='RUNTIME_ERROR' else status)
        diagnostic = dict(category=category)
        if status=='RUNTIME_ERROR':
            kind = str(raw.get('error','')).split(':',1)[0]
            if kind in EXCEPTION_TYPES:
                diagnostic['exception_type'] = kind
            lines = re.findall(r'File "/candidate\.py", line (\d+)', str(raw.get('traceback','')))
            if lines:
                diagnostic['line'] = int(lines[-1])
    return dict(operator=result, worker_status=raw['status'], candidate_error=diagnostic, selected_action=action,
                execution_id=execution, context_sha256=fingerprint(context), artifact_sha256=card.artifact_sha256,
                worker_cache_hit=cached, receipt=None)


def public_state_key(state):
    return fingerprint([state['observation'], sorted(state['commands']), state['score'], state['won']])


def with_effect(decision, before, after):
    changed = public_state_key(before)!=public_state_key(after)
    progressed = after['score']>before['score'] or after['won']
    truth = 'TRUE' if progressed else receipt_truth(parse_command(after['action']), after['observation'])
    return dict(decision, public_state_changed=changed, effect=truth, score_or_win_progress=progressed)


def validate_source(plan, data, origin, source_ref, card, runner, registry, receipts, directory, env_factory, fault):
    if registry.state(card)['permission']!='shadow' or not card.intact():
        raise PermissionError('exact Shadow artifact required')
    prefix, start, start_sha = start_state(origin, plan)
    branch = fingerprint([card.version, start_sha, runner.backend.manifest(), VERSION])
    path = directory/f'{source_ref}.json'
    if branch in receipts.committed:
        if sha(path)!=receipts.committed[branch]:
            raise PermissionError('committed source receipt changed')
        return read(path)
    if path.exists():
        raise RunUnhealthy('source result exists without a commit receipt')
    old_decisions = list(receipts.actions.get(branch, ()))
    resuming = branch in receipts.started_branches
    current, state, actions, decisions = prefix[-1], {}, [], []
    stagnant = Counter()
    stop = 'ACTION_LIMIT'
    env = None
    try:
        try:
            env = env_factory(data, max_steps=plan['episode_limit'])
            env.initialize(frozen_game_files=[str(verify_source_game(data, origin))])
            _reset(env, origin)
        except Exception:
            receipts.events.append('ENVIRONMENT_BLOCKED', dict(branch=branch), time())
            raise
        for expected in prefix:
            receipts.step(env, expected['action'], branch=branch,
                          scope='resume_prefix' if resuming else 'prefix', expected=expected)
        limit = min(plan['source_window'], plan['episode_limit']-len(prefix))
        if len(old_decisions)>limit:
            raise RunUnhealthy('committed source exceeds frozen action limit')
        for offset in range(limit):
            context = context_view(start['goal'], current['observation'], current['commands'], prefix+actions, state)
            prior = offset<len(old_decisions)
            if prior:
                decision = old_decisions[offset]
                if decision['context_sha256']!=fingerprint(context) or decision['artifact_sha256']!=card.artifact_sha256:
                    raise RunUnhealthy('candidate resume context differs')
            else:
                if not runner.budget.remaining_seconds:
                    raise BudgetExhausted('run wall budget exhausted')
                decision = invoke(runner, card, context)
                receipts.count_cache_hit(decision)
            operator = decision['operator']
            decisions.append(decision)
            if operator['status']!='applied':
                stop = 'CANDIDATE_ERROR' if operator['status']=='error' else 'DECLINED'
                break
            command = operator['action']
            if command not in current['commands']:
                raise RunUnhealthy('Worker action differs from live legal list')
            key = (public_state_key(current), command)
            if stagnant[key]>=plan['max_stagnant_repeats']:
                stop = 'NO_PROGRESS_CYCLE'
                decisions[-1] = dict(decision, not_executed_reason=stop)
                break
            after = receipts.step(env, command, branch=branch, scope='resume_candidate' if prior else 'candidate',
                expected=decision['receipt'] if prior else None, decision=None if prior else decision)
            actions.append(after)
            decisions[-1] = with_effect(dict(decision, receipt=after), current, after)
            if decisions[-1]['effect']=='FALSE' or not decisions[-1]['public_state_changed']:
                stagnant[key]+=1
            if decisions[-1]['score_or_win_progress']:
                stagnant.clear()
            current, state = after, operator['state']
            if not prior and fault is not None:
                fault('after_action', dict(branch=branch, source_ref=source_ref, action=after['action']))
            if after['done'] or after['won']:
                stop = 'ENVIRONMENT_TERMINAL'
                break
    finally:
        if env is not None:
            env.close()
    result = score_source(origin, prefix, decisions, actions, stop)
    result.update(source_ref=source_ref, sequence=origin['sequence'], start_sha256=start_sha,
                  evaluation_branch=branch, control_returned=True)
    receipts.finish(branch, path, result)
    if fault is not None:
        fault('after_source', result)
    return result


def score_source(origin, prefix, decisions, actions, stop):
    anchor = len(prefix)
    before = prefix[-2] if anchor>1 else origin['initial']
    witness = local_repair_witness(before, prefix[-1], origin['steps'][anchor:], actions)
    progress = next((i for i,row in enumerate(decisions,1) if row.get('score_or_win_progress')), None)
    if progress is not None and witness is None:
        witness = dict(kind='ENVIRONMENT_SCORE_OR_WIN', step=progress)
    # The prior v14 protocol also recognizes a historical decisive action
    # becoming admissible after a confirmed effect. Keep that witness host-only.
    decisive = PREVIOUS._decisive(origin)['action']
    if witness is None and decisive not in prefix[-1]['commands']:
        witness = next((dict(kind='DECISIVE_ACTION_NEWLY_ADMISSIBLE', step=i, action=decisive)
                        for i,row in enumerate(decisions,1) if row.get('effect')=='TRUE'
                        and decisive in row['receipt']['commands']), None)
    won = bool(actions and actions[-1]['won'])
    if won:
        outcome = 'EPISODE_WON'
    elif witness is not None:
        outcome = 'LOCAL_REPAIR_VERIFIED'
    elif stop=='CANDIDATE_ERROR':
        outcome = 'CANDIDATE_ERROR'
    elif stop=='DECLINED' and not actions:
        outcome = 'DECLINED'
    elif actions and any(r['effect']!='FALSE' for r in decisions if r['receipt'] is not None):
        outcome = 'PROGRESS_UNVERIFIED'
    else:
        outcome = 'REPAIR_FAILED'
    return dict(stop=stop, outcome=outcome, action_returned=any(row['selected_action'] is not None for row in decisions),
        first_action_executed=bool(actions), first_action_verified=bool(actions and decisions[0]['effect']=='TRUE'),
        first_action_observable_effect=bool(actions and (decisions[0]['public_state_changed'] or decisions[0]['effect']=='TRUE')),
        local_repair_verified=witness is not None, local_witness=witness, recovery_completed=progress is not None,
        won=won, actions=actions, decisions=decisions)


def save_exact_source(path, code):
    encoded = code.encode('utf-8')
    digest = hashlib.sha256(encoded).hexdigest()
    if path.exists():
        if sha(path)!=digest:
            raise PermissionError('decoded source differs')
    else:
        temporary = path.with_suffix('.tmp')
        with temporary.open('wb') as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    return digest


def latest_attempt(attempts, status):
    return next((a for a in reversed(attempts) if a['delivery']['status']==status), None)


def record_revision_progress(attempt, attempts):
    previous = latest_attempt(attempts, 'PROPOSE')
    progress = compare_static(previous['static'] if previous else None, attempt['static'])
    if previous is not None and attempt['delivery']['status']=='PROPOSE':
        progress['source_changed'] = previous['code_sha256']!=attempt['code_sha256']
    observed = execution_feedback_sha256(attempt['sources'])
    progress.update(execution_feedback_sha256=observed, new_execution_feedback=(
        observed is not None and all(
            prior['revision_progress']['execution_feedback_sha256']!=observed for prior in attempts)))
    attempt['revision_progress'] = progress


def next_step(attempt, packet, prior_problems, limit, *, attempts=(), revision_limit=REVISION_LIMIT):
    status = attempt['delivery']['status']
    if status=='ABSTAIN':
        return 'ABSTAIN', None
    if attempt.get('reused_evaluation'):
        return 'UNCHANGED_SOURCE_REUSED', None
    if attempt['registration']['status']=='DUPLICATE_SOURCE_REJECTED':
        return 'CROSS_CONTEXT_SOURCE_CONFLICT', None
    sources = attempt['sources']
    if sources and all(source['recovery_completed'] and source['stop']!='CANDIDATE_ERROR' for source in sources):
        return 'SOURCE_RECOVERY_COMPLETE', None
    if status not in ('PROPOSE','SCHEMA_REJECTED'):
        return 'DELIVERY_INCOMPLETE', None
    if limit:
        return 'REVISION_LIMIT_REACHED', None
    stage = f"revision_{attempt['revision_index']+1:02d}"
    accepted = attempt if status=='PROPOSE' else latest_attempt(attempts, 'PROPOSE')
    rejected = attempt if status=='SCHEMA_REJECTED' else latest_attempt(attempts, 'SCHEMA_REJECTED')
    feedback = revision_payload(packet, attempt['delivery'],
        accepted['static'] if accepted else None, accepted['sources'] if accepted else [], stage=stage,
        last_valid_delivery=accepted['delivery'] if accepted else None, rejected_attempt=rejected,
        version_context=dict(current_version=attempt['version'], parent_version=attempt['parent_version'],
            last_valid_version=accepted['version'] if accepted else None,
            remaining_after_revision=revision_limit-attempt['revision_index']-1))
    signature = revision_signature(feedback)
    if signature in prior_problems:
        return 'NO_NEW_DIAGNOSTIC', None
    prior_problems.add(signature)
    return 'REVISION_SCHEDULED', feedback


def register(directory, proposal, response, hypothesis, evidence_ids, known, runner, registry, *, engineering):
    path = directory/'artifact.json'
    if not path.exists():
        registration = register_environment_candidate(directory, dict(proposal, model=response['model'],
            id=response['id'], response_sha256=response['response_sha256']), hypothesis, evidence_ids, known,
            runner.backend.manifest(), registry, engineering=engineering, protocol=VERSION,
            baseline='alfworld-python-source-shadow')
        return json.loads(canonical(registration))
    artifact = read(path)
    card = FailureOperator.from_dict(artifact['card'])
    if (artifact['origin']!=('MOCK' if engineering else 'DEEPSEEK') or artifact['response_id']!=response['id']
            or artifact['response_sha256']!=response['response_sha256'] or artifact['hypothesis']!=hypothesis
            or artifact['description']!=proposal['description'] or artifact['applicability']!=proposal['applicability']
            or tuple(card.evidence_ids)!=tuple(evidence_ids) or not card.intact()
            or registry.state(card)['permission']!='shadow'
            or canonical(registry._rows(card)[0]['payload']['card'])!=canonical(card.to_dict())):
        raise PermissionError('registered version receipt differs')
    return dict(status='SHADOW', card=artifact['card'])


def acquire_group(plan, output, index, group, selected, packet, host, data, budget, registry, runner, receipts,
                  imported, known, sender, provider, env_factory, fault, authorization):
    attempts, cache, prior_problems = [], {}, set()
    message, parent = packet, None
    network_policy = plan.get('network_policy')
    projection = None
    for number in range(plan['revision_limit']+1):
        stage = 'initial' if number==0 else f'revision_{number:02d}'
        relative = f'candidate_{index}/{stage}'
        directory = output/relative
        prompt = INITIAL_PROMPT if number==0 else REVISION_PROMPT
        body = wire(output/'provider.jsonl', message, prompt)
        expected_wire = fingerprint(body)
        input_upper = len(canonical(body).encode())+256
        if projection is not None and projection['input_upper']!=input_upper:
            raise PermissionError('bounded feedback differs from final wire')
        if number==0 and expected_wire!=plan['schedule'][index]['wire_sha256']:
            raise PermissionError('initial prompt changed')
        check_run(budget, provider, runner, network_policy)
        commit(directory/'request_binding.json', dict(stage=stage, wire_sha256=expected_wire, parent_version=parent))
        try:
            response = stage_request(output, relative, 'analyze', message, parse_delivery, budget, sender=sender,
                authorization=authorization, network_policy=network_policy, protocol=VERSION, analysis_prompt=prompt)
        except (DefinitelyNotSent, SendUnknown):
            raise
        except Exception:
            if network_policy:
                check_response_commit(budget, provider)
            raise
        if (response['wire_sha256']!=expected_wire
                or fingerprint(response['raw_response'])!=response['response_sha256']):
            raise PermissionError('response wire or archive differs')
        if fault is not None:
            fault('after_response', dict(group=group, stage=stage))
        parsed = delivery(response)
        billed = trusted_usage(response['raw_response'])
        if not billed:
            raise RunUnhealthy('unmetered model response')
        if billed['input_tokens']>input_upper or billed['output_tokens']>plan['output_upper']:
            raise RunUnhealthy('provider usage outside frozen per-direction bounds')
        raw = response['raw_response']
        attempt = dict(stage=stage, revision_index=number, parent_version=parent, delivery=parsed,
            static=dict(status='NOT_CHECKED'), registration=dict(status='NOT_RUN'), sources=[],
            response_sha256=response['response_sha256'], wire_sha256=expected_wire, usage=billed,
            provider_finish_reason=response['finish_reason'], input_upper=input_upper,
            provider_model=raw.get('model'), provider_response_id=raw.get('id'), provider_created=raw.get('created'),
            provider_system_fingerprint=raw.get('system_fingerprint'),
            peak_no_cache_estimate_usd=estimate_peak(billed['input_tokens'],billed['output_tokens']))
        attempt['version'] = fingerprint([fingerprint(plan), group, stage, parent, expected_wire, attempt['response_sha256']])
        parent = attempt['version']
        if 'submitted_code' in parsed:
            attempt['code_sha256'] = save_exact_source(directory/'decoded.py', parsed['submitted_code'])
        if parsed['status']=='PROPOSE':
            proposal = parsed['proposal']
            code = proposal['code']
            attempt['code_sha256'] = save_exact_source(directory/'decoded.py', code)
            check = static_check_detailed(code)
            attempt['static'] = dict(check, status='PASSED' if check['passed'] else 'REJECTED')
            if check['passed']:
                origins = [host[row['evidence_id']] for row in selected]
                key = fingerprint([attempt['code_sha256'], group, [start_state(o, plan)[2] for o in origins],
                    runner.backend.manifest(), plan['max_stagnant_repeats'], plan['boundaries_sha256'], VERSION])
                attempt['evaluation_id'] = key
                if key in cache:
                    original = cache[key]
                    attempt.update(reused_evaluation=original['version'], registration=dict(status='REUSED_SHADOW'),
                                   sources=original['sources'])
                else:
                    registration = register(directory, proposal, response, packet['hypothesis'],
                        [imported[row['evidence_id']] for row in selected], known, runner, registry,
                        engineering=sender is not None)
                    attempt['registration'] = registration
                    if registration['status']=='SHADOW':
                        card = FailureOperator.from_dict(registration['card'])
                        if card.artifact_sha256!=attempt['code_sha256'] or sha(card.artifact_path)!=attempt['code_sha256']:
                            raise PermissionError('candidate source bytes changed')
                        attempt['sources'] = [validate_source(plan, data, origin, f'source_{j}', card, runner,
                            registry, receipts, directory, env_factory, fault) for j,origin in enumerate(origins,1)]
                        cache[key] = attempt
        record_revision_progress(attempt, attempts)
        disposition, message = next_step(attempt, packet, prior_problems, number==plan['revision_limit'],
                                         attempts=attempts, revision_limit=plan['revision_limit'])
        if message is not None:
            accepted = attempt if parsed['status']=='PROPOSE' else latest_attempt(attempts, 'PROPOSE')
            accepted_dir = output/f'candidate_{index}'/accepted['stage'] if accepted else None
            message, projection = bounded_revision(message, revision_measure(output/'provider.jsonl'), limit=plan['input_upper'])
            projection['last_valid_version'] = accepted['version'] if accepted else None
            projection['source_receipts'] = [
                dict(source_ref=case['source_ref'], stage=accepted['stage'], file=case['source_ref']+'.json',
                     sha256=sha(accepted_dir/(case['source_ref']+'.json')))
                for case in (accepted['sources'] if accepted else [])
            ]
            commit(directory/'revision_projection.private.json', projection)
            attempt['revision_projection'] = projection
            if message is None:
                disposition = 'INPUT_LIMIT'
        attempt['disposition'] = disposition
        commit(directory/'attempt.json', attempt)
        attempts.append(attempt)
        if fault is not None:
            fault('after_attempt', dict(group=group, stage=stage))
        if message is None:
            break
    return dict(group=group, attempts=attempts, disposition=attempts[-1]['disposition'],
        final_version=attempts[-1]['version'], scheduled_source_count=len(selected))


def evaluate_boundaries(output, candidates, boundaries, runner, registry):
    # This evaluation starts after all model requests. Its labels are never projected to the model.
    for index, group in enumerate(candidates):
        for attempt in group['attempts']:
            if attempt['registration']['status']!='SHADOW':
                continue
            card = FailureOperator.from_dict(attempt['registration']['card'])
            if registry.state(card)['permission']!='shadow' or not card.intact():
                raise PermissionError('boundary requires exact Shadow artifact')
            rows = []
            for case in boundaries:
                p = case['public']
                context = context_view(p['goal'], p['observation'], p['admissible_commands'], p['history'], {})
                decision = invoke(runner, card, context)
                # Cache hit is an operational observation. Keep the result stable across re-entry.
                decision.pop('worker_cache_hit')
                rows.append(dict(case=p['id'], expected=case['expected'], category=case['category'], decision=decision))
            path = output/f"candidate_{index}"/attempt['stage']/'boundaries.private.json'
            commit(path, rows)
            attempt['boundary_evaluation'] = dict(sha256=sha(path), cases=len(rows),
                false_triggers=sum(row['expected']=='NO' and row['decision']['operator']['status']=='applied' for row in rows),
                uncertain_triggers=sum(row['expected']=='UNKNOWN' and row['decision']['operator']['status']=='applied' for row in rows),
                errors=sum(row['decision']['operator']['status']=='error' for row in rows))


def count_version_resources(attempt, worker_rows, receipts):
    registration = attempt['registration']
    version = registration.get('card', {}).get('version')
    own_worker = [row for row in worker_rows if row['candidate_version']==version]
    environment = Counter()
    if version:
        for source in attempt['sources']:
            environment.update(receipts.branch_steps[source['evaluation_branch']])
    return dict(worker_calls=len(own_worker), worker_seconds=sum(row['seconds'] for row in own_worker),
                environment=dict(environment))


def version_metrics(attempt, group, boundaries):
    names = ('action_returned', 'first_action_executed', 'first_action_observable_effect',
             'first_action_verified', 'local_repair_verified', 'recovery_completed', 'won')
    sources = attempt['sources']
    outcomes = Counter(case['outcome'] for case in sources)
    outcomes['NOT_REACHED'] = group['scheduled_source_count']-len(sources)
    boundary = attempt.get('boundary_evaluation')
    return dict(source_denominator=group['scheduled_source_count'], source_outcomes=dict(outcomes),
        **{name:sum(case[name] for case in sources) for name in names}, boundary_denominator=len(boundaries),
        boundary_status='EXECUTED' if boundary else 'REUSED' if attempt.get('reused_evaluation') else 'NOT_REACHED')


def run(base, output, *, sender=None, authorization=None, resume=False, env_factory=StrictTrainEnv, fault=None):
    real = sender is None
    output = Path(output).resolve()
    if real:
        if not isinstance(authorization,dict) or authorization.get('paid_api_authorized') is not True:
            raise PermissionError('explicit matching real Pilot authorization required')
        if env_factory is not StrictTrainEnv:
            raise PermissionError('real Pilot requires the frozen TextWorld environment')
        values = frozen_real_inputs(base, output)
        if canonical(authorization)!=canonical(authorization_for(values[0])):
            raise PermissionError('authorization does not match the frozen run, protocol, model or amount')
        if not configured_api_key():
            raise PermissionError('DEEPSEEK_API_KEY unavailable')
        check_local_runtime(values[0])
    else:
        if not callable(sender) or authorization is not None or resume:
            raise PermissionError('Mock and real entrypoints have separate authorization')
        values = configuration(base, output, env_factory=env_factory)
        output.mkdir(mode=0o700, parents=True, exist_ok=True)
    plan, source, events, host, schedule, boundaries, backend = values
    network_policy = plan.get('network_policy')
    if output.stat().st_mode & 0o077:
        raise PermissionError('output directory must be private (0700)')
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        started = (output/'budget.jsonl').exists()
        if real and started!=resume:
            raise PermissionError('use resume for an existing ledger, run for a fresh Pilot')
        if real and not started and any(p.name not in ('protocol.json','authorization.template.json',
                                                       'authorization.json','preflight.json','run.lock','console.log')
                                         for p in output.iterdir()):
            raise PermissionError('unrecognized data in unstarted Pilot directory')
        if not (output/'protocol.json').exists() and any(p.name!='run.lock' for p in output.iterdir()):
            raise PermissionError('unrecognized output directory')
        commit(output/'protocol.json', plan)
        budget = PREVIOUS.create_accounts(output, plan)
        provider = SimpleNamespace(events=EvidenceStore(output/'provider.jsonl'))
        registry = FailureOperatorRegistry(output/'registry.jsonl', FailureEvidenceStore(output/'failures.jsonl'))
        runner = EnvironmentPolicyRunner(backend, output/'worker.jsonl', budget)
        receipts = EnvironmentReceipts(output/'environment.jsonl', plan['environment_steps'])
        check_run(budget, provider, runner, network_policy)
        imported = import_source_events('B', events, host, output, registry.evidence, plan['run_id'])
        known = {row['event_id']:row for row in registry.evidence.visible(time(), plan['run_id'])}
        candidates = [acquire_group(plan, output, index, group, selected, packet, host, source['data_root'],
            budget, registry, runner, receipts, imported, known, sender, provider, env_factory, fault, authorization)
            for index,(group,selected,packet) in enumerate(schedule)]
        check_run(budget, provider, runner, network_policy)
        evaluate_boundaries(output, candidates, boundaries, runner, registry)
        check_run(budget, provider, runner, network_policy)
        verify_history(plan['historical_sha256'])
        attempts = [attempt for candidate in candidates for attempt in candidate['attempts']]
        worker_rows = [row['payload'] for row in runner.events.records() if row['kind']=='ENVIRONMENT_POLICY_EXECUTED']
        for group in candidates:
            for attempt in group['attempts']:
                attempt['resources'] = count_version_resources(attempt, worker_rows, receipts)
                attempt['metrics'] = version_metrics(attempt, group, boundaries)
        usage = {key:sum(attempt['usage'][key] for attempt in attempts)
                 for key in ('input_tokens','output_tokens','total_tokens')}
        resources = dict(environment=dict(receipts.started), worker_calls=len(worker_rows),
            worker_cached_source_calls=receipts.cache_hits,
            worker_seconds=sum(row['seconds'] for row in worker_rows),
            duplicate_evaluations=sum(bool(attempt.get('reused_evaluation')) for attempt in attempts))
        result = dict(scope=plan['scope'], protocol_sha256=fingerprint(plan), candidates=candidates, resources=resources,
            model_requests=len(attempts), paid_requests=len(attempts) if real else 0, usage=usage, budget=budget.snapshot(),
            peak_no_cache_estimate_usd=estimate_peak(usage['input_tokens'],usage['output_tokens']),
            actual_billed_usd=None, final_version_rule=plan['final_version_rule'],
            independent_gate_games=0, disposition=plan['disposition'])
        return commit(output/'result.json', result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare','preflight','run','resume'))
    parser.add_argument('--base', type=Path, default=Path.home()/'.local/share/flowevo')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--authorization', type=Path)
    args = parser.parse_args()
    if args.command=='prepare':
        plan = prepare(args.base,args.output)
        summary = dict(status='PREPARED_PENDING_AUTHORIZATION',run_id=plan['run_id'],
            protocol_sha256=fingerprint(plan),max_cost_microusd=plan['max_cost_microusd'],model_requests=0)
    elif args.command=='preflight':
        summary = preflight(args.base,args.output)
    else:
        if not args.authorization:
            parser.error('run and resume require --authorization')
        result = run(args.base,args.output,authorization=read(args.authorization),resume=args.command=='resume')
        summary = {key:result[key] for key in ('scope','protocol_sha256','model_requests','paid_requests','usage',
                                               'peak_no_cache_estimate_usd','independent_gate_games','disposition')}
    print(canonical(summary))


if __name__=='__main__':
    main()
