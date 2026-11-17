"""A2 Mock execution; opt-in frozen A3 requires separate explicit authorization. No Gate."""
import argparse
import fcntl
import json
from pathlib import Path
from time import time
from types import SimpleNamespace

from alfworld_ import recovery_applicability_learning as learning
from alfworld_.failure_learning import EnvironmentPolicyRunner,static_check_detailed
from alfworld_.python_recovery_feedback import delivery,parse_delivery
from alfworld_.recovery_applicability import worker_artifact
from alfworld_.recovery_acquisition import RecoveryAdapter,stage_request
from alfworld_.route_a_training_labels import model_projection
from alfworld_.skill_acquisition import StrictTrainEnv,MODEL,INPUT_LIMIT
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import fingerprint,canonical,PublicFeedback
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator,FailureOperatorRegistry
from failure_evo.math_stream import read,sha
from failure_evo.run_health import assert_run_healthy,trusted_usage,RunUnhealthy
from failure_evo.runtime import BudgetExhausted
from prepare_alfworld_applicability_data import S0,BASE,ROOT,S0_RESULT_SHA
from prepare_alfworld_route_a_training_checkpoints import load_origin
from run_alfworld_skill_acquisition import create_accounts,IMAGE,WORKER
from run_alfworld_applicability_pilot import learned_decision,checkpoint_context
import run_alfworld_python_recovery_feedback as pilot

DATA=ROOT/'runs/alfworld_route_a_a1b_collection_20261113_01'
CODE=S0/'candidate_0/revision_02/decoded.py'
VERSION=learning.VERSION


def wire(root,packet,prompt,temperature,input_policy=None):
    provider=RecoveryAdapter(root/'provider.jsonl',None,model=MODEL,mock=True,sender=lambda _:None,
        stage='analyze',payload=packet,parser=parse_delivery,protocol=VERSION,
        analysis_prompt=prompt,temperature=temperature,max_wire_input_upper=input_policy['max_input_tokens'] if input_policy else INPUT_LIMIT,
        wire_input_policy=input_policy)
    return provider.preflight(dict(phase='induction',max_tokens=4096,
        discovery=dict(stage='analyze',payload_sha256=fingerprint(packet))))


def prepare(output,*,dataset=DATA,temperature=0.6,fixture_roles=None,input_policy=None,revision_policy=None,input_scheme='F'):
    if output.exists():raise FileExistsError('new A2 run required')
    roles=learning.load_dataset(dataset) if fixture_roles is None else learning.validate_rows(fixture_roles)
    if sha(CODE)!=learning.RECOVERY_SHA:raise PermissionError('frozen recovery drift')
    output.mkdir(mode=0o700,parents=True)
    packet=learning.training_packet(roles['TRAIN'],CODE.read_text())
    if input_policy:
        from alfworld_.recovery_learning_input import organize
        organized=organize(roles['TRAIN'],CODE.read_text(),None if input_scheme=='F' else int(input_scheme.split('-')[1]))
        packet=organized['packet']
        if revision_policy is None:raise ValueError('freeze revision input policy separately')
    body=wire(output,dict(candidate_id='candidate_0',training_input=packet),learning.INITIAL_PROMPT,temperature,input_policy)
    input_upper=len(canonical(body).encode())+256
    backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
    # A1 frozen order and admission; do not retune on fixture or real outcomes.
    n,v=len(roles['TRAIN']),len(roles['TRAIN_VALIDATION'])
    p=sum(r['label']=='MATCH' for rows in roles.values() for r in rows)
    plan=dict(version=VERSION,run_id='mock:'+output.name,scope='MOCK_ENGINEERING_ONLY',
        temperature=temperature,model=MODEL,max_calls=8,max_tokens=8*(INPUT_LIMIT+4096),
        max_cost_microusd=700000,worker_calls=8*(n+v+18*p)+11*19+42,
        environment_steps=2*(8*p*50+11*50),episode_limit=50,source_window=18,max_stagnant_repeats=2,
        environment_type='TEXTWORLD_TRAIN',environment=pilot.environment_manifest(read(dataset/'protocol.json')['data_root']),
        worker=backend.manifest(),source_mode='ENGINEERING_FIXTURE' if fixture_roles is not None else 'A1B_CONTROLLED',
        dataset=str(dataset.resolve()),dataset_sha256=sha(dataset/'dataset.json'),
        roles_sha256=fingerprint(roles),packet_sha256=fingerprint(packet),recovery_sha256=sha(CODE),
        rules=learning.SELECTION_RULES,rules_sha256=fingerprint(learning.SELECTION_RULES),
        initial_wire_sha256=fingerprint(body),initial_input_upper=input_upper,revision_input_upper=INPUT_LIMIT,
        output_upper=4096,paid_api_authorized=False,A3_ready=False,
        coverage=learning.coverage(roles),code_sha256={str(p.resolve()):sha(p) for p in
            [Path(__file__),ROOT/'FlowEvo/src/alfworld_/recovery_applicability_learning.py',
             ROOT/'FlowEvo/src/alfworld_/recovery_acquisition.py',ROOT/'FlowEvo/src/alfworld_/recovery_applicability.py',
             ROOT/'FlowEvo/src/alfworld_/failure_learning.py',ROOT/'scripts/run_alfworld_python_recovery_feedback.py']})
    if input_policy:
        from alfworld_.recovery_learning_input import FEEDBACK_RULE,PRICE
        plan.update(scope='A3_PREPARATION_MOCK_ONLY',input_policy=input_policy,revision_policy=revision_policy,
            run_id='a3:'+output.name,
            engineering_fixture=fixture_roles is not None,
            input_scheme=input_scheme,input_organization={k:v for k,v in organized.items() if k!='packet'},feedback_rules=FEEDBACK_RULE,
            max_tokens=4*(input_policy['max_input_tokens']+4096)+4*(revision_policy['max_input_tokens']+4096),
            max_cost_microusd=3500000,source_mode='A1CD_CONTROLLED',revision_input_upper=revision_policy['max_input_tokens'],
            pricing_reference=PRICE,prompt_sha256={'initial':fingerprint(learning.INITIAL_PROMPT),
                                                'revision':fingerprint(learning.REVISION_PROMPT)})
        for file in ('FlowEvo/src/alfworld_/recovery_learning_input.py','FlowEvo/src/failure_evo/wire_input_policy.py',
                     'FlowEvo/src/failure_evo/autonomous_generation.py','FlowEvo/src/failure_evo/compile_queue.py'):
            plan['code_sha256'][str(ROOT/file)]=sha(ROOT/file)
    pilot.commit(output/'protocol.json',plan);pilot.commit(output/'roles.private.json',roles)
    pilot.commit(output/'learning.private.json',packet)
    return plan


def preflight(output,*,paid=False,authorization=None):
    plan=read(output/'protocol.json');roles=read(output/'roles.private.json')
    learning.validate_rows(roles)
    if (fingerprint(roles)!=plan['roles_sha256'] or sha(CODE)!=plan['recovery_sha256']
            or sha(Path(plan['dataset'])/'dataset.json')!=plan['dataset_sha256']
            or fingerprint(read(output/'learning.private.json'))!=plan['packet_sha256']
            or any(sha(p)!=h for p,h in plan['code_sha256'].items())
            or plan['rules']!=learning.SELECTION_RULES):raise PermissionError('A2 freeze drift')
    if paid:
        if plan.get('engineering_fixture') or roles!=learning.load_dataset(Path(plan['dataset'])):
            raise PermissionError('ENGINEERING_FIXTURE_NOT_PAID_DATA')
        if not learning.coverage(roles)['ready']:raise PermissionError('DATA_COVERAGE_BLOCKED')
        if not plan.get('input_policy'):raise PermissionError('A2_ENGINEERING_ONLY_NO_PAID_AUTHORIZATION')
        if not read(Path(plan['dataset'])/'dataset.json').get('A3_data_ready'):raise PermissionError('A3_DATA_NOT_READY')
        required=dict(run_id=plan['run_id'],protocol_hash=fingerprint(plan),model=MODEL,
            protocol=VERSION+':'+fingerprint(plan),max_cost_microusd=plan['max_cost_microusd'],paid_api_authorized=True)
        if authorization!=required:raise PermissionError('A3_PENDING_EXPLICIT_AUTHORIZATION')
    return plan,roles


def register_source(output,registry,runner,roles,plan):
    known={}
    for row in roles['TRAIN']:
        event=registry.evidence.record(stream_id=plan['run_id'],task_id=fingerprint(row['sample_id']),
            family_id='A2_CONTROLLED_TRAINING_NOT_SPONTANEOUS',stage='environment',
            code=canonical(row['candidate_context']),feedback=PublicFeedback('WRONG_ANSWER',
                'Controlled or engineering failure evidence; not a native Agent failure.',
                (canonical(dict(expected='progress',actual='Nothing happens.')),)),
            observed_at=0,available_from=0,finish_reason='stop',parent_sha256=fingerprint(row),
            provenance_group_id='game:'+row['game_sha256'])
        known[event['event_id']]=event
    return known


def source_card(output,registry,plan,known,gate_version):
    archived=read(S0/'result.json')['attempt']['registration']['card']
    version=fingerprint([learning.RECOVERY_SHA,gate_version,plan['roles_sha256']])
    card=FailureOperator.from_dict(dict(archived,operator_id=version[:16],version=version,
        artifact_path=str(CODE),evidence_ids=list(known),source_group_ids=sorted({e['provenance_group_id'] for e in known.values()})))
    if not registry._rows(card):registry.register(card,time())
    if registry.state(card)['permission']!='shadow' or not card.intact():raise PermissionError('Shadow source required')
    return card


def source_origin(row,plan):
    dataset=Path(row.get('source_dataset',plan['dataset']))
    if (dataset/'games').is_dir():
        game,mode=row['source_key'].split('/')
        path=dataset/'games'/(game+'.private.json')
        if sha(path)!=row['source_receipt_sha256']:raise PermissionError('source receipt drift')
        record=read(path);branch=next(b for b in record['branches'] if b['mode']==mode)
        origin=dict(record['origin'])
        origin['sequence']='controlled:'+game
        if origin['row']['game_sha256']!=row['game_sha256'] or branch['original_goal']!=origin['goal']:
            raise PermissionError('source identity drift')
    else:
        branch=read(dataset/'branches'/(row['source_key']+'.private.json'))
        selected=read(dataset/'selection.private.json')['tasks']
        source=next(r for r in selected if r['task']['game_sha256']==row['game_sha256'])
        origin=load_origin(source)
    prefix=branch['prefix']+[branch['failure']]
    ids=row['public_history_scope'].get('retained_step_ids')
    if ids is not None and (not ids or any(type(i) is not int or not 1<=i<=len(prefix) for i in ids)
                           or ids!=sorted(set(ids)) or ids[-1]!=len(prefix)):
        raise PermissionError('invalid public projection')
    visible=prefix if ids is None else [prefix[i-1] for i in ids]
    view=pilot.context_view(origin['goal'],prefix[-1]['observation'],prefix[-1]['commands'],visible,{})
    if row['candidate_context']!={k:view[k] for k in row['candidate_context']}:
        raise PermissionError('cannot reconstruct the exact gate checkpoint')
    origin.update(steps=prefix+branch['recovery_probe'],projected={'anchor':len(prefix),'goal':origin['goal']},
                  receipt_sha256=row['source_receipt_sha256'])
    return dataset,origin,ids


def live_training(row,plan,directory,runner,registry,receipts,recovery):
    if row['label']!='MATCH':return dict(status='NOT_EXECUTED_NEGATIVE_OR_UNCERTAIN',actions=[])
    if 'source_key' not in row:return dict(status='ENGINEERING_STATE_NO_ENVIRONMENT_MAPPING',actions=[])
    dataset,origin,ids=source_origin(row,plan)
    ref=fingerprint(row['sample_id'])
    return pilot.validate_source(plan,read(dataset/'protocol.json')['data_root'],origin,ref,
        recovery,runner,registry,receipts,directory,StrictTrainEnv,None,public_history_indices=ids)


def evaluate(rows,attempt,gate,recovery,plan,directory,runner,registry,receipts):
    result=[]
    for sample in rows:
        ctx=dict(sample['candidate_context'],state={})
        decision=learned_decision(runner,gate,ctx)
        receipt=next(r['payload'] for r in runner.events.records() if r['kind']=='ENVIRONMENT_POLICY_EXECUTED'
                     and r['payload']['execution_id']==decision['execution_id'])
        live=live_training(sample,plan,directory,runner,registry,receipts,recovery) if decision['status']=='MATCH' else dict(status='GATE_REFUSED',actions=[])
        result.append(dict(candidate_id=attempt['candidate_id'],version=attempt['version'],role=sample['role'],
            sample_id=fingerprint(sample['sample_id']),game_sha256=sample['game_sha256'],
            physical_state_group_id=sample['physical_state_group_id'],actual=decision['status'],reason=decision['reason'],
            expected=sample['label'],classification=learning.classify(sample['label'],decision['status']),
            execution_id=decision['execution_id'],context_sha256=receipt['context_sha256'],
            worker_status=receipt['raw']['status'],worker_seconds=receipt['seconds'],live=live,
            recovery_verified=(bool(live.get('local_repair_verified')) if sample['label']=='MATCH' and 'source_key' in sample else None)))
    return result


def exposed_regression(plan,output,attempt,runner,registry,receipts,known):
    # Imported only AFTER final selection. No result returns to the model or ranking.
    # Reuse the historical data loader, but bind DATA to the archived protocol.
    # Do not re-create an old paid experiment's source-code identity using new code.
    _,source,_,host,_,checkpoints,boundaries,backend=pilot.frozen.configuration(BASE,output,False)
    archived=read(BASE/pilot.PARENT/'protocol.json')
    if (fingerprint(archived)!=pilot.PARENT_SHA or sha(S0/'result.json')!=S0_RESULT_SHA
            or fingerprint(checkpoints)!=archived['checkpoints_sha256']
            or fingerprint(boundaries)!=archived['boundaries_sha256']
            or backend.manifest()!=plan['worker'] or backend.manifest()!=archived['worker']):
        raise PermissionError('archived regression data or Worker drift')
    baseline=read(S0/'result.json')
    gate=FailureOperator.from_dict(attempt['registration']['card'])
    recovery=source_card(output,registry,plan,known,attempt['version']+'/regression')
    rows=[]
    for old in baseline['attempt']['sources']:
        origin=next(o for o in host.values() if o['sequence']==old['sequence'])
        _,ctx,_=pilot.start_state(origin,plan)
        decision=learned_decision(runner,gate,ctx)
        live=pilot.validate_source(plan,source['data_root'],origin,old['source_ref'],recovery,runner,registry,
            receipts,output/'regression',StrictTrainEnv,None) if decision['status']=='MATCH' else None
        rows.append(dict(role='EXPOSED_SOURCE',sequence=old['sequence'],decision=decision,
                         repaired=bool(live and live['local_repair_verified']),live=live))
    for case in boundaries:
        ctx=checkpoint_context(case);decision=learned_decision(runner,gate,ctx)
        recovery_result=pilot.invoke(runner,recovery,ctx) if decision['status']=='MATCH' else None
        rows.append(dict(role='EXPOSED_BOUNDARY',id=case['public']['id'],expected=case['expected'],decision=decision,
            action_selected=bool(recovery_result and recovery_result['operator']['status']=='applied'),
            recovery_worker=recovery_result,environment_executed=False))
    return dict(rows=rows,retention_passed=sum(r.get('repaired',False) for r in rows)==11,
                selection_feedback_allowed=False)


def run(output,*,sender=None,after_attempt=None,authorization=None):
    plan,roles=preflight(output,paid=sender is None,authorization=authorization)
    engineering=sender is not None
    backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
    if backend.manifest()!=plan['worker']:raise PermissionError('Worker version differs')
    if pilot.environment_manifest(read(Path(plan['dataset'])/'protocol.json')['data_root'])!=plan['environment']:
        raise PermissionError('environment differs')
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        budget=create_accounts(output,plan)
        provider=SimpleNamespace(events=EvidenceStore(output/'provider.jsonl'))
        runner=EnvironmentPolicyRunner(backend,output/'worker.jsonl',budget)
        registry=FailureOperatorRegistry(output/'registry.jsonl',FailureEvidenceStore(output/'failures.jsonl'))
        receipts=pilot.EnvironmentReceipts(output/'environment.jsonl',plan['environment_steps'])
        pilot.check_run(budget,provider,runner,None)
        if (output/'result.json').is_file():
            result=read(output/'result.json')
            if result['protocol_sha256']!=fingerprint(plan):raise PermissionError('result binding drift')
            return result
        known=register_source(output,registry,runner,roles,plan)
        packet=read(output/'learning.private.json'); attempts=[]; seen={}
        def one(index,revision,parent):
            cid=f'candidate_{index}';name=f'{cid}/v{revision}';directory=output/name
            policy=plan.get('revision_policy' if revision else 'input_policy')
            prompt=learning.INITIAL_PROMPT if not revision else learning.REVISION_PROMPT
            message=dict(candidate_id=cid,training_input=packet) if not revision else learning.feedback(parent,roles['TRAIN'],packet)
            try:
                if revision and policy:
                    from alfworld_.recovery_learning_input import revision as project_revision
                    message=project_revision(parent,roles['TRAIN'],policy)
                request=wire(output,message,prompt,plan['temperature'],policy)
            except ValueError as exc:
                if str(exc)!='EVIDENCE_REPRESENTATION_LIMIT':raise
                attempt=dict(candidate_id=cid,revision=revision,version=fingerprint([cid,revision,message]),
                    parent_version=parent['version'] if parent else None,status='INPUT_LIMIT',
                    delivery={'status':'NOT_SENT_INPUT_LIMIT'},code=None,code_sha256=None)
                pilot.commit(directory/'attempt.json',attempt);attempts.append(attempt)
                return attempt
            binding=dict(payload_sha256=fingerprint(message),wire_sha256=fingerprint(request),
                         parent_version=parent['version'] if parent else None,candidate_id=cid,revision=revision)
            pilot.commit(directory/'request.private.json',dict(binding,payload=message,wire=request))
            response=stage_request(output,name,'analyze',message,parse_delivery,budget,sender=sender,
                protocol=VERSION+':'+fingerprint(plan),analysis_prompt=prompt,temperature=plan['temperature'],input_policy=policy,
                authorization=authorization)
            if response['wire_sha256']!=binding['wire_sha256']:raise PermissionError('wire drift')
            parsed=delivery(response);code=parsed.get('submitted_code') or (parsed.get('proposal') or {}).get('code')
            attempt=dict(binding,version=fingerprint([binding,response['response_sha256'],code,plan['roles_sha256']]),
                status=parsed['status'],delivery=parsed,code=code,usage=trusted_usage(response['raw_response']),
                response_sha256=response['response_sha256'],request_id=response['id'],origin='MOCK' if engineering else 'DEEPSEEK',
                model=response['model'],parent_source_sha256=parent.get('code_sha256') if parent else None,
                code_sha256=pilot.save_exact_source(directory/'gate.py',code) if code else None)
            if parsed['status']=='PROPOSE':
                if attempt['code_sha256'] in seen:
                    attempt.update(status='DUPLICATE_SOURCE',duplicate_of=seen[attempt['code_sha256']])
                else:
                    seen[attempt['code_sha256']]=attempt['version']
                    try:
                        adapted=worker_artifact(code);attempt['static']=static_check_detailed(adapted)
                        attempt['status']='STATIC_PASSED' if attempt['static']['passed'] else 'STATIC_REJECTED'
                    except (SyntaxError,ValueError,RecursionError) as exc:
                        attempt.update(status='GATE_CONTRACT_REJECTED',static={'passed':False,'error':str(exc)})
                    if attempt['status']=='STATIC_PASSED':
                        registration=pilot.register(directory,dict(parsed['proposal'],code=adapted),response,
                            {'candidate_version':attempt['version'],'parent':binding['parent_version'],'data':plan['roles_sha256']},
                            list(known),known,runner,registry,engineering=engineering,protocol=VERSION)
                        if registration['status']!='SHADOW':raise PermissionError('Shadow registration required')
                        attempt['registration']=registration;gate=FailureOperator.from_dict(registration['card'])
                        recovery=source_card(output,registry,plan,known,attempt['version'])
                        attempt['train']=evaluate(roles['TRAIN'],attempt,gate,recovery,plan,directory/'train',runner,registry,receipts)
                        # Validation never enters the revision payload.
                        attempt['validation']=evaluate(roles['TRAIN_VALIDATION'],attempt,gate,recovery,plan,directory/'validation',runner,registry,receipts)
            pilot.commit(directory/'attempt.json',attempt);attempts.append(attempt)
            if after_attempt:after_attempt(attempt)
            return attempt
        initials=[one(i,0,None) for i in range(4)]
        for i,a in enumerate(initials):
            if learning.needs_revision(a):one(i,1,a)
        best_initial=learning.select(initials,roles,engineering=engineering)
        selection=learning.select(attempts,roles,engineering=engineering)
        pilot.commit(output/'selection.json',dict(selection,best_initial=best_initial))
        regression=None
        if selection['status']=='SELECTED_PENDING_REGRESSION':
            selected=next(a for a in attempts if a['version']==selection['selected']['version'])
            pilot.commit(output/'selected.json',selection['selected'])
            regression=exposed_regression(plan,output,selected,runner,registry,receipts,known)
            pilot.commit(output/'regression.json',regression)
        pilot.check_run(budget,provider,runner,None)
        result=dict(status='A2_MOCK_RUN_COMPLETED' if engineering else 'A3_CONTROLLED_RUN_COMPLETED',
            scope='ENGINEERING_NOT_LEARNING_EVIDENCE' if engineering else 'CONTROLLED_TRAINING_NOT_GENERALIZATION',
            selection=selection,best_initial=best_initial,regression=regression,
            retention_status=('SELECTED_BUT_RETENTION_FAILED' if regression and not regression['retention_passed'] else
                              ('ENGINEERING_REGRESSION_PASSED' if engineering else 'DEVELOPMENT_REGRESSION_PASSED') if regression else 'NOT_REACHED'),
            attempts=attempts,budget=budget.snapshot(),environment=dict(receipts.started),
            paid_requests=0 if engineering else sum(r['kind']=='SEND_STARTED' for r in provider.events.records()),
            actual_model_cost_usd=0 if engineering else None,A3_ready=False,protocol_sha256=fingerprint(plan))
        return pilot.commit(output/'result.json',result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','preflight','mock_run','run_a3'))
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--dataset',type=Path,default=DATA)
    parser.add_argument('--mock-responses',type=Path)
    parser.add_argument('--authorization',type=Path)
    args=parser.parse_args();out=args.output.resolve()
    if args.command=='prepare':result=prepare(out,dataset=args.dataset)
    elif args.command=='preflight':
        plan,roles=preflight(out);result=dict(status='A3_PENDING_AUTHORIZATION' if plan.get('input_policy') and learning.coverage(roles)['ready'] else 'A3_DATA_NOT_READY',coverage=learning.coverage(roles),paid_api_authorized=False)
    elif args.command=='run_a3':
        if args.authorization is None:parser.error('explicit new A3 authorization required')
        result=run(out,authorization=read(args.authorization))
    else:
        if args.mock_responses is None:parser.error('mock_run requires explicit fixture responses')
        responses=read(args.mock_responses)
        pilot.commit(out/'mock_responses.private.json',responses)
        def sender(wire):
            payload=json.loads(wire['messages'][1]['content']);key=payload['candidate_id']+('/v1' if 'parent_version' in payload else '/v0')
            return responses[key]
        result=run(out,sender=sender)
    print(canonical({k:v for k,v in result.items() if k in ('status','selection','budget','coverage','paid_requests')}))


if __name__=='__main__':main()
