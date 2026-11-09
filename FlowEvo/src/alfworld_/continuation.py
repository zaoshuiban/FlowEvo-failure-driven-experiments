"""Versioned isolation of metered, received ALFWorld delivery truncation."""
from pathlib import Path
import time

from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, save, sha
from failure_evo.run_health import assert_run_healthy, trusted_usage

VERSION='alfworld-settled-length-isolation-v1'
RUNNER='scripts/run_alfworld_audited_baseline.py'
MODULE='FlowEvo/src/alfworld_/continuation.py'


def truncation_receipt(root, account, task_id):
    assert_run_healthy(budgets=[account])
    records=EvidenceStore(root/'requests.jsonl').records()
    raw=[r for r in records if r['kind']=='RAW_RESPONSE' and r['payload']['request_id'].startswith(task_id+'/')]
    if not raw:
        raise PermissionError('no received response for task')
    last=raw[-1]
    p=last['payload']
    response=p['response']
    choices=response.get('choices',[])
    state=account.request_state(p['request_id'])
    if (len(choices)!=1 or choices[0].get('finish_reason')!='length'
            or response.get('model')!='deepseek-flash' or not trusted_usage(response)
            or not state or state['status']!='settled'
            or any(r['kind']=='SEND_UNKNOWN' for r in records)):
        raise PermissionError('only received metered settled length may be isolated')
    if any(r['kind']=='ACTION_RESPONSE' and r['payload']['request_id']==p['request_id'] for r in records):
        raise PermissionError('request already used as a valid action')
    return dict(request_id=p['request_id'],raw_record_hash=last['record_hash'],
                response_sha256=fingerprint(response),reason='METERED_LENGTH',
                status='INFRASTRUCTURE_OR_DELIVERY_ERROR')


def prepare(root, repo, account):
    cfg=read(root/'protocol.json')
    old_stop=read(root/'STOP.json')
    receipt=truncation_receipt(root,account,old_stop['task_id'])
    for name,digest in cfg['source_sha256'].items():
        target=repo/name
        if name==RUNNER:
            snapshot=root/'source_before_continuation'/name
            if not snapshot.is_file() or sha(snapshot)!=digest:
                raise PermissionError('original runner snapshot required')
        elif sha(target)!=digest:
            raise PermissionError('unrelated source changed: '+name)
    sources={name:sha(repo/name) for name in [*cfg['source_sha256'],MODULE]}
    frozen=dict(version=VERSION,protocol_sha256=fingerprint(cfg),source_sha256=sources,
                policy='ISOLATE_METERED_LENGTH_CONTINUE;UNKNOWN_GLOBAL_STOP',
                original_stop_sha256=fingerprint(old_stop),initial_truncation=receipt)
    path=root/'continuation_delivery_v1.json'
    if path.exists():
        if read(path)!=frozen:
            raise PermissionError('continuation already frozen with different evidence')
    else:
        save(root/'STOP_before_continuation.json',old_stop)
        save(path,frozen)
        path.chmod(0o400)
    return path


def validate(root,repo,path,cfg):
    overlay=read(path)
    if (overlay['version']!=VERSION or overlay['protocol_sha256']!=fingerprint(cfg)
            or overlay['policy']!='ISOLATE_METERED_LENGTH_CONTINUE;UNKNOWN_GLOBAL_STOP'
            or set(overlay['source_sha256'])!=set(cfg['source_sha256'])|{MODULE}
            or fingerprint(read(root/'STOP_before_continuation.json'))!=overlay['original_stop_sha256']):
        raise PermissionError('continuation identity mismatch')
    for name,digest in overlay['source_sha256'].items():
        if sha(repo/name)!=digest:
            raise PermissionError('continuation source changed: '+name)
    return overlay
