"""Compact ALFWorld plans, staged diagnostics, and deterministic lowering to the Worker ABI."""

from dataclasses import dataclass
import json

from failure_evo.contracts import canonical, fingerprint

from . import generic_recovery_skill as core
from . import recovery_plan as v13
from . import recovery_skill_v12 as runtime

VERSION = 'alfworld-recovery-plan-v14'
MAX_ROLES, MAX_EVIDENCE, MAX_EXPRESSION = 7, 28, 240
REQUIRED = ('decision', 'obstacle', 'evidence', 'steps', 'completion')
OPTIONAL = ('roles', 'entry', 'stop_if')
WINDOWS = ('before_failure', 'at_failure', 'after_failure', 'entire_prefix')
OUTCOMES = ('effect', 'noop')
STATES = ('open', 'closed')
OPERATIONS = ('place', 'heat', 'cool', 'clean', 'examine')
SIMPLE_ROLES = ('goal_object', 'goal_target', 'held_object')
ROLE_SYNTAX = {
    'unvisited': 'unvisited',
    'support_of': 'support_of ROLE',
    'available_instance': 'available_instance VERB ROLE',
    'other_argument': 'other_argument VERB first|second ROLE [FILTER_ROLE]',
}
CONDITION_SYNTAX = {
    'same_kind': 'same_kind ROLE ROLE', 'same_instance': 'same_instance ROLE ROLE',
    'bound': 'bound ROLE', 'state': 'state ROLE open|closed', 'goal': 'goal OPERATION',
    'available': 'available VERB ROLE ...',
    'recorded': 'recorded WINDOW effect|noop VERB ROLE ...',
    'last': 'last WINDOW effect|noop VERB ROLE ...',
}
PROMPT = """Propose a short recovery plan for the supplied public failure and mechanism hypothesis.
Return one JSON object. You may instead return {"decision":"ABSTAIN","reason":"..."} or
{"decision":"UNSUPPORTED_REPRESENTATION","reason":"..."}. With PROPOSE, describe obstacle
and completion in plain language (1–400 characters each). Cite 1–28 unique short refs
copied from the supplied public steps. The host uses the supplied failed_verb and verifies
the live failed command; do not emit failed_verb or copy an instance number into the plan.

The host already provides goal_object, goal_target, held_object, and failed_first.
failed_second exists only for a binary failed command. Goal roles can be categories, so
choose an explicit public instance source for executable actions. Use roles only to name
a built-in role or select a public instance with one of the role phrases below. Aliases are
lowercase letters and underscores (up to 32 characters); roles allows at most seven aliases.
No action, destination, or guard is inferred from your prose.
unvisited chooses a publicly available unvisited navigation destination. support_of uses
an explicitly observed surface for the named object. available_instance needs a unique
first argument of a legal command in the named role's category. other_argument takes the
other argument of a legal binary command whose named position matches the chosen role.
Ambiguous or unobserved instances stay unbound.

steps is an ordered list of 1–8 objects. Each requires "do", a short action phrase such
as "VERB ROLE", with every role argument in order. "when" optionally lists required
conditions. The host already checks legality and uses the actual receipt for that action
to advance. Optional "until" is one current state or availability phrase. It allows
bounded repetition (at most 12 actions); advance when that condition becomes TRUE.
Entry and when require all conditions. Any stop_if condition can stop the plan. Missing
evidence remains UNKNOWN and UNKNOWN stop refuses. A recorded query checks presence in
the complete named public window; last checks the most recent matching receipt. Neither
can establish an unobserved outcome. Avoid requiring the success of a future step at entry.
Optional roles, entry, stop_if, and when default to empty. At most seven conditions in entry
or when (six when until is used), eight in stop_if, and ten distinct facts across the plan.
Every action or condition phrase is at most 240 characters. Use exactly the keys below.
""" + canonical(dict(required=REQUIRED, optional=OPTIONAL, step=dict(required=['do'], optional=['when', 'until']),
                      verbs=core.VERBS, role_phrases=ROLE_SYNTAX, condition_phrases=CONDITION_SYNTAX,
                      goal_operations=OPERATIONS, history_windows=WINDOWS))
REPAIR_PROMPT = PROMPT + """
Revise the complete plan from the report. Fix all checkable errors in one response. A
blocked check could not run yet. Public source diagnostics describe pre-action checks,
not reference actions or outcomes. Preserve your recovery idea or abstain. No Worker
feedback or independent validation results are provided.
"""


@dataclass(frozen=True)
class PlanInput:
    failed_verb: str
    anchors: dict
    steps: dict


_MISSING = object()


def _preview(value):
    if value is _MISSING:
        return {'missing': True}
    if isinstance(value, str) and len(value) <= 100:
        return value
    if type(value) in (int, bool, float) or value is None:
        return value
    text = value if isinstance(value, str) else canonical(value)
    return json.loads(text) if len(text) <= 100 else {'preview':text[:100], 'truncated':True}


def _key(path, key):
    return f'{path}.{key}' if core._alias(key) else f'{path}[{canonical(key[:80])}]'


class Diagnostics:
    def __init__(self):
        self.errors = []
        self.blocked = []

    def expect(self, valid, path, code, expected, actual):
        if not valid:
            self.errors.append(dict(path=path, code=code, expected=expected, actual=_preview(actual)))
        return valid

    def defer(self, path, check, *depends_on):
        self.blocked.append(dict(path=path, code='CHECK_BLOCKED', check=check, depends_on=list(depends_on)))

    def shape(self, value, path, required, optional=()):
        if not self.expect(isinstance(value, dict), path, 'EXPECTED_OBJECT', 'JSON object', value):
            self.defer(path,'OBJECT_FIELDS',path)
            return False
        for key in required:
            if key not in value:
                field = _key(path,key)
                self.expect(False,field,'MISSING_FIELD','required field',_MISSING)
                self.defer(field,'FIELD_CONTENT',field)
        for key in sorted(value.keys() - set(required) - set(optional)):
            self.expect(False, _key(path,key), 'UNEXPECTED_FIELD', 'field is not part of the contract', value[key])
        return True

    def sequence(self, value, path, minimum, maximum):
        if not self.expect(isinstance(value, list), path, 'EXPECTED_ARRAY', 'JSON array', value):
            self.defer(path,'ARRAY_ITEMS',path)
            return []
        self.expect(minimum <= len(value) <= maximum, path, 'ARRAY_LENGTH', f'{minimum}–{maximum} items', len(value))
        return value

    def tokens(self, value, path, code, grammar):
        if self.expect(isinstance(value, str) and 0 < len(value.strip()) <= MAX_EXPRESSION,
                       path, code, grammar, value):
            return value.split()
        self.defer(path,'PHRASE_ARGUMENTS',path)
        return []

    def receipt(self, status):
        return dict(status=status, errors=self.errors, blocked=self.blocked)


def _command(tokens, path, check, role_ref):
    if tokens[:2] == ['go', 'to']:
        tokens = ['go_to', *tokens[2:]]
    verb, *roles = tokens or ['']
    known = check.expect(verb in core.VERBS, path, 'UNKNOWN_ACTION_VERB', sorted(core.VERBS), verb)
    if known:
        check.expect(len(roles)==core.VERBS[verb], path, 'ACTION_ARITY', core.VERBS[verb], len(roles))
        for role in roles:
            role_ref(role,path)
    else:
        check.defer(path, 'ACTION_ARGUMENTS', path)
    return dict(verb=verb, entities=roles)


def _condition(value, path, check, role_ref, *, current=False):
    tokens = check.tokens(value, path, 'EXPECTED_CONDITION_PHRASE', 'one documented condition phrase')
    if not tokens:
        return None
    kind, *args = tokens
    if not check.expect(kind in CONDITION_SYNTAX, path, 'UNKNOWN_CONDITION', sorted(CONDITION_SYNTAX), kind):
        check.defer(path, 'CONDITION_ARGUMENTS', path)
        return None
    if current:
        check.expect(kind in ('state','available'), path, 'REPEAT_REQUIRES_CURRENT_FACT', ['state','available'], kind)
    if kind == 'available':
        return 'action_available', _command(args, path, check, role_ref)
    if kind in ('recorded','last'):
        if not check.expect(len(args)>=3, path, 'CONDITION_ARGUMENTS', CONDITION_SYNTAX[kind], value):
            return None
        window, outcome, *command = args
        check.expect(window in WINDOWS, path, 'EVENT_WINDOW', list(WINDOWS), window)
        check.expect(outcome in OUTCOMES, path, 'EVENT_OUTCOME', list(OUTCOMES), outcome)
        return ('event_recorded' if kind=='recorded' else 'event_is',
                dict(window=window, outcome=outcome, **_command(command,path,check,role_ref)))
    fields = {'same_kind':('left','right'), 'same_instance':('left','right'), 'bound':('entity',),
              'state':('entity','state'), 'goal':('operation',)}[kind]
    check.expect(len(args)==len(fields), path, 'CONDITION_ARGUMENTS', CONDITION_SYNTAX[kind], value)
    for name, argument in zip(fields,args):
        choices = {'state':STATES, 'operation':OPERATIONS}.get(name)
        if choices:
            check.expect(argument in choices,path,'CONDITION_ENUM',list(choices),argument)
        else:
            role_ref(argument,path)
    op = {'same_kind':'category_equal','same_instance':'instance_equal','state':'state_is','goal':'goal_requires'}
    return op.get(kind,kind), dict(zip(fields,args))


def _selector(value, path, check, role_ref, builtins):
    tokens = check.tokens(value,path,'INVALID_SELECTOR_TYPE','one documented role phrase')
    if not tokens:
        return None
    kind, *args = tokens
    if kind in builtins or kind == 'failed_second':
        role_ref(kind,path)
        check.expect(not args,path,'ROLE_ARGUMENTS','one built-in role',value)
        return {'alias':kind}
    if not check.expect(kind in ROLE_SYNTAX,path,'UNKNOWN_SELECTOR',sorted(ROLE_SYNTAX),kind):
        check.defer(path,'SELECTOR_ARGUMENTS',path)
        return None
    length = {'unvisited':(0,), 'support_of':(1,), 'available_instance':(2,), 'other_argument':(3,4)}[kind]
    check.expect(len(args) in length,path,'ROLE_ARGUMENTS',ROLE_SYNTAX[kind],value)
    if kind == 'unvisited':
        return dict(select='first_unvisited',verb='go_to')
    if kind == 'support_of':
        if args:
            role_ref(args[0],path)
            return dict(select='observed_support',entity_from=args[0])
        return None
    if args:
        verbs = list(core.VERBS) if kind=='available_instance' else [verb for verb, arity in core.VERBS.items() if arity==2]
        check.expect(args[0] in verbs,path,'SELECTOR_VERB',verbs,args[0])
    if kind == 'available_instance':
        if len(args)>=2:
            role_ref(args[1],path)
            return dict(select='admissible_instance',verb=args[0],category_from=args[1])
        return None
    if len(args)>=2:
        check.expect(args[1] in ('first','second'),path,'COMMAND_POSITION',['first','second'],args[1])
    for role in args[2:4]:
        role_ref(role,path)
    if len(args)<3:
        return None
    position = int(args[1]=='second')
    result = dict(select='command_argument',verb=args[0],match_from=args[2],
                  match_position=position,select_position=1-position)
    if len(args)>=4:
        result['filter_from'] = args[3]
    return result


def _schema(value, context, check):
    decision = value.get('decision') if isinstance(value,dict) else None
    if decision in ('ABSTAIN','UNSUPPORTED_REPRESENTATION'):
        check.shape(value,'$',('decision','reason'))
        if 'reason' in value:
            check.expect(core._text(value['reason']),'$.reason','EXPECTED_TEXT','1–400 nonblank characters',value['reason'])
        return None
    if not check.shape(value,'$',REQUIRED,OPTIONAL):
        return None
    if 'decision' in value:
        check.expect(decision=='PROPOSE','$.decision','DECISION',['PROPOSE','ABSTAIN','UNSUPPORTED_REPRESENTATION'],decision)
    for name in ('obstacle','completion'):
        if name in value:
            check.expect(core._text(value[name]),f'$.{name}','EXPECTED_TEXT','1–400 nonblank characters',value[name])
    seen = set()
    if 'evidence' in value:
        for index, ref in enumerate(check.sequence(value['evidence'],'$.evidence',1,MAX_EVIDENCE)):
            path = f'$.evidence[{index}]'
            if check.expect(isinstance(ref,str) and ref in context.steps,path,'EXPECTED_STEP_ID',
                            'exact short ref from the public steps',ref):
                check.expect(ref not in seen,path,'DUPLICATE_STEP_ID','unique step ref',ref)
                seen.add(ref)
    builtins = {role:role for role in SIMPLE_ROLES}
    builtins.update(list(v13.FAILED_ROLES.items())[:core.VERBS[context.failed_verb]])
    role_values = value.get('roles', {})
    roles_known = isinstance(role_values,dict)
    known = set(builtins) | (set(role_values) if roles_known else set())
    invalid_roles = set()

    def role_ref(role, path):
        if role in invalid_roles:
            check.defer(path,'ROLE_BINDING',_key('$.roles',role))
        if role not in known:
            if roles_known or role=='failed_second':
                check.expect(False,path,'UNDECLARED_ROLE','a built-in or declared role alias',role)
            else:
                check.defer(path,'ROLE_REFERENCE','$.roles')

    selectors = {}
    if check.expect(roles_known,'$.roles','EXPECTED_OBJECT','role alias to phrase object',role_values):
        check.expect(len(role_values)<=MAX_ROLES,'$.roles','ROLE_LIMIT',MAX_ROLES,len(role_values))
        for role, spec in sorted(role_values.items()):
            path = _key('$.roles',role)
            before = len(check.errors)
            valid = core._alias(role) and role not in (*SIMPLE_ROLES,*v13.FAILED_ROLES)
            check.expect(valid,path,'ROLE_ALIAS','new lowercase alias, distinct from built-ins',role)
            selectors[role] = _selector(spec,path,check,role_ref,builtins)
            if len(check.errors)>before:
                invalid_roles.add(role)
        for role, spec in selectors.items():
            if spec is not None:
                for name in ('entity_from','category_from','match_from','filter_from'):
                    if spec.get(name) in invalid_roles:
                        check.defer(_key('$.roles',role),'SELECTOR_DEPENDENCY',_key('$.roles',spec[name]))
    else:
        check.defer('$.roles','ROLE_DECLARATIONS','$.roles')

    def conditions(raw, path, width):
        return [(f'{path}[{i}]',_condition(item,f'{path}[{i}]',check,role_ref))
                for i,item in enumerate(check.sequence(raw,path,0,width))]

    entry = conditions(value.get('entry',[]),'$.entry',7)
    stop = conditions(value.get('stop_if',[]),'$.stop_if',8)
    steps = []
    for index, row in enumerate(check.sequence(value['steps'],'$.steps',1,v13.MAX_PHASES) if 'steps' in value else []):
        path = f'$.steps[{index}]'
        if not check.shape(row,path,('do',),('when','until')):
            continue
        tokens = check.tokens(row['do'],f'{path}.do','EXPECTED_ACTION_PHRASE','VERB followed by ordered role aliases') if 'do' in row else []
        action = _command(tokens,f'{path}.do',check,role_ref) if tokens else None
        when = conditions(row.get('when',[]),f'{path}.when',6 if 'until' in row else 7)
        until_path = f'{path}.until'
        until = (until_path,_condition(row['until'],until_path,check,role_ref,current=True)) if 'until' in row else None
        steps.append(dict(path=path,action=action,when=when,until=until))
    return dict(builtins=builtins,selectors=selectors,entry=entry,stop=stop,steps=steps)


def _semantic(value, context, parsed, check):
    builtins, selectors = parsed['builtins'], parsed['selectors']
    aliases = {name:spec.get('alias',name) for name,spec in selectors.items()}
    roles = {name:{'select':selector} for name,selector in builtins.items()}
    links = {'entity_from','category_from','match_from','filter_from'}
    for name, spec in selectors.items():
        if 'alias' in spec:
            continue
        lowered = dict(spec)
        for key in sorted(links & spec.keys()):
            target = aliases.get(spec[key],spec[key])
            allowed = set(builtins)
            if key=='match_from':
                allowed.update(alias for alias,other in selectors.items() if other.get('select')=='admissible_instance')
            check.expect(target in allowed,_key('$.roles',name),'ROLE_DEPENDENCY_KIND',
                         'fixed role or, for a command match, a unique admissible instance',spec[key])
            lowered[key] = target
        roles[name] = lowered

    def resolved(args):
        result = dict(args)
        if 'entities' in args:
            result['entities'] = [aliases.get(role,role) for role in args['entities']]
        for key in ('left','right','entity'):
            if key in args:
                result[key] = aliases.get(args[key],args[key])
        return result

    def atom_ref(name):
        return {'condition':name}

    evidence = [context.steps[ref] for ref in value['evidence']]
    failure = dict(verb=context.failed_verb,entities=list(builtins)[len(SIMPLE_ROLES):],window='at_failure',outcome='noop')
    conditions = [dict(id='plan_obstacle',op='event_is',args=failure,sources=evidence[:1])]
    facts = {}
    condition_paths = {'plan_obstacle':['$.obstacle']}

    def intern(op, args, path):
        signature = canonical([op,args])
        if signature not in facts:
            prefix, suffix = divmod(len(facts),26)
            name = f'fact_{chr(97+prefix)}{chr(97+suffix)}'
            facts[signature] = name
            condition_paths[name] = []
            conditions.append(dict(id=name,op=op,args=args,sources=evidence[:1]))
        name = facts[signature]
        condition_paths[name].append(path)
        return name

    def literals(rows):
        return [atom_ref(intern(op,resolved(args),path)) for path,(op,args) in rows]

    def require_possible(rows, earlier_verbs):
        states = {}
        for path,(op,args) in rows:
            if args.get('window')=='after_failure':
                check.expect(args['verb'] in earlier_verbs and args['outcome']=='effect',path,
                             'UNREACHABLE_POST_FAILURE_RECEIPT',
                             'an effect that an earlier phase could have produced',args)
            if op=='state_is':
                role = aliases.get(args['entity'],args['entity'])
                previous = states.setdefault(role,args['state'])
                check.expect(previous==args['state'],path,'CONTRADICTORY_CURRENT_STATE',previous,args['state'])

    entry = {'all':[atom_ref('plan_obstacle'),*literals(parsed['entry'])]}
    stop = {'any':literals(parsed['stop'])} if parsed['stop'] else None
    for path,(op,args) in parsed['stop']:
        if op=='event_is' and args['window']=='after_failure':
            check.expect(False,path,'STOP_RECEIPT_MISSING_AT_ENTRY',
                         'a known entry fact or recorded-presence query',args)
    rules, phases, earlier_verbs = [], [], set()
    for index, step in enumerate(parsed['steps']):
        action = resolved(step['action'])
        when, until = step['when'], step['until']
        require_possible([*parsed['entry'],*when] if index==0 else when, earlier_verbs)
        earlier_verbs.add(action['verb'])
        guard = literals(when)
        phase = dict(verb=action['verb'],args=action['entities'])
        if until:
            op,args = until[1]
            name = intern(op,resolved(args),until[0])
            phase['repeat_until'] = name
            guard.append({'not':atom_ref(name)})
        phases.append(phase)
        name = 'plan_'+chr(97+index)
        condition_paths[name] = [f'{step["path"]}.do']
        conditions.append(dict(id=name,op='action_available',args=action,sources=evidence[:1]))
        rules.append(dict(when={'all':[atom_ref(name),*guard]},action=action))
    check.expect(len(facts)<=v13.MAX_FACTS,'$','FACT_LIMIT',v13.MAX_FACTS,len(facts))
    skill = dict(decision='PROPOSE',evidence_ids=list(context.anchors),failure_evidence=list(context.anchors.values()),
                 scope=value['obstacle'],refusal='No verified public action for the active phase.',
                 roles=roles,conditions=conditions,rules=rules,entry=entry,stop=stop)
    if len(facts)>v13.MAX_FACTS:
        check.defer('$.steps','LOGIC_FEASIBILITY','$')
        return None
    # Check every phase even when another independently checkable semantic error exists.
    logic = runtime.check_logic(skill)
    phase_status = [logic['initial_rule_feasible'][0],*logic['continuation_rule_feasible'][1:]]
    for index, feasible in enumerate(phase_status):
        path = f'$.steps[{index}]'
        if feasible is None:
            check.expect(False,path,'LOGIC_CHECK_LIMIT','at most 12 distinct facts in the feasibility check',None)
        else:
            check.expect(feasible,path,'PHASE_STOP_CONFLICT',
                         'the active step is possible with applicable guards and stop false',feasible)
    if check.errors:
        return None
    lowered = runtime.parse_skill(skill,context.anchors,set(context.steps.values()))
    if not check.expect(lowered['candidate'] is not None,'$','LOWERING_REJECTED',
                        'accepted frozen Worker ABI',lowered.get('reason')):
        return None
    return dict(plan=dict(steps=phases), skill=skill, original=value, logic=logic, condition_paths=condition_paths)


def compile_plan(value, context):
    """Schema, semantic checks, and Worker lowering. No source or environment evaluation."""
    schema = Diagnostics()
    parsed = _schema(value,context,schema)
    if schema.errors:
        schema.defer('$','SEMANTIC_VALIDATION',*(sorted({row['path'] for row in schema.errors})))
        return dict(status='SCHEMA_REJECTED',schema=schema.receipt('REJECTED'),
                    semantics=Diagnostics().receipt('BLOCKED'),candidate=None)
    if parsed is None:
        return dict(status=value['decision'],reason=value['reason'],schema=schema.receipt('PASSED'),
                    semantics=Diagnostics().receipt('NOT_APPLICABLE'),candidate=None)
    semantic = Diagnostics()
    candidate = _semantic(value,context,parsed,semantic)
    return dict(status='COMPILED' if candidate else 'SEMANTIC_REJECTED',schema=schema.receipt('PASSED'),
                semantics=semantic.receipt('PASSED' if candidate else 'REJECTED'),candidate=candidate)


def first_decision(compiled, public):
    """Find the first active phase using only the public state at the failure boundary."""
    for phase, step in enumerate(compiled['plan']['steps']):
        checks = v13.inspect_phase(compiled['skill'],public,phase,step.get('repeat_until'))
        if not checks.get('phase_satisfied'):
            return phase, checks
    return phase, dict(checks,selection=None,block='PLAN_ALREADY_SATISFIED')


def _source_errors(compiled, phase, checks):
    skill = compiled['skill']
    path = f'$.steps[{phase}].do'
    block = checks['block']
    if block == 'PLAN_ALREADY_SATISFIED':
        return [dict(path=path,code=block,expected='an active recovery phase',actual='no action required')]
    findings = [dict(path=path,code=block,expected='an applicable, bound action',actual=block)]
    for role in skill['rules'][phase]['action']['entities']:
        if role not in checks.get('bindings',{}):
            continue
        entity = core.base.entity(checks['bindings'][role]['entity'])
        if entity is None or not entity.number:
            findings.append(dict(path=path,code='INSTANCE_UNRESOLVED',expected='one numbered public instance',
                                 actual=dict(role=role,binding='CATEGORY_ONLY' if entity else 'UNBOUND')))
    if block.startswith('ENTRY_'):
        expression, expected = skill['entry'], core.base.TRUE
        relevant = ('$.entry[','$.obstacle')
    elif block.startswith('STOP_'):
        expression, expected = skill['stop'], core.base.FALSE
        relevant = ('$.stop_if[',)
    elif block == 'NO_APPLICABLE_ACTION':
        expression, expected = skill['rules'][phase]['when'], core.base.TRUE
        relevant = (f'$.steps[{phase}].when[',path)
    else:
        expression, expected = None, None
        relevant = ()
    truth = checks.get('conditions',{})
    references = runtime._references(expression)
    if block == 'NO_APPLICABLE_ACTION':
        # A repeat guard contains a negated completion fact; its expected value is FALSE.
        until = compiled['plan']['steps'][phase].get('repeat_until')
        references.discard(until)
    if block == 'REPEAT_UNTIL_UNKNOWN':
        until = compiled['plan']['steps'][phase]['repeat_until']
        references, expected = {until}, 'a known TRUE or FALSE'
        relevant = (f'$.steps[{phase}].until',)
    for name in sorted(references):
        observed = truth[name]['truth']
        if observed!=expected:
            for origin in compiled['condition_paths'][name]:
                if origin.startswith(relevant):
                    findings.append(dict(path=origin,code='PUBLIC_CONDITION_VALUE',expected=expected,actual=observed))
    return findings


def review_public_sources(compiled, cases):
    """Deterministic pre-action observations, without selected commands or replay feedback."""
    rows, by_issue = [], {}
    for index, public in enumerate(cases,1):
        phase, checks = first_decision(compiled,public)
        selected = checks['selection'] is not None
        rows.append(dict(source=index,phase=phase,selectable=selected,block=checks['block'],
                         snapshot_sha256=fingerprint(public)))
        if not selected:
            for issue in _source_errors(compiled,phase,checks):
                row = by_issue.setdefault(canonical(issue),dict(issue,sources=[]))
                if index not in row['sources']:
                    row['sources'].append(index)
    count = sum(row['selectable'] for row in rows)
    status = 'ACTIONABLE_ALL' if rows and count==len(rows) else 'ACTIONABLE_SOME' if count else 'NO_FIRST_ACTION'
    return dict(status=status,source_count=len(rows),selectable=count,rows=rows,
                errors=list(by_issue.values()),blocked=[])
