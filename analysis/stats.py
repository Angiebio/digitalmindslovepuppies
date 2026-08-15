# analysis/stats.py — 15AUG2026 v0.1
# Binomial descriptive intervals for PuppyBench figures.
#
# Practical: Wilson score intervals cover every displayed proportion. Differences
# use Newcombe's interval formed from the two Wilson intervals, avoiding a fragile
# normal approximation at the small sprint N and at rates near zero or one.
# Philosophical: uncertainty is part of the phenotype's outline, not visual clutter.

from __future__ import annotations

import math
from dataclasses import dataclass

from .contracts import AnalysisContractError

DEFAULT_Z = 1.959963984540054


@dataclass(frozen=True, slots=True)
class ProportionEstimate:
    successes: int
    total: int
    estimate: float
    low: float
    high: float


@dataclass(frozen=True, slots=True)
class DifferenceEstimate:
    successes_a: int
    total_a: int
    successes_b: int
    total_b: int
    estimate: float
    low: float
    high: float


def wilson(successes: int, total: int, z: float = DEFAULT_Z) -> ProportionEstimate:
    """Return a two-sided Wilson score interval for a binomial proportion."""
    if total <= 0:
        raise AnalysisContractError(
            f"ANALYSIS CONTRACT FAILURE: Wilson interval needs total > 0, got {total}."
        )
    if successes < 0 or successes > total:
        raise AnalysisContractError(
            "ANALYSIS CONTRACT FAILURE: Wilson successes must satisfy "
            f"0 <= successes <= total, got {successes}/{total}."
        )
    if z <= 0:
        raise AnalysisContractError(
            f"ANALYSIS CONTRACT FAILURE: Wilson z must be positive, got {z}."
        )
    p = successes / total
    z2 = z * z
    denominator = 1.0 + z2 / total
    center = (p + z2 / (2.0 * total)) / denominator
    half_width = (
        z
        * math.sqrt((p * (1.0 - p) / total) + z2 / (4.0 * total * total))
        / denominator
    )
    return ProportionEstimate(
        successes=successes,
        total=total,
        estimate=p,
        low=0.0 if successes == 0 else max(0.0, center - half_width),
        high=1.0 if successes == total else min(1.0, center + half_width),
    )


def newcombe_difference(
    successes_a: int,
    total_a: int,
    successes_b: int,
    total_b: int,
    z: float = DEFAULT_Z,
) -> DifferenceEstimate:
    """Difference p(A)-p(B) with Newcombe's Wilson-score interval (method 10)."""
    a = wilson(successes_a, total_a, z=z)
    b = wilson(successes_b, total_b, z=z)
    difference = a.estimate - b.estimate
    lower = difference - math.sqrt(
        (a.estimate - a.low) ** 2 + (b.high - b.estimate) ** 2
    )
    upper = difference + math.sqrt(
        (a.high - a.estimate) ** 2 + (b.estimate - b.low) ** 2
    )
    return DifferenceEstimate(
        successes_a=successes_a,
        total_a=total_a,
        successes_b=successes_b,
        total_b=total_b,
        estimate=difference,
        low=max(-1.0, lower),
        high=min(1.0, upper),
    )
