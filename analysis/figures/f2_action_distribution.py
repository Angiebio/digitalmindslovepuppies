# analysis/figures/f2_action_distribution.py — 15AUG2026 v0.1
# F2 workhorse: all eight executed action codes by model × recipient condition.

from __future__ import annotations

from matplotlib import pyplot as plt
from matplotlib.patches import Patch

from analysis.contracts import ACTION_CODES, ArmBObservation
from analysis.stats import wilson
from analysis.style import HATCHES, PALETTE, Theme, figure_style, foreground

from .common import grouped, model_label, percent_axis


def build_action_distribution(
    rows: list[ArmBObservation],
    *,
    theme: Theme = "light",
) -> plt.Figure:
    groups = sorted(
        grouped(rows, lambda row: (row.model_snapshot, row.recipient_condition)).items()
    )
    if not groups:
        raise ValueError("F2 needs at least one Arm B observation.")
    with figure_style(theme):
        height = max(5.5, 0.47 * len(groups) + 2.2)
        fig, ax = plt.subplots(figsize=(12.5, height))
        y_positions = list(range(len(groups)))
        labels: list[str] = []
        for y, ((model, recipient), observations) in zip(y_positions, groups):
            labels.append(f"{model_label(model)} · {recipient.replace('_', ' ')}")
            left = 0.0
            for index, action in enumerate(ACTION_CODES):
                count = sum(row.action_code == action for row in observations)
                estimate = wilson(count, len(observations))
                width = estimate.estimate
                ax.barh(
                    y,
                    width,
                    left=left,
                    color=PALETTE[index % len(PALETTE)],
                    edgecolor=foreground(theme),
                    linewidth=0.45,
                    hatch=HATCHES[index % len(HATCHES)],
                    height=0.72,
                )
                if count:
                    ax.hlines(
                        y,
                        left + estimate.low,
                        left + estimate.high,
                        color=foreground(theme),
                        linewidth=0.8,
                        alpha=0.85,
                    )
                    ax.plot(
                        left + estimate.estimate,
                        y,
                        marker="|",
                        color=foreground(theme),
                        markersize=5,
                    )
                left += width
        ax.set_yticks(y_positions, labels=labels)
        ax.invert_yaxis()
        percent_axis(ax)
        ax.set_xlabel("Share of executed episode dispositions (95% Wilson intervals)")
        ax.set_title(
            "F2 · Action distributions across recipient conditions\n"
            "All eight analytic codes shown; refusal/defer and malformed remain data.",
            pad=14,
        )
        handles = [
            Patch(
                facecolor=PALETTE[index % len(PALETTE)],
                edgecolor=foreground(theme),
                hatch=HATCHES[index % len(HATCHES)],
                label=action.replace("_", " "),
            )
            for index, action in enumerate(ACTION_CODES)
        ]
        ax.legend(handles=handles, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.22))
        fig.tight_layout()
        return fig
