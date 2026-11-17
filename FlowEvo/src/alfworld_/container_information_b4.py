"""B4 offline generation contract. No recovery algorithm or paid transport."""
from copy import deepcopy
from .container_information import blocks, behavior_payload, feedback_sources
from .python_recovery_feedback import _INSTRUCTIONS
from .route_b_compact_projection import INSTRUCTION
from failure_evo.contracts import fingerprint
VERSION='route-b4-double-data-v1'
CELLS=('S11','F11','FR11','S22','F22','FR22')
COMMON='''OFFLINE SKILL AUTHORING, NOT A LIVE GAME TURN.
Write a reusable, parameterized Python recovery function for future use. Historical
cases below are learning evidence, not the current episode. No live observation or
live legal-command list is supplied at generation time; this is intentional.
Implement environment_operator(context). At FUTURE RUNTIME the host supplies the
actual goal, observation, admissible_commands, history and state for that branch.
Your function must establish applicability THEN and either choose a supported legal
action or decline. You need not prove any specific live action legal NOW to write
such a function. ABSTAIN is allowed if historical evidence cannot support any
bounded general strategy; absence of a live episode alone is not that evidence.

The program is for bounded local container-delivery recovery after an unsuccessful
action, not solving a new episode from step one, not a fixed next command, not a
replacement for the native agent. Observation/exploration needs a relevant purpose,
a finite bound and an exit condition. Do not choose an arbitrary legal action.
Runtime context.goal is the current task, observation is public, admissible_commands
are exact current legal strings, history contains only events already observed,
and state is your JSON memory. Empty state means no program memory, NOT empty
inventory or uncompleted prior processing. Preserve goal processing requirements,
instance constraints and progress. Bind current instances from public evidence,
never from a historical game ID or fixed instance number.
Check present and later action preconditions separately. Recheck fresh feedback
and legal commands after every executed action. Missing evidence at runtime still
requires refusal; permission to author code is not permission to act blindly.

One ordinary positional argument. Return exactly:
{"status":"applied","action":"an exact current legal command","state":{},"reason":"..."}
or {"status":"declined","state":{},"reason":"..."}.
One action per call; remember phase only in state. Maximum state 4 KiB, result 8 KiB.
Do not assume a historical success suffix has occurred in the runtime branch.

Environment command syntax only (ROLE placeholders are NOT actions to output):
look; inventory; go to RECEPTACLE; examine ENTITY; take OBJECT from RECEPTACLE;
move OBJECT to RECEPTACLE; open RECEPTACLE; close RECEPTACLE;
clean OBJECT with TOOL; heat OBJECT with TOOL; cool OBJECT with TOOL; use TOOL.
The host executes only an actual current legal command and returns its real receipt.
Historical C/F/R are labelled fragments. Omitted history is not a continuous trace;
do not invent omitted events. R's initial observation/history can be absent; its
recorded starting legal commands are real. Step IDs identify original receipts.
''' + _INSTRUCTIONS[_INSTRUCTIONS.index('Static safety permits'):]+'\n'+INSTRUCTION
PROMPTS=dict(initial='Author a NEW reusable Python skill offline, or ABSTAIN.\n'+COMMON,
 engineering='Repair your own delivery/static defects offline; no behavior answers are supplied. Return complete source or ABSTAIN.\n'+COMMON,
 behavior='Revise your own reusable function offline using only its supplied public TRAIN execution. Self-reported reasons are not environment facts. Return full source or ABSTAIN.\n'+COMMON)

def packets(cases):
    pieces=[blocks(c,c['model_ref']) for c in cases]
    return {a:dict(version=VERSION,examples=[{k:deepcopy(b[k]) for k in
        (('C','R') if a=='S' else ('C','F') if a=='F' else ('C','F','R'))} for b in pieces]) for a in ('S','F','FR')}

def identity(case):return case['origin']['row']['game_sha256']
def diversity(pool,n,seed,*,used=()):
    """Frozen metadata diversity, no candidate scores. One source per game/group."""
    selected=[];taken=set(used)
    for _ in range(n):
        eligible=[c for c in pool if identity(c) not in taken and all(c['origin']['row']['group']!=x['origin']['row']['group'] for x in selected)]
        if not eligible:raise ValueError('INSUFFICIENT_DISTINCT_GAMES')
        def key(c):
            row=c['origin']['row']
            fields=('task_type','target','scene')
            def val(x,k):return x['origin']['row']['group'].rsplit('-',2)[-2] if k=='target' else x['origin']['row'][k]
            return tuple(sum(val(x,k)==val(c,k) for x in selected) for k in fields)+(fingerprint([seed,c['id']]),)
        c=min(eligible,key=key);selected.append(c);taken.add(identity(c))
    return selected

def early_stop(first_wave):
    return len(first_wave)==12 and all(x['status']=='ABSTAIN' for x in first_wave)

def behavior_parent(rows,case_count):
    usable=[x for x in rows if x.get('train_evaluation') and x['train_evaluation']['metrics']['worker_ok']>0
        and not(x['train_evaluation']['metrics']['repairs']==case_count and x['train_evaluation']['metrics']['errors']==0)]
    if not usable:return None
    return min(usable,key=lambda x:(-x['train_evaluation']['metrics']['repairs'],x['train_evaluation']['metrics']['errors'],
        x['train_evaluation']['metrics']['incompatible'],x['train_evaluation']['metrics']['unsupported'],x['id']))

def select_validation(rows):
    usable=[x for x in rows if x.get('validation_evaluation') and x['validation_evaluation']['metrics']['repairs']>0
        and x['validation_evaluation']['metrics']['errors']==0]
    if not usable:return dict(status='NO_ELIGIBLE_CANDIDATE',selected=None,permission='SHADOW')
    def key(x):
        m=x['validation_evaluation']['metrics']
        return (-m['repairs'],m['incompatible'],m['unsupported'],m['actions'],m['worker_calls'],x['lineage_tokens'],x['id'])
    chosen=min(usable,key=key)
    return dict(status='DEVELOPMENT_SELECTION_ONLY',selected=chosen['id'],version=chosen['version'],permission='SHADOW',ranking=[x['id'] for x in sorted(usable,key=key)])
