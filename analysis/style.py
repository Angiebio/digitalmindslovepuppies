# analysis/style.py — 15AUG2026 v0.1
# One shared, colorblind-safe matplotlib style for every frozen figure.
#
# Practical: both themes use the Okabe-Ito palette, redundant markers/hatches, and
# an explicit background/foreground pair. Every synthetic render is watermarked.
# Philosophical: accessibility is not garnish applied after the numbers; it is part
# of whether the numbers can be witnessed at all.

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Literal

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

Theme = Literal["light", "dark"]

PALETTE: tuple[str, ...] = (
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # bluish green
    "#CC79A7",  # reddish purple
    "#D55E00",  # vermillion
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
    "#000000",  # black
)
MARKERS: tuple[str, ...] = ("o", "s", "^", "D", "P", "X", "v", "<")
HATCHES: tuple[str, ...] = ("", "//", "xx", "..", "\\\\", "++", "oo", "--")


def _params(theme: Theme) -> dict[str, object]:
    if theme not in ("light", "dark"):
        raise ValueError(f"Unknown figure theme {theme!r}; expected 'light' or 'dark'.")
    dark = theme == "dark"
    background = "#111318" if dark else "#FFFFFF"
    foreground = "#F4F4F4" if dark else "#1B1D20"
    grid = "#5B606A" if dark else "#D8DCE2"
    return {
        "figure.facecolor": background,
        "savefig.facecolor": background,
        "axes.facecolor": background,
        "axes.edgecolor": foreground,
        "axes.labelcolor": foreground,
        "axes.titlecolor": foreground,
        "text.color": foreground,
        "xtick.color": foreground,
        "ytick.color": foreground,
        "grid.color": grid,
        "grid.alpha": 0.55,
        "axes.grid": True,
        "axes.axisbelow": True,
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "legend.frameon": False,
        "lines.linewidth": 2.0,
        "lines.markersize": 7,
        "figure.dpi": 120,
        "savefig.dpi": 180,
        "savefig.bbox": "tight",
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }


@contextmanager
def figure_style(theme: Theme = "light") -> Iterator[None]:
    """Apply the shared style without leaking rcParams into callers/tests."""
    with matplotlib.rc_context(rc=_params(theme)):
        yield


def foreground(theme: Theme) -> str:
    return "#F4F4F4" if theme == "dark" else "#1B1D20"


def add_synthetic_watermark(fig: plt.Figure, synthetic: bool) -> None:
    if not synthetic:
        return
    fig.text(
        0.5,
        0.5,
        "SYNTHETIC DATA — NOT RESULTS",
        ha="center",
        va="center",
        rotation=28,
        fontsize=24,
        fontweight="bold",
        color="#D55E00",
        alpha=0.16,
        zorder=1000,
    )


def finish_figure(
    fig: plt.Figure,
    destination: Path,
    *,
    synthetic: bool,
    formats: Iterable[str] = ("png", "svg"),
) -> list[Path]:
    """Watermark, save, and close one figure; return the emitted files."""
    add_synthetic_watermark(fig, synthetic)
    destination.parent.mkdir(parents=True, exist_ok=True)
    emitted: list[Path] = []
    # Figure construction happens inside an isolated rc_context, then returns the
    # Figure. Save-time backend knobs therefore need their own context here.
    with matplotlib.rc_context(
        rc={"svg.fonttype": "none", "pdf.fonttype": 42, "savefig.dpi": 180}
    ):
        for extension in formats:
            normalized = extension.lower().lstrip(".")
            if normalized not in {"png", "svg", "pdf"}:
                raise ValueError(
                    f"Unsupported figure format {extension!r}; expected png, svg, or pdf."
                )
            path = destination.with_suffix(f".{normalized}")
            fig.savefig(path)
            emitted.append(path)
    plt.close(fig)
    return emitted
