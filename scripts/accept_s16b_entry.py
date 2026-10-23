"""Zero-API acceptance through the explicit real runner; fixtures are not research.

Also rebuild two historical source checkpoints from raw responses, never old
mechanism cards. Source choice: first two distinct tasks with G l1 delivery
failure in frozen S15 chronological order. Do not consult later outcomes.
"""
import copy,json,socket,time
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import run_workflow_v2 as entry
from failure_evo.workflow_protocol_v2 import VERSION,delivery,repair_messages,prepare,Limits
from failure_evo.workflow_policy import WorkflowPolicy
from failure_evo.contracts import canonical,fingerprint
ROOT=entry.ROOT;S15=ROOT/'runs/s15_learn_reuse30_20261022_01';OUT=ROOT/'runs/s16b_preflight_20261022_02'
read=entry.read;write=entry.write;sha=entry.sha

def project_sources():
    selected=[];review=[]
    for task in read(S15/'tasks.json'):
        if len(selected)==2:break
        folder=S15/'branches'/task['task_id']/'G';wf=read(folder/'workflow.json')
        e=wf['events'][0];rawpath=folder/'response_1.json';raw=read(rawpath);c=raw['choices'][0]
        artifact=delivery(c['message']['content'],c['finish_reason'])
        ok=(e['stage']=='l1' and not artifact['code'] and c['finish_reason']=='length' and e['budget']['calls']==1)
        review.append(dict(task_id=task['task_id'],task_order=task['index'],stage=e['stage'],eligible=ok,reason='observed missing program; before retry with four remaining calls' if ok else 'not the fixed l1 missing-delivery selection criterion'))
        if not ok:continue
        feedback=dict(status='NO_COMPLETE_CODE',summary='No Python program was delivered; previous prose is not an algorithm to preserve.',public_cases=[],visibility='public')
        evidence=dict(task_public=task['task_public'],candidate_code='',public_feedback=feedback,generation_metadata=dict(finish_reason=c['finish_reason']),delivery_observation={k:v for k,v in artifact.items() if k!='code'},hook='before_native_retry',stage='l2a',observed_after_stage='l1',remaining_budget=dict(remaining_calls=4,remaining_tokens=204800-raw['usage']['total_tokens']))
        messages,_=repair_messages(task['task_public'],c['message']['content'],feedback,finish_reason=c['finish_reason'])
        proposed=prepare(messages,temperature=.5)
        retry_event=wf['events'][1]
        assert retry_event['stage']=='l2a' and retry_event['request']['timeout_seconds']>20
        packet=dict(projection_protocol=VERSION,old_interpretation_reused=False,public_evidence=evidence,
            lineage=dict(source_run=S15.name,arm='G',task_id=task['task_id'],task_order=task['index'],raw_response_path=str(rawpath.relative_to(ROOT)),raw_response_sha256=sha(rawpath),original_checkpoint_code_sha256=e['code_sha256'],problem_prompt_sha256=fingerprint(task['task_public']['prompt']),prior_development_exposure=True,independent_holdout=False,program_lineage='No program artifact; empty code hashes do not establish program identity or transfer.',old_specs_or_policies_included=False,future_outputs_included=False,audit_results_included=False),
            headroom=dict(hook='before_native_retry',position_reachable=True,allowed_action='request one host repair; public validation; native fallback',remaining_calls=4,minimum_calls_for_trial_and_fallback=2,shared_generic_can_do_same_action=True,efficacy_or_savings_proven=False,retry_input_upper=proposed.input_upper,observed_retry_remaining_seconds=retry_event['request']['timeout_seconds'],time_provenance='host retry attempt before rejected send; no later model output used; new replay deadline still enforced'))
        spec=prepare(entry.specification_messages(packet),limits=Limits(input_token_upper=65536),json_output=True)
        dest=OUT/'sources'/task['task_id'];write(dest/'checkpoint.json',packet);write(dest/'fresh_induction_request.json',dict(request=spec.body,sha256=spec.sha256,measures=spec.measures,provider_requests=0,specification_status='PENDING_FRESH_MODEL_INDUCTION'))
        selected.append(packet)
    assert len(selected)==2 and len({p['lineage']['task_id'] for p in selected})==2
    write(OUT/'selection.json',dict(rule='S15 task order; G only; l1 only; first two distinct missing-delivery sources; no future outcome selection',review=review,selected=[p['lineage'] for p in selected],mechanism_families_claimed=1,independent_transfer_claim=False))
    return selected

def raw(text,finish='stop'):
    return dict(model='deepseek-flash',choices=[dict(message=dict(content=text),finish_reason=finish)],usage=dict(prompt_tokens=5,completion_tokens=4,total_tokens=9))

def acceptance(packets):
    files=['scripts/run_workflow_v2.py','scripts/accept_s16b_entry.py','FlowEvo/src/failure_evo/workflow_protocol_v2.py','FlowEvo/src/failure_evo/workflow_runtime_v2.py','FlowEvo/src/failure_evo/workflow_policy.py']
    plan=dict(run_id='s16b_entry_acceptance_fixture_20261022_02',shared_protocol=VERSION,model='deepseek-flash',evidence_kind='engineering_fixture',frozen_files={p:sha(ROOT/p) for p in files},budgets={'solve':entry.prior.config(16,100,1000000),'learning':entry.prior.config(8,0,1000000,65536)},per_task=dict(max_calls=5,max_tokens=204800,max_tools=40,wall_seconds=600))
    plan['protocol_hash']=fingerprint(plan)
    solve_responses=iter([raw('Unfinished explanation.','length'),raw('```python\nprint(1)\n```')]*2+
        [raw('Unfinished explanation.','length'),raw('```python\nprint(0)\n```'),raw('```python\nprint(1)\n```')])
    spec={k:'ENGINEERING FIXTURE; no empirical mechanism claim' for k in entry.SPEC_FIELDS}
    bad=json.dumps(dict(code='def repair_operator(context):\n    return getattr(context, "x", None)',description='fixture',applicability='fixture'))
    good=json.dumps(dict(code='def repair_operator(context):\n    return {"status":"declined","reason":"fixture only"}',description='fixture',applicability='fixture'))
    learning_responses=iter([raw(json.dumps(spec)),raw(bad),raw(good),raw(json.dumps({'memory':'x'*6001})),raw('{"memory":"ENGINEERING FIXTURE MEMORY"}')])
    sent=[];received=[];fault={'unknown':False}
    def factory(channel):
        def send(wire):
            sent.append(dict(channel=channel,body=json.loads(wire),sha256=entry.prior.hashlib.sha256(wire).hexdigest(),synthetic_provider=True))
            if fault['unknown']:raise TimeoutError('engineering fixture: send result unknown')
            value=next(solve_responses if channel=='solve' else learning_responses);received.append(value);return value
        return send
    def evaluator(task):
        def check(public,code):
            good=code.strip()=='print(1)'
            return dict(status='PUBLIC_PASS' if good else 'WRONG_ANSWER',visibility='public',tests_run=1,tests_passed=int(good),cases=[dict(input='',expected='1',actual='1' if good else '0',exception_class=None,visibility='public',legal_verified=True)])
        return check
    runner=entry.ExperimentRunner(OUT/'entry_acceptance',plan,factory,evaluator_factory=evaluator,decision_runner=lambda *a:dict(status='request_repair',instruction='Fixture targeted repair',reason='fixture'))
    task=dict(task_id='engineering_fixture',dataset='taco',difficulty='easy',task_public=dict(problem_id='engineering_fixture',prompt='Engineering fixture only; print 1.'),public_cases=[])
    results={}
    # Learn through the exact production dispatch, not direct calls to helpers.
    jobs=[dict(kind='induction',key='fresh-source',packet=packets[0]),dict(kind='candidate',key='fresh-source'),dict(kind='revision',key='fresh-source',diagnosis=dict(passed=False,findings=['forbidden getattr'])),dict(kind='memory',key='M-update',public_evidence=[packets[0]['public_evidence']],allow_revision=True)]
    runner.dispatch(jobs)
    for arm in ('G','M'):results[arm]=runner.solve(arm,task)
    card=WorkflowPolicy('fixture','v1','UNEXECUTED_FIXTURE','fixture-sha',runner.context,'engineering only',('fixture-event',),('fixture-task',),allowed_feedback=('NO_COMPLETE_CODE',),structural_statuses=('NO_COMPLETE_CODE',))
    outcomes=[]
    # Only admission/decision surfaces are simulated; the actual WorkflowPlugin,
    # controller, host call, verification, fallback, ledgers and wire path run.
    with patch.object(runner.registry,'snapshot',return_value=NS(cards=(card,),snapshot_id='fixture-snapshot',task_index=1)),patch.object(runner.registry,'valid',return_value=True),patch.object(runner.registry,'reserve_opportunity',return_value='fixture-opportunity'),patch.object(runner.registry,'complete_opportunity',side_effect=lambda *a,**kw:outcomes.append(kw['outcome'])):
        results['F']=runner.solve('F',task)
    assert all(x['status']=='PUBLIC_ACCEPTED' for x in results.values())
    assert [results[a]['budget']['calls'] for a in ('G','M','F')]==[2,2,3]
    assert results['F']['hook_events'][0]['status']=='declined' and results['F']['events'][-1]['stage']=='l2a'
    assert results['F']['hook_events'][0]['actual_cost']['model_calls']==1
    assert runner.budgets['solve'].calls==7 and runner.budgets['learning'].calls==5
    assert len(runner.transports['learning'].audit)==5
    assert runner.outputs['M-update']['versions'][0]['diagnosis']['error']=='MEMORY_TEXT_TOO_LONG'
    # A new task with no local calls never enters the provider.
    zero=copy.deepcopy(task);zero['task_id']='zero-budget';zero['task_public']['problem_id']='zero-budget'
    before=len(sent);z=runner.solve('G',zero,task_limits=dict(plan['per_task'],max_calls=0));assert len(sent)==before and z['budget']['calls']==0 and z['events'][0]['request_state']=='NOT_SENT'
    for channel,tr in runner.transports.items():
        entries=[x for x in sent if x['channel']==channel]
        completed=[x for x in tr.audit if x['status']=='COMPLETED']
        assert len(entries)==len(completed)
        assert all(a['sha256']==b['request_sha256'] for a,b in zip(entries,completed))
    # M and F refinements flow through the shared solve entry; no old transport.
    assert any('ENGINEERING FIXTURE MEMORY' in canonical(s['body']) for s in sent if s['channel']=='solve')
    assert any('Fixture targeted repair' in canonical(s['body']) for s in sent if s['channel']=='solve')
    # Real entry cannot take the fixture plan as a paid-run grant.
    write(OUT/'fixture_authorization_denied.json',dict(run_id=plan['run_id'],protocol_hash=plan['protocol_hash'],model=plan['model'],budgets=plan['budgets'],allow_real_api=True))
    try:entry.execute(OUT/'entry_acceptance/plan.json',OUT/'fixture_authorization_denied.json')
    except PermissionError:denied=True
    else:raise AssertionError('fixture accepted as real grant')
    # Unknown sends retain their reservation and block further adaptive calls
    # across BOTH channels, even if the caller still has nominal allowance.
    fault['unknown']=True
    try:runner.induction('unknown-fixture',packets[0])
    except TimeoutError:pass
    else:raise AssertionError('unknown request not surfaced')
    before=len(sent);blocked=copy.deepcopy(task);blocked['task_id']='blocked-after-unknown';blocked['task_public']['problem_id']=blocked['task_id']
    stopped=runner.solve('G',blocked)
    assert len(sent)==before and stopped['budget']['calls']==0
    assert runner.budgets['learning'].snapshot()['unknown_or_pending_requests']==['unknown-fixture/spec']
    report=dict(passed=True,new_api_requests=0,fake_provider_responses=len(received),fake_send_attempts=len(sent),unknown_mock_send_preserved_and_stops_run=True,fake_solve_responses=7,fake_learning_responses=5,actual_operator_source_executions=0,actual_problem_program_executions=0,real_admissions=0,
        arm_calls={a:results[a]['budget']['calls'] for a in results},F_failed_host_repair_falls_back=True,zero_budget_does_not_send=True,exact_preflight_wire_sent=True,fixture_paid_execution_rejected=denied,
        learning_capabilities=[x['request_id'] for x in runner.transports['learning'].audit],production_entry='scripts/run_workflow_v2.py',acceptance_and_execute_share='ExperimentRunner + dispatch/solve + shared v2 transport/controller',limitation='Provider/checker/decision/admission fixture surfaces; no model efficacy, isolation or real authorization claim')
    write(OUT/'entry_acceptance_result.json',report);return report

def main():
    if OUT.exists():raise FileExistsError('preserve acceptance outputs; use a fresh run for another execution')
    OUT.mkdir(parents=True)
    frozen={str(p):sha(p) for d in (S15,ROOT/'runs/s16a_protocol_review_20261022_01') for p in d.rglob('*') if p.is_file()}
    write(OUT/'historical_before.json',frozen)
    def forbidden(*a,**k):raise AssertionError('network/key/old API forbidden in acceptance')
    with patch.object(entry.urllib.request,'urlopen',side_effect=forbidden),patch.object(entry.prior,'configured_api_key',side_effect=forbidden),patch.object(entry.prior.DeepSeekGenerator,'_post',side_effect=forbidden),patch.object(socket.socket,'connect',side_effect=forbidden):
        packets=project_sources();result=acceptance(packets)
    changed=[p for p,h in frozen.items() if sha(p)!=h];assert not changed
    write(OUT/'historical_integrity.json',dict(files_checked=len(frozen),changed=changed))
    write(OUT/'summary.json',dict(entry_acceptance=result,selected_source_tasks=[p['lineage']['task_id'] for p in packets],new_specifications_generated=0,new_specification_requests_prepared=2,old_interpretation_reused=False,new_api_requests=0))
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
