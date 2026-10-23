"""Constrained repair-choice v1. Opt-in; historical Python protocols unchanged.

Rules never execute Python, author prompts, change budgets or authorize themselves.
All model traffic uses WorkflowClient/SharedTransport and the caller's SAME Budget.
"""
import json
from .contracts import PublicTaskView, PublicFeedback, canonical, fingerprint
from .workflow_protocol_v2 import WorkflowClient, program_observation
from .native_adapter import SYSTEM_PROMPT

VERSION = 'repair-choice-json-v1'
ACTIONS = ('REPAIR_EXISTING', 'REGENERATE_FRESH')
STATES = ('STRUCTURAL_PASS', 'COMPILE_ERROR', 'NO_COMPLETE_CODE')
RESULTS = ('WRONG_ANSWER', 'RUNTIME_ERROR', 'TIME_LIMIT', 'COMPILE_ERROR', 'NO_COMPLETE_CODE')
SCHEMA = {'type':'object','additionalProperties':False,'required':['when','action','fallback'],
 'properties':{'when':{'type':'object','additionalProperties':False,
 'required':['candidate_state','public_result','remaining_calls_min'], 'properties':{
 'candidate_state':{'enum':list(STATES)},'public_result':{'enum':list(RESULTS)},
 'remaining_calls_min':{'type':'integer','minimum':1,'maximum':5}}},
 'action':{'enum':list(ACTIONS)},'fallback':{'const':'NATIVE'}}}
PROTOCOL_HASH = fingerprint({'version':VERSION,'schema':SCHEMA})

def validate_rule(value):
    if not isinstance(value,dict) or set(value)!={'when','action','fallback'}:raise ValueError('RULE_FIELDS')
    w=value['when']
    if not isinstance(w,dict) or set(w)!={'candidate_state','public_result','remaining_calls_min'}:raise ValueError('CONDITION_FIELDS')
    if w['candidate_state'] not in STATES or w['public_result'] not in RESULTS:raise ValueError('CONDITION_VALUE')
    if type(w['remaining_calls_min']) is not int or not 1<=w['remaining_calls_min']<=5:raise ValueError('CALL_THRESHOLD')
    if value['action'] not in ACTIONS or value['fallback']!='NATIVE':raise ValueError('ACTION_PERMISSION')
    if value['action']=='REPAIR_EXISTING' and w['candidate_state']=='NO_COMPLETE_CODE':raise ValueError('NO_SOURCE_TO_REPAIR')
    return json.loads(canonical(value))

def parse_rule(text):
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out:raise ValueError('DUPLICATE_FIELD')
            out[k]=v
        return out
    return validate_rule(json.loads(text,object_pairs_hook=unique))

def compile_messages(public_evidence):
    """Caller supplies audited public evidence only, never sealed evaluation data."""
    return [{'role':'system','content':'Learn one repair-choice rule from public failure evidence. Return only JSON matching the schema. No Python, free-text instruction, task ID predicate, permissions or budget changes.'},
            {'role':'user','content':canonical({'representation':VERSION,'schema':SCHEMA,
              'meaning':{'STRUCTURAL_PASS':'Python syntax passed, not completeness/correctness proof',
              'REPAIR_EXISTING':'Send current source and audited public feedback',
              'REGENERATE_FRESH':'Send problem and public checks without failed source, old response or traceback'},
              'evidence':public_evidence})}]

def observation(code,feedback,budget):
    if not isinstance(feedback,PublicFeedback):raise TypeError('typed public feedback required')
    return {'candidate_state':program_observation(code)['structural_status'],
            'public_result':feedback.status,'remaining_calls':max(0,budget.max_calls-budget.calls)}

def choose(rule,code,feedback,budget):
    rule=validate_rule(rule);o=observation(code,feedback,budget);w=rule['when']
    match=(o['candidate_state']==w['candidate_state'] and o['public_result']==w['public_result']
           and o['remaining_calls']>=w['remaining_calls_min'] and budget.remaining_seconds>0)
    return rule['action'] if match else 'NATIVE'

def generic_choice(code,feedback,budget):
    """Frozen strong Generic has exactly the same two host capabilities."""
    o=observation(code,feedback,budget)
    if o['public_result'] not in RESULTS or not o['remaining_calls'] or budget.remaining_seconds<=0:return 'NATIVE'
    return 'REGENERATE_FRESH' if o['candidate_state']=='NO_COMPLETE_CODE' else 'REPAIR_EXISTING'

def action_messages(action,task,code,feedback):
    if action not in ACTIONS:raise ValueError('ACTION_PERMISSION')
    if not isinstance(task,PublicTaskView) or not isinstance(feedback,PublicFeedback):raise TypeError('typed public projections required')
    # A fresh request does not copy actual output/exception text, which may embed source.
    public=feedback.to_dict()
    if action=='REGENERATE_FRESH':
        public={'status':feedback.status,'public_cases':[{k:c[k] for k in ('input','expected') if k in c} for c in public['public_cases']]}
    data={'task':task.to_dict(),'public_feedback':public,'mode':action}
    if action=='REPAIR_EXISTING':
        if not code.strip():raise ValueError('NO_SOURCE_TO_REPAIR')
        data['candidate_code']=code
    instruction=('Repair the supplied program using the public evidence.' if action=='REPAIR_EXISTING' else
                 'Develop a fresh solution from the problem and public examples; no previous implementation is supplied.')
    return [{'role':'system','content':SYSTEM_PROMPT}, {'role':'user','content':instruction+
      '\nReturn a complete executable Python program in one python fence. Avoid extended explanation. Do not special-case examples.\n'+canonical(data)}]

class RepairChoiceClient(WorkflowClient):
    def execute_action(self,action,task,code,feedback,budget):
        return self._call(action_messages(action,task,code,feedback),budget,0,'repair-choice/'+action)

    def attempt(self,action,task,code,feedback,budget,evaluate):
        """One action only. evaluate must be the trusted isolated public evaluator.

        No automatic retry here: caller resumes native workflow with the same
        depleted budget. Transport exceptions propagate, including unknown sends.
        """
        if action=='NATIVE':return {'status':'declined','fallback':'NATIVE','original_code':code}
        response=self.execute_action(action,task,code,feedback,budget)
        proposed=response['code'];checked=evaluate(proposed,task,budget) if proposed else None
        if checked is not None and not isinstance(checked,PublicFeedback):raise TypeError('evaluator must return audited PublicFeedback')
        cases=checked.to_dict()['public_cases'] if checked else []
        passed=bool(checked and checked.status=='PUBLIC_PASS' and cases and all(
            'expected' in c and 'actual' in c and c['actual']==c['expected'] and not c.get('exception_class') for c in cases))
        return {'status':'applied' if passed else 'declined','action':action,'fallback':None if passed else 'NATIVE',
                'code':proposed if passed else code,'proposed_code':proposed,'response':response,
                'public_feedback':checked.to_dict() if checked else None}


def generate_rule(transport,public_evidence,*,request_prefix,limits,allow_revision=False):
    """One candidate plus at most one diagnostic revision on the learning ledger.

    transport must already be authorized for a fresh run and frozen budget.
    Returned raw versions must be persisted by the experiment runner.
    """
    from .workflow_protocol_v2 import prepare
    base=compile_messages(public_evidence);versions=[]
    for index in range(2 if allow_revision else 1):
        messages=list(base)
        if versions:
            messages.append({'role':'user','content':'One bounded revision. Return the complete rule under the same schema.\n'+canonical(versions[-1])})
        prepared=prepare(messages,limits=limits,json_output=True)
        response=transport.send(prepared,request_id=f'{request_prefix}/rule/{index}',capability='repair-choice-compile')
        row={'response':response,'request_sha256':prepared.sha256,'protocol_hash':PROTOCOL_HASH}
        try:
            if response.get('finish_reason')=='length':raise ValueError('TRUNCATED_OUTPUT')
            rule=parse_rule(response['text'])
        except (ValueError,TypeError,KeyError) as exc:
            row['diagnosis']=str(exc);versions.append(row);continue
        versions.append(row)
        return {'representation':VERSION,'rule':rule,'rule_hash':fingerprint(rule),'versions':versions}
    return {'representation':VERSION,'rule':None,'versions':versions}
