"""S16-B bounded real workflow generation/source acceptance. One family only.
Uses the accepted v2 ExperimentRunner and its persistent transports. No generic
fallback success is counted. Frozen source/negative checks precede admission.
"""
import copy,json,os,tempfile,time,urllib.request
from pathlib import Path
import run_workflow_v2 as entry
from failure_evo.contracts import PublicFeedback,canonical,fingerprint
from failure_evo.runtime import Budget,BudgetExhausted
from failure_evo.workflow_protocol_v2 import WorkflowClient,revise_policy,delivery
from failure_evo.workflow_policy import WorkflowPolicy,worker_context,validate_source,validate_decision
ROOT=entry.ROOT;OUT=ROOT/'runs/s16b_source_20261022_01';PRE=ROOT/'runs/s16b_preflight_20261022_02'
read=entry.read;write=entry.write;sha=entry.sha
FAMILY='missing_program_delivery_policy'

def plan_and_inputs():
    packet=read(PRE/'sources/taco_0313/checkpoint.json')
    if sha(ROOT/packet['lineage']['raw_response_path'])!=packet['lineage']['raw_response_sha256']:raise ValueError('source raw changed')
    original=read(ROOT/packet['lineage']['raw_response_path']);c=original['choices'][0]
    assert not delivery(c['message']['content'],c['finish_reason'])['code']
    full=next(t for t in read(ROOT/'runs/s15_learn_reuse30_20261022_01/tasks.json') if t['task_id']=='taco_0313')
    task={k:full[k] for k in ('task_id','dataset','difficulty','task_public','public_cases','reference_path','reference_sha256')}
    assert sha(task['reference_path'])==task['reference_sha256']
    files=[Path(__file__),ROOT/'scripts/run_workflow_v2.py',ROOT/'scripts/learn_reuse30.py',ROOT/'scripts/compare30_workflows.py',entry.prior.old.WORKER,entry.prior.old.ACCEPTANCE,PRE/'sources/taco_0313/checkpoint.json',Path(task['reference_path'])]+list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))
    p=dict(run_id=OUT.name,shared_protocol=entry.VERSION,model='deepseek-flash',evidence_kind='real_experiment',
        frozen_files={str(f.relative_to(ROOT)):sha(f) for f in files},budgets={'learning':entry.prior.config(3,0,270000,65536),'solve':entry.prior.config(4,180,200000)},
        per_task=dict(max_calls=2,max_tokens=81920,max_tools=30,wall_seconds=180),
        families=[FAMILY],source_task='taco_0313',future_task='taco_0511',source_packet_sha256=fingerprint(packet),public_cases_sha256=fingerprint(task['public_cases']),
        max_specifications=1,max_initial_candidates=1,max_revisions=1,max_source_calls_per_version=2,
        request_limits=dict(learning_input_upper=65536,solve_input_upper=32768,output_tokens=8192,thinking='disabled',reasoning_effort='none',temperature=0),
        prices=dict(url='https://api-docs.deepseek.com/quick_start/pricing/',checked='2026-10-22',advertised_version='DeepSeek-V4.1-Flash-1017',peak_input_cache_miss_usd_per_million=.3,peak_output_usd_per_million=1.2,invoice_known=False),
        quoted_full_bound_usd=.1671168,persistent_conservative_hard_usd=.47,local_tool_currency_cost=None,
        negative_checks=['PUBLIC_PASS','UNKNOWN','zero_calls','one_call','missing_prompt','complete_program_length_PUBLIC_PASS','semantic_failure_complete_program','missing_context'],
        positive_checks=['source_four_calls','source_two_calls'],
        stopping='Stop source trials immediately on actual policy-induced public pass; otherwise <=2 per version. Revise once if static or functional failure. No second family, no generic continuation, no task stream.',
        admission='source public pass AND actual policy/negative/boundary/zero-budget fallback checks; one future task taco_0511, <=1 opportunity; no trial executed this run',
        authorization_basis='Current user explicitly requests S16-B real experiment with <=2 families, <=6 generation calls and <=8 source calls. This run freezes only one family, 3+4 calls, fresh budget.',
        source_trial_interpretation='Each trial invokes the same actual policy on the ORIGINAL source checkpoint, not generic fallback or independent tasks; first public pass stops trials.')
    p['protocol_hash']=fingerprint(p)
    return p,packet,task

def authorize(plan):
    return dict(run_id=plan['run_id'],protocol_hash=plan['protocol_hash'],model=plan['model'],budgets=plan['budgets'],allow_real_api=True,authorization_basis=plan['authorization_basis'])

def sender_factory(channel):
    def send(wire):
        key=entry.prior.configured_api_key()
        if not key:raise RuntimeError('configured API credential missing')
        req=urllib.request.Request('https://api.deepseek.com/chat/completions',data=wire,headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
        with urllib.request.urlopen(req,timeout=90) as reply:return json.loads(reply.read())
    return send

def validate(runner,card,packet,task,folder):
    ev=packet['public_evidence'];b=Budget(max_calls=4,max_tokens=163840,max_tools=30,wall_seconds=180)
    base=worker_context(ev['task_public'],ev['candidate_code'],ev['public_feedback'],ev['generation_metadata'],b)
    checks=[]
    def check(name,payload,want):
        output=runner.judge.decision(card,payload)
        try:d=validate_decision(output);passed=d['status'] in want
        except ValueError:d=output;passed=False
        checks.append(dict(name=name,input=payload,decision=d,passed=passed))
        write(folder/'decision_checks.json',checks);return d
    check('source_four_calls',copy.deepcopy(base),['request_repair'])
    two=copy.deepcopy(base);two['remaining_budget']['remaining_calls']=2;check('source_two_calls',two,['request_repair'])
    for name,status,calls in [('PUBLIC_PASS','PUBLIC_PASS',4),('UNKNOWN','UNKNOWN',4),('zero_calls','NO_COMPLETE_CODE',0),('one_call','NO_COMPLETE_CODE',1)]:
        x=copy.deepcopy(base);x['public_feedback']['status']=status;x['remaining_budget']['remaining_calls']=calls;check(name,x,['declined'])
    x=copy.deepcopy(base);x['task_public']['prompt']='';check('missing_prompt',x,['declined','error'])
    x=copy.deepcopy(base);x['candidate_code']='print(1)';x['public_feedback']['status']='PUBLIC_PASS';check('complete_program_length_PUBLIC_PASS',x,['declined'])
    x=copy.deepcopy(base);x['candidate_code']='print(1)';x['generation_metadata']['finish_reason']='stop';x['public_feedback']['status']='WRONG_ANSWER';check('semantic_failure_complete_program',x,['declined'])
    check('missing_context',{},['declined','error'])
    result=dict(passed=False,checks=checks,trials=[],source_result=None,host_fallback=None)
    if not all(c['passed'] for c in checks):
        result['reason']='actual policy applicability/refusal checks failed; source API not sent';write(folder/'functional.json',result);return result
    # Real generated policy was executed in Worker above. Actual host budget
    # rejection now checks that this positive decision cannot cause a request.
    client=WorkflowClient(runner.transports['solve'],FAMILY+'/'+card.version+'/exhausted')
    before=runner.budgets['solve'].calls
    try:client.host_repair(base,checks[0]['decision']['instruction'],Budget(max_calls=0))
    except BudgetExhausted:fallback=runner.budgets['solve'].calls==before
    else:fallback=False
    result['host_fallback']=dict(passed=fallback,original_unchanged=True,reason='actual worker decision rejected by zero host budget before provider call; native fallback eligibility preserved',generic_continuation_calls=0)
    for trial in range(1,3):
        local=Budget(**runner.plan['per_task']);payload=worker_context(ev['task_public'],ev['candidate_code'],ev['public_feedback'],ev['generation_metadata'],local)
        actual=runner.judge.decision(card,payload)
        try:decision=validate_decision(actual)
        except ValueError:decision=dict(status='error',reason='decision contract')
        if decision['status']!='request_repair':
            result['trials'].append(dict(trial=trial,decision=decision,host_calls=0,applied=False));break
        client=WorkflowClient(runner.transports['solve'],FAMILY+'/'+card.version+f'/source-{trial}')
        response=client.host_repair(payload,decision['instruction'],local)
        (folder/f'source_trial_{trial}.py').write_text(response['code']);write(folder/f'source_response_{trial}.json',response)
        public=runner.judge.run(task['task_id'],response['code'],task['public_cases'])
        trace=dict(trial=trial,decision=decision,host_calls=local.calls,host_tokens=local.used_tokens,finish_reason=response['finish_reason'],source_sha256=sha(folder/f'source_trial_{trial}.py'),public=public,applied=public['passed'],attribution='actual generated policy request -> same-budget host repair -> actual isolated public validation; no generic fallback')
        result['trials'].append(trace);result['source_result']=public
        result['delivery']=response['delivery'];result['passed']=public['passed'] and fallback
        write(folder/'functional.json',result);runner.save()
        print('SOURCE',card.version,trial,public['status'],public['tests_passed'],public['tests_run'],response['finish_reason'],flush=True)
        if result['passed']:break
    write(folder/'functional.json',result);return result

def admit(runner,card,event,folder):
    result=read(folder/'functional.json');path=folder/'functional.json';files=[dict(path=str(path),sha256=sha(path)),dict(path=str(folder/'static.json'),sha256=sha(folder/'static.json')),dict(path=str(entry.prior.old.ACCEPTANCE),sha256=sha(entry.prior.old.ACCEPTANCE))]
    checks={k:dict(passed=True,evidence_sha256=sha(path),artifact_sha256=card.artifact_sha256,execution='isolated_actual_source') for k in ('source_repair','boundary','inapplicable','host_fallback')}
    checks['source_repair'].update(event_id=event['event_id'],original_sha256=event['candidate_sha256'],host_public_outcome='passed',action='applied',tests_run=result['source_result']['tests_run'],tests_passed=result['source_result']['tests_passed'])
    checks['isolated_worker']=dict(passed=True,evidence_sha256=sha(entry.prior.old.ACCEPTANCE),artifact_sha256=card.artifact_sha256)
    checks['static_contract']=dict(passed=True,evidence_sha256=sha(folder/'static.json'),artifact_sha256=card.artifact_sha256)
    proof=dict(role='NURSERY_ADMISSION',operator_id=card.operator_id,version=card.version,artifact_sha256=card.artifact_sha256,fingerprint=card.evidence_fingerprint.to_dict(),scope=card.evidence_scope,evidence_ids=list(card.evidence_ids),experiment_id=runner.plan['run_id'],evaluated_at=time.time(),files=files,checks=checks)
    write(folder/'admission.json',proof)
    runner.registry.admit_nursery(card,folder/'admission.json',experiment_id=runner.plan['run_id'],stream_id=runner.plan['run_id']+'-future-taco_0511',after_task=0,effective_from=1,opportunity_limit=1,at=time.time())
    write(folder/'probation_scope.json',dict(task_ids=['taco_0511'],maximum_opportunities=1,execution_started=False,no_generic_success_attribution=True,stream_id=runner.plan['run_id']+'-future-taco_0511'))

def run():
    plan,packet,task=plan_and_inputs()
    # Keep temporary source mounts on the local Colima-shared repository path.
    os.environ.update(DOCKER_CONFIG=str(ROOT/'runs/s12c_functional_20261021_01/docker_public'),DOCKER_HOST='unix:///Users/majiatong/.colima/default/docker.sock')
    historical={str(p):sha(p) for d in [ROOT/'runs/s15_learn_reuse30_20261022_01',ROOT/'runs/s16a_protocol_review_20261022_01',PRE] for p in d.rglob('*') if p.is_file()}
    runner=entry.ExperimentRunner(OUT,plan,sender_factory)
    (OUT/'tmp').mkdir();tempfile.tempdir=str(OUT/'tmp');os.environ['TMPDIR']=str(OUT/'tmp')
    write(OUT/'authorization.json',authorize(plan));write(OUT/'historical_before.json',historical);write(OUT/'source_packet.json',packet);write(OUT/'task_public_frozen.json',task)
    cards=[];status='STARTED';error=None
    try:
        # Before any API, verify the existing public scorer/Worker on the source.
        positive=runner.judge.run(task['task_id'],Path(task['reference_path']).read_text(),task['public_cases'])
        negative=runner.judge.run(task['task_id'],"print('INVALID_FIXTURE')",task['public_cases'])
        write(OUT/'scorer_acceptance.json',dict(positive=positive,negative=negative))
        if not positive['passed'] or negative['passed']:raise RuntimeError('source public evaluator unavailable/untrusted')
        ev=packet['public_evidence'];now=time.time()
        event=runner.stores['F'].record(stream_id=OUT.name+'-development',task_id=task['task_id'],family_id=FAMILY,stage='l1',code=ev['candidate_code'],feedback=PublicFeedback('NO_COMPLETE_CODE'),observed_at=now,available_from=now,finish_reason='length',provenance_group_id=task['task_id'],synthetic=False)
        write(OUT/'source_event.json',event)
        print('ACCEPTED_LOCAL_SOURCE; frozen hard model budget $0.47; max 3 learning + 4 source calls',flush=True)
        runner.induction(FAMILY,packet);print('FRESH_SPECIFICATION_RECEIVED',flush=True)
        try:runner.candidate(FAMILY)
        except ValueError as exc:
            if 'candidate_response' not in runner.outputs[FAMILY]:raise
            runner.outputs[FAMILY]['static']=dict(passed=False,error=str(exc))
        response=runner.outputs[FAMILY]['candidate_response']
        for revision in range(2):
            folder=OUT/'operators'/f'v{revision}';folder.mkdir(parents=True);write(folder/'raw_compile_response.json',response)
            try:
                artifact=entry.prior.json_response(response)
                if set(artifact)!={'code','description','applicability'} or any(not isinstance(v,str) or not v.strip() for v in artifact.values()):raise ValueError('COMPILE_OUTPUT_CONTRACT_ERROR')
                write(folder/'artifact.json',artifact);(folder/'operator.py').write_text(artifact['code']);static=validate_source(artifact['code'])
            except ValueError as exc:static=dict(passed=False,error=str(exc))
            write(folder/'static.json',static);diagnosis=static;solver_response=None;proposed_code=None
            if static['passed']:
                card=WorkflowPolicy(FAMILY,f'v{revision}',str(folder/'operator.py'),sha(folder/'operator.py'),runner.context,'Missing-program delivery; source-effective only; at most one future taco_0511 probation opportunity', (event['event_id'],),(task['task_id'],),allowed_feedback=('NO_COMPLETE_CODE',),structural_statuses=('NO_COMPLETE_CODE',),source_mode='chronological_simulation')
                runner.registry.register(card,time.time());cards.append(card)
                result=validate(runner,card,packet,task,folder);diagnosis=result
                if result['passed']:
                    admit(runner,card,event,folder);status='SOURCE_EFFECTIVE_NURSERY_LIMITED';break
                trial=len([x for x in result['trials'] if x.get('host_calls')])
                if trial:
                    solver_response=read(folder/f'source_response_{trial}.json');proposed_code=solver_response['code']
            print('CANDIDATE',revision,'STATIC',static['passed'],'FUNCTIONAL',diagnosis.get('passed'),flush=True)
            if revision==1:status='ARCHIVED_NO_EFFECTIVE_OPERATOR';break
            # Same accepted shared revision path; full source program/finish reason
            # included once in compact diagnostic. No new spec or fresh candidate.
            revised=revise_policy(runner.transports['learning'],runner.outputs[FAMILY]['base_prompt'],response['text'],diagnosis,request_prefix=FAMILY,solver_response=solver_response,proposed_code=proposed_code)
            runner.outputs[FAMILY]['revision']=revised;runner.save();response=revised['response'];print('ONE_REVISION_RECEIVED',flush=True)
    except Exception as exc:
        status='STOPPED_ERROR';error=dict(type=type(exc).__name__,message=str(exc)[:1500]);print('STOPPED',error['type'],flush=True)
    finally:
        runner.save()
        changed=[p for p,h in historical.items() if sha(p)!=h];write(OUT/'historical_integrity.json',dict(checked=len(historical),changed=changed))
        rows=[x for t in runner.transports.values() for x in t.audit if x.get('raw_response')]
        costs=sum((x['raw_response']['usage']['prompt_tokens']*.3+x['raw_response']['usage']['completion_tokens']*1.2)/1e6 for x in rows if x['status']=='COMPLETED')
        summary=dict(status=status,error=error,source_task=task['task_id'],families=1,actual_response_count=len(rows),generation_calls=runner.budgets['learning'].calls,source_calls=runner.budgets['solve'].calls,total_response_tokens=sum(x['raw_response']['usage']['total_tokens'] for x in rows),peak_quote_estimated_usd=costs,actual_invoice=None,hard_budget_usd=.47,budgets={k:b.snapshot() for k,b in runner.budgets.items()},cards=[dict(card=c.to_dict(),review=runner.registry.review(c)) for c in cards],future_trials_run=0,historical_changed=changed)
        write(OUT/'summary.json',summary);print(json.dumps({k:v for k,v in summary.items() if k not in ('budgets','cards')},ensure_ascii=False),flush=True)
    if error:raise RuntimeError('S16-B stopped; inspect saved error; no automatic retry')
if __name__=='__main__':run()
