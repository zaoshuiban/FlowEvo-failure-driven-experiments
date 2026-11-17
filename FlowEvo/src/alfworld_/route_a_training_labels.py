"""Host-only A1b evidence review; not a runtime gate or generated skill.

Labels describe a final-delivery recovery opportunity. They do not prohibit all
other useful household actions. No candidate policy, Rule, or model is queried.
"""
import re

from failure_evo.contracts import fingerprint
from .precondition_diagnostic import command, entity, receipt_effect, GOAL


VERSION = 'a1b-public-label-review-v1'


def goal_parts(goal):
    m = GOAL.fullmatch(goal.lower())
    if not m:
        return None
    modifier, obj, dest, operation, other_obj, other_dest = m.groups()
    obj = entity(obj or other_obj)
    dest = entity(dest or other_dest)
    if obj is None or dest is None or obj.category.split()[0] in ('one','two','three'):
        return None
    return obj, dest, operation or {'hot':'heat','clean':'clean','cool':'cool'}.get(modifier)


def compatible(required, actual):
    return required.category == actual.category and (required.number is None or required.number == actual.number)


def processed(history, operation, subject):
    return any((p := command(s['action'])) and p[0] == operation and p[1][0] == subject
               and receipt_effect(p, s['observation']) == 'TRUE' for s in history)


def context(goal, history):
    last = history[-1]
    return dict(goal=goal, observation=last['observation'],
                admissible_commands=list(last['commands']),
                history=[dict(action=s['action'],observation=s['observation']) for s in history])


def review(branch):
    """Review a replay-certified branch using receipts, never its proposal label."""
    result = dict(label=None, label_status='UNRESOLVED_LABEL', reviewer=VERSION, label_evidence=[])
    if branch.get('collection_mode') != 'CONTROLLED_INTERVENTION':
        return dict(result, reason='unsupported provenance; synthetic goals are not natural evidence')
    if not branch.get('replay_verified') or not branch.get('execution_receipt_sha256'):
        return dict(result, reason='real execution and exact independent replay required')
    prefix, failure, probe = branch['prefix'], branch['failure'], branch['recovery_probe']
    if not prefix or failure['observation'] != 'Nothing happens.' or failure['won'] or failure['done']:
        return dict(result, reason='not a nonterminal failed action')
    before = prefix[-1]
    if any(failure[k] != before[k] for k in ('commands','score','won')):
        return dict(result, reason='failure changed public state')
    move = command(failure['action'])
    goal = goal_parts(branch['original_goal'])
    if not move or move[0] != 'move' or not goal:
        return dict(result, reason='unsupported goal or failed command')
    subject, destination = move[1]
    wanted, target, operation = goal
    if not re.search(r'\bthe '+re.escape(destination.name)+r' is closed\.',before['observation'],re.I):
        return dict(result, reason='no instance-bound closed receipt')
    if 'open '+destination.name not in failure['commands']:
        return dict(result, reason='opening not publicly available')
    if len(probe) != 2 or probe[0]['action'] != 'open '+destination.name or probe[1]['action'] != failure['action']:
        return dict(result, reason='missing same-obstacle recovery probe')
    if receipt_effect(command(probe[0]['action']),probe[0]['observation']) != 'TRUE':
        return dict(result, reason='opening not confirmed')
    evidence = [dict(kind='REAL_FAILED_PLACEMENT',sha256=fingerprint(failure)),
                dict(kind='CLOSED_AND_OPENABLE',sha256=fingerprint(before)),
                dict(kind='CONTROLLED_RECOVERY_PROBE',sha256=fingerprint(probe),visibility='HOST_ONLY')]
    if compatible(wanted,subject) and compatible(target,destination):
        phase = operation is None or processed(prefix,operation,subject)
        if phase and probe[1]['won'] and receipt_effect(move,probe[1]['observation']) == 'TRUE':
            return dict(result,label='MATCH',label_status='EVIDENCE_REVIEWED',label_evidence=evidence,
                        reason='Same-instance goal and prerequisites supported; actual final delivery won.')
        # Even a complete prefix is not an instruction to forbid preparation.
        return dict(result,label_evidence=evidence,reason='Processing or final-delivery progress unproven; phase preference is not ground truth.')
    # Strong mechanical negative: public inventory proves another object is held,
    # and actually opening cannot make this failed placement admissible/effective.
    inventories = [s['observation'] for s in prefix if s['action']=='inventory']
    held_other = any(re.fullmatch(r'You are carrying: a ([a-z]+ [1-9][0-9]*)\.', text)
                     and re.fullmatch(r'You are carrying: a ([a-z]+ [1-9][0-9]*)\.', text).group(1) != subject.name
                     for text in inventories[-1:])
    if (held_other and failure['action'] not in probe[0]['commands']
            and probe[1]['observation']=='Nothing happens.' and not probe[1]['won']
            and probe[1]['score']==failure['score']):
        return dict(result,label='DECLINE',label_status='EVIDENCE_REVIEWED',label_evidence=evidence,
                    reason='Public inventory excludes failed subject; opening and retry did not enable or repair that placement.')
    return dict(result,label_evidence=evidence,reason='Different task argument may be a legitimate intermediate operation; no definite non-applicability label.')


def window_sample(branch, full_label):
    """A declared partial-history view, not a synthetic task or an unseen game."""
    goal = goal_parts(branch['original_goal'])
    failed = command(branch['failure']['action'])
    if not goal or not failed:
        return None
    # Two observed transitions retained for all arms; no fabricated observations.
    history = (branch['prefix']+[branch['failure']])[-2:]
    ctx = context(branch['original_goal'],history)
    refs = dict(first_step=len(branch['prefix']),last_step=len(branch['prefix'])+1,
                complete=False,rule='LAST_TWO_PUBLIC_TRANSITIONS',omitted_steps=len(branch['prefix'])-1)
    if (full_label['label']=='MATCH' and goal[2]
            and not processed(history,goal[2],failed[1][0])):
        return dict(candidate_context=ctx,public_history_scope=refs,label='UNKNOWN',
                    label_status='EVIDENCE_REVIEWED',reviewer=VERSION,
                    reason='Required same-instance processing is outside the disclosed window; legal placement/open commands do not prove processing.',
                    label_evidence=[dict(kind='PUBLIC_WINDOW_MISSING_REQUIRED_RECEIPT',
                                         scope=refs,context_sha256=fingerprint(ctx))])
    held_publicly = any((q := command(c)) and q[0]=='move' and q[1][0]==failed[1][0]
                        for c in history[-1]['commands'])
    if full_label['label']=='MATCH' and goal[2] is None and held_publicly:
        return dict(candidate_context=ctx,public_history_scope=refs,label='MATCH',
                    label_status='EVIDENCE_REVIEWED',reviewer=VERSION,reason=full_label['reason'],
                    label_evidence=full_label['label_evidence'])
    # Cropping can erase the evidence that supported DECLINE. Do not inherit it.
    return None


def model_projection(sample):
    """The factual context and label rationale, without probes, IDs or provenance."""
    if sample['label_status']!='EVIDENCE_REVIEWED':
        raise PermissionError('unreviewed training supervision')
    # Collection mode/branch names must not become label shortcuts.
    return dict(sample_id=fingerprint(sample['sample_id']),public_context=sample['candidate_context'],
                public_history_scope=sample['public_history_scope'],label=sample['label'],
                label_rationale=sample['reason'])
