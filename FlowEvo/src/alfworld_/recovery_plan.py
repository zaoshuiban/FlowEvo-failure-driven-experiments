"""Compile bounded public recovery plans to the existing declarative action ABI."""

from failure_evo.contracts import canonical

from . import generic_recovery_skill as core
from . import recovery_skill_v12 as runtime

VERSION = 'alfworld-recovery-plan-v13'
MAX_FACTS = 10
MAX_PHASES = core.MAX_RULES
MAX_REPEAT_ACTIONS = 12
FAILED_ROLES = {'failed_first': 'failed_subject', 'failed_second': 'failed_target'}
FIXED = set(core.FIXED) - set(FAILED_ROLES.values())
PREDICATES = {**core.ARGS, 'event_recorded': core.ARGS['event_is']}
FIELDS = ('decision', 'obstacle', 'failed_action', 'evidence', 'roles', 'facts',
          'entry', 'stop_if', 'steps', 'completion')
PROMPT = """Describe a small recovery plan for the supplied historical public evidence.
Return JSON only. You may return {"decision":"ABSTAIN","reason":"..."} or
{"decision":"UNSUPPORTED_REPRESENTATION","reason":"..."}. Otherwise return PROPOSE
with exactly the fields below. Do not output code, instance numbers, or permissions.
obstacle and completion are short descriptions (1–400 characters). The failed_action
is the action verb of the anchored no-op. evidence lists 1–28 exact, unique public step
IDs for the plan. The host verifies the anchored no-op and binds its ordered arguments
as failed_first and, for binary actions only, failed_second. Do not redeclare them.
roles maps aliases to public selectors. facts maps aliases to {"op": ..., "args": {...}}.
entry and each step's requires are arrays of fact names, all of which must be true.
stop_if is an array of safety-stop facts, any of which can stop the plan. If the combined
stop result is UNKNOWN, the plan declines. Empty arrays are allowed. At most seven facts
in entry or a step's requires (six for repeat steps), and eight in stop_if. Aliases are lowercase letters and
underscores, at most 32 characters. Facts must all be referenced.
Each step has verb, args (ordered role aliases), and requires. Steps are ordered, at most
eight. Advance only after a public receipt confirms the exact issued action had an effect.
Optional repeat_until names a current action_available or state_is fact. If true, advance
without issuing the step; if false, repeat the action only on a confirmed effect, at most
12 times; if unknown, decline. The last confirmed step completes the plan; this does not
prove the task is won.
Use a current-state predicate for a current fact; event_is needs a matching historical
receipt. event_recorded can test presence in a complete public window and is false when
no qualifying receipt was recorded and the bindings/window are known. Do not require a
step's own successful receipt in order to execute it. Use only public evidence at runtime.
""" + canonical(dict(fields=FIELDS, verbs=core.VERBS, fixed_selectors=sorted(FIXED),
                      facts=PREDICATES, max_facts=MAX_FACTS, max_roles=10,
                      state_values=['open', 'closed'],
                      goal_operations=['place', 'heat', 'cool', 'clean', 'examine'],
                      event_windows=['before_failure', 'at_failure', 'after_failure', 'entire_prefix'],
                      event_outcomes=['effect', 'noop'],
                      selectors=[{'select':'admissible_instance', 'verb':'verb', 'category_from':'alias'},
                                 {'select':'first_unvisited', 'verb':'go_to'},
                                 {'select':'observed_support', 'entity_from':'alias'},
                                 {'select':'command_argument', 'verb':'binary verb', 'match_from':'alias',
                                  'match_position':0, 'select_position':1,
                                  'filter_from':'optional fixed alias'}],
                      step={'verb':'action verb', 'args':['role alias'], 'requires':['fact alias'],
                            'repeat_until':'optional current fact alias'}))
REPAIR_PROMPT = PROMPT + """
This is the single static revision. Return a full plan or abstain. The user message contains
only the earlier plan, compiler diagnostics and allowed citation IDs. Preserve the proposed
obstacle and recovery approach. No environment validation feedback is available.
"""


class PlanError(ValueError):
    def __init__(self, field, code, detail):
        self.diagnostic = dict(field=field, code=code, detail=detail)


def require(ok, field, code, detail):
    if not ok:
        raise PlanError(field, code, detail)


def shape(value, fields, field):
    require(isinstance(value, dict), field, 'OBJECT', 'Expected an object.')
    for key in fields:
        require(key in value, f'{field}.{key}', 'MISSING_FIELD', 'Required field is missing.')
    require(set(value) == set(fields), field, 'UNEXPECTED_FIELD', 'Object contains undeclared fields.')


def refs(values, allowed, field, *, minimum=0, limit=MAX_FACTS):
    require(isinstance(values, list) and minimum <= len(values) <= limit,
            field, 'REFERENCE_COUNT', f'Expected {minimum}–{limit} references.')
    seen = set()
    for index, value in enumerate(values):
        path = f'{field}[{index}]'
        require(isinstance(value, str) and value in allowed, path, 'UNKNOWN_REFERENCE',
                'Reference must name an item in the declared namespace.')
        require(value not in seen, path, 'DUPLICATE_REFERENCE', 'Each reference must be unique in this array.')
        seen.add(value)


def action(verb, aliases, roles, field, argument_field='args'):
    require(isinstance(verb, str) and verb in core.VERBS, f'{field}.verb', 'ACTION_VERB',
            'Use an action verb from the frozen interface.')
    path = f'{field}.{argument_field}'
    require(isinstance(aliases, list) and len(aliases) == core.VERBS[verb], path,
            'ACTION_ARITY', 'Supply every action argument in order.')
    for index, name in enumerate(aliases):
        require(isinstance(name, str) and name in roles, f'{path}[{index}]', 'ROLE_REFERENCE',
                'Use a declared role or an available failed-action argument.')


def roles_for(value, arity):
    require(isinstance(value, dict) and len(value) <= 10, '$.roles', 'ROLE_COUNT', 'At most ten declared roles.')
    roles = {alias: {'select': selector} for alias, selector in list(FAILED_ROLES.items())[:arity]}
    for alias, selector in value.items():
        require(core._alias(alias) and alias not in FAILED_ROLES, '$.roles', 'ROLE_ALIAS',
                'Role names must be lowercase aliases and must not shadow failed-action arguments.')
        path = f'$.roles.{alias}'
        require(isinstance(selector, dict) and isinstance(selector.get('select'), str), path,
                'ROLE_SELECTOR', 'Provide a public selector object.')
        kind = selector['select']
        require(kind in FIXED | runtime.EXTRA_ROLES | {'admissible_instance', 'first_unvisited'},
                f'{path}.select', 'ROLE_SELECTOR', 'Selector is not in the plan interface.')
        roles[alias] = selector
    for alias, selector in value.items():
        path = f'$.roles.{alias}'
        kind = selector['select']
        links = {'admissible_instance': ('category_from',), 'observed_support': ('entity_from',),
                 'command_argument': ('match_from', 'filter_from')}.get(kind, ())
        for key in links:
            if key == 'filter_from' and key not in selector:
                continue
            target = selector.get(key)
            allowed = set(core.FIXED) | ({'admissible_instance'} if key == 'match_from' else set())
            require(isinstance(target, str) and roles.get(target, {}).get('select') in allowed,
                    f'{path}.{key}', 'ROLE_DEPENDENCY', 'Selector dependency is missing or has the wrong kind.')
        if kind == 'admissible_instance':
            shape(selector, ('select', 'verb', 'category_from'), path)
            require(isinstance(selector['verb'], str) and selector['verb'] in core.VERBS,
                    f'{path}.verb', 'ACTION_VERB', 'Unknown public action verb.')
        elif kind == 'command_argument':
            optional = ('filter_from',) if 'filter_from' in selector else ()
            shape(selector, ('select', 'verb', 'match_from', 'match_position', 'select_position', *optional), path)
            require(isinstance(selector['verb'], str) and core.VERBS.get(selector['verb']) == 2,
                    f'{path}.verb', 'BINARY_VERB_REQUIRED', 'Command argument selection requires a binary verb.')
            positions = (selector['match_position'], selector['select_position'])
            require(all(type(index) is int for index in positions) and set(positions) == {0, 1},
                    path, 'COMMAND_POSITIONS', 'Use distinct zero-based argument positions 0 and 1.')
        elif kind == 'observed_support':
            shape(selector, ('select', 'entity_from'), path)
        elif kind == 'first_unvisited':
            shape(selector, ('select', 'verb'), path)
            require(selector['verb'] == 'go_to', f'{path}.verb', 'EXPLORATION_VERB', 'Expected go_to.')
        else:
            shape(selector, ('select',), path)
    return roles


def compile_plan(value, anchors, public_steps):
    """Return deterministic static diagnostics or a compiled plan. No environment inputs."""
    try:
        require(isinstance(value, dict), '$', 'OBJECT', 'Expected a JSON object.')
        decision = value.get('decision')
        if decision in ('ABSTAIN', 'UNSUPPORTED_REPRESENTATION'):
            shape(value, ('decision', 'reason'), '$')
            require(core._text(value['reason']), '$.reason', 'TEXT', 'Expected 1–400 nonblank characters.')
            return dict(status=decision, reason=value['reason'], candidate=None, diagnostics=[])
        return _compile(value, anchors, public_steps)
    except PlanError as error:
        return dict(status='STATIC_REJECTED', candidate=None, diagnostics=[error.diagnostic])


def _compile(value, anchors, public_steps):
    shape(value, FIELDS, '$')
    require(value['decision'] == 'PROPOSE', '$.decision', 'DECISION', 'Expected PROPOSE or a documented refusal.')
    for key in ('obstacle', 'completion'):
        require(core._text(value[key]), f'$.{key}', 'TEXT', 'Expected 1–400 nonblank characters.')
    failure = value['failed_action']
    require(isinstance(failure, str) and failure in core.VERBS, '$.failed_action', 'ACTION_VERB',
            'Use a frozen action verb for the anchored no-op.')
    refs(value['evidence'], public_steps, '$.evidence', minimum=1, limit=28)
    roles = roles_for(value['roles'], core.VERBS[failure])
    facts, phases = value['facts'], value['steps']
    require(isinstance(facts, dict) and len(facts) <= MAX_FACTS, '$.facts', 'FACT_COUNT', 'At most ten facts.')
    require(isinstance(phases, list) and 1 <= len(phases) <= MAX_PHASES,
            '$.steps', 'STEP_COUNT', 'Expected one to eight ordered steps.')
    for key in ('entry', 'stop_if'):
        refs(value[key], facts, f'$.{key}')

    def leaf(name):
        return {'condition': name}

    # v12 requires a citation on each atom. The compiled atoms carry a plan-level pointer;
    # the original plan retains all citations, without claiming per-atom support.
    def atom(key, op, args):
        return dict(id=key, op=op, args=args, sources=value['evidence'][:1])

    conditions = [atom('plan_obstacle', 'event_is', dict(verb=failure,
                  entities=list(FAILED_ROLES)[:core.VERBS[failure]], window='at_failure', outcome='noop'))]
    reserved = {'plan_obstacle', *(f'plan_{chr(97+i)}' for i in range(MAX_PHASES))}
    for name, row in facts.items():
        require(core._alias(name) and name not in reserved, '$.facts', 'FACT_ALIAS', 'Invalid or reserved fact alias.')
        path = f'$.facts.{name}'
        shape(row, ('op', 'args'), path)
        op, args = row['op'], row['args']
        require(isinstance(op, str) and op in PREDICATES, f'{path}.op', 'PREDICATE', 'Unknown public predicate.')
        shape(args, PREDICATES[op], f'{path}.args')
        if op in ('category_equal', 'instance_equal', 'bound', 'state_is'):
            names = ('left', 'right') if op.endswith('_equal') else ('entity',)
            for key in names:
                require(isinstance(args[key], str) and args[key] in roles, f'{path}.args.{key}',
                        'ROLE_REFERENCE', 'Use a declared role.')
        if op in ('action_available', 'event_is', 'event_recorded'):
            action(args['verb'], args['entities'], roles, f'{path}.args', 'entities')
        for key, choices in {'state': ('open', 'closed'), 'operation': ('place', 'heat', 'cool', 'clean', 'examine'),
                             'outcome': ('effect', 'noop'),
                             'window': ('before_failure', 'at_failure', 'after_failure', 'entire_prefix')}.items():
            if key in args:
                require(args[key] in choices, f'{path}.args.{key}', 'ENUM_VALUE', 'Value is outside the frozen vocabulary.')
        conditions.append(atom(name, op, args))
    rules, used = [], set(value['entry'] + value['stop_if'])
    for index, step in enumerate(phases):
        path = f'$.steps[{index}]'
        optional = ('repeat_until',) if isinstance(step, dict) and 'repeat_until' in step else ()
        shape(step, ('verb', 'args', 'requires', *optional), path)
        action(step['verb'], step['args'], roles, path)
        refs(step['requires'], facts, f'{path}.requires')
        used.update(step['requires'])
        if optional:
            until = step['repeat_until']
            require(isinstance(until, str) and until in facts, f'{path}.repeat_until', 'UNKNOWN_REFERENCE',
                    'Repeat completion must reference a declared fact.')
            require(facts[until]['op'] in ('state_is', 'action_available'), f'{path}.repeat_until',
                    'REPEAT_REQUIRES_CURRENT_FACT', 'Use current state or legal command availability.')
            used.add(until)
        command = dict(verb=step['verb'], entities=step['args'])
        available = f'plan_{chr(97+index)}'
        conditions.append(atom(available, 'action_available', command))
        guard = list(map(leaf, [available, *step['requires']]))
        if optional:
            guard.append({'not':leaf(until)})
        rules.append(dict(when={'all': guard}, action=command))
    require(used == set(facts), '$.facts', 'UNUSED_FACT', 'Every fact must be referenced by a guard.')
    for path, names in (('$.entry', value['entry']), ('$.steps[0].requires', phases[0]['requires']),
                        ('$.stop_if', value['stop_if'])):
        for index, name in enumerate(names):
            fact = facts[name]
            if (fact['args'].get('window') == 'after_failure'
                    and (path != '$.stop_if' or fact['op'] == 'event_is')):
                raise PlanError(f'{path}[{index}]', 'EMPTY_POST_FAILURE_PREFIX',
                                'At entry there is no post-failure receipt yet.')
    skill = dict(decision='PROPOSE', evidence_ids=list(anchors), failure_evidence=list(anchors.values()),
                 scope=value['obstacle'], refusal='No verified public action for the active phase.',
                 roles=roles, conditions=conditions, rules=rules,
                 entry={'all': list(map(leaf, ['plan_obstacle', *value['entry']]))},
                 stop={'any': list(map(leaf, value['stop_if']))} if value['stop_if'] else None)
    # v12 bounds each expression fanout at eight; fail before lowering is accepted.
    require(len(value['entry']) <= 7, '$.entry', 'GUARD_WIDTH', 'At most seven entry facts.')
    require(len(value['stop_if']) <= 8, '$.stop_if', 'GUARD_WIDTH', 'At most eight stop facts.')
    for index, step in enumerate(phases):
        width = 6 if 'repeat_until' in step else 7
        require(len(step['requires']) <= width, f'$.steps[{index}].requires', 'GUARD_WIDTH',
                f'At most {width} phase facts for this step.')
    parsed = runtime.parse_skill(skill, anchors, public_steps)
    require('logic' in parsed, '$', 'LOWERING_REJECTED', parsed.get('reason', 'Compiler output rejected.'))
    logic = parsed['logic']
    require(logic['initial_rule_feasible'][0] is not None, '$.steps[0]', 'LOGIC_CHECK_LIMIT',
            'The first phase uses too many distinct facts to check feasibility.')
    require(logic['initial_rule_feasible'][0] is not False, '$.steps[0]', 'ENTRY_STOP_CONFLICT',
            'The first phase cannot satisfy entry and its guard while the stop condition is false.')
    for index, possible in enumerate(logic['continuation_rule_feasible'][1:], 1):
        require(possible is not None, f'$.steps[{index}]', 'LOGIC_CHECK_LIMIT',
                'This phase uses too many distinct facts to check feasibility.')
        require(possible is not False, f'$.steps[{index}]', 'PHASE_STOP_CONFLICT',
                'This phase cannot satisfy its guard while the stop condition is false.')
    require(parsed['candidate'] is not None, '$', 'LOWERING_REJECTED', 'Compiled skill was rejected.')
    return dict(status='COMPILED', candidate=dict(plan=value, skill=skill), diagnostics=[], logic=logic)


def inspect_phase(skill, public, phase, until=None, *, starting=None):
    """Select only the active phase. The replay host owns the phase counter."""
    starting = phase == 0 if starting is None else starting
    if starting and (not public['history'] or public['history'][-1]['step_id'] != public['failure_step_id']):
        return dict(block='STALE_OR_MISSING_FAILURE', selection=None)
    result = runtime.inspect(dict(skill, rules=[skill['rules'][phase]]), public, starting=starting)
    if until and not (starting and result['entry'] != 'TRUE') and result['stop'] == 'FALSE':
        truth = result['conditions'][until]['truth']
        if truth != 'FALSE':
            return dict(result, selection=None, phase_satisfied=truth=='TRUE',
                        block='PHASE_SATISFIED' if truth=='TRUE' else 'REPEAT_UNTIL_UNKNOWN')
    if result['selection'] is not None:
        result['selection']['index'] = phase
    return result
