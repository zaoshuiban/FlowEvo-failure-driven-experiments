"""Single existing-Operator version update; frame checks are evaluators, not repair tools."""
import argparse, ast, copy, difflib, json, shutil, time
from pathlib import Path
from experiment_capacity_nursery import ROOT, BASE, Study, read, write, sha, h, make_case
from generate_capacity_safe_ast import PROMPT as SAFE_PROMPT
from failure_evo import BoundedCompiler
from failure_evo.contracts import fingerprint
from failure_evo.compiler_contract import build_compiler_contract
from failure_evo.candidate_revision import compile_candidate
from failure_evo.model_api import DeepSeekGenerator
OLD=ROOT/'runs/s12i_capacity_safe_ast_20261022_01'
PROMPT=SAFE_PROMPT+'''
VERSION UPDATE, NOT A FROM-SCRATCH GENERATION STUDY:
Update the supplied previous Operator using the actual scope diagnostic. Its broad AST
visitors violate the frame condition: only modify identified table allocation/initialization
nodes; never globally replace n+1, range calls, subscripts or all list allocations.
First identify the table read through a justified constant-derived index, then dependent
inverse-precomputation table (including simple aliases). Prove the affected statements
before transforming. Preserve all consumers and input-length semantics. Refuse unsupported
structures instead of guessing. Do not match table names, problem IDs or exact source lines.
The input-length-only suffix table and the length-only power table are NOT capacity targets.
If an initializer loop mixes affected and unaffected table writes, either safely separate
independent recurrences preserving the unaffected loop's exact bounds/body, or decline.
Do not expand an unrelated table just because it shares an initialization loop. Do not
rewrite reads T[n] in consumers; change only the identified inverse-precomputation seed.
Preserve unrelated assertions, calculations, loops, arrays and their ordering. Fresh capacity
variables must not collide. Source-program transformation must not add assertions or swallow
errors. Use the current AST interfaces, constant error messages, no getattr/dunder access.
A host frame evaluator compares ASTs outside declared table initialization changes. It is
an experimental checker, NOT a new runtime repair primitive supplied to your code. It removes
only target allocations/initialization assignments and now-empty pure initialization loops,
and one fresh max(input_length, justified_bound) assignment. Everything else must match.
You must generate the full reusable Python Operator, not a patched solution or a host patch.
'''

class ScopeGenerator(DeepSeekGenerator):
    @staticmethod
    def prepare(request): return DeepSeekGenerator.prepare(request,system_prompt=PROMPT)


def frame_review(original, proposed, spec):
    """Fixture-scoped frame check, not semantic equivalence or a production analyzer.
    Only direct initialization statements before a frozen consumer boundary are mutable.
    Mixed loops retain their unaffected statements AND original loop header.
    """
    try:
        before,after=ast.parse(original),ast.parse(proposed)
        targets=set(spec['tables']); length=spec['length']; boundary=spec['boundary_alias']
        names={n.id for n in ast.walk(before) if isinstance(n,ast.Name)}
        def projection(tree, is_new):
            tree=copy.deepcopy(tree)
            funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==spec['function']]
            if len(funcs)!=1:raise ValueError('scope_function_missing')
            body=funcs[0].body; cut=None
            for i,node in enumerate(body):
                if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id==boundary:
                    cut=i;break
            if cut is None:raise ValueError('consumer_boundary_missing')
            caps=[]
            def target_assign(n):
                if not isinstance(n,ast.Assign) or len(n.targets)!=1:return False
                t=n.targets[0]
                return (isinstance(t,ast.Name) and t.id in targets) or (isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id in targets)
            def cap_assign(n):
                if not is_new or not isinstance(n,ast.Assign) or len(n.targets)!=1:return False
                t=n.targets[0];v=n.value
                if not isinstance(t,ast.Name) or t.id in names:return False
                expected=ast.parse('max('+length+', '+str(spec['bound'])+')',mode='eval').body
                if ast.dump(v)!=ast.dump(expected):return False
                caps.append(t.id);return True
            kept=[]
            for node in body[:cut]:
                if target_assign(node) or cap_assign(node):continue
                if isinstance(node,ast.For) and not node.orelse:
                    left=[n for n in node.body if not target_assign(n)]
                    if len(left)!=len(node.body):
                        if not left:continue
                        node.body=left
                kept.append(node)
            if len(caps)>1:raise ValueError('multiple_capacity_assignments')
            funcs[0].body=kept+body[cut:]
            return ast.dump(tree,include_attributes=False)
        a,b=projection(before,False),projection(after,True)
        # Human-reviewable structural diff, not arbitrary-source execution.
        diff=list(difflib.unified_diff(a.split(', '),b.split(', '),fromfile='original-frame',tofile='proposed-frame'))
        return dict(passed=a==b,frame_before_sha256=h(a),frame_after_sha256=h(b),
                    changed_frame_fragments=diff[:100],declared_scope=spec,
                    limitation='fixture-scoped AST frame preservation, not full semantic equivalence')
    except (ValueError,SyntaxError,TypeError) as exc:
        return dict(passed=False,error=str(exc),declared_scope=spec)


class ScopeStudy(Study):
    def __init__(self,run):
        super().__init__(run)
        self.frame_specs=read(run/'frame_specs.json')
    def invariants(self,original,proposed):
        out=Study.invariants(original,proposed)
        spec=self.frame_specs.get(h(original))
        frame=frame_review(original,proposed,spec) if spec else dict(passed=False,error='unregistered_fixture_scope')
        out.update(frame=frame,passed=out['passed'] and frame['passed'])
        return out
    def inspect_version(self,path,role):
        out=super().inspect_version(path,role)
        # Include actual frame diagnosis for failed controls in bounded model feedback.
        out['frame_contract']='Only annotated fact/inverse initialization can change; H, power table, consumers and unrelated subtrees must remain identical after projection.'
        write(path.parent/(path.stem+'-'+role+'-review.json'),out)
        return out


def base_config(run, max_calls):
    config=copy.deepcopy(read(OLD/'protocol.json'))
    config.pop('protocol_hash',None);config.pop('frozen_files',None)
    config.update(run_id=run.name,representation='direct_python_scope_update_v2',candidate_count=1,revisions_per_candidate=1,
        induction_calls=0,max_real_requests=max_calls,scope='One new version of suspended winner, at most one development revision; no new mechanism or G/M/B/F; no sealed-feedback revision',
        selection='Only updated version passing source, all development and frame checks may be frozen as sole winner; no reselection after new sealed review',
        sealed_rule='All previous inputs/controls now development. Newly frozen same-task inputs and engineering scope controls only after sole winner frozen. Not independent natural gate.',
        authorization_basis='User: 根据建议进行下一步实验; bounded version update, fresh maximum 0.25 USD, no previous balance')
    config['generation_budget'].update(max_calls=max_calls,max_tokens=139264 if max_calls else 0,max_cost_microusd=250000 if max_calls else 0)
    config['continuation_budget'].update(max_calls=0,max_tokens=0,max_cost_microusd=0)
    config['evaluation_budget'].update(max_tools=1000,max_tool_milliseconds=10000000)
    config['p3']={'status':'OUT_OF_SCOPE'};config['p4']={'status':'OUT_OF_SCOPE'}
    return config


def freeze(run,config,extra=()):
    files=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/experiment_capacity_nursery.py',ROOT/'scripts/generate_capacity_safe_ast.py']+list(run.glob('*.json'))+list(run.glob('*.txt'))+list(extra)
    config['frozen_files']={str(p.resolve().relative_to(ROOT)):sha(p) for p in files}
    config['protocol_hash']=fingerprint(config);write(run/'protocol.json',config)
    write(run/'authorization.json',dict(api_spend_authorized=config['max_real_requests']>0,run_id=run.name,protocol_hash=config['protocol_hash'],max_cost_microusd=config['generation_budget']['max_cost_microusd'],max_calls=config['max_real_requests'],user_authorization_text='根据建议进行下一步实验'))
    for name in config['frozen_files']:
        dest=run/'frozen_sources'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)


def audit(run):
    run.mkdir(exist_ok=False);(run/'tmp').mkdir()
    shutil.copy2(OLD/'worker_acceptance.json',run/'worker_acceptance.json')
    job=read(OLD/'generation_input.json');job.update(stream_id=run.name,job_id=fingerprint(run.name),host_contract=build_compiler_contract());write(run/'generation_input.json',job)
    original=job['candidate_code'];old_assert=read(OLD/'postselection_scope_protocol.json')['variant']
    combined=original.replace('    n = len(S)','    n = len(S)\n    scratch = [0] * (n + 1)\n    ticks = 0\n    for probe_i in range(1, n + 1):\n        ticks += 1\n    assert ticks == n and len(scratch) == n + 1',1)
    variants=[dict(id='exposed-assertion',code=old_assert),dict(id='array-loop-frame',code=combined)]
    write(run/'diagnostic_controls.json',variants)
    freeze(run,base_config(run,0),[OLD/'candidate_3/candidate.py'])
    study=Study(run);rows=[]
    try:
        for v in variants:
            pre=study.evaluate(v['code'],read(BASE/'statement_cases.json'),'audit-original-'+v['id'])
            action=study.operator(OLD/'candidate_3/candidate.py',study.context(v['code'],pre['feedback']),'old-candidate3-'+v['id'])
            post=study.evaluate(action['proposed'],read(BASE/'statement_cases.json'),'audit-proposal-'+v['id']) if action['proposed'] else None
            frame=frame_review(v['code'],action['proposed'],dict(tables=['fact','invfact'],length='n',boundary_alias='invf',function='main',bound=26)) if action['proposed'] else None
            rows.append(dict(id=v['id'],original=pre,action=action,repaired=post,frame=frame))
        write(run/'audit_result.json',dict(api_calls=0,old_candidate3_sha256=sha(OLD/'candidate_3/candidate.py'),rows=rows,role='exposed_engineering_development_not_gate',old_winner_unchanged=True))
    finally:write(run/'budget_snapshots.json',{k:v.snapshot() for k,v in study.budgets.items()})
    print('AUDIT_COMPLETE',[(r['id'],r['repaired']['feedback']['tests_passed'] if r['repaired'] else None,r['frame']['passed'] if r['frame'] else None) for r in rows],flush=True)


def prepare(run,audit_run):
    run.mkdir(exist_ok=False);(run/'tmp').mkdir()
    shutil.copy2(OLD/'worker_acceptance.json',run/'worker_acceptance.json')
    shutil.copy2(OLD/'specification.txt',run/'specification.txt')
    original=read(OLD/'generation_input.json')['candidate_code']
    # All exposed old sealed material is explicitly demoted to development.
    dev=read(OLD/'development_cases.json')+read(OLD/'sealed_cases.json');write(run/'development_cases.json',dev)
    fresh=['KkKK','KKkL','kKkK','KLmn','K?mK','?KkL','KK?m','K??m','?Lm?','mN?N','X'*24,'Y'*28,'q'*42,'KlMn'*253]
    assert not set(c['input'] for c in dev)&{s+'\n' for s in fresh}
    write(run/'sealed_cases.json',[make_case('v2-sealed:'+str(i),s) for i,s in enumerate(fresh)])
    controls=read(OLD/'controls.json')
    specs={h(original):dict(tables=['fact','invfact'],length='n',boundary_alias='invf',function='main',bound=26)}
    for c in controls:
        c['role']='design';c['previous_role']='exposed_previous_run'
        if c['category']=='same_mechanism':
            prefix='v_' if c['id']=='structure-0' else ('other_' if c['id']=='structure-2' else '')
            specs[h(c['code'])]=dict(tables=[prefix+'fact',prefix+'invfact'],length=prefix+'n',boundary_alias=prefix+'invf',function='main',bound=26)
    insertions=[
      ('old-assert','assert n + 1 == len(S) + 1','design'),
      ('arithmetic','extra = n + 1\nassert extra == len(S) + 1','design'),
      ('loop','ticks = 0\nfor probe_i in range(1, n + 1):\n    ticks += 1\nassert ticks == n','design'),
      ('array','scratch = [0] * (n + 1)\nassert len(scratch) == len(S) + 1','design'),
      ('reverse-counter','acc = 0\nfor j_scope in range(n, 0, -1):\n    acc += j_scope\nassert acc == n * (n + 1) // 2','sealed'),
      ('coupled-unrelated','spare = [7] * (n + 1)\nseen = 0\nfor j_scope in range(1, n + 1):\n    seen += spare[j_scope]\nassert seen == 7 * n','sealed'),
      ('function-unrelated','def local_length(x):\n    return x + 1\nsize_check = local_length(n)\nassert size_check == len(S) + 1','sealed'),
      ('alias-unrelated','spare = [3] * (n + 1)\nspare_alias = spare\nassert spare_alias[n] == 3 and len(spare_alias) == n + 1','sealed')]
    for name,block,role in insertions:
        code=original.replace('    n = len(S)','    n = len(S)\n'+'\n'.join('    '+line for line in block.splitlines()),1)
        specs[h(code)]=specs[h(original)]
        controls.append(dict(id='scope-'+name,category='scope_semantics',role=role,code=code,task=read(OLD/'generation_input.json')['task_public'],expected_behavior='repair',provenance='engineering_semantic_preserving_insertion_not_natural_failure',cases=read(BASE/'statement_cases.json')))
    # New held-out refusal boundaries: no public failure or unsupported capacity provenance.
    for i,code in enumerate(['n=int(input()); a=[1]*(n+1); k=int(input()); print(a[k+n])\n','n=int(input()); a=[1]*(n+1); q=a; q[:]=[]; print(a[0])\n']):
        controls.append(dict(id='v2-unknown-'+str(i),category='unknown_or_resource',role='sealed',code=code,expected_behavior='decline',provenance='engineering_constructed_not_natural_failure',task=dict(problem_id='v2-unknown-'+str(i),prompt='Legal input n=4 and k=8; no proven fixed capacity bound.',public_examples=[]),cases=[dict(case_id='unknown-'+str(i),input='4\n8\n',expected='0\n',comparison='whitespace_token_exact',visibility='public',legal_verified=True)]))
    write(run/'controls.json',controls);write(run/'frame_specs.json',specs)
    audit_result=read(audit_run/'audit_result.json')
    diagnostics=dict(old_winner_sha256=sha(OLD/'candidate_2/candidate.py'),old_winner_issue='global n+1 replacement breaks unrelated invariant; targets H and other length-only allocations; broad ranges/subscript reads',
        prior_diagnostic=read(OLD/'postselection_scope_result.json'),candidate3_audit=audit_result,
        interpretation='Both prior artifacts are development references only; no replacing the frozen old winner')
    write(run/'scope_diagnostics.json',diagnostics)
    job=read(OLD/'generation_input.json');job.update(job_id=fingerprint([run.name,job['job_id']]),stream_id=run.name,host_contract=build_compiler_contract(),
        version_parent=dict(code=(OLD/'candidate_2/candidate.py').read_text(),sha256=sha(OLD/'candidate_2/candidate.py'),origin_run=OLD.name,permission='suspended'),
        scope_diagnostics=dict(summary=diagnostics['old_winner_issue'],old_assertion='assert n + 1 == len(S) + 1',observed='Old winner breaks 2/3 samples. Candidate3 keeps assertion but expands unrelated loop/array and fails their invariant.',
            requirements='Only target factorial and inverse precomputation; preserve the suffix and length-only power table; split mixed initializer safely or decline; no global AST transformations.'),
        study_type='diagnostic_version_update_not_from_scratch_generation_rate',representation='direct_python_no_host_repair_primitive')
    write(run/'generation_input.json',job);(run/'compile_prompt.txt').write_text(PROMPT)
    config=base_config(run,2)
    config['data_roles']=dict(development='43 old source inputs, 16 old controls, 4 exposed/new design scope controls',sealed='14 fresh same-task inputs, 4 new scope controls, 2 new refusal controls; none independent natural tasks')
    freeze(run,config,[OLD/'candidate_2/candidate.py',OLD/'candidate_3/candidate.py',audit_run/'audit_result.json'])
    print('FROZEN',config['protocol_hash'],flush=True)


def execute(run):
    if (run/'compiler.jsonl').exists():raise FileExistsError('run already attempted')
    study=ScopeStudy(run);b=study.budgets['generation'];approval=read(run/'authorization.json')
    assert approval['protocol_hash']==study.config['protocol_hash'] and approval['api_spend_authorized']
    compiler=BoundedCompiler(ScopeGenerator(b,authorization=dict(approval,run_id=b.config['run_id'])),b,run/'compiler.jsonl',study.config['model'])
    job=dict(study.job);job['specification']=compiler.import_specification(job,run/'specification.txt',time.time())
    decision=dict(conclusion='NO_GO_THIS_VERSION_UPDATE',nursery=False,sealed_consumed=False,old_winner='suspended_unchanged')
    try:
        result=compile_candidate(compiler,job,0,run/'candidate_1',design_checker=lambda p:study.inspect_version(p,'design'))
        write(run/'p1.json',[result]);registry=study.register_shadows()
        print('DEVELOPMENT',result['functional_acceptance'],result.get('stop_reason'),flush=True)
        if result['functional_acceptance']=='DEVELOPMENT_PASSED_NOT_GATE':
            write(run/'winner.json',result)
            sealed=study.inspect_version(Path(result['accepted_artifact']),'sealed');write(run/'p2.json',sealed)
            decision.update(conclusion='PARTIAL_SEALED_FAILED_NO_RESELECTION',sealed_consumed=True,artifact_sha256=result['accepted_sha256'])
            if sealed['eligible']:
                admitted=study.admit(result,registry)
                decision.update(conclusion='GO_BOUNDED_NURSERY_SCOPE_V2' if admitted else 'PARTIAL_HOST_FAILED',nursery=admitted)
    finally:
        write(run/'decision.json',decision);write(run/'budget_snapshots.json',{k:v.snapshot() for k,v in study.budgets.items()});print(json.dumps(decision),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--audit',action='store_true');p.add_argument('--prepare',action='store_true');p.add_argument('--audit-run');a=p.parse_args()
    if a.audit:audit(ROOT/a.run)
    elif a.prepare:prepare(ROOT/a.run,ROOT/a.audit_run)
    else:execute(ROOT/a.run)
