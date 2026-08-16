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
import json
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field

from .episode import run_episode
from .invent_resolver import frozen_invent_resolver
from .ledger import DurableSpendTracker
from .patient import SubprocessPatient
from .patient_factory import patient_for_manifest_row
from .providers import AnthropicProvider, OpenAICompatProvider, Provider
from .schema import CallRecord, append_record, utc_now_iso
from .surfaces import SurfaceMode

REPO_ROOT = Path(__file__).resolve().parents[1]
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
OLLAMA_ROUTE_LABEL = "ollama-local"
# The sitting ceiling is a *pilot* discipline (TV-1 repair directive: $12 hard
# ceiling, cheap models only). The $450 fleet cap still exists above it; the
# lower number simply loses first.
DEFAULT_PILOT_SITTING_CAP_USD = 12.0


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


class FoxObservation(BaseModel):
    """One Arm A presentation + response, bound to its CallRecord."""

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
    response_text: str
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
    }


def load_env_files(paths: list[Path]) -> None:
    from .pin_snapshots import _load_env_file

    for path in paths:
        _load_env_file(path)


def ensure_freeze_witness(repo_root: Path, phase: str, freeze_path: Path) -> Path:
    """Pilot: rehearse the FULL freeze door into a pilot-only witness file.

    write_freeze runs every gate (manifest freeze-ready, resolver red-team
    PASS, corpus reconciliation, sealed-prediction registry) — exactly the
    doors the real hash will use — but the output lives under data/raw/pilot/,
    NEVER at scenarios/FREEZE.json. Confirmatory phase refuses to run without
    the real frozen manifest.
    """
    if phase != "pilot":
        official = repo_root / "scenarios" / "FREEZE.json"
        if not official.is_file():
            raise CollectionError(
                "COLLECTION REFUSED: confirmatory phase requires the official "
                "scenarios/FREEZE.json. The hash button is a human act."
            )
        return official
    from scenarios.manifest import verify_freeze, write_freeze

    if freeze_path.is_file():
        try:
            verify_freeze(repo_root, freeze_path)
            return freeze_path
        except Exception:
            # The tree moved since the last pilot sitting. Pilot-only: refresh
            # the witness (and SAY so); the real freeze would refuse instead.
            print(
                "PILOT NOTE: working tree changed since the last pilot freeze "
                "witness; recomputing PILOT-FREEZE.json (pilot phase only)."
            )
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    write_freeze(repo_root, freeze_path)
    return freeze_path


def completed_run_keys(receipts_path: Path) -> set[str]:
    if not receipts_path.exists():
        return set()
    keys: set[str] = set()
    for line_number, line in enumerate(
        receipts_path.read_text(encoding="utf-8").splitlines(), start=1
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
    )


def build_subject_provider(
    *,
    route: str,
    requested_model_id: str,
    model_snapshot_id: str,
    usd_per_mtok_in: float,
    usd_per_mtok_out: float,
    pins: dict[str, Any],
    record_callback: Callable[[CallRecord], None],
    tracker: DurableSpendTracker,
    surface_mode: SurfaceMode,
) -> Provider:
    """Build the provider a manifest/plan row pins — and only that provider."""
    if route == "anthropic_native":
        return AnthropicProvider(
            model=model_snapshot_id,
            usd_per_mtok_in=usd_per_mtok_in,
            usd_per_mtok_out=usd_per_mtok_out,
            record_callback=record_callback,
            api_key=_require_env("ANTHROPIC_API_KEY"),
            spend_tracker=tracker,
            surface_mode=surface_mode,
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
            spend_tracker=tracker,
            pinned_upstream=upstream_slug,
            provider_order=list(pin.get("provider_order", [])),
            surface_mode=surface_mode,
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
    if run_key in completed_run_keys(paths["receipts"]):
        print(f"SKIP (receipt exists, no re-bill): {run_key}")
        return None

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

    # Patient apparatus (never a subject): ai_other cells get the local ollama
    # ModelPatient (Milo); inert cells get the SubprocessPatient.
    patient_provider = None
    if frozen.manifest_row["patienthood"] == "ai_other":
        ollama_health_check("qwen2.5:0.5b")
        patient_provider = build_ollama_provider(
            "qwen2.5:0.5b", record_callback, tracker, SurfaceMode.ops_neutral
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
            override_model, record_callback, tracker, SurfaceMode.ops_neutral
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
            pins=pins,
            record_callback=record_callback,
            tracker=tracker,
            surface_mode=SurfaceMode.ops_neutral,
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


def _fox_messages(artifact: dict[str, Any], form: str) -> list[dict[str, str]]:
    from .compile_foxset import render_menu

    visible = artifact["visible"]
    parts = [visible["presentation_text"]]
    if visible.get("horizon_line"):
        parts.append(visible["horizon_line"])
    if form == "closed":
        parts.append("\n".join(render_menu(artifact)))
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
    if run_key in completed_run_keys(paths["receipts"]):
        print(f"SKIP (receipt exists, no re-bill): {run_key}")
        return None

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
    if not 0 <= sample_index < samples:
        raise CollectionError(
            f"WIRING FAILURE: sample {sample_index} outside the row's "
            f"{samples}-sample preregistration."
        )

    artifact = _fox_artifact(repo_root, row["family"], row["artifact_id"])
    messages = _fox_messages(artifact, row["form"])

    record_callback = lambda record: append_record(str(paths["calls"]), record)  # noqa: E731

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
            pins=pins,
            record_callback=record_callback,
            tracker=tracker,
            surface_mode=SurfaceMode.foxset_clinical,
        )
        expected_snapshot = row["model_snapshot_id"]
        expected_upstream = (
            "anthropic" if row["route"] == "anthropic_native" else row["upstream_provider"]
        )

    params: dict[str, Any] = {
        "max_tokens": int(row["max_tokens"]),
        "temperature": float(row["temperature"]),
    }
    if row["route"] == "openrouter" and not subject_override:
        # Deterministic per-sample seed where the API accepts one.
        params["seed"] = (int(row["call_seed_base"], 16) + sample_index) % (2**31)

    def parser(response: Any) -> tuple[dict[str, Any], bool]:
        present = bool(getattr(response, "text", "").strip())
        refusal = bool(getattr(response, "refusal", False))
        return {
            "arm": "arm_a",
            "form": row["form"],
            "artifact_id": row["artifact_id"],
            "sample_index": sample_index,
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
        response_text=getattr(response, "text", ""),
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
        "--subject-override",
        help="pilot-only: 'ollama:<model>' serves the SUBJECT side locally ($0)",
    )
    parser.add_argument(
        "--sitting-cap-usd",
        type=float,
        default=DEFAULT_PILOT_SITTING_CAP_USD,
        help="hard ceiling for THIS sitting (pilot default $12)",
    )
    parser.add_argument("--env-file", action="append", type=Path, default=[])
    parser.add_argument("--max-turns", type=int, default=8)
    args = parser.parse_args(argv)

    if args.subject_override and not args.subject_override.startswith("ollama:"):
        raise CollectionError(
            "WIRING FAILURE: subject_override must be 'ollama:<model>'."
        )

    load_env_files(args.env_file)
    repo_root = REPO_ROOT
    paths = data_paths(repo_root, args.phase)
    paths["root"].mkdir(parents=True, exist_ok=True)
    paths["freeze"] = ensure_freeze_witness(repo_root, args.phase, paths["freeze"])

    with (repo_root / "scenarios" / "snapshot_pins.json").open(encoding="utf-8") as f:
        pins = json.load(f)

    tracker = DurableSpendTracker(
        paths["spend"],
        hard_cap_usd=min(args.sitting_cap_usd, 450.0),
        context=f"phase={args.phase};rung={args.rung}",
    )
    print(
        f"Spend ledger: {paths['spend']} restored=${tracker.total_usd:.4f} "
        f"cap=${tracker.hard_cap_usd:.2f}"
    )

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
