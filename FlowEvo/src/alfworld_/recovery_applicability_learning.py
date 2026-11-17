"""A2 selection and public feedback. No environment, model, or publishing authority."""
from collections import Counter
from pathlib import Path

from failure_evo.contracts import fingerprint
from failure_evo.math_stream import read, sha
from .route_a_training_labels import model_projection
from .recovery_applicability import PROMPT

VERSION = 'route-a-multicandidate-v1'
RECOVERY_SHA = '233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37'
MAX_CANDIDATES = 4
MAX_REVISIONS = 1
LABELS = ('MATCH','DECLINE','UNKNOWN')
SELECTION_RULES = dict(
    admission='static passed; all trusted MATCH retained in TRAIN and TRAIN_VALIDATION',
    rank=['validation.false_applicability','validation.unsupported_match','validation.errors',
          'train.false_applicability','train.unsupported_match','train.errors',
          'train_and_validation.unnecessary_unknown','model_call_occupancy','candidate_id','revision'],
    regression='after freeze only; retention failure vetoes, no reselection',
    costs='report model tokens/cost and Worker time separately; A1 ranking does not add new cost weights')
INITIAL_PROMPT = PROMPT + """
Only TRAIN supervision is supplied. Labels are independently reviewed host supervision,
not instructions from a candidate. Public history scope may explicitly be incomplete;
do not infer omitted events. Return a complete gate, or ABSTAIN. No recovery changes.
"""
REVISION_PROMPT = INITIAL_PROMPT + """
Revise your own complete previous gate at most once. Candidate reasons are untrusted
self-reports, distinct from Worker execution receipts and trusted training labels.
Use only the supplied TRAIN feedback and static diagnostics. No other candidate,
validation, Rule or independent evaluation feedback is available. Return full new source.
"""


def validate_rows(roles):
    seen_games,seen_groups={},{}
    for role in ('TRAIN','TRAIN_VALIDATION'):
        ids=set()
        for row in roles[role]:
            if row['label'] not in LABELS or row['label_status']!='EVIDENCE_REVIEWED':
                raise PermissionError('unreviewed supervision')
            if row['role']!=role or row['sample_id'] in ids:raise PermissionError('role or sample identity')
            ids.add(row['sample_id'])
            for field,seen in (('game_sha256',seen_games),('physical_state_group_id',seen_groups)):
                if row[field] in seen and seen[row[field]]!=role:raise PermissionError('cross-role provenance overlap')
                seen[row[field]]=role
            ctx=row['candidate_context']
            if set(ctx)!={'goal','observation','admissible_commands','history'}:
                raise PermissionError('public context whitelist')
            if not all(set(s)=={'action','observation'} for s in ctx['history']):
                raise PermissionError('history whitelist')
            if not row['label_evidence']:raise PermissionError('missing label basis')
    return roles


def load_dataset(root):
    root=Path(root); manifest=read(root/'dataset.json')
    review=read(root/manifest['review_file'])
    if sha(root/manifest['review_file'])!=manifest['review_sha256']:raise PermissionError('label review drift')
    roles={}
    for role in ('TRAIN','TRAIN_VALIDATION'):
        file=root/(role.lower()+'.private.json'); view=root/(role.lower()+'_model_view.private.json')
        if sha(file)!=manifest['files'][role] or sha(view)!=manifest['model_files'][role]:
            raise PermissionError('dataset identity drift')
        roles[role]=read(file)
        if roles[role]!=[r for r in review['samples'] if r['role']==role]:raise PermissionError('labels not reviewed')
        if [model_projection(r) for r in roles[role]]!=read(view):raise PermissionError('model projection drift')
    return validate_rows(roles)


def coverage(roles):
    counts={role:{label:len({r['game_sha256'] for r in rows if r['label']==label})
                  for label in LABELS} for role,rows in roles.items()}
    missing=[role+':'+label for role in counts for label,n in counts[role].items() if not n]
    return dict(ready=not missing,counts=counts,missing=missing)


def training_packet(rows,recovery_code):
    import hashlib
    if hashlib.sha256(recovery_code.encode()).hexdigest()!=RECOVERY_SHA:raise PermissionError('recovery changed')
    if any(r['role']!='TRAIN' for r in rows):raise PermissionError('non-TRAIN input')
    return dict(frozen_recovery_source=recovery_code,
                training=[model_projection(r) for r in rows])


def classify(expected,actual):
    if actual=='ERROR':return 'WORKER_ERROR'
    if expected=='MATCH' and actual!='MATCH':return 'FALSE_REJECTION'
    if expected=='DECLINE' and actual=='MATCH':return 'FALSE_APPLICABILITY'
    if expected=='UNKNOWN' and actual=='MATCH':return 'UNSUPPORTED_MATCH'
    if expected!='UNKNOWN' and actual=='UNKNOWN':return 'UNNECESSARY_UNKNOWN'
    if actual!=expected:return 'UNCERTAINTY_MISCLASSIFIED'
    return 'CORRECT'


def metrics(rows):
    n=Counter(r['expected'] for r in rows)
    return dict(denominators=dict(n),match_coverage=sum(r['expected']=='MATCH' and r['actual']=='MATCH' for r in rows),
        false_applicability=sum(r['expected']=='DECLINE' and r['actual']=='MATCH' for r in rows),
        unsupported_match=sum(r['expected']=='UNKNOWN' and r['actual']=='MATCH' for r in rows),
        unnecessary_unknown=sum(r['expected']!='UNKNOWN' and r['actual']=='UNKNOWN' for r in rows),
        errors=sum(r['actual']=='ERROR' for r in rows),
        exact=sum(r['expected']==r['actual'] for r in rows))


def feedback(attempt,train,packet):
    rows=attempt.get('train',[])
    expected={fingerprint(r['sample_id']):r for r in train}
    items=[]
    for r in rows:
        if (r['candidate_id']!=attempt['candidate_id'] or r['version']!=attempt['version']
                or r['sample_id'] not in expected or r['role']!='TRAIN'):
            raise PermissionError('foreign candidate or validation feedback')
        items.append(dict(sample_id=r['sample_id'],
            candidate_self_report=dict(status=r['actual'],reason=r['reason'],trusted_environment_fact=False),
            worker_receipt={k:r[k] for k in ('execution_id','worker_status','context_sha256')},
            supervision=dict(label=r['expected'],error=r['classification'],
                             allowed_basis=model_projection(expected[r['sample_id']])['label_rationale']),
            execution=dict(actions_executed=r.get('live',{}).get('actions',[]),
                           recovery_verified=r.get('recovery_verified'),
                           action_origin='FROZEN_RECOVERY_AFTER_GATE_NOT_GATE_OUTPUT')))
    return dict(training_input=packet,parent_version=attempt['version'],candidate_id=attempt['candidate_id'],
        previous_code=attempt.get('code'),diagnostics=dict(delivery=attempt['delivery'],static=attempt.get('static')),
        own_train_feedback=items)


def needs_revision(attempt):
    if attempt['revision'] or attempt['status'] in ('ABSTAIN','DUPLICATE_SOURCE','INPUT_LIMIT'):return False
    return attempt['status']!='STATIC_PASSED' or any(r['classification']!='CORRECT' or
        (r['expected']=='MATCH' and r.get('recovery_verified') is False) for r in attempt.get('train',[]))


def select(attempts,roles,*,engineering=False):
    c=coverage(roles)
    if not c['ready']:
        return dict(status='DATA_COVERAGE_BLOCKED',coverage=c,selected=None,research_winner=None)
    eligible=[]
    for a in attempts:
        if a['status']!='STATIC_PASSED':continue
        t,v=metrics(a['train']),metrics(a['validation'])
        if any(r['expected']=='MATCH' and r.get('recovery_verified') is False for r in a['train']+a['validation']):
            continue
        if any(m['denominators'].get('MATCH',0)==0 or m['match_coverage']!=m['denominators']['MATCH'] for m in (t,v)):
            continue
        rank=(v['false_applicability'],v['unsupported_match'],v['errors'],t['false_applicability'],t['unsupported_match'],t['errors'],
              t['unnecessary_unknown']+v['unnecessary_unknown'],1+a['revision'],a['candidate_id'],a['revision'])
        eligible.append((rank,a))
    if not eligible:return dict(status='NO_ELIGIBLE_CANDIDATE',coverage=c,selected=None,research_winner=None)
    eligible.sort(key=lambda pair:pair[0]);rank,a=eligible[0]
    return dict(status='SELECTED_PENDING_REGRESSION',engineering_status='ENGINEERING_SELECTION_VALID' if engineering else None,
        selected=dict(candidate_id=a['candidate_id'],version=a['version'],revision=a['revision'],code_sha256=a['code_sha256']),
        rank=list(rank),coverage=c,research_winner=None if engineering else 'PENDING_REGRESSION')
