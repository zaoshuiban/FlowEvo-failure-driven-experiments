"""Evidence-gated repair adapter. S1 has no network/model client dependency."""
from .contracts import PublicTaskView, PublicFeedback, Fingerprint, OperatorCard
from .runtime import Budget, Controller, Router, SandboxOperatorRunner
from .evidence import EvidenceStore, MechanismStore
from .admission import AdmissionRegistry
