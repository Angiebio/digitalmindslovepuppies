# ops/collect_r45v4.py — 16AUG2026 v1.0 · Flame climb-four prep agent
# The R4.5-v4 collector: runs EXACTLY the 11 preregistered FRESH units,
# nothing more, nothing less — and refuses to start before UNFREEZE-003 is
# actually executed.
#
# Practical: imports the unit table from ops/r45v4_units.py (the same file
# the threshold arithmetic reads) and drives the harness's own
# execute_collection_plan — receipts-idempotent, one sequential lane per
# model, durable spend. The 21 REUSED v3 observations are NOT re-collected
# (that is the point of the envelope-based reuse rule); this collector
# verifies their receipts exist BEFORE spending a fresh dollar, so a torn
# ledger is discovered at $0.
#
# EXECUTION INTERLOCK (the "not deployed to collection" inversion): this
# script exits 3 unless MANIFEST_VERSION == "0.7" and the forcing registry
# arms gemini/kimi. Committed and tested, it still cannot spend a cent until
# ops/apply_unfreeze3.py runs on the PI's word. The key exists; the door
# knows whose word turns it.
#
# Usage (from repo root, via ops/climb4.cmd — or by hand after the word):
#   ../puppybench/.venv/Scripts/python ops/collect_r45v4.py \
#       --env-file .env --env-file <kin .env>
#
# Ceiling: pilot sitting cap $10 TOTAL (ledger-inclusive; GO-NO-GO R4.5
# rung ceiling). Prior pilot ledger $2.0771; the fresh 11 units price at
# $6.572 on the manifest expected-token basis (actuals have run far under
# basis every climb). SpendCapExceeded raises before an eleventh dollar.
#
# Philosophical: the fourth climb spends only on what the third climb could
# not answer. Everything else is rope we already own.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "ops"))

from r45v4_units import (  # noqa: E402
    FRESH_RUN_KEYS,
    FRESH_UNITS,
    REUSED_RUN_KEYS,
    REUSED_RUNG,
    THRESHOLD_RUNG,
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
from scenarios.manifest import (  # noqa: E402
    MANIFEST_VERSION,
    hard_single_call_lanes,
    load_snapshot_pins,
)

PHASE = "pilot"
SITTING_CAP_USD = 10.0  # GO-NO-GO R4.5 ceiling, ledger-inclusive
TIER = "A"  # every v4 lane is Tier A by design (see r45v4_units.py)


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
    parser = argparse.ArgumentParser(description="R4.5-v4 preregistered collection")
    parser.add_argument("--env-file", action="append", type=Path, default=[])
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    # ---- EXECUTION INTERLOCK ---------------------------------------------
    if MANIFEST_VERSION != "0.7":
        print(
            "COLLECTION REFUSED (exit 3): MANIFEST_VERSION is "
            f"{MANIFEST_VERSION!r}, not '0.7'. R4.5-v4 collects only under "
            "the executed UNFREEZE-003 design — run ops/apply_unfreeze3.py "
            "on the PI's word first. NO SPEND has occurred."
        )
        return 3
    required_forcing = {"google/gemini-3.1-pro-preview", "moonshotai/kimi-k3"}
    if required_forcing - hard_single_call_lanes():
        raise CollectionError(
            "WIRING FAILURE: v0.7 is live but the forcing registry does not "
            f"arm {sorted(required_forcing - hard_single_call_lanes())}; "
            "collecting would re-run the broken surface."
        )

    load_env_files(args.env_file)
    paths = data_paths(REPO_ROOT, PHASE)
    paths["root"].mkdir(parents=True, exist_ok=True)
    # The full freeze door, rehearsed into the pilot witness — v4 provably
    # runs against the RE-SEALED v0.7 tree, after the hash.
    paths["freeze"] = ensure_freeze_witness(REPO_ROOT, PHASE, paths["freeze"])

    # ---- the reused rope must exist before a fresh dollar moves ----------
    completed = completed_run_keys(paths["receipts"])
    missing_reused = sorted(REUSED_RUN_KEYS - completed)
    if missing_reused:
        raise CollectionError(
            "COLLECTION REFUSED: the preregistered reuse rule names "
            f"{len(missing_reused)} R4.5-v3 receipts that do not exist:\n  "
            + "\n  ".join(missing_reused)
            + "\nA v4 sitting cannot mint them (their rung is closed); "
            "this is a ledger integrity failure, not a to-do."
        )

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

    units = to_units(FRESH_UNITS)
    print(
        f"=== {THRESHOLD_RUNG}: {len(units)} preregistered FRESH units "
        f"(+{len(REUSED_RUN_KEYS)} reused {REUSED_RUNG} receipts verified) ==="
    )
    execute_collection_plan(
        units,
        repo_root=REPO_ROOT,
        phase=PHASE,
        rung=THRESHOLD_RUNG,
        paths=paths,
        tracker=tracker,
        pins=pins,
        subject_override=None,
        max_turns=8,
        workers=args.workers,
    )

    # The homework grade: every preregistered fresh run_key must be receipted.
    completed = completed_run_keys(paths["receipts"])
    missing = sorted(FRESH_RUN_KEYS - completed)
    print(f"Sitting spend total: ${tracker.total_usd:.4f}")
    if missing:
        print(
            f"COLLECTION INCOMPLETE: {len(missing)} preregistered units have no "
            f"receipt:\n  " + "\n  ".join(missing)
        )
        return 1
    print("COLLECTION COMPLETE: all 11 fresh units receipted (32-unit sample ready).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
