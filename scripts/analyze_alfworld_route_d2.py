"""Read-only analysis of frozen D2 receipts; never executes a model or environment."""
import argparse
import collections
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def journal(path):
    rows = [json.loads(s) for s in path.read_text().splitlines()]
    previous = '0' * 64
    for row in rows:
        body = {k: v for k, v in row.items() if k != 'record_hash'}
        assert body['previous_hash'] == previous and digest(body) == row['record_hash'], path
        previous = row['record_hash']
    return rows


def main(root, out):
    protocol = read(root / 'protocol.json')
    frozen = read(root / 'Checkpoints_Frozen.json')
    complete = read(root / 'Completed.json')
    selection = read(root / 'selection.private.json')
    exposure = read(root / 'exposure.private.json')
    candidate = read(root / 'Frozen_Candidate.json')
    repository = root.parent.parent
    reserved_path = repository / 'runs/alfworld_route_a_online_value_20261117_01/online/selection.private.json'
    reserved = [r['task'] for r in read(reserved_path)['tasks']]
    tasks = selection['tasks']
    eligible = {r['task']['task_id'] for r in exposure['eligible']}
    protected = [r['task'] for r in exposure['protected_games']]
    validation = {
        'completed': len(complete['results']) == len(frozen['jobs']) == 6,
        'all_frozen_file_hashes_match': all(sha(Path(p)) == h for p, h in protocol['files'].items()),
        'original_and_copy_v2_unchanged': sha(Path(candidate['source'])) == sha(root / 'frozen/code.py') == candidate['code_sha256'] == complete['frozen_candidate_sha256'],
        'protocol_markdown_unchanged': sha(out / 'Protocol.md') == read(root / 'Preflight.json')['protocol_markdown_sha256'],
        'reserved60_manifest_unchanged': len(reserved) == 60 and sha(reserved_path) == selection['reserved60_manifest_sha256'],
        'all_selected_previously_eligible': all(t['task_id'] in eligible for t in tasks),
        'four_distinct_groups': len({t['group'] for t in tasks}) == 4,
        'no_malformed_exposure_records': not exposure['malformed'],
        'no_stopped_receipt': not list(root.glob('Stopped*')),
    }
    for label, excluded in [('reserved60', reserved), ('protected', protected)]:
        for key in ['task_id', 'game_sha256', 'trajectory_sha256', 'group']:
            validation[f'{label}_{key}_disjoint'] = not ({t[key] for t in tasks} & {t[key] for t in excluded})
    budget = journal(root / 'budget.jsonl')
    events = journal(root / 'events.jsonl')
    environment = journal(root / 'environment_actions.jsonl')
    requests = {r['payload']['request_id']: r['payload'] for r in budget if r['kind'] == 'RESERVED'}
    settled = {r['payload']['request_id']: r['payload'] for r in budget if r['kind'] == 'SETTLED'}
    validation['every_request_settled_no_unknown'] = requests.keys() == settled.keys() and not any(r['kind'] == 'UNKNOWN' for r in budget)
    starts = [r for r in environment if r['kind'] == 'STARTED']
    returns = [r for r in environment if r['kind'] == 'RETURNED']
    validation['every_environment_call_returned'] = len(starts) == len(returns) and {r['payload']['number'] for r in starts} == {r['payload']['number'] for r in returns}
    first_tool = min(r['at'] for r in budget if r['kind'] == 'RESERVED' and r['payload']['kind'] == 'tool')
    validation['all_checkpoints_frozen_before_first_worker'] = datetime.fromisoformat(frozen['created_at']).timestamp() < first_tool
    rows, strata = [], {}
    parser = collections.defaultdict(collections.Counter)
    for job in frozen['jobs']:
        index, kind, cp = job['game_index'], job['kind'], job['checkpoint']
        stem = root / f'pairs/{index:02d}/{kind}'
        arms = {a: read(stem / a / 'result.json') for a in ['G', 'F']}
        start = {a: read(stem / a / 'start.private.json') for a in arms}
        assert start['G'] == start['F']
        assert all(digest(start[a]) == arms[a]['start_sha256'] for a in arms)
        assert digest(cp) == job['checkpoint_sha256']
        assert all(arms[a]['remaining'] == 50 - cp['anchor'] and arms[a]['steps'][:cp['anchor']] == cp['steps'] for a in arms)
        row = dict(game_index=index, task_id=tasks[index]['task_id'], group=tasks[index]['group'], kind=kind, anchor=cp['anchor'], remaining=50-cp['anchor'])
        for a, result in arms.items():
            for k in ['won', 'status', 'suffix_steps', 'logical_model_calls', 'worker_calls', 'policy_actions', 'policy_errors', 'first_policy_status']:
                row[a + '_' + k] = result[k]
            row[a + '_illegal_executed'] = sum(rec['feedback']['action'] not in rec['legal_before'] for rec in result['records'])
            for rec in result['records']:
                if rec['parse']:
                    p = rec['parse']
                    parser[kind + '/' + a]['model_actions'] += 1
                    parser[kind + '/' + a]['intent_illegal'] += p['stated_is_legal'] is False
                    parser[kind + '/' + a]['parser_changed_action'] += p['different']
                    parser[kind + '/' + a][p['stage']] += 1
        row['rescued'] = not arms['G']['won'] and arms['F']['won']
        row['degraded'] = arms['G']['won'] and not arms['F']['won']
        row['model_calls_saved'] = arms['G']['logical_model_calls'] - arms['F']['logical_model_calls']
        row['environment_actions_saved'] = arms['G']['suffix_steps'] - arms['F']['suffix_steps']
        # Concrete public damage marker: removing a target already placed at a goal receptacle.
        # This is deliberately narrower than a general semantic damage classifier.
        placed, retakes = set(), []
        goal_dest = re.search(r'\bin (\w+)', cp['goal'])[1]
        for step in cp['steps']:
            m = re.fullmatch(r'You move the (.+?) to the (.+?)\.', step['observation'])
            if m and m[2].split()[0] == goal_dest:
                placed.add((m[1], m[2]))
            m = re.fullmatch(r'You pick up the (.+?) from the (.+?)\.', step['observation'])
            if m:
                placed.discard((m[1], m[2]))
        for rec in arms['F']['records']:
            m = re.fullmatch(r'You pick up the (.+?) from the (.+?)\.', rec['feedback']['observation'])
            if m and (m[1], m[2]) in placed and rec['actor'] == 'SKILL':
                retakes.append(rec['step'])
        row['skill_retakes_of_prefix_placed_objects'] = len(retakes)
        row['skill_only_completion'] = arms['F']['won'] and arms['F']['policy_actions'] > 0 and arms['F']['logical_model_calls'] == 0
        rows.append(row)
    validation['all_paired_start_hashes_prefixes_remaining_and_checkpoint_hashes_match'] = True
    for kind in sorted({r['kind'] for r in rows}):
        subset = [r for r in rows if r['kind'] == kind]
        summary = dict(checkpoints=len(subset), independent_games=len({r['game_index'] for r in subset}))
        for key in ['G_won', 'F_won', 'rescued', 'degraded', 'model_calls_saved', 'environment_actions_saved', 'skill_only_completion', 'skill_retakes_of_prefix_placed_objects']:
            summary[key] = sum(r[key] for r in subset)
        for a in ['G', 'F']:
            for k in ['logical_model_calls', 'suffix_steps', 'worker_calls', 'policy_actions', 'policy_errors', 'illegal_executed']:
                summary[a + '_' + k] = sum(r[a + '_' + k] for r in subset)
        summary['skill_takeovers'] = sum(r['F_policy_actions'] > 0 for r in subset)
        summary['zero_action_declines'] = sum(r['F_first_policy_status'] == 'declined' and r['F_policy_actions'] == 0 for r in subset)
        summary['F_used_more_environment_actions'] = sum(r['environment_actions_saved'] < 0 for r in subset)
        strata[kind] = summary
    costs = collections.defaultdict(lambda: collections.Counter())
    responses = list((root / 'requests').rglob('response.json'))
    for p in responses:
        rel = p.relative_to(root / 'requests')
        section = 'native' if rel.parts[0] == 'native' else f'pairs/{rel.parts[2]}/{rel.parts[3]}'
        usage = read(p)['usage']
        c = costs[section]
        c['calls'] += 1
        for key in ['prompt_tokens', 'completion_tokens', 'total_tokens']:
            c[key] += usage[key]
        request_id = str(rel.parent)
        assert settled[request_id]['tokens'] == usage['total_tokens']
        c['retained_reservation_microusd'] += requests[request_id]['cost_upper_microusd']
    for c in costs.values():
        c['peak_uncached_quote_usd'] = (c['prompt_tokens'] * 0.30 + c['completion_tokens'] * 1.20) / 1_000_000
    total = sum((collections.Counter(c) for c in costs.values()), collections.Counter())
    workers = list(root.glob('pairs/*/*/F/workers/*.json'))
    validation['worker_receipts_match_frozen_code'] = all(read(p)['code_sha256'] == candidate['code_sha256'] for p in workers)
    validation['model_worker_receipt_counts_match_ledger'] = len(responses) == sum(p['kind']=='model' for p in requests.values()) and len(workers) == sum(p['kind']=='tool' for p in requests.values())
    validation['no_learning_calls_or_response_cache'] = all(k.startswith(('native/', 'pairs/')) and '/plan' not in k for k,v in requests.items() if v['kind']=='model') and all(read(p)['cache_hits'] == 0 for p in root.glob('pairs/*/*/*/result.json'))
    wall = datetime.fromisoformat(complete['completed_at']).timestamp() - budget[0]['at']
    validation['within_frozen_limits'] = total['calls'] <= protocol['max_calls'] and total['retained_reservation_microusd'] <= protocol['max_cost_microusd'] and len(starts) <= protocol['max_environment'] and len(workers) <= protocol['max_workers'] and wall <= protocol['wall_seconds']
    assert all(validation.values()), validation
    result = dict(run_id=protocol['run_id'], candidate_sha256=candidate['code_sha256'], unique_games=4, checkpoint_pairs=len(rows), natural_recovery_status='NATURAL_OPPORTUNITY_NOT_OBSERVED', natural_opportunity_games=sum(c['natural_opportunity_observed'] for c in frozen['coverage']), native_collection=frozen['coverage'], strata=strata, paired_rows=rows, parser=dict(parser), costs_by_phase=dict(costs), costs_total=dict(total), actual_provider_bill_usd=None, environment_calls=len(starts), environment_calls_by_phase=dict(collections.Counter(r['payload']['phase'] for r in starts)), worker_calls=len(workers), worker_host_milliseconds=sum(read(p)['milliseconds'] for p in workers), experiment_wall_seconds=wall, learning_calls=0, revisions=0, R_run=False)
    out.mkdir(parents=True, exist_ok=True)
    for name, value in [('Results.json', result), ('Validation.json', validation)]:
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    with (out / 'Results.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps(dict(strata=strata, costs_total=dict(total), environment_calls=len(starts), worker_calls=len(workers), wall_seconds=wall, all_validation_passed=all(validation.values()), parser=dict(parser)), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('run', type=Path); p.add_argument('out', type=Path)
    a = p.parse_args(); main(a.run.resolve(), a.out.resolve())
