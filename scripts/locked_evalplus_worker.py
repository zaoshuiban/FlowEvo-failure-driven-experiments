"""Private scoring supervisor inside the existing no-network Docker boundary.

Uses unmodified EvalPlus data helpers, reference execution and correctness API.
No code generation provider, sanitizer, model client or solver is imported.
"""
import contextlib
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import random
import sys
import time

sys.path.insert(0, '/opt/evalplus')
import numpy as np
from evalplus.eval import untrusted_check
from evalplus.eval.utils import time_limit
from evalplus.gen.util import trusted_exec

# Load the official file reader without importing the optional datasets/model
# stacks in evalplus.data.__init__.py. Its code is not changed.
spec = importlib.util.spec_from_file_location('official_data_utils', '/opt/evalplus/evalplus/data/utils.py')
data_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_utils)


def sha(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def balanced(value):
    depth = 0
    for c in value:
        depth += 1 if c == '(' else -1
        if depth < 0:
            return False
    return depth == 0


def common_scope(problem, args):
    tid = problem['task_id']
    if tid == 'HumanEval/20':
        a = sorted(args[0])
        if any(not math.isfinite(x) for x in a):
            return False, 'nonfinite_numeric_semantics'
        distances = [b-a for a,b in zip(a,a[1:])]
        best = min(distances)
        pairs = {(a[i],a[i+1]) for i,d in enumerate(distances) if d == best}
        if len(pairs) != 1:
            return False, 'multiple_distinct_minimum_pairs_unspecified_tie_break'
    if tid == 'HumanEval/6' and not all(balanced(x) for x in args[0].split(' ') if x):
        return False, 'space_delimited_group_not_individually_balanced'
    return True, 'within_reviewed_common_scope'


def contract_check(problems):
    result = []
    for p in problems:
        # This builds only the official input predicate, not an answer program.
        code = p['prompt'] + p['contract'] + '\n    return True\n'
        ns = {}
        exec(code, ns)
        fn = ns[p['entry_point']]
        row = dict(task_id=p['task_id'], subsets={})
        for subset in ('base', 'plus'):
            details = []
            for i, inp in enumerate(p[subset+'_input']):
                try:
                    with time_limit(2):
                        fn(*deepcopy(inp))
                    common, reason = common_scope(p, inp)
                    details.append(dict(index=i, official_contract=True, common_scope=common, reason=reason))
                except BaseException as exc:
                    details.append(dict(index=i, official_contract=False, common_scope=False,
                                        reason='contract_'+type(exc).__name__))
            excluded={}
            for item in details:
                if not item['common_scope']:
                    excluded.setdefault(item['reason'],[]).append(item['index'])
            row['subsets'][subset] = dict(count=len(details),
                official_contract_invalid=[x['index'] for x in details if not x['official_contract']],
                common_scope_exclusions=excluded)
        result.append(row)
    return dict(status='CONTRACTS_CHECKED',tasks=result)


def score(problem, solution):
    result = dict(status='COMPLETED',task_id=problem['task_id'],source_sha256=sha(solution),subsets={})
    for subset in ('base','plus'):
        inputs = problem[subset+'_input']
        reference = problem['prompt'] + problem['canonical_solution']
        expected, reference_times = trusted_exec(reference, inputs, problem['entry_point'],record_time=True)
        started = time.monotonic()
        status, details = untrusted_check('humaneval',solution,deepcopy(inputs),problem['entry_point'],
            expected=expected,atol=problem['atol'],ref_time=reference_times,
            fast_check=False,min_time_limit=5.0,gt_time_limit_factor=4.0)
        result['subsets'][subset] = dict(status=status,planned_count=len(inputs),executed_count=len(details),
            passed_count=sum(details),failed_indices=[i for i,x in enumerate(details) if not x],
            details=list(map(bool,details)),seconds=time.monotonic()-started,
            reference_seconds=sum(reference_times),reference_max_seconds=max(reference_times,default=0))
    return result


def replay(problem, solution, request):
    """One fixed failing-case replay for diagnosis, not a replacement score.

    Original code bytes, entry, input and reference are unchanged. The primary
    verdict remains the official untrusted_check result. Actual and expected
    values below stay in a private receipt; no compiler consumes this object.
    """
    inp = problem[request['subset']+'_input'][request['index']]
    expected, rt = trusted_exec(problem['prompt']+problem['canonical_solution'],[inp],problem['entry_point'],record_time=True)
    limit = max(5.0,4.0*rt[0])
    started = time.monotonic()
    result = dict(status='REPLAY_COMPLETED',task_id=problem['task_id'],source_sha256=sha(solution),
        subset=request['subset'],index=request['index'],limit_seconds=limit,
        expected_repr=repr(expected[0]),expected_type=type(expected[0]).__name__)
    try:
        with time_limit(limit):
            actual = trusted_exec(solution,[inp],problem['entry_point'])[0]
        # Diagnostic equality only. Float discrepancy is reviewed against the
        # official tolerance and never silently converted to an exact failure.
        result.update(outcome='RETURNED',actual_repr=repr(actual),actual_type=type(actual).__name__,
                      exact_equal=bool(actual==expected[0]))
    except BaseException as exc:
        result.update(outcome='TIMEOUT' if type(exc).__name__=='TimeoutException' else 'RUNTIME_ERROR',
                      error_type=type(exc).__name__)
    result['seconds']=time.monotonic()-started
    return result


for line in sys.stdin:
    request=json.loads(line)
    random.seed(0);np.random.seed(0)
    try:
        problems=list(data_utils.stream_jsonl('/skills/problems.jsonl'))
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            if request['mode']=='contracts':
                result=contract_check(problems)
            else:
                samples=list(data_utils.load_solutions('/skills/samples.jsonl'))
                assert len(samples)==len(problems)==1
                sample=samples[0];problem=problems[0]
                assert sample['task_id']==problem['task_id']
                assert 'solution' in sample and 'completion' not in sample
                assert sample['solution'].encode('utf-8')==Path('/candidate.py').read_bytes()
                result=score(problem,sample['solution']) if request['mode']=='score' else replay(problem,sample['solution'],request)
        assert not any(n.startswith(('evalplus.codegen','evalplus.provider','openai','anthropic','transformers')) for n in sys.modules)
        result.update(python=sys.version,model_requests=0,official_scorer_commit='e5d0ed0bab96280b60b637ec7f15b5e4841b0cb2')
    except BaseException as exc:
        result=dict(status='SCORING_ERROR',error_type=type(exc).__name__,error=str(exc),model_requests=0)
    print(json.dumps(result),flush=True)
