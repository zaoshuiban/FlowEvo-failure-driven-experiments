"""Freeze TRAIN, DEV and TEST in a new private directory. Never sends API requests."""
import argparse
import json
from pathlib import Path

from code_math.no_gold import PublicMathTask
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_skill_transfer import freeze_manifest, training_projection
from failure_evo.math_stream import read, sha


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def bind(path, data):
    path.write_text(canonical(data)+'\n')
    path.chmod(0o400)


def freeze(history_run, history_data, candidates, out):
    # Full record integrity is checked before picking the first ten verified failures.
    raw=EvidenceStore(history_run/'F/cumulative/raw.jsonl').records()
    states=EvidenceStore(history_run/'F/task_state.jsonl').records()
    controls=EvidenceStore(history_run/'F/controller.jsonl').records()
    grades=EvidenceStore(history_run/'F/scores.jsonl').records()
    data=read(history_data/'freeze.json')
    pool=read(candidates/'freeze.json')
    for root,manifest in ((history_data,data),(candidates,pool)):
        if any(sha(root/name)!=digest for name,digest in manifest['files'].items()):
            raise PermissionError('dataset input drift')
    if read(history_run/'execution_plan.json')['tasks_sha256']!=data['tasks_sha256']:
        raise PermissionError('TRAIN does not match source run')
    recorded_tasks={r['task_id']:r for r in lines(history_data/'public/tasks.jsonl')}
    train_refs={r['task_id']:r for r in lines(history_data/'private/scoring.jsonl')}
    scores={r['payload']['task_id']:r['payload']['verdict'] for r in states if r['kind']=='PRIVATE_SCORED'}
    locks={r['payload']['task_id']:r['payload']['lock'] for r in states if r['kind']=='ANSWER_LOCKED'}
    durable={r['payload']['locked_sha256']:r['payload'] for r in controls if r['kind']=='MATH_ANSWER_LOCKED'}
    grades=[r['payload'] for r in grades if r['kind']=='MATH_PRIVATE_SCORE']
    train=[]
    for event in raw:
        f=event['payload']
        if event['kind']!='RAW_EVIDENCE' or f.get('correct') is not False:
            continue
        tid=f['task']['task_id']
        v=scores[tid]
        lock=locks[tid]
        if (recorded_tasks[tid]!=f['task'] or v['status']!='CONFIRMED_WRONG' or v not in grades
                or lock!=durable[f['locked_sha256']] or v['locked_sha256']!=lock['locked_sha256']
                or fingerprint({k:x for k,x in lock.items() if k!='locked_sha256'})!=lock['locked_sha256']
                or f['final_output']!=lock['final_output']
                or f['trajectory']!=[{k:r[k] for k in ('text','finish_reason','usage','model')} for r in lock['responses']]
                or any(r.get('origin')!='DEEPSEEK' for r in lock['responses'])):
            raise PermissionError('untrusted TRAIN outcome')
        train.append(f)
    train=sorted(train,key=lambda f:f['sequence'])[:10]
    if len(train)!=10:
        raise ValueError('ten real failures required')
    candidate_rows=lines(candidates/'public/tasks.jsonl')
    refs={r['task_id']:r for r in lines(candidates/'private/scoring.jsonl')}
    if len(candidate_rows)!=56:
        raise ValueError('expected eight DEV and forty-eight TEST tasks')
    records=[]
    tasks=[]
    def add(task,ref,source,split,source_run,exposure):
        t=PublicMathTask.parse(task)
        row=next(x for x in source['order'] if x['task_id']==t.task_id)
        tasks.append(t)
        records.append(dict(task_id=t.task_id,dataset=source['dataset'],dataset_revision=source['revision'],
                            source_row=row['source_row'],statement_hash=fingerprint(t.problem),split=split,
                            source_run=source_run,problem_family='UNKNOWN',exposure_status=exposure,
                            scoring_reference_id=fingerprint(ref),grading_method='math-stream-strict-v1'))
    for f in train:
        add(f['task'],train_refs[f['task']['task_id']],data,'TRAIN',history_run.name,'RECORDED_TRAIN_FAILURE')
    for i,task in enumerate(candidate_rows):
        add(task,refs[task['task_id']],pool,'DEV' if i<8 else 'TEST',None,'NO_MATCH_IN_LOCAL_EXPOSURE_AUDIT')
    manifest=freeze_manifest(records,tasks)
    projections=[training_projection(f,manifest) for f in train]
    out.mkdir(mode=0o700)
    bind(out/'data_split_manifest.json',manifest)
    bind(out/'train_public_failures.json',projections)
    for role,subset in [('DEV',candidate_rows[:8]),('TEST',candidate_rows[8:])]:
        directory=out/role.lower()
        directory.mkdir(mode=0o700)
        bind(directory/'tasks.json',subset)
        bind(directory/'scoring.private.json',[refs[t['task_id']] for t in subset])
    bind(out/'split_evidence.json',dict(
        train_failures=len(train),dev_tasks=8,test_tasks=48,source_run=str(history_run),
        evidence_journals={name:sha(history_run/name) for name in ('F/task_state.jsonl','F/controller.jsonl','F/scores.jsonl','F/cumulative/raw.jsonl')},
        candidate_source_sha256=sha(candidates/'freeze.json'),exposure_audit=pool['local_history_texts'],
        test_negative_cases='PENDING_SCOPE_LABELS_BEFORE_TEST',
        files={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}))
    print(manifest['manifest_sha256'])


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ('history-run','history-data','candidates','output'):
        p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args()
    freeze(a.history_run,a.history_data,a.candidates,a.output)
