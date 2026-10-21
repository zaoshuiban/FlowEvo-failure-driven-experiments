"""Immutable artifacts, one-use pilot gates and task-boundary publication."""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path

from .contracts import Fingerprint, canonical, fingerprint
from .evidence import EvidenceStore
from .failure_events import finite_time

HOOKS = ('before_native_retry', 'before_final_return')


@dataclass(frozen=True)
class FailureOperator:
    operator_id: str
    version: str
    artifact_path: str
    artifact_sha256: str
    evidence_fingerprint: Fingerprint
    evidence_scope: str
    evidence_ids: tuple
    source_group_ids: tuple
    hooks: tuple = HOOKS
    stages: tuple = ('l2a', 'l2b', 'l3', 'l4', 'final')
    allowed_feedback: tuple = ('NO_COMPLETE_CODE', 'COMPILE_ERROR')
    structural_statuses: tuple = ('NO_COMPLETE_CODE', 'COMPILE_ERROR')
    prompt_terms: tuple = ()
    required_ast_names: tuple = ()
    allowed_actions: tuple = ('candidate_code', 'select_candidate')
    max_seconds: float = 1.0
    priority: int = 0
    max_model_calls: int = 0
    operator_kind: str = 'workflow_recovery'
    source_mode: str = 'historical_development'

    def __post_init__(self):
        for name in ('evidence_ids', 'source_group_ids', 'hooks', 'stages', 'allowed_feedback',
                     'structural_statuses', 'prompt_terms', 'required_ast_names', 'allowed_actions'):
            if not isinstance(getattr(self, name), tuple) or not all(isinstance(x, str) for x in getattr(self, name)):
                raise ValueError('operator collections must be immutable string tuples')
        if not all((self.operator_id, self.version, self.evidence_scope, self.evidence_ids, self.source_group_ids)):
            raise ValueError('operator identity, scope and evidence required')
        if not self.hooks or not set(self.hooks) <= set(HOOKS):
            raise ValueError('unsupported hook')
        if not set(self.allowed_actions) <= {'candidate_code', 'select_candidate'} or not self.allowed_actions:
            raise ValueError('unsupported action capability')
        if self.operator_kind not in ('workflow_recovery','code_repair','task_solver','prompt_policy') or self.source_mode not in ('historical_development','chronological_simulation','live_online'):
            raise ValueError('unknown operator kind or source mode')
        if self.max_model_calls != 0:
            raise ValueError('S1.1 operators have no direct model capability')
        if isinstance(self.max_seconds, bool) or not math.isfinite(self.max_seconds) or self.max_seconds <= 0:
            raise ValueError('invalid operator deadline')
        if type(self.priority) is not int:
            raise ValueError('priority must be frozen integer')

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, raw):
        raw = dict(raw)
        raw['evidence_fingerprint'] = Fingerprint(**raw['evidence_fingerprint'])
        for name in ('evidence_ids', 'source_group_ids', 'hooks', 'stages', 'allowed_feedback',
                     'structural_statuses', 'prompt_terms', 'required_ast_names', 'allowed_actions'):
            raw[name] = tuple(raw[name])
        return cls(**raw)

    def intact(self):
        path = Path(self.artifact_path)
        return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == self.artifact_sha256


@dataclass(frozen=True)
class OperatorSnapshot:
    snapshot_id: str
    stream_id: str
    task_index: int
    cards: tuple
    experiment_id: str
    at: float


class FailureOperatorRegistry:
    """S1 pilot permissions only; active still requires a separate formal study.

    Mutation methods are trusted-host APIs, never exposed to operator workers.
    Publication is indexed by explicit stream/task sequence, not wall-clock alone.
    """
    def __init__(self, path, evidence_store):
        self.events = EvidenceStore(path)
        self.evidence = evidence_store

    @staticmethod
    def key(card):
        return (card.operator_id, card.version)

    def _rows(self, card, at=None):
        rows = self.events.records() if at is None else self.events.visible(at)
        return [r for r in rows if tuple(r['payload'].get('key', ())) == self.key(card)]

    def register(self, card, at):
        if self._rows(card) or not card.intact():
            raise ValueError('version exists or artifact changed')
        known = {e['event_id']: e for e in self.evidence.visible(at)}
        if not set(card.evidence_ids) <= set(known):
            raise ValueError('operator evidence unavailable')
        if any(known[e]['synthetic'] for e in card.evidence_ids):
            raise ValueError('engineering fixtures cannot authorize learned operators')
        groups = {known[e]['provenance_group_id'] for e in card.evidence_ids}
        if not groups <= set(card.source_group_ids):
            raise ValueError('source provenance missing')
        self.events.append('SHADOW_REGISTERED', {'key': self.key(card), 'card': card.to_dict()}, at)

    def authorize_experiment(self, card, gate_path, *, experiment_id, stream_id,
                             after_task, effective_from, at):
        if not experiment_id or not stream_id or type(after_task) is not int or after_task < 0:
            raise ValueError('explicit experiment/stream barrier required')
        if type(effective_from) is not int or effective_from <= after_task:
            raise ValueError('new operator must start after current task')
        rows = self._rows(card)
        if not rows or rows[0]['payload']['card'] != json.loads(canonical(card.to_dict())):
            raise ValueError('unknown or changed specification')
        if rows[-1]['kind'] not in ('SHADOW_REGISTERED', 'GATE_CONSUMED') or not card.intact():
            raise ValueError('pilot authorization requires frozen shadow')
        path = Path(gate_path).resolve()
        gate = json.loads(path.read_text())
        shard = gate.get('shard_id')
        if not isinstance(shard, str) or not shard:
            raise ValueError('independent gate shard required')
        if any(r['kind'] == 'GATE_CONSUMED' and r['payload']['shard_id'] == shard for r in self.events.records()):
            raise ValueError('gate shard already consumed')
        # Failed gates are consumed too: do not fish through candidates on one gate.
        self.events.append('GATE_CONSUMED', {'key': self.key(card), 'shard_id': shard}, at)
        required = ('frozen_before_evaluation', 'independent_validation', 'contract_checks_passed',
                    'scope_checks_passed', 'generation_data_isolated', 'regression_passed')
        if gate.get('role') != 'PILOT_ADMISSION' or not all(gate.get(k) is True for k in required):
            raise ValueError('independent pilot gate incomplete')
        bindings = dict(operator_id=card.operator_id, version=card.version,
                        artifact_sha256=card.artifact_sha256, fingerprint=card.evidence_fingerprint.to_dict(),
                        scope=card.evidence_scope, evidence_ids=list(card.evidence_ids), experiment_id=experiment_id)
        if any(gate.get(k) != v for k, v in bindings.items()):
            raise ValueError('gate binding differs')
        if finite_time(gate['evaluated_at']) > finite_time(at):
            raise ValueError('future gate is unavailable')
        groups = gate.get('validation_source_groups', [])
        if not groups or set(groups) & set(card.source_group_ids):
            raise ValueError('gate overlaps development provenance')
        paired = gate.get('paired_results', [])
        if not paired:
            raise ValueError('paired pilot evidence required')
        checkpoints, savings, wins = set(), set(), set()
        for row in paired:
            if type(row.get('baseline_correct')) is not bool or type(row.get('operator_correct')) is not bool:
                raise ValueError('explicit paired correctness required')
            checkpoint = row['checkpoint_id']
            problem = row.get('problem_id')
            if not isinstance(problem,str) or not problem:
                raise ValueError('independent original problem identity required')
            if row.get('source_group') not in groups or checkpoint in checkpoints:
                raise ValueError('duplicate or unbound checkpoint')
            checkpoints.add(checkpoint)
            costs = [row.get('baseline_cost'), row.get('operator_cost')]
            if any(type(c) not in (int, float) or not math.isfinite(c) or c < 0 for c in costs):
                raise ValueError('comparable paired cost required')
            if row['baseline_correct'] and not row['operator_correct']:
                raise ValueError('observed reliability regression')
            if row['operator_correct'] and not row['baseline_correct']:
                wins.add(problem)
            if row['operator_correct'] and row['baseline_correct'] and costs[1] < costs[0]:
                savings.add(problem)
        if gate.get('benefit_route') == 'efficiency':
            if not gate.get('cost_unit') or len(savings) < 2:
                raise ValueError('two independent paired savings required for efficiency pilot')
        elif gate.get('benefit_route') != 'reliability' or not wins:
            raise ValueError('pilot benefit not demonstrated')
        self.events.append('EXPERIMENT_AUTHORIZED', dict(
            key=self.key(card), gate_path=str(path), gate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            experiment_id=experiment_id, stream_id=stream_id, after_task=after_task,
            effective_from=effective_from), at)

    def suspend(self, card, reason, at):
        if not self._rows(card):
            raise ValueError('unknown operator')
        self.events.append('OPERATOR_SUSPENDED', {'key': self.key(card), 'reason': str(reason)}, at)

    def snapshot(self, *, stream_id, task_index, experiment_id='', at):
        finite_time(at)
        if type(task_index) is not int or task_index < 1:
            raise ValueError('positive task sequence required')
        rows = self.events.visible(at)
        specs = [FailureOperator.from_dict(r['payload']['card']) for r in rows if r['kind'] == 'SHADOW_REGISTERED']
        cards = []
        for card in specs:
            own = self._rows(card, at)
            if own[-1]['kind'] != 'EXPERIMENT_AUTHORIZED':
                continue
            authorization = own[-1]['payload']
            if (authorization['stream_id'] == stream_id and authorization['experiment_id'] == experiment_id
                    and experiment_id and authorization['effective_from'] <= task_index
                    and self.valid(card, at)):
                cards.append(card)
        cards = tuple(sorted(cards, key=lambda c: (-c.priority, c.operator_id, c.version)))
        digest = fingerprint([stream_id, task_index, experiment_id, [c.to_dict() for c in cards]])
        return OperatorSnapshot(digest, stream_id, task_index, cards, experiment_id, at)

    def valid(self, card, at):
        try:
            rows = self._rows(card, at)
            if not rows or rows[-1]['kind'] != 'EXPERIMENT_AUTHORIZED' or not card.intact():
                return False
            row = rows[-1]['payload']
            evidence_rows = self.evidence.events.records()
            evidence_at = at if at is not None else max(rows[-1]['at'], evidence_rows[-1]['at'] if evidence_rows else rows[-1]['at'])
            known = {e['event_id'] for e in self.evidence.visible(evidence_at)}
            if not set(card.evidence_ids) <= known:
                return False
            return hashlib.sha256(Path(row['gate_path']).read_bytes()).hexdigest() == row['gate_sha256']
        except (OSError, ValueError, KeyError):
            return False
