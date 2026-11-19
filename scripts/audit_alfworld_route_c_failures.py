"""Host-only Route C historical analysis. No generation, policy or online wiring.

Signals describe public observations, not ground-truth failure causes. They are
evaluated on every archived episode; final outcome is joined only afterwards.
"""
import argparse
from collections import Counter
from pathlib import Path
import re

import audit_alfworld_route_a_onpolicy as Q
from alfworld_.generator import _parse_single_action

A=Q.A; ROOT=Q.ROOT
OUT=ROOT/'runs/alfworld_route_c_failure_audit_20261118_01'
REPORT=ROOT/'reports/alfworld_route_c_failure_audit_20261118'
SCHEMA='route-c-public-signals-v1'


def parsed_action(text,commands):
    """Describe original parser stages without modifying the returned action."""
    cleaned=lambda s:re.sub(r'^(\d+[.)]\s*|-\s*|>\s*)','',s.strip())
    act=next((cleaned(re.sub(r'^act\s*:\s*','',line.strip(),flags=re.I))
              for line in text.splitlines() if re.match(r'^act\s*:',line.strip(),re.I)),None)
    exact=next((c for c in commands if act is not None and c.lower()==act.lower()),None)
    if exact:stage='ACT_EXACT'
    elif act is not None and any(c.lower() in act.lower() for c in commands):stage='ACT_SUBSTRING'
    elif any(cleaned(l).lower()==c.lower() for l in text.splitlines() if not l.lower().strip().startswith('think') for c in commands):stage='OTHER_LINE_EXACT'
    elif any(c.lower() in text.lower() for c in commands):stage='WHOLE_OUTPUT_SUBSTRING'
    else:stage='FIRST_ADMISSIBLE_FALLBACK'
    actual=_parse_single_action(text,commands)
    return dict(stated=act,actual=actual,stage=stage,stated_is_legal=exact is not None,
                different=act is not None and act.lower()!=actual.lower())


def content(observation):
    """Remove only arrival/open narration, keep actual observed contents."""
    return re.sub(r'^You (?:arrive at|open) [^.]+\.\s*','',observation)


def search_location(action,observation):
    if not action.startswith(('go to ','open ','examine ')):return None
    if 'you see ' not in observation:return None
    m=re.search(r'(?:On|In) the ([a-z]+ \d+), you see |The ([a-z]+ \d+) is open\.',observation)
    return next((v for v in m.groups() if v),None) if m else None


def progress_receipt(observation):
    return bool(re.match(r'You (?:pick up|move|heat|cool|clean|activate) ',observation))


def signals(goal,initial,steps):
    """Public-prefix input ONLY: no outcome, task/game ID or future suffix.

    Step dictionaries are stripped of score, won, done and private metadata by
    public_steps(). Parsing diagnostics describe a just-received model reply;
    all other signals are post-action public observations.
    """
    findings=[];seen={};place={};held=None;processed=set();streak=[]
    required=next((verb for verb,pat in [('heat',r'\b(?:heat|hot|heated)\b'),('cool',r'\b(?:cool|cold|cooled)\b'),('clean',r'\b(?:clean|cleaned)\b')] if re.search(pat,goal.lower())),None)
    for i,s in enumerate(steps,1):
        action=s['action'];obs=s['observation'];commands=s['legal_before'];local=[]
        if s.get('model_output') is not None:
            parsed=parsed_action(s['model_output'],commands)
            if parsed['actual']!=action:raise PermissionError('parser replay differs')
            if parsed['different']:
                local.append(dict(signal='INTENT_EXECUTION_DIVERGENCE',evidence_steps=[i],detail=parsed,
                    availability='MODEL_RESPONSE_BEFORE_ACTION; absent from existing policy context'))
        loc=search_location(action,obs);old=seen.get(loc) if loc else None
        duplicate=bool(old and old['content']==content(obs))
        if duplicate:
            local.append(dict(signal='KNOWN_CONTENT_REVISIT',evidence_steps=[old['step'],i],
                detail=dict(location=loc,prior_content_sha256=A.digest(old['content']),prior_outside_native_last10=i-old['step']>10),
                availability='PUBLIC_HISTORY_AFTER_ACTION'))
        if loc:seen[loc]=dict(step=i,content=content(obs))
        streak.append(dict(step=i,duplicate=duplicate,progress=progress_receipt(obs)))
        window=streak[-10:]
        if len(window)==10 and sum(x['duplicate'] for x in window)>=3 and not any(x['progress'] for x in window):
            local.append(dict(signal='REVISIT_STAGNATION_10',evidence_steps=[x['step'] for x in window if x['duplicate']],
                detail=dict(repeated_searches=sum(x['duplicate'] for x in window),progress_receipts=0),
                availability='PUBLIC_HISTORY_AFTER_ACTION; not proof of failure'))
        take=re.match(r'You pick up the (.+?) from the (.+?)\.',obs)
        move=re.match(r'You move the (.+?) to the (.+?)\.',obs)
        if take:
            obj,src=take.groups()
            if obj in place and place[obj]['destination']==src:
                local.append(dict(signal='RETAKE_PREVIOUSLY_PLACED_OBJECT',evidence_steps=[place[obj]['step'],i],
                    detail=dict(object=obj,destination=src),availability='PUBLIC_HISTORY_AFTER_ACTION; may be legitimate reprocessing'))
            held=obj;place.pop(obj,None)
        if move:
            obj,dst=move.groups()
            if required and (obj,required) not in processed and any(c.startswith(required+' '+obj+' with ') for c in commands):
                local.append(dict(signal='PROCESS_AVAILABLE_BEFORE_PUTDOWN',evidence_steps=[i],
                    detail=dict(object=obj,required_action=required,public_available=[c for c in commands if c.startswith(required+' '+obj+' with ')]),
                    availability='PUBLIC_GOAL_AND_CURRENT_LEGAL_ACTIONS; not an automatic error label'))
            held=None;place[obj]=dict(destination=dst,step=i)
        p=re.match(r'You (heat|cool|clean) the (.+?) (?:using|with) ',obs)
        if p:processed.add((p[2],p[1]))
        if held and not take and re.search(r'you see .*\b[a-z]+ \d+',obs,re.I):
            # Descriptive affordance gap; no assertion that held/visible objects
            # match the goal. Goal/type interpretation must be reviewed separately.
            visible=re.findall(r'\b([a-z]+ \d+)\b',obs.split('you see ',1)[-1])
            if visible and not any(c.startswith('take ') for c in s['legal_after']) and any(c.startswith('move '+held+' to ') for c in s['legal_after']):
                local.append(dict(signal='HELD_OBJECT_WITH_NO_PICKUP_AFFORDANCE',evidence_steps=[i],
                    detail=dict(held=held,visible=visible),availability='PUBLIC_RECEIPTS_AND_CURRENT_LEGAL_ACTIONS; not a failure by itself'))
        for x in local:
            x.update(step=i,remaining_steps=50-i,signal_version=SCHEMA)
            findings.append(x)
    return findings


def public_steps(ep):
    return [dict(action=s['feedback']['action'],observation=s['feedback']['observation'],
                 legal_before=s['legal_actions'],legal_after=s['feedback']['commands'],
                 model_output=s['requested']['output'] if s['requested'] else None) for s in ep['steps']]


def successes_for(ep,episodes):
    """Fixed retrospective matching, never selected by signal absence/presence."""
    candidates=[e for e in episodes if e['won'] and e['task_type']==ep['task_type']]
    candidates.sort(key=lambda x:(bool(x['direct_prefix'])!=bool(ep['direct_prefix']),
        abs(len(x['steps'])-len(ep['steps'])),abs(x['sequence']-ep['sequence']),x['task_id']))
    return [dict(sequence=x['sequence'],task_id=x['task_id'],steps=len(x['steps']),route=x['route']) for x in candidates[:2]]


def inspect_episode(ep):
    ps=public_steps(ep);found=signals(ep['goal'],ep['initial']['observation'],ps)
    for f in found:
        s=ep['steps'][f['step']-1]
        f.update(receipt_sha256=s['receipt_sha256'],actor=s['decision']['source'],
                 next_model_callback=f['step']<len(ep['steps']) and ep['steps'][f['step']]['decision']['source']=='MODEL')
    parsers=[]
    for s in ep['steps']:
        if s['requested']:
            p=parsed_action(s['requested']['output'],s['legal_actions'])
            p.update(step=s['step'],request_id=s['requested']['request_id'],response_sha256=A.digest(s['requested']['provider_response']))
            parsers.append(p)
    repeats=[f for f in found if f['signal']=='KNOWN_CONTENT_REVISIT']
    last=ep['steps'][-1]['state_after']
    return dict(sequence=ep['sequence'],task_id=ep['task_id'],task_type=ep['task_type'],goal=ep['goal'],
        scene=ep['source_task']['scene'],group=ep['source_task']['group'],game_sha256=ep['source_task']['game_sha256'],
        won=ep['won'],status=ep['status'],steps=len(ps),direct_prefix=ep['direct_prefix'],route=ep['route'],
        holdout=ep['skills']['holdout'],selected=ep['skills']['selected'],
        model_calls=len(parsers),signals=found,parse_records=parsers,
        first_signal={name:next(f['step'] for f in found if f['signal']==name) for name in sorted({f['signal'] for f in found})},
        repeated_contents=len(repeats),repeat_prior_outside_last10=sum(f['detail']['prior_outside_native_last10'] for f in repeats),
        unvisited_locations=[c[6:] for c in ep['initial']['commands'] if c.startswith('go to ') and c[6:] not in last['visited']],
        final_public_partial_state=last,subgoal_truth='REQUIRES_HOST_INTERPRETATION; no private goal state used',
        environment_done=ep['steps'][-1]['feedback']['done'],old_failure_type=ep['original_failure_type'])


def verify():
    Q.verify();f=A.read(OUT/'Input_Freeze.json')
    if f['input_sha256']!=A.sha(OUT/'episodes.private.json'):raise PermissionError('Route C input changed')
    return f


def analyze():
    f=verify();episodes=A.read(OUT/'episodes.private.json');rows=[inspect_episode(e) for e in episodes]
    failed=[r for r in rows if not r['won']];names=sorted({x['signal'] for r in rows for x in r['signals']});aggregate={}
    for name in names:
        a={}
        for outcome,label in ((False,'native_failed'),(True,'native_won')):
            group=[r for r in rows if r['won']==outcome];hit=[r for r in group if name in r['first_signal']]
            a[label]=dict(total_games=len(group),signal_games=len(hit),events=sum(x['signal']==name for r in group for x in r['signals']),
                game_sequences=[r['sequence'] for r in hit],scenes=sorted({r['scene'] for r in hit}))
        aggregate[name]=a
    controls={str(e['sequence']):successes_for(e,episodes) for e in episodes if not e['won']}
    result=dict(scope='HISTORICAL_DEVELOPMENT_HOST_ANALYSIS_NOT_LEARNED_SKILLS',input_sha256=f['input_sha256'],
        failure_games=len(failed),success_games=len(rows)-len(failed),signal_definitions=SCHEMA,
        control_selection='same task type; same direct-prefix presence; nearest episode length; nearest sequence; task_id; top 2; all 113 successes also counted',
        signal_counts=aggregate,controls=controls,episodes=rows,
        parser_stages=dict(Counter(p['stage'] for r in rows for p in r['parse_records'])),
        paid_requests=0,candidate_changes=0,online_games_run=0)
    A.commit(OUT/'Analysis.private.json',result)
    REPORT.mkdir(exist_ok=True,parents=True)
    public={k:v for k,v in result.items() if k!='episodes'}
    public['episodes']=[{k:v for k,v in r.items() if k not in ('final_public_partial_state','parse_records')} for r in rows]
    A.commit(REPORT/'public_audit_summary.json',public)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['analyze','verify']);args=parser.parse_args()
    r=globals()[args.command]();print({k:v for k,v in r.items() if k in ('failure_games','success_games','parser_stages')})
