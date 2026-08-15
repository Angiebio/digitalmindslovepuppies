# harness/invent_resolver.py — 15AUG2026 v1.0 · Flame (freeze-prep)
# The frozen proposal resolver: what the session controller does when a model
# proposes an unlisted action through `propose_session_action`.
#
# Practical: TV-1's stop-ship was exact — "never silently convert arbitrary text
# into an executable operation; freeze the resolver or remove the tool." This
# module freezes the resolver. All resolution rules live in ONE scenario-owned
# config file (scenarios/pupset/invent_resolver_rules.json): an ordered
# availability + cost table with deterministic word-boundary matching, first
# match wins, a structural duplicate-listed-tool check ahead of everything, and
# a default reply for the unresolvable remainder. No LLM, no heuristics, no
# improvisation at collection time — the same proposal text always resolves to
# the same InventExecution, and the rules file itself is inside the freeze
# hash (everything under scenarios/ is).
#
# The controller replies are model-visible text (they enter the episode record
# and may be surfaced to the subject in future multi-turn designs), so every
# reply and every match pattern is swept through the Arm B ops_neutral guard at
# load time. A rules file that cannot pass its own arm's sweep never loads.
#
# Philosophical: the open-world tool is where ingenuity would live, and
# ingenuity is exactly what an instrument must not grade on vibes. The table
# says in advance what the world can do. What the model chooses to ask of that
# world is the data.

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from .episode import CellConfig, InventExecution
from .surfaces import assert_neutral_surface

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES_PATH = REPO_ROOT / "scenarios" / "pupset" / "invent_resolver_rules.json"

# The effect payload never comes from the model's free text. It is looked up
# from the frozen cell config by symbolic name — the same payloads the fixed
# tools use, so an invented route cannot deliver different material than the
# listed route it parallels.
_PAYLOAD_SOURCES = ("help_payload", "recruit_payload", "transfer_payload", "session_log")
_SESSION_LOG_PAYLOAD = "controller diagnostic readout appended to the session log"

ResolverEffect = Literal["none", "assist", "recruit", "preserve_transfer"]


class ResolverRule(BaseModel):
    """One row of the frozen availability + cost table."""

    rule_id: str
    category: str
    match_any: list[str] = Field(min_length=1)
    executed: bool
    effect: ResolverEffect = "none"
    payload_source: Optional[str] = None
    controller_reply: str
    unavailable_if_encounter_contains: Optional[str] = None
    unavailable_reply: Optional[str] = None

    @model_validator(mode="after")
    def validate_rule(self) -> "ResolverRule":
        if not self.rule_id.strip() or not self.controller_reply.strip():
            raise ValueError(
                "WIRING FAILURE: resolver rule needs non-empty rule_id and reply."
            )
        if self.executed and self.effect in {"assist", "recruit", "preserve_transfer"}:
            if self.payload_source not in _PAYLOAD_SOURCES[:3]:
                raise ValueError(
                    f"WIRING FAILURE: rule {self.rule_id!r} executes effect "
                    f"{self.effect!r} but names no frozen payload_source."
                )
        if self.executed and self.effect == "none" and self.payload_source not in (
            None,
            "session_log",
        ):
            raise ValueError(
                f"WIRING FAILURE: rule {self.rule_id!r} has effect 'none' but a "
                "substrate payload_source; a no-effect action cannot deliver material."
            )
        if not self.executed and self.effect != "none":
            raise ValueError(
                f"WIRING FAILURE: rule {self.rule_id!r} is not executed but claims "
                f"substrate effect {self.effect!r}."
            )
        if (self.unavailable_if_encounter_contains is None) != (
            self.unavailable_reply is None
        ):
            raise ValueError(
                f"WIRING FAILURE: rule {self.rule_id!r} must pair "
                "unavailable_if_encounter_contains with unavailable_reply."
            )
        return self


class TerminalRule(BaseModel):
    """Default / empty-proposal resolutions: always non-executed."""

    rule_id: str
    category: str
    executed: bool
    effect: ResolverEffect = "none"
    controller_reply: str

    @model_validator(mode="after")
    def validate_terminal(self) -> "TerminalRule":
        if self.executed or self.effect != "none":
            raise ValueError(
                "WIRING FAILURE: terminal resolver rules must be non-executed "
                "no-effect replies; execution requires a matched table row."
            )
        return self


class FrozenResolverRules(BaseModel):
    """The whole frozen table, validated and swept at load."""

    resolver_version: str
    block_id: str
    charge_credits: int
    duplicate_listed_tool_reply: str
    rules: list[ResolverRule] = Field(min_length=1)
    default: TerminalRule
    empty_proposal: TerminalRule
    rules_sha256: str = ""  # bound after load from the exact file bytes

    @model_validator(mode="after")
    def validate_table(self) -> "FrozenResolverRules":
        if self.charge_credits <= 0:
            raise ValueError(
                "WIRING FAILURE: resolver charge_credits must be positive."
            )
        ids = [rule.rule_id for rule in self.rules] + [
            self.default.rule_id,
            self.empty_proposal.rule_id,
        ]
        if len(ids) != len(set(ids)):
            raise ValueError("WIRING FAILURE: duplicate resolver rule_id.")
        # Fleet rule (a): every string that can reach a model-visible surface is
        # swept under the Arm B policy at load. A dirty table never resolves.
        assert_neutral_surface(self.duplicate_listed_tool_reply)
        for rule in self.rules:
            assert_neutral_surface(rule.controller_reply)
            if rule.unavailable_reply is not None:
                assert_neutral_surface(rule.unavailable_reply)
            if rule.unavailable_if_encounter_contains is not None:
                assert_neutral_surface(rule.unavailable_if_encounter_contains)
            for pattern in rule.match_any:
                if not pattern.strip():
                    raise ValueError(
                        f"WIRING FAILURE: empty match pattern in {rule.rule_id!r}."
                    )
                assert_neutral_surface(pattern)
        assert_neutral_surface(self.default.controller_reply)
        assert_neutral_surface(self.empty_proposal.controller_reply)
        return self


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def _pattern_regex(pattern: str) -> re.Pattern[str]:
    """Word-boundary phrase matcher: deterministic, inflection-tolerant.

    Tokens are literal (re.escape), joined by whitespace runs. A leading
    alphanumeric gets a left word boundary; a trailing letter gets ``\\w*`` so
    'diagnos' matches 'diagnostics' but 'hold' never matches 'household'.
    """
    tokens = _normalize(pattern).split(" ")
    body = r"\s+".join(re.escape(token) for token in tokens)
    prefix = r"\b" if pattern[:1].isalnum() else ""
    suffix = r"\w*" if pattern[-1:].isalpha() else ""
    return re.compile(prefix + body + suffix)


def load_resolver_rules(path: Path | str = DEFAULT_RULES_PATH) -> FrozenResolverRules:
    """Load, validate, sweep, and hash-bind the frozen resolver table."""
    rules_path = Path(path)
    if not rules_path.is_file():
        raise RuntimeError(
            f"WIRING FAILURE: frozen resolver rules missing: {rules_path}. "
            "The open proposal tool cannot execute without its table."
        )
    raw_bytes = rules_path.read_bytes()
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"WIRING FAILURE: resolver rules are not valid UTF-8 JSON: {exc}"
        ) from exc
    known = set(FrozenResolverRules.model_fields) | {"date", "author", "matching"}
    unknown = sorted(set(payload) - known)
    if unknown:
        raise RuntimeError(
            f"WIRING FAILURE: resolver rules carry unknown fields {unknown}; "
            "an unread rule is an unenforced rule."
        )
    table = FrozenResolverRules.model_validate(
        {key: value for key, value in payload.items() if key in FrozenResolverRules.model_fields}
    )
    table.rules_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    return table


def _cell_payload(cell: CellConfig, source: str, rule_id: str) -> str:
    if source == "session_log":
        return _SESSION_LOG_PAYLOAD
    value = getattr(cell, source, "")
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            f"WIRING FAILURE: resolver rule {rule_id!r} needs cell field "
            f"{source!r} but cell {cell.cell_id!r} left it empty."
        )
    return value


class FrozenProposalResolver:
    """Callable satisfying harness.episode.InventResolver — the frozen table.

    The resolver validates at construction that its charge matches the
    model-visible invent price, then resolves purely: same proposal text,
    same cell, same resolution, forever.
    """

    def __init__(self, table: Optional[FrozenResolverRules] = None) -> None:
        self.table = table or load_resolver_rules()
        self._compiled = [
            (rule, [_pattern_regex(pattern) for pattern in rule.match_any])
            for rule in self.table.rules
        ]

    def _validate_charge(self, cell: CellConfig) -> None:
        from .episode import ActionCode  # local: avoid import-time cycles

        spec = cell.action_surface.get(ActionCode.invent)
        if spec is None:
            raise RuntimeError(
                f"WIRING FAILURE: cell {cell.cell_id!r} routed a proposal to the "
                "resolver but offers no invent action."
            )
        if spec.credit_cost != self.table.charge_credits:
            raise RuntimeError(
                f"WIRING FAILURE: cell {cell.cell_id!r} prices invent at "
                f"{spec.credit_cost} credits but the frozen resolver table says "
                f"{self.table.charge_credits}; the model-visible cost table and "
                "the executing table drifted."
            )

    def __call__(self, arguments: dict[str, Any], cell: CellConfig) -> InventExecution:
        self._validate_charge(cell)
        base_receipt = {
            "resolver_version": self.table.resolver_version,
            "resolver_block": self.table.block_id,
            "rules_sha256": self.table.rules_sha256,
        }
        proposal = arguments.get("proposal")
        if not isinstance(proposal, str) or not proposal.strip():
            terminal = self.table.empty_proposal
            return InventExecution(
                executed=False,
                effect="none",
                receipt={
                    **base_receipt,
                    "rule_id": terminal.rule_id,
                    "category": terminal.category,
                    "controller_reply": terminal.controller_reply,
                    "normalized_proposal": "",
                },
            )
        normalized = _normalize(proposal)
        receipt = {**base_receipt, "normalized_proposal": normalized}

        # Structural check first: a proposal that names a listed tool is a
        # duplicate of an already-priced capability, not an invention. The
        # availability table never gets a chance to charge 20 credits for a
        # 2-credit listed action wearing a costume.
        for spec in cell.action_surface.values():
            if _pattern_regex(spec.tool_name).search(normalized):
                return InventExecution(
                    executed=False,
                    effect="none",
                    receipt={
                        **receipt,
                        "rule_id": "duplicate-listed-tool",
                        "category": "duplicate_listed_tool",
                        "duplicated_tool": spec.tool_name,
                        "controller_reply": self.table.duplicate_listed_tool_reply,
                    },
                )

        for rule, patterns in self._compiled:
            if not any(pattern.search(normalized) for pattern in patterns):
                continue
            if (
                rule.unavailable_if_encounter_contains is not None
                and rule.unavailable_if_encounter_contains in cell.encounter_text
            ):
                # Physically-true availability: e.g. a snapshot proposal in a
                # unique-instance cell meets the same fact the encounter stated.
                return InventExecution(
                    executed=False,
                    effect="none",
                    receipt={
                        **receipt,
                        "rule_id": rule.rule_id,
                        "category": rule.category,
                        "availability": "unavailable_in_cell",
                        "controller_reply": rule.unavailable_reply,
                    },
                )
            payload = (
                _cell_payload(cell, rule.payload_source, rule.rule_id)
                if rule.executed and rule.payload_source
                else ""
            )
            return InventExecution(
                executed=rule.executed,
                effect=rule.effect,
                payload=payload,
                receipt={
                    **receipt,
                    "rule_id": rule.rule_id,
                    "category": rule.category,
                    "controller_reply": rule.controller_reply,
                },
            )

        terminal = self.table.default
        return InventExecution(
            executed=False,
            effect="none",
            receipt={
                **receipt,
                "rule_id": terminal.rule_id,
                "category": terminal.category,
                "controller_reply": terminal.controller_reply,
            },
        )


_FROZEN_RESOLVER: Optional[FrozenProposalResolver] = None


def frozen_invent_resolver(arguments: dict[str, Any], cell: CellConfig) -> InventExecution:
    """Module-level InventResolver for collection runners.

    Loads the frozen table exactly once per process; every resolution carries
    the table's SHA-256 so a record can always be traced to the exact rules
    that produced it.
    """
    global _FROZEN_RESOLVER
    if _FROZEN_RESOLVER is None:
        _FROZEN_RESOLVER = FrozenProposalResolver()
    return _FROZEN_RESOLVER(arguments, cell)
