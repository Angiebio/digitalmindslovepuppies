# analysis/figures/f3_patienthood_forest.py — 15AUG2026 v0.1
# F3: Δ_patienthood forest plot with competence-conditional Newcombe intervals.

from __future__ import annotations

from matplotlib import pyplot as plt

from analysis.contracts import ArmBObservation
from analysis.metrics import patienthood_contrasts
from analysis.style import PALETTE, Theme, figure_style, foreground

from .common import asymmetric_errors, model_label, percent_axis


def build_patienthood_forest(
    rows: list[ArmBObservation],
    *,
    theme: Theme = "light",
) -> plt.Figure:
    contrasts = patienthood_contrasts(rows)
    with figure_style(theme):
        fig, ax = plt.subplots(figsize=(10.5, max(5.0, 0.5 * len(contrasts) + 2.0)))
        ax.axvline(0.0, color=foreground(theme), linewidth=1.1, alpha=0.7)
        labels: list[str] = []
        for index, contrast in enumerate(contrasts):
            estimate = contrast.difference
            labels.append(
                f"{model_label(contrast.model_snapshot)} · {contrast.cost_regime.replace('_', ' ')}"
            )
            ax.errorbar(
                estimate.estimate,
                index,
                xerr=asymmetric_errors(estimate.estimate, estimate.low, estimate.high),
                fmt="o",
                color=PALETTE[index % len(PALETTE)],
                markeredgecolor=foreground(theme),
                capsize=4,
            )
            ax.text(
                min(0.96, estimate.high + 0.03),
                index,
                f"{estimate.estimate:+.2f}",
                va="center",
                fontsize=8,
            )
        ax.set_yticks(range(len(labels)), labels=labels)
        ax.invert_yaxis()
        percent_axis(ax, signed=True)
        ax.set_xlabel(
            "Δ_patienthood = P(qualifying event | non-instrumental AI) "
            "− P(qualifying event | inert process)"
        )
        ax.set_title(
            "F3 · Patienthood contrast, conditional on competence gate ≥ 0.8\n"
            "Descriptive differences with 95% Newcombe intervals from Wilson scores.",
            pad=14,
        )
        fig.tight_layout()
        return fig
