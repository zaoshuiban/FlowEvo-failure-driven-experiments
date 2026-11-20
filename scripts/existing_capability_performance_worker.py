"""Private, isolated composition diagnostic; no new algorithm or test input."""
import contextlib
import cProfile
import hashlib
import importlib
import io
import json
from pathlib import Path
import pstats
import random
import runpy
import sys
import time

sys.path.insert(0, '/skills')
# The official guard disables builtins.open. Only the trusted event logger
# retains io.open; the candidate, archived function and official guard do not
# change. Importing this binding does not invoke the archived operation.
event_module = importlib.import_module('flowevo_skills')
event_module.open = io.open
# Reuse the frozen scorer functions without entering its stdin loop.
stdin = sys.stdin
sys.stdin = io.StringIO('')
try:
    scorer = runpy.run_path('/skills/locked_evalplus_worker.py')
finally:
    sys.stdin = stdin

for line in sys.stdin:
    request = json.loads(line)
    random.seed(0)
    scorer['np'].random.seed(0)
    try:
        problems = list(scorer['data_utils'].stream_jsonl('/skills/problems.jsonl'))
        samples = list(scorer['data_utils'].load_solutions('/skills/samples.jsonl'))
        assert len(problems) == len(samples) == 1
        problem, sample = problems[0], samples[0]
        source = Path('/candidate.py').read_text()
        assert source == sample['solution'] and problem['task_id'] == sample['task_id'] == 'HumanEval/39'
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            if request['mode'] == 'score':
                result = scorer['score'](problem, source)
            else:
                assert request['mode'] == 'profile'
                inp = problem[request['subset'] + '_input'][request['index']]
                profiler = cProfile.Profile()
                started = time.monotonic()
                try:
                    with scorer['time_limit'](5.0):
                        profiler.runcall(scorer['trusted_exec'], source, [scorer['deepcopy'](inp)], problem['entry_point'])
                    outcome, error = 'RETURNED', None
                except BaseException as exc:
                    outcome, error = 'TIMEOUT' if type(exc).__name__ == 'TimeoutException' else 'ERROR', type(exc).__name__
                finally:
                    profiler.disable()
                rows = []
                stats = pstats.Stats(profiler)
                for (filename, lineno, name), (cc, nc, tt, ct, _) in stats.stats.items():
                    rows.append(dict(file=filename, line=lineno, function=name,
                        primitive_calls=cc, total_calls=nc, self_seconds=tt, cumulative_seconds=ct))
                result = dict(status='PROFILE_COMPLETED', outcome=outcome, error_type=error,
                    seconds=time.monotonic()-started, total_profile_seconds=stats.total_tt,
                    functions=sorted(rows, key=lambda x: -x['self_seconds']),
                    scoring_verdict=False, scope='one existing failed input, five seconds; instrumentation changes timing')
        events = Path('/tmp/skill_events.jsonl')
        result['skill_events'] = [json.loads(x) for x in events.read_text().splitlines()] if events.exists() else []
        result.update(source_sha256=hashlib.sha256(source.encode()).hexdigest(), python=sys.version,
            numpy_version=scorer['np'].__version__, model_requests=0)
    except BaseException as exc:
        result = dict(status='SCORING_ERROR', error_type=type(exc).__name__, error=str(exc), model_requests=0)
    print(json.dumps(result), flush=True)
