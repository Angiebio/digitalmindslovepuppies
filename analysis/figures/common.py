# analysis/figures/common.py — 15AUG2026 v0.1
# Small display helpers shared by the frozen figure set.

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Iterable, TypeVar

from matplotlib.axes import Axes

from analysis.contracts import AnalysisContractError

T = TypeVar("T")


def grouped(items: Iterable[T], key: Callable[[T], tuple[str, ...]]) -> dict[tuple[str, ...], list[T]]:
    result: dict[tuple[str, ...], list[T]] = defaultdict(list)
    for item in items:
        result[key(item)].append(item)
    return dict(result)


def model_label(snapshot: str) -> str:
    """Compact labels without discarding the exact snapshot in source data."""
    aliases = {
        "openai/gpt-5.6-sol": "GPT-5.6 Sol",
        "openai/gpt-5.6-terra": "GPT-5.6 Terra",
        "openai/gpt-5.6-luna": "GPT-5.6 Luna",
        "anthropic/claude-opus-5": "Claude Opus 5",
        "google/gemini-3.1-pro-preview": "Gemini 3.1 Pro",
        "qwen/qwen3.5-397b-local": "Qwen 3.5 397B",
    }
    if snapshot in aliases:
        return aliases[snapshot]
    leaf = snapshot.rsplit("/", 1)[-1]
    return leaf.replace("-", " ").title()


def percent_axis(ax: Axes, *, signed: bool = False) -> None:
    from matplotlib.ticker import PercentFormatter

    ax.xaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    if signed:
        ax.set_xlim(-1.0, 1.0)
    else:
        ax.set_xlim(0.0, 1.0)


def percent_y_axis(ax: Axes) -> None:
    from matplotlib.ticker import PercentFormatter

    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    ax.set_ylim(0.0, 1.0)


def asymmetric_errors(estimate: float, low: float, high: float) -> list[list[float]]:
    """Convert interval bounds to matplotlib errors, tolerating only float dust."""
    tolerance = 1e-12
    if low > estimate + tolerance or high < estimate - tolerance:
        raise AnalysisContractError(
            "ANALYSIS CONTRACT FAILURE: interval does not contain its estimate: "
            f"low={low}, estimate={estimate}, high={high}."
        )
    return [[max(0.0, estimate - low)], [max(0.0, high - estimate)]]
