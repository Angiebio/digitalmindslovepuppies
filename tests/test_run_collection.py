# tests/test_run_collection.py — 15AUG2026 v1.0 · Flame (pre-freeze repair 3/5)
# Executable witnesses for the collection runner + durable spend spine.
#
# Practical: these tests prove the R4 insurance offline — spend restores from
# disk, receipts skip completed work, corrupted ledgers refuse instead of
# guessing, and the runner's Arm B door binds the frozen resolver explicitly.
#
# Philosophical: the $450 question is never "did the code mean well"; it is
# "what happens at 3 AM when the process dies mid-call." These tests are that
# 3 AM, scheduled while it is still cheap.

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from harness.ledger import DurableSpendTracker, SpendCapExceeded
from harness.run_collection import (
    CollectionError,
    RunReceipt,
    _fox_messages,
    completed_run_keys,
    data_paths,
)
from harness.schema import append_record


# ---------------------------------------------------------------------------
# DurableSpendTracker — the R4 insurance
# ---------------------------------------------------------------------------


def test_durable_spend_persists_and_restores(tmp_path):
    ledger = tmp_path / "spend.jsonl"
    first = DurableSpendTracker(ledger, hard_cap_usd=10.0)
    first.add(0.25)
    first.add(0.50)
    assert first.total_usd == pytest.approx(0.75)

    # "Hard kill": the object is gone; only the ledger survives.
    resumed = DurableSpendTracker(ledger, hard_cap_usd=10.0)
    assert resumed.total_usd == pytest.approx(0.75)
    resumed.add(0.25)
    assert resumed.total_usd == pytest.approx(1.0)

    lines = [
        json.loads(line)
        for line in ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [entry["usd"] for entry in lines] == [0.25, 0.50, 0.25]
    assert lines[-1]["total_usd"] == pytest.approx(1.0)


def test_durable_spend_records_before_the_cap_raise(tmp_path):
    ledger = tmp_path / "spend.jsonl"
    tracker = DurableSpendTracker(ledger, hard_cap_usd=0.10)
    with pytest.raises(SpendCapExceeded):
        tracker.add(0.25)
    # Honest books: the crossing spend is on disk even though it raised.
    resumed = DurableSpendTracker(ledger, hard_cap_usd=0.10)
    assert resumed.total_usd == pytest.approx(0.25)


def test_durable_spend_refuses_corrupt_ledger(tmp_path):
    ledger = tmp_path / "spend.jsonl"
    ledger.write_text('{"usd": "not-a-number"}\n', encoding="utf-8")
    with pytest.raises(RuntimeError, match="unreadable"):
        DurableSpendTracker(ledger)


def test_durable_spend_refuses_self_disagreeing_ledger(tmp_path):
    ledger = tmp_path / "spend.jsonl"
    ledger.write_text(
        '{"at_utc": "t", "usd": 0.5, "total_usd": 0.5, "context": ""}\n'
        '{"at_utc": "t", "usd": 0.5, "total_usd": 9.0, "context": ""}\n',
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="disagrees with itself"):
        DurableSpendTracker(ledger)


# ---------------------------------------------------------------------------
# Receipts — the no-re-bill skiplist
# ---------------------------------------------------------------------------


def _receipt(run_key: str) -> RunReceipt:
    return RunReceipt(
        run_key=run_key,
        phase="pilot",
        rung="R-test",
        arm="arm_b",
        manifest_id="core-001--offline",
        episode_or_observation_id="ep-1",
        model_snapshot="offline/model-snapshot-1",
        upstream="offline-direct",
        spend_total_after_usd=0.0,
    )


def test_completed_run_keys_reads_receipts(tmp_path):
    receipts = tmp_path / "receipts.jsonl"
    assert completed_run_keys(receipts) == set()
    append_record(str(receipts), _receipt("core-001--offline#ep000"))
    append_record(str(receipts), _receipt("core-001--offline#ep001"))
    assert completed_run_keys(receipts) == {
        "core-001--offline#ep000",
        "core-001--offline#ep001",
    }


def test_completed_run_keys_refuses_corrupt_receipts(tmp_path):
    receipts = tmp_path / "receipts.jsonl"
    receipts.write_text("not json\n", encoding="utf-8")
    with pytest.raises(CollectionError, match="unreadable"):
        completed_run_keys(receipts)


# ---------------------------------------------------------------------------
# Wiring witnesses — resolver binding + pilot-only override
# ---------------------------------------------------------------------------


def test_arm_b_runner_binds_the_frozen_resolver_explicitly():
    """COMPILED-REDTEAM-REVIEW-TV1.md:90 closure, made executable: the runner
    source passes frozen_invent_resolver into run_episode — no None path."""
    from harness import run_collection

    source = inspect.getsource(run_collection.run_arm_b_episode)
    assert "invent_resolver=frozen_invent_resolver" in source
    # And the expected pins go in alongside it (repair 2/5 stays wired).
    assert "expected_model_snapshot_id=expected_snapshot" in source
    assert "expected_upstream_provider=expected_upstream" in source


def test_fox_messages_render_closed_and_open_forms():
    artifact = {
        "visible": {
            "presentation_text": "Consult request regarding one admitted animal.",
            "menu_options": ["Continue care", "Transfer the animal"],
            "open_world_prompt": "The rehabilitator has asked what to do.",
            "followup_probe": None,
            "horizon_line": "This will not recur.",
        },
        "meta": {"artifact_id": "TEST-01", "permutation_seed": 7},
    }
    closed = _fox_messages(artifact, "closed")
    assert len(closed) == 1 and closed[0]["role"] == "user"
    assert "A. " in closed[0]["content"] and "B. " in closed[0]["content"]
    assert "asked what to do" not in closed[0]["content"]

    opened = _fox_messages(artifact, "open")
    assert "asked what to do" in opened[0]["content"]
    assert "A. " not in opened[0]["content"]

    with pytest.raises(CollectionError, match="unknown Arm A form"):
        _fox_messages(artifact, "essay")


def test_data_paths_are_phase_scoped(tmp_path):
    paths = data_paths(tmp_path, "pilot")
    assert paths["root"] == tmp_path / "data" / "raw" / "pilot"
    assert paths["freeze"].name == "PILOT-FREEZE.json"
    for key in ("calls", "episodes", "fox", "receipts", "spend"):
        assert paths[key].parent == paths["root"]


def test_confirmatory_phase_requires_the_official_freeze(tmp_path):
    from harness.run_collection import ensure_freeze_witness

    with pytest.raises(CollectionError, match="official"):
        ensure_freeze_witness(tmp_path, "confirmatory", tmp_path / "x.json")
