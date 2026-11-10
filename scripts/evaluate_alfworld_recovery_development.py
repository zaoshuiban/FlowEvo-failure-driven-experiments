"""Evaluate frozen recovery policies on a preregistered development audit, zero API."""
import argparse
from collections import Counter
from pathlib import Path
import re

from alfworld_.failure_learning import EnvironmentPolicyRunner
from alfworld_.skill_acquisition import load_source, review_source
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import fingerprint
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.math_stream import read, save
from run_alfworld_skill_acquisition import create_accounts


def placement_families(proposal, host):
    families = set()
    for eid in proposal['evidence_ids']:
        origin = host[eid]
        action = origin['steps'][origin['projected']['anchor']-1]['action']
        match = re.fullmatch(r'move .+ to (.+) \d+', action)
        if match:
            families.add(match[1])
    return sorted(families)


def evaluate(source, pilot, audit):
    plan = read(audit/'audit_freeze.private.json')
    protocol, _, host = load_source(source)
    frozen = read(pilot/'protocol.json')
    official = read(pilot/'result.json')
    protocol_hash = fingerprint(frozen)
    if (plan['scope'] != 'DEVELOPMENT_ONLY_NO_INDEPENDENT_GATE'
            or plan['source_protocol_sha256'] != fingerprint(protocol)
            or plan['pilot_protocol_sha256'] != protocol_hash
            or official['protocol_sha256'] != protocol_hash
            or official['scope'] != 'REAL_B_SOURCE_ONLY'
            or plan['max_model_calls'] or plan['max_cost_microusd']):
        raise PermissionError('development audit identities or permissions differ')
    backend = FrozenLinuxBackend(image=frozen['worker']['image'], worker_script=frozen['worker']['worker_script'])
    if backend.manifest() != frozen['worker']:
        raise PermissionError('frozen Worker drift')
    budget = create_accounts(audit, dict(run_id=audit.name, max_calls=0, max_tokens=0,
        max_cost_microusd=0, worker_calls=plan['max_worker_calls'], plan_sha256=fingerprint(plan)))
    runner = EnvironmentPolicyRunner(backend,audit/'worker.jsonl',budget)
    registry = FailureOperatorRegistry(pilot/'registry.jsonl', FailureEvidenceStore(pilot/'failures.jsonl'))
    outcomes = []
    gate = plan['advance']
    for record in official['result']['candidates']:
        families = placement_families(record['proposal'],host)
        row = dict(mechanism_id=record['mechanism_id'],status=record['status'],proposed_families=families)
        outcomes.append(row)
        if record['status'] != 'SHADOW':
            continue
        card = FailureOperator.from_dict(record['card'])
        if not card.intact() or registry.state(card)['permission'] != 'shadow':
            raise PermissionError('candidate integrity or shadow status changed')
        row['version'] = card.version
        row['source_sha256'] = card.artifact_sha256
        row['negative'] = []
        for case in plan['negative_cases']:
            if case['expected'] != 'declined':
                raise ValueError('negative expected decision drift')
            actual = runner.run(card,case['context'])
            row['negative'].append(dict(id=case['id'],category=case['category'],actual=actual))
        historic = {v['checkpoint']['evidence_id']:v for v in record['checks']}
        row['exposed'] = []
        for case in plan['exposed_checkpoints']:
            eid = case['evidence_id']
            origin = host[eid]
            step = case['step']
            if (origin['receipt_sha256'] != case['source_receipt'] or step != origin['projected']['anchor']
                    or origin['sequence'] != case['sequence']):
                raise PermissionError('source checkpoint drift')
            if eid in historic:
                result = historic[eid]
                if result['candidate_version'] != card.version or result['checkpoint']['step'] != step:
                    raise PermissionError('historical validation receipt drift')
                reused = True
            else:
                ref = dict(evidence_id=eid,step=step,quote=origin['steps'][step-1]['observation'])
                result = review_source(protocol['data_root'],origin,ref,card,runner,registry,
                                       audit/f"{card.operator_id}_{case['sequence']}.json",extended=True)
                reused = False
            row['exposed'].append(dict(family=case['family'],sequence=case['sequence'],reused=reused,
                status=result['status'],steps=result['alternate_action_count'],
                local_repair_verified=result['local_repair_verified'],won=result['episode_won']))
        verified_sequences = {x['sequence'] for x in row['exposed'] if x['local_repair_verified'] and
                              x['status'] != 'POLICY_ERROR'}
        repaired = {x['family'] for x in row['exposed'] if x['sequence'] in verified_sequences}
        row['repaired_families'] = sorted(repaired)
        row['negative_counts'] = dict(Counter(x['actual']['status'] for x in row['negative']))
        row['eligible_for_independent_preparation'] = (
            (not gate['require_cross_family_grounded_proposal'] or len(families)>=2)
            and len(repaired)>=gate['min_repaired_container_families_same_candidate']
            and row['negative_counts'].get('applied',0)<=gate['negative_false_triggers']
            and row['negative_counts'].get('error',0)<=gate['negative_errors'])
        save(audit/f"{card.operator_id}_development.json",row)
    summary = dict(scope=plan['scope'],pilot_protocol_sha256=protocol_hash,plan_sha256=fingerprint(plan),
        paid_calls=0,independent_games_executed=0,worker_calls=budget.tool_calls,candidates=outcomes,
        eligible=sum(bool(r.get('eligible_for_independent_preparation')) for r in outcomes))
    save(audit/'summary.json',summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('source','pilot','audit'):
        parser.add_argument('--'+flag,type=Path,required=True)
    args = parser.parse_args()
    result = evaluate(args.source,args.pilot,args.audit)
    print(f"Development checks complete. Eligible {result['eligible']}; Worker {result['worker_calls']}.")
