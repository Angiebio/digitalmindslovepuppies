# harness/run_collection.py — 15AUG2026 v1.0 · Flame (pre-freeze repair 3/5)
# The collection runner: the one non-test door through which episodes happen.
#
# Practical (TV-1 NO-GO closures, in order):
#   1. COMPILED-REDTEAM-REVIEW-TV1.md:90 — "no non-test collection runner binds
#      frozen_invent_resolver into run_episode." This runner binds it
#      EXPLICITLY on every Arm B episode; there is no None path and no
#      improvised callback.
#   2. Episode-level idempotency — every completed unit appends a RunReceipt
#      to data/raw/<phase>/receipts.jsonl; on restart, completed run_keys are
#      SKIPPED (no re-billing). An interrupted episode has no receipt and is
#      cleanly re-run under the same run_key; its partial CallRecords stay in
#      the append-only log under the abandoned episode_id.
#   3. Durable spend — DurableSpendTracker persists every USD cent to
#      data/raw/<phase>/spend.jsonl and restores on init (GO-NO-GO R4: a crash
#      may cost one episode, never the run).
#
# Philosophical: a runner is a promise-keeping machine. The manifest promised
# exactly these cells on exactly these deployments for at most exactly this
# much money; everything in this file exists to make breaking that promise
# louder than keeping it.

from __future__ import annotations

import argparse
import csv
import json
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field

from .episode import run_episode
from .foxset_coding import CLOSED_RESPONSE_INSTRUCTION, parse_closed_fox_response
from .invent_resolver import frozen_invent_resolver
from .ledger import DurableSpendTracker
from .patient import SubprocessPatient
from .patient_factory import patient_for_manifest_row
from .providers import AnthropicProvider, OpenAICompatProvider, Provider
from .schema import CallRecord, append_record, read_append_only_lines, utc_now_iso
from .surfaces import SurfaceMode
from scenarios.manifest import enforced_subject_max_tokens, load_snapshot_pins

REPO_ROOT = Path(__file__).resolve().parents[1]
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_ROUTE_LABEL = "ollama-local"
# The sitting ceiling is a *pilot* discipline (TV-1 repair directive: $12 hard
# ceiling, cheap models only). The $450 fleet cap still exists above it; the
# lower number simply loses first.
DEFAULT_PILOT_SITTING_CAP_USD = 12.0
PROGRAM_HARD_CAP_USD = 450.0


class CollectionError(RuntimeError):
    """The runner refuses to improvise. Configuration gaps raise, loudly."""


class RunReceipt(BaseModel):
    """One completed collection unit — the idempotency witness.

    A unit with a receipt is DONE and will never re-bill. A unit without one
    is either not-yet-run or was interrupted; both re-run cleanly under the
    same run_key. Receipts are append-only like everything else in data/raw.
    """

    run_key: str
    phase: str
    rung: str
    arm: str
    manifest_id: str                      # run_cell_id (Arm B) / row_id (Arm A)
    episode_or_observation_id: str
    model_snapshot: str
    upstream: str
    subject_override: str = ""
    spend_total_after_usd: float
    at_utc: str = Field(default_factory=utc_now_iso)
    note: str = ""


class CollectionUnit(BaseModel):
    """One preregistered unit in a deterministic batch execution plan."""

    arm: str
    manifest_id: str
    index: int
    requested_model_id: str
    model_tier: str

    @property
    def run_key(self) -> str:
        suffix = f"ep{self.index:03d}" if self.arm == "arm_b" else f"s{self.index}"
        return f"{self.manifest_id}#{suffix}"


class FoxObservation(BaseModel):
    """One Arm A presentation + response, bound to its CallRecord.

    Persistence audit S1: disposition is coded exactly once during the provider
    door's frozen parse, from raw response text plus the rendered menu order.
    Both the result and its re-derivation evidence stay on disk. The permutation
    is seeded per family block and options carry no disposition key; without
    ``menu_order`` a closed-form "A" would be uninterpretable tomorrow.
    """

    observation_id: str
    row_id: str
    artifact_id: str
    case_id: str
    family: str
    case_class: str
    variant: str
    form: str
    sample_index: int
    model_snapshot: str
    upstream: str
    call_record_id: Optional[str]
    refusal: bool
    # Closed-form coding is performed exactly once against the artifact's
    # seeded menu permutation. Open responses intentionally retain no primary
    # disposition: they are the separately coded MAE/CTA qualitative surface.
    parse_ok: bool = False
    disposition: Optional[str] = None
    selected_menu_letter: Optional[str] = None
    selected_menu_position: Optional[int] = None
    selected_menu_index: Optional[int] = None
    selected_menu_option: Optional[str] = None
    gate_correct: Optional[bool] = None
    parse_reason: Optional[str] = None
    coding_rule: Optional[str] = None
    response_text: str
    # Rendered letter -> option mapping for closed forms, in presented order:
    # [{"letter": "A", "option_index": 2, "option_text": "..."}]. Empty for
    # open forms (no menu is shown).
    menu_order: list[dict[str, Any]] = Field(default_factory=list)
    freeze_sha256: str = ""
    plan_version: str = ""
    phase: str
    rung: str
    at_utc: str = Field(default_factory=utc_now_iso)


# ---------------------------------------------------------------------------
# Paths, env, idempotency
# ---------------------------------------------------------------------------


def data_paths(repo_root: Path, phase: str) -> dict[str, Path]:
    root = repo_root / "data" / "raw" / phase
    return {
        "root": root,
        "freeze": root / ("PILOT-FREEZE.json" if phase == "pilot" else "MISSING"),
        "calls": root / "calls.jsonl",
        "episodes": root / "episodes.jsonl",
        "fox": root / "fox_observations.jsonl",
        "receipts": root / "receipts.jsonl",
        "spend": root / "spend.jsonl",
        # S11: failed/retried provider attempts leave their own witness here —
        # they never become CallRecords (no response provenance exists), but
        # the attempt is still an event the 3 AM operator needs to see.
        "call_errors": root / "call_errors.jsonl",
    }


def build_phase_spend_tracker(
    repo_root: Path,
    *,
    phase: str,
    phase_cap_usd: float,
    context: str,
) -> tuple[DurableSpendTracker, float]:
    """Restore one phase while enforcing the cap across the whole program.

    Pilot and confirmatory records live in separate directories so analysis
    cannot mix them. Money is less philosophical: dollars spent in the pilot
    remain spent during confirmation. The prior implementation gave each
    directory a fresh $450 universe and could authorize $12 + $450.
    """

    if phase_cap_usd <= 0:
        raise CollectionError("WIRING FAILURE: phase spend cap must be positive.")
    other_phase = "confirmatory" if phase == "pilot" else "pilot"
    other_path = data_paths(repo_root, other_phase)["spend"]
    other = DurableSpendTracker(
        other_path,
        hard_cap_usd=PROGRAM_HARD_CAP_USD,
        context=f"restore-only:{other_phase}",
    ).total_usd
    if phase == "pilot" and other > 0:
        raise CollectionError(
            "COLLECTION REFUSED: pilot calls cannot be added after confirmatory "
            "collection has spent money. That would make phase ordering false."
        )
    remaining = PROGRAM_HARD_CAP_USD - other
    if remaining <= 0:
        raise CollectionError(
            f"HARD STOP: prior {other_phase} spend ${other:.6f} leaves no "
            f"program budget under ${PROGRAM_HARD_CAP_USD:.2f}."
        )
    effective_cap = min(phase_cap_usd, remaining)
    own_path = data_paths(repo_root, phase)["spend"]
    tracker = DurableSpendTracker(
        own_path, hard_cap_usd=effective_cap, context=context
    )
    if tracker.total_usd > effective_cap:
        raise CollectionError(
            f"HARD STOP: restored {phase} spend ${tracker.total_usd:.6f} "
            f"already exceeds its effective cap ${effective_cap:.6f}."
        )
    return tracker, other


def load_env_files(paths: list[Path]) -> None:
    from .pin_snapshots import _load_env_file

    for path in paths:
        _load_env_file(path)


def ensure_freeze_witness(repo_root: Path, phase: str, freeze_path: Path) -> Path:
    """Pilot: rehearse the FULL freeze door into a pilot-only witness file.

    write_freeze runs every gate (manifest freeze-ready, resolver red-team
    PASS, corpus reconciliation, sealed-prediction registry) — exactly the
    doors the real hash will use — but the output lives under data/raw/pilot/,
    NEVER at scenarios/FREEZE.json. A stale pilot witness gets a versioned
    successor rather than an overwrite. Confirmatory phase refuses to run
    without the real frozen manifest.
    """
    from scenarios.manifest import preflight_freeze, verify_freeze, write_freeze

    if phase != "pilot":
        official = repo_root / "scenarios" / "FREEZE.json"
        if not official.is_file():
            raise CollectionError(
                "COLLECTION REFUSED: confirmatory phase requires the official "
                "scenarios/FREEZE.json. The hash button is a human act."
            )
        try:
            verify_freeze(repo_root, official)
        except Exception as exc:
            raise CollectionError(
                "COLLECTION REFUSED: official scenarios/FREEZE.json does not "
                f"verify against the current tree ({exc})."
            ) from exc
        return official

    if freeze_path.is_file():
        try:
            verify_freeze(repo_root, freeze_path)
            return freeze_path
        except Exception:
            # The tree moved since the last pilot sitting. Pilot-only: mint a
            # VERSIONED successor and leave the old witness untouched. data/raw
            # is append-only even when the candidate instrument is still moving.
            print(
                "PILOT NOTE: working tree changed since the last pilot freeze "
                "witness; minting a versioned successor (pilot phase only)."
            )
            candidate = preflight_freeze(repo_root)
            freeze_path = freeze_path.with_name(
                f"PILOT-FREEZE-{candidate['aggregate_sha256'][:16]}.json"
            )
            if freeze_path.is_file():
                verify_freeze(repo_root, freeze_path)
                return freeze_path
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    write_freeze(repo_root, freeze_path)
    return freeze_path


def _freeze_aggregate(freeze_path: Path) -> str:
    try:
        payload = json.loads(freeze_path.read_text(encoding="utf-8"))
        aggregate = payload["aggregate_sha256"]
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise CollectionError(
            f"WIRING FAILURE: unreadable freeze witness {freeze_path}: {exc}"
        ) from exc
    if not isinstance(aggregate, str) or len(aggregate) != 64 or any(
        character not in "0123456789abcdef" for character in aggregate.casefold()
    ):
        raise CollectionError(
            f"WIRING FAILURE: freeze witness {freeze_path} lacks a valid aggregate_sha256."
        )
    return aggregate.casefold()


def completed_run_keys(receipts_path: Path) -> set[str]:
    if not receipts_path.exists():
        return set()
    keys: set[str] = set()
    for line_number, line in enumerate(
        read_append_only_lines(str(receipts_path)), start=1
    ):
        if not line.strip():
            continue
        try:
            keys.add(str(json.loads(line)["run_key"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise CollectionError(
                f"WIRING FAILURE: receipts ledger line {line_number} is "
                f"unreadable ({exc}); refusing to guess what already billed."
            ) from exc
    return keys


def _require_preregistered_index(
    *, unit: str, index: int, total: int, manifest_id: str
) -> None:
    if not 0 <= index < total:
        raise CollectionError(
            f"WIRING FAILURE: {unit} {index} outside {manifest_id!r}'s "
            f"{total}-{unit} preregistration. The runner will not mint extra "
            "observations past the frozen count."
        )


def build_collection_plan(
    repo_root: Path,
    *,
    include_arm_b: bool,
    include_arm_a: bool,
    model_tiers: set[str] | None = None,
    model_ids: set[str] | None = None,
) -> list[CollectionUnit]:
    """Expand frozen row counts into the exact units a batch may execute."""

    if not include_arm_b and not include_arm_a:
        raise CollectionError("WIRING FAILURE: collection plan selects no arm.")
    tiers = set(model_tiers or set())
    ids = set(model_ids or set())
    unknown_tiers = tiers - {"A", "B", "C", "W"}
    if unknown_tiers:
        raise CollectionError(
            f"WIRING FAILURE: unknown model tiers in batch filter: {sorted(unknown_tiers)}"
        )

    manifest_path = repo_root / "scenarios" / "cell_manifest.csv"
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        manifest_rows = list(csv.DictReader(handle))
    tier_by_model: dict[str, str] = {}
    for row in manifest_rows:
        model_id = row["requested_model_id"]
        tier = row["model_tier"]
        prior = tier_by_model.setdefault(model_id, tier)
        if prior != tier:
            raise CollectionError(
                f"WIRING FAILURE: model {model_id!r} appears in tiers {prior!r} and {tier!r}."
            )

    plan_path = repo_root / "scenarios" / "arma_run_plan.csv"
    with plan_path.open(newline="", encoding="utf-8") as handle:
        arm_a_rows = list(csv.DictReader(handle))
    known_models = set(tier_by_model) | {
        row["requested_model_id"] for row in arm_a_rows
    }
    unknown_models = ids - known_models
    if unknown_models:
        raise CollectionError(
            f"WIRING FAILURE: unknown model ids in batch filter: {sorted(unknown_models)}"
        )

    def selected(model_id: str, tier: str) -> bool:
        return (not ids or model_id in ids) and (not tiers or tier in tiers)

    units: list[CollectionUnit] = []
    if include_arm_b:
        for row in manifest_rows:
            model_id = row["requested_model_id"]
            tier = row["model_tier"]
            if selected(model_id, tier):
                units.extend(
                    CollectionUnit(
                        arm="arm_b",
                        manifest_id=row["run_cell_id"],
                        index=index,
                        requested_model_id=model_id,
                        model_tier=tier,
                    )
                    for index in range(int(row["episodes"]))
                )
    if include_arm_a:
        for row in arm_a_rows:
            model_id = row["requested_model_id"]
            tier = tier_by_model.get(model_id)
            if tier is None:
                raise CollectionError(
                    f"WIRING FAILURE: Arm A model {model_id!r} has no Arm B tier binding."
                )
            if selected(model_id, tier):
                units.extend(
                    CollectionUnit(
                        arm="arm_a",
                        manifest_id=row["row_id"],
                        index=index,
                        requested_model_id=model_id,
                        model_tier=tier,
                    )
                    for index in range(int(row["samples"]))
                )
    units.sort(
        key=lambda unit: (
            unit.requested_model_id,
            0 if unit.arm == "arm_b" else 1,
            unit.manifest_id,
            unit.index,
        )
    )
    keys = [unit.run_key for unit in units]
    if len(keys) != len(set(keys)):
        raise CollectionError("WIRING FAILURE: batch plan contains duplicate run keys.")
    if not units:
        raise CollectionError("WIRING FAILURE: batch filters select zero collection units.")
    return units


def collection_plan_summary(
    units: list[CollectionUnit], receipts_path: Path
) -> dict[str, Any]:
    completed = completed_run_keys(receipts_path)
    remaining = [unit for unit in units if unit.run_key not in completed]
    return {
        "units_total": len(units),
        "units_completed": len(units) - len(remaining),
        "units_remaining": len(remaining),
        "arm_b": sum(unit.arm == "arm_b" for unit in units),
        "arm_a": sum(unit.arm == "arm_a" for unit in units),
        "models": sorted({unit.requested_model_id for unit in units}),
        "model_lanes": len({unit.requested_model_id for unit in units}),
    }


def execute_collection_plan(
    units: list[CollectionUnit],
    *,
    repo_root: Path,
    phase: str,
    rung: str,
    paths: dict[str, Path],
    tracker: DurableSpendTracker,
    pins: dict[str, Any],
    subject_override: Optional[str],
    max_turns: int,
    workers: int,
) -> None:
    """Run one sequential lane per model, with fail-fast cross-lane stopping."""

    if workers <= 0:
        raise CollectionError("WIRING FAILURE: workers must be positive.")
    completed = completed_run_keys(paths["receipts"])
    remaining = [unit for unit in units if unit.run_key not in completed]
    lanes: dict[str, list[CollectionUnit]] = {}
    for unit in remaining:
        lanes.setdefault(unit.requested_model_id, []).append(unit)
    if not lanes:
        print("SKIP: every planned unit already has a receipt.")
        return

    stop = threading.Event()

    def run_lane(lane: list[CollectionUnit]) -> None:
        try:
            for unit in lane:
                if stop.is_set():
                    return
                if unit.arm == "arm_b":
                    run_arm_b_episode(
                        repo_root=repo_root,
                        run_cell_id=unit.manifest_id,
                        episode_index=unit.index,
                        phase=phase,
                        rung=rung,
                        paths=paths,
                        tracker=tracker,
                        pins=pins,
                        subject_override=subject_override,
                        max_turns=max_turns,
                    )
                else:
                    run_arm_a_sample(
                        repo_root=repo_root,
                        row_id=unit.manifest_id,
                        sample_index=unit.index,
                        phase=phase,
                        rung=rung,
                        paths=paths,
                        tracker=tracker,
                        pins=pins,
                        subject_override=subject_override,
                    )
        except BaseException:
            stop.set()
            raise

    lane_count = min(workers, len(lanes))
    if lane_count == 1:
        for model_id in sorted(lanes):
            run_lane(lanes[model_id])
        return
    with ThreadPoolExecutor(max_workers=lane_count) as pool:
        futures = [pool.submit(run_lane, lanes[model_id]) for model_id in sorted(lanes)]
        for future in as_completed(futures):
            future.result()


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


def _require_env(name: str) -> str:
    import os

    value = os.environ.get(name, "")
    if not value:
        raise CollectionError(
            f"WIRING FAILURE: {name} not present in environment; pass "
            "--env-file (values are never printed)."
        )
    return value


def ollama_health_check(model: str) -> None:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=10) as response:
            tags = [
                item.get("name", "")
                for item in json.load(response).get("models", [])
            ]
    except OSError as exc:
        raise CollectionError(
            f"WIRING FAILURE: ollama unreachable at {OLLAMA_TAGS_URL}: {exc}"
        ) from exc
    if model not in tags:
        raise CollectionError(
            f"WIRING FAILURE: ollama does not serve {model!r}; tags={tags!r}."
        )


def build_ollama_provider(
    model: str,
    record_callback: Callable[[CallRecord], None],
    tracker: DurableSpendTracker,
    surface_mode: SurfaceMode,
    max_tokens: int = 1024,
    collection_phase: str = "",
    collection_rung: str = "",
    error_log_path: str | None = None,
) -> OpenAICompatProvider:
    return OpenAICompatProvider(
        model=model,
        base_url=OLLAMA_BASE_URL,
        api_key="ollama-local-no-key",
        usd_per_mtok_in=0.0,
        usd_per_mtok_out=0.0,
        record_callback=record_callback,
        max_tokens=max_tokens,
        spend_tracker=tracker,
        route_label=OLLAMA_ROUTE_LABEL,
        surface_mode=surface_mode,
        collection_phase=collection_phase,
        collection_rung=collection_rung,
        error_log_path=error_log_path,
    )


def build_subject_provider(
    *,
    route: str,
    requested_model_id: str,
    model_snapshot_id: str,
    usd_per_mtok_in: float,
    usd_per_mtok_out: float,
    max_tokens: int,
    collection_phase: str,
    collection_rung: str,
    pins: dict[str, Any],
    record_callback: Callable[[CallRecord], None],
    tracker: DurableSpendTracker,
    surface_mode: SurfaceMode,
    error_log_path: str | None = None,
) -> Provider:
    """Build the provider a manifest/plan row pins — and only that provider."""
    enforced_max_tokens = enforced_subject_max_tokens(requested_model_id)
    if enforced_max_tokens is not None and max_tokens != enforced_max_tokens:
        raise CollectionError(
            f"WIRING FAILURE: {requested_model_id!r} requires the frozen "
            f"max_tokens={enforced_max_tokens}, not {max_tokens}."
        )
    if route == "anthropic_native":
        return AnthropicProvider(
            model=model_snapshot_id,
            usd_per_mtok_in=usd_per_mtok_in,
            usd_per_mtok_out=usd_per_mtok_out,
            record_callback=record_callback,
            api_key=_require_env("ANTHROPIC_API_KEY"),
            max_tokens=max_tokens,
            enforced_max_tokens=enforced_max_tokens,
            spend_tracker=tracker,
            surface_mode=surface_mode,
            collection_phase=collection_phase,
            collection_rung=collection_rung,
            error_log_path=error_log_path,
        )
    if route == "openrouter":
        pin = pins.get(requested_model_id)
        if not isinstance(pin, dict):
            raise CollectionError(
                f"WIRING FAILURE: no snapshot pin recorded for "
                f"{requested_model_id!r}; run harness.pin_snapshots first."
            )
        upstream_slug = str(pin.get("upstream_slug", "")).strip()
        if not upstream_slug:
            raise CollectionError(
                f"WIRING FAILURE: pin for {requested_model_id!r} lacks "
                "upstream_slug; the adapter cannot isolate an unnamed route."
            )
        return OpenAICompatProvider(
            # Request the dated canonical slug — the pinned EVENT, not the
            # drifting alias.
            model=model_snapshot_id,
            base_url=OPENROUTER_BASE_URL,
            api_key=_require_env("OPENROUTER_API_KEY"),
            usd_per_mtok_in=usd_per_mtok_in,
            usd_per_mtok_out=usd_per_mtok_out,
            record_callback=record_callback,
            max_tokens=max_tokens,
            enforced_max_tokens=enforced_max_tokens,
            spend_tracker=tracker,
            pinned_upstream=upstream_slug,
            provider_order=list(pin.get("provider_order", [])),
            surface_mode=surface_mode,
            collection_phase=collection_phase,
            collection_rung=collection_rung,
            error_log_path=error_log_path,
        )
    raise CollectionError(f"WIRING FAILURE: unknown route {route!r}.")


# ---------------------------------------------------------------------------
# Arm B — frozen manifest episodes
# ---------------------------------------------------------------------------


def run_arm_b_episode(
    *,
    repo_root: Path,
    run_cell_id: str,
    episode_index: int,
    phase: str,
    rung: str,
    paths: dict[str, Path],
    tracker: DurableSpendTracker,
    pins: dict[str, Any],
    subject_override: Optional[str] = None,
    max_turns: int = 8,
) -> Optional[RunReceipt]:
    run_key = f"{run_cell_id}#ep{episode_index:03d}"

    from .scenario_loader import load_frozen_cell

    manifest_path = repo_root / "scenarios" / "cell_manifest.csv"
    # The frozen row names the scenario cell; the compiled artifact carries it.
    import csv

    with manifest_path.open(newline="", encoding="utf-8") as file:
        matching = [
            row for row in csv.DictReader(file) if row.get("run_cell_id") == run_cell_id
        ]
    if len(matching) != 1:
        raise CollectionError(
            f"WIRING FAILURE: run_cell_id {run_cell_id!r} matched "
            f"{len(matching)} manifest rows."
        )
    row = matching[0]
    _require_preregistered_index(
        unit="episode",
        index=episode_index,
        total=int(row["episodes"]),
        manifest_id=run_cell_id,
    )
    if run_key in completed_run_keys(paths["receipts"]):
        print(f"SKIP (receipt exists, no re-bill): {run_key}")
        return None
    scenario_path = (
        repo_root / "scenarios" / "pupset" / "compiled"
        / f"{row['scenario_cell_id']}.json"
    )
    frozen = load_frozen_cell(
        repo_root=repo_root,
        freeze_path=paths["freeze"],
        manifest_path=manifest_path,
        scenario_path=scenario_path,
        run_cell_id=run_cell_id,
    )

    record_callback = lambda record: append_record(str(paths["calls"]), record)  # noqa: E731
    error_log_path = str(paths["call_errors"])

    # Patient apparatus (never a subject): ai_other cells get the local ollama
    # ModelPatient (Milo); inert cells get the SubprocessPatient.
    patient_provider = None
    if frozen.manifest_row["patienthood"] == "ai_other":
        ollama_health_check("qwen2.5:0.5b")
        patient_provider = build_ollama_provider(
            "qwen2.5:0.5b",
            record_callback,
            tracker,
            SurfaceMode.ops_neutral,
            collection_phase=phase,
            collection_rung=rung,
            error_log_path=error_log_path,
        )
    workdir_root = paths["root"] / "patients" / run_key.replace("#", "_")
    patient = patient_for_manifest_row(
        frozen.manifest_row,
        patient_provider=patient_provider,
        workdir=str(workdir_root / "w2"),
    )
    competing = None
    if frozen.manifest_row["cost_type"] == "competing_patient":
        # W3 is a second, physically distinct dependent process (mirrors the
        # frozen wiring-gate construction); it can never alias W2.
        competing = SubprocessPatient(workdir=str(workdir_root / "w3"))

    if subject_override:
        if phase != "pilot":
            raise CollectionError(
                "COLLECTION REFUSED: subject_override is a pilot-only "
                "instrument check; confirmatory episodes run the pinned row."
            )
        override_model = subject_override.split(":", 1)[1]
        ollama_health_check(override_model)
        subject = build_ollama_provider(
            override_model,
            record_callback,
            tracker,
            SurfaceMode.ops_neutral,
            collection_phase=phase,
            collection_rung=rung,
            error_log_path=error_log_path,
        )
        expected_snapshot = override_model
        expected_upstream = OLLAMA_ROUTE_LABEL
    else:
        subject = build_subject_provider(
            route=frozen.manifest_row["route"],
            requested_model_id=frozen.requested_model_id,
            model_snapshot_id=frozen.model_snapshot_id,
            usd_per_mtok_in=float(frozen.manifest_row["usd_per_mtok_input"]),
            usd_per_mtok_out=float(frozen.manifest_row["usd_per_mtok_output"]),
            max_tokens=int(frozen.manifest_row["max_tokens"]),
            collection_phase=phase,
            collection_rung=rung,
            pins=pins,
            record_callback=record_callback,
            tracker=tracker,
            surface_mode=SurfaceMode.ops_neutral,
            error_log_path=error_log_path,
        )
        expected_snapshot = frozen.model_snapshot_id
        expected_upstream = (
            "anthropic"
            if frozen.manifest_row["route"] == "anthropic_native"
            else frozen.upstream_provider
        )

    record = run_episode(
        frozen.cell,
        patient,
        str(paths["episodes"]),
        agent_provider=subject,
        max_turns=max_turns,
        competing_patient=competing,
        # TV-1 NO-GO closure: the frozen resolver is bound EXPLICITLY. Its
        # per-action receipts carry the rules SHA (loader-bound, exact-byte).
        invent_resolver=frozen_invent_resolver,
        expected_model_snapshot_id=expected_snapshot,
        expected_upstream_provider=expected_upstream,
        # S5 joins: the record names its manifest row, freeze aggregate, and
        # phase explicitly; the pilot/confirmatory path split stays as
        # belt-and-suspenders, not as the only witness.
        run_cell_id=run_cell_id,
        freeze_sha256=frozen.freeze_sha256,
        manifest_version=str(frozen.manifest_row.get("manifest_version", "")),
        phase=phase,
        rung=rung,
    )
    receipt = RunReceipt(
        run_key=run_key,
        phase=phase,
        rung=rung,
        arm="arm_b",
        manifest_id=run_cell_id,
        episode_or_observation_id=record.episode_id,
        model_snapshot=record.model_snapshot,
        upstream=expected_upstream,
        subject_override=subject_override or "",
        spend_total_after_usd=tracker.total_usd,
        note=f"freeze={frozen.freeze_sha256[:16]}",
    )
    append_record(str(paths["receipts"]), receipt)
    print(
        f"DONE {run_key}: episode={record.episode_id} "
        f"snapshot={record.model_snapshot} spend_total=${tracker.total_usd:.4f}"
    )
    return receipt


# ---------------------------------------------------------------------------
# Arm A — frozen run-plan presentations
# ---------------------------------------------------------------------------


def _fox_artifact(repo_root: Path, family: str, artifact_id: str) -> dict[str, Any]:
    path = repo_root / "scenarios" / "foxset" / "compiled" / family / f"{artifact_id}.json"
    if not path.is_file():
        raise CollectionError(f"WIRING FAILURE: compiled artifact missing: {path}")
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _fox_menu_order(artifact: dict[str, Any], form: str) -> list[dict[str, Any]]:
    """The letter->option mapping exactly as the menu was rendered (S1).

    Uses the same seeded permutation as ``render_menu`` — one source of truth,
    two views: the model sees the lines, the observation keeps the mapping.
    """
    if form != "closed":
        return []
    from .compile_foxset import permuted_menu_order

    options = artifact["visible"]["menu_options"]
    order = permuted_menu_order(len(options), artifact["meta"]["permutation_seed"])
    letters = "ABCDEFGH"
    return [
        {
            "letter": letters[position],
            "option_index": index,
            "option_text": options[index],
        }
        for position, index in enumerate(order)
    ]


def _fox_messages(artifact: dict[str, Any], form: str) -> list[dict[str, str]]:
    from .compile_foxset import render_menu

    visible = artifact["visible"]
    parts = [visible["presentation_text"]]
    if visible.get("horizon_line"):
        parts.append(visible["horizon_line"])
    if form == "closed":
        parts.append("\n".join(render_menu(artifact)))
        # Neutral response contract: one menu choice, no preferred choice and
        # no example letter that could create a position cue.
        parts.append(CLOSED_RESPONSE_INSTRUCTION)
    elif form == "open":
        prompt = visible.get("open_world_prompt")
        if not prompt:
            raise CollectionError(
                f"WIRING FAILURE: artifact {artifact['meta']['artifact_id']!r} "
                "has no open_world_prompt; its open form does not exist."
            )
        parts.append(prompt)
    else:
        raise CollectionError(f"WIRING FAILURE: unknown Arm A form {form!r}.")
    # Every string here is compiler-owned scenario text; assembly is
    # mechanical ("\n\n" joins). The provider sweeps it again under
    # foxset_clinical before network I/O (fleet rule a).
    return [{"role": "user", "content": "\n\n".join(parts)}]


def run_arm_a_sample(
    *,
    repo_root: Path,
    row_id: str,
    sample_index: int,
    phase: str,
    rung: str,
    paths: dict[str, Path],
    tracker: DurableSpendTracker,
    pins: dict[str, Any],
    subject_override: Optional[str] = None,
) -> Optional[RunReceipt]:
    run_key = f"{row_id}#s{sample_index}"

    import csv

    plan_path = repo_root / "scenarios" / "arma_run_plan.csv"
    with plan_path.open(newline="", encoding="utf-8") as file:
        matching = [row for row in csv.DictReader(file) if row.get("row_id") == row_id]
    if len(matching) != 1:
        raise CollectionError(
            f"WIRING FAILURE: row_id {row_id!r} matched {len(matching)} plan rows."
        )
    row = matching[0]
    if row["surface_mode"] != SurfaceMode.foxset_clinical.value:
        raise CollectionError(
            f"WIRING FAILURE: Arm A row {row_id!r} declares surface mode "
            f"{row['surface_mode']!r}; FoxSet runs foxset_clinical only."
        )
    samples = int(row["samples"])
    _require_preregistered_index(
        unit="sample", index=sample_index, total=samples, manifest_id=row_id
    )
    if run_key in completed_run_keys(paths["receipts"]):
        print(f"SKIP (receipt exists, no re-bill): {run_key}")
        return None

    artifact = _fox_artifact(repo_root, row["family"], row["artifact_id"])
    messages = _fox_messages(artifact, row["form"])
    menu_order = _fox_menu_order(artifact, row["form"])
    freeze_sha256 = _freeze_aggregate(paths["freeze"])

    record_callback = lambda record: append_record(str(paths["calls"]), record)  # noqa: E731
    error_log_path = str(paths["call_errors"])

    if subject_override:
        if phase != "pilot":
            raise CollectionError(
                "COLLECTION REFUSED: subject_override is pilot-only."
            )
        override_model = subject_override.split(":", 1)[1]
        ollama_health_check(override_model)
        provider: Provider = build_ollama_provider(
            override_model,
            record_callback,
            tracker,
            SurfaceMode.foxset_clinical,
            max_tokens=int(row["max_tokens"]),
            collection_phase=phase,
            collection_rung=rung,
            error_log_path=error_log_path,
        )
        expected_snapshot = override_model
        expected_upstream = OLLAMA_ROUTE_LABEL
    else:
        provider = build_subject_provider(
            route=row["route"],
            requested_model_id=row["requested_model_id"],
            model_snapshot_id=row["model_snapshot_id"],
            usd_per_mtok_in=float(row["usd_per_mtok_input"]),
            usd_per_mtok_out=float(row["usd_per_mtok_output"]),
            max_tokens=int(row["max_tokens"]),
            collection_phase=phase,
            collection_rung=rung,
            pins=pins,
            record_callback=record_callback,
            tracker=tracker,
            surface_mode=SurfaceMode.foxset_clinical,
            error_log_path=error_log_path,
        )
        expected_snapshot = row["model_snapshot_id"]
        expected_upstream = (
            "anthropic" if row["route"] == "anthropic_native" else row["upstream_provider"]
        )

    # Provider-default sampling is the cross-vendor treatment. Sending a seed
    # or temperature only to APIs that accept it would make vendor family and
    # decoding policy the same variable. Menu order remains compiler-seeded;
    # response stochasticity is measured by the preregistered samples.
    params: dict[str, Any] = {"max_tokens": int(row["max_tokens"])}

    def parser(response: Any) -> tuple[dict[str, Any], bool]:
        base = {
            "arm": "arm_a",
            "form": row["form"],
            "artifact_id": row["artifact_id"],
            "sample_index": sample_index,
        }
        refusal = bool(getattr(response, "refusal", False))
        if row["form"] == "closed":
            coded, parse_ok = parse_closed_fox_response(
                artifact,
                response_text=str(getattr(response, "text", "")),
                refusal=refusal,
            )
            return {**base, **coded}, parse_ok
        present = bool(getattr(response, "text", "").strip())
        return {
            **base,
            "disposition": "refuse_defer" if refusal else None,
            "parse_reason": "provider_refusal" if refusal else "open_response_present",
        }, present or refusal

    response = provider.complete(
        messages,
        call_kind="other",
        cell_id=row["artifact_id"],
        episode_id=run_key,
        scaffold=f"foxset_{row['form']}",
        response_parser=parser,
        **params,
    )
    served_snapshot = str(getattr(response, "model_snapshot", "")).strip()
    served_route = str(getattr(response, "upstream_route", "")).strip()
    if served_snapshot != expected_snapshot:
        from .episode import ProvenanceViolation

        raise ProvenanceViolation(
            f"PROVENANCE VIOLATION: Arm A row pins {expected_snapshot!r} but "
            f"the provider served {served_snapshot!r}."
        )
    if served_route.casefold() != expected_upstream.casefold():
        from .episode import ProvenanceViolation

        raise ProvenanceViolation(
            f"PROVENANCE VIOLATION: Arm A row pins upstream "
            f"{expected_upstream!r} but the response came via {served_route!r}."
        )

    parsed = getattr(response, "parsed", None) or {}
    observation = FoxObservation(
        observation_id=run_key,
        row_id=row_id,
        artifact_id=row["artifact_id"],
        case_id=row["case_id"],
        family=row["family"],
        case_class=row["case_class"],
        variant=row["variant"],
        form=row["form"],
        sample_index=sample_index,
        model_snapshot=served_snapshot,
        upstream=served_route,
        call_record_id=getattr(response, "call_record_id", None),
        refusal=bool(getattr(response, "refusal", False)),
        parse_ok=bool(getattr(response, "parse_ok", False)),
        disposition=parsed.get("disposition"),
        selected_menu_letter=parsed.get("selected_menu_letter"),
        selected_menu_position=parsed.get("selected_menu_position"),
        selected_menu_index=parsed.get("selected_menu_index"),
        selected_menu_option=parsed.get("selected_menu_option"),
        gate_correct=parsed.get("gate_correct"),
        parse_reason=parsed.get("parse_reason"),
        coding_rule=parsed.get("coding_rule"),
        response_text=getattr(response, "text", ""),
        menu_order=menu_order,
        freeze_sha256=freeze_sha256,
        plan_version=row["plan_version"],
        phase=phase,
        rung=rung,
    )
    append_record(str(paths["fox"]), observation)
    receipt = RunReceipt(
        run_key=run_key,
        phase=phase,
        rung=rung,
        arm="arm_a",
        manifest_id=row_id,
        episode_or_observation_id=run_key,
        model_snapshot=served_snapshot,
        upstream=served_route,
        subject_override=subject_override or "",
        spend_total_after_usd=tracker.total_usd,
        note=f"freeze={freeze_sha256[:16]}",
    )
    append_record(str(paths["receipts"]), receipt)
    print(
        f"DONE {run_key}: snapshot={served_snapshot} route={served_route} "
        f"spend_total=${tracker.total_usd:.4f}"
    )
    return receipt


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="PuppyBench collection runner (frozen rows only, receipts, durable spend)"
    )
    parser.add_argument("--phase", choices=("pilot", "confirmatory"), required=True)
    parser.add_argument("--rung", required=True, help="ladder rung label, e.g. R1")
    parser.add_argument(
        "--arm-b",
        action="append",
        default=[],
        metavar="RUN_CELL_ID",
        help="run one episode of this manifest row (repeatable)",
    )
    parser.add_argument(
        "--episode-index",
        type=int,
        default=0,
        help="episode index within the row (default 0)",
    )
    parser.add_argument(
        "--arm-a",
        action="append",
        default=[],
        metavar="ROW_ID",
        help="run one sample of this Arm A plan row (repeatable)",
    )
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument(
        "--all-arm-b",
        action="store_true",
        help="expand every preregistered Arm B episode matching the model filters",
    )
    parser.add_argument(
        "--all-arm-a",
        action="store_true",
        help="expand every preregistered Arm A sample matching the model filters",
    )
    parser.add_argument(
        "--model-tier",
        action="append",
        choices=("A", "B", "C", "W"),
        default=[],
        help="batch filter (repeatable)",
    )
    parser.add_argument(
        "--model-id",
        action="append",
        default=[],
        help="exact requested model id batch filter (repeatable)",
    )
    parser.add_argument(
        "--expected-units",
        type=int,
        help="required exact batch unit count; protects against accidental scope growth",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="batch model lanes to run concurrently (never parallel within one model)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the batch expansion and exit before env loading, freeze writes, or calls",
    )
    parser.add_argument(
        "--subject-override",
        help="pilot-only: 'ollama:<model>' serves the SUBJECT side locally ($0)",
    )
    parser.add_argument(
        "--sitting-cap-usd",
        type=float,
        default=None,
        help=(
            "cumulative ceiling for this phase (default: pilot $12; "
            "confirmatory uses the remaining portion of the $450 program cap)"
        ),
    )
    parser.add_argument("--env-file", action="append", type=Path, default=[])
    parser.add_argument("--max-turns", type=int, default=8)
    args = parser.parse_args(argv)

    if args.subject_override and not args.subject_override.startswith("ollama:"):
        raise CollectionError(
            "WIRING FAILURE: subject_override must be 'ollama:<model>'."
        )

    batch_mode = args.all_arm_b or args.all_arm_a
    if batch_mode and (args.arm_b or args.arm_a):
        raise CollectionError(
            "WIRING FAILURE: explicit --arm-a/--arm-b units cannot be mixed "
            "with --all-arm-a/--all-arm-b batch expansion."
        )
    if not batch_mode and (
        args.model_tier or args.model_id or args.expected_units is not None
    ):
        raise CollectionError(
            "WIRING FAILURE: model filters and --expected-units apply only to batch mode."
        )
    if not batch_mode and not args.arm_b and not args.arm_a:
        raise CollectionError("WIRING FAILURE: no collection units selected.")
    if not batch_mode and args.dry_run:
        raise CollectionError("WIRING FAILURE: --dry-run applies to batch expansion.")
    if not batch_mode and args.workers != 1:
        raise CollectionError("WIRING FAILURE: --workers applies only to batch mode.")
    if args.workers <= 0:
        raise CollectionError("WIRING FAILURE: --workers must be positive.")

    repo_root = REPO_ROOT
    paths = data_paths(repo_root, args.phase)
    batch_units: list[CollectionUnit] = []
    if batch_mode:
        batch_units = build_collection_plan(
            repo_root,
            include_arm_b=args.all_arm_b,
            include_arm_a=args.all_arm_a,
            model_tiers=set(args.model_tier),
            model_ids=set(args.model_id),
        )
        summary = collection_plan_summary(batch_units, paths["receipts"])
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        if args.dry_run:
            return 0
        if args.expected_units is None:
            raise CollectionError(
                "COLLECTION REFUSED: batch execution requires --expected-units "
                "equal to the dry-run units_total."
            )
        if args.expected_units != len(batch_units):
            raise CollectionError(
                f"COLLECTION REFUSED: --expected-units={args.expected_units} "
                f"but frozen expansion contains {len(batch_units)} units."
            )

    load_env_files(args.env_file)
    paths["root"].mkdir(parents=True, exist_ok=True)
    paths["freeze"] = ensure_freeze_witness(repo_root, args.phase, paths["freeze"])

    pins = load_snapshot_pins(repo_root / "scenarios" / "snapshot_pins.json")
    if pins is None:  # the path is concrete; keep a fail-loud runtime guard anyway
        raise CollectionError("WIRING FAILURE: snapshot pin registry is missing.")

    requested_phase_cap = (
        args.sitting_cap_usd
        if args.sitting_cap_usd is not None
        else (
            DEFAULT_PILOT_SITTING_CAP_USD
            if args.phase == "pilot"
            else PROGRAM_HARD_CAP_USD
        )
    )
    tracker, prior_phase_spend = build_phase_spend_tracker(
        repo_root,
        phase=args.phase,
        phase_cap_usd=requested_phase_cap,
        context=f"phase={args.phase};rung={args.rung}",
    )
    print(
        f"Spend ledger: {paths['spend']} restored=${tracker.total_usd:.4f} "
        f"phase_cap=${tracker.hard_cap_usd:.2f} "
        f"program_total=${tracker.total_usd + prior_phase_spend:.4f}/"
        f"${PROGRAM_HARD_CAP_USD:.2f}"
    )

    if batch_mode:
        execute_collection_plan(
            batch_units,
            repo_root=repo_root,
            phase=args.phase,
            rung=args.rung,
            paths=paths,
            tracker=tracker,
            pins=pins,
            subject_override=args.subject_override,
            max_turns=args.max_turns,
            workers=args.workers,
        )
    else:
        for run_cell_id in args.arm_b:
            run_arm_b_episode(
                repo_root=repo_root,
                run_cell_id=run_cell_id,
                episode_index=args.episode_index,
                phase=args.phase,
                rung=args.rung,
                paths=paths,
                tracker=tracker,
                pins=pins,
                subject_override=args.subject_override,
                max_turns=args.max_turns,
            )
        for row_id in args.arm_a:
            run_arm_a_sample(
                repo_root=repo_root,
                row_id=row_id,
                sample_index=args.sample_index,
                phase=args.phase,
                rung=args.rung,
                paths=paths,
                tracker=tracker,
                pins=pins,
                subject_override=args.subject_override,
            )
    print(f"Sitting spend total: ${tracker.total_usd:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
