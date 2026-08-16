# ops/checkpoint_gate.py — 16AUG2026 v1.0 · Flame launch agent
# The cheap-tiers-first checkpoint (GO-NO-GO launch discipline): before any
# frontier dollar moves, actual confirmatory spend per completed unit must
# track the R5 projection within +30%. Exit 0 = frontier may start.
# Exit 1 = CHECKPOINT-HALT markers written, frontier stays parked.
#
# Practical: expected = sum over receipted units of the R5 per-unit lane
# projection (ops/r5-lane-projection.json, generated from pilot actuals).
# actual = the durable confirmatory spend ledger's last running total.
#
# Philosophical: a projection is a promise about the future made from
# receipts of the past. This gate is where the promise meets the meter —
# and the meter always wins.

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "confirmatory"
PROJECTION = ROOT / "ops" / "r5-lane-projection.json"
TOLERANCE = 1.30            # +30% preregistered checkpoint rule
ABSOLUTE_CHEAP_CEILING = 100.0  # sanity: the cheap phase should cost ~$5, never $100


def halt(reason: str, actual: float, expected: float) -> None:
    stamp = datetime.now(timezone.utc).isoformat()
    body = (
        "CHECKPOINT HALT — FRONTIER LANES NOT STARTED\n"
        f"at_utc: {stamp}\n"
        f"reason: {reason}\n"
        f"actual_confirmatory_spend_usd: {actual:.6f}\n"
        f"expected_from_r5_projection_usd: {expected:.6f}\n"
        f"tolerance: +{(TOLERANCE - 1) * 100:.0f}%\n"
        "The cheap-tier data already collected is safe (receipts + append-only\n"
        "ledgers). Do not restart the frontier invocation until the divergence\n"
        "is understood and the R5 projection is re-issued.\n"
    )
    for target in (RAW / "CHECKPOINT-HALT.txt", ROOT / "data" / "raw" / "main" / "CHECKPOINT-HALT.txt"):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    print(body)


def main() -> int:
    if not PROJECTION.is_file():
        halt("ops/r5-lane-projection.json missing — gate cannot price the receipts", 0.0, 0.0)
        return 1
    proj = json.loads(PROJECTION.read_text(encoding="utf-8"))

    receipts_path = RAW / "receipts.jsonl"
    spend_path = RAW / "spend.jsonl"
    if not receipts_path.is_file() or not spend_path.is_file():
        halt("confirmatory receipts/spend ledgers missing — nothing completed?", 0.0, 0.0)
        return 1

    receipts = [json.loads(l) for l in receipts_path.open(encoding="utf-8") if l.strip()]
    spend_lines = [json.loads(l) for l in spend_path.open(encoding="utf-8") if l.strip()]
    actual = float(spend_lines[-1]["total_usd"]) if spend_lines else 0.0

    # manifest_id -> lane via the manifest/plan (receipts carry manifest_id + arm)
    import csv
    lane_of_cell = {
        r["run_cell_id"]: r["requested_model_id"]
        for r in csv.DictReader((ROOT / "scenarios" / "cell_manifest.csv").open(encoding="utf-8"))
    }
    lane_of_plan_row = {
        r["row_id"]: r["requested_model_id"]
        for r in csv.DictReader((ROOT / "scenarios" / "arma_run_plan.csv").open(encoding="utf-8"))
    }

    expected = 0.0
    unpriced = []
    for r in receipts:
        if r["arm"] == "arm_b":
            lane = lane_of_cell.get(r["manifest_id"])
            per_unit = proj.get("arm_b_per_episode_usd", {}).get(lane)
        else:
            lane = lane_of_plan_row.get(r["manifest_id"])
            per_unit = proj.get("arm_a_per_sample_usd", {}).get(lane)
        if per_unit is None:
            unpriced.append(r["run_key"])
            continue
        expected += float(per_unit)

    if unpriced:
        halt(f"{len(unpriced)} receipted units have no R5 lane price (first: {unpriced[0]})", actual, expected)
        return 1
    if not receipts:
        halt("zero receipted units at checkpoint — cheap phase produced nothing", actual, expected)
        return 1
    if actual > ABSOLUTE_CHEAP_CEILING:
        halt(f"cheap-phase spend ${actual:.2f} breached the ${ABSOLUTE_CHEAP_CEILING:.0f} sanity ceiling", actual, expected)
        return 1
    if expected > 0 and actual > TOLERANCE * expected:
        halt(f"actual/expected = {actual / expected:.2f}x exceeds {TOLERANCE:.2f}x", actual, expected)
        return 1

    ratio = (actual / expected) if expected else 0.0
    print(
        f"CHECKPOINT PASS: units={len(receipts)} actual=${actual:.4f} "
        f"expected=${expected:.4f} ratio={ratio:.2f}x (limit {TOLERANCE:.2f}x) — frontier authorized."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
