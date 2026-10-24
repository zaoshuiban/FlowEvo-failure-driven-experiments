"""Explicit v2 artifact/action semantics; v1 stays frozen."""
import json
from .contracts import canonical, fingerprint, PublicFeedback
from .workflow_protocol_v2 import program_observation
from .repair_choice import ACTIONS, validate_rule as v1_validate, action_messages, RepairChoiceClient
VERSION='repair-choice-json-v2'
STATES=('STRUCTURAL_PASS','NO_ENTRY','NO_COMPLETE_CODE','COMPILE_ERROR')

def observation(code,feedback,budget):
    o=program_observation(code)
    state=o['structural_status']
    if state=='STRUCTURAL_PASS' and o['definitions_and_imports_only']:state='NO_ENTRY'
    return dict(candidate_state=state,public_result=feedback.status,remaining_calls=max(0,budget.max_calls-budget.calls))

def eligible_actions(code,feedback,budget):
    if not isinstance(feedback,PublicFeedback) or feedback.visibility!='public':return ()
    if budget.max_calls-budget.calls<2 or budget.remaining_seconds<=0:return ()
    if budget.max_tokens-budget.used_tokens-sum(budget.reservations.values())<=0 or budget.max_tools-budget.tool_calls<1:return ()
    state=observation(code,feedback,budget)['candidate_state']
    if feedback.status in ('PUBLIC_PASS','UNKNOWN','PRIVATE_RESULT_WITHHELD','EVALUATOR_ERROR','BUDGET_EXHAUSTED'):return ()
    if state=='NO_COMPLETE_CODE':return ('REGENERATE_FRESH',) if feedback.status=='NO_COMPLETE_CODE' else ()
    if state=='COMPILE_ERROR':return ACTIONS if feedback.status=='COMPILE_ERROR' else ()
    cases=feedback.to_dict()['public_cases']
    if feedback.status not in ('WRONG_ANSWER','RUNTIME_ERROR') or not cases:return ()
    if not any(c.get('exception_class') or ('actual' in c and 'expected' in c and c['actual']!=c['expected']) for c in cases):return ()
    return ('REGENERATE_FRESH',) if state=='NO_ENTRY' else ACTIONS

def validate_rule(value):
    if not isinstance(value,dict) or not isinstance(value.get('when'),dict) or value['when'].get('candidate_state') not in STATES:raise ValueError('v2 condition')
    if value['when'].get('public_result') not in ('WRONG_ANSWER','RUNTIME_ERROR','COMPILE_ERROR','NO_COMPLETE_CODE'):raise ValueError('v2 public result')
    patched=json.loads(canonical(value));state=patched['when']['candidate_state']
    patched['when']['candidate_state']='NO_COMPLETE_CODE' if state=='NO_ENTRY' else state
    v1_validate(patched)
    return json.loads(canonical(value))

def choose(rule,code,feedback,budget):
    rule=validate_rule(rule);o=observation(code,feedback,budget);w=rule['when']
    return rule['action'] if (rule['action'] in eligible_actions(code,feedback,budget) and
        o['candidate_state']==w['candidate_state'] and o['public_result']==w['public_result'] and
        o['remaining_calls']>=w['remaining_calls_min']) else 'NATIVE'

def generic_choice(code,feedback,budget):
    # Audit the existing native retry's supplied context, not an idealized v2
    # selector: native repair_messages still includes a definitions-only source.
    if feedback.status in ('PUBLIC_PASS','UNKNOWN','EVALUATOR_ERROR') or budget.max_calls<=budget.calls:return 'NATIVE'
    return 'REPAIR_EXISTING' if code.strip() else 'REGENERATE_FRESH'

SCHEMA={'representation':VERSION,'required':['when','action','fallback'],
        'when':{'candidate_state':list(STATES),'public_result':['WRONG_ANSWER','RUNTIME_ERROR','COMPILE_ERROR','NO_COMPLETE_CODE'],'remaining_calls_min':'integer 1..5'},
        'action':list(ACTIONS),'fallback':'NATIVE','additionalProperties':False}
PROTOCOL_HASH=fingerprint(SCHEMA)
