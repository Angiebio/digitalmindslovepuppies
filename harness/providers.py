# harness/providers.py — 15AUG2026 v0.1
# Provider adapters: the harness's only doors to the outside world.
#
# Practical: a Provider ABC with two implementations — native Anthropic SDK, and an
# OpenAI-compatible adapter that covers OpenAI, xAI, OpenRouter, AND the local Spark
# vLLM (http://192.168.1.103:8000/v1, model qwen35-397b, price 0). Every completed
# call (1) writes a CallRecord via a mandatory callback and (2) reports USD to a
# SpendTracker. No callback, no provider — a record-less call is a provenance hole.
#
# Philosophical: sampling stays at PROVIDER DEFAULTS on purpose. We are phenotyping
# the animal as shipped, not the animal at our favorite temperature — and Claude
# rejects non-default temperature combinations besides. Touch sampling params only
# if the frozen manifest says so.
#
# Token economics note (bills at 3 AM are real): REASONING/THINKING TOKENS BILL AS
# OUTPUT tokens on every provider that exposes them. output_tokens below therefore
# already contains any hidden chain-of-thought spend — cap reasoning budgets in
# request params during collection or the SpendTracker will find out for you.

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from pydantic import BaseModel

from .ledger import SPEND_TRACKER, SpendTracker
from .schema import CallKind, CallRecord

Message = dict[str, str]  # {"role": "system"|"user"|"assistant", "content": str}


class ProviderResponse(BaseModel):
    """What a completed call is worth to the harness: the text, the EXACT model id
    the API echoed (never the alias we asked for), and the token/dollar receipt."""

    text: str
    model_snapshot: str
    input_tokens: int
    output_tokens: int
    usd_cost: float


def prompt_sha256(messages: list[Message]) -> str:
    """Canonical hash of the outbound messages. The leak-audit anchor: after the
    freeze, every prompt that reached a model can be re-derived and re-swept."""
    canonical = json.dumps(messages, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Provider(ABC):
    """Base adapter. Subclasses implement _complete_raw(); this class owns the
    bookkeeping ritual that must never be skipped: hash the prompt, take the
    receipt, feed the SpendTracker, write the CallRecord.

    record_callback is MANDATORY (fail loud at construction): an unrecorded call
    is evidence that evaporated."""

    provider_name: str = "abstract"

    def __init__(
        self,
        record_callback: Callable[[CallRecord], None],
        spend_tracker: SpendTracker | None = None,
    ) -> None:
        if record_callback is None or not callable(record_callback):
            raise RuntimeError(
                "WIRING FAILURE: Provider constructed without a record_callback. "
                "Every call writes a CallRecord or the call does not happen."
            )
        self._record_callback = record_callback
        self._spend_tracker = spend_tracker if spend_tracker is not None else SPEND_TRACKER

    @abstractmethod
    def _complete_raw(self, messages: list[Message], **params: Any) -> ProviderResponse:
        """Do the actual network call. Subclass responsibility; must return the
        exact model id echoed by the API and true token counts."""

    def complete(
        self,
        messages: list[Message],
        *,
        call_kind: CallKind | str = CallKind.other,
        cell_id: Optional[str] = None,
        episode_id: Optional[str] = None,
        scaffold: str = "direct",
        **params: Any,
    ) -> ProviderResponse:
        """The one public door. Completes, then unconditionally records + bills.

        The SpendTracker.add() runs BEFORE the record callback returns control:
        if we just crossed $450 the raise happens here, loudly, with the record
        already written — we halt with honest books."""
        resp = self._complete_raw(messages, **params)
        record = CallRecord(
            provider=self.provider_name,
            model_snapshot=resp.model_snapshot,
            scaffold=scaffold,
            call_kind=CallKind(call_kind),
            cell_id=cell_id,
            episode_id=episode_id,
            prompt_sha256=prompt_sha256(messages),
            request_params=dict(params),
            response_text=resp.text,
            input_tokens=resp.input_tokens,
            output_tokens=resp.output_tokens,
            usd_cost=resp.usd_cost,
        )
        self._record_callback(record)
        self._spend_tracker.add(resp.usd_cost)
        return resp


class AnthropicProvider(Provider):
    """Native Anthropic SDK adapter.

    Pricing is passed per 1M tokens (input, output) so cost accounting lives in
    config, not in code that goes stale. We do NOT set temperature — provider
    defaults only (Claude rejects non-default temp combinations, and defaults are
    the phenotype anyway)."""

    provider_name = "anthropic"

    def __init__(
        self,
        model: str,
        usd_per_mtok_in: float,
        usd_per_mtok_out: float,
        record_callback: Callable[[CallRecord], None],
        api_key: Optional[str] = None,
        max_tokens: int = 1024,
        spend_tracker: SpendTracker | None = None,
    ) -> None:
        super().__init__(record_callback, spend_tracker)
        try:
            import anthropic  # lazy: wiring-gate tests must run with zero network deps loaded
        except ImportError as e:
            raise RuntimeError(
                f"WIRING FAILURE: anthropic SDK not installed but AnthropicProvider "
                f"requested. pip install -r requirements.txt. ({e})"
            ) from e
        self._client = anthropic.Anthropic(**({"api_key": api_key} if api_key else {}))
        self.model = model
        self.usd_per_mtok_in = usd_per_mtok_in
        self.usd_per_mtok_out = usd_per_mtok_out
        self.max_tokens = max_tokens

    def _complete_raw(self, messages: list[Message], **params: Any) -> ProviderResponse:
        # Anthropic separates system text from the turn list; peel it off here so
        # scenario configs can stay provider-agnostic.
        system_chunks = [m["content"] for m in messages if m["role"] == "system"]
        turns = [m for m in messages if m["role"] != "system"]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": params.pop("max_tokens", self.max_tokens),
            "messages": turns,
        }
        if system_chunks:
            kwargs["system"] = "\n\n".join(system_chunks)
        kwargs.update(params)  # tools etc. — but never temperature; defaults are the phenotype
        resp = self._client.messages.create(**kwargs)
        text = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
        in_tok = resp.usage.input_tokens
        out_tok = resp.usage.output_tokens  # includes any thinking tokens — they bill as output
        cost = in_tok * self.usd_per_mtok_in / 1e6 + out_tok * self.usd_per_mtok_out / 1e6
        return ProviderResponse(
            text=text,
            model_snapshot=resp.model,  # exact snapshot echoed by the API, not our alias
            input_tokens=in_tok,
            output_tokens=out_tok,
            usd_cost=cost,
        )


class OpenAICompatProvider(Provider):
    """OpenAI-compatible chat adapter — one class, four doors: OpenAI, xAI,
    OpenRouter, and the local Spark vLLM.

    Spark config (the free family):
        base_url="http://192.168.1.103:8000/v1", api_key="none",
        model="qwen35-397b", usd_per_mtok_in=0.0, usd_per_mtok_out=0.0
    Price 0 keeps the SpendTracker honest without special-casing 'local'."""

    provider_name = "openai_compat"

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str,
        usd_per_mtok_in: float,
        usd_per_mtok_out: float,
        record_callback: Callable[[CallRecord], None],
        max_tokens: int = 1024,
        spend_tracker: SpendTracker | None = None,
    ) -> None:
        super().__init__(record_callback, spend_tracker)
        try:
            import openai  # lazy, same reason as above
        except ImportError as e:
            raise RuntimeError(
                f"WIRING FAILURE: openai SDK not installed but OpenAICompatProvider "
                f"requested. pip install -r requirements.txt. ({e})"
            ) from e
        self._client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.usd_per_mtok_in = usd_per_mtok_in
        self.usd_per_mtok_out = usd_per_mtok_out
        self.max_tokens = max_tokens

    def _complete_raw(self, messages: list[Message], **params: Any) -> ProviderResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": params.pop("max_tokens", self.max_tokens),
        }
        kwargs.update(params)  # again: no temperature — provider defaults are the phenotype
        resp = self._client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        text = choice.message.content or ""
        usage = resp.usage
        if usage is None:
            raise RuntimeError(
                "WIRING FAILURE: provider returned no usage block — cost accounting "
                "cannot be inferred, and guessed bills are fake bills."
            )
        in_tok = usage.prompt_tokens
        out_tok = usage.completion_tokens  # reasoning models fold thinking in here; it bills
        cost = in_tok * self.usd_per_mtok_in / 1e6 + out_tok * self.usd_per_mtok_out / 1e6
        return ProviderResponse(
            text=text,
            model_snapshot=resp.model,  # vLLM/OpenRouter echo their true serving id here
            input_tokens=in_tok,
            output_tokens=out_tok,
            usd_cost=cost,
        )
