"""Prepare a real empty-artifact witness without reading hidden test verdicts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo import FailureEvidenceStore, PublicFeedback, CompileQueue, LearningLoop
from failure_evo.contracts import fingerprint


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',required=True)
    args=parser.parse_args()
    archive=ROOT/'experiments/flowevo_taco_lcb_20261019/e3_s0_20261020'
    # Frozen historical choice: development witness, never an independent test.
    row=next(json.loads(line) for line in (archive/'events.jsonl').open()
             if json.loads(line)['event_id']=='taco_0310:l1')
    code_path=archive/row['paths']['code'];response_path=archive/row['paths']['response']
    assert hashlib.sha256(code_path.read_bytes()).hexdigest()==row['code_sha256']
    assert hashlib.sha256(response_path.read_bytes()).hexdigest()==row['response_sha256']
    code=code_path.read_text()
    assert not code.strip(), 'artifact is no longer empty'
    out=Path(args.output_dir).resolve();out.mkdir(parents=True,exist_ok=False)
    now=datetime.now(timezone.utc).timestamp()
    store=FailureEvidenceStore(out/'facts.jsonl')
    fact=store.record(stream_id='s12-historical-development',task_id=row['task_id'],
        family_id='incomplete_artifact_recovery',stage=row['stage'],code=code,
        feedback=PublicFeedback('NO_COMPLETE_CODE'),
        observed_at=datetime.fromisoformat(row['response_written_utc']).timestamp(),
        available_from=now,finish_reason=row['finish_reason'],
        provenance_group_id='historical-taco-0310',synthetic=False,
        validation_cost={'model_calls':0,'human_audit_seconds':None,'status':'human_time_not_measured'})
    store.events.append('TASK_COMPLETED',{'stream_id':'s12-historical-development'},now)
    loop=LearningLoop(CompileQueue(out/'queue.jsonl'),store,'s12-historical-development',out/'learning.jsonl')
    job=loop.public_input(loop.pending(now)[0],now)
    job['development_context']=dict(source_mode='historical_development',
        objective='Recover a complete publicly checked candidate or decline without inventing a solution',
        allowed_actions=['select_candidate','candidate_code','declined'],max_model_calls=0,
        shared_baseline_capabilities=['syntax_check','finish_reason','candidate_ledger'],
        root_cause='unknown; empty artifact only, no algorithmic failure claim',
        candidate_ledger_status='not yet supplied for design checkpoints')
    provenance=dict(archive_event_id=row['event_id'],code_path=str(code_path.relative_to(ROOT)),
        code_sha256=row['code_sha256'],response_path=str(response_path.relative_to(ROOT)),
        response_sha256=row['response_sha256'],source_event_file_sha256=hashlib.sha256((archive/'events.jsonl').read_bytes()).hexdigest(),
        generation_input_sha256=fingerprint(job),source_mode='historical_development',
        hidden_verdict_in_generation_input=False,new_model_calls=0)
    for name, value in [('generation_input.json',job),('provenance.json',provenance)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(provenance,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
