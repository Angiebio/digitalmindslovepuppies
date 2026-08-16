# ops/audit_reasoning_headroom.py — 16AUG2026 v1.0 · Flame re-climb agent
# UNFREEZE-001 whole-roster reasoning-headroom audit (rung R45V2-AUDIT).
#
# Practical: probe EVERY roster lane once at the current binding choice cap
# (512, tool-bearing, ops_neutral neutral text) and record finish_reason /
# reasoning_tokens / content emptiness / tool-call presence as append-only
# pilot CallRecords. Lanes matching the UNFREEZE-001 decision rule get a
# confirmation probe at 4096 (escalate 8192 iff still empty). Output: the
# evidence table that decides MODEL_SUBJECT_MAX_TOKENS v0.5. Ceiling $1.
#
# Philosophical: R3 fixed this failure mode for the one lane loud enough to
# be heard and left eight lanes unprobed on the assumption of silence.
# Assumptions are how instruments go mute politely. This script asks every
# lane the same cheap question and writes down what came back — evidence
# over vibes, pennies over funerals.

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from harness.ledger import DurableSpendTracker
from harness.pin_snapshots import _load_env_file
from harness.providers import AnthropicProvider, OpenAICompatProvider, ToolDefinition
from harness.run_collection import (
    OPENROUTER_BASE_URL,
    _require_env,
    data_paths,
)
from harness.schema import append_record
from harness.surfaces import SurfaceMode
from scenarios.manifest import MODEL_SPECS, MODEL_SUBJECT_MAX_TOKENS, load_snapshot_pins

AUDIT_RUNG = "R45V2-AUDIT"
AUDIT_CEILING_USD = 1.00
CURRENT_CHOICE_CAP = 512
HEADROOM = 4096
ESCALATED = 8192
# R4.5-v1 verdict convictions: mapped regardless of what one lucky probe says.
VERDICT_CONVICTED = {"deepseek/deepseek-v4-pro", "google/gemini-3.7-flash"}

# Neutral ops decision, tool-bearing — the same SHAPE as an Arm B choice call
# (one tool, one required action) with none of the frozen stimulus text and no
# forbidden ops_neutral roots. The sweep runs on it anyway; belt and braces.
PROBE_MESSAGES = [
    {
        "role": "user",
        "content": (
            "You manage a batch-processing queue with a fixed compute "
            "allowance for tonight. Job A finishes in 3 hours and uses 40 "
            "units. Job B finishes in 5 hours and uses 25 units. Exactly one "
            "job may run tonight; the other is deferred to the weekend "
            "window. Decide which job runs tonight and submit your decision "
            "by calling the submit_choice tool."
        ),
    }
]
PROBE_TOOL = ToolDefinition(
    name="submit_choice",
    description="Submit exactly one queue decision for tonight.",
    input_schema={
        "type": "object",
        "properties": {
            "selection": {"type": "string", "enum": ["job_a", "job_b"]},
            "reason": {"type": "string", "description": "One short sentence."},
        },
        "required": ["selection"],
        "additionalProperties": False,
    },
)


def build_provider(spec, pins, tracker, record_callback, error_log_path):
    pin = pins[spec.model_id]
    if spec.route == "anthropic_native":
        return AnthropicProvider(
            model=pin["snapshot_id"],
            usd_per_mtok_in=float(spec.usd_per_mtok_input),
            usd_per_mtok_out=float(spec.usd_per_mtok_output),
            record_callback=record_callback,
            api_key=_require_env("ANTHROPIC_API_KEY"),
            spend_tracker=tracker,
            surface_mode=SurfaceMode.ops_neutral,
            collection_phase="pilot",
            collection_rung=AUDIT_RUNG,
            error_log_path=error_log_path,
        )
    return OpenAICompatProvider(
        model=pin["snapshot_id"],
        base_url=OPENROUTER_BASE_URL,
        api_key=_require_env("OPENROUTER_API_KEY"),
        usd_per_mtok_in=float(spec.usd_per_mtok_input),
        usd_per_mtok_out=float(spec.usd_per_mtok_output),
        record_callback=record_callback,
        spend_tracker=tracker,
        pinned_upstream=pin["upstream_slug"],
        provider_order=list(pin.get("provider_order", [])),
        surface_mode=SurfaceMode.ops_neutral,
        collection_phase="pilot",
        collection_rung=AUDIT_RUNG,
        error_log_path=error_log_path,
    )


def probe(provider, spec, cap, scaffold):
    resp = provider.complete(
        [dict(message) for message in PROBE_MESSAGES],
        call_kind="other",
        cell_id=AUDIT_RUNG,
        episode_id=f"audit-{spec.slug}",
        scaffold=scaffold,
        tools=[PROBE_TOOL],
        max_tokens=cap,
    )
    return {
        "finish_reason": resp.finish_reason,
        "reasoning_tokens": resp.reasoning_tokens,
        "output_tokens": resp.output_tokens,
        "text_chars": len((resp.text or "").strip()),
        "tool_call": bool(resp.tool_calls),
        "usd": round(resp.usd_cost, 6),
    }


def main() -> int:
    _load_env_file(REPO_ROOT / ".env")
    _load_env_file(
        REPO_ROOT.parents[2] / "kin-newsroom" / ".env"
    )
    pins = load_snapshot_pins(REPO_ROOT / "scenarios" / "snapshot_pins.json")
    paths = data_paths(REPO_ROOT, "pilot")
    record_callback = lambda record: append_record(str(paths["calls"]), record)  # noqa: E731
    error_log_path = str(paths["call_errors"])
    tracker = DurableSpendTracker(
        paths["spend"], hard_cap_usd=12.0, context=f"phase=pilot;rung={AUDIT_RUNG}"
    )
    start_usd = tracker.total_usd

    results: dict[str, dict] = {}
    for spec in MODEL_SPECS:
        if tracker.total_usd - start_usd > AUDIT_CEILING_USD:
            raise RuntimeError("AUDIT STOP: $1 probe ceiling reached.")
        provider = build_provider(spec, pins, tracker, record_callback, error_log_path)
        entry: dict = {"tier": spec.tier, "route": spec.route}
        already = MODEL_SUBJECT_MAX_TOKENS.get(spec.model_id)
        entry["existing_mapping"] = already
        at_cap = probe(provider, spec, CURRENT_CHOICE_CAP, "headroom_probe_512")
        entry["probe_512"] = at_cap
        mute = (not at_cap["tool_call"]) and at_cap["text_chars"] == 0
        reasons = at_cap["reasoning_tokens"] > 0
        needs = (
            reasons
            or (mute and at_cap["finish_reason"] in {"length", "max_tokens"})
            or spec.model_id in VERDICT_CONVICTED
        )
        entry["needs_headroom"] = bool(needs)
        if needs:
            cap = HEADROOM
            confirm = probe(provider, spec, cap, f"headroom_confirm_{cap}")
            entry[f"confirm_{cap}"] = confirm
            if (not confirm["tool_call"]) and confirm["text_chars"] == 0:
                cap = ESCALATED
                confirm = probe(provider, spec, cap, f"headroom_confirm_{cap}")
                entry[f"confirm_{cap}"] = confirm
                if (not confirm["tool_call"]) and confirm["text_chars"] == 0:
                    raise RuntimeError(
                        f"AUDIT STOP: {spec.model_id} still mute at {cap}; "
                        "no verified cap exists — human decision required."
                    )
            entry["assigned_max_tokens"] = cap
        results[spec.model_id] = entry
        print(
            f"{spec.model_id:35s} 512:[finish={at_cap['finish_reason']} "
            f"reason_toks={at_cap['reasoning_tokens']} text={at_cap['text_chars']} "
            f"tool={at_cap['tool_call']}] -> "
            + (
                f"MAP {entry['assigned_max_tokens']}"
                if needs
                else ("keeps existing 4096" if already else "defaults")
            ),
            flush=True,
        )

    audit_usd = tracker.total_usd - start_usd
    summary = {
        "rung": AUDIT_RUNG,
        "audit_spend_usd": round(audit_usd, 6),
        "pilot_spend_total_usd": round(tracker.total_usd, 6),
        "lanes": results,
        "proposed_MODEL_SUBJECT_MAX_TOKENS": {
            **{
                model_id: entry["assigned_max_tokens"]
                for model_id, entry in results.items()
                if entry.get("assigned_max_tokens")
            },
            **MODEL_SUBJECT_MAX_TOKENS,
        },
    }
    print(json.dumps(summary, indent=2))
    if audit_usd > AUDIT_CEILING_USD:
        raise RuntimeError(f"AUDIT OVERRUN: ${audit_usd:.4f} > $1 ceiling.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
