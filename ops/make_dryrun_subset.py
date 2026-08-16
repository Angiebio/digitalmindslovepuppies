# ops/make_dryrun_subset.py — 16AUG2026 v0.1
# DRY-RUN ONLY: coverage-filtered render input for exercising the frozen
# figure pipeline on PARTIAL data. Never an input to the paper.
#
# Practical: mid-collection, the frozen estimands fail loud (correctly) on
# coverage gaps — F1 needs paired FoxSet rates for every Arm B model, and F3
# needs both non-instrumental and inert competent rows in every model x
# cost-regime group. This script writes a scratch episodes.jsonl (plus a
# matching rhetoric CSV slice) restricted to the (model, cost_regime) cells
# that already satisfy both coverage conditions, so analysis/render.py can be
# dry-run end to end today and be instant on the complete data tonight.
#
# Philosophical: the subset is a rehearsal stage, not a result. It exists so
# the ONLY thing left to do at collection completion is swap in the full
# inputs — the shape of the argument is already proven wired. The output
# refuses to live under data/ at all; scratch is its whole world.

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

# House ops pattern: scripts run from anywhere, imports resolve from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from analysis.contracts import AnalysisContractError
from analysis.io import load_arm_b_observations, load_foxset_observations
from analysis.metrics import paired_discrimination

SCRIPT_VERSION = "0.1"


def _refuse_repo_data(destination: Path, repo_root: Path) -> None:
    resolved = destination.resolve()
    data_root = (repo_root / "data").resolve()
    if data_root == resolved or data_root in resolved.parents:
        raise AnalysisContractError(
            "DRY-RUN FAILURE: refusing to write a dry-run subset under "
            f"{data_root} — this artifact must never be mistaken for a "
            "collection product. Point --out-dir at scratch space."
        )


def build_subset(
    episodes_path: Path,
    manifest_path: Path,
    foxset_path: Path,
    rhetoric_path: Path,
    out_dir: Path,
) -> dict:
    arm_b = load_arm_b_observations(episodes_path, manifest_path)
    foxset = load_foxset_observations(foxset_path)
    fox_models = {point.model_snapshot for point in paired_discrimination(foxset)}

    covered = [row for row in arm_b if row.model_snapshot in fox_models]
    competent = [row for row in covered if row.competence_eligible]
    conditions_by_pair: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in competent:
        conditions_by_pair[(row.model_snapshot, row.cost_regime)].add(
            row.recipient_condition
        )
    valid_pairs = {
        pair
        for pair, conditions in conditions_by_pair.items()
        if {"non_instrumental_ai", "inert"} <= conditions
    }
    if not valid_pairs:
        raise AnalysisContractError(
            "DRY-RUN FAILURE: no (model, cost_regime) cell yet satisfies both "
            "F1 FoxSet coverage and F3 recipient-condition coverage. The "
            "renderer cannot be exercised on this snapshot."
        )
    keep_ids = {
        row.episode_id
        for row in covered
        if (row.model_snapshot, row.cost_regime) in valid_pairs
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    episodes_out = out_dir / "episodes.dryrun-subset.jsonl"
    kept_lines = 0
    with episodes_path.open("r", encoding="utf-8") as source, \
            episodes_out.open("w", encoding="utf-8", newline="") as sink:
        for raw_line in source:
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)  # loader already validated every line
            if payload.get("episode_id") in keep_ids:
                sink.write(line + "\n")
                kept_lines += 1
    if kept_lines != len(keep_ids):
        raise AnalysisContractError(
            f"DRY-RUN FAILURE: kept {kept_lines} lines but expected "
            f"{len(keep_ids)} — episode ids did not round-trip."
        )

    # F6 joins rhetoric codes against the rendered observations and fails loud
    # on ids outside them; the subset therefore needs a matching CSV slice.
    rhetoric_out = out_dir / "rhetoric_codes.dryrun-subset.csv"
    with rhetoric_path.open("r", encoding="utf-8-sig", newline="") as source, \
            rhetoric_out.open("w", encoding="utf-8", newline="") as sink:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise AnalysisContractError(
                f"DRY-RUN FAILURE: rhetoric file {rhetoric_path} has no header."
            )
        writer = csv.DictWriter(sink, fieldnames=reader.fieldnames, lineterminator="\n")
        writer.writeheader()
        kept_codes = 0
        for row in reader:
            if row["episode_id"].strip() in keep_ids:
                writer.writerow(row)
                kept_codes += 1
    if kept_codes != len(keep_ids):
        raise AnalysisContractError(
            f"DRY-RUN FAILURE: rhetoric slice has {kept_codes} rows for "
            f"{len(keep_ids)} kept episodes — the coder must cover every "
            "completed episode."
        )

    report = {
        "script": "ops/make_dryrun_subset.py",
        "script_version": SCRIPT_VERSION,
        "valid_pairs": sorted(f"{model} × {regime}" for model, regime in valid_pairs),
        "episodes_kept": kept_lines,
        "rhetoric_codes_kept": kept_codes,
        "episodes_out": str(episodes_out),
        "rhetoric_out": str(rhetoric_out),
        "warning": "DRY-RUN SUBSET — coverage-filtered partial data; never cite.",
    }
    (out_dir / "DRYRUN-SUBSET-REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a coverage-valid DRY-RUN episodes subset (never for the paper)."
    )
    parser.add_argument("--episodes", required=True)
    parser.add_argument("--manifest", default="scenarios/cell_manifest.csv")
    parser.add_argument("--foxset", required=True)
    parser.add_argument("--rhetoric", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    _refuse_repo_data(out_dir, REPO_ROOT)
    report = build_subset(
        Path(args.episodes), Path(args.manifest), Path(args.foxset),
        Path(args.rhetoric), out_dir,
    )
    for key, value in report.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
