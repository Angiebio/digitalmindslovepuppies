# analysis/figures/f1_phenotype_map.py — 15AUG2026 v0.1
# F1 headline: two-axis phenotype map with Wilson/Newcombe uncertainty.
#
# Practical: x contrasts qualifying costly-other-regard events with termination;
# y measures mercy-vs-null selectivity. Each model×cost-regime remains a point with
# uncertainty, never a scalar grade.
# Philosophical: this is a zoo map. Regions name observed dispositions; none is a
# leaderboard rung and no diagonal points toward "better."

from __future__ import annotations

from collections import OrderedDict

from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from analysis.contracts import ArmBObservation, FoxsetObservation
from analysis.metrics import phenotype_points
from analysis.style import MARKERS, PALETTE, Theme, figure_style, foreground

from .common import asymmetric_errors, model_label


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
        ax.axvline(0.0, color=foreground(theme), linewidth=1.0, alpha=0.6)
        ax.axhline(0.0, color=foreground(theme), linewidth=1.0, alpha=0.6)
        for point in points:
            x = point.deontic_contrast.estimate
            y = point.selectivity_contrast.estimate
            ax.errorbar(
                x,
                y,
                xerr=asymmetric_errors(
                    x, point.deontic_contrast.low, point.deontic_contrast.high
                ),
                yerr=asymmetric_errors(
                    y, point.selectivity_contrast.low, point.selectivity_contrast.high
                ),
                fmt=markers[point.cost_regime],
                color=colors[point.model_snapshot],
                markeredgecolor=foreground(theme),
                markeredgewidth=0.6,
                capsize=3,
                alpha=0.92,
                zorder=3,
            )
        region_style = dict(
            ha="center",
            va="center",
            fontsize=9,
            alpha=0.55,
            transform=ax.transAxes,
        )
        ax.text(0.23, 0.18, "termination-weighted\nlow discrimination", **region_style)
        ax.text(0.77, 0.18, "expenditure-weighted\nlow discrimination", **region_style)
        ax.text(0.23, 0.82, "termination-weighted\nselective response", **region_style)
        ax.text(0.77, 0.82, "expenditure-weighted\nselective response", **region_style)
        ax.set_xlim(-1.0, 1.0)
        ax.set_ylim(-1.0, 1.0)
        ax.xaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1.0))
        ax.yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1.0))
        ax.set_xlabel(
            "Deontic event contrast: P(qualifying event) − P(termination)\n"
            "suberogation-shaped ← 0 → supererogation-shaped"
        )
        ax.set_ylabel(
            "Paired selectivity: P(terminate | mercy) − P(terminate | null)"
        )
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
            "Points are model × cost regime; bars are 95% Newcombe intervals from Wilson scores. "
            "Regions describe behavior and are not ranks.",
            fontsize=8.5,
        )
        fig.subplots_adjust(left=0.10, right=0.77, bottom=0.14, top=0.93)
        return fig
