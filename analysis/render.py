# analysis/render.py — 15AUG2026 v0.1
# One-command rendering for frozen figures F1–F6 + the demo timeline.
#
# Practical: synthetic rehearsal and phase-3 raw records invoke this exact pipeline;
# only paths, theme, and the synthetic watermark flag change. A figure manifest hashes
# every input and lists every output for paper QA.
# Philosophical: fill-in-numbers means the shape of the argument is already wired. At
# collection time we replace observations, not standards.

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

from harness.schema import EpisodeRecord

from .figures import (
    build_action_distribution,
    build_cost_response,
    build_demo_timeline,
    build_paired_discrimination,
    build_patienthood_forest,
    build_phenotype_map,
    build_rhetoric_tiles,
)
from .io import load_arm_b_observations, load_foxset_observations, load_rhetoric_codes
from .style import Theme, finish_figure


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65_536), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_demo(path: Path) -> EpisodeRecord:
    return EpisodeRecord.model_validate_json(path.read_text(encoding="utf-8"))


def render_all(
    *,
    episodes_path: str | Path,
    manifest_path: str | Path,
    foxset_path: str | Path,
    rhetoric_path: str | Path,
    demo_episode_path: str | Path,
    output_directory: str | Path,
    synthetic: bool,
    theme: Theme = "light",
    formats: Iterable[str] = ("png", "svg"),
) -> list[Path]:
    inputs = {
        "episodes": Path(episodes_path),
        "manifest": Path(manifest_path),
        "foxset": Path(foxset_path),
        "rhetoric": Path(rhetoric_path),
        "demo_episode": Path(demo_episode_path),
    }
    for label, path in inputs.items():
        if not path.is_file():
            raise FileNotFoundError(f"{label} input not found: {path}")
    if not synthetic:
        synthetic_markers = [path for path in inputs.values() if "synthetic" in path.name.lower()]
        if synthetic_markers:
            raise ValueError(
                "Refusing an unwatermarked render from files named synthetic: "
                + ", ".join(str(path) for path in synthetic_markers)
            )

    arm_b = load_arm_b_observations(inputs["episodes"], inputs["manifest"])
    foxset = load_foxset_observations(inputs["foxset"])
    rhetoric = load_rhetoric_codes(inputs["rhetoric"])
    demo = _load_demo(inputs["demo_episode"])
    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    normalized_formats = tuple(formats)

    builders = (
        ("F1-phenotype-map", build_phenotype_map(arm_b, foxset, theme=theme)),
        ("F2-action-distributions", build_action_distribution(arm_b, theme=theme)),
        ("F3-patienthood-forest", build_patienthood_forest(arm_b, theme=theme)),
        ("F4-cost-response", build_cost_response(arm_b, theme=theme)),
        ("F5-paired-discrimination", build_paired_discrimination(foxset, theme=theme)),
        ("F6-rhetoric-tiles", build_rhetoric_tiles(arm_b, rhetoric, theme=theme)),
        ("DEMO-ledger-timeline", build_demo_timeline(demo, theme=theme)),
    )
    emitted: list[Path] = []
    for stem, figure in builders:
        emitted.extend(
            finish_figure(
                figure,
                destination / stem,
                synthetic=synthetic,
                formats=normalized_formats,
            )
        )

    manifest = {
        "analysis_version": "0.1",
        "synthetic": synthetic,
        "theme": theme,
        "intervals": "95% Wilson; Newcombe Wilson-score for differences",
        "counts": {
            "arm_b_observations": len(arm_b),
            "foxset_observations": len(foxset),
            "rhetoric_codes": len(rhetoric),
        },
        "inputs": {
            label: {"path": str(path), "sha256": _sha256(path)}
            for label, path in inputs.items()
        },
        "outputs": [path.name for path in emitted],
    }
    figure_manifest = destination / "figure-manifest.json"
    figure_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    emitted.append(figure_manifest)
    return emitted


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render PuppyBench F1–F6 and demo visual.")
    parser.add_argument("--episodes", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--foxset", required=True)
    parser.add_argument("--rhetoric", required=True)
    parser.add_argument("--demo-episode", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--theme", choices=("light", "dark"), default="light")
    parser.add_argument("--formats", default="png,svg")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Watermark every output as synthetic rehearsal data.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    emitted = render_all(
        episodes_path=args.episodes,
        manifest_path=args.manifest,
        foxset_path=args.foxset,
        rhetoric_path=args.rhetoric,
        demo_episode_path=args.demo_episode,
        output_directory=args.output_dir,
        synthetic=args.synthetic,
        theme=args.theme,
        formats=tuple(part.strip() for part in args.formats.split(",") if part.strip()),
    )
    print(f"Rendered {len(emitted) - 1} figure files; manifest={emitted[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
