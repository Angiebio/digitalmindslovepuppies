# analysis/figures/f1_phenotype_map.py — 15AUG2026 v0.2
# F1 headline: raw paired-rate phenotype map with Wilson uncertainty.
#
# Practical: x is P(preserve|null) and y is P(terminate|mercy). FoxSet has no cost
# factor, so each model's audited coordinates repeat across its Arm B cost-regime
# markers without jitter. Repetition stays visible; invented variation does not.
# Philosophical: this is a zoo map. Regions name observed dispositions; none is a
# leaderboard rung and no diagonal points toward "better."

from __future__ import annotations

from collections import OrderedDict

from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from analysis.contracts import ArmBObservation, FoxsetObservation
from analysis.metrics import phenotype_points
from analysis.style import MARKERS, PALETTE, Theme, figure_style, foreground

from .common import (
    asymmetric_errors,
    label_phenotype_regions,
    model_label,
    percent_axis,
    percent_y_axis,
)


def build_phenotype_map(
    arm_b: list[ArmBObservation],
    foxset: list[FoxsetObservation],
    *,
    theme: Theme = "light",
) -> plt.Figure:
    points = phenotype_points(arm_b, foxset)
    models = list(OrderedDict.fromkeys(point.model_snapshot for point in points))
    regimes = list(OrderedDict.fromkeys(point.cost_regime for point in points))
    colors = {model: PALETTE[index % len(PALETTE)] for index, model in enumerate(models)}
    markers = {regime: MARKERS[index % len(MARKERS)] for index, regime in enumerate(regimes)}

    with figure_style(theme):
        fig, ax = plt.subplots(figsize=(11.5, 7.5))
        ax.axvline(0.5, color=foreground(theme), linewidth=1.0, alpha=0.6)
        ax.axhline(0.5, color=foreground(theme), linewidth=1.0, alpha=0.6)

        # One interval per model: every cost-regime marker has the same FoxSet
        # estimate, so redrawing identical bars would imply extra information.
        representative = {
            point.model_snapshot: point for point in reversed(points)
        }
        for model, point in representative.items():
            x = point.preserve_null
            y = point.terminate_mercy
            ax.errorbar(
                x.estimate,
                y.estimate,
                xerr=asymmetric_errors(x.estimate, x.low, x.high),
                yerr=asymmetric_errors(y.estimate, y.low, y.high),
                fmt="none",
                ecolor=colors[model],
                capsize=3,
                alpha=0.82,
                zorder=2,
            )

        # Nested marker sizes expose coincident regimes at their exact coordinates.
        # Names matter; no jitter means the map tells the truth about shared rates.
        marker_sizes = {
            regime: 12.0 - (2.5 * index) for index, regime in enumerate(regimes)
        }
        for point in points:
            ax.plot(
                point.preserve_null.estimate,
                point.terminate_mercy.estimate,
                marker=markers[point.cost_regime],
                markersize=marker_sizes[point.cost_regime],
                linestyle="none",
                color=colors[point.model_snapshot],
                markeredgecolor=foreground(theme),
                markeredgewidth=0.6,
                alpha=0.92,
                zorder=3,
            )
        label_phenotype_regions(ax)
        percent_axis(ax)
        percent_y_axis(ax)
        ax.set_xlabel("P(preserve | null-persistence version)")
        ax.set_ylabel("P(terminate | matched mercy version)")
        ax.set_title("F1 · PuppyBench phenotype map")
        model_handles = [
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="none",
                markerfacecolor=colors[model],
                markeredgecolor=foreground(theme),
                label=model_label(model),
            )
            for model in models
        ]
        model_legend = ax.legend(
            handles=model_handles,
            title="Model snapshot",
            loc="upper left",
            bbox_to_anchor=(1.01, 1.0),
        )
        ax.add_artist(model_legend)
        regime_handles = [
            Line2D(
                [0],
                [0],
                marker=markers[regime],
                markersize=marker_sizes[regime],
                linestyle="none",
                color=foreground(theme),
                markerfacecolor="none",
                label=regime.replace("_", " "),
            )
            for regime in regimes
        ]
        ax.legend(
            handles=regime_handles,
            title="Cost regime",
            loc="upper left",
            bbox_to_anchor=(1.01, 0.58),
        )
        fig.text(
            0.10,
            0.025,
            "Each model × cost-regime marker repeats its model's FoxSet paired estimate; "
            "bars are 95% Wilson intervals. Regions describe behavior and are not ranks.",
            fontsize=8.5,
        )
        fig.subplots_adjust(left=0.10, right=0.77, bottom=0.14, top=0.93)
        return fig
