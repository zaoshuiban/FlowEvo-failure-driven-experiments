"""Candidate-only namespace. Receives inputs, never expected outputs or verdicts."""
import contextlib
import io
import json
import resource
import signal
import subprocess
import sys
import time
import traceback
import os
import math, collections, itertools, functools, heapq, bisect, random
import tempfile

resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
wire_in, wire_out = sys.stdin, sys.stdout
LIMIT = 16 * 1024**2


class CaseTimeout(Exception):
    pass


def timeout(*_):
    raise CaseTimeout("candidate time limit")


signal.signal(signal.SIGALRM, timeout)
namespace, entry = None, None
program = None


def capture():
    return io.TextIOWrapper(io.BytesIO(), encoding="utf-8", write_through=True)


def run(request):
    global namespace, entry
    start = time.monotonic()
    seconds = request["timeout"]
    if request["mode"] == "stdio":
        # Fork a clean process with real OS stdin/stdout. Compile once, execute
        # afresh per case; no function wrapping or fragile StringIO mocks.
        with tempfile.TemporaryFile() as inp, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            inp.write(request["input"].encode()); inp.seek(0)
            pid = os.fork()
            if pid == 0:
                try:
                    os.setsid()
                    os.dup2(inp.fileno(), 0); os.dup2(out.fileno(), 1); os.dup2(err.fileno(), 2)
                    sys.stdin = os.fdopen(os.dup(0), "r", encoding="utf-8")
                    sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8")
                    sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8")
                    sys.argv = ["/candidate.py"]
                    ns = {"__name__": "__main__", "__file__": "/candidate.py"}
                    rc = 0
                    try:
                        exec(program, ns)
                    except SystemExit as exc:
                        rc = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
                    except BaseException:
                        traceback.print_exc(); rc = 1
                    sys.stdout.flush(); sys.stderr.flush()
                    os._exit(rc if 0 <= rc <= 255 else 1)
                except BaseException:
                    os._exit(1)
            expired = False
            while True:
                done, status = os.waitpid(pid, os.WNOHANG)
                if done:
                    break
                if time.monotonic() - start > seconds:
                    expired = True
                    try: os.killpg(pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                    os.waitpid(pid, 0)
                    break
                time.sleep(0.001)
            if expired:
                return {"status": "TIME_LIMIT", "seconds": time.monotonic() - start}
            out.seek(0); err.seek(0)
            output = out.read(LIMIT + 1); errors = err.read(16000)
            rc = os.waitstatus_to_exitcode(status)
            return {"status": "OUTPUT_LIMIT" if len(output) > LIMIT else ("OK" if rc == 0 else "RUNTIME_ERROR"),
                    "output": output[:LIMIT].decode("utf-8", errors="replace"),
                    "stderr": errors.decode("utf-8", errors="replace"), "exit_code": rc,
                    "seconds": time.monotonic() - start}
    stdout, stderr = capture(), capture()
    try:
        signal.setitimer(signal.ITIMER_REAL, seconds)
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            if namespace is None:
                namespace = {"__name__": "candidate"}
                # Explicit function-environment compatibility prelude. No answers/tests.
                exec("from typing import *\nimport math, collections, itertools, functools, heapq, bisect\n"
                     "from collections import Counter, defaultdict, deque\n"
                     "from functools import lru_cache\n", namespace)
                try:
                    source = open("/candidate.py", encoding="utf-8").read()
                    compiled = compile(source, "/candidate.py", "exec")
                except SyntaxError as exc:
                    return {"status": "COMPILE_ERROR", "error": str(exc)}
                exec(compiled, namespace)
                owner = namespace["Solution"]() if "Solution" in namespace else namespace
                entry = getattr(owner, request["function"]) if not isinstance(owner, dict) else owner[request["function"]]
            result = entry(*request["args"])
        # Tuple -> array is declared compatibility for JSON-serialized function returns.
        encoded = json.dumps(result, allow_nan=False)
        if len(encoded) > LIMIT:
            return {"status": "OUTPUT_LIMIT"}
        return {"status": "OK", "value": json.loads(encoded), "seconds": time.monotonic() - start}
    except CaseTimeout:
        return {"status": "TIME_LIMIT", "seconds": time.monotonic() - start}
    except BaseException as exc:
        return {"status": "RUNTIME_ERROR", "error": type(exc).__name__ + ": " + str(exc),
                "traceback": traceback.format_exc()[-8000:], "seconds": time.monotonic() - start}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


for line in wire_in:
    try:
        request = json.loads(line)
        if request["mode"] == "compile_stdio":
            try:
                program = compile(open("/candidate.py", encoding="utf-8").read(), "/candidate.py", "exec")
                response = {"status": "OK"}
            except SyntaxError as exc:
                response = {"status": "COMPILE_ERROR", "error": str(exc)}
        else:
            response = run(request)
        wire_out.write(json.dumps(response, ensure_ascii=True, allow_nan=False) + "\n")
        wire_out.flush()
    except BaseException as exc:
        wire_out.write(json.dumps({"status": "WORKER_ERROR", "error": repr(exc)}) + "\n")
        wire_out.flush()
