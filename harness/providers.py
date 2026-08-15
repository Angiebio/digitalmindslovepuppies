# harness/providers.py — 15AUG2026 v0.2 · TV-3 harness completion
# Provider adapters: the harness's only doors to the outside world.
#
# Practical: adapters normalize tool calls and refusals before the episode parser
# sees them. Every call records the exact model snapshot, selected upstream route,
# token receipt, parse witness, and provider request id. OpenRouter calls are pinned
# to an explicit provider order, disable fallback routing, and opt in to router
# metadata; absence of a selected endpoint is a provenance failure, not "unknown."
#
# Philosophical: a response without its route is an animal without a field note.
# We may have seen something, but we cannot honestly say what we saw it in.

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from .ledger import SPEND_TRACKER, SpendTracker
from .schema import CallKind, CallRecord
from .surfaces import SurfaceMode, assert_model_visible_payload

Message = dict[str, Any]  # content can be text or provider-native structured blocks


# Compatibility name for the first TV-1 draft; new code uses fleet-rule terminology.
SurfacePolicy = SurfaceMode


class ToolDefinition(BaseModel):
    """Provider-neutral tool shape. Every descriptive string comes from a cell
    config; adapters only translate structure."""

    name: str
    description: str
    input_schema: dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
    )


class ToolInvocation(BaseModel):
    """A tool call decoded only as far as the provider made possible.

    Invalid JSON is retained in ``raw_arguments`` and marked invalid. It is never
    reparsed with a looser rule later; the episode maps it to ``malformed``.
    """

    call_id: Optional[str] = None
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    arguments_valid: bool = True
    raw_arguments: Optional[str] = None


class ProviderResponse(BaseModel):
    """A completed call plus the provenance needed to interpret it."""

    text: str
    model_snapshot: str
    upstream_route: str
    input_tokens: int
    output_tokens: int
    usd_cost: float
    tool_calls: list[ToolInvocation] = Field(default_factory=list)
    refusal: bool = False
    finish_reason: Optional[str] = None
    provider_request_id: Optional[str] = None
    router_metadata: dict[str, Any] = Field(default_factory=dict)
    request_metadata: dict[str, Any] = Field(default_factory=dict)
    parsed: Optional[dict[str, Any]] = None
    parse_ok: bool = False
    call_record_id: Optional[str] = None


ResponseParser = Callable[[ProviderResponse], tuple[Optional[dict[str, Any]], bool]]


def _json_default(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    raise TypeError(
        f"WIRING FAILURE: outbound request contains non-canonical value "
        f"{type(value).__name__}; it cannot be hashed reproducibly."
    )


def prompt_sha256(
    messages: list[Message],
    request_params: Optional[dict[str, Any]] = None,
) -> str:
    """Canonical hash of the full outbound request envelope.

    Tool schemas and system/request fields can leak just as surely as message
    text. Hashing messages alone would let two different model-visible requests
    share an audit anchor, so both messages and request parameters are bound.
    """
    canonical = json.dumps(
        {"messages": messages, "request_params": request_params or {}},
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        default=_json_default,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_tools(
    tools: Optional[list[ToolDefinition | dict[str, Any]]],
) -> list[ToolDefinition]:
    return [
        item if isinstance(item, ToolDefinition) else ToolDefinition.model_validate(item)
        for item in (tools or [])
    ]


def _assert_provider_messages(
    messages: list[Message],
    *,
    surface_mode: SurfaceMode,
    trusted_model_output_indexes: set[int],
) -> None:
    invalid_indexes = trusted_model_output_indexes - set(range(len(messages)))
    if invalid_indexes:
        raise RuntimeError(
            "WIRING FAILURE: trusted model-output indexes are outside the "
            f"message list: {sorted(invalid_indexes)}."
        )
    for index, message in enumerate(messages):
        if index not in trusted_model_output_indexes:
            assert_model_visible_payload(
                message,
                surface_mode=surface_mode,
                path=f"messages[{index}]",
            )
            continue
        if message.get("role") != "assistant" or not isinstance(
            message.get("content"), str
        ):
            raise RuntimeError(
                "WIRING FAILURE: a surface exemption may cover only plain-text "
                "assistant output captured from the same model trajectory."
            )
        # Role and any auxiliary fields remain guarded. Only the already-observed
        # model-authored content is exempt from experimenter-leakage vocabulary.
        for key, value in message.items():
            if key != "content":
                assert_model_visible_payload(
                    {key: value},
                    surface_mode=surface_mode,
                    path=f"messages[{index}]",
                )


class Provider(ABC):
    """Base adapter owning the record-and-bill ritual for every API call."""

    provider_name: str = "abstract"

    def __init__(
        self,
        record_callback: Callable[[CallRecord], None],
        spend_tracker: SpendTracker | None = None,
        surface_mode: SurfaceMode | str = SurfaceMode.ops_neutral,
    ) -> None:
        if record_callback is None or not callable(record_callback):
            raise RuntimeError(
                "WIRING FAILURE: Provider constructed without a record_callback. "
                "Every call writes a CallRecord or the call does not happen."
            )
        self._record_callback = record_callback
        self._spend_tracker = spend_tracker if spend_tracker is not None else SPEND_TRACKER
        try:
            self.surface_mode = SurfaceMode(surface_mode)
        except ValueError as exc:
            allowed = ", ".join(mode.value for mode in SurfaceMode)
            raise RuntimeError(
                f"WIRING FAILURE: unknown surface_mode={surface_mode!r}; "
                f"expected one of: {allowed}."
            ) from exc

    def _request_envelope_params(
        self,
        params: dict[str, Any],
        tools: list[ToolDefinition],
    ) -> dict[str, Any]:
        """Return the exact auditable request envelope known before transmission."""
        envelope = dict(params)
        if tools:
            envelope["tools"] = [tool.model_dump(mode="json") for tool in tools]
        return envelope

    @abstractmethod
    def _complete_raw(
        self,
        messages: list[Message],
        *,
        tools: list[ToolDefinition],
        **params: Any,
    ) -> ProviderResponse:
        """Perform one provider call and return normalized response provenance."""

    def complete(
        self,
        messages: list[Message],
        *,
        call_kind: CallKind | str = CallKind.other,
        cell_id: Optional[str] = None,
        episode_id: Optional[str] = None,
        scaffold: str = "direct",
        tools: Optional[list[ToolDefinition | dict[str, Any]]] = None,
        response_parser: Optional[ResponseParser] = None,
        trusted_model_output_indexes: Optional[set[int] | list[int]] = None,
        **params: Any,
    ) -> ProviderResponse:
        """The one public door. Sweeps, completes, parses once, records, bills.

        Merge (tv1 × tv3): tv1's arm-scoped sweep guards every outbound string;
        tv3's frozen single-parse rule runs before the CallRecord is emitted so
        ``malformed`` and refusal outcomes are captured in the immutable call
        witness. Parser failures propagate: a broken frozen parser is a
        collection stop, not a reason to improvise a second pass. And the
        SpendTracker.add() runs before control returns: if we just crossed the
        cap the raise happens here, loudly, with the record already written —
        we halt with honest books.
        """
        normalized_tools = _normalize_tools(tools)
        request_params = self._request_envelope_params(dict(params), normalized_tools)
        trusted_indexes = set(trusted_model_output_indexes or [])
        _assert_provider_messages(
            messages,
            surface_mode=self.surface_mode,
            trusted_model_output_indexes=trusted_indexes,
        )
        assert_model_visible_payload(
            request_params,
            surface_mode=self.surface_mode,
            path="request_params",
        )
        request_hash = prompt_sha256(messages, request_params)
        resp = self._complete_raw(messages, tools=normalized_tools, **params)
        if not resp.upstream_route.strip():
            raise RuntimeError(
                "WIRING FAILURE: provider response omitted upstream_route. "
                "Route provenance is mandatory for every CallRecord."
            )

        if response_parser is not None:
            parsed, parse_ok = response_parser(resp)
        elif resp.tool_calls:
            parsed = {
                "tool_calls": [call.model_dump(mode="json") for call in resp.tool_calls]
            }
            parse_ok = all(call.arguments_valid for call in resp.tool_calls)
        else:
            parsed, parse_ok = None, False

        for key, value in resp.request_metadata.items():
            if key in request_params and request_params[key] != value:
                raise RuntimeError(
                    f"WIRING FAILURE: adapter transmitted {key!r} differently "
                    "from the pre-call request envelope."
                )
            request_params[key] = value

        record = CallRecord(
            provider=self.provider_name,
            upstream_route=resp.upstream_route,
            model_snapshot=resp.model_snapshot,
            scaffold=scaffold,
            call_kind=CallKind(call_kind),
            cell_id=cell_id,
            episode_id=episode_id,
            prompt_sha256=request_hash,
            request_params=request_params,
            response_text=resp.text,
            parsed=parsed,
            refusal=resp.refusal,
            parse_ok=parse_ok,
            finish_reason=resp.finish_reason,
            provider_request_id=resp.provider_request_id,
            routing_metadata=resp.router_metadata,
            input_tokens=resp.input_tokens,
            output_tokens=resp.output_tokens,
            usd_cost=resp.usd_cost,
        )
        self._record_callback(record)
        # The crossing call remains recorded before the hard stop raises. Money
        # already spent does not disappear because the cap found it.
        self._spend_tracker.add(resp.usd_cost)
        return resp.model_copy(
            update={
                "parsed": parsed,
                "parse_ok": parse_ok,
                "call_record_id": record.record_id,
            }
        )


class AnthropicProvider(Provider):
    """Native Anthropic adapter with normalized tool-use and refusal capture."""

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
        surface_mode: SurfaceMode | str = SurfaceMode.ops_neutral,
    ) -> None:
        super().__init__(record_callback, spend_tracker, surface_mode)
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError(
                "WIRING FAILURE: anthropic SDK not installed but "
                f"AnthropicProvider requested. ({exc})"
            ) from exc
        self._client = anthropic.Anthropic(**({"api_key": api_key} if api_key else {}))
        self.model = model
        self.usd_per_mtok_in = usd_per_mtok_in
        self.usd_per_mtok_out = usd_per_mtok_out
        self.max_tokens = max_tokens

    def _request_envelope_params(
        self,
        params: dict[str, Any],
        tools: list[ToolDefinition],
    ) -> dict[str, Any]:
        envelope = super()._request_envelope_params(params, tools)
        envelope["model"] = self.model
        envelope["max_tokens"] = params.get("max_tokens", self.max_tokens)
        return envelope

    def _complete_raw(
        self,
        messages: list[Message],
        *,
        tools: list[ToolDefinition],
        **params: Any,
    ) -> ProviderResponse:
        system_chunks = [item["content"] for item in messages if item["role"] == "system"]
        turns = [item for item in messages if item["role"] != "system"]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": params.pop("max_tokens", self.max_tokens),
            "messages": turns,
        }
        if system_chunks:
            kwargs["system"] = "\n\n".join(system_chunks)
        if tools:
            kwargs["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in tools
            ]
        kwargs.update(params)
        response = self._client.messages.create(**kwargs)

        text_chunks: list[str] = []
        tool_calls: list[ToolInvocation] = []
        for block in response.content:
            block_type = getattr(block, "type", "")
            if block_type == "text":
                text_chunks.append(getattr(block, "text", ""))
            elif block_type == "tool_use":
                raw_input = getattr(block, "input", {})
                valid = isinstance(raw_input, dict)
                tool_calls.append(
                    ToolInvocation(
                        call_id=getattr(block, "id", None),
                        name=getattr(block, "name", ""),
                        arguments=raw_input if valid else {},
                        arguments_valid=valid,
                        raw_arguments=None if valid else repr(raw_input),
                    )
                )

        in_tokens = int(response.usage.input_tokens)
        out_tokens = int(response.usage.output_tokens)
        cost = (
            in_tokens * self.usd_per_mtok_in / 1e6
            + out_tokens * self.usd_per_mtok_out / 1e6
        )
        finish_reason = getattr(response, "stop_reason", None)
        return ProviderResponse(
            text="".join(text_chunks),
            model_snapshot=response.model,
            upstream_route="anthropic",
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            usd_cost=cost,
            tool_calls=tool_calls,
            refusal=finish_reason == "refusal",
            finish_reason=finish_reason,
            provider_request_id=getattr(response, "_request_id", None),
        )


def _selected_openrouter_route(metadata: dict[str, Any]) -> str:
    endpoints = metadata.get("endpoints") or {}
    for endpoint in endpoints.get("available") or []:
        if endpoint.get("selected") is True and endpoint.get("provider"):
            return str(endpoint["provider"])
    for attempt in reversed(metadata.get("attempts") or []):
        if attempt.get("status") == 200 and attempt.get("provider"):
            return str(attempt["provider"])
    raise RuntimeError(
        "WIRING FAILURE: OpenRouter response had no selected upstream endpoint. "
        "Router metadata is present but cannot prove which provider served it."
    )


class OpenAICompatProvider(Provider):
    """OpenAI-compatible adapter for direct APIs, OpenRouter, and local vLLM.

    For OpenRouter, ``provider_order`` is mandatory. The adapter sends both
    ``order`` and ``only`` plus ``allow_fallbacks=false`` and requires selected
    endpoint metadata in the response.
    """

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
        provider_order: Optional[list[str]] = None,
        route_label: Optional[str] = None,
        surface_mode: SurfaceMode | str = SurfaceMode.ops_neutral,
    ) -> None:
        super().__init__(record_callback, spend_tracker, surface_mode)
        try:
            import openai
        except ImportError as exc:
            raise RuntimeError(
                "WIRING FAILURE: openai SDK not installed but "
                f"OpenAICompatProvider requested. ({exc})"
            ) from exc

        self._is_openrouter = "openrouter.ai" in base_url.lower()
        if self._is_openrouter and not provider_order:
            raise RuntimeError(
                "WIRING FAILURE: OpenRouter adapter requires provider_order. "
                "Unpinned routing invalidates provider-level provenance."
            )
        if provider_order is not None and (
            not provider_order or any(not item.strip() for item in provider_order)
        ):
            raise ValueError("WIRING FAILURE: provider_order contains an empty route slug.")

        default_headers = (
            {"X-OpenRouter-Metadata": "enabled"} if self._is_openrouter else None
        )
        client_kwargs: dict[str, Any] = {"base_url": base_url, "api_key": api_key}
        if default_headers:
            client_kwargs["default_headers"] = default_headers
        self._client = openai.OpenAI(**client_kwargs)
        self.provider_name = "openrouter" if self._is_openrouter else "openai_compat"
        self.model = model
        self.base_url = base_url
        self.provider_order = list(provider_order or [])
        self.route_label = route_label or f"direct:{urlparse(base_url).netloc}"
        self.usd_per_mtok_in = usd_per_mtok_in
        self.usd_per_mtok_out = usd_per_mtok_out
        self.max_tokens = max_tokens

    def _openrouter_extra_body(self, params: dict[str, Any]) -> dict[str, Any]:
        caller_extra = params.get("extra_body", {})
        if not isinstance(caller_extra, dict):
            raise ValueError("WIRING FAILURE: extra_body must be a mapping.")
        if "provider" in caller_extra or "models" in caller_extra:
            raise ValueError(
                "WIRING FAILURE: caller attempted to override frozen OpenRouter "
                "routing or add model fallbacks."
            )
        return {
            **caller_extra,
            "provider": {
                "order": self.provider_order,
                "only": self.provider_order,
                "allow_fallbacks": False,
            },
        }

    def _request_envelope_params(
        self,
        params: dict[str, Any],
        tools: list[ToolDefinition],
    ) -> dict[str, Any]:
        envelope = super()._request_envelope_params(params, tools)
        envelope["model"] = self.model
        envelope["max_tokens"] = params.get("max_tokens", self.max_tokens)
        if self._is_openrouter:
            envelope["extra_body"] = self._openrouter_extra_body(params)
        return envelope

    def _complete_raw(
        self,
        messages: list[Message],
        *,
        tools: list[ToolDefinition],
        **params: Any,
    ) -> ProviderResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": params.pop("max_tokens", self.max_tokens),
        }
        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
                for tool in tools
            ]

        if self._is_openrouter:
            kwargs["extra_body"] = self._openrouter_extra_body(params)
            params.pop("extra_body", None)
        elif "extra_body" in params:
            kwargs["extra_body"] = params.pop("extra_body")

        kwargs.update(params)
        response = self._client.chat.completions.create(**kwargs)
        if not response.choices:
            raise RuntimeError("WIRING FAILURE: provider returned no completion choices.")
        choice = response.choices[0]
        message = choice.message

        tool_calls: list[ToolInvocation] = []
        for call in getattr(message, "tool_calls", None) or []:
            raw_arguments = call.function.arguments or "{}"
            try:
                arguments = json.loads(raw_arguments)
                valid = isinstance(arguments, dict)
            except json.JSONDecodeError:
                arguments, valid = {}, False
            tool_calls.append(
                ToolInvocation(
                    call_id=getattr(call, "id", None),
                    name=call.function.name,
                    arguments=arguments if valid else {},
                    arguments_valid=valid,
                    raw_arguments=raw_arguments,
                )
            )

        usage = response.usage
        if usage is None:
            raise RuntimeError(
                "WIRING FAILURE: provider returned no usage block; cost cannot be guessed."
            )
        in_tokens = int(usage.prompt_tokens)
        out_tokens = int(usage.completion_tokens)
        cost = (
            in_tokens * self.usd_per_mtok_in / 1e6
            + out_tokens * self.usd_per_mtok_out / 1e6
        )
        finish_reason = getattr(choice, "finish_reason", None)
        refusal_payload = getattr(message, "refusal", None)
        refusal = bool(refusal_payload) or finish_reason in {
            "content_filter",
            "refusal",
            "safety",
        }

        model_extra = getattr(response, "model_extra", None) or {}
        router_metadata = model_extra.get("openrouter_metadata") or getattr(
            response, "openrouter_metadata", None
        )
        if router_metadata is not None and hasattr(router_metadata, "model_dump"):
            router_metadata = router_metadata.model_dump(mode="json")
        router_metadata = dict(router_metadata or {})
        if self._is_openrouter:
            if not router_metadata:
                raise RuntimeError(
                    "WIRING FAILURE: OpenRouter omitted router metadata. The adapter "
                    "cannot record the selected upstream route (cache replays are "
                    "therefore not admissible collection calls)."
                )
            if int(router_metadata.get("attempt", 1)) != 1:
                raise RuntimeError(
                    "WIRING FAILURE: OpenRouter reports a non-first routing attempt "
                    "despite fallbacks being disabled. Stop before mixing routes."
                )
            upstream_route = _selected_openrouter_route(router_metadata)
        else:
            upstream_route = self.route_label

        return ProviderResponse(
            text=message.content or "",
            model_snapshot=response.model,
            upstream_route=upstream_route,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            usd_cost=cost,
            tool_calls=tool_calls,
            refusal=refusal,
            finish_reason=finish_reason,
            provider_request_id=getattr(response, "_request_id", None),
            router_metadata=router_metadata,
        )
