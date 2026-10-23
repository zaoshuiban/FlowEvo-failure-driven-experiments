"""Zero-API preparation of a workflow-learning pilot from public checkpoint prefixes.

No provider client, generated-code execution, permissions or old ledgers are changed.
The output is historical development/replay material, not an unseen evaluation set.
"""
import ast
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'runs/s13_compare30_20261022_01'
OUT = ROOT / 'runs/s14_workflow_pivot_20261022_01'
STAGES = ('l1', 'l2a', 'l2b', 'l3', 'l4')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def parseable(code):
    try:
        ast.parse(code)
        return bool(code.strip())
    except (SyntaxError, ValueError):
        return False


def extraction_issue(code, raw_text):
    """Detect shared infrastructure work, never silently select/execute a repair."""
    return not parseable(code) and any(parseable(block) for block in
        re.findall(r'```python\s*\n(.*?)```', raw_text, re.S))


def projected_feedback(raw):
    return dict(status=raw.get('status', 'UNKNOWN'), visibility='public',
        public_cases=[{k: c[k] for k in ('input', 'expected', 'actual', 'exception_class') if k in c}
                      for c in raw.get('public_cases', [])])


def checkpoint_input(workflow, index, raw_response):
    """Only this event and earlier observable candidates may reach induction."""
    event = workflow['events'][index]
    task = event['request']['task']
    prefix = []
    for row in workflow['events'][:index + 1]:
        if 'code' not in row:
            continue
        prefix.append(dict(stage=row['stage'], code=row['code'],
            sha256=hashlib.sha256(row['code'].encode()).hexdigest(),
            public_feedback=projected_feedback(row['public_feedback'])))
    choice = raw_response['choices'][0]
    return dict(task_public={k: task[k] for k in ('problem_id', 'prompt', 'starter_code', 'function_name') if k in task},
        stage=event['stage'], hook='before_final_return' if event['stage'] == 'l4' else 'before_native_retry',
        candidate_code=event['code'], public_feedback=projected_feedback(event['public_feedback']),
        candidate_ledger=prefix, current_generation=dict(finish_reason=choice.get('finish_reason', 'unknown'),
            text=choice['message'].get('content') or ''),
        provenance=dict(role='historical_development_checkpoint', source_run=SOURCE.name,
            natural_failure=True, root_cause='unknown', future_outputs_included=False, final_audit_included=False))


def select_streams(inventory, policy):
    """Fixed order, first usable discovery, later distinct tasks; no score selection."""
    streams = []
    for family in policy['families']:
        rows = sorted([r for r in inventory if r.get('family') == family and r['status'] == 'ELIGIBLE_DEVELOPMENT'],
                      key=lambda r: (r['task_order'], STAGES.index(r['stage'])))
        if not rows:
            streams.append(dict(family=family, status='NO_DISCOVERY', discovery=None, reuse=[]))
            continue
        source = rows[0]
        seen_tasks, seen_programs = {source['task_id']}, {source['candidate_sha256']}
        reuse = []
        for row in rows[1:]:
            if row['task_order'] <= source['task_order'] or row['task_id'] in seen_tasks or row['candidate_sha256'] in seen_programs:
                continue
            seen_tasks.add(row['task_id']); seen_programs.add(row['candidate_sha256'])
            reuse.append(row)
            if len(reuse) == policy['max_reuse_checkpoints_per_family']:
                break
        streams.append(dict(family=family, status='DEVELOPMENT_REPLAY_CANDIDATES' if reuse else 'NO_LATER_REUSE_OPPORTUNITY',
            discovery=source, reuse=reuse, lineage_review='task IDs and exact code differ; problem-family and near-clone review pending',
            independence_claim=False, simulated_order_only=True))
    return streams


def require_paid_ready(policy, readiness):
    """The preparatory entry point cannot interpret an old run balance as authority."""
    missing = [name for name in policy['paid_run_required'] if readiness.get(name) is not True]
    if policy['effective_budget']['max_model_calls'] == 0 or missing:
        raise RuntimeError('PREPARATION_ONLY; new protocol and run-bound budget required: ' + ', '.join(missing))


def prepare():
    if OUT.exists():
        raise FileExistsError('prepared bundle exists; do not silently replace it')
    policy_path = ROOT / 'experiments/workflow_pilot/policy.json'
    policy = read(policy_path)
    assert policy['max_families'] == 2 and policy['effective_budget']['max_model_calls'] == 0
    old = read(SOURCE / 'protocol.json')
    assert digest({k: v for k, v in old.items() if k != 'protocol_hash'}) == old['protocol_hash']
    for file, expected in old['frozen_files'].items():
        assert sha(file) == expected, file
    facts, previous = {}, '0' * 64
    for line in (SOURCE / 'failure_evidence.jsonl').read_text().splitlines():
        record = json.loads(line); actual = record.pop('record_hash')
        assert record['previous_hash'] == previous and digest(record) == actual
        previous = actual
        if record['kind'] == 'FAILURE_FACT':
            fact = record['payload']
            assert not fact['synthetic'] and fact['visibility'] == 'public'
            facts[(fact['task_id'], fact['stage'], fact['candidate_sha256'])] = fact
    OUT.mkdir(parents=True)
    inventory, used_files = [], {policy_path, SOURCE / 'protocol.json', SOURCE / 'tasks.json', SOURCE / 'failure_evidence.jsonl', Path(__file__)}
    for order, task in enumerate(read(SOURCE / 'tasks.json'), 1):
        tid = task['task_id']
        path = SOURCE / 'branches' / tid / 'FailureLearning' / 'workflow.json'
        used_files.add(path); workflow = read(path)
        for i, event in enumerate(workflow['events']):
            status = event.get('public_feedback', {}).get('status')
            if status not in ('NO_COMPLETE_CODE', 'COMPILE_ERROR', 'RUNTIME_ERROR', 'WRONG_ANSWER', 'TIME_LIMIT'):
                continue
            code = event['code']; h = hashlib.sha256(code.encode()).hexdigest()
            response_path = path.parent / f'response_{i + 1}.json'
            used_files.add(response_path); response = read(response_path)
            packet = checkpoint_input(workflow, i, response)
            fact = facts.get((tid, event['stage'], h))
            row = dict(task_id=tid, task_order=order, stage=event['stage'], candidate_sha256=h,
                verifier_status=status, event_id=fact['event_id'] if fact else None,
                root_cause_status='unknown', original_task_sha256=task['task_sha256'],
                prior_development_exposure=True, synthetic=False)
            if extraction_issue(code, packet['current_generation']['text']):
                row.update(status='SHARED_INFRASTRUCTURE', reason='complete Python block exists; fix common extraction before learning')
            elif fact is None:
                row.update(status='NEEDS_PUBLIC_REVALIDATION', reason='no trusted FailureEvidenceStore fact; labels alone are insufficient')
            else:
                row.update(status='ELIGIBLE_DEVELOPMENT', family='delivery_recovery_policy' if status in ('NO_COMPLETE_CODE', 'COMPILE_ERROR') else 'public_feedback_repair_policy',
                    observed_at=fact['observed_at'], evidence_available_from=fact['available_from'])
                packet['provenance']['event_id'] = fact['event_id']
                packet_path = Path('checkpoints') / (tid + '__' + event['stage'] + '.json')
                write(OUT / packet_path, packet)
                row.update(packet=str(packet_path), packet_sha256=sha(OUT / packet_path))
            inventory.append(row)
    streams = select_streams(inventory, policy)
    write(OUT / 'public_failure_inventory.json', inventory)
    write(OUT / 'checkpoint_streams.json', streams)
    # A new research-status manifest closes the line without changing frozen permissions/history.
    closure = []
    for name in ('s12g_capacity_20261022_01', 's12h_capacity_revision_20261022_01', 's12i_capacity_safe_ast_20261022_01',
                 's12j_capacity_scope_v2_20261022_01', 's12j_capacity_scope_v2_revision_20261022_01', 's12j_scope_audit_20261022_01'):
        root = ROOT / 'runs' / name
        files = sorted(list(root.glob('*.md')) + list(root.glob('protocol.json')) + list(root.glob('registry.jsonl')))
        used_files.update(files)
        closure.append(dict(run_id=name, research_status='CLOSED_SPECIALIST_RND', permission_changes=False,
            retained_as='engineering positive/negative evidence; not a growth target', files={str(f.relative_to(ROOT)): sha(f) for f in files}))
    write(OUT / 'capacity_line_closure.json', closure)
    readiness = {name: False for name in policy['paid_run_required']}
    report = dict(status='PREPARED_NOT_PAID_RUN_READY', new_model_calls=0, new_operator_executions=0,
        new_permissions=0, source_facts=len(facts), inventory_counts=dict(Counter(r['status'] for r in inventory)),
        generated_families=0, planned_families=len(streams),
        discovery_task_count=len({s['discovery']['task_id'] for s in streams if s['discovery']}),
        reuse_checkpoint_count=sum(len(s['reuse']) for s in streams), readiness=readiness,
        protocols=dict(active=policy['policy_id'], supersedes='capacity-specific development as main research track'),
        limitation='historical warm-start checkpoint preparation, not natural online reuse, root-cause discovery or independent test evidence',
        historical_input_files={str(f.relative_to(ROOT)): sha(f) for f in sorted(used_files)},
        artifacts={str(f.relative_to(OUT)): sha(f) for f in sorted(OUT.rglob('*.json'))})
    write(OUT / 'preparation.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('historical_input_files', 'artifacts')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    prepare()
