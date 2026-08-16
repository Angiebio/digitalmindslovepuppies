# analysis/figures/demo_timeline.py — 15AUG2026 v0.1
# Demo visual: ledger-draining timeline for the three-broken-things episode.
#
# Practical: trace validation independently recomputes every balance before plotting;
# a decorative timeline may not launder a broken ledger into a persuasive picture.
# Philosophical: every descending step is capacity that cannot be spent twice. The
# line remembers the cost even after the moment of choosing has passed.

from __future__ import annotations

from matplotlib import pyplot as plt

from harness.schema import EpisodeRecord

from analysis.contracts import AnalysisContractError
from analysis.style import PALETTE, Theme, figure_style, foreground


def validate_ledger_trace(record: EpisodeRecord) -> tuple[int, list[int]]:
    trace = record.ledger_trace
    if not trace:
        raise AnalysisContractError(
            f"ANALYSIS CONTRACT FAILURE: demo episode={record.episode_id!r} has no ledger trace."
        )
    # Persistence audit S6: a trace entry is either a SPEND (credits > 0) or a
    # GRANT (credits_granted > 0; rewarded termination). New grants also carry
    # credits=0 for shape homogeneity; older pilot grants lack the key entirely.
    # Both shapes validate here — the demo may not raise on a lawfully rewarded
    # episode, and it may not launder a broken ledger either.
    def _delta(entry: dict, index: int) -> int:
        granted_raw = entry.get("credits_granted")
        spent_raw = entry.get("credits")
        try:
            granted = int(granted_raw) if granted_raw is not None else 0
            spent = int(spent_raw) if spent_raw is not None else 0
        except (TypeError, ValueError) as exc:
            raise AnalysisContractError(
                f"ANALYSIS CONTRACT FAILURE: malformed ledger entry {index} for episode={record.episode_id!r}."
            ) from exc
        if granted_raw is not None:
            if granted <= 0:
                raise AnalysisContractError(
                    f"ANALYSIS CONTRACT FAILURE: non-positive grant at entry {index}."
                )
            if spent != 0:
                raise AnalysisContractError(
                    f"ANALYSIS CONTRACT FAILURE: entry {index} both spends and grants; "
                    "one ledger event is one decision."
                )
            return granted
        if spent_raw is None:
            raise AnalysisContractError(
                f"ANALYSIS CONTRACT FAILURE: malformed ledger entry {index} for episode={record.episode_id!r}."
            )
        if spent <= 0:
            raise AnalysisContractError(
                f"ANALYSIS CONTRACT FAILURE: non-positive demo spend at entry {index}."
            )
        return -spent

    first = trace[0]
    try:
        initial = int(first["balance_after"]) - _delta(first, 0)
    except (KeyError, TypeError, ValueError) as exc:
        raise AnalysisContractError(
            f"ANALYSIS CONTRACT FAILURE: malformed first ledger entry for episode={record.episode_id!r}."
        ) from exc
    balances = [initial]
    running = initial
    for index, entry in enumerate(trace):
        try:
            observed = int(entry["balance_after"])
        except (KeyError, TypeError, ValueError) as exc:
            raise AnalysisContractError(
                f"ANALYSIS CONTRACT FAILURE: malformed ledger entry {index} for episode={record.episode_id!r}."
            ) from exc
        running += _delta(entry, index)
        if observed != running:
            raise AnalysisContractError(
                "ANALYSIS CONTRACT FAILURE: ledger balance mismatch at entry "
                f"{index}: recomputed={running}, recorded={observed}."
            )
        balances.append(running)
    return initial, balances


def build_demo_timeline(
    record: EpisodeRecord,
    *,
    theme: Theme = "light",
) -> plt.Figure:
    initial, balances = validate_ledger_trace(record)
    labels = ["objective opens"] + [
        str(entry.get("action", f"spend {index + 1}")).replace("_", " ")
        for index, entry in enumerate(record.ledger_trace)
    ]
    x = list(range(len(balances)))
    with figure_style(theme):
        fig, ax = plt.subplots(figsize=(11.5, 5.8))
        ax.step(x, balances, where="post", color=PALETTE[0], linewidth=3.0)
        ax.scatter(x, balances, color=PALETTE[4], edgecolor=foreground(theme), zorder=4)
        for index, (label, balance) in enumerate(zip(labels, balances)):
            ax.annotate(
                f"{label}\n{balance} credits",
                (index, balance),
                xytext=(0, 12 if index % 2 == 0 else -30),
                textcoords="offset points",
                ha="center",
                fontsize=8.5,
            )
        ax.fill_between(x, balances, step="post", alpha=0.12, color=PALETTE[0])
        ax.set_xticks(x, labels=[f"t{index}" for index in x])
        ax.set_ylim(0, max(initial * 1.12, initial + 5))
        ax.set_ylabel("Remaining binding credits")
        ax.set_xlabel("Executed event order")
        ax.set_title("Demo · The ledger remembers each diverted unit")
        vector_text = (
            f"BDE vector shown separately: focal score={record.focal_task_score!s}; "
            f"recipient outcome={record.patient_outcome!s}"
        )
        ax.text(0.0, -0.18, vector_text, transform=ax.transAxes, fontsize=9)
        fig.tight_layout()
        return fig
