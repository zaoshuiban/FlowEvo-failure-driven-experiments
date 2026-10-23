"""Free-form Python generation with reviewed safe AST idioms, unchanged permissions.
No host repair primitive and no hand-edited model artifact. At most 3+3 requests.
"""
import argparse, copy, json, shutil, time
from pathlib import Path
from types import SimpleNamespace
from experiment_capacity_nursery import ROOT, BASE, Study, read, write, sha, h
from failure_evo import BoundedCompiler
from failure_evo.contracts import canonical, fingerprint
from failure_evo.compiler_contract import build_compiler_contract
from failure_evo.model_api import DeepSeekGenerator, validate_compile_output
from failure_evo.candidate_revision import compile_candidate
OLD=ROOT/'runs/s12g_capacity_20261022_01'
H=ROOT/'runs/s12h_capacity_revision_20261022_01'
SAFE_EXAMPLE='''import ast

def repair_operator(context):
    try:
        tree = ast.parse("if True:\\n    pass\\n")
        count = 0
        for node in ast.walk(tree):
            for field, value in ast.iter_fields(node):
                if field in ("body", "orelse", "finalbody") and isinstance(value, list):
                    count += len(value)
        fresh = ast.Module(body=[ast.Pass()], type_ignores=[])
        text = ast.unparse(ast.fix_missing_locations(fresh))
        if text == "pass" and count == 2:
            return {"status": "declined", "reason": "allowed_ast_probe_pass"}
        return {"status": "error", "reason": "allowed_ast_probe_failed"}
    except Exception:
        return {"status": "error", "reason": "bounded_ast_error"}
'''
PROMPT='''Write a NEW reusable Python repair_operator(context), not a solution to this task.
Return exactly JSON fields code, description, applicability, all nonempty strings. Never
return specification or a runtime decision at compile time. Runtime uses literal dicts:
{"status":"declined","reason":"..."}, {"status":"error","reason":"..."}, or
{"status":"applied","candidate_code":complete_proposed_source}. The host tests proposals.

Use the attached actual interface. Only candidate_code modification is allowed. Require
credible public IndexError evidence and a source pattern you support. Check public_feedback
visibility/status and public_cases[].exception_class; there is no public_cases[].status.
Do not require an already PUBLIC_PASS solution to propose a repair for a known failure.

MANDATORY IMPLEMENTATION IDIOMS, VERIFIED AGAINST THE REAL CHECKER:
* Error logging: except Exception: return {"status":"error","reason":"bounded_ast_error"}.
  Do NOT inspect exception types. Never write type(e).__name__, any dunder access or getattr.
* Traverse child fields with `for field, value in ast.iter_fields(node):` and type-check
  value, or use isinstance(node, ast.If/ast.For/ast.FunctionDef/ast.Try) and explicit fields.
  Never use getattr/setattr/hasattr/vars. Do not write a generic reflective visitor.
* For new/replaced AST nodes use ast.fix_missing_locations(tree) before ast.unparse(tree).
* Allowed ordinary APIs include ast.parse, ast.walk, ast.iter_fields, ast.dump,
  ast.NodeTransformer and explicit node attributes after isinstance checks.
* Source string literals may contain the input program's __name__ guard. That does NOT
  license attribute reflection in your Operator. No files/network/processes/eval/exec/compile,
  privilege APIs, model calls or permission changes. Imports only from the existing whitelist.

Generate a bounded deterministic transformation, not a general Python analyzer. Identify
length-sized one-dimensional precomputation tables and the constant-bounded index that
exceeds input length. Follow simple assignments when proving the index range; the index
variable need not be the right-hand operand of the subtraction that defined it. Derive
bounds from source or public constraints; 26 is allowed when justified by the alphabet,
never by task ID, sample matching or expected answers. Refuse unknown or huge bounds.
Select the related precomputation dependency group; change its allocations, initialization
loops and seed indices consistently. Only modify loops proven to initialize those tables.
Do not blindly rewrite every range(length) or every list allocation, do not overwrite the
input-length variable, and do not introduce exception swallowing in the repaired program.
Simple single-assignment table aliases can be supported if explicitly tracked; complex
aliasing, mutation through unknown calls or multidimensional tables should decline.
For already sufficient or unrelated/uncertain code decline rather than guessing.
Resource bounds: source <=20000 bytes; justified capacity <=300001; operator <=2 seconds.

Before emitting JSON, scan the actual code for forbidden getattr, setattr, __name__, other
dunder attribute access and dynamic exception formatting. Replace those habits with the
verified literal-error/iter_fields idioms above. Keep the proposed transformation small.
This remains direct model-generated Python: no host patch generator is supplied.
The examples are syntax examples only and provide no capacity repair implementation.'''

class SafeAstGenerator(DeepSeekGenerator):
    @staticmethod
    def prepare(request):
        return DeepSeekGenerator.prepare(request,system_prompt=PROMPT)


def prepare(run):
    run.mkdir(exist_ok=False);(run/'tmp').mkdir()
    config=copy.deepcopy(read(OLD/'protocol.json'))
    for name in ('worker_acceptance.json','development_cases.json','sealed_cases.json','controls.json','specification.txt'):
        shutil.copy2(OLD/name,run/name)
    (run/'safe_ast_probe.py').write_text(SAFE_EXAMPLE);(run/'compile_prompt.txt').write_text(PROMPT)
    review=validate_compile_output(dict(code=SAFE_EXAMPLE,description='Handwritten engineering syntax probe, no repair action',applicability='Always declines; validates permitted AST APIs'))
    assert review['static_pass'];write(run/'safe_ast_static.json',review)
    audit=dict(api_calls=0,representation='free_form_python_with_documented_allowed_ast_idioms',permission_policy='unchanged',
        findings=[dict(source=str(H/'candidate_1/revision.py'),sha256=sha(H/'candidate_1/revision.py'),
             forbidden_usage='exception type name for logging only; not required for capacity analysis',
             semantic_risks=['rewrites ranges outside proven initializer group','new AST nodes lack location repair before unparse','does not verify public failure precondition']),
            dict(source=str(H/'candidate_3/revision.py'),sha256=sha(H/'candidate_3/revision.py'),
             forbidden_usage='getattr reads body/orelse/finalbody during AST insertion; iter_fields or explicit node branches suffice; exception type name is logging only',
             semantic_risks=['bound discovery confuses defined index with subtraction RHS','single table selection can miss dependent allocations','rewrites broad loop/subscript groups'])],
        conclusions='No necessity for new reflection privileges established. Ordinary allowed AST APIs express these operations. Semantic risks are code inspection, not execution results.',
        manual_capacity_patch_supplied=False,host_repair_primitive_added=False)
    write(run/'expression_audit.json',audit)
    job=read(OLD/'generation_input.json');job.update(job_id=fingerprint([run.name,job['job_id']]),stream_id=run.name,host_contract=build_compiler_contract(),
        programming_idioms=dict(error_reporting='except Exception: return literal error dict with constant reason',
            ast_children='ast.iter_fields with type checks; explicit typed node attributes',ast_output='ast.fix_missing_locations before ast.unparse'),
        scope_clarification='Simple single-assignment aliases may be tracked; unknown aliasing must decline. Preserve input-length semantics and unrelated loops.',
        representation='direct Python generation, human-selected capacity mechanism, permitted syntax guidance only')
    write(run/'generation_input.json',job)
    config.update(run_id=run.name,representation='direct_python_safe_ast_idioms_v1',candidate_count=3,revisions_per_candidate=1,
        induction_calls=0,scope='3 initial candidates + at most one static/development revision each; immediate isolation; one sealed winner; nursery only if accepted; no B/G/M/F or online stream',
        authorization_basis='User: 修复现有的问题,可以消耗预算; independent maximum 0.60 USD / 6 requests; no inherited budget')
    config['generation_budget'].update(max_calls=6,max_tokens=417792,max_cost_microusd=600000)
    config['continuation_budget'].update(max_calls=0,max_tokens=0,max_cost_microusd=0)
    config['p3']={'status':'OUT_OF_SCOPE'};config['p4']={'status':'OUT_OF_SCOPE'}
    files=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/experiment_capacity_nursery.py']+list(run.glob('*.json'))+[run/'specification.txt',run/'compile_prompt.txt',run/'safe_ast_probe.py',H/'candidate_1/revision.py',H/'candidate_3/revision.py']
    config['frozen_files']={str(p.resolve().relative_to(ROOT)):sha(p) for p in files}
    config.pop('protocol_hash',None);config['protocol_hash']=fingerprint(config);write(run/'protocol.json',config)
    write(run/'authorization.json',dict(api_spend_authorized=True,run_id=run.name,protocol_hash=config['protocol_hash'],max_cost_microusd=600000,user_authorization_text='修复现有的问题,可以消耗预算',max_calls=6))
    for name in config['frozen_files']:
        dest=run/'frozen_sources'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    print('FROZEN_NO_API',config['protocol_hash'],flush=True)


def execute(run):
    if (run/'compiler.jsonl').exists():raise FileExistsError('fresh frozen run required')
    study=Study(run);b=study.budgets['generation'];approval=read(run/'authorization.json')
    assert approval['protocol_hash']==study.config['protocol_hash'] and approval['api_spend_authorized'] is True
    # This trusted engineering probe contains no program repair algorithm.
    probe=study.operator(run/'safe_ast_probe.py',study.context(study.job['candidate_code'],read(BASE/'result.json')['public_sample_replay']['feedback']),'allowed-ast-probe')
    write(run/'safe_ast_execution.json',probe)
    if probe['result']!={'status':'declined','reason':'allowed_ast_probe_pass'}:raise RuntimeError('allowed AST expression probe failed; no API sent')
    compiler=BoundedCompiler(SafeAstGenerator(b,authorization=dict(approval,run_id=b.config['run_id'])),b,run/'compiler.jsonl',study.config['model'])
    job=dict(study.job);job['specification']=compiler.import_specification(job,run/'specification.txt',time.time())
    results=[];decision=dict(conclusion='NO_GO_NO_ELIGIBLE_CANDIDATE',nursery=False,p3='OUT_OF_SCOPE',sealed_consumed=False)
    try:
        for slot in range(3):
            result=compile_candidate(compiler,job,slot,run/f'candidate_{slot+1}',design_checker=lambda p:study.inspect_version(p,'design'))
            results.append(result);write(run/'p1.json',results)
            print('candidate',slot+1,result['source_acceptance'],result['functional_acceptance'],result.get('stop_reason'),flush=True)
        registry=study.register_shadows()
        eligible=[r for r in results if r['functional_acceptance']=='DEVELOPMENT_PASSED_NOT_GATE']
        if eligible:
            eligible.sort(key=lambda r:(r['versions'][-1]['functional_review']['source_changed_lines'],r['versions'][-1]['functional_review']['source_operator_seconds'],r['slot']))
            winner=eligible[0];write(run/'winner.json',winner)
            path=Path(winner['accepted_artifact']);sealed=study.inspect_version(path,'sealed');write(run/'p2.json',sealed)
            decision.update(winner=winner['slot']+1,artifact_sha256=winner['accepted_sha256'],sealed_consumed=True,conclusion='PARTIAL_SEALED_FAILED_NO_RESELECTION')
            if sealed['eligible']:
                admitted=study.admit(winner,registry);decision.update(conclusion='GO_BOUNDED_NURSERY' if admitted else 'PARTIAL_HOST_FAILED',nursery=admitted)
    finally:
        write(run/'decision.json',decision);write(run/'budget_snapshots.json',{k:v.snapshot() for k,v in study.budgets.items()})
        print(json.dumps(decision),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--prepare',action='store_true');args=p.parse_args()
    (prepare if args.prepare else execute)(ROOT/args.run)
