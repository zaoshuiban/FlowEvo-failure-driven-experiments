"""Offline evaluator: no sender import or provider request; requires ONLINE_LOCKED."""
import argparse,fcntl,pathlib
import s22_executor as e
from s22_ab import pair_result

def review(directory,judge=None):
    p,m=e.verify();d=pathlib.Path(directory).resolve()
    with (d/'execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=e.read(d/'state.json');identity=e.read(d/'identity.json')
        if state['status']!='ONLINE_LOCKED' or len(state['branches'])!=20:raise RuntimeError('ONLINE_LOCK_REQUIRED')
        if identity['executor_hash']!=e.fingerprint(m):raise ValueError('EXECUTOR_CHANGED')
        if (d/'final_review.json').exists():return e.read(d/'final_review.json')
        if (d/'final_review_started.json').exists():raise RuntimeError('Interrupted evaluation requires reconciliation')
        # Read answers only below the lock check. Never feed these to the executor.
        for path,h in p['evaluator_sources'].items():
            if e.sha(e.ROOT/path)!=h:raise ValueError('EVALUATOR_HASH_CHANGED')
        manifest=e.read(e.BASE/'scoring_manifest.json')
        budget=e.ledger(d/'budget.jsonl',d.name,identity['executor_hash'])
        if budget.snapshot()['unknown_or_pending_requests']:raise RuntimeError('UNRESOLVED_REQUEST')
        evaluate=judge or (e.mock_judge if identity['mode']=='mock' else e.worker(budget,d))
        e.save(d/'final_review_started.json',dict(online_state_hash=e.fingerprint(state)))
        pairs=[]
        for i,row in enumerate(manifest['rows'],1):
            raw=e.read(e.ROOT/row['evaluator_ref']);tid=row['task_id']
            if isinstance(raw,dict):cases=raw[tid]['audit_cases']
            else:
                record=next(x for x in raw if x['task_id']==tid)
                cases=record.get('audit_cases',record.get('cases'))
            if len(cases)!=row['sealed_case_count']:raise ValueError('CASE_COUNT_CHANGED')
            results={}
            for arm in ('A','B'):
                key=f'{i:02}-{arm}';artifact=e.read(d/f'{key}.artifact.json')
                result=evaluate(tid,artifact['code'],cases)
                results[arm]=dict(state['branches'][key],sealed_pass=result['passed'])
                e.save(d/f'{key}.sealed.json',dict(role='sealed_offline_only',result=result))
            pairs.append(dict(task_id=tid,**pair_result(results['A'],results['B'],online_locked=True),
                output_similarity=e.compare(e.read(d/f'{i:02}-A.artifact.json')['code'],e.read(d/f'{i:02}-B.artifact.json')['code'])))
        out=dict(mode=identity['mode'],pairs=pairs,budget=budget.snapshot(),new_model_calls=0)
        e.save(d/'final_review.json',out);return out
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('run_dir');print(e.canonical(review(a.parse_args().run_dir)))
