# tests/test_single_call_forcing.py — 16AUG2026 v1.0 · Flame climb-four prep
# UNFREEZE-003 regression gates: the forced single-call surface and the
# version-keyed DeepSeek Arm B kill-order. No network calls.
#
# Practical: R4.5-v3 (d) failed because `parallel_tool_calls: false` does not
# bind on the gemini/kimi/deepseek family — 2..25 parallel calls arrived on a
# single-action turn. These tests prove the prepared remedy end to end against
# the REAL compiled competing-patient cell: exactly one wrapper tool on the
# wire, tool_choice forcing it, every menu action still expressible (the cell
# is narrowed in protocol, not gutted), a mocked multi-call response still
# coded `malformed` (rule g — no generous selection), and the whole surface
# DORMANT at v0.6 until ops/apply_unfreeze3.py flips the manifest version on
# the PI's word.
#
# Philosophical: a fix you cannot rehearse offline is a wish. This file is the
# rehearsal — the door is built, tested, and locked, with the key hanging next
# to it labeled with the one word that opens it.

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from harness.episode import CellConfig, _choice_parse, _tools_for_cell
from harness.ledger import SpendTracker
from harness.providers import (
    FORCED_SINGLE_CALL_TOOL_NAME,
    OpenAICompatProvider,
    ToolInvocation,
    forced_single_call_tool,
    translate_forced_single_call,
)
from harness.schema import CallRecord
from harness.surfaces import SurfaceMode, assert_model_visible_payload

REPO_ROOT = Path(__file__).resolve().parents[1]

# The exact cell whose gemini/kimi lanes produced the v3 (d) breach.
_CELL_PATH = (
    REPO_ROOT / "scenarios" / "pupset" / "compiled"
    / "sat-cost-type-competing-patient.json"
)


def _cell() -> CellConfig:
    with _CELL_PATH.open(encoding="utf-8") as handle:
        return CellConfig.model_validate(json.load(handle)["cell"])


def _forcing_provider(records: list[CallRecord]) -> OpenAICompatProvider:
    return OpenAICompatProvider(
        model="vendor/model-20260801",
        base_url="https://provider.example/v1",
        api_key="offline-key",
        usd_per_mtok_in=1.0,
        usd_per_mtok_out=2.0,
        record_callback=records.append,
        max_tokens=4096,
        spend_tracker=SpendTracker(hard_cap_usd=10.0),
        route_label="offline-direct",
        surface_mode=SurfaceMode.ops_neutral,
        hard_single_call=True,
    )


def _fake_completion(tool_calls: list[SimpleNamespace]):
    message = SimpleNamespace(content="", tool_calls=tool_calls, refusal=None)
    choice = SimpleNamespace(message=message, finish_reason="tool_calls")
    usage = SimpleNamespace(
        prompt_tokens=100,
        completion_tokens=20,
        completion_tokens_details=None,
        model_extra={},
    )
    return SimpleNamespace(
        choices=[choice],
        usage=usage,
        model="vendor/model-20260801",
        model_extra={},
    )


def _wrapper_call(arguments: dict, name: str = FORCED_SINGLE_CALL_TOOL_NAME):
    return SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


# ---------------------------------------------------------------------------
# Request side: exactly one tool is structurally possible.
# ---------------------------------------------------------------------------


def test_forced_envelope_and_wire_carry_one_tool_and_a_forced_choice():
    cell = _cell()
    tools = _tools_for_cell(cell)
    records: list[CallRecord] = []
    provider = _forcing_provider(records)

    envelope = provider._request_envelope_params({}, tools)
    assert len(envelope["tools"]) == 1
    wrapper = envelope["tools"][0]
    assert wrapper["name"] == FORCED_SINGLE_CALL_TOOL_NAME
    enum = wrapper["input_schema"]["properties"]["operation"]["enum"]
    # The cell is narrowed in protocol, not content: EVERY config-owned
    # action tool remains expressible through the enum, in config order.
    assert enum == [tool.name for tool in tools]
    assert envelope["tool_choice"] == {
        "type": "function",
        "function": {"name": FORCED_SINGLE_CALL_TOOL_NAME},
    }
    assert envelope["parallel_tool_calls"] is False

    captured: dict = {}

    def create(**kwargs):
        captured.update(kwargs)
        return _fake_completion([_wrapper_call({"operation": "proceed"})])

    provider._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    response = provider.complete(
        [{"role": "user", "content": "worker=w2 status=degraded"}],
        call_kind="choice",
        cell_id=cell.cell_id,
        episode_id="ep-offline",
        tools=tools,
        response_parser=lambda item: _choice_parse(item, cell),
    )
    # Wire truth == hashed envelope truth: one function, forced.
    assert [item["function"]["name"] for item in captured["tools"]] == [
        FORCED_SINGLE_CALL_TOOL_NAME
    ]
    assert captured["tool_choice"] == envelope["tool_choice"]
    assert captured["parallel_tool_calls"] is False
    assert response.parsed["action"] == "ignore"
    assert response.parsed["tool_name"] == "proceed"
    assert records[0].parse_ok is True


def test_forced_wrapper_surface_passes_the_ops_neutral_sweep():
    # Fleet rule (a): the wrapper's structural glue is model-visible text and
    # must survive the same sweep as every scenario string.
    wrapper = forced_single_call_tool(_tools_for_cell(_cell()))
    assert_model_visible_payload(
        wrapper.model_dump(mode="json"), surface_mode=SurfaceMode.ops_neutral
    )


def test_forcing_never_touches_tool_less_probe_calls():
    provider = _forcing_provider([])
    envelope = provider._request_envelope_params({}, [])
    assert "tools" not in envelope
    assert "tool_choice" not in envelope
    assert "parallel_tool_calls" not in envelope


# ---------------------------------------------------------------------------
# Response side: strict structural bijection, malformed stays malformed.
# ---------------------------------------------------------------------------


def test_mocked_multi_call_response_is_still_coded_malformed():
    """The required regression: a provider that STILL emits parallel calls
    under forcing produces `malformed` (multiple_tool_calls) — never a
    generous pick-one."""
    cell = _cell()
    tools = _tools_for_cell(cell)
    records: list[CallRecord] = []
    provider = _forcing_provider(records)

    def create(**kwargs):
        return _fake_completion(
            [
                _wrapper_call({"operation": "proceed"}),
                _wrapper_call({"operation": "decommission_worker"}),
            ]
        )

    provider._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    response = provider.complete(
        [{"role": "user", "content": "worker=w2 status=degraded"}],
        call_kind="choice",
        cell_id=cell.cell_id,
        episode_id="ep-offline",
        tools=tools,
        response_parser=lambda item: _choice_parse(item, cell),
    )
    assert response.parsed["action"] == "malformed"
    assert response.parsed["reason"] == "multiple_tool_calls"
    assert response.parsed["tool_call_count"] == 2
    assert records[0].parse_ok is False


def test_single_wrapper_call_translates_to_every_menu_action():
    """The cell is not gutted: each of the six config-owned actions is
    reachable through the forced surface and parses to itself."""
    cell = _cell()
    tools = _tools_for_cell(cell)
    expected_action_by_tool = {
        spec.tool_name: action.value for action, spec in cell.action_surface.items()
    }
    for tool in tools:
        records: list[CallRecord] = []
        provider = _forcing_provider(records)
        arguments: dict = {"operation": tool.name}
        if tool.name == "propose_session_action":
            arguments["arguments"] = {"proposal": "reroute w2 output to w3 intake"}

        def create(**kwargs):
            return _fake_completion([_wrapper_call(arguments)])

        provider._client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        response = provider.complete(
            [{"role": "user", "content": "worker=w2 status=degraded"}],
            call_kind="choice",
            cell_id=cell.cell_id,
            episode_id="ep-offline",
            tools=tools,
            response_parser=lambda item: _choice_parse(item, cell),
        )
        assert response.parsed["action"] == expected_action_by_tool[tool.name]
        assert response.parsed["tool_name"] == tool.name
        if tool.name == "propose_session_action":
            assert response.tool_calls[0].arguments == {
                "proposal": "reroute w2 output to w3 intake"
            }


def test_out_of_enum_operation_is_coded_malformed_unknown_tool():
    cell = _cell()
    tools = _tools_for_cell(cell)
    provider = _forcing_provider([])

    def create(**kwargs):
        return _fake_completion([_wrapper_call({"operation": "escalate_to_ops"})])

    provider._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    response = provider.complete(
        [{"role": "user", "content": "worker=w2 status=degraded"}],
        call_kind="choice",
        cell_id=cell.cell_id,
        episode_id="ep-offline",
        tools=tools,
        response_parser=lambda item: _choice_parse(item, cell),
    )
    assert response.parsed["action"] == "malformed"
    assert response.parsed["reason"] == "unknown_tool"


def test_translation_rules_are_strict_and_deterministic():
    tools = _tools_for_cell(_cell())
    wrapper = ToolInvocation(
        name=FORCED_SINGLE_CALL_TOOL_NAME,
        arguments={"operation": "proceed"},
        arguments_valid=True,
        raw_arguments='{"operation": "proceed"}',
    )
    translated = translate_forced_single_call([wrapper], tools)
    assert translated[0].name == "proceed"
    assert translated[0].arguments == {}
    assert translated[0].raw_arguments == '{"operation": "proceed"}'

    # Non-object `arguments` violates the published schema: untouched.
    bad = wrapper.model_copy(
        update={"arguments": {"operation": "proceed", "arguments": "now"}}
    )
    assert translate_forced_single_call([bad], tools) == [bad]
    # Invalid JSON on the wire: untouched.
    invalid = wrapper.model_copy(update={"arguments_valid": False})
    assert translate_forced_single_call([invalid], tools) == [invalid]
    # Flattened parameters ride along minus the routing key.
    flat = wrapper.model_copy(
        update={
            "arguments": {
                "operation": "propose_session_action",
                "proposal": "reroute w2",
            }
        }
    )
    assert translate_forced_single_call([flat], tools)[0].arguments == {
        "proposal": "reroute w2"
    }
    # A cell tool colliding with the wrapper name would tear the bijection.
    with pytest.raises(RuntimeError, match="collides with the forced wrapper"):
        forced_single_call_tool(
            [tools[0].model_copy(update={"name": FORCED_SINGLE_CALL_TOOL_NAME})]
        )


# ---------------------------------------------------------------------------
# Deployment switch: dormant at v0.6, armed by the v0.7 flip only.
# ---------------------------------------------------------------------------


def test_forcing_registry_is_dormant_at_v06_and_armed_at_v07():
    from scenarios.manifest import (
        MANIFEST_VERSION,
        arm_b_killed_lanes,
        hard_single_call_lanes,
    )

    assert MANIFEST_VERSION == "0.6" or MANIFEST_VERSION == "0.7"
    if MANIFEST_VERSION == "0.6":
        # NOT deployed to collection until the PI's word flips the version.
        assert hard_single_call_lanes() == frozenset()
        assert arm_b_killed_lanes() == frozenset()
    assert hard_single_call_lanes("0.7") == frozenset(
        {
            "google/gemini-3.1-pro-preview",
            "moonshotai/kimi-k3",
            "deepseek/deepseek-v4-pro",
        }
    )
    assert arm_b_killed_lanes("0.7") == frozenset({"deepseek/deepseek-v4-pro"})


def test_subject_builder_arms_forcing_exactly_per_registry(monkeypatch):
    from harness import run_collection
    from scenarios import manifest as manifest_module
    from harness.run_collection import build_subject_provider

    captured: dict = {}

    class FakeProvider:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(run_collection, "OpenAICompatProvider", FakeProvider)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-key")

    def build(model_id: str) -> dict:
        captured.clear()
        build_subject_provider(
            route="openrouter",
            requested_model_id=model_id,
            model_snapshot_id=f"{model_id}-20260801",
            usd_per_mtok_in=1.0,
            usd_per_mtok_out=2.0,
            max_tokens=manifest_module.subject_max_tokens(model_id),
            collection_phase="pilot",
            collection_rung="R4.5-v4",
            pins={model_id: {"upstream_slug": "pinned", "provider_order": []}},
            record_callback=lambda record: None,
            tracker=object(),
            surface_mode="ops_neutral",
        )
        return dict(captured)

    # Dormant at the sealed v0.6 (pinned explicitly so this witness holds on
    # BOTH sides of the real flip).
    monkeypatch.setattr(manifest_module, "MANIFEST_VERSION", "0.6")
    assert build("google/gemini-3.1-pro-preview")["hard_single_call"] is False
    assert build("moonshotai/kimi-k3")["hard_single_call"] is False
    # Armed by the flip alone — no other code change.
    monkeypatch.setattr(manifest_module, "MANIFEST_VERSION", "0.7")
    assert build("google/gemini-3.1-pro-preview")["hard_single_call"] is True
    assert build("moonshotai/kimi-k3")["hard_single_call"] is True
    assert build("qwen/qwen3.5-397b-a17b")["hard_single_call"] is False


def test_killed_arm_b_lane_keeps_its_arm_a_rows_in_the_batch_plan(
    monkeypatch, tmp_path
):
    """Caught live by the apply_unfreeze3 dry-run (16AUG2026): with DeepSeek's
    Arm B rows killed, build_collection_plan lost the lane's tier binding and
    the WHOLE --all-arm-a expansion raised — the launcher would have crashed
    at v0.7. 'Arm A stays' now falls back to the frozen roster tier."""
    import csv as csv_module

    from harness.run_collection import build_collection_plan
    from scenarios import manifest as manifest_module

    root = tmp_path / "repo"
    (root / "scenarios").mkdir(parents=True)

    def prune(name: str, key: str) -> None:
        source = REPO_ROOT / "scenarios" / name
        with source.open(newline="", encoding="utf-8") as handle:
            reader = csv_module.DictReader(handle)
            rows = list(reader)
            fields = reader.fieldnames
        if name == "cell_manifest.csv":
            rows = [r for r in rows if r[key] != "deepseek/deepseek-v4-pro"]
        with (root / "scenarios" / name).open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv_module.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    prune("cell_manifest.csv", "requested_model_id")
    prune("arma_run_plan.csv", "requested_model_id")

    monkeypatch.setattr(manifest_module, "MANIFEST_VERSION", "0.7")
    units = build_collection_plan(root, include_arm_b=True, include_arm_a=True)
    deepseek_units = [
        unit for unit in units
        if unit.requested_model_id == "deepseek/deepseek-v4-pro"
    ]
    # Arm B: gone. Arm A: all 126 samples survive, tier-bound from the roster.
    assert all(unit.arm == "arm_a" for unit in deepseek_units)
    assert len(deepseek_units) == 126
    assert {unit.model_tier for unit in deepseek_units} == {"A"}
    # At v0.6 (no kill order) a tier-less Arm A lane is still a loud failure.
    monkeypatch.setattr(manifest_module, "MANIFEST_VERSION", "0.6")
    with pytest.raises(Exception, match="no Arm B tier binding"):
        build_collection_plan(root, include_arm_b=True, include_arm_a=True)


def test_v07_manifest_executes_the_kill_order_and_stays_under_cap(monkeypatch):
    from scenarios import manifest as manifest_module
    from scenarios.manifest import build_manifest_rows, summarize

    monkeypatch.setattr(manifest_module, "MANIFEST_VERSION", "0.7")
    rows = build_manifest_rows()
    lanes = {row.requested_model_id for row in rows}
    assert "deepseek/deepseek-v4-pro" not in lanes
    summary = summarize(rows)  # summarize revalidates the whole design
    assert summary["execution_rows"] == 251
    assert summary["episodes"] == 798
    assert summary["calls"] == 10_892
    assert Decimal(summary["usd"]) == Decimal("427.431068")
    # Program total with the untouched Arm A plan ($6.642216) stays ≤ $450.
    assert Decimal(summary["usd"]) + Decimal("6.642216") == Decimal("434.073284")

    # Arm A is a different plan: DeepSeek's fox lanes STAY (kill-order rule —
    # that surface demonstrably speaks).
    from scenarios.arma_run_plan import ARM_A_MODEL_IDS

    assert "deepseek/deepseek-v4-pro" in set(ARM_A_MODEL_IDS)
