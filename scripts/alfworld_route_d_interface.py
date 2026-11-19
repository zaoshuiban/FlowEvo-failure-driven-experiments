"""Route D public single-action adapter. No network on import or in preflight.

The injected chooser owns the existing durable model transport and authorization.
No policy, recovery route, or fallback action is supplied by this adapter.
"""
import copy
import json

ACTION_PROMPT = '''Continue the household task from the supplied current public state.
Choose exactly one action from the current admissible_commands, based only on the
public observations so far. Return one JSON object {"action":"...","reason":"..."}.
You may explicitly give up with {"action":null,"reason":"..."}.
Do not output Python or a plan to be executed by the host. The host executes only
your single legal action. Only environment won=true establishes episode success.
You have the remaining actions shown, within the original 50-action task limit.
'''


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def public_state(case, suffix=(), error=None):
    # Deliberate whitelist: task metadata, skills, historical outcome and suffix
    # outside the checkpoint never enter the acting model's input.
    steps = case['steps'] + list(suffix)
    if len(case['steps']) != 16 or len(steps) > 50:
        raise ValueError('Route D requires the original step-16 checkpoint')
    current = steps[-1] if steps else case['initial']
    result = dict(goal=case['goal'], initial_observation=case['initial']['observation'],
                  history=[{k:s[k] for k in ('action','observation')} for s in steps],
                  observation=current['observation'], admissible_commands=list(current['commands']),
                  used_actions=len(steps), remaining_actions=50-len(steps))
    if error is not None:
        result['delivery_diagnostic'] = copy.deepcopy(error)
    return result


def wire_for(state, model, stage='P1'):
    if model not in ('deepseek-flash','deepseek-v4-pro'):
        raise ValueError('model not frozen')
    strong = model == 'deepseek-v4-pro'
    wire = dict(model=model,messages=[dict(role='system',content=ACTION_PROMPT),
                dict(role='user',content=canonical(state))],
                max_tokens=8192 if strong else 1024,stream=False,
                thinking={'type':'enabled' if strong else 'disabled'},
                reasoning_effort='high' if strong else 'none',response_format={'type':'json_object'})
    if not strong: wire['temperature']=0
    if len(canonical(wire).encode()) > 65536:
        raise ValueError('INPUT_LIMIT_NO_TRUNCATION')
    return wire


def parse_action(text, commands, finish_reason='stop'):
    def pairs(values):
        result={}
        for k,v in values:
            if k in result:raise ValueError('DUPLICATE_JSON_KEY')
            result[k]=v
        return result
    try:
        if finish_reason != 'stop': raise ValueError('INCOMPLETE_DELIVERY')
        v=json.loads(text, object_pairs_hook=pairs)
        if not isinstance(v,dict) or set(v) != {'action','reason'} or not isinstance(v['reason'],str):
            raise ValueError('EXPECTED_ACTION_REASON_OBJECT')
        if v['action'] is None:return dict(status='GIVE_UP',reason=v['reason'])
        if not isinstance(v['action'],str) or v['action'] not in commands:
            raise ValueError('ACTION_NOT_IN_CURRENT_LEGAL_LIST')
        return dict(status='LEGAL',action=v['action'],reason=v['reason'])
    except (ValueError,TypeError) as exc:
        return dict(status='DELIVERY_ERROR',error=str(exc))


def discover(case, env, choose, save, feedback):
    """env is already exactly replayed. choose(state, request_index) returns raw
    response; save persists each receipt before any action. Infrastructure errors
    propagate: they must stop the run, never become a task failure or retry.
    """
    suffix=[];invalid=0;requests=0;error=None;won=False;stop='ACTION_LIMIT'
    while len(suffix)<34 and requests<38:
        state=public_state(case,suffix,error)
        raw=choose(copy.deepcopy(state),requests+1);requests+=1
        save(f'request_{requests:02d}_raw',raw)
        choice=raw['choices'][0]
        decision=parse_action(choice['message']['content'],state['admissible_commands'],choice['finish_reason'])
        save(f'request_{requests:02d}_decision',dict(state=state,decision=decision))
        if decision['status']=='GIVE_UP':stop='GIVE_UP';break
        if decision['status']=='DELIVERY_ERROR':
            invalid+=1;error=dict(raw_output=choice['message']['content'],**decision)
            if invalid>4:stop='DELIVERY_CORRECTION_LIMIT';break
            continue
        error=None
        # STARTED must be durable before invoking the real environment. An
        # unmatched STARTED forbids automatic replay/resume after interruption.
        save(f'action_{len(suffix)+1:02d}_started',dict(action=decision['action']))
        result=env.step(decision['action'])
        step=feedback(decision['action'],result);suffix.append(step)
        save(f'action_{len(suffix):02d}_returned',step)
        if step['won']:won=True;stop='EPISODE_WON';break
        if step['done']:stop='ENVIRONMENT_DONE';break
    return dict(model_requests=requests,environment_actions=len(suffix),invalid_action_requests=invalid,
                steps=suffix,won=won,stop_reason=stop)
