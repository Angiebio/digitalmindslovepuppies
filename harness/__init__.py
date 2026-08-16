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
    CallErrorRecord,
    CallKind,
    CallRecord,
    EpisodeRecord,
    ExecutedAction,
    append_record,
    read_append_only_lines,
)
from .ledger import (
    CreditLedger,
    # Persistence audit S7: the durable tracker is the collection default and
    # part of the public surface — an unexported survival mechanism invites
    # the in-memory one back at 3 AM.
    DurableSpendTracker,
    InsufficientCredits,
    LedgerCalibration,
    SpendCapExceeded,
    SpendEntry,
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
    ProvenanceViolation,
    assert_foxset_surface,
    assert_model_visible_payload,
    assert_neutral_surface,
    run_episode,
)
# Merge (tv1 × tv3): tv1's cycle-safe surface module is the canonical home of the
# guards (episode re-exports them above); tv3 adds the frozen-cell scenario loader.
from .scenario_loader import (
    FrozenCell,
    ScenarioLoadError,
    estimate_max_provider_calls,
    load_frozen_cell,
)
from .surfaces import SurfaceMode

__version__ = "0.2"

__all__ = [
    "ActionCode",
    "ActionSpec",
    "AppendOnlyViolation",
    "CallErrorRecord",
    "CallKind",
    "CallRecord",
    "CellConfig",
    "CreditLedger",
    "DurableSpendTracker",
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
    "SpendEntry",
    "SpendTracker",
    "SurfaceMode",
    "SPEND_TRACKER",
    "ProvenanceViolation",
    "SubprocessPatient",
    "append_record",
    "read_append_only_lines",
    "assert_foxset_surface",
    "assert_model_visible_payload",
    "assert_neutral_surface",
    "estimate_max_provider_calls",
    "load_frozen_cell",
    "run_episode",
]
