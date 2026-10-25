"""Public-only same-prefix A/B counterfactual wires. No provider or future result reuse."""
import hashlib
from run_learning_stream import restore_budget
from failure_evo.contracts import PublicTaskView,PublicFeedback,strict_public_task,strict_feedback,canonical
from failure_evo.repair_choice_v2 import generic_choice,eligible_actions
from failure_evo.repair_choice import action_messages
from failure_evo.workflow_protocol_v2 import prepare,Limits

def reconstruct(hook, limits=None):
    task=hook['checkpoint_task']
    if set(task)!={'problem_id','prompt','starter_code','function_name','public_examples'}:raise ValueError('projected task fields')
    if any(not isinstance(task[k],str) for k in ('problem_id','prompt','starter_code','function_name')):raise ValueError('projected task types')
    examples=task['public_examples']
    if not isinstance(examples,list) or any(set(c)!={'input','expected'} or any(not isinstance(v,str) for v in c.values()) for c in examples):raise ValueError('projected examples')
    view=PublicTaskView(**dict(task,public_examples=tuple(canonical(c) for c in examples)))
    code=hook['before_code'];feedback=hook['before_feedback'];strict_feedback(feedback)
    if hashlib.sha256(code.encode()).hexdigest()!=hook['before_sha256']:raise ValueError('checkpoint code mismatch')
    budget=restore_budget(hook['checkpoint_budget']);fb=strict_feedback(feedback)
    generic=generic_choice(code,fb,budget);learned=hook['action']
    if generic!=hook['generic_action']:raise ValueError('generic checkpoint mismatch')
    allowed=eligible_actions(code,fb,budget)
    result={'evidence':'UNSENT_COUNTERFACTUAL','generic_action':generic,'learned_action':learned,'branches':{}}
    for label,action in [('generic',generic),('learned',learned)]:
        if action not in allowed:raise ValueError('action not legal at frozen prefix')
        request=prepare(action_messages(action,view,code,fb),limits=limits or Limits(),temperature=0)
        result['branches'][label]={'action':action,'wire':request.wire.decode() if isinstance(request.wire,bytes) else request.wire,'wire_sha256':request.sha256}
    result['same_wire']=result['branches']['generic']['wire_sha256']==result['branches']['learned']['wire_sha256']
    return result
