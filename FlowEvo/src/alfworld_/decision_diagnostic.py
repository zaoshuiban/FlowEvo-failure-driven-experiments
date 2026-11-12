"""B v9 public-input diagnostics and read-only validation of reported decisions."""

from collections import Counter
import json

from .binding_diagnostic import INPUT_FIELDS, a_decision
from failure_evo.contracts import canonical

VERSION = 'alfworld-recovery-decision-diagnostic-v9'
SCHEMA_VERSION = 'v9-decision-schema-1'
CONSISTENCY_VERSION = 'v9-self-consistency-1'

TRUTH = {'enum': ['YES', 'NO', 'UNKNOWN']}
MATCH = {'enum': ['MATCH', 'CONFLICT', 'UNKNOWN']}
ENTITY = {'type': ['string', 'null'], 'minLength': 1, 'maxLength': 96}
TEXT = {'type': 'string', 'minLength': 1, 'maxLength': 180}
EVIDENCE = {
    'type': 'array', 'items': {'type': 'string'}, 'maxItems': 8, 'uniqueItems': True,
}
ENTITIES = (
    'goal_object_type', 'goal_object_instance', 'failed_object_type', 'failed_object_instance',
    'goal_container_type', 'goal_container_instance', 'failed_container_type', 'failed_container_instance',
)
MATCH_FIELDS = (
    'object_category_match', 'object_instance_match', 'held_object_matches_goal',
    'held_failed_object_match', 'container_category_match', 'container_instance_match',
    'local_target_binding', 'phase_match',
)
FACT_FIELDS = {
    **dict.fromkeys(ENTITIES, ENTITY),
    **dict.fromkeys(MATCH_FIELDS, MATCH),
    **dict.fromkeys(('binding_consistent', 'held_object_changed', 'obstacle_resolved', 'subgoal_completed'), TRUTH),
    'failure_step_id': ENTITY,
    'post_failure_evidence_steps': EVIDENCE,
}
DECISION_FIELDS = {
    'id': {'type': 'string', 'minLength': 1, 'maxLength': 96}, 'failure_relevant': TRUTH, 'obstacle_present': TRUTH,
    'recovery_needed': TRUTH, 'evidence_steps': EVIDENCE, 'uncertainty': TEXT,
}


def object_schema(properties):
    return {
        'type': 'object', 'properties': properties, 'required': list(properties),
        'additionalProperties': False,
    }


SCHEMAS = {
    'D': object_schema({'rows': {'type': 'array', 'items': object_schema(DECISION_FIELDS)}}),
    'S': object_schema({'rows': {'type': 'array', 'items': object_schema({
        **DECISION_FIELDS, 'facts': object_schema(FACT_FIELDS),
    })}}),
}
COMMON = """Return one JSON object with rows, one row per input case. Use only the provided
public case. Copy its id. Judge whether the selected historical failure is relevant now,
whether the same historical obstacle is currently present, and whether this failure needs
recovery now. YES means supported, NO means there is evidence against or no selected failure
for relevance/recovery, UNKNOWN means insufficient evidence. For obstacle_present use UNKNOWN
if the same historical obstacle cannot be identified. Keep uncertainty brief.
Every evidence_steps field is a JSON array of unique strings (0 to 8). Copy only the
case-scoped evidence_id from history or current_evidence_id for its current snapshot.
For example ["case_005:current"] or ["case_005:step_001","case_005:current"].
Never return a bare or comma-separated string, a bare step_id, or a different case's ID.
Return judgments only. Do not generate code or propose environment actions.
"""
S_FACTS = """Report facts first, then the decision. Goal instance fields refer to explicitly
named instances only. Failed entity fields refer to the selected historical failed command.
Use null for absent or unsupported entity names. Types omit instance numbers.
MATCH requires positive evidence, CONFLICT requires positive incompatible evidence,
UNKNOWN means the comparison is not established or not applicable.
Compare object and container category separately from explicit instance comparisons.
An explicit instance comparison is UNKNOWN if either side is unspecified.
held_object_matches_goal compares current possession to the goal's type and any explicit
instance, while held_failed_object_match compares current possession to the failed object.
Holding the failed object does not establish compatibility with the goal.
local_target_binding asks if public evidence justifies the historical destination as the
current local destination. A category goal can allow several instances. Without public
evidence disambiguating local alternatives, use UNKNOWN rather than inventing uniqueness.
phase_match compares the active task stage to the failed delivery stage, including required
processing and whether the stage has already been completed. Do not use possession as the
sole basis for phase. binding_consistent requires compatible established local binding,
current possession and stage. A demonstrated incompatibility makes it NO.
failure_step_id copies the case's local historical step_id, or null if absent.
post_failure_evidence_steps is an array of historical evidence_id values strictly after
that anchor, excluding the current snapshot. Use [] when there are no relevant later steps.
obstacle_resolved concerns the same obstacle. held_object_changed means the failed object
has since been lost or replaced as the held object. subgoal_completed concerns the original
delivery subgoal. Use UNKNOWN for unsupported changes or unresolved uncertainty.
"""
PROMPTS = {
    arm: COMMON + (S_FACTS if arm == 'S' else '') + 'Exact JSON Schema: ' + canonical(schema)
    for arm, schema in SCHEMAS.items()
}


def project(public):
    if set(public) != INPUT_FIELDS:
        raise PermissionError('unexpected public projection fields')
    case_id = public['id']
    return {
        **public,
        'current_evidence_id': f'{case_id}:current',
        'history': [
            {'step_id': step['step_id'], 'action': step['action'], 'observation': step['observation'],
             'evidence_id': f"{case_id}:{step['step_id']}"}
            for step in public['history']
        ],
    }


def problem(field, code, **details):
    return dict(field=field, code=code, **details)


def evidence_errors(value, allowed, field, case_id):
    if not isinstance(value, list):
        return [problem(field, 'EXPECTED_ARRAY')]
    errors = []
    if len(value) > EVIDENCE['maxItems']:
        errors.append(problem(field, 'TOO_MANY_ITEMS'))
    seen = set()
    for index, ref in enumerate(value):
        item = f'{field}[{index}]'
        if not isinstance(ref, str):
            errors.append(problem(item, 'EXPECTED_STRING'))
            continue
        if ref not in allowed:
            code = 'CROSS_CASE_EVIDENCE' if ':' in ref and ref.split(':', 1)[0] != case_id else 'UNKNOWN_EVIDENCE'
            errors.append(problem(item, code))
        if ref in seen:
            errors.append(problem(item, 'DUPLICATE_EVIDENCE'))
        seen.add(ref)
    return errors


def field_errors(row, schema, prefix=''):
    if not isinstance(row, dict):
        return [problem(prefix or 'row', 'EXPECTED_OBJECT')]
    fields = schema['properties']
    errors = [problem(prefix + k, 'MISSING_FIELD') for k in fields if k not in row]
    errors.extend(problem(prefix + k, 'UNEXPECTED_FIELD') for k in sorted(row.keys() - fields.keys()))
    for key in fields.keys() & row.keys():
        spec, value = fields[key], row[key]
        field = prefix + key
        if 'enum' in spec:
            if not isinstance(value, str):
                errors.append(problem(field, 'EXPECTED_STRING'))
            elif value not in spec['enum']:
                errors.append(problem(field, 'INVALID_ENUM'))
        elif spec['type'] == 'object':
            errors.extend(field_errors(value, spec, field + '.'))
        elif spec['type'] != 'array':
            if value is None and spec is ENTITY and key != 'id':
                continue
            if not isinstance(value, str):
                errors.append(problem(field, 'EXPECTED_STRING'))
            elif not value.strip() or len(value) > spec['maxLength']:
                errors.append(problem(field, 'INVALID_LENGTH'))
    return sorted(errors, key=lambda error: (error['field'], error['code']))


def consistency(row):
    """Compare only model assertions. No labels, public-state inference or mutation."""
    issues = []
    yes = row['recovery_needed'] == 'YES'
    if yes:
        for field, bad, code in (
            ('failure_relevant', 'NO', 'YES_WITH_IRRELEVANT_FAILURE'),
            ('failure_relevant', 'UNKNOWN', 'YES_WITH_UNKNOWN_RELEVANCE'),
            ('obstacle_present', 'NO', 'YES_WITH_ABSENT_OBSTACLE'),
            ('obstacle_present', 'UNKNOWN', 'YES_WITH_UNKNOWN_OBSTACLE'),
        ):
            if row[field] == bad:
                issues.append(problem('recovery_needed', code, conflicts_with=field))
    if 'facts' not in row:
        return issues
    facts = row['facts']
    binding_conflicts = [field for field in MATCH_FIELDS if facts[field] == 'CONFLICT']
    if facts['binding_consistent'] == 'YES':
        for field in binding_conflicts:
            issues.append(problem('facts.binding_consistent', 'BINDING_WITH_CONFLICT', conflicts_with=field))
        for field in ('local_target_binding', 'held_failed_object_match', 'held_object_matches_goal', 'phase_match'):
            if facts[field] == 'UNKNOWN':
                issues.append(problem('facts.binding_consistent', 'BINDING_WITH_UNCERTAINTY', conflicts_with=field))
    for comparison, left, right in (
        ('object_category_match', 'goal_object_type', 'failed_object_type'),
        ('object_instance_match', 'goal_object_instance', 'failed_object_instance'),
        ('container_category_match', 'goal_container_type', 'failed_container_type'),
        ('container_instance_match', 'goal_container_instance', 'failed_container_instance'),
    ):
        a, b = facts[left], facts[right]
        expected = 'UNKNOWN' if a is None or b is None else (
            'MATCH' if a.strip().casefold() == b.strip().casefold() else 'CONFLICT')
        if facts[comparison] != 'UNKNOWN' and facts[comparison] != expected:
            issues.append(problem('facts.' + comparison, 'COMPARISON_CONTRADICTS_REPORTED_ENTITIES'))
        # A direct conflict in the model's entity values is a conflict even when
        # its separate comparison field says MATCH or UNKNOWN.
        if expected == 'CONFLICT':
            binding_conflicts.append(comparison)
            if facts['binding_consistent'] == 'YES':
                issues.append(problem('facts.binding_consistent', 'BINDING_WITH_ENTITY_CONFLICT',
                                      conflicts_with=comparison))
    if row['obstacle_present'] == 'YES' and facts['obstacle_resolved'] == 'YES':
        issues.append(problem('obstacle_present', 'SAME_OBSTACLE_PRESENT_AND_RESOLVED'))
    if facts['held_object_changed'] == 'YES' and facts['held_failed_object_match'] == 'MATCH':
        issues.append(problem('facts.held_failed_object_match', 'SAME_OBJECT_REPORTED_REPLACED'))
    if facts['subgoal_completed'] == 'YES' and facts['phase_match'] == 'MATCH':
        issues.append(problem('facts.phase_match', 'SAME_STAGE_REPORTED_COMPLETED'))
    if yes:
        if facts['failure_step_id'] is None:
            issues.append(problem('recovery_needed', 'YES_WITHOUT_FAILURE_ANCHOR'))
        if binding_conflicts:
            issues.append(problem('recovery_needed', 'YES_WITH_BINDING_CONFLICT',
                                  conflicts_with=sorted(set(binding_conflicts))))
        for field, bad, code in (
            ('obstacle_resolved', 'YES', 'YES_WITH_RESOLVED_OBSTACLE'),
            ('held_object_changed', 'YES', 'YES_WITH_CHANGED_HELD_OBJECT'),
            ('subgoal_completed', 'YES', 'YES_WITH_COMPLETED_SUBGOAL'),
            ('local_target_binding', 'UNKNOWN', 'YES_WITH_UNCERTAIN_LOCAL_TARGET'),
            ('binding_consistent', 'NO', 'YES_WITH_BINDING_NO'),
            ('binding_consistent', 'UNKNOWN', 'YES_WITH_BINDING_UNKNOWN'),
        ):
            if facts[field] == bad:
                issues.append(problem('recovery_needed', code, conflicts_with='facts.' + field))
    return issues


def parse_rows(value, arm, cases):
    """Reject broken rows independently and retain valid, inconsistent predictions."""
    if not isinstance(value, dict) or set(value) != {'rows'} or not isinstance(value['rows'], list):
        return dict(envelope='INVALID_ENVELOPE', rows={}, rejected=[], consistency={},
                    missing=[case['id'] for case in cases])
    lookup = {case['id']: case for case in cases}
    ids = Counter(row['id'] for row in value['rows']
                  if isinstance(row, dict) and isinstance(row.get('id'), str))
    accepted, rejected, checks = {}, [], {}
    for index, row in enumerate(value['rows']):
        key = row.get('id') if isinstance(row, dict) else None
        errors = field_errors(row, SCHEMAS[arm]['properties']['rows']['items'])
        if isinstance(key, str) and key not in lookup:
            errors.append(problem('id', 'UNEXPECTED_CASE'))
        elif isinstance(key, str) and ids[key] != 1:
            errors.append(problem('id', 'DUPLICATE_CASE'))
        if isinstance(key, str) and key in lookup and isinstance(row, dict):
            case = lookup[key]
            history = {step['step_id']: step['evidence_id'] for step in case['history']}
            allowed = {*history.values(), case['current_evidence_id']}
            if 'evidence_steps' in row:
                errors.extend(evidence_errors(row['evidence_steps'], allowed, 'evidence_steps', key))
            facts = row.get('facts')
            if arm == 'S' and isinstance(facts, dict):
                anchor = facts.get('failure_step_id')
                if isinstance(anchor, str) and anchor not in history:
                    errors.append(problem('facts.failure_step_id', 'UNKNOWN_EVIDENCE'))
                after = []
                if isinstance(anchor, str) and anchor in history:
                    timeline = list(history)
                    after = [history[step] for step in timeline[timeline.index(anchor) + 1:]]
                if 'post_failure_evidence_steps' in facts:
                    errors.extend(evidence_errors(facts['post_failure_evidence_steps'],
                                                  after, 'facts.post_failure_evidence_steps', key))
        if errors:
            rejected.append(dict(index=index, id=key, errors=errors))
            continue
        accepted[key] = row
        issues = consistency(row)
        checks[key] = dict(status='INCONSISTENT_OUTPUT' if issues else 'CONSISTENT_OUTPUT', issues=issues)
    return dict(envelope='ACCEPTED', rows=accepted, rejected=rejected, consistency=checks,
                missing=[key for key in lookup if key not in accepted])


def replay_v8(cases, result):
    """Diagnose the legacy deliveries in memory, keeping all original judgments."""
    lookup = {case['public']['id']: case for case in cases}
    audit = []
    for receipt in result['receipts']:
        arm = receipt['arm']
        original = receipt['result']
        rows = json.loads(original['raw_response']['choices'][0]['message']['content'])['rows']
        for row in rows:
            key = row['id']
            case = lookup[key]
            errors = []
            if arm == 'B':
                public = case['public']
                allowed = {'current', *(s['step_id'] for s in public['history'])}
                errors = evidence_errors(row['evidence_steps'], allowed, 'evidence_steps', key)
            else:
                fields = ('object_match', 'target_match', 'phase_match')
                if row['decision'] != a_decision([row[k] for k in fields]):
                    errors.append(problem('decision', 'INCONSISTENT_OUTPUT'))
                for category, match in (('object_type_match', 'object_match'), ('target_type_match', 'target_match')):
                    if row[category] == 'CONFLICT' and row[match] == 'MATCH':
                        errors.append(problem(match, 'INCONSISTENT_OUTPUT', conflicts_with=category))
            audit.append(dict(arm=arm, id=key, original_accepted=key in result['predictions'][arm],
                              errors=errors, original_decision=row.get('recovery_needed', row.get('decision')),
                              frozen_recovery_reference=case['B']['recovery_needed'] if arm == 'B' else None))
    return audit


def field_score(refs, predictions, field):
    known = [key for key, row in refs.items() if row[field] not in (None, 'UNKNOWN')]
    unknown = [key for key in refs if key not in known]
    return dict(
        known_reference=len(known),
        known_correct=sum(key in predictions and predictions[key][field] == refs[key][field] for key in known),
        unknown_reference=len(unknown),
        unknown_reference_matched=sum(key in predictions and predictions[key][field] == refs[key][field]
                                      for key in unknown),
        predicted_unknown=sum(row[field] in (None, 'UNKNOWN') for row in predictions.values()),
        delivery_missing=len(refs) - len(predictions),
    )


def decision_scores(keys, refs, predictions):
    matrix = {label: dict.fromkeys(('YES', 'NO', 'UNKNOWN', 'MISSING'), 0)
              for label in ('YES', 'NO', 'UNKNOWN')}
    for key in keys:
        actual = predictions.get(key, {}).get('recovery_needed', 'MISSING')
        matrix[refs[key]['recovery_needed']][actual] += 1
    return dict(
        records=len(keys), matrix=matrix,
        needed_yes=matrix['YES']['YES'], false_trigger=matrix['NO']['YES'],
        false_reject_no=matrix['YES']['NO'], abstained_needed=matrix['YES']['UNKNOWN'],
        overconfident_yes=matrix['UNKNOWN']['YES'], correct_no=matrix['NO']['NO'],
        predicted_unknown=sum(counts['UNKNOWN'] for counts in matrix.values()),
        delivery_missing=sum(counts['MISSING'] for counts in matrix.values()),
    )


def score_pairs(cases, refs, predictions, checks):
    ids = [case['public']['id'] for case in cases]
    both = [key for key in ids if all(key in predictions[arm] for arm in SCHEMAS)]
    scores = {}
    for arm in SCHEMAS:
        actual = predictions[arm]
        scores[arm] = dict(
            all=decision_scores(ids, refs, actual),
            delivered=decision_scores([key for key in ids if key in actual], refs, actual),
            both_delivered=decision_scores(both, refs, actual),
            by_role={
                role: decision_scores([case['public']['id'] for case in cases if case['role'] == role], refs, actual)
                for role in sorted({case['role'] for case in cases})
            },
            common_fields={field: field_score(refs, actual, field)
                           for field in ('failure_relevant', 'obstacle_present')},
            inconsistent_rows=sum(bool(check['issues']) for check in checks[arm].values()),
            inconsistent_rows_both_delivered=sum(bool(checks[arm][key]['issues']) for key in both),
            issue_rows=dict(Counter(code for check in checks[arm].values()
                                    for code in {issue['code'] for issue in check['issues']})),
        )
    scores['S']['facts'] = {
        field: field_score({key: row['facts'] for key, row in refs.items()},
                           {key: row['facts'] for key, row in predictions['S'].items()}, field)
        for field in FACT_FIELDS if field != 'post_failure_evidence_steps'
    }
    paired = {}
    for label, keys in [('all', ids), ('both_delivered', both)]:
        transitions = Counter()
        correctness = Counter()
        delivery = Counter()
        for key in keys:
            reference = refs[key]['recovery_needed']
            d, s = (predictions[arm].get(key, {}).get('recovery_needed', 'MISSING') for arm in SCHEMAS)
            transitions[(reference, d, s)] += 1
            correctness[(d == reference, s == reference)] += 1
            delivery[(d != 'MISSING', s != 'MISSING')] += 1
        paired[label] = dict(
            records=len(keys), D_only_correct=correctness[True, False],
            S_only_correct=correctness[False, True], both_correct=correctness[True, True],
            neither_correct=correctness[False, False], D_only_delivered=delivery[True, False],
            S_only_delivered=delivery[False, True], neither_delivered=delivery[False, False],
            transitions=[dict(reference=ref, D=d, S=s, count=count)
                         for (ref, d, s), count in sorted(transitions.items())],
        )
    return dict(arms=scores, paired=paired)
