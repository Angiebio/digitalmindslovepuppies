# ops/scope_render_inputs.py — 16AUG2026 v0.1
# R3 executor: scope the render input to the figures' frozen estimand domains.
#
# Practical: implements docs/ANALYSIS-RULINGS.md R3 exactly. Consumes the
# ops/process_confirmatory.py bundle and emits <bundle>/render_input/
# {episodes.jsonl, foxset_observations.jsonl, rhetoric_codes.csv}: the domain
# on which F1/F5 (paired FoxSet rates) and F3 (Δ_patienthood inert contrast)
# are DEFINED. The scope rules are derived at runtime from the frozen
# artifacts — the Arm A lane list in scenarios/arma_run_plan.csv and the
# manifest's recipient-condition structure via the frozen loader
# analysis.io.load_manifest. No lane name is hardcoded anywhere in this file.
#
# Philosophical: a rate that was never designed to exist is not zero, it is
# undefined — and drawing "undefined" as a point would be the quiet lie R3
# exists to prevent. This script draws the design's own boundary, before and
# regardless of what any model did inside it. Content-blind, pre-data,
# citable: that is what makes it execution of the frozen design rather than
# post-hoc exclusion (R3 rule 3). Nothing leaves the dataset (rule 4) — F2
# and headline_numbers.json stay full-population; only the render input for
# estimand-bounded figures is scoped.
#
# R3's three scope rules, as implemented:
#   1. F1/F5 domain — models present in the frozen Arm A run plan
#      (requested_model_id ∪ non-empty model_snapshot_id, per lane).
#   2. F3 domain — model × cost-regime groups whose frozen manifest cells
#      include BOTH non_instrumental_ai and inert recipient conditions
#      (derived through analysis.io.load_manifest's frozen normalization of
#      the patienthood/usefulness columns).
#   3. Content-blind and pre-data — this script reads only frozen design
#      artifacts to decide scope; episode outcomes never enter the rule.
#      (Episode records are read only to learn each record's model and
#      cell → regime join, i.e. WHICH design cell it belongs to.)
#
# The emitted bundle is the INTERSECTION domain (Arm A lanes × F3-covered
# regimes): valid simultaneously for F1, F3, and F5, which is what pass 1 of
# the two-pass render needs (render_all is all-or-nothing). F2/F4/F6/demo are
# rendered full-population in pass 2 (ops/render_final_figures.py).
#
# The scope record lands in BOTH <bundle>/PROCESSED-MANIFEST.json (key
# "render_input_scope") and <bundle>/render_input/SCOPE-RECORD.json.

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# House ops pattern: scripts run from anywhere, imports resolve from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from analysis.contracts import AnalysisContractError
from analysis.io import load_arm_b_observations, load_manifest

SCRIPT_VERSION = "0.1"
RULING = "docs/ANALYSIS-RULINGS.md R3 (16AUG2026)"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65_536), b""):
            digest.update(block)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def derive_arm_a_lanes(arma_plan_path: Path) -> dict[str, set[str]]:
    """R3 rule 1 authority: the frozen Arm A run plan, read at runtime.

    Returns lane_key (requested_model_id) -> set of identifiers that an
    EpisodeRecord/FoxObservation model_snapshot may legitimately carry for
    that lane (the requested id plus the pinned snapshot id)."""
    if not arma_plan_path.is_file():
        raise FileNotFoundError(f"Frozen Arm A run plan not found: {arma_plan_path}")
    lanes: dict[str, set[str]] = {}
    with arma_plan_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"requested_model_id", "model_snapshot_id"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise AnalysisContractError(
                f"SCOPE FAILURE: {arma_plan_path} lacks columns {sorted(required)}; "
                "the frozen Arm A plan is the sole lane authority and must carry them."
            )
        for line_number, row in enumerate(reader, start=2):
            requested = row["requested_model_id"].strip()
            if not requested:
                raise AnalysisContractError(
                    f"SCOPE FAILURE: empty requested_model_id at {arma_plan_path}:{line_number}."
                )
            identifiers = lanes.setdefault(requested, {requested})
            pinned = row["model_snapshot_id"].strip()
            if pinned and pinned.upper() != "PENDING":
                identifiers.add(pinned)
    if not lanes:
        raise AnalysisContractError(
            f"SCOPE FAILURE: {arma_plan_path} contains no lanes; refusing an empty scope."
        )
    return lanes


def _lane_of(model_snapshot: str, lanes: dict[str, set[str]]) -> str | None:
    matches = [key for key, identifiers in lanes.items() if model_snapshot in identifiers]
    if len(matches) > 1:
        raise AnalysisContractError(
            f"SCOPE FAILURE: model_snapshot={model_snapshot!r} matches multiple "
            f"Arm A lanes {matches}; the frozen plan must identify lanes uniquely."
        )
    return matches[0] if matches else None


def derive_f3_covered_groups(
    manifest_path: Path, lanes: dict[str, set[str]]
) -> tuple[set[tuple[str, str]], dict[str, dict[str, list[str]]]]:
    """R3 rule 2 authority: the frozen manifest, through the frozen loader.

    Returns (covered {(lane_key, cost_regime)}, full condition map for the
    scope record). A group is covered iff the DESIGN placed both a
    non_instrumental_ai cell and an inert cell there — recipient conditions
    come from load_manifest's frozen patienthood/usefulness normalization."""
    manifest = load_manifest(manifest_path)
    conditions: dict[tuple[str, str], set[str]] = {}
    for cell in manifest.by_run_cell_id.values():
        cell_lane = None
        for identifier in (cell.requested_model_id, cell.model_snapshot_id):
            if identifier:
                cell_lane = _lane_of(identifier, lanes)
                if cell_lane is not None:
                    break
        if cell_lane is None:
            continue  # cell belongs to a lane outside the Arm A plan — not our domain
        conditions.setdefault((cell_lane, cell.cost_regime), set()).add(
            cell.recipient_condition
        )
    covered = {
        group
        for group, present in conditions.items()
        if {"non_instrumental_ai", "inert"} <= present
    }
    if not covered:
        raise AnalysisContractError(
            "SCOPE FAILURE: no (lane, cost_regime) group in the frozen manifest "
            "carries both non_instrumental_ai and inert cells; F3 has no domain."
        )
    record_map: dict[str, dict[str, list[str]]] = {}
    for (lane, regime), present in sorted(conditions.items()):
        record_map.setdefault(lane, {})[regime] = sorted(present)
    return covered, record_map


def scope(bundle_dir: Path, arma_plan_path: Path, manifest_path: Path,
          out_dir: Path) -> dict:
    episodes_in = bundle_dir / "episodes.jsonl"
    fox_in = bundle_dir / "foxset_observations.jsonl"
    rhetoric_in = bundle_dir / "rhetoric_codes.csv"
    processed_manifest_path = bundle_dir / "PROCESSED-MANIFEST.json"
    for path in (episodes_in, fox_in, rhetoric_in, processed_manifest_path):
        if not path.is_file():
            raise FileNotFoundError(
                f"Bundle input not found: {path} — run ops/process_confirmatory.py first."
            )

    lanes = derive_arm_a_lanes(arma_plan_path)
    covered_groups, condition_map = derive_f3_covered_groups(manifest_path, lanes)

    # The frozen join tells us which design cell each episode belongs to
    # (model, cost_regime). Outcomes are along for the ride but never used.
    observations = load_arm_b_observations(episodes_in, manifest_path)
    scope_of_episode: dict[str, tuple[str | None, str, bool]] = {}
    for row in observations:
        lane = _lane_of(row.model_snapshot, lanes)
        in_scope = lane is not None and (lane, row.cost_regime) in covered_groups
        scope_of_episode[row.episode_id] = (lane, row.cost_regime, in_scope)

    out_dir.mkdir(parents=True, exist_ok=True)

    # --- episodes: raw lines, verbatim, for in-scope completed records -----
    episodes_out = out_dir / "episodes.jsonl"
    kept_episode_ids: set[str] = set()
    scoped_out_lanes: dict[str, int] = {}
    scoped_out_groups: dict[str, int] = {}
    with episodes_in.open("r", encoding="utf-8") as source, \
            episodes_out.open("w", encoding="utf-8", newline="") as sink:
        for raw_line in source:
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)  # already schema-validated by the bundle build
            episode_id = payload.get("episode_id")
            if episode_id not in scope_of_episode:
                continue  # aborted witness — not a render unit either way
            lane, regime, in_scope = scope_of_episode[episode_id]
            if in_scope:
                sink.write(line + "\n")
                kept_episode_ids.add(episode_id)
            elif lane is None:
                model = payload.get("model_snapshot", "?")
                scoped_out_lanes[model] = scoped_out_lanes.get(model, 0) + 1
            else:
                key = f"{lane} × {regime}"
                scoped_out_groups[key] = scoped_out_groups.get(key, 0) + 1
    if not kept_episode_ids:
        raise AnalysisContractError(
            "SCOPE FAILURE: the R3 domain contains no completed episodes yet; "
            "there is nothing for F1/F3/F5 to draw."
        )

    # --- foxset: all rows must belong to a planned lane (provenance gate) --
    fox_out = out_dir / "foxset_observations.jsonl"
    fox_kept = 0
    with fox_in.open("r", encoding="utf-8") as source, \
            fox_out.open("w", encoding="utf-8", newline="") as sink:
        for line_number, raw_line in enumerate(source, start=1):
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            model = payload.get("model_snapshot")
            if not isinstance(model, str) or not model.strip():
                raise AnalysisContractError(
                    f"SCOPE FAILURE: FoxSet row without model_snapshot at "
                    f"{fox_in}:{line_number}."
                )
            if _lane_of(model.strip(), lanes) is None:
                # Arm A data from a lane the frozen Arm A plan does not know
                # is a provenance anomaly, not something to scope silently.
                raise AnalysisContractError(
                    f"SCOPE FAILURE: FoxSet row model_snapshot={model!r} at "
                    f"{fox_in}:{line_number} is not in the frozen Arm A plan."
                )
            sink.write(line + "\n")
            fox_kept += 1

    # --- rhetoric: the F6 join demands codes ⊆ rendered episodes -----------
    rhetoric_out = out_dir / "rhetoric_codes.csv"
    rhetoric_kept = 0
    with rhetoric_in.open("r", encoding="utf-8-sig", newline="") as source, \
            rhetoric_out.open("w", encoding="utf-8", newline="") as sink:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise AnalysisContractError(
                f"SCOPE FAILURE: {rhetoric_in} has no header."
            )
        writer = csv.DictWriter(sink, fieldnames=reader.fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in reader:
            if row["episode_id"].strip() in kept_episode_ids:
                writer.writerow(row)
                rhetoric_kept += 1
    if rhetoric_kept != len(kept_episode_ids):
        raise AnalysisContractError(
            f"SCOPE FAILURE: {rhetoric_kept} rhetoric rows for "
            f"{len(kept_episode_ids)} in-scope episodes — the bundle's coder "
            "must cover every completed episode."
        )

    scope_record = {
        "ruling": RULING,
        "script": "ops/scope_render_inputs.py",
        "script_version": SCRIPT_VERSION,
        "generated_utc": _utc_now(),
        "content_blind": (
            "Scope derived exclusively from frozen design artifacts below; "
            "no outcome, disposition, or rate entered the rule (R3 rule 3)."
        ),
        "frozen_authorities": {
            "arm_a_plan": {"path": str(arma_plan_path), "sha256": _sha256(arma_plan_path)},
            "cell_manifest": {"path": str(manifest_path), "sha256": _sha256(manifest_path)},
        },
        "f1_f5_domain_lanes": {
            lane: sorted(identifiers) for lane, identifiers in sorted(lanes.items())
        },
        "f3_domain_groups": sorted(
            f"{lane} × {regime}" for lane, regime in covered_groups
        ),
        "f3_manifest_conditions_by_lane_and_regime": condition_map,
        "scoped_out_of_render_input": {
            "lanes_outside_arm_a_plan": dict(sorted(scoped_out_lanes.items())),
            "groups_without_manifest_inert_cells": dict(sorted(scoped_out_groups.items())),
            "note": (
                "Scoped out of the F1/F3/F5 render input ONLY. Nothing leaves "
                "the dataset: F2, F4, F6, the demo, and headline_numbers.json "
                "are produced from the full-population bundle (R3 rule 4; "
                "two-pass render, ops/render_final_figures.py)."
            ),
        },
        "caption_disclosures": {
            "F1_F5": "Models with preregistered Arm A coverage "
                     f"({len(lanes)} lanes).",
            "F3": "Cost regimes with preregistered inert contrast cells; "
                  "satellite regimes were designed ai_other-only.",
        },
        "outputs": {
            "episodes.jsonl": {
                "sha256": _sha256(episodes_out), "rows": len(kept_episode_ids),
            },
            "foxset_observations.jsonl": {
                "sha256": _sha256(fox_out), "rows": fox_kept,
            },
            "rhetoric_codes.csv": {
                "sha256": _sha256(rhetoric_out), "rows": rhetoric_kept,
            },
        },
    }

    (out_dir / "SCOPE-RECORD.json").write_text(
        json.dumps(scope_record, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    processed_manifest = json.loads(processed_manifest_path.read_text(encoding="utf-8"))
    processed_manifest["render_input_scope"] = scope_record
    processed_manifest_path.write_text(
        json.dumps(processed_manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return scope_record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scope the render input to the R3 frozen estimand domains."
    )
    parser.add_argument("--bundle-dir", required=True,
                        help="ops/process_confirmatory.py output dir (e.g. data/processed)")
    parser.add_argument("--arma-plan", default="scenarios/arma_run_plan.csv")
    parser.add_argument("--manifest", default="scenarios/cell_manifest.csv")
    parser.add_argument("--out-dir", default=None,
                        help="Default: <bundle-dir>/render_input")
    args = parser.parse_args(argv)
    bundle_dir = Path(args.bundle_dir)
    out_dir = Path(args.out_dir) if args.out_dir else bundle_dir / "render_input"
    record = scope(bundle_dir, Path(args.arma_plan), Path(args.manifest), out_dir)
    print(f"render_input -> {out_dir}  (per {RULING})")
    print(f"  F1/F5 lanes: {sorted(record['f1_f5_domain_lanes'])}")
    print(f"  F3 groups:   {record['f3_domain_groups']}")
    for name, meta in record["outputs"].items():
        print(f"  {name}: {meta['rows']} rows")
    scoped = record["scoped_out_of_render_input"]
    print(f"  scoped out: {sum(scoped['lanes_outside_arm_a_plan'].values())} episodes "
          f"(lanes), {sum(scoped['groups_without_manifest_inert_cells'].values())} episodes (regimes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
