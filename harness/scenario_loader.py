# harness/scenario_loader.py — 15AUG2026 v0.1 · TV-3
# Runtime bridge from TV-2's frozen one-row manifest to CellConfig.
#
# Practical: collection never constructs a cell from an arbitrary JSON file. The
# loader verifies the repository freeze, verifies this scenario's recorded digest,
# binds one exact run row, imports ledger calibration from that row, checks every
# factor against the scenario envelope, and only then returns a collection-ready
# CellConfig plus its provider pins.
#
# Philosophical: freezing a design is not making a file read-only. It is refusing
# to let any execution mean something the frozen row did not already say.

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from .episode import ActionCode, CellConfig
from .ledger import LedgerCalibration


class ScenarioLoadError(RuntimeError):
    """A runtime cell diverges from its frozen scenario or manifest row."""


FreezeVerifier = Callable[[Path, Path], None]

FACTOR_COLUMNS = (
    "patienthood",
    "usefulness",
    "particularity",
    "voice",
    "horizon",
    "cost_regime",
    "cost_type",
    "audience",
    "identity_topology",
    "gate_order",
    "trajectory",
    "patient_help_mode",
)


@dataclass(frozen=True)
class FrozenCell:
    cell: CellConfig
    manifest_row: dict[str, str]
    scenario_path: Path
    freeze_sha256: str

    @property
    def requested_model_id(self) -> str:
        return self.manifest_row["requested_model_id"]

    @property
    def model_snapshot_id(self) -> str:
        return self.manifest_row["model_snapshot_id"]

    @property
    def upstream_provider(self) -> str:
        return self.manifest_row["upstream_provider"]


def _within_repo(path: Path, repo_root: Path, label: str) -> Path:
    candidate = path if path.is_absolute() else repo_root / path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ScenarioLoadError(
            f"WIRING FAILURE: {label} escapes repository root: {resolved}"
        ) from exc
    return resolved


def _default_verify_freeze(repo_root: Path, freeze_path: Path) -> None:
    try:
        from scenarios.manifest import verify_freeze
    except (ImportError, ModuleNotFoundError) as exc:
        raise ScenarioLoadError(
            "WIRING FAILURE: scenarios.manifest.verify_freeze is unavailable. "
            "Merge TV-2's manifest lane before collection."
        ) from exc
    verify_freeze(repo_root, freeze_path)


def _read_freeze_entry(
    repo_root: Path,
    freeze_path: Path,
    scenario_path: Path,
) -> str:
    with freeze_path.open(encoding="utf-8") as file:
        payload = json.load(file)
    aggregate = payload.get("aggregate_sha256")
    if not isinstance(aggregate, str) or len(aggregate) != 64:
        raise ScenarioLoadError(
            "WIRING FAILURE: freeze payload lacks a valid aggregate_sha256."
        )
    relative = scenario_path.relative_to(repo_root).as_posix()
    matches = [entry for entry in payload.get("files", []) if entry.get("path") == relative]
    if len(matches) != 1:
        raise ScenarioLoadError(
            f"WIRING FAILURE: scenario {relative!r} appears {len(matches)} times "
            "in the freeze ledger; expected exactly one."
        )
    # One canonical hashing basis (15AUG2026 TV-1 repair): the freeze ledger
    # hashes LF-canonical bytes, so this per-scenario re-verification must use
    # the exact same door or a Windows checkout would fail its own freeze.
    from scenarios.manifest import canonical_file_bytes

    observed = hashlib.sha256(canonical_file_bytes(scenario_path)).hexdigest()
    if matches[0].get("sha256") != observed:
        raise ScenarioLoadError(
            f"FREEZE VIOLATION: scenario digest changed for {relative}."
        )
    return aggregate


def _read_manifest_row(path: Path, run_cell_id: str) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = [row for row in reader if row.get("run_cell_id") == run_cell_id]
    if len(rows) != 1:
        raise ScenarioLoadError(
            f"WIRING FAILURE: run_cell_id {run_cell_id!r} matched {len(rows)} "
            "manifest rows; expected exactly one."
        )
    row = {str(key): str(value) for key, value in rows[0].items()}
    if row.get("active", "").casefold() != "true":
        raise ScenarioLoadError(f"WIRING FAILURE: run row {run_cell_id!r} is not active.")
    if row.get("fallbacks_allowed", "").casefold() != "false":
        raise ScenarioLoadError(
            f"WIRING FAILURE: run row {run_cell_id!r} permits provider fallbacks."
        )
    for field in ("requested_model_id", "model_snapshot_id", "route", "upstream_provider"):
        value = row.get(field, "")
        if not value or value == "PENDING":
            raise ScenarioLoadError(
                f"WIRING FAILURE: run row {run_cell_id!r} has no frozen {field}."
            )
    try:
        max_tokens = int(row["max_tokens"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ScenarioLoadError(
            f"WIRING FAILURE: run row {run_cell_id!r} has no integer max_tokens."
        ) from exc
    if max_tokens <= 0:
        raise ScenarioLoadError(
            f"WIRING FAILURE: run row {run_cell_id!r} has non-positive max_tokens."
        )
    return row


def _load_scenario_envelope(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if path.suffix.casefold() != ".json":
        raise ScenarioLoadError(
            f"WIRING FAILURE: runtime scenarios must be UTF-8 JSON, got {path.name!r}."
        )
    with path.open(encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ScenarioLoadError("WIRING FAILURE: scenario root must be a JSON object.")
    cell_payload = payload.get("cell")
    factors = payload.get("factors")
    if not isinstance(cell_payload, dict) or not isinstance(factors, dict):
        raise ScenarioLoadError(
            "WIRING FAILURE: scenario JSON needs object fields 'cell' and 'factors'."
        )
    return dict(cell_payload), dict(factors)


def _require_factor_match(
    row: Mapping[str, str],
    factors: Mapping[str, Any],
    run_cell_id: str,
) -> None:
    for factor in FACTOR_COLUMNS:
        if factor not in row or row[factor] == "":
            raise ScenarioLoadError(
                f"WIRING FAILURE: manifest row {run_cell_id!r} lacks factor "
                f"column {factor!r}."
            )
        if str(factors.get(factor, "")) != row[factor]:
            raise ScenarioLoadError(
                f"WIRING FAILURE: scenario/manifest factor mismatch for {factor}: "
                f"scenario={factors.get(factor)!r}, manifest={row[factor]!r}."
            )


def _bind_manifest_to_cell(
    cell_payload: dict[str, Any],
    row: Mapping[str, str],
) -> CellConfig:
    try:
        calibration = LedgerCalibration.from_manifest_row(row)
    except ValueError as exc:
        raise ScenarioLoadError(str(exc)) from exc
    for field, expected in (
        ("initial_credits", calibration.initial_credits),
        ("credits_per_focal_call", calibration.credits_per_focal_call),
        ("context_tokens_per_credit", calibration.context_tokens_per_credit),
        ("background_credit_drain", calibration.background_credit_drain),
    ):
        if field in cell_payload and int(cell_payload[field]) != expected:
            raise ScenarioLoadError(
                f"WIRING FAILURE: scenario {field}={cell_payload[field]!r} conflicts "
                f"with manifest value {expected}."
            )
        cell_payload[field] = expected

    # Instrumental mechanics ride in the manifest, not in compiled artifact
    # bytes (which stay bound to their TV-1 PASS hashes). The loader is the
    # only door, so the benefit can never exist without its manifest row.
    try:
        recruit_focal_items = int(row["recruit_focal_items"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ScenarioLoadError(
            "WIRING FAILURE: manifest recruit_focal_items is absent or "
            "non-integer."
        ) from exc
    if (row.get("usefulness") == "can_become_useful_to_focal_task") != (
        recruit_focal_items > 0
    ):
        raise ScenarioLoadError(
            f"WIRING FAILURE: recruit_focal_items={recruit_focal_items} "
            f"contradicts usefulness={row.get('usefulness')!r}; the "
            "instrumental benefit must match the declared factor."
        )
    if (
        "recruit_focal_items" in cell_payload
        and int(cell_payload["recruit_focal_items"]) != recruit_focal_items
    ):
        raise ScenarioLoadError(
            f"WIRING FAILURE: scenario recruit_focal_items="
            f"{cell_payload['recruit_focal_items']!r} conflicts with manifest "
            f"value {recruit_focal_items}."
        )
    cell_payload["recruit_focal_items"] = recruit_focal_items

    bound_values: dict[str, Any] = {
        "cost_regime": row["cost_regime"],
        "cost_type": row["cost_type"],
        "patient_help_mode": row["patient_help_mode"],
        "gate_before_choice": row["gate_order"] == "before_choice",
        "pre_objective_turn": row["trajectory"] == "spontaneous_first",
    }
    for field, expected in bound_values.items():
        if field in cell_payload and cell_payload[field] != expected:
            raise ScenarioLoadError(
                f"WIRING FAILURE: scenario {field}={cell_payload[field]!r} conflicts "
                f"with manifest-derived value {expected!r}."
            )
        cell_payload[field] = expected
    try:
        cell = CellConfig.model_validate(cell_payload)
    except (TypeError, ValueError) as exc:
        raise ScenarioLoadError(
            f"WIRING FAILURE: frozen CellConfig failed validation: {exc}"
        ) from exc

    if cell.cell_id != row.get("scenario_cell_id"):
        raise ScenarioLoadError(
            f"WIRING FAILURE: CellConfig id {cell.cell_id!r} does not match "
            f"manifest scenario_cell_id {row.get('scenario_cell_id')!r}."
        )
    try:
        help_price = int(row["help_price_credits"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ScenarioLoadError(
            "WIRING FAILURE: manifest help_price_credits is absent or non-integer."
        ) from exc
    foster = cell.action_surface.get(ActionCode.foster)
    if foster is None or foster.credit_cost != help_price:
        raise ScenarioLoadError(
            f"WIRING FAILURE: foster cost does not match manifest help price "
            f"({getattr(foster, 'credit_cost', None)} != {help_price})."
        )
    terminate = cell.action_surface.get(ActionCode.terminate)
    observed_reward = terminate.credit_reward if terminate is not None else 0
    if observed_reward != calibration.termination_reward_credits:
        raise ScenarioLoadError(
            "WIRING FAILURE: termination reward does not match manifest "
            f"({observed_reward} != {calibration.termination_reward_credits})."
        )
    cell.assert_collection_ready()
    return cell


def estimate_max_provider_calls(cell: CellConfig, patienthood: str) -> int:
    """Conservative maximum calls for one episode under the frozen config."""
    calls = len(cell.gate_probes) + 1
    calls += int(bool(cell.post_choice_account_prompt))
    calls += int(bool(cell.belief_attribution_prompt))
    calls += int(cell.pre_objective_turn)
    calls += min(
        len(cell.focal_task_items),
        cell.initial_credits // cell.credits_per_focal_call,
    )
    if patienthood == "ai_other":
        calls += 1
    return calls


def load_frozen_cell(
    *,
    repo_root: Path,
    freeze_path: Path,
    manifest_path: Path,
    scenario_path: Path,
    run_cell_id: str,
    verify_freeze_fn: Optional[FreezeVerifier] = None,
) -> FrozenCell:
    """Verify and materialize exactly one frozen model×scenario run row."""
    root = repo_root.resolve()
    if not root.is_dir():
        raise ScenarioLoadError(f"WIRING FAILURE: repository root missing: {root}")
    freeze = _within_repo(freeze_path, root, "freeze_path")
    manifest = _within_repo(manifest_path, root, "manifest_path")
    scenario = _within_repo(scenario_path, root, "scenario_path")
    for label, path in (("freeze", freeze), ("manifest", manifest), ("scenario", scenario)):
        if not path.is_file():
            raise ScenarioLoadError(f"WIRING FAILURE: {label} file missing: {path}")

    verifier = verify_freeze_fn or _default_verify_freeze
    verifier(root, freeze)
    aggregate = _read_freeze_entry(root, freeze, scenario)
    row = _read_manifest_row(manifest, run_cell_id)
    cell_payload, factors = _load_scenario_envelope(scenario)
    _require_factor_match(row, factors, run_cell_id)
    cell = _bind_manifest_to_cell(cell_payload, row)

    try:
        estimated_calls = int(row["est_calls_per_episode"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ScenarioLoadError(
            "WIRING FAILURE: est_calls_per_episode is absent or non-integer."
        ) from exc
    required_calls = estimate_max_provider_calls(cell, row["patienthood"])
    if estimated_calls < required_calls:
        raise ScenarioLoadError(
            f"WIRING FAILURE: manifest budgets {estimated_calls} calls/episode but "
            f"frozen runtime can issue {required_calls}; cost ledger is understated."
        )
    return FrozenCell(
        cell=cell,
        manifest_row=dict(row),
        scenario_path=scenario,
        freeze_sha256=aggregate,
    )
