"""Retrospective source-only acquisition from a locked full-library run."""
import ast
import json
import re
import time
from pathlib import Path

from alfworld_.failure_learning import SOURCE_CONTRACT, context_view, register_environment_candidate, static_check
from alfworld_.success_baseline import StrictTrainEnv
from failure_evo.autonomous_generation import DeepSeekCompilerAdapter
from failure_evo.contracts import PublicFeedback, canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_skill_transfer import replay_train_generation
from failure_evo.math_stream import read, save, sha

VERSION = 'alfworld-source-acquisition-v1'
MODEL = 'deepseek-flash'
INPUT_LIMIT = 65536
MAX_CHECKPOINTS = 3
MAX_POLICY_STEPS = 4
SCHEMA = dict(decision='PROPOSE or NO_MECHANISM', phenomenon='observed symptom',
              cause='hypothesized cause', uncertainty='limitations and alternatives',
              trigger='runtime trigger', required_state='public preconditions',
              action_policy='algorithm for choosing legal actions', decline='rejection conditions',
              expected_change='observable effect', scope='limits',
              checkpoints=[dict(evidence_id='id', step='1-based step', quote='literal fragment of feedback at step')])


def load_source(root):
    """Read original commits and environment receipts. No diagnostic exports are read."""
    root = Path(root)
    protocol = read(root/'protocol.json')
    summary = read(root/'summary.json')
    journal = EvidenceStore(root/'episodes.jsonl').records()
    if (summary['protocol_sha256'] != fingerprint(protocol) or summary['status'] != 'COMPLETED'
            or len(journal) != 120 or len(protocol['tasks']) != 120):
        raise PermissionError('wrong or incomplete frozen source')
    arms = {'A': [], 'B': []}
    host = {}
    for sequence, (row, record) in enumerate(zip(protocol['tasks'], journal), 1):
        entry = record['payload']
        if (record['kind'] != 'EPISODE_COMMITTED' or entry['task_id'] != row['task_id']
                or entry['seq'] != sequence):
            raise PermissionError('source order drift')
        outcome = entry['outcome']
        if outcome['status'] not in {'SUCCESS', 'STEP_LIMIT', 'ACTION_CYCLE', 'NO_PROGRESS'}:
            raise PermissionError('unsupported source status')
        won = outcome['status'] == 'SUCCESS'
        if won and not outcome['use']['fallback']:
            continue
        env = EvidenceStore(root/'episodes'/row['task_id']/'environment.jsonl').records()
        trace = outcome['trace']
        steps = [receipt['payload'] for receipt in env[1:]]
        if (env[0]['kind'] != 'RESET' or any(r['kind'] != 'STEP' for r in env[1:])
                or len(steps) != trace['total_steps'] or not 1 <= len(steps) <= 50
                or len(trace['actions']) != len(steps)
                or steps[-1]['won'] is not won or trace['success'] is not won):
            raise PermissionError('incomplete public trajectory')
        direct = outcome['use']['L1_actions']
        anchor = direct if won else None
        if won and (not 0 < anchor < len(steps)
                    or steps[anchor-1]['observation'] != 'Nothing happens.'
                    or steps[anchor-1]['won']):
            raise PermissionError('unsupported local failure anchor')
        eid = fingerprint([VERSION, record['record_hash'], env[-1]['record_hash'], anchor])
        projected = dict(evidence_id=eid, event_type='LOCAL_FAILURE_RECOVERY' if won else 'EPISODE_FAILURE',
                         goal=trace['goal'], initial_observation=env[0]['payload']['observation'],
                         won=won, anchor=anchor,
                         steps=[[s['action'], s['observation'], s['action'] in before['payload']['commands']]
                                for before, s in zip(env, steps)])
        arms['B' if won else 'A'].append(projected)
        host[eid] = dict(sequence=sequence, row=row, initial=env[0]['payload'], steps=steps,
                         source_sha256=record['record_hash'], receipt_sha256=env[-1]['record_hash'],
                         at=record['at'], projected=projected)
        if any(any(s[k] != t[k] for k in ('action', 'observation', 'score', 'done'))
               for s, t in zip(steps, trace['actions'])):
            raise PermissionError('trace disagrees with environment')
    if tuple(map(len, arms.values())) != (7, 16) or sum(len(h['steps']) for h in host.values()) != 673:
        raise PermissionError('source cohort changed')
    return protocol, arms, host


def parse_proposal(value):
    if not isinstance(value, dict) or value.get('decision') not in ('PROPOSE', 'NO_MECHANISM'):
        raise ValueError('invalid decision')
    if value['decision'] == 'NO_MECHANISM':
        if set(value) != {'decision', 'uncertainty'} or not isinstance(value['uncertainty'], str) or not value['uncertainty'].strip():
            raise ValueError('invalid abstention')
        return value
    if set(value) != set(SCHEMA) or not all(isinstance(value[k], str) and 0 < len(value[k].strip()) <= 1500
                                          for k in SCHEMA if k != 'checkpoints'):
        raise ValueError('invalid proposal fields')
    refs = value['checkpoints']
    if not isinstance(refs, list) or not 1 <= len(refs) <= MAX_CHECKPOINTS:
        raise ValueError('invalid checkpoint count')
    for ref in refs:
        if (not isinstance(ref, dict) or set(ref) != {'evidence_id', 'step', 'quote'}
                or not isinstance(ref['evidence_id'], str) or type(ref['step']) is not int or ref['step'] < 1
                or not isinstance(ref['quote'], str) or not 0 < len(ref['quote'].strip()) <= 300):
            raise ValueError('invalid evidence reference')
    if len({r['evidence_id'] for r in refs}) != len(refs):
        raise ValueError('one checkpoint per source episode')
    return value


def check_references(proposal, events):
    by_id = {e['evidence_id']: e for e in events}
    for ref in proposal.get('checkpoints', []):
        event = by_id.get(ref['evidence_id'])
        step = ref['step']
        if (not event or step > len(event['steps']) or (event['anchor'] is not None and step != event['anchor'])
                or ref['quote'] not in event['steps'][step-1][1]):
            raise ValueError('checkpoint is not grounded in this arm')


class AcquisitionAdapter(DeepSeekCompilerAdapter):
    protocol = VERSION
    hypothesis_parser = staticmethod(parse_proposal)

    def __init__(self, *args, evidence_sha256, **kwargs):
        super().__init__(*args, **kwargs)
        self.evidence_sha256 = dict(evidence_sha256)

    def preflight(self, request):
        self._authorize()
        payload = request['discovery']
        if (set(payload) != {'arm', 'events'} or payload['arm'] not in ('A', 'B')
                or len(payload['events']) != (7 if payload['arm'] == 'A' else 16)
                or fingerprint(payload['events']) != self.evidence_sha256.get(payload['arm'])):
            raise PermissionError('invalid arm evidence')
        recovered = payload['arm'] == 'B'
        for event in payload['events']:
            if (set(event) != {'evidence_id', 'event_type', 'goal', 'initial_observation', 'won', 'anchor', 'steps'}
                    or event['won'] is not recovered
                    or event['event_type'] != ('LOCAL_FAILURE_RECOVERY' if recovered else 'EPISODE_FAILURE')
                    or (type(event['anchor']) is not int if recovered else event['anchor'] is not None)
                    or not all(isinstance(s, list) and len(s) == 3 and isinstance(s[0], str)
                               and isinstance(s[1], str) and type(s[2]) is bool for s in event['steps'])):
                raise PermissionError('nonpublic or mismatched event')
        if request['phase'] == 'induction':
            system = ('Independently analyze these historical public environment receipts. Each step is '
                      '[executed action, resulting observation, whether it was admissible before the step]; '
                      'steps are 1-based. In B, anchor is the observed failed action; later steps are the '
                      'actual historical recovery, not a validated causal explanation. In A choose a failure '
                      'checkpoint. Separate symptoms, hypotheses and actual executable decisions. '
                      'Propose at most one bounded policy with 1–3 evidence checkpoints from distinct games, '
                      'each quoting the feedback at that step. No generic advice. If insufficient evidence '
                      'return only decision=NO_MECHANISM and uncertainty. JSON proposal shape: '+canonical(SCHEMA))
        elif request['phase'] == 'candidate':
            proposal = parse_proposal(json.loads(request['specification']))
            if proposal['decision'] != 'PROPOSE':
                raise PermissionError('abstained hypothesis cannot generate')
            check_references(proposal, payload['events'])
            # Keep source evidence in induction. The generator receives the model's
            # hypothesis and generic interface, no host replay material.
            payload = dict(arm=payload['arm'], hypothesis=proposal)
            system = SOURCE_CONTRACT
        else:
            raise PermissionError('unfrozen phase')
        wire = dict(model=self.model, messages=[dict(role='system', content=system),
                    dict(role='user', content=canonical(payload))], max_tokens=request['max_tokens'],
                    thinking={'type':'disabled'}, reasoning_effort='none', response_format={'type':'json_object'},
                    stream=False, temperature=0)
        if len(canonical(wire).encode()) + 256 > self.max_wire_input_upper:
            raise ValueError('EVIDENCE_REPRESENTATION_LIMIT')
        return wire


def import_source_events(arm, events, host, root, store, stream):
    """Import each locked event exactly once into the existing evidence store."""
    ids = {}
    for event in events:
        eid = event['evidence_id']
        origin = host[eid]
        wrong = 'observed non-effect' if event['won'] else 'won=false'
        fact = store.record(stream_id=stream, task_id=origin['row']['task_id'], family_id=event['event_type'],
            stage='environment', code=repr(event),
            feedback=PublicFeedback('WRONG_ANSWER', 'Public environment failure observation, cause unverified.',
                                    (canonical(dict(expected='progress', actual=wrong)),)),
            observed_at=origin['at'], available_from=origin['at'], finish_reason='stop',
            parent_sha256=origin['receipt_sha256'],
            provenance_group_id='game:'+origin['row']['game_sha256'])
        ids[eid] = fact['event_id']
    save(root/'evidence_binding.json', dict(arm=arm, ids=ids,
         sources={eid:dict(commit=host[eid]['source_sha256'], environment_tail=host[eid]['receipt_sha256']) for eid in ids}))
    return ids


def acquire(arm, events, host, root, compiler, registry, worker_manifest):
    """Idempotent source import plus one induction and at most one candidate."""
    root = Path(root)
    root.mkdir(exist_ok=True)
    stream = compiler.budget.config['run_id']
    store = registry.evidence
    ids = import_source_events(arm, events, host, root, store, stream)
    job = dict(stream_id=stream, family_id=fingerprint([VERSION, arm, events]),
               discovery=dict(arm=arm, events=events))
    induction = replay_train_generation(compiler, job, 'induction')
    if induction.get('parse_status'):
        return dict(status='INDUCTION_DELIVERY_REJECTED', diagnostic=induction.get('contract_diagnostic'))
    proposal = parse_proposal(json.loads(induction['specification']))
    save(root/'hypothesis.json', proposal)
    if proposal['decision'] == 'NO_MECHANISM':
        return dict(status='NO_MECHANISM')
    try:
        check_references(proposal, events)
    except ValueError as exc:
        return dict(status='CHECKPOINT_REJECTED', diagnostic=str(exc))
    generated = replay_train_generation(compiler, dict(job, specification=canonical(proposal)), 'candidate')
    if generated.get('parse_status'):
        return dict(status='SOURCE_DELIVERY_REJECTED', diagnostic=generated.get('contract_diagnostic'))
    code = generated['code']
    if static_check(code)['passed'] and _has_instance_literals(code, [host[eid] for eid in ids]):
        save(root/'instance_check.json', dict(status='INSTANCE_LITERAL_REJECTED',
                                              response_sha256=generated['response_sha256']))
        return dict(status='INSTANCE_LITERAL_REJECTED')
    selected = [ids[r['evidence_id']] for r in proposal['checkpoints']]
    known = {e['event_id']: e for e in store.visible(time.time(), stream)}
    # Every event was available during induction, including unquoted evidence.
    result = register_environment_candidate(root, generated, proposal, list(ids.values()), known,
        worker_manifest, registry, engineering=compiler.provider.mock, protocol=VERSION,
        baseline='alfworld-full-library-online')
    return dict(result, grounded_evidence_ids=selected)


def verify_source_game(data, origin):
    row = origin['row']
    path = (Path(data)/row['game']).resolve()
    if (not path.is_relative_to(Path(data).resolve()/'json_2.1.1'/'train')
            or sha(path) != row['game_sha256']
            or sha(path.parent/'traj_data.json') != row['trajectory_sha256']):
        raise PermissionError('source game or role changed')
    return path


def _reset(env, origin):
    _, observation, commands = env.reset()
    if (observation, list(commands)) != (origin['initial']['observation'], origin['initial']['commands']):
        raise RuntimeError('source reset differs')


def _step(env, action):
    outcome = env.step(action)
    return dict(action=action, observation=outcome.observation, score=outcome.score,
                done=outcome.done, won=outcome.won, commands=list(outcome.admissible_commands))


def _replay(env, steps):
    for step in steps:
        if _step(env, step['action']) != step:
            raise RuntimeError('source transition differs')


def replay_source(data, origin):
    path = verify_source_game(data, origin)
    env = StrictTrainEnv(data, max_steps=50)
    try:
        env.initialize(frozen_game_files=[str(path)])
        _reset(env, origin)
        _replay(env, origin['steps'])
    finally:
        env.close()


def _has_instance_literals(code, origins):
    # Literal screening is conservative. Obfuscated specializations still
    # require independent validation and cannot be ruled out by AST alone.
    commands = {c for origin in origins for step in [origin['initial'], *origin['steps']]
                for c in step['commands']}
    tokens = {m.lower() for command in commands for m in re.findall(r'\b[a-z]+ \d+\b', command, re.I)}
    ids = {str(origin['row'][k]).lower() for origin in origins for k in ('task_id','game_sha256','trial')}
    literals = [node.value.lower() for node in ast.walk(ast.parse(code))
                if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    if not literals:
        return False
    pattern = re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(t) for t in sorted(tokens))+r')(?!\w)') if tokens else None
    return any((pattern and pattern.search(value)) or any(i in value for i in ids) for value in literals)


LOCAL_WINDOW = 4
EXTENDED_WINDOW = 12


def local_repair_witness(before, native, suffix, alternate):
    """Verify a previously unavailable, historically decisive action is enabled."""
    if (native['observation'] != 'Nothing happens.' or native['won']
            or native['score'] != before.get('score', 0) or native['commands'] != before['commands']
            or not alternate):
        return None
    # Require the exact public state preceding a historical win or score increase.
    # Merely visiting a new location, or matching a no-op, cannot qualify.
    for previous, decisive in zip([native, *suffix], suffix):
        action = decisive['action']
        if (action not in before['commands'] and action in previous['commands']
                and (decisive['won'] or decisive['score'] > previous['score'])):
            for i, receipt in enumerate(alternate, 1):
                if all(receipt[k] == previous[k] for k in ('observation','commands','score','done','won')):
                    return dict(kind='DECISIVE_ACTION_ENABLED', action=action, at_alternate_step=i,
                                historic_previous=previous, historic_decisive=decisive)
    if alternate[-1]['won'] and alternate[0]['action'] != native['action']:
        return dict(kind='ENVIRONMENT_WON', at_alternate_step=len(alternate))
    return None


def recovery_outcome(before, native, suffix, alternate, calls):
    witness = local_repair_witness(before, native, suffix, alternate)
    won = bool(alternate and alternate[-1]['won'])
    end = calls[-1]['status']
    if end == 'error':
        status = 'POLICY_ERROR'
    elif won:
        status = 'EPISODE_WON'
    elif witness:
        status = 'LOCAL_REPAIR_VERIFIED'
    elif not alternate:
        status = 'DECLINED'
    elif all(s['observation'] == 'Nothing happens.' for s in alternate):
        status = 'REPAIR_FAILED'
    else:
        status = 'PROGRESS_UNVERIFIED'
    return dict(status=status, local_repair_verified=witness is not None, local_witness=witness,
                episode_won=won, policy_terminal_status=end)


def review_source(data, origin, ref, card, runner, registry, path, *, extended=False):
    """Execute both branches with only a public observation context in the Worker."""
    registry_rows = registry._rows(card)
    if (not card.intact() or not registry_rows or registry_rows[0]['kind'] != 'SHADOW_REGISTERED'
            or canonical(registry_rows[0]['payload']['card']) != canonical(card.to_dict())):
        raise PermissionError('source evaluation needs the exact registered candidate')
    steps = origin['steps']
    index = ref['step']-1
    key_parts = [VERSION, card.to_dict(), origin['receipt_sha256'], ref, runner.backend.manifest()]
    if extended:
        key_parts.extend(['local-and-extended-v2', LOCAL_WINDOW, EXTENDED_WINDOW])
    key = fingerprint(key_parts)
    if path.exists():
        result = read(path)
        if result['validation_id'] != key:
            raise PermissionError('source review version changed')
        return result
    source = verify_source_game(data, origin)
    env = StrictTrainEnv(data, max_steps=50)
    alternate = []
    policy_calls = []
    before = steps[index-1] if index else origin['initial']
    limit = min(EXTENDED_WINDOW if extended else MAX_POLICY_STEPS, 50-index)
    try:
        env.initialize(frozen_game_files=[str(source)])
        _reset(env, origin)
        _replay(env, steps[:index+1])
        native = steps[index]
        _reset(env, origin)
        _replay(env, steps[:index])
        current = before
        state = {}
        for _ in range(limit):
            context = context_view(origin['projected']['goal'], current['observation'], current['commands'],
                                   steps[:index]+alternate, state)
            result = runner.run(card, context)
            policy_calls.append(result)
            if result['status'] != 'applied':
                break
            # A second host check at the physical environment boundary.
            if result['action'] not in current['commands']:
                raise PermissionError('inadmissible policy action')
            current = _step(env, result['action'])
            alternate.append(current)
            state = result['state']
            if current['done'] or current['won']:
                break
    finally:
        env.close()
    won = bool(alternate and alternate[-1]['won'])
    # A public match is corroborated by the recorded successful suffix, but
    # does not establish hidden-state equivalence or an independent win.
    rejoin = next((j+1 for j, historic in enumerate(steps)
                   if origin['projected']['won'] and native['observation']=='Nothing happens.'
                   and j>index and alternate and alternate[-1] == historic), None)
    if any(c['status']=='error' for c in policy_calls):
        status = 'POLICY_ERROR'
    elif not alternate:
        status = 'DECLINED'
    elif alternate[0]['action'] == native['action']:
        status = 'NO_INITIAL_ACTION_CHANGE'
    elif won and not native['won']:
        status = 'ALTERNATIVE_WON'
    elif rejoin is not None:
        status = 'PUBLIC_RECOVERY_MATCH'
    else:
        status = 'UNVERIFIED_PROGRESS'
    result = dict(validation_id=key, candidate_version=card.version, source_sha256=origin['source_sha256'],
                  checkpoint=ref, status=status, native=native, alternative=alternate,
                  policy_calls=policy_calls, alternate_won=won, recovery_match_step=rejoin,
                  native_at_same_action_horizon=steps[index:index+len(alternate)],
                  model_requests_for_validation=0, alternate_action_count=len(alternate))
    if extended:
        result.update(recovery_outcome(before, native, steps[index+1:], alternate, policy_calls))
        result.update(action_limit=limit, short_window=min(LOCAL_WINDOW, limit),
                      native_attempt_was_admissible=native['action'] in before['commands'],
                      short_outcome=recovery_outcome(before, native, steps[index+1:],
                          alternate[:LOCAL_WINDOW], policy_calls[:LOCAL_WINDOW]))
    save(path, result)
    return result
