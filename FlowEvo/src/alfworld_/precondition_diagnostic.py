"""Restricted, public-evidence applicability checks for the B v10 diagnostic."""

import re
from collections import Counter
from dataclasses import dataclass

TRUE, FALSE, UNKNOWN = 'TRUE', 'FALSE', 'UNKNOWN'
VERSION = 'alfworld-applicability-diagnostic-v10'
SCHEMA_VERSION = 'public-condition-1'
CHECKER_VERSION = 'public-receipts-1'
SELECTORS = ('goal_object', 'goal_target', 'failed_subject', 'failed_target', 'held_object')
COMMANDS = {'open': 1, 'close': 1, 'move': 2, 'take': 2, 'heat': 2, 'cool': 2, 'clean': 2}
OPERATORS = {
    'selected_failure': {},
    'same_category': {'left': 'role', 'right': 'role'},
    'same_instance': {'left': 'role', 'right': 'role'},
    'state_is': {'entity': 'role', 'state': ('open', 'closed')},
    'command_available': {'verb': tuple(COMMANDS), 'entities': 'roles'},
    'unique_command_binding': {'verb': tuple(COMMANDS), 'entity': 'role', 'position': ('first', 'second')},
    'goal_requires': {'operation': ('place', 'heat', 'cool', 'clean')},
    'observed_event': {'verb': tuple(COMMANDS), 'entities': 'roles',
                       'window': ('before_failure', 'after_failure', 'entire_prefix')},
}
NAME = re.compile(r'[a-z][a-z_]{0,31}\Z')
IDENTITY = re.compile(r'([a-z]+(?: [a-z]+)*)(?: ([1-9][0-9]*))?\Z')
GOAL = re.compile(
    r'(?:put (?:some |the |a )?(?:(clean|cool|hot) )?(.+?) (?:in|on) (?:the )?(.+?)'
    r'|(heat|cool|clean) (?:some |the |a )?(.+?) and put it (?:in|on) (?:the )?(.+?))\.\Z'
)
STATE = re.compile(r'\bthe ([a-z]+(?: [a-z]+)* [1-9][0-9]*) is (open|closed)\.', re.I)
NOOP = 'Nothing happens.'
CONNECTOR = {'move': ' to ', 'take': ' from ', 'heat': ' with ', 'cool': ' with ', 'clean': ' with '}
RULES = {'max_roles': 8, 'max_conditions': 16, 'max_expression_depth': 4, 'max_expression_nodes': 48,
         'max_sources_per_condition': 6, 'max_text': 400}

PROMPT = """Learn applicability conditions for the supplied historical mechanism, from its public
failure and recovery receipts. Output one JSON object. You may abstain with
{"decision":"ABSTAIN","reason":"..."}.
For a proposal, exact top-level keys are decision ("PROPOSE"), roles, conditions, require,
abstain, recovery, refusal, uncertainty, and scope. roles maps your reusable aliases to
supported selectors. Each conditions item has id, op, args, sources, claim, supports, and
contradicts. sources is a nonempty array of exact learning evidence IDs. claim, supports
and contradicts explain the fact and evidence for/against it, independently of evaluation.
require and abstain are expressions using {"condition":"condition_id"}, {"all":[...]},
{"any":[...]}, or {"not":{...}}. abstain may be null. Every condition must be used.
recovery, refusal, uncertainty, and scope are brief text, not runnable instructions.
Use only roles, supported predicates and finite arguments. observed_event may use the
subject alone for a binary action to match any second argument. command_available
requires every argument. unique_command_binding checks the requested argument position
(first or second) among current admissible commands, within the supplied role category.
It checks the visible command set only. Do not key off a trace ID,
an instance number, or a hand-authored answer. Missing public facts are UNKNOWN.
The host permits recovery only when require is TRUE and abstain is FALSE (or null).
Explain what would justify or contradict each condition. Cite actual learning receipts.
No Python, action execution, evaluation labels, or hidden-state requests.
"""


@dataclass(frozen=True)
class Entity:
    category: str
    number: str | None = None

    @property
    def name(self):
        return f'{self.category} {self.number}' if self.number else self.category


def entity(text):
    match = IDENTITY.fullmatch(text.lower()) if isinstance(text, str) else None
    return Entity(*match.groups()) if match else None


def command(text):
    if not isinstance(text, str) or ' ' not in text:
        return None
    verb, rest = text.split(' ', 1)
    if verb not in COMMANDS:
        return None
    parts = rest.split(CONNECTOR[verb], 1) if verb in CONNECTOR else [rest]
    values = tuple(map(entity, parts))
    return (verb, values) if len(values) == COMMANDS[verb] and all(values) else None


def receipt_effect(parsed, observation):
    """Classify exact public action receipts, including confirmed no-ops."""
    if observation == NOOP:
        return FALSE
    if not parsed:
        return UNKNOWN
    verb, values = parsed
    subject = values[0].name
    if verb == 'take':
        expected = f'You pick up the {subject} from the {values[1].name}.'
    elif verb == 'move':
        expected = f'You move the {subject} to the {values[1].name}.'
    elif verb in ('open', 'close'):
        expected = f'You {verb} the {subject}.'
        if (subject, 'open' if verb == 'open' else 'closed') in {
                (name.lower(), state.lower()) for name, state in STATE.findall(observation)}:
            return TRUE
    else:
        expected = f'You {verb} the {subject} using the {values[1].name}.'
    return TRUE if observation.startswith(expected) else UNKNOWN


def three_value(op, values):
    if op == 'not':
        return {TRUE: FALSE, FALSE: TRUE, UNKNOWN: UNKNOWN}[values[0]]
    decisive, neutral = (FALSE, TRUE) if op == 'all' else (TRUE, FALSE)
    return decisive if decisive in values else UNKNOWN if UNKNOWN in values else neutral


def _text(value):
    return isinstance(value, str) and 0 < len(value.strip()) <= RULES['max_text']


def _name(value):
    return isinstance(value, str) and NAME.fullmatch(value) is not None


def _require(test, code):
    if not test:
        raise ValueError(code)


def parse_candidate(value, evidence_ids):
    """Return an inspectable outcome. Unknown operators are valid extensions, unsupported here."""
    if not isinstance(value, dict) or value.get('decision') not in ('PROPOSE', 'ABSTAIN'):
        return dict(status='INVALID_CONDITION', reason='INVALID_DECISION', candidate=None)
    if value['decision'] == 'ABSTAIN':
        if set(value) == {'decision', 'reason'} and _text(value['reason']):
            return dict(status='MODEL_ABSTAINED', reason=value['reason'], candidate=None)
        return dict(status='INVALID_CONDITION', reason='INVALID_ABSTENTION', candidate=None)
    try:
        unsupported = _validate(value, evidence_ids)
    except ValueError as exc:
        return dict(status='INVALID_CONDITION', reason=str(exc), candidate=None,
                    submitted_conditions=len(value['conditions']) if isinstance(value.get('conditions'), list) else 0)
    return dict(status='CANDIDATE_DELIVERED', candidate=value, unsupported_conditions=unsupported)


def _validate(value, evidence_ids):
    _require(set(value) == {'decision', 'roles', 'conditions', 'require', 'abstain',
                            'recovery', 'refusal', 'uncertainty', 'scope'}, 'PROPOSAL_FIELDS')
    _require(all(_text(value[k]) for k in ('recovery', 'refusal', 'uncertainty', 'scope')), 'PROPOSAL_TEXT')
    roles = value['roles']
    _require(isinstance(roles, dict) and len(roles) <= RULES['max_roles']
             and all(_name(alias) and selector in SELECTORS for alias, selector in roles.items()), 'ROLE_BINDINGS')
    conditions = value['conditions']
    _require(isinstance(conditions, list) and 1 <= len(conditions) <= RULES['max_conditions'], 'CONDITION_COUNT')
    ids, unsupported = set(), []
    for index, row in enumerate(conditions):
        prefix = f'conditions[{index}]'
        _require(isinstance(row, dict) and set(row) == {'id', 'op', 'args', 'sources', 'claim', 'supports', 'contradicts'},
                 f'{prefix}.FIELDS')
        key, op, args, sources = (row[k] for k in ('id', 'op', 'args', 'sources'))
        _require(_name(key) and key not in ids and _name(op), f'{prefix}.IDENTITY')
        ids.add(key)
        _require(all(_text(row[k]) for k in ('claim', 'supports', 'contradicts')), f'{prefix}.TEXT')
        _require(isinstance(sources, list) and 1 <= len(sources) <= RULES['max_sources_per_condition']
                 and all(isinstance(ref, str) and ref in evidence_ids for ref in sources)
                 and len(set(sources)) == len(sources), f'{prefix}.SOURCE_REFERENCE')
        _require(isinstance(args, dict), f'{prefix}.ARGUMENTS')
        spec = OPERATORS.get(op)
        if spec is None:
            _require(len(args) <= 4 and all(_name(k) and (_name(v) or
                     isinstance(v, list) and len(v) <= 3 and all(_name(item) for item in v))
                     for k, v in args.items()), f'{prefix}.EXTENSION_ARGUMENTS')
            unsupported.append(key)
            continue
        _require(set(args) == set(spec), f'{prefix}.ARGUMENT_FIELDS')
        for field, kind in spec.items():
            arg = args[field]
            valid = (isinstance(arg, str) and arg in roles if kind == 'role' else
                     isinstance(arg, list) and all(isinstance(a, str) and a in roles for a in arg)
                     and (len(arg) == COMMANDS[args['verb']] or op == 'observed_event' and len(arg) == 1)
                     if kind == 'roles' else arg in kind)
            _require(valid, f'{prefix}.args.{field}')
        if op == 'unique_command_binding':
            _require(args['position'] == 'first' or COMMANDS[args['verb']] == 2, f'{prefix}.args.position')
    used = set()
    visited = 0

    def walk(node, depth):
        nonlocal visited
        visited += 1
        _require(depth <= RULES['max_expression_depth'] and visited <= RULES['max_expression_nodes'],
                 'EXPRESSION_LIMIT')
        _require(isinstance(node, dict) and len(node) == 1, 'EXPRESSION_NODE')
        op, operand = next(iter(node.items()))
        if op == 'condition':
            _require(isinstance(operand, str) and operand in ids, 'EXPRESSION_REFERENCE')
            used.add(operand)
        elif op == 'not':
            walk(operand, depth+1)
        else:
            _require(op in ('all', 'any') and isinstance(operand, list) and operand, 'EXPRESSION_OPERATOR')
            for child in operand:
                walk(child, depth+1)

    walk(value['require'], 1)
    if value['abstain'] is not None:
        walk(value['abstain'], 1)
    _require(used == ids, 'UNUSED_CONDITION')
    return unsupported


class PublicFacts:
    """Derive bounded facts solely from the public prefix, using an auditable grammar."""

    def __init__(self, case):
        if set(case) != {'id', 'goal', 'failed_action', 'failure_step_id', 'observation', 'history',
                         'admissible_commands', 'held_object', 'current_evidence_id'}:
            raise PermissionError('public condition input has unexpected fields')
        self.case = case
        scope = case['id']
        if (case['current_evidence_id'] != f'{scope}:current'
                or any(set(step) != {'step_id', 'action', 'observation', 'evidence_id'} for step in case['history'])
                or any(step['evidence_id'] != f"{scope}:{step['step_id']}" for step in case['history'])
                or len({step['step_id'] for step in case['history']}) != len(case['history'])):
            raise PermissionError('public evidence scope drift')
        self.goal_id = f'{scope}:goal'
        self.commands_id = f'{scope}:admissible_commands'
        self.held_id = f'{scope}:held_object'
        self.steps = [(step['evidence_id'], command(step['action']), step['observation'])
                      for step in case['history']]
        anchor = case['failure_step_id']
        self.anchor = next((i for i, step in enumerate(case['history']) if step['step_id'] == anchor), None)
        if ((self.anchor is None) != (anchor is None)
                or self.anchor is None and case['failed_action'] is not None
                or self.anchor is not None and case['history'][self.anchor]['action'] != case['failed_action']):
            raise PermissionError('public failure anchor drift')
        goal = GOAL.fullmatch(case['goal'].lower())
        self.operations = None
        goal_object = goal_target = None
        if goal:
            modifier, first_obj, first_target, operation, second_obj, second_target = goal.groups()
            goal_object, goal_target = entity(first_obj or second_obj), entity(first_target or second_target)
            operation = operation or {'hot': 'heat', 'cool': 'cool', 'clean': 'clean'}.get(modifier)
            self.operations = {'place', operation} - {None}
        failed = command(case['failed_action'])
        values = failed[1] if failed else ()
        anchor_ref = [self.steps[self.anchor][0]] if self.anchor is not None else []
        self.roles = {
            'goal_object': (goal_object, [self.goal_id] if goal_object else []),
            'goal_target': (goal_target, [self.goal_id] if goal_target else []),
            'failed_subject': (values[0] if values else None, anchor_ref),
            'failed_target': (values[1] if len(values) > 1 else None, anchor_ref),
            'held_object': self.held(),
        }

    def held(self):
        held, refs = None, []
        for raw_step, (ref, parsed, observation) in zip(self.case['history'], self.steps):
            effect = receipt_effect(parsed, observation)
            if effect == FALSE:
                continue
            if effect == TRUE and parsed[0] == 'take':
                held, refs = parsed[1][0], [ref]
            elif effect == TRUE and parsed[0] == 'move' and parsed[1][0] == held:
                held, refs = None, [ref]
            elif effect == UNKNOWN and not (raw_step['action'] in {'look', 'inventory', 'help'}
                                             or raw_step['action'].startswith(('go to ', 'examine '))):
                held, refs = None, []
        explicit = entity(self.case['held_object'])
        if explicit:
            return explicit, [self.held_id]
        return held, refs

    def state(self, subject):
        if not subject or not subject.number:
            return set(), []
        current = self.case['current_evidence_id']
        observations = [(current, self.case['observation'])]
        # Preserve an explicit preceding observation across confirmed no-ops only.
        # A missing later "open" receipt is never treated as evidence of "closed".
        if self.case['observation'] == NOOP:
            for ref, _, observation in reversed(self.steps):
                observations.append((ref, observation))
                if observation != NOOP:
                    break
        for index, (ref, text) in enumerate(observations):
            states = {state.lower() for name, state in STATE.findall(text) if name.lower() == subject.name}
            if states:
                return states, list(dict.fromkeys(item[0] for item in observations[:index+1]))
        return set(), []

    def event(self, verb, values, window):
        if any(not value or not value.number for value in values):
            return UNKNOWN, []
        if window != 'entire_prefix' and self.anchor is None:
            return UNKNOWN, []
        steps = (self.steps[:self.anchor] if window == 'before_failure' else
                 self.steps[self.anchor+1:] if window == 'after_failure' else self.steps)
        for ref, parsed, observation in reversed(steps):
            if parsed and parsed[0] == verb and parsed[1][:len(values)] == tuple(values):
                return receipt_effect(parsed, observation), [ref]
        return UNKNOWN, []


def check(candidate, public):
    """Inspect one valid declarative proposal. The reference labels are unavailable here."""
    facts = PublicFacts(public)
    roles = {alias: facts.roles[selector] for alias, selector in candidate['roles'].items()}
    commands = {command(text) for text in public['admissible_commands']} - {None}
    results = {}
    for row in candidate['conditions']:
        op, args = row['op'], row['args']
        value, evidence, conflict = UNKNOWN, [], False
        status = 'CHECKED' if op in OPERATORS else 'UNSUPPORTED_CONDITION'
        if op == 'selected_failure':
            value = TRUE if facts.anchor is not None else FALSE
            evidence = [facts.steps[facts.anchor][0]] if facts.anchor is not None else [f"{public['id']}:failure_step_id"]
        elif op in ('same_category', 'same_instance'):
            left, lhs = roles[args['left']]
            right, rhs = roles[args['right']]
            evidence = lhs + rhs
            if left and right:
                if op == 'same_category':
                    value = TRUE if left.category == right.category else FALSE
                elif left.number and right.number:
                    value = TRUE if left == right else FALSE
        elif op == 'state_is':
            item, bound = roles[args['entity']]
            observed, evidence = facts.state(item)
            evidence += bound
            conflict = len(observed) > 1
            if len(observed) == 1:
                value = TRUE if args['state'] in observed else FALSE
        elif op in ('command_available', 'observed_event'):
            bindings = [roles[name] for name in args['entities']]
            values = [item for item, _ in bindings]
            evidence = [ref for _, refs in bindings for ref in refs]
            if op == 'observed_event':
                value, refs = facts.event(args['verb'], values, args['window'])
                evidence += refs
            elif all(item and item.number for item in values):
                value = TRUE if (args['verb'], tuple(values)) in commands else FALSE
                evidence.append(facts.commands_id)
        elif op == 'unique_command_binding':
            item, evidence = roles[args['entity']]
            if item:
                position = ('first', 'second').index(args['position'])
                matches = {values[position] for verb, values in commands
                           if verb == args['verb'] and values[position].category == item.category}
                evidence = evidence + [facts.commands_id]
                if all(match.number for match in matches):
                    value = TRUE if len(matches) == 1 and (not item.number or item in matches) else FALSE
        elif op == 'goal_requires' and facts.operations is not None:
            value = TRUE if args['operation'] in facts.operations else FALSE
            evidence = [facts.goal_id]
        results[row['id']] = dict(op=op, truth=value, status=status, evidence_ids=list(dict.fromkeys(evidence)),
                                  evidence_conflict=conflict, learning_sources=row['sources'])

    def evaluate(node):
        op, operand = next(iter(node.items()))
        if op == 'condition':
            return results[operand]['truth']
        return three_value(op, [evaluate(operand)] if op == 'not' else [evaluate(child) for child in operand])

    required = evaluate(candidate['require'])
    refused = evaluate(candidate['abstain']) if candidate['abstain'] is not None else FALSE
    checkable = all(row['status'] == 'CHECKED' for row in results.values())
    truth = three_value('all', [required, three_value('not', [refused])])
    return dict(
        conditions=results, required=required, abstain=refused,
        role_bindings={alias:dict(category=item.category if item else None,
                                  instance=item.name if item and item.number else None, evidence_ids=refs)
                       for alias, (item, refs) in roles.items()},
        status='CHECKED' if checkable else 'UNSUPPORTED_CONDITION',
        truth=truth if checkable else UNKNOWN,
        conflict=(required == TRUE and refused == TRUE or any(row['evidence_conflict'] for row in results.values())),
        recovery_allowed=checkable and truth == TRUE,
    )


def evaluate_development(candidate, public_rows, private_refs):
    decisions = {row['id']: check(candidate, row) for row in public_rows}
    by_role = {}
    for role in ['all', *sorted({row['role'] for row in private_refs.values()})]:
        selected = {key: row for key, row in decisions.items() if role == 'all' or private_refs[key]['role'] == role}
        matrix = {ref: dict.fromkeys((TRUE, FALSE, UNKNOWN, 'UNSUPPORTED'), 0) for ref in ('YES', 'NO', 'UNKNOWN')}
        for key, row in selected.items():
            outcome = row['truth'] if row['status'] == 'CHECKED' else 'UNSUPPORTED'
            matrix[private_refs[key]['recovery_needed']][outcome] += 1
        by_role[role] = dict(
            records=len(selected), matrix=matrix, conflicts=sum(row['conflict'] for row in selected.values()),
            evaluable=sum(row['status'] == 'CHECKED' for row in selected.values()),
            positive_covered=matrix['YES'][TRUE], false_trigger=matrix['NO'][TRUE],
            over_rejected=matrix['YES'][FALSE], positive_unknown=matrix['YES'][UNKNOWN],
            uncertainty_trigger=matrix['UNKNOWN'][TRUE], reasonable_abstention=matrix['UNKNOWN'][UNKNOWN],
        )
    signatures = [(row['op'], tuple(sorted((key, repr(val)) for key, val in row['args'].items())))
                  for row in candidate['conditions']]
    condition_counts = {
        condition['id']: dict(Counter(
            row['conditions'][condition['id']]['truth'] if row['conditions'][condition['id']]['status'] == 'CHECKED'
            else 'UNSUPPORTED' for row in decisions.values()))
        for condition in candidate['conditions']
    }
    return dict(
        decisions=decisions, by_role=by_role, condition_counts=condition_counts,
        complexity=dict(roles=len(candidate['roles']), conditions=len(signatures),
                        repeated_conditions=len(signatures)-len(set(signatures)),
                        operators=dict(Counter(row['op'] for row in candidate['conditions']))),
        development_screen=('REVIEWABLE' if by_role['all']['positive_covered'] > 0
                            and not by_role['all']['false_trigger'] and not by_role['all']['uncertainty_trigger']
                            else 'INSUFFICIENT_DEVELOPMENT_EVIDENCE'),
        disposition='SHADOW_DIAGNOSTIC_ONLY',
    )
