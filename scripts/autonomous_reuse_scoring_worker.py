"""Private pinned EvalPlus adapter and one trusted-logger regression."""
import contextlib
import importlib
import io
import json
from pathlib import Path
import random
import runpy
import sys
sys.path.insert(0,'/skills')
stdin=sys.stdin;sys.stdin=io.StringIO('')
try: scorer=runpy.run_path('/skills/locked_evalplus_worker.py')
finally:sys.stdin=stdin

for line in sys.stdin:
    request=json.loads(line);random.seed(0);scorer['np'].random.seed(0)
    try:
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            if request['mode']=='contracts':
                result=scorer['contract_check'](list(scorer['data_utils'].stream_jsonl('/skills/problems.jsonl')))
            elif request['mode']=='logger_regression':
                code=Path('/candidate.py').read_text()
                def check(source):
                    return scorer['untrusted_check']('humaneval',source,[[101],[6]],'logger_regression',
                        expected=[True,False],atol=0,ref_time=[0,0],fast_check=False,min_time_limit=5,gt_time_limit_factor=4)
                status,details=check(code)
                assert status=='pass' and all(details)
                # Same public inputs; controlled trusted-log failure, not an algorithm test.
                broken=code.replace('def logger_regression(n):',"import flowevo_skills\nflowevo_skills.EVENTS='/candidate.py'\ndef logger_regression(n):")
                bad,_=check(broken)
                assert bad=='fail' and Path('/tmp/flowevo_call_log_error').exists()
                result=dict(status='REGRESSION_PASS',official_guard_left_enabled=True,
                    normal_calls_pass=True,log_failure_is_engineering_error=True,task_score=False)
            else:
                assert request['mode']=='score'
                problems=list(scorer['data_utils'].stream_jsonl('/skills/problems.jsonl'))
                assert len(problems)==1
                # Private evaluation may call a helper thousands of times. Retain
                # bounded parameter evidence without making log volume a task failure.
                logger=importlib.import_module('flowevo_skills');original_event=logger._event
                count=[0]
                def bounded_event(name,event,**extra):
                    count[0]+=1
                    if count[0]<=128:original_event(name,event,**extra)
                    elif count[0]==129:original_event(name,'logging_truncated')
                logger._event=bounded_event
                result=scorer['score'](problems[0],Path('/candidate.py').read_text())
                if Path('/tmp/flowevo_call_log_error').exists():result['status']='CALL_LOG_ERROR'
        events=Path('/tmp/skill_events.jsonl')
        result['skill_events']=[json.loads(x) for x in events.read_text().splitlines()] if events.exists() else []
        result['model_requests']=0
    except BaseException as exc:
        result=dict(status='SCORING_ERROR',error_type=type(exc).__name__,error=str(exc),model_requests=0)
    print(json.dumps(result),flush=True)
