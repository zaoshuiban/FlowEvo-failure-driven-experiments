"""Audits only: request difference never implies reliability or causal benefit."""
from .contracts import fingerprint
from .workflow_protocol_v2 import prepare, PreflightRejected

def request_view(messages, **kwargs):
    try:
        p=prepare(messages,**kwargs)
        return dict(status='SENDABLE',wire_sha256=p.sha256,messages_sha256=fingerprint(messages),input_upper=p.input_upper)
    except PreflightRejected as exc:
        return dict(status='NOT_SENT',reason=exc.reason,details=exc.details,messages_sha256=fingerprint(messages))

def compare(learned,generic):
    available=learned.get('status')=='SENDABLE' and generic.get('status')=='SENDABLE'
    return dict(learned=learned,generic=generic,
        messages_equal=learned.get('messages_sha256')==generic.get('messages_sha256') if available else None,
        final_wire_equal=learned['wire_sha256']==generic['wire_sha256'] if available else None,
        interpretation='Protocol comparison only; counterfactual is not a paired model result')
