"""Generate compiler-facing documentation from trusted host code and projections."""
import ast
import hashlib
import inspect
from pathlib import Path
import textwrap
from .contracts import PublicTaskView, PublicFeedback
from .plugin import FailureLearningPlugin


def _dict_fields(method, target):
    tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
    values = [n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == target for t in n.targets)]
    if len(values) != 1 or not isinstance(values[0], ast.Call) or not isinstance(values[0].func, ast.Name) or values[0].func.id != 'dict':
        raise ValueError('host payload construction changed; contract extraction needs review')
    if values[0].args or any(k.arg is None for k in values[0].keywords):
        raise ValueError('dynamic host payload fields require review')
    return [k.arg for k in values[0].keywords]


def build_compiler_contract():
    # Trusted projection code only. This fixture is not a natural failure or gate.
    raw = dict(visibility='public',status='PUBLIC_PASS',cases=[dict(
        visibility='public',legal_verified=True,input='1\n',expected='1\n',actual='1\n',
        exception_class=None,status='PASS',private_probe='must not propagate')])
    feedback = PublicFeedback.project(raw).to_dict()
    task = PublicTaskView.project(dict(problem_id='synthetic-contract-example',prompt='Echo input.')).to_dict()
    files = {Path(inspect.getfile(cls)).resolve() for cls in (PublicFeedback,FailureLearningPlugin)}
    return dict(version='host-contract-projection-v1',
        payload_fields=_dict_fields(FailureLearningPlugin.invoke,'payload'),
        ledger_fields=_dict_fields(FailureLearningPlugin.observe,'candidate'),
        feedback_fields=list(feedback),case_fields=list(feedback['public_cases'][0]),
        task_fields=list(task),examples=dict(public_pass=feedback,unknown=PublicFeedback('UNKNOWN').to_dict(),task=task),
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},
        projection_source=inspect.getsource(PublicFeedback.project),
        limitations='Synthetic interface examples only, not execution or recovery evidence. PUBLIC_PASS is the host aggregate; case keys are optional and no per-case status exists.')
