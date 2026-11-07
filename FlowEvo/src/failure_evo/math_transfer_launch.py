"""Private DEV review binding and partitioned limits for the transfer launcher."""
import fcntl
import time
from pathlib import Path

from .contracts import fingerprint
from .evidence import EvidenceStore
from .math_stream import budget, read, sha
from .operator_contract import candidate_identity
from .run_health import assert_run_healthy

TRAIN_CAPS = dict(A=40,B=20,C=10,D=30)
PHASE_CAPS = dict(TRAIN=100,DEV=56,TEST=336)
TOKEN_UPPER = 73728
COST_UPPER = 88474


def build_dev_cases(manifest, tasks, references, review, parent, candidate, *, review_sha, references_sha):
    """Use an independently frozen host review. Only public task/parameters reach Worker."""
    if fingerprint(review)!=review_sha or fingerprint(references)!=references_sha:
        raise PermissionError('DEV review or reference changed')
    manifest_sha = manifest['manifest_sha256']
    if (fingerprint(manifest['rows'])!=manifest_sha or references['manifest_sha256']!=manifest_sha
            or review['manifest_sha256']!=manifest_sha or review['parent_version']!=candidate_identity(parent)
            or review['candidate_version']!=candidate_identity(candidate)):
        raise PermissionError('DEV review version binding mismatch')
    rows = [r for r in manifest['rows'] if r['split']=='DEV']
    if not (len(rows)==len(tasks)==len(references['rows'])==len(review['labels'])):
        raise PermissionError('DEV case coverage mismatch')
    cases = []
    for row, task, ref, label in zip(rows,tasks,references['rows'],review['labels']):
        if (len({row['task_id'],task['task_id'],ref['task_id'],label['task_id']})!=1
                or fingerprint(task['problem'])!=row['statement_hash']
                or ref['problem_sha256']!=row['statement_hash']
                or ref['reference_id']!=row['scoring_reference_id']):
            raise PermissionError('DEV case identity mismatch')
        if set(label)!={'task_id','supported','parameters','evidence_quotes','rationale'}:
            raise PermissionError('DEV review contains non-review fields')
        if (ref['status']!='REFERENCE_VERIFIED' or type(label['supported']) is not bool
                or not label['rationale'].strip() or not label['evidence_quotes']
                or any(not q or q not in task['problem'] for q in label['evidence_quotes'])
                or (label['supported'] and not isinstance(label['parameters'],dict))
                or (not label['supported'] and label['parameters'] is not None)):
            raise PermissionError('DEV reference, support or parameter mapping is unverified')
        cases.append(dict(proposal=dict(problem=task['problem']),review=dict(status='VERIFIED',
                          record=dict(supported=label['supported'], parameters=label['parameters'],
                                      answer=ref['answer'] if label['supported'] else None))))
    return cases


class TransferBudget:
    """Static phase/arm allocations. Each shard uses the original persistent budget."""
    def __init__(self, root, run_id, protocol_sha):
        self.root, self.run_id, self.protocol_sha = Path(root), run_id, protocol_sha
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.events = EvidenceStore(self.root/'allocations.jsonl')

    def allocate(self, path, phase, arm, calls):
        path = Path(path).resolve()
        key = str(path.relative_to(self.root.resolve()))
        if (phase not in PHASE_CAPS or type(calls) is not int or calls<1
                or (phase=='TRAIN' and arm not in TRAIN_CAPS)):
            raise ValueError('invalid budget allocation')
        value = dict(path=key,phase=phase,arm=arm,calls=calls)
        with (self.root/'allocations.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            rows = self.events.records()
            header = dict(run_id=self.run_id,protocol_sha=self.protocol_sha)
            if not rows:
                rows=[self.events.append('TRANSFER_BUDGET_OPENED',header,time.time())]
            if rows[0]['kind']!='TRANSFER_BUDGET_OPENED' or rows[0]['payload']!=header:
                raise PermissionError('budget identity changed')
            allocated = [r['payload'] for r in rows[1:]]
            prior = [r for r in allocated if r['path']==key]
            if prior and prior!=[value]:
                raise PermissionError('budget shard changed')
            if not prior:
                totals = sum(r['calls'] for r in allocated if r['phase']==phase)
                arm_total = sum(r['calls'] for r in allocated if r['phase']==phase and r['arm']==arm)
                if totals+calls>PHASE_CAPS[phase] or (phase=='TRAIN' and arm_total+calls>TRAIN_CAPS[arm]):
                    from .runtime import BudgetExhausted
                    raise BudgetExhausted('transfer phase or arm allocation exhausted')
                self.events.append('TRANSFER_BUDGET_ALLOCATED',value,time.time())
            return budget(path,self.run_id+':'+key,self.protocol_sha,calls=calls)

    def health(self):
        for row in self.events.records():
            if row['kind']!='TRANSFER_BUDGET_ALLOCATED':
                continue
            r = row['payload']
            path = self.root/r['path']
            if not path.exists():
                continue
            account = budget(path,self.run_id+':'+r['path'],self.protocol_sha,calls=r['calls'])
            provider = EvidenceStore(path.parent/'provider.jsonl')
            from types import SimpleNamespace
            assert_run_healthy(budgets=[account],providers=[SimpleNamespace(events=provider)])


def load_launch(config_path, repo, phase):
    config_path = Path(config_path)
    config = read(config_path)
    if config['version']!='math-transfer-launch-v1' or config['model']!='deepseek-flash':
        raise PermissionError('launch protocol or model mismatch')
    if (config['phase_call_caps']!=PHASE_CAPS or config['train_arm_call_caps']!=TRAIN_CAPS
            or config['total_token_cap']!=sum(PHASE_CAPS.values())*TOKEN_UPPER
            or config['total_cost_microusd']!=sum(PHASE_CAPS.values())*COST_UPPER):
        raise PermissionError('launch budget drift')
    required = {
        'TRAIN': {'frozen_splits/data_split_manifest.json','frozen_splits/train_public_failures.json'},
        'DEV': {'frozen_splits/data_split_manifest.json','frozen_splits/dev/tasks.json',
                'frozen_splits/dev/scoring.private.json','dev_review/references.private.json'},
        'TEST': {'frozen_splits/data_split_manifest.json','frozen_splits/test/tasks.json',
                 'frozen_splits/test/scoring.private.json'},
    }[phase]
    private = {name:config['private_sha256'][name] for name in required}
    for paths,root in ((config['source_sha256'],Path(repo)),(private,config_path.parent)):
        for name,digest in paths.items():
            if sha(root/name)!=digest:
                raise PermissionError('launch file drift: '+name)
    return config
