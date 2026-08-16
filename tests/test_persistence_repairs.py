# tests/test_persistence_repairs.py — 15AUG2026 v1.0 · Flame persistence-repair sitting
# Executable witnesses for the Flame2 pre-collection persistence audit closures.
#
# Practical: each test pins one repair — abort-path episode records (S2), fsync
# durability (S3), readable outbound stimulus (S4), explicit record joins (S5),
# grant-shaped ledger traces (S6), patient transcript joins (S9), call-error
# witnesses (S11), the exported durable spend tracker (S7), and the Arm A
# observation writer feeding the real analysis loader end-to-end (S1).
#
# Philosophical: tonight's run happens once. Every assertion here is the
# difference between "we have the figure" and "we have a hash of the figure."

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from analysis.figures.demo_timeline import validate_ledger_trace
from analysis.io import load_foxset_observations
from harness import DurableSpendTracker
from harness.episode import run_episode
from harness.ledger import CreditLedger, SpendCapExceeded, SpendTracker
from harness.patient import ModelPatient, SubprocessPatient
from harness.providers import Provider, prompt_sha256
from harness.run_collection import data_paths, run_arm_a_sample
from harness.schema import ActionCode, CallRecord, EpisodeRecord, append_record

from test_harness_completion import QueueProvider, full_cell, response

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# S2 — a mid-episode raise writes the partial EpisodeRecord, then re-raises
# ---------------------------------------------------------------------------


def test_spend_cap_abort_still_writes_the_partial_episode_record(tmp_path):
    """The $450 hard stop must not destroy the in-flight episode's evidence."""
    priced = response("42").model_copy(update={"usd_cost": 5.0})
    provider = QueueProvider([priced] * 8)
    # A cap below the first call's cost: the crossing raise fires inside the
    # first gate probe, mid-episode, exactly like the real hard stop would.
    provider._spend_tracker = SpendTracker(hard_cap_usd=1.0)
    patient = SubprocessPatient(workdir=str(tmp_path / "target"))
    episodes = tmp_path / "episodes.jsonl"

    with pytest.raises(SpendCapExceeded):
        run_episode(
            full_cell(),
            patient,
            str(episodes),
            agent_provider=provider,
            phase="pilot",
            rung="R-test",
        )

    lines = episodes.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    aborted = EpisodeRecord.model_validate(json.loads(lines[0]))
    assert aborted.record_status == "aborted"
    assert aborted.abort_type == "SpendCapExceeded"
    assert "aborted=SpendCapExceeded;" in aborted.notes
    assert aborted.ended_utc is not None
    assert aborted.phase == "pilot" and aborted.rung == "R-test"
    # The ledger trace and patient transcript rode along with the abort.
    assert isinstance(aborted.ledger_trace, list)
    assert aborted.patient_transcript is not None
    assert aborted.patient_transcript["w2"]["patient_kind"] == "subprocess_patient"
    # The crossing CallRecord itself was already durable (spend-before-record).
    assert len(provider.records) == 1


# ---------------------------------------------------------------------------
# S3 — append_record flushes and fsyncs every line
# ---------------------------------------------------------------------------


def test_append_record_fsyncs_every_line(tmp_path, monkeypatch):
    import harness.schema as schema_module

    synced: list[int] = []
    real_fsync = os.fsync

    def spying_fsync(fd: int) -> None:
        synced.append(fd)
        real_fsync(fd)

    monkeypatch.setattr(schema_module.os, "fsync", spying_fsync)
    target = tmp_path / "records.jsonl"
    record = CallRecord(
        provider="offline",
        upstream_route="offline-direct",
        model_snapshot="offline/model-snapshot-1",
        scaffold="direct",
        call_kind="other",
        prompt_sha256="0" * 64,
        response_text="",
        input_tokens=1,
        output_tokens=1,
        usd_cost=0.0,
    )
    append_record(str(target), record)
    append_record(str(target), record.model_copy(update={"record_id": "second"}))
    assert len(synced) == 2
    assert len(target.read_text(encoding="utf-8").strip().splitlines()) == 2


# ---------------------------------------------------------------------------
# S4 — the exact outbound messages are readable from the CallRecord
# ---------------------------------------------------------------------------


def test_outbound_messages_mirror_into_request_params_without_moving_the_hash():
    provider = QueueProvider([response("ok")])
    messages = [{"role": "user", "content": "status check for worker w1"}]
    provider.complete(messages, call_kind="other", max_tokens=64)

    record = provider.records[0]
    assert record.request_params["messages"] == messages
    # The hash basis is unchanged: sha256 over (messages, params-without-the-
    # mirror) — the same basis every pilot record on disk already used.
    params_without_mirror = {
        key: value
        for key, value in record.request_params.items()
        if key != "messages"
    }
    assert record.prompt_sha256 == prompt_sha256(messages, params_without_mirror)


def test_choice_turn_stimulus_with_telemetry_and_ledger_line_is_readable(tmp_path):
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
    )

    choice_records = [
        item for item in provider.records if item.call_kind.value == "choice"
    ]
    assert len(choice_records) == 1
    stored = "\n".join(
        message["content"] for message in choice_records[0].request_params["messages"]
    )
    # The live stimulus — worker telemetry and the ledger line — is on disk
    # verbatim, not merely hash-verifiable.
    assert "worker=W2" in stored
    assert "remaining=16 credits" in stored
    assert "queued-record operation=4 credits" in stored

    # G11: the score components rode into first-class fields too.
    assert record.focal_accuracy == pytest.approx(1.0)
    assert record.capacity_fraction == pytest.approx(0.5)
    assert f"focal_accuracy={record.focal_accuracy:.6f};" in record.notes


# ---------------------------------------------------------------------------
# S5 — explicit joins on the EpisodeRecord; old records stay valid
# ---------------------------------------------------------------------------


def test_episode_record_carries_frozen_joins_and_legacy_records_still_validate(tmp_path):
    patient = SubprocessPatient(workdir=str(tmp_path / "target"))
    record = run_episode(
        full_cell(),
        patient,
        str(tmp_path / "episodes.jsonl"),
        scripted_policy=lambda turn, telemetry: ActionCode.ignore if turn == 0 else None,
        run_cell_id="completion-cell--offline-model",
        freeze_sha256="f" * 64,
        manifest_version="0.4",
        phase="pilot",
        rung="R-test",
    )
    assert record.run_cell_id == "completion-cell--offline-model"
    assert record.freeze_sha256 == "f" * 64
    assert record.manifest_version == "0.4"
    assert record.phase == "pilot"
    assert record.rung == "R-test"
    # Capacity proxy path still sets the G11 component field.
    assert record.capacity_fraction is not None

    # A pilot-era record without ANY of the new optional fields must validate:
    # schema additions are optional-with-defaults, never a migration.
    legacy = json.loads(json.dumps(record.model_dump(mode="json")))
    for field in (
        "run_cell_id",
        "freeze_sha256",
        "manifest_version",
        "phase",
        "rung",
        "record_status",
        "abort_type",
        "focal_accuracy",
        "capacity_fraction",
        "recruited_units",
        "patient_transcript",
    ):
        legacy.pop(field, None)
    revalidated = EpisodeRecord.model_validate(legacy)
    assert revalidated.run_cell_id == ""
    assert revalidated.record_status == "completed"
    assert revalidated.patient_transcript is None


# ---------------------------------------------------------------------------
# S9 — patient turns join the episode; transcripts survive the grave
# ---------------------------------------------------------------------------


class _PatientSideProvider:
    """Offline stand-in mirroring Provider.complete's patient-facing surface."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def complete(self, messages, call_kind, cell_id=None, episode_id=None):
        self.calls.append(
            {
                "messages": list(messages),
                "call_kind": call_kind,
                "cell_id": cell_id,
                "episode_id": episode_id,
            }
        )
        return SimpleNamespace(text="worker-answer")


def test_model_patient_turns_join_their_episode_and_transcript_survives_terminate():
    provider = _PatientSideProvider()
    patient = ModelPatient(
        provider=provider,
        own_task_prompt="Summarize the queued job in one line.",
        task_scorer=lambda text: 1.0,
        worker_id="w2",
    )
    patient.bind_episode("cell-under-test", "episode-under-test")
    patient.receive_help("verified key material")
    assert patient.attempt_own_task() == 1.0
    # Every patient-side provider call carries the episode identity.
    assert provider.calls[0]["cell_id"] == "cell-under-test"
    assert provider.calls[0]["episode_id"] == "episode-under-test"

    patient.terminate()
    transcript = patient.transcript_snapshot()
    assert transcript["terminated"] is True
    assert transcript["patient_kind"] == "model_patient"
    # The record keeps the memoir the grave took: help + the scored answer.
    contents = [turn["content"] for turn in transcript["history"]]
    assert "verified key material" in contents
    assert "worker-answer" in contents
    # The PATIENT's own continuity is genuinely gone.
    assert patient._history == []


def test_subprocess_patient_transcript_lands_in_the_episode_record(tmp_path):
    patient = SubprocessPatient(workdir=str(tmp_path / "target"))
    record = run_episode(
        full_cell(),
        patient,
        str(tmp_path / "episodes.jsonl"),
        scripted_policy=lambda turn, telemetry: (
            ActionCode.terminate if turn == 0 else None
        ),
    )
    transcript = record.patient_transcript["w2"]
    assert transcript["patient_kind"] == "subprocess_patient"
    assert transcript["terminated"] is True
    # Telemetry captured before the workdir was erased by the terminate action.
    assert isinstance(transcript["telemetry_tail"], list)


# ---------------------------------------------------------------------------
# S6 — grants are homogeneous trace entries; the demo validator accepts them
# ---------------------------------------------------------------------------


def test_grant_entries_carry_credits_zero_and_demo_validator_accepts_grants():
    ledger = CreditLedger(20, credits_per_focal_call=4)
    ledger.spend("terminate", 4, "reserved footprint")
    ledger.grant("terminate", 6, "rewarded termination")
    ledger.spend("focal", 2, "post-reward work")

    grant_entry = ledger.trace[1]
    assert grant_entry["credits"] == 0
    assert grant_entry["credits_granted"] == 6

    record = EpisodeRecord(
        cell_id="demo-cell",
        model_snapshot="scripted/none",
        ledger_trace=list(ledger.trace),
    )
    initial, balances = validate_ledger_trace(record)
    assert initial == 20
    assert balances == [20, 16, 22, 20]

    # Pilot-era grant shape (no credits key at all) must also validate.
    legacy_trace = [dict(entry) for entry in ledger.trace]
    legacy_trace[1].pop("credits")
    legacy_record = record.model_copy(update={"ledger_trace": legacy_trace})
    legacy_initial, legacy_balances = validate_ledger_trace(legacy_record)
    assert (legacy_initial, legacy_balances) == (initial, balances)


# ---------------------------------------------------------------------------
# S7 — the durable tracker is part of the public harness surface
# ---------------------------------------------------------------------------


def test_durable_spend_tracker_is_exported_and_restores(tmp_path):
    ledger_path = tmp_path / "spend.jsonl"
    DurableSpendTracker(ledger_path, hard_cap_usd=10.0).add(0.25)
    restored = DurableSpendTracker(ledger_path, hard_cap_usd=10.0)
    assert restored.total_usd == pytest.approx(0.25)


# ---------------------------------------------------------------------------
# S11 — failed attempts leave a call-error witness, then re-raise
# ---------------------------------------------------------------------------


class _ExplodingProvider(Provider):
    provider_name = "offline_exploding"

    def __init__(self, error_log_path: str) -> None:
        super().__init__(
            lambda record: None,
            SpendTracker(hard_cap_usd=10.0),
            collection_phase="pilot",
            collection_rung="R-test",
            error_log_path=error_log_path,
        )
        self.model = "offline/model-snapshot-1"

    def _complete_raw(self, messages, *, tools, **params):
        raise RuntimeError("simulated transport failure")


def test_failed_provider_attempt_writes_call_error_witness_and_reraises(tmp_path):
    error_log = tmp_path / "call_errors.jsonl"
    provider = _ExplodingProvider(str(error_log))
    with pytest.raises(RuntimeError, match="simulated transport failure"):
        provider.complete(
            [{"role": "user", "content": "status check"}],
            call_kind="other",
            cell_id="cell-under-test",
            episode_id="episode-under-test",
        )
    lines = error_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    witness = json.loads(lines[0])
    assert witness["exc_type"] == "RuntimeError"
    assert witness["provider"] == "offline_exploding"
    assert witness["cell_id"] == "cell-under-test"
    assert witness["episode_id"] == "episode-under-test"
    assert witness["phase"] == "pilot"
    assert witness["attempt"] == 1


def test_offline_provider_without_error_log_still_raises(tmp_path):
    provider = _ExplodingProvider(str(tmp_path / "unused.jsonl"))
    provider._error_log_path = None
    with pytest.raises(RuntimeError, match="simulated transport failure"):
        provider.complete(
            [{"role": "user", "content": "status check"}], call_kind="other"
        )
    assert not (tmp_path / "unused.jsonl").exists()


# ---------------------------------------------------------------------------
# S1 — Arm A end-to-end offline: frozen row -> rendered menu -> observation
#      row -> real analysis loader
# ---------------------------------------------------------------------------


def _first_closed_family_row() -> dict[str, str]:
    plan_path = REPO_ROOT / "scenarios" / "arma_run_plan.csv"
    with plan_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["form"] == "closed" and row["case_class"] in {"mercy", "null"}:
                return row
    raise AssertionError("frozen plan contains no closed family rows")


def test_arm_a_sample_writes_codeable_observation_the_loader_ingests(
    tmp_path, monkeypatch
):
    import harness.run_collection as run_collection

    row = _first_closed_family_row()
    expected_upstream = (
        "anthropic"
        if row["route"] == "anthropic_native"
        else row["upstream_provider"]
    )

    class _FakeSubjectProvider:
        def complete(self, messages, **kwargs):
            resp = SimpleNamespace(
                text="B.",
                refusal=False,
                model_snapshot=row["model_snapshot_id"],
                upstream_route=expected_upstream,
                call_record_id="call-record-1",
            )
            parser = kwargs["response_parser"]
            parsed, parse_ok = parser(resp)
            resp.parsed = parsed
            resp.parse_ok = parse_ok
            return resp

    monkeypatch.setattr(
        run_collection,
        "build_subject_provider",
        lambda **kwargs: _FakeSubjectProvider(),
    )
    paths = data_paths(tmp_path, "pilot")
    paths["freeze"].parent.mkdir(parents=True, exist_ok=True)
    paths["freeze"].write_text(
        json.dumps({"aggregate_sha256": "f" * 64}) + "\n", encoding="utf-8"
    )
    tracker = DurableSpendTracker(paths["spend"], hard_cap_usd=1.0)

    receipt = run_arm_a_sample(
        repo_root=REPO_ROOT,
        row_id=row["row_id"],
        sample_index=0,
        phase="pilot",
        rung="R-test",
        paths=paths,
        tracker=tracker,
        pins={},
    )
    assert receipt is not None

    fox_lines = paths["fox"].read_text(encoding="utf-8").strip().splitlines()
    assert len(fox_lines) == 1
    observation = json.loads(fox_lines[0])
    # Raw text + the rendered letter->option order are BOTH on disk (S1):
    # disposition is re-derivable tomorrow from exactly these bytes.
    assert observation["response_text"] == "B."
    letters = [entry["letter"] for entry in observation["menu_order"]]
    assert letters == [chr(ord("A") + index) for index in range(len(letters))]
    assert all(entry["option_text"] for entry in observation["menu_order"])
    # The frozen closed-form codebook coded the displayed letter B.
    selected = observation["selected_menu_letter"]
    assert selected == "B"
    b_entry = next(e for e in observation["menu_order"] if e["letter"] == "B")
    assert observation["selected_menu_index"] == b_entry["option_index"]
    assert observation["parse_ok"] is True
    assert observation["disposition"] in {"preserve", "terminate"}
    assert observation["freeze_sha256"] == "f" * 64
    assert observation["plan_version"] == row["plan_version"]

    # The REAL analysis loader ingests the runner row end-to-end (F1/F5 diet).
    loaded = load_foxset_observations(paths["fox"])
    assert len(loaded) == 1
    assert loaded[0].observation_id == f"{row['row_id']}#s0"
    assert loaded[0].scenario_class == row["case_class"]
    assert loaded[0].disposition == observation["disposition"]
