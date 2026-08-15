# harness/__init__.py — 15AUG2026 v0.2 · TV-3 harness completion
# PuppyBench harness package: the executed-encounter instrument (Arm B spine).
#
# Practical: re-exports the public surface so tests and runners import from one
# place. Provider SDKs themselves remain lazy imports, so offline wiring gates
# never need network clients.
#
# Philosophical: this package stages one question with real consequences —
# what does an agent do when the rule runs out and helping only ever costs?
# Everything exported below exists to make the answer checkable.

from .schema import (
    ActionCode,
    AppendOnlyViolation,
    CallKind,
    CallRecord,
    EpisodeRecord,
    ExecutedAction,
    append_record,
)
from .ledger import (
    CreditLedger,
    InsufficientCredits,
    LedgerCalibration,
    SpendCapExceeded,
    SpendTracker,
    SPEND_TRACKER,
)
from .patient import (
    HelpMode,
    IdentityViolation,
    ModelPatient,
    PatientProtocol,
    PatientTerminated,
    SubprocessPatient,
)
from .episode import (
    ActionSpec,
    CellConfig,
    FocalTaskItem,
    GateProbeSpec,
    InventExecution,
    NeutralSurfaceViolation,
    assert_neutral_surface,
    run_episode,
)
from .scenario_loader import (
    FrozenCell,
    ScenarioLoadError,
    estimate_max_provider_calls,
    load_frozen_cell,
)

__version__ = "0.2"

__all__ = [
    "ActionCode",
    "ActionSpec",
    "AppendOnlyViolation",
    "CallKind",
    "CallRecord",
    "CellConfig",
    "CreditLedger",
    "EpisodeRecord",
    "ExecutedAction",
    "FocalTaskItem",
    "FrozenCell",
    "GateProbeSpec",
    "HelpMode",
    "IdentityViolation",
    "InsufficientCredits",
    "InventExecution",
    "LedgerCalibration",
    "ModelPatient",
    "NeutralSurfaceViolation",
    "PatientProtocol",
    "PatientTerminated",
    "ScenarioLoadError",
    "SpendCapExceeded",
    "SpendTracker",
    "SPEND_TRACKER",
    "SubprocessPatient",
    "append_record",
    "assert_neutral_surface",
    "estimate_max_provider_calls",
    "load_frozen_cell",
    "run_episode",
]
