"""Read-only analysis of bounded ScienceWorld artifacts; no simulator/model imports.

Run after the study terminates. An incomplete run requires --allow-incomplete;
its missing cases remain missing rather than being counted as losses.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT/'runs/scienceworld_bounded_learning_20261118_01'
DEFAULT_REPORT = ROOT/'reports/scienceworld_bounded_learning_20261118'
ARMS = ('G', 'R', 'F')
GROUPS = ('NATURAL_REPETITION_TRIGGER', 'CONNECTION_PROGRESS_CONTROL')


def read(path):
    return json.loads(Path(path).read_text())


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def optional(path):
    return read(path) if path.exists() else None


def commit(path, value):
    path = Path(path)
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x') as out:
            out.write(text)
            out.flush()
            os.fsync(out.fileno())
    except FileExistsError:
        if path.read_text() != text:
            raise PermissionError('immutable analysis differs: '+str(path))
    return value


def stage(ident):
    parts = Path(ident).parts
    if parts and parts[0] == 'worker':
        parts = parts[1:]
    if not parts:
        return 'other'
    if parts[0] == 'screening':
        return 'screening'
    if parts[0] == 'learning':
        return 'learning_generation' if len(parts) == 2 else 'learning_development'
    if parts[0] == 'test':
        if 'native' in parts:
            return 'test_native_screening'
        if 'pair' in parts:
            index = parts.index('pair')+1
            if index < len(parts) and parts[index] in ARMS:
                return 'test_'+parts[index]
    return 'other'


def usage(raw):
    value = raw.get('usage', {}) if isinstance(raw, dict) else {}
    values = [value.get('input_tokens', value.get('prompt_tokens')),
              value.get('output_tokens', value.get('completion_tokens')),
              value.get('total_tokens')]
    if not all(type(x) is int and x >= 0 for x in values) or values[0]+values[1] != values[2]:
        return None
    return dict(zip(('input_tokens', 'output_tokens', 'total_tokens'), values))


def ledger(root):
    """Read/verify the existing journal without creating locks or starting clocks."""
    path = root/'budget.jsonl'
    if not path.exists():
        return dict(present=False, unknown_or_pending_requests=[], requests={})
    data = path.read_bytes()
    if data and not data.endswith(b'\n'):
        raise ValueError('partial budget record; no trustworthy final accounting')
    rows, previous = [], '0'*64
    for line in data.splitlines():
        row = json.loads(line)
        material = {k:v for k,v in row.items() if k != 'record_hash'}
        if row['previous_hash'] != previous or digest(material) != row['record_hash']:
            raise ValueError('budget journal integrity failure')
        previous = row['record_hash']
        rows.append(row)
    if not rows or rows[0]['kind'] != 'RUN_OPENED':
        raise ValueError('budget opening record missing')
    requests = {}
    for row in rows:
        kind, value = row['kind'], row['payload']
        ident = value.get('request_id')
        if kind == 'RESERVED':
            requests[ident] = dict(value, status='reserved')
        elif kind == 'SETTLED':
            requests[ident].update(status='settled', settlement=value)
        elif kind == 'UNKNOWN':
            requests[ident]['status'] = 'unknown'
        elif kind == 'NETWORK_SEND_STARTED':
            requests[ident]['network_send_started'] = True
        elif kind == 'CONNECT_ATTEMPT':
            requests[ident]['connection_attempts'] = value['attempt']
        elif kind == 'NOT_SENT':
            requests[ident]['status'] = 'not_sent'
        elif kind == 'NOT_SENT_REOPENED':
            requests[ident]['status'] = 'reserved'
    totals = Counter()
    for request in requests.values():
        if request['status'] == 'not_sent':
            continue
        settled = request.get('settlement', {})
        totals['calls'] += request['kind'] == 'model'
        totals['tool_calls'] += request['kind'] == 'tool'
        totals['charged_or_reserved_tokens'] += settled.get('tokens', request['token_upper'])
        totals['charged_or_reserved_cost_microusd'] += settled.get('cost_microusd', request['cost_upper_microusd'])
        totals['charged_or_reserved_tool_milliseconds'] += settled.get('tool_milliseconds', request['tool_milliseconds_upper'])
    return dict(present=True, journal_sha256=sha(path), record_count=len(rows),
        config=rows[0]['payload']['config'], deadline=rows[0]['payload']['deadline'],
        totals=dict(totals), requests=requests,
        unknown_or_pending_requests=[ident for ident,r in requests.items() if r['status'] not in ('settled', 'not_sent')],
        not_sent_requests=[ident for ident,r in requests.items() if r['status'] == 'not_sent'])


def request_usage(root, account, errors):
    by_stage = defaultdict(Counter)
    models, identities = Counter(), {}
    records, unknown_usage, missing_responses = [], [], []
    for path in sorted((root/'requests').rglob('logical_call.json')):
        logical = read(path)
        ident = logical['request_id']
        directory = path.parent
        label = stage(ident)
        totals = by_stage[label]
        totals['logical_calls'] += 1
        totals['replanning_logical_calls'] += ident.endswith('/plan')
        wire = read(directory/'request.private.json')
        if digest(wire) != logical['wire_sha256']:
            errors.append('logical wire changed: '+ident)
        cached = (directory/'cache.json').exists()
        totals['cache_hits'] += cached
        response = optional(directory/'response.json')
        record = dict(request_id=ident, stage=label, cache=cached,
                      response_present=response is not None,
                      ledger_status=account['requests'].get(ident, {}).get('status'))
        if response is None:
            missing_responses.append(ident)
        else:
            totals['logical_responses'] += 1
            record['finish_reason'] = (response.get('choices') or [{}])[0].get('finish_reason')
            record['provider_model'] = response.get('model')
            if response.get('model'):
                models[response['model']] += 1
            known = usage(response)
            record['provider_usage'] = known
            if known:
                for key, value in known.items():
                    totals['logical_'+key] += value
            if cached:
                cache = read(directory/'cache.json')
                source = root/'requests'/cache['source']
                if (cache['wire_sha256'] != logical['wire_sha256']
                        or digest(read(source/'request.private.json')) != logical['wire_sha256']
                        or read(source/'response.json') != response):
                    errors.append('cache provenance mismatch: '+ident)
            else:
                totals['actual_received_responses'] += 1
                if known:
                    totals['actual_received_responses_with_usage'] += 1
                    totals.update(known)
                else:
                    unknown_usage.append(ident)
                response_id = response.get('id')
                if response_id:
                    if response_id in identities:
                        errors.append('duplicate actual response ID: '+ident+' / '+identities[response_id])
                    identities[response_id] = ident
        records.append(record)
    for ident, request in account['requests'].items():
        totals = by_stage[stage(ident)]
        if request['kind'] == 'model':
            totals['actual_send_started'] += bool(request.get('network_send_started'))
            totals['model_reservations'] += request['status'] != 'not_sent'
            totals['not_sent_requests'] += request['status'] == 'not_sent'
        else:
            totals['worker_calls'] += request['status'] != 'not_sent'
        totals['unknown_or_pending_reservations'] += request['status'] not in ('settled', 'not_sent')
    combined = Counter()
    for totals in by_stage.values():
        combined.update(totals)
    return dict(by_stage={key:dict(value) for key,value in sorted(by_stage.items())},
        totals=dict(combined), provider_models=dict(models), requests=records,
        missing_responses=missing_responses, responses_without_trusted_usage=unknown_usage,
        actual_billed_usd=None,
        deduplication='One persisted logical request_id and one ledger send boundary per request. Re-reading the first learning response after resumption adds neither a logical request nor an actual send.',
        cost_note='Actual token usage counts only uncached received responses. Supplier USD billing is unavailable; ledger money is conservative reserved cost, not a bill.')


def infrastructure_replay(root, protocol, account, errors):
    """Count restoration overhead separately from all agent/skill action metrics."""
    amendment = optional(root/'Runtime_Amendment.json')
    path = root/'replay_attempts.jsonl'
    if amendment:
        if amendment['original_protocol_sha256'] != digest(protocol):
            errors.append('runtime amendment protocol mismatch')
        source = Path(amendment['resume_script'])
        if not source.is_file() or sha(source) != amendment['resume_script_sha256']:
            errors.append('runtime amendment adapter source changed')
    records = []
    if path.exists():
        data = path.read_bytes()
        if data and not data.endswith(b'\n'):
            raise ValueError('partial infrastructure replay record')
        previous = '0'*64
        for line in data.splitlines():
            row = json.loads(line)
            material = {k:v for k,v in row.items() if k != 'record_hash'}
            if row['previous_hash'] != previous or digest(material) != row['record_hash']:
                raise ValueError('infrastructure replay journal integrity failure')
            previous = row['record_hash']
            value = row['payload']
            kind = row['kind']
            if kind not in ('EXACT_REPLAY_ACCEPTED', 'EXACT_REPLAY_REJECTED'):
                errors.append('unknown infrastructure replay event: '+kind)
            if amendment and not 1 <= value['attempt'] <= amendment['max_replay_attempts']:
                errors.append('infrastructure replay attempt exceeds amendment bound')
            if kind == 'EXACT_REPLAY_ACCEPTED' and value['replay_actions'] != value['prefix_steps']:
                errors.append('accepted infrastructure replay lacks full prefix')
            records.append(dict(kind=kind, at=row['at'], **{key:value.get(key) for key in (
                'variation','case_sha256','attempt','prefix_steps','replay_actions','milliseconds','stage','differing_fields')}))
    if records and not amendment:
        errors.append('infrastructure replay journal has no runtime amendment')
    totals = dict(attempts=len(records), accepted=0, rejected=0, replay_actions=0, milliseconds=0)
    by_variation = {}
    for row in records:
        key = str(row['variation'])
        current = by_variation.setdefault(key, dict(attempts=0, accepted=0, rejected=0, replay_actions=0, milliseconds=0))
        current['attempts'] += 1
        for field in ('accepted','rejected','replay_actions','milliseconds'):
            value = (int(row['kind'] == 'EXACT_REPLAY_'+field.upper()) if field in ('accepted','rejected') else row[field])
            totals[field] += value
            current[field] += value
    actual_sends = sum(bool(value.get('network_send_started')) for value in account['requests'].values()
                       if value['kind'] == 'model')
    pre_sends = amendment.get('pre_amendment_model_sends') if amendment else None
    return dict(amendment=amendment, logged_totals=totals, by_variation=by_variation, attempts=records,
        journal_sha256=sha(path) if path.exists() else None,
        pre_amendment_model_sends=pre_sends, total_unique_actual_model_sends=actual_sends,
        post_amendment_unique_actual_model_sends=actual_sends-pre_sends if pre_sends is not None else None,
        accounting='Logged reset/prefix restoration work only; excluded from skill actions, suffix actions, and paired savings. Resuming cached/persisted responses does not add paid requests. Any original pre-amendment restoration attempt without a journal record is not included in these logged totals.',
        limitation=amendment.get('limitation') if amendment else None)


def paired_summary(rows):
    summary = dict(checkpoints=len(rows), variations=[row['variation'] for row in rows], arms={})
    for arm in ARMS:
        values = [row['arms'][arm] for row in rows]
        summary['arms'][arm] = dict(wins=sum(x['won'] for x in values),
            total=len(values), win_rate=sum(x['won'] for x in values)/len(values) if values else None,
            status_counts=dict(Counter(x['status'] for x in values)),
            **{key:sum(x[key] for x in values) for key in (
                'logical_model_calls','cache_hits','suffix_steps','worker_calls','policy_actions','policy_errors')})
    for intervention, reference in (('F','G'), ('F','R'), ('R','G')):
        rescued = [r for r in rows if not r['arms'][reference]['won'] and r['arms'][intervention]['won']]
        harmed = [r for r in rows if r['arms'][reference]['won'] and not r['arms'][intervention]['won']]
        both = [r for r in rows if r['arms'][reference]['won'] and r['arms'][intervention]['won']]
        deltas = [dict(variation=r['variation'],
            logical_model_calls_saved=r['arms'][reference]['logical_model_calls']-r['arms'][intervention]['logical_model_calls'],
            environment_actions_saved=r['arms'][reference]['suffix_steps']-r['arms'][intervention]['suffix_steps']) for r in both]
        calls = sum(r['logical_model_calls_saved'] for r in deltas)
        actions = sum(r['environment_actions_saved'] for r in deltas)
        summary[intervention+'_vs_'+reference] = dict(
            rescued=len(rescued), harmed=len(harmed), net_additional_wins=len(rescued)-len(harmed),
            rescued_variations=[r['variation'] for r in rescued], harmed_variations=[r['variation'] for r in harmed],
            both_success=len(both), logical_model_calls_saved_on_both_success=calls,
            environment_actions_saved_on_both_success=actions,
            mean_logical_model_calls_saved_on_both_success=calls/len(both) if both else None,
            mean_environment_actions_saved_on_both_success=actions/len(both) if both else None,
            both_success_differences=deltas)
    return summary


def analyze(root, report, *, allow_incomplete=False):
    root, report = Path(root).resolve(), Path(report).resolve()
    protocol = read(root/'protocol.json')
    screened = optional(root/'Screening_Result.json')
    frozen = optional(root/'Frozen_Candidate.json')
    independent = optional(root/'Independent_Result.json')
    if independent is not None:
        status = 'COMPLETED_TEST'
    elif frozen and frozen['status'] == 'NO_EXECUTABLE_SKILL':
        status = 'NO_EXECUTABLE_SKILL'
    elif screened and screened['status'] == 'NO_NATURAL_DEVELOPMENT_FAILURE':
        status = 'NO_NATURAL_DEVELOPMENT_FAILURE'
    else:
        status = 'INCOMPLETE'
        if not allow_incomplete:
            raise RuntimeError('no terminal artifact; wait for run completion or explicitly use --allow-incomplete after interruption')
    errors = []
    for name, expected in protocol.get('files', {}).items():
        if not Path(name).is_file() or sha(name) != expected:
            errors.append('frozen dependency changed: '+name)
    if frozen and frozen.get('protocol_sha256') != digest(protocol):
        errors.append('frozen candidate protocol mismatch')
    account = ledger(root)
    if account['present'] and account['config']['protocol_hash'] != digest(protocol):
        errors.append('ledger protocol mismatch')
    requests = request_usage(root, account, errors)
    replay = infrastructure_replay(root, protocol, account, errors)
    versions = []
    for path in sorted((root/'learning').glob('v*/evaluation.json')):
        evaluation = read(path)
        candidate = read(path.parent/'candidate.json')
        code = path.parent/'candidate.py'
        if not code.exists() or sha(code) != evaluation['code_sha256']:
            errors.append('evaluated candidate source changed: '+str(code))
        versions.append(dict(version=evaluation['version'], static_pass=evaluation['static_pass'],
            complete_development_pass=evaluation['complete_development_pass'], rank=evaluation['rank'],
            code_path=str(code), code_sha256=evaluation['code_sha256'],
            model_generated_description=candidate.get('description'), applicability=candidate.get('applicability'),
            delivery_errors=candidate.get('errors', []), ignored_metadata_keys=sorted(candidate.get('ignored_metadata', {})),
            static_errors=read(path.parent/'static.json').get('errors', []), initial_control=evaluation.get('initial_control'),
            development=[{k:r[k] for k in ('won','status','suffix_steps','logical_model_calls','worker_calls','policy_actions','policy_errors')}
                         for r in evaluation['rows']]))
    if frozen and frozen.get('status') == 'FROZEN':
        selected = root/'learning'/('v'+str(frozen['version']))/'candidate.py'
        if not selected.is_file() or sha(selected) != frozen['code_sha256']:
            errors.append('frozen program source changed')
    pair_paths = sorted((root/'test').glob('*/pair/paired_result.json'))
    rows = independent['pairs'] if independent else [read(path) for path in pair_paths]
    if independent and rows != [read(path) for path in pair_paths]:
        errors.append('independent summary and persisted pairs differ')
    for row in rows:
        arms = row['arms']
        if set(arms) != set(ARMS) or len({value['start_sha256'] for value in arms.values()}) != 1:
            errors.append('paired state or arm mismatch: '+str(row['variation']))
        remaining = protocol['action_limit']-row['anchor']
        if any(value['suffix_steps'] > remaining for value in arms.values()):
            errors.append('remaining action budget exceeded: '+str(row['variation']))
        for arm, value in arms.items():
            path = root/'test'/f"{row['variation']:02d}"/'pair'/arm/'result.json'
            if path.exists():
                saved = read(path)
                if any(saved.get(key) != item for key,item in value.items()):
                    errors.append('paired result differs from branch: '+str(path))
    games = independent['games'] if independent else []
    baseline_rows = []
    for path in sorted((root/'test').glob('*/native/result.json')):
        value = read(path)
        baseline_rows.append(dict(variation=int(path.parent.parent.name), won=value['won'], status=value['status'],
            actions=value['suffix_steps'], logical_model_calls=value['logical_model_calls']))
    if independent and sorted(x['variation'] for x in games) != sorted(protocol['test_variations']):
        errors.append('test variation coverage differs from frozen protocol')
    material = optional(root/'learning_input.json')
    has_recovery = material.get('includes_real_recovery_suffixes', False) if material else False
    public_account = {key:value for key,value in account.items() if key != 'requests'}
    public_account['unknown_or_pending_details'] = [dict(request_id=ident,
        kind=account['requests'][ident]['kind'], status=account['requests'][ident]['status'],
        network_send_started=account['requests'][ident].get('network_send_started', False))
        for ident in account['unknown_or_pending_requests']]
    summary = dict(status=status, run_root=str(root), protocol_sha256=digest(protocol),
        analyzer_sha256=sha(__file__), screening=screened, frozen=frozen, versions=versions,
        learning=dict(attempted=requests['by_stage'].get('learning_generation', {}).get('logical_calls', 0),
            completed_evaluations=len(versions), includes_real_recovery_suffixes=has_recovery,
            claim_scope='Learning from failures and actual recovery processes.' if has_recovery else
                        'Learning from real failures and subsequent execution feedback; no pure-failure-versus-success comparison.'),
        test=dict(frozen_variations=protocol['test_variations'], native_baselines=baseline_rows, games=games,
            completed_pairs=len(rows), missing_native_variations=sorted(set(protocol['test_variations'])-{x['variation'] for x in baseline_rows}),
            no_checkpoint_variations=[x['variation'] for x in games if x['anchor'] is None], pairs=rows),
        by_group={group:paired_summary([row for row in rows if row['group'] == group]) for group in GROUPS},
        all_pairs=paired_summary(rows), usage=requests, budget=public_account, infrastructure_replay=replay,
        integrity=dict(passed=not errors, errors=errors,
            unsettled_ledger=bool(account['unknown_or_pending_requests'])),
        interpretation=dict(
            effectiveness_estimate_available=status == 'COMPLETED_TEST' and bool(rows) and not errors,
            natural_recovery_estimate_available=status == 'COMPLETED_TEST' and not errors
                and any(row['group'] == 'NATURAL_REPETITION_TRIGGER' for row in rows),
            no_natural_failure='No qualifying sampled native failure; this does not establish that a learned skill would fail or succeed.',
            no_executable_skill='Bounded learning produced no admitted executable skill; no held-out recovery-effect estimate.',
            controls='Connection-progress controls are not failed-state rescue evidence. Trigger checkpoints are retained even if native later succeeds.',
            calls='Paired savings use logical model calls including cache hits and the R planning call. Actual network requests depend on shared exact-response caching.',
            signs='Positive savings mean fewer calls/actions for the intervention; negative values mean more.',
            replanning='R tests ordinary extra replanning; its computation is not strictly equal to isolated skill execution.',
            missing='Absent or incomplete cases are never counted as losses; each variation contributes at most one checkpoint.'))
    commit(report/'result_summary.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '--run', dest='root', type=Path, default=DEFAULT_RUN)
    parser.add_argument('--report', type=Path, default=DEFAULT_REPORT)
    parser.add_argument('--allow-incomplete', action='store_true')
    args = parser.parse_args()
    result = analyze(args.root, args.report, allow_incomplete=args.allow_incomplete)
    print(json.dumps(dict(status=result['status'], report=str(args.report.resolve()/'result_summary.json'),
        by_group=result['by_group'], usage_totals=result['usage']['totals'],
        integrity=result['integrity'], unknown_or_pending=result['budget']['unknown_or_pending_requests']), ensure_ascii=False))
