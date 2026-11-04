"""Fail-closed dispatch checks; audit journals remain append-only."""
from .contracts import fingerprint

class RunUnhealthy(RuntimeError):
    pass

def assert_run_healthy(*, budgets=(), providers=(), faults=(), network_policy=None):
    reasons = list(faults)
    for budget in budgets:
        pending = budget.blocking_requests(network_policy) if network_policy else budget.snapshot()['unknown_or_pending_requests']
        if pending:
            reasons.append('LEDGER_UNKNOWN_OR_PENDING:' + ','.join(pending))
    for provider in providers:
        rows = provider.events.records()
        started, received = set(), set()
        for row in rows:
            p = row['payload']
            if row['kind'] == 'SEND_STARTED':
                started.add(p['key'])
                if fingerprint(p['wire']) != p['wire_sha256']:
                    reasons.append('REQUEST_HASH_MISMATCH')
            elif row['kind'] == 'RAW_RESPONSE':
                received.add(p['key'])
                if fingerprint(p['response']) != p['sha256']:
                    reasons.append('RESPONSE_HASH_MISMATCH')
            elif row['kind'] == 'SEND_UNKNOWN':
                reasons.append('SEND_UNKNOWN:' + p['key'])
        if started - received:
            reasons.append('UNRESOLVED_TRANSPORT')
    if reasons:
        raise RunUnhealthy(';'.join(reasons))
    return {'status': 'HEALTHY'}

def trusted_usage(raw):
    """Provider usage only, before any model-content parsing. No inferred tokens."""
    usage = raw.get('usage', {}) if isinstance(raw, dict) else {}
    i = usage.get('input_tokens', usage.get('prompt_tokens'))
    o = usage.get('output_tokens', usage.get('completion_tokens'))
    t = usage.get('total_tokens')
    valid = all(type(x) is int and x >= 0 for x in (i, o, t)) and i + o == t
    return dict(input_tokens=i, output_tokens=o, total_tokens=t) if valid else {}
