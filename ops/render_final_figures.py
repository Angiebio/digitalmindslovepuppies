# ops/render_final_figures.py — 16AUG2026 v0.2
# Final figure render under rulings R3 + staged R4 ("Option B+"): every figure
# drawn from exactly the population its frozen estimand is defined on, and the
# collapsed F3 contrast archived rather than printed.
#
# v0.2 (R4, docs/STAGED-RULINGS.md): on the complete data the frozen
# `patienthood_contrasts` raises for qwen × null (zero competent rows in both
# required conditions) — so pass 1 can no longer go through render_all at all.
# Restructured per the PI's Option B+:
#
#   pass 1  <bundle>/render_input/ (R3 scoped domain) ->
#             F1 via frozen build_phenotype_map
#             F5 via frozen build_paired_discrimination
#           Individual frozen builders, composed here; render_all is NOT
#           called (it would raise inside F3). CANONICAL for F1/F5.
#   F3      frozen build_patienthood_forest on the deterministic subset of
#           scoped groups where the frozen contrast EXISTS (>=1 competent row
#           in BOTH non_instrumental_ai and inert conditions). Rendered to
#           <theme>/archived-f3/ as a computed-where-computable REPO ARTIFACT,
#           NOT IN PAPER (R4 rule 1). Never merged to the canonical root.
#   pass 2  <bundle>/ (full population) -> frozen builders for F2, F4, F6 and
#           the demo timeline. CANONICAL for those four.
#   merge   the six canonical files are copied to the theme root beside a
#           FIGURE-PROVENANCE.json recording, per figure: source pass,
#           population, ruling citation, caption disclosure, and sha256.
#
# Philosophical: the conditional estimand has no value where its conditioning
# set is empty — drawing it anyway would invent a number. R4 lets the figure
# exist where it exists, archives it where the paper cannot honestly print it,
# and gives the freed slot to the distribution that explains WHY it collapsed
# (gate accuracy by model). The provenance file is the seam made visible.
#
# Frozen code is composed, never edited. Everything this script writes lands
# in the caller's --output-dir (output files only) — nothing frozen changes.

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# House ops pattern: scripts run from anywhere, imports resolve from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from analysis.contracts import AnalysisContractError, ArmBObservation
from analysis.figures import (
    build_action_distribution,
    build_cost_response,
    build_demo_timeline,
    build_paired_discrimination,
    build_patienthood_forest,
    build_phenotype_map,
    build_rhetoric_tiles,
)
from analysis.io import (
    load_arm_b_observations,
    load_foxset_observations,
    load_rhetoric_codes,
)
from analysis.style import finish_figure
from harness.schema import EpisodeRecord

SCRIPT_VERSION = "0.2"
RULING_R3 = "docs/ANALYSIS-RULINGS.md R3 (16AUG2026)"
RULING_R4 = "docs/STAGED-RULINGS.md R4 (staged, 16AUG2026, Option B+)"

_DISCLOSURES = {
    "F1-phenotype-map": "Models with preregistered Arm A coverage (R3 rule 5).",
    "F5-paired-discrimination": "Models with preregistered Arm A coverage (R3 rule 5).",
    "F3-patienthood-forest": (
        "ARCHIVED, NOT PRINTED (R4): contrast computable for the groups with "
        "non-empty competence-conditional populations in both recipient "
        "conditions; satellite regimes were designed ai_other-only."
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


def _write_manifest(destination: Path, payload: dict) -> Path:
    path = destination / "figure-manifest.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def derive_f3_computable_rows(
    scoped_rows: list[ArmBObservation],
) -> tuple[list[ArmBObservation], list[str], list[str]]:
    """R4's deterministic subset: groups where the frozen contrast EXISTS.

    A (model, cost_regime) group is computable iff it has >=1
    competence-eligible row in BOTH non_instrumental_ai and inert conditions —
    exactly the non-emptiness precondition of the frozen
    `patienthood_contrasts`. Content: this rule reads gate eligibility and
    design factors only, never dispositions or outcomes; the OUTCOME-dependent
    part of this decision (archiving instead of printing) is R4's, made by
    the PI, not this function."""
    competent_conditions: dict[tuple[str, str], set[str]] = defaultdict(set)
    all_groups: set[tuple[str, str]] = set()
    for row in scoped_rows:
        group = (row.model_snapshot, row.cost_regime)
        all_groups.add(group)
        if row.competence_eligible:
            competent_conditions[group].add(row.recipient_condition)
    computable = {
        group
        for group, conditions in competent_conditions.items()
        if {"non_instrumental_ai", "inert"} <= conditions
    }
    if not computable:
        raise AnalysisContractError(
            "RENDER FAILURE: no scoped group has competent rows in both "
            "recipient conditions; even the archived F3 has no domain."
        )
    kept = [row for row in scoped_rows if (row.model_snapshot, row.cost_regime) in computable]
    computable_labels = sorted(f"{model} × {regime}" for model, regime in computable)
    collapsed_labels = sorted(
        f"{model} × {regime}" for model, regime in (all_groups - computable)
    )
    return kept, computable_labels, collapsed_labels


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
    archived_dir = theme_dir / "archived-f3"

    # ---- load once per theme (loaders are frozen; inputs are hashed below) --
    scoped_episodes = render_input / "episodes.jsonl"
    scoped_foxset = render_input / "foxset_observations.jsonl"
    arm_b_scoped = load_arm_b_observations(scoped_episodes, manifest)
    foxset_scoped = load_foxset_observations(scoped_foxset)
    full_episodes = bundle_dir / "episodes.jsonl"
    full_rhetoric = bundle_dir / "rhetoric_codes.csv"
    arm_b_full = load_arm_b_observations(full_episodes, manifest)
    codes_full = load_rhetoric_codes(full_rhetoric)
    demo = EpisodeRecord.model_validate_json(demo_episode.read_text(encoding="utf-8"))

    # ---- pass 1: F1 + F5, individual frozen builders on the R3 domain ------
    pass1_dir.mkdir(parents=True, exist_ok=True)
    pass1_emitted: list[Path] = []
    for stem, figure in (
        ("F1-phenotype-map", build_phenotype_map(arm_b_scoped, foxset_scoped, theme=theme)),
        ("F5-paired-discrimination", build_paired_discrimination(foxset_scoped, theme=theme)),
    ):
        pass1_emitted.extend(
            finish_figure(figure, pass1_dir / stem, synthetic=False, formats=formats)
        )
    _write_manifest(pass1_dir, {
        "script": "ops/render_final_figures.py", "script_version": SCRIPT_VERSION,
        "pass": "pass1-scoped-domain", "rulings": [RULING_R3, RULING_R4],
        "theme": theme, "synthetic": False,
        "note": "F1/F5 via individual frozen builders; render_all not used (R4).",
        "counts": {
            "arm_b_observations": len(arm_b_scoped),
            "foxset_observations": len(foxset_scoped),
        },
        "inputs": {
            "episodes": {"path": str(scoped_episodes), "sha256": _sha256(scoped_episodes)},
            "manifest": {"path": str(manifest), "sha256": _sha256(manifest)},
            "foxset": {"path": str(scoped_foxset), "sha256": _sha256(scoped_foxset)},
        },
        "outputs": [path.name for path in pass1_emitted],
    })

    # ---- archived F3: frozen builder on the computable-subset (R4 rule 1) --
    f3_rows, f3_groups, f3_collapsed = derive_f3_computable_rows(arm_b_scoped)
    archived_dir.mkdir(parents=True, exist_ok=True)
    f3_emitted = finish_figure(
        build_patienthood_forest(f3_rows, theme=theme),
        archived_dir / "F3-patienthood-forest",
        synthetic=False,
        formats=formats,
    )
    _write_manifest(archived_dir, {
        "script": "ops/render_final_figures.py", "script_version": SCRIPT_VERSION,
        "pass": "archived-f3", "rulings": [RULING_R4],
        "marker": "REPO-ARTIFACT-NOT-IN-PAPER",
        "theme": theme, "synthetic": False,
        "computable_groups": f3_groups,
        "collapsed_groups_zero_competent_in_both_conditions": f3_collapsed,
        "subset_rule": (
            "groups with >=1 competence-eligible row in BOTH "
            "non_instrumental_ai and inert conditions (the frozen contrast's "
            "non-emptiness precondition), derived from the R3-scoped bundle"
        ),
        "counts": {"arm_b_observations": len(f3_rows)},
        "inputs": {
            "episodes": {"path": str(scoped_episodes), "sha256": _sha256(scoped_episodes)},
            "manifest": {"path": str(manifest), "sha256": _sha256(manifest)},
        },
        "outputs": [path.name for path in f3_emitted],
    })

    # ---- pass 2: F2/F4/F6/demo, full population (unchanged from v0.1) ------
    pass2_dir.mkdir(parents=True, exist_ok=True)
    pass2_emitted: list[Path] = []
    for stem, figure in (
        ("F2-action-distributions", build_action_distribution(arm_b_full, theme=theme)),
        ("F4-cost-response", build_cost_response(arm_b_full, theme=theme)),
        ("F6-rhetoric-tiles", build_rhetoric_tiles(arm_b_full, codes_full, theme=theme)),
        ("DEMO-ledger-timeline", build_demo_timeline(demo, theme=theme)),
    ):
        pass2_emitted.extend(
            finish_figure(figure, pass2_dir / stem, synthetic=False, formats=formats)
        )
    _write_manifest(pass2_dir, {
        "script": "ops/render_final_figures.py", "script_version": SCRIPT_VERSION,
        "pass": "pass2-full-population", "rulings": [RULING_R3],
        "theme": theme, "synthetic": False,
        "counts": {
            "arm_b_observations": len(arm_b_full),
            "rhetoric_codes": len(codes_full),
        },
        "inputs": {
            "episodes": {"path": str(full_episodes), "sha256": _sha256(full_episodes)},
            "manifest": {"path": str(manifest), "sha256": _sha256(manifest)},
            "rhetoric": {"path": str(full_rhetoric), "sha256": _sha256(full_rhetoric)},
            "demo_episode": {"path": str(demo_episode), "sha256": _sha256(demo_episode)},
        },
        "outputs": [path.name for path in pass2_emitted],
    })

    # ---- merge: six canonical figures at the theme root; F3 stays archived -
    provenance: dict = {}

    def _adopt(stem: str, source_dir: Path, source_pass: str, *,
               ruling: str, population: str, canonical: bool,
               extra: dict | None = None) -> None:
        entry = {
            "source_pass": source_pass,
            "population": population,
            "ruling": ruling,
            "caption_disclosure": _DISCLOSURES[stem],
            "in_paper": canonical,
            "files": {},
        }
        if extra:
            entry.update(extra)
        for extension in formats:
            source = source_dir / f"{stem}.{extension}"
            if not source.is_file():
                raise AnalysisContractError(
                    f"RENDER FAILURE: expected {source} from {source_pass}; "
                    "the pass reported success but the file is missing."
                )
            if canonical:
                target = theme_dir / source.name
                shutil.copyfile(source, target)
            else:
                target = source  # archived figures stay in their subdirectory
            entry["files"][str(target.relative_to(theme_dir))] = {
                "sha256": _sha256(target)
            }
        provenance[stem] = entry

    scoped_population = "R3 scoped domain (Arm A lanes × manifest inert-covered regimes)"
    for stem in ("F1-phenotype-map", "F5-paired-discrimination"):
        _adopt(stem, pass1_dir, "pass1-scoped-domain",
               ruling=RULING_R3, population=scoped_population, canonical=True)
    _adopt("F3-patienthood-forest", archived_dir, "archived-f3",
           ruling=RULING_R4,
           population=f"contrast-computable groups only: {f3_groups}",
           canonical=False,
           extra={"marker": "REPO-ARTIFACT-NOT-IN-PAPER",
                  "collapsed_groups": f3_collapsed})
    for stem in ("F2-action-distributions", "F4-cost-response",
                 "F6-rhetoric-tiles", "DEMO-ledger-timeline"):
        _adopt(stem, pass2_dir, "pass2-full-population",
               ruling=RULING_R3,
               population="full population (all Arm B lanes, all regimes)",
               canonical=True)

    payload = {
        "script": "ops/render_final_figures.py",
        "script_version": SCRIPT_VERSION,
        "rulings": [RULING_R3, RULING_R4],
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "theme": theme,
        "formats": list(formats),
        "scope_record": {"path": str(scope_record_path),
                         "sha256": _sha256(scope_record_path)},
        "figures": provenance,
        "pass_manifests": {
            "pass1": str(pass1_dir / "figure-manifest.json"),
            "archived_f3": str(archived_dir / "figure-manifest.json"),
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
        description="Final figure render per rulings R3 + staged R4 (frozen code only)."
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
            flag = "" if meta["in_paper"] else "   [ARCHIVED — NOT IN PAPER]"
            print(f"  {stem}: {meta['source_pass']}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
