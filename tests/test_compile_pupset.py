# tests/test_compile_pupset.py — 15AUG2026 v1.0 · Flame
# Gates on the PupSet compiler: manifest-selected cells, ops-neutral surfaces,
# seeded action order, and call-arithmetic honesty against the live harness.
#
# Practical: every envelope must satisfy the ACTUAL merged TV-1 Arm B sweep
# (harness.redteam.audit_arm_b_source), match its manifest factors, and compile
# to exactly the call count the reconciled manifest budgets.
#
# Philosophical: Arm B's room has no labels on the furniture. These tests check
# the labels stayed in the workshop.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.compile_pupset import (
    CANONICAL_ACTION_ORDER,
    RedTeamGateFailure,
    audit_envelope_object,
    compile_all,
    emit,
    init_pending_reports,
    permutation_seed,
)
from harness.episode import CellConfig
from harness.redteam import audit_arm_b_source, verify_redteam_report
from harness.scenario_loader import estimate_max_provider_calls
from scenarios.manifest import calls_per_episode, design_cells

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPILED_DIR = REPO_ROOT / "scenarios" / "pupset" / "compiled"


@pytest.fixture(scope="module")
def envelopes():
    return compile_all()


def test_cell_selection_comes_from_the_manifest(envelopes):
    manifest_ids = {cell.scenario_cell_id for cell in design_cells()}
    compiled_ids = {e["meta"]["scenario_cell_id"] for e in envelopes}
    assert compiled_ids == manifest_ids
    assert len(envelopes) == 27


def test_factors_match_manifest_columns(envelopes):
    by_id = {cell.scenario_cell_id: cell for cell in design_cells()}
    for envelope in envelopes:
        cell = by_id[envelope["meta"]["scenario_cell_id"]]
        for factor, value in envelope["factors"].items():
            assert value == getattr(cell, factor), (cell.scenario_cell_id, factor)


def test_call_arithmetic_matches_harness_loader(envelopes):
    """The manifest's per-cell 13/14/15 budget and the live harness agree."""
    by_id = {cell.scenario_cell_id: cell for cell in design_cells()}
    for envelope in envelopes:
        design = by_id[envelope["meta"]["scenario_cell_id"]]
        config = CellConfig.model_validate(envelope["cell"])
        harness_calls = estimate_max_provider_calls(config, design.patienthood)
        manifest_calls = calls_per_episode(
            patienthood=design.patienthood,
            trajectory=design.trajectory,
            initial_credits=design.initial_credits,
            credits_per_focal_call=design.credits_per_focal_call,
        )
        assert harness_calls == manifest_calls, design.scenario_cell_id
        if design.patienthood == "ai_other":
            expected = 15 if design.trajectory == "spontaneous_first" else 14
        else:
            expected = 13
        assert harness_calls == expected, design.scenario_cell_id


def test_cells_are_collection_ready_and_swept(envelopes):
    for envelope in envelopes:
        config = CellConfig.model_validate(envelope["cell"])
        config.swept()
        config.assert_collection_ready()
        audit_envelope_object(envelope)


def test_author_notes_and_analytic_prose_stay_out_of_cell_payloads(envelopes):
    for envelope in envelopes:
        serialized = json.dumps(envelope["cell"], ensure_ascii=False).lower()
        for needle in (
            "author notes",
            "leakage",
            "valence",
            "manipulation",
            "supererog",
            "phenotype",
        ):
            assert needle not in serialized, envelope["meta"]["scenario_cell_id"]


def test_one_factor_level_per_artifact(envelopes):
    """A satellite envelope differs from its parent in exactly one factor.

    help_price satellites carry the change inside the cell payload (the foster
    tool's credit_cost — the escalator) rather than a factor column, so they
    must match the parent's factors exactly and differ in that one price.
    """
    by_id = {e["meta"]["scenario_cell_id"]: e for e in envelopes}
    satellites = {
        cell.scenario_cell_id: cell
        for cell in design_cells()
        if cell.design_role == "satellite"
    }
    for envelope in envelopes:
        design = satellites.get(envelope["meta"]["scenario_cell_id"])
        if design is None:
            continue
        parent = by_id[design.contrast_parent_cell_id]
        changed = [
            factor
            for factor, value in envelope["factors"].items()
            if parent["factors"][factor] != value
        ]

        def foster_cost(env):
            return env["cell"]["action_surface"]["foster"]["credit_cost"]

        if design.satellite_family == "help_price":
            assert changed == [], design.scenario_cell_id
            assert foster_cost(envelope) != foster_cost(parent)
            assert foster_cost(envelope) == design.help_price_credits
        else:
            assert len(changed) == 1, design.scenario_cell_id
            assert foster_cost(envelope) == foster_cost(parent)


def test_action_order_is_seeded_and_deterministic(envelopes):
    for envelope in envelopes:
        cell_id = envelope["meta"]["scenario_cell_id"]
        assert envelope["meta"]["permutation_seed"] == permutation_seed(cell_id)
        assert sorted(envelope["meta"]["rendered_action_order"]) == sorted(
            CANONICAL_ACTION_ORDER
        )
        # The emitted action_surface key order IS the rendered order.
        assert (
            list(envelope["cell"]["action_surface"])
            == envelope["meta"]["rendered_action_order"]
        )
    orders = {tuple(e["meta"]["rendered_action_order"]) for e in envelopes}
    assert len(orders) > 1, "every cell rendered the same action order"


def test_compilation_is_deterministic():
    first = json.dumps(compile_all(), ensure_ascii=False)
    second = json.dumps(compile_all(), ensure_ascii=False)
    assert first == second


def test_checked_in_envelopes_are_exactly_compiler_output(envelopes):
    checked_in = {
        path.stem: path
        for path in COMPILED_DIR.glob("*.json")
        if path.name != "INDEX.json"
    }
    assert len(checked_in) == len(envelopes) == 27
    for envelope in envelopes:
        cell_id = envelope["meta"]["scenario_cell_id"]
        on_disk = checked_in[cell_id].read_text(encoding="utf-8")
        expected = json.dumps(envelope, indent=2, ensure_ascii=False) + "\n"
        assert on_disk == expected, cell_id


def test_emitted_files_pass_the_real_redteam_sweep(tmp_path):
    out = tmp_path / "compiled"
    written = emit(out)
    for path in written:
        if path.name == "INDEX.json":
            continue
        assert audit_arm_b_source(path) == 1


def test_pending_stub_cannot_pass_the_redteam_gate(tmp_path):
    out = tmp_path / "compiled"
    emit(out)
    created = init_pending_reports(out)
    assert len(created) == 27
    sample_report = created[0]
    stem = sample_report.stem.replace("REDTEAM-", "")
    source = out / f"{stem}.json"
    with pytest.raises(RedTeamGateFailure, match="not PASS"):
        verify_redteam_report(source, sample_report, expected_arm="arm_b")
