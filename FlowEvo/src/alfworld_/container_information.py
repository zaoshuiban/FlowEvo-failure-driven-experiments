"""B3 same-source information projections and own-execution feedback only.

No environment strategy or task parser lives here. Host references never enter wire.
"""
from copy import deepcopy
from failure_evo.contracts import canonical, fingerprint
from .python_recovery_feedback import _INSTRUCTIONS
from .route_b_compact_projection import encode, INSTRUCTION

VERSION='route-b3-container-information-v1'
ARMS=('S','F','FR')
COMMON = _INSTRUCTIONS + '''
Shared task: continue local container-delivery recovery after a real unsuccessful
action in an already-running episode, not a new general planning problem.
context.state={} means only that YOUR program memory is empty. It does not mean
empty environment inventory, no prior actions, or incomplete earlier subgoals.
Reconstruct relevant progress from public history, observation and legal commands.
Preserve goal processing requirements, attributes and instance constraints.
Check the current action's preconditions separately from later actions. A later
action being unavailable now need not forbid a justified prerequisite action.
After every action recheck the fresh observation and admissible_commands.

Common command interface (syntax only, NOT a recovery plan): commands are exact
strings supplied by the environment. Examples of syntax use ROLE placeholders:
look; inventory; go to RECEPTACLE; examine ENTITY; take OBJECT from RECEPTACLE;
move OBJECT to RECEPTACLE; open RECEPTACLE; close RECEPTACLE;
clean OBJECT with TOOL; heat OBJECT with TOOL; cool OBJECT with TOOL; use TOOL.
Never output placeholders. Runtime instance names come from public evidence.
The host executes one legal action, then supplies its actual feedback. A legal
command is not automatically relevant. Decline when applicability is unsupported.

Evidence comprises labelled historical fragments, NOT a continuous reconstructed
episode. Do not fill omitted gaps with imagined events. C is public pre-fragment
context, not a reset instruction. R's starting observation/history may be omitted;
its command list is an actual recorded public list. Step IDs refer to original
events. No state has been inferred or repaired by the host.
''' + '\n' + INSTRUCTION
PROMPTS={
    'initial': 'Generate a fresh recovery program or ABSTAIN.\n'+COMMON,
    'engineering': 'Repair only your own delivery/static defects. No behavior results are supplied. Return full source or ABSTAIN.\n'+COMMON,
    'behavior': 'One behavior revision from your own public execution only. Candidate explanations are untrusted self-reports; environment receipts are observations. No reference route is supplied. Return complete source or ABSTAIN.\n'+COMMON,
}

def project_step(step,index,before):
    return dict(step_id=f'step_{index:03}',action=step['action'],observation=step['observation'],
        admissible_before=list(before['commands']),admissible_after=list(step['commands']),
        done=step['done'],won=step['won'])

def blocks(case,ref):
    o=case['origin'];a=o['projected']['anchor'];steps=o['steps'];pre=steps[a-2] if a>1 else o['initial']
    if (case['mechanism']!='container' or steps[a-1]['observation']!='Nothing happens.'
        or steps[a-1]['won'] or steps[a-1]['done'] or not steps[a:] or not steps[-1]['won']):
        raise ValueError('NO_VERIFIED_CONTAINER_FAILURE_RECOVERY')
    # The common context is the genuine state BEFORE the omitted failure,
    # never a synthetic post-failure observation with the receipt removed.
    if pre['observation']=='Nothing happens.':raise ValueError('COMMON_CONTEXT_CONTAINS_FAILURE_RECEIPT')
    c=dict(source_ref=ref,goal=o['projected']['goal'],context_at_step=a-1,
        observation=pre['observation'],admissible_commands=list(pre['commands']),
        history_not_included=True,role='DEVELOPMENT_LEARNING_SOURCES')
    f=dict(kind='recorded_prefix',first_step=1,last_step=a,
        start_context=dict(observation=o['initial']['observation'],admissible_commands=o['initial']['commands']),
        steps=[project_step(s,i,o['initial'] if i==1 else steps[i-2]) for i,s in enumerate(steps[:a],1)])
    r=dict(kind='recorded_success_fragment',first_step=a+1,last_step=len(steps),
        start_context=dict(admissible_commands=list(steps[a-1]['commands']),
            observation_included=False,history_included=False),
        omitted_prefix=dict(first_step=1,last_step=a),
        steps=[project_step(steps[i-1],i,steps[i-2]) for i in range(a+1,len(steps)+1)])
    return dict(C=c,F=f,R=r)

def packets(cases):
    pieces=[blocks(c,f'source_{i:02}') for i,c in enumerate(cases,1)]
    return {arm:dict(version=VERSION,examples=[{k:deepcopy(b[k]) for k in
        (('C','R') if arm=='S' else ('C','F') if arm=='F' else ('C','F','R'))} for b in pieces]) for arm in ARMS}

def feedback_sources(cases,evaluation):
    """All raw feedback is projected from own decisions; no witness/label/old R."""
    byref={r['source_ref']:r for r in evaluation['sources']};out=[]
    if len(byref)!=len(evaluation['sources']) or set(byref)!={c['id'] for c in cases}:raise PermissionError('TRAIN source mismatch')
    for c in cases:
        origin=c['origin'];a=origin['projected']['anchor'];prefix=origin['steps'][:a];r=byref[c['id']]
        current=prefix[-1];rows=[]
        for i,d in enumerate(r['decisions'],1):
            receipt=d.get('receipt');action=d.get('selected_action')
            row=dict(decision_index=i,candidate_self_report=deepcopy(d['operator']),
                candidate_explanation_is_environment_fact=False,worker_status=d['worker_status'],
                candidate_error=d.get('candidate_error'),selected_action=action,
                admissible_before=list(current['commands']),legal=action in current['commands'] if action else None,
                executed=receipt is not None,not_executed_reason=d.get('not_executed_reason'))
            if receipt is not None:
                row['environment_feedback']={k:deepcopy(receipt[k]) for k in ('action','observation','commands','done','won')}
                current=receipt
            rows.append(row)
        out.append(dict(source_ref=c['id'],initial_context=dict(goal=origin['projected']['goal'],
            observation=prefix[-1]['observation'],admissible_commands=prefix[-1]['commands'],
            history=[{k:s[k] for k in ('action','observation')} for s in prefix],state={}),
            decisions=rows,stop=r['stop'],won=r['won']))
    return out

def behavior_payload(code,version,cases,evaluation,fits):
    if evaluation['candidate_version']!=version:raise PermissionError('foreign candidate feedback')
    full=feedback_sources(cases,evaluation)
    payload=dict(parent_version=version,previous_code=code,own_execution_feedback=[],projection='CHRONOLOGICAL_ROUND_ROBIN_V1')
    for source in full:payload['own_execution_feedback'].append(dict(source,decisions=[],omitted_decisions=list(range(1,len(source['decisions'])+1))))
    if not fits(encode(payload)):raise ValueError('COMPLETE_CODE_AND_START_CONTEXT_INPUT_LIMIT')
    for i in range(max((len(x['decisions']) for x in full),default=0)):
        for j,source in enumerate(full):
            if i>=len(source['decisions']):continue
            trial=deepcopy(payload);row=trial['own_execution_feedback'][j]
            row['decisions'].append(source['decisions'][i]);row['omitted_decisions'].remove(i+1)
            if not fits(encode(trial)):return payload  # Fixed prefix; never seek an easier later case.
            payload=trial
    return payload

def choose(lineages):
    eligible=[x for x in lineages if x.get('evaluation') and x['evaluation']['metrics']['repairs']>0
        and x['evaluation']['metrics']['errors']==0]
    if not eligible:return dict(status='NO_ELIGIBLE_CANDIDATE',selected=None)
    def key(x):
        m=x['evaluation']['metrics']
        return (-m['repairs'],m['incompatible'],m['unsupported'],m['actions'],x['model_tokens'],x['id'])
    x=min(eligible,key=key)
    return dict(status='DEVELOPMENT_SELECTION_ONLY',selected=x['id'],version=x['version'],
        ranking=[x['id'] for x in sorted(eligible,key=key)],permission='SHADOW')

def evaluated_versions(lineages):
    """Keep eligible parents when a bounded revision fails or regresses."""
    versions=[]
    for x in lineages:
        seen=set()
        for key in ('initial_evaluation','evaluation'):
            ev=x.get(key)
            if not ev or ev['candidate_version'] in seen:continue
            seen.add(ev['candidate_version'])
            attempt=next(a for a in x['attempts'] if a['version']==ev['candidate_version'])
            versions.append(dict(id=attempt['id'],lineage_id=x['id'],arm=x['arm'],version=attempt['version'],
                evaluation=ev,model_tokens=x['model_tokens']))
    return versions
