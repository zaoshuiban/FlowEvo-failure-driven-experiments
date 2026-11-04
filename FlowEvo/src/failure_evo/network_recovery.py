"""Read-only inventory for the unified run/resume entry. Never reclassifies old UNKNOWN."""
from pathlib import Path
from .persistent_budget import PersistentBudget

def inspect_run(path,policy=None,*,isolations=()):
    isolated={(q['ledger'],q['request_id'],q['state_sha256']) for q in isolations}
    requests=[]
    for p in sorted(Path(path).rglob('*budget.jsonl')):
        b=PersistentBudget.__new__(PersistentBudget);b.path=p
        with b._locked() as rows:
            states,_=b._state(rows)
            for key,r in states.items():
                if r['status']=='settled':continue
                safe=b.safe_pre_send(r,policy)
                n=r.get('connection_attempts',0)
                remaining=max(0,policy['max_connect_attempts']-n) if safe else 0
                allowed=remaining>0 and r.get('not_sent',{}).get('retry_allowed',True) if safe else False
                state=('NOT_SENT_RETRYABLE' if allowed else 'NOT_SENT_EXHAUSTED_OR_BLOCKED') if safe else ('UNKNOWN' if r['status']=='unknown' or r.get('network_send_started') else 'UNPROVEN_PENDING')
                from .contracts import fingerprint
                if r['status']=='unknown' and (str(p.relative_to(path)),key,fingerprint(r)) in isolated:state='ISOLATED_UNKNOWN'
                requests.append(dict(ledger=str(p.relative_to(path)),request_id=key,state=state,
                    connection_attempts=n,remaining_connection_attempts=remaining,
                    reserved_upper_microusd=0 if r['status']=='not_sent' else r['cost_upper_microusd'],
                    no_model_resend=not allowed))
    blockers=[r for r in requests if r['state'] not in ('NOT_SENT_RETRYABLE','ISOLATED_UNKNOWN')]
    return dict(status='BLOCKED' if blockers else 'SAFE_TO_RESUME' if requests else 'NO_UNRESOLVED_REQUESTS',
        network_policy=policy,requests=requests,blockers=blockers,
        note='Read-only classification; legacy UNKNOWN and reservations are unchanged. No paid request sent.')
