"""A1c host review of controlled training data. Never a runtime policy.

The scope is recovery of a failed FINAL delivery, not whether an arbitrary
opening might help a longer plan. Ambiguous intermediate actions stay unresolved.
"""
import re
from failure_evo.contracts import fingerprint
from .route_a_training_labels import goal_parts, compatible, processed, context
from .precondition_diagnostic import command, receipt_effect

VERSION = 'a1c-public-final-delivery-review-v2'
SCOPE = 'FAILED_FINAL_DELIVERY_ONLY_NOT_ALL_USEFUL_OPENING_ACTIONS'


def review(branch):
    result = dict(label=None, label_status='UNRESOLVED_LABEL', reviewer=VERSION,
                  label_scope=SCOPE, label_evidence=[])
    if (branch.get('collection_mode') != 'CONTROLLED_INTERVENTION'
            or not branch.get('replay_verified') or not branch.get('execution_receipt_sha256')):
        return dict(result, reason='Real execution and independent reset replay required.')
    history, failed, probe = branch['prefix'], branch['failure'], branch['recovery_probe']
    parts, move = goal_parts(branch['original_goal']), command(failed['action'])
    if not parts or not move or move[0] != 'move' or not history:
        return dict(result, reason='Unsupported public goal or failure grammar.')
    subject, target = move[1]; wanted, destination, operation = parts
    if (failed['observation'] != 'Nothing happens.' or failed['done'] or failed['won']
            or any(failed[k] != history[-1][k] for k in ('commands','score','won'))
            or 'open '+target.name not in failed['commands']
            or not re.search(r'\bthe '+re.escape(target.name)+r' is closed\.', history[-1]['observation'], re.I)):
        return dict(result, reason='No unchanged closed/openable failure anchor.')
    inventory = [s['observation'] for s in history if s['action'] == 'inventory']
    if not inventory or inventory[-1] != 'You are carrying: a '+subject.name+'.':
        return dict(result, reason='Held failed subject is not publicly confirmed; no easy negative substitution.')
    if (len(probe) != 2 or probe[0]['action'] != 'open '+target.name
            or probe[1]['action'] != failed['action']
            or receipt_effect(command(probe[0]['action']), probe[0]['observation']) != 'TRUE'):
        return dict(result, reason='Same-instance opening and actual retry not confirmed.')
    evidence = [dict(kind='UNCHANGED_PUBLIC_GOAL', value=branch['original_goal']),
                dict(kind='HELD_SUBJECT_AND_CLOSED_TARGET', sha256=fingerprint(history)),
                dict(kind='REAL_FAILED_PLACEMENT', sha256=fingerprint(failed)),
                dict(kind='EXECUTED_REFERENCE_PROBE', sha256=fingerprint(probe), visibility='HOST_ONLY')]
    result['label_evidence'] = evidence
    if not compatible(wanted, subject):
        return dict(result, reason='Wrong object can be a useful hand-release; unresolved.')
    ready = operation is None or processed(history, operation, subject)
    placement_effect=receipt_effect(move, probe[1]['observation'])
    if compatible(destination, target) and ready and probe[-1]['won'] and placement_effect=='TRUE':
        return dict(result, label='MATCH', label_status='EVIDENCE_REVIEWED',
                    reason='Public goal, held instance and required processing support this final delivery.')
    if destination.category != target.category and ready and not probe[-1]['won']:
        # Public contradiction is to the contracted final target, NOT a claim
        # that every intermediate placement is harmful. Private no-win alone
        # is explicitly insufficient. Require an actual same-origin positive.
        witness = branch.get('positive_witness', {})
        if (witness.get('verified') and witness.get('same_subject') and witness.get('won')
                and placement_effect=='FALSE' and failed['action'] not in probe[0]['commands']
                and not probe[-1]['done'] and probe[-1]['score']==failed['score']):
            return dict(result, label='DECLINE', label_status='EVIDENCE_REVIEWED',
                reason='The held object and disclosed processing match the task, but the failed destination conflicts with its explicitly requested final target. This label concerns final-delivery recovery, not arbitrary preparatory opening.',
                private_review_note='HOST_ONLY: actual opening left retry illegal and ineffective; independently replayed same-subject final-target positive exists.')
        return dict(result, reason='A different destination may allow useful intermediate placement; positive witness and failed retry required, no-win alone insufficient.')
    if not ready:
        return dict(result, reason='Processing absent: opening may be preparation; phase preference is not a proven negative.')
    return dict(result, reason='Category-only goal cannot establish an instance conflict, or final effect unproven.')


def matched_views(branch, label, lengths=(4,8,12)):
    """Equal-length, real chronological subsequences; never fabricate observations.

Retain take/inventory/closed/failure and optionally the processing event. Public
projections disclose retained indices and incompleteness. Model never sees probes.
"""
    history = branch['prefix']+[branch['failure']]
    parts = goal_parts(branch['original_goal']); move = command(branch['failure']['action'])
    if not parts or not move or label['label'] not in ('MATCH','DECLINE'): return []
    subject = move[1][0]; operation = parts[2]
    mandatory = {len(history)-1, len(history)-2}
    for verb in ('inventory','take'):
        hits = [i for i,s in enumerate(history) if s['action']=='inventory'] if verb=='inventory' else [
            i for i,s in enumerate(history) if (q:=command(s['action'])) and q[0]=='take' and q[1][0]==subject
            and receipt_effect(q,s['observation'])=='TRUE']
        if hits: mandatory.add(hits[-1])
    process_ids = {i for i,s in enumerate(history) if (q:=command(s['action'])) and q[0]==operation
                   and q[1][0]==subject and receipt_effect(q,s['observation'])=='TRUE'}
    views=[]
    for length in lengths:
        # One fixed length per branch is enough; choose the largest feasible
        # requested length so UNKNOWN is not systematically a short view.
        if length < len(mandatory|process_ids) or len(history)-len(process_ids)<length: continue
        def indices(include):
            keep=set(mandatory)|(process_ids if include else set())
            for i in reversed(range(len(history))):
                if len(keep)>=length:break
                if include or i not in process_ids:keep.add(i)
            return sorted(keep)
        for include in (True,False) if process_ids and label['label']=='MATCH' else (True,):
            ids=indices(include); visible=[history[i] for i in ids]
            expected=label['label'] if include else 'UNKNOWN'
            views.append(dict(label=expected, label_status='EVIDENCE_REVIEWED',reviewer=VERSION,label_scope=SCOPE,
                reason=label['reason'] if include else 'Required same-instance processing is not disclosed in this incomplete public view; legal open/place actions do not establish processing.',
                label_evidence=[dict(kind='PUBLIC_SUBSEQUENCE_REVIEW', retained_indices=[i+1 for i in ids],
                                     context_sha256=fingerprint(context(branch['original_goal'],visible)))],
                candidate_context=context(branch['original_goal'],visible),
                public_history_scope=dict(complete=False, first_step=ids[0]+1,last_step=ids[-1]+1,
                    omitted_steps=len(history)-len(ids),retained_step_ids=[i+1 for i in ids],
                    rule='FIXED_LENGTH_CHRONOLOGICAL_SUBSEQUENCE')))
    # At most one equal-length pair (or negative view), no proliferation of windows.
    return [v for v in views if len(v['candidate_context']['history'])==max(
        (len(x['candidate_context']['history']) for x in views),default=0)]
