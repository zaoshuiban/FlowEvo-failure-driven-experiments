"""Opt-in experiment request bounds, separate from generated-source safety."""
from .contracts import canonical


def validate_wire_input_policy(p,model):
    keys={'version','model','max_wire_input_bytes','max_input_tokens','model_context_tokens','output_tokens','estimator'}
    if not isinstance(p,dict) or set(p)!=keys or p['version']!='route-a3-wire-v1' or p['model']!=model or model!='deepseek-flash':
        raise ValueError('unsupported experiment input policy')
    if any(type(p[k]) is not int or p[k]<1 for k in ('max_wire_input_bytes','max_input_tokens','model_context_tokens','output_tokens')):
        raise ValueError('positive integral bounds required')
    if (p['estimator']!='UTF8_BYTES_PLUS_256_UPPER' or p['max_input_tokens']!=p['max_wire_input_bytes']+256
            or p['max_input_tokens']+p['output_tokens']>p['model_context_tokens']
            or p['model_context_tokens']>1000000 or p['output_tokens']!=4096):
        raise ValueError('input/output context or accounting conflict')


def check_wire(wire,p):
    validate_wire_input_policy(p,wire['model'])
    n=len(canonical(wire).encode())
    if n>p['max_wire_input_bytes'] or n+256>p['max_input_tokens'] or wire['max_tokens']!=p['output_tokens']:
        raise ValueError('EVIDENCE_REPRESENTATION_LIMIT')
    return dict(wire_bytes=n,input_token_upper=n+256,actual_provider_tokens=None,
                accounting=p['estimator'],context_headroom=p['model_context_tokens']-(n+256)-wire['max_tokens'])
