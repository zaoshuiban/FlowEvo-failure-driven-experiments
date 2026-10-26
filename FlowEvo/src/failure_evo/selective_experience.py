"""S21 offline-only selective experience prototype. No sender, code execution or grants.

A recommendation is never an Experimental permission. Existing S20 callers do
not import this module. `prepare_view` is a pure request preview; sending remains
with the existing authorized SharedTransport/Worker path.
"""
import ast
import copy
import math
from .contracts import fingerprint, strict_feedback, PublicTaskView
from .learning_evidence_bundle import check_packet, checkpoint_budget
from .repair_choice_v2 import observation, eligible_actions, generic_choice
from .repair_choice import action_messages
from .workflow_protocol_v2 import WorkflowClient, prepare

VERSION = 'selective-experience-offline-v1'
STAGES = {s: i for i, s in enumerate(('l1','l2a','l2b','l3','l4'))}
KINDS = ('TARGETED_REPAIR_GUIDANCE','LEGAL_ACTION_SWITCH')
FEATURES = {'candidate_state','public_result','repeat_same_program_feedback',
            'definitions_only','exception_classes','remaining_calls_min'}
CARD_FIELDS = {'version','experience_id','origin','source_refs','observed_failure_pattern',
               'applicability_conditions','proposed_intervention','expected_local_effect',
               'refusal_conditions','stop_conditions','evidence_level','uncertainty',
               'available_from','provenance_hash','card_hash'}


def finite(v):
    if type(v) not in (int,float) or not math.isfinite(v) or v < 0:
        raise ValueError('invalid host time')
    return v


def public_signature(p):
    return fingerprint([p['candidate_sha256'],p['feedback']])


def snapshot(packet, *, observed_at, history=()):
    """Host-observed current prefix only. History is same-task, earlier-stage data.
    Stage ordering resolves equal task-finalization timestamps, never later stages.
    Expected outputs here are only the packet's already-public test expectations.
    """
    check_packet(packet);finite(observed_at)
    if packet['stage'] not in STAGES:raise ValueError('unknown stage')
    prior=[]
    for h in history:
        if set(h)!={'packet','observed_at'}:raise ValueError('history fields')
        p=check_packet(h['packet']);finite(h['observed_at'])
        if (p['task_id']!=packet['task_id'] or h['observed_at']>observed_at or
            p['stage'] not in STAGES or STAGES[p['stage']]>=STAGES[packet['stage']]):
            raise ValueError('future or cross-task local history')
        prior.append(p)
    if len({p['event_id'] for p in prior})!=len(prior):raise ValueError('duplicate history')
    feedback=strict_feedback(packet['feedback']);budget=checkpoint_budget(packet)
    base=observation(packet['code'],feedback,budget)
    tree=None
    try:tree=ast.parse(packet['code'])
    except (SyntaxError,ValueError):pass
    only=bool(tree and tree.body and all(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Import,ast.ImportFrom)) or isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str) for n in tree.body))
    repeated=sorted(p['event_id'] for p in prior if public_signature(p)==public_signature(packet))
    features=dict(base,repeat_same_program_feedback=bool(repeated),definitions_only=only,
                  exception_classes=sorted({c['exception_class'] for c in packet['feedback']['public_cases'] if c.get('exception_class')}))
    evidence=dict(packet=copy.deepcopy(packet),observed_at=observed_at,history=sorted(copy.deepcopy(list(history)),key=lambda h:(STAGES[h['packet']['stage']],h['packet']['event_id'])))
    return dict(version=VERSION,features=features,legal_actions=list(eligible_actions(packet['code'],feedback,budget)),
                generic_action=generic_choice(packet['code'],feedback,budget),prior_same_signature=repeated,
                operations=sorted({type(n).__name__ for n in ast.walk(tree) if isinstance(n,(ast.For,ast.While,ast.Subscript,ast.Call))}) if tree else [],
                root_cause='UNKNOWN',evidence=evidence,input_hash=fingerprint(evidence))


def source_ref(packet, fact):
    check_packet(packet)
    if (fact.get('visibility')!='public' or fact.get('synthetic') is not False or
        any(fact.get(k)!=packet[k] for k in ('event_id','task_id','stage','candidate_sha256'))):
        raise ValueError('unbound public source')
    finite(fact['observed_at']);finite(fact['available_from'])
    if fact['available_from']<fact['observed_at']:raise ValueError('source chronology')
    return dict(event_id=packet['event_id'],task_id=packet['task_id'],lineage_id=fact.get('provenance_group_id') or packet['task_id'],
                packet_hash=fingerprint(packet),fact_hash=fingerprint(fact),observed_at=fact['observed_at'],available_from=fact['available_from'])


def seal_card(value):
    card=copy.deepcopy(value);card['version']=VERSION
    card['provenance_hash']=fingerprint(card['source_refs'])
    card['card_hash']=fingerprint(card)
    return validate_card(card)


def validate_card(card):
    if set(card)!=CARD_FIELDS or card['version']!=VERSION:raise ValueError('card schema/version')
    if card['card_hash']!=fingerprint({k:v for k,v in card.items() if k!='card_hash'}):raise ValueError('card changed')
    if card['origin'] not in ('HUMAN_HYPOTHESIS','DETERMINISTIC_EXTRACTION','MODEL_LEARNED'):raise ValueError('origin')
    # No offline label can manufacture source verification or registry authority.
    if card['evidence_level'] not in ('UNKNOWN','OBSERVED_PATTERN','LOCAL_SUPPORT'):raise ValueError('unsupported evidence claim')
    for key in ('experience_id','observed_failure_pattern','expected_local_effect','uncertainty'):
        if type(card[key]) is not str or not card[key].strip() or len(card[key])>2000:raise ValueError('card text')
    for key in ('refusal_conditions','stop_conditions'):
        if not isinstance(card[key],list) or not card[key] or any(type(x) is not str or not x for x in card[key]):raise ValueError('boundaries')
    refs=card['source_refs']
    if not isinstance(refs,list) or not refs or len({r['event_id'] for r in refs})!=len(refs):raise ValueError('source refs')
    if card['provenance_hash']!=fingerprint(refs):raise ValueError('provenance hash')
    for r in refs:
        if set(r)!={'event_id','task_id','lineage_id','packet_hash','fact_hash','observed_at','available_from'}:raise ValueError('source schema')
        if any(type(r[k]) is not str or not r[k] for k in ('event_id','task_id','lineage_id','packet_hash','fact_hash')):raise ValueError('source identity')
        if finite(r['observed_at'])>finite(r['available_from']):raise ValueError('source time')
    if finite(card['available_from'])<max(r['available_from'] for r in refs):raise ValueError('early publication')
    conditions=card['applicability_conditions']
    if not isinstance(conditions,dict) or not conditions or set(conditions)-FEATURES:raise ValueError('unsupported predicate')
    for k,v in conditions.items():
        if k in ('definitions_only','repeat_same_program_feedback') and type(v) is not bool:raise ValueError('boolean condition')
        if k=='remaining_calls_min' and (type(v) is not int or not 2<=v<=5):raise ValueError('budget condition')
        if k=='exception_classes' and (not isinstance(v,list) or any(type(x) is not str for x in v)):raise ValueError('exception condition')
        if k=='candidate_state' and v not in ('STRUCTURAL_PASS','NO_ENTRY','NO_COMPLETE_CODE','COMPILE_ERROR'):raise ValueError('state condition')
        if k=='public_result' and v not in ('WRONG_ANSWER','RUNTIME_ERROR','COMPILE_ERROR','NO_COMPLETE_CODE'):raise ValueError('status condition')
    action=card['proposed_intervention']
    if set(action)!={'kind','action','guidance'} or action['kind'] not in KINDS:raise ValueError('intervention schema')
    if action['kind']=='LEGAL_ACTION_SWITCH':
        if action['action'] not in ('REPAIR_EXISTING','REGENERATE_FRESH') or action['guidance']!='':raise ValueError('action')
    elif action['action']!='GENERIC' or not isinstance(action['guidance'],str) or not 1<=len(action['guidance'])<=1200:
        raise ValueError('guidance')
    return copy.deepcopy(card)


def recommend(state, cards, *, enabled=False, source_catalog=None, target_lineage=None):
    """Pure hypothetical decision. Actual behavior remains NO_INTERVENTION/Shadow.
    A source_catalog maps IDs to trusted {packet,fact}; no model assertions accepted.
    """
    evidence=state['evidence'];actual=snapshot(evidence['packet'],observed_at=evidence['observed_at'],history=evidence['history'])
    if actual!=state:raise ValueError('state changed')
    packet=evidence['packet'];time=evidence['observed_at'];features=state['features']
    audit=[];matches=[];catalog=source_catalog or {};ids=[]
    for raw in sorted(cards,key=lambda c:c.get('experience_id','')):
        c=validate_card(raw);ids.append(c['experience_id']);fails=[];checks={}
        if not enabled:fails.append('DISABLED')
        if c['available_from']>time:fails.append('FUTURE_EXPERIENCE')
        for ref in c['source_refs']:
            if ref['task_id']==packet['task_id'] or ref['lineage_id']==(target_lineage or packet['task_id']):fails.append('SAME_SOURCE_TASK_OR_LINEAGE')
            src=catalog.get(ref['event_id'])
            if not src or source_ref(src['packet'],src['fact'])!=ref:fails.append('SOURCE_NOT_VERIFIED')
            if ref['available_from']>time:fails.append('FUTURE_SOURCE')
        if c['evidence_level']=='UNKNOWN':fails.append('INSUFFICIENT_EVIDENCE')
        for k,v in c['applicability_conditions'].items():
            good=features['remaining_calls']>=v if k=='remaining_calls_min' else features[k]==v
            checks[k]=dict(expected=v,observed=features['remaining_calls'] if k=='remaining_calls_min' else features[k],satisfied=good)
            if not good:fails.append('CONDITION:'+k)
        if not state['legal_actions']:fails.append('NO_LEGAL_ACTION_OR_BUDGET')
        intervention=c['proposed_intervention'];action=state['generic_action'] if intervention['kind']=='TARGETED_REPAIR_GUIDANCE' else intervention['action']
        if action not in state['legal_actions']:fails.append('ACTION_NOT_ELIGIBLE')
        if intervention['kind']=='LEGAL_ACTION_SWITCH' and action==state['generic_action']:fails.append('GENERIC_EQUIVALENT')
        audit.append(dict(experience_id=c['experience_id'],card_hash=c['card_hash'],checks=checks,rejections=sorted(set(fails))))
        if not fails:matches.append(c)
    if len(ids)!=len(set(ids)):raise ValueError('duplicate experience id')
    unique={fingerprint(c['proposed_intervention']) for c in matches}
    proposal=None;reason='NO_APPLICABLE_EXPERIENCE'
    if len(unique)>1:reason='CONFLICT_ABSTAIN'
    elif matches:proposal=matches[0]['proposed_intervention'];reason='SHADOW_PROPOSAL_ONLY'
    result=dict(version=VERSION,input_hash=state['input_hash'],actual_kind='NO_INTERVENTION',permission='shadow',
                generic_action=state['generic_action'],proposal=proposal,matched_ids=[c['experience_id'] for c in matches],
                reason=reason,conditions=audit,actual_model_calls=0,extra_tool_calls=0,
                root_cause='UNKNOWN',proven_benefit=False)
    result['audit_hash']=fingerprint(result);return result


def prepare_view(state, decision, *, offline_proposal=False):
    """Build complete final wire before budget reservation. No send method here.
    The offline flag previews a shadow candidate; it grants no runtime permission.
    """
    if decision.get('input_hash')!=state['input_hash'] or decision.get('audit_hash')!=fingerprint({k:v for k,v in decision.items() if k!='audit_hash'}):raise ValueError('decision binding')
    ev=state['evidence']
    if snapshot(ev['packet'],observed_at=ev['observed_at'],history=ev['history'])!=state:raise ValueError('state changed before preparation')
    p=ev['packet'];client=WorkflowClient(None,'s21-preview')
    native=client.native_messages(dict(task=p['task_public'],stage=p['stage'],previous_candidate=p['code'],feedback=p['feedback']))
    messages=copy.deepcopy(native);proposal=decision['proposal'] if offline_proposal else None
    if proposal:
        if proposal['kind']=='TARGETED_REPAIR_GUIDANCE':messages[1]['content']+='\nCondition-specific public-evidence check:\n'+proposal['guidance']
        else:messages=action_messages(proposal['action'],PublicTaskView.project(p['task_public']),p['code'],strict_feedback(p['feedback']))
    base=prepare(native);selected=prepare(messages)
    return selected,dict(native_sha256=base.sha256,selected_sha256=selected.sha256,
                         request_changed=selected.wire!=base.wire,action_changed=bool(proposal and proposal['kind']=='LEGAL_ACTION_SWITCH' and proposal['action']!=state['generic_action']),
                         added_input_upper=selected.input_upper-base.input_upper,added_utf8_bytes=len(selected.wire.encode())-len(base.wire.encode()),
                         measure='UTF8 conservative upper proxy, NOT provider token usage',model_calls=0,mode='OFFLINE_SHADOW_PREVIEW' if offline_proposal else 'GENERIC_TRANSPARENT')
