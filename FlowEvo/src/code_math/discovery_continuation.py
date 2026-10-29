"""Versioned P1 continuation: no replay of consumed or UNKNOWN tasks."""
from failure_evo.math_discovery_p1p2 import grade_output
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from .no_gold import PublicMathTask

VERSION='math-p1-continuation-v1'

def grade_continuation(text,gold,finish_reason):
    if finish_reason=='length':
        return dict(status='TRUNCATED',correct=None,parsed_answer=None,reason='OUTPUT_TOKEN_LIMIT',scorer_version=VERSION)
    return dict(grade_output(text,gold,finish_reason),scorer_version=VERSION)

def plan_tasks(public_rows,old_controller,old_budget):
    events=EvidenceStore(old_controller).records();ledger=EvidenceStore(old_budget).records()
    started={r['payload']['task_id'] for r in events if r['kind']=='MATH_TASK_STARTED'}
    locked={r['payload']['task_id'] for r in events if r['kind']=='MATH_ANSWER_LOCKED'}
    unknown=[r['payload']['request_id'] for r in ledger if r['kind']=='UNKNOWN']
    allowed={x['task_id'] for x in public_rows}
    if not started<=allowed or not locked<=started:raise ValueError('historical task identity mismatch')
    return dict(version=VERSION,new_tasks=[PublicMathTask.parse(x).to_dict() for x in public_rows if x['task_id'] not in started],
        exposed_locked=[x['task_id'] for x in public_rows if x['task_id'] in locked],
        quarantined_started_unlocked=[x['task_id'] for x in public_rows if x['task_id'] in started-locked],
        unknown_requests=unknown,original_order_preserved=True,repeated_requests=0)
