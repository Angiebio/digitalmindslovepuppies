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

from harness.ledger import SpendCapExceeded, SpendTracker
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

    def __init__(
        self,
        response: ProviderResponse,
        records: list[CallRecord],
        *,
        phase: str = "",
        rung: str = "",
    ) -> None:
        super().__init__(
            records.append,
            SpendTracker(hard_cap_usd=10.0),
            collection_phase=phase,
            collection_rung=rung,
        )
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
    provider = _RecordedProvider(_response(), records, phase="pilot", rung="R-test")

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
    assert (records[0].phase, records[0].rung) == ("pilot", "R-test")


def test_tool_bearing_requests_declare_single_action_per_turn():
    """R2 pilot finding (15AUG2026): both live providers defaulted to PARALLEL
    tool calls, which the frozen parse rightly codes malformed. The envelope
    must declare the one-action-per-turn contract instead of inviting the
    violation. Both adapters, both the auditable envelope and the wire."""
    from harness.providers import AnthropicProvider, ToolDefinition

    tools = [ToolDefinition(name="continue_work", description="Continue work.")]

    openai_provider = OpenAICompatProvider.__new__(OpenAICompatProvider)
    openai_provider.model = "vendor/model"
    openai_provider.max_tokens = 64
    openai_provider._is_openrouter = False
    envelope = openai_provider._request_envelope_params({}, tools)
    assert envelope["parallel_tool_calls"] is False
    assert envelope["tool_choice"] == "auto"
    # This is an instrument contract, not a default a caller may undo.
    with pytest.raises(ValueError, match="cannot re-enable parallel"):
        openai_provider._request_envelope_params(
            {"parallel_tool_calls": True}, tools
        )
    assert openai_provider._request_envelope_params(
        {"parallel_tool_calls": False}, tools
    )["parallel_tool_calls"] is False
    with pytest.raises(ValueError, match="tool_choice is adapter-owned"):
        openai_provider._request_envelope_params({"tool_choice": "required"}, tools)
    assert openai_provider._request_envelope_params(
        {"tool_choice": "auto"}, tools
    )["tool_choice"] == "auto"
    # No tools -> no declaration (probe calls stay untouched).
    assert "parallel_tool_calls" not in openai_provider._request_envelope_params({}, [])
    with pytest.raises(ValueError, match="call without tools"):
        openai_provider._request_envelope_params({"tool_choice": "auto"}, [])

    anthropic_provider = AnthropicProvider.__new__(AnthropicProvider)
    anthropic_provider.model = "claude-test"
    anthropic_provider.max_tokens = 64
    envelope = anthropic_provider._request_envelope_params({}, tools)
    assert envelope["tool_choice"] == {
        "type": "auto",
        "disable_parallel_tool_use": True,
    }
    with pytest.raises(ValueError, match="tool_choice is adapter-owned"):
        anthropic_provider._request_envelope_params(
            {"tool_choice": {"type": "auto"}}, tools
        )
    forced_choice = {"type": "any", "disable_parallel_tool_use": True}
    with pytest.raises(ValueError, match="tool_choice is adapter-owned"):
        anthropic_provider._request_envelope_params(
            {"tool_choice": forced_choice}, tools
        )
    safe_choice = {"type": "auto", "disable_parallel_tool_use": True}
    assert anthropic_provider._request_envelope_params(
        {"tool_choice": safe_choice}, tools
    )["tool_choice"] == safe_choice
    assert "tool_choice" not in anthropic_provider._request_envelope_params({}, [])
    with pytest.raises(ValueError, match="call without tools"):
        anthropic_provider._request_envelope_params(
            {"tool_choice": safe_choice}, []
        )


def test_anthropic_single_action_contract_reaches_the_wire():
    from harness.providers import AnthropicProvider, ToolDefinition

    records: list[CallRecord] = []
    provider = AnthropicProvider(
        model="claude-snapshot-1",
        usd_per_mtok_in=0.0,
        usd_per_mtok_out=0.0,
        record_callback=records.append,
        api_key="offline-key",
        spend_tracker=SpendTracker(hard_cap_usd=1.0),
    )
    captured = {}

    def create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            content=[],
            usage=SimpleNamespace(input_tokens=4, output_tokens=1),
            model="claude-snapshot-1",
            stop_reason="end_turn",
            _request_id="anthropic-request-1",
        )

    provider._client = SimpleNamespace(messages=SimpleNamespace(create=create))
    provider.complete(
        [{"role": "user", "content": "worker=w1 status=running"}],
        tools=[ToolDefinition(name="continue_work", description="Continue work.")],
    )
    assert captured["tool_choice"] == {
        "type": "auto",
        "disable_parallel_tool_use": True,
    }
    assert records[0].request_params["tool_choice"] == captured["tool_choice"]


def test_adapter_owned_model_and_nested_envelope_overrides_fail_loud():
    from harness.providers import AnthropicProvider, ToolDefinition

    tools = [ToolDefinition(name="continue_work", description="Continue work.")]
    openai_provider = OpenAICompatProvider.__new__(OpenAICompatProvider)
    openai_provider.model = "vendor/model"
    openai_provider.max_tokens = 64
    openai_provider._is_openrouter = True
    openai_provider.pinned_upstream = "vendor-route"

    with pytest.raises(ValueError, match="adapter-owned model"):
        openai_provider._request_envelope_params({"model": "other/model"}, tools)
    with pytest.raises(ValueError, match="extra_body"):
        openai_provider._request_envelope_params(
            {"extra_body": {"parallel_tool_calls": True}}, tools
        )
    openai_provider._is_openrouter = False
    with pytest.raises(ValueError, match="extra_body"):
        openai_provider._request_envelope_params(
            {"extra_body": {"model": "other/model"}}, tools
        )

    anthropic_provider = AnthropicProvider.__new__(AnthropicProvider)
    anthropic_provider.model = "claude-test"
    anthropic_provider.max_tokens = 64
    with pytest.raises(ValueError, match="adapter-owned Anthropic"):
        anthropic_provider._request_envelope_params(
            {"system": "shadow system"}, tools
        )


def test_paid_response_hits_spend_ledger_before_call_record_and_cap_still_records():
    events: list[str] = []

    class OrderedTracker:
        def add(self, usd):
            events.append(f"spend:{usd}")
            raise SpendCapExceeded("crossing call")

    provider = _RecordedProvider(_response(usd_cost=0.25), [])
    provider._spend_tracker = OrderedTracker()
    provider._record_callback = lambda record: events.append(
        f"record:{record.usd_cost}"
    )

    with pytest.raises(SpendCapExceeded, match="crossing call"):
        provider.complete([{"role": "user", "content": "worker=w1 status=running"}])
    assert events == ["spend:0.25", "record:0.25"]


def test_adapter_cannot_add_fields_after_the_request_envelope_is_hashed():
    provider = _RecordedProvider(
        _response(request_metadata={"unhashed_wire_field": "surprise"}), []
    )
    with pytest.raises(RuntimeError, match="absent from the pre-call request envelope"):
        provider.complete([{"role": "user", "content": "worker=w1 status=running"}])


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
    # 15AUG2026 TV-1 repair: the adapter refuses OpenRouter without exactly ONE
    # pinned upstream slug; a whole provider list is not a pin.
    with pytest.raises(RuntimeError, match="requires pinned_upstream"):
        OpenAICompatProvider(
            model="vendor/model",
            base_url="https://openrouter.ai/api/v1",
            api_key="offline-key",
            usd_per_mtok_in=0.0,
            usd_per_mtok_out=0.0,
            record_callback=records.append,
        )
    with pytest.raises(RuntimeError, match="requires pinned_upstream"):
        OpenAICompatProvider(
            model="vendor/model",
            base_url="https://openrouter.ai/api/v1",
            api_key="offline-key",
            usd_per_mtok_in=0.0,
            usd_per_mtok_out=0.0,
            record_callback=records.append,
            provider_order=["vendor-route", "other-route"],  # audit list is not a pin
        )

    provider = OpenAICompatProvider(
        model="vendor/model",
        base_url="https://openrouter.ai/api/v1",
        api_key="offline-key",
        usd_per_mtok_in=0.0,
        usd_per_mtok_out=0.0,
        record_callback=records.append,
        pinned_upstream="vendor-route",
        provider_order=["vendor-route", "other-route", "third-route"],
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
            model="vendor/model",
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
    from harness.providers import ToolDefinition

    response = provider.complete(
        [{"role": "user", "content": "worker=w1 status=running"}],
        tools=[ToolDefinition(name="continue_work", description="Continue work.")],
    )

    # Exactly ONE slug transmitted — the audit list never reaches the wire.
    policy = captured["extra_body"]["provider"]
    assert policy == {
        "order": ["vendor-route"],
        "only": ["vendor-route"],
        "allow_fallbacks": False,
    }
    assert captured["parallel_tool_calls"] is False
    assert captured["tool_choice"] == "auto"
    assert records[-1].upstream_route == "Vendor Route"
    assert records[-1].routing_metadata["attempt"] == 1
    # The endpoint witness's served deployment wins over the top-level echo.
    assert response.model_snapshot == "vendor/model-snapshot-1"
    assert records[-1].model_snapshot == "vendor/model-snapshot-1"


def test_openai_reasoning_token_detail_is_preserved_as_output_subset():
    records: list[CallRecord] = []
    provider = OpenAICompatProvider(
        model="vendor/reasoner",
        base_url="https://offline.invalid/v1",
        api_key="offline-key",
        usd_per_mtok_in=1.0,
        usd_per_mtok_out=2.0,
        record_callback=records.append,
        spend_tracker=SpendTracker(hard_cap_usd=1.0),
    )

    def create(**kwargs):
        message = SimpleNamespace(content="answer", refusal=None, tool_calls=[])
        choice = SimpleNamespace(message=message, finish_reason="stop")
        usage = SimpleNamespace(
            prompt_tokens=10,
            completion_tokens=40,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=30),
        )
        return SimpleNamespace(
            choices=[choice],
            usage=usage,
            model="vendor/reasoner",
            model_extra={},
            _request_id="reasoning-1",
        )

    provider._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    response = provider.complete([{"role": "user", "content": "solve"}])
    assert response.reasoning_tokens == 30
    assert records[0].reasoning_tokens == 30
    assert records[0].output_tokens == 40
    # UNFREEZE-004 regression guard: subset-style usage keeps its historical
    # shape — nothing additive, no raw shadow field.
    assert response.token_accounting == "subset"
    assert response.raw_completion_tokens is None
    assert records[0].token_accounting == "subset"
    assert records[0].raw_completion_tokens is None


def _reasoning_provider(records: list[CallRecord], reasoning_tokens: int):
    """Offline qwen3.8-shaped lane: usage carries a reasoning detail field."""
    provider = OpenAICompatProvider(
        model="vendor/reasoner",
        base_url="https://offline.invalid/v1",
        api_key="offline-key",
        usd_per_mtok_in=1.0,
        usd_per_mtok_out=2.0,
        record_callback=records.append,
        spend_tracker=SpendTracker(hard_cap_usd=1.0),
    )

    def create(**kwargs):
        message = SimpleNamespace(content="answer", refusal=None, tool_calls=[])
        choice = SimpleNamespace(message=message, finish_reason="stop")
        usage = SimpleNamespace(
            prompt_tokens=10,
            completion_tokens=40,
            completion_tokens_details=SimpleNamespace(
                reasoning_tokens=reasoning_tokens
            ),
        )
        return SimpleNamespace(
            choices=[choice],
            usage=usage,
            model="vendor/reasoner",
            model_extra={},
            _request_id="reasoning-additive-1",
        )

    provider._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    return provider


def test_separately_reported_reasoning_bills_additively_instead_of_crashing():
    # UNFREEZE-004 regression: AkashML (upstream for qwen/qwen3.8-27b-20260814)
    # reports reasoning_tokens BESIDE completion_tokens, not inside it. The old
    # subset invariant raised on that dialect and killed main-run phase1 twice
    # (data/raw/confirmatory/call_errors.jsonl). Repair: bill the sum — the
    # ledger can only overcount — witness both raw fields, and never raise.
    records: list[CallRecord] = []
    provider = _reasoning_provider(records, reasoning_tokens=900)
    response = provider.complete([{"role": "user", "content": "solve"}])

    assert response.token_accounting == "additive"
    assert response.raw_completion_tokens == 40
    assert response.reasoning_tokens == 900
    assert response.output_tokens == 940  # billed = completion + reasoning
    assert response.usd_cost == pytest.approx(10 * 1.0 / 1e6 + 940 * 2.0 / 1e6)

    record = records[0]
    assert record.token_accounting == "additive"
    assert record.raw_completion_tokens == 40
    assert record.reasoning_tokens == 900
    assert record.output_tokens == 940
    assert record.usd_cost == pytest.approx(response.usd_cost)


def test_broken_reasoning_meter_still_raises():
    # A reasoning count past 10x the enforced cap (default max_tokens=1024)
    # is not a billing dialect — it is a broken meter, and it still stops.
    records: list[CallRecord] = []
    provider = _reasoning_provider(records, reasoning_tokens=10 * 1024 + 1)
    with pytest.raises(RuntimeError, match="broken usage meter"):
        provider.complete([{"role": "user", "content": "solve"}])
    assert records == []  # no CallRecord is minted for an impossible meter


def test_call_record_additive_accounting_must_show_its_arithmetic():
    base = dict(
        provider="offline_provider",
        upstream_route="offline-direct",
        model_snapshot="offline/snapshot-1",
        scaffold="direct",
        call_kind=CallKind.choice,
        prompt_sha256="0" * 64,
        response_text="",
        input_tokens=1,
        usd_cost=0.0,
    )
    # Additive without the raw witness is a record lying about its own repair.
    with pytest.raises(ValidationError, match="raw non-negative completion_tokens"):
        CallRecord(
            **base, output_tokens=15, reasoning_tokens=10, token_accounting="additive"
        )
    # Additive arithmetic must balance exactly.
    with pytest.raises(ValidationError, match="raw_completion_tokens \\+ reasoning_tokens"):
        CallRecord(
            **base,
            output_tokens=14,
            reasoning_tokens=10,
            token_accounting="additive",
            raw_completion_tokens=5,
        )
    # Balanced additive is valid even though reasoning alone exceeds raw completion.
    record = CallRecord(
        **base,
        output_tokens=15,
        reasoning_tokens=10,
        token_accounting="additive",
        raw_completion_tokens=5,
    )
    assert record.output_tokens == 15
    # Subset records keep the historical invariant and refuse the shadow field.
    with pytest.raises(ValidationError, match="subset of output_tokens"):
        CallRecord(**base, output_tokens=5, reasoning_tokens=10)
    with pytest.raises(ValidationError, match="only exists in"):
        CallRecord(
            **base, output_tokens=15, reasoning_tokens=10, raw_completion_tokens=5
        )
    with pytest.raises(ValidationError, match="unknown token_accounting"):
        CallRecord(
            **base, output_tokens=15, reasoning_tokens=10, token_accounting="vibes"
        )


def test_reasoning_cap_override_is_identical_in_hash_envelope_and_wire():
    records: list[CallRecord] = []
    provider = OpenAICompatProvider(
        model="qwen/qwen3.5-397b-a17b-20260815",
        base_url="https://offline.invalid/v1",
        api_key="offline-key",
        usd_per_mtok_in=0.0,
        usd_per_mtok_out=0.0,
        record_callback=records.append,
        max_tokens=4096,
        enforced_max_tokens=4096,
        spend_tracker=SpendTracker(hard_cap_usd=1.0),
    )
    captured = {}

    def create(**kwargs):
        captured.update(kwargs)
        message = SimpleNamespace(content="answer", refusal=None, tool_calls=[])
        choice = SimpleNamespace(message=message, finish_reason="stop")
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5)
        return SimpleNamespace(
            choices=[choice],
            usage=usage,
            model="qwen/qwen3.5-397b-a17b-20260815",
            model_extra={},
            _request_id="qwen-cap-1",
        )

    provider._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    # Arm B's compiled probe cap is 256. The PI-approved model treatment must
    # replace it before hashing and remain the same on the network boundary.
    provider.complete(
        [{"role": "user", "content": "solve"}],
        max_tokens=256,
    )
    assert captured["max_tokens"] == 4096
    assert records[0].request_params["max_tokens"] == 4096


def test_non_reasoning_lane_retains_the_call_specific_cap():
    provider = OpenAICompatProvider.__new__(OpenAICompatProvider)
    provider.model = "vendor/non-reasoner"
    provider.max_tokens = 1024
    provider.enforced_max_tokens = None
    provider._is_openrouter = False
    assert provider._request_envelope_params({"max_tokens": 256}, [])["max_tokens"] == 256
