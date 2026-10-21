"""Zero-API S1.1 smoke checks, fixed-response replay and immutable archive audit."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'FlowEvo/src'))
from failure_evo import (Budget, Controller, Fingerprint, FailureEvidenceStore,
    FailureOperatorRegistry, FailureLearningPlugin, baseline_manifest)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay():
    archive = ROOT / 'experiments/flowevo_taco_lcb_20261019/e3_s1_20261020'
    manifest = read(archive / 'review_manifest.json')
    rows = []
    with tempfile.TemporaryDirectory(prefix='flowevo-v2-replay-') as temporary:
        for task in manifest['tasks']:
            tid = task['task_id']
            source = archive / 'source/tasks' / (tid + '.json')
            if not source.exists():
                raise RuntimeError('Restore archived tasks first: python3 scripts/restore_datasets.py')
            raw = read(source)
            statuses, counts, programs = [], [], []
            for attempt in task['historical_programs']:
                base = read(archive / 'verdicts' / tid / (attempt['stage'] + '.json'))
                stress_path = archive / 'stress_verdicts_v2' / tid / (attempt['stage'] + '.json')
                extra = read(stress_path) if stress_path.exists() else None
                verdict = extra if base['passed'] and extra is not None and not extra['passed'] else base
                statuses.append(verdict['status'])
                counts.append(verdict['tests_run'])
                programs.append((archive / attempt['source_path']).read_text())
            expected = next((i for i, s in enumerate(statuses) if s == 'PASS'), None)
            runs = []
            for mode in ('disabled', 'shadow'):
                position = [-1]
                requests = []
                def provider(request):
                    position[0] += 1
                    requests.append(json.loads(json.dumps(request)))
                    return dict(code=programs[position[0]], model='fixture', usage={'total_tokens': 0})
                def evaluate(task_view, code):
                    i = position[0]
                    return dict(visibility='public', status='PUBLIC_PASS' if statuses[i] == 'PASS' else statuses[i],
                                tests_run=counts[i], tests_passed=counts[i] if statuses[i] == 'PASS' else 0)
                state = Path(temporary) / tid / mode
                evidence = FailureEvidenceStore(state / 'events.jsonl')
                registry = FailureOperatorRegistry(state / 'registry.jsonl', evidence)
                fp = Fingerprint('archived-stage-adapter', 'saved-public-suite', 'fixture', 'pinned', 's1.1-replay')
                plugin = FailureLearningPlugin(registry, evidence, fp, stream_id='replay', enabled=mode == 'shadow', synthetic=True)
                out = Controller(provider, evaluate, fp, plugin=plugin, clock=lambda: 1).solve(raw, Budget(max_tokens=1000000, clock=lambda: 0))
                expected_stage = task['historical_programs'][expected]['stage'] if expected is not None else None
                assert (out['selected']['stage'] if out['selected'] else None) == expected_stage, tid
                runs.append((requests, out))
            assert runs[0][0] == runs[1][0], tid
            for key in ('selected', 'status', 'last_candidate', 'retained_candidates', 'budget', 'events'):
                assert runs[0][1][key] == runs[1][1][key], (tid, key)
            rows.append(dict(task_id=tid, checked_stages=len(runs[0][0]), status='PARITY_PASS'))
    return dict(tasks=len(rows), fixture_provider_replays=sum(r['checked_stages'] for r in rows), rows=rows,
                limitation='Saved responses/verdicts only; no fresh generation, sandbox execution, or causal performance claim')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default=str(ROOT / 'smoke-results/v2'))
    args = parser.parse_args()
    output = Path(args.output_dir).resolve()
    if output == ROOT / 'experiments' or ROOT / 'experiments' in output.parents:
        parser.error('write smoke results outside frozen experiments')
    output.mkdir(parents=True, exist_ok=True)
    check = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT / 'FlowEvo/tests'),
                            '-p', 'test_failure_evo*.py', '-v'], capture_output=True, text=True)
    (output / 'unittest.log').write_text(check.stdout + check.stderr)
    if check.returncode:
        raise RuntimeError('unit tests failed; see unittest.log')
    parity = replay()
    archive = ROOT / 'experiments/flowevo_taco_lcb_20261019/e3_s1_20261020'
    pins = read(archive / 'artifact_hashes.json')
    mismatches = [name for name, digest in pins.items() if not (archive / name).is_file() or sha(archive / name) != digest]
    assert not mismatches, mismatches
    fp = Fingerprint('public-feedback-native-adapter', 'host-audited-public-checks', 'not-configured', 'not-configured', 'ETOI-v2-S1.1')
    manifest = baseline_manifest(ROOT, fp)
    (output / 'baseline_manifest.json').write_text(json.dumps(manifest, indent=2))
    report = dict(status='PASS', new_model_calls=0, python=sys.version,
                  replay=parity, frozen_artifacts_checked=len(pins), frozen_artifact_mismatches=mismatches,
                  scope='S1.1 offline adapter acceptance; server/API/Linux sandbox not validated')
    (output / 'summary.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='replay'}, indent=2))
    print('Fixed-response parity:', parity['tasks'], 'tasks;', parity['fixture_provider_replays'], 'provider responses per mode')


if __name__ == '__main__':
    main()
