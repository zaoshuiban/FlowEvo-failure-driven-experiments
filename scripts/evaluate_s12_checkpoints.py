"""Evaluate a supplied operator only after real local Worker acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo import PersistentBudget
from failure_evo.checkpoint_evaluator import CheckpointEvaluator
WORKER=ROOT/'experiments/flowevo_taco_lcb_20261019/repair_v2/epochs/repair_v2d_20261020/code/candidate_worker.py'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acceptance',required=True)
    parser.add_argument('--config',required=True)
    parser.add_argument('--operator')
    parser.add_argument('--checkpoint')
    parser.add_argument('--output-dir',required=True)
    args=parser.parse_args();out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=False)
    proof=json.loads(Path(args.acceptance).read_text())
    result=dict(status='BLOCKED',executed_generated_code=False,new_api_calls=0)
    if proof.get('status')!='PASS':
        result['reason']='real local Worker has not passed acceptance'
    elif not args.operator or not args.checkpoint:
        result['reason']='operator artifact and frozen checkpoint required'
    else:
        config=json.loads(Path(args.config).read_text())
        budget=PersistentBudget(out/'evaluation_budget.jsonl',run_id=config['run_id']+':evaluation',
                                protocol_hash=config['protocol_hash'],**config['evaluation_budget'])
        evaluator=CheckpointEvaluator(ROOT,budget,image=proof['image'],worker_script=WORKER,acceptance_path=args.acceptance)
        source=Path(args.operator).read_text();checkpoint=json.loads(Path(args.checkpoint).read_text())
        dataset=dict(role='design',checkpoints=[checkpoint])
        result=dict(status='COMPLETED',executed_generated_code=True,new_api_calls=0,
            operator_sha256=hashlib.sha256(source.encode()).hexdigest(),
            checkpoint_sha256=hashlib.sha256(Path(args.checkpoint).read_bytes()).hexdigest(),
            evaluation=evaluator(source,dataset,10))
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='COMPLETED' else 2

if __name__=='__main__':raise SystemExit(main())
