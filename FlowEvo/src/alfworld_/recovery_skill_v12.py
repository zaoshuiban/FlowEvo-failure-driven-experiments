"""Versioned recovery checks for public observations and complete action prefixes."""

from itertools import product
import re

from failure_evo.contracts import canonical
from . import generic_recovery_skill as old
from . import precondition_diagnostic as base

VERSION = 'alfworld-recovery-reliability-v12'
EXTRA_ROLES = {'observed_support', 'command_argument'}
EXTRA_ATOM = 'event_recorded'
VISIBLE = re.compile(r'\bOn the ([a-z]+(?: [a-z]+)* [1-9][0-9]*), you see ([^.]+)\.', re.I)
ITEM = re.compile(r'(?:^|, | and )(?:a |an |the )?([a-z]+(?: [a-z]+)* [1-9][0-9]*)(?=,| and |$)', re.I)
PROMPT = old.GENERATION_PROMPT + """
Additional v12 capabilities (alongside the frozen interface above):
- {"select":"observed_support","entity_from":"fixed_alias"} binds an explicit supporting
  surface from the current public observation, carrying across a recorded no-op only.
- {"select":"command_argument","verb":"take","match_from":"earlier_alias",
   "match_position":0,"select_position":1} binds the unique other argument from
  a matching public admissible binary command. Optionally use "filter_from" to constrain
  the selected argument by a fixed role category or explicit instance. The matched
  dependency must use a fixed selector or admissible_instance.
- event_recorded uses the same args as event_is. It checks if a matching receipt
  exists in the complete supplied prefix/window. FALSE means no qualifying receipt
  was recorded in that observed window. UNKNOWN means missing binding, anchor or
  an undecidable matching receipt. event_is uses only the latest matching receipt
  and stays UNKNOWN if absent. Neither implies hidden world state.
- Example condition: {"id":"used","op":"event_recorded","args":{"verb":"use",
  "entities":["tool"],"window":"after_failure","outcome":"effect"},"sources":["copy a step ID"]}.
For stopping on a recorded effect, bind the actual action entity. At the first
step the post-failure prefix can be empty. Stop still refuses when TRUE or UNKNOWN.
Use goal_target for the tool in an "examine X with Y" goal; goal_object denotes X.
Use failed_subject for the only argument of a unary failed action.
goal_requires operations are place, heat, cool, clean, examine. 'move' is an action verb,
not a goal operation. goal_requires never checks completion.
args must be named objects, sources must be arrays with 1–6 exact step IDs, and
reason, scope and refusal are 1–400 characters. Use not only in expressions.
Check that some state can satisfy entry and allow the first rule without stopping,
and that a continuation rule is not precluded by its own stop condition.
"""


def parse_skill(value, anchors, steps):
    """Validate extensions, then reuse the v11 envelope and shared constraints."""
    if not isinstance(value, dict) or value.get('decision') != 'PROPOSE':
        return old.parse_skill(value, anchors, steps)
    roles, atoms = value.get('roles'), value.get('conditions')
    if not isinstance(roles, dict) or not isinstance(atoms, list):
        return old.parse_skill(value, anchors, steps)
    projected_roles = {}
    for alias, selector in roles.items():
        kind = selector.get('select') if isinstance(selector, dict) else None
        if not isinstance(kind,str):
            return _rejected('INVALID_DELIVERY','ROLE_SHAPE')
        if kind == 'observed_support':
            operand = selector.get('entity_from')
            if (set(selector) != {'select', 'entity_from'} or not isinstance(operand, str)
                    or operand not in roles or not isinstance(roles[operand], dict)
                    or roles[operand].get('select') not in old.FIXED):
                return _rejected('INVALID_DELIVERY', 'SUPPORT_ROLE_SOURCE')
        elif kind == 'command_argument':
            operand = selector.get('match_from')
            verb = selector.get('verb')
            positions = (selector.get('match_position'), selector.get('select_position'))
            filter_from = selector.get('filter_from')
            expected = {'select','verb','match_from','match_position','select_position'}
            if 'filter_from' in selector:
                expected.add('filter_from')
                if (not isinstance(filter_from,str) or not isinstance(roles.get(filter_from),dict)
                        or roles[filter_from].get('select') not in old.FIXED):
                    return _rejected('INVALID_DELIVERY','COMMAND_ARGUMENT_FILTER')
            if (set(selector) != expected
                    or not isinstance(operand,str) or not isinstance(roles.get(operand),dict)
                    or roles[operand].get('select') not in (*old.FIXED,'admissible_instance')
                    or not isinstance(verb,str) or old.VERBS.get(verb) != 2
                    or any(type(index) is not int for index in positions) or set(positions) != {0,1}):
                return _rejected('INVALID_DELIVERY', 'COMMAND_ARGUMENT_BINDING')
        projected_roles[alias] = {'select':'goal_object'} if kind in EXTRA_ROLES else selector
    projected_atoms = [{**atom,'op':'event_is'} if isinstance(atom,dict)
                       and atom.get('op')==EXTRA_ATOM else atom for atom in atoms]
    checked = old.parse_skill(dict(value,roles=projected_roles,conditions=projected_atoms),anchors,steps)
    if checked['candidate'] is None:
        return checked
    analysis = check_logic(value)
    if analysis['hard_conflicts']:
        return dict(status='LOGIC_REJECTED',reason='NO_FEASIBLE_RULE',candidate=None,logic=analysis)
    return dict(status='STRUCTURED_DELIVERED',candidate=value,logic=analysis)


def _rejected(status, reason):
    return dict(status=status,reason=reason,candidate=None)


def expression(node, truth):
    operator, operand = next(iter(node.items()))
    if operator == 'condition':
        return truth[operand]
    return base.three_value(operator, [expression(operand,truth)] if operator=='not'
                            else [expression(child,truth) for child in operand])


def _references(node):
    if node is None:
        return set()
    operator, operand = next(iter(node.items()))
    if operator == 'condition':
        return {operand}
    return _references(operand) if operator=='not' else set().union(*map(_references,operand))


def check_logic(skill):
    """Necessary feasibility under abstract Boolean assignments, not a proof over game states."""
    stop = skill['stop']
    entry = skill['entry']
    signatures = {row['id']:canonical([row['op'],row['args']]) for row in skill['conditions']}

    def feasible(nodes):
        ids = set().union(*(_references(node) for node in nodes))
        classes = sorted({signatures[key] for key in ids})
        if len(classes) > 12:
            return None
        for values in product((base.FALSE,base.TRUE),repeat=len(classes)):
            assignment = dict(zip(classes,values))
            truth = {key:assignment[signatures[key]] for key in ids}
            if all(expression(node,truth)==base.TRUE for node in nodes[:-1]) and (
                    nodes[-1] is None or expression(nodes[-1],truth)==base.FALSE):
                return True
        return False

    initial = [feasible((entry,rule['when'],stop)) for rule in skill['rules']]
    continuation = [feasible((rule['when'],stop)) for rule in skill['rules']]
    hard = []
    if all(value is False for value in initial):
        hard.append('NO_ENTRY_RULE_WITH_STOP_FALSE')
    return dict(initial_rule_feasible=initial,continuation_rule_feasible=continuation,
                unreachable_continuation_rules=[i for i,ok in enumerate(continuation) if ok is False],
                hard_conflicts=hard)


def _support(common, subject):
    if not subject:
        return None,[]
    observations = [(common.case['current_evidence_id'],common.case['observation'])]
    if observations[0][1]==base.NOOP:
        for ref,_,text in reversed(common.steps):
            observations.append((ref,text))
            if text!=base.NOOP:
                break
    for index,(_,text) in enumerate(observations):
        matching = set()
        for surface, listing in VISIBLE.findall(text):
            items = [base.entity(name) for name in ITEM.findall(listing)]
            if any(item and item.category==subject.category and
                   (not subject.number or item==subject) for item in items):
                matching.add(base.entity(surface))
        if matching:
            return (next(iter(matching)) if len(matching)==1 else None,
                    list(dict.fromkeys(ref for ref,_ in observations[:index+1])))
    return None,[]


def bindings(skill, public, common, fixed, steps, commands):
    roles = {}
    ordered = sorted(skill['roles'].items(),key=lambda row:row[1]['select']=='command_argument')
    for alias, rule in ordered:
        selector = rule['select']
        if selector in old.FIXED:
            roles[alias] = fixed[selector]
        elif selector == 'observed_support':
            value,refs = fixed[skill['roles'][rule['entity_from']]['select']]
            item,observations = _support(common,value)
            roles[alias] = item, refs+observations
        elif selector == 'command_argument':
            value,refs = roles[rule['match_from']]
            matches = {items[rule['select_position']] for verb,items in commands
                       if verb==rule['verb'] and value and value.number and items[rule['match_position']]==value}
            if 'filter_from' in rule:
                filter_entity,filter_refs=fixed[skill['roles'][rule['filter_from']]['select']]
                matches = {item for item in matches if filter_entity and item.category==filter_entity.category
                           and (not filter_entity.number or item==filter_entity)}
                refs=refs+filter_refs
            roles[alias] = (next(iter(matches)) if len(matches)==1 else None,refs+[common.commands_id])
        elif selector == 'admissible_instance':
            value,refs = fixed[skill['roles'][rule['category_from']]['select']]
            matches = {items[0] for verb,items in commands if verb==rule['verb'] and value and items[0].number
                       and items[0].category==value.category and (not value.number or items[0]==value)}
            roles[alias] = (next(iter(matches)) if len(matches)==1 else None,refs+[common.commands_id])
        else:
            visited = [(ref,parsed[1][0]) for ref,parsed,text in steps
                       if parsed and parsed[0]=='go_to' and old.receipt_truth(parsed,text)==base.TRUE]
            available = {items[0] for verb,items in commands if verb=='go_to' and items[0].number}
            choices = available-{item for _,item in visited}
            roles[alias] = (min(choices,key=lambda item:item.name) if choices else None,
                            [common.commands_id,*[ref for ref,_ in visited]])
    return roles


def _events(op, args, values, steps, anchor, raw_actions):
    window = args['window']
    if anchor is None and window!='entire_prefix':
        return base.UNKNOWN,[]
    selected = steps if window=='entire_prefix' else {
        'before_failure':steps[:anchor], 'at_failure':steps[anchor:anchor+1],
        'after_failure':steps[anchor+1:],
    }[window]
    found=[]
    verb_text = 'go to' if args['verb']=='go_to' else args['verb']
    for ref,parsed,text in reversed(selected):
        if parsed and parsed[0]==args['verb']:
            entities = parsed[1][:len(values)]
            if entities==values:
                truth = old.receipt_truth(parsed,text)
                found.append((ref,base.three_value('not',[truth]) if args['outcome']=='noop' else truth))
            elif all(a.category==b.category and (a==b or not a.number) for a,b in zip(entities,values,strict=True)):
                found.append((ref,base.UNKNOWN))
        elif parsed is None and raw_actions[ref].startswith(verb_text+' '):
            found.append((ref,base.UNKNOWN))
    if op=='event_is':
        if found:
            return found[0][1],[found[0][0]]
        if window=='at_failure' and selected and selected[0][1]:
            return base.FALSE,[selected[0][0]]
        return base.UNKNOWN,[]
    # Non-matching command receipts establish absence from the observed window,
    # not absence in the world. Unparseable commands with the exact requested verb
    # cannot silently be treated as evidence of absence.
    if any(value==base.TRUE for _,value in found):
        return base.TRUE,[next(ref for ref,value in found if value==base.TRUE)]
    if any(value==base.UNKNOWN for _,value in found):
        return base.UNKNOWN,[ref for ref,_ in found]
    return base.FALSE,[ref for ref,_,_ in selected]


def inspect(skill,public,*,starting):
    common,fixed,steps,operations = old.public_facts(public)
    commands = {parsed for command in public['admissible_commands'] if (parsed:=old.parse_command(command))}
    roles = bindings(skill,public,common,fixed,steps,commands)
    raw_actions = {row['evidence_id']:row['action'] for row in public['history']}
    results = {}
    for row in skill['conditions']:
        op,args = row['op'],row['args']
        truth,refs=base.UNKNOWN,[]
        if op in ('category_equal','instance_equal'):
            left,left_refs=roles[args['left']]
            right,right_refs=roles[args['right']]
            refs=left_refs+right_refs
            if left and right and (op=='category_equal' or left.number and right.number):
                equal=left.category==right.category if op=='category_equal' else left==right
                truth=base.TRUE if equal else base.FALSE
        elif op=='bound':
            item,refs=roles[args['entity']]
            if item and item.number:
                truth=base.TRUE
        elif op=='state_is':
            item,bound_refs=roles[args['entity']]
            observed,refs=common.state(item)
            refs+=bound_refs
            if len(observed)==1:
                truth=base.TRUE if args['state'] in observed else base.FALSE
        elif op=='goal_requires' and operations is not None:
            truth,refs=(base.TRUE if args['operation'] in operations else base.FALSE),[common.goal_id]
        elif op=='selected_failure':
            truth=base.TRUE if common.anchor is not None else base.FALSE
            refs=[steps[common.anchor][0]] if common.anchor is not None else [f"{public['id']}:failure_step_id"]
        elif op in ('action_available','event_is',EXTRA_ATOM):
            values=tuple(roles[alias][0] for alias in args['entities'])
            refs=[ref for alias in args['entities'] for ref in roles[alias][1]]
            if all(item and item.number for item in values):
                if op=='action_available':
                    truth=base.TRUE if (args['verb'],values) in commands else base.FALSE
                    refs.append(common.commands_id)
                else:
                    truth,evidence=_events(op,args,values,steps,common.anchor,raw_actions)
                    refs+=evidence
                    if op==EXTRA_ATOM and truth==base.FALSE:
                        refs.append(f"{public['id']}:observed_prefix")
        results[row['id']]=dict(truth=truth,evidence_ids=list(dict.fromkeys(refs)))

    truth={key:value['truth'] for key,value in results.items()}
    entry=expression(skill['entry'],truth)
    stop=expression(skill['stop'],truth) if skill['stop'] is not None else base.FALSE
    guards=[expression(rule['when'],truth) for rule in skill['rules']]
    result=dict(entry=entry,stop=stop,rules=guards,conditions=results,selection=None,
                bindings={alias:dict(entity=item.name if item else None,evidence_ids=refs)
                          for alias,(item,refs) in roles.items()})
    if starting and entry!=base.TRUE:
        return dict(result,block='ENTRY_'+entry)
    if stop!=base.FALSE:
        return dict(result,block='STOP_'+stop)
    for index,(rule,guard) in enumerate(zip(skill['rules'],guards)):
        action=rule['action']
        values=tuple(roles[alias][0] for alias in action['entities'])
        if guard==base.TRUE and all(item and item.number for item in values) and (action['verb'],values) in commands:
            return dict(result,selection=dict(index=index,values=[item.name for item in values]),block=None)
    return dict(result,block='NO_APPLICABLE_ACTION')
