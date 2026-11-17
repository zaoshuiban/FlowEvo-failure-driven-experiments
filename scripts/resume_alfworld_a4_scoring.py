"""Versioned A4 host-scoring repair only; frozen candidates and old entry unchanged."""
import argparse
from pathlib import Path
import run_alfworld_a4_exploratory as E
P=E.B.pilot
local_repair_witness=P.local_repair_witness
PREVIOUS=P.PREVIOUS

def score_source(origin, prefix, decisions, actions, stop):
    anchor = len(prefix)
    before = prefix[-2] if anchor>1 else origin['initial']
    witness = local_repair_witness(before, prefix[-1], origin['steps'][anchor:], actions)
    progress = next((i for i,row in enumerate(decisions,1) if row.get('score_or_win_progress')), None)
    if progress is not None and witness is None:
        witness = dict(kind='ENVIRONMENT_SCORE_OR_WIN', step=progress)
    # The prior v14 protocol also recognizes a historical decisive action
    # becoming admissible after a confirmed effect. Keep that witness host-only.
    try:
        decisive = PREVIOUS._decisive(origin)['action']
    except StopIteration:
        decisive = None  # No historical success witness: do not invent one.
    if witness is None and decisive is not None and decisive not in prefix[-1]['commands']:
        witness = next((dict(kind='DECISIVE_ACTION_NEWLY_ADMISSIBLE', step=i, action=decisive)
                        for i,row in enumerate(decisions,1) if row.get('effect')=='TRUE'
                        and decisive in row['receipt']['commands']), None)
    won = bool(actions and actions[-1]['won'])
    if won:
        outcome = 'EPISODE_WON'
    elif witness is not None:
        outcome = 'LOCAL_REPAIR_VERIFIED'
    elif stop=='CANDIDATE_ERROR':
        outcome = 'CANDIDATE_ERROR'
    elif stop=='DECLINED' and not actions:
        outcome = 'DECLINED'
    elif actions and any(r['effect']!='FALSE' for r in decisions if r['receipt'] is not None):
        outcome = 'PROGRESS_UNVERIFIED'
    else:
        outcome = 'REPAIR_FAILED'
    return dict(stop=stop, outcome=outcome, action_returned=any(row['selected_action'] is not None for row in decisions),
        first_action_executed=bool(actions), first_action_verified=bool(actions and decisions[0]['effect']=='TRUE'),
        first_action_observable_effect=bool(actions and (decisions[0]['public_state_changed'] or decisions[0]['effect']=='TRUE')),
        local_repair_verified=witness is not None, local_witness=witness, recovery_completed=progress is not None,
        won=won, actions=actions, decisions=decisions)


def resume(out):
    amendment=E.B.read(out/'scoring_amendment.json')
    if E.B.sha(__file__)!=amendment['adapter_sha256'] or E.B.sha(out/'protocol.json')!=amendment['old_protocol_file_sha256']:
        raise PermissionError('scoring amendment drift')
    E.verify(out)
    P.score_source=score_source
    result=E.run(out)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(E.B.canonical({'status':resume(a.output.resolve())['status']}))
