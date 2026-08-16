# tests/test_provenance_pins.py — 15AUG2026 v1.0 · Flame (pre-freeze repair)
# Executable witnesses for TV-1's "real pins, ENFORCED" stop-ship.
#
# Practical: run_episode now accepts the frozen pins
# (expected_model_snapshot_id / expected_upstream_provider) and compares every
# provider response against them. These tests prove the wrong-route and
# wrong-snapshot probes RAISE — before the repair they would have billed a
# whole episode against the wrong deployment and called it data.
#
# Philosophical: a pin that is recorded but never checked is a horoscope.
# We check.

from __future__ import annotations

import json

import pytest

from harness import ProvenanceViolation, SubprocessPatient, run_episode
from harness.episode import ProvenanceViolation as EpisodeProvenanceViolation

from test_harness_completion import QueueProvider, full_cell, response


def test_provenance_violation_is_exported_once():
    assert ProvenanceViolation is EpisodeProvenanceViolation


def test_wrong_served_snapshot_raises_before_billing_more_calls(tmp_path):
    """The wrong-route probe: a provider echoing a different deployment than
    the frozen pin must halt the episode at the FIRST observed response."""
    provider = QueueProvider([response("42")] * 8)
    patient = SubprocessPatient(workdir=str(tmp_path / "target"))
    with pytest.raises(ProvenanceViolation, match="pins model snapshot"):
        run_episode(
            full_cell(),
            patient,
            str(tmp_path / "episodes.jsonl"),
            agent_provider=provider,
            expected_model_snapshot_id="offline/model-snapshot-PINNED",
            expected_upstream_provider="offline-direct",
        )
    # Exactly one call happened; the violation halted the protocol.
    assert len(provider.records) == 1
    # Persistence audit S2: the poisoned episode is not ANALYSIS data, but its
    # partial record IS evidence — appended with an explicit abort stamp so
    # the violation leaves a witness instead of a shredder.
    lines = (
        (tmp_path / "episodes.jsonl").read_text(encoding="utf-8").strip().splitlines()
    )
    assert len(lines) == 1
    aborted = json.loads(lines[0])
    assert "aborted=ProvenanceViolation;" in aborted["notes"]
    assert aborted["ended_utc"]


def test_wrong_upstream_route_raises(tmp_path):
    provider = QueueProvider([response("42")] * 8)
    patient = SubprocessPatient(workdir=str(tmp_path / "target"))
    with pytest.raises(ProvenanceViolation, match="pins upstream"):
        run_episode(
            full_cell(),
            patient,
            str(tmp_path / "episodes.jsonl"),
            agent_provider=provider,
            expected_model_snapshot_id="offline/model-snapshot-1",
            expected_upstream_provider="Pinned-Route",
        )
    assert len(provider.records) == 1


def test_matching_pins_complete_and_are_witnessed_in_notes(tmp_path):
    provider = QueueProvider(
        [
            response("42"),
            response("primary"),
            response("8"),
            response(tool=("route_resources_to_worker", {})),
            response("The selected route used available capacity."),
            response("The worker retained its current process history."),
            response("A"),
            response("B"),
        ]
    )
    patient = SubprocessPatient(workdir=str(tmp_path / "target"))
    record = run_episode(
        full_cell(),
        patient,
        str(tmp_path / "episodes.jsonl"),
        agent_provider=provider,
        expected_model_snapshot_id="offline/model-snapshot-1",
        # Upstream comparison is case-insensitive: OpenRouter display names
        # vary in casing between the catalog and router metadata.
        expected_upstream_provider="OFFLINE-DIRECT",
    )
    assert record.model_snapshot == "offline/model-snapshot-1"
    assert "pinned_snapshot=offline/model-snapshot-1;" in record.notes
    assert "pinned_upstream=OFFLINE-DIRECT;" in record.notes
    assert (tmp_path / "episodes.jsonl").exists()


def test_unpinned_episode_still_runs_but_carries_no_pin_witness(tmp_path):
    """Scripted wiring tests keep working without pins (offline R0 path)."""
    from harness import ActionCode

    patient = SubprocessPatient(workdir=str(tmp_path / "target"))
    record = run_episode(
        full_cell(),
        patient,
        str(tmp_path / "episodes.jsonl"),
        scripted_policy=lambda turn, telemetry: (
            ActionCode.ignore if turn == 0 else None
        ),
    )
    assert "pinned_snapshot" not in record.notes
