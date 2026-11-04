"""Explicit paid 200-task exploration/resume, using the existing stream runtime.

No independent Gate provider is installed: candidates remain Shadow. Unresolved
scoring semantics are quarantined before scoring, never converted into failures.
Running this command is an explicit request to send real DeepSeek requests.
"""
import argparse
import time
from pathlib import Path
from run_math_stream200 import (
    ROOT, DATA, PREP, WORKER, IMAGE, lines, read, save, sha, freeze_plan,
    StreamRuntime, WindowLearner, FrozenLinuxBackend, summarize,
)
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.model_api import configured_api_key

AUDIT = ROOT/'runs/math_stream200_provenance_gate_20261102_01'


class QuarantinedScorer:
    def __init__(self, inner, excluded):
        self.inner = inner
        self.excluded = set(excluded)
        self.events, self.controller, self._rows = inner.events, inner.controller, inner._rows

    def score(self, task, locked):
        if task.task_id not in self.excluded:
            return self.inner.score(task, locked)
        raw = {k: v for k, v in locked.items() if k != 'locked_sha256'}
        if fingerprint(raw) != locked.get('locked_sha256') or locked.get('task_id') != task.task_id:
            raise PermissionError('quarantine answer lock mismatch')
        if not any(r['kind'] == 'MATH_ANSWER_LOCKED' and r['payload'] == locked for r in self.controller.records()):
            raise PermissionError('quarantine requires durable answer lock')
        result = dict(status='UNVERIFIED', correct=None, credible_failure=False,
            reason='PREDECLARED_SCORING_SEMANTICS_QUARANTINE',
            episode_id=locked['episode_id'], task_id=task.task_id,
            locked_sha256=locked['locked_sha256'], scorer_version='math-stream-semantics-quarantine-v1',
            visibility='HOST_POST_TASK_ONLY', gold_exposed=False)
        old = [r['payload'] for r in self.events.records() if r['payload'].get('episode_id') == locked['episode_id']]
        if old:
            if old != [result]:
                raise PermissionError('quarantine score replay drift')
            return old[0]
        self.events.append('MATH_PRIVATE_SCORE', result, time.time())
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, default=ROOT/'runs/math_stream200_exploratory_20261102_01')
    parser.add_argument('--check-only', action='store_true', help='local preflight only; no model request')
    args = parser.parse_args()
    path = args.run_dir.resolve()
    protocol = read(DATA/'protocol.json')
    if sha(DATA/'protocol.json') != read(DATA/'freeze.json')['protocol_sha256']:
        raise PermissionError('original dataset protocol changed')
    if not all(sha(DATA/k) == v for k, v in protocol['files'].items()):
        raise PermissionError('original dataset changed')
    tasks = lines(DATA/'public/tasks.jsonl')
    if len(tasks) != 200:
        raise PermissionError('exact frozen200 required')
    private = lines(DATA/'private/scoring.jsonl')
    lineage = read(AUDIT/'provenance.json')
    excluded = sorted(r['task_id'] for r in read(AUDIT/'scoring_semantics_flags.json'))
    if not set(excluded) <= {t['task_id'] for t in tasks}:
        raise PermissionError('quarantine task mismatch')
    plan = freeze_plan(tasks, 20, 6, 'EXPLORATORY200_NO_INDEPENDENT_GATE_CLAIM')
    plan['sources'][str(Path(__file__).resolve().relative_to(ROOT))] = sha(__file__)
    plan.update(scoring_quarantine=excluded, lineage_sha256=sha(AUDIT/'provenance.json'),
        scoring_audit_sha256=sha(AUDIT/'scoring_semantics_flags.json'), independent_gate_provider='NONE_SHADOW_ONLY',
        interpretation='200 records, not200 independently verified originals; no cross-original benefit claim without reviewed Gate',
        paid_execution_requested_by='explicit invocation of run_math_stream200_exploratory.py')
    if (path/'execution_plan.json').exists():
        frozen = read(path/'execution_plan.json')
        if frozen != plan:
            raise PermissionError('frozen execution changed; do not resume with changed source/data/protocol')
    if not configured_api_key():
        raise PermissionError('configured DeepSeek credential missing; never print the key')
    backend = FrozenLinuxBackend(image=IMAGE, worker_script=WORKER)
    import subprocess
    subprocess.run(['docker', 'image', 'inspect', IMAGE], check=True, stdout=subprocess.DEVNULL)
    print('200 tasks; G/T/F/R;20-task windows; scoring quarantine:', len(excluded), flush=True)
    print('No Gate provider: all new operators remain Shadow. No automatic request retry.', flush=True)
    print('Run directory:', path, flush=True)
    if args.check_only:
        print('LOCAL_PREFLIGHT_OK; zero model API calls; no experiment state created', flush=True)
        return
    path.mkdir(parents=True, exist_ok=True)
    if not (path/'execution_plan.json').exists():
        save(path/'execution_plan.json', plan)
        save(path/'authorization.json', dict(scope='200-task exploration; existing per-channel hard ceilings',
            protocol_sha256=fingerprint(plan), real_api=True, independent_gate_authorized=False))
        save(path/'lineage.json', lineage)
    stream = StreamRuntime(path, plan, tasks, private, lineage, backend=backend,
        learner_factory=lambda s, arm: WindowLearner(s, arm))
    for state in stream.arms.values():
        state['scorer'] = QuarantinedScorer(state['scorer'], excluded)
    try:
        stream.run()
    except BaseException as exc:
        EvidenceStore(path/'stops.jsonl').append('STOP', dict(type=type(exc).__name__, reason=str(exc), no_resend=True), time.time())
        raise
    finally:
        summarize(path)


if __name__ == '__main__':
    main()
