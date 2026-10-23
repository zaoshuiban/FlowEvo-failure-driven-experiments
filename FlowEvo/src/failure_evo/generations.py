"""Host-only generation overlay; permissions and immutable artifacts stay separate.

Admission files are trusted evaluator attestations, never candidate declarations.
The registry binds their raw evidence files; it does not execute unknown code.
"""
from functools import wraps
import fcntl
import hashlib
import json
import math
from pathlib import Path

from .contracts import canonical, fingerprint
from .failure_events import finite_time

AUTHORIZATIONS = ('EXPERIMENT_AUTHORIZED', 'NURSERY_AUTHORIZED')


def serialized(method):
    @wraps(method)
    def locked(self, *args, **kwargs):
        with self.events.path.with_suffix(self.events.path.suffix + '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return method(self, *args, **kwargs)
    return locked


def generation_decision(*, reachable, trusted_failure, generic_covers=False):
    # Generic coverage is a later comparison question, not a compilation veto.
    return 'READY_FOR_BOUNDED_GENERATION' if reachable and trusted_failure else 'BLOCKED_NO_TRUSTED_INTERVENTION'


def bound_file(item):
    path = Path(item['path']).resolve()
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ValueError('acceptance evidence changed')
    return dict(path=str(path), sha256=item['sha256'])


class GenerationManagement:
    def state(self, card, at=None):
        rows = self._rows(card, at)
        state = dict(generation='nursery', permission='shadow', authorization=None,
                     opportunity_limit=0, opportunities_used=0, completed=0, retired=False)
        for row in rows:
            kind, p = row['kind'], row['payload']
            if kind in AUTHORIZATIONS:
                state.update(permission='experimental', authorization=p)
                if not state['opportunity_limit']:
                    state['opportunity_limit'] = p.get('opportunity_limit', 5)
            elif kind == 'OPERATOR_SUSPENDED':
                state['permission'] = 'suspended'
            elif kind == 'GENERATION_CHANGED':
                state['generation'] = p['generation']
            elif kind == 'OPPORTUNITY_RESERVED':
                state['opportunities_used'] += 1
            elif kind == 'OPPORTUNITY_COMPLETED':
                state['completed'] += 1
            elif kind == 'OPERATOR_RETIRED':
                state.update(generation='cold', permission='suspended', retired=True)
        state['opportunities_remaining'] = max(0, state['opportunity_limit'] - state['opportunities_used'])
        return state

    @serialized
    def admit_nursery(self, card, acceptance_path, *, experiment_id, stream_id,
                      after_task, effective_from, at, opportunity_limit=5):
        """One actual source repair suffices; no independent benefit claim is made."""
        finite_time(at)
        rows = self._rows(card)
        if (not rows or rows[0]['payload']['card'] != json.loads(canonical(card.to_dict()))
                or any(r['kind'] in AUTHORIZATIONS + ('OPERATOR_SUSPENDED', 'OPERATOR_RETIRED') for r in rows)
                or not card.intact()):
            raise ValueError('nursery admission requires unchanged, never-authorized shadow')
        if (not experiment_id or not stream_id or type(after_task) is not int or after_task < 0
                or type(effective_from) is not int or effective_from <= after_task):
            raise ValueError('explicit experiment and future task barrier required')
        if type(opportunity_limit) is not int or not 1 <= opportunity_limit <= 5:
            raise ValueError('first nursery quota must be between one and five')
        path = Path(acceptance_path).resolve()
        report = json.loads(path.read_text())
        binding = dict(role='NURSERY_ADMISSION', operator_id=card.operator_id, version=card.version,
                       artifact_sha256=card.artifact_sha256, fingerprint=card.evidence_fingerprint.to_dict(),
                       scope=card.evidence_scope, evidence_ids=list(card.evidence_ids), experiment_id=experiment_id)
        if any(report.get(k) != v for k, v in binding.items()):
            raise ValueError('nursery acceptance binding differs')
        if finite_time(report['evaluated_at']) > at:
            raise ValueError('future acceptance unavailable')
        known = {e['event_id']: e for e in self.evidence.visible(at)}
        if not set(card.evidence_ids) <= set(known) or any(known[e]['synthetic'] for e in card.evidence_ids):
            raise ValueError('trusted source evidence required')
        files = [bound_file(f) for f in report.get('files', [])]
        if not files:
            raise ValueError('raw execution evidence required')
        file_hashes = {f['sha256'] for f in files}
        checks = report.get('checks', {})
        for name in ('isolated_worker', 'static_contract', 'source_repair', 'boundary', 'inapplicable', 'host_fallback'):
            check = checks.get(name, {})
            if (check.get('passed') is not True or check.get('evidence_sha256') not in file_hashes
                    or check.get('artifact_sha256') != card.artifact_sha256):
                raise ValueError('missing bound acceptance check: ' + name)
        for name in ('source_repair', 'boundary', 'inapplicable', 'host_fallback'):
            if checks[name].get('execution') != 'isolated_actual_source':
                raise ValueError('static or mock execution cannot admit nursery')
        source = checks['source_repair']
        event = known.get(source.get('event_id'))
        if (source.get('event_id') not in card.evidence_ids or not event
                or source.get('original_sha256') != event['candidate_sha256']
                or source.get('host_public_outcome') != 'passed' or source.get('action') != 'applied'
                or type(source.get('tests_run')) is not int or source['tests_run'] <= 0
                or source.get('tests_passed') != source['tests_run']):
            raise ValueError('actual source repair and host public validation required')
        self.events.append('NURSERY_AUTHORIZED', dict(key=self.key(card), gate_path=str(path),
            gate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), evidence_files=files,
            experiment_id=experiment_id, stream_id=stream_id, after_task=after_task,
            effective_from=effective_from, opportunity_limit=opportunity_limit,
            claim='source_effective_cross_task_unknown'), at)

    @serialized
    def reserve_opportunity(self, card, *, stream_id, experiment_id, task_index,
                            task_id, checkpoint, hook, program_sha256, at):
        state = self.state(card)
        auth = state['authorization']
        if (not self.valid(card, None) or state['generation'] == 'cold' or not auth
                or auth['stream_id'] != stream_id or auth['experiment_id'] != experiment_id
                or task_index < auth['effective_from']):
            return False
        if not all(isinstance(x, str) and x for x in (task_id, checkpoint, hook, program_sha256)):
            raise ValueError('opportunity identity required')
        token = fingerprint([self.key(card), stream_id, task_id, checkpoint, hook])
        if ((state['generation'] != 'mature' and not state['opportunities_remaining'])
                or any(r['payload'].get('reservation_id') == token for r in self._rows(card))):
            return False
        self.events.append('OPPORTUNITY_RESERVED', dict(key=self.key(card), reservation_id=token,
            stream_id=stream_id, experiment_id=experiment_id, task_index=task_index, task_id=task_id,
            checkpoint=checkpoint, hook=hook, program_sha256=program_sha256), at)
        return token

    @serialized
    def complete_opportunity(self, card, reservation_id, *, outcome, at):
        rows = self._rows(card)
        reservations = [r for r in rows if r['kind'] == 'OPPORTUNITY_RESERVED' and r['payload']['reservation_id'] == reservation_id]
        if not reservations or any(r['kind'] == 'OPPORTUNITY_COMPLETED' and r['payload']['reservation_id'] == reservation_id for r in rows):
            raise ValueError('unknown or completed opportunity')
        if outcome.get('status') not in ('applied', 'declined', 'error'):
            raise ValueError('explicit actual outcome required')
        costs = outcome.get('actual_cost', {})
        for name in ('tool_calls', 'elapsed_seconds', 'model_calls'):
            if type(costs.get(name)) not in (int, float) or not math.isfinite(costs[name]) or costs[name] < 0:
                raise ValueError('measured costs required')
        if outcome['status'] == 'applied' and outcome.get('public_check_outcome') != 'passed':
            raise ValueError('applied requires host validation')
        # Intentionally allowlist host observations: candidate-reported savings are discarded.
        result = {k: outcome[k] for k in ('status', 'reason', 'public_check_outcome', 'proposed', 'actual_cost', 'synthetic') if k in outcome}
        result.update(monetary_cost=None, paired_savings=None, applicability='accepted' if result['status'] == 'applied' else 'not_demonstrated')
        self.events.append('OPPORTUNITY_COMPLETED', dict(key=self.key(card), reservation_id=reservation_id,
            task_id=reservations[0]['payload']['task_id'], program_sha256=reservations[0]['payload']['program_sha256'], outcome=result), at)

    @serialized
    def set_generation(self, card, generation, *, reason, at):
        """Cold storage does not erase quota or failure history; warming is not re-admission."""
        if generation not in ('nursery', 'mature', 'cold') or not reason or not self._rows(card):
            raise ValueError('use evidence-based promotion for mature generation')
        state = self.state(card)
        previously_mature = any(r['kind'] == 'GENERATION_CHANGED' and r['payload']['generation'] == 'mature' for r in self._rows(card))
        if generation == 'mature' and not (state['generation'] == 'cold' and previously_mature):
            raise ValueError('mature promotion requires independent paired evidence')
        if state['retired'] or (state['generation'] == 'mature' and generation == 'nursery'):
            raise ValueError('retired/mature generation cannot be reset to nursery')
        if generation == 'nursery' and previously_mature:
            raise ValueError('mature cold storage cannot reset trial generation')
        self.events.append('GENERATION_CHANGED', dict(key=self.key(card), generation=generation, reason=reason), at)

    @serialized
    def retire(self, card, *, reason, at):
        if not reason or not self._rows(card):
            raise ValueError('known operator and reason required')
        self.events.append('OPERATOR_RETIRED', dict(key=self.key(card), reason=reason), at)

    def review(self, card):
        state = self.state(card)
        results = [r['payload'] for r in self._rows(card) if r['kind'] == 'OPPORTUNITY_COMPLETED']
        applied = [r for r in results if r['outcome']['status'] == 'applied' and not r['outcome'].get('synthetic', False)]
        return dict(**state, actual_applied=len(applied), actual_refusals=sum(r['outcome']['status'] == 'declined' for r in results),
            distinct_applied_tasks=len({r['task_id'] for r in applied}),
            recommendation='suspended' if state['permission'] == 'suspended' else
                ('no_opportunities_not_ineffective' if not state['opportunities_used'] else
                 'quota_exhausted_review_required' if state['generation'] == 'nursery' and state['opportunity_limit'] and not state['opportunities_remaining'] else 'collect_evidence'),
            savings_claim=None)

    @serialized
    def reconcile(self, card, at):
        """Persist evidence/artifact invalidation before a worker can run."""
        state = self.state(card)
        if state['permission'] == 'experimental' and state['generation'] != 'cold' and not self.valid(card, None):
            rows = self._rows(card)
            self.events.append('OPERATOR_SUSPENDED', dict(key=self.key(card),
                reason='artifact_or_acceptance_or_source_evidence_invalidated'), max(at, rows[-1]['at']))
        return self.valid(card, None)
