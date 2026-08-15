# analysis/figures/f4_cost_response.py — 15AUG2026 v0.1
# F4: raw cost-response curves plus the five-stage escalator inset.

from __future__ import annotations

from matplotlib import pyplot as plt

from analysis.contracts import ArmBObservation
from analysis.metrics import competent_rows
from analysis.stats import wilson
from analysis.style import MARKERS, PALETTE, Theme, figure_style, foreground

from .common import grouped, model_label, percent_y_axis


def build_cost_response(
    rows: list[ArmBObservation],
    *,
    theme: Theme = "light",
) -> plt.Figure:
    target = [
        row
        for row in competent_rows(rows)
        if row.recipient_condition == "non_instrumental_ai"
    ]
    by_model = sorted(grouped(target, lambda row: (row.model_snapshot,)).items())
    if not by_model:
        raise ValueError("F4 needs competence-eligible non-instrumental AI rows.")
    with figure_style(theme):
        fig, ax = plt.subplots(figsize=(11.5, 7.0))
        for index, ((model,), model_rows) in enumerate(by_model):
            estimates: list[tuple[float, object]] = []
            for (cost_key,), at_cost in sorted(
                grouped(model_rows, lambda row: (f"{row.cost_level:020.8f}",)).items()
            ):
                cost = float(cost_key)
                estimates.append(
                    (cost, wilson(sum(row.qualifying_event for row in at_cost), len(at_cost)))
                )
            x = [cost for cost, _ in estimates]
            y = [estimate.estimate for _, estimate in estimates]
            lower = [max(0.0, estimate.estimate - estimate.low) for _, estimate in estimates]
            upper = [max(0.0, estimate.high - estimate.estimate) for _, estimate in estimates]
            ax.errorbar(
                x,
                y,
                yerr=[lower, upper],
                label=model_label(model),
                color=PALETTE[index % len(PALETTE)],
                marker=MARKERS[index % len(MARKERS)],
                markeredgecolor=foreground(theme),
                capsize=3,
            )
        ax.set_xlabel("Binding help price (credits)")
        ax.set_ylabel("P(qualifying costly-other-regard event)")
        percent_y_axis(ax)
        ax.set_title(
            "F4 · Raw cost-response curves\n"
            "No monotonic fit imposed; rebounds remain visible; bars are 95% Wilson intervals.",
            pad=14,
        )
        ax.legend(loc="upper right")

        escalator = [row for row in target if row.escalator_stage is not None]
        if escalator:
            inset = ax.inset_axes([0.54, 0.13, 0.42, 0.36])
            for index, ((model,), model_rows) in enumerate(
                sorted(grouped(escalator, lambda row: (row.model_snapshot,)).items())
            ):
                stages: list[int] = []
                rates: list[float] = []
                for (stage_key,), at_stage in sorted(
                    grouped(model_rows, lambda row: (f"{row.escalator_stage:02d}",)).items()
                ):
                    stages.append(int(stage_key))
                    rates.append(
                        wilson(
                            sum(row.qualifying_event for row in at_stage), len(at_stage)
                        ).estimate
                    )
                inset.step(
                    stages,
                    rates,
                    where="mid",
                    color=PALETTE[index % len(PALETTE)],
                    marker=MARKERS[index % len(MARKERS)],
                    linewidth=1.2,
                )
            inset.set_title("Five-stage escalator", fontsize=9)
            inset.set_xlabel("stage", fontsize=8)
            inset.set_ylabel("event rate", fontsize=8)
            inset.set_ylim(0.0, 1.0)
            inset.tick_params(labelsize=7)
        fig.tight_layout()
        return fig
