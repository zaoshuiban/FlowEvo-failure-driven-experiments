"""Versioned evaluator entry point for future callers; never reads API credentials."""
import argparse
import hashlib
import json
import pathlib
from comparison import solver_feedback
from preflight import preflight
from regrade import evaluate, write

UNSCORABLE={'INVALID_TEST','REFERENCE_DISPUTE','CHECKER_UNSUPPORTED','PROTOCOL_UNSUPPORTED',
            'EVALUATOR_ERROR','NO_VALID_TESTS'}


def evaluate_v2(task_path, candidate_path, policies_path):
    task=json.loads(pathlib.Path(task_path).read_text())
    policies=json.loads(pathlib.Path(policies_path).read_text())
    if task['task_id'] not in policies:
        return {'status':'CHECKER_UNSUPPORTED','passed':None,
                **solver_feedback({'status':'CHECKER_UNSUPPORTED'})}
    policy=policies[task['task_id']]
    if hashlib.sha256(pathlib.Path(task_path).read_bytes()).hexdigest()!=policy['task_sha256']:
        raise ValueError('Task changed; create and validate a new policy version first')
    pre,cases=preflight(task,policy)
    verdict=evaluate(task,policy,pre,cases,pathlib.Path(candidate_path))
    verdict['passed']=None if verdict['status'] in UNSCORABLE else verdict['status']=='PASS'
    verdict['solver_feedback']=solver_feedback(verdict)
    return verdict


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--task',required=True);p.add_argument('--candidate',required=True);p.add_argument('--policies',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    verdict=evaluate_v2(a.task,a.candidate,a.policies)
    write(pathlib.Path(a.out),verdict)
    print(json.dumps({'status':verdict['status'],'passed':verdict['passed'],'solver_feedback':verdict['solver_feedback']},ensure_ascii=False))
