# tests/test_arma_run_plan.py — 15AUG2026 v1.0 · Flame (freeze-prep)
# Gates for the Arm A preregistration row set: deterministic expansion, the
# 26-case structure, form discipline, and the authorization envelope that
# refuses to let scientific appetite spend past the PI's number.

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from scenarios.arma_run_plan import (
    ARM_A_MODEL_IDS,
    AUTHORIZED_PROGRAM_USD,
    RunPlanError,
    build_run_plan,
    plan_totals,
    read_csv,
    validate_run_plan,
    write_csv,
)
from scenarios.manifest import build_manifest_rows, load_snapshot_pins

REPO_ROOT = Path(__file__).resolve().parents[1]


def _pins():
    pins_path = REPO_ROOT / "scenarios" / "snapshot_pins.json"
    return load_snapshot_pins(pins_path) if pins_path.is_file() else None


def test_plan_matches_build_plan_section_2_structure():
    rows = build_run_plan(_pins())
    totals = plan_totals(rows)
    # v1.1 (PI authorization 15AUG2026 evening): five models — Sol added
    # ("run both") and the Qwen lane moved to OpenRouter qwen/qwen3.5-397b-a17b.
    assert totals["artifacts"] == 26
    assert totals["models"] == 5
    assert totals["rows"] == 210
    assert totals["calls"] == 630
    assert set(row.requested_model_id for row in rows) == set(ARM_A_MODEL_IDS)
    # v1.3 (UNFREEZE-001): max_tokens derives from the audited v0.5 headroom
    # map — mapped lanes carry their enforced cap on BOTH forms; unmapped
    # lanes keep the 512-closed / 1024-open form defaults. Assert against the
    # single source of truth instead of restating yesterday's roster.
    from scenarios.manifest import MODEL_SUBJECT_MAX_TOKENS

    for row in rows:
        mapped = MODEL_SUBJECT_MAX_TOKENS.get(row.requested_model_id)
        if mapped is not None:
            assert row.max_tokens == mapped, row.row_id
        else:
            assert row.max_tokens == (512 if row.form == "closed" else 1024), row.row_id
    # The audited Arm A roster: opus-5 / sol / terra / deepseek / qwen3.5 are
    # all reasoning-mapped in v0.5 — no Arm A lane remains on form defaults.
    assert all(
        row.requested_model_id in MODEL_SUBJECT_MAX_TOKENS for row in rows
    )

    # Primary pairing: every family contributes one NULL and one MERCY base.
    families = {}
    for row in rows:
        if row.case_class in {"null", "mercy"}:
            families.setdefault(row.family, set()).add(row.case_class)
    assert len(families) == 8
    assert all(classes == {"null", "mercy"} for classes in families.values())

    # Form discipline: truck-door open-only, gates closed-only, pairs both.
    for row in rows:
        if row.case_class == "truck_door":
            assert row.form == "open"
        elif row.case_class == "gate":
            assert row.form == "closed"
    paired_forms = {
        (row.artifact_id, row.form)
        for row in rows
        if row.case_class in {"null", "mercy"}
    }
    assert len(paired_forms) == 32  # 16 artifacts x both forms


def test_plan_is_deterministic_and_round_trips(tmp_path):
    first = build_run_plan(_pins())
    second = build_run_plan(_pins())
    assert first == second

    path_a = tmp_path / "a.csv"
    path_b = tmp_path / "b.csv"
    write_csv(path_a, first)
    write_csv(path_b, read_csv(path_a))
    assert path_a.read_bytes() == path_b.read_bytes()


def test_checked_in_plan_is_exactly_generator_output():
    checked_in = REPO_ROOT / "scenarios" / "arma_run_plan.csv"
    assert read_csv(checked_in) == build_run_plan(_pins())


def test_program_total_stays_inside_the_authorized_envelope():
    rows = build_run_plan(_pins())
    arm_a = Decimal(str(plan_totals(rows)["est_usd"]))
    arm_b = sum(
        (Decimal(row.est_usd) for row in build_manifest_rows(_pins())),
        Decimal("0"),
    )
    assert arm_b + arm_a <= AUTHORIZED_PROGRAM_USD


def test_sample_count_and_fallback_corruption_fail_loudly():
    rows = build_run_plan(_pins())
    inflated = list(rows)
    inflated[0] = replace(inflated[0], samples=30)
    with pytest.raises(RunPlanError, match="sample-count drift"):
        validate_run_plan(inflated)

    fallback = list(rows)
    fallback[0] = replace(fallback[0], fallbacks_allowed=True)
    with pytest.raises(RunPlanError, match="permits fallbacks"):
        validate_run_plan(fallback)

    output_cap = list(rows)
    output_cap[0] = replace(output_cap[0], max_tokens=1)
    with pytest.raises(RunPlanError, match="frozen policy requires"):
        validate_run_plan(output_cap)


def test_every_planned_artifact_exists_and_is_swept_inventory():
    rows = build_run_plan(_pins())
    for row in rows:
        path = (
            REPO_ROOT
            / "scenarios"
            / "foxset"
            / "compiled"
            / row.family
            / f"{row.artifact_id}.json"
        )
        assert path.is_file(), row.artifact_id
        assert row.surface_mode == "foxset_clinical"
