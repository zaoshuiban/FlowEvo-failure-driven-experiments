"""Read-only A1 evidence audit. No model, environment, or candidate execution.

This is a data readiness check, not an applicability oracle. In particular, an
absent failure at the frozen intervention hook must not become a labelled hard
negative, and an absent processing receipt is not proof of a phase conflict.
"""

import argparse
from collections import Counter
from pathlib import Path
import re

from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, save, sha


ROOT = Path(__file__).resolve().parents[1]
BASE = Path.home()/'.local/share/flowevo'
S1 = ROOT/'runs/alfworld_container_boundary_learning_20261113_02'
S0 = ROOT/'runs/python_recovery_decline_revision_20261112_01'
S0_SHA = '233fef28c08a68a44e8fbbcb5aa5928ae76a162a104f8b4abd8b6157189c7f37'
TRAIN_SHA = 'c42a0fe65623b9a39ee724bbb7f8093a773622504ddc028532f20e6d986db067'
VERSION = 'route-a-readonly-data-audit-v1'
MOVE = re.compile(r'^move\s+(.+?)\s+to\s+(.+?)\s*$')
PUBLIC_KEYS = {'goal', 'observation', 'admissible_commands', 'history'}


def chain(path):
    # EvidenceStore can create a missing parent. Require an existing file first.
    if not path.is_file():
        raise FileNotFoundError(path)
    return EvidenceStore(path).records()


def fresh_failure(context):
    history = context['history']
    return bool(history and MOVE.fullmatch(' '.join(history[-1]['action'].split()))
                and history[-1]['observation'].strip() == 'Nothing happens.'
                and context['observation'].strip() == 'Nothing happens.')


def assess_context(row):
    """Report public facts only; never infer the requested three-valued label."""
    ctx = row['public_context']
    if set(ctx) != PUBLIC_KEYS or any(set(s) != {'action', 'observation'} for s in ctx['history']):
        raise PermissionError('public context whitelist')
    latest = ctx['history'][-1] if ctx['history'] else None
    return dict(sample_id=row['evidence_ref'], candidate_context=ctx,
                context_sha256=fingerprint(ctx), fresh_failed_placement=fresh_failure(ctx),
                label=None, label_provenance='NOT_ADJUDICATED',
                confidence_or_review_status='CONTEXT_ONLY_NOT_TRAIN_LABEL',
                label_evidence=[dict(kind='OBSERVED_LAST_TRANSITION', value=latest)],
                exclusion_reason=None if fresh_failure(ctx) else 'OUTSIDE_FAILED_PLACEMENT_HOOK')


def trace_hits(trace):
    return [dict(step=i, action=s['action'], observation=s['observation'])
            for i, s in enumerate(trace['actions'], 1)
            if MOVE.fullmatch(' '.join(s['action'].split()))
            and s['observation'].strip() == 'Nothing happens.']


def native_scan(root, excluded):
    protocol = read(root/'protocol.json')
    summary = read(root/'summary.json')
    if summary['status'] != 'COMPLETED' or summary['protocol_sha256'] != fingerprint(protocol):
        raise PermissionError('native run not committed')
    rows = [r for r in chain(root/'episodes.jsonl') if r['kind'] == 'EPISODE_COMMITTED']
    hits = []
    steps = 0
    for task, row in zip(protocol['tasks'], rows, strict=True):
        entry = row['payload']
        if task['task_id'] != entry['task_id']:
            raise PermissionError('native game binding')
        trace = entry['outcome']['trace']
        journal = root/'episodes'/task['task_id']/'environment.jsonl'
        receipts = chain(journal)
        if receipts[0]['kind'] != 'RESET' or any(r['kind'] != 'STEP' for r in receipts[1:]):
            raise PermissionError('unexpected environment event')
        for actual, recorded in zip(receipts[1:], trace['actions'], strict=True):
            if any(actual['payload'][k] != recorded[k] for k in ('action', 'observation', 'done', 'score')):
                raise PermissionError('native public trace drift')
        steps += len(trace['actions'])
        hits.extend(dict(h, game_id=task['game_sha256'], source_record=row['record_hash'],
                         excluded=task['game_sha256'] in excluded) for h in trace_hits(trace))
    return dict(episodes=len(rows), public_steps=steps, failed_placements=hits,
                new_failure_games=len({r['game_id'] for r in hits if not r['excluded']}),
                files={str(root/n):sha(root/n) for n in ('protocol.json','summary.json','episodes.jsonl')})


def other_historical_scans(base):
    """Inventory search, not admission: positive hits would need full provenance review."""
    result = []
    p = base/'alfworld_baseline_20261108/run120'
    rows = [r for r in chain(p/'episodes.jsonl') if r['kind'] == 'EPISODE_LOCKED']
    groups = [('pure_dynamic120', rows, ['payload'], p/'episodes.jsonl')]
    for name in ('alfworld_learning20_20261108_01', 'alfworld_learning120_20261108_01'):
        file = base/name/'run/stream.jsonl'
        rows = [r for r in chain(file) if r['kind'] == 'FUTURE_PAIRED_DONE']
        groups.append((name, rows, ['G', 'F'], file))
    for name, rows, arms, file in groups:
        counts, hits, omitted = Counter(), [], Counter()
        for record in rows:
            for arm in arms:
                entry = record['payload'] if arm == 'payload' else record['payload'][arm]
                if entry['status'] not in ('SUCCESS', 'STEP_LIMIT', 'ACTION_CYCLE', 'NO_PROGRESS'):
                    omitted[entry['status']] += 1
                    continue
                counts[arm] += 1
                hits.extend(dict(h, task_id=entry['task_id'], arm=arm,
                                 source_record=record['record_hash']) for h in trace_hits(entry['trace']))
        result.append(dict(run=name, valid_episode_observations=dict(counts), excluded_states=dict(omitted),
                           failed_placements=hits, source=str(file), source_sha256=sha(file),
                           admission='SEARCH_ONLY_REQUIRES_PROVENANCE_REVIEW_IF_HITS'))
    return result


def data_readiness(train, validation):
    """Check basic label coverage, without claiming statistical adequacy."""
    issues = []
    for role, rows in [('TRAIN', train), ('TRAIN_VALIDATION', validation)]:
        for label in ('MATCH', 'DECLINE', 'UNKNOWN'):
            games = {r['game_id'] for r in rows if r.get('label') == label
                     and r.get('confidence_or_review_status') == 'EVIDENCE_REVIEWED'}
            if not games:
                issues.append(f'{role}_{label}_EVIDENCE_MISSING')
    a = {r['game_id'] for r in train}
    b = {r['game_id'] for r in validation}
    if a & b:
        issues.append('TRAIN_VALIDATION_GAME_OVERLAP')
    for rows in (train, validation):
        if any(r.get('label') not in ('MATCH','DECLINE','UNKNOWN') or not r.get('label_evidence') for r in rows):
            issues.append('MISSING_TRUSTED_LABEL_EVIDENCE')
    return dict(status='DATA_READY' if not issues else 'BLOCKED_DATA_INSUFFICIENT', blockers=issues)


def audit(base):
    if sha(S0/'candidate_0/revision_02/decoded.py') != S0_SHA or sha(S1/'historical_training.private.json') != TRAIN_SHA:
        raise PermissionError('historical source or evidence identity differs')
    training = read(S1/'historical_training.private.json')
    formal = read(base/'alfworld_full_library_online120_20261109_01/protocol.json')
    old_rules = read(S1/'selection_rules.json')
    # Preserve the complete prior exclusions, including the non-container
    # game underlying some exposed boundary tests.
    source = read(S0/'protocol.json')
    # The immutable S1 training report explicitly records scene roles, while
    # source/negative bindings below come from their original archived records.
    import run_alfworld_python_recovery_feedback as pilot
    _, _, _, _, _, boundaries, _ = pilot.frozen_real_inputs(
        base, ROOT/'runs/python_recovery_container_pilot_20261112_01', container_only=True)
    excluded_sequences = set(old_rules['excluded_source_sequences_in_formal_run']) | {r['source_sequence'] for r in boundaries}
    excluded = {formal['tasks'][i-1]['game_sha256'] for i in excluded_sequences}
    records = []
    for row in training['rows']:
        p = row['provenance']
        journal = Path(p['journal'])
        if sha(journal) != p['journal_sha256']:
            raise PermissionError('historical journal drift')
        steps = chain(journal)
        at = steps[p['step']]
        if (at['record_hash'] != p['receipt_sha256']
                or row['public_context']['history'] != [{k:s['payload'][k] for k in ('action','observation')}
                                                       for s in steps[1:p['step']+1]]
                or row['public_context']['observation'] != at['payload']['observation']
                or row['public_context']['admissible_commands'] != at['payload']['commands']):
            raise PermissionError('public checkpoint drift')
        task = p['task']
        records.append(dict(assess_context(row), game_id=task['game_sha256'], scene_id=task['scene'],
                            task_type=task['task_type'], source_identity=p,
                            checkpoint_identity=fingerprint([task['game_sha256'],p['receipt_sha256'],p['step']]),
                            historical_exposure='S1_TRAINING_ALREADY_EXPOSED'))
    reserved = read(S1/'independent_inventory.private.json')
    tests = reserved['strict_scene'] + reserved['expanded_game_group']
    if {r['game_id'] for r in records} & {r['game_sha256'] for r in tests}:
        raise PermissionError('independent role overlap')
    if excluded & {r['game_sha256'] for r in tests}:
        raise PermissionError('regression and independent overlap')
    native = {name:native_scan(base/name, excluded) for name in old_rules['historical_runs']}
    result = dict(version=VERSION, scope='A1_DATA_READINESS_ONLY', paid_requests=0,
        worker_calls=0, independent_games_executed=0, recovery_source_sha256=S0_SHA,
        existing_context_audit=records, native_scan=native, additional_search=other_historical_scans(base),
        roles=dict(TRAIN=[], TRAIN_VALIDATION=[],
                   EXPOSED_REGRESSION=dict(positive_sources=11, boundary_inputs=21,
                     excluded_games=sorted(excluded), boundary_sha256=source['boundaries_sha256'],
                     positive_retention_use='POST_SELECTION_VETO_NO_RESELECTION'),
                   INDEPENDENT_TEST=dict(inventory_sha256=sha(S1/'independent_inventory.private.json'),
                     strict_scene_games=len(reserved['strict_scene']), expanded_games=len(reserved['expanded_game_group']),
                     labelled_checkpoints=0, status='METADATA_ONLY_NOT_TEST_READY')),
        readiness=data_readiness([], []), training_candidate_contexts=len(records),
        note='No absence, successful intermediate move or ambiguous instance was converted into a negative label.')
    result['historical_sha256'] = {str(S1/n):sha(S1/n) for n in
        ('historical_training.private.json','selection_rules.json','independent_inventory.private.json','result.json')}
    result['historical_sha256'].update({str(S0/n):sha(S0/n) for n in ('protocol.json','result.json','candidate_0/revision_02/decoded.py')})
    return result


def freeze(output, result):
    if output.exists():
        if read(output) != result:
            raise PermissionError('A1 audit already frozen with different content')
    else:
        save(output, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.output.parent.is_dir() or args.output.parent.stat().st_mode & 0o077:
        raise PermissionError('create a private 0700 audit directory first')
    result = freeze(args.output, audit(args.base))
    print(result['readiness']['status'])


if __name__ == '__main__':
    main()
