"""Offline acceptance entry; no API client, secret access, or automatic compilation."""
import argparse
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'src'))
from failure_evo import (Controller, Budget, Fingerprint, FailureEvidenceStore,
    FailureOperatorRegistry, FailureLearningPlugin, CompileQueue, LearningLoop)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--v2', action='store_true', help='Enable zero-API S1.1 observation/hooks')
    parser.add_argument('--state-dir', help='Separate per-run evidence/registry/queue directory')
    args = parser.parse_args()
    if args.v2 and not args.state_dir:
        parser.error('--v2 requires --state-dir')
    fixture = json.loads(pathlib.Path(args.fixture).read_text())
    responses, checks = iter(fixture['responses']), iter(fixture['public_checks'])
    context = Fingerprint(**fixture['fingerprint'])
    plugin = None
    if args.v2:
        state = pathlib.Path(args.state_dir)
        evidence = FailureEvidenceStore(state / 'failure_events.jsonl')
        registry = FailureOperatorRegistry(state / 'failure_registry.jsonl', evidence)
        plugin = FailureLearningPlugin(registry, evidence, context,
            stream_id=fixture.get('stream_id', 'fixture-stream'), synthetic=True)
    controller = Controller(lambda request: next(responses), lambda task, code: next(checks),
        context, max_output=fixture.get('max_output', 32768), plugin=plugin)
    result = controller.solve(fixture['task'], Budget(**fixture.get('budget', {})))
    if args.v2:
        loop = LearningLoop(CompileQueue(state / 'compile_queue.jsonl'), evidence,
                            plugin.stream_id, state / 'learning.jsonl')
        result['pending_compile_jobs'] = list(loop.pending(__import__('time').time()))
        result['source_mode'] = 'synthetic_engineering_fixture'
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(result['status'], result['budget'])


if __name__ == '__main__':
    main()
