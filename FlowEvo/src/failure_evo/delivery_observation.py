"""Host-only delivery observations; provider facts never encode local rejection.

This layer grants no registration, execution or mathematical validation rights.
Downstream validation remains bound to its own source hash and ledger.
"""
from dataclasses import dataclass, asdict, replace

@dataclass(frozen=True)
class DeliveryObservation:
    provider_finish_reason: object
    provider_status: object
    transport_status: str = 'RESPONSE_RECEIVED'
    contract_status: str = 'NOT_CHECKED'
    contract_error: object = None
    program_status: str = 'NOT_CHECKED'
    mathematics_status: str = 'NOT_EVALUATED'
    candidate_status: str = 'NOT_REGISTERED'
    observation_schema: str = 'delivery-observation-v1'

    @classmethod
    def received(cls, raw):
        choices = raw.get('choices', [])
        reason = choices[0].get('finish_reason') if len(choices) == 1 else None
        return cls(reason, raw.get('status'))

    def decide_contract(self, accepted, error=None):
        if self.contract_status != 'NOT_CHECKED':
            raise ValueError('contract observation already finalized')
        if accepted and error:
            raise ValueError('accepted contract cannot contain rejection')
        return replace(self, contract_status='ACCEPTED' if accepted else 'REJECTED',
                       contract_error=error)

    def fields(self):
        return asdict(self)


def source_contract_error(value, required):
    if not isinstance(value, dict):
        return 'WRONG_TYPE: $ must be object'
    missing = sorted(set(required) - set(value))
    extra = sorted(set(value) - set(required))
    invalid = sorted(k for k in set(value) & set(required)
                     if not isinstance(value[k], str) or not value[k].strip())
    return ('MISSING_REQUIRED_FIELDS: ' + ','.join(missing) if missing else
            'UNKNOWN_FIELDS: ' + ','.join(extra) if extra else
            'INVALID_FIELD_VALUES: ' + ','.join(invalid) if invalid else None)
