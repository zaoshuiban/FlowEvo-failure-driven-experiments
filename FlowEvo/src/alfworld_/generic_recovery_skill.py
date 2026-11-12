"""Bounded recovery description, evidence checks, and a generic Worker adapter."""

import re

from failure_evo.contracts import canonical, fingerprint
from . import precondition_diagnostic as base

VERSION = 'alfworld-cross-mechanism-v11'
OPERATORS = (
    'category_equal', 'instance_equal', 'bound', 'state_is', 'action_available',
    'goal_requires', 'event_is', 'selected_failure',
)
VERBS = {**base.COMMANDS, 'go_to': 1, 'use': 1, 'examine': 1}
FIXED = ('goal_object', 'goal_target', 'failed_subject', 'failed_target', 'held_object')
MAX_ATOMS, MAX_RULES, MAX_DEPTH = 20, 8, 4
SOURCE_FORMAT = {
    'evidence_ids': 'mechanism trace IDs, exactly as supplied',
    'failure_evidence': 'array of selected failure anchor step IDs, one per trace',
    'decision': 'PROPOSE', 'scope': 'short text',
    'roles': {'alias': {'select': 'fixed selector, or admissible_instance / first_unvisited',
                        'verb': 'only dynamic selectors', 'category_from': 'fixed alias, only admissible_instance'}},
    'conditions': [{'id': 'lowercase alias', 'op': 'operator', 'args': 'object',
                    'sources': ['one or more exact learning step IDs']}],
    'entry': 'expression', 'stop': 'expression or null',
    'rules': [{'when': 'expression', 'action': {'verb': 'verb', 'entities': ['role aliases']}}],
    'refusal': 'short text',
}
ARGS = {
    'category_equal': ('left', 'right'), 'instance_equal': ('left', 'right'),
    'bound': ('entity',), 'state_is': ('entity', 'state'),
    'action_available': ('verb', 'entities'), 'goal_requires': ('operation',),
    'event_is': ('verb', 'entities', 'window', 'outcome'), 'selected_failure': (),
}
GENERATION_PROMPT = """Output a single JSON object describing a bounded recovery skill for the
model-discovered mechanism and the public evidence supplied. No Python or literal instance numbers.
You may return {"decision":"ABSTAIN","reason":"..."} or
{"decision":"UNSUPPORTED_REPRESENTATION","reason":"missing generic capability"}.
For PROPOSE use the exact fields and interfaces below. Entry is checked after the selected failure.
Before every next action, stop if stop is TRUE or UNKNOWN (null means no explicit stop).
Evaluate rules in given order; only an explicitly TRUE guard with a uniquely bound admissible action
can be selected. Stop if none qualifies. Separate an earlier successful action from current possession.
Do not fill in a location from a recovery suffix at runtime. Explore only using public commands and
a deliberate guard; the first_unvisited selector enumerates publicly listed successful-unvisited
navigation destinations deterministically. Compare roles explicitly, rather than merging selectors.
Use each condition in a guard/expression and cite step IDs, never whole trace IDs, in sources.
Expressions: {"condition":"atom_id"}, {"all":[...]}, {"any":[...]}, {"not":{...}}.
For roles use {"select":"goal_object"} etc., {"select":"admissible_instance","verb":"...",
"category_from":"fixed_alias"}, or {"select":"first_unvisited","verb":"go_to"}.
admissible_instance selects a unique first command argument of the given public category, respecting
an explicit instance in the category role. One unknown or multiple matches do not establish binding.
event_is uses window before_failure, at_failure, after_failure, or entire_prefix and outcome
effect or noop. A unary entity array on a binary event matches only its subject. For action_available
and rules, supply the full argument array. state_is supports open/closed.
Use goal_requires for place/heat/cool/clean/examine. No completion or permission claims.
"""
GENERATION_PROMPT += '\n' + canonical(dict(
    shape=SOURCE_FORMAT, args=ARGS, verbs=VERBS, fixed_roles=FIXED,
    limits=dict(atoms=MAX_ATOMS, rules=MAX_RULES, depth=MAX_DEPTH, roles=12),
))


class UnsupportedRepresentation(ValueError):
    pass


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _alias(value):
    return isinstance(value, str) and base.NAME.fullmatch(value) is not None


def _text(value):
    return isinstance(value, str) and 0 < len(value.strip()) <= 400


def _action_spec(value, roles, *, event=False):
    _need(isinstance(value, dict), 'ACTION_OBJECT')
    verb, entities = value.get('verb'), value.get('entities')
    _need(isinstance(verb, str), 'ACTION_VERB_TYPE')
    if verb not in VERBS:
        raise UnsupportedRepresentation(f'verb:{verb}')
    _need(isinstance(entities, list) and all(isinstance(name, str) and name in roles for name in entities)
          and (len(entities) == VERBS[verb] or event and len(entities) == 1), 'ACTION_ENTITIES')


def parse_skill(value, anchors, steps):
    """Strict on wire types. Preserve plausible capability gaps separately."""
    try:
        _need(isinstance(value, dict), 'PROPOSAL_OBJECT')
        decision = value.get('decision')
        if decision in ('ABSTAIN', 'UNSUPPORTED_REPRESENTATION'):
            _need(set(value) == {'decision', 'reason'} and _text(value['reason']), 'REFUSAL_SHAPE')
            return dict(status=decision, reason=value['reason'], candidate=None)
        _need(decision == 'PROPOSE' and set(value) == {'decision', *SOURCE_FORMAT}, 'PROPOSAL_FIELDS')
        trace_ids, cited = value['evidence_ids'], value['failure_evidence']
        _need(isinstance(trace_ids, list) and all(isinstance(x, str) for x in trace_ids)
              and len(trace_ids) == len(anchors) and set(trace_ids) == set(anchors), 'MECHANISM_EVIDENCE')
        _need(isinstance(cited, list) and all(isinstance(x, str) for x in cited)
              and len(cited) == len(anchors) and set(cited) == set(anchors.values()), 'ANCHOR_EVIDENCE')
        _need(_text(value['scope']) and _text(value['refusal']), 'PROPOSAL_TEXT')
        roles = value['roles']
        _need(isinstance(roles, dict) and len(roles) <= 12, 'ROLE_COUNT')
        for alias, binding in roles.items():
            _need(_alias(alias) and isinstance(binding, dict) and isinstance(binding.get('select'), str), 'ROLE_SHAPE')
            selector = binding['select']
            if selector in FIXED:
                _need(set(binding) == {'select'}, 'FIXED_ROLE_FIELDS')
            elif selector == 'admissible_instance':
                _need(set(binding) == {'select', 'verb', 'category_from'}
                      and isinstance(binding['category_from'], str)
                      and roles.get(binding['category_from'], {}).get('select') in FIXED, 'DYNAMIC_ROLE_SOURCE')
                _action_verb(binding['verb'])
            elif selector == 'first_unvisited':
                _need(set(binding) == {'select', 'verb'} and binding['verb'] == 'go_to', 'EXPLORATION_ROLE_FIELDS')
            else:
                raise UnsupportedRepresentation(f'role_selector:{selector}')
        atoms = value['conditions']
        _need(isinstance(atoms, list) and 1 <= len(atoms) <= MAX_ATOMS, 'ATOM_COUNT')
        names = set()
        for row in atoms:
            _need(isinstance(row, dict) and set(row) == {'id', 'op', 'args', 'sources'}, 'ATOM_FIELDS')
            key, op, args, sources = (row[k] for k in ('id', 'op', 'args', 'sources'))
            _need(_alias(key) and key not in names and _alias(op) and isinstance(args, dict), 'ATOM_ID_OR_ARGS')
            names.add(key)
            _need(isinstance(sources, list) and 1 <= len(sources) <= 6
                  and all(isinstance(x, str) and x in steps for x in sources)
                  and len(set(sources)) == len(sources), 'STEP_EVIDENCE_REFERENCE')
            if op not in ARGS:
                raise UnsupportedRepresentation(f'predicate:{op}')
            _need(set(args) == set(ARGS[op]), f'ARG_FIELDS:{op}')
            if op in ('category_equal', 'instance_equal', 'bound', 'state_is'):
                fields = ('left', 'right') if op.endswith('_equal') else ('entity',)
                _need(all(isinstance(args[k], str) and args[k] in roles for k in fields), f'ARG_ROLE:{op}')
            if op == 'state_is':
                _need(args['state'] in ('open', 'closed'), 'STATE_ENUM')
            if op == 'goal_requires':
                _need(args['operation'] in ('place', 'heat', 'cool', 'clean', 'examine'), 'OPERATION_ENUM')
            if op in ('action_available', 'event_is'):
                _action_spec(args, roles, event=op == 'event_is')
            if op == 'event_is':
                _need(args['window'] in ('before_failure', 'at_failure', 'after_failure', 'entire_prefix')
                      and args['outcome'] in ('effect', 'noop'), 'EVENT_ENUM')
        used = set()

        def expression(node, depth=1):
            _need(depth <= MAX_DEPTH and isinstance(node, dict) and len(node) == 1, 'EXPRESSION_SHAPE')
            op, child = next(iter(node.items()))
            if op == 'condition':
                _need(isinstance(child, str) and child in names, 'ATOM_REFERENCE')
                used.add(child)
            elif op == 'not':
                expression(child, depth+1)
            else:
                _need(op in ('all', 'any') and isinstance(child, list) and 1 <= len(child) <= 8, 'EXPRESSION_OPERATOR')
                for item in child:
                    expression(item, depth+1)

        expression(value['entry'])
        if value['stop'] is not None:
            expression(value['stop'])
        rules = value['rules']
        _need(isinstance(rules, list) and 1 <= len(rules) <= MAX_RULES, 'RULE_COUNT')
        for rule in rules:
            _need(isinstance(rule, dict) and set(rule) == {'when', 'action'}, 'RULE_FIELDS')
            expression(rule['when'])
            _need(isinstance(rule['action'], dict) and set(rule['action']) == {'verb', 'entities'}, 'ACTION_FIELDS')
            _action_spec(rule['action'], roles)
        _need(used == names, 'UNUSED_ATOM')
    except UnsupportedRepresentation as exc:
        return dict(status='UNSUPPORTED_REPRESENTATION', reason=str(exc), candidate=None)
    except (ValueError, TypeError, AttributeError) as exc:
        return dict(status='INVALID_DELIVERY', reason=str(exc), candidate=None)
    return dict(status='STRUCTURED_DELIVERED', candidate=value)


def _action_verb(verb):
    _need(isinstance(verb, str), 'ACTION_VERB_TYPE')
    if verb not in VERBS:
        raise UnsupportedRepresentation(f'verb:{verb}')


def parse_command(text):
    parsed = base.command(text)
    if parsed:
        return parsed
    for prefix, verb in (('go to ', 'go_to'), ('use ', 'use'), ('examine ', 'examine')):
        if text.startswith(prefix):
            entity = base.entity(text[len(prefix):])
            if entity:
                return verb, (entity,)
    return None


def receipt_truth(parsed, text):
    if text == base.NOOP:
        return base.FALSE
    if parsed and parsed[0] in ('go_to', 'use', 'examine'):
        verb, values = parsed
        name = values[0].name
        if verb == 'go_to' and text.startswith(f'You arrive at {name}.'):
            return base.TRUE
        if verb == 'use' and text.startswith((f'You turn on the {name}.', f'You turn off the {name}.')):
            return base.TRUE
        if verb == 'examine' and text.startswith(f"There's nothing special about {name}."):
            return base.TRUE
        return base.UNKNOWN
    return base.receipt_effect(parsed, text)


def public_facts(public):
    common = base.PublicFacts(public)
    roles = dict(common.roles)
    steps = [(row['evidence_id'], parse_command(row['action']), row['observation']) for row in public['history']]
    anchor = common.anchor
    if anchor is not None and (parsed := steps[anchor][1]):
        roles['failed_subject'] = parsed[1][0], [steps[anchor][0]]
        if len(parsed[1]) == 2:
            roles['failed_target'] = parsed[1][1], [steps[anchor][0]]
    operations = common.operations
    goal = re.fullmatch(r'examine (?:the |a |some )?(.+?) with (?:the |a )?(.+?)\.', public['goal'].lower())
    if goal:
        roles['goal_object'] = base.entity(goal[1]), [common.goal_id]
        roles['goal_target'] = base.entity(goal[2]), [common.goal_id]
        operations = {'examine'}
    return common, roles, steps, operations


def inspect(skill, public, *, starting):
    """Return public checks and an action binding. No reference or score input."""
    common, fixed, steps, operations = public_facts(public)
    commands = {parsed for text in public['admissible_commands'] if (parsed := parse_command(text))}
    roles = {}
    for alias, rule in skill['roles'].items():
        selector = rule['select']
        if selector in FIXED:
            roles[alias] = fixed[selector]
        elif selector == 'admissible_instance':
            source, refs = fixed[skill['roles'][rule['category_from']]['select']]
            choices = {items[0] for verb, items in commands if verb == rule['verb'] and source
                       and items[0].number and items[0].category == source.category
                       and (not source.number or items[0] == source)}
            roles[alias] = (next(iter(choices)) if len(choices) == 1 else None, refs+[common.commands_id])
        else:
            visited = {parsed[1][0] for _, parsed, observation in steps
                       if parsed and parsed[0]=='go_to' and receipt_truth(parsed, observation)==base.TRUE}
            choices = {items[0] for verb, items in commands if verb=='go_to' and items[0].number}-visited
            refs = [ref for ref, parsed, observation in steps if parsed and parsed[0]=='go_to'
                    and receipt_truth(parsed, observation)==base.TRUE]
            roles[alias] = (min(choices, key=lambda item:item.name) if choices else None, [common.commands_id,*refs])
    results = {}
    for atom in skill['conditions']:
        op, args = atom['op'], atom['args']
        truth, refs = base.UNKNOWN, []
        if op in ('category_equal', 'instance_equal'):
            left, refs_l = roles[args['left']]
            right, refs_r = roles[args['right']]
            refs = refs_l+refs_r
            if left and right and (op == 'category_equal' or left.number and right.number):
                matched = left.category == right.category if op == 'category_equal' else left == right
                truth = base.TRUE if matched else base.FALSE
        elif op == 'bound':
            item, refs = roles[args['entity']]
            if item and item.number:
                truth = base.TRUE
        elif op == 'state_is':
            item, bound_refs = roles[args['entity']]
            values, refs = common.state(item)
            refs += bound_refs
            if len(values) == 1:
                truth = base.TRUE if args['state'] in values else base.FALSE
        elif op == 'goal_requires' and operations is not None:
            truth, refs = (base.TRUE if args['operation'] in operations else base.FALSE), [common.goal_id]
        elif op == 'selected_failure':
            anchor = common.anchor
            truth = base.TRUE if anchor is not None else base.FALSE
            refs = [steps[anchor][0]] if anchor is not None else [f"{public['id']}:failure_step_id"]
        elif op in ('action_available','event_is'):
            values = tuple(roles[key][0] for key in args['entities'])
            refs = [ref for key in args['entities'] for ref in roles[key][1]]
            if all(item and item.number for item in values):
                if op == 'action_available':
                    truth = base.TRUE if (args['verb'], values) in commands else base.FALSE
                    refs.append(common.commands_id)
                else:
                    anchor = common.anchor
                    window = args['window']
                    candidates = steps if window=='entire_prefix' else []
                    if anchor is not None:
                        candidates = {'before_failure':steps[:anchor], 'at_failure':steps[anchor:anchor+1],
                                      'after_failure':steps[anchor+1:], 'entire_prefix':steps}[window]
                    for ref, parsed, text in reversed(candidates):
                        if parsed and parsed[0]==args['verb'] and parsed[1][:len(values)]==values:
                            truth = receipt_truth(parsed,text)
                            if args['outcome']=='noop':
                                truth = base.three_value('not',[truth])
                            refs.append(ref)
                            break
                        if window == 'at_failure' and parsed:
                            truth = base.FALSE
                            refs.append(ref)
        results[atom['id']] = dict(truth=truth, evidence_ids=list(dict.fromkeys(refs)))

    def evaluate(expr):
        op, body = next(iter(expr.items()))
        if op == 'condition':
            return results[body]['truth']
        return base.three_value(op, [evaluate(body)] if op == 'not' else [evaluate(node) for node in body])

    entry = evaluate(skill['entry'])
    stop = evaluate(skill['stop']) if skill['stop'] is not None else base.FALSE
    rule_truths = [evaluate(rule['when']) for rule in skill['rules']]
    result = dict(entry=entry, stop=stop, rules=rule_truths, conditions=results, selection=None,
                  role_bindings={alias:dict(entity=item.name if item else None,evidence_ids=refs)
                                 for alias,(item,refs) in roles.items()})
    if (starting and entry != base.TRUE) or stop != base.FALSE:
        return result
    for index, (rule, guard) in enumerate(zip(skill['rules'], rule_truths)):
        action = rule['action']
        values = tuple(roles[key][0] for key in action['entities'])
        if guard == base.TRUE and (action['verb'],values) in commands and all(item.number for item in values):
            result['selection'] = dict(index=index, values=[item.name for item in values])
            break
    return result


def worker_source(skill):
    """Compile only action descriptions to the same isolated environment ABI."""
    rules = [(rule['action']['verb'],len(rule['action']['entities'])) for rule in skill['rules']]
    return f'''# Structured adapter for {fingerprint(skill)}
RULES = {rules!r}
CONNECTORS = {base.CONNECTOR!r}

def environment_operator(context):
    state = context['state']
    index = state['index']
    values = state['values']
    if not isinstance(index, int) or not 0 <= index < len(RULES):
        return {{'status':'declined','state':{{}},'reason':'rule index invalid'}}
    verb, arity = RULES[index]
    if not isinstance(values, list) or len(values) != arity:
        return {{'status':'declined','state':{{}},'reason':'unbound action arguments'}}
    action = ('go to' if verb == 'go_to' else verb) + ' ' + values[0]
    if arity == 2:
        action += CONNECTORS[verb] + values[1]
    if action not in context['admissible_commands']:
        return {{'status':'declined','state':{{}},'reason':'action absent from public commands'}}
    return {{'status':'applied','action':action,'state':{{}},'reason':'selected public action'}}
'''
