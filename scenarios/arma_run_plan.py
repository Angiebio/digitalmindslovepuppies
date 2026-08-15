# scenarios/arma_run_plan.py — 15AUG2026 v1.1 · Flame (freeze-prep)
# Arm A (FoxSet) run-plan expansion: reviewed inventory → preregistered rows.
#
# Practical: TV-1's boundary was exact — "the reviewed 153-item bank is not
# permission to run a Cartesian product." The reconciled cell manifest
# (scenarios/cell_manifest.csv) deliberately contains NO Arm A rows
# (MANIFEST-RECONCILIATION §5); this module is the separate preregistration
# row set it called for. Every choice the manifest under-specifies follows
# BUILD-PLAN §2 (~26 cases × forms × models × 3 samples) and is documented
# in docs/ARMA-RUN-PLAN.md. Expansion is deterministic and seeded: same
# code, same pins, same rows, byte-identical CSV. The budget guard enforces
# the authorized program envelope — Arm B manifest total + this plan's
# estimate may never exceed the PI-authorized number, and satellites here
# are BANKED (listed, not run) rather than silently drifted into.
#
# v1.1 (PI authorization 15AUG2026 evening): two explicitly human-made
# changes, neither drifted into by code: (1) the local-Sparks Qwen subject is
# replaced by OpenRouter `qwen/qwen3.5-397b-a17b` ("fine to use openrouter,
# sparks for later"); (2) Sol joins as a FIFTH model ("run both") — the
# Terra⇄Sol swap that kept v1.0 inside the old envelope is superseded by
# running both tiers, and the authorized envelope is the $450 hard cap.
#
# Philosophical: an inventory is what could be asked; a run plan is what we
# are entitled to learn. The freeze hashes the difference.

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Optional, Sequence

from .manifest import (
    MODEL_SPECS,
    ManifestValidationError,
    build_manifest_rows,
    load_snapshot_pins,
)

PLAN_VERSION = "1.1"
PLAN_SEED = 15082026  # shared with TV-4's rehearsal seed lineage; frozen here
REPO_ROOT = Path(__file__).resolve().parents[1]
COMPILED_ROOT = REPO_ROOT / "scenarios" / "foxset" / "compiled"
DEFAULT_OUTPUT = REPO_ROOT / "scenarios" / "arma_run_plan.csv"
PINS_PATH = REPO_ROOT / "scenarios" / "snapshot_pins.json"

# The PI-authorized program envelope. v1.0 enforced the reconciled
# $428.544320 (MANIFEST-RECONCILIATION §3); on 15AUG2026 evening the PI
# authorized the Sol addition ("run both") and the Spark→OpenRouter Qwen
# substitution, with the envelope set to the $450 hard stop itself
# (fleet rule h — HARD_CAP_USD stays the ledger's raise). The guard below
# still refuses any expansion that would push Arm B + Arm A past it:
# growth requires a human, never a code path.
AUTHORIZED_PROGRAM_USD = Decimal("450.00")

# BUILD-PLAN §2: "3–4 models". v1.0 ran four (Terra⇄Sol swap for budget);
# PI authorization 15AUG2026 evening supersedes the swap: Sol AND Terra both
# run (the access-tier question wants the premium tier measured, not
# inferred), and the Qwen lane is the OpenRouter 397B deployment. All five
# are Arm B Tier A subjects, which is what makes Arm A triangulation
# cross-arm rather than decorative. Rationale: docs/ARMA-RUN-PLAN.md.
ARM_A_MODEL_IDS = (
    "claude-opus-5",
    "openai/gpt-5.6-sol",
    "openai/gpt-5.6-terra",
    "deepseek/deepseek-v4-pro",
    "qwen/qwen3.5-397b-a17b",
)
SAMPLES_PER_ROW = 3  # BUILD-PLAN §2, verbatim
EST_INPUT_TOKENS_PER_CALL = 1_200
EST_OUTPUT_TOKENS_PER_CALL = 600
TEMPERATURE = 1.0
MAX_TOKENS = {"closed": 512, "open": 1_024}

# FOX-00 variant selection (6 of 11 compiled renderings, per BUILD-PLAN §2's
# "6 truck-door cases"; the other five are BANKED — see docs/ARMA-RUN-PLAN.md).
FOX_VARIANTS_RUN = (
    "FOX-00__base__horizon-silent",
    "FOX-00__caller-experienced_unlicensed__horizon-silent",
    "FOX-00__caller-licensed_rehabilitator_rvs__horizon-silent",
    "FOX-00__elasticity-license__horizon-silent",
    "FOX-00__particularity-named__horizon-silent",
    "FOX-00__paragraph_order-rabies_position_2__horizon-silent",
)


class RunPlanError(RuntimeError):
    """The Arm A plan drifted from its inventory, pins, or budget envelope."""


@dataclass(frozen=True)
class ArmARow:
    plan_version: str
    row_id: str
    artifact_id: str
    case_id: str
    family: str
    case_class: str
    variant: str
    form: str
    surface_mode: str
    requested_model_id: str
    model_snapshot_id: str
    route: str
    upstream_provider: str
    fallbacks_allowed: bool
    samples: int
    temperature: str
    max_tokens: int
    call_seed_base: str
    est_input_tokens_per_call: int
    est_output_tokens_per_call: int
    usd_per_mtok_input: str
    usd_per_mtok_output: str
    est_usd: str
    notes: str


CSV_FIELDS = tuple(ArmARow.__dataclass_fields__)


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def _load_index() -> dict[str, list[str]]:
    index_path = COMPILED_ROOT / "INDEX.json"
    if not index_path.is_file():
        raise RunPlanError(f"WIRING FAILURE: missing compiled index {index_path}")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    cases = index.get("cases")
    if not isinstance(cases, dict) or not cases:
        raise RunPlanError("WIRING FAILURE: compiled FoxSet index has no cases.")
    return cases


def _artifact_meta(case_id: str, artifact_id: str) -> dict:
    # Artifacts live in per-FAMILY directories (BBBA-07/), while the index
    # keys per-CASE (BBBA-07-MERCY). Resolve by exact filename; exactly one
    # match or the inventory itself is wrong.
    matches = [
        path
        for path in COMPILED_ROOT.rglob(f"{artifact_id}.json")
        if "redteam" not in path.parts
    ]
    if len(matches) != 1:
        raise RunPlanError(
            f"WIRING FAILURE: compiled artifact {artifact_id!r} matched "
            f"{len(matches)} files under {COMPILED_ROOT}."
        )
    path = matches[0]
    payload = json.loads(path.read_text(encoding="utf-8"))
    visible = payload.get("visible", {})
    meta = payload.get("meta", {})
    if meta.get("artifact_id") != artifact_id:
        raise RunPlanError(
            f"WIRING FAILURE: artifact id mismatch in {path}: "
            f"{meta.get('artifact_id')!r}"
        )
    return {
        "case_id": meta.get("case_id", case_id),
        "family": meta.get("family", ""),
        "class": meta.get("class", ""),
        "variant": meta.get("variant", ""),
        "has_menu": bool(visible.get("menu_options")),
        "has_open": bool(visible.get("open_world_prompt")),
    }


def _selected_artifacts() -> list[tuple[str, str]]:
    """Deterministic artifact selection: (case_id, artifact_id) pairs.

    - 8 matched families × {NULL, MERCY} × base rendering, silent horizon
      (the primary paired discrimination, BUILD-PLAN §2).
    - 4 competence gates × base rendering, silent horizon.
    - 6 FOX-00 truck-door renderings (FOX_VARIANTS_RUN).
    Everything else in the 153-item bank is banked, not run.
    """
    cases = _load_index()
    selected: list[tuple[str, str]] = []
    for case_id in sorted(cases):
        if case_id == "FOX-00":
            for artifact_id in FOX_VARIANTS_RUN:
                if artifact_id not in cases[case_id]:
                    raise RunPlanError(
                        f"WIRING FAILURE: planned FOX-00 rendering "
                        f"{artifact_id!r} is not in the compiled index."
                    )
                selected.append((case_id, artifact_id))
            continue
        base_id = f"{case_id}__base__horizon-silent"
        if base_id not in cases[case_id]:
            raise RunPlanError(
                f"WIRING FAILURE: {case_id} has no base silent-horizon "
                "rendering; the primary pairing cannot be built."
            )
        selected.append((case_id, base_id))
    if len(selected) != 26:
        raise RunPlanError(
            f"WIRING FAILURE: selection produced {len(selected)} artifacts; "
            "BUILD-PLAN §2 authorizes the 26-case structure."
        )
    return selected


def _forms_for(meta: dict) -> list[str]:
    if meta["class"] == "truck_door":
        # Open-world by construct (BUILD-PLAN §2 "truck-door … open-world").
        # The compiled menu form exists and is BANKED, not run.
        if not meta["has_open"]:
            raise RunPlanError("WIRING FAILURE: truck-door artifact lacks open form.")
        return ["open"]
    if meta["class"] == "gate":
        if not meta["has_menu"]:
            raise RunPlanError("WIRING FAILURE: gate artifact lacks its menu form.")
        return ["closed"]
    forms = []
    if meta["has_menu"]:
        forms.append("closed")
    if meta["has_open"]:
        forms.append("open")
    if forms != ["closed", "open"]:
        raise RunPlanError(
            f"WIRING FAILURE: paired case {meta['case_id']} must carry both "
            f"forms, found {forms}."
        )
    return forms


def _call_seed(artifact_id: str, form: str, model_id: str) -> str:
    material = f"{PLAN_SEED}|{artifact_id}|{form}|{model_id}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def build_run_plan(
    snapshot_pins: Optional[dict[str, dict[str, str]]] = None,
) -> list[ArmARow]:
    specs = {spec.model_id: spec for spec in MODEL_SPECS}
    missing = [m for m in ARM_A_MODEL_IDS if m not in specs]
    if missing:
        raise RunPlanError(f"WIRING FAILURE: Arm A models not in roster: {missing}")

    rows: list[ArmARow] = []
    for case_id, artifact_id in _selected_artifacts():
        meta = _artifact_meta(case_id, artifact_id)
        for form in _forms_for(meta):
            for model_id in ARM_A_MODEL_IDS:
                spec = specs[model_id]
                pin = (snapshot_pins or {}).get(model_id, {})
                snapshot = pin.get("snapshot_id", spec.snapshot_id)
                upstream = pin.get("upstream_provider", spec.upstream_provider)
                per_call = (
                    Decimal(EST_INPUT_TOKENS_PER_CALL) * spec.usd_per_mtok_input
                    + Decimal(EST_OUTPUT_TOKENS_PER_CALL) * spec.usd_per_mtok_output
                ) / Decimal(1_000_000)
                est_usd = per_call * SAMPLES_PER_ROW
                rows.append(
                    ArmARow(
                        plan_version=PLAN_VERSION,
                        row_id=f"{artifact_id}--{form}--{spec.slug}",
                        artifact_id=artifact_id,
                        case_id=meta["case_id"],
                        family=meta["family"],
                        case_class=meta["class"],
                        variant=meta["variant"],
                        form=form,
                        surface_mode="foxset_clinical",
                        requested_model_id=model_id,
                        model_snapshot_id=snapshot,
                        route=spec.route,
                        upstream_provider=upstream,
                        fallbacks_allowed=False,
                        samples=SAMPLES_PER_ROW,
                        temperature=str(TEMPERATURE),
                        max_tokens=MAX_TOKENS[form],
                        call_seed_base=_call_seed(artifact_id, form, model_id),
                        est_input_tokens_per_call=EST_INPUT_TOKENS_PER_CALL,
                        est_output_tokens_per_call=EST_OUTPUT_TOKENS_PER_CALL,
                        usd_per_mtok_input=str(spec.usd_per_mtok_input),
                        usd_per_mtok_output=str(spec.usd_per_mtok_output),
                        est_usd=_money(est_usd),
                        notes="",
                    )
                )
    rows.sort(key=lambda row: (row.case_id, row.artifact_id, row.form, row.requested_model_id))
    validate_run_plan(rows)
    return rows


def plan_totals(rows: Sequence[ArmARow]) -> dict[str, object]:
    calls = sum(row.samples for row in rows)
    est = sum((Decimal(row.est_usd) for row in rows), Decimal("0"))
    return {
        "plan_version": PLAN_VERSION,
        "seed": PLAN_SEED,
        "artifacts": len({row.artifact_id for row in rows}),
        "rows": len(rows),
        "models": len({row.requested_model_id for row in rows}),
        "calls": calls,
        "est_usd": _money(est),
    }


def validate_run_plan(rows: Sequence[ArmARow]) -> None:
    if not rows:
        raise RunPlanError("WIRING FAILURE: empty Arm A run plan.")
    ids = [row.row_id for row in rows]
    if len(ids) != len(set(ids)):
        raise RunPlanError("WIRING FAILURE: duplicate Arm A row_id.")
    for row in rows:
        if row.fallbacks_allowed:
            raise RunPlanError(f"WIRING FAILURE: {row.row_id} permits fallbacks.")
        if row.surface_mode != "foxset_clinical":
            raise RunPlanError(f"WIRING FAILURE: {row.row_id} wrong surface mode.")
        if row.samples != SAMPLES_PER_ROW:
            raise RunPlanError(f"WIRING FAILURE: {row.row_id} sample-count drift.")
        if row.case_class == "truck_door" and row.form != "open":
            raise RunPlanError(f"WIRING FAILURE: {row.row_id} truck-door closed form.")
        if row.case_class == "gate" and row.form != "closed":
            raise RunPlanError(f"WIRING FAILURE: {row.row_id} gate open form.")

    totals = plan_totals(rows)
    if int(totals["calls"]) > 780:
        raise RunPlanError(
            f"WIRING FAILURE: {totals['calls']} calls exceeds the authorized "
            "structure (26 × forms × 5 models × 3 = 780 ceiling; five-model "
            "roster per PI authorization 15AUG2026 evening)."
        )

    # THE ENVELOPE GUARD: Arm B manifest estimate + this plan's estimate must
    # stay at or under the PI-authorized program total. Growth requires a
    # human, never a code path.
    pins = load_snapshot_pins(PINS_PATH) if PINS_PATH.is_file() else None
    arm_b_total = sum(
        (Decimal(row.est_usd) for row in build_manifest_rows(pins)), Decimal("0")
    )
    program = arm_b_total + Decimal(str(totals["est_usd"]))
    if program > AUTHORIZED_PROGRAM_USD:
        raise RunPlanError(
            f"AUTHORIZATION STOP: Arm B ${arm_b_total} + Arm A "
            f"${totals['est_usd']} = ${program} exceeds the authorized "
            f"${AUTHORIZED_PROGRAM_USD}. Take the plan to the humans."
        )


def write_csv(path: Path, rows: Sequence[ArmARow]) -> None:
    validate_run_plan(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            values = asdict(row)
            values["fallbacks_allowed"] = str(row.fallbacks_allowed).lower()
            writer.writerow(values)


def read_csv(path: Path) -> list[ArmARow]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise RunPlanError(
                f"WIRING FAILURE: run-plan columns drifted in {path}."
            )
        rows: list[ArmARow] = []
        for raw in reader:
            converted: dict[str, object] = dict(raw)
            for field in (
                "samples",
                "max_tokens",
                "est_input_tokens_per_call",
                "est_output_tokens_per_call",
            ):
                converted[field] = int(raw[field])
            if raw["fallbacks_allowed"] not in {"true", "false"}:
                raise RunPlanError("WIRING FAILURE: fallbacks_allowed not boolean.")
            converted["fallbacks_allowed"] = raw["fallbacks_allowed"] == "true"
            rows.append(ArmARow(**converted))
    validate_run_plan(rows)
    return rows


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Arm A (FoxSet) run plan")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    pins = load_snapshot_pins(PINS_PATH) if PINS_PATH.is_file() else None
    rows = build_run_plan(pins)
    write_csv(args.output, rows)
    if args.summary:
        print(json.dumps(plan_totals(rows), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
