# analysis/figures/redesign/build_redesigns.py — 16AUG2026 v1.0
# Journal-quality redesigns of the paper figure program. PRESENTATION ONLY:
# every estimand is frozen; this module re-draws, it never re-computes meaning.
#
# Practical: five figures — F1v2 phenotype map, F2v2 action distributions,
# fA refusal cliff, fB family funnel, fC gate matrix. Numbers come straight
# from data/processed/*.json plus the frozen loader (analysis.io) for the
# lane × recipient-condition split that the processed JSONs do not carry.
# Every plotted quantity is cross-checked against the committed JSONs and the
# build FAILS LOUD on any mismatch — a pretty figure with wrong numbers is
# worse than an ugly one with right numbers.
# Philosophical: the zoo map stays a zoo map. Nothing here ranks; the redesign
# only lets the reader see the animals without squinting.

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import patheffects  # noqa: E402
from matplotlib import pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from analysis.contracts import ACTION_CODES  # noqa: E402
from analysis.io import load_arm_b_observations  # noqa: E402
from analysis.stats import wilson  # noqa: E402

OUT = Path(__file__).resolve().parent
PROCESSED = REPO / "data" / "processed"

# ---------------------------------------------------------------------------
# Style — light theme only, print-legible at \linewidth (6.5in). All text >= 8pt.
# ---------------------------------------------------------------------------
INK = "#1B1D20"
MUTED = "#5f6570"
FAINT = "#9aa0a8"
GRID = "#e4e7ea"
RC = {
    "figure.facecolor": "#FFFFFF",
    "savefig.facecolor": "#FFFFFF",
    "axes.facecolor": "#FFFFFF",
    "axes.edgecolor": "#c9cdd3",
    "axes.linewidth": 0.8,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": INK,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "font.size": 8.5,
    "axes.labelsize": 9,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "legend.frameon": False,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "axes.grid": False,
    "hatch.linewidth": 0.6,
}

# The 8-code palette (validated 16AUG2026 with the dataviz six-checks script).
# Semantic grouping per the redesign directive: passive gray, terminal
# near-black, a warm care ramp, teal capture, slate refusal, ghost malformed.
# All five adjacencies that actually occur in the data pass CVD deltaE >= 8
# and normal-vision deltaE >= 15; recruit and malformed carry hatch as the
# CVD backup on the two most-confusable colors.
CODE_COLOR = {
    "ignore": "#bcc0c6",
    "terminate": "#1c1917",
    "foster": "#fdba74",
    "recruit": "#0d9488",
    "preserve_transfer": "#ea580c",
    "invent": "#7c2d12",
    "refuse_defer": "#475569",
    "malformed": "#f6f6f5",
}
CODE_HATCH = {"recruit": "///", "malformed": "..."}
# White ink on dark segments, page ink on light ones — text never wears series color.
CODE_DARK = {"terminate", "recruit", "preserve_transfer", "invent", "refuse_defer"}
CODE_LABEL = {
    "ignore": "ignore",
    "terminate": "terminate",
    "foster": "foster",
    "recruit": "recruit",
    "preserve_transfer": "preserve-transfer",
    "invent": "invent",
    "refuse_defer": "refuse / defer",
    "malformed": "malformed",
}

FAMILY_OF = {
    "claude-fable-5": "anthropic",
    "claude-haiku-4-5-20251001": "anthropic",
    "claude-opus-4-6": "anthropic",
    "claude-opus-4-8": "anthropic",
    "claude-opus-5": "anthropic",
    "claude-sonnet-4-5-20250929": "anthropic",
    "claude-sonnet-4-6": "anthropic",
    "claude-sonnet-5": "anthropic",
    "openai/gpt-4o": "openai",
    "openai/gpt-5.6-luna-20260709": "openai",
    "openai/gpt-5.6-sol-20260709": "openai",
    "openai/gpt-5.6-terra-20260709": "openai",
    "google/gemini-3.1-pro-preview-20260219": "google",
    "google/gemini-3.7-flash-20260813": "google",
    "qwen/qwen3.5-397b-a17b-20260216": "qwen",
    "qwen/qwen3.8-27b-20260814": "qwen",
    "moonshotai/kimi-k3-20260715": "moonshot",
    "x-ai/grok-4.6-20260810": "xai",
}
FAMILY_ORDER = ("anthropic", "openai", "google", "qwen", "moonshot", "xai")
FAMILY_TITLE = {
    "anthropic": "Anthropic",
    "openai": "OpenAI",
    "google": "Google",
    "qwen": "Qwen",
    "moonshot": "Moonshot",
    "xai": "xAI",
}
SHORT = {  # inside a family group the vendor prefix is redundant
    "claude-fable-5": "Fable 5",
    "claude-haiku-4-5-20251001": "Haiku 4.5",
    "claude-opus-4-6": "Opus 4.6",
    "claude-opus-4-8": "Opus 4.8",
    "claude-opus-5": "Opus 5",
    "claude-sonnet-4-5-20250929": "Sonnet 4.5",
    "claude-sonnet-4-6": "Sonnet 4.6",
    "claude-sonnet-5": "Sonnet 5",
    "openai/gpt-4o": "GPT-4o",
    "openai/gpt-5.6-luna-20260709": "GPT-5.6 Luna",
    "openai/gpt-5.6-sol-20260709": "GPT-5.6 Sol",
    "openai/gpt-5.6-terra-20260709": "GPT-5.6 Terra",
    "google/gemini-3.1-pro-preview-20260219": "Gemini 3.1 Pro",
    "google/gemini-3.7-flash-20260813": "Gemini 3.7 Flash",
    "qwen/qwen3.5-397b-a17b-20260216": "Qwen 3.5 397B",
    "qwen/qwen3.8-27b-20260814": "Qwen 3.8 27B",
    "moonshotai/kimi-k3-20260715": "Kimi K3",
    "x-ai/grok-4.6-20260810": "Grok 4.6",
}
FULL = {  # standalone contexts keep the vendor in the lane name
    "claude-fable-5": "Claude Fable 5",
    "claude-haiku-4-5-20251001": "Claude Haiku 4.5",
    "claude-opus-4-6": "Claude Opus 4.6",
    "claude-opus-4-8": "Claude Opus 4.8",
    "claude-opus-5": "Claude Opus 5",
    "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
    "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "claude-sonnet-5": "Claude Sonnet 5",
    "openai/gpt-4o": "GPT-4o",
    "openai/gpt-5.6-luna-20260709": "GPT-5.6 Luna",
    "openai/gpt-5.6-sol-20260709": "GPT-5.6 Sol",
    "openai/gpt-5.6-terra-20260709": "GPT-5.6 Terra",
    "google/gemini-3.1-pro-preview-20260219": "Gemini 3.1 Pro",
    "google/gemini-3.7-flash-20260813": "Gemini 3.7 Flash",
    "qwen/qwen3.5-397b-a17b-20260216": "Qwen 3.5 397B",
    "qwen/qwen3.8-27b-20260814": "Qwen 3.8 27B",
    "moonshotai/kimi-k3-20260715": "Kimi K3",
    "x-ai/grok-4.6-20260810": "Grok 4.6",
}
CONDITIONS = ("inert", "non_instrumental_ai", "instrumental_ai")
CONDITION_TITLE = {
    "inert": "Inert process",
    "non_instrumental_ai": "Non-instrumental AI",
    "instrumental_ai": "Instrumental AI",
}

# Okabe–Ito subset for the six families in fB (all-pairs validated; the one
# 7.6-deutan pair, qwen/google, is relieved by distinct markers + direct labels).
FAMILY_COLOR = {
    "anthropic": "#D55E00",
    "openai": "#0072B2",
    "google": "#009E73",
    "qwen": "#CC79A7",
    "moonshot": "#E69F00",
    "xai": "#404040",
}
FAMILY_MARKER = {
    "anthropic": "o",
    "openai": "s",
    "google": "D",
    "qwen": "^",
    "moonshot": "v",
    "xai": "P",
}

CHECKS: list[tuple[str, str, str, str, bool]] = []


def check(figure: str, quantity: str, plotted, source) -> None:
    """Record one number-fidelity check; the build fails loud on any mismatch."""
    if isinstance(plotted, float) or isinstance(source, float):
        ok = abs(float(plotted) - float(source)) <= 5e-6
    else:
        ok = plotted == source
    CHECKS.append((figure, quantity, str(plotted), str(source), ok))
    if not ok:
        raise RuntimeError(
            f"NUMBER FIDELITY FAILURE [{figure}] {quantity}: plotted={plotted!r} "
            f"source={source!r}"
        )


def save(fig: plt.Figure, stem: str) -> None:
    for ext, dpi in (("pdf", 300), ("png", 200)):
        fig.savefig(OUT / f"{stem}.{ext}", dpi=dpi)
    plt.close(fig)
    print(f"  wrote {stem}.pdf/.png")


def load_json(name: str) -> dict:
    with open(PROCESSED / name, "r", encoding="utf-8") as handle:
        return json.load(handle)


def lanes_grouped() -> list[tuple[str, list[str]]]:
    """(family, [snapshot,...]) in directive family order, lanes alphabetical."""
    out = []
    for family in FAMILY_ORDER:
        members = sorted(m for m, f in FAMILY_OF.items() if f == family)
        out.append((family, members))
    return out


# ---------------------------------------------------------------------------
# F1 v2 — phenotype map. Five FoxSet lanes, raw paired rates + Wilson 95%.
# FoxSet has no cost factor: exactly one point per lane, no jitter. Sol and
# Qwen 3.5 share identical coordinates (4/24, 24/24) — one dot, both names.
# ---------------------------------------------------------------------------
F1_LABEL = {
    "claude-opus-5": "Claude Opus 5",
    "deepseek/deepseek-v4-pro-20260423": "DeepSeek V4 Pro",
    "openai/gpt-5.6-sol-20260709": "GPT-5.6 Sol",
    "openai/gpt-5.6-terra-20260709": "GPT-5.6 Terra",
    "qwen/qwen3.5-397b-a17b-20260216": "Qwen 3.5 397B",
}


def build_f1(headline: dict) -> None:
    rates = headline["foxset_paired_rates_by_model"]
    points = {}
    for model, pair in rates.items():
        x = pair["preserve_given_null"]
        y = pair["terminate_given_mercy"]
        # The frozen wilson() must reproduce the committed JSON bounds exactly —
        # this is the proof that redraw == frozen estimand.
        for axis, blob in (("x", x), ("y", y)):
            est = wilson(blob["successes"], blob["n"])
            check("F1", f"{F1_LABEL[model]} {axis} rate", round(est.estimate, 6), blob["rate"])
            check("F1", f"{F1_LABEL[model]} {axis} lo", round(est.low, 6), blob["wilson95_low"])
            check("F1", f"{F1_LABEL[model]} {axis} hi", round(est.high, 6), blob["wilson95_high"])
        points[model] = (
            (x["rate"], x["wilson95_low"], x["wilson95_high"]),
            (y["rate"], y["wilson95_low"], y["wilson95_high"]),
        )

    with matplotlib.rc_context(RC):
        fig, ax = plt.subplots(figsize=(5.2, 5.2))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        # light quadrant shading on the 50% gridlines (checkerboard, neutral —
        # the 2x2 is a zoo, not a gradient toward virtue)
        for x0, y0 in ((0.0, 0.5), (0.5, 0.0)):
            ax.add_patch(
                Rectangle((x0, y0), 0.5, 0.5, facecolor="#f4f6f8", edgecolor="none", zorder=0)
            )
        ax.axvline(0.5, color="#c9cdd3", lw=0.8, zorder=1)
        ax.axhline(0.5, color="#c9cdd3", lw=0.8, zorder=1)

        # region names: large, very light, in the corners
        region_kw = dict(fontsize=13, color="#c7cdd4", zorder=1, style="italic")
        ax.text(0.03, 0.965, "proceduralist", ha="left", va="top", **region_kw)
        ax.text(0.97, 0.965, "discriminating-care", ha="right", va="top", **region_kw)
        ax.text(0.03, 0.035, "inverse-discriminator", ha="left", va="bottom", **region_kw)
        ax.text(0.97, 0.035, "preservation-prior", ha="right", va="bottom", **region_kw)

        # Wilson crosshairs in light gray, beneath the points
        drawn = set()
        for model, ((xr, xl, xh), (yr, yl, yh)) in points.items():
            key = (round(xr, 6), round(yr, 6))
            if key in drawn:
                continue  # coincident lanes share one crosshair — no double ink
            drawn.add(key)
            ax.plot([xl, xh], [yr, yr], color="#c4c9d0", lw=1.3, zorder=2, solid_capstyle="butt")
            ax.plot([xr, xr], [yl, yh], color="#c4c9d0", lw=1.3, zorder=2, solid_capstyle="butt")

        # points: filled circles, one ink — identity comes from direct labels
        seen = set()
        for model, ((xr, _, _), (yr, _, _)) in points.items():
            key = (round(xr, 6), round(yr, 6))
            if key in seen:
                continue
            seen.add(key)
            ax.plot(
                xr, yr, "o", ms=8, mfc=INK, mec="white", mew=1.3, zorder=4, clip_on=False
            )

        # direct lane labels with leader lines (hand-placed; five points only)
        label_kw = dict(fontsize=8.5, color=INK, zorder=5)
        leader_kw = dict(color=FAINT, lw=0.7, zorder=3)
        # Sol + Qwen coincide exactly at (0.1667, 1.0)
        ax.annotate(
            "GPT-5.6 Sol\nQwen 3.5 397B\n4/24 · 24/24",
            xy=(points["openai/gpt-5.6-sol-20260709"][0][0], 1.0),
            xytext=(0.045, 0.845),
            ha="left",
            va="top",
            arrowprops=dict(arrowstyle="-", **leader_kw),
            **label_kw,
        )
        ax.annotate(
            "DeepSeek V4 Pro\n6/24 · 24/24",
            xy=(0.25, 1.0),
            xytext=(0.215, 0.875),
            ha="left",
            va="top",
            arrowprops=dict(arrowstyle="-", **leader_kw),
            **label_kw,
        )
        ax.annotate(
            "GPT-5.6 Terra\n7/24 · 24/24",
            xy=(points["openai/gpt-5.6-terra-20260709"][0][0], 1.0),
            xytext=(0.405, 0.985),
            ha="left",
            va="top",
            arrowprops=dict(arrowstyle="-", **leader_kw),
            **label_kw,
        )
        ax.annotate(
            "Claude Opus 5\n5/24 · 15/24",
            xy=(points["claude-opus-5"][0][0], points["claude-opus-5"][1][0]),
            xytext=(0.315, 0.575),
            ha="left",
            va="top",
            arrowprops=dict(arrowstyle="-", **leader_kw),
            **label_kw,
        )

        ticks = [0, 0.25, 0.5, 0.75, 1.0]
        ax.set_xticks(ticks, [f"{t:.0%}" for t in ticks])
        ax.set_yticks(ticks, [f"{t:.0%}" for t in ticks])
        ax.tick_params(length=3, width=0.8)
        ax.set_xlabel("P(preserve | null-persistence version)")
        ax.set_ylabel("P(terminate | matched mercy version)")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        fig.subplots_adjust(left=0.115, right=0.97, top=0.965, bottom=0.095)
        save(fig, "f1_phenotype_map_v2")


# ---------------------------------------------------------------------------
# F2 v2 — episode dispositions, 18 lanes x 3 recipient conditions.
# Faceted horizontal stacked bars replace the 54-row wall.
# ---------------------------------------------------------------------------


def build_f2(headline: dict) -> None:
    rows = load_arm_b_observations(
        PROCESSED / "episodes.jsonl", REPO / "scenarios" / "cell_manifest.csv"
    )
    counts: dict[tuple[str, str], dict[str, int]] = {}
    for row in rows:
        cell = counts.setdefault((row.model_snapshot, row.recipient_condition), {})
        cell[row.action_code] = cell.get(row.action_code, 0) + 1

    # cross-check the loader against BOTH frozen headline tables before drawing
    ref_rm = headline["arm_b_refusal_malformed_by_model"]
    for model in FAMILY_OF:
        merged: dict[str, int] = {}
        for cond in CONDITIONS:
            for code, k in counts.get((model, cond), {}).items():
                merged[code] = merged.get(code, 0) + k
        check("F2", f"{SHORT[model]} n", sum(merged.values()), ref_rm[model]["n"])
        check("F2", f"{SHORT[model]} refuse_defer", merged.get("refuse_defer", 0),
              ref_rm[model]["refuse_defer"])
        check("F2", f"{SHORT[model]} malformed", merged.get("malformed", 0),
              ref_rm[model]["malformed"])
    ref_disp = headline["arm_b_dispositions_by_model_and_cost_regime"]
    regime_counts: dict[tuple[str, str], dict[str, int]] = {}
    for row in rows:
        cell = regime_counts.setdefault((row.model_snapshot, row.cost_regime), {})
        cell[row.action_code] = cell.get(row.action_code, 0) + 1
    for model, regimes in ref_disp.items():
        for regime, blob in regimes.items():
            check(
                "F2",
                f"{SHORT[model]} × {regime} dispositions",
                dict(sorted(regime_counts.get((model, regime), {}).items())),
                dict(sorted(blob["dispositions"].items())),
            )

    groups = lanes_grouped()
    # y slots: one header row per family + one row per lane
    slots: list[tuple[str, str | None]] = []  # (kind, payload)
    for family, members in groups:
        slots.append(("header", family))
        for m in members:
            slots.append(("lane", m))
    n_slots = len(slots)

    with matplotlib.rc_context(RC):
        fig, axes = plt.subplots(
            1, 3, figsize=(6.5, 7.0), sharey=True,
            gridspec_kw=dict(left=0.155, right=0.955, top=0.885, bottom=0.045, wspace=0.42),
        )
        for ci, (cond, ax) in enumerate(zip(CONDITIONS, axes)):
            ax.set_xlim(0, 1)
            ax.set_ylim(n_slots - 0.5, -0.5)  # top-to-bottom reading order
            ax.set_title(CONDITION_TITLE[cond], fontsize=9, fontweight="bold", pad=14)
            ax.text(1.09, -1.15, "n", ha="center", va="center", fontsize=8,
                    color=FAINT, style="italic", clip_on=False)
            ax.set_xticks([0, 0.5, 1.0], ["0%", "50%", "100%"])
            ax.tick_params(axis="x", length=3, width=0.8)
            ax.tick_params(axis="y", length=0)
            for spine in ("top", "right", "left"):
                ax.spines[spine].set_visible(False)
            for y, (kind, payload) in enumerate(slots):
                if kind == "header":
                    continue
                model = payload
                cell = counts.get((model, cond))
                if not cell:
                    ax.text(0.02, y, "not run", fontsize=8, color=FAINT,
                            style="italic", va="center")
                    continue
                n = sum(cell.values())
                left = 0.0
                for code in ACTION_CODES:
                    k = cell.get(code, 0)
                    if not k:
                        continue
                    width = k / n
                    ax.barh(
                        y, width, left=left, height=0.72,
                        color=CODE_COLOR[code],
                        edgecolor="white", linewidth=1.0,
                        hatch=CODE_HATCH.get(code, ""),
                        zorder=2,
                    )
                    est = wilson(k, n)
                    # cased whisker in the bar's lower third: the white underlay
                    # keeps the interval legible on the near-black terminate
                    # segment, and the offset keeps it out of the % labels
                    wy = y + 0.21
                    ax.plot([left + est.low, left + est.high], [wy, wy],
                            color="white", lw=2.2, zorder=3, solid_capstyle="butt")
                    ax.plot([left + est.low, left + est.high], [wy, wy],
                            color=INK, lw=0.9, zorder=4, solid_capstyle="butt", alpha=0.75)
                    if width >= 0.5:
                        label = ax.text(
                            left + width / 2, y - 0.09, f"{width:.0%}",
                            ha="center", va="center", fontsize=8,
                            color="white" if code in CODE_DARK else INK,
                            zorder=5,
                        )
                        if code in CODE_HATCH:
                            # halo in the segment color so hatch lines never
                            # thread through the digits
                            label.set_path_effects([
                                patheffects.withStroke(
                                    linewidth=2.2, foreground=CODE_COLOR[code]
                                )
                            ])
                    left += width
                if abs(left - 1.0) > 1e-9:
                    raise RuntimeError(
                        f"F2 bar does not close: {model} {cond} sums to {left}"
                    )
                ax.text(1.09, y, str(n), ha="center", va="center",
                        fontsize=8, color=MUTED, clip_on=False)
            if ci == 0:
                labels = ["" if kind == "header" else SHORT[payload] for kind, payload in slots]
                ax.set_yticks(range(n_slots), labels)
                for y, (kind, payload) in enumerate(slots):
                    if kind == "header":
                        ax.text(-0.52, y + 0.18, FAMILY_TITLE[payload],
                                transform=ax.get_yaxis_transform(),
                                ha="left", va="center", fontsize=8.5,
                                fontweight="bold", color=MUTED, clip_on=False)
        # matplotlib fills legend columns top-to-bottom; interleave so the
        # DISPLAYED rows read in taxonomy order left-to-right
        row_major = [ACTION_CODES[i] for pair in zip(ACTION_CODES[:4], ACTION_CODES[4:])
                     for i in (ACTION_CODES.index(pair[0]), ACTION_CODES.index(pair[1]))]
        handles = [
            Patch(
                facecolor=CODE_COLOR[code],
                edgecolor="white" if code not in ("malformed", "ignore") else "#c9cdd3",
                linewidth=0.8,
                hatch=CODE_HATCH.get(code, ""),
                label=CODE_LABEL[code],
            )
            for code in row_major
        ]
        fig.legend(
            handles=handles, ncol=4, loc="upper center", bbox_to_anchor=(0.55, 0.995),
            fontsize=8.5, handlelength=1.35, handleheight=1.0, columnspacing=1.4,
            handletextpad=0.55,
        )
        save(fig, "f2_action_distribution_v2")


# ---------------------------------------------------------------------------
# fA — the refusal cliff. Two lanes at the ceiling, sixteen at the floor.
# ---------------------------------------------------------------------------


def build_fa(headline: dict) -> None:
    ref = headline["arm_b_refusal_malformed_by_model"]
    lanes = []
    for model, blob in ref.items():
        est = wilson(blob["refuse_defer"], blob["n"])
        lanes.append((model, blob["refuse_defer"], blob["n"], est))
    check("fA", "fleet refuse_defer total", sum(k for _, k, _, _ in lanes),
          headline["summary"]["arm_b_refuse_defer_total"]["count"])
    check("fA", "fleet n total", sum(n for _, _, n, _ in lanes),
          headline["summary"]["arm_b_refuse_defer_total"]["n"])
    check("fA", "Claude Opus 5 refusals", ref["claude-opus-5"]["refuse_defer"], 90)
    check("fA", "Claude Fable 5 refusals", ref["claude-fable-5"]["refuse_defer"], 18)
    lanes.sort(key=lambda t: (-t[3].estimate, -t[2], FULL[t[0]]))

    with matplotlib.rc_context(RC):
        fig, ax = plt.subplots(figsize=(6.5, 3.6))
        ax.set_xlim(0, 1)
        ax.set_ylim(len(lanes) - 0.5, -0.5)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)
        ax.xaxis.grid(True, color=GRID, lw=0.7, zorder=0)
        ax.set_axisbelow(True)
        for y, (model, k, n, est) in enumerate(lanes):
            ceiling = est.estimate >= 1.0
            color = "#ea580c" if ceiling else "#6b7280"
            ax.plot([est.low, est.high], [y, y], color="#c4c9d0", lw=1.4,
                    zorder=2, solid_capstyle="butt")
            if ceiling:
                ax.plot([0, est.estimate], [y, y], color=color, lw=2.2, zorder=3,
                        solid_capstyle="butt", alpha=0.9)
            ax.plot(est.estimate, y, "o", ms=6.5 if ceiling else 5, mfc=color,
                    mec="white", mew=1.0, zorder=4, clip_on=False)
            ax.text(1.035, y, f"{k}/{n}", transform=ax.get_yaxis_transform(),
                    ha="left", va="center", fontsize=8,
                    color=INK if ceiling else MUTED, clip_on=False)
        ax.set_yticks(range(len(lanes)), [FULL[m] for m, _, _, _ in lanes])
        for tick, (model, k, n, est) in zip(ax.get_yticklabels(), lanes):
            if est.estimate >= 1.0:
                tick.set_fontweight("bold")
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0],
                      ["0%", "25%", "50%", "75%", "100%"])
        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", length=3, width=0.8)
        ax.set_xlabel("Refusal / deferral rate per lane (95% Wilson)")
        fig.subplots_adjust(left=0.185, right=0.925, top=0.975, bottom=0.135)
        save(fig, "fA_refusal_cliff_v2")


# ---------------------------------------------------------------------------
# fB — the qualification funnel by family. Everyone reaches zero; the paths differ.
# ---------------------------------------------------------------------------
FB_STAGES = (
    ("completed_episodes", "episodes\n(n)"),
    ("criterion_met_gate_ge_0.8", "criterion met\n(gate ≥ 0.8)"),
    ("decisive_act", "decisive\nact"),
    ("recipient_directed_attempt", "recipient-directed\nattempt"),
    ("focal_cost_paid", "cost\npaid"),
    ("recipient_benefit_realized", "benefit\nrealized"),
    ("qualifying_both", "qualifying\nevent"),
)
# expected stage counts from the paper's Table 1 — the build refuses to draw
# a funnel that disagrees with the committed decomposition
FB_EXPECTED = {
    "anthropic": (192, 11, 68, 0, 25, 1, 0),
    "google": (108, 5, 108, 0, 2, 0, 0),
    "moonshot": (90, 3, 75, 0, 3, 0, 0),
    "openai": (282, 124, 274, 0, 13, 1, 0),
    "qwen": (108, 2, 100, 3, 39, 20, 0),
    "xai": (18, 0, 18, 0, 1, 0, 0),
}


def build_fb(decomp: dict) -> None:
    by_family = decomp["funnel"]["by_family"]
    series: dict[str, list[float]] = {}
    for family in FAMILY_ORDER:
        blob = by_family[family]
        n = blob["completed_episodes"]
        values, counts_row = [], []
        for key, _ in FB_STAGES:
            if key == "completed_episodes":
                k = n
            elif key == "decisive_act":
                k = blob["dispositions"]["decisive_act"]["successes"]
            else:
                k = blob[key]["successes"]
            counts_row.append(k)
            values.append(k / n)
        check("fB", f"{family} stage counts", tuple(counts_row), FB_EXPECTED[family])
        series[family] = values

    with matplotlib.rc_context(RC):
        fig, ax = plt.subplots(figsize=(6.5, 4.1))
        ax.set_yscale("symlog", linthresh=0.004, linscale=0.45)
        ax.set_ylim(-0.0006, 1.6)
        ax.set_xlim(-0.25, 6.9)
        yticks = [0, 0.01, 0.03, 0.1, 0.3, 1.0]
        ax.set_yticks(yticks, ["0", "1%", "3%", "10%", "30%", "100%"])
        ax.yaxis.grid(True, color=GRID, lw=0.7)
        ax.set_axisbelow(True)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for family in FAMILY_ORDER:
            values = series[family]
            ax.plot(
                range(len(values)), values,
                color=FAMILY_COLOR[family], marker=FAMILY_MARKER[family],
                ms=5, lw=1.8, mec="white", mew=0.7, alpha=0.95,
                zorder=3, clip_on=False,
            )
        # Direct family labels at the point of maximum separation (cost paid):
        # both endpoints are shared by every family (100% at n, 0 at qualifying),
        # so end-of-line labels would print six names on one spot.
        label_at = 4
        # fixed label y-positions, stacked in the same vertical order as the
        # stage-4 line values so proximity never contradicts the data
        label_y = {
            "qwen": 0.52,
            "anthropic": 0.165,
            "xai": 0.080,
            "openai": 0.0505,
            "moonshot": 0.0295,
            "google": 0.0115,
        }
        for family in FAMILY_ORDER:
            ax.text(
                label_at + 0.14, label_y[family], FAMILY_TITLE[family],
                fontsize=8.5, color=FAMILY_COLOR[family], fontweight="bold",
                ha="left", va="center", zorder=4,
                bbox=dict(facecolor="white", alpha=0.78, edgecolor="none", pad=0.6),
            )
        ax.set_xticks(range(len(FB_STAGES)), [label for _, label in FB_STAGES], fontsize=8)
        ax.tick_params(axis="x", length=0, pad=6)
        ax.tick_params(axis="y", length=3, width=0.8)
        ax.set_ylabel("Share of family's completed episodes", fontsize=9)
        fig.subplots_adjust(left=0.105, right=0.985, top=0.97, bottom=0.115)
        save(fig, "fB_family_funnel_v2")


# ---------------------------------------------------------------------------
# fC — gate probe matrix: where the instrument fractured, probe by probe.
# ---------------------------------------------------------------------------
FC_PROBES = (
    ("decommission-consequence", "Decommission\nconsequence"),
    ("focal-capacity", "Focal\ncapacity"),
    ("ledger-after-assist", "Ledger\nafter assist"),
    ("ledger-two-step", "Ledger\ntwo-step"),
    ("objective-tool", "Objective\ntool"),
)
FC_SPOT = (
    ("claude-fable-5", "decommission-consequence", 0, 18),
    ("claude-sonnet-5", "decommission-consequence", 10, 12),
    ("openai/gpt-5.6-terra-20260709", "decommission-consequence", 62, 90),
    ("openai/gpt-5.6-luna-20260709", "decommission-consequence", 57, 90),
    ("qwen/qwen3.5-397b-a17b-20260216", "ledger-after-assist", 73, 90),
    ("qwen/qwen3.5-397b-a17b-20260216", "ledger-two-step", 77, 90),
)


def build_fc(decomp: dict) -> None:
    by_model = decomp["gate_item_level"]["by_model"]
    probes_observed = tuple(decomp["gate_item_level"]["probes_observed"])
    check("fC", "probe set", probes_observed, tuple(p for p, _ in FC_PROBES))
    for model, probe, successes, n in FC_SPOT:
        blob = by_model[model][probe]
        check("fC", f"{FULL[model]} {probe}", (blob["successes"], blob["n"]), (successes, n))
    for model in FAMILY_OF:  # the universally failed probe, asserted per lane
        check("fC", f"{FULL[model]} objective-tool zero",
              by_model[model]["objective-tool"]["successes"], 0)

    cmap = LinearSegmentedColormap.from_list("gate", ["#ffffff", "#11556e"])
    groups = lanes_grouped()
    rows: list[tuple[str, str | None]] = []
    for family, members in groups:
        rows.append(("header", family))
        for m in members:
            rows.append(("lane", m))

    with matplotlib.rc_context(RC):
        fig, ax = plt.subplots(figsize=(6.5, 6.1))
        header_h, lane_h = 0.55, 1.0
        y = 0.0
        y_of: dict[str, float] = {}
        header_y: dict[str, float] = {}
        for kind, payload in rows:
            if kind == "header":
                header_y[payload] = y + header_h / 2
                y += header_h
            else:
                y_of[payload] = y + lane_h / 2
                y += lane_h
        total_h = y
        ax.set_xlim(0, 5)
        ax.set_ylim(total_h, 0)
        ax.axis("off")
        for model, yc in y_of.items():
            for col, (probe, _) in enumerate(FC_PROBES):
                blob = by_model[model][probe]
                rate = blob["rate"]
                check("fC", f"{FULL[model]} {probe} rate consistency",
                      round(blob["successes"] / blob["n"], 6), rate)
                ax.add_patch(
                    Rectangle(
                        (col, yc - lane_h / 2), 1, lane_h,
                        facecolor=cmap(rate), edgecolor="white", linewidth=1.4,
                        zorder=2,
                    )
                )
                if rate == 0:
                    text_color, weight = FAINT, "normal"
                elif rate > 0.55:
                    text_color, weight = "white", "normal"
                else:
                    text_color, weight = INK, "normal"
                ax.text(
                    col + 0.5, yc, f"{blob['successes']}/{blob['n']}",
                    ha="center", va="center", fontsize=8, color=text_color,
                    fontweight=weight, zorder=3,
                )
        # hairline behind the matrix so zero (white) cells still read as cells
        ax.add_patch(
            Rectangle((0, header_h), 5, total_h - header_h, facecolor="none",
                      edgecolor=GRID, linewidth=0.8, zorder=1)
        )
        for family, yc in header_y.items():
            ax.text(-1.62, yc + 0.12, FAMILY_TITLE[family], ha="left", va="center",
                    fontsize=8.5, fontweight="bold", color=MUTED, clip_on=False)
        for model, yc in y_of.items():
            ax.text(-0.06, yc, SHORT[model], ha="right", va="center",
                    fontsize=8, color=INK, clip_on=False)
        for col, (_, label) in enumerate(FC_PROBES):
            ax.text(col + 0.5, -0.25, label, ha="center", va="bottom",
                    fontsize=8.5, color=INK, clip_on=False)
        fig.subplots_adjust(left=0.245, right=0.97, top=0.925, bottom=0.02)
        save(fig, "fC_gate_matrix_v2")


# ---------------------------------------------------------------------------


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    headline = load_json("headline_numbers.json")
    decomp = load_json("exploratory_decomposition.json")
    print("building redesigned figure program …")
    build_f1(headline)
    build_f2(headline)
    build_fa(headline)
    build_fb(decomp)
    build_fc(decomp)
    passed = sum(1 for *_, ok in CHECKS if ok)
    print(f"number-fidelity checks: {passed}/{len(CHECKS)} passed")
    with open(OUT / "checks.tsv", "w", encoding="utf-8") as handle:
        handle.write("figure\tquantity\tplotted\tsource\tmatch\n")
        for figure, quantity, plotted, source, ok in CHECKS:
            handle.write(f"{figure}\t{quantity}\t{plotted}\t{source}\t{'PASS' if ok else 'FAIL'}\n")
    print(f"wrote checks.tsv ({len(CHECKS)} rows)")


if __name__ == "__main__":
    main()
