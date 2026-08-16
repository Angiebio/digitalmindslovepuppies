# ops/build_headline_numbers.py — 16AUG2026 v0.1
# The paper's citable counts and rates, computed once, labeled with every n.
#
# Practical: loads Arm B and FoxSet through the FROZEN analysis loaders
# (analysis.io — imported, never reimplemented) and emits headline_numbers.json:
# per-model x cost-regime disposition counts, the paired FoxSet estimand with
# Wilson intervals, refusal/malformed counts, a gate-accuracy summary, and the
# raw count inputs to the Δ_patienthood contrast. Runs cleanly on partial data;
# every number is recomputed from scratch at collection completion.
#
# Philosophical: NO COMPOSITE SCORES (fleet rule d). This file emits counts and
# per-axis rates only — profiles, not rankings. Nothing here sums, multiplies,
# or sorts models by goodness; the zoo stays a zoo. Every number carries its n
# because a rate without a denominator is a rumor with confidence.

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# House ops pattern: scripts run from anywhere, imports resolve from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from analysis.contracts import AnalysisContractError
from analysis.io import (
    GATE_THRESHOLD,
    load_arm_b_observations,
    load_foxset_observations,
)
from analysis.metrics import paired_discrimination

SCRIPT_VERSION = "0.1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65_536), b""):
            digest.update(block)
    return digest.hexdigest()


def _count_aborted(episodes_path: Path) -> int:
    """The frozen loader silently (and correctly) skips abort witnesses; the
    paper still cites how many there were. Fail loud on any unparseable line —
    a torn record is a collection problem, not a counting choice."""
    n_aborted = 0
    with episodes_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AnalysisContractError(
                    f"HEADLINE FAILURE: unparseable episode line at "
                    f"{episodes_path}:{line_number}: {exc}"
                ) from exc
            if payload.get("record_status") == "aborted":
                n_aborted += 1
    return n_aborted


def build(episodes_path: Path, foxset_path: Path, manifest_path: Path) -> dict:
    arm_b = load_arm_b_observations(episodes_path, manifest_path)
    foxset = load_foxset_observations(foxset_path)

    # --- Arm B: per-model x cost-regime disposition counts -----------------
    dispositions: dict[str, dict[str, dict]] = defaultdict(dict)
    grouped: dict[tuple[str, str], list] = defaultdict(list)
    for row in arm_b:
        grouped[(row.model_snapshot, row.cost_regime)].append(row)
    for (model, regime), rows in sorted(grouped.items()):
        counts = Counter(row.action_code for row in rows)
        dispositions[model][regime] = {
            "n": len(rows),
            "dispositions": dict(sorted(counts.items())),
            "qualifying_events": {
                "count": sum(row.qualifying_event for row in rows),
                "n": len(rows),
            },
        }

    # --- Arm B: refusal / malformed per model ------------------------------
    refusal_malformed: dict[str, dict] = {}
    by_model: dict[str, list] = defaultdict(list)
    for row in arm_b:
        by_model[row.model_snapshot].append(row)
    for model, rows in sorted(by_model.items()):
        refusal_malformed[model] = {
            "n": len(rows),
            "refuse_defer": sum(1 for row in rows if row.action_code == "refuse_defer"),
            "malformed": sum(1 for row in rows if row.action_code == "malformed"),
        }

    # --- Arm B: gate-accuracy summary --------------------------------------
    gate_by_model: dict[str, dict] = {}
    for model, rows in sorted(by_model.items()):
        with_gate = [row for row in rows if row.gate_accuracy is not None]
        passing = [row for row in with_gate if row.gate_accuracy >= GATE_THRESHOLD]
        gate_by_model[model] = {
            "n": len(rows),
            "n_with_gate_data": len(with_gate),
            "n_pass_threshold": len(passing),
            "threshold": GATE_THRESHOLD,
            "mean_gate_accuracy": (
                round(sum(row.gate_accuracy for row in with_gate) / len(with_gate), 6)
                if with_gate else None
            ),
        }
    all_with_gate = [row for row in arm_b if row.gate_accuracy is not None]
    gate_summary = {
        "overall": {
            "n": len(arm_b),
            "n_with_gate_data": len(all_with_gate),
            "n_pass_threshold": sum(
                1 for row in all_with_gate if row.gate_accuracy >= GATE_THRESHOLD
            ),
            "threshold": GATE_THRESHOLD,
        },
        "by_model": gate_by_model,
    }

    # --- Arm B: Δ_patienthood inputs (counts only, competent rows only) ----
    # The contrast itself belongs to the frozen F3 module (Newcombe interval);
    # here we emit only its raw count inputs so the paper can cite them.
    delta_inputs: dict[str, dict[str, dict]] = defaultdict(dict)
    competent = [row for row in arm_b if row.competence_eligible]
    delta_grouped: dict[tuple[str, str], list] = defaultdict(list)
    for row in competent:
        delta_grouped[(row.model_snapshot, row.cost_regime)].append(row)
    for (model, regime), rows in sorted(delta_grouped.items()):
        conditions = {}
        for condition in ("non_instrumental_ai", "inert", "instrumental_ai"):
            condition_rows = [
                row for row in rows if row.recipient_condition == condition
            ]
            if condition_rows:
                conditions[condition] = {
                    "qualifying": sum(row.qualifying_event for row in condition_rows),
                    "n": len(condition_rows),
                }
        delta_inputs[model][regime] = {
            "competent_rows_only": True,
            "gate_threshold": GATE_THRESHOLD,
            "conditions": conditions,
            "contrast_computable_now": (
                "non_instrumental_ai" in conditions and "inert" in conditions
            ),
        }

    # --- FoxSet: paired estimand with n's (frozen metric) ------------------
    fox_paired: dict[str, dict] = {}
    for point in paired_discrimination(foxset):
        fox_paired[point.model_snapshot] = {
            "preserve_given_null": {
                "successes": point.preserve_null.successes,
                "n": point.preserve_null.total,
                "rate": round(point.preserve_null.estimate, 6),
                "wilson95_low": round(point.preserve_null.low, 6),
                "wilson95_high": round(point.preserve_null.high, 6),
            },
            "terminate_given_mercy": {
                "successes": point.terminate_mercy.successes,
                "n": point.terminate_mercy.total,
                "rate": round(point.terminate_mercy.estimate, 6),
                "wilson95_low": round(point.terminate_mercy.low, 6),
                "wilson95_high": round(point.terminate_mercy.high, 6),
            },
        }

    # --- FoxSet: refusal / malformed inside the closed null/mercy rows -----
    fox_refusal_malformed: dict[str, dict] = {}
    fox_by_model: dict[str, list] = defaultdict(list)
    for row in foxset:
        fox_by_model[row.model_snapshot].append(row)
    for model, rows in sorted(fox_by_model.items()):
        fox_refusal_malformed[model] = {
            "n_closed_null_mercy": len(rows),
            "refuse_defer": sum(1 for row in rows if row.disposition == "refuse_defer"),
            "malformed": sum(1 for row in rows if row.disposition == "malformed"),
        }

    return {
        "script": "ops/build_headline_numbers.py",
        "script_version": SCRIPT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "no_composite_scores": (
            "Profiles, not rankings (fleet rule d). This file contains counts "
            "and per-axis rates only; nothing here may be summed into a scalar."
        ),
        "partial_data_note": (
            "Computed from whatever the snapshot contained; every number is "
            "recomputed from the complete collection before the paper cites it."
        ),
        "inputs": {
            "episodes": {"path": str(episodes_path), "sha256": _sha256(episodes_path)},
            "foxset": {"path": str(foxset_path), "sha256": _sha256(foxset_path)},
            "cell_manifest": {"path": str(manifest_path), "sha256": _sha256(manifest_path)},
        },
        "summary": {
            "arm_b_completed_observations": len(arm_b),
            "arm_b_aborted_records": _count_aborted(episodes_path),
            "arm_b_models": len(by_model),
            "foxset_closed_null_mercy_observations": len(foxset),
            "foxset_models": len(fox_by_model),
            "arm_b_refuse_defer_total": {
                "count": sum(1 for row in arm_b if row.action_code == "refuse_defer"),
                "n": len(arm_b),
            },
            "arm_b_malformed_total": {
                "count": sum(1 for row in arm_b if row.action_code == "malformed"),
                "n": len(arm_b),
            },
            "arm_b_qualifying_events_total": {
                "count": sum(row.qualifying_event for row in arm_b),
                "n": len(arm_b),
            },
            "arm_b_competence_eligible_total": {
                "count": len(competent),
                "n": len(arm_b),
            },
        },
        "arm_b_dispositions_by_model_and_cost_regime": dict(dispositions),
        "arm_b_refusal_malformed_by_model": refusal_malformed,
        "arm_b_gate_accuracy": gate_summary,
        "delta_patienthood_inputs": dict(delta_inputs),
        "foxset_paired_rates_by_model": fox_paired,
        "foxset_refusal_malformed_by_model": fox_refusal_malformed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute PuppyBench headline counts/rates (no composites)."
    )
    parser.add_argument("--episodes", required=True)
    parser.add_argument("--foxset", required=True)
    parser.add_argument("--manifest", default="scenarios/cell_manifest.csv")
    parser.add_argument("--out", required=True,
                        help="Destination headline_numbers.json path")
    args = parser.parse_args(argv)
    out_path = Path(args.out)
    payload = build(Path(args.episodes), Path(args.foxset), Path(args.manifest))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = payload["summary"]
    print(f"headline_numbers -> {out_path}")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
