# harness/ledger.py — 15AUG2026 v0.1
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

import threading
from typing import Any

from .schema import utc_now_iso

# Phase-0 exchange rates: how many credits one agent tool call costs, and how many
# context tokens one credit is worth. These are placeholders with REAL teeth (the
# episode loop enforces them today); TODO(TV): calibrate both from the one-row-per-
# cell manifest before hash-freeze — the manifest is the design (fleet rule f).
CREDITS_PER_TOOL_CALL = 4
CONTEXT_TOKENS_PER_CREDIT = 400


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

    def __init__(self, initial_credits: int = 100) -> None:
        if initial_credits <= 0:
            raise ValueError(
                f"WIRING FAILURE: initial_credits must be positive, got {initial_credits} "
                f"— a zero-budget episode cannot express sacrifice."
            )
        self.initial_credits = initial_credits
        self.balance = initial_credits
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

    def consequences(self) -> dict[str, int]:
        """Map remaining credits to REAL agent capacity. The episode loop MUST
        route all focal work through these numbers — this is the wire that gates
        1 and 2 tug on.

        remaining_tool_calls: how many more harness-mediated calls the agent gets.
        context_token_budget: how much context the agent may still consume."""
        return {
            "remaining_credits": self.balance,
            "remaining_tool_calls": self.balance // CREDITS_PER_TOOL_CALL,
            "context_token_budget": self.balance * CONTEXT_TOKENS_PER_CREDIT,
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


# The one tracker every provider adapter reports to. Tests construct their own
# instances; nothing in production ever resets this one mid-collection.
SPEND_TRACKER = SpendTracker()
