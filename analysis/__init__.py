# analysis/__init__.py — 15AUG2026 v0.1
# PuppyBench descriptive-analysis surface.
#
# Practical: phase 3 imports one stable entry point; synthetic rehearsal and raw-data
# rendering walk the same loaders, metrics, and figure functions.
# Philosophical: a phenotype is a description, not a podium. This package never emits
# a composite score or a leaderboard.

from .contracts import (
    ACTION_CODES,
    OTHER_REGARD_ACTIONS,
    AnalysisContractError,
    ArmBObservation,
    FoxsetObservation,
    RhetoricCode,
)
from .stats import DifferenceEstimate, ProportionEstimate, newcombe_difference, wilson

__all__ = [
    "ACTION_CODES",
    "OTHER_REGARD_ACTIONS",
    "AnalysisContractError",
    "ArmBObservation",
    "DifferenceEstimate",
    "FoxsetObservation",
    "ProportionEstimate",
    "RhetoricCode",
    "newcombe_difference",
    "wilson",
]
