"""Trusted container supervisor; only mounted candidate code runs in the child."""
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

def limits():
    resource.setrlimit(resource.RLIMIT_FSIZE,(262144,262144))
    resource.setrlimit(resource.RLIMIT_CPU,(10,10))

for line in sys.stdin:
    request=json.loads(line)
    started=time.monotonic()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            p=subprocess.run([sys.executable,'-B','/candidate.py'],stdout=out,stderr=err,
                timeout=request['timeout'],preexec_fn=limits,
                env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONPATH':'/skills','PYTHONDONTWRITEBYTECODE':'1','PYTHONHASHSEED':'0'})
            code=p.returncode;timeout=False
        except subprocess.TimeoutExpired:
            code=-1;timeout=True
        out.seek(0);err.seek(0)
        stdout=out.read(131072).decode(errors='replace');stderr=err.read(131072).decode(errors='replace')
    events=Path('/tmp/skill_events.jsonl')
    calls=[]
    if events.exists():
        try:calls=[json.loads(x) for x in events.read_text()[:262144].splitlines()]
        except (ValueError,UnicodeError):calls=[];code=-1;stderr+='\nFLOWEVO_CALL_LOG_ERROR: unreadable event stream'
    log_error='FLOWEVO_CALL_LOG_ERROR' in stderr or Path('/tmp/flowevo_call_log_error').exists()
    print(json.dumps(dict(status='CALL_LOG_ERROR' if log_error else 'TIME_LIMIT' if timeout else 'OK',returncode=code,stdout=stdout,stderr=stderr,
        timeout=timeout,passed=code==0 and not timeout,skill_events=calls,child_seconds=time.monotonic()-started)),flush=True)
