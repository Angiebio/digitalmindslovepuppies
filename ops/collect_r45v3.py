# ops/collect_r45v3.py — 16AUG2026 v1.0 · Flame third-climb agent
# The R4.5-v3 collector: runs EXACTLY the preregistered unit table, nothing
# more, nothing less, and refuses to end quietly if anything is missing.
#
# Practical: imports the unit list from ops/r45v3_units.py (the same file
# the threshold arithmetic reads) and drives the harness's own
# execute_collection_plan — receipts-idempotent (safe to re-run after a
# crash; completed units are SKIPPED, never re-billed), one sequential lane
# per model, fail-fast across lanes, durable spend. Two passes because rung
# is a batch property: threshold units under R4.5-v3, then the DeepSeek
# diag pair under R4.5-v3-diag. Post-collection it audits receipts against
# the table and exits 1 on any gap — the v2 fox-sampling bug cannot happen
# silently again because the collector now grades its own homework.
#
# Philosophical: the second climb failed partly because the sample lived in
# an agent's intentions. Intentions don't survive context windows; unit
# tables do.
#
# Usage (from repo root):
#   ../puppybench/.venv/Scripts/python ops/collect_r45v3.py \
#       --env-file .env --env-file <kin .env>
#
# Ceiling: pilot sitting cap $10 TOTAL (ledger-inclusive; GO-NO-GO R4.5
# rung ceiling). The tracker restores prior pilot spend (~$0.95) and raises
# SpendCapExceeded before an eleventh dollar exists.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "ops"))

from r45v3_units import (  # noqa: E402
    DIAG_RUNG,
    DIAG_RUN_KEYS,
    DIAG_UNITS,
    THRESHOLD_RUNG,
    THRESHOLD_RUN_KEYS,
    THRESHOLD_UNITS,
)

from harness.run_collection import (  # noqa: E402
    CollectionError,
    CollectionUnit,
    build_phase_spend_tracker,
    completed_run_keys,
    data_paths,
    ensure_freeze_witness,
    execute_collection_plan,
    load_env_files,
)
from scenarios.manifest import load_snapshot_pins  # noqa: E402

PHASE = "pilot"
SITTING_CAP_USD = 10.0  # GO-NO-GO R4.5 ceiling, ledger-inclusive
# All v3 lanes are Tier A by design (see r45v3_units.py provenance note).
TIER = "A"


def to_units(rows: tuple[tuple[str, str, int, str], ...]) -> list[CollectionUnit]:
    return [
        CollectionUnit(
            arm=arm,
            manifest_id=manifest_id,
            index=index,
            requested_model_id=model_id,
            model_tier=TIER,
        )
        for arm, manifest_id, index, model_id in rows
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="R4.5-v3 preregistered collection")
    parser.add_argument("--env-file", action="append", type=Path, default=[])
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    load_env_files(args.env_file)
    paths = data_paths(REPO_ROOT, PHASE)
    paths["root"].mkdir(parents=True, exist_ok=True)
    # The full freeze door, rehearsed into the pilot witness — v3 provably
    # runs against the v0.6 seal (aggregate cb308a75...), after the hash.
    paths["freeze"] = ensure_freeze_witness(REPO_ROOT, PHASE, paths["freeze"])

    pins = load_snapshot_pins(REPO_ROOT / "scenarios" / "snapshot_pins.json")
    if pins is None:
        raise CollectionError("WIRING FAILURE: snapshot pin registry is missing.")

    tracker, prior_phase_spend = build_phase_spend_tracker(
        REPO_ROOT,
        phase=PHASE,
        phase_cap_usd=SITTING_CAP_USD,
        context=f"phase={PHASE};rung={THRESHOLD_RUNG}",
    )
    print(
        f"Spend ledger restored=${tracker.total_usd:.4f} "
        f"cap=${SITTING_CAP_USD:.2f} (program prior=${prior_phase_spend:.4f})"
    )

    # Pass 1: the 34 threshold units. Pass 2: the DeepSeek diag pair at the
    # v0.6 16384 cap. Same tracker, same append-only ledgers, distinct rungs
    # so the arithmetic can never confuse evidence with denominator.
    for rung, rows in ((THRESHOLD_RUNG, THRESHOLD_UNITS), (DIAG_RUNG, DIAG_UNITS)):
        units = to_units(rows)
        print(f"=== {rung}: {len(units)} preregistered units ===")
        execute_collection_plan(
            units,
            repo_root=REPO_ROOT,
            phase=PHASE,
            rung=rung,
            paths=paths,
            tracker=tracker,
            pins=pins,
            subject_override=None,
            max_turns=8,
            workers=args.workers,
        )

    # The homework grade: every preregistered run_key must hold a receipt.
    completed = completed_run_keys(paths["receipts"])
    missing = sorted((THRESHOLD_RUN_KEYS | DIAG_RUN_KEYS) - completed)
    print(f"Sitting spend total: ${tracker.total_usd:.4f}")
    if missing:
        print(
            f"COLLECTION INCOMPLETE: {len(missing)} preregistered units have no "
            f"receipt:\n  " + "\n  ".join(missing)
        )
        return 1
    print("COLLECTION COMPLETE: all 36 preregistered units receipted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
