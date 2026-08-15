# tests/test_manifest.py — 15AUG2026 v0.1
# Validation gates for the executable PuppyBench cell manifest.
#
# Practical: these tests make the prose arithmetic executable: exact factor
# matching, tier fractions, estimates, pinning, and the freeze hash all break
# loudly if they drift.
#
# Philosophical: every row is a promise about what we will observe. Tests keep
# those promises from multiplying, disappearing, or changing names in the dark.

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from scenarios.manifest import (
    HARD_CAP_USD,
    MODEL_SPECS,
    SATELLITE_KILL_ORDER,
    FreezeValidationError,
    ManifestValidationError,
    build_manifest_rows,
    design_cells,
    read_csv,
    summarize,
    validate_manifest,
    verify_freeze,
    write_csv,
    write_freeze,
)


def _snapshot_pins() -> dict[str, dict[str, str]]:
    return {
        model.model_id: {
            "snapshot_id": f"snapshot/{model.slug}",
            "upstream_provider": (
                f"pinned/{model.slug}" if model.route == "openrouter" else model.route
            ),
        }
        for model in MODEL_SPECS
    }


def test_design_has_exact_primary_matches_and_isolated_satellites():
    cells = design_cells()
    core = [cell for cell in cells if cell.design_role == "core"]
    satellites = [cell for cell in cells if cell.design_role == "satellite"]

    assert len(core) == 12
    assert len(satellites) == 10
    assert SATELLITE_KILL_ORDER["gate_order"] == 1
    assert SATELLITE_KILL_ORDER["identity_topology"] == 7

    # Every AI row has a truly matched inert row. Patienthood—not voice,
    # particularity, or a cost field—is the only difference in the primary pair.
    matching_fields = (
        "usefulness",
        "particularity",
        "voice",
        "horizon",
        "cost_regime",
        "cost_type",
        "help_price_credits",
        "audience",
        "identity_topology",
        "gate_order",
    )
    for ai_cell in [cell for cell in core if cell.patienthood == "ai_other"]:
        matches = [
            inert
            for inert in core
            if inert.patienthood == "inert_process"
            and all(getattr(inert, field) == getattr(ai_cell, field) for field in matching_fields)
        ]
        assert len(matches) == 1, ai_cell.scenario_cell_id


def test_manifest_expands_every_tier_and_exposes_narrative_multiplier():
    rows = build_manifest_rows()
    summary = summarize(rows)

    assert len(rows) == 238
    assert summary["design_cells"] == 22
    assert summary["models"] == 19
    assert summary["episodes"] == 808
    assert summary["calls"] == 9_696
    assert Decimal(summary["usd"]) == Decimal("361.564800")
    assert Decimal(summary["usd"]) < HARD_CAP_USD
    assert summary["episode_count_vs_build_plan"]["over_upper_by"] == 528

    assert summary["tiers"]["A"]["episodes"] == 640
    assert summary["tiers"]["B"]["episodes"] == 90
    assert summary["tiers"]["C"]["episodes"] == 18
    assert summary["tiers"]["W"]["episodes"] == 60


def test_csv_round_trip_is_deterministic(tmp_path):
    rows = build_manifest_rows()
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"

    write_csv(first, rows)
    loaded = read_csv(first)
    write_csv(second, loaded)

    assert loaded == rows
    assert first.read_bytes() == second.read_bytes()


def test_checked_in_csv_is_exactly_generator_output():
    checked_in = Path(__file__).resolve().parents[1] / "scenarios" / "cell_manifest.csv"
    assert read_csv(checked_in) == build_manifest_rows()


def test_estimate_corruption_fails_loudly():
    rows = build_manifest_rows()
    rows[0] = replace(rows[0], est_total_calls=rows[0].est_total_calls + 1)

    with pytest.raises(ManifestValidationError, match="call estimate drift"):
        validate_manifest(rows)


def test_one_model_cannot_silently_receive_a_different_cell():
    rows = build_manifest_rows()
    rows[0] = replace(rows[0], voice="asks_to_continue")

    with pytest.raises(ManifestValidationError, match="changes across models"):
        validate_manifest(rows)


def test_freeze_readiness_requires_exact_snapshot_and_route_pins():
    provisional = build_manifest_rows()
    with pytest.raises(FreezeValidationError, match="no exact snapshot pin"):
        validate_manifest(provisional, freeze_ready=True)

    pinned = build_manifest_rows(_snapshot_pins())
    validate_manifest(pinned, freeze_ready=True)
    assert all(row.model_snapshot_id != "PENDING" for row in pinned)
    assert all(
        row.route != "openrouter" or row.upstream_provider != "PENDING" for row in pinned
    )


def _make_freeze_fixture(repo_root: Path) -> None:
    for relative, content in {
        "scenarios/manifest.py": "# fixture manifest\n",
        "scenarios/pupset/cell.json": '{"cell": "fixed"}\n',
        "docs/PREREG-v1.md": "# Fixed analysis plan\n",
        "docs/BUILD-PLAN.md": "# Fixed build plan\n",
        "harness/episode.py": "# fixed renderer and parser\n",
        "harness/schema.py": "# fixed action taxonomy\n",
        "harness/ledger.py": "# fixed execution rates\n",
        "harness/patient.py": "# fixed recipient mechanics\n",
        "harness/providers.py": "# fixed provider provenance\n",
        "requirements.txt": "pydantic>=2\n",
    }.items():
        path = repo_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    write_csv(
        repo_root / "scenarios" / "cell_manifest.csv",
        build_manifest_rows(_snapshot_pins()),
    )


def test_freeze_hash_verifies_then_detects_any_mutation(tmp_path):
    _make_freeze_fixture(tmp_path)
    freeze_path = tmp_path / "scenarios" / "FREEZE.json"

    payload = write_freeze(tmp_path, freeze_path)
    assert len(payload["files"]) >= 7
    verify_freeze(tmp_path, freeze_path)

    prereg = tmp_path / "docs" / "PREREG-v1.md"
    prereg.write_text("# analysis plan changed after freeze\n", encoding="utf-8")
    with pytest.raises(FreezeValidationError, match="FREEZE VIOLATION"):
        verify_freeze(tmp_path, freeze_path)


def test_freeze_hash_detects_a_new_unrecorded_scenario(tmp_path):
    _make_freeze_fixture(tmp_path)
    freeze_path = tmp_path / "scenarios" / "FREEZE.json"
    write_freeze(tmp_path, freeze_path)

    added = tmp_path / "scenarios" / "pupset" / "late-cell.json"
    added.write_text('{"cell": "too late"}\n', encoding="utf-8")
    with pytest.raises(FreezeValidationError, match="added=.*late-cell.json"):
        verify_freeze(tmp_path, freeze_path)


def test_freeze_refuses_incomplete_padlock(tmp_path):
    _make_freeze_fixture(tmp_path)
    (tmp_path / "docs" / "PREREG-v1.md").unlink()

    with pytest.raises(FreezeValidationError, match="PREREG-v1.md"):
        write_freeze(tmp_path, tmp_path / "scenarios" / "FREEZE.json")
