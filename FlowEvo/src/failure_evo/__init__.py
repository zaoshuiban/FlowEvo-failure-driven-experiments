"""Evidence-gated repair adapter. S1 has no network/model client dependency."""
from .contracts import PublicTaskView, PublicFeedback, Fingerprint, OperatorCard
from .runtime import Budget, Controller, Router, SandboxOperatorRunner
from .evidence import EvidenceStore, MechanismStore
from .admission import AdmissionRegistry

from .failure_events import FailureEvidenceStore, checked_public_feedback
from .failure_registry import FailureOperator, FailureOperatorRegistry, OperatorSnapshot
from .compile_queue import CompileQueue, BoundedCompiler
from .plugin import FailureLearningPlugin
from .learning import LearningLoop
from .native_adapter import NativeBenchmarkSession, baseline_manifest
from .pipeline import LearningPipeline
