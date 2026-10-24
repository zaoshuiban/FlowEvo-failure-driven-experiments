"""Zero-API public scorer parity for prepared DEVELOPMENT tasks, not final review."""
import argparse,tempfile
from pathlib import Path
import run_workflow_v2 as e
from run_learning_stream import configure_worker
from failure_evo.contracts import strict_stream_task,fingerprint

def accept(bundle,output):
    bundle,output=Path(bundle),Path(output)
    manifest=e.read(bundle/'task_manifest.json');tasks=e.read(bundle/'development_tasks.json')
    if e.sha(bundle/'development_tasks.json')!=manifest['development_sha256']:raise ValueError('frozen tasks changed')
    output.mkdir(parents=True,exist_ok=False);(output/'tmp').mkdir();tempfile.tempdir=str(output/'tmp')
    configure_worker(e.read(e.ROOT/'reports/s19_v2_acceptance/worker_environment.json'))
    budget=e.PersistentBudget(output/'budget.jsonl',run_id=output.name,protocol_hash=fingerprint(manifest),**e.prior.config(0,1000,0))
    judge=e.prior.Judge(budget);rows=[]
    for task,origin in zip(tasks,manifest['rows']):
        strict_stream_task(task);source=e.ROOT/origin['source']
        if e.sha(source)!=origin['source_file_sha256']:raise ValueError('source changed')
        old=e.read(source)[origin['source_index']]
        if origin['exposure']=='S18-observed':
            folder=e.ROOT/'runs/s18_data_freeze_20261023_01/tasks'/old['original_id']
            expected=e.read(folder/'task.json')['reference_hashes'][0];reference=folder/'reference_0.py'
        else:reference=Path(old['reference_path']);expected=old['reference_sha256']
        if e.sha(reference)!=expected:raise ValueError('reference changed')
        positive=judge.run(task['task_id'],reference.read_text(),task['public_cases'])
        negative=judge.run(task['task_id'],"print('S19_INVALID_FIXTURE')",task['public_cases'])
        rows.append(dict(task_id=task['task_id'],reference_sha256=expected,positive=positive,negative=negative,passed=positive['passed'] and not negative['passed']))
        e.write(output/'public_acceptance.json',dict(real_api_calls=0,scope='already_exposed_development_public_only',passed=all(r['passed'] for r in rows),completed=len(rows),expected=len(tasks),rows=rows,budget=budget.snapshot()))
        print(task['task_id'],rows[-1]['passed'],flush=True)
        if not rows[-1]['passed']:raise ValueError('public scoring failed; no task substitution')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',required=True);p.add_argument('--output',required=True);a=p.parse_args();accept(a.bundle,a.output)
