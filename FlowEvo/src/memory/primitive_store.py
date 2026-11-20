"""Persistent store for executable helper primitives."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.schemas import PrimitiveCard


class PrimitiveStore:
    """Persist, match, and update conservative executable primitives."""

    def __init__(
        self,
        file_path: str = "data/primitives/registry.json",
        primitives_root: str | None = None,
    ) -> None:
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.primitives_root = Path(primitives_root) if primitives_root is not None else self.file_path.parent
        self.primitives_root.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _priority(self, card: PrimitiveCard) -> float:
        return float(card.support_count) + float(card.success_count) + float(card.utility) - float(card.failure_count)

    def _sort_key(self, card: PrimitiveCard) -> tuple[float, str]:
        return (-self._priority(card), str(card.primitive_id))

    def _normalize(self, card: PrimitiveCard) -> PrimitiveCard:
        if not card.updated_at:
            card.updated_at = self._now()
        return card

    def _write(self, cards: list[PrimitiveCard]) -> None:
        payload = [self._normalize(card).model_dump(mode="json") for card in sorted(cards, key=self._sort_key)]
        self.file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_all(self) -> list[PrimitiveCard]:
        data = json.loads(self.file_path.read_text(encoding="utf-8"))
        return [self._normalize(PrimitiveCard.model_validate(item)) for item in data]

    def get(self, primitive_id: str) -> PrimitiveCard | None:
        for card in self.list_all():
            if card.primitive_id == primitive_id:
                return card
        return None

    def upsert(self, card: PrimitiveCard) -> None:
        table = {item.primitive_id: item for item in self.list_all()}
        table[card.primitive_id] = self._normalize(card)
        self._write(list(table.values()))

    def save_code(self, primitive_id: str, code: str) -> Path:
        path = self.primitives_root / f"{primitive_id}.py"
        path.write_text(code, encoding="utf-8")
        return path

    def observe_candidate(self, card: PrimitiveCard, code: str) -> PrimitiveCard:
        current = self.get(card.primitive_id)
        now = self._now()
        verified = card.validation_status == "source_verified_dependency_checked"
        if verified:
            from failure_evo.skill_runtime import sha
            if sha(code) != card.source_sha256:
                raise ValueError("PRIMITIVE_SOURCE_HASH_MISMATCH")
        if current is not None and current.validation_status != card.validation_status:
            raise ValueError("PRIMITIVE_VALIDATION_MODE_CONFLICT")
        if current is None:
            current = card.model_copy(deep=True)
            if verified:
                current.independent_source_ids = list(dict.fromkeys(card.independent_source_ids or card.source_trace_ids))
                current.support_count = len(current.independent_source_ids)
            else:
                current.support_count = max(1, int(current.support_count or 1))
            current.status = "active" if current.support_count >= 2 else "draft"
        else:
            current.name = card.name or current.name
            current.description = card.description or current.description
            current.signature = card.signature or current.signature
            current.helper_name = card.helper_name or current.helper_name
            current.target_entry_point = card.target_entry_point or current.target_entry_point
            if verified:
                sources = set(current.independent_source_ids or current.source_trace_ids)
                sources.update(card.independent_source_ids or card.source_trace_ids)
                current.independent_source_ids = sorted(sources)
                current.support_count = len(sources)
                if current.source_sha256 and current.source_sha256 != card.source_sha256:
                    raise ValueError("PRIMITIVE_HASH_DRIFT")
            else:
                current.support_count += max(1, int(card.support_count or 1))
            current.utility = max(float(current.utility), float(card.utility))
            for trace_id in card.source_trace_ids:
                if trace_id not in current.source_trace_ids:
                    current.source_trace_ids.append(trace_id)
            for skill_id in card.source_skill_ids:
                if skill_id not in current.source_skill_ids:
                    current.source_skill_ids.append(skill_id)
            if current.status != "suppressed" and current.support_count >= 2:
                current.status = "active"
        current.updated_at = now
        current.code_path = str(self.save_code(current.primitive_id, code))
        self.upsert(current)
        return self.get(current.primitive_id) or current

    def observe_support(self, primitive_id, evidence):
        current = self.get(primitive_id)
        if current is None or current.source_sha256 != evidence.get('sha256'):
            raise ValueError('SUPPORT_VERSION_MISMATCH')
        source = evidence.get('source_lineage_id')
        if not source or not evidence.get('passed') or not evidence.get('return_use_verified'):
            raise ValueError('UNVERIFIED_SUPPORT')
        if not any(e.get('event') == 'returned' and e.get('sha256') == current.source_sha256
                   for e in evidence.get('actual_calls', [])):
            raise ValueError('SUPPORT_REQUIRES_REAL_CALL')
        if source in current.independent_source_ids:
            return current
        current.independent_source_ids.append(source)
        current.source_trace_ids.append('support:' + evidence['program_sha256'])
        current.support_evidence.append(evidence)
        updated = self.observe_candidate(current, Path(current.code_path).read_text())
        updated.support_evidence = current.support_evidence
        self.upsert(updated)
        return updated

    def match(self, benchmark: str, task_pattern: str, limit: int = 2) -> list[PrimitiveCard]:
        cards = [
            card
            for card in self.list_all()
            if card.status == "active"
            and card.benchmark == benchmark
            and card.task_pattern == task_pattern
        ]
        cards.sort(key=self._sort_key)
        return cards[:limit]

    def record_feedback(self, primitive_ids: list[str], success: bool) -> list[PrimitiveCard]:
        table = {item.primitive_id: item for item in self.list_all()}
        updated: list[PrimitiveCard] = []
        for primitive_id in primitive_ids:
            current = table.get(primitive_id)
            if current is None:
                continue
            if success:
                current.success_count += 1
                current.utility = round(min(1.0, float(current.utility) + 0.1), 4)
                if current.status != "suppressed" and current.support_count >= 2:
                    current.status = "active"
            else:
                current.failure_count += 1
                current.utility = round(max(0.0, float(current.utility) - 0.15), 4)
                if current.failure_count >= 2 and current.failure_count >= current.success_count:
                    current.status = "suppressed"
            current.last_used_at = self._now()
            current.updated_at = current.last_used_at
            table[current.primitive_id] = current
            updated.append(current.model_copy(deep=True))
        self._write(list(table.values()))
        updated.sort(key=self._sort_key)
        return updated

    def status_counts(self) -> dict[str, int]:
        counts = {"draft": 0, "active": 0, "suppressed": 0}
        for card in self.list_all():
            if card.status in counts:
                counts[card.status] += 1
        return counts

    def top_for_audit(self, top_k: int = 3) -> list[PrimitiveCard]:
        cards = [card for card in self.list_all() if card.status in {"active", "suppressed"}]
        cards.sort(key=self._sort_key)
        return cards[:top_k]
