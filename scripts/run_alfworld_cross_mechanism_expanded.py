"""Expanded, source-only B v11 follow-up. The original Pilot is read only."""

import argparse
from collections import Counter
import fcntl
import json
from pathlib import Path
from time import time

from alfworld_.failure_learning import EnvironmentPolicyRunner, register_environment_candidate
from alfworld_.generic_recovery_skill import GENERATION_PROMPT, VERSION, parse_skill, worker_source
from alfworld_.recovery_acquisition import parse_mechanisms, parse_step_analyses, rank_mechanisms, recovery_view, stage_request
from alfworld_.skill_acquisition import INPUT_LIMIT, import_source_events, verify_source_game
from failure_evo.contracts import canonical, fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperator, FailureOperatorRegistry
from failure_evo.math_stream import read, save, sha
from failure_evo.run_health import trusted_usage
import run_alfworld_cross_mechanism_v11 as previous


EXPANDED = 'alfworld_cross_mechanism_v11_expanded_20261111_01'
PROTOCOL = VERSION + '-expanded28'
CAP = 3
NAVIGATION = 'navigation_no_effect'
PROMPT = GENERATION_PROMPT + """
Delivery limits: sources contains 1 to 6 exact step IDs per atom; reason, scope and
refusal are 1 to 400 characters. args is always an object with named fields.
Example event args: {"verb":"go_to","entities":["example_role"],"window":"at_failure","outcome":"noop"}.
The roles in args must be your declared aliases. goal_requires expresses what the task requests.
Use a public effect or another observable state to decide whether to stop.
"""


def additions(source, plan, host):
    commits = EvidenceStore(source/'episodes.jsonl').records()
    if len(commits) != len(plan['tasks']) or len(commits) != 120:
        raise PermissionError('source commit coverage changed')
    original_sequences = {record['sequence'] for record in host.values()}
    events, records = [], {}
    for sequence, (entry, task) in enumerate(zip(commits, plan['tasks'], strict=True), 1):
        payload = entry['payload']
        if entry['kind'] != 'EPISODE_COMMITTED' or payload['seq'] != sequence or payload['task_id'] != task['task_id']:
            raise PermissionError('source commit identity changed')
        outcome = payload['outcome']
        if sequence in original_sequences or outcome['status'] != 'SUCCESS' or outcome['use']['fallback']:
            continue
        trace = outcome['trace']
        candidate = next((i for i, step in enumerate(trace['actions'], 1)
                          if step['action'].startswith('go to ') and step['observation']=='Nothing happens.'), None)
        if candidate is None:
            continue
        env = EvidenceStore(source/'episodes'/task['task_id']/'environment.jsonl').records()
        steps = [row['payload'] for row in env[1:]]
        if (env[0]['kind']!='RESET' or any(row['kind']!='STEP' for row in env[1:])
                or len(steps)!=len(trace['actions']) or len(steps)!=trace['total_steps']
                or not candidate < len(steps) <= 50 or not steps[-1]['won']
                or steps[candidate-1]['done'] or steps[candidate-1]['won']
                or any(any(a[key]!=b[key] for key in ('action','observation','score','done'))
                       for a,b in zip(steps,trace['actions'],strict=True))):
            raise PermissionError('source expansion receipt mismatch')
        eid = fingerprint([PROTOCOL,entry['record_hash'],env[-1]['record_hash'],candidate])
        initial = env[0]['payload']
        event = dict(evidence_id=eid,event_type='LOCAL_FAILURE_RECOVERY',goal=trace['goal'],
                     initial_observation=initial['observation'],won=True,anchor=candidate,
                     steps=[[step['action'],step['observation'],step['action'] in earlier['payload']['commands']]
                            for step,earlier in zip(steps,env[:-1],strict=True)])
        origin = dict(sequence=sequence,row=task,initial=initial,steps=steps,projected=event,
                      source_sha256=entry['record_hash'],receipt_sha256=env[-1]['record_hash'],at=entry['at'])
        verify_source_game(plan['data_root'],origin)
        events.append(event)
        records[eid]=origin
    if len(events)!=12:
        raise PermissionError('expected twelve added real navigation events')
    return events,records


def navigation_boundaries(origin, start):
    steps, goal = origin['steps'], origin['projected']['goal']
    anchor = origin['projected']['anchor']-1
    decisive = steps.index(previous._decisive(origin))
    ready = steps[decisive-1]
    prefix = steps[:anchor+1]
    rows = (
        ('wrong_goal','examine the cd with the desklamp.',steps[anchor],prefix,anchor,'NO'),
        ('stale_failure',goal,steps[-1],steps,anchor,'NO'),
        ('state_changed',goal,ready,steps[:decisive],anchor,'NO'),
        ('wrong_phase','heat some toiletpaper and put it in toiletpaperhanger.',ready,steps[:decisive],anchor,'NO'),
        ('instance_conflict','put the toiletpaper 999 in the toiletpaperhanger.',ready,steps[:decisive],anchor,'NO'),
        ('insufficient',goal,dict(observation='You are in the room.',commands=['look','inventory']),[steps[anchor]],0,'UNKNOWN'),
        ('native_ready',goal,ready,steps[:decisive],None,'NO'),
    )
    return [dict(group=NAVIGATION,category=category,expected=expected,source_sequence=origin['sequence'],
                 public=previous.public_state(f'dev_{start+index:03d}',task,current,history,selected))
            for index,(category,task,current,history,selected,expected) in enumerate(rows,1)]


def configuration(base, output, mock):
    protected = [base/previous.SOURCE, *base.glob('alfworld_recovery_v[3-7]_*'),
                 *base.glob('alfworld_binding_v8_*'), *base.glob('alfworld_decision_v9_*'),
                 *base.glob('alfworld_precondition_v10_*'), base/previous.PILOT,
                 *base.glob('alfworld_cross_mechanism_v11_acceptance_*')]
    if any(output.resolve().is_relative_to(path.resolve()) or path.resolve().is_relative_to(output.resolve())
           for path in protected):
        raise PermissionError('expanded output must be separate from historical runs')
    source,events,host,views,checkpoints,boundaries = previous.cohort(base)
    extra,records = additions(base/previous.SOURCE,source,host)
    checkpoints = [*checkpoints,*[dict(evidence_id=event['evidence_id'],sequence=records[event['evidence_id']]['sequence'],
        source_receipt=records[event['evidence_id']]['receipt_sha256'],anchor=event['anchor'],group=NAVIGATION)
        for event in extra]]
    host = {**host,**records}
    events = sorted([*events,*extra],key=lambda row:host[row['evidence_id']]['sequence'])
    checkpoints.sort(key=lambda row:row['sequence'])
    views=[]
    for event in events:
        current = host[event['evidence_id']]['steps'][event['anchor']-1]
        row = recovery_view(event,current['commands'])
        views.append({k:row[k] for k in ('evidence_id','goal','initial_observation','steps',
                                        'failure_step_id','anchor_admissible_commands')})
    if len({event['evidence_id'][:12] for event in events}) != 28:
        raise PermissionError('ambiguous evidence scope')
    first = records[extra[0]['evidence_id']]
    if first['sequence'] != 8:
        raise PermissionError('navigation development fixture identity changed')
    boundaries += navigation_boundaries(first,len(boundaries))
    historical,v9 = previous.history_snapshot(base)
    old_path=base/previous.PILOT
    old,old_result=read(old_path/'protocol.json'),read(old_path/'result.json')
    if (old_result['protocol_sha256']!=fingerprint(old)
            or old_result['paid_requests']!=5
            or any(sha(path)!=digest for path,digest in old['historical_sha256'].items())):
        raise PermissionError('original v11 provenance mismatch')
    historical.update({str(path.resolve()):sha(path) for path in old_path.rglob('*') if path.is_file()})
    backend=previous.FrozenLinuxBackend(image=previous.IMAGE,worker_script=previous.WORKER)
    sizes,wire_hashes=previous.wire_bound(views)
    bounds=[*sizes,*([INPUT_LIMIT]*(1+CAP))]
    files={Path(__file__).resolve(), *(previous.ROOT/path for path in old['code_sha256'])}
    plan=dict(version=PROTOCOL, scope='MOCK_EXPANDED' if mock else 'REAL_EXPANDED_SOURCE_ONLY',
        run_id=('mock:' if mock else 'real:')+output.name,model=previous.MODEL,
        learning_sha256=fingerprint(views),checkpoints_sha256=fingerprint(checkpoints),
        boundaries_sha256=fingerprint(boundaries),source_protocol_sha256=fingerprint(source),
        parent_protocol_sha256=fingerprint(old),analysis_wire_sha256=wire_hashes,
        generation_prompt_sha256=fingerprint(PROMPT),code_sha256={str(path.relative_to(previous.ROOT)):sha(path)
            for path in sorted(files)},historical_sha256=historical,worker=backend.manifest(),
        max_calls=len(bounds),max_tokens=sum(bounds)+len(bounds)*previous.OUTPUT_UPPER,
        max_cost_microusd=sum((120*(size+previous.OUTPUT_UPPER)+99)//100 for size in bounds),
        quote_upper_usd=(30*sum(bounds)+120*len(bounds)*previous.OUTPUT_UPPER)/100_000_000,
        worker_calls=len(events)*previous.SOURCE_WINDOW+CAP*len(boundaries),
        source_window=previous.SOURCE_WINDOW,candidate_cap=CAP,network_policy=v9['network_policy'])
    return plan,source,events,host,views,checkpoints,boundaries,backend


def grant(plan):
    return dict(run_id=plan['run_id'],protocol_hash=fingerprint(plan),model=plan['model'],protocol=PROTOCOL,
                max_cost_microusd=plan['max_cost_microusd'],paid_api_authorized=True)


def prepare(base,output):
    plan,_,_,_,views,checkpoints,boundaries,_=configuration(base,output,False)
    output.mkdir(mode=0o700,parents=True,exist_ok=False)
    for name,value in [('protocol.json',plan),('learning.public.json',views),
                       ('checkpoints.private.json',checkpoints),('boundaries.private.json',boundaries),
                       ('authorization.template.json',{**grant(plan),'paid_api_authorized':False})]:
        save(output/name,value)
    return plan


def run(base,output,*,sender=None,authorization=None):
    plan,source,events,host,views,checkpoints,boundaries,backend=configuration(base,output,sender is not None)
    if sender is None and (authorization!=grant(plan) or read(output/'protocol.json')!=plan):
        raise PermissionError('exact separate expanded authorization and freeze required')
    output.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if sender is None:
            if read(output/'protocol.json')!=plan:
                raise PermissionError('expanded protocol drift')
            copies=[('learning.public.json',views),('checkpoints.private.json',checkpoints),
                    ('boundaries.private.json',boundaries)]
            if any(read(output/name)!=expected for name,expected in copies):
                raise PermissionError('expanded frozen data drift')
        elif (output/'protocol.json').exists() and read(output/'protocol.json')!=plan:
            raise PermissionError('expanded mock protocol drift')
        else:
            save(output/'protocol.json',plan)
        try:
            return acquire(plan,source,events,host,views,checkpoints,boundaries,backend,output,sender,authorization)
        except (Exception,KeyboardInterrupt) as exc:
            save(output/'interruption.json',dict(type=type(exc).__name__,reason=str(exc),
                                                protocol_sha256=fingerprint(plan)))
            raise


def acquire(plan,source,events,host,views,checkpoints,boundaries,backend,output,sender,authorization):
    budget=previous.create_accounts(output,plan)
    registry=FailureOperatorRegistry(output/'registry.jsonl',FailureEvidenceStore(output/'failures.jsonl'))
    runner=EnvironmentPolicyRunner(backend,output/'worker.jsonl',budget)
    evidence=import_source_events('B',events,host,output,registry.evidence,plan['run_id'])
    known={row['event_id']:row for row in registry.evidence.visible(time(),plan['run_id'])}
    receipts=[]
    analyses,rejected=[],[]

    def model(name,kind,payload,parser,**extra):
        response=stage_request(output,name,kind,payload,parser,budget,sender=sender,authorization=authorization,
                               protocol=PROTOCOL,network_policy=plan['network_policy'] if sender is None else None,**extra)
        receipts.append(dict(stage=name,response_sha256=response['response_sha256'],usage=trusted_usage(response['raw_response'])))
        return response,json.loads(response['specification']) if not response.get('parse_status') else None

    for start in range(0,len(events),8):
        batch=events[start:start+8]
        response,value=model(f'analysis_{start//8}','analyze',dict(events=views[start:start+8]),
                             lambda output:parse_step_analyses(output,batch))
        if response['wire_sha256']!=plan['analysis_wire_sha256'][start//8]:
            raise PermissionError('expanded analysis wire drift')
        if value:
            analyses.extend(value['analyses'])
            rejected.extend(value['rejected'])
        else:
            rejected.extend(dict(evidence_id=row['evidence_id'],reason='BATCH_DELIVERY_REJECTED') for row in batch)
    eligible=[row for row in analyses if row['decision']=='HYPOTHESIS']
    merged=model('merge','merge',dict(analyses=eligible),
                 lambda value:parse_mechanisms(value,eligible))[1] if eligible else None
    ranked=rank_mechanisms(merged,analyses) if merged else []
    candidates=[]
    for index,item in enumerate(ranked):
        mechanism=item['proposal']
        selected=[row for row in checkpoints if row['evidence_id'] in mechanism['evidence_ids']]
        record=dict(mechanism_id=item['mechanism_id'],mechanism=mechanism,
                    source_groups=sorted({row['group'] for row in selected}),support_count=len(selected),
                    status='FROZEN_CAP_NOT_SELECTED')
        candidates.append(record)
        if index>=CAP:
            continue
        payload=previous.generation_payload(mechanism,eligible,views)
        anchors={row['evidence_id']:row['failure_step_id'] for row in payload['source_receipts']}
        steps={step[0] for row in payload['source_receipts'] for step in row['steps']}
        directory=output/f'candidate_{index}'
        response,parsed=model(directory.name,'analyze',payload,lambda value:parse_skill(value,anchors,steps),
                              analysis_prompt=PROMPT)
        record.update(parsed or dict(status='PROVIDER_DELIVERY_REJECTED',candidate=None))
        if not record['candidate']:
            continue
        skill=record['candidate']
        generated=dict(code=worker_source(skill),description='Host-compiled declarative adapter',
                       applicability=skill['scope'],model=response['model'],id=response['id'],
                       response_sha256=response['response_sha256'])
        registration=register_environment_candidate(directory,generated,dict(mechanism=mechanism,skill=skill),
            list(evidence.values()),known,backend.manifest(),registry,engineering=sender is not None,
            protocol=PROTOCOL,baseline='alfworld-structured-expanded-shadow')
        record.update(registration)
        if record['status']!='SHADOW':
            continue
        card=FailureOperator.from_dict(registration['card'])
        source_rows=[]
        for cp in selected:
            replay=previous.validate_source(source['data_root'],host[cp['evidence_id']],skill,card,
                                            runner,registry,directory/f"source_{cp['sequence']}.json")
            source_rows.append({**replay,'group':cp['group']})
        boundary_rows=[]
        for fixture in boundaries:
            verdict,operator=previous.decision(skill,fixture['public'],card,runner,starting=True)
            boundary_rows.append(dict(id=fixture['public']['id'],group=fixture['group'],category=fixture['category'],
                expected=fixture['expected'],status=operator['status'],conditions=verdict,operator=operator))
        record.update(source_validation=source_rows,boundary_validation=boundary_rows,
                      development_reviewable=(any(x['local_repair_verified'] for x in source_rows)
                          and all(x['stop']!='POLICY_ERROR' for x in source_rows)
                          and all(x['status']=='declined' for x in boundary_rows)))
        if registry.state(card)['permission']!='shadow':
            raise PermissionError('expanded candidate is no longer Shadow')
        save(directory/'validation.json',record)
    groups={}
    for group in (*previous.GROUPS,NAVIGATION):
        source_rows=[row for candidate in candidates for row in candidate.get('source_validation',[]) if row['group']==group]
        boundary_rows=[row for candidate in candidates for row in candidate.get('boundary_validation',[]) if row['group']==group]
        groups[group]=dict(
            learning=sum(cp['group']==group for cp in checkpoints),
            source_checks=len(source_rows),local_witnesses=sum(row['local_repair_verified'] for row in source_rows),
            wins=sum(row['won'] for row in source_rows),boundary_checks=len(boundary_rows),
            false_triggers=sum(row['expected']=='NO' and row['status']=='applied' for row in boundary_rows),
            uncertain_triggers=sum(row['expected']=='UNKNOWN' and row['status']=='applied' for row in boundary_rows))
    usage=Counter()
    for receipt in receipts:
        usage.update(receipt['usage'])
    result=dict(scope=plan['scope'],protocol_sha256=fingerprint(plan),analyses=analyses,rejected=rejected,merge=merged,
                candidates=candidates,groups=groups,model_receipts=receipts,usage=dict(usage),budget=budget.snapshot(),
                paid_requests=len(receipts) if sender is None else 0,independent_gate_games=0)
    if any(sha(path)!=digest for path,digest in plan['historical_sha256'].items()):
        raise PermissionError('historical artifacts changed during expanded run')
    save(output/'result.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','run'))
    parser.add_argument('--base',type=Path,default=Path.home()/'.local/share/flowevo')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--authorization',type=Path)
    args=parser.parse_args()
    if args.action=='prepare':
        plan=prepare(args.base,args.output)
        print(canonical(dict(status='PREPARED_NOT_AUTHORIZED',protocol_sha256=fingerprint(plan),
                             max_calls=plan['max_calls'],max_cost_microusd=plan['max_cost_microusd'])))
    else:
        if args.authorization is None:
            parser.error('run requires --authorization')
        result=run(args.base,args.output,authorization=read(args.authorization))
        print(canonical(dict(paid_requests=result['paid_requests'],groups=result['groups'],
                             candidate_statuses=[row['status'] for row in result['candidates']])))


if __name__=='__main__':
    main()
