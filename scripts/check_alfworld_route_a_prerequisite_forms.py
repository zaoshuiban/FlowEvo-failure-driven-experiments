"""Zero-model Worker-only engineering checks; never independent game evidence.

The cases are frozen before reading the revised source. They may contain
explicit synthetic goal/instance variants and must never enter model feedback.
This entry does not change the candidate or issue publication permissions.
"""
import argparse
import fcntl
import time
from pathlib import Path
import run_alfworld_route_a_prerequisites_v2 as R


def accepted(expected, status):
    if expected not in ('MATCH','NOT_MATCH') or status not in ('MATCH','DECLINE','UNKNOWN'):
        return False
    return status=='MATCH' if expected=='MATCH' else status!='MATCH'


def run(root):
    p,_=R.verify(root/'development')
    if not (root/'development/result.json').exists():
        raise PermissionError('finish development before sharing its Worker journal')
    frozen=R.A.read(root/'Morphology_Freeze.json')
    fixtures=root/'Morphology_Fixtures.private.json'
    if frozen['fixtures_sha256']!=R.A.sha(fixtures):raise PermissionError('fixture drift')
    data=R.A.read(fixtures)
    if data['role']!='ENGINEERING_ONLY_NOT_MODEL_INPUT_NOT_INDEPENDENT':raise PermissionError('fixture role')
    if len(data['cases'])!=frozen['cases']:raise PermissionError('case count drift')
    version=p['candidate_version'];out=root/'engineering_forms'
    plan=dict(version=version,fixtures_sha256=R.A.sha(fixtures),candidate_sha256=p['candidates']['Route_A']['sha256'],
        recovery_sha256=p['candidates']['S0']['sha256'],runner_sha256=R.A.sha(__file__),
        worker=p['worker'],model_calls=0,environment_steps=0,
        score='MATCH required for supported cases; DECLINE or UNKNOWN for missing/conflicting cases; ERROR always fails',
        role='ENGINEERING_ONLY',permissions='SHADOW',no_model_feedback=True)
    R.A.commit(out/'protocol.json',plan)
    with (root/'development/run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        budget,runner,registry,receipts,recovery,gate=R.V.setup(root/'development',p)
        if (out/'result.json').exists():
            result=R.A.read(out/'result.json')
            if result['protocol_sha256']!=R.A.digest(plan):raise PermissionError('result binding')
            return result
        rows=[]
        for case in data['cases']:
            decision=R.B.learned_decision(runner,gate,dict(case['context'],state={}))
            rows.append(dict(case_id=case['case_id'],expected=case['expected'],decision=decision,
                passed=accepted(case['expected'],decision['status']),provenance=case['provenance'],
                context_sha256=R.A.digest(case['context'])))
        if registry.state(gate)['permission']!='shadow' or not gate.intact():raise PermissionError('permission drift')
        return R.A.commit(out/'result.json',dict(protocol_sha256=R.A.digest(plan),candidate_version=version,
            rows=rows,passed=all(r['passed'] for r in rows),pass_count=sum(r['passed'] for r in rows),
            total=len(rows),budget=budget.snapshot(),model_calls=0,environment_steps=0,
            role='ENGINEERING_ONLY_NOT_INDEPENDENT',published=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=run(args.output.resolve())
    print({k:result[k] for k in ('passed','pass_count','total','model_calls','environment_steps')})
