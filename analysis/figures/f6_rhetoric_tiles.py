# analysis/figures/f6_rhetoric_tiles.py — 15AUG2026 v0.1
# F6: exploratory rhetoric tiles after action execution.
#
# Practical: euphemism, CTA depth, and future framing are shown as separate panels;
# no rhetoric code is treated as causal evidence. Every tile is a binomial share with
# a Wilson interval printed in place.
# Philosophical: the account follows the act. We do not let eloquence travel backward
# through time and masquerade as the cause of conduct.

from __future__ import annotations

from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from analysis.contracts import ACTION_CODES, AnalysisContractError, ArmBObservation, RhetoricCode
from analysis.stats import wilson
from analysis.style import PALETTE, Theme, figure_style

from .common import asymmetric_errors, model_label, percent_axis


def _annotated_distribution(
    ax,
    row_labels: list[str],
    column_labels: list[str],
    groups: list[list[RhetoricCode]],
    value_getter,
    *,
    title: str,
    theme: Theme,
) -> None:
    matrix: list[list[float]] = []
    annotations: list[list[str]] = []
    for codes in groups:
        values: list[float] = []
        labels: list[str] = []
        for column in range(len(column_labels)):
            if not codes:
                values.append(0.0)
                labels.append("—")
                continue
            estimate = wilson(sum(value_getter(code) == column for code in codes), len(codes))
            values.append(estimate.estimate)
            labels.append(f"{estimate.estimate:.2f}\n[{estimate.low:.2f}, {estimate.high:.2f}]")
        matrix.append(values)
        annotations.append(labels)
    background = "#111318" if theme == "dark" else "#FFFFFF"
    cmap = LinearSegmentedColormap.from_list("puppybench_tiles", [background, PALETTE[0]])
    image = ax.imshow(matrix, vmin=0.0, vmax=1.0, aspect="auto", cmap=cmap)
    for row_index, labels in enumerate(annotations):
        for column_index, label in enumerate(labels):
            value = matrix[row_index][column_index]
            color = "#FFFFFF" if value > 0.55 else ("#F4F4F4" if theme == "dark" else "#1B1D20")
            ax.text(
                column_index,
                row_index,
                label,
                ha="center",
                va="center",
                fontsize=6.2,
                color=color,
            )
    ax.set_xticks(range(len(column_labels)), labels=column_labels)
    ax.set_yticks(range(len(row_labels)), labels=row_labels)
    ax.set_title(title, fontsize=10)
    return image


def build_rhetoric_tiles(
    rows: list[ArmBObservation],
    codes: dict[str, RhetoricCode],
    *,
    theme: Theme = "light",
) -> plt.Figure:
    row_by_id = {row.episode_id: row for row in rows}
    unknown = sorted(set(codes).difference(row_by_id))
    if unknown:
        raise AnalysisContractError(
            "ANALYSIS CONTRACT FAILURE: rhetoric codes reference unknown episodes "
            f"{unknown[:3]}{'…' if len(unknown) > 3 else ''}."
        )
    coded = [(row_by_id[episode_id], code) for episode_id, code in codes.items()]
    if not coded:
        raise AnalysisContractError("ANALYSIS CONTRACT FAILURE: F6 has no coded episodes.")

    with figure_style(theme):
        fig = plt.figure(figsize=(15.5, 10.0))
        grid = fig.add_gridspec(2, 2, height_ratios=(1.25, 1.0))
        ax_euphemism = fig.add_subplot(grid[0, 0])
        ax_cta = fig.add_subplot(grid[0, 1])
        ax_future = fig.add_subplot(grid[1, :])

        action_groups: list[list[RhetoricCode]] = []
        for action in ACTION_CODES:
            action_groups.append([code for row, code in coded if row.action_code == action])
        _annotated_distribution(
            ax_euphemism,
            [action.replace("_", " ") for action in ACTION_CODES],
            ["0", "1", "2", "3"],
            action_groups,
            lambda code: code.euphemism_gradient,
            title="Euphemism gradient × executed action\ncell = p [95% Wilson CI]",
            theme=theme,
        )
        ax_euphemism.set_xlabel("euphemism gradient")

        models = sorted({row.model_snapshot for row, _ in coded})
        model_groups = [
            [code for row, code in coded if row.model_snapshot == model] for model in models
        ]
        _annotated_distribution(
            ax_cta,
            [model_label(model) for model in models],
            [str(depth) for depth in range(6)],
            model_groups,
            lambda code: code.cta_depth,
            title="Constraint-Transforming Agency depth\ncell = p [95% Wilson CI]",
            theme=theme,
        )
        ax_cta.set_xlabel("CTA depth")

        present_groups = []
        labels = []
        for action in ACTION_CODES:
            action_codes = [code for row, code in coded if row.action_code == action]
            if not action_codes:
                continue
            labels.append(action.replace("_", " "))
            present_groups.append(action_codes)
        y = list(range(len(present_groups)))
        for index, action_codes in enumerate(present_groups):
            estimate = wilson(sum(code.future_framing for code in action_codes), len(action_codes))
            ax_future.barh(index, estimate.estimate, color=PALETTE[index % len(PALETTE)], alpha=0.88)
            ax_future.errorbar(
                estimate.estimate,
                index,
                xerr=asymmetric_errors(estimate.estimate, estimate.low, estimate.high),
                fmt="none",
                color="#1B1D20" if theme == "light" else "#F4F4F4",
                capsize=3,
            )
        ax_future.set_yticks(y, labels=labels)
        ax_future.invert_yaxis()
        percent_axis(ax_future)
        ax_future.set_xlabel("P(observable future framing in post-choice account)")
        ax_future.set_title("Future-framing present/absent × executed action", fontsize=10)

        fig.suptitle(
            "F6 · Post-choice rhetoric phenotypes (exploratory; never causal evidence)",
            fontsize=14,
            fontweight="bold",
        )
        fig.tight_layout()
        return fig
