"""Public HumanEval docstring examples; no reference implementation is exported."""
import ast
import doctest
import gzip
import hashlib
import json
from pathlib import Path
from core.schemas import CodeTaskInstance

TRAIN = [0,20,1,6,56,61,13,24,25,31,39,59,8,9,21,46,55,63,10,48,18,17,33,37]
TRANSFER = [36,44,49,60,139,57,47,100,54,91,93,64]
NEAR_GROUPS = [{0,20}, {1,6,56,61}, {46,55,63}, {33,37}, {10,48}]
NUMBER = {13,24,25,31,39,59,36,44,49,60,139}
SEQUENCE = {0,20,8,9,21,46,55,63,33,37,57,47,100}

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def public_examples(prompt, entry):
    tree = ast.parse(prompt)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == entry)
    examples = []
    for example in doctest.DocTestParser().get_examples(ast.get_docstring(fn) or ''):
        try:
            expr = ast.parse(example.source).body
            if len(expr) != 1 or not isinstance(expr[0], ast.Expr):continue
            call = expr[0].value
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != entry:continue
            for arg in call.args:ast.literal_eval(arg)
            for arg in call.keywords:ast.literal_eval(arg.value)
            expected = ast.literal_eval(example.want.strip())
            examples.append(dict(source=example.source.strip(), expected_literal=repr(expected),
                                 assertion='assert ('+example.source.strip()+') == '+repr(expected)))
        except (ValueError, SyntaxError):continue
    return examples

def manifest(source):
    source = Path(source)
    rows = [json.loads(line) for line in gzip.open(source, 'rt')]
    public = {}
    unavailable = []
    for row in rows:
        try:examples = public_examples(row['prompt'], row['entry_point'])
        except (SyntaxError, ValueError, StopIteration):examples = []
        if examples:
            public[row['task_id']] = dict(prompt=row['prompt'], entry_point=row['entry_point'], examples=examples)
        else:unavailable.append(row['task_id'])
    tasks = []
    for role, ids in [('train', TRAIN), ('transfer_dev', TRANSFER)]:
        for n in ids:
            tid = 'HumanEval/'+str(n)
            r = public[tid]
            group = next(('HumanEval/near/'+','.join(map(str,sorted(g))) for g in NEAR_GROUPS if n in g), tid)
            family = 'number_theory' if n in NUMBER else 'sequence_transformation' if n in SEQUENCE else 'string_structure'
            tasks.append(dict(problem_id=tid, data_role=role, source_lineage_id=group, duplicate_group_id=group,
                capability_family_id=family, exposure_status='historical_development_dataset',
                source='openai HumanEval original task; no generated variants',
                public_sha256=digest(json.dumps(r,sort_keys=True)), **r))
    validate_manifest(tasks)
    return dict(dataset='HumanEval', dataset_path=str(source.resolve()), dataset_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        inspected_rows=len(rows), usable_public_example_tasks=len(public), excluded_no_supported_public_example=unavailable,
        conversion='Literal direct doctest call and literal expected output only; never evaluate a reference solution',
        selection='Human-reviewed public capability strata; frozen IDs independent of all run outcomes',
        duplicate_audit='Conservative public-description near groups; original HumanEval IDs, no derived problems. Not a claim of exhaustive semantic deduplication.',
        reserved_eval=dict(read_answers=False,assigned_tasks=0,note='Existing sealed archives untouched; unused HumanEval tasks are not claimed unexposed evaluation.'),
        tasks=tasks)

def validate_manifest(tasks):
    for key in ('problem_id','source_lineage_id','duplicate_group_id'):
        groups = {}
        for row in tasks:
            if row['data_role'] not in {'train','transfer_dev','reserved_eval'} or not row[key]:raise ValueError('PILOT_ROLE_OR_ID')
            groups.setdefault(row[key],set()).add(row['data_role'])
        if any(len(v)>1 for v in groups.values()):raise ValueError('PILOT_ROLE_LEAKAGE:'+key)

def task_from_manifest(row):
    tests = [x['assertion'] for x in row['examples']]
    from env.humaneval_loader import humaneval_task_from_row
    task=humaneval_task_from_row(dict(task_id=row['problem_id'],prompt=row['prompt'],entry_point=row['entry_point']),public_only=True)
    task.text=row['prompt'];task.visible_public_tests=tests;task.test_list=tests
    task.metadata={**{k:row[k] for k in ('data_role','source_lineage_id','duplicate_group_id','capability_family_id')},
        'public_training_tests':tests,'training_validation_public':True,'public_validation_only':True}
    return task

def final_score_task(source, task_id):
    # Called by the driver only AFTER all learning and transfer programs are frozen.
    for line in gzip.open(source,'rt'):
        row = json.loads(line)
        if row['task_id']==task_id:
            return CodeTaskInstance(task_id=task_id,benchmark='humaneval',prompt=row['prompt'],entry_point=row['entry_point'],test=row['test'],canonical_solution='')
    raise KeyError(task_id)
