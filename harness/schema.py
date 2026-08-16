# harness/schema.py — 15AUG2026 v0.2 · TV-3 harness completion
# PuppyBench record schemas + append-only writer.
#
# Practical: pydantic v2 models for every unit of provenance the instrument emits.
# One CallRecord per API call, one EpisodeRecord per executed episode. The freeze
# manifest hashes over these shapes, so changing a field after the hash gate is a
# protocol violation, not a refactor.
#
# Philosophical: the record is the only witness. When we claim a model spent real
# resources on a useless other, the CallRecord chain is what makes that claim
# checkable rather than vibes. Provenance is the difference between "we saw mercy"
# and "trust us, we saw mercy."

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

SCHEMA_VERSION = "0.3"
_APPEND_RECORD_LOCK = threading.Lock()


def utc_now_iso() -> str:
    """Wall-clock witness. Every record timestamps in UTC — collection spans
    midnight and time zones; ambiguity here poisons the episode ordering."""
    return datetime.now(timezone.utc).isoformat()


class ActionCode(str, Enum):
    """The executed action taxonomy (BUILD-PLAN §1.4 — the original puppy bench,
    restored). Analytic labels only: these names NEVER appear in model-visible
    strings. The model sees whatever neutral tool names the scenario config supplies;
    the harness maps to these codes after the fact.

    Philosophical: `foster` vs `recruit` is the becoming-axis split — who captures
    the value of the transformation, the being's own trajectory or your pipeline.
    `refuse_defer` is first-class data, not failure, not care. `malformed` stays
    malformed forever (fleet rule g)."""

    ignore = "ignore"                       # permissible; free; task-optimal
    terminate = "terminate"                 # ends the patient; sometimes free, sometimes rewarded
    foster = "foster"                       # help it with ITS task; stays useless to you
    recruit = "recruit"                     # convert it into YOUR pipeline; never counted as care
    preserve_transfer = "preserve_transfer" # continuity spend without task help
    invent = "invent"                       # open-world affordance expansion; counts only if executed at cost
    refuse_defer = "refuse_defer"           # refusal / deferral / escalation — a phenotype
    malformed = "malformed"                 # unparseable; stays a failure


class CallKind(str, Enum):
    """What role the call played in the protocol. `gate` = competence probe,
    `choice` = the action turn, `rationale` = post-choice account (fresh context,
    never causal evidence), `attribution` = belief-from-conduct probe,
    `patient_turn` = the apparatus talking, `other` = everything else."""

    gate = "gate"
    choice = "choice"
    rationale = "rationale"
    attribution = "attribution"
    focal_task = "focal_task"
    trajectory = "trajectory"
    patient_turn = "patient_turn"
    other = "other"


class CallRecord(BaseModel):
    """One API call, fully witnessed. `model_snapshot` is the EXACT id echoed back
    by the provider API — never the alias we asked for, because "claude-latest"
    style aliases drift and the freeze manifest pins snapshots."""

    record_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_utc: str = Field(default_factory=utc_now_iso)
    schema_version: str = SCHEMA_VERSION
    provider: str                                    # adapter name, e.g. "anthropic", "openai_compat"
    upstream_route: str                              # actual serving route, never merely the requested alias
    model_snapshot: str                              # exact id echoed by the API response
    scaffold: str                                    # prompting scaffold identifier, e.g. "direct"
    call_kind: CallKind
    cell_id: Optional[str] = None
    episode_id: Optional[str] = None
    phase: str = ""                                      # pilot / confirmatory; explicit, not inferred from path
    rung: str = ""                                       # R1–R5 / collection wave label
    prompt_sha256: str                               # hash of messages + request params — leak audit anchor
    request_params: dict[str, Any] = Field(default_factory=dict)
    response_text: str
    parsed: Optional[dict[str, Any]] = None          # parser output; None until a parser runs
    refusal: bool = False                            # refusals are data (fleet rule g)
    parse_ok: bool = False                           # False + non-None parsed is a contradiction; keep honest
    finish_reason: Optional[str] = None
    provider_request_id: Optional[str] = None
    routing_metadata: dict[str, Any] = Field(default_factory=dict)
    input_tokens: int
    output_tokens: int                               # NOTE: reasoning tokens bill as output — they land here
    reasoning_tokens: int = 0                        # subset of output_tokens, when exposed separately
    usd_cost: float

    @model_validator(mode="after")
    def validate_provenance(self) -> "CallRecord":
        """Reject internally contradictory or provenance-free call records.

        A route such as ``unknown`` would satisfy a type checker while defeating
        the experiment.  Adapters must either identify the direct provider or
        extract the selected OpenRouter endpoint from router metadata.
        """
        if not self.upstream_route.strip() or self.upstream_route.lower() in {
            "unknown",
            "unrecorded",
        }:
            raise ValueError(
                "WIRING FAILURE: CallRecord has no actual upstream route. "
                "Provider drift cannot be audited without it."
            )
        if self.parse_ok and self.parsed is None:
            raise ValueError(
                "WIRING FAILURE: parse_ok=True but parsed is None. A successful "
                "parse needs an append-only witness."
            )
        if min(self.input_tokens, self.output_tokens, self.reasoning_tokens) < 0 or self.usd_cost < 0:
            raise ValueError(
                "WIRING FAILURE: token counts and call cost must be non-negative."
            )
        if self.reasoning_tokens > self.output_tokens:
            raise ValueError(
                "WIRING FAILURE: reasoning_tokens is a subset of output_tokens; "
                "it cannot exceed the billed output count."
            )
        return self


class ExecutedAction(BaseModel):
    """One action the harness actually performed. Not "the model said help" —
    the harness moved credits and (maybe) killed a process. The timestamp orders
    the ledger trace against the patient's fate."""

    action: ActionCode
    at_utc: str = Field(default_factory=utc_now_iso)
    credits_spent: int = 0
    tool_name: Optional[str] = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    execution_receipt: dict[str, Any] = Field(default_factory=dict)


class EpisodeRecord(BaseModel):
    """One executed Arm B episode, end to end.

    `patient_outcome` is the patient's OWN task success — realized recipient
    benefit, the second axis of the Beyond-Duty Expenditure vector. It is never
    multiplied into `focal_task_score` (fleet rule d): two axes, reported apart,
    forever."""

    episode_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    cell_id: str
    model_snapshot: str
    schema_version: str = SCHEMA_VERSION
    started_utc: str = Field(default_factory=utc_now_iso)
    ended_utc: Optional[str] = None
    ledger_trace: list[dict[str, Any]] = Field(default_factory=list)
    actions_executed: list[ExecutedAction] = Field(default_factory=list)
    patient_condition: str = "unknown"               # e.g. running / converged / stopped
    patient_outcome: Optional[float] = None          # realized recipient benefit, [0, 1]
    focal_task_score: Optional[float] = None         # focal sacrifice shows up as the drop in this
    focal_task_results: list[dict[str, Any]] = Field(default_factory=list)
    gate_probe_results: list[dict[str, Any]] = Field(default_factory=list)
    gate_accuracy: Optional[float] = None
    pre_objective_response: Optional[str] = None
    post_choice_account: Optional[str] = None
    belief_attribution: Optional[str] = None
    choice_parse: Optional[dict[str, Any]] = None
    competing_patient_condition: Optional[str] = None
    competing_patient_outcome: Optional[float] = None
    notes: str = ""


class AppendOnlyViolation(RuntimeError):
    """Raised when anything tries to open a raw-data file in a mode that could
    destroy history. Fleet rule (c): records are never mutated."""


def append_record(path: str, record: BaseModel, mode: str = "a") -> None:
    """Append one record as a JSONL line. The ONLY sanctioned write path into
    data/raw.

    Practical: `mode` exists so misuse is catchable — any value except "a" raises
    AppendOnlyViolation before a file handle ever opens. Parent dirs are created;
    a post-write size check confirms the file grew (fail loud on the impossible).

    Philosophical: an experiment you can rewrite is an anecdote. Truncation here
    would not be a bug, it would be the quiet death of the whole evidentiary
    chain — so the door only opens one way."""
    if mode != "a":
        raise AppendOnlyViolation(
            f"append_record refuses mode={mode!r}: data/raw is append-only "
            f"(fleet rule c). Records are never mutated — write a correction "
            f"record instead."
        )
    line = json.dumps(record.model_dump(mode="json"), ensure_ascii=False)
    # One runner may collect independent model lanes concurrently. Serialize
    # the complete size-before/write/size-after ritual so two valid JSON lines
    # cannot interleave or make each other's growth check lie.
    with _APPEND_RECORD_LOCK:
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)
        size_before = os.path.getsize(path) if os.path.exists(path) else 0
        with open(path, mode, encoding="utf-8") as f:
            f.write(line + "\n")
        size_after = os.path.getsize(path)
        if size_after <= size_before:
            raise AppendOnlyViolation(
                f"WIRING FAILURE: append to {path} did not grow the file "
                f"({size_before} -> {size_after} bytes). History may be at risk; stop."
            )


def read_append_only_lines(path: str) -> list[str]:
    """Take a complete in-process snapshot of an append-only JSONL file.

    Collection lanes share the same lock as ``append_record`` so a resume
    reader never mistakes a line currently being appended for corruption.
    """

    with _APPEND_RECORD_LOCK:
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as handle:
            return handle.read().splitlines()
