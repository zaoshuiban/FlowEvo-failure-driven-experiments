"""Zero-API acceptance entry point for the skill transfer Pilot."""
import argparse
import json
import time
from pathlib import Path

from accept_post_pilot50_validator import fixture
from code_math.no_gold import NoGoldMathController, NoGoldPolicy, PublicMathTask
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.contracts import fingerprint
from failure_evo.math_skill_transfer import (
    ARMS, CumulativeTrainHandler, TransferShadowRelease, SingleFailureAdapter, SkillLifecycle, TransferTrain, SingleFailureTrainHandler, compare_dev_versions, acquire_single_failure,
    checkpoint_messages, compiler_job, evaluate_mock_checkpoint, freeze_manifest, paired_counts, skill_spec,
    replay_train_generation, text_experience, training_projection, validate_skill_decision,
)
from failure_evo.math_stream import DurableSolver, budget, save
from failure_evo.operator_contract import candidate_identity
from failure_evo.runtime import BudgetExhausted
from math_candidate_mock import assessment
from run_math_manual_lifecycle import problem


def raw(text):
    return dict(id='MOCK-'+fingerprint([text,time.time_ns()]),model='deepseek-flash',
                choices=[dict(message=dict(content=text),finish_reason='stop')],
                usage=dict(prompt_tokens=100,completion_tokens=50,total_tokens=150))


def expect_denied(fn, exception=PermissionError):
    try:
        fn()
    except exception:
        return
    raise AssertionError('expected fail-closed boundary')


def acceptance(root):
    root.mkdir(mode=0o700)
    train=PublicMathTask('source',problem(7))
    dev=PublicMathTask('dev','Compute the product of integers from 1 through 4, inclusive.')
    test=PublicMathTask('heldout','Find the value of the sum of the integers from 1 to 7, inclusive.')
    # Mock tasks only. The held-out task is marked an explicit synthetic family.
    manifest=freeze_manifest([
        dict(task_id=t.task_id,dataset='MOCK',dataset_revision='fixture-v1',source_row=i+1,
             statement_hash=fingerprint(t.problem),split=split,source_run=None,problem_family=t.task_id,
             exposure_status='NO_MATCH_IN_LOCAL_EXPOSURE_AUDIT',scoring_reference_id='MOCK-'+t.task_id,
             grading_method='math-stream-strict-v1')
        for i,(t,split) in enumerate(zip((train,dev,test),('TRAIN','DEV','TEST')))
    ],[train,dev,test])
    fact=dict(id='source-failure',task=train.to_dict(),correct=False,delivery_status='COMPLETE',
              final_output='The answer is 0',trajectory=[dict(text='The answer is 0',finish_reason='stop')])
    projected=training_projection(fact,manifest)
    expect_denied(lambda:training_projection(dict(fact,task=test.to_dict()),manifest))
    diagnosed=dict(kind='VERIFIER_CANDIDATE',subtask='integer sum',error_location='final sum',
                   error_type='incorrect arithmetic',observable_evidence='final answer is zero',
                   correction='independently recompute the finite integer sum',unknown_conditions='other targets',
                   verification_scope='OBJECTIVE_VALUE',assessment=assessment([fact['id']],role='DIAGNOSTIC'))
    plain=dict(diagnosed,kind='NON_EXECUTABLE_EXPERIENCE',verification_scope='NONE',
               assessment=assessment([fact['id']],decision='NEEDS_SPECIFICATION'))
    assert validate_skill_decision(plain,fact['id'])['kind']=='NON_EXECUTABLE_EXPERIENCE'
    cards=[text_experience(diagnosed,fact['id'])]
    assert skill_spec(dict(diagnosed,kind='SOLVER_CANDIDATE'),fact['id'])['skill_type']=='SOLVER_CANDIDATE'
    b=root/'B'
    a,registry,runner,cases=fixture(b)
    schema=json.loads(a['contract']['parameter_schema'])
    source=dict(a['operator_contract'],input_schema=schema,source_evidence=[fact['id']])
    wire_code=dict(code=Path(a['solver_path']).read_text()+'\n'+Path(a['matcher_path']).read_text(),
                   description=json.dumps(a['contract']),applicability=json.dumps(source))
    account=budget(b/'budget.jsonl','engineering:transfer-B','fixture',calls=2)
    def send(wire):
        body=json.loads(wire['messages'][-1]['content'])
        assert test.problem not in wire['messages'][-1]['content']
        return raw(json.dumps(wire_code if 'hypothesis' in body else diagnosed))
    provider=SingleFailureAdapter(b/'provider.jsonl',account,model='deepseek-flash',mock=True,sender=send)
    compiler=BoundedCompiler(provider,account,b/'compiler.jsonl','deepseek-flash')
    job=compiler_job(fact,manifest,stream_id=account.config['run_id'],family_id='single-failure')
    response=compiler.request(job,'induction',0,time.time())
    diagnosis=validate_skill_decision(json.loads(response['specification']),fact['id'])
    def compile_code(spec,value):
        job['specification']=json.dumps(value, sort_keys=True)
        return compiler.request(job,'candidate',0,time.time())
    learned=acquire_single_failure(projected,diagnosis,compile_code,b/'single',registry,runner,
                                   engineering=True,source_cases=cases)
    assert learned['status']=='UNVERIFIED' and learned['safety']['passed'] and learned['source']['passed']
    bad_source=dict(wire_code,code='import socket\n'+wire_code['code'],finish_reason='stop',delivery_status='PARSE_VALID')
    rejected=acquire_single_failure(projected,diagnosis,lambda *_:bad_source,b/'bad',registry,runner,engineering=True)
    assert rejected['status']=='STATIC_REJECTED'
    lifecycle=SkillLifecycle('B',b)
    artifact=learned['artifact']
    version=lifecycle.update('CREATE',artifact,evidence=[fact['id']])
    assert version==candidate_identity(artifact)
    expect_denied(lambda:lifecycle.freeze([artifact],registry,manifest['manifest_sha256']))
    schedule = TransferTrain(root/'train_schedule', manifest, [projected],
                             manifest_sha=manifest['manifest_sha256'], failures_sha=fingerprint([projected]))
    def train_handler(arm):
        folder = root/'train_handlers'/arm
        from failure_evo.math_operators import MathOperatorRegistry
        arm_registry = MathOperatorRegistry(folder/'registry.jsonl')

        def compiler_for(path, label):
            arm_budget = budget(path/'budget.jsonl','engineering:train:'+label,'fixture',calls=2)
            def sender(wire):
                body = json.loads(wire['messages'][-1]['content'])
                assert test.problem not in json.dumps(wire)
                return raw(json.dumps(wire_code if 'hypothesis' in body else plain if label=='C' else diagnosed))
            adapter = SingleFailureAdapter(path/'provider.jsonl',arm_budget,model='deepseek-flash',
                                           mock=True,sender=sender)
            return BoundedCompiler(adapter,arm_budget,path/'compiler.jsonl','deepseek-flash')
        return SingleFailureTrainHandler(arm,manifest,compiler_for,arm_registry,runner,folder,engineering=True)

    handlers = {arm:train_handler(arm) for arm in 'BCD'}
    from types import SimpleNamespace
    from failure_evo.math_cumulative_learning import CumulativeLearner

    cfg = dict(comparison='workflow', association_batch=4, bundle_bytes=24000,
               max_association_jobs=10, retrieval_limit=4, wire_upper=32768,
               output_upper=4096, max_generation_jobs=10)
    stream = SimpleNamespace(plan=dict(cumulative=cfg, window=10, r_max_extra_calls=40),
                             arms={'F':dict(path=root/'train_handlers'/'A')},
                             engineering=True, path=root, ph='fixture', health=lambda: None)

    def associate(wire):
        data = json.loads(wire['messages'][-1]['content'])
        return raw(json.dumps(dict(clusters=[], descriptions=[
            dict(evidence_id=e['evidence_id'], task_structure='finite sum',
                 observable_symptom='wrong value', possible_cause='unknown',
                 possible_correction='recompute', uncertainty='one witness') for e in data['evidence']
        ])))

    cumulative = CumulativeLearner(stream,'F',sender=associate,release=TransferShadowRelease())
    handlers['A'] = CumulativeTrainHandler(cumulative)
    scheduled = schedule.run(handlers, lambda: None)
    assert [r['job']['arm'] for r in scheduled]==list('ABCD')
    assert [r['result']['status'] for r in scheduled]==['PREFIX_ANALYZED','UNVERIFIED','TEXT_ONLY','UNVERIFIED']
    assert next(r['payload']['outcome'] for r in cumulative.memory.views.records() if r['kind']=='ASSOCIATION_DONE')=='ACCEPTED_UNVERIFIED'
    assert schedule.run(handlers, lambda: None)==scheduled

    from failure_evo.operator_contract import attach_contract
    from failure_evo.semantic_contract import artifact as make_artifact
    def version(solver):
        v=make_artifact(root/'dev_versions',solver,Path(a['matcher_path']).read_text(),a['contract'],
                        provenance={'origin':'MOCK'})
        return attach_contract(v,a['operator_contract'],evidence_ids=['e1','e2'],
                               protocol='engineering',original_ids=['source1','source2'])
    parent=version('def solve(parameters):\n return "0"')
    child=version(Path(a['solver_path']).read_text())
    dev_rows=[dict(split='DEV',statement_hash=fingerprint(c['proposal']['problem'])) for c in cases]
    dev_manifest=dict(rows=dev_rows,manifest_sha256=fingerprint(dev_rows))
    receipt=compare_dev_versions(registry,runner,parent,child,dev_manifest,cases,
                                 cases_sha=fingerprint(cases),engineering=True)
    assert receipt['improved'] and receipt['gains']==[0] and receipt['losses']==[]
    count=len(runner.events.records())
    assert compare_dev_versions(registry,runner,parent,child,dev_manifest,cases,
                                cases_sha=fingerprint(cases),engineering=True)==receipt
    assert len(runner.events.records())==count
    reverse=compare_dev_versions(registry,runner,child,parent,dev_manifest,cases,
                                 cases_sha=fingerprint(cases),engineering=True)
    assert not reverse['improved'] and reverse['losses']==[0]
    evolved=SkillLifecycle('D',root/'dev_lifecycle')
    pv=evolved.update('CREATE',parent,evidence=['e1'])
    evolved.update('REFINE',child,parents=[pv],evidence=['e2'],dev_receipt=receipt,registry=registry)
    # Engineering branch-result fixtures are explicitly injected to exercise scoring;
    # they are not admitted output from the unverified skill.
    native_path=root/'native'
    native_account=budget(native_path/'budget.jsonl','engineering:transfer-native','fixture',calls=1)
    native_client=DurableSolver(native_path,native_account,engineering=True,sender=lambda _:raw('The answer is 0'))
    native=NoGoldMathController(native_client,native_path/'controller.jsonl',
                                policy=NoGoldPolicy(reflection_calls=0)).solve(test,episode_id='native/1',sequence=1,resume=True)
    refs=[dict(task_id=test.task_id,problem_sha256=fingerprint(test.problem),gold_answer='28')]
    clients={}
    journals={}
    def answer(arm,wire):
        text=wire['messages'][-1]['content']
        assert ('historical text experience' in text)==(arm=='C')
        assert ('Bounded skill evidence' in text)==(arm in ('B','D'))
        return raw('The answer is '+('28' if arm in ('B','D') else '0'))
    for arm in ARMS:
        folder=root/'transfer'/arm
        bgt=budget(folder/'budget.jsonl','engineering:transfer-'+arm,'fixture',calls=1)
        clients[arm]=DurableSolver(folder,bgt,engineering=True,sender=lambda wire,a=arm:answer(a,wire))
        journals[arm]=folder/'controller.jsonl'
    injected={arm:dict(scope='OBJECTIVE_VALUE',result='synthetic fixture') for arm in ('B','D')}
    first=evaluate_mock_checkpoint(test,1,native,refs,clients,journals,cards=cards,skill_results=injected)
    assert first['B']['outcome']=='CORRECTED_ERROR' and first['C']['text_hits']==1
    # The second evaluation must replay existing responses and score locks.
    assert evaluate_mock_checkpoint(test,1,native,refs,clients,journals,cards=cards,skill_results=injected)==first
    assert all(client.budget.snapshot()['calls']==1 for client in clients.values())
    expect_denied(lambda:clients['A'].generate_no_gold(
        messages=checkpoint_messages(test,native,arm='A'),policy=NoGoldPolicy(delivery_profile='concise-v1'),request_id='overflow'),
        BudgetExhausted)
    save(root/'acceptance_summary.json',dict(scope='ENGINEERING_ONLY',paid_requests=0,
        dev_comparison=True,train_schedule_replay=True,single_failure_candidate=True,real_linux_worker=True,safety=True,source=True,
        no_oracle_blocks_release=True,test_input_blocked=True,paired=paired_counts([first]),branches=first))
    print('ENGINEERING_ONLY: candidate, Linux Worker, scoring, isolation and settled replay passed')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['acceptance'])
    parser.add_argument('--output',type=Path,required=True)
    acceptance(parser.parse_args().output)
