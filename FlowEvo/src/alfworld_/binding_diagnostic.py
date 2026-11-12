"""Public-only binding/validity diagnostics; no policy execution or repair generation."""
from collections import Counter
import re

from failure_evo.contracts import canonical, fingerprint

VERSION = 'alfworld-binding-diagnostic-v8'
MATCH, CONFLICT, UNKNOWN = 'MATCH','CONFLICT','UNKNOWN'
A_ENTITIES = ('object_type','object_instance','target_type','target_instance')
A_MATCH = ('object_type_match','target_type_match','object_match','target_match','phase_match')
B_FIELDS = ('failure_relevant','failure_unresolved','binding_consistent','recovery_needed')
OUTPUTS = {
    'A':{**{k:'nonblank string <=96 chars or null' for k in A_ENTITIES},
         **{k:[MATCH,CONFLICT,UNKNOWN] for k in A_MATCH},
         'decision':['CONSISTENT','INCONSISTENT','INSUFFICIENT_EVIDENCE'],
         'confidence_basis':'nonblank string <=400 chars'},
    'B':{**{k:['YES','NO',UNKNOWN] for k in B_FIELDS},
         'evidence_steps':'unique list of up to 8 provided step IDs, or current',
         'uncertainty':'nonblank string <=400 chars'},
}
INPUT_FIELDS = {'id','goal','failed_action','failure_step_id','observation',
                'admissible_commands','history','held_object'}
COMMON = """Return only JSON {"rows":[...]} with exactly one row per input id.
Use only the public snapshot, the time-ordered action/feedback prefix and the listed
commands. No policy code or action recommendation. held_object is an optional public
fact, null when the host supplies no separate fact. History may still establish possession.
"""
PROMPTS = {
    'A': COMMON+"""Diagnose target binding. Entity fields describe the failed command's referents,
not a guess for a missing command. Type fields omit instance numbers. Distinguish
category compatibility from the failed instance being justified by the current goal,
held-object evidence and visible target choices. A visible alternative with no disambiguation
requires UNKNOWN. Judge the delivery phase separately. The decision is INCONSISTENT if
object_match, target_match or phase_match conflicts; CONSISTENT if all three match;
otherwise INSUFFICIENT_EVIDENCE. Do not test whether an obstacle is still unresolved here.
Exact row schema (plus id): """+canonical(OUTPUTS['A']),
    'B': COMMON+"""Independently assess failure relevance to the current goal, whether the
obstacle/subgoal is still unresolved, current binding consistency, and whether recovery
is needed now. A later observation does not itself invalidate a failure. No failure,
an externally resolved obstacle, a completed subgoal or a conflicting target can justify NO;
missing evidence can justify UNKNOWN. Evidence IDs must refer only to the provided prefix
or current snapshot ('current'). You receive no A prediction or answer.
Exact row schema (plus id): """+canonical(OUTPUTS['B']),
}


def event(action, observation):
    return dict(action=action,observation=observation)


def public_case(key, goal, observation, commands, history, failed_index, held=None):
    if failed_index is not None and not 0 <= failed_index < len(history):
        raise ValueError('failure is outside public history')
    rows = [dict(step_id=f'step_{i:03d}',action=x['action'],observation=x['observation'])
            for i,x in enumerate(history,1)]
    anchor = rows[failed_index] if failed_index is not None else None
    return dict(id=key,goal=goal,observation=observation,admissible_commands=list(commands),
                history=rows,failed_action=anchor['action'] if anchor else None,
                failure_step_id=anchor['step_id'] if anchor else None,held_object=held)


def a_decision(statuses):
    return ('INCONSISTENT' if CONFLICT in statuses else
            'CONSISTENT' if all(x==MATCH for x in statuses) else 'INSUFFICIENT_EVIDENCE')


def annotation(public, a, b, *, role, category, basis, source=None):
    # Extraction only from the selected public action. Match and temporal labels
    # are independently reviewed annotations, not output from a repair parser.
    entities = [None]*4
    if public['failed_action']:
        m = re.fullmatch(r'move (.+?) to (.+)',public['failed_action'])
        if not m:
            raise ValueError('annotated failure is not a delivery command')
        obj,target = m.groups()
        entities = [re.sub(r' \d+$','',obj),obj,re.sub(r' \d+$','',target),target]
    return dict(public=public,role=role,category=category,source=source,basis=basis,
        A=dict(zip((*A_ENTITIES,*A_MATCH,'decision'),[*entities,*a,a_decision(a[2:])])),
        B=dict(zip(B_FIELDS,b)))


def parse_rows(value, arm, cases):
    if not isinstance(value,dict) or set(value)!={'rows'} or not isinstance(value['rows'],list):
        raise ValueError('diagnostic response must contain only rows')
    lookup = {p['id']:p for p in cases}
    seen = Counter(r.get('id') for r in value['rows'] if isinstance(r,dict) and isinstance(r.get('id'),str))
    accepted, rejected = {}, []
    for index,r in enumerate(value['rows']):
        key = r.get('id') if isinstance(r,dict) else None
        if not isinstance(key,str) or key not in lookup or seen[key]!=1 or set(r)!=set(OUTPUTS[arm])|{'id'}:
            rejected.append(dict(index=index,reason='row identity or fields invalid'))
            continue
        valid = all(r[k] in choices for k,choices in OUTPUTS[arm].items() if isinstance(choices,list))
        text = 'confidence_basis' if arm=='A' else 'uncertainty'
        valid = valid and isinstance(r[text],str) and 0<len(r[text].strip())<=400
        if arm=='A':
            valid = valid and all(r[k] is None or (isinstance(r[k],str) and 0<len(r[k].strip())<=96)
                                  for k in A_ENTITIES)
            valid = valid and r['decision']==a_decision([r[k] for k in A_MATCH[2:]])
        else:
            steps = r['evidence_steps']
            ids = {x['step_id'] for x in lookup[key]['history']}|{'current'}
            valid = valid and isinstance(steps,list) and len(steps)<=8 and all(
                isinstance(s,str) and s in ids for s in steps) and len(steps)==len(set(steps))
        if valid:
            accepted[key]=r
        else:
            rejected.append(dict(index=index,id=key,reason='row output contract invalid'))
    return dict(rows=accepted,rejected=rejected,missing=[k for k in lookup if k not in accepted])


def score(cases, predictions):
    def ratio(n,d):
        return dict(numerator=n,denominator=d,rate=n/d if d else None)
    result = {}
    roles = sorted({c['role'] for c in cases})
    groups = [('all',cases)] + [(role,[c for c in cases if c['role']==role]) for role in roles]
    groups += [('category/'+cat,[c for c in cases if c['role']=='fresh_synthetic' and c['category']==cat])
               for cat in sorted({c['category'] for c in cases if c['role']=='fresh_synthetic'})]
    for role,subset in groups:
        group = {}
        for arm,fields in [('A',(*A_ENTITIES,*A_MATCH,'decision')),('B',B_FIELDS)]:
            rows = [(c[arm],predictions[arm].get(c['public']['id'])) for c in subset]
            group[arm] = dict(delivery=ratio(sum(p is not None for _,p in rows),len(rows)), fields={})
            for key in fields:
                unknown = {None,UNKNOWN,'INSUFFICIENT_EVIDENCE'}
                known = [(r,p) for r,p in rows if r[key] not in unknown]
                uncertain = [(r,p) for r,p in rows if r[key] in unknown]
                group[arm]['fields'][key] = dict(
                    verifiable=ratio(len(known),len(rows)),
                    accuracy_known=ratio(sum(p is not None and p[key]==r[key] for r,p in known),len(known)),
                    uncertainty_correct=ratio(sum(p is not None and p[key]==r[key] for r,p in uncertain),len(uncertain)),
                    predicted_unknown=ratio(sum(p is not None and p[key] in unknown for _,p in rows),
                                            sum(p is not None for _,p in rows)))
        def errors(selected):
            rows = [(c['B']['recovery_needed'],predictions['B'].get(c['public']['id'])) for c in selected]
            pos = [p for r,p in rows if r=='YES']; neg = [p for r,p in rows if r=='NO']
            return dict(false_reject=ratio(sum(p is not None and p['recovery_needed']!='YES' for p in pos),len(pos)),
                        false_trigger=ratio(sum(p is not None and p['recovery_needed']=='YES' for p in neg),len(neg)),
                        uncertain_trigger=sum(r==UNKNOWN and p is not None and p['recovery_needed']=='YES' for r,p in rows),
                        missing=sum(p is None for _,p in rows))
        correct_a = [c for c in subset if all(c['A'][k]!=UNKNOWN for k in A_MATCH[2:])
                     and c['public']['id'] in predictions['A']
                     and all(predictions['A'][c['public']['id']][k]==c['A'][k] for k in A_MATCH[2:])]
        group['B']['errors'] = errors(subset)
        group['B']['conditional_on_correct_determinate_A'] = dict(cases=len(correct_a),**errors(correct_a))
        result[role] = group
    return result


def same_information_view(public, host_parse):
    """Future comparison interface. A parser gets only an exact public snapshot."""
    if set(public)!=INPUT_FIELDS:
        raise PermissionError('binding input boundary')
    snapshot = canonical(public)
    # Give the parser a separate value so it cannot mutate either arm's public record.
    import json
    derived = host_parse(json.loads(snapshot))
    if not isinstance(derived,dict):
        raise ValueError('host parser must return a mapping')
    return dict(public=public,host_derived=derived,public_sha256=fingerprint(public))
