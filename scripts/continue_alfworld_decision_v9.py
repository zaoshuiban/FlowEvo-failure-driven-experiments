"""Run only the two unsent B v9 batches in a separate authorized ledger."""

import argparse
import fcntl
import json
from pathlib import Path

from alfworld_.decision_diagnostic import parse_rows, score_pairs
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, save, sha
from run_alfworld_decision_v9 import (
    MODEL, PRICE, ROOT, VERSION, create_accounts, delivery_counts, grant, load_v8,
    request_bounds, stage_request,
)

PARENT_FILES = ('protocol.json', 'public_input.json', 'references.private.json',
                'provider.jsonl', 'budget.jsonl', 'partial_read_only_audit.json')
BATCHES = ('S_04', 'S_05')


def context(v8, parent, output, mock):
    if output.resolve().parent != parent.resolve().parent or output.resolve() == parent.resolve():
        raise PermissionError('continuation requires a separate sibling directory')
    original = read(parent/'protocol.json')
    audit = read(parent/'partial_read_only_audit.json')
    if (audit['scope'] != 'PARTIAL_STOPPED_SEND_UNKNOWN'
            or audit['protocol_sha256'] != fingerprint(original)
            or any(sha(parent/name) != digest for name, digest in audit['input_file_sha256'].items())
            or any(sha(ROOT/name) != digest for name, digest in original['code_sha256'].items())):
        raise PermissionError('parent protocol, audit or code drift')
    _, cases, _ = load_v8(v8)
    public = read(parent/'public_input.json')
    refs = read(parent/'references.private.json')
    if fingerprint(public) != original['public_sha256'] or fingerprint(refs) != original['reference_sha256']:
        raise PermissionError('parent dataset drift')
    if request_bounds(public) != original['schedule']:
        raise PermissionError('parent wire schedule drift')
    statuses = {entry['batch']: entry['status'] for entry in audit['batch_status']}
    if set(name for name, status in statuses.items() if status == 'NOT_STARTED') != set(BATCHES):
        raise PermissionError('unexpected unsent batch set')
    if set(name for name, status in statuses.items() if status == 'SEND_UNKNOWN') != {'S_03'}:
        raise PermissionError('unexpected unknown batch set')
    schedule = [row for row in original['schedule'] if f"{row['arm']}_{row['batch']:02d}" in BATCHES]
    sent = {row['payload']['wire_sha256'] for row in EvidenceStore(parent/'provider.jsonl').records()
            if row['kind'] == 'SEND_STARTED'}
    if any(row['wire_sha256'] in sent for row in schedule):
        raise PermissionError('continuation includes a previously sent batch')
    parent_budget = EvidenceStore(parent/'budget.jsonl').records()
    reserved = [row['payload'] for row in parent_budget if row['kind'] == 'RESERVED']
    max_cost = sum((PRICE['output']*(row['input_upper']+row['output_upper'])+99)//100
                   for row in schedule)
    if (len(reserved)+len(schedule) > original['max_calls']
            or sum(row['cost_upper_microusd'] for row in reserved)+max_cost > original['max_cost_microusd']):
        raise PermissionError('combined original and continuation upper bounds exceed parent authorization')
    plan = dict(
        scope='MOCK_UNSENT_CONTINUATION' if mock else 'REAL_UNSENT_CONTINUATION',
        run_id=('mock:' if mock else 'real:')+output.name,
        version=VERSION, model=MODEL, parent_protocol_sha256=fingerprint(original),
        parent_artifact_sha256={name:sha(parent/name) for name in PARENT_FILES},
        continuation_code_sha256=sha(Path(__file__)), schedule=schedule,
        network_policy=original['network_policy'], worker_calls=0, max_calls=len(schedule),
        max_tokens=sum(row['input_upper']+row['output_upper'] for row in schedule),
        max_cost_microusd=max_cost, unknown_parent_batch='S_03',
    )
    return plan, original, audit, cases, {row['id']:row for row in public}, refs


def run(v8, parent, output, *, sender=None, authorization=None):
    plan, original, audit, cases, public, refs = context(v8, parent, output, sender is not None)
    if sender is None and authorization != grant(plan):
        raise PermissionError('exact continuation authorization required')
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        protocol = output/'protocol.json'
        if protocol.exists() and read(protocol) != plan:
            raise PermissionError('continuation protocol drift')
        if sender is None and not protocol.exists():
            raise PermissionError('freeze continuation protocol before sending')
        if sender is not None:
            save(protocol, plan)
        budget = create_accounts(output, plan)
        predictions = {arm:dict(rows) for arm, rows in audit['model_predictions'].items()}
        checks = {arm:dict(rows) for arm, rows in audit['consistency_checks'].items()}
        receipts = []
        for spec in plan['schedule']:
            arm = spec['arm']
            name = f"{arm}_{spec['batch']:02d}"
            batch_cases = [public[key] for key in spec['case_ids']]
            print(f'{name} · {len(batch_cases)} records', flush=True)
            response = stage_request(
                output, name, 'analyze', dict(cases=batch_cases),
                lambda value: parse_rows(value, arm, batch_cases), budget,
                sender=sender, authorization=authorization,
                network_policy=plan['network_policy'] if sender is None else None,
                protocol=VERSION, analysis_prompt=original['prompts'][arm],
            )
            if response['wire_sha256'] != spec['wire_sha256']:
                raise PermissionError('continuation wire drift')
            parsed = (dict(envelope='PROVIDER_DELIVERY_REJECTED', rows={}, consistency={},
                           rejected=[], missing=spec['case_ids']) if response.get('parse_status')
                      else json.loads(response['specification']))
            if predictions[arm].keys() & parsed['rows'].keys():
                raise PermissionError('continuation would overwrite a parent prediction')
            predictions[arm].update(parsed['rows'])
            checks[arm].update(parsed['consistency'])
            receipts.append(dict(batch=name, response=response, parsed=parsed))
        if any(sha(parent/name) != digest for name, digest in plan['parent_artifact_sha256'].items()):
            raise PermissionError('parent artifacts changed during continuation')
        result = dict(
            scope=plan['scope'], protocol_sha256=fingerprint(plan), parent_unknown_batch='S_03',
            budget=budget.snapshot(), paid_requests=0 if sender is not None else len(receipts),
            continuation_delivery=delivery_counts(receipts), parent_delivery=audit['delivery'],
            receipts=receipts, model_predictions=predictions, consistency_checks=checks,
            reference_evaluation=score_pairs(cases, refs, predictions, checks),
        )
        save(output/'result.json', result)
        return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    for arg in ('v8', 'parent', 'output', 'authorization'):
        cli.add_argument('--'+arg, type=Path, required=True)
    args = cli.parse_args()
    result = run(args.v8, args.parent, args.output, authorization=read(args.authorization))
    print(canonical(dict(status='CONTINUATION_COMPLETE_PARENT_PARTIAL',
                         paid_requests=result['paid_requests'],
                         delivery=result['continuation_delivery'])))


if __name__ == '__main__':
    main()
