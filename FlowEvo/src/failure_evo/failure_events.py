"""Host-recorded public facts; weaker than MechanismStore causal certification."""
import ast
import hashlib
import math
from pathlib import Path

from .contracts import PublicFeedback, canonical, fingerprint
from .evidence import EvidenceStore


def finite_time(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('finite timestamp required')
    return value


def generation_metadata(response):
    """Never propagate arbitrary provider text, metadata, or hidden verdict fields."""
    reason = response.get('finish_reason')
    return {'finish_reason': reason if reason in ('stop', 'length', 'error', 'unknown') else 'unknown'}


def structural_status(code):
    if not isinstance(code, str) or not code.strip():
        return 'NO_COMPLETE_CODE'
    try:
        ast.parse(code)
    except (SyntaxError, ValueError):
        return 'COMPILE_ERROR'
    return 'STRUCTURAL_PASS'


def checked_public_feedback(raw):
    """Require explicit nonempty host-audited checks before accepting public PASS."""
    feedback = PublicFeedback.project(raw)
    if feedback.status == 'PUBLIC_PASS':
        count = raw.get('tests_run')
        if type(count) is not int or count <= 0 or type(raw.get('tests_passed')) is not int or raw.get('tests_passed') != count:
            return PublicFeedback('UNKNOWN')
    return feedback


class FailureEvidenceStore:
    """Only trusted host code may call record; candidates receive no store handle."""
    def __init__(self, path):
        self.events = EvidenceStore(path)
        self.artifacts = Path(path).parent / 'failure_artifacts'

    def visible(self, at, stream_id=None):
        finite_time(at)
        records = self.events.visible(at)
        revoked = {r['payload']['event_id'] for r in records if r['kind']=='EVIDENCE_REVOKED'}
        visible = {}
        for record in records:
            event = record['payload']
            if record['kind'] != 'FAILURE_FACT' or event['available_from'] > at or event['event_id'] in revoked:
                continue
            if stream_id is not None and event['stream_id'] != stream_id:
                continue
            if all(source in visible for source in event['source_evidence_ids']):
                artifact = self.artifacts / (event['candidate_sha256'] + '.py')
                if artifact.is_file() and hashlib.sha256(artifact.read_bytes()).hexdigest() == event['candidate_sha256']:
                    visible[event['event_id']] = event
        return tuple(visible.values())

    def revoke(self, event_id, reason, at):
        if event_id not in {e['event_id'] for e in self.visible(at)}:
            raise ValueError('cannot revoke unknown evidence')
        self.events.append('EVIDENCE_REVOKED', {'event_id':event_id, 'reason':str(reason)}, at)

    def record(self, *, stream_id, task_id, family_id, stage, code, feedback,
               observed_at, available_from, finish_reason='unknown', parent_sha256='',
               provenance_group_id='', source_evidence_ids=(), synthetic=False, validation_cost=None):
        finite_time(observed_at)
        finite_time(available_from)
        if available_from < observed_at:
            raise ValueError('evidence cannot precede observation')
        if not all(isinstance(x, str) and x for x in (stream_id, task_id, family_id, stage)):
            raise ValueError('event identity required')
        if not isinstance(code, str):
            raise ValueError('original code must be retained as text')
        if not isinstance(feedback, PublicFeedback) or feedback.visibility != 'public':
            raise ValueError('projected public feedback required')
        if feedback.status == 'PRIVATE_RESULT_WITHHELD':
            return None
        known = {event['event_id'] for event in self.visible(available_from, stream_id)}
        if not set(source_evidence_ids) <= known:
            raise ValueError('source evidence is unavailable')
        status = structural_status(code)
        kind = 'artifact'
        legal = 'not_applicable'
        trusted = status in ('NO_COMPLETE_CODE', 'COMPILE_ERROR')
        if not trusted:
            kind = 'runtime' if feedback.status == 'RUNTIME_ERROR' else 'functional'
            legal = 'verified' if feedback.public_cases else 'unknown'
            cases = feedback.to_dict()['public_cases']
            trusted = any(
                case.get('exception_class') in {'IndexError','KeyError','ValueError','TypeError','NameError','ZeroDivisionError','RecursionError','AttributeError','OverflowError','AssertionError','UnboundLocalError','ImportError','ModuleNotFoundError','EOFError'} if kind == 'runtime'
                else ('expected' in case and 'actual' in case and case['expected'] != case['actual'])
                for case in cases
            ) and feedback.status in ('RUNTIME_ERROR', 'WRONG_ANSWER')
        # Old labels alone remain signals. Infrastructure/checker errors never become rules.
        if not trusted or feedback.status in ('EVALUATOR_ERROR', 'TIME_LIMIT'):
            return None
        digest = hashlib.sha256(code.encode()).hexdigest()
        event = dict(stream_id=stream_id, task_id=task_id, family_id=family_id,
                     provenance_group_id=provenance_group_id or task_id, stage=stage,
                     candidate_sha256=digest, parent_sha256=parent_sha256,
                     observation_type=kind, finish_reason=generation_metadata({'finish_reason': finish_reason})['finish_reason'],
                     input_legality_status=legal, verifier_status=status if kind == 'artifact' else feedback.status,
                     root_cause_status='unknown', observed_at=observed_at,
                     validated_at=available_from, available_from=available_from, visibility='public',
                     source_evidence_ids=list(source_evidence_ids), repair_evidence_ids=[],
                     synthetic=bool(synthetic), validation_cost=validation_cost if validation_cost is not None else {'status':'not_recorded'})
        event['event_id'] = fingerprint(event)
        if any(r['payload'].get('event_id') == event['event_id'] for r in self.events.records()):
            return event
        self.artifacts.mkdir(parents=True, exist_ok=True)
        (self.artifacts / (digest + '.py')).write_text(code)
        self.events.append('FAILURE_FACT', event, available_from)
        return event


def public_check_outcome(raw):
    """Coverage is orthogonal to structural validity and private correctness."""
    feedback = checked_public_feedback(raw)
    count = raw.get('tests_run')
    if feedback.status == 'PUBLIC_PASS':
        return {'public_check_outcome':'passed','tests_run':count,'unavailable_reason':''}
    if (raw.get('visibility') == 'public' and type(count) is int and count > 0
            and feedback.status in ('WRONG_ANSWER','RUNTIME_ERROR','TIME_LIMIT')):
        return {'public_check_outcome':'failed','tests_run':count,'unavailable_reason':''}
    return {'public_check_outcome':'unavailable','tests_run':count if type(count) is int and count >= 0 else 0,
            'unavailable_reason':'checker_error' if feedback.status=='EVALUATOR_ERROR' else 'no_reliable_public_checks'}
