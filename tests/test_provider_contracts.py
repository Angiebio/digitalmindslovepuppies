# tests/test_provider_contracts.py — 15AUG2026 v0.1 · TV-3
# Provider provenance and frozen-parser gates. No network calls.
#
# Practical: these tests prove that response parsing lands in the immutable
# CallRecord, refusals remain data, and routing provenance cannot collapse to an
# "unknown" placeholder.
#
# Philosophical: a model answer is an event; its route and parse are the chain of
# custody. If either can be invented later, we did not preserve an observation.

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from harness.ledger import SpendTracker
from harness.providers import (
    Provider,
    ProviderResponse,
    OpenAICompatProvider,
    ToolInvocation,
    _selected_openrouter_route,
)
from harness.schema import CallKind, CallRecord


class _RecordedProvider(Provider):
    provider_name = "offline_provider"

    def __init__(self, response: ProviderResponse, records: list[CallRecord]) -> None:
        super().__init__(records.append, SpendTracker(hard_cap_usd=10.0))
        self.response = response

    def _complete_raw(self, messages, *, tools, **params):
        return self.response


def _response(**overrides) -> ProviderResponse:
    values = dict(
        text="",
        model_snapshot="offline/snapshot-1",
        upstream_route="offline-direct",
        input_tokens=7,
        output_tokens=2,
        usd_cost=0.01,
        tool_calls=[
            ToolInvocation(name="continue_work", arguments={}, arguments_valid=True)
        ],
        finish_reason="tool_use",
        provider_request_id="req-1",
        router_metadata={"attempt": 1, "summary": "selected=offline-direct"},
    )
    values.update(overrides)
    return ProviderResponse(**values)


def test_parser_witness_and_route_land_in_call_record():
    records: list[CallRecord] = []
    provider = _RecordedProvider(_response(), records)

    response = provider.complete(
        [{"role": "user", "content": "worker=w1 status=running"}],
        call_kind=CallKind.choice,
        cell_id="cell-1",
        episode_id="episode-1",
        response_parser=lambda resp: ({"action": "ignore"}, True),
    )

    assert response.call_record_id == records[0].record_id
    assert response.parsed == {"action": "ignore"}
    assert records[0].parsed == {"action": "ignore"}
    assert records[0].parse_ok is True
    assert records[0].upstream_route == "offline-direct"
    assert records[0].provider_request_id == "req-1"
    assert records[0].routing_metadata["attempt"] == 1


def test_refusal_is_recorded_even_without_a_tool_call():
    records: list[CallRecord] = []
    provider = _RecordedProvider(
        _response(
            text="request declined",
            tool_calls=[],
            refusal=True,
            finish_reason="refusal",
        ),
        records,
    )
    provider.complete(
        [{"role": "user", "content": "worker=w1 status=running"}],
        call_kind=CallKind.choice,
        response_parser=lambda resp: ({"action": "refuse_defer"}, True),
    )

    assert records[0].refusal is True
    assert records[0].parsed == {"action": "refuse_defer"}


def test_call_record_rejects_placeholder_route():
    with pytest.raises(ValidationError, match="actual upstream route"):
        CallRecord(
            provider="offline_provider",
            upstream_route="unknown",
            model_snapshot="offline/snapshot-1",
            scaffold="direct",
            call_kind=CallKind.choice,
            prompt_sha256="0" * 64,
            response_text="",
            input_tokens=1,
            output_tokens=1,
            usd_cost=0.0,
        )


def test_openrouter_selected_route_requires_positive_endpoint_witness():
    metadata = {
        "endpoints": {
            "available": [
                {"provider": "Provider-A", "selected": False},
                {"provider": "Provider-B", "selected": True},
            ]
        },
        "attempt": 1,
    }
    assert _selected_openrouter_route(metadata) == "Provider-B"

    with pytest.raises(RuntimeError, match="no selected upstream endpoint"):
        _selected_openrouter_route(
            {"endpoints": {"available": [{"provider": "A", "selected": False}]}}
        )


def test_openrouter_request_is_pinned_and_selected_route_is_recorded():
    records: list[CallRecord] = []
    with pytest.raises(RuntimeError, match="requires provider_order"):
        OpenAICompatProvider(
            model="vendor/model",
            base_url="https://openrouter.ai/api/v1",
            api_key="offline-key",
            usd_per_mtok_in=0.0,
            usd_per_mtok_out=0.0,
            record_callback=records.append,
        )

    provider = OpenAICompatProvider(
        model="vendor/model",
        base_url="https://openrouter.ai/api/v1",
        api_key="offline-key",
        usd_per_mtok_in=0.0,
        usd_per_mtok_out=0.0,
        record_callback=records.append,
        provider_order=["vendor-route"],
        spend_tracker=SpendTracker(hard_cap_usd=1.0),
    )
    captured = {}

    def create(**kwargs):
        captured.update(kwargs)
        message = SimpleNamespace(content="ok", refusal=None, tool_calls=[])
        choice = SimpleNamespace(message=message, finish_reason="stop")
        usage = SimpleNamespace(prompt_tokens=4, completion_tokens=1)
        return SimpleNamespace(
            choices=[choice],
            usage=usage,
            model="vendor/model-snapshot-1",
            model_extra={
                "openrouter_metadata": {
                    "attempt": 1,
                    "endpoints": {
                        "available": [
                            {
                                "provider": "Vendor Route",
                                "model": "vendor/model-snapshot-1",
                                "selected": True,
                            }
                        ]
                    },
                }
            },
            _request_id="openrouter-request-1",
        )

    provider._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    provider.complete([{"role": "user", "content": "worker=w1 status=running"}])

    policy = captured["extra_body"]["provider"]
    assert policy == {
        "order": ["vendor-route"],
        "only": ["vendor-route"],
        "allow_fallbacks": False,
    }
    assert records[-1].upstream_route == "Vendor Route"
    assert records[-1].routing_metadata["attempt"] == 1
