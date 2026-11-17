"""A3 deterministic TRAIN-only input organization. No execution or authority."""
import math
from collections import Counter
from failure_evo.contracts import canonical,fingerprint
from failure_evo.wire_input_policy import validate_wire_input_policy,check_wire
from . import recovery_applicability_learning as L
from .route_a_training_labels import model_projection,goal_parts

VERSION='route-a3-input-v1'
PRICE=dict(verified_date='2026-11-13',source='https://api-docs.deepseek.com/quick_start/pricing/',
    model_version='DeepSeek-V4.1-Flash-1017',peak_input_per_million=0.30,peak_output_per_million=1.20)


def policy(kib):
    p=dict(version='route-a3-wire-v1',model='deepseek-flash',max_wire_input_bytes=kib*1024,
        max_input_tokens=kib*1024+256,model_context_tokens=1000000,output_tokens=4096,
        estimator='UTF8_BYTES_PLUS_256_UPPER')
    validate_wire_input_policy(p,p['model']);return p


def wire(payload,prompt,temperature=0.6):
    return dict(model='deepseek-flash',messages=[dict(role='system',content=prompt),dict(role='user',content=canonical(payload))],
        max_tokens=4096,temperature=temperature,thinking={'type':'disabled'},reasoning_effort='none',response_format={'type':'json_object'},stream=False)


def measure(payload,prompt,temperature=0.6):
    w=wire(payload,prompt,temperature);s=canonical(w);n=len(s.encode())
    # Supplier's character ratios are only a rough local estimate, not usage.
    estimated=math.ceil(sum(0.3 if ord(c)<128 else 0.6 for c in s))+256
    return dict(wire_bytes=n,local_input_tokens_estimate=estimated,estimate_method='supplier character heuristic: ASCII*0.3 + non-ASCII*0.6 + 256 framing',
        provider_input_tokens=None,reserved_input_tokens=n+256,output_tokens=4096,
        context_headroom_conservative=1000000-(n+256)-4096,
        estimated_peak_cost_usd=(estimated*0.30+4096*1.20)/1000000,
        conservative_peak_cost_usd=((n+256)*0.30+4096*1.20)/1000000)


def public_packet(rows,code):return L.training_packet(rows,code)


def summarize(rows):
    targets=[]
    for r in rows:
        p=goal_parts(r['candidate_context']['goal']);targets.append(p[1].category if p else 'UNPARSED')
    return dict(samples=len(rows),labels=dict(Counter(r['label'] for r in rows)),
        task_types=dict(Counter(r['task_type'] for r in rows)),containers=dict(Counter(targets)),
        games=len({r['game_sha256'] for r in rows}),physical_groups=len({r['physical_state_group_id'] for r in rows}),
        repetition_weights='each selected sample exactly once; no duplication',
        evidence='whole public sample preserved; no within-sample truncation')


def organize(rows,code,kib=None):
    if any(r['role']!='TRAIN' for r in rows):raise PermissionError('non-TRAIN organization')
    if kib is None:selected=list(rows)
    else:
        remaining=sorted(rows,key=lambda r:fingerprint(r['sample_id']));selected=[]
        counts=Counter();games=set();groups=set();types=set();containers=set()
        while remaining:
            # Explicit class balancing without copying negatives. Prefer new
            # task, target, game and checkpoint within the currently rare class.
            def priority(r):
                p=goal_parts(r['candidate_context']['goal']);target=p[1].category if p else 'UNPARSED'
                return (counts[r['label']],r['task_type'] in types,target in containers,
                        r['game_sha256'] in games,r['physical_state_group_id'] in groups,fingerprint(r['sample_id']))
            row=min(remaining,key=priority);remaining.remove(row)
            packet=public_packet(selected+[row],code)
            if measure(dict(candidate_id='candidate_0',training_input=packet),L.INITIAL_PROMPT)['wire_bytes']>kib*1024:continue
            selected.append(row);counts[row['label']]+=1;types.add(row['task_type']);games.add(row['game_sha256']);groups.add(row['physical_state_group_id'])
            p=goal_parts(row['candidate_context']['goal']);containers.add(p[1].category if p else 'UNPARSED')
    packet=public_packet(selected,code)
    return dict(packet=packet,selected_ids=[fingerprint(r['sample_id']) for r in selected],
        omitted_ids=[fingerprint(r['sample_id']) for r in rows if r not in selected],
        coverage=summarize(selected),measurement=measure(dict(candidate_id='candidate_0',training_input=packet),L.INITIAL_PROMPT))


FEEDBACK_RULE=dict(version='a3-feedback-v1',order=['FALSE_APPLICABILITY','UNSUPPORTED_MATCH','WORKER_ERROR','FALSE_REJECTION',
    'SOURCE_REPAIR_FAILED','UNNECESSARY_UNKNOWN','UNCERTAINTY_MISCLASSIFIED','CORRECT_MATCH_CONTROL','OTHER_CORRECT'],
    max_correct_controls=8,max_action_receipts_per_case=18,full_previous_code=True,
    omit_rule='whole sample/feedback only; record all omitted IDs; never truncate code',no_validation=True)


def revision(attempt,train,p):
    # Reuse A2's candidate/role/parent checks, then project out repeated raw
    # delivery material and preserve bounded actual execution receipts only.
    full=L.feedback(attempt,train,{})
    by_id={fingerprint(r['sample_id']):r for r in train}
    diagnostics=dict(delivery_status=attempt['delivery']['status'],static=attempt.get('static'))
    payload=dict(candidate_id=attempt['candidate_id'],parent_version=attempt['version'],previous_code=attempt.get('code'),
        parent_source_sha256=attempt.get('code_sha256'),diagnostics=diagnostics,own_train_feedback=[],
        omitted_feedback=[],feedback_rules=FEEDBACK_RULE)
    items=[]
    for x in full['own_train_feedback']:
        row=by_id[x['sample_id']]
        actions=x['execution']['actions_executed']
        if len(actions)>18:raise PermissionError('execution receipt exceeds frozen source window')
        x=dict(x,public_evidence=model_projection(row),execution=dict(x['execution'],actions_executed=[
            {k:a[k] for k in ('action','observation','score','done','won') if k in a} for a in actions]))
        items.append(x)
    def order(x):
        c=x['supervision']['error']
        if c=='CORRECT':
            c=('SOURCE_REPAIR_FAILED' if x['execution']['recovery_verified'] is False else
               'CORRECT_MATCH_CONTROL' if x['supervision']['label']=='MATCH' else 'OTHER_CORRECT')
        return (FEEDBACK_RULE['order'].index(c),x['sample_id'])
    controls=0
    for x in sorted(items,key=order):
        correct=x['supervision']['error']=='CORRECT' and x['execution']['recovery_verified'] is not False
        if correct and controls>=8:
            payload['omitted_feedback'].append(dict(sample_id=x['sample_id'],reason='CORRECT_CONTROL_CAP'));continue
        proposal=dict(payload,own_train_feedback=payload['own_train_feedback']+[x])
        # Reserve small deterministic space for all omission identities.
        if measure(proposal,L.REVISION_PROMPT)['wire_bytes']+len(items)*160>p['max_wire_input_bytes']:
            payload['omitted_feedback'].append(dict(sample_id=x['sample_id'],reason='FROZEN_WIRE_BOUND'));continue
        payload['own_train_feedback'].append(x);controls+=int(correct)
    check_wire(wire(payload,L.REVISION_PROMPT),p)
    if payload['previous_code']!=attempt.get('code'):raise PermissionError('source truncation')
    return payload
