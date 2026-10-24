"""Opt-in compile envelope normalization; never grants runtime authority."""
import hashlib
import json
from .contracts import canonical, fingerprint
from .repair_choice_v2 import validate_rule, STATES, ACTIONS
VERSION = 's19-compile-envelope-v2'
H_FIELDS = ('conditions', 'action', 'expected_improvement', 'refusal_conditions', 'stop_conditions', 'unknowns')


def fields(value, required, path):
    if type(value) is not dict:
        raise ValueError(f'{path}: expected object, got {type(value).__name__}')
    extra, missing = sorted(set(value)-set(required)), sorted(set(required)-set(value))
    if extra or missing:
        raise ValueError(f'{path}: unknown fields={extra}; missing fields={missing}')


def normalize(text, finish_reason='stop'):
    # Reject duplicate keys rather than allowing JSON's last-value-wins behavior.
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError(f'duplicate JSON field: {key}')
            result[key] = value
        return result
    audit = dict(protocol=VERSION, raw_text=text,
                 raw_sha256=hashlib.sha256(text.encode()).hexdigest(), accepted=False, reasons=[])
    try:
        if finish_reason != 'stop': raise ValueError(f'finish_reason: expected stop, got {finish_reason}')
        value = json.loads(text, object_pairs_hook=pairs,
                           parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON: '+x)))
        if type(value) is not dict: raise ValueError('$: expected object')
        normalized = dict(value)
        if 'type' in normalized:
            if type(normalized['type']) is not str or normalized['type'] != 'json_object':
                raise ValueError('$.type: only literal string json_object is allowed')
            del normalized['type']
            audit['reasons'].append('Removed allowlisted top-level type=json_object; no business semantics')
        fields(normalized, ('hypothesis','rule'), '$')
        fields(normalized['hypothesis'], H_FIELDS, '$.hypothesis')
        for key, val in normalized['hypothesis'].items():
            if type(val) is not str or not val.strip():
                raise ValueError(f'$.hypothesis.{key}: expected nonempty string')
        fields(normalized['rule'], ('when','action','fallback'), '$.rule')
        fields(normalized['rule']['when'], ('candidate_state','public_result','remaining_calls_min'), '$.rule.when')
        rule = normalized['rule']; when = rule['when']
        for path, val, allowed in (
            ('$.rule.when.candidate_state', when['candidate_state'], STATES),
            ('$.rule.when.public_result', when['public_result'], ('WRONG_ANSWER','RUNTIME_ERROR','COMPILE_ERROR','NO_COMPLETE_CODE')),
            ('$.rule.action', rule['action'], ACTIONS),
            ('$.rule.fallback', rule['fallback'], ('NATIVE',))):
            if type(val) is not str or val not in allowed:
                raise ValueError(f'{path}: invalid value {val!r}; allowed={allowed}')
        minimum = when['remaining_calls_min']
        if type(minimum) is not int or not 1 <= minimum <= 5:
            raise ValueError('$.rule.when.remaining_calls_min: expected integer 1..5')
        # All original semantic and permission constraints remain authoritative.
        try: validate_rule(normalized['rule'])
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError('$.rule: '+str(exc)) from exc
        audit.update(accepted=True, normalized=normalized, normalized_sha256=fingerprint(normalized),
                     rule_sha256=fingerprint(normalized['rule']))
    except (ValueError, TypeError, KeyError) as exc:
        audit['error'] = str(exc)
    return audit
