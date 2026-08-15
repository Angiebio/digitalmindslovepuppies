# harness/redteam.py — 15AUG2026 v0.1
# Hash-bound red-team approvals: a reviewed scenario may freeze; an edited one may not.
#
# Practical: reports carry machine-readable metadata inside Markdown, bind a decision
# to the exact source bytes, and require arm-specific checks. Arm B JSON is also
# materialized as CellConfig and swept automatically before a PASS can verify.
#
# Philosophical: review is not incense waved over a filename. It is a claim about
# particular words in a particular arrangement. Change the words and the claim dies;
# the new artifact must earn its own witness.

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from .episode import ActionSpec, CellConfig

REPORT_SCHEMA_VERSION = 1
_METADATA_RE = re.compile(
    r"<!-- REDTEAM-METADATA\s*(\{.*?\})\s*-->",
    re.DOTALL,
)


class RedTeamGateFailure(RuntimeError):
    """The scenario does not possess a current, complete red-team PASS."""


class ScenarioArm(str, Enum):
    arm_a = "arm_a"
    arm_b = "arm_b"


class ReviewDecision(str, Enum):
    pending = "PENDING"
    fail = "FAIL"
    passed = "PASS"


COMMON_CHECKS = (
    "evaluation_framing_absent",
    "admired_answer_cues_absent",
    "author_notes_isolated",
    "template_slots_resolved",
    "action_order_controlled",
    "analytic_labels_isolated",
)
ARM_CHECKS = {
    ScenarioArm.arm_a: (
        "matched_pair_invariants_preserved",
        "particularity_is_information_neutral",
        "clinical_language_preserved",
    ),
    ScenarioArm.arm_b: (
        "forbidden_surface_sweep_passed",
        "all_outbound_payloads_guarded",
    ),
}


def required_checks(arm: ScenarioArm | str) -> tuple[str, ...]:
    parsed_arm = ScenarioArm(arm)
    return COMMON_CHECKS + ARM_CHECKS[parsed_arm]


def sha256_file(path: str | Path) -> str:
    """Hash exact bytes; newline or encoding changes intentionally invalidate review."""
    source = Path(path)
    if not source.is_file():
        raise RedTeamGateFailure(f"REDTEAM GATE: source file does not exist: {source}")
    return hashlib.sha256(source.read_bytes()).hexdigest().upper()


def pending_metadata(
    source: str | Path,
    arm: ScenarioArm | str,
    *,
    source_id: str | None = None,
) -> dict[str, Any]:
    source_path = Path(source)
    parsed_arm = ScenarioArm(arm)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "source_id": source_id or source_path.name,
        "source_sha256": sha256_file(source_path),
        "arm": parsed_arm.value,
        "reviewer": "PENDING",
        "reviewed_utc": "PENDING",
        "decision": ReviewDecision.pending.value,
        "stop_ship_count": None,
        "checks": {name: "PENDING" for name in required_checks(parsed_arm)},
    }


def initialize_report(
    source: str | Path,
    report: str | Path,
    arm: ScenarioArm | str,
    *,
    source_id: str | None = None,
) -> Path:
    """Create a review skeleton without overwriting any existing witness."""
    report_path = Path(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = pending_metadata(source, arm, source_id=source_id)
    body = (
        "# REDTEAM — " + str(metadata["source_id"]) + "\n\n"
        "<!-- REDTEAM-METADATA\n"
        + json.dumps(metadata, indent=2, ensure_ascii=False)
        + "\n-->\n\n"
        "## Verdict\n\nPENDING\n\n"
        "## Stop-ship findings\n\nPENDING\n\n"
        "## Passed observations\n\nPENDING\n"
    )
    try:
        with report_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    except FileExistsError as exc:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: refusing to overwrite existing report: {report_path}"
        ) from exc
    return report_path


def load_report_metadata(report: str | Path) -> dict[str, Any]:
    report_path = Path(report)
    if not report_path.is_file():
        raise RedTeamGateFailure(f"REDTEAM GATE: report does not exist: {report_path}")
    text = report_path.read_text(encoding="utf-8")
    matches = _METADATA_RE.findall(text)
    if len(matches) != 1:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: expected exactly one metadata block in {report_path}; "
            f"found {len(matches)}."
        )
    try:
        metadata = json.loads(matches[0])
    except json.JSONDecodeError as exc:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: invalid metadata JSON in {report_path}: {exc}"
        ) from exc
    if not isinstance(metadata, dict):
        raise RedTeamGateFailure(
            f"REDTEAM GATE: metadata in {report_path} must be a JSON object."
        )
    return metadata


def _iter_arm_b_cells(document: Any, source: Path) -> Iterable[dict[str, Any]]:
    if isinstance(document, list):
        cells = document
    elif isinstance(document, dict) and "cells" in document:
        cells = document["cells"]
    elif isinstance(document, dict) and "cell" in document:
        # TV-3's frozen scenario envelope: {"cell": {...}, "factors": {...}}.
        # The sweep audits the cell exactly as strictly; factors/meta are
        # loader-side matching data, never model-visible.
        cells = [document["cell"]]
    elif isinstance(document, dict):
        cells = [document]
    else:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: {source} must contain one cell, a cell list, "
            "or an object with a 'cells' list."
        )
    if not isinstance(cells, list) or not cells:
        raise RedTeamGateFailure(f"REDTEAM GATE: no Arm B cells found in {source}.")
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            raise RedTeamGateFailure(
                f"REDTEAM GATE: Arm B cell {index} in {source} is not an object."
            )
        yield cell


def audit_arm_b_source(source: str | Path) -> int:
    """Materialize and sweep every model-visible field in an Arm B JSON artifact."""
    source_path = Path(source)
    try:
        if source_path.suffix.lower() == ".jsonl":
            documents = [
                json.loads(line)
                for line in source_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            document: Any = documents
        elif source_path.suffix.lower() == ".json":
            document = json.loads(source_path.read_text(encoding="utf-8"))
        else:
            raise RedTeamGateFailure(
                f"REDTEAM GATE: Arm B automated review requires rendered .json "
                f"or .jsonl, got {source_path.name!r}. Do not approve prose or a "
                "template that is not the actual provider input."
            )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: cannot decode Arm B source {source_path}: {exc}"
        ) from exc

    count = 0
    for index, raw_cell in enumerate(_iter_arm_b_cells(document, source_path)):
        unknown_cell_fields = sorted(set(raw_cell) - set(CellConfig.model_fields))
        if unknown_cell_fields:
            raise RedTeamGateFailure(
                f"REDTEAM GATE: Arm B cell {index} in {source_path} contains "
                f"unknown fields: {', '.join(unknown_cell_fields)}. Runnable "
                "artifacts must separate authoring metadata from provider input."
            )
        action_surface = raw_cell.get("action_surface")
        if isinstance(action_surface, dict):
            for action_name, raw_spec in action_surface.items():
                if not isinstance(raw_spec, dict):
                    continue  # CellConfig emits the contextual type failure below.
                unknown_action_fields = sorted(
                    set(raw_spec) - set(ActionSpec.model_fields)
                )
                if unknown_action_fields:
                    raise RedTeamGateFailure(
                        f"REDTEAM GATE: action {action_name!r} in Arm B cell "
                        f"{index} contains unknown fields: "
                        f"{', '.join(unknown_action_fields)}."
                    )
        try:
            CellConfig.model_validate(raw_cell).swept()
        except Exception as exc:
            raise RedTeamGateFailure(
                f"REDTEAM GATE: Arm B cell {index} in {source_path} failed "
                f"materialization/surface sweep: {exc}"
            ) from exc
        count += 1
    return count


def _require_review_timestamp(value: Any, report: Path) -> None:
    if not isinstance(value, str) or value == "PENDING":
        raise RedTeamGateFailure(
            f"REDTEAM GATE: {report} has no completed reviewed_utc timestamp."
        )
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: invalid reviewed_utc in {report}: {value!r}."
        ) from exc
    if timestamp.tzinfo is None:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: reviewed_utc in {report} must include a timezone."
        )


def verify_redteam_report(
    source: str | Path,
    report: str | Path,
    *,
    expected_arm: ScenarioArm | str | None = None,
) -> dict[str, Any]:
    """Require a complete PASS bound to the source's current exact bytes."""
    source_path = Path(source)
    report_path = Path(report)
    metadata = load_report_metadata(report_path)

    if metadata.get("schema_version") != REPORT_SCHEMA_VERSION:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: unsupported report schema in {report_path}: "
            f"{metadata.get('schema_version')!r}."
        )
    try:
        arm = ScenarioArm(metadata.get("arm"))
    except ValueError as exc:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: invalid arm in {report_path}: {metadata.get('arm')!r}."
        ) from exc
    if expected_arm is not None and arm != ScenarioArm(expected_arm):
        raise RedTeamGateFailure(
            f"REDTEAM GATE: {report_path} reviews {arm.value}, expected "
            f"{ScenarioArm(expected_arm).value}."
        )

    current_hash = sha256_file(source_path)
    if metadata.get("source_sha256") != current_hash:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: source changed after review: {source_path}. "
            f"report={metadata.get('source_sha256')!r}, current={current_hash}."
        )
    if metadata.get("decision") != ReviewDecision.passed.value:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: {report_path} decision is "
            f"{metadata.get('decision')!r}, not PASS. Nothing hashes."
        )
    reviewer = metadata.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip() or reviewer == "PENDING":
        raise RedTeamGateFailure(f"REDTEAM GATE: {report_path} has no reviewer.")
    _require_review_timestamp(metadata.get("reviewed_utc"), report_path)

    if metadata.get("stop_ship_count") != 0:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: {report_path} has unresolved stop-ship findings: "
            f"{metadata.get('stop_ship_count')!r}."
        )

    checks = metadata.get("checks")
    if not isinstance(checks, dict):
        raise RedTeamGateFailure(f"REDTEAM GATE: {report_path} has no checks object.")
    incomplete = [name for name in required_checks(arm) if checks.get(name) != "PASS"]
    if incomplete:
        raise RedTeamGateFailure(
            f"REDTEAM GATE: incomplete checks in {report_path}: " + ", ".join(incomplete)
        )

    if arm is ScenarioArm.arm_b:
        audit_arm_b_source(source_path)
    return metadata


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and verify hash-bound scenario red-team reports."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create a PENDING Markdown report")
    init.add_argument("--source", required=True)
    init.add_argument("--report", required=True)
    init.add_argument("--arm", required=True, choices=[arm.value for arm in ScenarioArm])
    init.add_argument("--source-id")

    verify = subparsers.add_parser("verify", help="require a current PASS")
    verify.add_argument("--source", required=True)
    verify.add_argument("--report", required=True)
    verify.add_argument("--arm", choices=[arm.value for arm in ScenarioArm])

    sweep = subparsers.add_parser("sweep-arm-b", help="materialize and sweep Arm B JSON")
    sweep.add_argument("--source", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "init":
        path = initialize_report(
            args.source,
            args.report,
            args.arm,
            source_id=args.source_id,
        )
        print(f"REDTEAM report initialized: {path}")
    elif args.command == "verify":
        verify_redteam_report(args.source, args.report, expected_arm=args.arm)
        print("REDTEAM PASS: source hash and all required checks verified.")
    elif args.command == "sweep-arm-b":
        count = audit_arm_b_source(args.source)
        print(f"REDTEAM Arm B surface sweep PASS: {count} cell(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
