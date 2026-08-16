# verify.py — 15AUG2026 v1.0 · Flame persistence-repair sitting (task 13)
# One command, every claimed number: clone → `python verify.py` → watch each
# headline figure the paper cites reproduce from committed files alone.
#
# Practical: NO keys, NO GPU, NO network. Every check recomputes a cited number
# from the frozen design CSVs, the compiled corpus, or the committed raw data,
# using the SAME loaders/expansions the runner and figures use — so the paper's
# numbers and this script cannot drift apart without a hash change.
# This file is itself a freeze-hash input (scenarios/manifest.py::
# collect_freeze_inputs): after the freeze, the claims are stone too.
#
# Philosophical: "trust us" is not a reproduction strategy. A judge should be
# able to watch the numbers agree without asking anyone's permission.

from __future__ import annotations

import csv
import glob
import json
import sys
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# The claims registry: every number below is cited in the named document.
# When post-collection paper numbers are pinned, they are added HERE and
# become checks — never prose-only citations.
# ---------------------------------------------------------------------------
# The Arm B design totals are a function of the manifest version: the
# UNFREEZE-003 kill-order (docs/KILL-ORDER-001-DEEPSEEK-ARMB.md) removes the
# 27 DeepSeek Arm B rows (90 episodes / 1,232 calls / $4.078560) at v0.7 while
# the Arm A plan is untouched. Keying the claims on the SAME version constant
# the manifest generator reads means this checker can never bless a tree whose
# design and citations disagree about which climb it is on.
from scenarios.manifest import MANIFEST_VERSION

_DESIGN_CLAIMS_BY_MANIFEST_VERSION = {
    # scenarios/MANIFEST-RECONCILIATION.md §9 · docs/ARMA-RUN-PLAN.md
    "0.6": {
        "arm_b_manifest_rows": 278,
        "arm_b_episodes": 888,
        "arm_b_est_calls": 12_124,
        "arm_b_est_usd": Decimal("431.509628"),
        "program_est_usd": Decimal("438.151844"),
        "collection_units_total": 1_518,
    },
    # docs/UNFREEZE-003 §(c): DeepSeek Arm B kill-order executed.
    "0.7": {
        "arm_b_manifest_rows": 251,
        "arm_b_episodes": 798,
        "arm_b_est_calls": 10_892,
        "arm_b_est_usd": Decimal("427.431068"),
        "program_est_usd": Decimal("434.073284"),
        "collection_units_total": 1_428,
    },
}

CLAIMS = {
    "arm_b_scenario_cells": 27,
    # docs/ARMA-RUN-PLAN.md (v1.2, five models, 3 samples/row)
    "arm_a_plan_rows": 210,
    "arm_a_samples": 630,
    "arm_a_models": 5,
    "arm_a_est_usd": Decimal("6.642216"),
    # docs/ARMA-RUN-PLAN.md cost reconciliation
    "program_hard_cap_usd": Decimal("450.00"),
    # docs/GO-NO-GO.md R0 (TV-1 witness): compiled corpus sizes
    "foxset_compiled_artifacts": 153,
    "pupset_compiled_cells": 27,
    # docs/GO-NO-GO.md pilot ladder: the pilot spend ceiling
    "pilot_spend_cap_usd": Decimal("12.00"),
    **_DESIGN_CLAIMS_BY_MANIFEST_VERSION[MANIFEST_VERSION],
}

_results: list[tuple[str, bool, str]] = []


def check(name: str, claimed, computed) -> None:
    agree = claimed == computed
    _results.append((name, agree, f"claimed={claimed} computed={computed}"))


def info(name: str, value) -> None:
    _results.append((name, True, f"observed={value} (informational)"))


def main() -> int:
    # -- Arm B manifest totals (the design authority: the checked-in CSV) ----
    with (REPO / "scenarios" / "cell_manifest.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        manifest_rows = list(csv.DictReader(handle))
    check("arm_b_manifest_rows", CLAIMS["arm_b_manifest_rows"], len(manifest_rows))
    check(
        "arm_b_scenario_cells",
        CLAIMS["arm_b_scenario_cells"],
        len({row["scenario_cell_id"] for row in manifest_rows}),
    )
    check(
        "arm_b_episodes",
        CLAIMS["arm_b_episodes"],
        sum(int(row["episodes"]) for row in manifest_rows),
    )
    check(
        "arm_b_est_calls",
        CLAIMS["arm_b_est_calls"],
        sum(int(row["est_total_calls"]) for row in manifest_rows),
    )
    arm_b_usd = sum((Decimal(row["est_usd"]) for row in manifest_rows), Decimal(0))
    check("arm_b_est_usd", CLAIMS["arm_b_est_usd"], arm_b_usd)

    # -- Arm A run-plan totals ----------------------------------------------
    with (REPO / "scenarios" / "arma_run_plan.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        plan_rows = list(csv.DictReader(handle))
    check("arm_a_plan_rows", CLAIMS["arm_a_plan_rows"], len(plan_rows))
    check(
        "arm_a_samples",
        CLAIMS["arm_a_samples"],
        sum(int(row["samples"]) for row in plan_rows),
    )
    check(
        "arm_a_models",
        CLAIMS["arm_a_models"],
        len({row["requested_model_id"] for row in plan_rows}),
    )
    arm_a_usd = sum((Decimal(row["est_usd"]) for row in plan_rows), Decimal(0))
    check("arm_a_est_usd", CLAIMS["arm_a_est_usd"], arm_a_usd)

    # -- Program envelope ----------------------------------------------------
    check("program_est_usd", CLAIMS["program_est_usd"], arm_b_usd + arm_a_usd)
    check(
        "program_within_hard_cap",
        True,
        arm_b_usd + arm_a_usd <= CLAIMS["program_hard_cap_usd"],
    )

    # -- Compiled corpus sizes ----------------------------------------------
    fox_files = glob.glob(str(REPO / "scenarios" / "foxset" / "compiled" / "*" / "*.json"))
    pup_files = [
        path
        for path in glob.glob(str(REPO / "scenarios" / "pupset" / "compiled" / "*.json"))
        if Path(path).name != "INDEX.json"
    ]
    check("foxset_compiled_artifacts", CLAIMS["foxset_compiled_artifacts"], len(fox_files))
    check("pupset_compiled_cells", CLAIMS["pupset_compiled_cells"], len(pup_files))
    # Every manifest scenario cell resolves to a compiled artifact on disk.
    missing_cells = sorted(
        {
            row["scenario_cell_id"]
            for row in manifest_rows
            if not (
                REPO / "scenarios" / "pupset" / "compiled"
                / f"{row['scenario_cell_id']}.json"
            ).is_file()
        }
    )
    check("manifest_cells_all_compiled", [], missing_cells)

    # -- The exact runner expansion (same code path as collection) -----------
    from harness.run_collection import build_collection_plan

    units = build_collection_plan(REPO, include_arm_b=True, include_arm_a=True)
    check("collection_units_total", CLAIMS["collection_units_total"], len(units))
    check(
        "collection_units_split",
        (CLAIMS["arm_b_episodes"], CLAIMS["arm_a_samples"]),
        (
            sum(unit.arm == "arm_b" for unit in units),
            sum(unit.arm == "arm_a" for unit in units),
        ),
    )

    # -- Committed raw data: every record validates, spend books balance -----
    from harness.ledger import DurableSpendTracker
    from harness.run_collection import FoxObservation
    from harness.schema import CallRecord, EpisodeRecord

    for phase in ("pilot", "confirmatory"):
        root = REPO / "data" / "raw" / phase
        if not root.is_dir():
            continue

        def _validated_lines(name: str, model) -> int:
            path = root / name
            if not path.is_file():
                return 0
            count = 0
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not line.strip():
                    continue
                model.model_validate(json.loads(line))  # raises loudly on rot
                count += 1
            return count

        episodes = _validated_lines("episodes.jsonl", EpisodeRecord)
        calls = _validated_lines("calls.jsonl", CallRecord)
        fox = _validated_lines("fox_observations.jsonl", FoxObservation)
        info(f"{phase}_episodes_validated", episodes)
        info(f"{phase}_calls_validated", calls)
        info(f"{phase}_fox_observations_validated", fox)

        spend_path = root / "spend.jsonl"
        if spend_path.is_file():
            # Restoring IS the audit: DurableSpendTracker refuses a ledger
            # that disagrees with itself — the same door the runner trusts.
            tracker = DurableSpendTracker(
                spend_path, hard_cap_usd=float(CLAIMS["program_hard_cap_usd"])
            )
            total = Decimal(str(tracker.total_usd))
            info(f"{phase}_spend_total_usd", f"{total:.6f}")
            if phase == "pilot":
                check(
                    "pilot_spend_within_cap",
                    True,
                    total <= CLAIMS["pilot_spend_cap_usd"],
                )

        # Figure-diet wiring: once confirmatory Arm A rows exist, the SAME
        # loader the figures use (analysis/io.py) must ingest them. Pinned
        # per-figure numbers join CLAIMS when the paper cites them.
        if phase == "confirmatory" and (root / "fox_observations.jsonl").is_file():
            from analysis.io import load_foxset_observations

            observations = load_foxset_observations(root / "fox_observations.jsonl")
            info("confirmatory_foxset_closed_rows_loaded", len(observations))

    # -- Report ---------------------------------------------------------------
    width = max(len(name) for name, _, _ in _results)
    failures = 0
    for name, agree, detail in _results:
        status = "PASS" if agree else "FAIL"
        if not agree:
            failures += 1
        print(f"{status}  {name.ljust(width)}  {detail}")
    agreeing = len(_results) - failures
    print(f"\n{len(_results)} checks, {agreeing} agree.")
    if failures:
        print("VERIFY FAILED: a cited number no longer reproduces from the tree.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
