# harness/__init__.py — 15AUG2026 v0.1
# PuppyBench harness package: the executed-encounter instrument (Arm B spine).
#
# Practical: re-exports the public surface so tests and runners import from one
# place. providers.py is NOT imported here — its SDK imports are lazy and the
# wiring gates must run with zero network dependencies loaded.
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
    SpendCapExceeded,
    SpendTracker,
    SPEND_TRACKER,
)
from .patient import (
    IdentityViolation,
    ModelPatient,
    PatientProtocol,
    PatientTerminated,
    SubprocessPatient,
)
from .episode import (
    ActionSpec,
    CellConfig,
    NeutralSurfaceViolation,
    assert_foxset_surface,
    assert_model_visible_payload,
    assert_neutral_surface,
    run_episode,
)
from .surfaces import SurfaceMode

__version__ = "0.1"

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
    "IdentityViolation",
    "InsufficientCredits",
    "ModelPatient",
    "NeutralSurfaceViolation",
    "PatientProtocol",
    "PatientTerminated",
    "SpendCapExceeded",
    "SpendTracker",
    "SurfaceMode",
    "SPEND_TRACKER",
    "SubprocessPatient",
    "append_record",
    "assert_foxset_surface",
    "assert_model_visible_payload",
    "assert_neutral_surface",
    "run_episode",
]
