"""Bounded, zero-model real-data controls plus focused interface regression."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'FlowEvo/src'))
from env.taco_function_loader import public_task,scoring_task,adapt_candidate
from eval.verifier import verify_task
from failure_evo.contracts import fingerprint
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.pilot_runtime import IsolatedCodeSandbox,write_json

PREP=REPO/'runs/taco_function_acquisition_20261120/preparation'
OUT=REPO/'reports/taco_function_acquisition_20261120'
IMAGE='sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8'


def data_controls():
    os.chdir(REPO)
    pool=json.loads((PREP/'candidate_pool.json').read_text())
    # Seal before any control execution. These tasks are not executed even with references.
    ordered=sorted(pool,key=lambda r:fingerprint('taco-reserve-v1/'+r['source_lineage_id']))
    reserved=ordered[:12];candidates=ordered[12:]
    protocol=dict(candidate_pool_sha256=fingerprint(pool),reserved=[r['problem_id'] for r in reserved],
                  controls=[r['problem_id'] for r in candidates],image=IMAGE,max_executions=256,model_requests=0)
    write_json(PREP/'data_control_protocol.json',protocol)
    root=PREP/'data_controls';root.mkdir(exist_ok=True)
    budget=PersistentBudget(root/'budget.jsonl',run_id='taco_data_controls',protocol_hash=fingerprint(protocol),
        max_calls=0,max_tokens=0,max_tools=256,max_cost_microusd=0,token_rate_microusd_per_million=0,
        tool_cost_upper_microusd=0,max_tool_milliseconds=5120000,tool_milliseconds_upper=20000,wall_seconds=1800)
    box=IsolatedCodeSandbox(image=IMAGE,budget=budget,root=root)
    outcomes=[];qualified=[]
    for row in candidates:
        key=str(row['row_index'])
        status=dict(task_id=row['problem_id'],public_pass=False,full_pass=False)
        try:
            code=adapt_candidate((REPO/row['positive_control_ref']).read_text(),row['call_protocol']['entry_point'])
            public=public_task(dict(row,data_role='development'))
            box.context('positive_public',key)
            feedback=verify_task(public,code,box)
            status['public_pass']=feedback.passed
            private=scoring_task(dict(row,data_role='development'),REPO)
            box.context('positive_private',key)
            full=verify_task(private,code,box)
            status['full_pass']=full.passed
            write_json(root/'private_feedback'/key/'public.json',feedback.model_dump(mode='json'))
            write_json(root/'private_feedback'/key/'private.json',full.model_dump(mode='json'))
            if feedback.passed and full.passed:qualified.append(row)
            status['status']='QUALIFIED' if feedback.passed and full.passed else 'CONTROL_DISAGREEMENT_NOT_ALGORITHM_EVIDENCE'
        except (SyntaxError,ValueError,KeyError,TypeError) as exc:
            status.update(status='CONTROL_ERROR',error_type=type(exc).__name__)
        outcomes.append(status)
        write_json(PREP/'data_control_progress.json',outcomes)
        print(row['problem_id'],status['status'],flush=True)
    # Transfer assignment is fixed using public IDs, never Actor failures/outcomes.
    qualified.sort(key=lambda r:fingerprint('taco-dev-v1/'+r['source_lineage_id']))
    transfer=qualified[:12];remaining=qualified[12:]
    rank={'VERY_HARD':0,'HARD':1,'MEDIUM_HARD':2,'MEDIUM':3,'EASY':4}
    families={f:sorted([r for r in remaining if r['capability_family_id']==f],
                        key=lambda r:(rank[r['difficulty']],fingerprint(r['problem_id'])))
              for f in sorted({r['capability_family_id'] for r in remaining})}
    train_order=[]
    while any(families.values()):
        for family in families:
            if families[family]:train_order.append(families[family].pop(0))
    train_n=min(64,(len(train_order)//16)*16)
    if train_n<16 or len(transfer)<12:raise RuntimeError('INSUFFICIENT_QUALIFIED_POOL')
    selected=[]
    for role,rows in [('train',train_order[:train_n]),('transfer_dev',transfer),('reserved_eval',reserved)]:
        for row in rows:
            r=dict(row,data_role=role)
            r.pop('positive_control_ref',None)  # references never enter real run manifests
            selected.append(r)
    manifest=dict(dataset='TACO',tasks=selected,train_count=train_n,transfer_count=12,reserved_count=12,
        selection='fixed source hash reserve; scorer-qualified fixed dev hash; training difficulty-first stratum round-robin; no Actor results used',
        controls=dict(qualified=len(qualified),unqualified=len(candidates)-len(qualified),outcomes=outcomes,budget=budget.snapshot()),
        semantic_validation_limit='JSON/signature checks, statement-only examples, nonunique/float exclusions, independent archived solution agreement; finite controls do not prove all inputs valid or programs correct.')
    write_json(OUT/'Data_Manifest.json',manifest)
    print(json.dumps(dict(train=train_n,transfer=12,reserved=12,qualified=len(qualified),budget=budget.snapshot())))


def acceptance():
    import ast
    from compiler.compiler import Compiler
    from compiler.admission import admit_compiled_trace
    from compiler.primitive_compiler import PrimitiveCompiler
    from core.schemas import ExecutionTrace,AttemptRecord,CodeTaskInstance,VerifierFeedback
    from failure_evo.acquisition_selectors import revoked_evidence,eligible_failure,select
    from failure_evo.acquisition_adapters import CodeAdapter
    from failure_evo.skill_runtime import bundle_from_cards,sha
    from failure_evo.teacher_acquisition import AcquisitionScheduler,ReplayTeacher
    from memory.primitive_store import PrimitiveStore
    from memory.skill_registry import SkillRegistry
    from run_taco_function_acquisition import load_config,ROOT as REAL_ROOT,Experiment,opportunity_target_reached
    from run_failure_acquisition_pilot import runner,tree_hash,snapshot
    os.chdir(REPO)
    cfg,data=load_config()
    root=PREP/'acceptance';root.mkdir(exist_ok=True)
    b=PersistentBudget(root/'budget.jsonl',run_id='taco_focused_acceptance',protocol_hash=cfg['protocol_sha256'],
        max_calls=0,max_tokens=0,max_tools=40,max_cost_microusd=0,token_rate_microusd_per_million=0,
        tool_cost_upper_microusd=0,max_tool_milliseconds=800000,tool_milliseconds_upper=20000,wall_seconds=900)
    box=IsolatedCodeSandbox(image=IMAGE,budget=b,root=root)
    checks={}
    rev=json.loads((REPO/'reports/failure_acquisition_prepare_20261119/Evidence_Revocations.json').read_text())['records'][0]
    record=dict(rev['original_evidence'],success=False,execution_confirmed=True,failure_type='runtime_error',data_role='train',formal_training_eligible=True)
    assert revoked_evidence(record) and not eligible_failure(record)
    assert not select([record],'G+U',1,'test')[0]
    fresh=dict(record,evidence_sha256='new-receipt',evidence_ref='new-valid-execution')
    assert not revoked_evidence(fresh) and eligible_failure(fresh)
    checks['specific_invalid_evidence_revoked_not_whole_task']=True
    controls=read_json(PREP/'data_control_progress.json')
    selected={r['problem_id'] for r in data['tasks'] if r['data_role']!='reserved_eval'}
    assert all(x['public_pass'] and x['full_pass'] for x in controls if x['task_id'] in selected)
    assert selected.issubset({x['task_id'] for x in controls})
    assert not {x['task_id'] for x in controls}&{r['problem_id'] for r in data['tasks'] if r['data_role']=='reserved_eval'}
    # Exercise the final signature-preserving Solution bridge on a real task.
    row=next(r for r in data['tasks'] if r['data_role']=='train' and r['call_protocol']['kind']=='solution_method')
    original=REPO/'runs/taco_function_acquisition_20261120/preparation/private_data'/str(row['row_index'])/'positive_control.py'
    code=adapt_candidate(original.read_text(),row['call_protocol']['entry_point'])
    box.context('method_bridge',str(row['row_index']));fb=verify_task(public_task(row),code,box);assert fb.passed
    private=scoring_task(row,REPO);box.context('method_private',str(row['row_index']));pf=verify_task(private,code,box);assert pf.passed
    checks['real_function_and_method_data_dispatch']=True
    class PreviewReady(BaseException):pass
    class NoClient:
        def generate(self,**kwargs):
            wire=dict(model=cfg['actor']['model'],messages=[dict(role='system',content=kwargs['instructions']),dict(role='user',content=kwargs['input_text'])],
                      max_tokens=cfg['actor']['output_tokens'],thinking={'type':'disabled'},temperature=0,stream=False)
            write_json(OUT/'First_Actor_Request_Preview.json',dict(sent=False,wire=wire))
            raise PreviewReady()
    if not (root/'normal_actor').exists():snapshot(REPO/cfg['initial_library'],root/'normal_actor')
    native=runner(root/'normal_actor',cfg,NoClient(),box)
    assert native.executor.max_repairs==2 and not native.frozen_eval
    assert tree_hash(REPO/cfg['initial_library'])==cfg['initial_library_sha256']
    assert cfg['budget']['actor_calls']==4*data['train_count']+72
    assert cfg['budget']['teacher_calls']==12
    assert cfg['actor']['model']=='deepseek-flash' and cfg['teacher']['model']=='deepseek-v4-pro'
    try:native.run_episode(public_task(next(r for r in data['tasks'] if r['data_role']=='train')))
    except PreviewReady:pass
    else:raise AssertionError('ACTOR_PREVIEW_NOT_CAPTURED')
    checks['normal_actor_and_base_library_preserved']=True
    trace=ExecutionTrace(trace_id='private_canary',task_id=row['problem_id'],family='taco',benchmark='taco',query='public',success=True,
        code_history=[code],verifier_feedback=[pf],attempts=[AttemptRecord(attempt_index=0,stage='probe',candidate_code=code,verifier_feedback=pf)],validated_entry_point=row['call_protocol']['entry_point'])
    try:Compiler(str(root/'rejected')).compile(trace,'private_probe')
    except ValueError as exc:assert str(exc)=='PRIVATE_FEEDBACK_CANNOT_BE_COMPILED'
    else:raise AssertionError('PRIVATE_FEEDBACK_ACCEPTED')
    assert PrimitiveCompiler().compile_success_primitives(trace)==[]
    view=CodeAdapter().public_view(public_task(row))
    assert not any(k in view for k in ['solutions','input_output','private_scoring_ref','canonical_solution'])
    assert pf.executed_code not in json.dumps(view)
    checks['private_feedback_never_compiled_or_projected']=True
    public_trace=trace.model_copy(deep=True)
    public_trace.trace_id='public_taco_admission';public_trace.verifier_feedback=[fb]
    public_trace.attempts[0].verifier_feedback=fb
    box.context('native_admission',str(row['row_index']))
    admitted=admit_compiled_trace(public_trace,provenance='zero_model_interface_control',
        registry=SkillRegistry(str(root/'native_admission/registry.json')),sandbox=box,timeout_seconds=box.timeout_seconds)
    assert admitted.admitted and admitted.admission_bank=='active_seed_only',admitted
    checks['taco_native_admission_with_valid_public_replay']=True
    # HumanEval/59: unchanged final algorithm, explicit top-level candidate, one call.
    old=read_json(REPO/'runs/failure_acquisition_pilot_20261120/real_01/base/traces/trace_8c0627be.json')
    t=ExecutionTrace.model_validate(old)
    t.operation_contracts={'largest_prime_factor':dict(purpose='largest prime factor',parameters={'n':'composite int > 1'},preconditions='n composite > 1',output='int',side_effects='none',failure='outside contract unsupported')}
    candidates=PrimitiveCompiler().compile_success_primitives(t);assert len(candidates)==1
    c=candidates[0];assert c.code==old['attempts'][-1]['candidate_code']
    store=PrimitiveStore(root/'top_level/registry.json');card=store.observe_candidate(c.card,c.code)
    try:bundle_from_cards([card.model_dump(mode='json')])
    except ValueError:pass
    else:raise AssertionError('DRAFT_VISIBLE_IN_NORMAL_EXECUTION')
    pack=bundle_from_cards([card.model_dump(mode='json')],training_support=(card.primitive_id,card.source_sha256))
    call=pack['card_names'][card.primitive_id];box.context('top_level','HumanEval59')
    verified=box.run('from flowevo_skills import '+call+'\nassert '+call+'(81) == 3\n',module_bundle=pack)
    assert verified['passed'] and any(e['event']=='returned' and e['sha256']==card.source_sha256 for e in verified['skill_events'])
    # Reuse the old interface fixtures, explicitly not real learning or evaluation.
    op='def ordered(xs):\n    return sorted(xs, key=abs)\n'
    f=VerifierFeedback(benchmark='taco',task_id='fixture_A',passed=True,returncode=0,executed_code=op+'\nassert ordered([-4,1]) == [1,-4]',
        metrics={'acquisition_public_tests':['assert ordered([-4,1]) == [1,-4]'],'feedback_visibility':'public'})
    fixture=ExecutionTrace(trace_id='engineering_A',task_id='fixture_A',family='taco',benchmark='taco',query='Order by absolute magnitude',success=True,
        code_history=[op],attempts=[AttemptRecord(attempt_index=0,stage='fixture',candidate_code=op,verifier_feedback=f)],verifier_feedback=[f],validated_entry_point='ordered',independent_source_ids=['engineering_A'],
        operation_contracts={'ordered':dict(purpose='order absolute magnitude',parameters={'xs':'list[int]'},preconditions='integer list',output='list[int]',side_effects='none',failure='unsupported otherwise')},task_pattern='sort')
    cc=PrimitiveCompiler().compile_success_primitives(fixture)[0];ps=PrimitiveStore(root/'support/primitive.json');pc=ps.observe_candidate(cc.card,cc.code)
    pb=bundle_from_cards([pc.model_dump(mode='json')],training_support=(pc.primitive_id,pc.source_sha256));opname=pb['card_names'][pc.primitive_id]
    task=CodeTaskInstance(task_id='fixture_B',benchmark='taco',entry_point='maximum_value',prompt='Return the element with greatest absolute value.',
        metadata=dict(taco_function_subset=True,data_role='train',source_lineage_id='engineering_B',public_validation_only=True,training_validation_public=True,
                      public_training_tests=['assert maximum_value([-4,1]) == -4'],call_protocol={'entry_point':'maximum_value','parameters':['xs']}))
    teacher=ReplayTeacher([dict(code='from flowevo_skills import '+opname+'\ndef maximum_value(xs):\n    return '+opname+'(xs)[-1]\n')])
    def full_check(task,code,bundle):
        full=task.model_copy(deep=True);full.metadata['public_validation_only']=False;full.test_list=task.metadata['public_training_tests']
        with box.bind_dependencies(bundle):res=verify_task(full,code,box)
        return dict(verdict='FULL_CHECK_PASS' if res.passed else 'FULL_CHECK_FAIL',receipt_ref='engineering_private_receipt',source_sha256=sha(code),dependency_bundle_sha256=fingerprint(bundle))
    scheduler=AcquisitionScheduler(root=root/'support/acquisition',teacher=teacher,registry=SkillRegistry(str(root/'support/skills.json')),primitive_store=ps,sandbox=box,
        phase='train',max_attempts=2,training_validator=full_check)
    box.context('support','existing_engineering_fixture');result=scheduler.support_frozen(pc.primitive_id,task)
    assert result['status']=='SUPPORT_ADMITTED' and ps.get(pc.primitive_id).support_count==2
    assert scheduler.support_frozen(pc.primitive_id,task)['status']=='SUPPORT_ADMITTED'
    assert ps.get(pc.primitive_id).support_count==2 and teacher.calls==1
    bad=task.model_copy(deep=True);bad.metadata['data_role']='transfer_dev'
    try:scheduler.support_frozen(pc.primitive_id,bad)
    except RuntimeError:pass
    else:raise AssertionError('SUPPORT_IN_TRANSFER')
    checks['top_level_frozen_source_and_training_support']=True
    # Pure I/O regression; the historical algorithm and repair bytes are unchanged.
    hist=REPO/'experiments/flowevo_taco_lcb_20261019/trusted_rgf_20261020/counterfactuals/taco_0875'
    original=(hist/'original.py').read_text();fixed=(hist/'fixed.py').read_text()
    assert fixed==original.replace('import sys\n','import sys\nsys.setrecursionlimit(10000)\n',1)
    assert original==(REPO/'experiments/flowevo_taco_lcb_20261019/repair_v2/runs/taco_EASY/taco_0875/l1.py').read_text()
    inp=(hist/'public_input.txt').read_text();expected=(hist/'expected.txt').read_text().strip()
    outcomes=[]
    for label,program in [('original',original),('historical_manual_repair',fixed)]:
        wrapper='import io, sys, contextlib\nLEGACY='+repr(program)+'\ndef invoke(input_text):\n    old=sys.stdin\n    sys.stdin=io.TextIOWrapper(io.BytesIO(input_text.encode()))\n    out=io.StringIO()\n    try:\n        with contextlib.redirect_stdout(out):\n            exec(compile(LEGACY, "legacy_0875.py", "exec"), {"__name__":"__main__"})\n    finally:\n        sys.stdin=old\n    return out.getvalue().strip()\nassert invoke('+repr(inp)+') == '+repr(expected)+'\n'
        box.context('legacy_io',label);outcome=box.run(wrapper);outcomes.append(outcome['passed'])
    assert outcomes==[False,True]
    write_json(OUT/'Historical_Regression.json',dict(taco_0875=dict(original_sha256=sha(original),repair_sha256=sha(fixed),repair_origin='historical manually constructed counterfactual; replay.py explicitly makes patch without generation',new_interface='generic text input/output invocation only',outcomes=outcomes,new_teacher_learning=False),
        humaneval_59=dict(source_sha256=sha(c.code),algorithm_unchanged=True,top_level_callable=True,new_learning=False)))
    checks['historical_regressions_correctly_attributed']=True
    # Phase resume must skip completed phases. This exercises the real stage loop
    # with no models, using a separate temporary ROOT and counted no-op stages.
    import run_taco_function_acquisition as driver
    original_root=driver.ROOT;driver.ROOT=root/'resume_probe';seen=[]
    try:
        fake=object.__new__(Experiment)
        for name in driver.STAGES:setattr(fake,name,lambda name=name:seen.append(name) or {'stage':name})
        fake.run();fake.run();assert seen==list(driver.STAGES)
    finally:driver.ROOT=original_root
    records=[dict(source_kind='unresolved_failure',row={'capability_family_id':str(i%3)}) for i in range(6)]
    assert opportunity_target_reached(records)
    assert not opportunity_target_reached(records[:5])
    assert not opportunity_target_reached([dict(x,row={'capability_family_id':'one'}) for x in records])
    assert not opportunity_target_reached([dict(x,source_kind='already_callable') for x in records])
    # Hard zero-call budget; no actual transport is constructed by this check.
    assert b.snapshot()['calls']==0 and not b.snapshot()['unknown_or_pending_requests']
    assert not list(REAL_ROOT.glob('requests/**/request.json'))
    checks['bounded_budget_and_completed_stage_resume']=True
    value=dict(protocol_sha256=cfg['protocol_sha256'],checks=checks,new_model_requests=0,
        budget=b.snapshot(),data_controls_budget=read_json(OUT/'Data_Manifest.json')['controls']['budget'],
        engineering_fixture_label='one reused two-source interface fixture; not a learned ability or Actor autonomous transfer')
    write_json(OUT/'Acceptance.json',value)
    print(json.dumps(value,ensure_ascii=False))


def read_json(path):return json.loads(Path(path).read_text())


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--data-controls',action='store_true');parser.add_argument('--acceptance',action='store_true');args=parser.parse_args()
    if args.data_controls:data_controls()
    if args.acceptance:acceptance()
