"""B v14 compact-plan Pilot with two bounded, source-only revision slots."""

import argparse
from collections import Counter
import fcntl
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time

from alfworld_.failure_learning import EnvironmentPolicyRunner, register_environment_candidate
from alfworld_.generic_recovery_skill import parse_command, receipt_truth, worker_source
from alfworld_.recovery_acquisition import RecoveryAdapter, stage_request
from alfworld_.recovery_plan_v14 import (
    PROMPT, REPAIR_PROMPT, VERSION, PlanInput, compile_plan, first_decision, review_public_sources,
)
from alfworld_.skill_acquisition import INPUT_LIMIT, import_source_events
from failure_evo.contracts import canonical, fingerprint
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.math_stream import read, save, sha
from failure_evo.run_health import trusted_usage
import run_alfworld_recovery_plan_v13 as parent


PREVIOUS = parent.PREVIOUS
PARENT_RUN = 'alfworld_recovery_plan_v13_pilot_20261112_01'
OUTPUT_LIMIT = parent.OUTPUT_LIMIT
REVISION_LIMIT = 2
REVISION_INPUT_LIMIT = 49_152
MAX_PREVIOUS_BYTES = 16_384
STAGES = ('schema','semantics','source')


def learning_input(payload):
    """Keep the frozen public receipts but use only one citation namespace on the wire."""
    traces, anchors, refs, verbs = [], {}, {}, set()
    for receipt in payload['source_receipts']:
        anchor = receipt['failure_step_id']
        anchors[receipt['evidence_id']] = anchor
        public_steps, failure_ref = [], None
        for original, action, observation, admissible in receipt['steps']:
            ref = f's{len(refs)+1:03}'
            refs[ref] = original
            public_steps.append(dict(ref=ref,action=action,observation=observation,was_admissible=admissible))
            if original==anchor:
                command = parse_command(action)
                if not command or receipt_truth(command,observation)!='FALSE':
                    raise PermissionError('unsupported or unverified failure anchor')
                failure_ref = ref
                verbs.add(command[0])
        if failure_ref is None:
            raise PermissionError('frozen trace is missing its failure receipt')
        traces.append(dict(goal=receipt['goal'],failure_ref=failure_ref,steps=public_steps,
                           admissible_at_failure=receipt['anchor_admissible_commands']))
    if len(verbs)!=1 or len(set(refs.values()))!=len(refs) or len(anchors)!=len(traces):
        raise PermissionError('ambiguous frozen failure or citation identity')
    failed_verb, = verbs
    mechanism = {key:value for key,value in payload['mechanism'].items() if key!='evidence_ids'}
    return dict(failed_verb=failed_verb,hypothesis=mechanism,public_traces=traces), PlanInput(failed_verb,anchors,refs)


def wire(path, packet, prompt, input_limit=INPUT_LIMIT):
    # Use the same adapter as the actual request, with a non-callable experimental transport.
    adapter = RecoveryAdapter(path, None, model=PREVIOUS.MODEL, mock=True, sender=lambda _: None,
        stage='analyze',payload=packet,parser=None,protocol=VERSION,
        analysis_prompt=prompt,max_wire_input_upper=input_limit)
    return adapter.preflight(dict(phase='induction',max_tokens=OUTPUT_LIMIT,
        discovery=dict(stage='analyze',payload_sha256=fingerprint(packet))))


def configuration(base, output, mock):
    historical = (base/PARENT_RUN).resolve()
    target = output.resolve()
    if target.is_relative_to(historical) or historical.is_relative_to(target):
        raise PermissionError('v14 needs a separate directory')
    previous, source, events, host, schedule, boundaries, backend = parent.configuration(base,output,False)
    parent_frozen, parent_result = read(historical/'protocol.json'), read(historical/'result.json')
    if ({**previous,'run_id':'real:'+PARENT_RUN}!=parent_frozen
            or parent_result['protocol_sha256']!=fingerprint(parent_frozen)
            or parent_result['paid_requests']!=6):
        raise PermissionError('v13 provenance mismatch')
    history = {**previous['historical_sha256'],
               **{str(path):sha(path) for path in historical.rglob('*') if path.is_file()}}
    if any(sha(path)!=digest for path,digest in history.items()):
        raise PermissionError('historical evidence changed')
    files = {Path(__file__).resolve(), PREVIOUS.ROOT/'FlowEvo/src/alfworld_/recovery_plan_v14.py',
             *(PREVIOUS.ROOT/name for name in previous['code_sha256'])}
    entries, inputs = [], []
    with TemporaryDirectory() as temp:
        for group, selected, payload, _ in schedule:
            packet, context = learning_input(payload)
            initial = wire(Path(temp)/'provider.jsonl',packet,PROMPT)
            entries.append(dict(group=group,sequences=[row['sequence'] for row in selected],
                                wire_sha256=fingerprint(initial),input_upper=len(canonical(initial).encode())+256))
            inputs.append((group,selected,packet,context))
    bounds = [row['input_upper'] for row in entries] + [REVISION_INPUT_LIMIT]*(len(entries)*REVISION_LIMIT)
    calls = len(bounds)
    plan = dict(version=VERSION,scope='MOCK_COMPACT_PLAN_SOURCE_ONLY' if mock else 'REAL_COMPACT_PLAN_SOURCE_ONLY',
        disposition='SHADOW_SOURCE_ONLY',run_id=('mock:' if mock else 'real:')+output.name,
        model=PREVIOUS.MODEL,parent_protocol_sha256=fingerprint(parent_frozen),
        parent_result_sha256=sha(historical/'result.json'),schedule=entries,network_policy=previous['network_policy'],
        worker=backend.manifest(),worker_calls=previous['worker_calls'],source_window=previous['source_window'],
        checkpoints_sha256=previous['checkpoints_sha256'],boundaries_sha256=previous['boundaries_sha256'],
        historical_sha256=history,code_sha256={str(path.relative_to(PREVIOUS.ROOT)):sha(path) for path in sorted(files)},
        prompt_sha256=fingerprint(PROMPT),revision_prompt_sha256=fingerprint(REPAIR_PROMPT),
        revision_trigger=['SCHEMA_REJECTED','SEMANTIC_REJECTED','NO_FIRST_ACTION'],
        revision_limit=REVISION_LIMIT,revision_input_upper=REVISION_INPUT_LIMIT,output_upper=OUTPUT_LIMIT,
        max_calls=calls,max_tokens=sum(bounds)+calls*OUTPUT_LIMIT,
        max_cost_microusd=sum((120*(size+OUTPUT_LIMIT)+99)//100 for size in bounds),
        quote_upper_usd=(30*sum(bounds)+120*calls*OUTPUT_LIMIT)/100_000_000)
    return plan,source,events,host,inputs,boundaries,backend


def authorization_for(plan):
    return dict(run_id=plan['run_id'],protocol_hash=fingerprint(plan),model=plan['model'],protocol=VERSION,
                max_cost_microusd=plan['max_cost_microusd'],paid_api_authorized=True)


def prepare(base, output):
    plan,*_ = configuration(base,output,False)
    output.mkdir(mode=0o700,parents=True,exist_ok=False)
    save(output/'protocol.json',plan)
    save(output/'authorization.template.json',{**authorization_for(plan),'paid_api_authorized':False})
    return plan


def public_cases(selected, host):
    cases = []
    for index, row in enumerate(selected,1):
        origin = host[row['evidence_id']]
        anchor = origin['projected']['anchor']
        prefix = origin['steps'][:anchor]
        cases.append(PREVIOUS.public_state(f'source_{index}',origin['projected']['goal'],prefix[-1],prefix,anchor-1))
    return cases


def compile_receipt(response, cases):
    if not response.get('parse_status'):
        outcome = json.loads(response['specification'])
    else:
        complete = response.get('finish_reason')=='stop'
        errors = [dict(path='$',code='INVALID_JSON',expected='one complete JSON object',actual='unparseable response')]
        outcome = dict(status='SCHEMA_REJECTED' if complete else 'PROVIDER_DELIVERY_REJECTED',candidate=None,
            schema=dict(status='REJECTED' if complete else 'BLOCKED',errors=errors if complete else [],blocked=[]),
            semantics=dict(status='BLOCKED',errors=[],blocked=[]))
    if outcome['candidate'] is not None:
        outcome['source'] = review_public_sources(outcome['candidate'],cases)
    else:
        status = 'NOT_APPLICABLE' if outcome['status'] in ('ABSTAIN','UNSUPPORTED_REPRESENTATION') else 'BLOCKED'
        outcome['source'] = dict(status=status,errors=[],blocked=[])
    return outcome


def revision_packet(response, outcome, context):
    content = response['raw_response']['choices'][0]['message'].get('content')
    if not isinstance(content,str) or len(content.encode())>MAX_PREVIOUS_BYTES:
        return None
    reports = {stage:{key:outcome[stage][key] for key in ('status','errors','blocked')} for stage in STAGES}
    return dict(previous_plan=content,reports=reports,allowed_step_refs=sorted(context.steps),
                failed_verb=context.failed_verb)


def schedule_revision(plan, path, response, outcome, context, attempt):
    triggers = plan['revision_trigger']
    if outcome['status'] not in triggers and outcome['source']['status'] not in triggers:
        return 'NO_REVISION_REQUIRED', None
    if attempt>=plan['revision_limit']:
        return 'REVISION_LIMIT_REACHED', None
    packet = revision_packet(response,outcome,context) if response.get('finish_reason')=='stop' else None
    if packet is None:
        return 'REVISION_INPUT_UNAVAILABLE', None
    try:
        wire(path,packet,REPAIR_PROMPT,plan['revision_input_upper'])
    except ValueError as error:
        if str(error)!='EVIDENCE_REPRESENTATION_LIMIT':
            raise
        return 'REVISION_PACKET_LIMIT', None
    return 'REVISION_SCHEDULED', packet


def revision_audit(before, after):
    """Compare diagnostics only for checked fields; a newly reachable check is not a regression."""
    def keys(result, stage):
        return Counter((row['path'],row['code']) for row in result[stage]['errors'])

    def checked(result, stage, path):
        if result[stage]['status'] in ('BLOCKED','NOT_APPLICABLE'):
            return False
        return not any(path==row['path'] or path.startswith((row['path']+'.',row['path']+'['))
                       for row in result[stage]['blocked'] if row['check']!='SEMANTIC_VALIDATION')

    changes = {key:[] for key in ('no_longer_reported','persisting','newly_reported','newly_checkable','now_blocked')}
    for stage in STAGES:
        previous, current = keys(before,stage), keys(after,stage)
        for path,code in sorted(previous.keys() | current.keys()):
            old, new = previous[path,code], current[path,code]
            row = dict(stage=stage,path=path,code=code)
            if min(old,new):
                changes['persisting'].append(dict(row,count=min(old,new)))
            if old>new:
                kind = 'no_longer_reported' if checked(after,stage,path) else 'now_blocked'
                changes[kind].append(dict(row,count=old-new))
            if new>old:
                kind = 'newly_reported' if checked(before,stage,path) else 'newly_checkable'
                changes[kind].append(dict(row,count=new-old))
    return changes


def changed_fields(previous, current):
    try:
        before, after = [json.loads(row['raw_response']['choices'][0]['message']['content'])
                         for row in (previous,current)]
    except (TypeError,ValueError,KeyError,IndexError,RecursionError):
        return None
    if not isinstance(before,dict) or not isinstance(after,dict):
        return None
    return sorted(key for key in before.keys() | after.keys()
                  if key not in before or key not in after or before[key]!=after[key])


def acquire_plan(plan, group, index, packet, context, cases, budget, output, sender, authorization):
    attempts, usage = [], Counter()
    directory = output/f'candidate_{index}'
    previous, previous_response = None, None
    for number in range(plan['revision_limit']+1):
        prompt = PROMPT if number==0 else REPAIR_PROMPT
        stage = 'initial' if number==0 else f'revision_{number:02}'
        input_limit = INPUT_LIMIT if number==0 else plan['revision_input_upper']
        expected_wire = fingerprint(wire(output/'provider.jsonl',packet,prompt,input_limit))
        if number==0 and expected_wire!=plan['schedule'][index]['wire_sha256']:
            raise PermissionError('initial request differs from freeze')
        response = stage_request(output,f'{directory.name}/{stage}','analyze',packet,
            lambda value:compile_plan(value,context),budget,sender=sender,authorization=authorization,
            network_policy=plan['network_policy'] if sender is None else None,protocol=VERSION,analysis_prompt=prompt)
        if response['wire_sha256']!=expected_wire:
            raise PermissionError('request wire differs from preflight')
        billed = trusted_usage(response['raw_response'])
        usage.update(billed)
        outcome = compile_receipt(response,cases)
        attempt = dict(stage=stage,response_sha256=response['response_sha256'],wire_sha256=expected_wire,
                       finish_reason=response.get('finish_reason'),usage=billed,result=outcome)
        if previous is not None:
            attempt['revision_audit'] = revision_audit(previous,outcome)
            attempt['changed_fields'] = changed_fields(previous_response,response)
        attempts.append(attempt)
        reason, packet = schedule_revision(plan,output/'provider.jsonl',response,outcome,context,number)
        save(directory/'compile_receipt.json',dict(group=group,status=outcome['status'],attempts=attempts,
                                                  disposition=reason,environment='NOT_RUN'))
        if reason!='REVISION_SCHEDULED':
            break
        previous, previous_response = outcome, response
    return dict(group=group,status=outcome['status'],attempts=attempts,revision_disposition=reason,
                environment='NOT_RUN'), response, usage


def validate_candidate(plan, record, response, context, selected, source, host, boundaries, imported, known,
                       directory, registry, runner, mock):
    result = record['attempts'][-1]['result']
    compiled = result['candidate']
    if compiled is None:
        return
    if result['source']['selectable']==0:
        record['status'] = 'SOURCE_BLOCKED'
        return
    skill = compiled['skill']
    generated = dict(code=worker_source(skill),description='Compiled public recovery plan',
        applicability=skill['scope'],model=response['model'],id=response['id'],response_sha256=response['response_sha256'])
    registration = register_environment_candidate(directory,generated,dict(plan=compiled['original'],skill=skill,
        source_receipt_sha256=fingerprint(result['source'])),[imported[key] for key in context.anchors],known,
        runner.backend.manifest(),registry,engineering=mock,protocol=VERSION,baseline='alfworld-v14-plan-shadow')
    record.update(registration)
    if record['status']!='SHADOW':
        return
    card = FailureOperator.from_dict(registration['card'])
    sources = [parent.validate_source(source['data_root'],host[row['evidence_id']],compiled,card,runner,registry,
              directory/f"source_{row['sequence']}.json",plan['source_window']) for row in selected]
    controls = []
    for case in boundaries:
        public = case['public']
        phase, checks = first_decision(compiled,public)
        if checks['selection'] is None:
            action = dict(status='declined',reason=checks['block'])
        else:
            until = compiled['plan']['steps'][phase].get('repeat_until')
            checks,action = parent.decide(skill,public,phase,card,runner,until)
        controls.append(dict(category=case['category'],expected=case['expected'],checks=checks,operator=action))
    metrics = dict(source_checks=len(sources),boundary_checks=len(controls),
        false_triggers=sum(row['expected']=='NO' and row['operator']['status']=='applied' for row in controls),
        uncertain_triggers=sum(row['expected']=='UNKNOWN' and row['operator']['status']=='applied' for row in controls),
        boundary_errors=sum(row['operator']['status']=='error' for row in controls))
    for name in ('first_action_executed','first_action_verified','plan_completed','local_repair_verified','won'):
        metrics[name] = sum(row[name] for row in sources)
    record.update(environment='SOURCE_VALIDATED',sources=sources,boundaries=controls,metrics=metrics)
    if registry.state(card)['permission']!='shadow':
        raise PermissionError('unexpected candidate permission')
    save(directory/'validation.json',record)


def acquire(plan, source, events, host, schedule, boundaries, backend, output, sender, authorization):
    budget = PREVIOUS.create_accounts(output,plan)
    registry = FailureOperatorRegistry(output/'registry.jsonl',FailureEvidenceStore(output/'failures.jsonl'))
    runner = EnvironmentPolicyRunner(backend,output/'worker.jsonl',budget)
    imported = import_source_events('B',events,host,output,registry.evidence,plan['run_id'])
    known = {row['event_id']:row for row in registry.evidence.visible(time(),plan['run_id'])}
    candidates, usage = [], Counter()
    for index,(group,selected,packet,context) in enumerate(schedule):
        record,response,billed = acquire_plan(plan,group,index,packet,context,public_cases(selected,host),budget,
                                            output,sender,authorization)
        candidates.append(record)
        usage.update(billed)
        validate_candidate(plan,record,response,context,selected,source,host,boundaries,imported,known,
                           output/f'candidate_{index}',registry,runner,sender is not None)
    if any(sha(path)!=digest for path,digest in plan['historical_sha256'].items()):
        raise PermissionError('historical evidence changed during v14')
    counts = dict(initial_compiled=sum(row['attempts'][0]['result']['status']=='COMPILED' for row in candidates),
                  initial_schema_passed=sum(row['attempts'][0]['result']['schema']['status']=='PASSED' for row in candidates),
                  final_schema_passed=sum(row['attempts'][-1]['result']['schema']['status']=='PASSED' for row in candidates),
                  final_compiled=sum(row['attempts'][-1]['result']['status']=='COMPILED' for row in candidates),
                  revisions=sum(len(row['attempts'])-1 for row in candidates),
                  source_actionable=sum(row['attempts'][-1]['result']['source'].get('selectable',0)>0 for row in candidates),
                  environment_evaluated=sum(row['environment']=='SOURCE_VALIDATED' for row in candidates))
    result = dict(scope=plan['scope'],protocol_sha256=fingerprint(plan),candidates=candidates,summary=counts,
        usage=dict(usage),paid_requests=0 if sender is not None else len(candidates)+counts['revisions'],
        quote_estimated_usd=(30*usage['input_tokens']+120*usage['output_tokens'])/100_000_000,
        budget=budget.snapshot(),independent_gate_games=0,disposition=plan['disposition'])
    save(output/'result.json',result)
    return result


def run(base, output, *, sender=None, authorization=None):
    plan,*inputs = configuration(base,output,sender is not None)
    frozen = output/'protocol.json'
    if sender is None and (not frozen.is_file() or authorization!=authorization_for(plan)):
        raise PermissionError('frozen v14 protocol and separate authorization required')
    output.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        if frozen.exists() and read(frozen)!=plan:
            raise PermissionError('v14 protocol drift')
        if not frozen.exists():
            if sender is None:
                raise PermissionError('v14 protocol disappeared')
            save(frozen,plan)
        try:
            return acquire(plan,*inputs,output,sender,authorization)
        except (Exception,KeyboardInterrupt) as error:
            save(output/'interruption.json',dict(protocol_sha256=fingerprint(plan),type=type(error).__name__,
                                                 reason=str(error)))
            raise


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('action',choices=('prepare','run'))
    cli.add_argument('--base',type=Path,default=Path.home()/'.local/share/flowevo')
    cli.add_argument('--output',type=Path,required=True)
    cli.add_argument('--authorization',type=Path)
    args = cli.parse_args()
    if args.action=='prepare':
        plan = prepare(args.base,args.output)
        print(canonical({key:plan[key] for key in ('run_id','max_calls','max_cost_microusd','quote_upper_usd')} |
                        dict(status='PREPARED_NOT_AUTHORIZED',protocol_sha256=fingerprint(plan))))
    elif args.authorization is None:
        cli.error('run requires --authorization')
    else:
        result = run(args.base,args.output,authorization=read(args.authorization))
        print(canonical(dict(paid_requests=result['paid_requests'],summary=result['summary'],candidates=[
            dict(group=row['group'],status=row['status'],metrics=row.get('metrics')) for row in result['candidates']])))


if __name__=='__main__':
    main()
