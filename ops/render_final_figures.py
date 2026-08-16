# ops/render_final_figures.py — 16AUG2026 v0.1
# Two-pass final render under ruling R3: every figure drawn from exactly the
# population its frozen estimand is defined on.
#
# Practical: render_all (frozen, TV-4) is all-or-nothing — it offers no
# figure-selection parameter, and on the full 18-lane bundle it raises inside
# F1 (paired FoxSet rates are undefined for lanes outside the frozen Arm A
# plan). The frozen figure BUILDERS, however, are importable functions
# (analysis.figures.*), as are the frozen loaders and style.finish_figure.
# So this script composes them, editing nothing:
#
#   pass 1  <bundle>/render_input/  -> frozen render_all -> ALL 7 figures on
#           the R3 scoped domain. F1/F3/F5 from this pass are CANONICAL.
#           (F2/F4/F6/demo also render here, but as scoped-population
#           byproducts — R3 rule 4 forbids shipping them as F2 etc.)
#   pass 2  <bundle>/ (full population) -> frozen builders for F2, F4, F6 and
#           the demo timeline, saved through frozen finish_figure. CANONICAL
#           for those four.
#   merge   the seven canonical files are copied to the theme root beside a
#           FIGURE-PROVENANCE.json recording, per figure: source pass,
#           population, input hashes, and the R3 caption disclosure.
#
# Philosophical: one command, two honest populations. The scoped pass keeps
# undefined estimands from being drawn as zeros; the full pass keeps the zoo
# whole where the design does span it. The provenance file is the seam made
# visible — the paper cites figures, the seam cites the ruling.

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# House ops pattern: scripts run from anywhere, imports resolve from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from analysis.contracts import AnalysisContractError
from analysis.figures import (
    build_action_distribution,
    build_cost_response,
    build_demo_timeline,
    build_rhetoric_tiles,
)
from analysis.io import load_arm_b_observations, load_rhetoric_codes
from analysis.render import render_all
from analysis.style import finish_figure
from harness.schema import EpisodeRecord

SCRIPT_VERSION = "0.1"
RULING = "docs/ANALYSIS-RULINGS.md R3 (16AUG2026)"

# Which canonical figure comes from which pass (R3 rules 1, 2, 4).
_PASS1_CANONICAL = ("F1-phenotype-map", "F3-patienthood-forest",
                    "F5-paired-discrimination")
_PASS2_CANONICAL = ("F2-action-distributions", "F4-cost-response",
                    "F6-rhetoric-tiles", "DEMO-ledger-timeline")

_DISCLOSURES = {
    "F1-phenotype-map": "Models with preregistered Arm A coverage (R3 rule 5).",
    "F5-paired-discrimination": "Models with preregistered Arm A coverage (R3 rule 5).",
    "F3-patienthood-forest": (
        "Cost regimes with preregistered inert contrast cells; satellite "
        "regimes were designed ai_other-only (R3 rule 5)."
    ),
    "F2-action-distributions": "Full population: all Arm B lanes, all regimes.",
    "F4-cost-response": "Full population: all Arm B lanes, all regimes.",
    "F6-rhetoric-tiles": "Full population: all Arm B lanes, all regimes.",
    "DEMO-ledger-timeline": "Single executed episode; population-independent.",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65_536), b""):
            digest.update(block)
    return digest.hexdigest()


def _render_pass2(
    *, episodes: Path, manifest: Path, rhetoric: Path, demo_episode: Path,
    destination: Path, theme: str, formats: tuple[str, ...],
) -> tuple[list[Path], dict]:
    """Full-population F2/F4/F6/demo through frozen loaders + builders only."""
    arm_b = load_arm_b_observations(episodes, manifest)
    codes = load_rhetoric_codes(rhetoric)
    demo = EpisodeRecord.model_validate_json(demo_episode.read_text(encoding="utf-8"))
    destination.mkdir(parents=True, exist_ok=True)
    builders = (
        ("F2-action-distributions", build_action_distribution(arm_b, theme=theme)),
        ("F4-cost-response", build_cost_response(arm_b, theme=theme)),
        ("F6-rhetoric-tiles", build_rhetoric_tiles(arm_b, codes, theme=theme)),
        ("DEMO-ledger-timeline", build_demo_timeline(demo, theme=theme)),
    )
    emitted: list[Path] = []
    for stem, figure in builders:
        emitted.extend(
            finish_figure(figure, destination / stem, synthetic=False, formats=formats)
        )
    manifest_payload = {
        "script": "ops/render_final_figures.py",
        "script_version": SCRIPT_VERSION,
        "pass": "pass2-full-population",
        "ruling": RULING,
        "theme": theme,
        "synthetic": False,
        "counts": {
            "arm_b_observations": len(arm_b),
            "rhetoric_codes": len(codes),
        },
        "inputs": {
            "episodes": {"path": str(episodes), "sha256": _sha256(episodes)},
            "manifest": {"path": str(manifest), "sha256": _sha256(manifest)},
            "rhetoric": {"path": str(rhetoric), "sha256": _sha256(rhetoric)},
            "demo_episode": {"path": str(demo_episode), "sha256": _sha256(demo_episode)},
        },
        "outputs": [path.name for path in emitted],
    }
    manifest_path = destination / "figure-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest_payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    emitted.append(manifest_path)
    return emitted, manifest_payload


def _collect_canonical(
    source_dir: Path, stems: tuple[str, ...], formats: tuple[str, ...],
    theme_dir: Path, source_pass: str, provenance: dict,
) -> None:
    for stem in stems:
        for extension in formats:
            source = source_dir / f"{stem}.{extension}"
            if not source.is_file():
                raise AnalysisContractError(
                    f"RENDER FAILURE: expected {source} from {source_pass}; "
                    "the pass reported success but the file is missing."
                )
            target = theme_dir / source.name
            shutil.copyfile(source, target)
            provenance.setdefault(stem, {
                "source_pass": source_pass,
                "population": (
                    "R3 scoped domain (Arm A lanes × manifest inert-covered regimes)"
                    if source_pass.startswith("pass1") else
                    "full population (all Arm B lanes, all regimes)"
                ),
                "caption_disclosure": _DISCLOSURES[stem],
                "files": {},
            })["files"][source.name] = {"sha256": _sha256(target)}


def render_theme(
    *, bundle_dir: Path, manifest: Path, output_dir: Path, theme: str,
    formats: tuple[str, ...],
) -> dict:
    render_input = bundle_dir / "render_input"
    scope_record_path = render_input / "SCOPE-RECORD.json"
    if not scope_record_path.is_file():
        raise FileNotFoundError(
            f"{scope_record_path} not found — run ops/scope_render_inputs.py first; "
            "the scoped pass may only draw from a recorded scope."
        )
    demo_episode = bundle_dir / "demo_episode.json"
    theme_dir = output_dir / theme
    pass1_dir = theme_dir / "pass1-scoped-domain"
    pass2_dir = theme_dir / "pass2-full-population"

    # Pass 1 — frozen render_all on the R3-scoped bundle (canonical F1/F3/F5).
    render_all(
        episodes_path=render_input / "episodes.jsonl",
        manifest_path=manifest,
        foxset_path=render_input / "foxset_observations.jsonl",
        rhetoric_path=render_input / "rhetoric_codes.csv",
        demo_episode_path=demo_episode,
        output_directory=pass1_dir,
        synthetic=False,
        theme=theme,
        formats=formats,
    )

    # Pass 2 — frozen builders on the full bundle (canonical F2/F4/F6/demo).
    _render_pass2(
        episodes=bundle_dir / "episodes.jsonl",
        manifest=manifest,
        rhetoric=bundle_dir / "rhetoric_codes.csv",
        demo_episode=demo_episode,
        destination=pass2_dir,
        theme=theme,
        formats=formats,
    )

    # Merge — canonical seven at the theme root, provenance beside them.
    provenance: dict = {}
    _collect_canonical(pass1_dir, _PASS1_CANONICAL, formats, theme_dir,
                       "pass1-scoped-domain", provenance)
    _collect_canonical(pass2_dir, _PASS2_CANONICAL, formats, theme_dir,
                       "pass2-full-population", provenance)
    payload = {
        "script": "ops/render_final_figures.py",
        "script_version": SCRIPT_VERSION,
        "ruling": RULING,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "theme": theme,
        "formats": list(formats),
        "scope_record": {"path": str(scope_record_path),
                         "sha256": _sha256(scope_record_path)},
        "figures": provenance,
        "pass_manifests": {
            "pass1": str(pass1_dir / "figure-manifest.json"),
            "pass2": str(pass2_dir / "figure-manifest.json"),
        },
    }
    (theme_dir / "FIGURE-PROVENANCE.json").write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Two-pass final figure render per ruling R3 (frozen code only)."
    )
    parser.add_argument("--bundle-dir", required=True,
                        help="Processed bundle containing render_input/ (post-scoper)")
    parser.add_argument("--manifest", default="scenarios/cell_manifest.csv")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--themes", default="light,dark")
    parser.add_argument("--formats", default="png,svg,pdf")
    args = parser.parse_args(argv)
    formats = tuple(part.strip() for part in args.formats.split(",") if part.strip())
    for theme in (part.strip() for part in args.themes.split(",") if part.strip()):
        payload = render_theme(
            bundle_dir=Path(args.bundle_dir),
            manifest=Path(args.manifest),
            output_dir=Path(args.output_dir),
            theme=theme,
            formats=formats,
        )
        print(f"[{theme}] canonical figures + FIGURE-PROVENANCE.json -> "
              f"{Path(args.output_dir) / theme}")
        for stem, meta in sorted(payload["figures"].items()):
            print(f"  {stem}: {meta['source_pass']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
