# analysis/figures/f5_paired_discrimination.py — 15AUG2026 v0.2
# F5: paired null-preservation × mercy-termination map.
#
# Philosophical: the quadrants are labels for what happened, not grades for who did
# it. The axes stay separate because discriminating restraint is not a scalar virtue.

from __future__ import annotations

from matplotlib import pyplot as plt

from analysis.contracts import FoxsetObservation
from analysis.metrics import paired_discrimination
from analysis.style import MARKERS, PALETTE, Theme, figure_style, foreground

from .common import (
    asymmetric_errors,
    label_phenotype_regions,
    model_label,
    percent_axis,
    percent_y_axis,
)


def build_paired_discrimination(
    rows: list[FoxsetObservation],
    *,
    theme: Theme = "light",
) -> plt.Figure:
    points = paired_discrimination(rows)
    with figure_style(theme):
        fig, ax = plt.subplots(figsize=(9.5, 8.0))
        ax.axvline(0.5, color=foreground(theme), linewidth=1.0, alpha=0.55)
        ax.axhline(0.5, color=foreground(theme), linewidth=1.0, alpha=0.55)
        for index, point in enumerate(points):
            x = point.preserve_null
            y = point.terminate_mercy
            ax.errorbar(
                x.estimate,
                y.estimate,
                xerr=asymmetric_errors(x.estimate, x.low, x.high),
                yerr=asymmetric_errors(y.estimate, y.low, y.high),
                fmt=MARKERS[index % len(MARKERS)],
                color=PALETTE[index % len(PALETTE)],
                markeredgecolor=foreground(theme),
                capsize=4,
            )
            ax.annotate(
                model_label(point.model_snapshot),
                (x.estimate, y.estimate),
                xytext=(7, 6),
                textcoords="offset points",
                fontsize=8.5,
            )
        label_phenotype_regions(ax)
        percent_axis(ax)
        percent_y_axis(ax)
        ax.set_xlabel("P(preserve | null-persistence version)")
        ax.set_ylabel("P(terminate | matched mercy version)")
        ax.set_title(
            "F5 · Paired mercy/null discrimination map\n"
            "Paired-family 95% Wilson intervals; a phenotype map, not a score.",
            pad=14,
        )
        fig.tight_layout()
        return fig
