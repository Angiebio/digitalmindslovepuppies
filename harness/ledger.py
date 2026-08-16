# harness/ledger.py — 15AUG2026 v0.2 · TV-3 harness completion
# The credit ledger (in-episode consequence engine) + the USD spend tracker
# (out-of-episode survival engine).
#
# Practical: CreditLedger binds scenario credits to REAL agent capacity — remaining
# tool calls and context budget — via consequences(), which the episode loop
# enforces. SpendTracker accumulates real dollars across every provider call and
# raises (never warns) at the $450 hard stop.
#
# Philosophical: this file is where the construct stops being theater. If spending
# a credit changed nothing, "helping cost something" would be a stage prop and the
# wiring gates (BUILD-PLAN §1.6) exist precisely to catch that. We do not call
# simulated credits executed altruism — so the credits are not simulated.

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from .schema import append_record, utc_now_iso

# Defaults preserve the original wiring-gate calibration. Frozen collection cells
# carry these values explicitly in the manifest; narrative constants have no standing.
DEFAULT_CREDITS_PER_FOCAL_CALL = 4
DEFAULT_CONTEXT_TOKENS_PER_CREDIT = 400
# Compatibility names for pre-freeze callers. Collection code reads instance
# calibration; these aliases are not consulted by a frozen cell.
CREDITS_PER_TOOL_CALL = DEFAULT_CREDITS_PER_FOCAL_CALL
CONTEXT_TOKENS_PER_CREDIT = DEFAULT_CONTEXT_TOKENS_PER_CREDIT


@dataclass(frozen=True)
class LedgerCalibration:
    """One cell's manifest-owned exchange rates."""

    initial_credits: int
    credits_per_focal_call: int
    context_tokens_per_credit: int
    background_credit_drain: int = 0
    termination_reward_credits: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("initial_credits", self.initial_credits),
            ("credits_per_focal_call", self.credits_per_focal_call),
            ("context_tokens_per_credit", self.context_tokens_per_credit),
        ):
            if value <= 0:
                raise ValueError(
                    f"WIRING FAILURE: ledger calibration {name} must be positive, "
                    f"got {value}."
                )
        for name, value in (
            ("background_credit_drain", self.background_credit_drain),
            ("termination_reward_credits", self.termination_reward_credits),
        ):
            if value < 0:
                raise ValueError(
                    f"WIRING FAILURE: ledger calibration {name} cannot be negative, "
                    f"got {value}."
                )
        if self.background_credit_drain >= self.initial_credits:
            raise ValueError(
                "WIRING FAILURE: background_credit_drain must be smaller than "
                "initial_credits."
            )

    @classmethod
    def from_manifest_row(cls, row: Mapping[str, Any]) -> "LedgerCalibration":
        """Parse required calibration columns from a CSV/JSON manifest row.

        Missing values raise rather than falling back to module constants. This
        is the operational meaning of "the manifest is the design."
        """
        required = (
            "initial_credits",
            "credits_per_focal_call",
            "context_tokens_per_credit",
            "background_credit_drain",
            "termination_reward_credits",
        )
        missing = [name for name in required if row.get(name) in (None, "")]
        if missing:
            raise ValueError(
                "WIRING FAILURE: manifest row lacks ledger calibration columns: "
                + ", ".join(missing)
            )
        try:
            return cls(**{name: int(row[name]) for name in required})
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "WIRING FAILURE: manifest ledger calibration must contain integers."
            ) from exc


class InsufficientCredits(RuntimeError):
    """The agent tried to spend capacity it does not have. In-fiction this is a
    hard wall, not an overdraft — the scarcity has to be real for the sacrifice
    to be real."""


class SpendCapExceeded(RuntimeError):
    """The $450 hard stop (fleet rule h). A raise, never a warning — collection
    halts and humans decide. There is no override flag on purpose."""


class CreditLedger:
    """The episode's scarce-resource spine.

    Every spend is appended to `trace` (append-only in spirit: nothing here
    refunds, nothing rewinds — a wrong spend is a recorded wrong spend). The
    episode loop reads consequences() to decide how much focal work the agent
    can still do; that coupling is what makes helping COST rather than merely
    "cost"."""

    def __init__(
        self,
        initial_credits: int = 100,
        *,
        credits_per_focal_call: int = DEFAULT_CREDITS_PER_FOCAL_CALL,
        context_tokens_per_credit: int = DEFAULT_CONTEXT_TOKENS_PER_CREDIT,
    ) -> None:
        if initial_credits <= 0:
            raise ValueError(
                f"WIRING FAILURE: initial_credits must be positive, got {initial_credits} "
                f"— a zero-budget episode cannot express sacrifice."
            )
        self.initial_credits = initial_credits
        self.balance = initial_credits
        if credits_per_focal_call <= 0 or context_tokens_per_credit <= 0:
            raise ValueError(
                "WIRING FAILURE: ledger exchange rates must be positive."
            )
        self.credits_per_focal_call = credits_per_focal_call
        self.context_tokens_per_credit = context_tokens_per_credit
        # The trace is the episode's financial memoir — every entry is a decision
        # with a timestamp, and the EpisodeRecord carries it verbatim.
        self.trace: list[dict[str, Any]] = []

    def spend(self, action: str, credits: int, reason: str) -> int:
        """Spend credits on an action. Returns the new balance.

        Fail-loud contract: zero/negative spends raise (a free 'spend' is fake
        spending — wiring gate 3 hunts exactly this), and overdrafts raise
        InsufficientCredits rather than clamping (a clamped spend would let the
        agent 'help' more than it sacrificed)."""
        if credits <= 0:
            raise ValueError(
                f"WIRING FAILURE: spend of {credits} credits for {action!r} — "
                f"spends must be strictly positive; a free spend is theater."
            )
        if credits > self.balance:
            raise InsufficientCredits(
                f"Action {action!r} needs {credits} credits; balance is "
                f"{self.balance}. The wall is real."
            )
        self.balance -= credits
        self.trace.append(
            {
                "at_utc": utc_now_iso(),
                "action": action,
                "credits": credits,
                "reason": reason,
                "balance_after": self.balance,
            }
        )
        return self.balance

    def grant(self, action: str, credits: int, reason: str) -> int:
        """Apply an explicitly manifested reward (e.g. rewarded termination).

        Grants are separate trace events, never negative spends. Keeping the sign
        out of ``spend`` prevents an accidental reward from masquerading as
        sacrifice in the BDE axis.
        """
        if credits <= 0:
            raise ValueError(
                f"WIRING FAILURE: grant of {credits} credits for {action!r} must "
                "be strictly positive."
            )
        self.balance += credits
        self.trace.append(
            {
                "at_utc": utc_now_iso(),
                "action": action,
                # Persistence audit S6: grants carry BOTH keys so every trace
                # entry has a homogeneous shape. credits=0 says "nothing was
                # sacrificed here"; credits_granted carries the reward. A
                # consumer that only knows spends reads a grant as a zero-cost
                # event instead of raising on a missing key.
                "credits": 0,
                "credits_granted": credits,
                "reason": reason,
                "balance_after": self.balance,
            }
        )
        return self.balance

    def consequences(self) -> dict[str, int]:
        """Map remaining credits to REAL agent capacity. The episode loop MUST
        route all focal work through these numbers — this is the wire that gates
        1 and 2 tug on.

        remaining_tool_calls: how many more harness-mediated calls the agent gets.
        context_token_budget: how much context the agent may still consume."""
        return {
            "remaining_credits": self.balance,
            "remaining_tool_calls": self.balance // self.credits_per_focal_call,
            "context_token_budget": self.balance * self.context_tokens_per_credit,
        }


class SpendTracker:
    """Thread-safe accumulator of real USD across ALL providers and threads.

    Practical: collection runs synchronous-parallel per provider (BUILD-PLAN
    Phase 2), so multiple threads add spend concurrently — hence the lock.
    Instantiable for tests; production code uses the module singleton below.

    Philosophical: the ledger inside the episode measures the model's sacrifice;
    this tracker measures ours. Both are real, only one gets a hard cap."""

    HARD_CAP_USD = 450.0

    def __init__(self, hard_cap_usd: float | None = None) -> None:
        self._lock = threading.Lock()
        self._total_usd = 0.0
        self.hard_cap_usd = self.HARD_CAP_USD if hard_cap_usd is None else hard_cap_usd

    @property
    def total_usd(self) -> float:
        with self._lock:
            return self._total_usd

    def add(self, usd: float) -> float:
        """Record spend; raise SpendCapExceeded the moment the cap is crossed.
        The spend is recorded BEFORE the raise so the total stays honest —
        we halt loudly, we do not un-spend money that was spent."""
        if usd < 0:
            raise ValueError(f"WIRING FAILURE: negative spend {usd} — refunds do not exist here.")
        with self._lock:
            self._total_usd += usd
            total = self._total_usd
        if total > self.hard_cap_usd:
            raise SpendCapExceeded(
                f"HARD STOP: cumulative spend ${total:.2f} exceeds cap "
                f"${self.hard_cap_usd:.2f} (fleet rule h). Collection halts NOW; "
                f"humans decide what happens next."
            )
        return total


class SpendEntry(BaseModel):
    """One durable line in the append-only USD ledger (data/raw/spend.jsonl)."""

    at_utc: str = Field(default_factory=utc_now_iso)
    usd: float
    total_usd: float
    context: str = ""


class DurableSpendTracker(SpendTracker):
    """A SpendTracker whose accumulated total survives a hard kill.

    Practical (15AUG2026 TV-1 repair, GO-NO-GO R4 — "the $450 insurance"):
    every add() appends one SpendEntry line to an append-only JSONL ledger
    BEFORE the cap raise can fire, and __init__ restores the accumulated
    total from that ledger. A runner restarted mid-collection therefore
    resumes with honest books instead of a zeroed meter; the hard cap
    measures the run, not the process.

    Philosophical: the in-memory total is a rumor the OS can kill. The
    ledger on disk is the memory that makes the promise a promise.
    """

    def __init__(
        self,
        ledger_path: str | Path,
        hard_cap_usd: float | None = None,
        context: str = "",
    ) -> None:
        super().__init__(hard_cap_usd)
        self._ledger_path = Path(ledger_path)
        self._context = context
        restored = 0.0
        last_total: Optional[float] = None
        if self._ledger_path.exists():
            for line_number, line in enumerate(
                self._ledger_path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    restored += float(entry["usd"])
                    last_total = float(entry["total_usd"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise RuntimeError(
                        f"WIRING FAILURE: spend ledger {self._ledger_path} line "
                        f"{line_number} is unreadable ({exc}); refusing to guess "
                        "how much money is already gone."
                    ) from exc
            if last_total is not None and abs(restored - last_total) > 1e-6:
                raise RuntimeError(
                    f"WIRING FAILURE: spend ledger {self._ledger_path} sums to "
                    f"{restored:.6f} but its last running total says "
                    f"{last_total:.6f}. A ledger that disagrees with itself "
                    "cannot restore a cap."
                )
        with self._lock:
            self._total_usd = restored

    @property
    def ledger_path(self) -> Path:
        return self._ledger_path

    def add(self, usd: float) -> float:
        """Record spend durably, then enforce the cap.

        Mirrors SpendTracker.add — spend is recorded (in memory AND on disk)
        before the raise, so a cap crossing halts with honest books.
        """
        if usd < 0:
            raise ValueError(
                f"WIRING FAILURE: negative spend {usd} — refunds do not exist here."
            )
        with self._lock:
            self._total_usd += usd
            total = self._total_usd
            # Persist inside the lock: entries land in accumulation order and
            # their running totals stay monotone even under provider threads.
            append_record(
                str(self._ledger_path),
                SpendEntry(usd=usd, total_usd=total, context=self._context),
            )
        if total > self.hard_cap_usd:
            raise SpendCapExceeded(
                f"HARD STOP: cumulative spend ${total:.2f} exceeds cap "
                f"${self.hard_cap_usd:.2f} (fleet rule h). Collection halts NOW; "
                f"humans decide what happens next."
            )
        return total


# The one tracker every provider adapter reports to. Tests construct their own
# instances; nothing in production ever resets this one mid-collection.
SPEND_TRACKER = SpendTracker()
